# Function Calling with Voxtral

This document describes the function calling capabilities implemented in FlexiAI's VoxtralAssistantModel.

## Overview

Function calling allows the Voxtral model to interact with external tools and APIs by calling predefined functions based on audio input. This enables the AI assistant to provide real-time information, perform actions, and access data beyond its training knowledge.

## Features

- 🎯 **Audio-triggered function calls**: Functions are called based on spoken requests
- 🔧 **Built-in functions**: Pre-configured functions like weather queries
- 🛠️ **Custom function registration**: Add your own functions easily
- 📊 **Detailed latency tracking**: Monitor performance of function calls
- 🔄 **Multi-step conversations**: Functions can be part of longer conversations

## How It Works

The function calling process follows these steps:

1. **Audio Input**: User provides audio containing a request
2. **Model Processing**: Voxtral processes the audio and determines if a function should be called
3. **Function Execution**: The appropriate function is called with extracted parameters
4. **Response Generation**: A final response is generated using the function result

## Quick Start

### Basic Usage

```python
from flexiai.models.voxtral_model import VoxtralAssistantModel

# Initialize model
model = VoxtralAssistantModel("mistralai/Voxtral-Mini-3B-2507", "cuda")
model.load()

# Define tools (functions available to the model)
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather information for a specific location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and country/province"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

# Generate response with function calling
response = model.generate_response(
    audio_data="path/to/weather_question.wav",
    tools=tools
)
```

### Custom Function Registration

```python
import json

def get_stock_price(symbol: str) -> str:
    """Get stock price for a symbol (mock implementation)."""
    # In reality, this would call a financial API
    mock_data = {
        "symbol": symbol,
        "price": "$150.25",
        "change": "+2.3%",
        "volume": "1.2M"
    }
    return json.dumps(mock_data)

# Register the custom function
model.register_function(
    name="get_stock_price",
    func=get_stock_price,
    description="Get current stock price information",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "Stock ticker symbol (e.g., AAPL, TSLA)"
            }
        },
        "required": ["symbol"]
    }
)
```

## Built-in Functions

### Weather Function

The model comes with a built-in weather function for testing:

- **Function Name**: `get_weather`
- **Purpose**: Returns weather information for a specified location
- **Parameters**: `location` (string) - City and country/province
- **Returns**: JSON string with weather data

**Example Response**:
```json
{
  "location": "Oakville, Ontario",
  "temperature": "22°C",
  "condition": "Partly cloudy",
  "humidity": "65%",
  "wind": "15 km/h NW",
  "forecast": "Sunny periods with a chance of afternoon showers"
}
```

## Function Definition Format

Functions must be defined using the OpenAI function calling format:

```python
{
    "type": "function",
    "function": {
        "name": "function_name",
        "description": "Clear description of what the function does",
        "parameters": {
            "type": "object",
            "properties": {
                "param_name": {
                    "type": "string|number|boolean|array|object",
                    "description": "Parameter description"
                }
            },
            "required": ["param_name"]
        }
    }
}
```

## API Reference

### VoxtralAssistantModel Methods

#### `generate_response()`

Generate a response from audio input with optional function calling.

**Parameters**:
- `audio_data` (str|np.ndarray): Audio file path or numpy array
- `prompt` (str, optional): Text prompt to guide response
- `tools` (List[Dict], optional): List of available functions
- `measure_latency` (bool): Enable detailed timing measurements
- `**kwargs`: Additional generation parameters

**Returns**: Generated response string

#### `register_function()`

Register a custom function for the model to use.

**Parameters**:
- `name` (str): Function name
- `func` (Callable): The function to register
- `description` (str): Function description
- `parameters` (Dict): JSON schema for function parameters

#### `get_model_info()`

Get information about the loaded model including available functions.

**Returns**: Dictionary with model information

## Examples

### Example 1: Weather Query

```python
# Audio input: "What's the weather like in Toronto?"
response = model.generate_response(
    audio_data="weather_question.wav",
    tools=weather_tools
)
# Output: "The weather in Toronto is currently 18°C and partly cloudy..."
```

### Example 2: Multiple Functions

```python
tools = [
    weather_tool,
    stock_tool,
    news_tool
]

response = model.generate_response(
    audio_data="multi_query.wav",
    tools=tools
)
```

### Example 3: Without Function Calling

```python
# Disable function calling by not providing tools
response = model.generate_response(
    audio_data="question.wav",
    tools=None  # No function calling
)
```

## Best Practices

### Function Design

1. **Clear Descriptions**: Provide detailed function and parameter descriptions
2. **Type Safety**: Use proper type annotations and validation
3. **Error Handling**: Handle errors gracefully and return meaningful messages
4. **Performance**: Keep functions fast to minimize response latency

### Security Considerations

1. **Input Validation**: Always validate function parameters
2. **API Keys**: Store API keys securely, never hardcode them
3. **Rate Limiting**: Implement rate limiting for external API calls
4. **Permissions**: Only expose functions that are safe to call

### Performance Tips

1. **Latency Monitoring**: Use `measure_latency=True` to track performance
2. **Function Caching**: Cache function results when appropriate
3. **Async Functions**: Consider async implementations for I/O operations
4. **Batch Operations**: Combine multiple related calls when possible

## Testing

### Running Tests

```bash
# Run the comprehensive test suite
python tests/test_voxtral_function_calling.py

# Run the simple demo
python tests/demo_function_calling.py

# Run the detailed example
python examples/function_calling_example.py
```

### Mock Audio Creation

For testing, you can create mock audio files:

```python
import numpy as np
import wave
import tempfile

def create_mock_audio(duration=2, sample_rate=16000):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio = 0.3 * np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
    audio = (audio * 32767).astype(np.int16)
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_file.close()
    
    with wave.open(temp_file.name, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())
    
    return temp_file.name
```

## Troubleshooting

### Common Issues

1. **Function Not Called**: 
   - Check function description clarity
   - Verify tool format matches OpenAI specification
   - Ensure audio input is clear about the intent

2. **Parameter Extraction Failed**:
   - Improve parameter descriptions
   - Use more specific parameter names
   - Add example values in descriptions

3. **Function Execution Errors**:
   - Add proper error handling in functions
   - Validate input parameters
   - Return meaningful error messages

### Debug Mode

Enable debug output to see function calling details:

```python
from flexiai.utils import debug_print

# Debug output will show:
# - Function call detection
# - Parameter extraction
# - Function execution results
# - Latency breakdowns
```

## Limitations

- Function calling detection relies on model interpretation of audio
- Complex function calls may require clearer audio input
- Function execution adds latency to response generation
- Mock audio testing doesn't reflect real speech recognition accuracy

## Future Enhancements

- [ ] Parallel function calling support
- [ ] Function call confidence scoring
- [ ] Advanced parameter extraction
- [ ] Function call history and context
- [ ] Streaming function results
- [ ] Integration with external function registries

## Support

For issues or questions about function calling:

1. Check the troubleshooting section above
2. Review the examples in the `examples/` directory
3. Run the test scripts to verify your setup
4. Open an issue with detailed error information