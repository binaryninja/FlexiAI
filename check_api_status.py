#!/usr/bin/env python3
"""
Simple OpenWeatherMap API Key Status Checker

This script checks your current API key status and tells you exactly what to do.
"""

import os
import sys
import requests
from pathlib import Path


def load_env_file():
    """Load API key from .env file."""
    env_file = Path('.env')
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('OPENWEATHERMAP_API_KEY='):
                        key = line.split('=', 1)[1].strip().strip('"').strip("'")
                        os.environ['OPENWEATHERMAP_API_KEY'] = key
                        return key
        except Exception as e:
            print(f"Error reading .env file: {e}")
    return None


def check_api_key():
    """Check API key status."""
    print("🌤️ OpenWeatherMap API Key Status Check")
    print("=" * 50)

    # Get API key
    api_key = os.getenv('OPENWEATHERMAP_API_KEY')
    if not api_key:
        api_key = load_env_file()

    if not api_key:
        print("❌ No API key found!")
        print("\n💡 Next steps:")
        print("1. Get API key from: https://openweathermap.org/api")
        print("2. Add to .env file: OPENWEATHERMAP_API_KEY=your_key_here")
        return

    # Mask key for display
    masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    print(f"🔍 Testing API key: {masked}")
    print(f"📏 Key length: {len(api_key)} characters")

    # Test basic weather API
    try:
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': 'London',
            'appid': api_key,
            'units': 'metric'
        }

        print("\n🧪 Testing basic weather API...")
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            location = f"{data['name']}, {data['sys']['country']}"
            temp = data['main']['temp']
            print(f"✅ SUCCESS! Weather in {location}: {temp}°C")

            # Test One Call API 3.0
            print("\n🧪 Testing One Call API 3.0...")
            onecall_url = "https://api.openweathermap.org/data/3.0/onecall"
            onecall_params = {
                'lat': 51.5074,
                'lon': -0.1278,
                'appid': api_key,
                'units': 'metric',
                'exclude': 'minutely,alerts'
            }

            onecall_response = requests.get(onecall_url, params=onecall_params, timeout=15)

            if onecall_response.status_code == 200:
                print("✅ SUCCESS! One Call API 3.0 is working!")
                print("\n🎉 YOUR SETUP IS PERFECT!")
                print("✅ Basic weather: Working")
                print("✅ Forecasts & alerts: Working")
                print("✅ You have One Call API 3.0 subscription")
            elif onecall_response.status_code == 401:
                error_data = onecall_response.json()
                message = error_data.get('message', '')
                if 'subscription' in message.lower():
                    print("⚠️ One Call API 3.0 not subscribed")
                    print("\n📊 CURRENT STATUS:")
                    print("✅ Basic weather: Working")
                    print("❌ Forecasts & alerts: Need subscription")
                    print("\n💡 TO GET FORECASTS:")
                    print("1. Go to: https://openweathermap.org/price")
                    print("2. Subscribe to 'One Call by Call' (1,000 free calls/day)")
                    print("3. Wait a few minutes for activation")
                else:
                    print(f"❌ One Call API error: {message}")
            else:
                print(f"❌ One Call API error: HTTP {onecall_response.status_code}")

        elif response.status_code == 401:
            error_data = response.json()
            message = error_data.get('message', 'Invalid API key')
            print(f"❌ INVALID API KEY: {message}")
            print("\n🔧 POSSIBLE FIXES:")
            print("1. Check your API key at: https://home.openweathermap.org/api_keys")
            print("2. Generate a new API key if needed")
            print("3. Wait 10-15 minutes for new keys to activate")
            print("4. Update your .env file with the correct key")
            print("5. Make sure no extra spaces/quotes in .env file")

        elif response.status_code == 429:
            print("❌ RATE LIMIT EXCEEDED")
            print("Your API key is valid but you've made too many requests")
            print("Wait a bit and try again")

        else:
            print(f"❌ API ERROR: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
        print("Check your internet connection")

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")


def main():
    """Main function."""
    check_api_key()

    print("\n" + "=" * 50)
    print("📚 HELPFUL LINKS:")
    print("• Get API key: https://openweathermap.org/api")
    print("• Account dashboard: https://home.openweathermap.org/")
    print("• One Call API 3.0: https://openweathermap.org/api/one-call-3")
    print("• Pricing: https://openweathermap.org/price")


if __name__ == "__main__":
    main()
