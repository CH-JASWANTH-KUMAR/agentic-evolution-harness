"""Pull request rules for Agentic Evolution Harness.

Encodes CONTRIBUTING.md and the "Architectural Boundaries" section of
docs/contributing/extension-points.md, so reviewers do not have to police them.

Run it yourself before pushing (standard library only, no install needed):

    python .github/scripts/pr_rules.py origin/main

BLOCKING (exit 1):
  1. Core modules changed by an outside contributor: src/harness/core/,
     src/harness/runner/runner.py, src/harness/benchmarks/schema.py or
     loader.py. The guide allows this only when an assigned issue requires an
     architectural change, so a maintainer opts in by adding the
     `core-change-approved` label to the pull request.
  2. Code under src/ changed with no change under tests/.
  3. .github/ changed by an outside contributor (CI is maintainer-owned).
  4. pyproject.toml changed without uv.lock (CI installs with --locked).

WARNINGS (never fail the build):
  5. A new plugin module whose tests are not in the matching tests/unit/<area>/.
  6. A new plugin with no change under docs/ or README.md.
  7. Dependencies changed.
  8. No "Closes #<number>" in the description.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IN_CI = os.environ.get("GITHUB_ACTIONS") == "true"
MAINTAINER_ROLES = {"OWNER", "MEMBER", "COLLABORATOR"}
CORE_APPROVAL_LABEL = "core-change-approved"

CORE_PATHS = (
    "src/harness/core/",
    "src/harness/runner/runner.py",
    "src/harness/benchmarks/schema.py",
    "src/harness/benchmarks/loader.py",
)

# Extension zone -> where its tests are expected to live.
PLUGIN_TEST_DIRS = {
    "src/harness/evaluators/": "tests/unit/evaluators/",
    "src/harness/metrics/": "tests/unit/metrics/",
    "src/harness/adapters/": "tests/unit/adapters/",
    "src/harness/reporters/": "tests/unit/reporters/",
    "src/harness/comparison/": "tests/unit/comparison/",
    "src/harness/cli/": "tests/integration/",
}

errors = 0


def report(level: str, message: str, path: str | None = None) -> None:
    global errors
    if level == "error":
        errors += 1
    if IN_CI:
        print(f"::{level}{f' file={path}' if path else ''}::{message}")
    else:
        print(f"{level.upper()}: {f'{path}: ' if path else ''}{message}")


def git_diff(base: str, filter_: str) -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--name-only", f"--diff-filter={filter_}", f"{base}...HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python .github/scripts/pr_rules.py <base-ref>   (e.g. origin/main)")
        return 2
    base = sys.argv[1]

    changed = git_diff(base, "ACMRD")
    added = set(git_diff(base, "A"))
    role = os.environ.get("AUTHOR_ASSOCIATION", "")
    outsider = bool(role) and role not in MAINTAINER_ROLES
    labels = set(json.loads(os.environ.get("PR_LABELS", "[]") or "[]"))

    src = [f for f in changed if f.startswith("src/") and f.endswith(".py")]
    tests = [f for f in changed if f.startswith("tests/")]
    docs = [f for f in changed if f.startswith("docs/") or f == "README.md"]
    print(
        f"Changed files: {len(changed)}  (src: {len(src)}, tests: {len(tests)}, docs: {len(docs)})"
    )

    # 1. Core modules
    core = [f for f in changed if f.startswith(CORE_PATHS)]
    if core and outsider and CORE_APPROVAL_LABEL not in labels:
        for f in core:
            report(
                "error",
                "This is a core module. extension-points.md asks contributors not to modify "
                "it unless an assigned issue requires an architectural change. Move the "
                "change into an extension zone (evaluators/, metrics/, adapters/, reporters/, "
                "comparison/, cli/), or ask a maintainer to add the "
                f"'{CORE_APPROVAL_LABEL}' label if the issue really needs it.",
                f,
            )
    elif core:
        for f in core:
            report("warning", "Core module changed; review carefully.", f)

    # 2. Tests required
    if src and not tests:
        report(
            "error",
            "Code changed but nothing under tests/. CONTRIBUTING.md asks for unit tests "
            "covering every change.",
            src[0],
        )

    # 3. CI is maintainer-owned
    gh = [f for f in changed if f.startswith(".github/")]
    if gh and outsider:
        report(
            "error",
            "CI and repository settings under .github/ are maintainer-owned. Remove these "
            "changes, or open an issue proposing them.",
            gh[0],
        )

    # 4. Lockfile in sync
    if "pyproject.toml" in changed and "uv.lock" not in changed:
        report(
            "error",
            "pyproject.toml changed but uv.lock did not. Run `uv lock` and commit uv.lock; "
            "CI installs with --locked and will fail otherwise.",
            "pyproject.toml",
        )

    # 5 & 6. New plugins
    for f in sorted(added):
        for zone, test_dir in PLUGIN_TEST_DIRS.items():
            if f.startswith(zone) and f.endswith(".py") and not f.endswith("__init__.py"):
                if not any(t.startswith(test_dir) for t in tests):
                    report(
                        "warning",
                        f"New plugin module, but no test changed in {test_dir}. Put its "
                        "tests next to the other tests for this extension point.",
                        f,
                    )
                if not docs:
                    report(
                        "warning",
                        "New plugin with no documentation change. Mention it in docs/ or "
                        "README.md so users can find it.",
                        f,
                    )

    # 7. Dependencies
    if "pyproject.toml" in changed:
        report(
            "warning",
            "pyproject.toml changed. Justify any new dependency in the PR.",
            "pyproject.toml",
        )

    # 8. Linked issue
    body = os.environ.get("PR_BODY")
    if body is not None and not re.search(
        r"(?i)\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\s+#\d+", body
    ):
        report(
            "warning",
            "The description has no 'Closes #<number>'. Link the issue so it closes on merge.",
        )

    print("OK" if errors == 0 else f"{errors} blocking problem(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
