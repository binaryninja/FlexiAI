"""
Secure API key management for FlexiAI.

This module provides a secure way to manage API keys for various services
like OpenAI, ElevenLabs, OpenWeatherMap, etc.

Security features:
- Environment variable loading
- .env file support
- Optional encrypted storage
- No hardcoded keys
- Secure key validation
"""

import os
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class APIKeyConfig:
    """Configuration for API key management."""

    # Supported API keys
    SUPPORTED_KEYS = {
        'OPENAI_API_KEY': 'OpenAI API key for GPT models',
        'ELEVENLABS_API_KEY': 'ElevenLabs API key for text-to-speech',
        'ELEVENLABS_VOICE_ID': 'ElevenLabs voice ID for TTS synthesis',
        'OPENWEATHERMAP_API_KEY': 'OpenWeatherMap API key for weather data',
        'ANTHROPIC_API_KEY': 'Anthropic API key for Claude models',
        'GOOGLE_API_KEY': 'Google API key for various services',
        'AZURE_OPENAI_KEY': 'Azure OpenAI API key',
        'HUGGINGFACE_API_KEY': 'Hugging Face API key',
        'DEEPL_API_KEY': 'DeepL API key for translation',
    }

    # Default .env file locations to check
    env_file_paths: list = field(default_factory=lambda: [
        '.env',
        '.env.local',
        '~/.flexiai/.env',
        os.path.expanduser('~/.config/flexiai/.env')
    ])

    # Whether to create missing config directories
    create_config_dirs: bool = True

    # Whether to use encrypted storage (requires cryptography package)
    use_encryption: bool = False


