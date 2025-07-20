#!/usr/bin/env python3
"""
FlexiAI API Key Management Example

This example demonstrates how to use the secure API key management system
in FlexiAI for various services like OpenAI, ElevenLabs, OpenWeatherMap, etc.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flexiai.config.api_keys import (
    get_api_key,
    set_api_key,
    api_keys,
    setup_api_keys
)


def basic_usage_example():
    """Basic API key usage examples."""
    print("🔑 Basic API Key Usage Examples")
    print("=" * 40)

    # Example 1: Get an API key (returns None if not found)
    openai_key = get_api_key('OPENAI_API_KEY')
    if openai_key:
        print(f"✅ OpenAI API key found: {openai_key[:8]}...")
    else:
        print("❌ OpenAI API key not found")

    # Example 2: Get a required API key (raises exception if not found)
    try:
        elevenlabs_key = get_api_key('ELEVENLABS_API_KEY', required=True)
        print(f"✅ ElevenLabs API key found: {elevenlabs_key[:8]}...")
    except ValueError as e:
        print(f"❌ {e}")

    # Example 3: Check multiple keys
    keys_to_check = ['OPENAI_API_KEY', 'ELEVENLABS_API_KEY', 'OPENWEATHERMAP_API_KEY']
    for key_name in keys_to_check:
        key_value = get_api_key(key_name)
        status = "✅ Available" if key_value else "❌ Missing"
        print(f"  {key_name}: {status}")


def setting_keys_example():
    """Examples of setting API keys programmatically."""
    print("\n🔧 Setting API Keys Examples")
    print("=" * 40)

    # Example 1: Set a key for current session
    try:
        # Note: Use a dummy key for example purposes
        set_api_key('EXAMPLE_API_KEY', 'demo-key-12345')
        print("✅ Example API key set successfully")

        # Verify it was set
        retrieved_key = get_api_key('EXAMPLE_API_KEY')
        print(f"✅ Retrieved key: {retrieved_key}")
    except Exception as e:
        print(f"❌ Error setting key: {e}")

    # Example 2: Set key with validation (will fail for invalid format)
    try:
        set_api_key('OPENAI_API_KEY', 'invalid-key')
        print("✅ OpenAI key set")
    except ValueError as e:
        print(f"❌ Key validation failed: {e}")

    # Example 3: Set a properly formatted OpenAI key
    try:
        set_api_key('OPENAI_API_KEY', 'sk-example-key-here')
        print("✅ Valid OpenAI key format accepted")
    except Exception as e:
        print(f"❌ Error: {e}")


def advanced_usage_example():
    """Advanced API key management examples."""
    print("\n🚀 Advanced Usage Examples")
    print("=" * 40)

    # Example 1: List all available keys
    available_keys = api_keys.list_available_keys()
    print("📊 API Key Status Report:")

    for key_name, info in available_keys.items():
        status_icon = "✅" if info['available'] else "❌"
        source_info = f"({info['source']})" if info['available'] else ""
        print(f"  {status_icon} {key_name}: {info['description']} {source_info}")

    # Example 2: Conditional API usage
    print("\n🔄 Conditional API Usage:")

    def use_openai_if_available():
        """Example of conditional API usage."""
        openai_key = get_api_key('OPENAI_API_KEY')
        if openai_key:
            print("  🤖 OpenAI API available - would initialize OpenAI client")
            # In real code: openai.api_key = openai_key
            return True
        else:
            print("  ⚠️ OpenAI API not available - falling back to local model")
            return False

    def use_elevenlabs_if_available():
        """Example of conditional TTS usage."""
        elevenlabs_key = get_api_key('ELEVENLABS_API_KEY')
        if elevenlabs_key:
            print("  🔊 ElevenLabs API available - would use premium TTS")
            # In real code: initialize ElevenLabs client
            return True
        else:
            print("  🔊 ElevenLabs API not available - using system TTS")
            return False

    use_openai_if_available()
    use_elevenlabs_if_available()


def real_world_integration_example():
    """Example of how to integrate API key management in a real application."""
    print("\n🌍 Real-World Integration Example")
    print("=" * 40)

    class WeatherService:
        """Example service that uses API keys."""

        def __init__(self):
            self.api_key = get_api_key('OPENWEATHERMAP_API_KEY')
            if not self.api_key:
                print("⚠️ Weather service: No API key found, using mock data")

        def get_weather(self, location: str):
            if self.api_key:
                print(f"🌤️ Getting real weather for {location} using API")
                # In real code: make actual API request
                return {"temperature": "22°C", "condition": "Sunny", "real": True}
            else:
                print(f"🌤️ Returning mock weather for {location}")
                return {"temperature": "20°C", "condition": "Unknown", "real": False}

    class TTSService:
        """Example TTS service with fallbacks."""

        def __init__(self):
            self.elevenlabs_key = get_api_key('ELEVENLABS_API_KEY')
            self.openai_key = get_api_key('OPENAI_API_KEY')

        def speak(self, text: str):
            if self.elevenlabs_key:
                print(f"🔊 Using ElevenLabs TTS: '{text[:30]}...'")
            elif self.openai_key:
                print(f"🔊 Using OpenAI TTS: '{text[:30]}...'")
            else:
                print(f"🔊 Using system TTS: '{text[:30]}...'")

    # Demonstrate the services
    weather = WeatherService()
    tts = TTSService()

    weather_data = weather.get_weather("London")
    weather_text = f"The weather in London is {weather_data['condition']} with temperature {weather_data['temperature']}"
    tts.speak(weather_text)


def security_best_practices():
    """Show security best practices."""
    print("\n🔒 Security Best Practices")
    print("=" * 40)

    print("✅ DO:")
    print("  • Use environment variables or .env files")
    print("  • Add .env to .gitignore")
    print("  • Use get_api_key() function instead of os.getenv()")
    print("  • Validate API keys before using them")
    print("  • Use required=True for critical API keys")
    print("  • Consider encrypted storage for production")

    print("\n❌ DON'T:")
    print("  • Hardcode API keys in source code")
    print("  • Commit .env files to version control")
    print("  • Share API keys in logs or error messages")
    print("  • Use dummy or test keys in production")
    print("  • Store keys in plain text files")

    print("\n💡 Example of secure usage:")
    print("""
    # Good ✅
    from flexiai.config.api_keys import get_api_key

    def init_openai_client():
        api_key = get_api_key('OPENAI_API_KEY', required=True)
        return openai.OpenAI(api_key=api_key)

    # Bad ❌
    import openai
    openai.api_key = "sk-hardcoded-key-here"  # Never do this!
    """)


def setup_walkthrough():
    """Interactive setup walkthrough."""
    print("\n🛠️ Setup Walkthrough")
    print("=" * 40)

    print("To set up your API keys, you have several options:")
    print("\n1. 📝 Create .env file manually:")
    print("   Create a file named '.env' in your project root:")
    print("""
   OPENAI_API_KEY=sk-your-openai-key-here
   ELEVENLABS_API_KEY=your-elevenlabs-key-here
   OPENWEATHERMAP_API_KEY=your-weather-key-here
   """)

    print("\n2. 🚀 Use the setup script:")
    print("   python setup_api_keys.py")

    print("\n3. 🔧 Use interactive setup:")

    try:
        response = input("\n   Would you like to run interactive setup now? (y/N): ").strip().lower()
        if response == 'y':
            setup_api_keys()
    except KeyboardInterrupt:
        print("\n   Setup cancelled.")


def main():
    """Run all examples."""
    print("🎯 FlexiAI API Key Management Examples")
    print("=" * 50)

    # Run all examples
    basic_usage_example()
    setting_keys_example()
    advanced_usage_example()
    real_world_integration_example()
    security_best_practices()
    setup_walkthrough()

    print("\n" + "=" * 50)
    print("🎉 Example completed!")
    print("\n💡 Next steps:")
    print("   1. Set up your API keys using setup_api_keys.py")
    print("   2. Use get_api_key() in your applications")
    print("   3. Follow security best practices")
    print("\n📚 For more information, see:")
    print("   • flexiai/config/api_keys.py - Full API documentation")
    print("   • setup_api_keys.py - Interactive setup script")


if __name__ == "__main__":
    main()
