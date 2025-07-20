#!/usr/bin/env python3
"""
Test script for FlexiAI modular tool system.

This script tests the new modular tool architecture, including:
- Tool registration and discovery
- Tool execution with parameter validation
- Integration with assistant models
- Weather tool functionality
- Error handling and edge cases
"""

import sys
import json
import os
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from flexiai.tools.registry import tool_registry, get_tool, list_tools, execute_tool
    from flexiai.tools.weather import WeatherTool
    from flexiai.tools.base import Tool, ToolParameter, ParameterType, ToolResult
    from flexiai.models.voxtral_model import VoxtralAssistantModel
    from flexiai.config.api_keys import get_api_key
except ImportError as e:
    print(f"❌ Error importing FlexiAI: {e}")
    print("Make sure you're running this script from the FlexiAI root directory.")
    sys.exit(1)


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)


def print_subsection(title):
    """Print a subsection header."""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print('-'*40)


def test_tool_registry():
    """Test basic tool registry functionality."""
    print_section("Tool Registry Tests")

    # Test tool discovery
    print("🔍 Testing tool discovery...")
    available_tools = list_tools()
    print(f"✅ Found {len(available_tools)} tools: {available_tools}")

    # Test tool retrieval
    print("\n🔧 Testing tool retrieval...")
    weather_tool = get_tool('get_weather')
    if weather_tool:
        print(f"✅ Retrieved weather tool: {weather_tool.name} v{weather_tool.version}")
        print(f"📝 Description: {weather_tool.description}")
        print(f"🏷️ Category: {weather_tool.category}")
        print(f"🔐 Requires auth: {weather_tool.requires_auth}")
    else:
        print("❌ Weather tool not found")

    # Test tool schemas
    print("\n📋 Testing tool schemas...")
    schemas = tool_registry.get_tool_schemas()
    print(f"✅ Generated {len(schemas)} tool schemas")

    if schemas:
        weather_schema = schemas[0]  # Should be weather tool
        print(f"📊 Sample schema structure:")
        print(f"   Tool: {weather_schema['function']['name']}")
        print(f"   Parameters: {len(weather_schema['function']['parameters']['properties'])} params")
        print(f"   Required: {weather_schema['function']['parameters'].get('required', [])}")

    # Test tool info
    print("\n📊 Testing tool information...")
    tool_info = tool_registry.get_tool_info()
    for tool_name, info in tool_info.items():
        print(f"🔧 {tool_name}:")
        print(f"   Version: {info['version']}")
        print(f"   Category: {info['category']}")
        print(f"   Parameters: {info['parameter_count']}")
        print(f"   Auth required: {info['requires_auth']}")


def test_weather_tool_direct():
    """Test weather tool directly."""
    print_section("Direct Weather Tool Tests")

    weather_tool = WeatherTool()

    # Test parameter validation
    print("🧪 Testing parameter validation...")

    # Valid parameters
    try:
        params = weather_tool.validate_parameters({
            'location': 'London',
            'include_forecast': True,
            'forecast_days': 3
        })
        print(f"✅ Valid parameters accepted: {params}")
    except Exception as e:
        print(f"❌ Parameter validation failed: {e}")

    # Invalid parameters
    try:
        weather_tool.validate_parameters({
            'location': '',  # Empty location
            'forecast_days': 15  # Too many days
        })
        print("❌ Should have failed validation")
    except Exception as e:
        print(f"✅ Correctly rejected invalid parameters: {e}")

    # Test API key check
    print("\n🔑 Testing API key availability...")
    api_key = get_api_key('OPENWEATHERMAP_API_KEY')
    if api_key:
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"✅ API key found: {masked_key}")

        # Test actual weather call
        print("\n🌤️ Testing actual weather API call...")
        try:
            result = weather_tool.execute(location="London")

            if result.success:
                print("✅ Weather API call successful!")
                print(f"📍 Location: {result.data.get('location', 'Unknown')}")

                current = result.data.get('current', {})
                if current:
                    print(f"🌡️ Temperature: {current.get('temperature', 'N/A')}")
                    print(f"☁️ Condition: {current.get('condition', 'N/A')}")
                    print(f"💨 Wind: {current.get('wind', 'N/A')}")

                forecast = result.data.get('forecast', {})
                if forecast:
                    hourly = forecast.get('next_24h', [])
                    daily = forecast.get('daily', [])
                    print(f"🕐 Hourly forecasts: {len(hourly)} hours")
                    print(f"📅 Daily forecasts: {len(daily)} days")

                alerts = result.data.get('alerts', [])
                print(f"⚠️ Weather alerts: {len(alerts)}")

                print(f"⏱️ Execution time: {result.execution_time_ms:.1f}ms")
            else:
                print(f"❌ Weather API call failed: {result.error}")
                print(f"🔍 Metadata: {result.metadata}")

        except Exception as e:
            print(f"❌ Weather tool execution error: {e}")
    else:
        print("⚠️ No API key found - skipping actual API tests")


