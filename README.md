# FlexiAI 🤖

**A Modular AI Assistant with Hotkey Activation**

FlexiAI is a powerful, extensible AI assistant that supports local and remote models for speech-to-text transcription, LLM chat assistance, and real-time streaming text-to-speech. Originally evolved from HoldTranscribe, it now provides a complete AI interaction experience with plug-and-play model architecture.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform Support](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)](https://github.com/binaryninja/FlexiAI)

## ✨ Features

### 🎤 **Speech-to-Text Transcription**
- **Whisper Integration**: Support for OpenAI Whisper models (tiny to large-v3)
- **Hotkey Activation**: Hold customizable hotkeys to record and transcribe
- **Real-time Processing**: Live transcription with voice activity detection
- **Clipboard Integration**: Automatic copying of transcribed text

### 🧠 **LLM Chat Assistant**
- **Local Models**: Voxtral, Mistral, and other local LLMs
- **Remote APIs**: OpenAI GPT, Claude, and other cloud services
- **Context Awareness**: Maintains conversation context
- **Customizable Prompts**: Configurable system prompts and behaviors

### 🔊 **Real-time Streaming TTS**
- **ElevenLabs Integration**: High-quality voice synthesis with streaming
- **Local TTS Models**: Dia, Kyutai, and other local text-to-speech engines
- **Direct Audio Playback**: No external players needed
- **Low Latency**: Real-time audio streaming as text is generated
- **Multi-format Support**: PCM, MP3, and other audio formats

### 🔧 **Modular Architecture**
- **Plug-and-Play Models**: Easy model swapping and configuration
- **Extensible Framework**: Add new models and providers
- **Fallback Systems**: Automatic fallbacks when models fail
- **Resource Management**: Intelligent model loading/unloading

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/binaryninja/FlexiAI.git
cd FlexiAI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# GPU Support (CUDA) - Install PyTorch first:
# For RTX 5090 and newer (CUDA 12.8) - TESTED AND WORKING:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# For RTX 4090 and RTX 40-series (CUDA 12.1):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# For older GPUs (CUDA 11.8):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# CPU-only (no GPU acceleration):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install core dependencies
pip install -r requirements.txt

# Force install Dia TTS for compatibility with latest PyTorch:
pip install git+https://github.com/nari-labs/dia.git --force-reinstall --no-deps

# Install the package
pip install -e .

# Alternative: Use automated GPU installation script
chmod +x install_gpu.sh && ./install_gpu.sh
```

### Basic Usage

```bash
# Run with default configuration
flexiai

# Enable TTS for AI responses
flexiai --tts

# Use specific models
flexiai --transcription-model large-v3 --assistant-model voxtral --tts-model elevenlabs

# Debug mode
flexiai --debug --tts
```

### Hotkeys (Default)
- **Transcription**: `Ctrl + Mouse Forward Button` (hold to record, release to transcribe)
- **AI Assistant**: `Ctrl + Shift + Mouse Back Button` (hold to record, release for AI response)

## 🛠️ Configuration

### Command Line Options

```bash
# Model Configuration
--transcription-model MODEL     # Whisper model (tiny, base, small, medium, large-v3)
--assistant-model MODEL         # LLM model (voxtral, gpt-4, etc.)
--tts-model MODEL              # TTS model (elevenlabs, dia, etc.)

# Audio Configuration
--audio-buffer-size SIZE       # Audio buffer size in samples (default: 1024)
--audio-queue-size SIZE        # Audio queue maximum size (default: 10)
--audio-timeout SECONDS        # Audio playback timeout (default: 30.0)

# Hotkey Configuration
--transcribe-hotkey KEYS       # Transcription hotkey combination
--assistant-hotkey KEYS        # AI assistant hotkey combination

# Performance
--device DEVICE               # Processing device (auto, cpu, cuda)
--force-file-tts              # Force file-based TTS (disable streaming)

# Debug and Logging
--debug                       # Enable debug mode
--verbose                     # Verbose output
```

### Environment Variables

```bash
# API Keys
export OPENAI_API_KEY="your-openai-key"
export ELEVENLABS_API_KEY="your-elevenlabs-key"
export ANTHROPIC_API_KEY="your-claude-key"

# Audio Device Selection
export SOUNDDEVICE_DEFAULT_DEVICE=1

# Force fallback modes
export FLEXIAI_FORCE_SYSTEM_AUDIO=1
```

## 📋 Supported Models

### Speech-to-Text (Whisper)
- `tiny`, `base`, `small`, `medium`, `large-v3`
- Automatic language detection
- Multiple language support
- GPU acceleration with CUDA

### Large Language Models
- **Voxtral**: Local Mistral-based models
- **OpenAI**: GPT-3.5, GPT-4, GPT-4-turbo
- **Anthropic**: Claude models (when supported)
- **Local Models**: Any Hugging Face compatible model

### Text-to-Speech
- **ElevenLabs**: Cloud-based high-quality TTS with streaming
- **Dia**: Local neural TTS models
- **Kyutai**: Local TTS engines
- **System TTS**: Platform native TTS as fallback

## 🏗️ Architecture

### Model Factory System
```python
from flexiai.models import ModelFactory, ModelType

# Load models dynamically
transcription_model = ModelFactory.create_model(
    ModelType.TRANSCRIPTION, 
    "large-v3", 
    device="cuda"
)

assistant_model = ModelFactory.create_model(
    ModelType.ASSISTANT, 
    "voxtral", 
    device="cuda"
)

tts_model = ModelFactory.create_model(
    ModelType.TTS, 
    "elevenlabs", 
    api_key="your-key"
)
```

### Audio Pipeline
1. **Recording**: VAD-enabled audio capture with hotkey activation
2. **Transcription**: Whisper-based speech-to-text processing
3. **LLM Processing**: Context-aware AI response generation
4. **TTS Synthesis**: Real-time streaming or file-based audio generation
5. **Playback**: Direct audio device output with buffering

### Plugin Architecture
- **Model Wrappers**: Standardized interfaces for different model types
- **Provider Abstraction**: Support for local and remote model providers
- **Fallback Chains**: Automatic fallbacks when models fail
- **Resource Management**: Smart loading/unloading based on usage

## 🎛️ Advanced Usage

### Custom Model Configuration

```python
# Custom model wrapper
from flexiai.models import TTSModel, ModelType

class MyCustomTTS(TTSModel):
    def synthesize(self, text: str, output_file: str) -> bool:
        # Your custom TTS implementation
        pass
    
    def synthesize_streaming(self, text: str):
        # Your streaming implementation
        pass

# Register with factory
ModelFactory.register_model("mycustom", MyCustomTTS)
```

### Audio Configuration Tuning

```bash
# For low-latency systems
flexiai --audio-buffer-size 512 --audio-queue-size 5

# For high-quality/stable systems  
flexiai --audio-buffer-size 2048 --audio-queue-size 20

# Force PCM format for better streaming
flexiai --tts --debug  # Will attempt PCM formats automatically
```

### Integration Examples

```python
from flexiai.app import FlexiAIApp

# Programmatic usage
app = FlexiAIApp()
app.audio_buffer_size = 1024
app.force_file_tts = False

# Run with custom configuration
app.run()
```

## 🧪 Testing

```bash
# Test audio playback system
python test_audio_playback.py

# Test individual components
python -m pytest tests/ -v

# Performance testing
python tests/benchmark_models.py
```

## 🤝 Contributing

We welcome contributions! FlexiAI is designed to be extensible:

### Adding New Models
1. Implement the appropriate base class (`TranscriptionModel`, `AssistantModel`, `TTSModel`)
2. Register with the `ModelFactory`
3. Add configuration options
4. Write tests

### Adding New Features
1. Fork the repository
2. Create a feature branch
3. Implement your feature with tests
4. Submit a pull request

### Areas for Contribution
- **New Model Integrations**: More LLM providers, TTS engines
- **Audio Improvements**: Better streaming, noise reduction
- **Cross-platform**: Enhanced Windows/macOS support
- **UI/UX**: Optional GUI interface
- **Documentation**: Tutorials, examples, guides

## 📊 Performance

### Typical Latency (RTX 5090 TESTED - PyTorch 2.7.1+cu128)
- **Transcription**: ~0.5-2s (depending on audio length)
- **LLM Response**: ~0.5-3s (depending on model and response length)
- **TTS Streaming**: ~0.2-0.5s to first audio (ElevenLabs)
- **Total Round-trip**: ~1-6s for complete interaction

### Memory Usage (RTX 5090 Tested)
- **Base System**: ~500MB
- **With Whisper Large**: ~2GB
- **With Voxtral**: ~4-8GB
- **Peak Usage**: ~10-12GB (all models loaded)
- **RTX 5090**: Excellent performance with 24GB VRAM

## 🐛 Troubleshooting

### Common Issues

**No Audio Playback**
```bash
# Check audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Test audio system
python test_audio_playback.py

# Force system player fallback
flexiai --force-file-tts
```

**Model Loading Errors**
```bash
# Check CUDA availability and version
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"

# For RTX 5090 users - ensure CUDA 12.8 PyTorch (TESTED WORKING):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Fix Dia TTS compatibility issues:
pip install git+https://github.com/nari-labs/dia.git --force-reinstall --no-deps

# Force CPU mode if GPU issues persist
flexiai --device cpu

# Debug model loading
flexiai --debug
```

**Dia TTS Compatibility Issues**
```bash
# Force install Dia TTS with latest PyTorch (bypasses version conflicts):
pip install git+https://github.com/nari-labs/dia.git --force-reinstall --no-deps

# Test Dia TTS compatibility:
python -c "import dia; print('✅ Dia TTS working with PyTorch', __import__('torch').__version__)"
```

**Streaming TTS Issues**
```bash
# Check ElevenLabs API key
flexiai --debug --tts

# Force file-based TTS
flexiai --force-file-tts --tts
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI**: For Whisper speech recognition
- **Mistral AI**: For Voxtral language models
- **ElevenLabs**: For high-quality TTS APIs
- **Hugging Face**: For model hosting and transformers library
- **Contributors**: All community members who helped improve FlexiAI

## 🔗 Links

- **GitHub**: [https://github.com/binaryninja/FlexiAI](https://github.com/binaryninja/FlexiAI)
- **Issues**: [Report bugs and request features](https://github.com/binaryninja/FlexiAI/issues)
- **Discussions**: [Community discussions](https://github.com/binaryninja/FlexiAI/discussions)

---

**FlexiAI** - *Where AI meets flexibility* 🚀