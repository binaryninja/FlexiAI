# MCP (Model Context Protocol) Integration with FlexiAI

## Overview

FlexiAI now supports MCP (Model Context Protocol) integration, allowing your voice assistant to dynamically discover and use tools from external MCP servers. This enables modular, composable AI capabilities without hardcoding every tool into the main application.

## What is MCP?

MCP is an open standard (sometimes called the "USB-C for AI") that defines a lightweight HTTP/SSE interface for exposing tool-like capabilities to LLMs and agents. Instead of writing bespoke code for every API or data source, you "install" an MCP server that publishes its functions via a standard schema, and your agent simply discovers and invokes them over the network.

### Benefits of MCP Integration

- **Modularity**: Wrap each subsystem (file operations, web search, calendar, etc.) as its own MCP server
- **Dynamic Discovery**: New capabilities can be added by spinning up another MCP server and updating config
- **Standardized Security**: Each server enforces its own auth, quotas, and access controls
- **No Code Changes**: Add new tools without modifying FlexiAI source code

## Quick Start

### 1. Enable MCP Integration

```bash
# Basic MCP setup with default configuration
python -m flexiai --enable-mcp --tts

# Use custom MCP configuration file
python -m flexiai --enable-mcp --mcp-config my_mcp_config.yaml --tts
```

### 2. Configure MCP Servers

Copy the example configuration:
```bash
cp mcp_config.yaml my_mcp_config.yaml
```

Edit `my_mcp_config.yaml` to enable and configure your MCP servers:

```yaml
servers:
  - name: "web_search"
    url: "http://localhost:8002"
    enabled: true  # Enable this server
    auth_type: "api_key"
    auth_token: "${WEB_SEARCH_API_KEY}"
    allowed_tools:
      - "search_web"
      - "fetch_url"
```

### 3. Set Environment Variables

```bash
export WEB_SEARCH_API_KEY="your-api-key-here"
```

### 4. Start an MCP Server

You'll need MCP servers running. Here's a simple example using the Python MCP SDK:

```python
# web_search_server.py
from mcp import MCPServer, tool
import requests

app = MCPServer()

@tool(name="search_web", description="Search the web for information")
def search_web(query: str) -> str:
    # Implement web search logic
    return f"Search results for: {query}"

if __name__ == "__main__":
    app.serve(port=8002)
```

## Configuration Reference

### Global Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `default_timeout` | 30.0 | Default timeout for server connections |
| `auto_discover_tools` | true | Automatically discover tools from servers |
| `tool_discovery_interval` | 300.0 | How often to refresh tool discovery (seconds) |
| `fallback_to_builtin_tools` | true | Use built-in tools if MCP tools fail |

### Server Configuration

Each server in the `servers` list can have these properties:

#### Basic Settings
- `name`: Unique server identifier
- `url`: Server base URL (e.g., "http://localhost:8001")
- `enabled`: Whether to use this server (true/false)
- `timeout`: Request timeout in seconds
- `max_retries`: Number of retry attempts
- `retry_delay`: Delay between retries

#### Authentication
- `auth_type`: "bearer", "basic", "api_key", or "custom"
- `auth_token`: API token for bearer/api_key auth
- `auth_username`/`auth_password`: For basic auth
- `auth_headers`: Custom authentication headers

#### Tool Filtering
- `allowed_tools`: List of tool names to allow (null = allow all)
- `blocked_tools`: List of tool names to block

#### Advanced Settings
- `use_sse`: Enable Server-Sent Events for streaming
- `verify_ssl`: Verify SSL certificates
- `custom_headers`: Additional HTTP headers
- `rate_limit_requests_per_minute`: Rate limiting
- `health_check_enabled`: Enable health monitoring

## Command Line Options

| Option | Description |
|--------|-------------|
| `--enable-mcp` | Enable MCP integration |
| `--mcp-config PATH` | Path to MCP configuration file |
| `--mcp-timeout SECONDS` | Default timeout for MCP connections |
| `--disable-mcp-fallback` | Don't fallback to built-in tools |

## Creating MCP Servers

### Using Python MCP SDK

```python
from mcp import MCPServer, tool
import json

app = MCPServer()

@tool(
    name="get_weather",
    description="Get current weather for a location",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City and country/state"
            }
        },
        "required": ["location"]
    }
)
def get_weather(location: str) -> str:
    # Your weather API logic here
    weather_data = {
        "location": location,
        "current": {
            "temperature": "22°C",
            "condition": "Partly cloudy",
            "humidity": "65%",
            "wind": "10 km/h"
        }
    }
    return json.dumps(weather_data)

@tool(name="create_task", description="Create a new task")
def create_task(title: str, description: str = "", due_date: str = None) -> str:
    # Your task management logic here
    return f"Created task: {title}"

if __name__ == "__main__":
    app.serve(host="localhost", port=8001)
```

### Server Requirements

Your MCP server must implement these endpoints:

- `GET /mcp/tools` - Return tool schemas
- `POST /mcp/execute` - Execute tools via JSON-RPC
- `GET /mcp/health` - Health check (optional)
- `GET /mcp/stream` - SSE streaming (optional)

## Usage Examples

