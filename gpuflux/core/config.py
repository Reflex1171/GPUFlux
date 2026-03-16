"""Configuration management for GPUFlux."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field

CONFIG_DIR = Path.home() / ".gpuflux"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


class ProviderConfig(BaseModel):
    """Configuration for a single provider."""
    enabled: bool = True
    api_key: Optional[str] = None
    regions: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class Config(BaseModel):
    """Global GPUFlux configuration."""
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    default_gpu: str = "A100"
    max_price: Optional[float] = None

    @classmethod
    def load(cls) -> Config:
        """Load config from disk, or return defaults."""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                data = yaml.safe_load(f) or {}
            return cls.model_validate(data)
        return cls()

    def save(self) -> None:
        """Persist config to disk."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)

    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        """Get config for a specific provider."""
        return self.providers.get(name)

    def set_provider_key(self, name: str, api_key: str) -> None:
        """Set API key for a provider."""
        if name not in self.providers:
            self.providers[name] = ProviderConfig()
        self.providers[name].api_key = api_key
        # Also check env var as fallback
        env_key = f"GPUFLUX_{name.upper()}_API_KEY"
        if not api_key and os.environ.get(env_key):
            self.providers[name].api_key = os.environ[env_key]
