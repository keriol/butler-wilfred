from pathlib import Path


WORKFLOW = Path(".github/workflows/release.yml")


def test_release_workflow_exists() -> None:
    assert WORKFLOW.is_file()


def test_release_workflow_guards_release_contract() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    required = [
        'tags:',
        '"v*.*.*"',
        "contents: write",
        'test "$PACKAGE_VERSION" = "$VERSION"',
        "git merge-base --is-ancestor HEAD origin/main",
        "pytest -q",
        "python -m build",
        "python -m pip check",
        "wilfred status",
        "wilfred tools",
        "gh release create",
        "dist/*.whl",
        "dist/*.tar.gz",
    ]

    for marker in required:
        assert marker in text


def test_release_workflow_requires_versioned_public_notes() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    required = [
        'RELEASE_NOTES="docs/releases/${VERSION}.md"',
        'test -s "$RELEASE_NOTES"',
        'grep -Fq "# Wilfred $VERSION" "$RELEASE_NOTES"',
        'echo "RELEASE_NOTES=$RELEASE_NOTES" >> "$GITHUB_ENV"',
        '--notes-file "$RELEASE_NOTES"',
    ]

    for marker in required:
        assert marker in text

    assert "--generate-notes" not in text


def test_release_workflow_has_no_fixed_release_version() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "0.1.7.dev0" not in text
    assert 'RELEASE_VERSION="0.' not in text
