"""Trace data models capturing observable agent execution without private chain-of-thought."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolCallRecord(BaseModel):
    """Structured record of an observed tool call by an agent."""

    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)
    output: Any | None = None
    duration: float | None = None
    status: Literal["success", "error"] = "success"
    error: str | None = None


class TraceStep(BaseModel):
    """An individual step or event during agent execution."""

    step_index: int = 0
    step_type: str = "action"
    content: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Trace(BaseModel):
    """Observable execution trace of an agent run."""

    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    steps: list[TraceStep] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
