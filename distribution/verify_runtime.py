from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request


def get_json(
    base_url: str,
    path: str,
) -> dict[str, object]:
    with urllib.request.urlopen(
        base_url.rstrip("/") + path,
        timeout=3,
    ) as response:
        return json.load(response)


def wait_for_health(
    base_url: str,
    *,
    attempts: int,
) -> None:
    last_error: Exception | None = None

    for _ in range(attempts):
        try:
            health = get_json(
                base_url,
                "/health",
            )

            if health == {"status": "ok"}:
                return
        except (
            OSError,
            urllib.error.URLError,
            ValueError,
        ) as exc:
            last_error = exc

        time.sleep(1)

    raise RuntimeError(
        "Wilfred did not become healthy."
    ) from last_error


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "base_url",
    )

    parser.add_argument(
        "--attempts",
        type=int,
        default=30,
    )

    args = parser.parse_args()

    wait_for_health(
        args.base_url,
        attempts=args.attempts,
    )

    health = get_json(
        args.base_url,
        "/health",
    )

    runtime = get_json(
        args.base_url,
        "/v1/runtime",
    )

    tools = get_json(
        args.base_url,
        "/v1/tools",
    )

    names = sorted(
        item["name"]
        for item in tools["tools"]
    )

    required = {
        "wilfred_status",
        "wilfred_tools",
        "home_assistant_get_state",
        "home_assistant_call_action",
    }

    missing = sorted(
        required - set(names)
    )

    if missing:
        raise RuntimeError(
            "Missing expected tools: "
            + ", ".join(missing)
        )

    if health != {"status": "ok"}:
        raise RuntimeError(
            f"Unexpected health response: {health}"
        )

    if runtime.get("status") != "ok":
        raise RuntimeError(
            f"Unexpected runtime response: {runtime}"
        )

    print(
        json.dumps(
            {
                "health": health,
                "runtime": runtime,
                "tools": names,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
