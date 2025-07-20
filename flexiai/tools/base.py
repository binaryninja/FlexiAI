"""
Base tool framework for FlexiAI assistant models.

This module provides the foundation for creating modular, reusable tools
that can be shared across different AI assistant implementations.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union, Callable, Awaitable
from inspect import signature, Parameter

logger = logging.getLogger(__name__)


class ParameterType(Enum):
    """Supported parameter types for tools."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ToolParameter:
    """Represents a tool parameter with validation rules."""
    name: str
    param_type: ParameterType
    description: str
    required: bool = True
    default: Any = None
    enum_values: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None

    def validate(self, value: Any) -> Any:
        """Validate parameter value against rules."""
        if value is None:
            if self.required:
                raise ToolValidationError(f"Required parameter '{self.name}' is missing")
            return self.default

        # Type validation
        if self.param_type == ParameterType.STRING:
            if not isinstance(value, str):
                raise ToolValidationError(f"Parameter '{self.name}' must be a string")
            if self.min_length and len(value) < self.min_length:
                raise ToolValidationError(f"Parameter '{self.name}' must be at least {self.min_length} characters")
            if self.max_length and len(value) > self.max_length:
                raise ToolValidationError(f"Parameter '{self.name}' must be at most {self.max_length} characters")

        elif self.param_type == ParameterType.INTEGER:
            if not isinstance(value, int):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    raise ToolValidationError(f"Parameter '{self.name}' must be an integer")
            if self.min_value is not None and value < self.min_value:
                raise ToolValidationError(f"Parameter '{self.name}' must be at least {self.min_value}")
            if self.max_value is not None and value > self.max_value:
                raise ToolValidationError(f"Parameter '{self.name}' must be at most {self.max_value}")

        elif self.param_type == ParameterType.FLOAT:
            if not isinstance(value, (int, float)):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    raise ToolValidationError(f"Parameter '{self.name}' must be a number")
            if self.min_value is not None and value < self.min_value:
                raise ToolValidationError(f"Parameter '{self.name}' must be at least {self.min_value}")
            if self.max_value is not None and value > self.max_value:
                raise ToolValidationError(f"Parameter '{self.name}' must be at most {self.max_value}")

        elif self.param_type == ParameterType.BOOLEAN:
            if not isinstance(value, bool):
                if isinstance(value, str):
                    value = value.lower() in ('true', '1', 'yes', 'on')
                else:
                    value = bool(value)

        elif self.param_type == ParameterType.ARRAY:
            if not isinstance(value, (list, tuple)):
                raise ToolValidationError(f"Parameter '{self.name}' must be an array")

        elif self.param_type == ParameterType.OBJECT:
            if not isinstance(value, dict):
                raise ToolValidationError(f"Parameter '{self.name}' must be an object")

        # Enum validation
        if self.enum_values and value not in self.enum_values:
            raise ToolValidationError(f"Parameter '{self.name}' must be one of: {self.enum_values}")

        return value


