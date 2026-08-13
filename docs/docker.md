# Docker distribution

Wilfred can run as a standalone container while integrations remain external
plugin packages.

The official Public Alpha composition currently contains:

- Wilfred standalone runtime;
- Butler Core through Wilfred's package dependency;
- the official Home Assistant plugin;
- the optional Wilfred HTTP transport;
- the optional OpenAI planner provider.

Home Assistant itself is not installed inside the Wilfred container.

## Prepare configuration

Copy the public examples:

    cp distribution/env.example .env
    mkdir -p config
    cp distribution/home-assistant.example.toml config/home-assistant.toml

Edit `.env` and provide:

- the planner model;
- the OpenAI API key;
- the Home Assistant URL;
- a Home Assistant long-lived access token.

Edit `config/home-assistant.toml` and replace the demonstration targets and
actions with the logical targets that this Wilfred instance is authorized to
use.

Never commit `.env` or a household-specific Home Assistant configuration.

The Home Assistant URL must be reachable from inside the Wilfred container.
For a Home Assistant instance exposed on the Docker host,
`host.docker.internal` is available in the reference Compose configuration.

## Start

Build and start the reference distribution:

    docker compose up --build -d

Check the runtime:

    curl http://127.0.0.1:8000/health
    curl http://127.0.0.1:8000/v1/runtime
    curl http://127.0.0.1:8000/v1/tools

The reference port binding is loopback-only by default. Deliberately change
`WILFRED_BIND_ADDRESS` only when an authenticated reverse proxy or an explicit
network policy protects the API.

## Security boundary

The reference container:

- runs as a non-root user;
- uses a read-only root filesystem;
- mounts plugin configuration read-only;
- drops Linux capabilities;
- enables `no-new-privileges`;
- exposes no Docker socket;
- provides only a small writable tmpfs;
- keeps Wilfred's normal READ/ACTION/DANGEROUS execution policy.

Docker is the application distribution boundary here. It is not the Wilfred
sandbox execution backend.

A future Docker-backed sandbox should remain a separate subsystem and should
not require mounting the host Docker socket into the Wilfred runtime.

## Compatibility

`distribution/bom.toml` is the compatibility snapshot for this development
distribution.

The Home Assistant plugin is pinned to an immutable public Git revision during
the 0.2.0 development cycle. Stable package and image references are finalized
as part of the 0.2.0 release choreography.

## Container artifact checkout

The container CI verifies more than a successful local image build.

The image is first started locally and checked through the published HTTP
interface. CI then pushes the image to an isolated temporary registry, removes
the local image reference, pulls it back from the registry and repeats the
runtime checkout against the retrieved image.

The checkout verifies:

- HTTP health;
- runtime metadata;
- native Wilfred tools;
- Home Assistant plugin tools;
- non-root execution;
- absence of a Docker socket mount.

For a stable public release the same model applies to the actual public
registry: publish, remove the local image, pull the published tag or digest,
then execute the checkout against the retrieved artifact.
