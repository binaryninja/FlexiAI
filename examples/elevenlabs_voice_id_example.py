#!/usr/bin/env python3
"""
Example script demonstrating ELEVENLABS_VOICE_ID environment variable usage.

This example shows how to:
1. Set voice ID via environment variable
2. Override voice ID programmatically
3. List available voices
4. Test voice synthesis with different voices

Usage:
    # Set voice ID via environment variable
    export ELEVENLABS_VOICE_ID="21m00Tcm4TlvDq8ikWAM"
    python elevenlabs_voice_id_example.py

    # Or set API key and voice ID together
    export ELEVENLABS_API_KEY="your_api_key_here"
    export ELEVENLABS_VOICE_ID="your_preferred_voice_id"
    python elevenlabs_voice_id_example.py
"""

import os
import sys
import time
from pathlib import Path

# Add FlexiAI to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flexiai.models import ModelFactory
from flexiai.config.api_keys import get_api_key


def check_prerequisites():
    """Check if prerequisites are met."""
    print("🔍 Checking Prerequisites")
    print("=" * 40)

    # Check API key
    api_key = get_api_key('ELEVENLABS_API_KEY')
    if not api_key:
        print("❌ ElevenLabs API key not found!")
        print("Please set your API key:")
        print("  export ELEVENLABS_API_KEY='your_api_key_here'")
        print("Get your API key from: https://elevenlabs.io/app/settings/api-keys")
        return False

    print(f"✅ API key found: {api_key[:8]}...")

    # Check voice ID
    voice_id = os.getenv('ELEVENLABS_VOICE_ID')
    if voice_id:
        print(f"✅ Voice ID from environment: {voice_id}")
    else:
        print("⚠️ No ELEVENLABS_VOICE_ID set - will use default voice")

    return True


def demonstrate_environment_voice():
    """Demonstrate using voice ID from environment variable."""
    print("\n🎭 Environment Variable Voice Example")
    print("=" * 45)

    # Create model - it will automatically use ELEVENLABS_VOICE_ID if set
    model = ModelFactory.create_tts_model(
        model_name="elevenlabs",
        device="cpu"
    )

    if not model or not model.load():
        print("❌ Failed to create/load ElevenLabs model")
        return False

    print(f"✅ Model loaded successfully")
    print(f"🎯 Current voice ID: {model.voice_id}")

    # Test synthesis
    test_text = "Hello! This is a test using the voice ID from the environment variable."
    output_file = "env_voice_test.mp3"

    print(f"\n🗣️ Synthesizing: '{test_text}'")
    start_time = time.time()

    success = model.synthesize(test_text, output_file)
    synthesis_time = time.time() - start_time

    if success:
        print(f"✅ Synthesis successful in {synthesis_time:.2f}s")
        print(f"📄 Audio saved to: {output_file}")
    else:
        print("❌ Synthesis failed")
        return False

    return True


def demonstrate_programmatic_override():
    """Demonstrate overriding voice ID programmatically."""
    print("\n🔧 Programmatic Voice Override Example")
    print("=" * 45)

    # Create model with specific voice ID (overrides environment)
    custom_voice_id = "EXAVITQu4vr4xnSDxMaL"  # Bella voice

    model = ModelFactory.create_tts_model(
        model_name="elevenlabs",
        device="cpu",
        voice_id=custom_voice_id
    )

    if not model or not model.load():
        print("❌ Failed to create/load ElevenLabs model")
        return False

    print(f"✅ Model loaded with custom voice")
    print(f"🎯 Voice ID override: {model.voice_id}")

    env_voice = os.getenv('ELEVENLABS_VOICE_ID')
    if env_voice and env_voice != custom_voice_id:
        print(f"📝 Environment voice ({env_voice}) was overridden")

    # Test synthesis
    test_text = "This message uses a programmatically specified voice, overriding the environment variable."
    output_file = "custom_voice_test.mp3"

    print(f"\n🗣️ Synthesizing: '{test_text}'")
    start_time = time.time()

    success = model.synthesize(test_text, output_file)
    synthesis_time = time.time() - start_time

    if success:
        print(f"✅ Synthesis successful in {synthesis_time:.2f}s")
        print(f"📄 Audio saved to: {output_file}")
    else:
        print("❌ Synthesis failed")
        return False

    return True


