"""Metric protocol and registry for cross-benchmark metrics."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from enum import StrEnum
from typing import Any, ClassVar, Protocol, TypeVar, runtime_checkable

from harness.core.experiment import MetricResult
from harness.core.result import TestCaseResult


class MetricDirection(StrEnum):
    """Indicates whether higher or lower metric values represent improvement."""

    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    NEUTRAL = "neutral"


@runtime_checkable
class Metric(Protocol):
    """Protocol for cross-benchmark aggregate metric plugins."""

    name: str
    direction: MetricDirection

    def calculate(self, results: Sequence[TestCaseResult]) -> MetricResult:
        """Compute aggregate metric across all test case results."""
        ...


T_metric = TypeVar("T_metric", bound=type)


class MetricRegistry:
    """Registry for discovering and instantiating metrics by name."""

    _registry: ClassVar[dict[str, type]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[T_metric], T_metric]:
        """Decorator to register a metric implementation."""

        def decorator(metric_cls: T_metric) -> T_metric:
            cls._registry[name.lower()] = metric_cls
            return metric_cls

        return decorator

    @classmethod
    def get(cls, name: str, **options: Any) -> Metric:
        """Instantiate a metric by registered name."""
        key = name.lower()
        if key not in cls._registry:
            available = ", ".join(sorted(cls._registry.keys()))
            raise KeyError(f"Metric '{name}' is not registered. Available metrics: [{available}]")
        metric_cls = cls._registry[key]
        return metric_cls(**options)  # type: ignore[no-any-return]

    @classmethod
    def list_available(cls) -> list[str]:
        """Return list of all registered metric names."""
        return sorted(cls._registry.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear the registry (useful for testing)."""
        cls._registry.clear()
