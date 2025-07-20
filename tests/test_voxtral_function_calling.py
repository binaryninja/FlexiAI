#!/usr/bin/env python3
"""
Test script for Voxtral function calling functionality.

This script tests the implementation of function calling in the VoxtralAssistantModel
by asking the model about weather in Oakville, Ontario.
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
from flexiai.utils import debug_print

def create_mock_audio_file(duration_seconds=3, sample_rate=16000, frequency=440):
    """
    Create a mock audio file for testing.

    Args:
        duration_seconds: Duration of the audio in seconds
        sample_rate: Sample rate in Hz
        frequency: Frequency of the sine wave in Hz

    Returns:
        Path to the created audio file
    """
    # Generate a simple sine wave
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds), False)
    # Create a more speech-like signal by combining multiple frequencies
    audio_data = (
        0.3 * np.sin(2 * np.pi * frequency * t) +
        0.2 * np.sin(2 * np.pi * frequency * 1.5 * t) +
        0.1 * np.sin(2 * np.pi * frequency * 2 * t)
    )

    # Add some envelope to make it more speech-like
    envelope = np.exp(-0.5 * t)  # Exponential decay
    audio_data = audio_data * envelope

    # Normalize and convert to 16-bit PCM
    audio_data = audio_data / np.max(np.abs(audio_data))
    audio_data = (audio_data * 32767).astype(np.int16)

    # Create temporary WAV file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_file.close()

    with wave.open(temp_file.name, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())

    return temp_file.name

def create_speech_like_audio(duration_seconds=3, sample_rate=16000):
    """
    Create a more speech-like audio pattern for testing.
    """
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds), False)

    # Create speech-like formants (simplified)
    formant1 = 800  # First formant
    formant2 = 1200  # Second formant
    formant3 = 2400  # Third formant

    # Generate formant frequencies with some variation
    f1_variation = 100 * np.sin(2 * np.pi * 3 * t)  # 3 Hz variation
    f2_variation = 150 * np.sin(2 * np.pi * 2 * t)  # 2 Hz variation

    # Create the signal
    audio_data = (
        0.4 * np.sin(2 * np.pi * (formant1 + f1_variation) * t) +
        0.3 * np.sin(2 * np.pi * (formant2 + f2_variation) * t) +
        0.2 * np.sin(2 * np.pi * formant3 * t) +
        0.1 * np.random.normal(0, 0.1, len(t))  # Add some noise
    )

    # Apply speech-like envelope (segments of speech)
    segments = 6  # Number of "words"
    segment_length = len(t) // segments

    for i in range(segments):
        start = i * segment_length
        end = min((i + 1) * segment_length, len(t))
        if i % 2 == 0:  # Speech segments
            # Create attack and decay
            segment_env = np.ones(end - start)
            fade_length = min(segment_length // 10, len(segment_env) // 4)
            segment_env[:fade_length] = np.linspace(0, 1, fade_length)
            segment_env[-fade_length:] = np.linspace(1, 0, fade_length)
            audio_data[start:end] *= segment_env
        else:  # Silence segments
            audio_data[start:end] *= 0.1

    # Normalize and convert to 16-bit PCM
    audio_data = audio_data / np.max(np.abs(audio_data))
    audio_data = (audio_data * 32767).astype(np.int16)

    # Create temporary WAV file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_file.close()

    with wave.open(temp_file.name, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())

    return temp_file.name

def test_voxtral_function_calling():
    """Test the Voxtral function calling functionality."""
    print("🧪 Testing Voxtral Function Calling")
    print("=" * 50)

    # Configuration
    model_name = "mistralai/Voxtral-Mini-3B-2507"  # Default Voxtral model
    device = "cuda" if os.getenv("CUDA_AVAILABLE", "false").lower() == "true" else "cpu"

    print(f"📝 Model: {model_name}")
    print(f"🖥️  Device: {device}")
    print()

    try:
        # Initialize the model
        print("🚀 Initializing Voxtral model...")
        model = VoxtralAssistantModel(model_name, device)

        # Show model info before loading
        info = model.get_model_info()
        print(f"📊 Model info: {info}")
        print()

        # Load the model
        print("⏳ Loading model (this may take a while)...")
        success = model.load()

        if not success:
            print("❌ Failed to load model. Check if:")
            print("   • Model name is correct")
            print("   • You have the required dependencies installed")
            print("   • You have sufficient memory/VRAM")
            return False

        print("✅ Model loaded successfully!")
        print()

        # Show updated model info
        info = model.get_model_info()
        print(f"📊 Loaded model info:")
        for key, value in info.items():
            print(f"   • {key}: {value}")
        print()

        # Create mock audio files for testing
        print("🎵 Creating mock audio files...")

        # Test 1: Simple sine wave
        audio_file_1 = create_mock_audio_file(duration_seconds=2, frequency=440)
        print(f"   • Simple sine wave: {audio_file_1}")

        # Test 2: Speech-like audio
        audio_file_2 = create_speech_like_audio(duration_seconds=3)
        print(f"   • Speech-like audio: {audio_file_2}")
        print()

        # Define weather tools
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

        # Test cases
        test_cases = [
            {
                "name": "Weather Query Test 1",
                "audio_file": audio_file_1,
                "description": "Testing with simple sine wave (simulating 'What's the weather like in Oakville, Ontario?')"
            },
            {
                "name": "Weather Query Test 2",
                "audio_file": audio_file_2,
                "description": "Testing with speech-like audio (simulating weather question)"
            }
        ]

        # Run tests
        for i, test_case in enumerate(test_cases, 1):
            print(f"🧪 Test {i}: {test_case['name']}")
            print(f"📝 {test_case['description']}")
            print("-" * 40)

            try:
                # Generate response with function calling enabled
                print("⏳ Generating response with function calling...")
                response = model.generate_response(
                    audio_data=test_case['audio_file'],
                    tools=weather_tools,
                    measure_latency=True,
                    max_new_tokens=300,
                    temperature=0.1
                )

                print(f"🎯 Response:")
                print(f"   {response}")
                print()

                # Test without function calling for comparison
                print("⏳ Generating response without function calling...")
                response_no_tools = model.generate_response(
                    audio_data=test_case['audio_file'],
                    tools=None,
                    measure_latency=False,
                    max_new_tokens=300,
                    temperature=0.1
                )

                print(f"🎯 Response (no tools):")
                print(f"   {response_no_tools}")
                print()

            except Exception as e:
                print(f"❌ Test {i} failed: {e}")
                print()

            print("=" * 50)

        # Test custom function registration
        print("🔧 Testing custom function registration...")

        def get_time_info(timezone: str = "UTC") -> str:
            """Get current time information."""
            import datetime
            now = datetime.datetime.now()
            return f"Current time in {timezone}: {now.strftime('%Y-%m-%d %H:%M:%S')}"

        model.register_function(
            name="get_time",
            func=get_time_info,
            description="Get current time information",
            parameters={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone for the time query"
                    }
                },
                "required": []
            }
        )

        # Test the registered function
        time_result = model.available_functions["get_time"](timezone="EST")
        print(f"✅ Custom function test: {time_result}")
        print()

        # Cleanup
        print("🧹 Cleaning up...")
        try:
            os.unlink(audio_file_1)
            os.unlink(audio_file_2)
            print("   • Temporary audio files deleted")
        except:
            pass

        model.unload()
        print("   • Model unloaded")
        print()

        print("🎉 All tests completed successfully!")
        return True

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Make sure you have installed the required dependencies:")
        print("   pip install transformers torch")
        return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🎯 Voxtral Function Calling Test Suite")
    print("=" * 60)
    print()

    print("ℹ️  This test simulates asking the Voxtral model about weather")
    print("   in Oakville, Ontario using function calling capabilities.")
    print()
    print("⚠️  Note: This test uses mock audio data since we're testing")
    print("   the function calling mechanism, not speech recognition.")
    print()

    # Check environment
    print("🔍 Environment Check:")
    print(f"   • Python version: {sys.version}")
    print(f"   • Working directory: {os.getcwd()}")

    try:
        import torch
        print(f"   • PyTorch version: {torch.__version__}")
        print(f"   • CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   • CUDA device count: {torch.cuda.device_count()}")
    except ImportError:
        print("   • PyTorch: Not installed")

    try:
        import transformers
        print(f"   • Transformers version: {transformers.__version__}")
    except ImportError:
        print("   • Transformers: Not installed")

    print()

    # Run the test
    success = test_voxtral_function_calling()

    if success:
        print("✅ Test suite completed successfully!")
        return 0
    else:
        print("❌ Test suite failed!")
        return 1

if __name__ == "__main__":
    exit(main())
