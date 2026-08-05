# Runtime configuration

Wilfred starts without a configuration file.

The built-in defaults are:

- Butler name: `Wilfred`
- locale: `en`
- log level: `INFO`

## Configuration file

Pass an explicit TOML file with `--config`:

~bash
wilfred --config examples/wilfred.toml
~

The supported structure is:

~toml
[identity]
name = "Wilfred"
locale = "en"

[runtime]
log_level = "INFO"
~

Unknown sections and keys are rejected so that misspelled or obsolete
settings do not silently change runtime behaviour.

## Environment variables

The following variables are supported:

| Variable | Configuration value |
| --- | --- |
| `WILFRED_NAME` | `identity.name` |
| `WILFRED_LOCALE` | `identity.locale` |
| `WILFRED_LOG_LEVEL` | `runtime.log_level` |

Example:

~bash
WILFRED_LOCALE=it-IT WILFRED_LOG_LEVEL=DEBUG wilfred
~

## Command-line overrides

The public entrypoint supports:

~text
--config PATH
--name NAME
--locale LOCALE
--log-level LEVEL
~

Example:

~bash
wilfred \
  --config examples/wilfred.toml \
  --name "House Butler" \
  --locale it-IT \
  --log-level WARNING
~

## Precedence

Configuration is resolved from lowest to highest precedence:

1. built-in defaults;
2. the TOML file selected with `--config`;
3. `WILFRED_*` environment variables;
4. explicit command-line overrides.

Wilfred does not read configuration, credentials, paths or environment
variables from Alfred or from any other consumer application.

## Validation

The runtime rejects:

- missing configuration files;
- malformed TOML;
- unknown sections or keys;
- empty Butler names;
- invalid locale formats;
- unsupported log levels.

Configuration errors are written to standard error and the command exits
with status code `2`.
