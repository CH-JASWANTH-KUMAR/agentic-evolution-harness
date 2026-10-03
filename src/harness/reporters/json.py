"""JSON reporter for serializing experiments into machine-readable format."""

from __future__ import annotations

from pathlib import Path

from harness.core.experiment import Experiment
from harness.reporters.base import ReporterRegistry


@ReporterRegistry.register("json")
class JSONReporter:
    """Exports experiments into standardized JSON files or strings."""

    def __init__(self, indent: int = 2) -> None:
        self.indent = indent

    def report(self, experiment: Experiment, destination: Path | None = None) -> str:
        json_str = experiment.model_dump_json(indent=self.indent)

        if destination is not None:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json_str, encoding="utf-8")

        return json_str
