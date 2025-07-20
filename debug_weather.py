#!/usr/bin/env python3
"""
Weather Tool Debug Script

This script tests the weather tool directly with full debug output
to help identify API issues, authentication problems, or other errors.
"""

import sys
import os
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent))

# Enable debug output BEFORE importing
os.environ['FLEXIAI_DEBUG'] = '1'

try:
    from flexiai.tools.weather import WeatherTool
    from flexiai.config.api_keys import get_api_key
except ImportError as e:
    print(f"❌ Error importing FlexiAI: {e}")
    print("Make sure you're running this script from the FlexiAI root directory.")
    sys.exit(1)


def print_header(title):
    """Print a debug section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)


def test_api_key():
    """Test API key availability and format."""
    print_header("API Key Debug")

    api_key = get_api_key('OPENWEATHERMAP_API_KEY')

    if api_key:
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"✅ API key found: {masked_key}")
        print(f"📏 Key length: {len(api_key)} characters")
        print(f"🔤 Key type: {type(api_key)}")
        print(f"🔍 Key format check:")
        print(f"   - Is alphanumeric: {api_key.isalnum()}")
        print(f"   - Has spaces: {' ' in api_key}")
        has_quotes = ('"' in api_key) or ("'" in api_key)
        print(f"   - Has quotes: {has_quotes}")

        # Check .env file format
        env_file = Path('.env')
        if env_file.exists():
            print(f"\n📁 Checking .env file format...")
            with open(env_file, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    if 'OPENWEATHERMAP_API_KEY' in line:
                        print(f"   Line {i}: {line.strip()}")

                        # Check for common formatting issues
                        if line.count('=') != 1:
                            print(f"   ⚠️ Multiple or missing '=' signs")

                        key_part = line.split('=', 1)[1].strip()
                        if key_part.startswith('"') or key_part.startswith("'"):
                            print(f"   ⚠️ Key appears to be quoted")

                        if len(key_part) != len(api_key):
                            print(f"   ⚠️ Length mismatch: .env has {len(key_part)}, loaded has {len(api_key)}")
    else:
        print("❌ No API key found!")
        print("\n💡 Troubleshooting steps:")
        print("1. Check if .env file exists")
        print("2. Verify OPENWEATHERMAP_API_KEY is set correctly")
        print("3. Make sure no extra spaces or quotes around the key")
        print("4. Get a new key from: https://openweathermap.org/api")

    return api_key


def test_direct_api_calls(api_key):
    """Test API calls directly without the tool wrapper."""
    print_header("Direct API Testing")

    if not api_key:
        print("❌ Skipping direct API tests - no API key")
        return

    import requests

    # Test 1: Basic connectivity
    print("🧪 Test 1: Basic API connectivity")
    try:
        response = requests.get("http://api.openweathermap.org", timeout=5)
        print(f"✅ OpenWeatherMap API reachable (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Cannot reach OpenWeatherMap API: {e}")
        return

    # Test 2: Geocoding API
    print("\n🧪 Test 2: Geocoding API")
    geocoding_url = "http://api.openweathermap.org/geo/1.0/direct"
    geocoding_params = {
        'q': 'London',
        'limit': 1,
        'appid': api_key
    }

    print(f"🔗 URL: {geocoding_url}")
    print(f"📝 Params: {geocoding_params}")

    try:
        response = requests.get(geocoding_url, params=geocoding_params, timeout=10)

        print(f"📊 Status: {response.status_code}")
        print(f"📄 Headers: {dict(response.headers)}")
        print(f"💾 Response: {response.text}")

        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"✅ Geocoding works! Found: {data[0].get('name')}, {data[0].get('country')}")
                return data[0]
            else:
                print("⚠️ Geocoding returned empty results")
        elif response.status_code == 401:
            print("❌ Geocoding failed: Invalid API key")
        else:
            print(f"❌ Geocoding failed with status {response.status_code}")

    except Exception as e:
        print(f"❌ Geocoding request failed: {e}")

    return None


def test_onecall_api(api_key, coords=None):
    """Test One Call API 3.0 directly."""
    print_header("One Call API 3.0 Testing")

    if not api_key:
        print("❌ Skipping One Call API tests - no API key")
        return

    if not coords:
        # Use London coordinates as fallback
        coords = {'lat': 51.5074, 'lon': -0.1278}
        print(f"⚠️ Using default coordinates: {coords}")

    import requests

    onecall_url = "https://api.openweathermap.org/data/3.0/onecall"
    onecall_params = {
        'lat': coords['lat'],
        'lon': coords['lon'],
        'appid': api_key,
        'units': 'metric',
        'exclude': 'minutely,alerts'
    }

    print(f"🔗 URL: {onecall_url}")
    print(f"📝 Params: {onecall_params}")

    try:
        response = requests.get(onecall_url, params=onecall_params, timeout=15)

        print(f"📊 Status: {response.status_code}")
        print(f"📄 Headers: {dict(response.headers)}")
        print(f"💾 Response: {response.text}")

        if response.status_code == 200:
            data = response.json()
            current = data.get('current', {})
            if current:
                temp = current.get('temp', 'N/A')
                condition = current.get('weather', [{}])[0].get('description', 'N/A')
                print(f"✅ One Call API works! Current: {temp}°C, {condition}")
            else:
                print("⚠️ One Call API returned data but no current weather")
        elif response.status_code == 401:
            print("❌ One Call API failed: Invalid API key or subscription required")
            print("💡 You may need to subscribe to One Call API 3.0 at:")
            print("   https://openweathermap.org/price")
        else:
            print(f"❌ One Call API failed with status {response.status_code}")

    except Exception as e:
        print(f"❌ One Call API request failed: {e}")


def test_weather_tool():
    """Test the weather tool directly."""
    print_header("Weather Tool Testing")

    print("🔧 Creating WeatherTool instance...")
    try:
        weather_tool = WeatherTool()
        print(f"✅ Weather tool created: {weather_tool.name} v{weather_tool.version}")
    except Exception as e:
        print(f"❌ Failed to create weather tool: {e}")
        return

    print("\n🧪 Testing weather tool execution with debug output...")
    print("Location: London")

    try:
        result = weather_tool.execute(location="London")

        print(f"\n📊 Tool Result:")
        print(f"   Success: {result.success}")
        print(f"   Error: {result.error}")
        print(f"   Metadata: {result.metadata}")

        if result.success and result.data:
            print(f"   Data keys: {list(result.data.keys()) if isinstance(result.data, dict) else 'Not a dict'}")

            if isinstance(result.data, dict):
                location_info = result.data.get('location', 'Unknown')
                current = result.data.get('current', {})
                if current:
                    temp = current.get('temperature', 'N/A')
                    condition = current.get('condition', 'N/A')
                    print(f"   Weather: {location_info} - {temp}, {condition}")

    except Exception as e:
        print(f"❌ Weather tool execution failed: {e}")
        import traceback
        print(f"🔍 Full traceback:")
        traceback.print_exc()


def main():
    """Main debug function."""
    print("🔍 FlexiAI Weather Tool Debug Script")
    print("=" * 60)
    print("This script will help identify weather API issues.")

    # Test API key
    api_key = test_api_key()

    # Test direct API calls
    coords = test_direct_api_calls(api_key)

    # Test One Call API
    test_onecall_api(api_key, coords)

    # Test weather tool
    test_weather_tool()

    # Final summary
    print_header("Debug Summary")

    has_api_key = api_key is not None
    print(f"🔑 API Key: {'✅ Found' if has_api_key else '❌ Missing'}")

    if has_api_key:
        print("\n💡 Next steps if weather still doesn't work:")
        print("1. Wait 10-15 minutes for new API keys to activate")
        print("2. Check your OpenWeatherMap account status")
        print("3. Verify One Call API 3.0 subscription")
        print("4. Try the weather tool again")
    else:
        print("\n💡 To fix the API key issue:")
        print("1. Get API key from: https://openweathermap.org/api")
        print("2. Add to .env file: OPENWEATHERMAP_API_KEY=your_key_here")
        print("3. Make sure no quotes or extra spaces")
        print("4. Run this script again to verify")

    print(f"\n🔗 Useful links:")
    print(f"   • Get API key: https://openweathermap.org/api")
    print(f"   • Account dashboard: https://home.openweathermap.org/")
    print(f"   • One Call API 3.0: https://openweathermap.org/api/one-call-3")
    print(f"   • Pricing: https://openweathermap.org/price")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Debug cancelled by user.")
    except Exception as e:
        print(f"\n❌ Debug script error: {e}")
        import traceback
        traceback.print_exc()
