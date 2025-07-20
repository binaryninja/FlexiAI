# Voice Configuration Guide

This guide explains how to configure and customize the voice used for text-to-speech (TTS) synthesis in FlexiAI.

## Overview

FlexiAI supports voice customization through the ElevenLabs TTS integration. You can:

- Set a default voice using environment variables
- Override voices programmatically
- Switch voices at runtime
- List and explore available voices

## Quick Start

### 1. Set Your Preferred Voice

Set the `ELEVENLABS_VOICE_ID` environment variable:

```bash
# Linux/Mac
export ELEVENLABS_VOICE_ID="21m00Tcm4TlvDq8ikWAM"

# Windows (Command Prompt)
set ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Windows (PowerShell)
$env:ELEVENLABS_VOICE_ID="21m00Tcm4TlvDq8ikWAM"
```

### 2. Use FlexiAI with TTS

```bash
flexiai --tts
```

Your specified voice will be used automatically!

## Configuration Methods

### Environment Variable (Recommended)

Set `ELEVENLABS_VOICE_ID` in your environment:

```bash
export ELEVENLABS_API_KEY="your_api_key"
export ELEVENLABS_VOICE_ID="21m00Tcm4TlvDq8ikWAM"
```

### .env File

Create or edit a `.env` file in your project root:

```env
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

### Programmatic Configuration

```python
from flexiai.models import ModelFactory

# Method 1: Pass voice_id during model creation
model = ModelFactory.create_tts_model(
    model_name="elevenlabs",
    device="cpu",
    voice_id="21m00Tcm4TlvDq8ikWAM"
)

# Method 2: Change voice after model creation
model = ModelFactory.create_tts_model("elevenlabs", "cpu")
model.load()
model.set_voice_parameters("EXAVITQu4vr4xnSDxMaL")
```

## Finding Voice IDs

### List Available Voices

```python
from flexiai.models import ModelFactory

model = ModelFactory.create_tts_model("elevenlabs", "cpu")
model.load()

voices = model.get_available_voices()
for voice in voices:
    print(f"Name: {voice['name']}")
    print(f"ID: {voice['voice_id']}")
    print(f"Category: {voice['category']}")
    print("---")
```

### Popular Voice IDs

Here are some popular ElevenLabs voices:

| Voice Name | Voice ID | Description |
|------------|----------|-------------|
| Rachel | `21m00Tcm4TlvDq8ikWAM` | Young, female, American |
| Drew | `29vD33N1CtxCmqQRPOHJ` | Middle-aged, male, American |
| Bella | `EXAVITQu4vr4xnSDxMaL` | Young, female, American |
| Antoni | `ErXwobaYiN019PkySvjV` | Middle-aged, male, American |
| Elli | `MF3mGyEYCl7XYWbV9V6O` | Young, female, American |
| Josh | `TxGEqnHWrfWFTfGW9XjX` | Young, male, American |

## Configuration Priority

FlexiAI uses the following priority order for voice selection:

1. **Explicit parameter** - `voice_id` passed to model creation
2. **Environment variable** - `ELEVENLABS_VOICE_ID`
3. **Default voice** - Built-in fallback voice

Example:
```python
# This will use "explicit_voice_id" regardless of environment variable
model = ModelFactory.create_tts_model(
    "elevenlabs", "cpu", 
    voice_id="explicit_voice_id"
)

# This will use ELEVENLABS_VOICE_ID if set, otherwise default
model = ModelFactory.create_tts_model("elevenlabs", "cpu")
```

## Advanced Usage

### Voice Settings Customization

```python
model.set_voice_parameters(
    voice_id="21m00Tcm4TlvDq8ikWAM",
    stability=0.7,          # 0.0 to 1.0
    similarity_boost=0.8,   # 0.0 to 1.0
    style=0.5,              # 0.0 to 1.0
    use_speaker_boost=True
)
```

### Runtime Voice Switching

```python
# Start with one voice
model.set_voice_parameters("21m00Tcm4TlvDq8ikWAM")
model.synthesize("Hello with Rachel's voice", "rachel.mp3")

