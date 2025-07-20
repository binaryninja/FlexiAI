#!/usr/bin/env python3
"""
Example MCP Server for FlexiAI Integration

This script demonstrates how to create a production-ready MCP server
that can be used with FlexiAI voice assistant. It implements several
useful tools including weather, file operations, web search, and more.

Installation:
    pip install aiohttp requests beautifulsoup4

Usage:
    python example_mcp_server.py --port 8001

Configuration:
    Set environment variables for API keys:
    - OPENWEATHER_API_KEY: For weather data
    - SEARCH_API_KEY: For web search (optional)

Then configure FlexiAI to use this server:
    python -m flexiai --enable-mcp --mcp-config your_config.yaml --tts
"""

import argparse
import asyncio
import json
import logging
import os
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import urllib.parse

try:
    from flexiai.config.api_keys import get_api_key
    HAS_FLEXIAI_CONFIG = True
except ImportError:
    HAS_FLEXIAI_CONFIG = False
    def get_api_key(key_name: str) -> Optional[str]:
        """Fallback to os.getenv if flexiai config not available."""
        return os.getenv(key_name)

try:
    import aiohttp
    from aiohttp import web
    import requests
except ImportError as e:
    print(f"Missing required dependencies: {e}")
    print("Install with: pip install aiohttp requests")
    exit(1)

