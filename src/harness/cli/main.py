"""Main Typer CLI application for Agentic Evolution Harness."""

from __future__ import annotations

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.table import Table

# Ensure all built-in modules are registered
import harness.adapters  # noqa: F401
import harness.evaluators  # noqa: F401
import harness.metrics  # noqa: F401
import harness.reporters  # noqa: F401
from harness import __version__
from harness.adapters.base import AdapterRegistry
from harness.cli.compare import run_compare
from harness.cli.evaluate import run_evaluate
from harness.cli.validate import run_validate
from harness.evaluators.base import EvaluatorRegistry
from harness.metrics.base import MetricRegistry
from harness.reporters.base import ReporterRegistry

app = typer.Typer(
    name="harness",
    help="Agentic Evolution Harness: Modular evaluation & benchmarking for AI agents.",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()

app.command(name="evaluate")(run_evaluate)
app.command(name="compare")(run_compare)
app.command(name="validate")(run_validate)


@app.command(name="list-plugins")
def list_plugins(
    category: str = typer.Argument(
        "all",
        help="Plugin category to inspect: evaluators, metrics, adapters, reporters, or all.",
    ),
) -> None:
    """List all registered plugins and components."""
    categories = {
        "Evaluators": EvaluatorRegistry.list_available(),
        "Metrics": MetricRegistry.list_available(),
        "Adapters": AdapterRegistry.list_available(),
        "Reporters": ReporterRegistry.list_available(),
    }

    table = Table(box=ROUNDED, title=f"Available Plugins ({category})")
    table.add_column("Category", style="cyan bold")
    table.add_column("Registered Plugins", style="green")

    for cat_name, items in categories.items():
        if category != "all" and category.lower() not in cat_name.lower():
            continue
        table.add_row(cat_name, ", ".join(items))

    console.print(table)


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit.",
    ),
) -> None:
    if version:
        console.print(f"Agentic Evolution Harness v{__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()
