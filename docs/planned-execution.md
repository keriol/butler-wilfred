# Planned execution

Wilfred exposes a provider-neutral bridge between Butler Core planning and
safe tool execution.

The public API is:

- `PlannedExecution`
- `PlannedExecutionResult`

The flow is:

`request -> ButlerPlanner -> validated ToolPlan -> ExecutionEngine -> result`

Planning does not execute tools and does not grant confirmation.

## Confirmation boundary

`PlannedExecution.execute()` uses `confirmed=False` by default.

The Butler Core execution policy remains authoritative:

- `READ` can execute without confirmation.
- `ACTION` requires confirmation by default.
- `DANGEROUS` is denied by default.
- confirmation never overrides a policy denial.

A caller may pass `confirmed=True` only after confirmation has been obtained
outside the planner.

## Provider neutrality

Wilfred receives a Butler Core `PlannerProvider` from the caller.

The planned-execution bridge contains no provider SDK, credentials, OpenAI
logic, Home Assistant logic or other provider-specific behavior.

A concrete provider, including future BYOK support, is a separate integration.

## Scope

WILF-030 does not add:

- a concrete AI provider;
- BYOK credential handling;
- goal-oriented CLI commands;
- Home Assistant integration;
- automatic READ-ACTION-VERIFY construction;
- workers, queues, schedulers or retries.
