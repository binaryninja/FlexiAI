#!/usr/bin/env python3
"""
Setup script for FlexiAI package.
"""

import os
import re
from setuptools import setup, find_packages

# Read version from __init__.py
def get_version():
    with open(os.path.join(os.path.dirname(__file__), 'flexiai', '__init__.py'), 'r') as f:
        content = f.read()
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.M)
        if version_match:
            return version_match.group(1)
        raise RuntimeError("Unable to find version string.")

# Read README for long description
def get_long_description():
    with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r', encoding='utf-8') as f:
        return f.read()

# Read requirements
def get_requirements():
    with open(os.path.join(os.path.dirname(__file__), 'requirements.txt'), 'r') as f:
        requirements = []
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                # Remove inline comments
                if '#' in line:
                    line = line.split('#')[0].strip()
                requirements.append(line)
        return requirements

setup(
    name="flexiai",
    version=get_version(),
    author="binaryninja",
    author_email="",
    description="Modular AI Assistant with Hotkey Activation - Supporting Local and Remote Models for Transcription, LLM Chat, and Streaming TTS",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/binaryninja/FlexiAI",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Utilities",
        "Environment :: Console",
        "Environment :: No Input/Output (Daemon)",
    ],
    python_requires=">=3.8",
    install_requires=get_requirements(),
    extras_require={
        "gpu": [
            "torch>=2.0.0",
            "torchvision>=0.15.0",
            "torchaudio>=2.0.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "flexiai=flexiai.main:main",
            "holdtranscribe=flexiai.main:main",  # Keep backward compatibility
        ],
    },
    keywords="ai assistant voice transcription whisper hotkey llm tts speech-to-text text-to-speech local remote models modular",
    project_urls={
        "Bug Reports": "https://github.com/binaryninja/FlexiAI/issues",
        "Source": "https://github.com/binaryninja/FlexiAI",
    },
    include_package_data=True,
    zip_safe=False,
)
