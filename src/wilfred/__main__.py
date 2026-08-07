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
from wilfred.native import register_native_tools
from wilfred.registry import ToolRegistry


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

    commands = parser.add_subparsers(dest="command")

    commands.add_parser(
        "status",
        help="Show Wilfred native runtime status.",
    )
    commands.add_parser(
        "tools",
        help="List Wilfred native capabilities.",
    )

    return parser


def run_native_command(command: str) -> int:
    registry = ToolRegistry()
    register_native_tools(registry)

    tool_name = {
        "status": "wilfred_status",
        "tools": "wilfred_tools",
    }[command]

    result = registry.execute(tool_name)

    if not result.ok:
        print(
            json.dumps(
                result.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    print(
        json.dumps(
            result.value,
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)

    if arguments.command is not None:
        return run_native_command(arguments.command)

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
