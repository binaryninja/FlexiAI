#!/usr/bin/env python3
"""
FlexiAI MCP Integration Demo

This script demonstrates how to use MCP (Model Context Protocol) servers
with FlexiAI voice assistant. It creates a simple MCP server and shows
how voice commands can automatically invoke external tools.

Usage:
    python demo_mcp_integration.py

The demo will:
1. Start a simple MCP server with example tools
2. Configure FlexiAI to use the MCP server
3. Show how voice commands trigger MCP tool execution
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, Any

# Add flexiai to path
sys.path.insert(0, str(Path(__file__).parent / "flexiai"))

try:
    from aiohttp import web
    from flexiai.mcp.integration import MCPToolIntegration
    from flexiai.mcp.config import MCPConfig
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: pip install aiohttp")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DemoMCPServer:
    """Simple MCP server for demonstration."""

    def __init__(self, port: int = 8900):
        self.port = port
        self.app = None
        self.runner = None

        # Demo tools with realistic responses
        self.tools = {
            "get_weather": {
                "name": "get_weather",
                "description": "Get current weather information for any location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City and country/state (e.g., 'New York, NY' or 'London, UK')"
                        }
                    },
                    "required": ["location"]
                }
            },
            "search_web": {
                "name": "search_web",
                "description": "Search the web for information on any topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query or question"
                        }
                    },
                    "required": ["query"]
                }
            },
            "create_task": {
                "name": "create_task",
                "description": "Create a new task or reminder",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Task title or description"
                        },
                        "due_date": {
                            "type": "string",
                            "description": "Due date (optional, format: YYYY-MM-DD)"
                        },
                        "priority": {
                            "type": "string",
                            "description": "Priority level: low, medium, high"
                        }
                    },
                    "required": ["title"]
                }
            },
            "get_time": {
                "name": "get_time",
                "description": "Get current time and date information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Timezone (optional, e.g., 'UTC', 'US/Eastern')"
                        }
                    }
                }
            }
        }

    async def start(self):
        """Start the MCP server."""
        self.app = web.Application()

        # Add CORS headers for development
        self.app.middlewares.append(self._cors_handler)

        # Add routes
        self.app.router.add_get('/mcp/tools', self._handle_tools)
        self.app.router.add_post('/mcp/execute', self._handle_execute)
        self.app.router.add_get('/mcp/health', self._handle_health)

        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, 'localhost', self.port)
        await site.start()

        print(f"🌐 Demo MCP Server started on http://localhost:{self.port}")
        print(f"   Available tools: {', '.join(self.tools.keys())}")

    async def stop(self):
        """Stop the MCP server."""
        if self.runner:
            await self.runner.cleanup()
            print("🛑 Demo MCP Server stopped")

    @web.middleware
    async def _cors_handler(self, request, handler):
        """Add CORS headers."""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    async def _handle_tools(self, request):
        """Handle /mcp/tools endpoint - return available tools."""
        tools_list = list(self.tools.values())
        return web.json_response({"tools": tools_list})

    async def _handle_execute(self, request):
        """Handle /mcp/execute endpoint - execute tools."""
        try:
            data = await request.json()
            method = data.get("method")
            params = data.get("params", {})
            request_id = data.get("id")

            if method != "tool_execute":
                return web.json_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Unknown method: {method}"}
                })

            tool_name = params.get("tool")
            tool_params = params.get("parameters", {})

            print(f"🔧 Executing tool: {tool_name} with params: {tool_params}")

            # Execute the requested tool
            if tool_name == "get_weather":
                result = self._execute_weather_tool(tool_params)
            elif tool_name == "search_web":
                result = self._execute_search_tool(tool_params)
            elif tool_name == "create_task":
                result = self._execute_task_tool(tool_params)
            elif tool_name == "get_time":
                result = self._execute_time_tool(tool_params)
            else:
                return web.json_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                })

            return web.json_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            })

        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return web.json_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            })

    async def _handle_health(self, request):
        """Handle /mcp/health endpoint."""
        return web.json_response({
            "status": "healthy",
            "timestamp": time.time(),
            "server": "FlexiAI Demo MCP Server",
            "tools_available": len(self.tools)
        })

    def _execute_weather_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute weather tool with realistic mock data."""
        location = params.get("location", "Unknown Location")

        # Mock realistic weather data
        weather_conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Clear"]
        temps = ["18°C", "22°C", "25°C", "15°C", "28°C"]

        import random
        condition = random.choice(weather_conditions)
        temp = random.choice(temps)

        return {
            "location": location,
            "current": {
                "temperature": temp,
                "condition": condition,
                "humidity": f"{random.randint(40, 80)}%",
                "wind": f"{random.randint(5, 25)} km/h"
            },
            "summary": f"Pleasant weather in {location} today!"
        }

    def _execute_search_tool(self, params: Dict[str, Any]) -> str:
        """Execute web search tool with mock results."""
        query = params.get("query", "")

        # Mock search results
        topics = {
            "python": "Python programming tutorials, documentation, and community resources",
            "mcp": "Model Context Protocol specifications and implementation guides",
            "ai": "Latest artificial intelligence research, tools, and applications",
            "weather": "Weather forecasting services and meteorological data",
            "news": "Current news headlines and breaking stories from around the world"
        }

        # Find relevant topic or provide generic response
        for topic, description in topics.items():
            if topic.lower() in query.lower():
                return f"Search results for '{query}': {description}. Found multiple relevant articles and resources."

        return f"Search results for '{query}': Found several articles and resources related to your query. Top results include recent publications and authoritative sources on this topic."

    def _execute_task_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task creation tool."""
        title = params.get("title", "Untitled Task")
        due_date = params.get("due_date", "")
        priority = params.get("priority", "medium")

        # Generate a mock task ID
        import uuid
        task_id = str(uuid.uuid4())[:8]

        return {
            "task_id": task_id,
            "title": title,
            "due_date": due_date,
            "priority": priority,
            "status": "created",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def _execute_time_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute time tool."""
        timezone = params.get("timezone", "Local")

        current_time = time.strftime("%H:%M:%S")
        current_date = time.strftime("%Y-%m-%d")
        day_of_week = time.strftime("%A")

        return {
            "current_time": current_time,
            "current_date": current_date,
            "day_of_week": day_of_week,
            "timezone": timezone,
            "formatted": f"{day_of_week}, {current_date} at {current_time}"
        }