# Optional dependencies
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPServer:
    """Production MCP Server for FlexiAI."""

    def __init__(self, port: int = 8001, host: str = "localhost"):
        self.port = port
        self.host = host
        self.app = None
        self.runner = None

        # Tool registry
        self.tools = {}
        self._register_tools()

    def _register_tools(self):
        """Register all available tools."""

        # Weather tool
        self.tools["get_weather"] = {
            "name": "get_weather",
            "description": "Get current weather information for any location worldwide",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name, optionally with country (e.g., 'London' or 'London, UK')"
                    },
                    "units": {
                        "type": "string",
                        "description": "Temperature units: 'metric' (°C), 'imperial' (°F), or 'kelvin'",
                        "enum": ["metric", "imperial", "kelvin"],
                        "default": "metric"
                    }
                },
                "required": ["location"]
            }
        }

        # File operations
        self.tools["read_file"] = {
            "name": "read_file",
            "description": "Read the contents of a text file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8)",
                        "default": "utf-8"
                    }
                },
                "required": ["file_path"]
            }
        }

        self.tools["write_file"] = {
            "name": "write_file",
            "description": "Write content to a text file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8)",
                        "default": "utf-8"
                    }
                },
                "required": ["file_path", "content"]
            }
        }

        self.tools["list_directory"] = {
            "name": "list_directory",
            "description": "List files and directories in a given path",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "Path to the directory to list"
                    },
                    "show_hidden": {
                        "type": "boolean",
                        "description": "Whether to show hidden files (default: false)",
                        "default": False
                    }
                },
                "required": ["directory_path"]
            }
        }

        # Web search tool
        self.tools["search_web"] = {
            "name": "search_web",
            "description": "Search the web for information on any topic",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query or question"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["query"]
            }
        }

        # System information
        self.tools["get_system_info"] = {
            "name": "get_system_info",
            "description": "Get system information including OS, CPU, memory, and disk usage",
            "parameters": {
                "type": "object",
                "properties": {
                    "detailed": {
                        "type": "boolean",
                        "description": "Whether to include detailed information (default: false)",
                        "default": False
                    }
                }
            }
        }

        # Date and time
        self.tools["get_datetime"] = {
            "name": "get_datetime",
            "description": "Get current date and time information",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone name (e.g., 'UTC', 'US/Eastern', 'Europe/London')",
                        "default": "local"
                    },
                    "format": {
                        "type": "string",
                        "description": "Date format string (default: ISO format)",
                        "default": "iso"
                    }
                }
            }
        }

        # URL fetching
        self.tools["fetch_url"] = {
            "name": "fetch_url",
            "description": "Fetch content from a URL and optionally extract text",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to fetch"
                    },
                    "extract_text": {
                        "type": "boolean",
                        "description": "Whether to extract readable text from HTML (default: true)",
                        "default": True
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Request timeout in seconds (default: 10)",
                        "default": 10
                    }
                },
                "required": ["url"]
            }
        }

    async def start(self):
        """Start the MCP server."""
        self.app = web.Application()

        # Add CORS middleware for development
        self.app.middlewares.append(self._cors_handler)

        # Add routes
        self.app.router.add_get('/mcp/tools', self._handle_tools)
        self.app.router.add_post('/mcp/execute', self._handle_execute)
        self.app.router.add_get('/mcp/health', self._handle_health)
        self.app.router.add_get('/mcp/info', self._handle_info)

        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()

        logger.info(f"MCP Server started on http://{self.host}:{self.port}")
        logger.info(f"Available tools: {', '.join(self.tools.keys())}")
        logger.info("Endpoints:")
        logger.info(f"  - GET  /mcp/tools   - List available tools")
        logger.info(f"  - POST /mcp/execute - Execute tools")
        logger.info(f"  - GET  /mcp/health  - Health check")
        logger.info(f"  - GET  /mcp/info    - Server information")

    async def stop(self):
        """Stop the MCP server."""
        if self.runner:
            await self.runner.cleanup()
            logger.info("MCP Server stopped")

    @web.middleware
    async def _cors_handler(self, request, handler):
        """Add CORS headers for cross-origin requests."""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    async def _handle_tools(self, request):
        """Handle GET /mcp/tools - return available tools."""
        tools_list = list(self.tools.values())
        return web.json_response({
            "tools": tools_list,
            "server_info": {
                "name": "FlexiAI Example MCP Server",
                "version": "1.0.0",
                "total_tools": len(tools_list)
            }
        })

    async def _handle_execute(self, request):
        """Handle POST /mcp/execute - execute tools via JSON-RPC."""
        try:
            data = await request.json()
            method = data.get("method")
            params = data.get("params", {})
            request_id = data.get("id")

            if method != "tool_execute":
                return web.json_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                })

            tool_name = params.get("tool")
            tool_params = params.get("parameters", {})

            logger.info(f"Executing tool: {tool_name} with parameters: {tool_params}")

            # Execute the tool
            result = await self._execute_tool(tool_name, tool_params)

            return web.json_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            })

        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            return web.json_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            })

    async def _handle_health(self, request):
        """Handle GET /mcp/health - health check."""
        return web.json_response({
            "status": "healthy",
            "timestamp": time.time(),
            "server": "FlexiAI Example MCP Server",
            "tools_available": len(self.tools),
            "uptime_seconds": time.time() - getattr(self, '_start_time', time.time())
        })

    async def _handle_info(self, request):
        """Handle GET /mcp/info - server information."""
        return web.json_response({
            "server_name": "FlexiAI Example MCP Server",
            "version": "1.0.0",
            "description": "Example MCP server with various utility tools",
            "host": self.host,
            "port": self.port,
            "tools_count": len(self.tools),
            "supported_features": [
                "weather_data",
                "file_operations",
                "web_search",
                "system_info",
                "datetime",
                "url_fetching"
            ],
            "requirements": [
                "OpenWeather API key for weather data",
                "Internet connection for web features"
            ]
        })

    async def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute a tool and return the result."""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Route to appropriate tool implementation
        if tool_name == "get_weather":
            return await self._tool_get_weather(params)
        elif tool_name == "read_file":
            return await self._tool_read_file(params)
        elif tool_name == "write_file":
            return await self._tool_write_file(params)
        elif tool_name == "list_directory":
            return await self._tool_list_directory(params)
        elif tool_name == "search_web":
            return await self._tool_search_web(params)
        elif tool_name == "get_system_info":
            return await self._tool_get_system_info(params)
        elif tool_name == "get_datetime":
            return await self._tool_get_datetime(params)
        elif tool_name == "fetch_url":
            return await self._tool_fetch_url(params)
        else:
            raise ValueError(f"Tool implementation not found: {tool_name}")

    async def _tool_get_weather(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get weather information using OpenWeatherMap API."""
        location = params.get("location")
        units = params.get("units", "metric")

        api_key = get_api_key("OPENWEATHERMAP_API_KEY")
        if not api_key:
            # Return mock data if no API key
            logger.warning("No OpenWeatherMap API key found, returning mock data")
            return {
                "location": location,
                "current": {
                    "temperature": "22°C",
                    "condition": "Partly cloudy",
                    "humidity": "65%",
                    "wind": "10 km/h"
                },
                "summary": f"Mock weather data for {location} (set OPENWEATHERMAP_API_KEY for real data)"
            }

        try:
            # Call OpenWeatherMap API
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params_api = {
                "q": location,
                "appid": api_key,
                "units": units
            }

            response = requests.get(url, params=params_api, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Format temperature unit
            temp_unit = {"metric": "°C", "imperial": "°F", "kelvin": "K"}[units]

            return {
                "location": f"{data['name']}, {data['sys']['country']}",
                "current": {
                    "temperature": f"{data['main']['temp']:.1f}{temp_unit}",
                    "condition": data['weather'][0]['description'].title(),
                    "humidity": f"{data['main']['humidity']}%",
                    "wind": f"{data['wind']['speed']} m/s"
                },
                "summary": f"Weather in {data['name']}: {data['weather'][0]['description']}"
            }

        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return {
                "error": f"Failed to get weather data: {str(e)}",
                "location": location
            }

    async def _tool_read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read file contents."""
        file_path = params.get("file_path")
        encoding = params.get("encoding", "utf-8")

        try:
            path = Path(file_path).expanduser().resolve()

            # Security check - don't allow reading outside current directory tree
            # You may want to adjust this based on your security requirements
            if not str(path).startswith(str(Path.cwd())):
                return {"error": "Access denied: file outside allowed directory"}

            with open(path, 'r', encoding=encoding) as f:
                content = f.read()

            return {
                "file_path": str(path),
                "content": content,
                "size_bytes": len(content.encode(encoding)),
                "encoding": encoding
            }

        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}

    async def _tool_write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Write content to file."""
        file_path = params.get("file_path")
        content = params.get("content")
        encoding = params.get("encoding", "utf-8")

        try:
            path = Path(file_path).expanduser().resolve()

            # Security check
            if not str(path).startswith(str(Path.cwd())):
                return {"error": "Access denied: file outside allowed directory"}

            # Create directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'w', encoding=encoding) as f:
                f.write(content)

            return {
                "file_path": str(path),
                "bytes_written": len(content.encode(encoding)),
                "encoding": encoding,
                "success": True
            }

        except Exception as e:
            return {"error": f"Failed to write file: {str(e)}"}

    async def _tool_list_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List directory contents."""
        directory_path = params.get("directory_path")
        show_hidden = params.get("show_hidden", False)

        try:
            path = Path(directory_path).expanduser().resolve()

            if not path.exists():
                return {"error": "Directory does not exist"}

            if not path.is_dir():
                return {"error": "Path is not a directory"}

            items = []
            for item in path.iterdir():
                if not show_hidden and item.name.startswith('.'):
                    continue

                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })

            return {
                "directory_path": str(path),
                "items": sorted(items, key=lambda x: (x["type"], x["name"])),
                "total_items": len(items)
            }

        except Exception as e:
            return {"error": f"Failed to list directory: {str(e)}"}

    async def _tool_search_web(self, params: Dict[str, Any]) -> str:
        """Search the web for information."""
        query = params.get("query")
        num_results = params.get("num_results", 5)

        # For this example, we'll use DuckDuckGo's instant answer API
        # In production, you might use Google Custom Search API or similar
        try:
            # DuckDuckGo instant answer API
            url = "https://api.duckduckgo.com/"
            params_api = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }

            response = requests.get(url, params=params_api, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Extract useful information
            result_parts = []

            if data.get("Abstract"):
                result_parts.append(f"Summary: {data['Abstract']}")

            if data.get("Definition"):
                result_parts.append(f"Definition: {data['Definition']}")

            # Add related topics
            if data.get("RelatedTopics"):
                topics = []
                for topic in data["RelatedTopics"][:3]:  # Limit to first 3
                    if isinstance(topic, dict) and topic.get("Text"):
                        topics.append(topic["Text"])
                if topics:
                    result_parts.append(f"Related: {'; '.join(topics)}")

            if result_parts:
                return f"Search results for '{query}': " + " | ".join(result_parts)
            else:
                return f"Search completed for '{query}', but no detailed results were found. Try a more specific query."

        except Exception as e:
            logger.error(f"Search error: {e}")
            return f"Search failed for '{query}': {str(e)}"

    async def _tool_get_system_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get system information."""
        detailed = params.get("detailed", False)

        try:
            import psutil
        except ImportError:
            return {"error": "psutil not available - install with 'pip install psutil'"}

        try:
            info = {
                "system": platform.system(),
                "platform": platform.platform(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory": {
                    "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                    "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                    "percent_used": psutil.virtual_memory().percent
                },
                "disk": {
                    "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                    "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
                    "percent_used": round((psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100, 1)
                }
            }

            if detailed:
                info.update({
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                    "network_interfaces": list(psutil.net_if_addrs().keys())
                })

            return info

        except Exception as e:
            return {"error": f"Failed to get system info: {str(e)}"}

    async def _tool_get_datetime(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get current date and time."""
        timezone_name = params.get("timezone", "local")
        format_type = params.get("format", "iso")

        try:
            if timezone_name == "local":
                dt = datetime.now()
                tz_info = "Local"
            elif timezone_name.upper() == "UTC":
                dt = datetime.now(timezone.utc)
                tz_info = "UTC"
            else:
                # For other timezones, you'd need pytz library
                dt = datetime.now()
                tz_info = f"Local (requested: {timezone_name})"

            if format_type == "iso":
                formatted = dt.isoformat()
            else:
                formatted = dt.strftime(format_type)

            return {
                "datetime": formatted,
                "timezone": tz_info,
                "timestamp": dt.timestamp(),
                "day_of_week": dt.strftime("%A"),
                "readable": dt.strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            return {"error": f"Failed to get datetime: {str(e)}"}

    async def _tool_fetch_url(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch content from a URL."""
        url = params.get("url")
        extract_text = params.get("extract_text", True)
        timeout = params.get("timeout", 10)

        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()

            result = {
                "url": url,
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", ""),
                "content_length": len(response.content)
            }

            if extract_text and "text/html" in response.headers.get("content-type", ""):
                if HAS_BS4:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    # Extract text, removing scripts and styles
                    for script in soup(["script", "style"]):
                        script.decompose()
                    text = soup.get_text()
                    # Clean up whitespace
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                    result["text"] = text[:2000] + "..." if len(text) > 2000 else text
                else:
                    result["text"] = "Text extraction requires BeautifulSoup4 (pip install beautifulsoup4)"
            else:
                result["content"] = response.text[:1000] + "..." if len(response.text) > 1000 else response.text

            return result

        except Exception as e:
            return {"error": f"Failed to fetch URL: {str(e)}"}


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="FlexiAI Example MCP Server")
    parser.add_argument("--port", type=int, default=8001, help="Port to run server on")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check for API keys
    if not os.getenv("OPENWEATHER_API_KEY"):
        print("⚠️  No OPENWEATHER_API_KEY found. Weather tool will return mock data.")
        print("   Get a free API key at: https://openweathermap.org/api")

    # Start server
    server = MCPServer(port=args.port, host=args.host)
    server._start_time = time.time()

    try:
        await server.start()

        print(f"\n🚀 MCP Server running on http://{args.host}:{args.port}")
        print("📋 Configure FlexiAI with:")
        print(f"   servers:")
        print(f"     - name: example_server")
        print(f"       url: http://{args.host}:{args.port}")
        print(f"       enabled: true")
        print("\n🎤 Try voice commands like:")
        print("   - 'What's the weather in London?'")
        print("   - 'What time is it?'")
        print("   - 'Search for Python tutorials'")
        print("   - 'Show system information'")
        print("\n📱 Press Ctrl+C to stop")

        # Keep server running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
