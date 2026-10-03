"""Agent protocol and output data models."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.core.trace import ToolCallRecord, Trace


class TokenUsage(BaseModel):
    """Token consumption accounting."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class AgentOutput(BaseModel):
    """Standardized result produced by an agent execution."""

    output: str | dict[str, Any] = ""
    latency: float | None = None
    token_usage: TokenUsage | None = None
    cost: float | None = None
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    trace: Trace | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None

    @property
    def is_error(self) -> bool:
        """True if the agent execution resulted in an error."""
        return self.error is not None

    @property
    def text(self) -> str:
        """Helper to get string representation of the output."""
        if isinstance(self.output, str):
            return self.output
        if isinstance(self.output, dict):
            import json

            return json.dumps(self.output)
        return str(self.output)


@runtime_checkable
class Agent(Protocol):
    """Protocol for any agent under evaluation."""

    def run(
        self,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> AgentOutput:
        """Execute the agent on the given input and return structured output."""
        ...
