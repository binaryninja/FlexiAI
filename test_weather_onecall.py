#!/usr/bin/env python3
"""
Test script for OpenWeatherMap One Call API 3.0 integration.

This script tests the enhanced weather function with various locations
to demonstrate the rich data available from the One Call API 3.0.
"""

import sys
import json
import os
from pathlib import Path

# Add the package to the path so we can import from flexiai
sys.path.insert(0, str(Path(__file__).parent))

try:
    from flexiai.models.voxtral_model import VoxtralAssistantModel
    from flexiai.config.api_keys import get_api_key
    from flexiai.utils import debug_print
except ImportError as e:
    print(f"❌ Error importing FlexiAI: {e}")
    print("Make sure you're running this script from the FlexiAI root directory.")
    sys.exit(1)


def print_separator(title=""):
    """Print a nice separator for test sections."""
    print("\n" + "=" * 60)
    if title:
        print(f" {title}")
        print("=" * 60)


def format_weather_output(weather_json_str):
    """Format weather JSON for readable display."""
    try:
        data = json.loads(weather_json_str)

        print(f"📍 Location: {data.get('location', 'Unknown')}")

        # Current conditions
        current = data.get('current', {})
        if current:
            print(f"\n🌤️  Current Conditions:")
            print(f"   Temperature: {current.get('temperature', 'N/A')}")
            print(f"   Feels like: {current.get('feels_like', 'N/A')}")
            print(f"   Condition: {current.get('condition', 'N/A')}")
            print(f"   Humidity: {current.get('humidity', 'N/A')}")
            print(f"   Wind: {current.get('wind', 'N/A')}")
            print(f"   Pressure: {current.get('pressure', 'N/A')}")
            print(f"   UV Index: {current.get('uv_index', 'N/A')}")
            print(f"   Clouds: {current.get('clouds', 'N/A')}")
            print(f"   Visibility: {current.get('visibility', 'N/A')}")

        # Forecast
        forecast = data.get('forecast', {})
        if forecast:
            # Next 24 hours (show first 6 hours)
            next_24h = forecast.get('next_24h', [])
            if next_24h:
                print(f"\n🕐 Next 6 Hours:")
                for i, hour in enumerate(next_24h[:6]):
                    time_str = f"Hour {i+1}"
                    temp = hour.get('temperature', 'N/A')
                    condition = hour.get('condition', 'N/A')
                    precip = hour.get('precipitation_chance', 'N/A')
                    print(f"   {time_str}: {temp}, {condition}, Rain: {precip}")

            # Daily forecast
            next_days = forecast.get('next_7_days', [])
            if next_days:
                print(f"\n📅 5-Day Forecast:")
                for i, day in enumerate(next_days[:5]):
                    day_num = i + 1
                    condition = day.get('condition', 'N/A')
                    high = day.get('temperature_high', 'N/A')
                    low = day.get('temperature_low', 'N/A')
                    precip = day.get('precipitation_chance', 'N/A')
                    summary = day.get('summary', 'No summary')
                    print(f"   Day {day_num}: {high}/{low}, {condition}, Rain: {precip}")
                    if summary != 'No summary available':
                        print(f"          {summary}")

        # Alerts
        alerts = data.get('alerts', [])
        if alerts:
            print(f"\n⚠️  Weather Alerts:")
            for alert in alerts:
                event = alert.get('event', 'Weather Alert')
                sender = alert.get('sender', 'Weather Service')
                print(f"   🚨 {event} (from {sender})")
                description = alert.get('description', 'No description')
                # Truncate long descriptions
                if len(description) > 200:
                    description = description[:200] + "..."
                print(f"      {description}")
        else:
            print(f"\n✅ No weather alerts")

        # Summary
        summary = data.get('summary', '')
        if summary:
            print(f"\n📋 Summary: {summary}")

    except json.JSONDecodeError as e:
        print(f"❌ Error parsing weather data: {e}")
        print(f"Raw response: {weather_json_str}")
    except Exception as e:
        print(f"❌ Error formatting output: {e}")


