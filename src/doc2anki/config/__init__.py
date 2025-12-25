"""Configuration module for doc2anki."""

from .loader import (
    ConfigError,
    get_provider_config,
    list_providers,
    fatal_exit,
)
from .models import ProviderConfig, ProviderInfo

__all__ = [
    "ConfigError",
    "ProviderConfig",
    "ProviderInfo",
    "get_provider_config",
    "list_providers",
    "fatal_exit",
]
