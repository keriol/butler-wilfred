# Pending actions

Pending actions represent work that a Butler has proposed or deferred
but has not yet resolved.

They are distinct from workflow execution results. A workflow result
records an execution that already happened. A pending action represents
work that can still be resumed, snoozed, completed, dismissed, expire,
or fail.

## Model

A `PendingAction` contains:

- `id`
- `action_type`
- `status`
- `created_at`
- `updated_at`
- optional `expires_at`
- optional `snooze_until`
- provider-neutral `data`

Frontend wording, confirmation text, service-specific identifiers, and
deployment-specific behavior stay outside the reusable model.

## Lifecycle

Supported states are:

- `pending`
- `snoozed`
- `done`
- `dismissed`
- `expired`
- `failed`

A snoozed action automatically returns to `pending` when its snooze
deadline passes.

An unresolved action automatically becomes `expired` when its
expiration deadline passes.

Terminal states cannot transition again.

## Deterministic selection

`get_next()` selects only currently available pending actions.

Selection is deterministic:

1. oldest `created_at`
2. action ID as a stable tie-breaker

## Storage

`PendingActionStore` defines the persistence boundary.

Wilfred provides:

- `InMemoryPendingActionStore`
- `JsonPendingActionStore`

The JSON store uses atomic replacement when writing its state.

Pending actions intentionally use a dedicated store rather than
`WorkflowStore`, because mutable deferred actions and completed workflow
records have different lifecycle and query semantics.

## Responsibility boundary

Wilfred owns the reusable pending-action lifecycle.

Applications decide:

- which actions should be created
- what domain-specific data they carry
- how they are presented to users
- whether a particular action requires confirmation
- what actually happens when an action is eventually executed
