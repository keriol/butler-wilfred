# ADR 0001: Separate public and private development contexts

- Status: Accepted
- Date: 2026-08-06
- Task: WILF-017

## Context

Wilfred is a public distribution built around reusable butler contracts,
runtime components, tools, workflows, adapters, and integrations.

Private consumers may combine released Wilfred components with operational
configuration, deployment-specific integrations, infrastructure, and behaviour
that does not belong in the public distribution.

Using one undifferentiated development context for the public distribution and
private deployments would create a risk of accidental disclosure and could
make the public architecture depend on private implementation knowledge.

## Decision

The public Wilfred development context and private consumer contexts remain
separate.

The Wilfred context may contain only information that is safe and useful for
the public distribution:

- public architecture and contracts;
- installation and configuration documentation;
- provider-agnostic tools, workflows, and adapters;
- public issues, milestones, release notes, and examples;
- sanitized acceptance criteria and test evidence.

Private consumer contexts own operational knowledge such as:

- deployment-specific configuration and mappings;
- private services, adapters, endpoints, and infrastructure;
- secrets, identifiers, personal data, and acquisition mechanisms;
- deployment procedures and consumer-specific behaviour.

Knowledge may cross the boundary only through reviewed, versioned artifacts:

1. architecture decision records;
2. public contracts and schemas;
3. release notes;
4. sanitized examples;
5. explicit compatibility and acceptance checklists.

Conversation history is not a synchronization mechanism.

## Architectural consequences

Wilfred must remain understandable, testable, and installable without access
to any private consumer context.

Public components must not import consumer-specific modules or rely on private
paths, services, credentials, device identifiers, infrastructure, or household
assumptions.

Private deployments may consume released Wilfred contracts and packages.
Private extensions remain adapters or plugins owned by their consumer and are
not copied into the public distribution.

Changes affecting both public contracts and private consumers are implemented
in this order:

1. define or update the public contract in Wilfred;
2. test and version the public behaviour;
3. update private consumers separately;
4. record deployment evidence in the private consumer's own development ledger.

## Review checklist

Before publishing a Wilfred change, verify that:

- the change is useful in standalone Wilfred;
- documentation does not expose private operational details;
- examples use neutral names and placeholder values;
- no secret, private endpoint, local path, device ID, or personal data appears;
- deployment-specific behaviour is represented only as a generic extension
  point;
- compatibility requirements are expressed as public contracts or tests.

## Rejected alternatives

### One shared development context

Rejected because private operational details could influence or enter public
documentation, examples, tests, or implementation.

### Copying selected conversations between contexts

Rejected because conversation fragments are not versioned, reviewable
interfaces and can silently omit assumptions.

### Making a private deployment the reference implementation

Rejected because Wilfred must be independently installable and must not depend
on any private consumer deployment.
