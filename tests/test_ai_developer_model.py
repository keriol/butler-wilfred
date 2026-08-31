from __future__ import annotations

from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL = PROJECT_ROOT / "docs" / "ai-developer-model.md"
README = PROJECT_ROOT / "README.md"


class PublicAIDeveloperModelTests(unittest.TestCase):
    def test_model_exists_and_describes_current_public_baseline(self) -> None:
        text = MODEL.read_text(encoding="utf-8")

        for term in (
            "Wilfred `0.2.2`",
            "Butler Core `0.2.0`",
            "GitHub Issues",
            "deterministic request resolution",
            "optional planner fallback",
            "Execution Engine",
            "WilfredRuntime",
            "READ → ACTION → READ → VERIFY",
            "official public Home Assistant plugin",
            "version-specific release BOM",
        ):
            self.assertIn(term, text)

    def test_model_does_not_contain_non_public_operational_context(self) -> None:
        text = MODEL.read_text(encoding="utf-8").lower()

        forbidden = (
            "alfred",
            "umberto",
            "/home/server",
            ".venvs/",
            "keriol-python",
            "keriol-test",
            "release candidate:",
            "current priorities",
            "task ledger",
        )

        for term in forbidden:
            self.assertNotIn(term.lower(), text)

    def test_model_does_not_claim_planned_features_as_current(self) -> None:
        text = MODEL.read_text(encoding="utf-8").lower()

        for term in (
            "background workers are available",
            "generic multi-tool planning chains are available",
            "scheduler is available",
            "retry infrastructure is available",
        ):
            self.assertNotIn(term, text)

    def test_readme_links_public_ai_model(self) -> None:
        readme = README.read_text(encoding="utf-8")

        self.assertIn("## AI developer model", readme)
        self.assertIn("public AI model for developers", readme)
        self.assertIn("docs/ai-developer-model.md", readme)
        self.assertIn("GitHub Issues", readme)


if __name__ == "__main__":
    unittest.main()
