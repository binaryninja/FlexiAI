"""
Exception classes for MCP (Model Context Protocol) integration.

This module defines custom exceptions for handling MCP-related errors
including connection issues, tool execution failures, and schema validation errors.
"""


class MCPError(Exception):
    """Base exception for all MCP-related errors."""

    def __init__(self, message: str, server_url: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.server_url = server_url
        self.details = details or {}

    def __str__(self):
        if self.server_url:
            return f"MCP Error [{self.server_url}]: {self.message}"
        return f"MCP Error: {self.message}"


class MCPConnectionError(MCPError):
    """Raised when unable to connect to an MCP server."""

    def __init__(self, message: str, server_url: str = None, status_code: int = None):
        super().__init__(message, server_url)
        self.status_code = status_code

    def __str__(self):
        base_msg = super().__str__()
        if self.status_code:
            return f"{base_msg} (HTTP {self.status_code})"
        return base_msg


class MCPToolError(MCPError):
    """Raised when tool execution fails on an MCP server."""

    def __init__(self, message: str, tool_name: str = None, server_url: str = None,
                 error_code: str = None):
        super().__init__(message, server_url)
        self.tool_name = tool_name
        self.error_code = error_code

    def __str__(self):
        base_msg = super().__str__()
        if self.tool_name:
            return f"{base_msg} (tool: {self.tool_name})"
        return base_msg


class MCPSchemaError(MCPError):
    """Raised when MCP schema validation fails."""

    def __init__(self, message: str, schema_type: str = None, server_url: str = None):
        super().__init__(message, server_url)
        self.schema_type = schema_type

    def __str__(self):
        base_msg = super().__str__()
        if self.schema_type:
            return f"{base_msg} (schema: {self.schema_type})"
        return base_msg


class MCPTimeoutError(MCPError):
    """Raised when MCP operations timeout."""

    def __init__(self, message: str, timeout_seconds: float = None, server_url: str = None):
        super().__init__(message, server_url)
        self.timeout_seconds = timeout_seconds

    def __str__(self):
        base_msg = super().__str__()
        if self.timeout_seconds:
            return f"{base_msg} (timeout: {self.timeout_seconds}s)"
        return base_msg


class MCPAuthenticationError(MCPError):
    """Raised when MCP server authentication fails."""

    def __init__(self, message: str, server_url: str = None, auth_method: str = None):
        super().__init__(message, server_url)
        self.auth_method = auth_method

    def __str__(self):
        base_msg = super().__str__()
        if self.auth_method:
            return f"{base_msg} (auth: {self.auth_method})"
        return base_msg


class MCPServerUnavailableError(MCPConnectionError):
    """Raised when MCP server is temporarily unavailable."""

    def __init__(self, message: str, server_url: str = None, retry_after: int = None):
        super().__init__(message, server_url)
        self.retry_after = retry_after

    def __str__(self):
        base_msg = super().__str__()
        if self.retry_after:
            return f"{base_msg} (retry after: {self.retry_after}s)"
        return base_msg


class MCPConfigurationError(MCPError):
    """Raised when MCP configuration is invalid."""

    def __init__(self, message: str, config_field: str = None):
        super().__init__(message)
        self.config_field = config_field

    def __str__(self):
        base_msg = super().__str__()
        if self.config_field:
            return f"{base_msg} (field: {self.config_field})"
        return base_msg
