# Wilfred

Wilfred is a public, extensible Butler runtime for deterministic tool
registration and execution.

It provides:

- typed tool definitions and permission levels;
- a deterministic tool registry;
- a structured Execution Engine with validation, policy and timeouts;
- provider-agnostic READ-ACTION-VERIFY workflows;
- local SQLite persistence for completed workflow results;
- a public plugin contract and loader;
- a standalone command-line entrypoint;
- an optional FastAPI HTTP transport for the Goal Runtime;
- an example read-only plugin;
- standalone identity and runtime configuration;
- public distribution and clean-room tests.

## Requirements

- Python 3.12 or newer
- `pip`
- `venv`

## Quick start

From a checked-out copy of this repository:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools
python -m pip install --no-build-isolation .
wilfred
```

Expected output:

```json
{"locale": "en", "log_level": "INFO", "name": "Wilfred", "runtime": "standalone-bootstrap", "status": "ok", "version": "0.1.9.dev0"}
```

The same runtime can also be started with:

```bash
python -m wilfred
```

See [Installation and first run](docs/installation.md) for the complete
procedure, plugin example and verification commands.

See [Public onboarding](docs/onboarding.md) for the shortest path from a
clean environment to deterministic verification, optional BYOK planning
and the optional HTTP transport.

See [Runtime configuration](docs/configuration.md) for TOML, environment
variables, command-line overrides, validation and precedence.

See [Execution Engine](docs/execution-engine.md) for argument validation,
permissions, confirmations, timeouts and structured results.

See [Planned execution](docs/planned-execution.md) for the provider-neutral
planning-to-execution bridge and its confirmation boundary.

See [Wilfred runtime](docs/runtime.md) for the public goal-oriented
composition API.

See [Goal-oriented CLI](docs/goal-cli.md) for natural-language goal
planning and execution from the command line.

See [HTTP API](docs/http-api.md) for the optional FastAPI transport,
loopback-only defaults, structured confirmation flow and security boundary.

See [Provider latency acknowledgement](docs/provider-latency-acknowledgement.md)
for optional pre-planning conversational feedback.

See [OpenAI planner provider](docs/openai-provider.md) for optional BYOK
planning with an environment-only API key.

See [Verified workflows](docs/verified-workflows.md) for
provider-agnostic READ-ACTION-VERIFY execution and verification.

See [Workflow persistence](docs/persistence.md) for the provider-neutral
store contract and local SQLite implementation.

## Current development status

Wilfred currently provides:

- a standalone public runtime;
- autonomous identity and configuration;
- public tool and plugin contracts;
- shared tool, registry and execution contracts from Butler Core 0.1.3;
- deterministic plugin loading;
- an Execution Engine facade backed by Butler Core;
- provider-neutral planned execution backed by Butler Core;
- a public goal-oriented `WilfredRuntime` composition API;
- a goal-oriented CLI for provider-backed planning and execution;
- an optional FastAPI transport for health, runtime, tools and goals;
- an optional OpenAI BYOK planner provider;
- provider-agnostic READ-ACTION-VERIFY workflows;
- clean-room wheel verification as a standalone distribution.

The following capabilities are still under development and are not presented
as available:

- native Butler capabilities;
- the public Home Assistant adapter;
- the Wilfred `0.2.0` public alpha.

The crowdfunding campaign will only launch after the `0.2.0` release exists
and Wilfred can demonstrate useful native behaviour.

## Public boundary

This repository contains only generic runtime components, contracts,
documentation, tests and publishable plugins.

Wilfred is documented and distributed as a standalone public product.
Public interfaces and user-facing documentation do not assume knowledge of
any private consumer deployment.

Consumer-specific integrations, infrastructure details, credentials and
operational configuration belong in separate repositories.

## Provider-agnostic output

Wilfred exposes public contracts for speech, notifications, sounds and
display output without depending on a physical provider.

See
[ADR 0002: Provider-agnostic output contracts](docs/adr/0002-provider-agnostic-output.md).

## Development

Create a Python 3.12 environment and install the development extra:

~~~bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest -q
~~~

The suite includes a clean-room distribution test that builds a wheel,
installs it into a fresh virtual environment and verifies that Wilfred runs
without any consumer application or editable source checkout.

See the [development guide](docs/development.md) for the complete
compile, test, and clean-room workflow.
