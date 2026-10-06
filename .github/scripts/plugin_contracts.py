"""Plugin contract checks for Agentic Evolution Harness.

docs/contributing/extension-points.md lists "Required Behavior" for every kind
of plugin. Unit tests only check what their author thought to test, so this
script checks those rules against EVERY registered plugin, including ones a
pull request just added.

Run it yourself before pushing:

    uv run python .github/scripts/plugin_contracts.py

It checks:

  Registration
    - every @XRegistry.register("name") in the source is actually registered at
      runtime. If not, the module was never imported, almost always because it
      is missing from the package's __init__.py, and the plugin is invisible
      to benchmarks and to `harness list-plugins`.
    - no name is registered twice. Registries are plain dicts, so a duplicate
      silently replaces the earlier plugin, built-ins included.

  Evaluators  (extension-points.md section 1)
    - constructible with no arguments, so `- name: <evaluator>` works in YAML
    - an errored AgentOutput returns score 0.0 and passed False, never raises
    - normal string and dict outputs return a score within [0.0, 1.0]

  Metrics  (section 2)
    - `direction` is a MetricDirection
    - an empty result list is handled (no ZeroDivisionError)
    - formatted_value is a non-empty string

  Reporters  (section 4)
    - report() returns a str, and writes the file when given a destination

  Adapters  (section 3)
    - registered class exposes create_agent() or is itself callable
"""

from __future__ import annotations

import ast
import contextlib
import io
import os
import sys
import tempfile
import traceback
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "src" / "harness"
IN_CI = os.environ.get("GITHUB_ACTIONS") == "true"

# directory -> (registry class name, human label)
PLUGIN_DIRS = {
    "evaluators": ("EvaluatorRegistry", "evaluator"),
    "metrics": ("MetricRegistry", "metric"),
    "reporters": ("ReporterRegistry", "reporter"),
    "adapters": ("AdapterRegistry", "adapter"),
}

# Violations that already exist on main. They are reported as warnings so the
# check stays green on main, while every NEW plugin is held to the rule. Remove
# an entry once it is fixed; the script then enforces it for that plugin too.
KNOWN_VIOLATIONS = {
    ("evaluator", "tool_usage", "errored-output"): (
        "tool_usage does not check output.is_error, so a crashed agent passes when the "
        "benchmark sets only forbidden_tools or no expected_tools"
    ),
}

errors = 0


def report(level: str, message: str, path: str | None = None, line: int | None = None) -> None:
    global errors
    if level == "error":
        errors += 1
    if IN_CI:
        loc = f" file={path}" + (f",line={line}" if line else "") if path else ""
        print(f"::{level}{loc}::{message}")
    else:
        where = f"{path}:{line}: " if path and line else (f"{path}: " if path else "")
        print(f"{level.upper()}: {where}{message}")


