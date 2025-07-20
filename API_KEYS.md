# 🔐 FlexiAI API Key Management

This document explains how to securely manage API keys for FlexiAI services including OpenAI, ElevenLabs, OpenWeatherMap, and other external APIs.

## 🌟 Features

- **Secure Storage**: Environment variables, .env files, and optional encryption
- **Multiple Sources**: Automatically checks environment variables, .env files, and encrypted storage
- **Validation**: Built-in format validation for known API key types
- **Easy Setup**: Interactive setup script and templates
- **Fallback Handling**: Graceful degradation when API keys are missing
- **Security First**: No hardcoded keys, .gitignore integration, secure defaults

## 🚀 Quick Start

### 1. Run the Setup Script

```bash
python setup_api_keys.py
```

This interactive script will guide you through setting up your API keys securely.

### 2. Or Create .env File Manually

Create a `.env` file in your project root:

```env
# FlexiAI API Keys
OPENAI_API_KEY=sk-your-openai-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here
OPENWEATHERMAP_API_KEY=your-weather-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

### 3. Use in Your Code

```python
from flexiai.config.api_keys import get_api_key

# Get an API key (returns None if not found)
openai_key = get_api_key('OPENAI_API_KEY')

# Get a required API key (raises exception if not found)
elevenlabs_key = get_api_key('ELEVENLABS_API_KEY', required=True)
```

## 📋 Supported API Keys

| Service | Key Name | Description | Where to Get |
|---------|----------|-------------|--------------|
| OpenAI | `OPENAI_API_KEY` | GPT models, embeddings, TTS | [platform.openai.com](https://platform.openai.com/api-keys) |
| ElevenLabs | `ELEVENLABS_API_KEY` | Premium text-to-speech | [elevenlabs.io](https://elevenlabs.io/app/speech-synthesis) |
| OpenWeatherMap | `OPENWEATHERMAP_API_KEY` | Weather data | [openweathermap.org](https://openweathermap.org/api) |
| Anthropic | `ANTHROPIC_API_KEY` | Claude models | [console.anthropic.com](https://console.anthropic.com/) |
| Google | `GOOGLE_API_KEY` | Google Cloud services | [console.cloud.google.com](https://console.cloud.google.com/) |
| Azure OpenAI | `AZURE_OPENAI_KEY` | Azure OpenAI services | [portal.azure.com](https://portal.azure.com/) |
| Hugging Face | `HUGGINGFACE_API_KEY` | Model downloads, inference | [huggingface.co](https://huggingface.co/settings/tokens) |
| DeepL | `DEEPL_API_KEY` | Translation services | [deepl.com](https://www.deepl.com/pro-api) |

## 🔧 Setup Methods

### Method 1: Environment Variables (Recommended for Production)

#### Linux/Mac:
```bash
export OPENAI_API_KEY="sk-your-key-here"
export ELEVENLABS_API_KEY="your-key-here"
```

#### Windows:
```cmd
set OPENAI_API_KEY=sk-your-key-here
set ELEVENLABS_API_KEY=your-key-here
```

#### Windows PowerShell:
```powershell
$env:OPENAI_API_KEY="sk-your-key-here"
$env:ELEVENLABS_API_KEY="your-key-here"
```

### Method 2: .env File (Recommended for Development)

Create a `.env` file in your project root:

```env
# OpenAI API key for GPT models
OPENAI_API_KEY=sk-your-openai-key-here

# ElevenLabs API key for text-to-speech
ELEVENLABS_API_KEY=your-elevenlabs-key-here

# OpenWeatherMap API key for weather data
OPENWEATHERMAP_API_KEY=your-weather-key-here

# Optional: Other service keys
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GOOGLE_API_KEY=your-google-key-here
```

### Method 3: Programmatic Setup

```python
from flexiai.config.api_keys import set_api_key

# Set keys programmatically (for current session only)
set_api_key('OPENAI_API_KEY', 'sk-your-key-here')
set_api_key('ELEVENLABS_API_KEY', 'your-key-here')
```

### Method 4: Interactive Setup

```python
from flexiai.config.api_keys import setup_api_keys

# Run interactive setup
setup_api_keys()
```

## 📖 Usage Examples

### Basic Usage

```python
from flexiai.config.api_keys import get_api_key

