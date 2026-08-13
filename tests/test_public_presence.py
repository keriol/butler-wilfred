from __future__ import annotations

from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]


EXPECTED_IMAGES = {
    "linkedin-logo.png":
        (400, 400),
    "linkedin-cover.png":
        (4200, 700),
    "facebook-profile.png":
        (320, 320),
    "facebook-cover.png":
        (851, 315),
}


def png_dimensions(
    path: Path,
) -> tuple[int, int]:
    data = path.read_bytes()

    assert data.startswith(
        b"\x89PNG\r\n\x1a\n"
    )

    assert data[12:16] == b"IHDR"

    return struct.unpack(
        ">II",
        data[16:24],
    )


def test_public_presence_copy_exists() -> None:
    document = (
        ROOT / "docs" / "public-presence.md"
    ).read_text(
        encoding="utf-8"
    )

    assert "## LinkedIn" in document
    assert "## Facebook" in document
    assert "## Launch content" in document
    assert "## Crowdfunding boundary" in document

    assert (
        "https://github.com/keriol/butler-wilfred"
        in document
    )

    assert (
        "https://github.com/keriol/"
        "wilfred-home-assistant"
        in document
    )


def test_release_post_is_explicitly_gated() -> None:
    document = (
        ROOT / "docs" / "public-presence.md"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "must not be published with"
        in document
    )

    assert (
        "after the 0.2.0 release"
        in document
    )


def test_social_assets_are_valid_pngs() -> None:
    directory = (
        ROOT / "assets" / "social"
    )

    for name, expected in (
        EXPECTED_IMAGES.items()
    ):
        path = directory / name

        assert path.is_file()
        assert png_dimensions(path) == expected
        assert path.stat().st_size > 100


def test_asset_generator_is_public_stdlib() -> None:
    source = (
        ROOT
        / "scripts"
        / "generate_social_assets.py"
    ).read_text(
        encoding="utf-8"
    )

    assert "import zlib" in source
    assert "from PIL" not in source
    assert "cairosvg" not in source
