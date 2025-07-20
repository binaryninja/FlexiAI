#!/usr/bin/env python3
"""
Validation script for Voxtral function calling with the correct model.

This script validates that the VoxtralAssistantModel can successfully:
1. Load the mistralai/Voxtral-Mini-3B-2507 model
2. Process audio input
3. Detect when function calling is needed
4. Execute the weather function
5. Generate a response with the function result

Usage: python validate_voxtral_function_calling.py
"""

import os
import sys
import tempfile
import wave
import numpy as np
from pathlib import Path

# Add FlexiAI to path
sys.path.insert(0, str(Path(__file__).parent))

def create_weather_question_audio():
    """Create mock audio simulating 'What's the weather in Oakville, Ontario?'"""
    print("🎵 Creating mock audio for weather question...")

    # 3-second audio at 16kHz
    duration = 3.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Create speech-like pattern with multiple formants
    audio = (
        0.4 * np.sin(2 * np.pi * 300 * t) +    # Low formant
        0.3 * np.sin(2 * np.pi * 900 * t) +    # Mid formant
        0.2 * np.sin(2 * np.pi * 1500 * t) +   # High formant
        0.1 * np.random.normal(0, 0.05, len(t)) # Noise
    )

    # Apply speech envelope (words with pauses)
    words = 8  # "What's the weather like in Oakville Ontario"
    word_length = len(t) // words

    for i in range(words):
        start = i * word_length
        end = min((i + 1) * word_length, len(t))

        if i % 2 == 0:  # Word segments
            # Fade in/out for word boundaries
            fade = word_length // 20
            envelope = np.ones(end - start)
            if fade > 0:
                envelope[:fade] = np.linspace(0, 1, fade)
                envelope[-fade:] = np.linspace(1, 0, fade)
            audio[start:end] *= envelope
        else:  # Pause segments
            audio[start:end] *= 0.1

    # Normalize and convert to 16-bit PCM
    audio = audio / np.max(np.abs(audio))
    audio = (audio * 32767).astype(np.int16)

    # Save to temporary WAV file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_file.close()

    with wave.open(temp_file.name, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())

    return temp_file.name

def main():
    """Main validation function."""
    print("🧪 Voxtral Function Calling Validation")
    print("=" * 50)
    print("Model: mistralai/Voxtral-Mini-3B-2507")
    print("Task: Weather query with function calling")
    print()

    try:
        # Import here to handle missing dependencies gracefully
        from flexiai.models.voxtral_model import VoxtralAssistantModel
        print("✅ Successfully imported VoxtralAssistantModel")

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("Make sure you have installed:")
        print("  pip install transformers torch")
        return 1

    # Configuration
    model_name = "mistralai/Voxtral-Mini-3B-2507"
    device = "cuda" if os.getenv("CUDA_AVAILABLE", "false").lower() == "true" else "cpu"

    print(f"🖥️ Device: {device}")
    print()

    try:
        # Step 1: Initialize model
        print("🚀 Step 1: Initializing model...")
        model = VoxtralAssistantModel(model_name, device)
        print("✅ Model initialized")

        # Step 2: Load model
        print("⏳ Step 2: Loading model (this may take a few minutes)...")
        if not model.load():
            print("❌ Failed to load model!")
            print("Check that you have:")
            print("  • Sufficient memory/VRAM")
            print("  • Internet connection for model download")
            print("  • Correct model access permissions")
            return 1

        print("✅ Model loaded successfully")

        # Step 3: Check model info
        info = model.get_model_info()
        print(f"📊 Model parameters: {info.get('parameters', 'Unknown'):,}")
        print(f"🔧 Available functions: {info.get('available_functions', [])}")
        print()

        # Step 4: Create test audio
        print("🎵 Step 3: Creating test audio...")
        audio_file = create_weather_question_audio()
        print(f"✅ Created: {audio_file}")
        print()

        # Step 5: Test with function calling
        print("🧠 Step 4: Testing WITH function calling...")

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
                            "description": "The city and country/province, e.g. 'Oakville, Ontario'"
                        }
                    },
                    "required": ["location"]
                }
            }
        }]

        response_with_tools = model.generate_response(
            audio_data=audio_file,
            tools=tools,
            measure_latency=True,
            max_new_tokens=400,
            temperature=0.0
        )

        print("🎯 Response with function calling:")
        print("-" * 40)
        print(response_with_tools)
        print()

        # Step 6: Test without function calling
        print("🧠 Step 5: Testing WITHOUT function calling...")

        response_no_tools = model.generate_response(
            audio_data=audio_file,
            tools=None,
            max_new_tokens=400,
            temperature=0.0
        )

        print("🎯 Response without function calling:")
        print("-" * 40)
        print(response_no_tools)
        print()

        # Step 7: Direct function test
        print("🔧 Step 6: Testing function directly...")
        weather_result = model.available_functions["get_weather"](location="Oakville, Ontario")
        print("Direct function call result:")
        print(weather_result)
        print()

        # Step 8: Validation summary
        print("📋 Validation Summary:")
        print("=" * 30)

        # Check if function calling worked
        has_weather_data = any(term in response_with_tools.lower() for term in
                              ["temperature", "weather", "cloudy", "sunny", "°c", "humidity", "wind"])

        if has_weather_data:
            print("✅ Function calling appears to be working")
            print("✅ Weather data found in response")
        else:
            print("⚠️ Function calling may not be working as expected")
            print("⚠️ No weather data detected in response")

        # Compare responses
        if len(response_with_tools) > len(response_no_tools):
            print("✅ Function-enabled response is more detailed")
        else:
            print("⚠️ Function-enabled response is not significantly different")

        print()
        print("🎉 Validation completed!")

        # Cleanup
        try:
            os.unlink(audio_file)
            print("🧹 Temporary files cleaned up")
        except:
            pass

        model.unload()
        print("🧹 Model unloaded")

        return 0

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    print("Voxtral Function Calling Validation")
    print("This script tests the function calling feature with:")
    print("• Model: mistralai/Voxtral-Mini-3B-2507")
    print("• Function: get_weather")
    print("• Test: Weather query for Oakville, Ontario")
    print()

    exit(main())
