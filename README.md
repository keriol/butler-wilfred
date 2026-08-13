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

## Quick Start

### Docker Compose

Docker Compose is the quickest way to run the Wilfred Public Alpha
with the official Home Assistant plugin.

```bash
git clone https://github.com/keriol/butler-wilfred.git
cd butler-wilfred

mkdir -p config
cp distribution/home-assistant.example.toml config/home-assistant.toml
```

Create a `.env` file with the required runtime values:

```dotenv
WILFRED_MODEL=your-openai-model
WILFRED_OPENAI_API_KEY=your-api-key
WILFRED_HOME_ASSISTANT_URL=http://host.docker.internal:8123
WILFRED_HOME_ASSISTANT_TOKEN=your-long-lived-access-token
```

Review `config/home-assistant.toml` and replace the demonstration
targets with values appropriate for your Home Assistant installation.

Then start Wilfred:

```bash
docker compose up --build -d
```

Check the runtime:

```bash
curl http://127.0.0.1:8000/health
```

For container configuration, networking and security details, see
[`docs/docker.md`](docs/docker.md).

### Native Python

For development or direct Python usage, install Wilfred in a Python 3.12
virtual environment:

```bash
git clone https://github.com/keriol/butler-wilfred.git
cd butler-wilfred

python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

See [`docs/installation.md`](docs/installation.md) and
[`docs/onboarding.md`](docs/onboarding.md) for the complete native setup.

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

The `0.2.0` Public Alpha also includes:

- the official public Home Assistant plugin;
- the reference Docker distribution.

The following capabilities remain under development and are not presented as
stable releases:

- native Butler capabilities;
- the Wilfred `0.2.0` Public Alpha.

The crowdfunding campaign will only launch after the `0.2.0` release
exists and completes its release verification.

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

## Docker Public Alpha

The standalone Docker distribution composes Wilfred with installed external
plugins without embedding integration-specific code into the runtime.

See `docs/docker.md` for the reference Compose deployment and
`distribution/bom.toml` for the development compatibility snapshot.
