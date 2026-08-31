from __future__ import annotations

from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class WilfredDocumentationTests(unittest.TestCase):
    def test_readme_tracks_current_public_status(self) -> None:
        readme = (
            PROJECT_ROOT / "README.md"
        ).read_text(encoding="utf-8")

        for term in (
            "Build your Butler, one capability at a time.",
            "## Capabilities know their domain",
            "### ✅ Available",
            "### 🧪 In testing",
            "### 🧭 Designed to enable",
            "In testing is not a release promise.",
            "## Current Public Alpha",
        ):
            self.assertIn(term, readme)
        self.assertIn(
            "docs/execution-engine.md",
            readme,
        )
        self.assertNotIn(
            "## What Wilfred 0.2.0 is today",
            readme,
        )
        self.assertNotIn(
            "## Current development status",
            readme,
        )
        self.assertNotIn(
            "## Docker Public Alpha",
            readme,
        )

        h2_headings = [
            line
            for line in readme.splitlines()
            if line.startswith("## ")
        ]
        self.assertEqual(
            len(h2_headings),
            len(set(h2_headings)),
        )
        self.assertIn(
            "Wilfred `0.2.2` is the current Public Alpha",
            readme,
        )
        self.assertIn(
            "support Wilfred on Ko-fi",
            readme,
        )
        self.assertNotIn(
            "crowdfunding campaign will only launch",
            readme.lower(),
        )
        self.assertIn(
            "docs/http-api.md",
            readme,
        )

    def test_public_onboarding_documents_first_session(self) -> None:
        guide = (
            PROJECT_ROOT
            / "docs"
            / "onboarding.md"
        ).read_text(encoding="utf-8")

        readme = (
            PROJECT_ROOT
            / "README.md"
        ).read_text(encoding="utf-8")

        for term in (
            "wilfred status",
            "wilfred tools",
            "wilfred goal",
            "wilfred api",
            "demo.echo",
            "WILFRED_OPENAI_API_KEY",
            "127.0.0.1:8000",
            "0.2.2",
            "Home Assistant Plugin",
        ):
            self.assertIn(term, guide)

        self.assertIn(
            "does not provide authentication",
            " ".join(guide.split()),
        )

        self.assertIn(
            "docs/onboarding.md",
            readme,
        )

    def test_http_api_guide_documents_security_contract(self) -> None:
        guide = (
            PROJECT_ROOT
            / "docs"
            / "http-api.md"
        ).read_text(encoding="utf-8")

        normalized = " ".join(guide.split())

        for endpoint in (
            "GET /health",
            "GET /v1/runtime",
            "GET /v1/tools",
            "POST /v1/goals",
        ):
            self.assertIn(endpoint, guide)

        self.assertIn(
            "127.0.0.1",
            guide,
        )
        self.assertIn(
            "CORS is not enabled",
            normalized,
        )
        self.assertIn(
            "does not include authentication",
            normalized,
        )
        self.assertIn(
            "confirmed",
            guide,
        )
        self.assertIn(
            "confirmation_required",
            guide,
        )
        self.assertNotIn(
            "allow_origins=[\"*\"]",
            guide,
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
        normalized = " ".join(guide.split())

        self.assertIn(
            "Wilfred `0.2.2` Public Alpha",
            normalized,
        )
        self.assertIn(
            "official Home Assistant plugin",
            normalized,
        )
        self.assertIn(
            "Public Alpha hardening",
            normalized,
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

    def test_verified_workflow_guide_documents_contract(self) -> None:
        guide = (
            PROJECT_ROOT
            / "docs"
            / "verified-workflows.md"
        ).read_text(encoding="utf-8")

        normalized = " ".join(guide.split())

        for status in (
            "verified",
            "failed",
            "indeterminate",
        ):
            self.assertIn(status, guide)

        self.assertIn(
            "It does not prove that the requested external "
            "or physical state was reached.",
            normalized,
        )
        self.assertIn(
            "Automatic ACTION retries are deliberately outside",
            normalized,
        )

    def test_persistence_guide_documents_contract(self) -> None:
        guide = (
            PROJECT_ROOT
            / "docs"
            / "persistence.md"
        ).read_text(encoding="utf-8")

        normalized = " ".join(guide.split())

        for term in (
            "WorkflowStore",
            "SQLiteWorkflowStore",
            "WorkflowRecord",
            "WorkflowPersistenceError",
        ):
            self.assertIn(term, guide)

        self.assertIn(
            "Persistence is deliberately separate from workflow execution.",
            normalized,
        )
        self.assertIn(
            "does not silently overwrite workflow history",
            normalized,
        )
        self.assertIn(
            "does not persist automatically",
            normalized,
        )


if __name__ == "__main__":
    unittest.main()
