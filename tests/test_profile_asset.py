"""Wilfred owns a static, source-attributed profile picture."""

from pathlib import Path
import struct


def test_official_profile_is_a_bounded_png():
    image = Path(__file__).resolve().parents[1] / "assets" / "profile.png"
    data = image.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert 0 < len(data) <= 3 * 1024 * 1024
    assert data[12:16] == b"IHDR"
    width, height = struct.unpack(">II", data[16:24])
    assert 64 <= width <= 512
    assert 64 <= height <= 512
