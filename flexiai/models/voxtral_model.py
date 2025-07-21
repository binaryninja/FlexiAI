"""
Voxtral assistant model implementation.
"""

import tempfile
import wave
import json
import re
import requests
import os
from typing import Optional, Any, List, Dict, Callable

try:
    from transformers import AutoProcessor, VoxtralForConditionalGeneration
    import torch
    HAS_VOXTRAL = True
except ImportError:
    HAS_VOXTRAL = False

from . import AssistantModel
from ..utils import debug_print
from ..tools.registry import tool_registry


class VoxtralAssistantModel(AssistantModel):
    """Voxtral model implementation for AI assistant functionality."""

    def __init__(self, model_name: str, device: str, torch_dtype=None):
        super().__init__(model_name, device)
        self.torch_dtype = torch_dtype or torch.bfloat16
        self.model = None
        self.processor = None
        self.available_functions = {}
        self._setup_builtin_functions()

        if not HAS_VOXTRAL:
            raise ImportError("Voxtral dependencies not available. Install with: pip install transformers torch")

        if not model_name.startswith("mistralai/Voxtral"):
            raise ValueError(f"Invalid Voxtral model name: {model_name}")

        # Currently supported model
        if model_name != "mistralai/Voxtral-Mini-3B-2507":
            print(f"⚠️ Warning: Using untested model '{model_name}'. Recommended: 'mistralai/Voxtral-Mini-3B-2507'")

    def _setup_builtin_functions(self):
        """Setup built-in functions using modular tool system."""
        # Get available tools from the tool registry
        available_tools = tool_registry.list_available_tools()

        self.available_functions = {}
        for tool_name in available_tools:
            tool = tool_registry.get_tool(tool_name)
            if tool:
                # Create a wrapper function that uses the tool system
                self.available_functions[tool_name] = self._create_tool_wrapper(tool_name)

        debug_print(f"🔧 Registered {len(self.available_functions)} tools: {list(self.available_functions.keys())}")

    def refresh_available_functions(self):
        """Refresh available functions to include newly registered tools (e.g., MCP tools)."""
        # Get available tools from the tool registry (including MCP tools)
        available_tools = tool_registry.list_available_tools()

        self.available_functions = {}
        for tool_name in available_tools:
            tool = tool_registry.get_tool(tool_name)
            if tool:
                # Create a wrapper function that uses the tool system
                self.available_functions[tool_name] = self._create_tool_wrapper(tool_name)

        debug_print(f"🔧 Refreshed {len(self.available_functions)} tools: {list(self.available_functions.keys())}")

    def _create_tool_wrapper(self, tool_name: str):
        """
        Create a wrapper function for a tool that converts tool results to JSON strings.

        Args:
            tool_name: Name of the tool to wrap

        Returns:
            Wrapper function that executes the tool and returns JSON string
        """
        def tool_wrapper(**kwargs):
            try:
                # Execute the tool using the tool registry
                result = tool_registry.execute_tool(tool_name, **kwargs)

                if result.success:
                    # Return the tool data as JSON string
                    return json.dumps(result.data, indent=2)
                else:
                    # Return error information as JSON
                    error_data = {
                        "error": result.error,
                        "metadata": result.metadata
                    }
                    return json.dumps(error_data)

            except Exception as e:
                debug_print(f"❌ Error executing tool {tool_name}: {e}")
                error_data = {
                    "error": f"Tool execution failed: {str(e)}",
                    "tool": tool_name
                }
                return json.dumps(error_data)

        return tool_wrapper

    def register_function(self, name: str, func: Callable, description: str, parameters: Dict):
        """
        Register a custom function for the model to use.

        Args:
            name: Function name
            func: The callable function
            description: Function description
            parameters: JSON schema for function parameters
        """
        self.available_functions[name] = func

    def load(self) -> bool:
        """Load the Voxtral model and processor."""
        try:
            debug_print(f"Loading Voxtral model: {self.model_name}")

            # Load processor
            self.processor = AutoProcessor.from_pretrained(self.model_name)

            # Load model
            self.model = VoxtralForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=self.torch_dtype
            ).to(self.device)

            self.is_loaded = True
            print(f"🚀 Voxtral model '{self.model_name}' loaded successfully on {self.device}")
            return True

        except Exception as e:
            print(f"⚠️ Failed to load Voxtral model '{self.model_name}': {e}")
            self.model = None
            self.processor = None
            self.is_loaded = False
            return False

    def unload(self):
        """Unload the Voxtral model."""
        if self.model is not None:
            # Move model to CPU and clear CUDA cache if using GPU
            if self.device == "cuda":
                self.model.cpu()
                torch.cuda.empty_cache()

            self.model = None
            self.processor = None
            self.is_loaded = False
            debug_print(f"Voxtral model '{self.model_name}' unloaded")

    def generate_response(self, audio_data: Any, prompt: str = None, tools: List[Dict] = None, measure_latency: bool = False, **kwargs) -> str:
        """
        Generate a response from audio input with optional function calling.

        Args:
            audio_data: Can be a file path (str) or numpy array
            prompt: Optional text prompt to guide the response
            tools: List of available tools/functions in OpenAI format
            measure_latency: Whether to enable detailed latency measurements
            **kwargs: Additional parameters for generation

        Returns:
            Generated response text or function call result
        """
        if not self.is_loaded or self.model is None or self.processor is None:
            raise RuntimeError("Voxtral model is not loaded")

        import time

        try:
            # If tools are provided, set up default weather tool for testing
            if tools is None and 'get_weather' in self.available_functions:
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
                                        "description": "The city and country/province, e.g. 'Oakville, Ontario'"
                                    }
                                },
                                "required": ["location"]
                            }
                        }
                    }
                ]

            # Measure audio preprocessing step
            if measure_latency:
                preprocessing_start = time.time()

            # Handle different types of audio data
            if isinstance(audio_data, str):
                # File path - read audio file
                audio_file = audio_data
            else:
                # Assume numpy array - need to save to temp file
                audio_file = self._save_audio_to_temp_file(audio_data, kwargs.get('sample_rate', 16000))

            # Use Voxtral conversation format
            conversation = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "audio",
                            "path": audio_file,
                        },
                    ],
                }
            ]

            if measure_latency:
                preprocessing_time = time.time() - preprocessing_start
                template_start = time.time()

            # Apply chat template with tools if provided
            if tools:
                inputs = self.processor.apply_chat_template(conversation, tools=tools)
            else:
                inputs = self.processor.apply_chat_template(conversation)

            if measure_latency:
                template_time = time.time() - template_start
                transfer_start = time.time()

            inputs = inputs.to(self.device, dtype=torch.bfloat16)

            if measure_latency:
                transfer_time = time.time() - transfer_start
                generation_start = time.time()

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=kwargs.get('max_new_tokens', 500),
                    temperature=kwargs.get('temperature', 0.0)
                )

            if measure_latency:
                generation_time = time.time() - generation_start
                decode_start = time.time()

            decoded_outputs = self.processor.batch_decode(outputs[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)
            response = decoded_outputs[0].strip()

            # Check if response contains function calls
            if tools and self._contains_function_call(response):
                debug_print("🔧 Function call detected in response")
                return self._handle_function_call(response, tools, audio_file, measure_latency, **kwargs)

            if measure_latency:
                decode_time = time.time() - decode_start

                # Log detailed breakdown
                debug_print(f"🔍 Voxtral Inference Breakdown:")
                debug_print(f"   • Audio preprocessing: {preprocessing_time*1000:.1f}ms")
                debug_print(f"   • Processor template (file load + audio proc): {template_time*1000:.1f}ms")
                debug_print(f"   • Tensor device transfer: {transfer_time*1000:.1f}ms")
                debug_print(f"   • Model generation: {generation_time*1000:.1f}ms")
                debug_print(f"   • Output decoding: {decode_time*1000:.1f}ms")
                debug_print(f"   • Response length: {len(response)} characters")

                # Calculate potential optimization savings
                file_processing_overhead = template_time
                debug_print(f"🎯 File processing overhead: {file_processing_overhead*1000:.1f}ms")
                debug_print(f"   (This could be eliminated with streaming optimization)")
            else:
                debug_print(f"Generated response: {len(response)} characters")

            return response

        except Exception as e:
            error_msg = f"Response generation failed: {e}"
            debug_print(error_msg)
            raise RuntimeError(error_msg)

    def _contains_function_call(self, response: str) -> bool:
        """Check if the response contains a function call pattern."""
        # Look for function call patterns in the response
        function_indicators = [
            '[{"name":',
            '{"name":',
            '"function":',
            'function_call',
            'get_weather',  # Our specific function for testing
            '"arguments":'  # Common in function calls
        ]

        response_lower = response.lower()
        contains_call = any(indicator.lower() in response_lower for indicator in function_indicators)

        # Also check if the response starts with [ and contains "name" and "arguments"
        stripped = response.strip()
        if stripped.startswith('[') and '"name"' in stripped and '"arguments"' in stripped:
            contains_call = True

        return contains_call

    def _handle_function_call(self, response: str, tools: List[Dict], audio_file: str, measure_latency: bool, **kwargs) -> str:
        """
        Handle function calling workflow.

        Args:
            response: The model's response containing function call
            tools: Available tools
            audio_file: Original audio file path
            measure_latency: Whether to measure latency
            **kwargs: Additional parameters

        Returns:
            Final response after function execution
        """
        try:
            # Extract function call information from response
            function_call_info = self._extract_function_call(response)

            if not function_call_info:
                debug_print("⚠️ Could not extract function call information")
                return response

            function_name = function_call_info.get('name')
            function_args = function_call_info.get('arguments', {})

            debug_print(f"🔧 Executing function: {function_name} with args: {function_args}")

            # Execute the function
            if function_name in self.available_functions:
                function_result = self.available_functions[function_name](**function_args)
                debug_print(f"🔧 Function result (raw): {function_result}")
                debug_print(f"🔧 Function result type: {type(function_result)}")
                debug_print(f"🔧 Function result length: {len(str(function_result))}")

                # Parse the function result to make it more conversational
                try:
                    function_data = json.loads(function_result)
                    debug_print(f"🔧 Parsed function_data: {json.dumps(function_data, indent=2)}")

                    # Check if the function returned an error
                    if 'error' in function_data:
                        error_msg = function_data['error']
                        metadata = function_data.get('metadata', {})
                        location = metadata.get('location', 'the requested location')

                        debug_print(f"🔧 Function returned error: {error_msg}")

                        if 'network' in error_msg.lower() or 'connection' in error_msg.lower():
                            return f"I'm sorry, I'm having trouble connecting to the weather service right now to get the weather for {location}. Please try again in a moment."
                        elif 'api key' in error_msg.lower():
                            return f"I'm sorry, there's an issue with the weather service configuration. The weather data is temporarily unavailable."
                        elif 'location' in error_msg.lower():
                            return f"I couldn't find weather information for '{location}'. Could you please specify the location more clearly, perhaps including the city and state or country?"
                        else:
                            return f"I'm sorry, I encountered an issue while getting the weather information for {location}. Please try again."

                    location = function_data.get('location', 'the requested location')
                    debug_print(f"🔧 Extracted location: {location}")

                    current = function_data.get('current', {})
                    debug_print(f"🔧 Extracted current: {current}")

                    temp = current.get('temperature', 'unknown')
                    condition = current.get('condition', 'unknown')
                    humidity = current.get('humidity', 'unknown')
                    wind = current.get('wind', 'unknown')
                    summary = function_data.get('summary', '')

                    debug_print(f"🔧 Weather fields - temp: {temp}, condition: {condition}, humidity: {humidity}, wind: {wind}")
                    debug_print(f"🔧 Summary: {summary}")

                    # Create a natural response using the weather data
                    natural_response = f"The weather in {location} is currently {temp} and {condition.lower()}. "
                    natural_response += f"The humidity is {humidity} with winds at {wind}. "
                    if summary:
                        natural_response += f"{summary}"

                    debug_print(f"🎯 Generated natural response from function result")
                    return natural_response.strip()

                except json.JSONDecodeError as e:
                    # If function result isn't JSON, create a simple response
                    debug_print(f"🔧 JSON decode error: {e}")
                    natural_response = f"I've retrieved the information you requested: {function_result}"
                    debug_print(f"🎯 Generated simple response from function result")
                    return natural_response
            else:
                debug_print(f"⚠️ Unknown function: {function_name}")
                return f"Sorry, I don't have access to the function '{function_name}'."

        except Exception as e:
            debug_print(f"⚠️ Function call handling failed: {e}")
            return response

    def _extract_function_call(self, response: str) -> Optional[Dict]:
        """
        Extract function call information from model response.

        Args:
            response: Model response text

        Returns:
            Dictionary with function name and arguments, or None if no function call found
        """
        try:
            stripped_response = response.strip()

            # First try to parse as JSON array (Voxtral format)
            if stripped_response.startswith('[') and stripped_response.endswith(']'):
                try:
                    parsed_array = json.loads(stripped_response)
                    if isinstance(parsed_array, list) and len(parsed_array) > 0:
                        function_call = parsed_array[0]
                        if 'name' in function_call:
                            return function_call
                except json.JSONDecodeError:
                    debug_print("⚠️ Failed to parse JSON array format")

            # Try to parse as single JSON object
            if stripped_response.startswith('{') and stripped_response.endswith('}'):
                try:
                    parsed = json.loads(stripped_response)
                    if 'name' in parsed:
                        return parsed
                except json.JSONDecodeError:
                    debug_print("⚠️ Failed to parse JSON object format")

            # Look for JSON within the response
            json_start = stripped_response.find('[{')
            if json_start != -1:
                json_end = stripped_response.find('}]', json_start)
                if json_end != -1:
                    json_str = stripped_response[json_start:json_end+2]
                    try:
                        parsed_array = json.loads(json_str)
                        if isinstance(parsed_array, list) and len(parsed_array) > 0:
                            function_call = parsed_array[0]
                            if 'name' in function_call:
                                return function_call
                    except json.JSONDecodeError:
                        debug_print("⚠️ Failed to parse embedded JSON array")

            # Fallback: simple pattern matching for weather function
            response_lower = response.lower()
            if 'get_weather' in response_lower:
                debug_print("🔧 Using fallback pattern matching for get_weather")

                # Look for location mentions
                location_patterns = [
                    r'"location"[:\s]*"([^"]+)"',
                    r'oakville[,\s]*ontario',
                    r'oakville[,\s]*on',
                    r'oakville',
                ]

                for pattern in location_patterns:
                    match = re.search(pattern, response, re.IGNORECASE)
                    if match:
                        location = match.group(1) if match.lastindex and len(match.groups()) > 0 else match.group(0)
                        location = location.strip(' ,"\'')
                        if location:
                            return {
                                'name': 'get_weather',
                                'arguments': {'location': location}
                            }

                # Default fallback
                return {
                    'name': 'get_weather',
                    'arguments': {'location': 'Oakville, Ontario'}
                }

            return None

        except Exception as e:
            debug_print(f"⚠️ Error extracting function call: {e}")
            return None

    def _save_audio_to_temp_file(self, audio_data, sample_rate: int) -> str:
        """Save numpy audio data to a temporary WAV file."""
        import numpy as np

        # Ensure audio_data is numpy array
        if not isinstance(audio_data, np.ndarray):
            audio_data = np.array(audio_data)

        # Convert to 16-bit PCM if needed
        if audio_data.dtype != np.int16:
            # Normalize to [-1, 1] if not already
            if audio_data.max() > 1.0 or audio_data.min() < -1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            # Convert to 16-bit PCM
            audio_data = (audio_data * 32767).astype(np.int16)

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_file.close()

        # Write WAV file
        with wave.open(temp_file.name, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        return temp_file.name

    def set_system_prompt(self, system_prompt: str):
        """Set a system prompt for consistent behavior."""
        self.system_prompt = system_prompt

    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "torch_dtype": str(self.torch_dtype),
            "is_loaded": self.is_loaded,
            "parameters": sum(p.numel() for p in self.model.parameters()) if self.model else 0,
            "available_functions": list(self.available_functions.keys())
        }

    def __str__(self) -> str:
        return f"VoxtralAssistantModel(model={self.model_name}, device={self.device}, loaded={self.is_loaded})"
