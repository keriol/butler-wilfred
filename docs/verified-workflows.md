# Verified workflows

Wilfred provides a provider-agnostic READ-ACTION-VERIFY workflow for actions
whose external outcome must be checked after dispatch.

The workflow builds on the Execution Engine rather than replacing it.

An Execution Engine `success` means that a tool handler completed
successfully. It does not prove that the requested external or physical state
was reached.

A verified workflow performs:

1. a READ of the initial state;
2. an ACTION through the Execution Engine;
3. a second READ of observable state;
4. verification over the three returned values.

## Verification statuses

The workflow returns:

- `verified`: the verifier returned `True`;
- `failed`: the action failed or verification returned `False`;
- `indeterminate`: Wilfred cannot establish the outcome reliably.

A failed initial READ stops execution before ACTION.

A failed post-action READ leaves a successful dispatch unverified and returns
`indeterminate`.

## Permission boundary

Both observation steps must use `READ` tools.

The action step must use an `ACTION` or `DANGEROUS` tool. Normal Execution
Engine policy still applies, including confirmations and dangerous-tool
policy.

The workflow validates this structure before executing any step.

## Verifier contract

The verifier receives:

- the value returned by READ-before;
- the value returned by ACTION;
- the value returned by READ-after.

It must return `True`, `False` or `None`.

`None` means the observations are insufficient to determine the outcome.

## Current boundary

This first workflow is synchronous and intentionally small.

Persistence is available as a separate optional storage layer. The workflow
does not persist automatically. See [Workflow persistence](persistence.md).

The workflow does not yet provide retries, delayed verification, recovery
or Home Assistant-specific behaviour.

Automatic ACTION retries are deliberately outside this contract because
repeating an external or physical action may be unsafe or non-idempotent.
