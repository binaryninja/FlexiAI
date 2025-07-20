#!/bin/bash

# FlexiAI GPU Installation Script
# Handles PyTorch and Dia TTS dependencies for different GPU generations

set -e

echo "🚀 FlexiAI GPU Installation Script"
echo "=================================="

# Detect GPU type
detect_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        GPU_INFO=$(nvidia-smi --query-gpu=name --format=csv,noheader,nounits 2>/dev/null | head -1)
        echo "Detected GPU: $GPU_INFO"

        if [[ $GPU_INFO == *"RTX 5090"* ]] || [[ $GPU_INFO == *"RTX 5080"* ]]; then
            echo "RTX 50-series detected - using CUDA 12.8"
            CUDA_VERSION="cu128"
            TORCH_INDEX="https://download.pytorch.org/whl/cu128"
        elif [[ $GPU_INFO == *"RTX 40"* ]] || [[ $GPU_INFO == *"RTX 4090"* ]] || [[ $GPU_INFO == *"RTX 4080"* ]]; then
            echo "RTX 40-series detected - using CUDA 12.1"
            CUDA_VERSION="cu121"
            TORCH_INDEX="https://download.pytorch.org/whl/cu121"
        elif [[ $GPU_INFO == *"RTX"* ]] || [[ $GPU_INFO == *"GTX"* ]]; then
            echo "Older NVIDIA GPU detected - using CUDA 11.8"
            CUDA_VERSION="cu118"
            TORCH_INDEX="https://download.pytorch.org/whl/cu118"
        else
            echo "Unknown NVIDIA GPU - using CUDA 12.1 as default"
            CUDA_VERSION="cu121"
            TORCH_INDEX="https://download.pytorch.org/whl/cu121"
        fi
    else
        echo "No NVIDIA GPU detected - using CPU-only PyTorch"
        CUDA_VERSION="cpu"
        TORCH_INDEX="https://download.pytorch.org/whl/cpu"
    fi
}

# Install PyTorch
install_pytorch() {
    echo ""
    echo "📦 Installing PyTorch for $CUDA_VERSION..."

    if [[ $CUDA_VERSION == "cpu" ]]; then
        pip install torch torchvision torchaudio --index-url $TORCH_INDEX
    else
        pip install torch torchvision torchaudio --index-url $TORCH_INDEX
    fi

    echo "✅ PyTorch installation complete"

    # Verify installation
    python -c "import torch; print(f'PyTorch {torch.__version__} installed successfully')"
    if [[ $CUDA_VERSION != "cpu" ]]; then
        python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
        python -c "import torch; print(f'CUDA Version: {torch.version.cuda}')" 2>/dev/null || echo "CUDA version info not available"
    fi
}

# Install core dependencies
install_core_deps() {
    echo ""
    echo "📦 Installing core FlexiAI dependencies..."

    pip install \
        faster-whisper>=0.9.0 \
        sounddevice>=0.4.6 \
        pydub>=0.25.0 \
        pynput>=1.7.6 \
        webrtcvad>=2.0.10 \
        pyperclip>=1.8.2 \
        notify2>=0.3.1 \
        numpy>=1.21.0 \
        psutil>=5.9.0 \
        elevenlabs>=1.0.0

    echo "✅ Core dependencies installed"
}

# Install Voxtral/Transformers dependencies
install_voxtral_deps() {
    echo ""
    echo "📦 Installing Voxtral/Transformers dependencies..."

    pip install \
        git+https://github.com/huggingface/transformers \
        "mistral-common[audio]>=1.8.1" \
        "accelerate>=1.9.0"

    echo "✅ Voxtral dependencies installed"
}

# Install Dia TTS (with dependency override)
install_dia_tts() {
    echo ""
    echo "📦 Installing Dia TTS (forcing compatibility with latest PyTorch)..."

    # First, try to install Dia TTS ignoring dependency conflicts
    pip install git+https://github.com/nari-labs/dia.git --force-reinstall --no-deps || {
        echo "⚠️  Direct Dia installation failed, trying alternative approach..."

        # Download and install manually if needed
        pip install git+https://github.com/nari-labs/dia.git --force-reinstall || {
            echo "⚠️  Dia TTS installation failed - continuing without it"
            echo "    You can still use ElevenLabs and other TTS models"
            return 0
        }
    }

    # Test if Dia works with current PyTorch
    python -c "
try:
    import dia
    print('✅ Dia TTS installed successfully')
except ImportError as e:
    print(f'⚠️  Dia TTS import failed: {e}')
    print('    FlexiAI will work without Dia TTS')
except Exception as e:
    print(f'⚠️  Dia TTS test failed: {e}')
    print('    FlexiAI will work without Dia TTS')
" 2>/dev/null || echo "⚠️  Dia TTS verification failed - continuing anyway"
}

# Test installation
test_installation() {
    echo ""
    echo "🧪 Testing FlexiAI installation..."

    # Test core imports
    python -c "
import sys
import torch
import sounddevice as sd
import numpy as np
from pydub import AudioSegment

print('✅ Core dependencies working')
print(f'✅ PyTorch {torch.__version__}')
print(f'✅ CUDA Available: {torch.cuda.is_available()}')

if torch.cuda.is_available():
    print(f'✅ GPU: {torch.cuda.get_device_name(0)}')
    print(f'✅ CUDA Version: {torch.version.cuda}')

# Test FlexiAI import
try:
    import flexiai
    print('✅ FlexiAI package import successful')
except ImportError as e:
    print(f'⚠️  FlexiAI import failed: {e}')
    print('    Run: pip install -e . in the FlexiAI directory')
"

    echo ""
    echo "🎉 Installation complete!"
    echo ""
    echo "Next steps:"
    echo "1. Run: pip install -e . (in the FlexiAI directory)"
    echo "2. Set up your API keys:"
    echo "   export ELEVENLABS_API_KEY='your-key'"
    echo "   export OPENAI_API_KEY='your-key'"
    echo "3. Test with: flexiai --debug --tts"
}

# Main installation flow
main() {
    echo "Starting FlexiAI GPU installation..."
    echo ""

    # Check if we're in a virtual environment
    if [[ -z "$VIRTUAL_ENV" ]]; then
        echo "⚠️  WARNING: Not in a virtual environment"
        echo "   It's recommended to use a virtual environment:"
        echo "   python -m venv venv && source venv/bin/activate"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    detect_gpu
    install_pytorch
    install_core_deps
    install_voxtral_deps
    install_dia_tts
    test_installation
}

# Parse command line arguments
case "${1:-}" in
    --pytorch-only)
        detect_gpu
        install_pytorch
        ;;
    --no-dia)
        detect_gpu
        install_pytorch
        install_core_deps
        install_voxtral_deps
        test_installation
        ;;
    --help|-h)
        echo "FlexiAI GPU Installation Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --pytorch-only    Install only PyTorch for detected GPU"
        echo "  --no-dia         Install everything except Dia TTS"
        echo "  --help, -h       Show this help message"
        echo ""
        echo "Default: Install everything including PyTorch, core deps, and Dia TTS"
        ;;
    *)
        main
        ;;
esac
