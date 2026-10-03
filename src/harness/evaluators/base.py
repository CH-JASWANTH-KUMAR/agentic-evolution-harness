"""Evaluator protocol and registry for modular evaluator plugins."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar, Protocol, TypeVar, runtime_checkable

from harness.core.agent import AgentOutput
from harness.core.result import EvaluationResult
from harness.core.testcase import TestCase


@runtime_checkable
class Evaluator(Protocol):
    """Protocol for single-test evaluation plugins."""

    name: str

    def evaluate(self, test_case: TestCase, output: AgentOutput) -> EvaluationResult:
        """Evaluate agent output against expected result in a test case."""
        ...


T_evaluator = TypeVar("T_evaluator", bound=type)


class EvaluatorRegistry:
    """Registry for discovering and instantiating evaluators by name."""

    _registry: ClassVar[dict[str, type]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[T_evaluator], T_evaluator]:
        """Decorator to register an evaluator implementation."""

        def decorator(eval_cls: T_evaluator) -> T_evaluator:
            cls._registry[name.lower()] = eval_cls
            return eval_cls

        return decorator

    @classmethod
    def get(cls, name: str, **options: Any) -> Evaluator:
        """Instantiate an evaluator by registered name with optional configuration."""
        key = name.lower()
        if key not in cls._registry:
            available = ", ".join(sorted(cls._registry.keys()))
            raise KeyError(
                f"Evaluator '{name}' is not registered. Available evaluators: [{available}]"
            )
        eval_cls = cls._registry[key]
        return eval_cls(**options)  # type: ignore[no-any-return]

    @classmethod
    def list_available(cls) -> list[str]:
        """Return list of all registered evaluator names."""
        return sorted(cls._registry.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear the registry (useful for testing)."""
        cls._registry.clear()
