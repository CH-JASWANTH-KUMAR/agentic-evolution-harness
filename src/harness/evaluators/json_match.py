"""JSON match evaluator for structural and semantic JSON verification."""

from __future__ import annotations

import json
from typing import Any

from harness.core.agent import AgentOutput
from harness.core.result import EvaluationResult
from harness.core.testcase import TestCase
from harness.evaluators.base import EvaluatorRegistry


@EvaluatorRegistry.register("json_match")
class JSONMatchEvaluator:
    """Evaluates whether agent output matches expected JSON structure and values."""

    name: str = "json_match"

    def __init__(self, subset: bool = True, ignore_order: bool = True) -> None:
        self.subset = subset
        self.ignore_order = ignore_order

    def _parse_json(self, value: Any) -> Any:
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            # Attempt to extract JSON if wrapped in markdown code blocks
            cleaned = value.strip()
            if cleaned.startswith("```json") and cleaned.endswith("```"):
                cleaned = cleaned[7:-3].strip()
            elif cleaned.startswith("```") and cleaned.endswith("```"):
                cleaned = cleaned[3:-3].strip()
            return json.loads(cleaned)
        raise ValueError(f"Cannot parse value into JSON: {value}")

    def _matches(self, actual: Any, expected: Any) -> bool:
        if isinstance(expected, dict):
            if not isinstance(actual, dict):
                return False
            for key, exp_val in expected.items():
                if key not in actual:
                    return False
                if not self._matches(actual[key], exp_val):
                    return False
            return self.subset or len(actual) == len(expected)

        if isinstance(expected, list):
            if not isinstance(actual, list):
                return False
            if not self.ignore_order:
                if len(actual) != len(expected):
                    return False
                return all(self._matches(a, e) for a, e in zip(actual, expected, strict=False))
            # If ignore order, check every item in expected has a match in actual
            actual_copy = list(actual)
            for exp_item in expected:
                matched_idx = -1
                for idx, act_item in enumerate(actual_copy):
                    if self._matches(act_item, exp_item):
                        matched_idx = idx
                        break
                if matched_idx == -1:
                    return False
                actual_copy.pop(matched_idx)
            return bool(self.subset or len(actual) == len(expected))

        return bool(actual == expected)

    def evaluate(self, test_case: TestCase, output: AgentOutput) -> EvaluationResult:
        if output.is_error:
            return EvaluationResult(
                evaluator=self.name,
                score=0.0,
                passed=False,
                explanation=f"Agent produced an error: {output.error}",
            )

        expected = test_case.expected
        if expected is None:
            return EvaluationResult(
                evaluator=self.name,
                score=1.0,
                passed=True,
                explanation="No expected JSON specified; passed by default.",
            )

        try:
            exp_json = self._parse_json(expected)
        except Exception as err:
            return EvaluationResult(
                evaluator=self.name,
                score=0.0,
                passed=False,
                explanation=f"Malformed expected JSON: {err}",
            )

        try:
            act_json = self._parse_json(output.output)
        except Exception as err:
            return EvaluationResult(
                evaluator=self.name,
                score=0.0,
                passed=False,
                explanation=f"Agent output is not valid JSON: {err}",
                details={"raw_output": output.text},
            )

        match = self._matches(act_json, exp_json)
        explanation = (
            "JSON structure and values matched expectations."
            if match
            else "JSON output did not match expected structure/values."
        )

        return EvaluationResult(
            evaluator=self.name,
            score=1.0 if match else 0.0,
            passed=match,
            explanation=explanation,
            details={
                "subset": self.subset,
                "ignore_order": self.ignore_order,
                "parsed_actual": act_json,
                "parsed_expected": exp_json,
            },
        )
