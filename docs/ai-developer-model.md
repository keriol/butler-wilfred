# Wilfred AI Developer Model

## Purpose

This file is the compact public context for AI-assisted development of Wilfred.

Use it to understand the current repository, its runtime boundaries, and its
development rules before proposing or changing code.

It is deliberately smaller than the full documentation set. It describes
implemented public behavior and durable development constraints, not future
plans.

## Sources of truth

Use sources in this order for the kind of information they own:

- **Git code, tests, documentation, and history** describe the implemented
  public software and its architectural contracts.
- **GitHub Issues** describe active work, task status, priorities,
  dependencies, and planned changes.
- **GitHub Releases and versioned release notes** describe published
  checkpoints and release artifacts.

Do not infer current task state from this file.

Do not treat examples, discussion, or an open GitHub Issue as proof that a
feature is already implemented.

## Current public baseline

Wilfred `0.2.1` is the current Public Alpha.

The current runtime includes:

- a standalone Python runtime and configuration model;
- public tool and plugin contracts;
- Butler Core `0.1.4` as the provider-neutral execution foundation;
- deterministic plugin loading;
- the shared tool registry and Execution Engine contracts;
- deterministic request resolution before planner fallback;
- provider-neutral planned execution;
- `WilfredRuntime` goal execution;
- a goal-oriented CLI;
- an optional HTTP API;
- an optional OpenAI BYOK planner provider;
- provider-neutral output contracts;
- READ → ACTION → READ → VERIFY workflows;
- local workflow persistence;
- reusable pending-action lifecycle support;
- provider-latency acknowledgement support;
- standalone wheel and container distribution;
- the official public Home Assistant plugin as an external integration.

When documentation and runtime code disagree, inspect current tests and code
before changing the model.

## Architecture

The public dependency direction is:

`Butler Core → Wilfred → plugins / applications`

### Butler Core

Butler Core owns reusable provider-neutral execution foundations and contracts.

Wilfred consumes those contracts rather than duplicating them.

Do not move service-specific behavior, presentation behavior, or application
domain knowledge into Butler Core.

### Wilfred

Wilfred owns public Butler runtime composition.

Its responsibilities include:

- loading plugins;
- composing registered tools;
- resolving known requests deterministically;
- falling back to planning when appropriate;
- applying execution policy;
- coordinating goals and workflows;
- exposing public CLI and HTTP transports.

Transport layers do not become alternate orchestration cores.

### Plugins

Plugins connect external integrations to the Wilfred runtime and register
public executable behavior through Wilfred's plugin and tool contracts.

Plugin-specific knowledge stays with the plugin rather than entering generic
conversation or execution infrastructure.

## Resolution and execution

Prefer deterministic behavior for known requests.

The normal resolution direction is:

`request → deterministic resolution → optional planner fallback → execution`

Planning never grants permissions or confirmation.

Execution policy remains authoritative after planning.

Protected operations must continue through the normal execution path.

Where success can be observed, use:

`READ → ACTION → READ → VERIFY`

Dispatch alone is not proof that the requested external state was reached.

## AI provider boundary

AI planning is optional.

Wilfred must remain usable without making an AI provider part of its core
execution contracts.

Provider credentials stay outside repository content and public runtime
introspection.

AI fallback receives only the context required for the requested goal.

Do not use AI planning where deterministic resolution already owns the request.

## Development rules

Before changing code:

1. Read the relevant implementation and tests.
2. Check GitHub Issues for active work or ownership conflicts.
3. Keep one focused feature per branch and commit.
4. Preserve existing public contracts unless the issue explicitly changes them.
5. Add or update tests with behavior changes.
6. Run focused tests first, then the complete suite.
7. Review the final diff for unrelated changes.

Use the repository's existing development environment and tooling.

Do not install or upgrade dependencies merely to make an unrelated task pass.

## Public repository boundary

Repository content must be publishable as-is.

Never commit:

- credentials or tokens;
- real service endpoints that are not intentionally public;
- local runtime databases;
- deployment-specific identifiers;
- user data;
- machine-specific operational paths;
- consumer-specific implementation details.

Examples and fixtures must remain generic and reproducible.

## Documentation discipline

Document behavior at its actual maturity.

A GitHub Issue may describe future work but does not make that work available.

Do not copy planned functionality into this model until the implementation,
tests, and public documentation support it.

Keep this file compact. Detailed behavior belongs in the dedicated public
documentation and code.
