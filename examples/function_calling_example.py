#!/usr/bin/env python3
"""
Function Calling Example for Voxtral Model

This example demonstrates how to use function calling with the VoxtralAssistantModel
to create an AI assistant that can call external functions to provide real-time information.

Example: Asking about weather in Oakville, Ontario
"""

import os
import sys
import tempfile
import wave
import numpy as np
from pathlib import Path

# Add FlexiAI to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flexiai.models.voxtral_model import VoxtralAssistantModel


def create_mock_audio_question(question_text="What's the weather like in Oakville, Ontario?"):
    """
    Create a mock audio file simulating a spoken question.
    In a real application, this would be actual recorded audio.
    """
    print(f"🎵 Creating mock audio for: '{question_text}'")

    # Generate simple audio pattern (2 seconds, 16kHz)
    duration = 2.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Create speech-like frequency mix
    audio = (
        0.4 * np.sin(2 * np.pi * 400 * t) +    # Fundamental frequency
        0.3 * np.sin(2 * np.pi * 800 * t) +    # First harmonic
        0.2 * np.sin(2 * np.pi * 1200 * t) +   # Second harmonic
        0.1 * np.random.normal(0, 0.1, len(t)) # Background noise
    )

    # Apply speech envelope (simulating word boundaries)
    words = 6  # Simulate 6 words
    word_length = len(t) // words

    for i in range(words):
        start = i * word_length
        end = min((i + 1) * word_length, len(t))

        if i % 2 == 0:  # Speech segments
            fade = word_length // 10
            envelope = np.ones(end - start)
            envelope[:fade] = np.linspace(0, 1, fade)
            envelope[-fade:] = np.linspace(1, 0, fade)
            audio[start:end] *= envelope
        else:  # Brief pauses
            audio[start:end] *= 0.2

    # Normalize and convert to 16-bit PCM
    audio = audio / np.max(np.abs(audio))
    audio = (audio * 32767).astype(np.int16)

    # Save to temporary WAV file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_file.close()

    with wave.open(temp_file.name, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())

    return temp_file.name


def setup_weather_tools():
    """
    Define the weather function tool specification.
    This follows the OpenAI function calling format.
    """
    return [
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


def custom_weather_function(location: str) -> str:
    """
    Custom weather function that could connect to a real weather API.
    For this example, we return realistic mock data.
    """
    import json
    from datetime import datetime

    # In a real application, you would call a weather API here
    # For demo purposes, we return mock data based on location

    weather_data = {
        "location": location,
        "timestamp": datetime.now().isoformat(),
        "temperature": "18°C",
        "condition": "Partly cloudy",
        "humidity": "72%",
        "wind": "12 km/h SW",
        "pressure": "1013 hPa",
        "forecast": "Cloudy with sunny breaks. High of 22°C, low of 14°C."
    }

    return json.dumps(weather_data, indent=2)


def main():
    """Main example demonstrating function calling."""
    print("🌤️  Voxtral Function Calling Example")
    print("=" * 60)
    print()
    print("This example shows how to:")
    print("• Set up function calling with Voxtral")
    print("• Define custom functions")
    print("• Process audio with function calling enabled")
    print()

    # Configuration
    model_name = "mistralai/Voxtral-Mini-3B-2507"
    device = "cuda" if os.getenv("CUDA_AVAILABLE", "false").lower() == "true" else "cpu"

    print(f"📝 Model: {model_name}")
    print(f"🖥️ Device: {device}")
    print()

    try:
        # Step 1: Initialize and load the model
        print("🚀 Step 1: Loading Voxtral model...")
        model = VoxtralAssistantModel(model_name, device)

        if not model.load():
            print("❌ Failed to load model. Check your setup:")
            print("  • Install dependencies: pip install transformers torch")
            print("  • Ensure sufficient memory/VRAM")
            print("  • Verify model name is correct")
            return 1

        print("✅ Model loaded successfully!")
        print()

        # Step 2: Register custom function (optional)
        print("🔧 Step 2: Registering custom weather function...")
        model.register_function(
            name="get_detailed_weather",
            func=custom_weather_function,
            description="Get detailed weather information with forecast",
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location for weather query"
                    }
                },
                "required": ["location"]
            }
        )

        # Show available functions
        info = model.get_model_info()
        print(f"Available functions: {info['available_functions']}")
        print()

        # Step 3: Set up tools for function calling
        print("⚙️ Step 3: Setting up function calling tools...")
        tools = setup_weather_tools()
        print(f"Configured {len(tools)} tool(s)")
        print()

        # Step 4: Create audio input
        print("🎵 Step 4: Creating audio input...")
        audio_file = create_mock_audio_question()
        print(f"Audio file: {audio_file}")
        print()

        # Step 5: Process with function calling
        print("🧠 Step 5: Processing audio with function calling...")
        print("⏳ Generating response...")

        response = model.generate_response(
            audio_data=audio_file,
            tools=tools,
            measure_latency=True,
            max_new_tokens=500,
            temperature=0.1
        )

        print()
        print("🎯 Response with function calling:")
        print("-" * 40)
        print(response)
        print()

        # Step 6: Compare without function calling
        print("🧠 Step 6: Processing same audio WITHOUT function calling...")

        response_no_tools = model.generate_response(
            audio_data=audio_file,
            tools=None,  # No tools = no function calling
            max_new_tokens=500,
            temperature=0.1
        )

        print("🎯 Response without function calling:")
        print("-" * 40)
        print(response_no_tools)
        print()

        # Step 7: Test custom function directly
        print("🔧 Step 7: Testing custom function directly...")
        custom_result = model.available_functions["get_detailed_weather"](
            location="Oakville, Ontario"
        )
        print("Custom weather function result:")
        print(custom_result)
        print()

        # Summary
        print("📊 Summary:")
        print("✅ Function calling allows AI to access external data")
        print("✅ Functions can be called based on audio input")
        print("✅ Custom functions can be easily registered")
        print("✅ Responses are more informative with real-time data")
        print()

        # Cleanup
        try:
            os.unlink(audio_file)
            print("🧹 Temporary files cleaned up")
        except:
            pass

        model.unload()
        print("🧹 Model unloaded")
        print()

        print("🎉 Example completed successfully!")
        return 0

    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Install with: pip install transformers torch numpy")
        return 1

    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    print("To run this example:")
    print("1. Install dependencies: pip install transformers torch numpy")
    print("2. Set CUDA_AVAILABLE=true if you have GPU support")
    print("3. Run: python function_calling_example.py")
    print()

    exit(main())
