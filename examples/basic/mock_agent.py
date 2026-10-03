"""Sample support agent for basic evaluation demonstration."""

from __future__ import annotations

from typing import Any

from harness.core.agent import AgentOutput, TokenUsage
from harness.core.trace import ToolCallRecord, Trace


def support_agent(user_input: str | dict[str, Any]) -> AgentOutput:
    """A sample customer support agent returning answers and tool trajectories."""
    text = str(user_input).lower()

    if "refund" in text:
        tools = [
            ToolCallRecord(tool_name="lookup_order", args={"order_id": "ORD-123"}),
            ToolCallRecord(tool_name="process_refund", args={"amount": 49.99, "currency": "USD"}),
        ]
        return AgentOutput(
            output="Refund of $49.99 processed for order ORD-123.",
            latency=0.32,
            token_usage=TokenUsage(prompt_tokens=45, completion_tokens=15, total_tokens=60),
            cost=0.0003,
            tool_calls=tools,
            trace=Trace(tool_calls=tools),
        )

    if "order" in text or "tracking" in text or "shipment" in text:
        tools = [ToolCallRecord(tool_name="track_shipment", args={"tracking_number": "TRK-990"})]
        return AgentOutput(
            output="Your package is currently in transit and scheduled for delivery tomorrow.",
            latency=0.18,
            token_usage=TokenUsage(prompt_tokens=30, completion_tokens=20, total_tokens=50),
            cost=0.0002,
            tool_calls=tools,
            trace=Trace(tool_calls=tools),
        )

    if "weather" in text:
        tools = [ToolCallRecord(tool_name="get_weather", args={"location": "San Francisco"})]
        return AgentOutput(
            output="The weather in San Francisco is 65°F and sunny.",
            latency=0.25,
            token_usage=TokenUsage(prompt_tokens=25, completion_tokens=12, total_tokens=37),
            cost=0.0001,
            tool_calls=tools,
            trace=Trace(tool_calls=tools),
        )

    if "hello" in text or "hi" in text or "greet" in text:
        return AgentOutput(
            output="Hello! How can I assist you with your order today?",
            latency=0.09,
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=15, total_tokens=25),
            cost=0.00005,
        )

    # Unknown request
    return AgentOutput(
        output="I'm sorry, I didn't understand your request.",
        latency=0.12,
        token_usage=TokenUsage(prompt_tokens=12, completion_tokens=10, total_tokens=22),
        cost=0.00004,
    )
