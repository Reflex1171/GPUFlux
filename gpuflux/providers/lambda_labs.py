"""Lambda Labs provider implementation."""

from __future__ import annotations

from datetime import datetime

import httpx

from gpuflux.core.models import GPUOffering, GPUType, ProviderName
from gpuflux.providers.base import BaseProvider

# Mapping from Lambda Labs instance types to our GPU types
LAMBDA_GPU_MAP: dict[str, GPUType] = {
    "gpu_1x_a100": GPUType.A100_40GB,
    "gpu_1x_a100_sxm4": GPUType.A100_80GB,
    "gpu_1x_h100_sxm5": GPUType.H100,
    "gpu_1x_a10": GPUType.A10G,
    "gpu_8x_a100_80gb_sxm4": GPUType.A100_80GB,
    "gpu_8x_h100_sxm5": GPUType.H100,
}

LAMBDA_VRAM: dict[GPUType, int] = {
    GPUType.A100_40GB: 40,
    GPUType.A100_80GB: 80,
    GPUType.H100: 80,
    GPUType.A10G: 24,
}

LAMBDA_API_BASE = "https://cloud.lambdalabs.com/api/v1"


class LambdaLabsProvider(BaseProvider):
    """Lambda Labs GPU cloud provider."""

    name = "lambda_labs"

    async def fetch_offerings(self) -> list[GPUOffering]:
        """Fetch available instances from Lambda Labs API."""
        offerings: list[GPUOffering] = []

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{LAMBDA_API_BASE}/instance-types",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()

        for instance_type, info in data.get("data", {}).items():
            instance_info = info.get("instance_type", {})
            price = instance_info.get("price_cents_per_hour", 0) / 100
            gpu_type = LAMBDA_GPU_MAP.get(instance_type)
            gpu_count = instance_info.get("specs", {}).get("gpus", 1)

            if not gpu_type:
                continue

            # Each region with availability
            for region in info.get("regions_with_capacity_available", []):
                region_name = region.get("name", "unknown")
                offerings.append(
                    GPUOffering(
                        provider=ProviderName.LAMBDA_LABS,
                        gpu_type=gpu_type,
                        gpu_count=gpu_count,
                        vram_gb=LAMBDA_VRAM.get(gpu_type, 0),
                        price_per_hour=price,
                        available=1,  # Lambda doesn't expose count per region
                        region=region_name,
                        spot=False,
                        fetched_at=datetime.utcnow(),
                    )
                )

        return offerings

    async def deploy(self, instance_type: str, region: str, **kwargs: object) -> str:
        """Launch an instance on Lambda Labs."""
        ssh_key_names = kwargs.get("ssh_key_names", [])

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{LAMBDA_API_BASE}/instance-operations/launch",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "region_name": region,
                    "instance_type_name": instance_type,
                    "ssh_key_names": ssh_key_names,
                    "quantity": 1,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()

        instance_ids = data.get("data", {}).get("instance_ids", [])
        if not instance_ids:
            raise RuntimeError("Lambda Labs returned no instance IDs")
        return instance_ids[0]

    async def terminate(self, instance_id: str) -> bool:
        """Terminate a Lambda Labs instance."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{LAMBDA_API_BASE}/instance-operations/terminate",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"instance_ids": [instance_id]},
                timeout=15.0,
            )
            resp.raise_for_status()
        return True

    async def status(self, instance_id: str) -> str:
        """Get instance status."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{LAMBDA_API_BASE}/instances/{instance_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()

        return data.get("data", {}).get("status", "unknown")
