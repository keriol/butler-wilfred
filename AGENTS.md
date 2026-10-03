# Agent entrypoint

Wilfred is the public reusable Butler runtime built on Butler Core.

## Read before feature design

Use the public Butler documentation hub in `keriol/Iot-home-automation` as the
canonical ecosystem map:

1. `docs/agent/index.md`
2. `docs/agent/source-of-truth.md`
3. `docs/agent/feature-design.md`
4. relevant API/architecture/ADR/milestone pages

Do not import private Alfred assumptions into Wilfred.

## This repository owns

- runtime composition;
- plugin discovery/loading;
- deterministic-first routing;
- planner fallback composition;
- public runtime interfaces;

## This repository does not own

- Butler Core contracts;
- Bifröst transport;
- Midgard routing;
- Alfred private behavior;
- Home Assistant provider internals;

## Sources of truth

- GitHub Issues: tasks, priorities, dependencies and active status;
- this repository's `main`: merged implementation and versioned local docs;
- tags/releases/workflows: release evidence;
- live systems: deployed/runtime behavior.

Do not infer release or runtime state from this file.

## Development rule

Before proposing code:

1. identify the owning layer;
2. search existing issues and PRs;
3. define interfaces, failure semantics and public/private scope;
4. define tests and E2E/observable evidence where relevant;
5. follow Issue -> branch -> commit -> main -> close.

Keep this file short. Full architecture belongs in canonical docs, not here.