class FlexiAIMCPDemo:
    """Main demo orchestrator."""

    def __init__(self):
        self.mcp_server = DemoMCPServer()
        self.config_file = None
        self.integration = None

    def create_demo_config(self):
        """Create MCP configuration for the demo."""
        config_data = {
            "default_timeout": 10.0,
            "auto_discover_tools": True,
            "fallback_to_builtin_tools": True,
            "fail_on_server_error": False,
            "servers": [
                {
                    "name": "demo_server",
                    "url": f"http://localhost:{self.mcp_server.port}",
                    "enabled": True,
                    "timeout": 15.0,
                    "health_check_enabled": True,
                    "health_check_interval": 30.0
                }
            ]
        }

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            self.config_file = f.name

        print(f"📄 Created demo MCP config: {self.config_file}")
        return self.config_file

    async def test_mcp_integration(self):
        """Test MCP integration with example commands."""
        print("\n🧪 Testing MCP Integration...")

        try:
            # Initialize MCP integration
            self.integration = MCPToolIntegration(self.config_file)
            await self.integration.initialize()

            # Get integration stats
            stats = self.integration.get_stats()
            print(f"✅ MCP Integration initialized:")
            print(f"   • Connected servers: {stats.connected_servers}")
            print(f"   • Available MCP tools: {stats.mcp_tools}")
            print(f"   • Built-in tools: {stats.builtin_tools}")
            print(f"   • Total tools: {stats.total_tools}")

            # Test individual tools
            test_cases = [
                {
                    "name": "Weather Query",
                    "tool": "get_weather",
                    "params": {"location": "New York, NY"},
                    "voice_command": "What's the weather in New York?"
                },
                {
                    "name": "Web Search",
                    "tool": "search_web",
                    "params": {"query": "Python MCP integration tutorials"},
                    "voice_command": "Search for Python MCP integration tutorials"
                },
                {
                    "name": "Task Creation",
                    "tool": "create_task",
                    "params": {"title": "Review MCP integration demo", "priority": "high"},
                    "voice_command": "Create a high priority task to review MCP integration demo"
                },
                {
                    "name": "Time Query",
                    "tool": "get_time",
                    "params": {},
                    "voice_command": "What time is it?"
                }
            ]

            for i, test_case in enumerate(test_cases, 1):
                print(f"\n🎯 Test {i}: {test_case['name']}")
                print(f"   Voice Command: \"{test_case['voice_command']}\"")
                print(f"   → Executes: {test_case['tool']}({test_case['params']})")

                # Execute the tool
                result = await self.integration.execute_tool_unified(
                    test_case['tool'],
                    test_case['params']
                )

                if result.success:
                    print(f"   ✅ Success: {self._format_result(result.data)}")
                else:
                    print(f"   ❌ Failed: {result.error}")

            # Show available tools for assistant
            print(f"\n📋 Tools available to FlexiAI assistant:")
            tools_for_assistant = self.integration.get_tools_for_assistant()
            for tool in tools_for_assistant:
                if 'function' in tool:
                    func_info = tool['function']
                    print(f"   • {func_info['name']}: {func_info['description']}")

        except Exception as e:
            print(f"❌ MCP Integration test failed: {e}")
            import traceback
            traceback.print_exc()

    def _format_result(self, data) -> str:
        """Format tool result for display."""
        if isinstance(data, dict):
            if "location" in data and "current" in data:
                # Weather result
                current = data["current"]
                return f"{data['location']}: {current['temperature']}, {current['condition']}"
            elif "task_id" in data:
                # Task result
                return f"Created task '{data['title']}' (ID: {data['task_id']})"
            elif "current_time" in data:
                # Time result
                return data["formatted"]
            else:
                return str(data)[:100] + "..." if len(str(data)) > 100 else str(data)
        else:
            return str(data)[:100] + "..." if len(str(data)) > 100 else str(data)

    async def run_demo(self):
        """Run the complete demo."""
        print("🚀 FlexiAI MCP Integration Demo")
        print("=" * 50)

        try:
            # Start MCP server
            await self.mcp_server.start()

            # Create configuration
            self.create_demo_config()

            # Wait for server to be ready
            await asyncio.sleep(1)

            # Test MCP integration
            await self.test_mcp_integration()

            print("\n🎉 Demo completed successfully!")
            print("\nTo use MCP with FlexiAI:")
            print("1. Start your MCP servers")
            print("2. Configure them in mcp_config.yaml")
            print("3. Run: python -m flexiai --enable-mcp --tts")
            print("4. Use voice commands that trigger MCP tools!")

        except KeyboardInterrupt:
            print("\n👋 Demo interrupted by user")
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up demo resources."""
        print("\n🧹 Cleaning up...")

        if self.integration:
            await self.integration.shutdown()

        await self.mcp_server.stop()

        if self.config_file and os.path.exists(self.config_file):
            os.unlink(self.config_file)
            print("   Removed temporary config file")


async def main():
    """Main demo entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(__doc__)
        return 0

    demo = FlexiAIMCPDemo()
    await demo.run_demo()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
