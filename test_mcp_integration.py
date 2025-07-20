#!/usr/bin/env python3
"""
Test script for MCP (Model Context Protocol) integration with FlexiAI.

This script tests the MCP client functionality, tool discovery,
and integration with the FlexiAI voice assistant system.
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
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Add flexiai to path for testing
sys.path.insert(0, str(Path(__file__).parent / "flexiai"))

try:
    from flexiai.mcp.config import MCPConfig, MCPServerConfig
    from flexiai.mcp.client import MCPClient, MCPClientManager
    from flexiai.mcp.integration import MCPToolIntegration
    from flexiai.mcp.exceptions import MCPError, MCPConnectionError
except ImportError as e:
    print(f"Error importing MCP modules: {e}")
    print("Make sure FlexiAI is properly installed and MCP dependencies are available")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockMCPServer:
    """Mock MCP server for testing."""

    def __init__(self, port: int = 8901):
        self.port = port
        self.tools = {
            "get_weather": {
                "name": "get_weather",
                "description": "Get weather information for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City and country/state"
                        }
                    },
                    "required": ["location"]
                }
            },
            "search_web": {
                "name": "search_web",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
        self.server = None
        self.app = None

    async def start(self):
        """Start the mock server."""
        try:
            from aiohttp import web, web_response

            self.app = web.Application()

            # Add routes
            self.app.router.add_get('/mcp/tools', self.handle_tools)
            self.app.router.add_post('/mcp/execute', self.handle_execute)
            self.app.router.add_get('/mcp/health', self.handle_health)

            # Start server
            runner = web.AppRunner(self.app)
            await runner.setup()
            site = web.TCPSite(runner, 'localhost', self.port)
            await site.start()

            self.server = runner
            logger.info(f"Mock MCP server started on port {self.port}")

        except Exception as e:
            logger.error(f"Failed to start mock server: {e}")
            raise

    async def stop(self):
        """Stop the mock server."""
        if self.server:
            await self.server.cleanup()
            self.server = None
            logger.info("Mock MCP server stopped")

    async def handle_tools(self, request):
        """Handle /mcp/tools endpoint."""
        from aiohttp import web

        tools_list = list(self.tools.values())
        response_data = {"tools": tools_list}
        return web.json_response(response_data)

    async def handle_execute(self, request):
        """Handle /mcp/execute endpoint."""
        from aiohttp import web

        try:
            data = await request.json()
            method = data.get("method")
            params = data.get("params", {})
            request_id = data.get("id")

            if method == "tool_execute":
                tool_name = params.get("tool")
                tool_params = params.get("parameters", {})

                # Mock tool execution
                if tool_name == "get_weather":
                    location = tool_params.get("location", "Unknown")
                    result = {
                        "location": location,
                        "current": {
                            "temperature": "22°C",
                            "condition": "Partly cloudy",
                            "humidity": "65%",
                            "wind": "10 km/h"
                        },
                        "summary": f"Nice weather in {location} today!"
                    }
                elif tool_name == "search_web":
                    query = tool_params.get("query", "")
                    result = f"Mock search results for '{query}': Found 10 relevant articles about {query}."
                else:
                    return web.json_response({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    })

                return web.json_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                })
            else:
                return web.json_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown method: {method}"
                    }
                })

        except Exception as e:
            return web.json_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            })

    async def handle_health(self, request):
        """Handle /mcp/health endpoint."""
        from aiohttp import web
        return web.json_response({"status": "healthy", "timestamp": time.time()})


class MCPIntegrationTester:
    """Test suite for MCP integration."""

    def __init__(self):
        self.mock_server = MockMCPServer()
        self.temp_config_file = None
        self.test_results = []

    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        status = "✓ PASS" if success else "✗ FAIL"
        full_message = f"{status} {test_name}"
        if message:
            full_message += f": {message}"

        print(full_message)
        logger.info(full_message)

        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })

    def create_test_config(self) -> str:
        """Create a temporary MCP configuration file."""
        config_data = {
            "default_timeout": 10.0,
            "auto_discover_tools": True,
            "fallback_to_builtin_tools": True,
            "servers": [
                {
                    "name": "test_server",
                    "url": f"http://localhost:{self.mock_server.port}",
                    "enabled": True,
                    "timeout": 10.0,
                    "max_retries": 2,
                    "health_check_enabled": False,  # Disable for testing
                }
            ]
        }

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            self.temp_config_file = f.name

        return self.temp_config_file

    async def test_config_loading(self):
        """Test MCP configuration loading."""
        try:
            config_file = self.create_test_config()
            config = MCPConfig.load_from_file(config_file)

            assert len(config.servers) == 1
            assert config.servers[0].name == "test_server"
            assert config.servers[0].enabled == True

            self.log_test("Config Loading", True, "Configuration loaded successfully")

        except Exception as e:
            self.log_test("Config Loading", False, str(e))

    async def test_server_connection(self):
        """Test MCP server connection."""
        try:
            config_file = self.create_test_config()
            config = MCPConfig.load_from_file(config_file)
            server_config = config.servers[0]

            client = MCPClient(server_config)
            await client.connect()

            # Test health check
            healthy = await client._health_check()
            assert healthy, "Health check failed"

            await client.close()

            self.log_test("Server Connection", True, "Connected to mock server successfully")

        except Exception as e:
            self.log_test("Server Connection", False, str(e))

    async def test_tool_discovery(self):
        """Test tool discovery from MCP server."""
        try:
            config_file = self.create_test_config()
            config = MCPConfig.load_from_file(config_file)
            server_config = config.servers[0]

            client = MCPClient(server_config)
            await client.connect()

            # Discover tools
            tools = await client.discover_tools()

            assert len(tools) >= 2, f"Expected at least 2 tools, got {len(tools)}"

            tool_names = [tool.name for tool in tools]
            assert "get_weather" in tool_names, "get_weather tool not found"
            assert "search_web" in tool_names, "search_web tool not found"

            await client.close()

            self.log_test("Tool Discovery", True, f"Discovered {len(tools)} tools: {tool_names}")

        except Exception as e:
            self.log_test("Tool Discovery", False, str(e))

    async def test_tool_execution(self):
        """Test tool execution via MCP."""
        try:
            config_file = self.create_test_config()
            config = MCPConfig.load_from_file(config_file)
            server_config = config.servers[0]

            client = MCPClient(server_config)
            await client.connect()

            # Discover tools first
            await client.discover_tools()

            # Test weather tool
            weather_result = await client.execute_tool("get_weather", {"location": "New York"})
            assert weather_result.success, f"Weather tool failed: {weather_result.error}"
            assert isinstance(weather_result.result, dict), "Weather result should be a dict"
            assert "location" in weather_result.result, "Weather result missing location"

            # Test search tool
            search_result = await client.execute_tool("search_web", {"query": "Python MCP"})
            assert search_result.success, f"Search tool failed: {search_result.error}"
            assert isinstance(search_result.result, str), "Search result should be a string"

            await client.close()

            self.log_test("Tool Execution", True, "Both tools executed successfully")

        except Exception as e:
            self.log_test("Tool Execution", False, str(e))

    async def test_client_manager(self):
        """Test MCP client manager functionality."""
        try:
            config_file = self.create_test_config()
            config = MCPConfig.load_from_file(config_file)

            manager = MCPClientManager(config)
            await manager.connect_all()

            # Check connections
            assert manager.is_connected(), "Manager should be connected"
            assert len(manager.get_server_names()) == 1, "Should have 1 connected server"

            # Discover all tools
            await manager.discover_all_tools()

            # Check tools
            tool_schemas = manager.get_all_tool_schemas()
            assert len(tool_schemas) >= 2, f"Expected at least 2 tools, got {len(tool_schemas)}"

            # Test tool execution through manager
            result = await manager.execute_tool("get_weather", {"location": "London"})
            assert result.success, f"Manager tool execution failed: {result.error}"

            await manager.close_all()

            self.log_test("Client Manager", True, "Manager functionality works correctly")

        except Exception as e:
            self.log_test("Client Manager", False, str(e))

    async def test_tool_integration(self):
        """Test MCP tool integration with FlexiAI."""
        try:
            config_file = self.create_test_config()

            integration = MCPToolIntegration(config_file)
            await integration.initialize()

            # Check stats
            stats = integration.get_stats()
            assert stats.connected_servers == 1, f"Expected 1 connected server, got {stats.connected_servers}"
            assert stats.mcp_tools >= 2, f"Expected at least 2 MCP tools, got {stats.mcp_tools}"

            # Test getting tools for assistant
            tools_for_assistant = integration.get_tools_for_assistant()
            assert len(tools_for_assistant) >= 2, "Should have tools for assistant"

            # Check OpenAI format
            for tool in tools_for_assistant[:2]:  # Check first 2 tools
                assert "type" in tool, "Tool missing 'type' field"
                assert tool["type"] == "function", "Tool type should be 'function'"
                assert "function" in tool, "Tool missing 'function' field"
                assert "name" in tool["function"], "Tool function missing 'name'"
                assert "description" in tool["function"], "Tool function missing 'description'"

            # Test unified execution
            result = await integration.execute_tool_unified("get_weather", {"location": "Tokyo"})
            assert result.success, f"Unified execution failed: {result.error}"

            await integration.shutdown()

            self.log_test("Tool Integration", True, "Integration with FlexiAI works correctly")

        except Exception as e:
            self.log_test("Tool Integration", False, str(e))

    async def test_error_handling(self):
        """Test error handling scenarios."""
        try:
            config_file = self.create_test_config()
            config = MCPConfig.load_from_file(config_file)

            # Test invalid server
            invalid_config = MCPServerConfig(
                name="invalid_server",
                url="http://localhost:9999",  # Non-existent port
                timeout=1.0,
                max_retries=1
            )

            client = MCPClient(invalid_config)

            # This should fail gracefully
            try:
                await client.connect()
                self.log_test("Error Handling", False, "Should have failed to connect to invalid server")
                return
            except MCPConnectionError:
                pass  # Expected

            # Test unknown tool execution
            config = MCPConfig.load_from_file(config_file)
            manager = MCPClientManager(config)
            await manager.connect_all()

            result = await manager.execute_tool("unknown_tool", {})
            assert not result.success, "Unknown tool should fail"
            assert "not found" in result.error.lower(), "Error message should mention tool not found"

            await manager.close_all()

            self.log_test("Error Handling", True, "Error scenarios handled correctly")

        except Exception as e:
            self.log_test("Error Handling", False, str(e))

    async def cleanup(self):
        """Clean up test resources."""
        # Remove temporary config file
        if self.temp_config_file and os.path.exists(self.temp_config_file):
            os.unlink(self.temp_config_file)

    def print_summary(self):
        """Print test summary."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests

        print("\n" + "="*60)
        print("MCP INTEGRATION TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")

        print("="*60)

    async def run_all_tests(self):
        """Run all MCP integration tests."""
        print("Starting MCP Integration Tests...")
        print("="*60)

        try:
            # Start mock server
            await self.mock_server.start()

            # Wait a moment for server to be ready
            await asyncio.sleep(0.5)

            # Run tests
            await self.test_config_loading()
            await self.test_server_connection()
            await self.test_tool_discovery()
            await self.test_tool_execution()
            await self.test_client_manager()
            await self.test_tool_integration()
            await self.test_error_handling()

        finally:
            # Cleanup
            await self.mock_server.stop()
            await self.cleanup()

        # Print summary
        self.print_summary()

        # Return success status
        return all(result["success"] for result in self.test_results)


async def main():
    """Main test function."""
    print("FlexiAI MCP Integration Test Suite")
    print("="*60)

    # Check dependencies
    try:
        import aiohttp
        import httpx
    except ImportError as e:
        print(f"Missing required dependencies: {e}")
        print("Install with: pip install aiohttp httpx")
        return 1

    # Run tests
    tester = MCPIntegrationTester()
    success = await tester.run_all_tests()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
