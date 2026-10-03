"""Benchmark schema and validation models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from harness.core.testcase import EvaluatorConfig, TestCase


class BenchmarkAgentConfig(BaseModel):
    """Specification for the agent under test."""

    adapter: str = "generic"
    module: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class BenchmarkConfig(BaseModel):
    """Declarative specification of an evaluation benchmark."""

    version: str = "1.0"
    name: str
    description: str | None = None
    agent: BenchmarkAgentConfig = Field(default_factory=BenchmarkAgentConfig)
    evaluators: list[EvaluatorConfig] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=lambda: ["success_rate"])
    thresholds: dict[str, dict[str, float]] = Field(default_factory=dict)
    tests: list[TestCase] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