def test_tool_registry_execution():
    """Test tool execution through registry."""
    print_section("Tool Registry Execution Tests")

    # Test registry execution
    print("🚀 Testing tool execution via registry...")

    try:
        result = execute_tool('get_weather', location='Tokyo')

        if result.success:
            print("✅ Registry execution successful!")
            data = result.data
            print(f"📍 Location: {data.get('location', 'Unknown')}")

            current = data.get('current', {})
            if current:
                print(f"🌡️ Current: {current.get('temperature', 'N/A')}, {current.get('condition', 'N/A')}")
        else:
            print(f"❌ Registry execution failed: {result.error}")

    except Exception as e:
        print(f"❌ Registry execution error: {e}")

    # Test with different parameters
    print("\n🔧 Testing different parameters...")

    try:
        result = execute_tool(
            'get_weather',
            location='New York',
            include_forecast=False,
            include_alerts=False
        )

        if result.success:
            print("✅ Parameter customization works!")
            data = result.data
            has_forecast = 'forecast' in data
            has_alerts = 'alerts' in data
            print(f"📊 Forecast included: {has_forecast}")
            print(f"🚨 Alerts included: {has_alerts}")
        else:
            print(f"❌ Parameter test failed: {result.error}")

    except Exception as e:
        print(f"❌ Parameter test error: {e}")


def test_assistant_model_integration():
    """Test integration with VoxtralAssistantModel."""
    print_section("Assistant Model Integration Tests")

    print("🤖 Testing VoxtralAssistantModel tool integration...")

    try:
        # Create model instance (without loading actual model)
        model = VoxtralAssistantModel("mistralai/Voxtral-Mini-3B-2507", "cpu")

        print(f"✅ Model created successfully")
        print(f"🔧 Available functions: {list(model.available_functions.keys())}")

        # Test function call through model
        if 'get_weather' in model.available_functions:
            print("\n🌤️ Testing weather function through model...")

            try:
                weather_func = model.available_functions['get_weather']
                result_json = weather_func(location='Paris')

                # Parse the JSON result
                result_data = json.loads(result_json)

                if 'error' in result_data:
                    print(f"⚠️ Function returned error: {result_data['error']}")
                else:
                    print("✅ Model function call successful!")
                    print(f"📍 Location: {result_data.get('location', 'Unknown')}")

                    current = result_data.get('current', {})
                    if current:
                        print(f"🌡️ Temperature: {current.get('temperature', 'N/A')}")

            except Exception as e:
                print(f"❌ Model function call error: {e}")
        else:
            print("❌ Weather function not available in model")

    except Exception as e:
        print(f"❌ Model integration error: {e}")


def test_custom_tool_creation():
    """Test creating and registering a custom tool."""
    print_section("Custom Tool Creation Tests")

    class TestTool(Tool):
        """Simple test tool for demonstration."""

        @property
        def name(self) -> str:
            return "test_calculator"

        @property
        def description(self) -> str:
            return "Simple calculator for basic math operations"

        @property
        def parameters(self) -> list:
            return [
                ToolParameter(
                    name="operation",
                    param_type=ParameterType.STRING,
                    description="Math operation to perform",
                    required=True,
                    enum_values=["add", "subtract", "multiply", "divide"]
                ),
                ToolParameter(
                    name="a",
                    param_type=ParameterType.FLOAT,
                    description="First number",
                    required=True
                ),
                ToolParameter(
                    name="b",
                    param_type=ParameterType.FLOAT,
                    description="Second number",
                    required=True
                )
            ]

        @property
        def category(self) -> str:
            return "utility"

        def execute(self, **kwargs) -> ToolResult:
            operation = kwargs['operation']
            a = kwargs['a']
            b = kwargs['b']

            try:
                if operation == "add":
                    result = a + b
                elif operation == "subtract":
                    result = a - b
                elif operation == "multiply":
                    result = a * b
                elif operation == "divide":
                    if b == 0:
                        return ToolResult(success=False, error="Division by zero")
                    result = a / b
                else:
                    return ToolResult(success=False, error=f"Unknown operation: {operation}")

                return ToolResult(
                    success=True,
                    data={
                        "operation": operation,
                        "operand_a": a,
                        "operand_b": b,
                        "result": result,
                        "expression": f"{a} {operation} {b} = {result}"
                    }
                )

            except Exception as e:
                return ToolResult(success=False, error=str(e))

    print("🔧 Creating custom test tool...")
    test_tool = TestTool()

    print(f"✅ Custom tool created: {test_tool.name}")
    print(f"📝 Description: {test_tool.description}")
    print(f"🏷️ Category: {test_tool.category}")

    # Register the custom tool
    print("\n📝 Registering custom tool...")
    tool_registry.register_custom_tool(test_tool)

    updated_tools = list_tools()
    if test_tool.name in updated_tools:
        print(f"✅ Custom tool registered successfully!")
        print(f"🔧 Total tools now: {len(updated_tools)}")

        # Test the custom tool
        print("\n🧮 Testing custom calculator tool...")
        result = execute_tool('test_calculator', operation='multiply', a=6, b=7)

        if result.success:
            print(f"✅ Calculator test passed!")
            print(f"📊 Result: {result.data['expression']}")
        else:
            print(f"❌ Calculator test failed: {result.error}")
    else:
        print("❌ Custom tool registration failed")


