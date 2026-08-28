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
from wilfred import CapabilityDefinition

playback = CapabilityDefinition(
    name="playback",
    domain="media",
    description="Play resolved media.",
)

assert playback.identity == "media.playback"
```

Capability identity is deterministic and domain-qualified. This prevents the same short capability name in two domains from being treated as the same semantic owner.

Both definitions are immutable value objects. Equivalent definitions compare equally and can be used wherever deterministic public metadata is required.

## Ownership boundary

The contracts intentionally do not introduce another registry into Butler Core or Wilfred.

The current separation remains:

- integration/provider: connection to an external service;
- plugin: packaging and integration boundary;
- domain: owner of related knowledge and behaviour;
- capability: something the Butler knows how to do;
- tool: typed executable operation;
- goal: requested outcome.

Butler Core remains provider-neutral and continues to own generic execution and resolution foundations. Wilfred owns the semantic capability/domain model.

## Compatibility and next step

Existing tool-only plugins and existing `WilfredRuntime` construction are unchanged by these contracts. A consumer does not need to declare domains or capabilities merely to continue using the current public plugin/tool APIs.

Plugin declaration, loading, duplicate-identity validation and runtime capability discovery are deliberately separate follow-up work. They must build on these contracts rather than duplicating them.

This separation keeps the first public contract small and avoids making speculative registry or loader behaviour part of the compatibility surface before it is needed.
