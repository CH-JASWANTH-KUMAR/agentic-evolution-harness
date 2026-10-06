"""Generic agent adapter dynamically loading Python functions or classes."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

from harness.adapters.base import AdapterRegistry
from harness.core.agent import Agent, AgentOutput


def load_callable(import_path: str) -> Callable[..., Any]:
    """Dynamically import a callable given a module:attribute string."""
    if ":" not in import_path:
        raise ValueError(
            f"Invalid import path '{import_path}'. Expected format 'module.submodule:function_or_class'"
        )

    module_name, attr_name = import_path.split(":", 1)
    import sys
    from pathlib import Path

    cwd = str(Path.cwd().resolve())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    try:
        mod = importlib.import_module(module_name)
    except ImportError as err:
        raise ImportError(f"Could not import module '{module_name}': {err}") from err

    if not hasattr(mod, attr_name):
        raise AttributeError(f"Module '{module_name}' has no attribute '{attr_name}'")

    target = getattr(mod, attr_name)
    if not callable(target):
        raise TypeError(f"Target '{import_path}' is not callable.")

    return target  # type: ignore[no-any-return]


@AdapterRegistry.register("generic")
class GenericAgent:
    """Wraps any Python callable into the standard Agent protocol."""

    def __init__(self, target: Callable[..., Any] | str | None = None, **config: Any) -> None:
        self.config = config
        if isinstance(target, str):
            self.callable_obj = load_callable(target)
        elif callable(target):
            self.callable_obj = target
        else:
            # Fallback echo function
            def _fallback_echo(inp: object) -> str:
                return str(inp)

            self.callable_obj = _fallback_echo

        # If it's a class, instantiate it
        self.instance: Any = None
        if isinstance(self.callable_obj, type):
            self.instance = self.callable_obj(**config)

    def run(
        self,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> AgentOutput:
        try:
            if self.instance is not None:
                if hasattr(self.instance, "run"):
                    res = self.instance.run(input)
                else:
                    res = self.instance(input)
            else:
                res = self.callable_obj(input)

            if isinstance(res, AgentOutput):
                return res

            if isinstance(res, (str, dict)):
                return AgentOutput(output=res)

            return AgentOutput(output=str(res))
        except Exception as exc:
            return AgentOutput(output="", error=f"Generic adapter execution failed: {exc}")


class GenericAgentAdapter:
    """Adapter creating a GenericAgent."""

    def create_agent(self, **config: Any) -> Agent:
        target = config.get("target") or config.get("module")
        return GenericAgent(target=target, **config)
