# Function Calling with Voxtral

This document provides a quick guide to using function calling with the Voxtral model in FlexiAI.

## Overview

Function calling allows the Voxtral model (`mistralai/Voxtral-Mini-3B-2507`) to execute external functions based on audio input. This enables the AI to provide real-time information like weather data, stock prices, or any custom functionality you define.

## Quick Example

```python
from flexiai.models.voxtral_model import VoxtralAssistantModel

# Initialize model
model = VoxtralAssistantModel("mistralai/Voxtral-Mini-3B-2507", "cuda")
model.load()

# Define weather tool
tools = [{
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
}]

# Ask about weather (using audio file)
response = model.generate_response(
    audio_data="path/to/weather_question.wav",
    tools=tools
)
```

## Built-in Weather Function

The model includes a built-in weather function for testing:

- **Function**: `get_weather(location: str)`
- **Purpose**: Returns mock weather data for any location
- **Example**: Ask "What's the weather like in Oakville, Ontario?"

### Sample Response
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

## Testing & Validation

Run the validation script to test function calling:

```bash
python validate_voxtral_function_calling.py
```

Or run the comprehensive tests:

```bash
# Simple demo
python tests/demo_function_calling.py

# Full test suite
python tests/test_voxtral_function_calling.py

# Detailed example
python examples/function_calling_example.py
```

## Custom Functions

Register your own functions:

```python
import json

def get_time(timezone: str = "UTC") -> str:
    import datetime
    now = datetime.datetime.now()
    return json.dumps({
        "time": now.strftime("%H:%M:%S"),
        "timezone": timezone,
        "date": now.strftime("%Y-%m-%d")
    })

model.register_function(
    name="get_time",
    func=get_time,
    description="Get current time",
    parameters={
        "type": "object",
        "properties": {
            "timezone": {"type": "string"}
        },
        "required": []
    }
)
```

## How It Works

1. **Audio Input**: Provide audio asking a question
2. **Function Detection**: Model determines if a function should be called
3. **Parameter Extraction**: Model extracts function parameters from audio
4. **Function Execution**: The appropriate function is called
5. **Response Generation**: Final response includes function results

## Requirements

- `transformers` library
- `torch` (PyTorch)
- `numpy` for audio processing
- CUDA GPU recommended for better performance

```bash
pip install transformers torch numpy
```

## Model Information

- **Model**: `mistralai/Voxtral-Mini-3B-2507`
- **Type**: Multimodal (Audio + Text)
- **Function Calling**: Supported
- **Parameters**: ~3B

## Environment Setup

```bash
# For GPU support
export CUDA_AVAILABLE=true

# Run validation
python validate_voxtral_function_calling.py
```

## Key Features

✅ **Audio-triggered function calls** - Functions called based on spoken requests  
✅ **Built-in weather function** - Ready-to-use weather queries  
✅ **Custom function registration** - Add your own functions easily  
✅ **Latency measurement** - Track performance with `measure_latency=True`  
✅ **Mock audio testing** - Test without real speech files  

## Limitations

- Function calling depends on model's interpretation of audio
- Currently uses mock audio for testing (real speech recognition accuracy may vary)
- Function execution adds latency to response time
- Model needs to be specifically prompted to use functions

## Next Steps

1. Run the validation script to ensure everything works
2. Try the weather example with your own audio
3. Implement custom functions for your use case
4. Explore the detailed examples in `examples/function_calling_example.py`

For detailed documentation, see `docs/function_calling.md`.