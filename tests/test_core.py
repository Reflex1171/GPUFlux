"""Tests for GPUFlux core functionality."""

import pytest
from gpuflux.core.models import GPUOffering, GPUType, ProviderName, JobSpec
from gpuflux.core.aggregator import find_cheapest
from gpuflux.core.config import Config


def make_offering(**kwargs):
    """Helper to create test offerings."""
    defaults = {
        "provider": ProviderName.LAMBDA_LABS,
        "gpu_type": GPUType.A100_80GB,
        "gpu_count": 1,
        "vram_gb": 80,
        "price_per_hour": 1.10,
        "available": 3,
        "region": "us-west",
        "spot": False,
    }
    defaults.update(kwargs)
    return GPUOffering(**defaults)


class TestFindCheapest:
    def test_returns_cheapest(self):
        offerings = [
            make_offering(price_per_hour=3.00, provider=ProviderName.AWS),
            make_offering(price_per_hour=1.10, provider=ProviderName.LAMBDA_LABS),
            make_offering(price_per_hour=1.64, provider=ProviderName.RUNPOD),
        ]
        result = find_cheapest(offerings)
        assert result is not None
        assert result.provider == ProviderName.LAMBDA_LABS
        assert result.price_per_hour == 1.10

    def test_respects_min_vram(self):
        offerings = [
            make_offering(price_per_hour=0.50, vram_gb=24),
            make_offering(price_per_hour=1.10, vram_gb=80),
        ]
        result = find_cheapest(offerings, min_vram=40)
        assert result is not None
        assert result.vram_gb == 80

    def test_respects_gpu_count(self):
        offerings = [
            make_offering(price_per_hour=0.50, available=1),
            make_offering(price_per_hour=1.10, available=4),
        ]
        result = find_cheapest(offerings, gpu_count=2)
        assert result is not None
        assert result.available >= 2

    def test_returns_none_when_no_match(self):
        offerings = [
            make_offering(price_per_hour=1.10, vram_gb=24),
        ]
        result = find_cheapest(offerings, min_vram=80)
        assert result is None

    def test_empty_offerings(self):
        assert find_cheapest([]) is None


class TestJobSpec:
    def test_basic_spec(self):
        spec = JobSpec(
            name="test-job",
            gpu="A100",
            docker_image="pytorch/pytorch:latest",
            command="python train.py",
        )
        assert spec.name == "test-job"
        assert spec.gpu_count == 1
        assert spec.max_price is None

    def test_full_spec(self):
        spec = JobSpec(
            name="finetune",
            gpu="H100",
            gpu_count=2,
            min_vram=80,
            docker_image="nvcr.io/nvidia/pytorch:23.10",
            command="torchrun --nproc_per_node=2 train.py",
            upload=["./train.py", "./data/"],
            env={"WANDB_API_KEY": "xxx"},
            max_price=5.00,
        )
        assert spec.gpu_count == 2
        assert spec.max_price == 5.00
        assert len(spec.upload) == 2


class TestConfig:
    def test_default_config(self):
        config = Config()
        assert config.default_gpu == "A100"
        assert len(config.providers) == 0

    def test_set_provider_key(self):
        config = Config()
        config.set_provider_key("lambda_labs", "test-key-123")
        assert config.providers["lambda_labs"].api_key == "test-key-123"
