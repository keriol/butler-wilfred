from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

from butler_core import ExecutionStatus, GoalExpectation

if TYPE_CHECKING:
    from wilfred.plugins import PluginDefinition


@dataclass(frozen=True)
class VerificationResult:
    expectation_id: str
    plugin_name: str
    passed: bool
    diagnostics: tuple[str, ...] = ()


def verify_plugins(
    plugins: Iterable["PluginDefinition"],
) -> tuple[VerificationResult, ...]:
    """Execute plugin-declared deterministic expectations through WilfredRuntime."""

    from wilfred.runtime import WilfredRuntime

    loaded_plugins = tuple(plugins)

    def unexpected_planner(*args: object, **kwargs: object) -> str:
        raise RuntimeError("planner fallback was used")

    runtime = WilfredRuntime(
        provider=unexpected_planner,
        system_prompt="Plugin verification harness.",
        plugins=loaded_plugins,
    )

    results: list[VerificationResult] = []

    for plugin in sorted(loaded_plugins, key=lambda item: item.name):
        owned_capabilities = {
            capability.identity for capability in plugin.capabilities
        }

        for expectation in plugin.verification:
            diagnostics: list[str] = []

            if expectation.capability not in owned_capabilities:
                diagnostics.append(
                    "expectation references capability not owned by plugin: "
                    f"{expectation.capability}"
                )

            if not diagnostics:
                try:
                    outcome = runtime.execute_goal(expectation.goal)
                except Exception as exc:
                    diagnostics.append(
                        f"runtime execution failed: {type(exc).__name__}: {exc}"
                    )
                else:
                    plan = outcome.planning.plan
                    if plan is None:
                        diagnostics.append("goal produced no tool plan")
                    else:
                        if plan.tool_name != expectation.tool_name:
                            diagnostics.append(
                                "tool mismatch: "
                                f"expected {expectation.tool_name}, got {plan.tool_name}"
                            )
                        if expectation.expected_arguments is not None and dict(
                            plan.arguments
                        ) != dict(expectation.expected_arguments):
                            diagnostics.append(
                                "arguments mismatch: "
                                f"expected {dict(expectation.expected_arguments)!r}, "
                                f"got {dict(plan.arguments)!r}"
                            )

                    execution = outcome.execution
                    if execution is None:
                        diagnostics.append("goal was not executed")
                    elif execution.status is not ExecutionStatus.SUCCESS:
                        diagnostics.append(
                            "execution status mismatch: "
                            f"expected success, got {execution.status.value}"
                        )
                    elif expectation.verify_value and (
                        execution.value != expectation.expected_value
                    ):
                        diagnostics.append(
                            "value mismatch: "
                            f"expected {expectation.expected_value!r}, "
                            f"got {execution.value!r}"
                        )

            results.append(
                VerificationResult(
                    expectation_id=expectation.identity,
                    plugin_name=plugin.name,
                    passed=not diagnostics,
                    diagnostics=tuple(diagnostics),
                )
            )

    return tuple(results)


__all__ = [
    "GoalExpectation",
    "VerificationResult",
    "verify_plugins",
]
