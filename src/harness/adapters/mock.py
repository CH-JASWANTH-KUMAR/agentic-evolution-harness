"""Mock agent for deterministic testing and demonstrations without network calls."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from harness.adapters.base import AdapterRegistry
from harness.core.agent import Agent, AgentOutput, TokenUsage
from harness.core.trace import ToolCallRecord, Trace


@AdapterRegistry.register("mock")
class MockAgent:
    """Configurable mock agent returning deterministic responses."""

    def __init__(
        self,
        default_output: str = "Mock response",
        responses: dict[str, str | dict[str, Any]] | None = None,
        tool_calls: list[ToolCallRecord] | None = None,
        latency: float = 0.05,
        token_usage: dict[str, int] | None = None,
        cost: float | None = None,
        handler: Callable[[str | dict[str, Any]], AgentOutput] | None = None,
        should_error: bool = False,
        error_message: str = "Mock execution failure",
    ) -> None:
        self.default_output = default_output
        self.responses = responses or {}
        self.tool_calls = tool_calls or []
        self.latency = latency
        self.token_usage = token_usage or {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        }
        self.cost = cost if cost is not None else 0.0005
        self.handler = handler
        self.should_error = should_error
        self.error_message = error_message

    def run(
        self,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> AgentOutput:
        if self.latency > 0:
            time.sleep(min(self.latency, 0.05))  # Sleep briefly for realism, capped for speed

        if self.handler is not None:
            return self.handler(input)

        if self.should_error:
            return AgentOutput(
                output="",
                latency=self.latency,
                error=self.error_message,
                metadata={"mock": True},
            )

        key = str(input).strip()
        matched_output = self.responses.get(key, self.default_output)

        return AgentOutput(
            output=matched_output,
            latency=self.latency,
            token_usage=TokenUsage(**self.token_usage),
            cost=self.cost,
            tool_calls=self.tool_calls.copy(),
            trace=Trace(tool_calls=self.tool_calls.copy()),
            metadata={"mock": True, "input_key": key},
            error=None,
        )


class MockAgentAdapter:
    """Adapter producing a MockAgent instance."""

    def create_agent(self, **config: Any) -> Agent:
        return MockAgent(**config)