def test_weather_locations():
    """Test weather function with various locations."""

    # Test locations with different formats
    test_locations = [
        "London",
        "New York, NY",
        "Tokyo, Japan",
        "Sydney, Australia",
        "51.5074,-0.1278",  # London coordinates
        "Invalid Location That Should Fail"
    ]

    print("🧪 Testing weather function with various locations...")

    # Create a minimal model instance just for testing the weather function
    try:
        model = VoxtralAssistantModel("dummy_model", "cpu")

        for i, location in enumerate(test_locations, 1):
            print_separator(f"Test {i}: {location}")

            try:
                weather_data = model._get_weather_info(location)
                print(f"✅ Successfully retrieved weather data for: {location}")
                format_weather_output(weather_data)

            except Exception as e:
                print(f"❌ Error testing location '{location}': {e}")

            # Add a small delay between requests to be nice to the API
            import time
            time.sleep(1)

    except Exception as e:
        print(f"❌ Error creating model instance: {e}")
        return


def check_api_setup():
    """Check if API key is properly configured."""
    print_separator("API Configuration Check")

    # Check if API key is available
    api_key = get_api_key('OPENWEATHERMAP_API_KEY')

    if not api_key:
        print("❌ No OpenWeatherMap API key found!")
        print("\n💡 To fix this:")
        print("1. Get your API key from: https://openweathermap.org/api")
        print("2. Add it to your .env file:")
        print("   OPENWEATHERMAP_API_KEY=your_api_key_here")
        print("3. Or run: python setup_api_keys.py")
        return False

    # Mask the key for security
    masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    print(f"✅ OpenWeatherMap API key found: {masked_key}")

    # Check if .env file exists
    env_file = Path('.env')
    if env_file.exists():
        print(f"✅ .env file found: {env_file.absolute()}")
    else:
        print("⚠️ No .env file found (using environment variables)")

    return True


def test_api_connectivity():
    """Test basic API connectivity."""
    print_separator("API Connectivity Test")

    try:
        import requests

        # Test basic connectivity to OpenWeatherMap
        test_url = "https://api.openweathermap.org"
        response = requests.get(test_url, timeout=10)
        print(f"✅ Successfully connected to OpenWeatherMap (Status: {response.status_code})")

        # Test geocoding API
        api_key = get_api_key('OPENWEATHERMAP_API_KEY')
        if api_key:
            geocoding_url = "http://api.openweathermap.org/geo/1.0/direct"
            params = {'q': 'London', 'limit': 1, 'appid': api_key}
            response = requests.get(geocoding_url, params=params, timeout=10)

            if response.status_code == 200:
                print(f"✅ Geocoding API working (Status: {response.status_code})")
            elif response.status_code == 401:
                print(f"❌ Invalid API key (Status: {response.status_code})")
                return False
            else:
                print(f"⚠️ Geocoding API issue (Status: {response.status_code})")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Network connectivity issue: {e}")
        return False
    except Exception as e:
        print(f"❌ Connectivity test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🌤️ OpenWeatherMap One Call API 3.0 Test Suite")
    print("=" * 60)

    # Enable debug output
    os.environ['FLEXIAI_DEBUG'] = '1'

    # Step 1: Check API setup
    if not check_api_setup():
        print("\n❌ API setup failed. Please configure your API key first.")
        return

    # Step 2: Test connectivity
    if not test_api_connectivity():
        print("\n❌ Connectivity test failed. Check your internet connection.")
        return

    # Step 3: Test weather locations
    test_weather_locations()

    # Final summary
    print_separator("Test Complete")
    print("🎉 Weather function testing completed!")
    print("\n💡 What to check:")
    print("✅ Current weather conditions")
    print("✅ 24-hour hourly forecast")
    print("✅ 5-day daily forecast")
    print("✅ Weather alerts (if any)")
    print("✅ Comprehensive weather summary")
    print("\n📊 Your One Call API 3.0 subscription provides:")
    print("• 1,000 free calls per day")
    print("• Current weather + forecasts")
    print("• Government weather alerts")
    print("• UV index and detailed conditions")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
