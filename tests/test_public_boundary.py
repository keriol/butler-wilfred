import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ADR = ROOT / "docs" / "adr" / "0001-public-private-development-boundary.md"


def test_boundary_adr_is_published() -> None:
    assert ADR.is_file()


def test_readme_presents_standalone_public_boundary() -> None:
    text = README.read_text(encoding="utf-8")
    assert "standalone public product" in text
    assert "private consumer deployment" in text


def test_boundary_defines_separate_ownership() -> None:
    text = ADR.read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    assert (
        "public Wilfred development context and private consumer contexts "
        "remain separate"
    ) in normalized
    assert "Conversation history is not a synchronization mechanism" in normalized
    assert "reviewed, versioned artifacts" in normalized
    assert "Public components must not import consumer-specific modules" in normalized


def test_public_adr_contains_no_runtime_fingerprints() -> None:
    text = ADR.read_text(encoding="utf-8")

    forbidden_patterns = (
        r"/home/[A-Za-z0-9._-]+/",
        r"\b10\.(?:\d{1,3}\.){2}\d{1,3}\b",
        r"\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b",
        r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b",
        r"(?:token|password|secret)\s*=",
    )

    assert not any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in forbidden_patterns
    )
