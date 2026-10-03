"""AgentRunner: Pipeline execution orchestrator for agent evaluation."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from typing import Any

from harness.core.agent import Agent, AgentOutput
from harness.core.experiment import Experiment, MetricResult
from harness.core.result import EvaluationResult, TestCaseResult
from harness.core.testcase import EvaluatorConfig, TestCase
from harness.evaluators.base import Evaluator, EvaluatorRegistry
from harness.metrics.base import Metric, MetricRegistry
from harness.runner.execution import measure_time


class AgentRunner:
    """Orchestrates test case execution against an agent, evaluation, and metric aggregation."""

    def __init__(
        self,
        agent: Agent,
        default_evaluators: Sequence[Evaluator | EvaluatorConfig | str] | None = None,
        metrics: Sequence[Metric | str] | None = None,
        on_test_start: Callable[[TestCase], None] | None = None,
        on_test_complete: Callable[[TestCaseResult], None] | None = None,
    ) -> None:
        self.agent = agent
        self.default_evaluators: list[Evaluator] = (
            [self._resolve_evaluator(e) for e in default_evaluators]
            if default_evaluators is not None
            else [EvaluatorRegistry.get("exact_match")]
        )
        self.metrics: list[Metric] = (
            [self._resolve_metric(m) for m in metrics]
            if metrics is not None
            else [MetricRegistry.get("success_rate")]
        )
        self.on_test_start = on_test_start
        self.on_test_complete = on_test_complete

    def _resolve_evaluator(self, item: Evaluator | EvaluatorConfig | str) -> Evaluator:
        if isinstance(item, str):
            return EvaluatorRegistry.get(item)
        if hasattr(item, "name") and hasattr(item, "options"):
            return EvaluatorRegistry.get(item.name, **item.options)
        return item  # type: ignore[return-value]

    def _resolve_metric(self, item: Metric | str) -> Metric:
        if isinstance(item, str):
            return MetricRegistry.get(item)
        return item

    def evaluate_test_case(
        self,
        test_case: TestCase,
    ) -> TestCaseResult:
        """Run a single test case against the agent and evaluate outcomes."""
        if self.on_test_start:
            self.on_test_start(test_case)

        # 1. Run agent and capture execution time
        with measure_time() as timer:
            try:
                output = self.agent.run(test_case.input)
            except Exception as exc:  # Catch agent crash
                output = AgentOutput(
                    output="",
                    latency=timer.duration,
                    error=f"Agent crashed with exception: {exc}",
                )

        duration = timer.duration
        if output.latency is None:
            output.latency = duration

        # 2. Resolve evaluators for this specific test case
        active_evaluators: list[Evaluator] = []
        if test_case.evaluators:
            for eval_cfg in test_case.evaluators:
                active_evaluators.append(EvaluatorRegistry.get(eval_cfg.name, **eval_cfg.options))
        else:
            active_evaluators = self.default_evaluators

        # 3. Run all evaluators
        evaluations: list[EvaluationResult] = []
        for evaluator in active_evaluators:
            try:
                eval_res = evaluator.evaluate(test_case, output)
            except Exception as exc:
                eval_res = EvaluationResult(
                    evaluator=evaluator.name,
                    score=0.0,
                    passed=False,
                    explanation=f"Evaluator error: {exc}",
                    details={"exception": str(exc)},
                )
            evaluations.append(eval_res)

        # 4. Determine overall test case pass
        overall_passed = all(e.passed for e in evaluations) if evaluations else False

        result = TestCaseResult(
            test_case=test_case,
            output=output,
            evaluations=evaluations,
            passed=overall_passed,
            duration=duration,
        )

        if self.on_test_complete:
            self.on_test_complete(result)

        return result

    def run(
        self,
        test_cases: Sequence[TestCase],
        experiment_name: str = "evaluation-run",
        metadata: dict[str, Any] | None = None,
        agent_info: dict[str, Any] | None = None,
        benchmark_info: dict[str, Any] | None = None,
    ) -> Experiment:
        """Execute all test cases, aggregate metrics, and return an Experiment record."""
        results: list[TestCaseResult] = []

        for tc in test_cases:
            res = self.evaluate_test_case(tc)
            results.append(res)

        # 5. Compute metrics across all test case results
        computed_metrics: dict[str, MetricResult] = {}
        for metric in self.metrics:
            try:
                m_result = metric.calculate(results)
                computed_metrics[metric.name] = m_result
            except Exception as exc:
                computed_metrics[metric.name] = MetricResult(
                    name=metric.name,
                    value=0.0,
                    formatted_value="ERR",
                    direction="neutral",
                    description=f"Metric calculation failed: {exc}",
                )

        experiment_id = str(uuid.uuid4())[:8]
        return Experiment(
            id=experiment_id,
            name=experiment_name,
            agent_info=agent_info or {"adapter": getattr(self.agent, "name", "custom")},
            benchmark_info=benchmark_info or {"total_cases": len(test_cases)},
            results=results,
            metrics=computed_metrics,
            metadata=metadata or {},
        )
