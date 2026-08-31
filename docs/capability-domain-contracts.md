# Capability and domain contracts

Wilfred exposes provider-neutral semantic contribution contracts owned by Butler Core through its existing public import surfaces:

- `DomainDefinition` identifies a domain that owns related knowledge and behaviour;
- `CapabilityDefinition` identifies something the Butler knows how to do inside one domain;
- `PluginDefinition` groups tool registration, semantic declarations and verification expectations;
- `GoalExpectation` declares deterministic behavior a capability promises.

These value contracts are defined by Butler Core so the same domain package can be consumed by multiple Butler runtimes without importing Wilfred merely to describe its semantic surface. Wilfred re-exports the exact Core classes for compatibility.

Wilfred still owns runtime composition: capability aggregation, plugin discovery/loading, deterministic runtime composition and executable verification remain Wilfred responsibilities.

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

Both definitions are immutable Core value objects. Equivalent definitions compare equally and can be used wherever deterministic public metadata is required.

## Plugin declarations

A public plugin may declare the domains and capabilities it owns alongside its tool registrar:

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

`PluginDefinition` is also a Butler Core contract. Core validates declaration structure and ownership relationships without becoming responsible for discovery, loading or runtime lifecycle.

Declarations are normalized into deterministic identity order. A capability must reference a domain declared by the same plugin, making semantic ownership explicit rather than inferred from tool names or conversation code.

When multiple plugins are loaded together, Wilfred validates semantic ownership before mutating the shared tool registry. Duplicate domain and capability identities are rejected clearly rather than allowing competing owners.

Resolver names must also be unique across loaded capabilities. Butler Core reports the resolver name in resolution results and traces, so global uniqueness keeps that evidence attributable to one capability.

`PluginLoadResult` remains a Wilfred runtime result and reports the deterministic `domain_names` and `capability_names` contributed by each loaded plugin in addition to its registered `tool_names`.

## Runtime introspection

`CapabilityRegistry` belongs to Wilfred. It composes Core semantic declarations from loaded plugins into a deterministic queryable runtime view. It is separate from `ToolRegistry`: the tool registry remains the owner of executable operations, while the capability registry owns runtime aggregation, plugin ownership and resolver composition.

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

## Verification contributions

`GoalExpectation` is a Butler Core declaration contract. It can therefore travel with a reusable domain package without importing Wilfred.

Wilfred owns executable verification through `verify_plugins()` and returns Wilfred-specific `VerificationResult` values. Core does not discover plugins, instantiate Wilfred runtimes or execute the Wilfred verification harness.

This keeps declaration portable while runtime verification remains owned by the runtime that knows how to compose and execute the contribution.

## Compatibility

Existing Wilfred imports remain valid. `wilfred.DomainDefinition`, `wilfred.CapabilityDefinition`, `wilfred.PluginDefinition` and `wilfred.GoalExpectation` are compatibility facades exposing the exact Butler Core classes.

Existing tool-only plugins remain valid. `domains`, `capabilities` and `verification` default to empty tuples, so current plugin factories and current `WilfredRuntime` construction do not need to change merely to keep working.

A plugin that declares capabilities opts into the semantic ownership contract. It must also declare the corresponding domains it owns.

Existing callers of `WilfredRuntime(resolvers=...)` remain supported. New domain behavior should prefer capability-owned resolvers so semantic ownership stays beside the capability that provides it.

## Ownership boundary

The current separation is:

- **Butler Core** owns provider-neutral declaration and execution contracts, including domain, capability, plugin contribution and goal-expectation value objects;
- **Wilfred** owns runtime composition, `CapabilityRegistry`, plugin discovery/loading, runtime introspection and executable verification;
- **plugins/providers** own concrete integration and domain behavior;
- **frontends** own presentation and provider-specific interaction details.

Conceptually:

- integration/provider: connection to an external service;
- plugin: packaging and contribution boundary;
- domain: owner of related knowledge and behaviour;
- capability: something the Butler knows how to do and the deterministic resolvers it owns;
- tool: typed executable operation;
- goal: requested outcome.

Butler Core remains provider-neutral. Owning portable contribution declarations does not make Core a plugin runtime: discovery, loading, lifecycle, concrete domain behavior and Wilfred verification stay outside Core.
