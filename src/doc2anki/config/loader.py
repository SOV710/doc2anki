"""Configuration loader for AI providers."""

import os
import sys
from pathlib import Path
from typing import Any

import tomli
from dotenv import load_dotenv
from rich.console import Console

from .models import ProviderConfig, ProviderInfo

console = Console()


class ConfigError(Exception):
    """Configuration error that causes fatal exit."""

    pass


def load_toml_config(config_path: Path) -> dict[str, Any]:
    """Load TOML configuration file."""
    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "rb") as f:
            return tomli.load(f)
    except tomli.TOMLDecodeError as e:
        raise ConfigError(f"Invalid TOML in {config_path}: {e}")


def resolve_provider_config(
    provider_name: str, raw_config: dict[str, Any]
) -> ProviderConfig:
    """
    Resolve provider configuration based on auth_type.

    Supports three authentication methods:
    - direct: Credentials directly in config file
    - env: Read from environment variables
    - dotenv: Load from .env file then read as env vars
    """
    if "auth_type" not in raw_config:
        raise ConfigError(f"Provider '{provider_name}' missing 'auth_type' field")

    auth_type = raw_config["auth_type"]

    if auth_type == "direct":
        return _resolve_direct_auth(provider_name, raw_config)
    elif auth_type == "env":
        return _resolve_env_auth(provider_name, raw_config)
    elif auth_type == "dotenv":
        return _resolve_dotenv_auth(provider_name, raw_config)
    else:
        raise ConfigError(
            f"Provider '{provider_name}' has unknown auth_type: {auth_type}"
        )


def _resolve_direct_auth(provider_name: str, config: dict[str, Any]) -> ProviderConfig:
    """Resolve direct authentication config."""
    required = ["base_url", "model", "api_key"]
    for field in required:
        if field not in config:
            raise ConfigError(
                f"Provider '{provider_name}' with auth_type=direct missing '{field}'"
            )

    return ProviderConfig(
        base_url=config["base_url"],
        model=config["model"],
        api_key=config["api_key"],
    )


def _resolve_env_auth(provider_name: str, config: dict[str, Any]) -> ProviderConfig:
    """Resolve environment variable authentication config."""
    if "api_key" not in config:
        raise ConfigError(
            f"Provider '{provider_name}' with auth_type=env missing 'api_key'"
        )

    api_key = os.getenv(config["api_key"])
    if not api_key:
        raise ConfigError(
            f"Provider '{provider_name}': environment variable "
            f"'{config['api_key']}' not set or empty"
        )

    # base_url field contains the env var name to look up
    base_url = None
    if "base_url" in config:
        base_url = os.getenv(config["base_url"])
    if not base_url:
        base_url = config.get("default_base_url")
    if not base_url:
        raise ConfigError(
            f"Provider '{provider_name}': no base_url available "
            f"(env var not set and no default)"
        )

    # model field contains the env var name to look up
    model = None
    if "model" in config:
        model = os.getenv(config["model"])
    if not model:
        model = config.get("default_model")
    if not model:
        raise ConfigError(
            f"Provider '{provider_name}': no model available "
            f"(env var not set and no default)"
        )

    return ProviderConfig(base_url=base_url, model=model, api_key=api_key)


def _resolve_dotenv_auth(provider_name: str, config: dict[str, Any]) -> ProviderConfig:
    """Resolve dotenv file authentication config."""
    if "dotenv_path" not in config:
        raise ConfigError(
            f"Provider '{provider_name}' with auth_type=dotenv missing 'dotenv_path'"
        )
    if "api_key" not in config:
        raise ConfigError(
            f"Provider '{provider_name}' with auth_type=dotenv missing 'api_key'"
        )

    dotenv_path = Path(config["dotenv_path"])
    if not dotenv_path.exists():
        raise ConfigError(
            f"Provider '{provider_name}': dotenv file not found: {dotenv_path}"
        )

    # Load the dotenv file
    load_dotenv(dotenv_path, override=True)

    api_key = os.getenv(config["api_key"])
    if not api_key:
        raise ConfigError(
            f"Provider '{provider_name}': key '{config['api_key']}' "
            f"not found in {dotenv_path}"
        )

    # base_url field contains the key name to look up in dotenv
    base_url = None
    if "base_url" in config:
        base_url = os.getenv(config["base_url"])
    if not base_url:
        base_url = config.get("default_base_url")
    if not base_url:
        raise ConfigError(
            f"Provider '{provider_name}': no base_url available "
            f"(not in dotenv and no default)"
        )

    # model field contains the key name to look up in dotenv
    model = None
    if "model" in config:
        model = os.getenv(config["model"])
    if not model:
        model = config.get("default_model")
    if not model:
        raise ConfigError(
            f"Provider '{provider_name}': no model available "
            f"(not in dotenv and no default)"
        )

    return ProviderConfig(base_url=base_url, model=model, api_key=api_key)


