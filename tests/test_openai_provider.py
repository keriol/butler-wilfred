from __future__ import annotations

import json
from types import SimpleNamespace

import pytest


SECRET = "sk-test-secret-never-leak"


class FakeResponses:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            output_text=self.output_text,
        )


class FakeClient:
    def __init__(self, output_text: str) -> None:
        self.responses = FakeResponses(output_text)


def _plan_json() -> str:
    return json.dumps(
        {
            "tool_name": "wilfred_status",
            "arguments": {},
            "confidence": 1.0,
            "reason": "Read runtime status.",
        }
    )


def test_from_environment_uses_namespaced_secret():
    from wilfred.providers.openai import OpenAIPlannerProvider

    captured = {}
    client = FakeClient(_plan_json())

    def factory(**kwargs):
        captured.update(kwargs)
        return client

    provider = OpenAIPlannerProvider.from_environment(
        model="test-model",
        environ={
            "WILFRED_OPENAI_API_KEY": SECRET,
        },
        client_factory=factory,
    )

    assert captured == {
        "api_key": SECRET,
    }

    assert SECRET not in repr(provider)
    assert SECRET not in repr(vars(provider))


def test_missing_key_is_rejected_without_secret_output():
    from wilfred.providers.openai import (
        OpenAIPlannerProvider,
        OpenAIProviderConfigurationError,
    )

    with pytest.raises(
        OpenAIProviderConfigurationError,
        match="WILFRED_OPENAI_API_KEY",
    ) as error:
        OpenAIPlannerProvider.from_environment(
            model="test-model",
            environ={},
            client_factory=lambda **kwargs: None,
        )

    assert "sk-" not in str(error.value)


def test_provider_returns_response_output_text():
    from wilfred.providers.openai import OpenAIPlannerProvider

    expected = _plan_json()
    client = FakeClient(expected)

    provider = OpenAIPlannerProvider(
        client=client,
        model="test-model",
    )

    result = provider(
        "what is your status?",
        "Plan Wilfred tool use.",
        [
            {
                "name": "wilfred_status",
                "description": "Return runtime status.",
                "category": "native",
                "permission": "READ",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            }
        ],
    )

    assert result == expected


def test_provider_uses_responses_structured_output():
    from wilfred.providers.openai import OpenAIPlannerProvider

    client = FakeClient(_plan_json())

    provider = OpenAIPlannerProvider(
        client=client,
        model="test-model",
    )

    provider(
        "what is your status?",
        "Plan Wilfred tool use.",
        [],
    )

    assert len(client.responses.calls) == 1

    call = client.responses.calls[0]

    assert call["model"] == "test-model"
    assert call["input"] == "what is your status?"
    assert call["store"] is False

    output_format = call["text"]["format"]

    assert output_format["type"] == "json_schema"
    assert output_format["name"] == "wilfred_tool_plan"
    assert output_format["strict"] is True

    schema = output_format["schema"]

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "tool_name",
        "arguments",
        "confidence",
        "reason",
    }


def test_provider_supplies_prompt_and_tool_catalog():
    from wilfred.providers.openai import OpenAIPlannerProvider

    client = FakeClient(_plan_json())

    provider = OpenAIPlannerProvider(
        client=client,
        model="test-model",
    )

    provider(
        "check status",
        "PUBLIC SYSTEM PROMPT",
        [
            {
                "name": "wilfred_status",
                "description": "Return status.",
                "category": "native",
                "permission": "READ",
                "parameters": {},
            }
        ],
    )

    instructions = client.responses.calls[0]["instructions"]

    assert "PUBLIC SYSTEM PROMPT" in instructions
    assert "wilfred_status" in instructions
    assert SECRET not in instructions


def test_openai_provider_is_public_provider_api():
    from wilfred.providers import (
        OpenAIPlannerProvider as PublicProvider,
        OpenAIProviderConfigurationError as PublicError,
    )
    from wilfred.providers.openai import (
        OpenAIPlannerProvider,
        OpenAIProviderConfigurationError,
    )

    assert PublicProvider is OpenAIPlannerProvider
    assert PublicError is OpenAIProviderConfigurationError
