from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json

from wilfred import CapabilityDefinition, DomainDefinition
from wilfred.__main__ import main
from wilfred.plugins import PluginDefinition


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


def test_domains_and_capabilities_commands_expose_plugin_metadata(
    monkeypatch,
) -> None:
    plugin = PluginDefinition(
        name="test.media",
        register=lambda registry: None,
        domains=(
            DomainDefinition(
                name="media",
                description="Media domain.",
            ),
        ),
        capabilities=(
            CapabilityDefinition(
                name="playback",
                domain="media",
                description="Play media.",
            ),
        ),
    )

    monkeypatch.setattr(
        "wilfred.__main__.discover_configured_plugins",
        lambda specs, environ: [plugin],
    )

    domains_result, domains_output, domains_errors = run_cli(
        ["domains", "--plugin", "test:factory"]
    )
    capabilities_result, capabilities_output, capabilities_errors = run_cli(
        ["capabilities", "--plugin", "test:factory"]
    )

    assert domains_result == 0
    assert capabilities_result == 0
    assert domains_errors == ""
    assert capabilities_errors == ""
    assert json.loads(domains_output) == {
        "domains": [
            {
                "name": "media",
                "description": "Media domain.",
                "owner_plugin": "test.media",
            }
        ]
    }
    assert json.loads(capabilities_output) == {
        "capabilities": [
            {
                "name": "media.playback",
                "domain": "media",
                "description": "Play media.",
                "owner_plugin": "test.media",
            }
        ]
    }


def test_discovery_commands_do_not_require_planner_configuration() -> None:
    domains_result, domains_output, domains_errors = run_cli(["domains"])
    capabilities_result, capabilities_output, capabilities_errors = run_cli(
        ["capabilities"]
    )

    assert domains_result == 0
    assert capabilities_result == 0
    assert domains_errors == ""
    assert capabilities_errors == ""
    assert json.loads(domains_output) == {"domains": []}
    assert json.loads(capabilities_output) == {"capabilities": []}


def test_no_command_preserves_existing_cli() -> None:
    result, output, errors = run_cli([])

    assert result == 0
    assert errors == ""

    payload = json.loads(output)
    assert payload["runtime"] == "standalone-bootstrap"