# Check if a key is available
if get_api_key('OPENAI_API_KEY'):
    print("OpenAI API key is configured")
else:
    print("OpenAI API key not found")

# Get a required key (raises exception if missing)
try:
    api_key = get_api_key('OPENAI_API_KEY', required=True)
    # Use the API key
except ValueError as e:
    print(f"Error: {e}")
```

### Service Integration

```python
from flexiai.config.api_keys import get_api_key
import openai

class OpenAIService:
    def __init__(self):
        api_key = get_api_key('OPENAI_API_KEY', required=True)
        self.client = openai.OpenAI(api_key=api_key)
    
    def generate_text(self, prompt):
        # Use OpenAI API
        pass

# Conditional service usage
def create_tts_service():
    if get_api_key('ELEVENLABS_API_KEY'):
        return ElevenLabsTTS()
    elif get_api_key('OPENAI_API_KEY'):
        return OpenAITTS()
    else:
        return SystemTTS()  # Fallback
```

### Status Checking

```python
from flexiai.config.api_keys import api_keys

# Get status of all keys
status = api_keys.list_available_keys()

for key_name, info in status.items():
    print(f"{key_name}: {'✅' if info['available'] else '❌'}")
    print(f"  Description: {info['description']}")
    if info['available']:
        print(f"  Source: {info['source']}")
```

## 🔒 Security Features

### Automatic .gitignore Protection

The system automatically ensures `.env` files are in your `.gitignore`:

```gitignore
# Environment variables (API keys)
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
```

### Key Validation

Built-in validation for known API key formats:

```python
# These will be validated automatically
set_api_key('OPENAI_API_KEY', 'sk-...')        # Must start with 'sk-'
set_api_key('ANTHROPIC_API_KEY', 'sk-ant-...')  # Must start with 'sk-ant-'
set_api_key('OPENWEATHERMAP_API_KEY', '...')    # Must be 32 chars, alphanumeric
```

### Encrypted Storage (Optional)

For enhanced security, install the cryptography package:

```bash
pip install cryptography
```

Then use encrypted storage:

```python
from flexiai.config.api_keys import set_api_key

# Store encrypted (requires cryptography package)
set_api_key('OPENAI_API_KEY', 'sk-your-key', encrypt=True)
```

### Secure File Permissions

Encrypted key files are automatically created with secure permissions:
- Key files: `0o600` (owner read/write only)
- Config directories: `0o700` (owner access only)

## 🌍 Environment-Specific Configuration

### Development
```env
# .env (local development)
OPENAI_API_KEY=sk-dev-key-here
ELEVENLABS_API_KEY=dev-key-here
```

### Staging
```bash
# Environment variables (staging server)
export OPENAI_API_KEY="sk-staging-key-here"
export ELEVENLABS_API_KEY="staging-key-here"
```

### Production
```bash
# Environment variables (production server)
export OPENAI_API_KEY="sk-prod-key-here"
export ELEVENLABS_API_KEY="prod-key-here"
```

## 🛠️ Advanced Configuration

### Custom Configuration

```python
from flexiai.config.api_keys import APIKeyManager, APIKeyConfig

# Custom configuration
config = APIKeyConfig(
    env_file_paths=['.env', '.env.production'],
    use_encryption=True,
    create_config_dirs=True
)

# Custom manager
custom_manager = APIKeyManager(config)
api_key = custom_manager.get_key('CUSTOM_API_KEY')
```

### Adding Custom API Keys

```python
from flexiai.config.api_keys import api_keys

# Extend supported keys
api_keys.config.SUPPORTED_KEYS['CUSTOM_SERVICE_KEY'] = 'My custom service API key'

