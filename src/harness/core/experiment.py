"""Experiment and MetricResult data models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from harness.core.result import TestCaseResult


class MetricResult(BaseModel):
    """Result of an aggregated metric calculation."""

    name: str
    value: float
    formatted_value: str
    direction: str = "higher_is_better"  # "higher_is_better" | "lower_is_better" | "neutral"
    description: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class Experiment(BaseModel):
    """Represents a complete benchmark evaluation experiment run."""

    id: str
    name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    agent_info: dict[str, Any] = Field(default_factory=dict)
    benchmark_info: dict[str, Any] = Field(default_factory=dict)
    results: list[TestCaseResult] = Field(default_factory=list)
    metrics: dict[str, MetricResult] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def total_tests(self) -> int:
        return len(self.results)

    @property
    def passed_tests(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_tests(self) -> int:
        return self.total_tests - self.passed_tests

    @property
    def success_rate(self) -> float:
        if not self.results:
            return 0.0
        return self.passed_tests / self.total_tests
