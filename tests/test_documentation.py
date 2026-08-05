from __future__ import annotations

from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class WilfredDocumentationTests(unittest.TestCase):
    def test_readme_tracks_current_public_status(self) -> None:
        readme = (
            PROJECT_ROOT / "README.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "structured Execution Engine",
            readme,
        )
        self.assertIn(
            "docs/execution-engine.md",
            readme,
        )
        self.assertIn(
            "## Current development status",
            readme,
        )
        self.assertIn(
            (
                "The crowdfunding campaign will only "
                "launch after the `0.2.0` release"
            ),
            readme,
        )

    def test_installation_uses_execution_engine(self) -> None:
        installation = (
            PROJECT_ROOT
            / "docs"
            / "installation.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "ExecutionEngine",
            installation,
        )
        self.assertIn(
            "ExecutionRequest",
            installation,
        )
        self.assertIn(
            "Status:  success",
            installation,
        )
        self.assertNotIn(
            "result = registry.execute(",
            installation,
        )

    def test_execution_guide_documents_contract(self) -> None:
        guide = (
            PROJECT_ROOT
            / "docs"
            / "execution-engine.md"
        ).read_text(encoding="utf-8")

        for status in (
            "success",
            "confirmation_required",
            "denied",
            "invalid_arguments",
            "tool_not_found",
            "timeout",
            "error",
        ):
            self.assertIn(status, guide)

        self.assertIn(
            "not a complete JSON Schema implementation",
            guide,
        )
        self.assertIn(
            "cannot forcibly terminate arbitrary Python code",
            guide,
        )
        self.assertIn(
            "The crowdfunding campaign has not launched",
            guide,
        )
        self.assertIn(
            "wilfred.plugins.demo_echo",
            guide,
        )
        self.assertIn(
            'tool_name="demo_echo"',
            guide,
        )
        self.assertNotIn(
            'tool_name="example_tool"',
            guide,
        )


if __name__ == "__main__":
    unittest.main()