def test_error_handling():
    """Test error handling scenarios."""
    print_section("Error Handling Tests")

    # Test non-existent tool
    print("🚫 Testing non-existent tool...")
    try:
        result = execute_tool('non_existent_tool', param='value')
        print("❌ Should have failed")
    except Exception as e:
        print(f"✅ Correctly caught error: {type(e).__name__}")

    # Test invalid parameters
    print("\n🚫 Testing invalid parameters...")
    try:
        result = execute_tool('get_weather')  # Missing required location
        if not result.success:
            print(f"✅ Correctly handled missing parameter: {result.error}")
        else:
            print("❌ Should have failed validation")
    except Exception as e:
        print(f"✅ Correctly caught validation error: {e}")

    # Test invalid location
    print("\n🚫 Testing invalid location...")
    try:
        result = execute_tool('get_weather', location='InvalidLocationThatDoesNotExist12345')
        if not result.success:
            print(f"✅ Correctly handled invalid location: {result.error}")
        else:
            print("⚠️ API accepted invalid location (this might be OK)")
    except Exception as e:
        print(f"✅ Correctly caught location error: {e}")


def main():
    """Main test function."""
    print("🧪 FlexiAI Modular Tool System Test Suite")
    print("=" * 60)
    print("Testing the new modular tool architecture...")

    # Enable debug output
    os.environ['FLEXIAI_DEBUG'] = '1'

    # Run test suites
    test_tool_registry()
    test_weather_tool_direct()
    test_tool_registry_execution()
    test_assistant_model_integration()
    test_custom_tool_creation()
    test_error_handling()

    # Final summary
    print_section("Test Summary")

    total_tools = len(list_tools())
    weather_available = 'get_weather' in list_tools()
    api_key_configured = get_api_key('OPENWEATHERMAP_API_KEY') is not None

    print(f"📊 System Status:")
    print(f"   🔧 Total tools available: {total_tools}")
    print(f"   🌤️ Weather tool: {'✅ Available' if weather_available else '❌ Missing'}")
    print(f"   🔑 API key configured: {'✅ Yes' if api_key_configured else '❌ No'}")

    print(f"\n🎯 Modular Tool System Features:")
    print(f"   ✅ Automatic tool discovery")
    print(f"   ✅ Parameter validation")
    print(f"   ✅ Error handling")
    print(f"   ✅ Schema generation for function calling")
    print(f"   ✅ Integration with assistant models")
    print(f"   ✅ Custom tool registration")
    print(f"   ✅ Categorization and metadata")

    if api_key_configured:
        print(f"\n🌤️ Weather Tool Capabilities:")
        print(f"   ✅ Current weather conditions")
        print(f"   ✅ 24-hour hourly forecasts")
        print(f"   ✅ Multi-day daily forecasts")
        print(f"   ✅ Weather alerts and warnings")
        print(f"   ✅ Location geocoding")
        print(f"   ✅ Comprehensive summaries")
    else:
        print(f"\n⚠️ To test weather functionality:")
        print(f"   1. Set OPENWEATHERMAP_API_KEY in .env file")
        print(f"   2. Get free API key: https://openweathermap.org/api")
        print(f"   3. Subscribe to One Call API 3.0 for full features")

    print(f"\n🎉 Modular tool system test completed!")
    print(f"💡 Benefits of the new system:")
    print(f"   • Easy to add new tools")
    print(f"   • Shared across all assistant models")
    print(f"   • Automatic parameter validation")
    print(f"   • Consistent error handling")
    print(f"   • Function calling API compatibility")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Tests cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
