from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
import os
from pathlib import Path
import sys

from wilfred import __version__
from wilfred.capability_registry import CapabilityRegistry
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
from wilfred.plugins import discover_configured_plugins
from wilfred.registry import ToolRegistry
from wilfred.runtime import WilfredRuntime


DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8000


class HTTPAPIConfigurationError(ValueError):
    """Raised when the optional HTTP runtime cannot start."""


def _api_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "port must be an integer"
        ) from exc

    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError(
            "port must be between 1 and 65535"
        )

    return port


def _plugin_specs(
    cli_values: Sequence[str],
    environ: Mapping[str, str],
) -> tuple[str, ...]:
    environment_values = [
        value.strip()
        for value in environ.get(
            "WILFRED_PLUGINS",
            "",
        ).split(",")
        if value.strip()
    ]

    return tuple(
        sorted(
            {
                value.strip()
                for value in [
                    *environment_values,
                    *cli_values,
                ]
                if value.strip()
            }
        )
    )


def _add_plugin_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--plugin",
        action="append",
        default=[],
        metavar="MODULE:FACTORY",
        help=(
            "Load a configured plugin factory. "
            "May be repeated."
        ),
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

    commands = parser.add_subparsers(dest="command")

    commands.add_parser(
        "status",
        help="Show Wilfred native runtime status.",
    )
    commands.add_parser(
        "tools",
        help="List Wilfred native tools.",
    )

    domains = commands.add_parser(
        "domains",
        help="List domains declared by configured plugins.",
    )
    _add_plugin_argument(domains)

    capabilities = commands.add_parser(
        "capabilities",
        help="List capabilities declared by configured plugins.",
    )
    _add_plugin_argument(capabilities)

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
    _add_plugin_argument(goal)

    goal.add_argument(
        "--confirmed",
        action="store_true",
        help="Explicitly confirm ACTION execution.",
    )

    api = commands.add_parser(
        "api",
        help="Serve the goal runtime through the optional HTTP API.",
        description=(
            "Serve the goal runtime through the optional HTTP API."
        ),
    )
    _add_plugin_argument(api)

    api.add_argument(
        "--provider",
        choices=("openai",),
        required=True,
        help="Planner provider.",
    )
    api.add_argument(
        "--model",
        required=True,
        help="Provider model identifier.",
    )
    api.add_argument(
        "--host",
        default=DEFAULT_API_HOST,
        help=(
            "HTTP bind address. Defaults to the loopback-only "
            f"address {DEFAULT_API_HOST}."
        ),
    )
    api.add_argument(
        "--port",
        type=_api_port,
        default=DEFAULT_API_PORT,
        help=f"HTTP port. Defaults to {DEFAULT_API_PORT}.",
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


def run_discovery_command(
    *,
    command: str,
    plugin_specs: Sequence[str],
    environ: Mapping[str, str],
) -> int:
    plugins = discover_configured_plugins(
        plugin_specs,
        environ=environ,
    )
    registry = CapabilityRegistry.from_plugins(plugins)

    payload = (
        {"domains": registry.describe_domains()}
        if command == "domains"
        else {"capabilities": registry.describe_capabilities()}
    )

    print(
        json.dumps(
            payload,
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
    plugin_specs: Sequence[str],
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

    plugins = discover_configured_plugins(
        plugin_specs,
        environ=environ,
    )

    runtime = WilfredRuntime(
        provider=provider,
        plugins=plugins,
        system_prompt=(
            "Select the appropriate Wilfred tool for the "
            "user's goal using only the available tools."
        ),
    )

    result = runtime.execute_goal(
        message,
        confirmed=confirmed,
    )

    print(
        json.dumps(
            result.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
        )
    )

    return 0


def run_api_command(
    *,
    provider_name: str,
    model: str,
    host: str,
    port: int,
    plugin_specs: Sequence[str],
    environ: Mapping[str, str],
) -> int:
    try:
        from wilfred.api import (
            HTTPAPIUnavailableError,
            serve_api,
        )
    except (ImportError, RuntimeError) as exc:
        raise HTTPAPIConfigurationError(
            "HTTP API support requires the optional "
            "'http' dependencies."
        ) from exc

    if provider_name != "openai":
        raise ValueError(
            f"Unsupported planner provider: {provider_name}"
        )

    provider = OpenAIPlannerProvider.from_environment(
        model=model,
        environ=environ,
    )

    plugins = discover_configured_plugins(
        plugin_specs,
        environ=environ,
    )

    runtime = WilfredRuntime(
        provider=provider,
        plugins=plugins,
        system_prompt=(
            "Select the appropriate Wilfred tool for the "
            "user's goal using only the available tools."
        ),
    )

    secret = environ.get(
        "WILFRED_OPENAI_API_KEY",
        "",
    ).strip()

    try:
        serve_api(
            runtime,
            host=host,
            port=port,
            sensitive_values=(secret,),
        )
    except HTTPAPIUnavailableError as exc:
        raise HTTPAPIConfigurationError(str(exc)) from exc

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

    if arguments.command in {"domains", "capabilities"}:
        effective_environment = (
            os.environ
            if environ is None
            else environ
        )
        return run_discovery_command(
            command=arguments.command,
            plugin_specs=_plugin_specs(
                arguments.plugin,
                effective_environment,
            ),
            environ=effective_environment,
        )

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
                plugin_specs=_plugin_specs(
                    arguments.plugin,
                    effective_environment,
                ),
                environ=effective_environment,
            )
        except OpenAIProviderConfigurationError as exc:
            print(
                f"wilfred: configuration error: {exc}",
                file=sys.stderr,
            )
            return 2

    if arguments.command == "api":
        effective_environment = (
            os.environ
            if environ is None
            else environ
        )

        try:
            return run_api_command(
                provider_name=arguments.provider,
                model=arguments.model,
                host=arguments.host,
                port=arguments.port,
                plugin_specs=_plugin_specs(
                    arguments.plugin,
                    effective_environment,
                ),
                environ=effective_environment,
            )
        except (
            HTTPAPIConfigurationError,
            OpenAIProviderConfigurationError,
        ) as exc:
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
