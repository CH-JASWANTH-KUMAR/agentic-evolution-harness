"""Regex evaluator matching, error paths and registry integration."""

import re

import pytest

from harness.core.agent import AgentOutput
from harness.core.testcase import TestCase
from harness.evaluators import EvaluatorRegistry, RegexMatchEvaluator


@pytest.mark.parametrize(
    ("pattern", "text", "sensitive", "full", "passed", "match"),
    [
        (r"ORD-[0-9]{5}", "Order ORD-12345 confirmed", True, False, True, "ORD-12345"),
        (r"ORD-[0-9]{5}", "No order", True, False, False, None),
        ("hello", "HELLO", False, False, True, "HELLO"),
        ("hello", "HELLO", True, False, False, None),
        ("hello", "hello", True, True, True, "hello"),
        ("hello", "hello world", True, True, False, None),
        ("", "", True, True, True, ""),
    ],
)
def test_matches(pattern, text, sensitive, full, passed, match):
    evaluator = RegexMatchEvaluator(pattern, case_sensitive=sensitive, full_match=full)
    result = evaluator.evaluate(
        TestCase(id="regex", name="Regex", input=""), AgentOutput(output=text)
    )
    assert result.evaluator == "regex_match"
    assert result.passed is passed
    assert result.score == float(passed)
    assert result.details["pattern"] == pattern
    assert result.details["flags"] == (0 if sensitive else re.IGNORECASE)
    assert result.details["match"] == match


def test_invalid_pattern_returns_failed_result():
    result = RegexMatchEvaluator("[").evaluate(
        TestCase(id="regex", name="Regex", input=""), AgentOutput(output="text")
    )
    assert result.score == 0.0
    assert not result.passed
    assert result.explanation.startswith("Invalid regular expression pattern:")


def test_agent_error_takes_precedence_even_over_invalid_pattern():
    result = RegexMatchEvaluator("[").evaluate(
        TestCase(id="regex", name="Regex", input=""), AgentOutput(error="test failure")
    )
    assert result.score == 0.0
    assert not result.passed
    assert result.explanation == "Agent produced an error: test failure"


def test_registered_plugin():
    assert isinstance(EvaluatorRegistry.get("regex_match"), RegexMatchEvaluator)