def declared_plugins() -> dict[str, list[tuple[str, str, int]]]:
    """AST-scan plugin directories for Registry.register("name") decorators.

    Returns {dir: [(name, relpath, line), ...]}.
    """
    found: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    for directory, (registry, _) in PLUGIN_DIRS.items():
        for path in sorted((PKG / directory).glob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                for deco in node.decorator_list:
                    if (
                        isinstance(deco, ast.Call)
                        and isinstance(deco.func, ast.Attribute)
                        and deco.func.attr == "register"
                        and isinstance(deco.func.value, ast.Name)
                        and deco.func.value.id == registry
                        and deco.args
                        and isinstance(deco.args[0], ast.Constant)
                        and isinstance(deco.args[0].value, str)
                    ):
                        found[directory].append((deco.args[0].value.lower(), rel, deco.lineno))
    return found


def check_registration(registries: dict[str, object]) -> None:
    for directory, entries in declared_plugins().items():
        _, label = PLUGIN_DIRS[directory]
        seen: dict[str, tuple[str, int]] = {}
        for name, rel, line in entries:
            if name in seen:
                first_rel, first_line = seen[name]
                report(
                    "error",
                    f"{label} name '{name}' is already registered in {first_rel}:{first_line}. "
                    "Registries are dicts, so this silently replaces the other plugin. "
                    "Pick a unique name.",
                    rel,
                    line,
                )
            seen[name] = (rel, line)

        available = set(registries[directory].list_available())  # type: ignore[attr-defined]
        for name, rel, line in entries:
            if name not in available:
                init = f"src/harness/{directory}/__init__.py"
                module = Path(rel).stem
                report(
                    "error",
                    f"{label} '{name}' is declared but never registered at runtime, because "
                    f"its module is not imported. Add "
                    f"'from harness.{directory}.{module} import <YourClass>' to {init} "
                    "(and to __all__).",
                    rel,
                    line,
                )


def where(cls: type) -> str | None:
    module = sys.modules.get(cls.__module__)
    file = getattr(module, "__file__", None)
    if not file:
        return None
    try:
        return Path(file).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None


def check_evaluators() -> None:
    from harness.core.agent import AgentOutput
    from harness.core.result import EvaluationResult
    from harness.core.testcase import TestCase
    from harness.evaluators.base import EvaluatorRegistry

    case = TestCase(id="contract-1", name="contract", input="ping", expected="pong")
    for name in EvaluatorRegistry.list_available():
        cls = EvaluatorRegistry._registry[name]
        path = where(cls)
        try:
            evaluator = EvaluatorRegistry.get(name)
        except Exception as exc:  # noqa: BLE001
            report(
                "error",
                f"evaluator '{name}' cannot be created with no options ({exc!r}). Give every "
                "__init__ option a default so '- name: {name}' works in a benchmark.",
                path,
            )
            continue

        scenarios = {
            "an errored AgentOutput": AgentOutput(output="", error="simulated agent failure"),
            "a string output": AgentOutput(output="pong"),
            "a dict output": AgentOutput(output={"answer": "pong"}),
        }
        for label, output in scenarios.items():
            try:
                result = evaluator.evaluate(case, output)
            except Exception:  # noqa: BLE001
                report(
                    "error",
                    f"evaluator '{name}' raised on {label}. Evaluators must return an "
                    "EvaluationResult instead of raising.\n" + traceback.format_exc(limit=3),
                    path,
                )
                continue
            if not isinstance(result, EvaluationResult):
                report(
                    "error",
                    f"evaluator '{name}' returned {type(result).__name__} for {label}, "
                    "expected EvaluationResult.",
                    path,
                )
                continue
            if label == "an errored AgentOutput" and (result.passed or result.score != 0.0):
                known = KNOWN_VIOLATIONS.get(("evaluator", name, "errored-output"))
                report(
                    "warning" if known else "error",
                    f"evaluator '{name}' gave score={result.score}, passed={result.passed} "
                    "for an errored output. The guide requires score 0.0 and passed False "
                    "when output.is_error is True.",
                    path,
                )
            if not result.explanation:
                report(
                    "warning",
                    f"evaluator '{name}' returned an empty explanation for {label}.",
                    path,
                )


def check_metrics() -> None:
    from harness.core.agent import AgentOutput
    from harness.core.experiment import MetricResult
    from harness.core.result import TestCaseResult
    from harness.core.testcase import TestCase
    from harness.metrics.base import MetricDirection, MetricRegistry

    failed = TestCaseResult(
        test_case=TestCase(id="c", name="c", input="x"),
        output=AgentOutput(output="", error="boom"),
        passed=False,
    )
    for name in MetricRegistry.list_available():
        cls = MetricRegistry._registry[name]
        path = where(cls)
        try:
            metric = MetricRegistry.get(name)
        except Exception as exc:  # noqa: BLE001
            report("error", f"metric '{name}' cannot be created with no options ({exc!r}).", path)
            continue

        if not isinstance(getattr(metric, "direction", None), MetricDirection):
            report(
                "error",
                f"metric '{name}' must set `direction` to a MetricDirection value.",
                path,
            )

        for label, results in {"an empty result list": [], "one errored result": [failed]}.items():
            try:
                value = metric.calculate(results)
            except Exception:  # noqa: BLE001
                report(
                    "error",
                    f"metric '{name}' raised on {label}. Metrics must handle this cleanly "
                    "(guard against len(results) == 0).\n" + traceback.format_exc(limit=3),
                    path,
                )
                continue
            if not isinstance(value, MetricResult):
                report("error", f"metric '{name}' returned {type(value).__name__}.", path)
            elif not isinstance(value.formatted_value, str) or not value.formatted_value:
                report("error", f"metric '{name}' has an empty formatted_value.", path)


def check_reporters() -> None:
    from harness.core.experiment import Experiment
    from harness.reporters.base import ReporterRegistry

    experiment = Experiment(id="contract", name="contract")
    for name in ReporterRegistry.list_available():
        cls = ReporterRegistry._registry[name]
        path = where(cls)
        try:
            reporter = ReporterRegistry.get(name)
            with contextlib.redirect_stdout(io.StringIO()):
                text = reporter.report(experiment)
        except Exception:  # noqa: BLE001
            report(
                "error",
                f"reporter '{name}' failed on an empty Experiment.\n"
                + traceback.format_exc(limit=3),
                path,
            )
            continue
        if not isinstance(text, str):
            report("error", f"reporter '{name}' must return a str from report().", path)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "nested" / f"report.{name}"
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    reporter.report(experiment, destination=dest)
            except Exception:  # noqa: BLE001
                report(
                    "error",
                    f"reporter '{name}' failed when given a destination path. Create parent "
                    "directories with dest.parent.mkdir(parents=True, exist_ok=True).\n"
                    + traceback.format_exc(limit=3),
                    path,
                )


def check_adapters() -> None:
    from harness.adapters.base import AdapterRegistry

    for name in AdapterRegistry.list_available():
        cls = AdapterRegistry._registry[name]
        if not (callable(getattr(cls, "create_agent", None)) or callable(cls)):
            report(
                "error",
                f"adapter '{name}' exposes neither create_agent() nor __call__.",
                where(cls),
            )


def main() -> int:
    sys.path.insert(0, str(PKG.parent))
    import harness.cli.main  # noqa: F401  (imports every built-in plugin package)
    from harness.adapters.base import AdapterRegistry
    from harness.evaluators.base import EvaluatorRegistry
    from harness.metrics.base import MetricRegistry
    from harness.reporters.base import ReporterRegistry

    registries = {
        "evaluators": EvaluatorRegistry,
        "metrics": MetricRegistry,
        "reporters": ReporterRegistry,
        "adapters": AdapterRegistry,
    }
    check_registration(registries)
    check_evaluators()
    check_metrics()
    check_reporters()
    check_adapters()

    counts = ", ".join(f"{len(r.list_available())} {k}" for k, r in registries.items())
    print(f"Checked {counts}.")
    print("OK" if errors == 0 else f"{errors} contract violation(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
