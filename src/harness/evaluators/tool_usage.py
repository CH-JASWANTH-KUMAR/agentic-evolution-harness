"""Tool usage and trajectory evaluator for agent actions and MCP tools."""

from __future__ import annotations

from typing import Any

from harness.core.agent import AgentOutput
from harness.core.result import EvaluationResult
from harness.core.testcase import TestCase
from harness.evaluators.base import EvaluatorRegistry


@EvaluatorRegistry.register("tool_usage")
class ToolUsageEvaluator:
    """Evaluates agent tool calling trajectories, argument matching, and constraints."""

    name: str = "tool_usage"

    def __init__(
        self,
        expected_tools: list[str] | None = None,
        ordered: bool = False,
        forbidden_tools: list[str] | None = None,
        require_all: bool = True,
        exact: bool = False,
        validate_args: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.expected_tools = expected_tools or []
        self.ordered = ordered
        self.forbidden_tools = forbidden_tools or []
        self.require_all = require_all
        self.exact = exact
        self.validate_args = validate_args or {}

    def evaluate(self, test_case: TestCase, output: AgentOutput) -> EvaluationResult:
        # Collect observed tool calls from output.tool_calls or trace
        actual_calls = list(output.tool_calls)
        if not actual_calls and output.trace and output.trace.tool_calls:
            actual_calls = list(output.trace.tool_calls)

        actual_tool_names = [call.tool_name for call in actual_calls]

        # 1. Check forbidden tools
        for forbidden in self.forbidden_tools:
            if forbidden in actual_tool_names:
                return EvaluationResult(
                    evaluator=self.name,
                    score=0.0,
                    passed=False,
                    explanation=f"Forbidden tool '{forbidden}' was invoked.",
                    details={"actual_tools": actual_tool_names, "forbidden": forbidden},
                )

        # 2. Check exact tool matches
        if self.exact and actual_tool_names != self.expected_tools:
            return EvaluationResult(
                evaluator=self.name,
                score=0.0,
                passed=False,
                explanation=(
                    f"Tool sequence did not match exactly. "
                    f"Expected: {self.expected_tools}, Actual: {actual_tool_names}"
                ),
                details={"actual_tools": actual_tool_names, "expected": self.expected_tools},
            )

        # 3. Check expected tools inclusion
        if self.require_all:
            missing_tools = [t for t in self.expected_tools if t not in actual_tool_names]
            if missing_tools:
                return EvaluationResult(
                    evaluator=self.name,
                    score=0.0,
                    passed=False,
                    explanation=f"Missing expected tool call(s): {missing_tools}",
                    details={"missing": missing_tools, "actual": actual_tool_names},
                )

        # 4. Check ordering if requested
        if self.ordered and self.expected_tools:
            last_idx = -1
            for exp_tool in self.expected_tools:
                try:
                    curr_idx = actual_tool_names.index(exp_tool, last_idx + 1)
                    last_idx = curr_idx
                except ValueError:
                    return EvaluationResult(
                        evaluator=self.name,
                        score=0.0,
                        passed=False,
                        explanation=f"Tool '{exp_tool}' was called out of expected order.",
                        details={
                            "expected_order": self.expected_tools,
                            "actual": actual_tool_names,
                        },
                    )

        # 5. Validate arguments if specified
        if self.validate_args:
            call_dict = {call.tool_name: call.args for call in actual_calls}
            for tool_name, expected_args in self.validate_args.items():
                if tool_name not in call_dict:
                    continue
                actual_args = call_dict[tool_name]
                for arg_key, arg_val in expected_args.items():
                    if actual_args.get(arg_key) != arg_val:
                        return EvaluationResult(
                            evaluator=self.name,
                            score=0.0,
                            passed=False,
                            explanation=(
                                f"Argument mismatch for tool '{tool_name}'. "
                                f"Expected {arg_key}={arg_val!r}, got {actual_args.get(arg_key)!r}."
                            ),
                            details={
                                "tool": tool_name,
                                "expected_args": expected_args,
                                "actual_args": actual_args,
                            },
                        )

        return EvaluationResult(
            evaluator=self.name,
            score=1.0,
            passed=True,
            explanation=f"Tool invocation criteria satisfied ({len(actual_tool_names)} tool calls observed).",
            details={
                "actual_tools": actual_tool_names,
                "expected_tools": self.expected_tools,
            },
        )
