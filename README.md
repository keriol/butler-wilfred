# Wilfred 🎩

**Build your Butler, one capability at a time.**

Wilfred is an open-source runtime for building a Butler from reusable
capabilities around the domains and services that matter to you.

Instead of spreading complex behaviour across scripts, automations, API calls
and AI prompts, you can give the Butler capabilities with clear domain
boundaries and a common execution model.

**Integrations connect Wilfred to things.**

**Capabilities teach Wilfred what it can do with them.**

**Goals describe what you want the Butler to achieve.**

Wilfred provides the runtime for resolving, executing and governing those
capabilities consistently.

## Capabilities know their domain

Wilfred separates a few concepts deliberately:

- an **integration or provider** connects to an external service;
- a **tool** is a typed operation the runtime can execute;
- a **capability** represents something the Butler knows how to do;
- a **domain** groups related knowledge and behaviour;
- a **goal** describes the outcome the user wants.

Plugins can package tools and domain behaviour without pushing that knowledge
into the conversational layer. Butler Core provides the provider-neutral
contracts for domains, capabilities and contributions; Wilfred owns discovery,
loading, aggregation, introspection and runtime composition.

The public [Home Assistant Plugin](https://github.com/keriol/home-assistant-plugin)
is the first real smart-home integration built around this model. It began as a
concrete proving example for Wilfred and is now evolving into a reusable Butler
plugin in its own right. Home Assistant remains responsible for devices,
integrations and physical orchestration; the plugin owns reusable Home
Assistant integration behaviour; Wilfred remains one consumer of that plugin.

That boundary is deliberate. Home Assistant is not baked into Butler Core and
is not the only smart-home manager the architecture can support. A future
integration for another automation platform can be implemented as another
plugin following the same provider-neutral Butler contracts rather than adding
platform-specific logic to Wilfred itself.

## What could you build?

A media domain could handle discovery and playback while a home capability
handles the physical environment:

> **Find me something to watch and play it in the living room.**

An appliance domain could eventually use context from other capabilities:

> **Is this a good time to run the washing machine?**

The point is not to create one automation for every possible request. Each
domain contributes the knowledge it owns.

These examples do not mean that every domain already exists publicly in
Wilfred 0.2.2.

## Capability maturity

Wilfred uses three maturity labels for public features and capability examples.

### ✅ Available

Public, documented and usable today.

Wilfred 0.2.2 ships the capability-first Public Alpha foundation described in
[Current Public Alpha](#current-public-alpha).

### 🧪 In testing

Implemented or actively consolidated in a private real-world Butler deployment,
but not yet published as reusable Wilfred capabilities.

Current validation areas include richer media behaviour, appliances and
laundry, proactive communication and reusable plugin composition across Butler
runtimes.

**In testing is not a release promise.**

### 🧭 Designed to enable

Use cases that fit the capability model but are not presented as implemented
features, such as energy-aware appliances, EV charging coordination, garden
domains and other user-built capabilities.

See [Wilfred use cases](docs/use-cases.md) for the detailed maturity boundary
and examples.

## Deterministic when possible. AI when useful.

Known requests can be resolved deterministically first. More open-ended goals
can optionally fall back to a planner.

Capabilities may own their deterministic resolvers. Plugins may also declare
deterministic verification expectations that Wilfred executes through the
normal runtime path.

Planning does not bypass execution policy. Permissions, confirmation and
validation remain runtime responsibilities.

Where an outcome can be observed, Wilfred also supports provider-agnostic
READ → ACTION → READ → VERIFY workflows.

## Requirements

- Python 3.12 or newer
- `pip`
- `venv`

## Quick Start

### Docker Compose

Docker Compose is the quickest way to run the Wilfred Public Alpha
with the Home Assistant integration currently included in the reference
distribution.

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

See [`docs/capability-domain-contracts.md`](docs/capability-domain-contracts.md)
and [`docs/plugin-authoring.md`](docs/plugin-authoring.md) for capability-first
plugin authoring and ownership boundaries.

See [`docs/execution-engine.md`](docs/execution-engine.md) for validation,
permissions, confirmations, timeouts and structured execution results.

See [`docs/http-api.md`](docs/http-api.md) for the optional HTTP transport,
endpoints and security boundary.

## Current Public Alpha

Wilfred `0.2.2` is the current Public Alpha.

It currently provides:

- a standalone public runtime;
- autonomous identity and configuration;
- public tool and plugin compatibility surfaces;
- Butler Core 0.2.0 as the immutable provider-neutral contract baseline;
- Core-owned domain, capability, plugin/contribution and goal-expectation contracts;
- deterministic plugin loading;
- a Wilfred-owned capability registry and runtime introspection;
- capability-owned deterministic resolvers before planner fallback;
- CLI and HTTP domain/capability discovery;
- plugin-declared deterministic verification contributions;
- an Execution Engine facade backed by Butler Core;
- provider-neutral planned execution backed by Butler Core;
- a public goal-oriented `WilfredRuntime` composition API;
- a goal-oriented CLI for provider-backed planning and execution;
- an optional FastAPI transport for health, runtime, tools and goals;
- an optional OpenAI BYOK planner provider;
- provider-agnostic READ-ACTION-VERIFY workflows;
- clean-room wheel verification as a standalone distribution;
- public CI coverage reporting;
- the dependency-free `demo.echo` reference capability plugin;
- the public Home Assistant integration currently consumed by the reference distribution;
- the reference Docker distribution;
- a version-specific immutable BOM for every public release checkpoint.

The canonical Home Assistant repository is now
[`keriol/home-assistant-plugin`](https://github.com/keriol/home-assistant-plugin).
Its ongoing HAP-004 work is moving the plugin from the original Wilfred-coupled
implementation to a consumer-neutral Butler Core boundary. That direction is
not retroactively claimed as part of Wilfred 0.2.2.

The Public Alpha does not yet provide generic multi-tool planning chains,
background workers, schedulers or retry infrastructure.

Its runtime, APIs and plugin contracts may continue to evolve, and
compatibility guarantees remain more limited than they will be for a stable
release.

See [`docs/releases/0.2.2.md`](docs/releases/0.2.2.md) for the release scope and
`distribution/releases/0.2.2.toml` for the exact dependency baseline.

If Wilfred is useful to you and you would like to support its continued
development, you can [support Wilfred on Ko-fi](https://ko-fi.com/butlerwilfred).

## Public boundary

This repository contains only generic runtime components, contracts,
documentation, tests and publishable plugins.

Wilfred is documented and distributed as a standalone public product.
Public interfaces and user-facing documentation do not assume knowledge of
any private consumer deployment.

Consumer-specific integrations, infrastructure details, credentials and
operational configuration belong in separate repositories.

Reusable integrations may also live in independent plugin repositories. The
Home Assistant Plugin is the first concrete example: a plugin can evolve and be
consumed independently of Wilfred while still using the same Butler Core
contracts.

## Provider-agnostic output

Wilfred exposes public contracts for speech, notifications, sounds and
display output without depending on a physical provider.

See
[ADR 0002: Provider-agnostic output contracts](docs/adr/0002-provider-agnostic-output.md).

## AI developer model

Wilfred includes a **public AI model for developers** who use coding assistants
or other AI tooling while working on the project.

[`docs/ai-developer-model.md`](docs/ai-developer-model.md) provides a compact
repository-safe description of the current architecture, execution rules,
public boundaries and authoritative development sources.

Active work and task status remain in GitHub Issues; the model is intentionally
not a roadmap or task ledger.

## Development

For contributor setup, compilation, the complete test suite and clean-room
distribution verification, see the
[development guide](docs/development.md).
