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
from wilfred.providers import (
    OpenAIPlannerProvider,
    OpenAIProviderConfigurationError,
)
from wilfred.registry import ToolRegistry
from wilfred.runtime import WilfredRuntime


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

    goal = commands.add_parser(
        "goal",
        help="Plan and execute a goal through a planner provider.",
    )
    goal.add_argument(
        "message",
        help="Natural-language goal to plan.",
    )
    goal.add_argument(
        "--provider",
        choices=("openai",),
        required=True,
        help="Planner provider.",
    )
    goal.add_argument(
        "--model",
        required=True,
        help="Provider model identifier.",
    )
    goal.add_argument(
        "--confirmed",
        action="store_true",
        help="Explicitly confirm ACTION execution.",
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


def run_goal_command(
    *,
    message: str,
    provider_name: str,
    model: str,
    confirmed: bool,
    environ: Mapping[str, str],
) -> int:
    if provider_name != "openai":
        raise ValueError(
            f"Unsupported planner provider: {provider_name}"
        )

    provider = OpenAIPlannerProvider.from_environment(
        model=model,
        environ=environ,
    )

    runtime = WilfredRuntime(
        provider=provider,
        system_prompt=(
            "Select the appropriate Wilfred tool for the "
            "user's goal using only the available tools."
        ),
    )

    result = runtime.execute_goal(
        message,
        confirmed=confirmed,
    )

    plan = result.planning.plan

    planning = {
        "status": result.planning.status.value,
        "duration_ms": result.planning.duration_ms,
        "plan": (
            None
            if plan is None
            else {
                "tool_name": plan.tool_name,
                "arguments": dict(plan.arguments),
                "confidence": plan.confidence,
                "reason": plan.reason,
            }
        ),
        "model": result.planning.model,
        "error_code": result.planning.error_code,
        "error_message": result.planning.error_message,
        "validation_errors": [
            str(item)
            for item in result.planning.validation_errors
        ],
    }

    payload = {
        "planning": planning,
        "execution": (
            None
            if result.execution is None
            else result.execution.to_dict()
        ),
    }

    print(
        json.dumps(
            payload,
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

    if arguments.command in {"status", "tools"}:
        return run_native_command(arguments.command)

    if arguments.command == "goal":
        effective_environment = (
            os.environ
            if environ is None
            else environ
        )

        try:
            return run_goal_command(
                message=arguments.message,
                provider_name=arguments.provider,
                model=arguments.model,
                confirmed=arguments.confirmed,
                environ=effective_environment,
            )
        except OpenAIProviderConfigurationError as exc:
            print(
                f"wilfred: configuration error: {exc}",
                file=sys.stderr,
            )
            return 2

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
