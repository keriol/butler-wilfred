from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
import tomllib


EXPECTED_PROJECT_NAME = "wilfred-butler"
DEFAULT_BASE_REF = "origin/main"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


CommandRunner = Callable[[Sequence[str], Path], CommandResult]


def _run_command(
    command: Sequence[str],
    cwd: Path,
) -> CommandResult:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _detail(result: CommandResult, *, limit: int = 1000) -> str | None:
    text = (result.stderr.strip() or result.stdout.strip())
    if not text:
        return None
    return text[-limit:]


def _check(
    name: str,
    result: CommandResult,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": name,
        "ok": result.returncode == 0,
        "exit_code": result.returncode,
    }
    detail = _detail(result)
    if detail is not None and result.returncode != 0:
        payload["detail"] = detail
    return payload


def _project_name(root: Path) -> str | None:
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return None

    try:
        payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None

    project = payload.get("project")
    if not isinstance(project, dict):
        return None

    name = project.get("name")
    return str(name).strip() if name else None


def _working_tree_state(status_output: str) -> dict[str, bool]:
    lines = [
        line
        for line in status_output.splitlines()
        if line
    ]

    untracked = any(line.startswith("??") for line in lines)
    staged = any(
        not line.startswith("??")
        and len(line) >= 1
        and line[0] not in {" ", "?"}
        for line in lines
    )
    unstaged = any(
        not line.startswith("??")
        and len(line) >= 2
        and line[1] not in {" ", "?"}
        for line in lines
    )

    return {
        "clean": not lines,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
    }


def _divergence(value: str) -> tuple[int | None, int | None]:
    parts = value.strip().split()
    if len(parts) != 2:
        return None, None

    try:
        behind = int(parts[0])
        ahead = int(parts[1])
    except ValueError:
        return None, None

    return behind, ahead


def validate_repository(
    root: Path,
    *,
    test_targets: Sequence[str] = (),
    full_tests: bool = False,
    base_ref: str = DEFAULT_BASE_REF,
    runner: CommandRunner = _run_command,
) -> dict[str, object]:
    requested_root = root.expanduser().resolve()

    if not requested_root.exists():
        return {
            "ok": False,
            "repository": {
                "requested_root": str(requested_root),
            },
            "checks": [
                {
                    "name": "repository_exists",
                    "ok": False,
                    "exit_code": 1,
                    "detail": "Repository path does not exist.",
                }
            ],
        }

    git_root_result = runner(
        ("git", "rev-parse", "--show-toplevel"),
        requested_root,
    )

    if git_root_result.returncode != 0:
        return {
            "ok": False,
            "repository": {
                "requested_root": str(requested_root),
            },
            "checks": [
                _check("git_repository", git_root_result),
            ],
        }

    repository_root = Path(
        git_root_result.stdout.strip()
    ).expanduser().resolve()

    project_name = _project_name(repository_root)
    project_check = {
        "name": "project_identity",
        "ok": project_name == EXPECTED_PROJECT_NAME,
        "exit_code": (
            0
            if project_name == EXPECTED_PROJECT_NAME
            else 1
        ),
    }
    if not project_check["ok"]:
        project_check["detail"] = (
            "Expected project "
            f"{EXPECTED_PROJECT_NAME!r}, found {project_name!r}."
        )
        return {
            "ok": False,
            "repository": {
                "root": str(repository_root),
                "project": project_name,
            },
            "checks": [project_check],
        }

    branch_result = runner(
        ("git", "branch", "--show-current"),
        repository_root,
    )
    head_result = runner(
        ("git", "rev-parse", "HEAD"),
        repository_root,
    )
    base_result = runner(
        ("git", "rev-parse", base_ref),
        repository_root,
    )
    status_result = runner(
        ("git", "status", "--porcelain=v1"),
        repository_root,
    )

    divergence_result = (
        runner(
            (
                "git",
                "rev-list",
                "--left-right",
                "--count",
                f"{base_ref}...HEAD",
            ),
            repository_root,
        )
        if base_result.returncode == 0
        else CommandResult(
            returncode=1,
            stderr=f"Base ref {base_ref!r} is unavailable.",
        )
    )

    behind, ahead = (
        _divergence(divergence_result.stdout)
        if divergence_result.returncode == 0
        else (None, None)
    )

    working_tree = (
        _working_tree_state(status_result.stdout)
        if status_result.returncode == 0
        else {
            "clean": False,
            "staged": False,
            "unstaged": False,
            "untracked": False,
        }
    )

    checks: list[dict[str, object]] = [
        project_check,
        _check("git_branch", branch_result),
        _check("git_head", head_result),
        _check("git_base_ref", base_result),
        _check("git_divergence", divergence_result),
        _check("git_status", status_result),
    ]

    unstaged_diff = runner(
        ("git", "diff", "--check"),
        repository_root,
    )
    staged_diff = runner(
        ("git", "diff", "--cached", "--check"),
        repository_root,
    )
    checks.extend(
        (
            _check("git_diff_check", unstaged_diff),
            _check("git_staged_diff_check", staged_diff),
        )
    )

    compile_result = runner(
        (
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "src",
            "tests",
        ),
        repository_root,
    )
    checks.append(_check("compile", compile_result))

    targets = tuple(
        target.strip()
        for target in test_targets
        if target.strip()
    )

    if targets:
        targeted_result = runner(
            (
                sys.executable,
                "-m",
                "pytest",
                "-q",
                *targets,
            ),
            repository_root,
        )
        checks.append(
            _check("targeted_tests", targeted_result)
        )

    if full_tests or not targets:
        full_result = runner(
            (
                sys.executable,
                "-m",
                "pytest",
                "-q",
            ),
            repository_root,
        )
        checks.append(_check("full_tests", full_result))

    return {
        "ok": all(bool(check["ok"]) for check in checks),
        "repository": {
            "root": str(repository_root),
            "project": project_name,
            "branch": branch_result.stdout.strip() or None,
            "head": head_result.stdout.strip() or None,
            "base_ref": base_ref,
            "base_sha": base_result.stdout.strip() or None,
            "behind": behind,
            "ahead": ahead,
            "working_tree": working_tree,
        },
        "checks": checks,
    }


__all__ = [
    "CommandResult",
    "DEFAULT_BASE_REF",
    "EXPECTED_PROJECT_NAME",
    "validate_repository",
]
