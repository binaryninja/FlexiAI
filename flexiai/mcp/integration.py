"""
MCP (Model Context Protocol) integration with FlexiAI tool system.

This module provides integration between MCP servers and the FlexiAI tool registry,
allowing dynamic tool discovery and execution through a unified interface.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass
import inspect

from ..tools.base import Tool, ToolResult, ToolParameter, ParameterType
from ..tools.registry import ToolRegistry, tool_registry
from .client import MCPClientManager, MCPToolResult, MCPToolSchema
from .config import MCPConfig, load_mcp_config
from .exceptions import MCPError, MCPConnectionError, MCPToolError

logger = logging.getLogger(__name__)


class MCPToolWrapper(Tool):
    """Wrapper to make MCP tools compatible with FlexiAI Tool interface."""

    def __init__(self, mcp_schema: MCPToolSchema, client_manager: MCPClientManager):
        self.mcp_schema = mcp_schema
        self.client_manager = client_manager
        self._parameters = None

        # Initialize base Tool with MCP schema information
        super().__init__()

    @property
    def name(self) -> str:
        return self.mcp_schema.name

    @property
    def description(self) -> str:
        return self.mcp_schema.description

    @property
    def version(self) -> str:
        return "1.0.0"  # MCP tools don't have versions

    @property
    def category(self) -> str:
        return "mcp"  # All MCP tools go in mcp category

    @property
    def requires_auth(self) -> bool:
        return False  # Auth is handled at MCP client level

    @property
    def is_async(self) -> bool:
        return True  # All MCP tools are async

    @property
    def parameters(self) -> List[ToolParameter]:
        if self._parameters is None:
            self._parameters = self._extract_parameters()
        return self._parameters

    def _extract_parameters(self) -> List[ToolParameter]:
        """Extract ToolParameter objects from MCP schema."""
        parameters = []

        if not isinstance(self.mcp_schema.parameters, dict):
            return parameters

        properties = self.mcp_schema.parameters.get("properties", {})
        required = self.mcp_schema.parameters.get("required", [])

        for param_name, param_info in properties.items():
            if not isinstance(param_info, dict):
                continue

            param_type = self._map_json_type_to_parameter_type(param_info.get("type", "string"))

            parameter = ToolParameter(
                name=param_name,
                param_type=param_type,
                description=param_info.get("description", ""),
                required=param_name in required,
                default=param_info.get("default")
            )
            parameters.append(parameter)

        return parameters

    def _map_json_type_to_parameter_type(self, json_type: str) -> ParameterType:
        """Map JSON schema types to ToolParameter types."""
        mapping = {
            "string": ParameterType.STRING,
            "integer": ParameterType.INTEGER,
            "number": ParameterType.FLOAT,
            "boolean": ParameterType.BOOLEAN,
            "array": ParameterType.ARRAY,
            "object": ParameterType.OBJECT,
        }
        return mapping.get(json_type, ParameterType.STRING)

    async def execute_async(self, **kwargs) -> ToolResult:
        """Execute the MCP tool asynchronously."""
        try:
            # Execute through MCP client manager
            mcp_result = await self.client_manager.execute_tool(
                self.mcp_schema.name,
                kwargs,
                preferred_server=self.mcp_schema.server_name
            )

            if mcp_result.success:
                return ToolResult(
                    success=True,
                    data=mcp_result.result,
                    execution_time_ms=mcp_result.execution_time * 1000 if mcp_result.execution_time else None
                )
            else:
                return ToolResult(
                    success=False,
                    error=mcp_result.error,
                    execution_time_ms=mcp_result.execution_time * 1000 if mcp_result.execution_time else None
                )

        except Exception as e:
            logger.error(f"MCP tool execution failed for {self.name}: {e}")
            return ToolResult(
                success=False,
                error=f"MCP tool execution failed: {e}"
            )

    def execute(self, **kwargs) -> ToolResult:
        """Synchronous execution wrapper."""
        # Create new event loop if none exists
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, we need to handle this differently
                logger.warning(f"Cannot run async MCP tool {self.name} from sync context in running loop")
                return ToolResult(
                    success=False,
                    error="Cannot execute async MCP tool from sync context"
                )
        except RuntimeError:
            loop = None

        if loop and not loop.is_running():
            return loop.run_until_complete(self.execute_async(**kwargs))
        else:
            # Create new loop for this execution
            new_loop = asyncio.new_event_loop()
            try:
                return new_loop.run_until_complete(self.execute_async(**kwargs))
            finally:
                new_loop.close()


@dataclass
class MCPIntegrationStats:
    """Statistics about MCP integration."""
    connected_servers: int
    total_tools: int
    mcp_tools: int
    builtin_tools: int
    failed_connections: int
    last_discovery: Optional[float] = None


class MCPToolIntegration:
    """Main integration class for MCP tools with FlexiAI."""

    def __init__(self, config_path: Optional[str] = None, tool_registry: Optional[ToolRegistry] = None):
        self.config = load_mcp_config(config_path)
        self.registry = tool_registry or globals()['tool_registry']
        self.client_manager: Optional[MCPClientManager] = None
        self.mcp_tools: Dict[str, MCPToolWrapper] = {}
        self._initialized = False
        self._integration_lock = asyncio.Lock()

    async def initialize(self):
        """Initialize MCP integration."""
        if self._initialized:
            return

        async with self._integration_lock:
            if self._initialized:
                return

            try:
                logger.info("Initializing MCP integration...")

                # Create and connect client manager
                self.client_manager = MCPClientManager(self.config)
                await self.client_manager.connect_all()

                # Register MCP tools with the tool registry
                await self._register_mcp_tools()

                self._initialized = True
                logger.info(f"MCP integration initialized with {len(self.mcp_tools)} tools")

            except Exception as e:
                logger.error(f"Failed to initialize MCP integration: {e}")
                if self.client_manager:
                    await self.client_manager.close_all()
                raise

    async def shutdown(self):
        """Shutdown MCP integration."""
        if not self._initialized:
            return

        async with self._integration_lock:
            if not self._initialized:
                return

            logger.info("Shutting down MCP integration...")

            # Unregister MCP tools
            self._unregister_mcp_tools()

            # Close client manager
            if self.client_manager:
                await self.client_manager.close_all()
                self.client_manager = None

            self._initialized = False
            logger.info("MCP integration shutdown complete")

    async def _register_mcp_tools(self):
        """Register MCP tools with the FlexiAI tool registry."""
        if not self.client_manager:
            return

        # Get all tool schemas from MCP servers
        tool_schemas = self.client_manager.get_all_tool_schemas()

        for schema in tool_schemas:
            try:
                # Create wrapper tool
                wrapper = MCPToolWrapper(schema, self.client_manager)

                # Register with tool registry
                self.registry.register_custom_tool(wrapper)
                self.mcp_tools[schema.name] = wrapper

                logger.debug(f"Registered MCP tool: {schema.name} from {schema.server_name}")

            except Exception as e:
                logger.warning(f"Failed to register MCP tool {schema.name}: {e}")

    def _unregister_mcp_tools(self):
        """Unregister MCP tools from the tool registry."""
        for tool_name in list(self.mcp_tools.keys()):
            try:
                # Remove from registry (assuming registry has a remove method)
                # Note: The current ToolRegistry doesn't have a remove method,
                # so we'll clear our tracking and let GC handle cleanup
                del self.mcp_tools[tool_name]
                logger.debug(f"Unregistered MCP tool: {tool_name}")
            except Exception as e:
                logger.warning(f"Failed to unregister MCP tool {tool_name}: {e}")

    async def refresh_tools(self):
        """Refresh tools from all MCP servers."""
        if not self._initialized or not self.client_manager:
            logger.warning("MCP integration not initialized, cannot refresh tools")
            return

        try:
            logger.info("Refreshing MCP tools...")

            # Unregister existing MCP tools
            self._unregister_mcp_tools()

            # Discover tools again
            await self.client_manager.discover_all_tools(force_refresh=True)

            # Re-register tools
            await self._register_mcp_tools()

            logger.info(f"Tool refresh complete: {len(self.mcp_tools)} MCP tools available")

        except Exception as e:
            logger.error(f"Failed to refresh MCP tools: {e}")

    def get_tools_for_assistant(self, include_builtin: bool = True) -> List[Dict[str, Any]]:
        """
        Get all available tools in OpenAI function calling format.

        Args:
            include_builtin: Whether to include built-in FlexiAI tools

        Returns:
            List of tool schemas in OpenAI format
        """
        tools = []

        # Add MCP tools
        if self.client_manager:
            mcp_schemas = self.client_manager.get_tool_schemas_for_openai()
            tools.extend(mcp_schemas)

        # Add built-in tools
        if include_builtin:
            builtin_schemas = self.registry.get_tool_schemas()

            # Filter out MCP tools to avoid duplicates
            mcp_tool_names = {schema['function']['name'] for schema in tools}
            for schema in builtin_schemas:
                if schema.get('function', {}).get('name') not in mcp_tool_names:
                    tools.append(schema)

        return tools

    async def execute_tool_unified(self, tool_name: str, parameters: Dict[str, Any] = None) -> ToolResult:
        """
        Execute a tool through unified interface (MCP or built-in).

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters

        Returns:
            ToolResult from execution
        """
        parameters = parameters or {}

        # Try MCP tools first if available
        if self._initialized and self.client_manager:
            mcp_result = await self.client_manager.execute_tool(tool_name, parameters)
            if mcp_result.success:
                return ToolResult(
                    success=True,
                    data=mcp_result.result,
                    execution_time_ms=mcp_result.execution_time * 1000 if mcp_result.execution_time else None
                )
            elif not self.config.fallback_to_builtin_tools:
                return ToolResult(
                    success=False,
                    error=mcp_result.error,
                    execution_time_ms=mcp_result.execution_time * 1000 if mcp_result.execution_time else None
                )

        # Fallback to built-in tools
        try:
            return await self.registry.execute_tool_async(tool_name, **parameters)
        except Exception as e:
            # Try sync execution as fallback
            try:
                return self.registry.execute_tool(tool_name, **parameters)
            except Exception as sync_e:
                return ToolResult(
                    success=False,
                    error=f"Tool execution failed: {e} (sync fallback: {sync_e})"
                )

    def get_stats(self) -> MCPIntegrationStats:
        """Get integration statistics."""
        connected_servers = 0
        total_mcp_tools = 0
        failed_connections = 0

        if self.client_manager:
            connected_servers = len(self.client_manager.get_server_names())
            total_mcp_tools = len(self.client_manager.get_all_tool_schemas())
            # Calculate failed connections
            enabled_servers = len(self.config.get_enabled_servers())
            failed_connections = enabled_servers - connected_servers

        builtin_tools = len(self.registry.list_available_tools()) - len(self.mcp_tools)
        total_tools = total_mcp_tools + builtin_tools

        return MCPIntegrationStats(
            connected_servers=connected_servers,
            total_tools=total_tools,
            mcp_tools=total_mcp_tools,
            builtin_tools=builtin_tools,
            failed_connections=failed_connections,
            last_discovery=getattr(self.client_manager, 'last_discovery', None) if self.client_manager else None
        )

    def is_mcp_tool(self, tool_name: str) -> bool:
        """Check if a tool is from MCP."""
        return tool_name in self.mcp_tools

    def get_mcp_servers(self) -> List[str]:
        """Get list of connected MCP server names."""
        if self.client_manager:
            return self.client_manager.get_server_names()
        return []

    def get_server_tools(self, server_name: str) -> List[str]:
        """Get tools available from a specific server."""
        if not self.client_manager:
            return []

        client = self.client_manager.get_client(server_name)
        if client:
            return client.list_tool_names()
        return []

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()


# Global integration instance
_global_integration: Optional[MCPToolIntegration] = None


async def get_mcp_integration(config_path: Optional[str] = None) -> MCPToolIntegration:
    """Get or create global MCP integration instance."""
    global _global_integration

    if _global_integration is None:
        _global_integration = MCPToolIntegration(config_path)
        await _global_integration.initialize()

    return _global_integration


def create_mcp_tool_function(tool_name: str, integration: MCPToolIntegration) -> Callable:
    """
    Create a function that can be called by the voice assistant for MCP tools.

    This is useful for integrating with existing function calling systems.
    """
    async def mcp_tool_function(**kwargs):
        result = await integration.execute_tool_unified(tool_name, kwargs)
        if result.success:
            return result.result
        else:
            raise MCPToolError(f"Tool execution failed: {result.error}", tool_name)

    # Set function metadata for better introspection
    mcp_tool_function.__name__ = tool_name
    mcp_tool_function.__doc__ = f"MCP tool: {tool_name}"

    return mcp_tool_function


# Convenience functions for backward compatibility
async def initialize_mcp(config_path: Optional[str] = None):
    """Initialize global MCP integration."""
    await get_mcp_integration(config_path)


async def get_mcp_tools_for_assistant() -> List[Dict[str, Any]]:
    """Get all MCP tools in OpenAI format for the assistant."""
    integration = await get_mcp_integration()
    return integration.get_tools_for_assistant()


async def execute_mcp_tool(tool_name: str, parameters: Dict[str, Any] = None) -> ToolResult:
    """Execute an MCP tool through the global integration."""
    integration = await get_mcp_integration()
    return await integration.execute_tool_unified(tool_name, parameters)
