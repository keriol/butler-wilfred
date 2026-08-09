from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json

import pytest

import wilfred.__main__ as wilfred_main


class FakeOpenAIProvider:
    calls = []

    @classmethod
    def from_environment(cls, *, model, environ=None):
        cls.calls.append((model, dict(environ or {})))

        def provider(message, system_prompt, tools):
            return json.dumps(
                {
                    "tool_name": "wilfred_status",
                    "arguments": {},
                    "confidence": 1.0,
                    "reason": "goal cli test",
                }
            )

        return provider


def run_cli(arguments, *, environ=None):
    output = StringIO()
    errors = StringIO()

    with redirect_stdout(output), redirect_stderr(errors):
        rc = wilfred_main.main(
            arguments,
            environ={} if environ is None else environ,
        )

    return rc, output.getvalue(), errors.getvalue()


def test_goal_parser_has_no_api_key_option():
    parser = wilfred_main.build_parser()

    parsed = parser.parse_args(
        [
            "goal",
            "what is your status?",
            "--provider",
            "openai",
            "--model",
            "test-model",
            "--confirmed",
        ]
    )

    assert parsed.command == "goal"
    assert parsed.message == "what is your status?"
    assert parsed.provider == "openai"
    assert parsed.model == "test-model"
    assert parsed.confirmed is True

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "goal",
                "status",
                "--provider",
                "openai",
                "--model",
                "test-model",
                "--api-key",
                "forbidden",
            ]
        )


def test_goal_uses_environment_provider_and_emits_result_json(
    monkeypatch,
):
    FakeOpenAIProvider.calls = []

    monkeypatch.setattr(
        wilfred_main,
        "OpenAIPlannerProvider",
        FakeOpenAIProvider,
        raising=False,
    )

    rc, output, errors = run_cli(
        [
            "goal",
            "what is your status?",
            "--provider",
            "openai",
            "--model",
            "test-model",
        ],
        environ={
            "WILFRED_OPENAI_API_KEY": "test-secret",
        },
    )

    assert rc == 0
    assert errors == ""

    assert FakeOpenAIProvider.calls == [
        (
            "test-model",
            {"WILFRED_OPENAI_API_KEY": "test-secret"},
        )
    ]

    payload = json.loads(output)

    assert payload["planning"]["status"] == "success"
    assert (
        payload["planning"]["plan"]["tool_name"]
        == "wilfred_status"
    )
    assert payload["execution"]["status"] == "success"

    assert "test-secret" not in output


def test_goal_confirmation_is_explicit_cli_input(monkeypatch):
    from wilfred.runtime import WilfredRuntime as RealRuntime

    confirmations = []

    class RecordingRuntime(RealRuntime):
        def execute_goal(self, message, *, confirmed=False):
            confirmations.append(confirmed)
            return super().execute_goal(
                message,
                confirmed=confirmed,
            )

    monkeypatch.setattr(
        wilfred_main,
        "OpenAIPlannerProvider",
        FakeOpenAIProvider,
        raising=False,
    )
    monkeypatch.setattr(
        wilfred_main,
        "WilfredRuntime",
        RecordingRuntime,
        raising=False,
    )

    environment = {
        "WILFRED_OPENAI_API_KEY": "test-secret",
    }

    rc, _, _ = run_cli(
        [
            "goal",
            "status",
            "--provider",
            "openai",
            "--model",
            "test-model",
        ],
        environ=environment,
    )
    assert rc == 0

    rc, _, _ = run_cli(
        [
            "goal",
            "status",
            "--provider",
            "openai",
            "--model",
            "test-model",
            "--confirmed",
        ],
        environ=environment,
    )
    assert rc == 0

    assert confirmations == [False, True]


def test_goal_missing_key_is_clean_configuration_error():
    rc, output, errors = run_cli(
        [
            "goal",
            "status",
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


def test_goal_provider_configuration_error_is_clean(monkeypatch):
    from wilfred.providers import OpenAIProviderConfigurationError

    class BrokenProvider:
        @classmethod
        def from_environment(cls, **kwargs):
            raise OpenAIProviderConfigurationError(
                "OpenAI provider unavailable."
            )

    monkeypatch.setattr(
        wilfred_main,
        "OpenAIPlannerProvider",
        BrokenProvider,
    )

    rc, output, errors = run_cli(
        [
            "goal",
            "status",
            "--provider",
            "openai",
            "--model",
            "test-model",
        ],
        environ={"WILFRED_OPENAI_API_KEY": "test-secret"},
    )

    assert rc == 2
    assert output == ""
    assert errors == (
        "wilfred: configuration error: "
        "OpenAI provider unavailable.\n"
    )
    assert "test-secret" not in errors
