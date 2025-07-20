#!/usr/bin/env python3
"""
FlexiAI API Key Setup Script

This script helps you securely configure API keys for FlexiAI services.
Run this script to set up your API keys for OpenAI, ElevenLabs, OpenWeatherMap, and other services.

Usage:
    python setup_api_keys.py
"""

import sys
import os
from pathlib import Path

# Add the package to the path so we can import from flexiai
sys.path.insert(0, str(Path(__file__).parent))

try:
    from flexiai.config.api_keys import setup_api_keys, api_keys, get_api_key
except ImportError as e:
    print(f"❌ Error importing FlexiAI: {e}")
    print("Make sure you're running this script from the FlexiAI root directory.")
    sys.exit(1)


def check_gitignore():
    """Check if .env is in .gitignore and add it if not."""
    gitignore_path = Path('.gitignore')

    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            content = f.read()

        if '.env' not in content:
            print("⚠️ Adding .env to .gitignore for security...")
            with open(gitignore_path, 'a') as f:
                f.write('\n# Environment variables (API keys)\n.env\n.env.local\n')
            print("✅ Updated .gitignore")
    else:
        print("⚠️ Creating .gitignore...")
        with open(gitignore_path, 'w') as f:
            f.write("""# Environment variables (API keys)
.env
.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
""")
        print("✅ Created .gitignore")


def main():
    """Main setup function."""
    print("🚀 Welcome to FlexiAI API Key Setup!")
    print("=" * 50)

    # Check and update .gitignore
    check_gitignore()

    # Show current status
    print("\n📊 Current API Key Status:")
    available_keys = api_keys.list_available_keys()

    has_any_keys = False
    for key_name, info in available_keys.items():
        if info['available']:
            has_any_keys = True
            status = "✅ Available"
            source = f"({info['source']})"
        else:
            status = "❌ Missing"
            source = ""

        print(f"  {key_name}: {status} {source}")

    if has_any_keys:
        print("\n✅ Some API keys are already configured!")
    else:
        print("\n⚠️ No API keys found. Let's set them up!")

    # Run the interactive setup
    print("\n" + "=" * 50)
    setup_api_keys()

    # Final status check
    print("\n" + "=" * 50)
    print("🎉 Setup Complete!")

    updated_keys = api_keys.list_available_keys()
    configured_count = sum(1 for info in updated_keys.values() if info['available'])
    total_count = len(updated_keys)

    print(f"📈 API Keys Configured: {configured_count}/{total_count}")

    if configured_count > 0:
        print("\n✅ You're ready to use FlexiAI!")
        print("🔗 Quick start:")
        print("   from flexiai.config.api_keys import get_api_key")
        print("   api_key = get_api_key('OPENAI_API_KEY')")
    else:
        print("\n💡 To get started, you'll need at least one API key.")
        print("🔗 Get your API keys from:")
        print("   • OpenAI: https://platform.openai.com/api-keys")
        print("   • ElevenLabs: https://elevenlabs.io/app/speech-synthesis")
        print("   • OpenWeatherMap: https://openweathermap.org/api")

    print("\n🔒 Security Reminder:")
    print("   • Your API keys are stored securely")
    print("   • .env files are added to .gitignore")
    print("   • Never share your API keys publicly")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled. Run this script again anytime!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        print("Please check your FlexiAI installation and try again.")
        sys.exit(1)
