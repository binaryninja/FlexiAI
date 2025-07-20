#!/usr/bin/env python3
"""
OpenWeatherMap API Key Verification and Setup Helper

This script helps you verify and set up your OpenWeatherMap API key
for use with FlexiAI weather functions, including One Call API 3.0.
"""

import os
import sys
import requests
import json
from pathlib import Path


def print_header():
    """Print welcome header."""
    print("🌤️  OpenWeatherMap API Setup Helper")
    print("=" * 50)
    print("This tool will help you set up your weather API key")
    print()


def get_current_api_key():
    """Get the current API key from environment or .env file."""
    # First check environment variable
    api_key = os.getenv('OPENWEATHERMAP_API_KEY')
    if api_key:
        return api_key, 'environment'

    # Then check .env file
    env_file = Path('.env')
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('OPENWEATHERMAP_API_KEY='):
                        key = line.split('=', 1)[1].strip().strip('"').strip("'")
                        return key, '.env file'
        except Exception as e:
            print(f"⚠️ Error reading .env file: {e}")

    return None, None


def validate_api_key_format(api_key):
    """Validate API key format."""
    if not api_key:
        return False, "API key is empty"

    if len(api_key) != 32:
        return False, f"API key should be 32 characters, got {len(api_key)}"

    if not api_key.isalnum():
        return False, "API key should contain only letters and numbers"

    return True, "API key format looks correct"


def test_api_key(api_key):
    """Test if API key works with OpenWeatherMap."""
    try:
        # Test basic weather API
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': 'London',
            'appid': api_key,
            'units': 'metric'
        }

        print("🔍 Testing API key with basic weather endpoint...")
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            location = f"{data['name']}, {data['sys']['country']}"
            temp = data['main']['temp']
            print(f"✅ Basic API works! Current weather in {location}: {temp}°C")
            return True, "basic"
        elif response.status_code == 401:
            error_data = response.json()
            return False, f"Invalid API key: {error_data.get('message', 'Unknown error')}"
        elif response.status_code == 429:
            return False, "Rate limit exceeded - try again later"
        else:
            return False, f"API error: HTTP {response.status_code}"

    except requests.RequestException as e:
        return False, f"Network error: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def test_onecall_api(api_key):
    """Test One Call API 3.0 subscription."""
    try:
        url = "https://api.openweathermap.org/data/3.0/onecall"
        params = {
            'lat': 51.5074,  # London
            'lon': -0.1278,
            'appid': api_key,
            'units': 'metric',
            'exclude': 'minutely,alerts'
        }

        print("🔍 Testing One Call API 3.0 subscription...")
        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            current_temp = data.get('current', {}).get('temp', 'N/A')
            hourly_count = len(data.get('hourly', []))
            daily_count = len(data.get('daily', []))
            print(f"✅ One Call API 3.0 works! Current: {current_temp}°C")
            print(f"📊 Available: {hourly_count} hourly + {daily_count} daily forecasts")
            return True
        elif response.status_code == 401:
            error_data = response.json()
            message = error_data.get('message', '')
            if 'subscription' in message.lower():
                print("⚠️ Valid API key but no One Call API 3.0 subscription")
                print("💡 You need to subscribe to One Call API 3.0")
                return False
            else:
                print(f"❌ API key error: {message}")
                return False
        else:
            print(f"❌ One Call API error: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ One Call API test failed: {e}")
        return False


def update_env_file(api_key):
    """Update or create .env file with API key."""
    env_file = Path('.env')

    # Read existing .env content
    existing_lines = []
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                existing_lines = f.readlines()
        except Exception as e:
            print(f"⚠️ Error reading existing .env file: {e}")

    # Update or add the API key line
    updated = False
    new_lines = []

    for line in existing_lines:
        if line.strip().startswith('OPENWEATHERMAP_API_KEY='):
            new_lines.append(f'OPENWEATHERMAP_API_KEY={api_key}\n')
            updated = True
        else:
            new_lines.append(line)

    # Add API key if not found
    if not updated:
        new_lines.append(f'OPENWEATHERMAP_API_KEY={api_key}\n')

    # Write updated .env file
    try:
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
        print(f"✅ Updated .env file: {env_file.absolute()}")
        return True
    except Exception as e:
        print(f"❌ Error writing .env file: {e}")
        return False


