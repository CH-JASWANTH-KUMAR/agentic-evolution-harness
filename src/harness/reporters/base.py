"""Reporter protocol and registry for formatting experiment results."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar, Protocol, TypeVar, runtime_checkable

from harness.core.experiment import Experiment


@runtime_checkable
class Reporter(Protocol):
    """Protocol for generating formatted reports from an Experiment."""

    def report(self, experiment: Experiment, destination: Path | None = None) -> str:
        """Generate and optionally save an experiment report, returning string output."""
        ...


T_reporter = TypeVar("T_reporter", bound=type)


class ReporterRegistry:
    """Registry for discovering and instantiating reporters."""

    _registry: ClassVar[dict[str, type]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[T_reporter], T_reporter]:
        """Decorator to register a reporter."""

        def decorator(rep_cls: T_reporter) -> T_reporter:
            cls._registry[name.lower()] = rep_cls
            return rep_cls

        return decorator

    @classmethod
    def get(cls, name: str, **options: Any) -> Reporter:
        """Instantiate a reporter by registered name."""
        key = name.lower()
        if key not in cls._registry:
            available = ", ".join(sorted(cls._registry.keys()))
            raise KeyError(
                f"Reporter '{name}' is not registered. Available reporters: [{available}]"
            )
        rep_cls = cls._registry[key]
        return rep_cls(**options)  # type: ignore[no-any-return]

    @classmethod
    def list_available(cls) -> list[str]:
        """Return list of all registered reporter names."""
        return sorted(cls._registry.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear the registry."""
        cls._registry.clear()
