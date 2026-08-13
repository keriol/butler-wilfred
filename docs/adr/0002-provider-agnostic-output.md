# ADR 0002: Provider-agnostic output contracts

- Status: Accepted
- Date: 2026-08-06
- Task: WILF-018

## Context

A butler may speak, send notifications, play sounds, or present
information on a display. The physical delivery mechanism varies
between installations.

Binding public workflows to one provider would leak infrastructure
choices into domain logic.

## Decision

Wilfred exposes the provider-agnostic output contracts owned by Butler Core:

- `OutputRequest` describes content, kind, logical target, priority,
  locale, metadata, and correlation identity.
- `OutputAdapter` declares supported output kinds and performs delivery.
- `OutputDeliveryResult` normalizes accepted, delivered, unsupported, and failed
  outcomes.

The initial output kinds are speech, notification, sound, and display.

No concrete provider adapter is included in this task.

## Consequences

Workflows request an output without naming the physical provider.

Provider adapters, routing, fallback, policy, rendering, verification,
HTTP APIs, and concrete integrations remain separate capabilities.


## Butler Core 0.1.3 convergence

Starting with Wilfred 0.1.9, the output contract is no longer independently
defined by Wilfred. `wilfred.output` is a compatibility facade over the
provider-neutral contracts published by Butler Core 0.1.3.

The shared contract distinguishes an accepted asynchronous dispatch from a
positively verified delivery. Concrete rendering, transports and providers
remain outside Butler Core.

`OutputCapability` remains temporarily available as a pre-0.2 compatibility
name and aliases `OutputKind`. New integrations should use `OutputKind` and
`OutputAdapter.supported_kinds` directly.
