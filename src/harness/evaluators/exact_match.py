"""Exact match evaluator for verifying identical string outputs."""

from __future__ import annotations

from harness.core.agent import AgentOutput
from harness.core.result import EvaluationResult
from harness.core.testcase import TestCase
from harness.evaluators.base import EvaluatorRegistry


@EvaluatorRegistry.register("exact_match")
class ExactMatchEvaluator:
    """Evaluates whether agent output exactly matches expected output."""

    name: str = "exact_match"

    def __init__(self, ignore_case: bool = False, strip_whitespace: bool = True) -> None:
        self.ignore_case = ignore_case
        self.strip_whitespace = strip_whitespace

    def _normalize(self, text: str) -> str:
        if self.strip_whitespace:
            text = text.strip()
        if self.ignore_case:
            text = text.lower()
        return text

    def evaluate(self, test_case: TestCase, output: AgentOutput) -> EvaluationResult:
        if test_case.expected is None:
            return EvaluationResult(
                evaluator=self.name,
                score=1.0,
                passed=True,
                explanation="No expected output specified; defaulted to passed.",
            )

        if output.is_error:
            return EvaluationResult(
                evaluator=self.name,
                score=0.0,
                passed=False,
                explanation=f"Agent produced an error: {output.error}",
                details={"error": output.error},
            )

        actual_str = output.text
        expected_str = str(test_case.expected)

        norm_actual = self._normalize(actual_str)
        norm_expected = self._normalize(expected_str)

        matched = norm_actual == norm_expected
        explanation = (
            "Output matches expected output exactly."
            if matched
            else f"Expected '{norm_expected}', but received '{norm_actual}'."
        )

        return EvaluationResult(
            evaluator=self.name,
            score=1.0 if matched else 0.0,
            passed=matched,
            explanation=explanation,
            details={
                "actual": actual_str,
                "expected": expected_str,
                "ignore_case": self.ignore_case,
                "strip_whitespace": self.strip_whitespace,
            },
        )
