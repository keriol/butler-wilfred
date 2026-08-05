# Wilfred

Wilfred is a public, extensible Butler runtime for deterministic tool
registration and execution.

It provides:

- typed tool definitions and permission levels;
- a deterministic tool registry;
- a public plugin contract and loader;
- a standalone command-line entrypoint;
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
{"locale": "en", "log_level": "INFO", "name": "Wilfred", "runtime": "standalone-bootstrap", "status": "ok", "version": "0.1.0"}
```

The same runtime can also be started with:

```bash
python -m wilfred
```

See [Installation and first run](docs/installation.md) for the complete
procedure, plugin example and verification commands.

See [Runtime configuration](docs/configuration.md) for TOML, environment
variables, command-line overrides, validation and precedence.

## Development

Run the public test suite from the repository root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The suite includes a clean-room distribution test that builds a wheel,
installs it into a fresh virtual environment and verifies that Wilfred runs
without any consumer application or editable source checkout.

## Public boundary

This repository contains only generic runtime components, contracts,
documentation, tests and publishable plugins.

Consumer-specific integrations, infrastructure details, credentials and
operational configuration belong in separate repositories.
