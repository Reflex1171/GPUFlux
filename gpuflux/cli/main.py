"""GPUFlux CLI — main entry point."""

from __future__ import annotations

import asyncio
import sys

import click
from rich.console import Console
from rich.table import Table

from gpuflux.core.aggregator import fetch_prices, find_cheapest
from gpuflux.core.config import Config

console = Console()


@click.group()
@click.version_option(package_name="gpuflux")
def cli() -> None:
    """⚡ GPUFlux — Stop overpaying for GPU compute."""
    pass


@cli.command()
def init() -> None:
    """Set up GPUFlux with your provider API keys."""
    config = Config.load()

    console.print("\n⚡ [bold]GPUFlux Setup[/bold]\n")
    console.print("Let's configure your GPU providers.\n")

    # Lambda Labs
    console.print("[bold]1. Lambda Labs[/bold]")
    console.print("   Get your API key at: https://cloud.lambdalabs.com/api-keys")
    key = click.prompt("   API key (or press Enter to skip)", default="", show_default=False)
    if key:
        config.set_provider_key("lambda_labs", key)
        console.print("   ✅ Lambda Labs configured\n")
    else:
        console.print("   ⏭️  Skipped\n")

    # RunPod
    console.print("[bold]2. RunPod[/bold]")
    console.print("   Get your API key at: https://www.runpod.io/console/user/settings")
    key = click.prompt("   API key (or press Enter to skip)", default="", show_default=False)
    if key:
        config.set_provider_key("runpod", key)
        console.print("   ✅ RunPod configured\n")
    else:
        console.print("   ⏭️  Skipped\n")

    config.save()

    enabled = [name for name, pc in config.providers.items() if pc.api_key]
    if enabled:
        console.print(f"🎉 Config saved! {len(enabled)} provider(s) configured.")
        console.print("   Run [bold]gpuflux prices[/bold] to see live GPU pricing.\n")
    else:
        console.print("⚠️  No providers configured. Run [bold]gpuflux init[/bold] again when you have API keys.\n")


def _demo_offerings() -> list:
    """Return realistic mock offerings for demo mode."""
    from datetime import datetime
    from gpuflux.core.models import GPUOffering, GPUType, ProviderName
    return [
        GPUOffering(provider=ProviderName.LAMBDA_LABS, gpu_type=GPUType.A100_80GB, vram_gb=80, price_per_hour=1.10, available=3, region="us-west-1", spot=False, fetched_at=datetime.utcnow()),
        GPUOffering(provider=ProviderName.RUNPOD,      gpu_type=GPUType.A100_80GB, vram_gb=80, price_per_hour=1.34, available=8, region="us-east-1", spot=True,  fetched_at=datetime.utcnow()),
        GPUOffering(provider=ProviderName.RUNPOD,      gpu_type=GPUType.A100_80GB, vram_gb=80, price_per_hour=1.64, available=12, region="us-east-1", spot=False, fetched_at=datetime.utcnow()),
        GPUOffering(provider=ProviderName.LAMBDA_LABS, gpu_type=GPUType.H100,      vram_gb=80, price_per_hour=2.49, available=2, region="us-east-1", spot=False, fetched_at=datetime.utcnow()),
        GPUOffering(provider=ProviderName.RUNPOD,      gpu_type=GPUType.H100,      vram_gb=80, price_per_hour=2.79, available=5, region="eu-central-1", spot=False, fetched_at=datetime.utcnow()),
        GPUOffering(provider=ProviderName.LAMBDA_LABS, gpu_type=GPUType.A10G,      vram_gb=24, price_per_hour=0.60, available=10, region="us-west-1", spot=False, fetched_at=datetime.utcnow()),
        GPUOffering(provider=ProviderName.RUNPOD,      gpu_type=GPUType.RTX_4090,  vram_gb=24, price_per_hour=0.74, available=20, region="us-east-1", spot=False, fetched_at=datetime.utcnow()),
        GPUOffering(provider=ProviderName.AWS,         gpu_type=GPUType.A100_80GB, vram_gb=80, price_per_hour=3.97, available=8, region="us-east-1", spot=True,  fetched_at=datetime.utcnow()),
    ]


