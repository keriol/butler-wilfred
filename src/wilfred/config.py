from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import tomllib
from typing import Any


_VALID_LOG_LEVELS = frozenset(
    {
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    }
)

_LOCALE_PATTERN = re.compile(
    r"[a-z]{2}(?:-[A-Z]{2})?"
)

_ALLOWED_SECTIONS = frozenset(
    {
        "identity",
        "runtime",
    }
)

_ALLOWED_IDENTITY_KEYS = frozenset(
    {
        "name",
        "locale",
        "aliases",
        "description",
        "profile_picture",
    }
)

_ALLOWED_RUNTIME_KEYS = frozenset(
    {
        "log_level",
    }
)


class ConfigurationError(ValueError):
    """Raised when Wilfred configuration is invalid."""


@dataclass(frozen=True)
class ButlerIdentity:
    """Public identity exposed by a Butler runtime."""

    name: str = "Wilfred"
    locale: str = "en"
    aliases: tuple[str, ...] = ()
    description: str = ""
    profile_picture: str | None = None


@dataclass(frozen=True)
class RuntimeConfig:
    """Resolved standalone Wilfred runtime configuration."""

    identity: ButlerIdentity = field(
        default_factory=ButlerIdentity
    )
    log_level: str = "INFO"


def _require_table(
    document: Mapping[str, Any],
    section: str,
) -> Mapping[str, Any]:
    value = document.get(section, {})

    if not isinstance(value, dict):
        raise ConfigurationError(
            f"Configuration section [{section}] "
            "must be a TOML table."
        )

    return value


def _reject_unknown(
    actual: set[str],
    allowed: frozenset[str],
    *,
    location: str,
) -> None:
    unknown = sorted(actual - allowed)

    if unknown:
        raise ConfigurationError(
            f"Unknown {location}: {', '.join(unknown)}"
        )


def _read_config_file(
    path: Path,
) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigurationError(
            f"Configuration file does not exist: {path}"
        )

    try:
        with path.open("rb") as stream:
            document = tomllib.load(stream)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigurationError(
            f"Invalid TOML in {path}: {exc}"
        ) from exc
    except OSError as exc:
        raise ConfigurationError(
            f"Cannot read configuration file {path}: {exc}"
        ) from exc

    _reject_unknown(
        set(document),
        _ALLOWED_SECTIONS,
        location="configuration sections",
    )

    identity = _require_table(
        document,
        "identity",
    )
    runtime = _require_table(
        document,
        "runtime",
    )

    _reject_unknown(
        set(identity),
        _ALLOWED_IDENTITY_KEYS,
        location="[identity] keys",
    )
    _reject_unknown(
        set(runtime),
        _ALLOWED_RUNTIME_KEYS,
        location="[runtime] keys",
    )

    values: dict[str, Any] = {}

    for key in ("name", "locale"):
        if key not in identity:
            continue

        value = identity[key]

        if not isinstance(value, str):
            raise ConfigurationError(
                f"identity.{key} must be a string."
            )

        values[key] = value

    if "aliases" in identity:
        aliases = identity["aliases"]
        if not isinstance(aliases, list) or not all(isinstance(x, str) for x in aliases):
            raise ConfigurationError("identity.aliases must be an array of strings.")
        values["aliases"] = tuple(aliases)

    for key in ("description", "profile_picture"):
        if key in identity:
            value = identity[key]
            if not isinstance(value, str):
                raise ConfigurationError(f"identity.{key} must be a string.")
            values[key] = value

    if "log_level" in runtime:
        value = runtime["log_level"]

        if not isinstance(value, str):
            raise ConfigurationError(
                "runtime.log_level must be a string."
            )

        values["log_level"] = value

    return values


def _environment_values(
    environ: Mapping[str, str],
) -> dict[str, str]:
    variables = {
        "name": "WILFRED_NAME",
        "locale": "WILFRED_LOCALE",
        "log_level": "WILFRED_LOG_LEVEL",
    }

    return {
        key: environ[variable]
        for key, variable in variables.items()
        if variable in environ
    }


