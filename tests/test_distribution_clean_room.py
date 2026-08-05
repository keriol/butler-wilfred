from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _venv_executable(
    root: Path,
    name: str,
) -> Path:
    if os.name == "nt":
        suffix = ".exe" if name in {"python", "wilfred"} else ""
        return root / "Scripts" / f"{name}{suffix}"

    return root / "bin" / name


def _run(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )


class WilfredCleanRoomDistributionTests(unittest.TestCase):
    def test_wheel_runs_without_alfred(self) -> None:
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment.pop("PYTHONHOME", None)
        environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
        environment["PIP_NO_INDEX"] = "1"

        with tempfile.TemporaryDirectory(
            prefix="wilfred-clean-room-",
        ) as temporary:
            lab = Path(temporary)
            wheelhouse = lab / "wheelhouse"
            virtualenv = lab / "venv"

            wheelhouse.mkdir()

            _run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "wheel",
                    "--no-deps",
                    "--no-build-isolation",
                    "--wheel-dir",
                    str(wheelhouse),
                    str(PROJECT_ROOT),
                ],
                cwd=lab,
                environment=environment,
            )

            wheels = list(
                wheelhouse.glob(
                    "wilfred_butler-*.whl"
                )
            )

            self.assertEqual(len(wheels), 1)
            wheel = wheels[0]

            with zipfile.ZipFile(wheel) as archive:
                members = archive.namelist()

            unexpected = [
                member
                for member in members
                if not (
                    member.startswith("wilfred/")
                    or member.startswith(
                        "wilfred_butler-"
                    )
                )
            ]

            self.assertEqual(unexpected, [])
            self.assertFalse(
                any(
                    member.startswith("alfred/")
                    for member in members
                )
            )

            _run(
                [
                    sys.executable,
                    "-m",
                    "venv",
                    str(virtualenv),
                ],
                cwd=lab,
                environment=environment,
            )

            clean_python = _venv_executable(
                virtualenv,
                "python",
            )
            clean_wilfred = _venv_executable(
                virtualenv,
                "wilfred",
            )

            _run(
                [
                    str(clean_python),
                    "-m",
                    "pip",
                    "install",
                    "--no-deps",
                    "--no-index",
                    str(wheel),
                ],
                cwd=lab,
                environment=environment,
            )

            script = """
import importlib.util
import json
from pathlib import Path
import sys

import wilfred
from wilfred import (
    ExecutionEngine,
    ExecutionRequest,
    ExecutionStatus,
    ToolPermission,
    ToolRegistry,
    discover_plugins,
    load_plugins,
)

module_path = Path(wilfred.__file__).resolve()
prefix = Path(sys.prefix).resolve()

if prefix not in module_path.parents:
    raise RuntimeError(
        "Wilfred was not loaded from the clean virtualenv."
    )

if importlib.util.find_spec("alfred") is not None:
    raise RuntimeError(
        "Alfred is importable in the clean environment."
    )

registry = ToolRegistry()
plugins = discover_plugins(
    ["wilfred.plugins.demo_echo"]
)
results = load_plugins(registry, plugins)

tool = registry.get("demo_echo")

engine = ExecutionEngine(registry)

first = engine.execute(
    ExecutionRequest(
        tool_name="demo_echo",
        arguments={
            "message": "clean-room",
        },
    )
)
second = engine.execute(
    ExecutionRequest(
        tool_name="demo_echo",
        arguments={
            "message": "clean-room",
        },
    )
)

if tool is None:
    raise RuntimeError("Demo tool was not loaded.")

if tool.permission is not ToolPermission.READ:
    raise RuntimeError("Unexpected demo permission.")

if first.status is not ExecutionStatus.SUCCESS:
    raise RuntimeError(
        "Demo execution did not succeed."
    )

if second.status is not ExecutionStatus.SUCCESS:
    raise RuntimeError(
        "Second demo execution did not succeed."
    )

if first.value != second.value:
    raise RuntimeError(
        "Demo execution is not deterministic."
    )

if first.value != {"message": "clean-room"}:
    raise RuntimeError(
        "Unexpected demo execution result."
    )

print(
    json.dumps(
        {
            "module": str(module_path),
            "plugin": plugins[0].name,
            "tools": registry.names(),
            "result": first.value,
            "execution_status": first.status.value,
            "execution_id": first.execution_id,
            "load_results": len(results),
        },
        sort_keys=True,
    )
)
"""

            isolated = _run(
                [
                    str(clean_python),
                    "-I",
                    "-c",
                    script,
                ],
                cwd=lab,
                environment=environment,
            )

            payload = json.loads(
                isolated.stdout.strip()
            )

            self.assertEqual(
                payload["plugin"],
                "demo.echo",
            )
            self.assertEqual(
                payload["tools"],
                ["demo_echo"],
            )
            self.assertEqual(
                payload["result"],
                {"message": "clean-room"},
            )
            self.assertEqual(
                payload["execution_status"],
                "success",
            )
            self.assertTrue(
                payload["execution_id"],
            )

            entrypoint = _run(
                [str(clean_wilfred)],
                cwd=lab,
                environment=environment,
            )

            status = json.loads(
                entrypoint.stdout.strip()
            )

            self.assertEqual(
                status["name"],
                "Wilfred",
            )
            self.assertEqual(
                status["status"],
                "ok",
            )
            self.assertEqual(
                status["runtime"],
                "standalone-bootstrap",
            )


if __name__ == "__main__":
    unittest.main()
