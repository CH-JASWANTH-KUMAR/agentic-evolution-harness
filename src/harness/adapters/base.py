"""Adapter protocol and registry for wrapping diverse agents."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar, Protocol, TypeVar, runtime_checkable

from harness.core.agent import Agent


@runtime_checkable
class AgentAdapter(Protocol):
    """Protocol for creating an Agent instance from configuration."""

    def create_agent(self, **config: Any) -> Agent:
        """Instantiate and return an Agent adhering to the standard protocol."""
        ...


T_adapter = TypeVar("T_adapter", bound=type)


class AdapterRegistry:
    """Registry for discovering and instantiating agent adapters."""

    _registry: ClassVar[dict[str, type]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[T_adapter], T_adapter]:
        """Decorator to register an agent adapter."""

        def decorator(adapter_cls: T_adapter) -> T_adapter:
            cls._registry[name.lower()] = adapter_cls
            return adapter_cls

        return decorator

    @classmethod
    def get(cls, name: str, **config: Any) -> Agent:
        """Instantiate an agent adapter by registered name."""
        key = name.lower()
        if key not in cls._registry:
            available = ", ".join(sorted(cls._registry.keys()))
            raise KeyError(
                f"Agent adapter '{name}' is not registered. Available adapters: [{available}]"
            )
        target = cls._registry[key]
        if hasattr(target, "create_agent") and callable(target.create_agent):
            return target().create_agent(**config)  # type: ignore[no-any-return]
        return target(**config)  # type: ignore[no-any-return]

    @classmethod
    def list_available(cls) -> list[str]:
        """Return list of all registered adapter names."""
        return sorted(cls._registry.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear registry for testing."""
        cls._registry.clear()
