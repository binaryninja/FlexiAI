#!/usr/bin/env python3
"""
FlexiAI Tools Demo Script

This script demonstrates the modular tool system in FlexiAI, showing how to:
- Use built-in tools like weather
- Create custom tools
- Execute tools with parameter validation
- Handle errors gracefully
- Integrate tools with assistant models

Run this script to see the tool system in action!
"""

import sys
import json
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent))

from flexiai.tools.registry import tool_registry, get_tool, list_tools, execute_tool
from flexiai.tools.base import Tool, ToolParameter, ParameterType, ToolResult
from flexiai.config.api_keys import get_api_key


def demo_header(title):
    """Print a demo section header."""
    print(f"\n{'🎯 ' + title}")
    print('=' * (len(title) + 3))


def demo_basic_usage():
    """Demonstrate basic tool usage."""
    demo_header("Basic Tool Usage")

    print("📋 Available tools:")
    tools = list_tools()
    for tool_name in tools:
        tool = get_tool(tool_name)
        print(f"   • {tool_name} - {tool.description}")

    print(f"\n🔧 Total tools available: {len(tools)}")


def demo_weather_tool():
    """Demonstrate the weather tool."""
    demo_header("Weather Tool Demo")

    # Check if API key is available
    api_key = get_api_key('OPENWEATHERMAP_API_KEY')
    if not api_key:
        print("⚠️ No OpenWeatherMap API key found!")
        print("💡 To test weather functionality:")
        print("   1. Get a free API key: https://openweathermap.org/api")
        print("   2. Add to .env file: OPENWEATHERMAP_API_KEY=your_key_here")
        print("   3. For full features, subscribe to One Call API 3.0")
        return

    print(f"🔑 API key configured (length: {len(api_key)} chars)")

    # Demo weather tool with different parameters
    test_locations = ["London", "New York", "Tokyo"]

    for location in test_locations:
        print(f"\n🌤️ Getting weather for {location}...")

        try:
            # Execute weather tool
            result = execute_tool('get_weather', location=location)

            if result.success:
                data = result.data
                print(f"✅ Success! Location: {data.get('location', 'Unknown')}")

                current = data.get('current', {})
                if current:
                    temp = current.get('temperature', 'N/A')
                    condition = current.get('condition', 'N/A')
                    print(f"   Temperature: {temp}")
                    print(f"   Condition: {condition}")

                # Show forecast info
                forecast = data.get('forecast', {})
                if forecast:
                    daily = forecast.get('daily', [])
                    if daily:
                        print(f"   📅 {len(daily)}-day forecast available")

                print(f"   ⏱️ Response time: {result.execution_time_ms:.1f}ms")
            else:
                print(f"❌ Failed: {result.error}")

        except Exception as e:
            print(f"❌ Error: {e}")


def demo_custom_tool():
    """Demonstrate creating and using a custom tool."""
    demo_header("Custom Tool Demo")

    print("🛠️ Creating a custom 'text_analyzer' tool...")

    class TextAnalyzerTool(Tool):
        """Analyzes text and provides statistics."""

        @property
        def name(self) -> str:
            return "text_analyzer"

        @property
        def description(self) -> str:
            return "Analyze text and provide detailed statistics including word count, character count, and readability"

        @property
        def parameters(self):
            return [
                ToolParameter(
                    name="text",
                    param_type=ParameterType.STRING,
                    description="Text to analyze",
                    required=True,
                    min_length=1,
                    max_length=10000
                ),
                ToolParameter(
                    name="include_details",
                    param_type=ParameterType.BOOLEAN,
                    description="Include detailed analysis (sentences, paragraphs, etc.)",
                    required=False,
                    default=True
                )
            ]

        @property
        def category(self) -> str:
            return "text"

        def execute(self, **kwargs) -> ToolResult:
            text = kwargs['text']
            include_details = kwargs.get('include_details', True)

            # Basic analysis
            words = text.split()
            chars = len(text)
            chars_no_spaces = len(text.replace(' ', ''))

            result_data = {
                "text_length": chars,
                "character_count": chars,
                "character_count_no_spaces": chars_no_spaces,
                "word_count": len(words),
                "average_word_length": round(sum(len(word) for word in words) / len(words), 2) if words else 0
            }

            if include_details:
                sentences = text.split('.')
                paragraphs = text.split('\n\n')

                result_data.update({
                    "sentence_count": len([s for s in sentences if s.strip()]),
                    "paragraph_count": len([p for p in paragraphs if p.strip()]),
                    "longest_word": max(words, key=len) if words else "",
                    "shortest_word": min(words, key=len) if words else "",
                    "readability_score": min(100, max(0, 100 - len(words) / 10))  # Simple readability
                })

            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "analysis_type": "detailed" if include_details else "basic",
                    "text_preview": text[:50] + "..." if len(text) > 50 else text
                }
            )

    # Create and register the custom tool
    analyzer_tool = TextAnalyzerTool()
    tool_registry.register_custom_tool(analyzer_tool)

    print(f"✅ Custom tool '{analyzer_tool.name}' registered!")
    print(f"📝 Description: {analyzer_tool.description}")

    # Test the custom tool
    sample_text = """
    FlexiAI is a powerful modular AI assistant framework.
    It provides tools for weather information, text analysis, and much more.
    The modular design makes it easy to add new capabilities.
    """

    print(f"\n📊 Analyzing sample text...")
    print(f"Text preview: '{sample_text.strip()[:60]}...'")

    try:
        result = execute_tool('text_analyzer', text=sample_text.strip())

        if result.success:
            data = result.data
            print("✅ Analysis complete!")
            print(f"   📏 Length: {data['character_count']} characters")
            print(f"   📝 Words: {data['word_count']}")
            print(f"   📋 Sentences: {data.get('sentence_count', 'N/A')}")
            print(f"   📖 Avg word length: {data['average_word_length']}")
            print(f"   🎯 Readability score: {data.get('readability_score', 'N/A')}/100")
            print(f"   📚 Longest word: '{data.get('longest_word', 'N/A')}'")
        else:
            print(f"❌ Analysis failed: {result.error}")

    except Exception as e:
        print(f"❌ Error: {e}")


