"""
MCP (Model Context Protocol) client implementation.

This module provides client classes for connecting to MCP servers,
discovering tools, and executing them via JSON-RPC over HTTP.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union, Callable, AsyncGenerator
from urllib.parse import urljoin
import uuid

try:
    import httpx
    import aiohttp
    from sse_starlette import EventSourceResponse
except ImportError as e:
    raise ImportError(f"Missing required dependencies for MCP client: {e}. Install with: pip install httpx aiohttp sse-starlette")

from .config import MCPConfig, MCPServerConfig
from .exceptions import (
    MCPError, MCPConnectionError, MCPToolError, MCPTimeoutError,
    MCPAuthenticationError, MCPServerUnavailableError, MCPSchemaError
)

logger = logging.getLogger(__name__)


@dataclass
class MCPToolSchema:
    """Represents a tool schema from an MCP server."""
    name: str
    description: str
    parameters: Dict[str, Any]
    server_name: str
    server_url: str
    last_updated: float

    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


@dataclass
class MCPToolResult:
    """Result from MCP tool execution."""
    success: bool
    result: Any = None
    error: Optional[str] = None
    server_name: Optional[str] = None
    tool_name: Optional[str] = None
    execution_time: Optional[float] = None
    request_id: Optional[str] = None


class RateLimiter:
    """Simple rate limiter for MCP requests."""

    def __init__(self, requests_per_minute: int, burst: int = None):
        self.requests_per_minute = requests_per_minute
        self.burst = burst or requests_per_minute
        self.tokens = self.burst
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """Acquire a token for making a request."""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # Refill tokens based on elapsed time
            tokens_to_add = elapsed * (self.requests_per_minute / 60.0)
            self.tokens = min(self.burst, self.tokens + tokens_to_add)
            self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False


class MCPClient:
    """Client for connecting to a single MCP server."""

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.base_url = config.url.rstrip('/')
        self.session: Optional[httpx.AsyncClient] = None
        self.tool_schemas: Dict[str, MCPToolSchema] = {}
        self.last_schema_update = 0
        self.rate_limiter = None
        self.health_check_task: Optional[asyncio.Task] = None
        self._closed = False

        if config.rate_limit_requests_per_minute:
            self.rate_limiter = RateLimiter(
                config.rate_limit_requests_per_minute,
                config.rate_limit_burst
            )

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        """Connect to the MCP server."""
        if self._closed:
            raise MCPError("Client is closed")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "FlexiAI-MCP-Client/1.0"
        }

        # Add authentication headers
        auth_headers = self.config.get_auth_headers()
        headers.update(auth_headers)
        headers.update(self.config.custom_headers)

        self.session = httpx.AsyncClient(
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
            headers=headers
        )

        # Test connection
        try:
            health_ok = await self._health_check()
            if not health_ok:
                raise MCPConnectionError(
                    "Health check failed - server may be unavailable",
                    server_url=self.config.url
                )

            logger.info(f"Connected to MCP server: {self.config.name}")

            # Start health check task if enabled
            if self.config.health_check_enabled:
                self.health_check_task = asyncio.create_task(self._health_check_loop())

        except MCPConnectionError:
            await self.close()
            raise
        except Exception as e:
            await self.close()
            raise MCPConnectionError(
                f"Failed to connect to server: {e}",
                server_url=self.config.url
            )

    async def close(self):
        """Close the client connection."""
        if self._closed:
            return

        self._closed = True

        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

        if self.session:
            await self.session.aclose()
            self.session = None

        logger.info(f"Closed connection to MCP server: {self.config.name}")

    async def _health_check(self):
        """Perform health check on the server."""
        try:
            response = await self.session.get(
                urljoin(self.base_url, "/mcp/health"),
                timeout=self.config.health_check_timeout
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Health check failed for {self.config.name}: {e}")
            return False

    async def _health_check_loop(self):
        """Background health check loop."""
        while not self._closed:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                if not self._closed:
                    await self._health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error for {self.config.name}: {e}")

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make HTTP request with retries and rate limiting."""
        if self._closed or not self.session:
            raise MCPConnectionError("Client not connected")

        # Apply rate limiting
        if self.rate_limiter:
            attempts = 0
            while attempts < 10:  # Prevent infinite loop
                if await self.rate_limiter.acquire():
                    break
                attempts += 1
                await asyncio.sleep(0.1)
            else:
                raise MCPError("Rate limit exceeded")

        url = urljoin(self.base_url, endpoint)
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self.session.request(method, url, **kwargs)

                if response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get("retry-after", 60))
                    raise MCPServerUnavailableError(
                        "Server rate limited",
                        server_url=self.config.url,
                        retry_after=retry_after
                    )

                if response.status_code == 401:
                    raise MCPAuthenticationError(
                        "Authentication failed",
                        server_url=self.config.url,
                        auth_method=self.config.auth_type
                    )

                response.raise_for_status()
                return response

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}), retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                continue
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < self.config.max_retries:
                    # Retry on server errors
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Server error (attempt {attempt + 1}), retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                    continue
                raise MCPConnectionError(
                    f"HTTP error: {e.response.status_code}",
                    server_url=self.config.url,
                    status_code=e.response.status_code
                )

        # All retries exhausted
        raise MCPConnectionError(
            f"Max retries exhausted: {last_exception}",
            server_url=self.config.url
        )

    async def discover_tools(self, force_refresh: bool = False) -> List[MCPToolSchema]:
        """Discover available tools from the server."""
        current_time = time.time()

        # Use cached schemas if they're still fresh
        if (not force_refresh and
            self.tool_schemas and
            current_time - self.last_schema_update < 300):  # 5 minutes cache
            return list(self.tool_schemas.values())

        try:
            response = await self._make_request("GET", "/mcp/tools")
            data = response.json()

            if not isinstance(data, dict) or "tools" not in data:
                raise MCPSchemaError(
                    "Invalid tools response format",
                    schema_type="tools",
                    server_url=self.config.url
                )

            schemas = []
            for tool_data in data["tools"]:
                try:
                    schema = MCPToolSchema(
                        name=tool_data["name"],
                        description=tool_data.get("description", ""),
                        parameters=tool_data.get("parameters", {}),
                        server_name=self.config.name,
                        server_url=self.config.url,
                        last_updated=current_time
                    )

                    # Check if tool is allowed
                    if self.config.is_tool_allowed(schema.name):
                        schemas.append(schema)
                        self.tool_schemas[schema.name] = schema
                    else:
                        logger.debug(f"Tool {schema.name} not allowed by configuration")

                except KeyError as e:
                    logger.warning(f"Invalid tool schema missing field {e}: {tool_data}")
                    continue

            self.last_schema_update = current_time
            logger.info(f"Discovered {len(schemas)} tools from {self.config.name}")
            return schemas

        except Exception as e:
            if isinstance(e, (MCPError, MCPConnectionError)):
                raise
            raise MCPSchemaError(
                f"Failed to discover tools: {e}",
                schema_type="tools",
                server_url=self.config.url
            )

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any] = None) -> MCPToolResult:
        """Execute a tool on the server."""
        if tool_name not in self.tool_schemas:
            # Try to refresh schemas
            await self.discover_tools(force_refresh=True)

            if tool_name not in self.tool_schemas:
                return MCPToolResult(
                    success=False,
                    error=f"Tool '{tool_name}' not found on server {self.config.name}",
                    server_name=self.config.name,
                    tool_name=tool_name
                )

        if not self.config.is_tool_allowed(tool_name):
            return MCPToolResult(
                success=False,
                error=f"Tool '{tool_name}' not allowed by configuration",
                server_name=self.config.name,
                tool_name=tool_name
            )

        request_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Prepare JSON-RPC request
            rpc_request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tool_execute",
                "params": {
                    "tool": tool_name,
                    "parameters": parameters or {}
                }
            }

            response = await self._make_request(
                "POST",
                "/mcp/execute",
                json=rpc_request
            )

            execution_time = time.time() - start_time
            data = response.json()

            # Handle JSON-RPC response
            if "error" in data:
                error_info = data["error"]
                return MCPToolResult(
                    success=False,
                    error=f"{error_info.get('message', 'Unknown error')} (code: {error_info.get('code', 'unknown')})",
                    server_name=self.config.name,
                    tool_name=tool_name,
                    execution_time=execution_time,
                    request_id=request_id
                )

            result = data.get("result")
            return MCPToolResult(
                success=True,
                result=result,
                server_name=self.config.name,
                tool_name=tool_name,
                execution_time=execution_time,
                request_id=request_id
            )

        except Exception as e:
            execution_time = time.time() - start_time
            if isinstance(e, (MCPError, MCPConnectionError)):
                error_msg = str(e)
            else:
                error_msg = f"Tool execution failed: {e}"

            return MCPToolResult(
                success=False,
                error=error_msg,
                server_name=self.config.name,
                tool_name=tool_name,
                execution_time=execution_time,
                request_id=request_id
            )

    async def stream_tool_execution(self, tool_name: str, parameters: Dict[str, Any] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute a tool with streaming results via SSE."""
        if not self.config.use_sse:
            raise MCPError("SSE streaming not enabled for this server")

        if tool_name not in self.tool_schemas:
            await self.discover_tools(force_refresh=True)

            if tool_name not in self.tool_schemas:
                yield {
                    "type": "error",
                    "error": f"Tool '{tool_name}' not found on server {self.config.name}"
                }
                return

        if not self.config.is_tool_allowed(tool_name):
            yield {
                "type": "error",
                "error": f"Tool '{tool_name}' not allowed by configuration"
            }
            return

        request_id = str(uuid.uuid4())

        try:
            # Stream endpoint with query parameters
            params = {
                "tool": tool_name,
                "request_id": request_id,
                **parameters
            }

            url = urljoin(self.base_url, "/mcp/stream")

            async with self.session.stream("GET", url, params=params) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            yield data
                        except json.JSONDecodeError:
                            continue
                    elif line.startswith("event: "):
                        # Handle different event types if needed
                        continue

        except Exception as e:
            yield {
                "type": "error",
                "error": f"Streaming failed: {e}",
                "request_id": request_id
            }

    def get_tool_schema(self, tool_name: str) -> Optional[MCPToolSchema]:
        """Get schema for a specific tool."""
        return self.tool_schemas.get(tool_name)

    def list_tool_names(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tool_schemas.keys())


class MCPClientManager:
    """Manager for multiple MCP server connections."""

    def __init__(self, config: MCPConfig):
        self.config = config
        self.clients: Dict[str, MCPClient] = {}
        self.tool_schemas: Dict[str, MCPToolSchema] = {}
        self.schema_cache_lock = asyncio.Lock()
        self._closed = False
        self.discovery_task: Optional[asyncio.Task] = None

    async def __aenter__(self):
        await self.connect_all()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_all()

    async def connect_all(self):
        """Connect to all enabled servers."""
        if self._closed:
            raise MCPError("Manager is closed")

        enabled_servers = self.config.get_enabled_servers()

        if not enabled_servers:
            logger.warning("No enabled MCP servers found in configuration")
            return

        connection_tasks = []
        for server_config in enabled_servers:
            client = MCPClient(server_config)
            self.clients[server_config.name] = client
            connection_tasks.append(self._connect_client(client))

        # Connect to all servers concurrently
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)

        connected_count = 0
        for i, result in enumerate(results):
            server_name = enabled_servers[i].name
            if isinstance(result, Exception):
                logger.error(f"Failed to connect to {server_name}: {result}")
                # Remove failed client
                if server_name in self.clients:
                    del self.clients[server_name]
            else:
                connected_count += 1

        logger.info(f"Connected to {connected_count}/{len(enabled_servers)} MCP servers")

        # Start tool discovery if auto-discovery is enabled
        if self.config.auto_discover_tools and connected_count > 0:
            await self.discover_all_tools()

            # Start periodic discovery task
            self.discovery_task = asyncio.create_task(self._discovery_loop())

    async def _connect_client(self, client: MCPClient):
        """Connect a single client with error handling."""
        try:
            await client.connect()
            return True
        except Exception as e:
            # Let the exception propagate to be handled by gather()
            raise e

    async def close_all(self):
        """Close all client connections."""
        if self._closed:
            return

        self._closed = True

        if self.discovery_task:
            self.discovery_task.cancel()
            try:
                await self.discovery_task
            except asyncio.CancelledError:
                pass

        close_tasks = [client.close() for client in self.clients.values()]
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)

        self.clients.clear()
        self.tool_schemas.clear()
        logger.info("Closed all MCP client connections")

    async def _discovery_loop(self):
        """Background tool discovery loop."""
        while not self._closed:
            try:
                await asyncio.sleep(self.config.tool_discovery_interval)
                if not self._closed:
                    await self.discover_all_tools()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Tool discovery loop error: {e}")

    async def discover_all_tools(self, force_refresh: bool = False):
        """Discover tools from all connected servers."""
        if not self.clients:
            logger.warning("No connected MCP clients for tool discovery")
            return

        async with self.schema_cache_lock:
            # Clear old schemas if force refresh
            if force_refresh:
                self.tool_schemas.clear()

            discovery_tasks = []
            for client in self.clients.values():
                discovery_tasks.append(self._discover_client_tools(client, force_refresh))

            # Discover from all clients concurrently
            results = await asyncio.gather(*discovery_tasks, return_exceptions=True)

            total_tools = 0
            for i, result in enumerate(results):
                client_name = list(self.clients.keys())[i]
                if isinstance(result, Exception):
                    logger.error(f"Tool discovery failed for {client_name}: {result}")
                else:
                    schemas = result
                    for schema in schemas:
                        self.tool_schemas[f"{schema.server_name}.{schema.name}"] = schema
                        # Also store without server prefix for backwards compatibility
                        if schema.name not in self.tool_schemas:
                            self.tool_schemas[schema.name] = schema
                    total_tools += len(schemas)

            logger.info(f"Discovered {total_tools} total tools from {len(self.clients)} servers")

    async def _discover_client_tools(self, client: MCPClient, force_refresh: bool = False) -> List[MCPToolSchema]:
        """Discover tools from a single client."""
        try:
            return await client.discover_tools(force_refresh)
        except Exception as e:
            logger.error(f"Failed to discover tools from {client.config.name}: {e}")
            return []

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any] = None, preferred_server: str = None) -> MCPToolResult:
        """
        Execute a tool on any available server.

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            preferred_server: Preferred server name (optional)
        """
        if not self.clients:
            return MCPToolResult(
                success=False,
                error="No MCP servers connected",
                tool_name=tool_name
            )

        # Try preferred server first
        if preferred_server and preferred_server in self.clients:
            client = self.clients[preferred_server]
            if tool_name in client.tool_schemas:
                return await client.execute_tool(tool_name, parameters)

        # Try servers that have this tool
        for client in self.clients.values():
            if tool_name in client.tool_schemas:
                result = await client.execute_tool(tool_name, parameters)
                if result.success or not self.config.fail_on_server_error:
                    return result

        return MCPToolResult(
            success=False,
            error=f"Tool '{tool_name}' not found on any connected server",
            tool_name=tool_name
        )

    async def execute_tool_with_fallback(self, tool_name: str, parameters: Dict[str, Any] = None) -> MCPToolResult:
        """Execute tool with fallback to other servers on failure."""
        if not self.clients:
            return MCPToolResult(
                success=False,
                error="No MCP servers connected",
                tool_name=tool_name
            )

        # Get all clients that have this tool
        available_clients = [
            client for client in self.clients.values()
            if tool_name in client.tool_schemas
        ]

        if not available_clients:
            return MCPToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found on any connected server",
                tool_name=tool_name
            )

        # Try each client until one succeeds
        last_error = None
        for client in available_clients:
            result = await client.execute_tool(tool_name, parameters)
            if result.success:
                return result
            last_error = result.error

        return MCPToolResult(
            success=False,
            error=f"All servers failed to execute '{tool_name}': {last_error}",
            tool_name=tool_name
        )

    def get_all_tool_schemas(self) -> List[MCPToolSchema]:
        """Get all available tool schemas."""
        return list(self.tool_schemas.values())

    def get_tool_schemas_for_openai(self) -> List[Dict[str, Any]]:
        """Get all tool schemas in OpenAI function calling format."""
        schemas = []
        seen_names = set()

        for schema in self.tool_schemas.values():
            # Avoid duplicates (prefer server-specific names)
            if schema.name not in seen_names:
                schemas.append(schema.to_openai_format())
                seen_names.add(schema.name)

        return schemas

    def get_server_names(self) -> List[str]:
        """Get list of connected server names."""
        return list(self.clients.keys())

    def get_client(self, server_name: str) -> Optional[MCPClient]:
        """Get client for a specific server."""
        return self.clients.get(server_name)

    def is_connected(self, server_name: str = None) -> bool:
        """Check if servers are connected."""
        if server_name:
            return server_name in self.clients
        return len(self.clients) > 0

    def get_tool_info(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed information about all available tools."""
        info = {}
        for tool_name, schema in self.tool_schemas.items():
            info[tool_name] = {
                "name": schema.name,
                "description": schema.description,
                "parameters": schema.parameters,
                "server_name": schema.server_name,
                "server_url": schema.server_url,
                "last_updated": schema.last_updated,
            }
        return info
