# OpenAI planner provider

Wilfred includes an optional OpenAI implementation of the Butler Core
`PlannerProvider` contract.

The provider is exposed from `wilfred.providers` as
`OpenAIPlannerProvider`.

## Installation

OpenAI support is optional:

`python -m pip install 'wilfred-butler[openai]'`

The base Wilfred installation does not require the OpenAI SDK.

## BYOK credential

The OpenAI API key is supplied only through:

`WILFRED_OPENAI_API_KEY`

The key is intentionally excluded from:

- TOML configuration;
- command-line options;
- `RuntimeConfig`;
- runtime status;
- provider output.

A caller creates the provider with `OpenAIPlannerProvider.from_environment()`.

## Planning

The adapter uses the OpenAI Responses API and requests a structured JSON tool
plan matching the Butler Core planner contract.

Wilfred still validates that plan before execution.

The OpenAI provider does not execute tools and does not grant confirmation.

## Scope

This provider does not change Butler Core and does not make OpenAI a mandatory
Wilfred dependency.

It does not add Home Assistant integration or a goal-oriented CLI command.
