#!/usr/bin/env python3
"""
Hold the chosen hot‑key(s) to record → transcribe → copy to clipboard.

Requirements:
  pip install faster-whisper sounddevice pynput webrtcvad pyperclip notify2 numpy torch
  pip install git+https://github.com/huggingface/transformers
  pip install --upgrade "mistral-common[audio]"
"""

import asyncio
import sys
from .app import FlexiAIApp

def main():
    """Main entry point for the HoldTranscribe application."""
    app = FlexiAIApp()
    return asyncio.run(app.run())

if __name__ == "__main__":
    sys.exit(main())
