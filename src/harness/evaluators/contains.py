"""Contains evaluator for verifying substring inclusion and regex patterns."""

from __future__ import annotations

import re

from harness.core.agent import AgentOutput
from harness.core.result import EvaluationResult
from harness.core.testcase import TestCase
from harness.evaluators.base import EvaluatorRegistry


@EvaluatorRegistry.register("contains")
class ContainsEvaluator:
    """Evaluates whether agent output contains a target substring or regex match."""

    name: str = "contains"

    def __init__(
        self,
        substring: str | None = None,
        is_regex: bool = False,
        case_sensitive: bool = True,
    ) -> None:
        self.substring = substring
        self.is_regex = is_regex
        self.case_sensitive = case_sensitive

    def evaluate(self, test_case: TestCase, output: AgentOutput) -> EvaluationResult:
        if output.is_error:
            return EvaluationResult(
                evaluator=self.name,
                score=0.0,
                passed=False,
                explanation=f"Agent returned an error: {output.error}",
                details={"error": output.error},
            )

        target = self.substring
        if target is None and test_case.expected is not None:
            target = str(test_case.expected)

        if target is None:
            return EvaluationResult(
                evaluator=self.name,
                score=1.0,
                passed=True,
                explanation="No target substring specified; passed by default.",
            )

        actual_text = output.text

        if self.is_regex:
            flags = 0 if self.case_sensitive else re.IGNORECASE
            try:
                pattern = re.compile(target, flags)
                match = pattern.search(actual_text) is not None
                explanation = (
                    f"Output matched regex pattern '{target}'."
                    if match
                    else f"Output did not match regex pattern '{target}'."
                )
            except re.error as err:
                return EvaluationResult(
                    evaluator=self.name,
                    score=0.0,
                    passed=False,
                    explanation=f"Invalid regular expression: {err}",
                    details={"error": str(err)},
                )
        else:
            if not self.case_sensitive:
                match = target.lower() in actual_text.lower()
            else:
                match = target in actual_text

            explanation = (
                f"Output contains '{target}'." if match else f"Output did not contain '{target}'."
            )

        return EvaluationResult(
            evaluator=self.name,
            score=1.0 if match else 0.0,
            passed=match,
            explanation=explanation,
            details={
                "target": target,
                "is_regex": self.is_regex,
                "case_sensitive": self.case_sensitive,
            },
        )
