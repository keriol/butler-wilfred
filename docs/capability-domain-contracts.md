# Capability and domain contracts

Wilfred models semantic ownership explicitly through two provider-neutral public contracts:

- `DomainDefinition` identifies a domain that owns related knowledge and behaviour;
- `CapabilityDefinition` identifies something the Butler knows how to do inside one domain.

These contracts describe semantic ownership. They do not connect to external services, execute operations or replace the tool registry.

## DomainDefinition

```python
from wilfred import DomainDefinition

media = DomainDefinition(
    name="media",
    description="Media discovery and playback.",
)

assert media.identity == "media"
```

A domain name is its stable public identity. Names use the same repository-safe form as plugin identities: lowercase alphanumeric segments separated by `.`, `_` or `-`.

## CapabilityDefinition

```python
from butler_core import ResolutionResult, ResolverDefinition
from wilfred import CapabilityDefinition

playback = CapabilityDefinition(
    name="playback",
    domain="media",
    description="Play resolved media.",
    resolvers=(
        ResolverDefinition(
            name="media.playback.local",
            handler=resolve_playback,
        ),
    ),
)

assert playback.identity == "media.playback"
```

Capability identity is deterministic and domain-qualified. This prevents the same short capability name in two domains from being treated as the same semantic owner.

A capability may own zero or more Butler Core `ResolverDefinition` values. Resolver declaration order is explicit and preserved inside the capability. Duplicate resolver names inside one capability are rejected.

Both definitions are immutable value objects. Equivalent definitions compare equally and can be used wherever deterministic public metadata is required.

## Plugin declarations

A public plugin may declare the domains and capabilities it owns alongside its existing tool registrar:

```python
from wilfred import CapabilityDefinition, DomainDefinition
from wilfred.plugins import PluginDefinition

plugin = PluginDefinition(
    name="example.media",
    register=register_tools,
    domains=(
        DomainDefinition(
            name="media",
            description="Media discovery and playback.",
        ),
    ),
    capabilities=(playback,),
)
```

Declarations are normalized into deterministic identity order. A capability must reference a domain declared by the same plugin, making semantic ownership explicit rather than inferred from tool names or conversation code.

When multiple plugins are loaded together, Wilfred validates semantic ownership before mutating the shared tool registry. Duplicate domain and capability identities are rejected clearly rather than allowing competing owners.

Resolver names must also be unique across loaded capabilities. Butler Core reports the resolver name in resolution results and traces, so global uniqueness keeps that evidence attributable to one capability.

`PluginLoadResult` reports the deterministic `domain_names` and `capability_names` contributed by each loaded plugin in addition to its registered `tool_names`.

## Runtime introspection

`CapabilityRegistry` composes the semantic declarations from loaded plugins into a deterministic queryable view. It is separate from `ToolRegistry`: the tool registry remains the owner of executable operations, while the capability registry owns semantic metadata, plugin ownership and resolver composition.

`WilfredRuntime` exposes the semantic view directly:

```python
runtime.domain_names()
runtime.capability_names()
runtime.describe_domains()
runtime.describe_capabilities()
```

Descriptions contain only public semantic metadata: identity, description, domain relationship and owning plugin. They do not expose credentials, provider payloads or executable handlers.

`describe_runtime()` also reports `domain_count` and `capability_count` alongside `tool_count`.

Semantic conflicts use the same `CapabilityRegistry` validation path during plugin loading, so ownership validation is not implemented separately by the loader and runtime.

## Deterministic resolver composition

Capability-owned resolvers are composed automatically into the Butler Core `DeterministicResolutionPipeline` used by `WilfredRuntime`.

Ordering is stable and explicit:

1. resolver definitions supplied through the legacy `WilfredRuntime(resolvers=...)` parameter, preserving their existing order;
2. capability-owned resolvers ordered by capability identity;
3. within one capability, resolver declaration order is preserved.

The legacy runtime parameter is a compatibility surface, not the preferred ownership model for new capability code. Existing consumers that use only `resolvers=...` retain their historical behavior while migrations can move resolvers into their owning capabilities incrementally.

A capability resolver only resolves a goal into the normal planning result. It does not execute a tool directly. The resolved tool still passes through the same `ExecutionEngine`, `ExecutionPolicy`, permission validation and confirmation rules as planner-resolved goals. ACTION and DANGEROUS operations therefore cannot bypass policy merely because resolution was deterministic.

If every deterministic resolver returns `NOT_HANDLED`, planner fallback remains unchanged.

## Compatibility

Existing tool-only plugins remain valid. `domains` and `capabilities` default to empty tuples, so current plugin factories and current `WilfredRuntime` construction do not need to change merely to keep working.

A plugin that declares capabilities opts into the semantic ownership contract. It must also declare the corresponding domains it owns.

Existing callers of `WilfredRuntime(resolvers=...)` remain supported. New domain behavior should prefer capability-owned resolvers so semantic ownership stays beside the capability that provides it.

## Ownership boundary

The semantic registry belongs to Wilfred and does not duplicate the executable tool registry or introduce Wilfred capability/domain concepts into Butler Core.

The current separation remains:

- integration/provider: connection to an external service;
- plugin: packaging and integration boundary;
- domain: owner of related knowledge and behaviour;
- capability: something the Butler knows how to do and the deterministic resolvers it owns;
- tool: typed executable operation;
- goal: requested outcome.

Butler Core remains provider-neutral and continues to own generic execution and resolution foundations. Wilfred owns the semantic capability/domain model, registry, plugin declaration rules and capability-to-resolver association.
