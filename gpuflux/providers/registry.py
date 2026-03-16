"""Provider registry — maps names to provider classes."""

from __future__ import annotations

from typing import Type

from gpuflux.core.config import Config
from gpuflux.providers.base import BaseProvider
from gpuflux.providers.lambda_labs import LambdaLabsProvider
from gpuflux.providers.runpod import RunPodProvider

PROVIDER_REGISTRY: dict[str, Type[BaseProvider]] = {
    "lambda_labs": LambdaLabsProvider,
    "runpod": RunPodProvider,
}


def get_enabled_providers(config: Config) -> list[BaseProvider]:
    """Instantiate all providers that are enabled and have credentials."""
    providers: list[BaseProvider] = []

    for name, provider_cls in PROVIDER_REGISTRY.items():
        provider_config = config.get_provider(name)
        if provider_config and provider_config.enabled and provider_config.api_key:
            providers.append(provider_cls(api_key=provider_config.api_key))

    return providers
