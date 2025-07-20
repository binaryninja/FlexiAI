"""
Model Context Protocol (MCP) integration for FlexiAI.

This module provides MCP client capabilities to discover and use tools
from MCP servers, enabling dynamic tool discovery and execution.
"""

from .client import MCPClient, MCPClientManager
from .config import MCPServerConfig, MCPConfig
from .integration import MCPToolIntegration
from .exceptions import MCPError, MCPConnectionError, MCPToolError

__all__ = [
    "MCPClient",
    "MCPClientManager",
    "MCPServerConfig",
    "MCPConfig",
    "MCPToolIntegration",
    "MCPError",
    "MCPConnectionError",
    "MCPToolError",
]
