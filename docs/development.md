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

## Read-only repository validation

Wilfred includes a public, repository-local validation command for mechanical
development checks:

~~~bash
wilfred validate
~~~

The command is read-only. It reports:

- the detected Wilfred repository root and project identity;
- current branch and HEAD;
- the configured comparison ref, defaulting to `origin/main`;
- ahead/behind divergence when that ref is available locally;
- staged, unstaged and untracked working-tree state;
- `git diff --check` for unstaged and staged changes;
- source/test compilation;
- pytest results.

It does not fetch, pull, stage, commit, merge, close issues, change versions,
install dependencies or deploy anything.

Focused tests can be run without the full suite:

~~~bash
wilfred validate --test tests/test_runtime.py
~~~

Multiple `--test` values are accepted. Add `--full` when the complete suite
should run after the focused targets:

~~~bash
wilfred validate \
  --test tests/test_runtime.py \
  --test tests/test_capability_resolvers.py \
  --full
~~~

Use `--base-ref` when comparing against another already-local Git ref. The
command never performs network synchronization implicitly.

The `dev` extra contains development, packaging and HTTP test tools.
Normal Wilfred installations do not install them. Production HTTP support
is available separately through the `http` extra.

The suite includes the clean-room wheel test, which verifies that the
public distribution works without another butler repository.

## Versioning and public checkpoints

Wilfred `0.2.0` established the Public Alpha baseline.

The current release baseline is `0.2.2`.

Development versions are working lines, not release promises. A new public
version is opened or released only when accumulated coherent value justifies
another public checkpoint.

A change to a release-contract dependency requires a new Wilfred semantic
version. When public compatibility is preserved, that means at least a patch
bump. A released `x.y.z` must never silently acquire a different dependency
baseline.

## Release BOM discipline

`distribution/bom.toml` describes the dependency baseline of the current
release checkpoint.

Every stable release also owns an immutable snapshot at:

`distribution/releases/<version>.toml`

At release time the current BOM and versioned snapshot must be byte-identical.
The release workflow validates the snapshot against the package version and tag
and publishes it as a GitHub Release asset beside the wheel and source
distribution.

The BOM records exact release-contract dependencies. For Wilfred 0.2.2 this
includes the immutable Butler Core 0.2.0 wheel and SHA256 plus the exact Home
Assistant plugin commit embedded by the reference Docker distribution.

Historical BOM snapshots are retained rather than rewritten when a later
release changes dependencies.

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
tags such as `v0.2.2`.

The release workflow verifies that the tag and package version match,
that the tagged commit belongs to `main`, that the version-specific BOM matches
the current distribution BOM, and that the public test suite passes. It then
builds wheel and source distributions, verifies the wheel in a clean virtual
environment, checks package dependencies and CLI entry points, and finally
publishes the artifacts plus the release BOM as a GitHub Release.

Development versions therefore cannot be published using a stable release tag.

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
