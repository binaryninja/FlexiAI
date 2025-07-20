#!/usr/bin/env python3
"""
Test script for function call parsing logic.

This script tests the function call detection and parsing methods
to ensure they correctly handle the JSON format returned by Voxtral.
"""

import sys
import json
from pathlib import Path

# Add FlexiAI to path
sys.path.insert(0, str(Path(__file__).parent))

from flexiai.models.voxtral_model import VoxtralAssistantModel

def test_function_call_detection():
    """Test the _contains_function_call method."""
    print("🧪 Testing function call detection...")

    # Create a model instance for testing (without loading)
    model = VoxtralAssistantModel("mistralai/Voxtral-Mini-3B-2507", "cpu")

    # Test cases for function call detection
    test_cases = [
        # Valid function calls
        ('[{"name": "get_weather", "arguments": {"location": "Oakville, Ontario"}}]', True),
        ('{"name": "get_weather", "arguments": {"location": "Toronto"}}', True),
        ('I need to get_weather for you', True),
        ('Let me call the function: [{"name": "get_weather", "arguments": {"location": "Vancouver"}}]', True),
        ('{"function": "get_weather"}', True),

        # Invalid/non-function responses
        ('The weather is nice today', False),
        ('Hello, how can I help you?', False),
        ('I can help you with weather information', False),
        ('', False),
    ]

    passed = 0
    total = len(test_cases)

    for response, expected in test_cases:
        result = model._contains_function_call(response)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{response[:50]}...' -> {result} (expected {expected})")
        if result == expected:
            passed += 1

    print(f"\n📊 Detection Test Results: {passed}/{total} passed")
    return passed == total

def test_function_call_parsing():
    """Test the _extract_function_call method."""
    print("\n🧪 Testing function call parsing...")

    # Create a model instance for testing
    model = VoxtralAssistantModel("mistralai/Voxtral-Mini-3B-2507", "cpu")

    # Test cases for function call parsing
    test_cases = [
        # JSON array format (Voxtral's preferred format)
        ('[{"name": "get_weather", "arguments": {"location": "Oakville, Ontario"}}]',
         {"name": "get_weather", "arguments": {"location": "Oakville, Ontario"}}),

        # Single JSON object format
        ('{"name": "get_weather", "arguments": {"location": "Toronto"}}',
         {"name": "get_weather", "arguments": {"location": "Toronto"}}),

        # JSON embedded in text
        ('I need to call [{"name": "get_weather", "arguments": {"location": "Vancouver"}}] for you.',
         {"name": "get_weather", "arguments": {"location": "Vancouver"}}),

        # Pattern matching fallback
        ('I need to get_weather for Oakville, Ontario',
         {"name": "get_weather", "arguments": {"location": "Oakville, Ontario"}}),

        # Location extraction from quotes
        ('get_weather with "location": "Calgary, Alberta"',
         {"name": "get_weather", "arguments": {"location": "Calgary, Alberta"}}),

        # Non-function response
        ('The weather is nice today', None),
    ]

    passed = 0
    total = len(test_cases)

    for response, expected in test_cases:
        result = model._extract_function_call(response)

        if expected is None:
            success = result is None
        else:
            success = (result is not None and
                      result.get("name") == expected.get("name") and
                      result.get("arguments") == expected.get("arguments"))

        status = "✅" if success else "❌"
        print(f"  {status} '{response[:50]}...'")
        print(f"      Result: {result}")
        print(f"      Expected: {expected}")

        if success:
            passed += 1

    print(f"\n📊 Parsing Test Results: {passed}/{total} passed")
    return passed == total

def test_weather_function():
    """Test the built-in weather function."""
    print("\n🧪 Testing weather function...")

    model = VoxtralAssistantModel("mistralai/Voxtral-Mini-3B-2507", "cpu")

    # Test the weather function directly
    locations = [
        "Oakville, Ontario",
        "Toronto, Canada",
        "Vancouver, BC",
        "Montreal, Quebec"
    ]

    passed = 0
    total = len(locations)

    for location in locations:
        try:
            result = model._get_weather_info(location)

            # Parse the JSON result
            weather_data = json.loads(result)

            # Check that required fields are present
            required_fields = ["location", "temperature", "condition", "humidity", "wind"]
            has_all_fields = all(field in weather_data for field in required_fields)

            status = "✅" if has_all_fields else "❌"
            print(f"  {status} {location}: {weather_data.get('temperature', 'N/A')}, {weather_data.get('condition', 'N/A')}")

            if has_all_fields:
                passed += 1

        except Exception as e:
            print(f"  ❌ {location}: Error - {e}")

    print(f"\n📊 Weather Function Test Results: {passed}/{total} passed")
    return passed == total

def test_end_to_end_parsing():
    """Test end-to-end parsing with realistic Voxtral responses."""
    print("\n🧪 Testing end-to-end parsing...")

    model = VoxtralAssistantModel("mistralai/Voxtral-Mini-3B-2507", "cpu")

    # Simulate the exact response format from Voxtral
    voxtral_response = '[{"name": "get_weather", "arguments": {"location": "Oakville, Ontario"}}]'

    print(f"Testing Voxtral response: {voxtral_response}")

    # Test detection
    contains_call = model._contains_function_call(voxtral_response)
    print(f"  Function call detected: {contains_call}")

    if contains_call:
        # Test extraction
        function_info = model._extract_function_call(voxtral_response)
        print(f"  Extracted function info: {function_info}")

        if function_info and function_info.get("name") == "get_weather":
            # Test execution
            location = function_info.get("arguments", {}).get("location")
            if location:
                weather_result = model._get_weather_info(location)
                print(f"  Weather result: {weather_result}")

                # Test natural response generation
                try:
                    weather_data = json.loads(weather_result)
                    temp = weather_data.get('temperature', 'unknown')
                    condition = weather_data.get('condition', 'unknown')
                    natural_response = f"The weather in {location} is currently {temp} and {condition.lower()}."
                    print(f"  Natural response: {natural_response}")
                    return True
                except:
                    print("  ❌ Failed to generate natural response")
                    return False

    print("  ❌ End-to-end test failed")
    return False

def main():
    """Run all tests."""
    print("🎯 Function Call Parsing Test Suite")
    print("=" * 50)

    tests = [
        ("Function Call Detection", test_function_call_detection),
        ("Function Call Parsing", test_function_call_parsing),
        ("Weather Function", test_weather_function),
        ("End-to-End Parsing", test_end_to_end_parsing),
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            success = test_func()
            if success:
                passed_tests += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n📊 Overall Results: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 All tests passed! Function call parsing should work correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
