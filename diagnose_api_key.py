#!/usr/bin/env python3
"""
OpenWeatherMap API Key Diagnostic Script

This script helps diagnose issues with OpenWeatherMap API keys,
especially for One Call API 3.0 subscription problems.
"""

import sys
import os
import requests
import json
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from flexiai.config.api_keys import get_api_key
except ImportError:
    print("❌ Could not import FlexiAI config. Running standalone diagnostics...")
    get_api_key = lambda key: os.getenv(key)


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)


def load_env_file():
    """Load .env file manually if needed."""
    env_path = Path('.env')
    if env_path.exists():
        print(f"📁 Loading .env file: {env_path.absolute()}")
        with open(env_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key == 'OPENWEATHERMAP_API_KEY':
                        print(f"✅ Found API key in .env file (line {line_num})")
                        if key not in os.environ:
                            os.environ[key] = value
                            print(f"🔄 Set environment variable from .env")
        return True
    else:
        print("❌ No .env file found")
        return False


def check_api_key_format():
    """Check API key format and basic validation."""
    print_section("API Key Format Check")

    # Try to get the API key
    api_key = get_api_key('OPENWEATHERMAP_API_KEY')

    if not api_key:
        print("❌ No OPENWEATHERMAP_API_KEY found!")
        print("\n💡 Possible solutions:")
        print("1. Check your .env file contains: OPENWEATHERMAP_API_KEY=your_key_here")
        print("2. Check environment variables: echo $OPENWEATHERMAP_API_KEY")
        print("3. Get a new key from: https://openweathermap.org/api")
        return None

    # Mask the key for security
    masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    print(f"✅ API key found: {masked_key}")
    print(f"🔍 Key length: {len(api_key)} characters")

    # Basic format validation
    if len(api_key) < 20:
        print("⚠️ API key seems too short for OpenWeatherMap")
    elif len(api_key) > 50:
        print("⚠️ API key seems too long for OpenWeatherMap")
    else:
        print("✅ API key length looks reasonable")

    # Check for common characters
    if api_key.isalnum():
        print("✅ API key contains only alphanumeric characters")
    else:
        print("⚠️ API key contains special characters (might be wrapped in quotes?)")

    return api_key


def test_current_weather_api(api_key):
    """Test the basic Current Weather API (free tier)."""
    print_section("Current Weather API Test (Free Tier)")

    try:
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': 'London',
            'appid': api_key,
            'units': 'metric'
        }

        print(f"🔍 Testing URL: {url}")
        print(f"🔍 Parameters: q=London, units=metric, appid={api_key[:8]}...")

        response = requests.get(url, params=params, timeout=10)

        print(f"📡 Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Current Weather API works!")
            print(f"📍 Location: {data.get('name')}, {data.get('sys', {}).get('country')}")
            print(f"🌡️ Temperature: {data.get('main', {}).get('temp')}°C")
            print(f"☁️ Condition: {data.get('weather', [{}])[0].get('description', 'N/A')}")
            return True
        elif response.status_code == 401:
            print("❌ Current Weather API: Invalid API key")
            try:
                error_data = response.json()
                print(f"📝 Error message: {error_data.get('message', 'No message')}")
            except:
                pass
            return False
        elif response.status_code == 429:
            print("❌ Current Weather API: Rate limit exceeded")
            return False
        else:
            print(f"❌ Current Weather API failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"📝 Error: {error_data}")
            except:
                print(f"📝 Raw response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False


def test_geocoding_api(api_key):
    """Test the Geocoding API (free)."""
    print_section("Geocoding API Test (Free)")

    try:
        url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {
            'q': 'London',
            'limit': 1,
            'appid': api_key
        }

        response = requests.get(url, params=params, timeout=10)
        print(f"📡 Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data:
                location = data[0]
                print("✅ Geocoding API works!")
                print(f"📍 Found: {location.get('name')}, {location.get('country')}")
                print(f"🗺️ Coordinates: {location.get('lat')}, {location.get('lon')}")
                return True, location
            else:
                print("⚠️ Geocoding API returned empty results")
                return False, None
        elif response.status_code == 401:
            print("❌ Geocoding API: Invalid API key")
            return False, None
        else:
            print(f"❌ Geocoding API failed with status {response.status_code}")
            return False, None

    except Exception as e:
        print(f"❌ Geocoding test error: {e}")
        return False, None


def test_onecall_api(api_key, lat=51.5074, lon=-0.1278):
    """Test the One Call API 3.0 (requires subscription)."""
    print_section("One Call API 3.0 Test (Paid Subscription)")

    try:
        url = "https://api.openweathermap.org/data/3.0/onecall"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': api_key,
            'units': 'metric',
            'exclude': 'minutely,alerts'  # Minimal request
        }

        print(f"🔍 Testing URL: {url}")
        print(f"🔍 Coordinates: {lat}, {lon}")

        response = requests.get(url, params=params, timeout=15)
        print(f"📡 Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ One Call API 3.0 works!")

            current = data.get('current', {})
            if current:
                print(f"🌡️ Current temp: {current.get('temp')}°C")
                print(f"☁️ Condition: {current.get('weather', [{}])[0].get('description', 'N/A')}")
                print(f"🌈 UV Index: {current.get('uvi', 'N/A')}")

            hourly = data.get('hourly', [])
            daily = data.get('daily', [])
            print(f"🕐 Hourly forecasts: {len(hourly)} hours")
            print(f"📅 Daily forecasts: {len(daily)} days")

            return True
        elif response.status_code == 401:
            print("❌ One Call API 3.0: Invalid API key or subscription required")
            try:
                error_data = response.json()
                print(f"📝 Error message: {error_data.get('message', 'No message')}")

                if 'subscription' in error_data.get('message', '').lower():
                    print("\n💡 This means:")
                    print("• Your API key is valid for basic APIs")
                    print("• But you need One Call API 3.0 subscription")
                    print("• Go to: https://openweathermap.org/price")
                    print("• Subscribe to 'One Call by Call' plan")

            except:
                pass
            return False
        elif response.status_code == 429:
            print("❌ One Call API 3.0: Rate limit exceeded")
            return False
        else:
            print(f"❌ One Call API 3.0 failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"📝 Error: {error_data}")
            except:
                print(f"📝 Raw response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ One Call API test error: {e}")
        return False


def check_subscription_status(api_key):
    """Try to determine subscription status."""
    print_section("Subscription Status Check")

    # Try to get current subscription info (this might not work directly)
    print("🔍 Attempting to determine your subscription level...")

    # Test different API endpoints to infer subscription
    current_works = test_current_weather_api(api_key)
    geocoding_works, coords = test_geocoding_api(api_key)

    if coords:
        onecall_works = test_onecall_api(api_key, coords['lat'], coords['lon'])
    else:
        onecall_works = test_onecall_api(api_key)  # Use default London coords

    print_section("Summary")

    print("📊 API Endpoint Test Results:")
    print(f"• Current Weather API (free): {'✅ Working' if current_works else '❌ Failed'}")
    print(f"• Geocoding API (free): {'✅ Working' if geocoding_works else '❌ Failed'}")
    print(f"• One Call API 3.0 (paid): {'✅ Working' if onecall_works else '❌ Failed'}")

    if current_works and not onecall_works:
        print("\n🎯 Diagnosis: Valid API key, but no One Call API 3.0 subscription")
        print("\n💡 To fix this:")
        print("1. Go to: https://openweathermap.org/api/pricing")
        print("2. Subscribe to 'One Call by Call' plan")
        print("3. The base plan includes 1,000 free calls/day")
        print("4. Wait a few minutes for subscription to activate")

    elif not current_works:
        print("\n🎯 Diagnosis: API key is invalid or expired")
        print("\n💡 To fix this:")
        print("1. Check your API key in your OpenWeatherMap account")
        print("2. Generate a new API key if needed")
        print("3. Update your .env file with the correct key")
        print("4. Make sure there are no extra spaces or quotes")

    elif current_works and onecall_works:
        print("\n🎯 Diagnosis: Everything working perfectly!")
        print("✅ You have a valid API key with One Call API 3.0 access")

    return current_works, onecall_works


def main():
    """Main diagnostic function."""
    print("🩺 OpenWeatherMap API Key Diagnostic Tool")
    print("=" * 60)
    print("This tool will help diagnose API key and subscription issues.")

    # Load .env file if present
    load_env_file()

    # Check API key format
    api_key = check_api_key_format()
    if not api_key:
        return

    # Test APIs and check subscription
    current_works, onecall_works = check_subscription_status(api_key)

    print_section("Recommendations")

    if onecall_works:
        print("🎉 Your setup is working perfectly!")
        print("You can use the enhanced weather function with One Call API 3.0")
    elif current_works:
        print("⚠️ Partial setup - basic weather works, but missing One Call API 3.0")
        print("You can use basic weather, but won't get forecasts and alerts")
    else:
        print("❌ API key issues detected")
        print("Please fix the API key before using weather functions")

    print(f"\n📚 Documentation:")
    print("• OpenWeatherMap API: https://openweathermap.org/api")
    print("• One Call API 3.0: https://openweathermap.org/api/one-call-3")
    print("• Pricing: https://openweathermap.org/price")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Diagnostic cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
