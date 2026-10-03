"""EvaluationResult and TestCaseResult data models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from harness.core.agent import AgentOutput
from harness.core.testcase import TestCase


class EvaluationResult(BaseModel):
    """Result of an individual evaluator on a test case."""

    evaluator: str
    score: float = Field(ge=0.0, le=1.0, description="Normalized score between 0.0 and 1.0")
    passed: bool
    explanation: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TestCaseResult(BaseModel):
    """Aggregated evaluation outcome for a single test case."""

    __test__ = False

    test_case: TestCase
    output: AgentOutput
    evaluations: list[EvaluationResult] = Field(default_factory=list)
    passed: bool = False
    duration: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def average_score(self) -> float:
        """Mean score across all evaluators for this test case."""
        if not self.evaluations:
            return 1.0 if self.passed else 0.0
        return sum(e.score for e in self.evaluations) / len(self.evaluations)
