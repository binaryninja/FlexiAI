#!/usr/bin/env python3
"""
Simple demo script for Voxtral function calling.

This demonstrates how the VoxtralAssistantModel can call functions
when processing audio input asking about weather in Oakville, Ontario.
"""

import os
import sys
import numpy as np
import wave
import tempfile
from pathlib import Path

# Add the parent directory to sys.path to import FlexiAI modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from flexiai.models.voxtral_model import VoxtralAssistantModel

def create_simple_audio(text_description="weather question", duration=2, sample_rate=16000):
    """Create a simple audio file for testing."""
    print(f"🎵 Creating mock audio simulating: '{text_description}'")

    # Generate simple speech-like signal
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Mix of frequencies to simulate speech
    audio = (
        0.3 * np.sin(2 * np.pi * 300 * t) +  # Low frequency
        0.3 * np.sin(2 * np.pi * 800 * t) +  # Mid frequency
        0.2 * np.sin(2 * np.pi * 1500 * t) + # Higher frequency
        0.1 * np.random.normal(0, 0.1, len(t))  # Noise
    )

    # Add speech-like envelope
    envelope = np.exp(-0.3 * t) * (1 + 0.5 * np.sin(2 * np.pi * 4 * t))
    audio = audio * envelope

    # Normalize and convert to 16-bit
    audio = audio / np.max(np.abs(audio))
    audio = (audio * 32767).astype(np.int16)

    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_file.close()

    with wave.open(temp_file.name, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())

    return temp_file.name

def main():
    """Run the function calling demo."""
    print("🎯 Voxtral Function Calling Demo")
    print("=" * 50)
    print()
    print("This demo shows how Voxtral can call functions when asked")
    print("about weather in Oakville, Ontario.")
    print()

    # Configuration
    model_name = "mistralai/Voxtral-Mini-3B-2507"
    device = "cuda" if os.getenv("CUDA_AVAILABLE", "false").lower() == "true" else "cpu"

    print(f"📝 Model: {model_name}")
    print(f"🖥️ Device: {device}")
    print()

    try:
        # Initialize and load model
        print("🚀 Loading Voxtral model...")
        model = VoxtralAssistantModel(model_name, device)

        if not model.load():
            print("❌ Failed to load model!")
            print("Make sure you have:")
            print("  • transformers and torch installed")
            print("  • sufficient memory/VRAM")
            print("  • correct model name")
            return 1

        print("✅ Model loaded successfully!")
        print()

        # Show available functions
        info = model.get_model_info()
        print(f"🔧 Available functions: {info['available_functions']}")
        print()

        # Create mock audio
        audio_file = create_simple_audio("What's the weather like in Oakville, Ontario?")
        print(f"   • Audio file: {audio_file}")
        print()

        # Define weather tool
        weather_tools = [
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

        print("🧪 Test 1: WITH function calling enabled")
        print("-" * 40)

        try:
            response_with_tools = model.generate_response(
                audio_data=audio_file,
                tools=weather_tools,
                measure_latency=True,
                max_new_tokens=400,
                temperature=0.0
            )

            print("🎯 Response with function calling:")
            print(f"   {response_with_tools}")
            print()

        except Exception as e:
            print(f"❌ Error with function calling: {e}")
            print()

        print("🧪 Test 2: WITHOUT function calling (for comparison)")
        print("-" * 40)

        try:
            response_no_tools = model.generate_response(
                audio_data=audio_file,
                tools=None,
                max_new_tokens=400,
                temperature=0.0
            )

            print("🎯 Response without function calling:")
            print(f"   {response_no_tools}")
            print()

        except Exception as e:
            print(f"❌ Error without function calling: {e}")
            print()

        # Test the weather function directly
        print("🔧 Direct function test:")
        weather_result = model.available_functions["get_weather"](location="Oakville, Ontario")
        print(f"   get_weather('Oakville, Ontario') -> {weather_result}")
        print()

        print("📊 Summary:")
        print("  • Function calling allows the model to access real-time data")
        print("  • The weather function returns hardcoded data for this demo")
        print("  • In production, this could connect to real weather APIs")
        print()

        # Cleanup
        try:
            os.unlink(audio_file)
            print("🧹 Cleaned up temporary files")
        except:
            pass

        model.unload()
        print("🧹 Model unloaded")
        print()

        print("🎉 Demo completed successfully!")
        return 0

    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Install with: pip install transformers torch")
        return 1

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
