from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Literal


class HTTPAPIUnavailableError(RuntimeError):
    """Raised when optional HTTP dependencies are unavailable."""


try:
    from fastapi import FastAPI
    from fastapi.encoders import jsonable_encoder
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, ConfigDict, Field
except ModuleNotFoundError as exc:
    raise HTTPAPIUnavailableError(
        "HTTP API support requires 'wilfred-butler[http]'."
    ) from exc

from wilfred import __version__
from wilfred.runtime import WilfredRuntime


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
MAX_GOAL_LENGTH = 10_000
REDACTED = "[REDACTED]"

_SENSITIVE_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "password",
        "secret",
        "token",
    }
)


class HealthResponse(BaseModel):
    status: Literal["ok"]


class RuntimeResponse(BaseModel):
    name: str
    status: Literal["ok"]
    version: str
    runtime: str
    tool_count: int
    domain_count: int
    capability_count: int


class ToolResponse(BaseModel):
    name: str
    description: str
    category: str
    permission: str
    parameters: dict[str, Any]


class ToolsResponse(BaseModel):
    tools: list[ToolResponse]


class DomainResponse(BaseModel):
    name: str
    description: str
    owner_plugin: str


class DomainsResponse(BaseModel):
    domains: list[DomainResponse]


class CapabilityResponse(BaseModel):
    name: str
    domain: str
    description: str
    owner_plugin: str


class CapabilitiesResponse(BaseModel):
    capabilities: list[CapabilityResponse]


class GoalRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    message: str = Field(
        min_length=1,
        max_length=MAX_GOAL_LENGTH,
    )
    confirmed: bool = Field(
        default=False,
        strict=True,
    )


class ToolPlanResponse(BaseModel):
    tool_name: str | None
    arguments: dict[str, Any]
    confidence: float
    reason: str


class PlanningResponse(BaseModel):
    status: str
    duration_ms: float
    plan: ToolPlanResponse | None
    model: str | None
    error_code: str | None
    error_message: str | None
    validation_errors: list[str]


class ResultErrorResponse(BaseModel):
    code: str
    message: str | None


class ExecutionResponse(BaseModel):
    execution_id: str
    tool_name: str
    status: str
    duration_ms: float
    permission: str | None
    value: Any = None
    error: ResultErrorResponse | None
    validation_errors: list[str]


class GoalResponse(BaseModel):
    planning: PlanningResponse
    execution: ExecutionResponse | None


class ValidationIssueResponse(BaseModel):
    location: list[str | int]
    code: str
    message: str


class APIErrorDetailResponse(BaseModel):
    code: str
    message: str
    validation_errors: list[ValidationIssueResponse] = Field(
        default_factory=list
    )


class APIErrorResponse(BaseModel):
    error: APIErrorDetailResponse


def _key_is_sensitive(key: object) -> bool:
    normalized = str(key).strip().lower().replace("-", "_")

    return (
        normalized in _SENSITIVE_KEYS
        or normalized.endswith("_api_key")
        or normalized.endswith("_password")
        or normalized.endswith("_secret")
        or normalized.endswith("_token")
    )


def _sanitize(
    value: Any,
    *,
    sensitive_values: tuple[str, ...],
) -> Any:
    if isinstance(value, Mapping):
        return {
            key: (
                REDACTED
                if _key_is_sensitive(key)
                else _sanitize(
                    item,
                    sensitive_values=sensitive_values,
                )
            )
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            _sanitize(
                item,
                sensitive_values=sensitive_values,
            )
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            _sanitize(
                item,
                sensitive_values=sensitive_values,
            )
            for item in value
        ]

    if isinstance(value, str):
        sanitized = value

        for secret in sensitive_values:
            sanitized = sanitized.replace(secret, REDACTED)

        return sanitized

    return value


def _resolved_sensitive_values(
    values: Iterable[str],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                value
                for item in values
                if (value := item.strip())
            },
            key=len,
            reverse=True,
        )
    )


def create_app(
    runtime: WilfredRuntime,
    *,
    sensitive_values: Iterable[str] = (),
) -> FastAPI:
    """Create the optional FastAPI transport for a Goal Runtime."""

    secrets = _resolved_sensitive_values(sensitive_values)

    app = FastAPI(
        title="Wilfred HTTP API",
        version=__version__,
        description=(
            "Provider-neutral HTTP transport for the Wilfred "
            "Goal Runtime."
        ),
    )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(
        request: object,
        error: RequestValidationError,
    ) -> JSONResponse:
        del request

        issues = [
            {
                "location": list(issue.get("loc", ())),
                "code": str(issue.get("type", "invalid")),
                "message": str(
                    issue.get("msg", "Invalid request value.")
                ),
            }
            for issue in error.errors()
        ]

        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "invalid_request",
                    "message": "Request validation failed.",
                    "validation_errors": issues,
                }
            },
        )

    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["system"],
    )
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get(
        "/v1/runtime",
        response_model=RuntimeResponse,
        tags=["runtime"],
    )
    def runtime_info() -> dict[str, object]:
        return runtime.describe_runtime()

    @app.get(
        "/v1/tools",
        response_model=ToolsResponse,
        tags=["runtime"],
    )
    def tools() -> dict[str, object]:
        return {"tools": runtime.describe_tools()}

    @app.get(
        "/v1/domains",
        response_model=DomainsResponse,
        tags=["runtime"],
    )
    def domains() -> dict[str, object]:
        return {"domains": runtime.describe_domains()}

    @app.get(
        "/v1/capabilities",
        response_model=CapabilitiesResponse,
        tags=["runtime"],
    )
    def capabilities() -> dict[str, object]:
        return {"capabilities": runtime.describe_capabilities()}

    @app.post(
        "/v1/goals",
        response_model=GoalResponse,
        responses={
            422: {"model": APIErrorResponse},
            500: {"model": APIErrorResponse},
        },
        tags=["goals"],
    )
    def execute_goal(request: GoalRequest) -> Any:
        try:
            result = runtime.execute_goal(
                request.message,
                confirmed=request.confirmed,
            )
            payload = _sanitize(
                result.to_dict(),
                sensitive_values=secrets,
            )

            return jsonable_encoder(payload)
        except Exception:
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "runtime_error",
                        "message": "Goal execution failed.",
                        "validation_errors": [],
                    }
                },
            )

    return app


def serve_api(
    runtime: WilfredRuntime,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    sensitive_values: Iterable[str] = (),
) -> None:
    """Serve a configured runtime without public-network defaults."""

    try:
        import uvicorn
    except ModuleNotFoundError as exc:
        raise HTTPAPIUnavailableError(
            "HTTP API support requires 'wilfred-butler[http]'."
        ) from exc

    app = create_app(
        runtime,
        sensitive_values=sensitive_values,
    )

    uvicorn.run(
        app,
        host=host,
        port=port,
        access_log=False,
    )


__all__ = [
    "CapabilitiesResponse",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "DomainsResponse",
    "GoalRequest",
    "GoalResponse",
    "HTTPAPIUnavailableError",
    "create_app",
    "serve_api",
]
