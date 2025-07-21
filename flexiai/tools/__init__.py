"""
FlexiAI Tools Module

This module provides a modular tool system for AI assistants. Tools can be
easily created, registered, and used across different assistant models.

The tool system supports:
- Function calling with parameter validation
- Asynchronous and synchronous execution
- Tool discovery and registration
- Parameter schemas and descriptions
- Error handling and logging
"""

from .base import (
    Tool,
    ToolParameter,
    ToolResult,
    ToolManager,
    ToolError,
    ToolValidationError
)

from .registry import tool_registry

__all__ = [
    'Tool',
    'ToolParameter',
    'ToolResult',
    'ToolManager',
    'ToolError',
    'ToolValidationError',
    'tool_registry'
]

# Version info
__version__ = '1.0.0'
