# HTTP API

Wilfred provides an optional FastAPI transport for the existing
`WilfredRuntime`. FastAPI supplies request validation, response schemas and an
OpenAPI document; the transport does not reimplement planning or execution.

## Installation

HTTP dependencies are optional:

```bash
python -m pip install 'wilfred-butler[http]'
```

The built-in server command currently supports the optional OpenAI planner.
Install both extras when using that provider:

```bash
python -m pip install 'wilfred-butler[http,openai]'
```

Provide the BYOK credential only through the environment:

```bash
export WILFRED_OPENAI_API_KEY='your-key-from-a-secret-store'
wilfred api --provider openai --model MODEL
```

There is no API-key command-line option and the credential is not part of an
HTTP request or response.

## Network defaults

The server binds to `127.0.0.1:8000` by default. It is therefore reachable
only from the local machine unless the operator explicitly selects another
bind address.

CORS is not enabled. Uvicorn access logging is disabled by the Wilfred server
command so query strings are not written to an access log.

The transport does not include authentication, TLS termination or rate
limiting. Do not bind it to a public interface without a separately managed
authenticated reverse proxy, TLS and an explicit network policy.

An embedding application can construct the transport directly:

```python
from wilfred.api import create_app

app = create_app(runtime)
```

`create_app()` accepts an already configured `WilfredRuntime`, so this path is
provider-neutral.

## Endpoints

### GET /health

Returns transport liveness without calling a planner provider:

```json
{"status": "ok"}
```

### GET /v1/runtime

Returns credential-free runtime metadata including registered tool, domain and
capability counts.

### GET /v1/tools

Returns deterministic public tool descriptions, including parameter schemas
and permissions. Python handlers are never exposed.

### GET /v1/domains

Returns deterministic domain metadata from the loaded capability registry:

```json
{
  "domains": [
    {
      "name": "media",
      "description": "Media discovery and playback.",
      "owner_plugin": "example.media"
    }
  ]
}
```

### GET /v1/capabilities

Returns deterministic, sanitized capability metadata:

```json
{
  "capabilities": [
    {
      "name": "media.playback",
      "domain": "media",
      "description": "Play resolved media.",
      "owner_plugin": "example.media"
    }
  ]
}
```

Discovery responses expose semantic metadata only. Resolver handlers, provider
configuration, credentials and private runtime payloads are not part of the
schema.

### POST /v1/goals

Delegates directly to `WilfredRuntime.execute_goal()`.

```json
{
  "message": "what is your status?",
  "confirmed": false
}
```

`message` is required. `confirmed` is optional, defaults to `false` and must be
a JSON boolean.

The response preserves the shared structured planning and execution result:

```json
{
  "planning": {
    "status": "success",
    "duration_ms": 1.0,
    "plan": {
      "tool_name": "wilfred_status",
      "arguments": {},
      "confidence": 1.0,
      "reason": "Read runtime status."
    },
    "model": null,
    "error_code": null,
    "error_message": null,
    "validation_errors": []
  },
  "execution": {
    "execution_id": "generated-identifier",
    "tool_name": "wilfred_status",
    "status": "success",
    "duration_ms": 1.0,
    "permission": "READ",
    "value": {
      "status": "ok"
    },
    "error": null,
    "validation_errors": []
  }
}
```

## CLI discovery

Capability discovery is also available without starting the HTTP transport or
configuring a planner:

```bash
wilfred domains
wilfred capabilities
```

Configured plugins can be supplied with repeated `--plugin MODULE:FACTORY`
arguments or through `WILFRED_PLUGINS`. These commands load plugin declarations
for introspection but do not call a planner provider.

## Confirmation boundary

The planner cannot grant confirmation. If an `ACTION` requires approval, a
request with the default `confirmed: false` returns an execution status of
`confirmation_required`.

Only after obtaining confirmation outside the planner may a client repeat the
goal with:

```json
{
  "message": "perform the action",
  "confirmed": true
}
```

`DANGEROUS` tools remain subject to `ExecutionPolicy`; confirmation does not
override the default dangerous-tool denial.

## Errors and secret handling

Planner and Execution Engine failures remain structured inside the normal goal
response. Request validation failures use HTTP 422 with an `invalid_request`
code. Validation responses omit received values instead of echoing the request
body. Unexpected runtime failures use HTTP 500 with a generic `runtime_error`
message.

The built-in command redacts the configured provider credential from nested
goal results. Values under common sensitive keys such as `api_key`, `password`,
`secret` and `token` are also redacted. Plugins and embedding applications must
still avoid placing credentials in tool schemas, results or exception text.

## Scope

This transport does not add Home Assistant entities, household configuration,
background jobs or a multi-step planner. Those remain separate public
integration tasks.
