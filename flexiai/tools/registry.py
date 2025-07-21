"""
Tool registry for automatic tool discovery and registration.

This module provides a centralized registry for all available tools
in the FlexiAI system, with automatic discovery and registration.
"""

import logging
from typing import Dict, List, Type, Optional

from .base import Tool, ToolManager

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for FlexiAI tools with automatic discovery.

    The registry automatically discovers and registers available tools,
    providing a centralized way to access and manage tools across
    different assistant models.
    """

    def __init__(self):
        """Initialize the tool registry."""
        self._manager = ToolManager()
        self._tool_classes: Dict[str, Type[Tool]] = {}
        self._auto_discovered = False
        self._mcp_mode = False

    def _auto_discover_tools(self):
        """Automatically discover and register built-in tools."""
        if self._auto_discovered:
            return

        # Skip built-in tools if MCP mode is enabled
        if self._mcp_mode:
            logger.info("MCP mode enabled - skipping built-in tool discovery")
            self._auto_discovered = True
            return

        logger.info("Auto-discovering FlexiAI tools...")

        # Register built-in tools
        builtin_tools = [
            # Add more built-in tools here as they are created
        ]

        registered_count = 0
        for tool_class in builtin_tools:
            try:
                if issubclass(tool_class, Tool):
                    tool_instance = tool_class()
                    self.register_tool_class(tool_class)
                    self.register_tool_instance(tool_instance)
                    registered_count += 1
                    logger.debug(f"Auto-registered tool: {tool_instance.name}")
            except Exception as e:
                logger.warning(f"Failed to auto-register tool {tool_class.__name__}: {e}")

        logger.info(f"Auto-discovered and registered {registered_count} tools")
        self._auto_discovered = True

    def set_mcp_mode(self, enabled: bool):
        """
        Enable or disable MCP mode.

        When MCP mode is enabled, built-in tools are disabled to avoid conflicts.

        Args:
            enabled: Whether to enable MCP mode
        """
        self._mcp_mode = enabled
        if enabled:
            logger.info("MCP mode enabled - built-in tools will be disabled")
        else:
            logger.info("MCP mode disabled - built-in tools will be available")

    def register_tool_class(self, tool_class: Type[Tool]) -> None:
        """
        Register a tool class for lazy instantiation.

        Args:
            tool_class: Tool class to register
        """
        if not issubclass(tool_class, Tool):
            raise ValueError("Tool class must be a subclass of Tool")

        # Get tool name by instantiating temporarily
        temp_instance = tool_class()
        tool_name = temp_instance.name

        self._tool_classes[tool_name] = tool_class
        logger.debug(f"Registered tool class: {tool_name}")

    def register_tool_instance(self, tool: Tool) -> None:
        """
        Register a tool instance.

        Args:
            tool: Tool instance to register
        """
        self._manager.register_tool(tool)

    def register_custom_tool(self, tool: Tool) -> None:
        """
        Register a custom tool (convenience method).

        Args:
            tool: Custom tool instance to register
        """
        self.register_tool_instance(tool)
        logger.info(f"Registered custom tool: {tool.name}")

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """
        Get a tool by name, creating it if needed.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool instance or None if not found
        """
        self._auto_discover_tools()

        # Try to get from manager first
        tool = self._manager.get_tool(tool_name)
        if tool:
            return tool

        # Try to create from registered class
        if tool_name in self._tool_classes:
            tool_class = self._tool_classes[tool_name]
            tool_instance = tool_class()
            self.register_tool_instance(tool_instance)
            return tool_instance

        return None

    def list_available_tools(self) -> List[str]:
        """
        Get list of all available tool names.

        Returns:
            List of tool names
        """
        self._auto_discover_tools()

        # Combine registered instances and classes
        instance_tools = set(self._manager.list_tools())
        class_tools = set(self._tool_classes.keys())

        return sorted(list(instance_tools | class_tools))

    def get_tools_by_category(self, category: str) -> List[Tool]:
        """
        Get tools by category.

        Args:
            category: Tool category

        Returns:
            List of tools in the category
        """
        self._auto_discover_tools()

        tools = []
        for tool_name in self.list_available_tools():
            tool = self.get_tool(tool_name)
            if tool and tool.category == category:
                tools.append(tool)

        return tools

    def get_tool_schemas(self) -> List[Dict]:
        """
        Get schemas for all available tools.

        Returns:
            List of tool schemas for function calling APIs
        """
        self._auto_discover_tools()

        schemas = []
        for tool_name in self.list_available_tools():
            tool = self.get_tool(tool_name)
            if tool:
                schemas.append(tool.get_schema())

        return schemas

    def execute_tool(self, tool_name: str, **kwargs):
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters

        Returns:
            ToolResult containing the execution result
        """
        self._auto_discover_tools()
        return self._manager.execute_tool(tool_name, **kwargs)

    async def execute_tool_async(self, tool_name: str, **kwargs):
        """
        Execute a tool asynchronously.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters

        Returns:
            ToolResult containing the execution result
        """
        self._auto_discover_tools()
        return await self._manager.execute_tool_async(tool_name, **kwargs)

    def get_manager(self) -> ToolManager:
        """
        Get the underlying tool manager.

        Returns:
            ToolManager instance
        """
        self._auto_discover_tools()
        return self._manager

    def clear_registry(self) -> None:
        """Clear all registered tools (useful for testing)."""
        self._manager = ToolManager()
        self._tool_classes.clear()
        self._auto_discovered = False
        logger.info("Tool registry cleared")

    def get_tool_info(self) -> Dict[str, Dict]:
        """
        Get detailed information about all available tools.

        Returns:
            Dictionary with tool information
        """
        self._auto_discover_tools()

        info = {}
        for tool_name in self.list_available_tools():
            tool = self.get_tool(tool_name)
            if tool:
                info[tool_name] = {
                    "name": tool.name,
                    "description": tool.description,
                    "version": tool.version,
                    "category": tool.category,
                    "requires_auth": tool.requires_auth,
                    "is_async": tool.is_async,
                    "parameter_count": len(tool.parameters),
                    "parameters": [
                        {
                            "name": param.name,
                            "type": param.param_type.value,
                            "required": param.required,
                            "description": param.description
                        }
                        for param in tool.parameters
                    ]
                }

        return info

    def __len__(self) -> int:
        """Return number of available tools."""
        return len(self.list_available_tools())

    def __contains__(self, tool_name: str) -> bool:
        """Check if a tool is available."""
        return tool_name in self.list_available_tools()

    def __str__(self) -> str:
        """String representation of the registry."""
        tool_count = len(self)
        return f"ToolRegistry({tool_count} tools available)"


# Global registry instance
tool_registry = ToolRegistry()


def get_tool(tool_name: str) -> Optional[Tool]:
    """
    Convenience function to get a tool from the global registry.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool instance or None if not found
    """
    return tool_registry.get_tool(tool_name)


def list_tools() -> List[str]:
    """
    Convenience function to list all available tools.

    Returns:
        List of tool names
    """
    return tool_registry.list_available_tools()


def execute_tool(tool_name: str, **kwargs):
    """
    Convenience function to execute a tool.

    Args:
        tool_name: Name of the tool to execute
        **kwargs: Tool parameters

    Returns:
        ToolResult containing the execution result
    """
    return tool_registry.execute_tool(tool_name, **kwargs)


def get_tool_schemas() -> List[Dict]:
    """
    Convenience function to get all tool schemas.

    Returns:
        List of tool schemas
    """
    return tool_registry.get_tool_schemas()


def register_custom_tool(tool: Tool) -> None:
    """
    Convenience function to register a custom tool.

    Args:
        tool: Custom tool instance to register
    """
    tool_registry.register_custom_tool(tool)