class APIKeyManager:
    """Secure API key management system."""

    def __init__(self, config: Optional[APIKeyConfig] = None):
        """Initialize the API key manager."""
        self.config = config or APIKeyConfig()
        self._keys_cache: Dict[str, str] = {}
        self._load_env_files()

        # Try to import cryptography for encryption support
        self._encryption_available = False
        try:
            from cryptography.fernet import Fernet
            self._encryption_available = True
        except ImportError:
            if self.config.use_encryption:
                print("⚠️ Cryptography package not installed. Encryption disabled.")

    def _load_env_files(self):
        """Load environment variables from .env files."""
        for env_path in self.config.env_file_paths:
            expanded_path = os.path.expanduser(env_path)
            if os.path.exists(expanded_path):
                self._load_env_file(expanded_path)

    def _load_env_file(self, file_path: str):
        """Load a single .env file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")

                        # Only set if not already in environment
                        if key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            print(f"⚠️ Warning: Could not load .env file {file_path}: {e}")

    def get_key(self, key_name: str, required: bool = False) -> Optional[str]:
        """
        Get an API key securely.

        Args:
            key_name: Name of the API key (e.g., 'OPENAI_API_KEY')
            required: Whether the key is required (raises exception if missing)

        Returns:
            The API key value or None if not found

        Raises:
            ValueError: If required=True and key is not found
        """
        # Check cache first
        if key_name in self._keys_cache:
            return self._keys_cache[key_name]

        # Try environment variable
        key_value = os.getenv(key_name)

        if key_value:
            # Validate key format
            if self._validate_key(key_name, key_value):
                self._keys_cache[key_name] = key_value
                return key_value
            else:
                print(f"⚠️ Warning: {key_name} has invalid format")

        # Try encrypted storage if available
        if self._encryption_available and self.config.use_encryption:
            encrypted_key = self._get_encrypted_key(key_name)
            if encrypted_key:
                self._keys_cache[key_name] = encrypted_key
                return encrypted_key

        if required:
            raise ValueError(f"Required API key '{key_name}' not found. Please set it as an environment variable or in a .env file.")

        return None

    def set_key(self, key_name: str, key_value: str, encrypt: bool = False):
        """
        Set an API key.

        Args:
            key_name: Name of the API key
            key_value: The API key value
            encrypt: Whether to store the key encrypted (requires cryptography)
        """
        if not self._validate_key(key_name, key_value):
            raise ValueError(f"Invalid key format for {key_name}")

        # Update cache
        self._keys_cache[key_name] = key_value

        # Store encrypted if requested and available
        if encrypt and self._encryption_available:
            self._set_encrypted_key(key_name, key_value)
        else:
            # Store in environment for current session
            os.environ[key_name] = key_value

    def _validate_key(self, key_name: str, key_value: str) -> bool:
        """Validate API key format."""
        if not key_value or len(key_value.strip()) < 10:
            return False

        # Basic format validation for known keys
        validations = {
            'OPENAI_API_KEY': lambda k: k.startswith('sk-'),
            'ELEVENLABS_API_KEY': lambda k: len(k) >= 32,
            'ELEVENLABS_VOICE_ID': lambda k: len(k) >= 16 and len(k) <= 32 and k.replace('-', '').isalnum(),
            'OPENWEATHERMAP_API_KEY': lambda k: len(k) == 32 and k.isalnum(),
            'ANTHROPIC_API_KEY': lambda k: k.startswith('sk-ant-'),
        }

        validator = validations.get(key_name)
        if validator:
            return validator(key_value)

        return True  # Default: accept if no specific validation

    def _get_encrypted_key(self, key_name: str) -> Optional[str]:
        """Get encrypted key from secure storage."""
        if not self._encryption_available:
            return None

        try:
            config_dir = os.path.expanduser('~/.config/flexiai')
            key_file = os.path.join(config_dir, 'keys.enc')

            if not os.path.exists(key_file):
                return None

            # Load encryption key
            key_key_file = os.path.join(config_dir, '.key')
            if not os.path.exists(key_key_file):
                return None

            with open(key_key_file, 'rb') as f:
                encryption_key = f.read()

            from cryptography.fernet import Fernet
            cipher = Fernet(encryption_key)

            # Load and decrypt keys
            with open(key_file, 'rb') as f:
                encrypted_data = f.read()

            decrypted_data = cipher.decrypt(encrypted_data)
            keys_dict = json.loads(decrypted_data.decode('utf-8'))

            return keys_dict.get(key_name)

        except Exception as e:
            print(f"⚠️ Error reading encrypted key {key_name}: {e}")
            return None

    def _set_encrypted_key(self, key_name: str, key_value: str):
        """Set encrypted key in secure storage."""
        if not self._encryption_available:
            return

        try:
            from cryptography.fernet import Fernet

            config_dir = os.path.expanduser('~/.config/flexiai')
            os.makedirs(config_dir, mode=0o700, exist_ok=True)

            key_file = os.path.join(config_dir, 'keys.enc')
            key_key_file = os.path.join(config_dir, '.key')

            # Generate or load encryption key
            if os.path.exists(key_key_file):
                with open(key_key_file, 'rb') as f:
                    encryption_key = f.read()
            else:
                encryption_key = Fernet.generate_key()
                with open(key_key_file, 'wb') as f:
                    f.write(encryption_key)
                os.chmod(key_key_file, 0o600)

            cipher = Fernet(encryption_key)

            # Load existing keys or create new dict
            keys_dict = {}
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = cipher.decrypt(encrypted_data)
                keys_dict = json.loads(decrypted_data.decode('utf-8'))

            # Add new key
            keys_dict[key_name] = key_value

            # Encrypt and save
            json_data = json.dumps(keys_dict)
            encrypted_data = cipher.encrypt(json_data.encode('utf-8'))

            with open(key_file, 'wb') as f:
                f.write(encrypted_data)
            os.chmod(key_file, 0o600)

        except Exception as e:
            print(f"❌ Error storing encrypted key {key_name}: {e}")

    def list_available_keys(self) -> Dict[str, bool]:
        """List all supported keys and their availability."""
        result = {}
        for key_name, description in self.config.SUPPORTED_KEYS.items():
            result[key_name] = {
                'description': description,
                'available': self.get_key(key_name) is not None,
                'source': self._get_key_source(key_name)
            }
        return result

    def _get_key_source(self, key_name: str) -> str:
        """Determine where a key is coming from."""
        if key_name in os.environ:
            return 'environment'
        elif self._encryption_available and self._get_encrypted_key(key_name):
            return 'encrypted'
        else:
            return 'not_found'

    def create_env_template(self, file_path: str = '.env'):
        """Create a template .env file with all supported keys."""
        template_content = [
            "# FlexiAI API Keys Configuration",
            "# Copy this file and fill in your actual API keys",
            "# Keep this file secure and never commit it to version control!",
            ""
        ]

        for key_name, description in self.config.SUPPORTED_KEYS.items():
            template_content.extend([
                f"# {description}",
                f"{key_name}=your_{key_name.lower()}_here",
                ""
            ])

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(template_content))

        print(f"✅ Created .env template at {file_path}")
        print("⚠️ Remember to:")
        print("   1. Add your actual API keys")
        print("   2. Keep this file secure")
        print("   3. Add .env to your .gitignore")


# Global instance for easy access
api_keys = APIKeyManager()


def get_api_key(key_name: str, required: bool = False) -> Optional[str]:
    """Convenience function to get an API key."""
    return api_keys.get_key(key_name, required=required)


def set_api_key(key_name: str, key_value: str, encrypt: bool = False):
    """Convenience function to set an API key."""
    api_keys.set_key(key_name, key_value, encrypt=encrypt)


def setup_api_keys():
    """Interactive setup for API keys."""
    print("🔐 FlexiAI API Key Setup")
    print("=" * 40)

    available_keys = api_keys.list_available_keys()

    print("\nCurrent API Key Status:")
    for key_name, info in available_keys.items():
        status = "✅ Available" if info['available'] else "❌ Missing"
        source = f"({info['source']})" if info['available'] else ""
        print(f"  {key_name}: {status} {source}")
        print(f"    {info['description']}")

    print(f"\n💡 Setup Options:")
    print("1. Create .env template file")
    print("2. Set individual API keys interactively")
    print("3. Show setup instructions")

    try:
        choice = input("\nEnter your choice (1-3): ").strip()

        if choice == '1':
            api_keys.create_env_template()
        elif choice == '2':
            _interactive_key_setup()
        elif choice == '3':
            _show_setup_instructions()
        else:
            print("Invalid choice. Exiting.")

    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")


def _interactive_key_setup():
    """Interactive API key setup."""
    print("\n🔧 Interactive API Key Setup")
    print("Press Enter to skip a key, or Ctrl+C to exit")

    for key_name, description in api_keys.config.SUPPORTED_KEYS.items():
        current_key = api_keys.get_key(key_name)
        status = "✅ Set" if current_key else "❌ Not set"

        print(f"\n{key_name} - {description}")
        print(f"Status: {status}")

        if current_key:
            masked_key = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "***"
            print(f"Current: {masked_key}")

            update = input("Update? (y/N): ").strip().lower()
            if update != 'y':
                continue

        try:
            new_key = input(f"Enter {key_name}: ").strip()
            if new_key:
                api_keys.set_key(key_name, new_key)
                print("✅ Key set successfully")
        except KeyboardInterrupt:
            print("\nSetup cancelled.")
            break
        except Exception as e:
            print(f"❌ Error setting key: {e}")


def _show_setup_instructions():
    """Show detailed setup instructions."""
    instructions = """
