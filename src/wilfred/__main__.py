from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
import os
from pathlib import Path
import sys

from wilfred import __version__
from wilfred.config import (
    ConfigurationError,
    RuntimeConfig,
    load_config,
)


def runtime_status(
    config: RuntimeConfig | None = None,
) -> dict[str, str]:
    resolved = config or RuntimeConfig()

    return {
        "name": resolved.identity.name,
        "locale": resolved.identity.locale,
        "log_level": resolved.log_level,
        "status": "ok",
        "version": __version__,
        "runtime": "standalone-bootstrap",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wilfred",
        description=(
            "Start the public standalone Wilfred runtime."
        ),
    )

    parser.add_argument(
        "--config",
        type=Path,
        help=(
            "Load configuration from a TOML file. "
            "Environment and CLI values override it."
        ),
    )
    parser.add_argument(
        "--name",
        help="Override the public Butler name.",
    )
    parser.add_argument(
        "--locale",
        help="Override the Butler locale, such as en or it-IT.",
    )
    parser.add_argument(
        "--log-level",
        help=(
            "Override the runtime log level: DEBUG, INFO, "
            "WARNING, ERROR or CRITICAL."
        ),
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)

    try:
        config = load_config(
            config_file=arguments.config,
            environ=(
                os.environ
                if environ is None
                else environ
            ),
            cli_overrides={
                "name": arguments.name,
                "locale": arguments.locale,
                "log_level": arguments.log_level,
            },
        )
    except ConfigurationError as exc:
        print(
            f"wilfred: configuration error: {exc}",
            file=sys.stderr,
        )
        return 2

    print(
        json.dumps(
            runtime_status(config),
            ensure_ascii=False,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
