# ⚡ GPUFlux

**Stop overpaying for GPU compute. GPUFlux finds the cheapest provider and deploys your AI workload in one command.**

GPU prices vary 3–5x across providers at any given moment. A training job costing $10/hr on AWS might cost $3/hr on bare-metal. GPUFlux checks live pricing across multiple providers and deploys your workload to the cheapest option — automatically.

## The Problem

- You're running AI/ML workloads and burning money on GPU compute
- Prices vary wildly between providers, but you don't have time to price-shop
- Managing a mix of cloud VMs and dedicated servers is painful
- When a spot instance gets reclaimed, your job dies

## The Solution

```bash
gpuflux deploy --gpu A100 --job ./train.yaml
```

GPUFlux handles the rest: finds the cheapest available GPU across providers, provisions the server, deploys your job, and monitors it.

## Features

- 🔍 **Live Price Comparison** — Real-time pricing from multiple GPU providers
- 🚀 **One-Command Deploy** — Define your job once, deploy anywhere
- 💰 **Cost Optimization** — Automatically selects the cheapest option matching your requirements
- 📊 **Spend Tracking** — See exactly what you're spending and what you're saving
- 🔌 **Provider Agnostic** — Works with OVH, Hetzner, Lambda Labs, RunPod, and more

## Quick Start

### Installation

```bash
pip install gpuflux
```

### Configure Providers

```bash
gpuflux init
```

This walks you through adding API credentials for your GPU providers.

### Check Prices

```bash
# See live GPU pricing across all configured providers
gpuflux prices --gpu A100

# Example output:
# Provider      | GPU     | $/hr  | Available | Region
# --------------|---------|-------|-----------|--------
# Lambda Labs   | A100    | 1.10  | 3         | us-west
# RunPod        | A100    | 1.64  | 12        | us-east
# OVH           | A100    | 2.10  | 2         | eu-west
# AWS (spot)    | A100    | 3.97  | 8         | us-east-1
```

### Deploy a Job

```yaml
# train.yaml
name: finetune-llama
gpu: A100
gpu_count: 1
min_vram: 80  # GB
docker_image: pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime
command: python train.py --model llama-7b --data ./data
upload:
  - ./train.py
  - ./data/
```

```bash
gpuflux deploy --job train.yaml
```

### Monitor

```bash
gpuflux status           # All running jobs
gpuflux logs <job-id>    # Stream logs from a running job
gpuflux spend            # Cost summary for the current month
```

## Supported Providers

| Provider    | Status      | GPU Types              |
|-------------|-------------|------------------------|
| Lambda Labs | ✅ Live      | A100, H100, A10G       |
| RunPod      | ✅ Live      | A100, H100, RTX 4090   |
| OVH         | 🚧 Coming   | A100, V100             |
| Hetzner     | 🚧 Coming   | —                      |
| AWS (Spot)  | 🚧 Coming   | A100, H100, various    |
| GCP (Spot)  | 📋 Planned  | A100, H100, T4         |

## Architecture

```
┌──────────────┐     ┌──────────────────────┐     ┌──────────────┐
│   CLI / API  │────▶│   GPUFlux Core       │────▶│  Providers   │
│              │     │                      │     │              │
│  gpuflux     │     │  • Price Aggregator  │     │  Lambda Labs │
│  deploy      │     │  • Job Scheduler     │     │  RunPod      │
│  prices      │     │  • Deploy Engine     │     │  OVH         │
│  status      │     │  • Monitor           │     │  AWS         │
└──────────────┘     └──────────────────────┘     └──────────────┘
```

## Roadmap

- [x] Core price comparison engine
- [x] CLI interface
- [x] Lambda Labs provider
- [x] RunPod provider
- [ ] OVH bare-metal provider
- [ ] Job checkpointing & migration
- [ ] Auto-failover on instance termination
- [ ] Web dashboard
- [ ] Team accounts & spend controls
- [ ] Spot instance preemption prediction

## Contributing

We're early stage and moving fast. If you're interested in contributing:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/add-provider`)
3. Commit your changes
4. Open a PR

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for more details.

## License

MIT License — see [LICENSE](LICENSE) for details.

## Links

- [Documentation](https://gpuflux.dev) *(coming soon)*
- [Discord](https://discord.gg/gpuflux) *(coming soon)*
- [Twitter/X](https://x.com/gpuflux) *(coming soon)*
