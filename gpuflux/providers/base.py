"""Base provider interface — all GPU providers implement this."""

from __future__ import annotations

from abc import ABC, abstractmethod

from gpuflux.core.models import GPUOffering


class BaseProvider(ABC):
    """Abstract base class for GPU cloud providers."""

    name: str

    def __init__(self, api_key: str | None = None, **kwargs: object) -> None:
        self.api_key = api_key

    @abstractmethod
    async def fetch_offerings(self) -> list[GPUOffering]:
        """Fetch current GPU offerings with live pricing."""
        ...

    @abstractmethod
    async def deploy(self, instance_type: str, region: str, **kwargs: object) -> str:
        """
        Provision an instance. Returns an instance ID.
        """
        ...

    @abstractmethod
    async def terminate(self, instance_id: str) -> bool:
        """Terminate a running instance."""
        ...

    @abstractmethod
    async def status(self, instance_id: str) -> str:
        """Get status of an instance."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
