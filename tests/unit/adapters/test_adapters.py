"""Unit tests for agent adapters."""

from __future__ import annotations

from harness.adapters.base import AdapterRegistry
from harness.adapters.generic import GenericAgent
from harness.adapters.mock import MockAgent
from harness.adapters.subprocess import SubprocessAgent
from harness.core.agent import AgentOutput


def test_mock_agent_deterministic_responses() -> None:
    agent = MockAgent(
        default_output="Fallback",
        responses={"ping": "pong"},
        latency=0.01,
    )
    res = agent.run("ping")
    assert res.output == "pong"
    assert res.latency == 0.01

    res_default = agent.run("unknown")
    assert res_default.output == "Fallback"


def test_mock_agent_error_simulation() -> None:
    agent = MockAgent(should_error=True, error_message="Simulated DB outage")
    res = agent.run("query")
    assert res.is_error
    assert res.error == "Simulated DB outage"


def test_generic_agent_callable_function() -> None:
    def custom_fn(user_input: str) -> str:
        return f"Echo: {user_input}"

    agent = GenericAgent(target=custom_fn)
    out = agent.run("Testing")
    assert out.output == "Echo: Testing"


def test_generic_agent_callable_returning_agent_output() -> None:
    def custom_fn(user_input: str) -> AgentOutput:
        return AgentOutput(output=f"Processed {user_input}", cost=0.05)

    agent = GenericAgent(target=custom_fn)
    out = agent.run("Order")
    assert out.output == "Processed Order"
    assert out.cost == 0.05


def test_subprocess_agent_echo() -> None:
    agent = SubprocessAgent(command=["echo", "Hello from CLI"], parse_json_output=False)
    out = agent.run("test input")
    assert "Hello from CLI" in out.text
    assert not out.is_error


def test_adapter_registry_lookup() -> None:
    mock_agent = AdapterRegistry.get("mock", default_output="Registry test")
    out = mock_agent.run("test")
    assert out.output == "Registry test"
