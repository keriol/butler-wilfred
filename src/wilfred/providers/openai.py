from __future__ import annotations

from collections.abc import Callable, Mapping
import json
import os
from typing import Any


ClientFactory = Callable[..., Any]


class OpenAIProviderConfigurationError(ValueError):
    """Raised when the OpenAI provider cannot be configured safely."""


def _default_client_factory(**kwargs: Any) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise OpenAIProviderConfigurationError(
            "OpenAI provider requires the optional 'openai' package."
        ) from exc

    return OpenAI(**kwargs)


class OpenAIPlannerProvider:
    """OpenAI Responses API adapter for Butler Core planning."""

    def __init__(
        self,
        *,
        client: Any,
        model: str,
    ) -> None:
        resolved_model = model.strip()

        if not resolved_model:
            raise OpenAIProviderConfigurationError(
                "OpenAI model cannot be empty."
            )

        self._client = client
        self._model = resolved_model

    @classmethod
    def from_environment(
        cls,
        *,
        model: str,
        environ: Mapping[str, str] | None = None,
        client_factory: ClientFactory | None = None,
    ) -> OpenAIPlannerProvider:
        effective_environment = (
            os.environ
            if environ is None
            else environ
        )

        api_key = effective_environment.get(
            "WILFRED_OPENAI_API_KEY",
            "",
        ).strip()

        if not api_key:
            raise OpenAIProviderConfigurationError(
                "WILFRED_OPENAI_API_KEY is required "
                "for the OpenAI provider."
            )

        factory = client_factory or _default_client_factory
        client = factory(api_key=api_key)

        return cls(
            client=client,
            model=model,
        )

    def __call__(
        self,
        message: str,
        system_prompt: str,
        tools: list[dict[str, Any]],
    ) -> str:
        tool_catalog = json.dumps(
            tools,
            ensure_ascii=False,
            sort_keys=True,
        )

        instructions = (
            f"{system_prompt.strip()}\n\n"
            "Available Wilfred tools:\n"
            f"{tool_catalog}\n\n"
            "Return exactly one tool plan matching "
            "the required JSON schema."
        )

        response = self._client.responses.create(
            model=self._model,
            instructions=instructions,
            input=message,
            store=False,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "wilfred_tool_plan",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "tool_name": {
                                "type": [
                                    "string",
                                    "null",
                                ],
                            },
                            "arguments": {
                                "type": "object",
                                "additionalProperties": True,
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "reason": {
                                "type": "string",
                            },
                        },
                        "required": [
                            "tool_name",
                            "arguments",
                            "confidence",
                            "reason",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
        )

        output_text = response.output_text

        if not isinstance(output_text, str):
            raise TypeError(
                "OpenAI response output_text must be a string."
            )

        return output_text


__all__ = [
    "OpenAIPlannerProvider",
    "OpenAIProviderConfigurationError",
]
