"""RunPod provider implementation."""

from __future__ import annotations

from datetime import datetime

import httpx

from gpuflux.core.models import GPUOffering, GPUType, ProviderName
from gpuflux.providers.base import BaseProvider

RUNPOD_GPU_MAP: dict[str, GPUType] = {
    "NVIDIA A100 80GB PCIe": GPUType.A100_80GB,
    "NVIDIA A100-SXM4-80GB": GPUType.A100_80GB,
    "NVIDIA H100 80GB HBM3": GPUType.H100,
    "NVIDIA GeForce RTX 4090": GPUType.RTX_4090,
    "NVIDIA GeForce RTX 3090": GPUType.RTX_3090,
    "NVIDIA L40": GPUType.L40,
}

RUNPOD_VRAM: dict[str, int] = {
    "NVIDIA A100 80GB PCIe": 80,
    "NVIDIA A100-SXM4-80GB": 80,
    "NVIDIA H100 80GB HBM3": 80,
    "NVIDIA GeForce RTX 4090": 24,
    "NVIDIA GeForce RTX 3090": 24,
    "NVIDIA L40": 48,
}

RUNPOD_API_BASE = "https://api.runpod.io/graphql"

QUERY_GPU_TYPES = """
query GpuTypes {
    gpuTypes {
        id
        displayName
        memoryInGb
        secureCloud
        communityCloud
        lowestPrice(input: {gpuCount: 1}) {
            minimumBidPrice
            uninterruptablePrice
        }
    }
}
"""


class RunPodProvider(BaseProvider):
    """RunPod GPU cloud provider."""

    name = "runpod"

    async def fetch_offerings(self) -> list[GPUOffering]:
        """Fetch GPU offerings from RunPod GraphQL API."""
        offerings: list[GPUOffering] = []

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                RUNPOD_API_BASE,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"query": QUERY_GPU_TYPES},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()

        for gpu in data.get("data", {}).get("gpuTypes", []):
            display_name = gpu.get("displayName", "")
            gpu_type = RUNPOD_GPU_MAP.get(display_name)
            if not gpu_type:
                continue

            lowest = gpu.get("lowestPrice") or {}
            on_demand_price = lowest.get("uninterruptablePrice")
            spot_price = lowest.get("minimumBidPrice")

            vram = gpu.get("memoryInGb", RUNPOD_VRAM.get(display_name, 0))

            # On-demand offering
            if on_demand_price:
                offerings.append(
                    GPUOffering(
                        provider=ProviderName.RUNPOD,
                        gpu_type=gpu_type,
                        gpu_count=1,
                        vram_gb=vram,
                        price_per_hour=on_demand_price,
                        available=1,  # RunPod doesn't expose exact count
                        region="us",  # RunPod abstracts regions
                        spot=False,
                        fetched_at=datetime.utcnow(),
                    )
                )

            # Spot/community offering
            if spot_price and spot_price > 0:
                offerings.append(
                    GPUOffering(
                        provider=ProviderName.RUNPOD,
                        gpu_type=gpu_type,
                        gpu_count=1,
                        vram_gb=vram,
                        price_per_hour=spot_price,
                        available=1,
                        region="us-community",
                        spot=True,
                        fetched_at=datetime.utcnow(),
                    )
                )

        return offerings

    async def deploy(self, instance_type: str, region: str, **kwargs: object) -> str:
        """Deploy a pod on RunPod."""
        # RunPod uses GraphQL mutations for pod creation
        raise NotImplementedError("RunPod deploy coming in v0.2")

    async def terminate(self, instance_id: str) -> bool:
        """Terminate a RunPod pod."""
        raise NotImplementedError("RunPod terminate coming in v0.2")

    async def status(self, instance_id: str) -> str:
        """Get pod status."""
        raise NotImplementedError("RunPod status coming in v0.2")