def show_instructions():
    """Show instructions for getting API key."""
    print("\n📋 How to get your OpenWeatherMap API key:")
    print()
    print("1. 🌐 Go to: https://openweathermap.org/api")
    print("2. 📝 Sign up for a free account (if you don't have one)")
    print("3. 🔑 Go to your account dashboard > API keys")
    print("4. 📋 Copy your API key (32-character string)")
    print("5. ⏰ Wait 10-15 minutes for the key to activate")
    print()
    print("📋 For One Call API 3.0 (forecasts and alerts):")
    print()
    print("1. 💳 Go to: https://openweathermap.org/price")
    print("2. 🎯 Find 'One Call by Call' subscription")
    print("3. 📊 Subscribe to Base plan (1,000 free calls/day)")
    print("4. ⏰ Wait a few minutes for subscription to activate")
    print()


def interactive_setup():
    """Interactive API key setup."""
    print("\n🔧 Interactive API Key Setup")
    print("-" * 30)

    while True:
        try:
            api_key = input("\n📝 Enter your OpenWeatherMap API key: ").strip()

            if not api_key:
                print("❌ Empty API key. Please try again.")
                continue

            # Validate format
            valid, message = validate_api_key_format(api_key)
            if not valid:
                print(f"❌ {message}")
                retry = input("🔄 Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    return False
                continue

            print(f"✅ {message}")

            # Test the key
            works, result = test_api_key(api_key)
            if not works:
                print(f"❌ API key test failed: {result}")
                print("\n💡 Common issues:")
                print("• Key might need 10-15 minutes to activate")
                print("• Check for typos in the key")
                print("• Verify your OpenWeatherMap account is active")

                retry = input("🔄 Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    return False
                continue

            print(f"✅ API key works for basic weather!")

            # Test One Call API
            onecall_works = test_onecall_api(api_key)

            # Save to .env file
            save = input("\n💾 Save API key to .env file? (y/n): ").strip().lower()
            if save == 'y':
                if update_env_file(api_key):
                    print("✅ API key saved successfully!")
                else:
                    print("❌ Failed to save API key")

            return True

        except KeyboardInterrupt:
            print("\n\n👋 Setup cancelled.")
            return False
        except Exception as e:
            print(f"\n❌ Error during setup: {e}")
            return False


def main():
    """Main function."""
    print_header()

    # Check current API key
    current_key, source = get_current_api_key()

    if current_key:
        masked_key = current_key[:8] + "..." + current_key[-4:]
        print(f"🔍 Found existing API key from {source}: {masked_key}")

        # Validate format
        valid, message = validate_api_key_format(current_key)
        print(f"📋 Format check: {message}")

        if valid:
            # Test the key
            works, result = test_api_key(current_key)
            if works:
                print("✅ Your current API key works for basic weather!")

                # Test One Call API
                onecall_works = test_onecall_api(current_key)

                if onecall_works:
                    print("\n🎉 Perfect! Your setup is complete!")
                    print("✅ Basic weather API: Working")
                    print("✅ One Call API 3.0: Working")
                    print("\nYou can now use all weather features including:")
                    print("• Current weather conditions")
                    print("• 24-hour hourly forecasts")
                    print("• 5-day daily forecasts")
                    print("• Weather alerts")
                    print("• UV index and detailed data")
                    return
                else:
                    print("\n⚠️ Partial setup detected:")
                    print("✅ Basic weather API: Working")
                    print("❌ One Call API 3.0: Not subscribed")
                    print("\n💡 To get forecasts and alerts, subscribe to One Call API 3.0")

                    show_subscription_info = input("📚 Show subscription instructions? (y/n): ").strip().lower()
                    if show_subscription_info == 'y':
                        show_instructions()
                    return
            else:
                print(f"❌ Your current API key has issues: {result}")
        else:
            print("❌ Your current API key has format issues")

        # Ask if user wants to update
        update = input("\n🔄 Would you like to enter a new API key? (y/n): ").strip().lower()
        if update != 'y':
            return
    else:
        print("❌ No API key found")
        print("\n💡 You need to set up your OpenWeatherMap API key")

    # Show instructions
    show_instructions()

    # Interactive setup
    setup = input("\n🚀 Ready to enter your API key? (y/n): ").strip().lower()
    if setup == 'y':
        success = interactive_setup()
        if success:
            print("\n🎉 Setup completed! You can now use weather functions.")
        else:
            print("\n😔 Setup incomplete. You can run this script again anytime.")
    else:
        print("\n👋 No problem! Run this script again when you're ready.")
        print("Remember to get your API key from: https://openweathermap.org/api")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
