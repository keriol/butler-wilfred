from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json

from wilfred.__main__ import main


def run_cli(arguments: list[str]) -> tuple[int, str, str]:
    output = StringIO()
    errors = StringIO()

    with redirect_stdout(output), redirect_stderr(errors):
        result = main(arguments, environ={})

    return result, output.getvalue(), errors.getvalue()


def test_status_command() -> None:
    result, output, errors = run_cli(["status"])

    assert result == 0
    assert errors == ""

    payload = json.loads(output)
    assert payload["name"] == "Wilfred"
    assert payload["status"] == "ok"
    assert payload["runtime"] == "standalone"


def test_tools_command() -> None:
    result, output, errors = run_cli(["tools"])

    assert result == 0
    assert errors == ""

    payload = json.loads(output)

    assert [tool["name"] for tool in payload["tools"]] == [
        "wilfred_status",
        "wilfred_tools",
    ]


def test_no_command_preserves_existing_cli() -> None:
    result, output, errors = run_cli([])

    assert result == 0
    assert errors == ""

    payload = json.loads(output)
    assert payload["runtime"] == "standalone-bootstrap"