@cli.command()
@click.option("--gpu", default=None, help="Filter by GPU type (e.g. A100, H100)")
@click.option("--max-price", default=None, type=float, help="Maximum $/hr")
@click.option("--sort", "sort_by", default="price", type=click.Choice(["price", "available"]))
@click.option("--demo", is_flag=True, help="Run with mock data — no API keys required")
def prices(gpu: str | None, max_price: float | None, sort_by: str, demo: bool) -> None:
    """Show live GPU pricing across all providers."""
    if demo:
        offerings = _demo_offerings()
        if gpu:
            gpu_upper = gpu.upper().replace(" ", "_")
            offerings = [o for o in offerings if gpu_upper in o.gpu_type.value.upper()]
        if max_price is not None:
            offerings = [o for o in offerings if o.price_per_hour <= max_price]
        offerings.sort(key=lambda o: o.price_per_hour if sort_by == "price" else -o.available)
        console.print("\n[dim]⚡ Demo mode — prices are illustrative, not live.[/dim]")
    else:
        config = Config.load()
        offerings = asyncio.run(fetch_prices(config, gpu_filter=gpu, max_price=max_price, sort_by=sort_by))

    if not offerings:
        console.print("\n⚠️  No offerings found. Check your config with [bold]gpuflux init[/bold].\n")
        return

    table = Table(title="⚡ Live GPU Prices", show_lines=False)
    table.add_column("Provider", style="cyan")
    table.add_column("GPU", style="green")
    table.add_column("VRAM", justify="right")
    table.add_column("$/hr", justify="right", style="yellow bold")
    table.add_column("Available", justify="right")
    table.add_column("Region")
    table.add_column("Spot", justify="center")

    for o in offerings:
        table.add_row(
            o.provider.value,
            o.display_gpu,
            f"{o.vram_gb}GB",
            f"${o.price_per_hour:.2f}",
            str(o.available),
            o.region,
            "⚡" if o.spot else "",
        )

    console.print()
    console.print(table)
    console.print()

    cheapest = find_cheapest(offerings)
    if cheapest:
        console.print(
            f"💰 Cheapest: [bold]{cheapest.display_gpu}[/bold] on "
            f"[cyan]{cheapest.provider.value}[/cyan] at "
            f"[yellow bold]${cheapest.price_per_hour:.2f}/hr[/yellow bold] "
            f"({cheapest.region})\n"
        )


@cli.command()
@click.argument("job_file", type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True, help="Show what would happen without deploying")
def deploy(job_file: str, dry_run: bool) -> None:
    """Deploy a GPU job to the cheapest available provider."""
    import yaml
    from gpuflux.core.models import JobSpec

    config = Config.load()

    with open(job_file) as f:
        job_data = yaml.safe_load(f)

    spec = JobSpec.model_validate(job_data)

    console.print(f"\n⚡ Deploying [bold]{spec.name}[/bold]")
    console.print(f"   GPU: {spec.gpu} x{spec.gpu_count}")
    if spec.min_vram:
        console.print(f"   Min VRAM: {spec.min_vram}GB")
    console.print(f"   Image: {spec.docker_image}")
    console.print()

    # Find cheapest offering
    offerings = asyncio.run(fetch_prices(config, gpu_filter=spec.gpu, max_price=spec.max_price))
    cheapest = find_cheapest(offerings, gpu_count=spec.gpu_count, min_vram=spec.min_vram)

    if not cheapest:
        console.print("❌ No available GPUs matching your requirements.\n")
        sys.exit(1)

    console.print(
        f"🎯 Best match: [cyan]{cheapest.provider.value}[/cyan] — "
        f"{cheapest.display_gpu} at [yellow bold]${cheapest.price_per_hour:.2f}/hr[/yellow bold] "
        f"({cheapest.region})"
    )

    if dry_run:
        console.print("\n[dim]Dry run — no instance launched.[/dim]\n")
        return

    console.print("\n🚀 Provisioning instance...")
    console.print("[dim]Deploy functionality coming in v0.2[/dim]\n")


@cli.command()
def status() -> None:
    """Show status of running jobs."""
    console.print("\n📊 No running jobs.\n")
    console.print("[dim]Job tracking coming in v0.2[/dim]\n")


@cli.command()
def spend() -> None:
    """Show cost summary for the current period."""
    console.print("\n💰 Spend tracking coming in v0.2\n")


if __name__ == "__main__":
    cli()
