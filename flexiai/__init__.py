"""
FlexiAI - Modular AI Assistant with Hotkey Activation

A powerful, modular AI assistant that supports local and remote models for:
- Speech-to-text transcription (Whisper)
- LLM chat and assistance (Voxtral, OpenAI, etc.)
- Real-time streaming text-to-speech (ElevenLabs, local TTS)

Features hotkey activation, plug-and-play model architecture, and direct audio device integration.
"""

__version__ = "1.0.1"
__author__ = "binaryninja"
__email__ = ""
__description__ = "Modular AI Assistant with Hotkey Activation - Supporting Local and Remote Models for Transcription, LLM Chat, and Streaming TTS"
__url__ = "https://github.com/binaryninja/FlexiAI"

from .main import main

__all__ = ["main", "__version__"]