def demonstrate_voice_listing():
    """Demonstrate listing available voices."""
    print("\n📋 Available Voices Example")
    print("=" * 35)

    model = ModelFactory.create_tts_model(
        model_name="elevenlabs",
        device="cpu"
    )

    if not model or not model.load():
        print("❌ Failed to create/load ElevenLabs model")
        return False

    print("🔍 Fetching available voices...")
    voices = model.get_available_voices()

    if not voices:
        print("❌ No voices available or API error")
        return False

    print(f"✅ Found {len(voices)} available voices:")
    print()

    current_voice = os.getenv('ELEVENLABS_VOICE_ID') or model.voice_id

    for i, voice in enumerate(voices[:10], 1):  # Show first 10 voices
        voice_id = voice.get('voice_id', 'unknown')
        name = voice.get('name', 'Unknown')
        category = voice.get('category', 'N/A')

        # Mark current voice
        marker = " ← CURRENT" if voice_id == current_voice else ""

        print(f"  {i:2d}. {name} ({category})")
        print(f"      ID: {voice_id}{marker}")

        if voice.get('description'):
            print(f"      Description: {voice['description']}")
        print()

    if len(voices) > 10:
        print(f"... and {len(voices) - 10} more voices available")

    return True


def demonstrate_voice_switching():
    """Demonstrate switching voices at runtime."""
    print("\n🔄 Runtime Voice Switching Example")
    print("=" * 40)

    model = ModelFactory.create_tts_model(
        model_name="elevenlabs",
        device="cpu"
    )

    if not model or not model.load():
        print("❌ Failed to create/load ElevenLabs model")
        return False

    # Get some voices to test with
    voices = model.get_available_voices()
    if len(voices) < 2:
        print("❌ Need at least 2 voices for switching demo")
        return False

    # Test with first two voices
    test_voices = voices[:2]
    test_text = "This is a test of voice switching capabilities."

    for i, voice in enumerate(test_voices, 1):
        voice_id = voice['voice_id']
        voice_name = voice['name']

        print(f"\n🎭 Testing voice {i}: {voice_name}")
        print(f"   Voice ID: {voice_id}")

        # Switch to this voice
        model.set_voice_parameters(voice_id)

        output_file = f"voice_switch_test_{i}.mp3"

        start_time = time.time()
        success = model.synthesize(test_text, output_file)
        synthesis_time = time.time() - start_time

        if success:
            print(f"   ✅ Synthesis successful in {synthesis_time:.2f}s")
            print(f"   📄 Audio saved to: {output_file}")
        else:
            print(f"   ❌ Synthesis failed")

    return True


def show_configuration_examples():
    """Show different ways to configure voice ID."""
    print("\n⚙️ Configuration Examples")
    print("=" * 30)

    examples = [
        "1. Environment Variable (Recommended):",
        "   export ELEVENLABS_VOICE_ID='21m00Tcm4TlvDq8ikWAM'",
        "   python your_script.py",
        "",
        "2. In .env file:",
        "   echo 'ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM' >> .env",
        "",
        "3. Programmatically:",
        "   model = ModelFactory.create_tts_model(",
        "       'elevenlabs', 'cpu',",
        "       voice_id='21m00Tcm4TlvDq8ikWAM'",
        "   )",
        "",
        "4. Runtime switching:",
        "   model.set_voice_parameters('EXAVITQu4vr4xnSDxMaL')",
        "",
        "Priority order:",
        "   1. Explicit parameter (voice_id=...)",
        "   2. Environment variable (ELEVENLABS_VOICE_ID)",
        "   3. Default voice",
    ]

    for line in examples:
        print(line)


def main():
    """Main function to run all examples."""
    print("🎯 ElevenLabs Voice ID Configuration Examples")
    print("=" * 50)

    if not check_prerequisites():
        return False

    # Show configuration options
    show_configuration_examples()

    success_count = 0
    total_tests = 4

    # Run examples
    if demonstrate_environment_voice():
        success_count += 1

    if demonstrate_programmatic_override():
        success_count += 1

    if demonstrate_voice_listing():
        success_count += 1

    if demonstrate_voice_switching():
        success_count += 1

    # Summary
    print(f"\n📊 Results Summary")
    print("=" * 20)
    print(f"✅ Successful tests: {success_count}/{total_tests}")

    if success_count == total_tests:
        print("🎉 All examples completed successfully!")
        print("\n💡 Next steps:")
        print("1. Set your preferred voice ID:")
        print("   export ELEVENLABS_VOICE_ID='your_preferred_voice_id'")
        print("2. Use FlexiAI with TTS:")
        print("   flexiai --tts")
        print("3. The voice will be used automatically!")
    else:
        print("⚠️ Some examples failed. Check the error messages above.")

    return success_count == total_tests


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Examples cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
