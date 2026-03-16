"""Core data models for GPUFlux."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class GPUType(str, Enum):
    """Supported GPU types."""
    A100_40GB = "A100_40GB"
    A100_80GB = "A100_80GB"
    H100 = "H100"
    A10G = "A10G"
    RTX_4090 = "RTX_4090"
    RTX_3090 = "RTX_3090"
    V100 = "V100"
    T4 = "T4"
    L40 = "L40"


class ProviderName(str, Enum):
    """Supported providers."""
    LAMBDA_LABS = "lambda_labs"
    RUNPOD = "runpod"
    OVH = "ovh"
    HETZNER = "hetzner"
    AWS = "aws"
    GCP = "gcp"


class GPUOffering(BaseModel):
    """A single GPU offering from a provider with pricing."""
    provider: ProviderName
    gpu_type: GPUType
    gpu_count: int = 1
    vram_gb: int
    price_per_hour: float
    available: int = Field(description="Number of instances available")
    region: str
    spot: bool = False
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def display_gpu(self) -> str:
        return self.gpu_type.value.replace("_", " ")


class JobSpec(BaseModel):
    """Specification for a GPU job to deploy."""
    name: str
    gpu: str = Field(description="GPU type requested, e.g. 'A100'")
    gpu_count: int = 1
    min_vram: Optional[int] = Field(default=None, description="Minimum VRAM in GB")
    docker_image: str
    command: str
    upload: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    max_price: Optional[float] = Field(default=None, description="Max $/hr willing to pay")


class JobStatus(str, Enum):
    """Status of a deployed job."""
    PENDING = "pending"
    PROVISIONING = "provisioning"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


class DeployedJob(BaseModel):
    """A job that has been deployed to a provider."""
    job_id: str
    spec: JobSpec
    provider: ProviderName
    instance_id: str
    status: JobStatus = JobStatus.PENDING
    price_per_hour: float
    region: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    ip_address: Optional[str] = None

    @property
    def cost_so_far(self) -> float:
        if not self.started_at:
            return 0.0
        end = self.ended_at or datetime.utcnow()
        hours = (end - self.started_at).total_seconds() / 3600
        return round(hours * self.price_per_hour, 4)