@dataclass
class ToolResult:
    """Represents the result of a tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "execution_time_ms": self.execution_time_ms
        }

    def to_json(self) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class ToolError(Exception):
    """Base exception for tool-related errors."""
    pass


class ToolValidationError(ToolError):
    """Raised when tool parameter validation fails."""
    pass


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""
    pass


class Tool(ABC):
    """
    Base class for all FlexiAI tools.

    Tools are modular components that can be used by AI assistants to
    perform specific tasks like getting weather information, searching
    the web, performing calculations, etc.
    """

    def __init__(self):
        """Initialize the tool."""
        self._validate_tool_definition()

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the tool name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of what the tool does."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        """Return the list of parameters this tool accepts."""
        pass

    @property
    def version(self) -> str:
        """Return the tool version."""
        return "1.0.0"

    @property
    def category(self) -> str:
        """Return the tool category (e.g., 'utility', 'web', 'data')."""
        return "general"

    @property
    def requires_auth(self) -> bool:
        """Return True if the tool requires authentication."""
        return False

    @property
    def is_async(self) -> bool:
        """Return True if the tool supports async execution."""
        return False

    def _validate_tool_definition(self):
        """Validate that the tool is properly defined."""
        if not self.name or not isinstance(self.name, str):
            raise ToolError("Tool name must be a non-empty string")

        if not self.description or not isinstance(self.description, str):
            raise ToolError("Tool description must be a non-empty string")

        if not isinstance(self.parameters, list):
            raise ToolError("Tool parameters must be a list")

        # Validate parameter names are unique
        param_names = [param.name for param in self.parameters]
        if len(param_names) != len(set(param_names)):
            raise ToolError("Tool parameter names must be unique")

    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize parameters.

        Args:
            params: Dictionary of parameter values

        Returns:
            Dictionary of validated and normalized parameters

        Raises:
            ToolValidationError: If validation fails
        """
        validated = {}

        for param in self.parameters:
            value = params.get(param.name)
            validated[param.name] = param.validate(value)

        # Check for unknown parameters
        known_params = {param.name for param in self.parameters}
        unknown_params = set(params.keys()) - known_params
        if unknown_params:
            logger.warning(f"Tool {self.name} received unknown parameters: {unknown_params}")

        return validated

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with the given parameters.

        Args:
            **kwargs: Tool parameters

        Returns:
            ToolResult containing the execution result

        Raises:
            ToolExecutionError: If execution fails
        """
        pass

    async def execute_async(self, **kwargs) -> ToolResult:
        """
        Async version of execute. Override this for true async tools.

        Args:
            **kwargs: Tool parameters

        Returns:
            ToolResult containing the execution result
        """
        if self.is_async:
            raise NotImplementedError("Async tools must implement execute_async")

        # Run sync execute in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute, **kwargs)

    def get_schema(self) -> Dict[str, Any]:
        """
        Get the tool schema for function calling APIs.

        Returns:
            Dictionary containing the tool schema
        """
        properties = {}
        required = []

        for param in self.parameters:
            prop = {
                "type": param.param_type.value,
                "description": param.description
            }

            if param.enum_values:
                prop["enum"] = param.enum_values

            if param.param_type in [ParameterType.INTEGER, ParameterType.FLOAT]:
                if param.min_value is not None:
                    prop["minimum"] = param.min_value
                if param.max_value is not None:
                    prop["maximum"] = param.max_value

            if param.param_type == ParameterType.STRING:
                if param.min_length is not None:
                    prop["minLength"] = param.min_length
                if param.max_length is not None:
                    prop["maxLength"] = param.max_length
                if param.pattern:
                    prop["pattern"] = param.pattern

            if param.default is not None:
                prop["default"] = param.default

            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    def __call__(self, **kwargs) -> ToolResult:
        """Make the tool callable directly."""
        return self.execute(**kwargs)

    def __str__(self) -> str:
        """String representation of the tool."""
        return f"Tool({self.name})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Tool(name='{self.name}', version='{self.version}', category='{self.category}')"


class ToolManager:
    """
    Manages a collection of tools for an AI assistant.

    Provides functionality for:
    - Registering and discovering tools
    - Executing tools with parameter validation
    - Managing tool schemas for function calling APIs
    """

    def __init__(self):
        """Initialize the tool manager."""
        self._tools: Dict[str, Tool] = {}
        self._tool_schemas: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool.

        Args:
            tool: Tool instance to register

        Raises:
            ToolError: If tool registration fails
        """
        if not isinstance(tool, Tool):
            raise ToolError("Only Tool instances can be registered")

        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' is already registered, replacing...")

        self._tools[tool.name] = tool
        self._tool_schemas[tool.name] = tool.get_schema()

        logger.info(f"Registered tool: {tool.name} v{tool.version}")

    def unregister_tool(self, tool_name: str) -> None:
        """
        Unregister a tool.

        Args:
            tool_name: Name of the tool to unregister
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            del self._tool_schemas[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")
        else:
            logger.warning(f"Tool '{tool_name}' not found for unregistration")

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """
        Get a tool by name.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """
        Get list of registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def get_tools_by_category(self, category: str) -> List[Tool]:
        """
        Get tools by category.

        Args:
            category: Tool category

        Returns:
            List of tools in the category
        """
        return [tool for tool in self._tools.values() if tool.category == category]

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get all tool schemas for function calling APIs.

        Returns:
            List of tool schemas
        """
        return list(self._tool_schemas.values())

    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a tool with parameters.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters

        Returns:
            ToolResult containing the execution result

        Raises:
            ToolError: If tool is not found
            ToolValidationError: If parameter validation fails
            ToolExecutionError: If tool execution fails
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ToolError(f"Tool '{tool_name}' not found")

        start_time = datetime.now()

        try:
            # Validate parameters
            validated_params = tool.validate_parameters(kwargs)

            # Execute tool
            result = tool.execute(**validated_params)

            # Add execution timing
            end_time = datetime.now()
            result.execution_time_ms = (end_time - start_time).total_seconds() * 1000

            return result

        except (ToolValidationError, ToolExecutionError):
            raise
        except Exception as e:
            logger.exception(f"Unexpected error executing tool '{tool_name}'")
            raise ToolExecutionError(f"Tool execution failed: {str(e)}")

    async def execute_tool_async(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a tool asynchronously.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters

        Returns:
            ToolResult containing the execution result
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ToolError(f"Tool '{tool_name}' not found")

        start_time = datetime.now()

        try:
            # Validate parameters
            validated_params = tool.validate_parameters(kwargs)

            # Execute tool
            result = await tool.execute_async(**validated_params)

            # Add execution timing
            end_time = datetime.now()
            result.execution_time_ms = (end_time - start_time).total_seconds() * 1000

            return result

        except (ToolValidationError, ToolExecutionError):
            raise
        except Exception as e:
            logger.exception(f"Unexpected error executing tool '{tool_name}' async")
            raise ToolExecutionError(f"Tool execution failed: {str(e)}")

    def __len__(self) -> int:
        """Return number of registered tools."""
        return len(self._tools)

    def __contains__(self, tool_name: str) -> bool:
        """Check if a tool is registered."""
        return tool_name in self._tools

    def __iter__(self):
        """Iterate over registered tools."""
        return iter(self._tools.values())
