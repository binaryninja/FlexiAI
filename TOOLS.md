# 🔧 FlexiAI Modular Tool System

A powerful, extensible tool system for AI assistants that provides modular, reusable components for enhanced functionality.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Built-in Tools](#built-in-tools)
- [Creating Custom Tools](#creating-custom-tools)
- [Integration with Assistant Models](#integration-with-assistant-models)
- [Parameter Validation](#parameter-validation)
- [Error Handling](#error-handling)
- [Function Calling API](#function-calling-api)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The FlexiAI modular tool system provides a framework for creating and managing reusable tools that can be shared across different AI assistant models. Tools are self-contained components that perform specific tasks like getting weather information, analyzing text, performing calculations, or integrating with external APIs.

### Key Features

- **🔄 Modular Design**: Tools are independent, reusable components
- **🔍 Automatic Discovery**: Built-in tools are automatically registered
- **✅ Parameter Validation**: Robust type checking and validation
- **📋 Schema Generation**: Compatible with OpenAI function calling APIs
- **🛡️ Error Handling**: Comprehensive error management
- **🏷️ Categorization**: Tools can be organized by category
- **🔐 Authentication**: Support for API keys and authentication
- **⚡ Async Support**: Both synchronous and asynchronous execution
- **🧪 Extensible**: Easy to create and register custom tools

## Architecture

```
FlexiAI/
├── flexiai/
│   ├── tools/
│   │   ├── __init__.py          # Tool system exports
│   │   ├── base.py              # Base tool framework
│   │   ├── registry.py          # Tool registration and discovery
│   │   ├── weather.py           # Weather tool implementation
│   │   └── ...                  # Additional tools
│   ├── models/
│   │   └── voxtral_model.py     # Updated to use tool system
│   └── config/
│       └── api_keys.py          # Secure API key management
```

### Core Components

1. **Tool Base Class**: Abstract base for all tools with validation and execution
2. **Tool Manager**: Manages tool instances and execution
3. **Tool Registry**: Automatic discovery and registration of tools
4. **Parameter System**: Type-safe parameter definition and validation
5. **Result System**: Structured results with metadata and error handling

## Quick Start

### Using Existing Tools

```python
from flexiai.tools.registry import execute_tool, list_tools

# List available tools
print("Available tools:", list_tools())

# Execute weather tool
result = execute_tool(
    'get_weather',
    location='London',
    include_forecast=True,
    forecast_days=5
)

if result.success:
    print("Weather data:", result.data)
else:
    print("Error:", result.error)
```

### Tool Registry Shortcuts

```python
from flexiai.tools.registry import tool_registry

# Get tool information
tools_info = tool_registry.get_tool_info()

# Get tools by category
weather_tools = tool_registry.get_tools_by_category('information')

# Get tool schemas for function calling
schemas = tool_registry.get_tool_schemas()
```

## Built-in Tools

### Weather Tool (`get_weather`)

Comprehensive weather information using OpenWeatherMap One Call API 3.0.

**Parameters:**
- `location` (required): City name, coordinates, or "City, Country" format
- `include_forecast` (optional): Include hourly/daily forecasts (default: true)
- `include_alerts` (optional): Include weather alerts (default: true)
- `forecast_days` (optional): Number of forecast days 1-8 (default: 5)

**Example:**
```python
result = execute_tool(
    'get_weather',
    location='Tokyo, Japan',
    include_forecast=True,
    forecast_days=3
)
```

**Output Structure:**
```json
{
  "location": "Tokyo, JP",
  "current": {
    "temperature": "22°C",
    "condition": "Partly Cloudy",
    "humidity": "65%",
    "wind": "12 km/h NW",
    "pressure": "1013 hPa",
    "uv_index": 5.2
  },
  "forecast": {
    "next_24h": [...],
    "daily": [...]
  },
  "alerts": [...],
  "summary": "Currently partly cloudy with temperature 22°C..."
}
```

**Setup:**
1. Get API key from [OpenWeatherMap](https://openweathermap.org/api)
2. Add to `.env`: `OPENWEATHERMAP_API_KEY=your_key_here`
3. For forecasts, subscribe to One Call API 3.0

## Creating Custom Tools

### Basic Tool Structure

```python
from flexiai.tools.base import Tool, ToolParameter, ToolResult, ParameterType

class MyCustomTool(Tool):
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property
    def description(self) -> str:
        return "Description of what this tool does"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="input_text",
                param_type=ParameterType.STRING,
                description="Text to process",
                required=True,
                min_length=1,
                max_length=1000
            ),
            ToolParameter(
                name="option",
                param_type=ParameterType.STRING,
                description="Processing option",
                required=False,
                default="default",
                enum_values=["default", "advanced", "minimal"]
            )
        ]
    
    @property
    def category(self) -> str:
        return "text"
    
    def execute(self, **kwargs) -> ToolResult:
        input_text = kwargs['input_text']
        option = kwargs.get('option', 'default')
        
        # Your tool logic here
        result_data = {
            "processed_text": input_text.upper(),
            "option_used": option,
            "length": len(input_text)
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"processing_option": option}
        )
```

### Parameter Types

| Type | Description | Validation Options |
|------|-------------|-------------------|
| `STRING` | Text input | `min_length`, `max_length`, `pattern` |
| `INTEGER` | Whole numbers | `min_value`, `max_value` |
| `FLOAT` | Decimal numbers | `min_value`, `max_value` |
| `BOOLEAN` | True/false values | Auto-converts strings |
| `ARRAY` | Lists of values | Element validation |
| `OBJECT` | Dictionary/JSON objects | Structure validation |

### Advanced Tool Features

```python
class AdvancedTool(Tool):
    @property
    def requires_auth(self) -> bool:
        return True  # Tool needs API keys
    
    @property
    def is_async(self) -> bool:
        return True  # Tool supports async execution
    
    @property
    def version(self) -> str:
        return "2.1.0"
    
    async def execute_async(self, **kwargs) -> ToolResult:
        # Async implementation
        await some_async_operation()
        return ToolResult(success=True, data=result)
```

### Registering Custom Tools

```python
from flexiai.tools.registry import tool_registry

# Create and register
my_tool = MyCustomTool()
tool_registry.register_custom_tool(my_tool)

# Tool is now available
result = execute_tool('my_tool', input_text="Hello World")
```

## Integration with Assistant Models

The tool system automatically integrates with assistant models:

```python
from flexiai.models.voxtral_model import VoxtralAssistantModel

# Create model - tools are automatically available
model = VoxtralAssistantModel("mistralai/Voxtral-Mini-3B-2507", "cpu")

# Tools are registered as available functions
print("Available functions:", list(model.available_functions.keys()))

# Tools can be called directly through the model
weather_result = model.available_functions['get_weather'](location='Paris')
```

### Function Calling Integration

```python
# Get schemas for OpenAI function calling
schemas = tool_registry.get_tool_schemas()

# Use with OpenAI API
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What's the weather in London?"}],
    functions=schemas
)
```

## Parameter Validation

The tool system provides comprehensive parameter validation:

### Validation Rules

```python
ToolParameter(
    name="temperature",
    param_type=ParameterType.FLOAT,
    description="Temperature value",
    required=True,
    min_value=-100.0,
    max_value=100.0
)

ToolParameter(
    name="city",
    param_type=ParameterType.STRING,
    description="City name",
    required=True,
    min_length=2,
    max_length=50,
    pattern=r"^[a-zA-Z\s-]+$"  # Letters, spaces, hyphens only
)

ToolParameter(
    name="mode",
    param_type=ParameterType.STRING,
    description="Processing mode",
    required=False,
    default="standard",
    enum_values=["standard", "detailed", "minimal"]
)
```

### Automatic Type Conversion

```python
# String numbers are automatically converted
execute_tool('my_tool', count="42")  # "42" -> 42

# Boolean strings are converted
execute_tool('my_tool', enabled="true")  # "true" -> True
```

## Error Handling

### Tool Result Structure

```python
@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time_ms: Optional[float] = None
```

### Error Types

- **ToolError**: Base exception for tool-related errors
- **ToolValidationError**: Parameter validation failures
- **ToolExecutionError**: Runtime execution errors

### Handling Errors

```python
try:
    result = execute_tool('get_weather', location='InvalidLocation')
    
    if result.success:
        print("Success:", result.data)
    else:
        print("Tool error:", result.error)
        print("Metadata:", result.metadata)
        
except ToolValidationError as e:
    print("Validation error:", e)
except ToolExecutionError as e:
    print("Execution error:", e)
```

## Function Calling API

### OpenAI Integration

```python
import openai
from flexiai.tools.registry import tool_registry

# Get tool schemas
tools = tool_registry.get_tool_schemas()

# Create chat completion with function calling
response = openai.ChatCompletion.create(
    model="gpt-4-1106-preview",
    messages=[
        {"role": "user", "content": "What's the weather like in Tokyo?"}
    ],
    tools=tools,
    tool_choice="auto"
)

# Handle function calls
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        # Execute the tool
        result = execute_tool(function_name, **function_args)
        
        # Send result back to model
        # ... continue conversation
```

### Anthropic Claude Integration

```python
import anthropic
from flexiai.tools.registry import tool_registry

client = anthropic.Anthropic()

# Convert schemas to Anthropic format
tools = []
for schema in tool_registry.get_tool_schemas():
    tools.append({
        "name": schema["function"]["name"],
        "description": schema["function"]["description"],
        "input_schema": schema["function"]["parameters"]
    })

# Use with Claude
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    tools=tools,
    messages=[
        {"role": "user", "content": "What's the weather in London?"}
    ]
)
```

## API Reference

### Tool Registry

```python
from flexiai.tools.registry import tool_registry

# Core methods
tool_registry.register_custom_tool(tool)
tool_registry.get_tool(name)
tool_registry.list_available_tools()
tool_registry.execute_tool(name, **kwargs)
tool_registry.get_tool_schemas()
tool_registry.get_tool_info()

# Convenience functions
from flexiai.tools.registry import get_tool, list_tools, execute_tool
```

### Tool Base Class

```python
class Tool(ABC):
    # Required properties
    @property
    @abstractmethod
    def name(self) -> str: pass
    
    @property
    @abstractmethod
    def description(self) -> str: pass
    
    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]: pass
    
    # Optional properties
    @property
    def version(self) -> str: return "1.0.0"
    
    @property
    def category(self) -> str: return "general"
    
    @property
    def requires_auth(self) -> bool: return False
    
    @property
    def is_async(self) -> bool: return False
    
    # Execution methods
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult: pass
    
    async def execute_async(self, **kwargs) -> ToolResult: pass
```

### Parameter Definition

```python
ToolParameter(
    name: str,                    # Parameter name
    param_type: ParameterType,    # Parameter type
    description: str,             # Human-readable description
    required: bool = True,        # Whether parameter is required
    default: Any = None,          # Default value if not required
    enum_values: List[Any] = None,# Allowed values
    min_value: Union[int, float] = None,  # Minimum numeric value
    max_value: Union[int, float] = None,  # Maximum numeric value
    min_length: int = None,       # Minimum string length
    max_length: int = None,       # Maximum string length
    pattern: str = None           # Regex pattern for strings
)
```

## Examples

### Example 1: Text Processing Tool

```python
class TextProcessorTool(Tool):
    @property
    def name(self) -> str:
        return "process_text"
    
    @property
    def description(self) -> str:
        return "Process text with various transformations"
    
    @property
    def parameters(self):
        return [
            ToolParameter(
                name="text",
                param_type=ParameterType.STRING,
                description="Text to process",
                required=True
            ),
            ToolParameter(
                name="operation",
                param_type=ParameterType.STRING,
                description="Operation to perform",
                required=True,
                enum_values=["uppercase", "lowercase", "reverse", "word_count"]
            )
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        text = kwargs['text']
        operation = kwargs['operation']
        
        if operation == "uppercase":
            result = text.upper()
        elif operation == "lowercase":
            result = text.lower()
        elif operation == "reverse":
            result = text[::-1]
        elif operation == "word_count":
            result = len(text.split())
        
        return ToolResult(
            success=True,
            data={"original": text, "result": result, "operation": operation}
        )

# Register and use
tool = TextProcessorTool()
tool_registry.register_custom_tool(tool)

result = execute_tool('process_text', text="Hello World", operation="uppercase")
print(result.data)  # {"original": "Hello World", "result": "HELLO WORLD", "operation": "uppercase"}
```

### Example 2: API Integration Tool

```python
class NewsSearchTool(Tool):
    @property
    def name(self) -> str:
        return "search_news"
    
    @property
    def description(self) -> str:
        return "Search for news articles on specific topics"
    
    @property
    def parameters(self):
        return [
            ToolParameter(
                name="query",
                param_type=ParameterType.STRING,
                description="Search query for news articles",
                required=True,
                min_length=1,
                max_length=100
            ),
            ToolParameter(
                name="limit",
                param_type=ParameterType.INTEGER,
                description="Maximum number of articles to return",
                required=False,
                default=5,
                min_value=1,
                max_value=20
            )
        ]
    
    @property
    def requires_auth(self) -> bool:
        return True  # Requires NEWS_API_KEY
    
    def execute(self, **kwargs) -> ToolResult:
        from flexiai.config.api_keys import get_api_key
        import requests
        
        query = kwargs['query']
        limit = kwargs.get('limit', 5)
        
        api_key = get_api_key('NEWS_API_KEY')
        if not api_key:
            return ToolResult(
                success=False,
                error="NEWS_API_KEY not found"
            )
        
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'pageSize': limit,
                'apiKey': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "total_results": data.get('totalResults', 0),
                    "articles": [
                        {
                            "title": article['title'],
                            "description": article['description'],
                            "url": article['url'],
                            "published_at": article['publishedAt']
                        }
                        for article in articles
                    ]
                },
                metadata={"api_version": "newsapi.org"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"News search failed: {str(e)}"
            )
```

### Example 3: Async Tool

```python
import asyncio
import aiohttp

class AsyncWebScrapeTool(Tool):
    @property
    def name(self) -> str:
        return "scrape_webpage"
    
    @property
    def is_async(self) -> bool:
        return True
    
    @property
    def description(self) -> str:
        return "Asynchronously scrape webpage content"
    
    @property
    def parameters(self):
        return [
            ToolParameter(
                name="url",
                param_type=ParameterType.STRING,
                description="URL to scrape",
                required=True
            )
        ]
    
    async def execute_async(self, **kwargs) -> ToolResult:
        url = kwargs['url']
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    content = await response.text()
                    
            return ToolResult(
                success=True,
                data={
                    "url": url,
                    "status_code": response.status,
                    "content_length": len(content),
                    "content_preview": content[:500]
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to scrape {url}: {str(e)}"
            )

# Use async tool
async def main():
    tool = AsyncWebScrapeTool()
    tool_registry.register_custom_tool(tool)
    
    result = await tool_registry.execute_tool_async(
        'scrape_webpage',
        url='https://example.com'
    )
    print(result.data)

asyncio.run(main())
```

## Best Practices

### Tool Design

1. **Single Responsibility**: Each tool should have one clear purpose
2. **Descriptive Names**: Use clear, descriptive names for tools and parameters
3. **Comprehensive Validation**: Define appropriate validation rules for all parameters
4. **Error Handling**: Provide clear error messages and handle edge cases
5. **Documentation**: Include detailed descriptions for tools and parameters

### Parameter Design

```python
# Good: Clear, specific parameters
ToolParameter(
    name="temperature_celsius",
    param_type=ParameterType.FLOAT,
    description="Temperature in Celsius (-273.15 to 100)",
    required=True,
    min_value=-273.15,
    max_value=100.0
)

# Avoid: Vague, unlimited parameters
ToolParameter(
    name="data",
    param_type=ParameterType.STRING,
    description="Some data",
    required=True
)
```

### Error Handling

```python
def execute(self, **kwargs) -> ToolResult:
    try:
        # Tool logic here
        result = process_data(kwargs['input'])
        
        return ToolResult(
            success=True,
            data=result,
            metadata={"processing_time": time.time() - start}
        )
        
    except ValidationError as e:
        return ToolResult(
            success=False,
            error=f"Invalid input: {e}",
            metadata={"error_type": "validation"}
        )
    except APIError as e:
        return ToolResult(
            success=False,
            error=f"API request failed: {e}",
            metadata={"error_type": "api", "retry_possible": True}
        )
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Unexpected error: {e}",
            metadata={"error_type": "unknown"}
        )
```

### Security Considerations

1. **API Keys**: Always use the secure API key management system
2. **Input Validation**: Validate all inputs thoroughly
3. **Output Sanitization**: Sanitize outputs when needed
4. **Rate Limiting**: Implement rate limiting for external API calls
5. **Timeout Handling**: Set appropriate timeouts for network requests

```python
from flexiai.config.api_keys import get_api_key

def execute(self, **kwargs) -> ToolResult:
    # Secure API key handling
    api_key = get_api_key('SERVICE_API_KEY')
    if not api_key:
        return ToolResult(
            success=False,
            error="API key not configured",
            metadata={"setup_help": "Set SERVICE_API_KEY in environment"}
        )
    
    # Input sanitization
    query = kwargs['query'].strip()
    if not query:
        return ToolResult(success=False, error="Empty query not allowed")
    
    # Safe API call with timeout
    try:
        response = requests.get(
            url,
            params={'q': query, 'key': api_key},
            timeout=10
        )
        # Process response...
```

## Troubleshooting

### Common Issues

#### Tool Not Found
```
ToolError: Tool 'my_tool' not found
```
**Solution**: Ensure the tool is registered with `tool_registry.register_custom_tool(tool)`

#### Parameter Validation Errors
```
ToolValidationError: Required parameter 'location' is missing
```
**Solution**: Check parameter names and ensure required parameters are provided

#### API Key Issues
```
OpenWeatherMap API key not found
```
**Solution**: Set API keys in `.env` file or environment variables

#### Import Errors
```
ImportError: cannot import name 'Tool' from 'flexiai.tools.base'
```
**Solution**: Ensure FlexiAI is properly installed and you're running from the correct directory

### Debugging

Enable debug output:
```python
import os
os.environ['FLEXIAI_DEBUG'] = '1'

# Now tool execution will show debug information
result = execute_tool('get_weather', location='London')
```

Check tool registration:
```python
from flexiai.tools.registry import tool_registry

print("Available tools:", tool_registry.list_available_tools())
print("Tool info:", tool_registry.get_tool_info())
```

Validate tool parameters manually:
```python
tool = tool_registry.get_tool('my_tool')
if tool:
    try:
        validated = tool.validate_parameters({'param1': 'value1'})
        print("Parameters valid:", validated)
    except Exception as e:
        print("Validation error:", e)
```

### Performance Optimization

1. **Cache Results**: Cache expensive API calls when appropriate
2. **Async Tools**: Use async execution for I/O-bound operations
3. **Parameter Validation**: Validate early to avoid expensive operations
4. **Timeout Management**: Set appropriate timeouts for external calls
5. **Resource Cleanup**: Clean up resources properly in error cases

```python
class OptimizedTool(Tool):
    def __init__(self):
        super().__init__()
        self._cache = {}
    
    def execute(self, **kwargs) -> ToolResult:
        # Check cache first
        cache_key = json.dumps(kwargs, sort_keys=True)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Expensive operation
        result = expensive_operation(**kwargs)
        
        # Cache result
        self._cache[cache_key] = result
        return result
```

---

## Contributing

To contribute new tools to FlexiAI:

1. Create your tool following the patterns in this documentation
2. Add comprehensive tests
3. Update this documentation
4. Submit a pull request

For questions or support, please open an issue on the FlexiAI repository.

---

**Next Steps:**
- Explore the weather tool implementation for API integration patterns
- Create custom tools for your specific use cases
- Integrate tools with function calling APIs
- Share useful tools with the FlexiAI community