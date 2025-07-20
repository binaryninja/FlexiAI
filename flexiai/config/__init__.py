"""
Configuration management for FlexiAI.

This package provides secure configuration management including API key storage,
environment variable handling, and encrypted key storage.
"""

from .api_keys import (
    APIKeyManager,
    APIKeyConfig,
    api_keys,
    get_api_key,
    set_api_key,
    setup_api_keys
)

__all__ = [
    'APIKeyManager',
    'APIKeyConfig',
    'api_keys',
    'get_api_key',
    'set_api_key',
    'setup_api_keys'
]
