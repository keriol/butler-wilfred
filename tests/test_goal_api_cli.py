from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

import pytest

import wilfred.__main__ as wilfred_main
import wilfred.api as wilfred_api


SECRET = "api-cli-secret"


class FakeOpenAIProvider:
    calls = []

    @classmethod
    def from_environment(cls, *, model, environ=None):
        cls.calls.append((model, dict(environ or {})))

        return lambda message, system_prompt, tools: "{}"


def run_cli(arguments, *, environ=None):
    output = StringIO()
    errors = StringIO()

    with redirect_stdout(output), redirect_stderr(errors):
        rc = wilfred_main.main(
            arguments,
            environ={} if environ is None else environ,
        )

    return rc, output.getvalue(), errors.getvalue()


def test_api_parser_is_loopback_only_and_has_no_key_option():
    parser = wilfred_main.build_parser()

    parsed = parser.parse_args(
        [
            "api",
            "--provider",
            "openai",
            "--model",
            "test-model",
        ]
    )

    assert parsed.host == "127.0.0.1"
    assert parsed.port == 8000

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "api",
                "--provider",
                "openai",
                "--model",
                "test-model",
                "--api-key",
                SECRET,
            ]
        )


def test_api_command_builds_runtime_and_serves_it(monkeypatch):
    FakeOpenAIProvider.calls = []
    calls = []

    monkeypatch.setattr(
        wilfred_main,
        "OpenAIPlannerProvider",
        FakeOpenAIProvider,
    )
    monkeypatch.setattr(
        wilfred_api,
        "serve_api",
        lambda runtime, **kwargs: calls.append(
            (runtime, kwargs)
        ),
    )

    rc, output, errors = run_cli(
        [
            "api",
            "--provider",
            "openai",
            "--model",
            "test-model",
        ],
        environ={"WILFRED_OPENAI_API_KEY": SECRET},
    )

    assert rc == 0
    assert output == ""
    assert errors == ""
    assert FakeOpenAIProvider.calls == [
        (
            "test-model",
            {"WILFRED_OPENAI_API_KEY": SECRET},
        )
    ]
    assert len(calls) == 1

    runtime, options = calls[0]

    assert isinstance(runtime, wilfred_main.WilfredRuntime)
    assert options == {
        "host": "127.0.0.1",
        "port": 8000,
        "sensitive_values": (SECRET,),
    }


def test_api_missing_key_is_clean_configuration_error(monkeypatch):
    called = False

    def fail_if_called(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(
        wilfred_api,
        "serve_api",
        fail_if_called,
    )

    rc, output, errors = run_cli(
        [
            "api",
            "--provider",
            "openai",
            "--model",
            "test-model",
        ],
        environ={},
    )

    assert rc == 2
    assert output == ""
    assert "configuration error" in errors.lower()
    assert "WILFRED_OPENAI_API_KEY" in errors
    assert "Traceback" not in errors
    assert called is False
