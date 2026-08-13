# Development environment

Wilfred requires Python 3.12 or newer.

Create an isolated environment from the repository root:

~~~bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
~~~

Compile source and tests:

~~~bash
.venv/bin/python -m compileall -q src tests
~~~

Run the complete suite:

~~~bash
.venv/bin/python -m pytest -q
~~~

The `dev` extra contains development, packaging and HTTP test tools.
Normal Wilfred installations do not install them. Production HTTP support
is available separately through the `http` extra.

The suite includes the clean-room wheel test, which verifies that the
public distribution works without another butler repository.

## Versioning toward 0.2.0

Wilfred uses the `0.1.x` series for small, verifiable milestones on the path
to `0.2.0`.

The current development baseline is `0.2.0.dev0`.

Subsequent `0.1.x` versions represent concrete increments in packaging,
distribution, onboarding and public usability. They are milestones, not a
literal percentage-complete scale.

`0.2.0` remains the target for the first sufficiently installable and
verified public release milestone.

## Native capabilities

Wilfred can provide capabilities through the same public tool contract used
by plugins and integrations.

The first built-in READ capabilities are:

- `wilfred_status`: reports public runtime status and package version.
- `wilfred_tools`: describes the tools currently registered in the runtime.

Native capabilities are registered in `ToolRegistry` and executed through
`ExecutionEngine`. They do not bypass validation, permissions or execution
policy.

### Native CLI capabilities

Wilfred exposes its native READ capabilities through the same Tool
Registry and Execution Engine used by registered tools.

Commands:

    wilfred status
    wilfred tools

Running `wilfred` without a subcommand preserves the existing
standalone bootstrap behavior.

### Automated releases

Stable Wilfred releases are published from immutable semantic-version
tags such as `v0.1.7`.

The release workflow verifies that the tag and package version match,
that the tagged commit belongs to `main`, and that the public test
suite passes. It then builds wheel and source distributions, verifies
the wheel in a clean virtual environment, checks package dependencies
and CLI entry points, and finally publishes the artifacts as a GitHub
Release.

Development versions such as `0.1.7.dev0` therefore cannot be
published using a stable `v0.1.7` tag.

### Versioned release notes

Every stable release must include a non-empty versioned public release note
at `docs/releases/<version>.md`.

The release workflow treats this file as part of the release contract:

- its version heading must match the stable package version;
- the workflow fails before publication if the file is missing or empty;
- the GitHub Release body is published directly from this file;
- GitHub-generated notes are not used as the authoritative release summary.

This keeps release notes reviewable, versioned with the source tree and
identical to the public GitHub Release description.
