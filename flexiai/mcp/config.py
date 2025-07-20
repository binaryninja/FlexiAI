"""
Configuration management for MCP (Model Context Protocol) integration.

This module provides configuration classes for managing MCP server connections,
authentication, and client settings with support for YAML/JSON loading.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urlparse

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .exceptions import MCPConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""

    name: str
    url: str
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    enabled: bool = True

    # Authentication settings
    auth_type: Optional[str] = None  # None, "bearer", "basic", "api_key", "custom"
    auth_token: Optional[str] = None
    auth_username: Optional[str] = None
    auth_password: Optional[str] = None
    auth_headers: Dict[str, str] = field(default_factory=dict)

    # Tool filtering
    allowed_tools: Optional[List[str]] = None  # None means all tools allowed
    blocked_tools: List[str] = field(default_factory=list)

    # Server-specific settings
    use_sse: bool = True  # Server-sent events for streaming
    verify_ssl: bool = True
    custom_headers: Dict[str, str] = field(default_factory=dict)

    # Rate limiting
    rate_limit_requests_per_minute: Optional[int] = None
    rate_limit_burst: Optional[int] = None

    # Health check settings
    health_check_enabled: bool = True
    health_check_interval: float = 60.0
    health_check_timeout: float = 5.0

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self):
        """Validate server configuration."""
        if not self.name:
            raise MCPConfigurationError("Server name cannot be empty", "name")

        if not self.url:
            raise MCPConfigurationError("Server URL cannot be empty", "url")

        # Validate URL format
        try:
            parsed = urlparse(self.url)
            if not parsed.scheme or not parsed.netloc:
                raise MCPConfigurationError(f"Invalid URL format: {self.url}", "url")
        except Exception as e:
            raise MCPConfigurationError(f"Invalid URL: {e}", "url")

        # Validate timeout values
        if self.timeout <= 0:
            raise MCPConfigurationError("Timeout must be positive", "timeout")

        if self.max_retries < 0:
            raise MCPConfigurationError("Max retries cannot be negative", "max_retries")

        if self.retry_delay < 0:
            raise MCPConfigurationError("Retry delay cannot be negative", "retry_delay")

        # Validate authentication
        if self.auth_type:
            if self.auth_type not in ["bearer", "basic", "api_key", "custom"]:
                raise MCPConfigurationError(f"Invalid auth_type: {self.auth_type}", "auth_type")

            if self.auth_type == "bearer" and not self.auth_token:
                raise MCPConfigurationError("Bearer auth requires auth_token", "auth_token")

            if self.auth_type == "basic" and (not self.auth_username or not self.auth_password):
                raise MCPConfigurationError("Basic auth requires username and password", "auth_username")

            if self.auth_type == "api_key" and not self.auth_token:
                raise MCPConfigurationError("API key auth requires auth_token", "auth_token")

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for requests."""
        headers = {}

        if self.auth_type == "bearer" and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        elif self.auth_type == "basic" and self.auth_username and self.auth_password:
            import base64
            credentials = base64.b64encode(f"{self.auth_username}:{self.auth_password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"
        elif self.auth_type == "api_key" and self.auth_token:
            headers["X-API-Key"] = self.auth_token

        # Add custom auth headers
        headers.update(self.auth_headers)

        return headers

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check if a tool is allowed to be used."""
        if tool_name in self.blocked_tools:
            return False

        if self.allowed_tools is None:
            return True

        return tool_name in self.allowed_tools

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "name": self.name,
            "url": self.url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "enabled": self.enabled,
            "auth_type": self.auth_type,
            "auth_token": self.auth_token,
            "auth_username": self.auth_username,
            "auth_password": self.auth_password,
            "auth_headers": self.auth_headers,
            "allowed_tools": self.allowed_tools,
            "blocked_tools": self.blocked_tools,
            "use_sse": self.use_sse,
            "verify_ssl": self.verify_ssl,
            "custom_headers": self.custom_headers,
            "rate_limit_requests_per_minute": self.rate_limit_requests_per_minute,
            "rate_limit_burst": self.rate_limit_burst,
            "health_check_enabled": self.health_check_enabled,
            "health_check_interval": self.health_check_interval,
            "health_check_timeout": self.health_check_timeout,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPServerConfig":
        """Create configuration from dictionary."""
        return cls(**data)


@dataclass
class MCPConfig:
    """Overall MCP client configuration."""

    servers: List[MCPServerConfig] = field(default_factory=list)

    # Global client settings
    default_timeout: float = 30.0
    default_max_retries: int = 3
    default_retry_delay: float = 1.0

    # Tool discovery settings
    auto_discover_tools: bool = True
    tool_discovery_interval: float = 300.0  # 5 minutes
    cache_tool_schemas: bool = True
    schema_cache_ttl: float = 3600.0  # 1 hour

    # Error handling
    fail_on_server_error: bool = False
    fallback_to_builtin_tools: bool = True

    # Logging and debugging
    enable_request_logging: bool = False
    enable_response_logging: bool = False
    log_level: str = "INFO"

    # Performance settings
    concurrent_requests: int = 10
    request_pool_size: int = 100

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self):
        """Validate overall configuration."""
        if self.default_timeout <= 0:
            raise MCPConfigurationError("Default timeout must be positive", "default_timeout")

        if self.default_max_retries < 0:
            raise MCPConfigurationError("Default max retries cannot be negative", "default_max_retries")

        if self.tool_discovery_interval <= 0:
            raise MCPConfigurationError("Tool discovery interval must be positive", "tool_discovery_interval")

        if self.schema_cache_ttl <= 0:
            raise MCPConfigurationError("Schema cache TTL must be positive", "schema_cache_ttl")

        if self.concurrent_requests <= 0:
            raise MCPConfigurationError("Concurrent requests must be positive", "concurrent_requests")

        # Validate server names are unique
        server_names = [server.name for server in self.servers]
        if len(server_names) != len(set(server_names)):
            raise MCPConfigurationError("Server names must be unique", "servers")

    def add_server(self, server_config: MCPServerConfig):
        """Add a server configuration."""
        # Check for duplicate names
        if any(s.name == server_config.name for s in self.servers):
            raise MCPConfigurationError(f"Server with name '{server_config.name}' already exists", "servers")

        self.servers.append(server_config)
        logger.info(f"Added MCP server configuration: {server_config.name}")

    def remove_server(self, server_name: str) -> bool:
        """Remove a server configuration by name."""
        for i, server in enumerate(self.servers):
            if server.name == server_name:
                del self.servers[i]
                logger.info(f"Removed MCP server configuration: {server_name}")
                return True
        return False

    def get_server(self, server_name: str) -> Optional[MCPServerConfig]:
        """Get server configuration by name."""
        for server in self.servers:
            if server.name == server_name:
                return server
        return None

    def get_enabled_servers(self) -> List[MCPServerConfig]:
        """Get list of enabled server configurations."""
        return [server for server in self.servers if server.enabled]

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "servers": [server.to_dict() for server in self.servers],
            "default_timeout": self.default_timeout,
            "default_max_retries": self.default_max_retries,
            "default_retry_delay": self.default_retry_delay,
            "auto_discover_tools": self.auto_discover_tools,
            "tool_discovery_interval": self.tool_discovery_interval,
            "cache_tool_schemas": self.cache_tool_schemas,
            "schema_cache_ttl": self.schema_cache_ttl,
            "fail_on_server_error": self.fail_on_server_error,
            "fallback_to_builtin_tools": self.fallback_to_builtin_tools,
            "enable_request_logging": self.enable_request_logging,
            "enable_response_logging": self.enable_response_logging,
            "log_level": self.log_level,
            "concurrent_requests": self.concurrent_requests,
            "request_pool_size": self.request_pool_size,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPConfig":
        """Create configuration from dictionary."""
        # Extract servers separately
        servers_data = data.pop("servers", [])
        servers = [MCPServerConfig.from_dict(server_data) for server_data in servers_data]

        # Create config with remaining data
        config = cls(servers=servers, **data)
        return config

    def save_to_file(self, file_path: Union[str, Path]):
        """Save configuration to file (YAML or JSON based on extension)."""
        file_path = Path(file_path)
        data = self.to_dict()

        if file_path.suffix.lower() in ['.yml', '.yaml']:
            if not YAML_AVAILABLE:
                raise MCPConfigurationError("PyYAML not available for YAML format")
            with open(file_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
        elif file_path.suffix.lower() == '.json':
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            raise MCPConfigurationError(f"Unsupported file format: {file_path.suffix}")

        logger.info(f"Saved MCP configuration to {file_path}")

    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> "MCPConfig":
        """Load configuration from file."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise MCPConfigurationError(f"Configuration file not found: {file_path}")

        try:
            if file_path.suffix.lower() in ['.yml', '.yaml']:
                if not YAML_AVAILABLE:
                    raise MCPConfigurationError("PyYAML not available for YAML format")
                with open(file_path, 'r') as f:
                    data = yaml.safe_load(f)
            elif file_path.suffix.lower() == '.json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
            else:
                raise MCPConfigurationError(f"Unsupported file format: {file_path.suffix}")

            config = cls.from_dict(data)
            logger.info(f"Loaded MCP configuration from {file_path}")
            return config

        except Exception as e:
            raise MCPConfigurationError(f"Failed to load configuration from {file_path}: {e}")

    @classmethod
    def create_default(cls) -> "MCPConfig":
        """Create default configuration with example servers."""
        config = cls()

        # Add some example server configurations (commented out by default)
        examples = [
            {
                "name": "filesystem",
                "url": "http://localhost:8001",
                "enabled": False,
                "allowed_tools": ["read_file", "write_file", "list_directory"],
            },
            {
                "name": "web_search",
                "url": "http://localhost:8002",
                "enabled": False,
                "allowed_tools": ["search_web", "fetch_url"],
            },
            {
                "name": "calendar",
                "url": "http://localhost:8003",
                "enabled": False,
                "auth_type": "api_key",
                "auth_token": "${CALENDAR_API_KEY}",
            },
        ]

        for example in examples:
            try:
                server_config = MCPServerConfig.from_dict(example)
                config.add_server(server_config)
            except Exception as e:
                logger.warning(f"Failed to add example server {example.get('name', 'unknown')}: {e}")

        return config


def load_mcp_config(config_path: Optional[Union[str, Path]] = None) -> MCPConfig:
    """
    Load MCP configuration from file or create default.

    Args:
        config_path: Path to configuration file. If None, searches for default locations.

    Returns:
        MCPConfig instance
    """
    if config_path:
        return MCPConfig.load_from_file(config_path)

    # Search for configuration in default locations
    default_paths = [
        "mcp_config.yaml",
        "mcp_config.yml",
        "mcp_config.json",
        "config/mcp.yaml",
        "config/mcp.yml",
        "config/mcp.json",
        os.path.expanduser("~/.flexiai/mcp_config.yaml"),
        os.path.expanduser("~/.flexiai/mcp_config.yml"),
        os.path.expanduser("~/.flexiai/mcp_config.json"),
    ]

    for path in default_paths:
        if os.path.exists(path):
            logger.info(f"Found MCP configuration at {path}")
            return MCPConfig.load_from_file(path)

    logger.info("No MCP configuration file found, using default configuration")
    return MCPConfig.create_default()


def create_example_config_file(file_path: Union[str, Path] = "mcp_config.yaml"):
    """Create an example MCP configuration file."""
    config = MCPConfig.create_default()
    config.save_to_file(file_path)
    print(f"Created example MCP configuration at {file_path}")
    print("Edit this file to configure your MCP servers.")


if __name__ == "__main__":
    # Create example configuration when run as script
    create_example_config_file()
