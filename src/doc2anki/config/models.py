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
    base_url_env: Optional[str] = None
    model_env: Optional[str] = None
    api_key: str  # Environment variable name containing the API key
    default_base_url: Optional[str] = None
    default_model: Optional[str] = None


class DotenvAuthConfig(BaseModel):
    """Dotenv file authentication."""

    enable: bool = False
    auth_type: Literal["dotenv"]
    dotenv_path: str
    base_url_key: Optional[str] = None
    model_key: Optional[str] = None
    api_key: str  # Key name in the dotenv file containing the API key
    default_base_url: Optional[str] = None
    default_model: Optional[str] = None


class ProviderInfo(BaseModel):
    """Information about a provider for display."""

    name: str
    enabled: bool
    auth_type: str
    model: Optional[str] = None
    base_url: Optional[str] = None
