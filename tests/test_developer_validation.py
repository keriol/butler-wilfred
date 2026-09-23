from __future__ import annotations

from pathlib import Path

from wilfred.developer_validation import (
    CommandResult,
    validate_repository,
)


def _runner(responses):
    calls = []

    def run(command, cwd):
        key = tuple(command)
        calls.append((key, cwd))
        return responses.get(
            key,
            CommandResult(returncode=0),
        )

    return run, calls


def test_validate_repository_reports_clean_checkout(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "wilfred-butler"\n',
        encoding="utf-8",
    )

    responses = {
        ("git", "rev-parse", "--show-toplevel"): CommandResult(
            0,
            stdout=f"{tmp_path}\n",
        ),
        ("git", "branch", "--show-current"): CommandResult(
            0,
            stdout="feature/example\n",
        ),
        ("git", "rev-parse", "HEAD"): CommandResult(
            0,
            stdout="headsha\n",
        ),
        ("git", "rev-parse", "origin/main"): CommandResult(
            0,
            stdout="basesha\n",
        ),
        (
            "git",
            "rev-list",
            "--left-right",
            "--count",
            "origin/main...HEAD",
        ): CommandResult(
            0,
            stdout="2 3\n",
        ),
        ("git", "status", "--porcelain=v1"): CommandResult(0),
        ("git", "diff", "--check"): CommandResult(0),
        ("git", "diff", "--cached", "--check"): CommandResult(0),
    }
    runner, calls = _runner(responses)

    result = validate_repository(
        tmp_path,
        runner=runner,
    )

    assert result["ok"] is True
    assert result["repository"] == {
        "root": str(tmp_path.resolve()),
        "project": "wilfred-butler",
        "branch": "feature/example",
        "head": "headsha",
        "base_ref": "origin/main",
        "base_sha": "basesha",
        "behind": 2,
        "ahead": 3,
        "working_tree": {
            "clean": True,
            "staged": False,
            "unstaged": False,
            "untracked": False,
        },
    }
    assert any(
        command[:3] == (
            Path(__import__("sys").executable).as_posix(),
            "-m",
            "pytest",
        )
        or command[:3] == (
            __import__("sys").executable,
            "-m",
            "pytest",
        )
        for command, _ in calls
    )


def test_validate_repository_reports_dirty_worktree_and_failed_tests(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "wilfred-butler"\n',
        encoding="utf-8",
    )

    import sys

    responses = {
        ("git", "rev-parse", "--show-toplevel"): CommandResult(
            0,
            stdout=f"{tmp_path}\n",
        ),
        ("git", "branch", "--show-current"): CommandResult(
            0,
            stdout="feature/example\n",
        ),
        ("git", "rev-parse", "HEAD"): CommandResult(0, stdout="head\n"),
        ("git", "rev-parse", "origin/main"): CommandResult(
            0,
            stdout="base\n",
        ),
        (
            "git",
            "rev-list",
            "--left-right",
            "--count",
            "origin/main...HEAD",
        ): CommandResult(0, stdout="0 1\n"),
        ("git", "status", "--porcelain=v1"): CommandResult(
            0,
            stdout="M  staged.py\n M unstaged.py\n?? new.py\n",
        ),
        ("git", "diff", "--check"): CommandResult(0),
        ("git", "diff", "--cached", "--check"): CommandResult(0),
        (
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_runtime.py",
        ): CommandResult(
            1,
            stderr="1 failed",
        ),
    }
    runner, _ = _runner(responses)

    result = validate_repository(
        tmp_path,
        test_targets=("tests/test_runtime.py",),
        runner=runner,
    )

    assert result["ok"] is False
    assert result["repository"]["working_tree"] == {
        "clean": False,
        "staged": True,
        "unstaged": True,
        "untracked": True,
    }
    targeted = next(
        check
        for check in result["checks"]
        if check["name"] == "targeted_tests"
    )
    assert targeted["ok"] is False
    assert targeted["detail"] == "1 failed"


def test_validate_repository_rejects_wrong_project(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "something-else"\n',
        encoding="utf-8",
    )

    responses = {
        ("git", "rev-parse", "--show-toplevel"): CommandResult(
            0,
            stdout=f"{tmp_path}\n",
        ),
        ("git", "branch", "--show-current"): CommandResult(0),
        ("git", "rev-parse", "HEAD"): CommandResult(0),
        ("git", "rev-parse", "origin/main"): CommandResult(1),
        ("git", "status", "--porcelain=v1"): CommandResult(0),
        ("git", "diff", "--check"): CommandResult(0),
        ("git", "diff", "--cached", "--check"): CommandResult(0),
    }
    runner, _ = _runner(responses)

    result = validate_repository(
        tmp_path,
        full_tests=False,
        test_targets=("tests/test_runtime.py",),
        runner=runner,
    )

    assert result["ok"] is False
    project = next(
        check
        for check in result["checks"]
        if check["name"] == "project_identity"
    )
    assert project["ok"] is False
    assert "wilfred-butler" in project["detail"]