# Switch to another voice
model.set_voice_parameters("EXAVITQu4vr4xnSDxMaL")
model.synthesize("Hello with Bella's voice", "bella.mp3")
```

## Integration with FlexiAI CLI

When using the FlexiAI command-line interface:

```bash
# Set voice via environment (recommended)
export ELEVENLABS_VOICE_ID="21m00Tcm4TlvDq8ikWAM"
flexiai --tts

# Voice will be used for all assistant responses
```

## Troubleshooting

### Voice Not Working

1. **Check API Key**: Ensure `ELEVENLABS_API_KEY` is set correctly
2. **Verify Voice ID**: Use the voice listing feature to confirm the ID exists
3. **Check Permissions**: Some voices may require specific subscription tiers

### Voice ID Validation

Valid voice IDs are typically:
- 16-32 characters long
- Alphanumeric with possible hyphens
- Case-sensitive

### Debug Voice Selection

Enable debug logging to see which voice is being used:

```bash
flexiai --tts --debug
```

Look for log messages like:
```
Using voice ID from environment variable: 21m00Tcm4TlvDq8ikWAM
```

## Examples

### Basic Setup Script

```bash
#!/bin/bash
# setup_voice.sh

# Set your ElevenLabs credentials
export ELEVENLABS_API_KEY="your_api_key_here"
export ELEVENLABS_VOICE_ID="21m00Tcm4TlvDq8ikWAM"

# Test the configuration
echo "Testing voice configuration..."
python -c "
from flexiai.models import ModelFactory
model = ModelFactory.create_tts_model('elevenlabs', 'cpu')
model.load()
print(f'Using voice: {model.voice_id}')
model.synthesize('Voice test successful!', 'test.mp3')
print('Test complete - check test.mp3')
"
```

### Voice Discovery Script

```python
#!/usr/bin/env python3
"""Discover and test ElevenLabs voices."""

from flexiai.models import ModelFactory

def discover_voices():
    model = ModelFactory.create_tts_model("elevenlabs", "cpu")
    if not model.load():
        print("Failed to load model")
        return
    
    voices = model.get_available_voices()
    print(f"Found {len(voices)} voices:")
    
    for voice in voices:
        print(f"\nName: {voice['name']}")
        print(f"ID: {voice['voice_id']}")
        print(f"Category: {voice.get('category', 'Unknown')}")
        
        # Test synthesis
        test_text = f"Hello, this is {voice['name']} speaking."
        output_file = f"test_{voice['name'].lower().replace(' ', '_')}.mp3"
        
        model.set_voice_parameters(voice['voice_id'])
        if model.synthesize(test_text, output_file):
            print(f"✅ Sample saved: {output_file}")
        else:
            print("❌ Synthesis failed")

if __name__ == "__main__":
    discover_voices()
```

## Best Practices

1. **Use Environment Variables**: Set `ELEVENLABS_VOICE_ID` for consistent voice across all applications
2. **Test Voices**: Use the discovery script to find voices that work well for your use case
3. **Document Voice Choices**: Keep track of voice IDs you prefer for different purposes
4. **Consider Context**: Different voices work better for different types of content
5. **Respect Limits**: Be mindful of API rate limits when testing multiple voices

## API Key Management

Voice configuration works alongside API key management. Use the FlexiAI API key system:

```python
from flexiai.config.api_keys import set_api_key, get_api_key

# Set keys programmatically
set_api_key('ELEVENLABS_API_KEY', 'your_api_key')
set_api_key('ELEVENLABS_VOICE_ID', 'your_voice_id')

# Get keys
api_key = get_api_key('ELEVENLABS_API_KEY')
voice_id = get_api_key('ELEVENLABS_VOICE_ID')
```

## Support

For voice-related issues:

1. Check the [ElevenLabs documentation](https://docs.elevenlabs.io/)
2. Verify your subscription includes the desired voices
3. Test voice IDs using the ElevenLabs web interface
4. Use the FlexiAI debug mode for detailed logging

## Related Documentation

- [ElevenLabs TTS Integration](./ELEVENLABS_INTEGRATION.md)
- [API Key Configuration](./API_KEYS.md)
- [FlexiAI CLI Reference](./CLI_REFERENCE.md)