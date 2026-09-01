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
CORE_REF = "827bbac1038b6591f88648e5b69e50ae66834c19"
CORE_ARCHIVE = (
    "https://github.com/keriol/butler-core/archive/"
    f"{CORE_REF}.tar.gz"
)


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
    def test_wheel_runs_as_standalone_distribution(self) -> None:
        build_environment = os.environ.copy()
        build_environment.pop("PYTHONPATH", None)
        build_environment.pop("PYTHONHOME", None)
        build_environment.pop("PIP_NO_INDEX", None)
        build_environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"

        offline_environment = build_environment.copy()
        offline_environment["PIP_NO_INDEX"] = "1"

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
                    "--wheel-dir",
                    str(wheelhouse),
                    CORE_ARCHIVE,
                ],
                cwd=lab,
                environment=build_environment,
            )

            core_wheels = list(
                wheelhouse.glob("butler_core-*.whl")
            )
            self.assertEqual(len(core_wheels), 1)
            core_wheel = core_wheels[0]
            self.assertIn("0.2.1.dev0", core_wheel.name)

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
                environment=build_environment,
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
            _run(
                [
                    sys.executable,
                    "-m",
                    "venv",
                    str(virtualenv),
                ],
                cwd=lab,
                environment=build_environment,
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
                    "--no-index",
                    str(core_wheel),
                ],
                cwd=lab,
                environment=offline_environment,
            )

            _run(
                [
                    str(clean_python),
                    "-m",
                    "pip",
                    "install",
                    "--no-index",
                    "--no-deps",
                    str(wheel),
                ],
                cwd=lab,
                environment=offline_environment,
            )

            _run(
                [
                    str(clean_python),
                    "-m",
                    "pip",
                    "check",
                ],
                cwd=lab,
                environment=offline_environment,
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

if importlib.util.find_spec("butler_core") is None:
    raise RuntimeError(
        "Butler Core is missing from the clean environment."
    )

if importlib.util.find_spec("fastapi") is not None:
    raise RuntimeError(
        "FastAPI leaked into the base Wilfred installation."
    )

if importlib.util.find_spec("uvicorn") is not None:
    raise RuntimeError(
        "Uvicorn leaked into the base Wilfred installation."
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
                environment=offline_environment,
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
                environment=offline_environment,
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

            api_help = _run(
                [
                    str(clean_wilfred),
                    "api",
                    "--help",
                ],
                cwd=lab,
                environment=offline_environment,
            )

            self.assertIn(
                "optional HTTP API",
                api_help.stdout,
            )


if __name__ == "__main__":
    unittest.main()