def _cli_values(
    overrides: Mapping[str, str | None],
) -> dict[str, str]:
    _reject_unknown(
        set(overrides),
        frozenset(
            {
                "name",
                "locale",
                "log_level",
            }
        ),
        location="CLI override keys",
    )

    return {
        key: value
        for key, value in overrides.items()
        if value is not None
    }


def _validate(
    values: Mapping[str, Any],
) -> RuntimeConfig:
    name = values["name"].strip()

    if not name:
        raise ConfigurationError(
            "identity.name cannot be empty."
        )

    if len(name) > 80:
        raise ConfigurationError(
            "identity.name cannot exceed 80 characters."
        )

    locale = values["locale"].strip()

    if _LOCALE_PATTERN.fullmatch(locale) is None:
        raise ConfigurationError(
            "identity.locale must use 'en' or "
            "'en-US' format."
        )

    log_level = values["log_level"].strip().upper()

    if log_level not in _VALID_LOG_LEVELS:
        allowed = ", ".join(sorted(_VALID_LOG_LEVELS))

        raise ConfigurationError(
            "runtime.log_level must be one of: "
            f"{allowed}."
        )

    aliases = values.get("aliases", ())
    if not isinstance(aliases, tuple) or not all(isinstance(x, str) for x in aliases):
        raise ConfigurationError("identity.aliases must be a tuple of strings.")
    normalized = [name.casefold()]
    for alias in aliases:
        candidate = alias.strip()
        if not candidate or len(candidate) > 80:
            raise ConfigurationError("identity.aliases must contain names of 1-80 characters.")
        key = candidate.casefold()
        if key in normalized:
            raise ConfigurationError("identity.aliases duplicate a canonical name or alias.")
        normalized.append(key)

    description = values.get("description", "")
    if not isinstance(description, str) or len(description) > 500:
        raise ConfigurationError("identity.description must be a string of at most 500 characters.")

    picture = values.get("profile_picture")
    if picture is not None:
        if not isinstance(picture, str):
            raise ConfigurationError("identity.profile_picture must be a string.")
        # Reference is intentionally NOT loaded or exposed in runtime metadata.
        # No absolute path, traversal or network scheme is admitted.
        pure = Path(picture)
        if (
            not picture.strip()
            or picture != picture.strip()
            or pure.is_absolute()
            or "\\\\" in picture
            or "\\" in picture
            or ":" in picture
            or any(segment in ("", ".", "..") for segment in picture.split("/"))
            or pure.suffix.lower() != ".png"
        ):
            raise ConfigurationError("identity.profile_picture must be a relative PNG path without traversal.")

    return RuntimeConfig(
        identity=ButlerIdentity(
            name=name,
            locale=locale,
            aliases=tuple(alias.strip() for alias in aliases),
            description=description,
            profile_picture=picture,
        ),
        log_level=log_level,
    )


def load_config(
    *,
    config_file: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    cli_overrides: Mapping[
        str,
        str | None,
    ] | None = None,
) -> RuntimeConfig:
    """
    Resolve Wilfred configuration.

    Precedence, from lowest to highest:

    1. built-in defaults;
    2. TOML configuration file;
    3. WILFRED_* environment variables;
    4. explicit CLI overrides.
    """

    resolved = {
        "name": "Wilfred",
        "locale": "en",
        "log_level": "INFO",
        "aliases": (),
        "description": "",
        "profile_picture": None,
    }

    if config_file is not None:
        resolved.update(
            _read_config_file(
                Path(config_file).expanduser()
            )
        )

    effective_environment = (
        os.environ
        if environ is None
        else environ
    )

    resolved.update(
        _environment_values(
            effective_environment
        )
    )

    if cli_overrides is not None:
        resolved.update(
            _cli_values(cli_overrides)
        )

    return _validate(resolved)
