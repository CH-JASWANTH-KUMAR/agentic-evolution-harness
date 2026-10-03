"""Console reporter rendering rich, human-friendly terminal evaluation summaries."""

from __future__ import annotations

from pathlib import Path

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from harness.core.experiment import Experiment
from harness.reporters.base import ReporterRegistry


@ReporterRegistry.register("console")
class ConsoleReporter:
    """Renders formatted evaluation summaries using Rich."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def report(self, experiment: Experiment, destination: Path | None = None) -> str:
        # Title Banner
        banner = Panel(
            f"[bold cyan]Agentic Evolution Harness[/bold cyan]\n"
            f"[dim]Experiment ID: {experiment.id} | Name: {experiment.name}[/dim]",
            box=ROUNDED,
            expand=False,
        )
        self.console.print(banner)

        # Test Results Table
        table = Table(box=ROUNDED, title=f"Test Results ({len(experiment.results)} cases)")
        table.add_column("Status", justify="center", width=8)
        table.add_column("Test Case", style="bold")
        table.add_column("Score", justify="right")
        table.add_column("Duration", justify="right")
        table.add_column("Explanation", style="dim")

        for r in experiment.results:
            status = "[green]✓ PASS[/green]" if r.passed else "[red]✗ FAIL[/red]"
            avg_score = f"{r.average_score:.2f}"
            duration = f"{r.duration:.2f}s"
            explanation = r.evaluations[0].explanation if r.evaluations else (r.output.error or "")
            table.add_row(status, r.test_case.name, avg_score, duration, explanation)

        self.console.print(table)

        # Metrics Summary Table
        if experiment.metrics:
            metrics_table = Table(box=ROUNDED, title="Summary Metrics")
            metrics_table.add_column("Metric", style="cyan bold")
            metrics_table.add_column("Value", style="green bold")
            metrics_table.add_column("Direction", style="dim")
            metrics_table.add_column("Description", style="dim")

            for m in experiment.metrics.values():
                direction_icon = (
                    "▲ higher is better"
                    if m.direction == "higher_is_better"
                    else ("▼ lower is better" if m.direction == "lower_is_better" else "• neutral")
                )
                metrics_table.add_row(
                    m.name.replace("_", " ").title(),
                    m.formatted_value,
                    direction_icon,
                    m.description or "",
                )

            self.console.print(metrics_table)

        if destination:
            self.console.print(f"[dim]Full report written to: {destination}[/dim]\n")

        return f"Experiment {experiment.id} evaluated {len(experiment.results)} test cases."
