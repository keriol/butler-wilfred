# Wilfred use cases

**Capabilities know their domain. Wilfred provides the runtime that lets
them work together.**

Wilfred is built around reusable capabilities rather than around one
particular service or smart-home platform.

An integration connects to something.

A tool exposes an operation.

A capability represents something the Butler knows how to do.

A domain groups the knowledge and behaviour needed to make that capability
useful.

This page shows what is public today, what is being validated in real-world
use, and what the capability model is designed to enable.

## ✅ Available

These foundations are public in Wilfred 0.2.2.

### Home Assistant connectivity

The public [Home Assistant Plugin](https://github.com/keriol/home-assistant-plugin)
connects the Butler ecosystem to the physical smart-home layer.

Home Assistant remains responsible for devices, integrations and physical
orchestration.

Wilfred does not try to replace it.

The plugin was originally built as a concrete Wilfred proving example. Its
current development direction is to become a consumer-neutral Butler plugin
that can be used by more than one sibling runtime through shared Butler Core
contracts.

That makes Home Assistant an example of the plugin architecture, not a special
case inside Wilfred. A future integration for another home-automation manager
can follow the same model with a separate platform plugin.

### Deterministic resolution

Known requests can be handled by deterministic resolvers before an optional
AI planner is considered.

Predictable requests can therefore remain predictable.

### Governed execution

Wilfred executes tools through shared contracts for validation, permissions,
confirmation and structured results.

### Verified workflows

When an outcome is observable, a workflow can follow:

    READ → ACTION → READ → VERIFY

This makes it possible to distinguish successful command dispatch from a
result that was actually observed and verified.

## 🧪 In testing

These patterns are implemented or actively being consolidated in a private
real-world Butler deployment.

They are not yet advertised as installable public Wilfred capabilities.

### Media

A richer media domain can know more than how to call a playback API.

It can combine concepts such as discovery, metadata, history and playback
into domain-level behaviour.

For example:

> **Find me something to watch and play it in the living room.**

The interesting part is not one individual service call.

The media capability can understand the request in its own domain and use
the appropriate providers underneath it without making the conversational
layer understand every provider.

### Appliances and laundry

Appliance-specific knowledge can live behind dedicated capability operations
instead of being scattered across unrelated scripts, templates and prompts.

Current real-world validation includes appliance state and domain-specific
program information.

That makes requests such as:

> **What is the washing machine doing?**

or:

> **Find me a program for this kind of laundry.**

part of one coherent domain rather than unrelated automation fragments.

### Proactive communication

Proactive communication is also being validated as a separate concern.

The Butler can decide what needs to be communicated without coupling the
runtime itself to one particular delivery frontend.

### Reusable plugin composition

The Home Assistant Plugin is also being used as a real proving case for a
stronger plugin boundary: one plugin artifact, shared Core contracts and
multiple independent Butler runtimes as consumers.

This direction is under active development and is not retroactively part of
the Wilfred 0.2.2 release contract.

### What "In testing" means

In testing is not a release promise.

Before privately validated behaviour becomes a public Wilfred capability,
it may still require:

- reusable contracts;
- provider-neutral boundaries;
- sanitisation;
- tests;
- documentation;
- clean installation and runtime evidence.

## 🧭 Designed to enable

These examples illustrate where the capability model can go.

They are not claims about features already shipped in Wilfred 0.2.2.

### Energy-aware appliances

Imagine asking:

> **Is this a good time to run the washing machine?**

A future goal could combine:

    Energy
       ↓
    Laundry
       ↓
    Presence
       ↓
    decision or action

Each capability contributes knowledge from its own domain.

The user does not need a dedicated automation for every possible combination.

### EV charging

An EV capability could understand charging state and charging operations.

An Energy capability could contribute production, tariff or household-load
context.

Wilfred could provide the common resolution, policy and execution layer used
to build a larger charging goal.

### Garden and irrigation

A Garden capability could understand soil or environmental conditions while
an integration handles the actual sensors and irrigation hardware.

The domain knowledge remains separate from the device transport.

### Another home-automation platform

Home Assistant is not an architectural requirement of Wilfred.

A different automation manager can be integrated through its own plugin that
implements the shared Butler contracts while keeping platform-specific
authentication, transport and API behavior in that plugin.

Conceptually:

    Butler runtime
       ├── Home Assistant Plugin -> Home Assistant
       └── Another Home Plugin   -> another automation platform

The runtime remains focused on composition and capability execution rather than
learning every platform API itself.

### Your domain

Wilfred is not limited to smart-home examples.

A plugin can connect Wilfred to a domain or service such as:

- 3D printing;
- workshop operations;
- calendars;
- personal services;
- household processes;
- custom APIs;
- something that exists only in your environment.

That domain can then expose reusable capabilities: things the Butler knows how
to read, decide or do.

The useful question becomes:

> **What would you teach your Butler to do?**

## Public Alpha boundary

Wilfred 0.2.2 provides the public runtime foundations for this model.

It does not yet provide a complete catalogue of domain capabilities.

It also does not currently provide generic multi-tool planning chains,
background workers, schedulers or retry infrastructure.

The examples on this page are deliberately labelled so that public
functionality, real-world testing and architectural direction are not confused
with one another.
