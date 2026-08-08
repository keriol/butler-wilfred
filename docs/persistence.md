# Workflow persistence

Wilfred provides a local SQLite store for completed verified workflow results.

Persistence is deliberately separate from workflow execution.

The workflow does not persist automatically.

A workflow produces a `ReadActionVerifyResult`. The caller may then persist
that completed result through `WorkflowStore`.

A storage failure therefore does not redefine whether an action was
dispatched or whether its external outcome was verified.

## Public contract

The persistence API provides:

- `WorkflowStore`: provider-neutral storage protocol;
- `SQLiteWorkflowStore`: local SQLite implementation;
- `WorkflowRecord`: persisted result plus persistence timestamp;
- `WorkflowPersistenceError`: persistence contract failure.

The basic operations are:

- `save(result)`;
- `get(workflow_id)`;
- `list_recent(limit=...)`.

## Immutable workflow history

A `workflow_id` identifies one completed workflow result.

Saving the same result again is idempotent and returns the existing record.

Attempting to save a different result with an already persisted
`workflow_id` raises `WorkflowPersistenceError`.

The SQLite implementation does not silently overwrite workflow history.

## Serialization

Workflow results are stored as JSON together with searchable record metadata.

The complete structured `ReadActionVerifyResult` is reconstructed when read,
including its READ-before, ACTION and READ-after execution results.

Result values must therefore be JSON serializable.

Invalid or corrupt stored payloads raise `WorkflowPersistenceError` rather
than being returned as apparently valid workflow results.

## SQLite lifecycle

A filesystem database survives store recreation and process restarts.

The special `:memory:` database is also supported. Wilfred keeps an anchor
connection alive internally so operations on the same store share the same
in-memory database.

No third-party database dependency is required. The implementation uses
Python's standard-library `sqlite3` module.

## Current boundary

Persistence stores completed workflow results only.

It does not currently provide:

- automatic persistence from workflow execution;
- retries or delayed verification;
- workflow resumption;
- distributed locking;
- retention policies;
- Home Assistant-specific storage.

These concerns can build on the persistence contract without making storage
part of the Execution Engine.
