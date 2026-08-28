from __future__ import annotations

from dataclasses import replace

import pytest

from wilfred import GoalExpectation, verify_plugins
from wilfred.plugins.demo_echo import plugin as demo_echo_plugin


def test_demo_echo_declares_passing_verification() -> None:
    results = verify_plugins((demo_echo_plugin,))

    assert len(results) == 1
    assert results[0].expectation_id == "demo.echo.basic"
    assert results[0].plugin_name == "demo.echo"
    assert results[0].passed is True
    assert results[0].diagnostics == ()


def test_mismatched_expectation_returns_structured_failure() -> None:
    failing = GoalExpectation(
        identity="demo.echo.mismatch",
        goal="echo hello",
        capability="demo.echo",
        tool_name="not_demo_echo",
    )
    plugin = replace(
        demo_echo_plugin,
        verification=(failing,),
    )

    results = verify_plugins((plugin,))

    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].diagnostics == (
        "tool mismatch: expected not_demo_echo, got demo_echo",
    )


def test_duplicate_expectation_identity_is_rejected() -> None:
    expectation = GoalExpectation(
        identity="demo.echo.duplicate",
        goal="echo hello",
        capability="demo.echo",
        tool_name="demo_echo",
    )

    with pytest.raises(
        ValueError,
        match="duplicate verification expectations",
    ):
        replace(
            demo_echo_plugin,
            verification=(expectation, expectation),
        )


def test_plugin_without_verification_remains_compatible() -> None:
    plugin = replace(
        demo_echo_plugin,
        verification=(),
    )

    assert verify_plugins((plugin,)) == ()
