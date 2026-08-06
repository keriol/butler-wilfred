# ADR 0001: Separate Alfred and Wilfred project contexts

- Status: Accepted
- Date: 2026-08-06
- Task: WILF-017

## Context

Wilfred is a public distribution built around reusable butler contracts,
runtime components, tools, workflows, and adapters.

Alfred is the private Keriol Home deployment. It contains operational
configuration, private integrations, household-specific behavior, and details
that must not leak into Wilfred's public development context.

Using one undifferentiated AI project context for both systems would create a
risk of accidental disclosure and would make the public architecture depend on
private implementation knowledge.

## Decision

Alfred and Wilfred use separate AI project contexts.

The Wilfred context may contain only information that is safe and useful for
the public distribution:

- public architecture and contracts;
- installation and configuration documentation;
- provider-agnostic tools, workflows, and adapters;
- public issues, milestones, release notes, and examples;
- sanitized acceptance criteria and test evidence.

The Alfred context owns private operational knowledge:

- household-specific configuration and entity mappings;
- private services, adapters, endpoints, and infrastructure;
- secrets, identifiers, personal data, and acquisition mechanisms;
- deployment procedures and behavior specific to Keriol Home.

Knowledge may cross the boundary only through reviewed, versioned artifacts:

1. architecture decision records;
2. public contracts and schemas;
3. release notes;
4. sanitized examples;
5. explicit compatibility and acceptance checklists.

Conversation history is not a synchronization mechanism.

## Architectural consequences

Wilfred must remain understandable, testable, and installable without access
to Alfred's project context.

Public components must not import private Alfred modules or rely on private
paths, services, credentials, device identifiers, or household assumptions.

Alfred may consume released Wilfred contracts and packages. Private extensions
remain adapters or plugins owned by Alfred and are not copied into the public
distribution.

Changes affecting both projects are implemented in this order:

1. define or update the public contract in Wilfred;
2. test and version the public behavior;
3. update Alfred as a consumer;
4. record private deployment evidence in Alfred's own ledger.

## Review checklist

Before publishing a Wilfred change, verify that:

- the change is useful without Alfred;
- documentation does not expose private operational details;
- examples use neutral names and placeholder values;
- no secret, private endpoint, local path, device ID, or personal data appears;
- Alfred-specific behavior is represented only as a generic extension point;
- compatibility requirements are expressed as public contracts or tests.

## Rejected alternatives

### One shared project context

Rejected because private operational details could influence or enter public
documentation, examples, tests, or implementation.

### Copying selected conversations between projects

Rejected because conversation fragments are not versioned, reviewable
interfaces and can silently omit assumptions.

### Making Alfred the reference implementation inside Wilfred

Rejected because Wilfred must be independently installable and must not depend
on the private household deployment.
