from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ADR = ROOT / "docs" / "adr" / "0001-chatgpt-project-boundary.md"


def test_boundary_adr_is_published() -> None:
    assert ADR.is_file()


def test_readme_presents_standalone_public_boundary() -> None:
    text = README.read_text(encoding="utf-8")
    assert "standalone public product" in text
    assert "private consumer deployment" in text
    assert "Alfred" not in text


def test_boundary_defines_separate_ownership() -> None:
    text = ADR.read_text(encoding="utf-8")

    assert "Alfred and Wilfred use separate AI project contexts" in text
    assert "Conversation history is not a synchronization mechanism" in text
    assert "reviewed, versioned artifacts" in text
    assert "Public components must not import private Alfred modules" in text


def test_public_adr_contains_no_private_runtime_values() -> None:
    text = ADR.read_text(encoding="utf-8").lower()

    forbidden = (
        "/home/server/",
        "keriolhome.online",
        "172.17.",
        "192.168.",
        "token=",
        "password=",
        "secret=",
    )

    assert not any(value in text for value in forbidden)
