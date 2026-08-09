# Wilfred runtime

`WilfredRuntime` is the public composition layer for goal-oriented Wilfred
execution.

It combines existing public components rather than replacing them:

- a `ToolRegistry`;
- Wilfred native READ tools;
- optional public plugins;
- provider-neutral `PlannedExecution`;
- Butler Core `ExecutionPolicy`.

A caller supplies a Butler Core `PlannerProvider` and a system prompt.

The runtime can then accept a goal through `execute_goal()`.

## Execution boundary

`execute_goal(message)` plans and executes through the existing Wilfred and
Butler Core contracts.

Confirmation is explicit:

- `confirmed=False` is the default;
- the planner never grants confirmation;
- `ACTION` remains subject to confirmation policy;
- `DANGEROUS` remains subject to dangerous-tool policy.

`confirmed=True` must come from the caller after confirmation has been
obtained outside the planner.

## Plugins

Optional `PluginDefinition` objects are loaded into the same registry as the
native Wilfred tools.

`tool_names()` exposes the resulting deterministic registry contents.

## Scope

`WilfredRuntime` does not provide:

- a concrete AI provider;
- provider credentials or BYOK;
- a goal CLI command;
- Home Assistant integration;
- background workers, queues, schedulers or retries.

Those remain separate integration concerns.
