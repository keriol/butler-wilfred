from __future__ import annotations

from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
GUIDE = ROOT / "docs" / "development.md"
README = ROOT / "README.md"


def requirement_name(requirement: str) -> str:
    name = requirement

    for separator in (
        "[",
        " ",
        "<",
        ">",
        "=",
        "!",
        "~",
        ";",
    ):
        name = name.split(separator, 1)[0]

    return name


class DevelopmentEnvironmentTests(unittest.TestCase):
    def load_project(self) -> dict:
        with PYPROJECT.open("rb") as stream:
            return tomllib.load(stream)["project"]

    def test_dev_extra_contains_required_tools(self) -> None:
        requirements = self.load_project()[
            "optional-dependencies"
        ]["dev"]

        names = {
            requirement_name(item)
            for item in requirements
        }

        self.assertEqual(
            names,
            {"pytest", "setuptools", "wheel"},
        )

    def test_runtime_dependencies_remain_empty(self) -> None:
        self.assertEqual(
            self.load_project()["dependencies"],
            [],
        )

    def test_commands_are_documented(self) -> None:
        text = GUIDE.read_text(encoding="utf-8")

        self.assertIn(
            "python3.12 -m venv .venv",
            text,
        )
        self.assertIn(
            "pip install -e '.[dev]'",
            text,
        )
        self.assertIn(
            "python -m pytest -q",
            text,
        )

    def test_readme_links_the_guide(self) -> None:
        text = README.read_text(encoding="utf-8")

        self.assertIn(
            "docs/development.md",
            text,
        )


if __name__ == "__main__":
    unittest.main()
