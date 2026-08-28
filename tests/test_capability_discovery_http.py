from __future__ import annotations

import json

from fastapi.testclient import TestClient

from wilfred import CapabilityDefinition, DomainDefinition, WilfredRuntime
from wilfred.api import create_app
from wilfred.models import ToolDefinition
from wilfred.plugins import PluginDefinition


def _provider(message, system_prompt, tools):
    return json.dumps(
        {
            "tool_name": "media_status",
            "arguments": {},
            "confidence": 1.0,
            "reason": "test",
        }
    )


def _runtime() -> WilfredRuntime:
    def register(registry) -> None:
        registry.register(
            ToolDefinition(
                name="media_status",
                description="Read media status.",
                handler=lambda: {"status": "ok"},
            )
        )

    plugin = PluginDefinition(
        name="test.media",
        register=register,
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

    return WilfredRuntime(
        provider=_provider,
        system_prompt="Test capability discovery.",
        plugins=(plugin,),
    )


def test_http_exposes_sanitized_domain_and_capability_discovery() -> None:
    client = TestClient(create_app(_runtime()))

    runtime = client.get("/v1/runtime")
    domains = client.get("/v1/domains")
    capabilities = client.get("/v1/capabilities")

    assert runtime.status_code == 200
    assert runtime.json()["domain_count"] == 1
    assert runtime.json()["capability_count"] == 1

    assert domains.status_code == 200
    assert domains.json() == {
        "domains": [
            {
                "name": "media",
                "description": "Media domain.",
                "owner_plugin": "test.media",
            }
        ]
    }

    assert capabilities.status_code == 200
    assert capabilities.json() == {
        "capabilities": [
            {
                "name": "media.playback",
                "domain": "media",
                "description": "Play media.",
                "owner_plugin": "test.media",
            }
        ]
    }

    capability = capabilities.json()["capabilities"][0]
    assert set(capability) == {
        "name",
        "domain",
        "description",
        "owner_plugin",
    }


def test_openapi_advertises_discovery_endpoints() -> None:
    client = TestClient(create_app(_runtime()))

    paths = client.get("/openapi.json").json()["paths"]

    assert "/v1/domains" in paths
    assert "/v1/capabilities" in paths
