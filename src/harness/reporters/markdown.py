"""Markdown reporter for generating GitHub-flavored summaries."""

from __future__ import annotations

from pathlib import Path

from harness.core.experiment import Experiment
from harness.reporters.base import ReporterRegistry


@ReporterRegistry.register("markdown")
class MarkdownReporter:
    """Formats experiment evaluation summaries as GitHub-Flavored Markdown."""

    def report(self, experiment: Experiment, destination: Path | None = None) -> str:
        lines: list[str] = [
            f"# Evaluation Report: {experiment.name}",
            "",
            f"- **Experiment ID**: `{experiment.id}`",
            f"- **Timestamp**: `{experiment.timestamp.isoformat()}`",
            f"- **Total Tests**: {experiment.total_tests}",
            f"- **Passed**: {experiment.passed_tests} ({experiment.success_rate * 100:.1f}%)",
            f"- **Failed**: {experiment.failed_tests}",
            "",
            "## Summary Metrics",
            "",
            "| Metric | Value | Direction | Description |",
            "| :--- | :--- | :--- | :--- |",
        ]

        for m in experiment.metrics.values():
            direction_label = (
                "Higher is better"
                if m.direction == "higher_is_better"
                else ("Lower is better" if m.direction == "lower_is_better" else "Neutral")
            )
            name_clean = m.name.replace("_", " ").title()
            lines.append(
                f"| **{name_clean}** | `{m.formatted_value}` | {direction_label} | {m.description or ''} |"
            )

        lines.extend(
            [
                "",
                "## Test Results",
                "",
                "| Status | Test Case | Score | Duration | Reason |",
                "| :---: | :--- | :---: | :---: | :--- |",
            ]
        )

        for r in experiment.results:
            status_icon = "✅ Pass" if r.passed else "❌ Fail"
            explanation = r.evaluations[0].explanation if r.evaluations else (r.output.error or "")
            # Sanitize pipe characters in explanation for markdown table
            explanation_safe = explanation.replace("|", "\\|")
            lines.append(
                f"| {status_icon} | {r.test_case.name} | `{r.average_score:.2f}` | `{r.duration:.2f}s` | {explanation_safe} |"
            )

        content = "\n".join(lines) + "\n"

        if destination is not None:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")

        return content