def get_provider_config(config_path: Path, provider_name: str) -> ProviderConfig:
    """
    Load and resolve configuration for a specific provider.

    Args:
        config_path: Path to the TOML configuration file
        provider_name: Name of the provider to load

    Returns:
        Resolved ProviderConfig ready for use

    Raises:
        ConfigError: If configuration is invalid or provider not found
    """
    all_config = load_toml_config(config_path)

    if provider_name not in all_config:
        available = [k for k in all_config.keys() if isinstance(all_config[k], dict)]
        raise ConfigError(
            f"Provider '{provider_name}' not found in config. "
            f"Available providers: {', '.join(available)}"
        )

    provider_config = all_config[provider_name]

    if not isinstance(provider_config, dict):
        raise ConfigError(f"Provider '{provider_name}' configuration must be a table")

    if not provider_config.get("enable", False):
        raise ConfigError(f"Provider '{provider_name}' is not enabled")

    return resolve_provider_config(provider_name, provider_config)


def _resolve_display_values_env(config: dict[str, Any]) -> tuple[str | None, str | None]:
    """Resolve base_url and model for env auth type for display purposes."""
    base_url = None
    model = None

    # base_url/model fields contain env var names
    if "base_url" in config:
        base_url = os.getenv(config["base_url"])
    if not base_url:
        base_url = config.get("default_base_url")

    if "model" in config:
        model = os.getenv(config["model"])
    if not model:
        model = config.get("default_model")

    return base_url, model


def _resolve_display_values_dotenv(
    config: dict[str, Any],
) -> tuple[str | None, str | None]:
    """Resolve base_url and model for dotenv auth type for display purposes."""
    base_url = None
    model = None

    # Try to load dotenv file if it exists
    if "dotenv_path" in config:
        dotenv_path = Path(config["dotenv_path"])
        if dotenv_path.exists():
            load_dotenv(dotenv_path, override=True)

            # base_url/model fields contain key names in dotenv
            if "base_url" in config:
                base_url = os.getenv(config["base_url"])
            if "model" in config:
                model = os.getenv(config["model"])

    # Fallback to defaults
    if not base_url:
        base_url = config.get("default_base_url")
    if not model:
        model = config.get("default_model")

    return base_url, model


def list_providers(config_path: Path, show_all: bool = False) -> list[ProviderInfo]:
    """
    List all providers from configuration.

    Args:
        config_path: Path to the TOML configuration file
        show_all: If True, include disabled providers

    Returns:
        List of ProviderInfo objects
    """
    all_config = load_toml_config(config_path)
    providers = []

    for name, config in all_config.items():
        if not isinstance(config, dict):
            continue

        enabled = config.get("enable", False)
        if not enabled and not show_all:
            continue

        auth_type = config.get("auth_type", "unknown")

        # Resolve actual model and base_url values
        model = None
        base_url = None

        if auth_type == "direct":
            model = config.get("model")
            base_url = config.get("base_url")
        elif auth_type == "env":
            base_url, model = _resolve_display_values_env(config)
        elif auth_type == "dotenv":
            base_url, model = _resolve_display_values_dotenv(config)

        providers.append(
            ProviderInfo(
                name=name,
                enabled=enabled,
                auth_type=auth_type,
                model=model,
                base_url=base_url,
            )
        )

    return providers


def fatal_exit(message: str) -> None:
    """Print error message and exit."""
    console.print(f"[red]Error:[/red] {message}")
    sys.exit(1)
