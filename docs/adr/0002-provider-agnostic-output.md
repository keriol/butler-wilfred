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

Wilfred defines provider-agnostic output contracts:

- `OutputRequest` describes content, kind, logical target, priority,
  locale, metadata, and correlation identity.
- `OutputAdapter` declares supported capabilities and performs delivery.
- `OutputDeliveryResult` normalizes delivered, unsupported, and failed
  outcomes.

The initial output kinds are speech, notification, sound, and display.

No concrete provider adapter is included in this task.

## Consequences

Workflows request an output without naming the physical provider.

Provider adapters, routing, fallback, policy, rendering, verification,
HTTP APIs, and concrete integrations remain separate capabilities.
