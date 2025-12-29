"""Configuration Pydantic models for AI providers."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    """Resolved provider configuration ready for use."""

    base_url: str
    model: str
    api_key: str


class DirectAuthConfig(BaseModel):
    """Direct authentication - credentials in config file."""

    enable: bool = False
    auth_type: Literal["direct"]
    base_url: str
    model: str
    api_key: str


class EnvAuthConfig(BaseModel):
    """Environment variable authentication."""

    enable: bool = False
    auth_type: Literal["env"]
    base_url: str  # Environment variable name for base URL
    model: str  # Environment variable name for model
    api_key: str  # Environment variable name for API key
    default_base_url: Optional[str] = None  # Fallback if env var not set
    default_model: Optional[str] = None  # Fallback if env var not set


class DotenvAuthConfig(BaseModel):
    """Dotenv file authentication."""

    enable: bool = False
    auth_type: Literal["dotenv"]
    dotenv_path: str  # Path to .env file
    base_url: str  # Key name in .env file for base URL
    model: str  # Key name in .env file for model
    api_key: str  # Key name in .env file for API key
    default_base_url: Optional[str] = None  # Fallback if key not in .env
    default_model: Optional[str] = None  # Fallback if key not in .env


class ProviderInfo(BaseModel):
    """Information about a provider for display."""

    name: str
    enabled: bool
    auth_type: str
    model: Optional[str] = None
    base_url: Optional[str] = None