# Use like any other key
api_keys.set_key('CUSTOM_SERVICE_KEY', 'your-custom-key')
```

## 📁 File Locations

The system checks for API keys in this order:

1. **Environment variables** (highest priority)
2. **Local .env files**:
   - `.env` (project root)
   - `.env.local` (project root)
3. **User config files**:
   - `~/.flexiai/.env`
   - `~/.config/flexiai/.env`
4. **Encrypted storage** (if enabled):
   - `~/.config/flexiai/keys.enc`

## 🚨 Security Best Practices

### ✅ DO:
- Use environment variables in production
- Add `.env` files to `.gitignore`
- Use `get_api_key()` instead of `os.getenv()`
- Set `required=True` for critical API keys
- Rotate API keys regularly
- Use different keys for different environments
- Monitor API key usage

### ❌ DON'T:
- Hardcode API keys in source code
- Commit `.env` files to version control
- Share API keys in logs or error messages
- Use production keys in development
- Store keys in plain text files in production
- Share API keys via email or chat

### 🔍 Code Review Checklist:
- [ ] No hardcoded API keys
- [ ] Using `get_api_key()` function
- [ ] `.env` files in `.gitignore`
- [ ] Proper error handling for missing keys
- [ ] No API keys in log outputs

## 🐛 Troubleshooting

### Common Issues

#### "API key not found" Error
```python
# Check if key is set
from flexiai.config.api_keys import get_api_key
key = get_api_key('OPENAI_API_KEY')
if not key:
    print("Key not found. Check your .env file or environment variables.")
```

#### .env File Not Loading
```python
# Check file location and permissions
import os
print("Current directory:", os.getcwd())
print(".env exists:", os.path.exists('.env'))

# Manually load .env for testing
from flexiai.config.api_keys import api_keys
api_keys._load_env_file('.env')
```

#### Invalid Key Format
```python
# Check key validation
from flexiai.config.api_keys import api_keys
valid = api_keys._validate_key('OPENAI_API_KEY', 'your-key-here')
print("Key valid:", valid)
```

### Debug Information

```python
from flexiai.config.api_keys import api_keys

# Get detailed status
status = api_keys.list_available_keys()
for key_name, info in status.items():
    print(f"{key_name}:")
    print(f"  Available: {info['available']}")
    print(f"  Source: {info['source']}")
    print(f"  Description: {info['description']}")
```

### Enable Debug Logging

```python
from flexiai.utils import debug_print
import os

# Enable debug output
os.environ['FLEXIAI_DEBUG'] = '1'

# Now API key operations will show debug information
from flexiai.config.api_keys import get_api_key
key = get_api_key('OPENAI_API_KEY')  # Will show debug info
```

## 🤝 Contributing

To add support for a new API service:

1. Add the key to `SUPPORTED_KEYS` in `APIKeyConfig`
2. Add validation logic in `_validate_key()` if needed
3. Update this documentation
4. Add examples and tests

Example:
```python
# In flexiai/config/api_keys.py
SUPPORTED_KEYS = {
    # ... existing keys ...
    'NEW_SERVICE_API_KEY': 'Description of the new service',
}

# Add validation if needed
def _validate_key(self, key_name: str, key_value: str) -> bool:
    validations = {
        # ... existing validations ...
        'NEW_SERVICE_API_KEY': lambda k: k.startswith('ns-') and len(k) == 40,
    }
    # ...
```

## 📚 API Reference

### Functions

#### `get_api_key(key_name: str, required: bool = False) -> Optional[str]`
Get an API key value.

**Parameters:**
- `key_name`: Name of the API key (e.g., 'OPENAI_API_KEY')
- `required`: If True, raises ValueError when key is not found

**Returns:** API key value or None

#### `set_api_key(key_name: str, key_value: str, encrypt: bool = False)`
Set an API key.

**Parameters:**
- `key_name`: Name of the API key
- `key_value`: The API key value
- `encrypt`: Whether to store encrypted (requires cryptography package)

#### `setup_api_keys()`
Run interactive API key setup.

### Classes

#### `APIKeyManager`
Main class for managing API keys.

#### `APIKeyConfig`
Configuration class for customizing behavior.

## 🔗 Related Documentation

- [FlexiAI Setup Guide](README.md)
- [Function Calling](FUNCTION_CALLING.md)
- [TTS Setup](TTS_SETUP.md)
- [ElevenLabs Quickstart](ELEVENLABS_QUICKSTART.md)

## 💡 Examples

See `examples/api_key_example.py` for comprehensive usage examples and `setup_api_keys.py` for the interactive setup script.

---

For questions or issues with API key management, please check the troubleshooting section above or open an issue on the FlexiAI repository.