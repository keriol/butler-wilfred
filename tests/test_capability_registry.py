from __future__ import annotations

import pytest

from wilfred import CapabilityDefinition, DomainDefinition
from wilfred.capability_registry import CapabilityRegistry
from wilfred.plugins import PluginDefinition


def _plugin(
    name: str,
    *,
    domains=(),
    capabilities=(),
) -> PluginDefinition:
    return PluginDefinition(
        name=name,
        register=lambda registry: None,
        domains=tuple(domains),
        capabilities=tuple(capabilities),
    )


def test_registry_orders_semantic_metadata_deterministically():
    media = _plugin(
        "plugin.media",
        domains=[DomainDefinition(name="media", description="Media domain")],
        capabilities=[
            CapabilityDefinition(
                name="playback",
                domain="media",
                description="Play media",
            )
        ],
    )
    home = _plugin(
        "plugin.home",
        domains=[DomainDefinition(name="home", description="Home domain")],
        capabilities=[
            CapabilityDefinition(
                name="status",
                domain="home",
                description="Read home status",
            )
        ],
    )

    registry = CapabilityRegistry.from_plugins([media, home])

    assert registry.domain_names() == ["home", "media"]
    assert registry.capability_names() == ["home.status", "media.playback"]
    assert registry.describe_domains() == [
        {
            "name": "home",
            "description": "Home domain",
            "owner_plugin": "plugin.home",
        },
        {
            "name": "media",
            "description": "Media domain",
            "owner_plugin": "plugin.media",
        },
    ]
    assert registry.describe_capabilities() == [
        {
            "name": "home.status",
            "domain": "home",
            "description": "Read home status",
            "owner_plugin": "plugin.home",
        },
        {
            "name": "media.playback",
            "domain": "media",
            "description": "Play media",
            "owner_plugin": "plugin.media",
        },
    ]


def test_registry_rejects_duplicate_domain_identity():
    first = _plugin(
        "plugin.first",
        domains=[DomainDefinition(name="media")],
    )
    second = _plugin(
        "plugin.second",
        domains=[DomainDefinition(name="media")],
    )

    with pytest.raises(ValueError, match="Duplicate domain identities: media"):
        CapabilityRegistry.from_plugins([first, second])


def test_registry_rejects_duplicate_capability_identity():
    domain = DomainDefinition(name="media")
    capability = CapabilityDefinition(name="playback", domain="media")
    first = _plugin(
        "plugin.first",
        domains=[domain],
        capabilities=[capability],
    )
    second = _plugin(
        "plugin.second",
        domains=[domain],
        capabilities=[capability],
    )

    with pytest.raises(ValueError, match="Duplicate domain identities: media"):
        CapabilityRegistry.from_plugins([first, second])


def test_tool_only_plugin_has_empty_semantic_view():
    registry = CapabilityRegistry.from_plugins([
        _plugin("plugin.legacy")
    ])

    assert registry.domain_names() == []
    assert registry.capability_names() == []
