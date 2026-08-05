# Execution Engine

The Execution Engine is the public path for invoking Wilfred tools.

It resolves a registered tool, validates its arguments, applies permission
policy, handles confirmation, enforces the declared timeout and returns a
structured result.

## Basic execution

```python
from wilfred import (
    ExecutionEngine,
    ExecutionRequest,
    ToolRegistry,
    discover_plugins,
    load_plugins,
)

registry = ToolRegistry()

plugins = discover_plugins(
    ["wilfred.plugins.demo_echo"]
)

load_plugins(registry, plugins)

engine = ExecutionEngine(registry)

result = engine.execute(
    ExecutionRequest(
        tool_name="demo_echo",
        arguments={
            "message": "Hello from Wilfred",
        },
    )
)

if result.ok:
    print(result.value)
else:
    print(result.to_dict())
```

Each execution exposes an identifier, status, duration, permission, returned
value and structured errors.

## Permission policy

- `READ` executes without confirmation.
- `ACTION` requires confirmation by default.
- `DANGEROUS` is denied by default and must be explicitly enabled.

Plugins cannot bypass the consumer execution policy.

## Structured statuses

The engine currently returns:

- `success`
- `confirmation_required`
- `denied`
- `invalid_arguments`
- `tool_not_found`
- `timeout`
- `error`

## Argument validation

The dependency-free validator supports object properties, required arguments,
additional-property rejection, primitive types, arrays and enumerated values.

It is a focused public contract, not a complete JSON Schema implementation.

## Timeout behaviour

Each tool declares `timeout_seconds`.

When the deadline is exceeded, Wilfred returns a structured timeout result.
The worker thread cannot forcibly terminate arbitrary Python code, so handlers
must remain bounded and cooperative.

## Current boundary

The Execution Engine is infrastructure, not yet a complete autonomous Butler.

Native capabilities, READ-ACTION-VERIFY workflows, persistence, goal APIs,
Home Assistant integration and the Wilfred `0.2.0` public alpha are still
under development.

The crowdfunding campaign has not launched.
