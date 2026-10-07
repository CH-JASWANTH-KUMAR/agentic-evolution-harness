"""Configurable regular-expression evaluation of agent output."""

from __future__ import annotations

import re

from harness.core.agent import AgentOutput
from harness.core.result import EvaluationResult
from harness.core.testcase import TestCase
from harness.evaluators.base import EvaluatorRegistry


@EvaluatorRegistry.register("regex_match")
class RegexMatchEvaluator:
    """Search or fully match output using a caller-supplied regular expression."""

    name: str = "regex_match"

    def __init__(
        self, pattern: str = r".*", case_sensitive: bool = True, full_match: bool = False
    ) -> None:
        self.pattern = pattern
        self.case_sensitive = case_sensitive
        self.full_match = full_match
        self._flags = 0 if case_sensitive else re.IGNORECASE

    def evaluate(self, test_case: TestCase, output: AgentOutput) -> EvaluationResult:
        details = {"pattern": self.pattern, "flags": self._flags, "match": None}
        if output.is_error:
            return EvaluationResult(
                evaluator=self.name,
                score=0.0,
                passed=False,
                explanation=f"Agent produced an error: {output.error}",
                details=details,
            )
        try:
            regex = re.compile(self.pattern, self._flags)
            match = regex.fullmatch(output.text) if self.full_match else regex.search(output.text)
        except re.error as exc:
            return EvaluationResult(
                evaluator=self.name,
                score=0.0,
                passed=False,
                explanation=f"Invalid regular expression pattern: {exc}",
                details=details,
            )
        return EvaluationResult(
            evaluator=self.name,
            score=1.0 if match is not None else 0.0,
            passed=match is not None,
            explanation="Output matches the pattern."
            if match is not None
            else "Output does not match the pattern.",
            details={**details, "match": match.group(0) if match is not None else None},
        )
