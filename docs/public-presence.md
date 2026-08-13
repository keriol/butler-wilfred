# Wilfred public presence

This document defines the public identity and launch material for Wilfred.

Wilfred's public communication must describe only the reusable public project.
Private deployments, household-specific integrations, credentials,
infrastructure and operational details are outside this scope.

## Identity

Public name:

    Wilfred

Project category:

    Open-source automation software

Primary description:

    Public, extensible Butler runtime for deterministic tools,
    pluggable capabilities and safe automation orchestration.

Short positioning:

    A Butler runtime that connects tools and services without becoming
    the software that owns them.

Core themes:

- deterministic tools;
- explicit permissions and confirmation boundaries;
- pluggable capabilities;
- provider-neutral planning and output contracts;
- READ-ACTION-VERIFY execution;
- standalone deployment;
- open-source automation.

## Canonical links

Runtime repository:

    https://github.com/keriol/butler-wilfred

Butler Core:

    https://github.com/keriol/butler-core

Official Home Assistant plugin:

    https://github.com/keriol/wilfred-home-assistant

Until dedicated social pages are created, GitHub is the canonical public
project destination.

## Preferred social naming

Page name:

    Wilfred

Preferred handle where available:

    wilfred-butler

Fallback handle:

    wilfred-runtime

Handle availability must be confirmed on the platform when the page is
created. A handle must never be documented as canonical before it is actually
claimed.

## LinkedIn

### Tagline

    Extensible Butler runtime for safe, deterministic automation.

### Short description

Wilfred is an open-source Butler runtime for deterministic tool execution,
pluggable capabilities and safe automation orchestration.

It provides explicit permissions, structured execution, provider-neutral
planning, verified READ-ACTION-VERIFY workflows, an HTTP Goal Runtime and a
public plugin contract.

### About

Wilfred is an open-source, extensible Butler runtime designed to orchestrate
tools and services without owning the systems behind them.

Its architecture keeps planning, authorization and execution separate.
Capabilities are exposed as deterministic tools with typed inputs and explicit
permission levels. Actions remain subject to confirmation and execution
policy, while verified workflows can read state before and after an action.

Wilfred can run standalone, expose an optional HTTP API and load external
plugins through a public plugin contract.

The 0.2.0 Public Alpha introduces the official Home Assistant plugin and the
reference Docker distribution.

Wilfred is developed publicly on GitHub.

## Facebook

### Intro

    Open-source Butler runtime for pluggable, safe automation.

### About

Wilfred connects deterministic tools, automation services and optional AI
planning through a public extensible runtime.

The project focuses on explicit permissions, safe execution, reusable plugins
and verification instead of hiding automation behind opaque actions.

Development, documentation and releases are public on GitHub.

## Launch content

The following posts are prepared material. They must not be published with
release wording until the referenced release actually exists.

### Post 1: project introduction

Meet Wilfred.

Wilfred is an open-source Butler runtime built around a simple idea: an
assistant should know how to work with different tools and services without
becoming the software that owns all of them.

Tools are deterministic. Permissions are explicit. Actions remain subject to
policy and confirmation. Integrations stay pluggable.

The current development line includes a standalone Goal Runtime, optional
provider-backed planning, verified READ-ACTION-VERIFY workflows, an HTTP API,
an official Home Assistant plugin and a Docker distribution.

The road to the 0.2.0 Public Alpha is getting shorter.

Project:
https://github.com/keriol/butler-wilfred

### Post 2: Home Assistant plugin

Wilfred now has an official Home Assistant plugin.

Home Assistant remains Home Assistant. Wilfred remains Wilfred.

The plugin gives the Butler runtime authorized logical targets and actions
through Home Assistant's API while preserving Wilfred's normal execution and
confirmation boundaries.

No household-specific entities belong in the public plugin. Configuration
stays with the deployment.

Plugin:
https://github.com/keriol/wilfred-home-assistant

### Post 3: Docker distribution

The Wilfred Public Alpha development line now has an official Docker
distribution.

The container runs non-root, uses hardened defaults and loads integrations as
external plugins rather than embedding them into the runtime.

Its CI also checks the artifact itself: build, run, HTTP verification, push to
a registry, local removal, pull, restart and verification again.

A Dockerfile that merely builds is useful.

A container artifact that survives the trip back from a registry is much more
interesting.

### Post 4: release-day template

Wilfred 0.2.0 Public Alpha is available.

This release brings together the standalone Goal Runtime, deterministic tool
execution, public plugins, verified workflows, the official Home Assistant
plugin and the reference Docker distribution.

The Public Alpha is intended for experimentation, development and feedback.
It is not presented as a finished home automation platform.

Release:
https://github.com/keriol/butler-wilfred/releases

Documentation:
https://github.com/keriol/butler-wilfred

## Publishing sequence

Recommended initial sequence:

1. project introduction;
2. Home Assistant plugin spotlight;
3. Docker distribution spotlight;
4. 0.2.0 release announcement after the verified release exists.

The first three items may be prepared before 0.2.0.

The release-day post must only be published after the 0.2.0 release and its
artifacts have passed final checkout.

## Crowdfunding boundary

Public social presence and crowdfunding are separate launch concerns.

Social pages and project communication may be prepared before 0.2.0.

Fundraising must not be activated until the real Wilfred 0.2.0 release exists
and has completed its release verification.

Crowdfunding copy, scope and readiness are tracked separately.

## Visual assets

Generated upload assets are stored in `assets/social/`.

Current assets:

- `linkedin-logo.png` — 400 x 400;
- `linkedin-cover.png` — 4200 x 700;
- `facebook-profile.png` — 320 x 320;
- `facebook-cover.png` — 851 x 315.

The avatar uses the Wilfred `W` network mark.

Covers keep the visual mark and wordmark away from the outer edges so that
normal platform cropping does not remove the primary identity.

The assets can be regenerated deterministically with:

    python scripts/generate_social_assets.py
