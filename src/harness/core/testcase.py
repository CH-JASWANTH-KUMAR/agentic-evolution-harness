"""TestCase and EvaluatorConfig data models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvaluatorConfig(BaseModel):
    """Configuration for an evaluator attached to a test case or benchmark."""

    name: str
    options: dict[str, Any] = Field(default_factory=dict)
    weight: float = 1.0


class TestCase(BaseModel):
    """A standardized test case for evaluating an AI agent."""

    __test__ = False

    id: str
    name: str
    description: str | None = None
    input: str | dict[str, Any]
    expected: Any | None = None
    evaluators: list[EvaluatorConfig] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def input_text(self) -> str:
        """Helper to get string representation of input."""
        if isinstance(self.input, str):
            return self.input
        if isinstance(self.input, dict):
            import json

            return json.dumps(self.input)
        return str(self.input)