### Voice Commands with MCP Tools

Once configured, you can use voice commands that automatically invoke MCP tools:

**Weather**: "What's the weather in New York?"
- FlexiAI detects this needs weather info
- Calls `get_weather` tool on the weather MCP server
- Returns natural language response

**File Operations**: "Read the contents of my notes file"
- Calls `read_file` tool on filesystem MCP server
- Returns file contents or error message

**Web Search**: "Search for Python MCP tutorials"
- Calls `search_web` tool on web search MCP server
- Returns summarized search results

### Function Call Flow

1. User speaks: "What's the weather in Paris?"
2. FlexiAI transcribes audio using Whisper
3. Voxtral model receives transcription + available tool schemas
4. Model generates function call: `get_weather(location="Paris")`
5. FlexiAI routes call to appropriate MCP server
6. MCP server executes tool and returns result
7. FlexiAI formats result into natural response
8. Response is spoken using TTS

## Available Example Servers

The configuration includes examples for:

- **Filesystem**: File read/write/list operations
- **Web Search**: Search engines and URL fetching
- **Calendar**: Event creation and scheduling
- **Email**: Send/receive/search emails
- **Task Management**: Todo list integration
- **Knowledge Base**: RAG document search
- **Smart Home**: IoT device control
- **Development Tools**: Code execution and documentation

## Troubleshooting

### Common Issues

**"No MCP servers connected"**
- Check that MCP servers are running on configured ports
- Verify `enabled: true` in configuration
- Check firewall/network connectivity

**"Tool 'X' not found"**
- Verify tool is listed in server's `/mcp/tools` endpoint
- Check `allowed_tools` and `blocked_tools` configuration
- Ensure server is connected and healthy

**"MCP tool execution failed"**
- Check server logs for errors
- Verify authentication credentials
- Test server endpoint manually with curl

**"Authentication failed"**
- Verify environment variables are set correctly
- Check auth_type matches server requirements
- Ensure API keys/tokens are valid

### Debug Mode

Enable debug logging to see MCP activity:

```bash
python -m flexiai --enable-mcp --debug --tts
```

This shows:
- MCP server connection attempts
- Tool discovery results
- Function call routing
- Execution results and errors

### Testing MCP Servers

Test your MCP server endpoints manually:

```bash
# Check available tools
curl http://localhost:8001/mcp/tools

# Test tool execution
curl -X POST http://localhost:8001/mcp/execute \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test",
    "method": "tool_execute",
    "params": {
      "tool": "get_weather",
      "parameters": {"location": "London"}
    }
  }'
```

## Security Considerations

### Best Practices

1. **Use Environment Variables**: Never hardcode API keys in config files
2. **Enable SSL**: Use HTTPS URLs for production servers
3. **Tool Filtering**: Configure `allowed_tools` and `blocked_tools` carefully
4. **Authentication**: Always use auth for external servers
5. **Rate Limiting**: Set appropriate limits to prevent abuse
6. **Network Security**: Run servers on private networks when possible

### Dangerous Operations

Be especially careful with tools that can:
- Delete files or data
- Send emails or messages
- Control smart home devices
- Execute code
- Access sensitive information

Use `blocked_tools` to prevent accidental access to dangerous operations.

## Performance Tips

1. **Local Servers**: Run MCP servers locally when possible for lower latency
2. **Caching**: Enable `cache_tool_schemas` to reduce discovery overhead
3. **Rate Limits**: Set reasonable limits to balance performance and safety
4. **Health Checks**: Enable health monitoring to detect server issues
5. **Concurrent Requests**: Adjust `concurrent_requests` based on your hardware

## Integration with Existing Tools

FlexiAI automatically combines MCP tools with built-in tools. The system:

1. Checks MCP servers for requested tools first
2. Falls back to built-in tools if MCP fails (when `fallback_to_builtin_tools: true`)
3. Provides unified tool schemas to the Voxtral model
4. Routes function calls to appropriate providers

## Future Enhancements

Planned improvements:
- WebSocket support for real-time streaming
- Tool composition and chaining
- Automatic server discovery via mDNS
- Built-in MCP server templates
- Integration with popular APIs (GitHub, Slack, etc.)
- Visual tool management interface

## Getting Help

- Check the debug logs with `--debug`
- Test MCP servers independently
- Verify configuration syntax with YAML validators
- Review FlexiAI issues on GitHub
- Join the community Discord for support

## Example Complete Setup

Here's a complete example to get started:

1. **Start a simple web search server**:
```python
# simple_search_server.py
from mcp import MCPServer, tool
import requests

app = MCPServer()

@tool(name="search_web", description="Search the web")
def search_web(query: str) -> str:
    return f"Mock search results for: {query}"

app.serve(port=8002)
```

2. **Configure FlexiAI**:
```yaml
# my_mcp_config.yaml
servers:
  - name: "search"
    url: "http://localhost:8002"
    enabled: true
```

3. **Run FlexiAI**:
```bash
python -m flexiai --enable-mcp --mcp-config my_mcp_config.yaml --tts
```

4. **Test with voice**: "Search the web for MCP tutorials"

The assistant will now use your MCP server to handle web search requests!