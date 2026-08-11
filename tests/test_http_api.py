from __future__ import annotations

import json

from fastapi.testclient import TestClient
import pytest

from wilfred.api import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    REDACTED,
    create_app,
    serve_api,
)
from wilfred.models import ToolDefinition, ToolPermission
from wilfred.plugins import PluginDefinition
from wilfred.runtime import WilfredRuntime


SECRET = "test-secret-never-return"


def _provider(tool_name, arguments=None):
    def provider(message, system_prompt, tools):
        return json.dumps(
            {
                "tool_name": tool_name,
                "arguments": arguments or {},
                "confidence": 1.0,
                "reason": "deterministic API test",
            }
        )

    return provider


def _runtime(*, tool_name="wilfred_status", plugins=()):
    return WilfredRuntime(
        provider=_provider(tool_name),
        system_prompt="Test Wilfred HTTP API.",
        plugins=plugins,
    )


def test_health_runtime_tools_and_openapi_are_exposed():
    client = TestClient(create_app(_runtime()))

    assert client.get("/health").json() == {"status": "ok"}

    runtime = client.get("/v1/runtime")

    assert runtime.status_code == 200
    assert runtime.json()["runtime"] == "goal-runtime"
    assert runtime.json()["tool_count"] == 2

    tools = client.get("/v1/tools")

    assert tools.status_code == 200
    assert [
        tool["name"]
        for tool in tools.json()["tools"]
    ] == [
        "wilfred_status",
        "wilfred_tools",
    ]

    paths = client.get("/openapi.json").json()["paths"]

    assert set(paths) >= {
        "/health",
        "/v1/runtime",
        "/v1/tools",
        "/v1/goals",
    }


def test_goal_endpoint_reuses_structured_goal_runtime_result():
    client = TestClient(create_app(_runtime()))

    response = client.post(
        "/v1/goals",
        json={"message": "what is your status?"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["planning"]["status"] == "success"
    assert (
        payload["planning"]["plan"]["tool_name"]
        == "wilfred_status"
    )
    assert payload["execution"]["status"] == "success"
    assert payload["execution"]["permission"] == "READ"
    assert payload["execution"]["execution_id"]


def test_action_confirmation_is_explicit_http_input():
    plugin = PluginDefinition(
        name="test.action",
        register=lambda registry: registry.register(
            ToolDefinition(
                name="test_action",
                description="Perform a test action.",
                handler=lambda: {"done": True},
                permission=ToolPermission.ACTION,
            )
        ),
    )

    client = TestClient(
        create_app(
            _runtime(
                tool_name="test_action",
                plugins=[plugin],
            )
        )
    )

    pending = client.post(
        "/v1/goals",
        json={"message": "do the action"},
    )

    assert pending.status_code == 200
    assert (
        pending.json()["execution"]["status"]
        == "confirmation_required"
    )

    confirmed = client.post(
        "/v1/goals",
        json={
            "message": "do the action",
            "confirmed": True,
        },
    )

    assert confirmed.status_code == 200
    assert confirmed.json()["execution"]["status"] == "success"
    assert confirmed.json()["execution"]["value"] == {
        "done": True
    }


def test_request_validation_never_echoes_received_values():
    client = TestClient(create_app(_runtime()))

    response = client.post(
        "/v1/goals",
        json={
            "message": " ",
            "api_key": SECRET,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
    assert SECRET not in response.text
    assert all(
        "input" not in issue
        for issue in response.json()["error"][
            "validation_errors"
        ]
    )


def test_goal_result_redacts_sensitive_keys_and_values():
    plugin = PluginDefinition(
        name="test.secret",
        register=lambda registry: registry.register(
            ToolDefinition(
                name="test_secret",
                description="Return unsafe test data.",
                handler=lambda: {
                    "api_key": SECRET,
                    "message": f"provider said {SECRET}",
                },
                permission=ToolPermission.READ,
            )
        ),
    )

    client = TestClient(
        create_app(
            _runtime(
                tool_name="test_secret",
                plugins=[plugin],
            ),
            sensitive_values=(SECRET,),
        )
    )

    response = client.post(
        "/v1/goals",
        json={"message": "read test data"},
    )

    assert response.status_code == 200
    assert SECRET not in response.text

    value = response.json()["execution"]["value"]

    assert value["api_key"] == REDACTED
    assert value["message"] == f"provider said {REDACTED}"


def test_unexpected_runtime_error_is_generic_and_not_logged(
    caplog,
    capsys,
):
    class BrokenRuntime:
        def describe_runtime(self):
            return {
                "name": "Wilfred",
                "status": "ok",
                "version": "test",
                "runtime": "goal-runtime",
                "tool_count": 0,
            }

        def describe_tools(self):
            return []

        def execute_goal(self, message, *, confirmed=False):
            raise RuntimeError(SECRET)

    client = TestClient(
        create_app(
            BrokenRuntime(),
            sensitive_values=(SECRET,),
        )
    )

    response = client.post(
        "/v1/goals",
        json={"message": "fail safely"},
    )

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "runtime_error",
            "message": "Goal execution failed.",
            "validation_errors": [],
        }
    }
    assert SECRET not in response.text
    assert SECRET not in caplog.text

    captured = capsys.readouterr()

    assert SECRET not in captured.out
    assert SECRET not in captured.err


def test_cors_is_not_enabled_by_default():
    client = TestClient(create_app(_runtime()))

    response = client.get(
        "/health",
        headers={"Origin": "https://example.invalid"},
    )

    assert "access-control-allow-origin" not in response.headers

    preflight = client.options(
        "/v1/goals",
        headers={
            "Origin": "https://example.invalid",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert "access-control-allow-origin" not in preflight.headers


def test_server_defaults_to_loopback_without_access_log(monkeypatch):
    captured = {}

    def fake_run(app, **kwargs):
        captured["app"] = app
        captured.update(kwargs)

    monkeypatch.setattr("uvicorn.run", fake_run)

    serve_api(_runtime())

    assert captured["host"] == DEFAULT_HOST == "127.0.0.1"
    assert captured["port"] == DEFAULT_PORT == 8000
    assert captured["access_log"] is False
    assert captured["app"].title == "Wilfred HTTP API"


def test_confirmed_requires_a_real_boolean():
    client = TestClient(create_app(_runtime()))

    response = client.post(
        "/v1/goals",
        json={
            "message": "status",
            "confirmed": "yes",
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize("port", ["0", "65536", "not-a-port"])
def test_api_cli_rejects_invalid_ports(port):
    from wilfred.__main__ import build_parser

    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "api",
                "--provider",
                "openai",
                "--model",
                "test-model",
                "--port",
                port,
            ]
        )
