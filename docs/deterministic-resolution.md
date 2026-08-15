# Deterministic resolution

Wilfred can resolve a goal deterministically before invoking an AI
planner.

The runtime uses Butler Core's provider-neutral deterministic
resolution pipeline. Applications may register ordered resolvers that
either handle a goal, decline it, or fail.

## Execution order

For each goal:

1. registered deterministic resolvers run in order;
2. the first handled result wins;
3. if every resolver declines, Wilfred falls back to the configured
   planner;
4. resolver errors stop resolution and do not silently fall through.

Resolvers return normal planner results, so the existing Wilfred
planning, execution, runtime, CLI and HTTP result contracts remain
unchanged.

## AI acknowledgement

Provider-latency acknowledgement is emitted only when deterministic
resolution falls through to the planner.

A deterministic hit therefore avoids both the provider call and the
frontend acknowledgement associated with provider latency.

## Responsibility boundary

Butler Core owns the resolution contract and pipeline semantics.

Wilfred owns integration into its reusable runtime.

Applications own the concrete deterministic resolvers and decide which
goals can be handled without an AI planner.
