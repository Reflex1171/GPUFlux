"""Price aggregation engine — the heart of GPUFlux."""

from __future__ import annotations

import asyncio
from typing import Optional

from gpuflux.core.config import Config
from gpuflux.core.models import GPUOffering
from gpuflux.providers.base import BaseProvider
from gpuflux.providers.registry import get_enabled_providers


async def fetch_prices(
    config: Config,
    gpu_filter: Optional[str] = None,
    max_price: Optional[float] = None,
    sort_by: str = "price",
) -> list[GPUOffering]:
    """
    Fetch live GPU pricing from all enabled providers.

    Args:
        config: GPUFlux configuration with provider credentials.
        gpu_filter: Optional GPU type to filter by (e.g. "A100").
        max_price: Maximum price per hour to include.
        sort_by: Sort key — "price" (default) or "available".

    Returns:
        Sorted list of GPU offerings across all providers.
    """
    providers: list[BaseProvider] = get_enabled_providers(config)

    if not providers:
        return []

    # Fetch from all providers concurrently
    tasks = [provider.fetch_offerings() for provider in providers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    offerings: list[GPUOffering] = []
    for result in results:
        if isinstance(result, Exception):
            # Log but don't crash — partial results are fine
            continue
        offerings.extend(result)

    # Apply filters
    if gpu_filter:
        gpu_upper = gpu_filter.upper().replace(" ", "_")
        offerings = [
            o for o in offerings
            if gpu_upper in o.gpu_type.value.upper()
        ]

    if max_price is not None:
        offerings = [o for o in offerings if o.price_per_hour <= max_price]

    # Sort
    if sort_by == "price":
        offerings.sort(key=lambda o: o.price_per_hour)
    elif sort_by == "available":
        offerings.sort(key=lambda o: o.available, reverse=True)

    return offerings


def find_cheapest(
    offerings: list[GPUOffering],
    gpu_count: int = 1,
    min_vram: Optional[int] = None,
) -> Optional[GPUOffering]:
    """Find the cheapest offering matching requirements."""
    for offering in sorted(offerings, key=lambda o: o.price_per_hour):
        if offering.available < gpu_count:
            continue
        if min_vram and offering.vram_gb < min_vram:
            continue
        return offering
    return None