def demo_parameter_validation():
    """Demonstrate parameter validation."""
    demo_header("Parameter Validation Demo")

    print("🔍 Testing parameter validation with weather tool...")

    # Test valid parameters
    print("\n✅ Valid parameters:")
    try:
        result = execute_tool(
            'get_weather',
            location='London',
            include_forecast=True,
            forecast_days=3
        )
        print(f"   Parameters accepted and executed")
    except Exception as e:
        print(f"   Error: {e}")

    # Test invalid parameters
    print("\n❌ Invalid parameters:")

    test_cases = [
        {
            "name": "Missing required parameter",
            "params": {"include_forecast": True},  # Missing location
        },
        {
            "name": "Invalid forecast_days range",
            "params": {"location": "London", "forecast_days": 15},  # Too many days
        },
        {
            "name": "Empty location",
            "params": {"location": ""},  # Empty string
        }
    ]

    for test_case in test_cases:
        print(f"\n   Testing: {test_case['name']}")
        try:
            result = execute_tool('get_weather', **test_case['params'])
            if result.success:
                print(f"   ⚠️ Unexpectedly succeeded")
            else:
                print(f"   ✅ Correctly rejected: {result.error}")
        except Exception as e:
            print(f"   ✅ Correctly caught: {type(e).__name__}: {e}")


def demo_tool_schemas():
    """Demonstrate tool schema generation for function calling APIs."""
    demo_header("Tool Schema Generation")

    print("📋 Generating schemas for function calling APIs...")

    schemas = tool_registry.get_tool_schemas()

    print(f"✅ Generated {len(schemas)} tool schemas")

    for schema in schemas:
        function_info = schema['function']
        print(f"\n🔧 Tool: {function_info['name']}")
        print(f"   Description: {function_info['description']}")

        params = function_info['parameters']
        properties = params.get('properties', {})
        required = params.get('required', [])

        print(f"   Parameters ({len(properties)} total):")
        for param_name, param_info in properties.items():
            req_marker = "✓" if param_name in required else "○"
            param_type = param_info.get('type', 'unknown')
            description = param_info.get('description', 'No description')
            print(f"     {req_marker} {param_name} ({param_type}): {description}")


def demo_error_handling():
    """Demonstrate error handling."""
    demo_header("Error Handling Demo")

    print("🛡️ Testing error handling scenarios...")

    # Test non-existent tool
    print("\n1. Non-existent tool:")
    try:
        result = execute_tool('non_existent_tool', param='value')
        print(f"   ⚠️ Unexpectedly succeeded")
    except Exception as e:
        print(f"   ✅ Correctly handled: {type(e).__name__}")

    # Test network/API errors (simulated with invalid location)
    print("\n2. Invalid location (API error):")
    try:
        result = execute_tool('get_weather', location='ThisLocationDoesNotExist12345XYZ')
        if result.success:
            print(f"   ⚠️ API accepted invalid location")
        else:
            print(f"   ✅ API correctly rejected: {result.error}")
    except Exception as e:
        print(f"   ✅ Error handled: {e}")

    # Test parameter type conversion
    print("\n3. Parameter type conversion:")
    try:
        result = execute_tool(
            'get_weather',
            location='London',
            forecast_days='3'  # String instead of int
        )
        print(f"   ✅ String '3' converted to integer")
    except Exception as e:
        print(f"   ❌ Type conversion failed: {e}")


def main():
    """Main demo function."""
    print("🎭 FlexiAI Modular Tool System Demo")
    print("=" * 40)
    print("Welcome to the FlexiAI tools demonstration!")
    print("This demo shows the powerful modular tool system.")

    # Run all demonstrations
    demo_basic_usage()
    demo_weather_tool()
    demo_custom_tool()
    demo_parameter_validation()
    demo_tool_schemas()
    demo_error_handling()

    # Final summary
    print("\n" + "=" * 40)
    print("🎉 Demo Complete!")
    print("\n💡 Key Features Demonstrated:")
    print("   ✅ Automatic tool discovery and registration")
    print("   ✅ Built-in weather tool with comprehensive data")
    print("   ✅ Easy custom tool creation")
    print("   ✅ Robust parameter validation")
    print("   ✅ Schema generation for function calling APIs")
    print("   ✅ Comprehensive error handling")
    print("   ✅ Integration with assistant models")

    print("\n🚀 Getting Started:")
    print("   1. Create your own tools by extending the Tool class")
    print("   2. Register them with tool_registry.register_custom_tool()")
    print("   3. Use execute_tool() to run them")
    print("   4. Tools automatically work with all assistant models")

    print("\n📚 Next Steps:")
    print("   • Check out the weather tool for API integration patterns")
    print("   • Create tools for your specific use cases")
    print("   • Use tool schemas with OpenAI function calling")
    print("   • Add tools to assistant models for enhanced capabilities")

    current_tools = list_tools()
    print(f"\n📊 Current system has {len(current_tools)} tools available:")
    for tool_name in current_tools:
        tool = get_tool(tool_name)
        print(f"   🔧 {tool_name} (v{tool.version}) - {tool.category}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo cancelled by user.")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
