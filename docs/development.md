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

The `dev` extra contains development and packaging tools only.
Normal Wilfred installations do not install them.

The suite includes the clean-room wheel test, which verifies that the
public distribution works without another butler repository.
