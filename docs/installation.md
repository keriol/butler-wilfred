# Installation and first run

This guide installs Wilfred from a local source checkout and verifies the
standalone runtime and example plugin.

## Requirements

Wilfred currently requires:

- Python 3.12 or newer;
- the standard Python `venv` module;
- `pip`;
- `setuptools` for local source builds.

Check the Python version:

```bash
python3.12 --version
```

## Create an isolated environment

From the repository root:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
```

On Windows PowerShell, activate it with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Confirm that the isolated interpreter is active:

```bash
python --version
python -m pip --version
```

## Install from the source checkout

Install the local project:

```bash
python -m pip install --upgrade pip setuptools
python -m pip install --no-build-isolation .
```

This creates the `wilfred` command inside the virtual environment.

The installation is not editable. Changes made to the source checkout after
installation are not automatically reflected in the installed package.

For development work, an editable installation can instead be created with:

```bash
python -m pip install --no-build-isolation --editable .
```

## First run

Start the standalone runtime:

```bash
wilfred
```

Expected output:

```json
{"locale": "en", "log_level": "INFO", "name": "Wilfred", "runtime": "standalone-bootstrap", "status": "ok", "version": "0.2.0.dev0"}
```

The module entrypoint is equivalent:

```bash
python -m wilfred
```

## Optional HTTP API

The base installation does not install an HTTP server. Install Wilfred with
the `http` extra to add the FastAPI transport and Uvicorn:

```bash
python -m pip install --no-build-isolation '.[http]'
```

The HTTP transport needs a configured planner provider. For the optional
OpenAI provider, install both extras:

```bash
python -m pip install --no-build-isolation '.[http,openai]'
```

See [HTTP API](http-api.md) for startup, endpoints, confirmation handling and
the network security boundary.

## Verify the public plugin contract

Wilfred includes a harmless read-only example plugin named `demo.echo`.

Run this example from the activated virtual environment:

```bash
python - <<'PY'
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

load_results = load_plugins(
    registry,
    plugins,
)

engine = ExecutionEngine(registry)

result = engine.execute(
    ExecutionRequest(
        tool_name="demo_echo",
        arguments={
            "message": "Hello from Wilfred",
        },
    )
)

print(f"Plugins: {load_results}")
print(f"Tools:   {registry.names()}")
print(f"Status:  {result.status.value}")
print(f"Result:  {result.value}")
PY
```

Expected result:

```text
Tools:   ['demo_echo']
Status:  success
Result:  {'message': 'Hello from Wilfred'}
```

The example demonstrates the public plugin lifecycle:

1. import a plugin module;
2. discover its `PluginDefinition`;
3. validate its name and registration callable;
4. register its tools deterministically;
5. execute the tool through the public `ExecutionEngine`.

## Run the public test suite

From the repository root:

```bash
python -m pytest -q
```

To run only the distribution isolation test:

```bash
python -m pytest -q tests/test_distribution_clean_room.py
```

The clean-room test:

- builds a wheel from the repository;
- creates a fresh temporary virtual environment;
- installs the wheel without dependencies or network access;
- verifies that Wilfred loads from `site-packages`;
- verifies that no consumer application is importable;
- starts the standalone entrypoint;
- discovers and executes `demo.echo`.

## Build a wheel manually

Create a local wheel without downloading build dependencies:

```bash
python -m pip wheel     --no-deps     --no-build-isolation     --wheel-dir dist     .
```

Install the generated wheel in another environment:

```bash
python -m pip install --no-deps dist/wilfred_butler-*.whl
```

## Uninstall

From the activated virtual environment:

```bash
python -m pip uninstall wilfred-butler
```
