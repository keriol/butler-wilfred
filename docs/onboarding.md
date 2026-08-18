# Wilfred public onboarding

Wilfred is a runtime for building a Butler from reusable capabilities.

Plugins connect the runtime to domains and services. Wilfred provides the
common foundations for resolution, execution, policy and verification.

This guide is the shortest path from a clean Python environment to a verified
standalone Wilfred runtime.

Start with deterministic local behaviour. AI planning and HTTP transport are
optional runtime components and should be enabled only after the base runtime
works.

For a product-level view of capabilities, domains and maturity, see
[Wilfred use cases](use-cases.md).

## 1. Requirements

Wilfred requires Python 3.12 or newer.

~~bash
python3.12 --version
~~

Create an isolated environment:

~~bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools
~~

On Windows PowerShell:

~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools
~~

## 2. Install Wilfred

From a checked-out Wilfred repository:

~~bash
python -m pip install --no-build-isolation .
~~

Verify the CLI:

~~bash
wilfred --help
~~

The public CLI exposes:

- `wilfred status`
- `wilfred tools`
- `wilfred goal`
- `wilfred api`

## 3. Verify the standalone runtime

Start with commands that require no external AI provider:

~~bash
wilfred status
wilfred tools
~~

`wilfred status` verifies the public standalone runtime.

`wilfred tools` lists the registered native capabilities.

## 4. Verify deterministic execution

Wilfred ships the harmless read-only `demo.echo` example plugin.

Before configuring an AI provider, follow the deterministic plugin example in
[Installation and first run](installation.md).

That verifies plugin discovery, registration and Execution Engine behaviour
independently from provider credentials or model behaviour.

## 5. Optional OpenAI BYOK planning

OpenAI support is optional.

~~bash
python -m pip install --no-build-isolation '.[openai]'
export WILFRED_OPENAI_API_KEY='your-key-from-a-secret-store'
~~

Then submit a natural-language goal:

~~bash
wilfred goal "what is your status?" --provider openai --model MODEL
~~

Replace `MODEL` with a model available to your provider account.

The planner selects a tool and constructs arguments. It does not execute tools
directly and cannot grant confirmation.

For an ACTION requiring confirmation, confirmation must come from the caller:

~~bash
wilfred goal "perform the action" \
  --provider openai \
  --model MODEL \
  --confirmed
~~

DANGEROUS tools remain governed by execution policy.

See [Goal-oriented CLI](goal-cli.md) and
[OpenAI planner provider](openai-provider.md).

## 6. Optional HTTP API

For an OpenAI-backed HTTP runtime:

~~bash
python -m pip install --no-build-isolation '.[http,openai]'
export WILFRED_OPENAI_API_KEY='your-key-from-a-secret-store'
wilfred api --provider openai --model MODEL
~~

The built-in server binds to `127.0.0.1:8000` by default.

Verify local liveness:

~~bash
curl http://127.0.0.1:8000/health
~~

Do not expose the built-in server directly to the public Internet. It does not
provide authentication, TLS termination or rate limiting.

See [HTTP API](http-api.md).

## 7. Current public-alpha boundary

Wilfred `0.2.0` is the current Public Alpha.

The Public Alpha includes the standalone runtime, the official Home Assistant
plugin integration and the reference Docker distribution.

The following remain outside the completed Public Alpha scope:
- a complete collection of native Butler capabilities;
- background workers, schedulers or retry infrastructure;
- multi-tool planning chains.

These boundaries are deliberate. Planning, deterministic execution,
confirmation policy, transports and external integrations remain separate
responsibilities.

## 8. Recommended first session

A first-time user should proceed in this order:

1. install Wilfred;
2. run `wilfred status`;
3. run `wilfred tools`;
4. verify `demo.echo`;
5. optionally configure OpenAI BYOK and run a goal;
6. optionally start the HTTP API and verify `/health`.

If a stage fails, diagnose that boundary before enabling the next optional
capability.
