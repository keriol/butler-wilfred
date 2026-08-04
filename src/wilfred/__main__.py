from __future__ import annotations

import json


def runtime_status() -> dict[str, str]:
    return {
        "name": "Wilfred",
        "status": "ok",
        "version": "0.1.0",
        "runtime": "standalone-bootstrap",
    }


def main() -> int:
    print(
        json.dumps(
            runtime_status(),
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
