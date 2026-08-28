from __future__ import annotations

import pytest

from butler_core import ResolutionResult, ResolverDefinition
from wilfred import (
    CapabilityDefinition,
    CapabilityRegistry,
    DomainDefinition,
)
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


def _resolver(name: str) -> ResolverDefinition:
    return ResolverDefinition(
        name=name,
        handler=lambda request: ResolutionResult.not_handled_result(),
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


def test_registry_composes_resolvers_by_capability_then_declaration_order():
    zeta = _plugin(
        "plugin.zeta",
        domains=[DomainDefinition(name="zeta")],
        capabilities=[
            CapabilityDefinition(
                name="status",
                domain="zeta",
                resolvers=(
                    _resolver("zeta.first"),
                    _resolver("zeta.second"),
                ),
            )
        ],
    )
    alpha = _plugin(
        "plugin.alpha",
        domains=[DomainDefinition(name="alpha")],
        capabilities=[
            CapabilityDefinition(
                name="status",
                domain="alpha",
                resolvers=(_resolver("alpha.only"),),
            )
        ],
    )

    registry = CapabilityRegistry.from_plugins([zeta, alpha])

    assert [
        resolver.name
        for resolver in registry.resolver_definitions()
    ] == ["alpha.only", "zeta.first", "zeta.second"]


def test_registry_rejects_duplicate_domain_identity():
    first = _plugin(
        "plugin.first",
        domains=[DomainDefinition(name="media")],
    )
    second = _plugin(
        "plugin.second",
        domains=[DomainDefinition(name="media")],
    )

    with pytest.raises(
        ValueError,
        match="Duplicate domain identity 'media'.*'plugin.first'.*'plugin.second'",
    ):
        CapabilityRegistry.from_plugins([first, second])


def test_registry_rejects_duplicate_resolver_name_across_capabilities():
    plugin = _plugin(
        "plugin.media",
        domains=[DomainDefinition(name="media")],
        capabilities=[
            CapabilityDefinition(
                name="playback",
                domain="media",
                resolvers=(_resolver("media.shared"),),
            ),
            CapabilityDefinition(
                name="search",
                domain="media",
                resolvers=(_resolver("media.shared"),),
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="Duplicate resolver name 'media.shared'.*'media.playback'.*'media.search'",
    ):
        CapabilityRegistry.from_plugins([plugin])


def test_tool_only_plugin_has_empty_semantic_view():
    registry = CapabilityRegistry.from_plugins([
        _plugin("plugin.legacy")
    ])

    assert registry.domain_names() == []
    assert registry.capability_names() == []
    assert registry.resolver_definitions() == ()