🔐 FlexiAI API Key Setup Instructions

1. ENVIRONMENT VARIABLES (Recommended)
   Set API keys as environment variables:

   Linux/Mac:
   export OPENAI_API_KEY="your-key-here"
   export ELEVENLABS_API_KEY="your-key-here"

   Windows:
   set OPENAI_API_KEY=your-key-here
   set ELEVENLABS_API_KEY=your-key-here

2. .ENV FILE
   Create a .env file in your project root:

   OPENAI_API_KEY=your-key-here
   ELEVENLABS_API_KEY=your-key-here
   OPENWEATHERMAP_API_KEY=your-key-here

3. PROGRAMMATICALLY
   Use the API key manager in your code:

   from flexiai.config.api_keys import set_api_key
   set_api_key('OPENAI_API_KEY', 'your-key-here')

SECURITY NOTES:
- Never hardcode API keys in source code
- Add .env files to .gitignore
- Use environment variables in production
- Consider encrypted storage for sensitive environments

API KEY SOURCES:
- OpenAI: https://platform.openai.com/api-keys
- ElevenLabs: https://elevenlabs.io/app/speech-synthesis
- OpenWeatherMap: https://openweathermap.org/api
"""
    print(instructions)


if __name__ == "__main__":
    setup_api_keys()
