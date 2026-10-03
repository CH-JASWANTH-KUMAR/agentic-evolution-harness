"""Subprocess adapter executing external agent CLI tools."""

from __future__ import annotations

import json
import subprocess
import time
from typing import Any

from harness.adapters.base import AdapterRegistry
from harness.core.agent import Agent, AgentOutput


@AdapterRegistry.register("subprocess")
class SubprocessAgent:
    """Runs an external CLI command as an agent via subprocess."""

    def __init__(
        self,
        command: list[str] | str,
        timeout_seconds: float = 30.0,
        parse_json_output: bool = True,
    ) -> None:
        self.command = command if isinstance(command, list) else command.split()
        self.timeout_seconds = timeout_seconds
        self.parse_json_output = parse_json_output

    def run(
        self,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> AgentOutput:
        input_str = input if isinstance(input, str) else json.dumps(input)
        start_time = time.perf_counter()

        try:
            proc = subprocess.run(
                self.command,
                input=input_str,
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
            duration = time.perf_counter() - start_time

            if proc.returncode != 0:
                return AgentOutput(
                    output="",
                    latency=duration,
                    error=f"Process exited with code {proc.returncode}: {proc.stderr.strip()}",
                )

            stdout = proc.stdout.strip()
            if self.parse_json_output:
                try:
                    parsed = json.loads(stdout)
                    return AgentOutput(output=parsed, latency=duration)
                except json.JSONDecodeError:
                    pass

            return AgentOutput(output=stdout, latency=duration)
        except subprocess.TimeoutExpired:
            return AgentOutput(
                output="",
                latency=self.timeout_seconds,
                error=f"Process timed out after {self.timeout_seconds} seconds.",
            )
        except Exception as exc:
            return AgentOutput(output="", error=f"Subprocess execution error: {exc}")


class SubprocessAgentAdapter:
    """Adapter creating a SubprocessAgent."""

    def create_agent(self, **config: Any) -> Agent:
        cmd = config.get("command", "cat")
        timeout = float(config.get("timeout_seconds", 30.0))
        parse_json = bool(config.get("parse_json_output", True))
        return SubprocessAgent(command=cmd, timeout_seconds=timeout, parse_json_output=parse_json)
