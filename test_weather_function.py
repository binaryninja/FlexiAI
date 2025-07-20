#!/usr/bin/env python3
"""
Simple test script for Voxtral function calling validation.

This script tests the weather function calling feature with the
mistralai/Voxtral-Mini-3B-2507 model.

Usage: python test_weather_function.py
"""

import os
import sys
import tempfile
import wave
import numpy as np

def create_test_audio():
    """Create a simple test audio file."""
    print("🎵 Creating test audio...")

    # Simple 2-second audio at 16kHz
    duration = 2.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Create a simple speech-like tone
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz
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

def test_weather_function():
    """Test the weather function calling."""
    print("🧪 Testing Voxtral Weather Function Calling")
    print("=" * 50)

    try:
        # Import FlexiAI
        from flexiai.models.voxtral_model import VoxtralAssistantModel
        print("✅ FlexiAI imported successfully")

        # Configuration
        model_name = "mistralai/Voxtral-Mini-3B-2507"
        device = "cuda" if os.getenv("CUDA_AVAILABLE", "false").lower() == "true" else "cpu"

        print(f"📝 Model: {model_name}")
        print(f"🖥️ Device: {device}")
        print()

        # Initialize model
        print("🚀 Loading model...")
        model = VoxtralAssistantModel(model_name, device)

        if not model.load():
            print("❌ Failed to load model")
            return False

        print("✅ Model loaded successfully")

        # Check available functions
        info = model.get_model_info()
        print(f"🔧 Available functions: {info.get('available_functions', [])}")
        print()

        # Create test audio
        audio_file = create_test_audio()
        print(f"✅ Test audio created: {audio_file}")

        # Define weather tools
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
                            "description": "The city and country/province, e.g. 'Oakville, Ontario'"
                        }
                    },
                    "required": ["location"]
                }
            }
        }]

        print("🧠 Testing function calling...")
        print("   (Simulating: 'What's the weather in Oakville, Ontario?')")

        # Test with function calling
        response = model.generate_response(
            audio_data=audio_file,
            tools=tools,
            max_new_tokens=300,
            temperature=0.0
        )

        print("\n🎯 Response:")
        print("-" * 30)
        print(response)
        print()

        # Test function directly
        print("🔧 Testing function directly:")
        weather_result = model.available_functions["get_weather"](location="Oakville, Ontario")
        print("Direct call result:")
        print(weather_result)
        print()

        # Check if response contains weather data
        weather_keywords = ["temperature", "weather", "cloudy", "sunny", "°c", "humidity", "wind"]
        has_weather = any(keyword in response.lower() for keyword in weather_keywords)

        print("📊 Test Results:")
        if has_weather:
            print("✅ SUCCESS: Weather data found in response")
            print("✅ Function calling appears to be working")
        else:
            print("⚠️ WARNING: No weather data detected in response")
            print("⚠️ Function calling may need adjustment")

        # Cleanup
        try:
            os.unlink(audio_file)
        except:
            pass

        model.unload()
        print("🧹 Cleanup completed")

        return has_weather

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Install dependencies: pip install transformers torch numpy")
        return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🎯 Voxtral Weather Function Test")
    print("Testing model: mistralai/Voxtral-Mini-3B-2507")
    print()

    success = test_weather_function()

    if success:
        print("\n🎉 Test PASSED! Function calling is working.")
        return 0
    else:
        print("\n❌ Test FAILED! Check the setup and try again.")
        return 1

if __name__ == "__main__":
    exit(main())
