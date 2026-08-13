from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
import zlib


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "social"

BACKGROUND = (10, 18, 32)
SURFACE = (20, 32, 51)
ACCENT = (94, 234, 212)
FOREGROUND = (242, 246, 250)
MUTED = (148, 163, 184)


@dataclass
class Canvas:
    width: int
    height: int

    def __post_init__(self) -> None:
        self.pixels = bytearray(
            self.width * self.height * 3
        )

        self.fill(BACKGROUND)

    def fill(
        self,
        color: tuple[int, int, int],
    ) -> None:
        row = bytes(color) * self.width

        for y in range(self.height):
            start = y * self.width * 3
            self.pixels[
                start:start + self.width * 3
            ] = row

    def pixel(
        self,
        x: int,
        y: int,
        color: tuple[int, int, int],
    ) -> None:
        if not (
            0 <= x < self.width
            and 0 <= y < self.height
        ):
            return

        offset = (
            y * self.width + x
        ) * 3

        self.pixels[
            offset:offset + 3
        ] = bytes(color)

    def circle(
        self,
        cx: int,
        cy: int,
        radius: int,
        color: tuple[int, int, int],
    ) -> None:
        rr = radius * radius

        for y in range(
            max(0, cy - radius),
            min(self.height, cy + radius + 1),
        ):
            dy = y - cy

            for x in range(
                max(0, cx - radius),
                min(self.width, cx + radius + 1),
            ):
                dx = x - cx

                if dx * dx + dy * dy <= rr:
                    self.pixel(
                        x,
                        y,
                        color,
                    )

    def line(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        width: int,
        color: tuple[int, int, int],
    ) -> None:
        dx = x1 - x0
        dy = y1 - y0
        steps = max(
            abs(dx),
            abs(dy),
            1,
        )

        radius = max(1, width // 2)

        for step in range(steps + 1):
            x = round(
                x0 + dx * step / steps
            )
            y = round(
                y0 + dy * step / steps
            )

            self.circle(
                x,
                y,
                radius,
                color,
            )

    def rectangle(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: tuple[int, int, int],
    ) -> None:
        for y in range(
            max(0, y0),
            min(self.height, y1),
        ):
            for x in range(
                max(0, x0),
                min(self.width, x1),
            ):
                self.pixel(
                    x,
                    y,
                    color,
                )

    def write_png(
        self,
        path: Path,
    ) -> None:
        raw = bytearray()

        stride = self.width * 3

        for y in range(self.height):
            raw.append(0)

            start = y * stride

            raw.extend(
                self.pixels[
                    start:start + stride
                ]
            )

        def chunk(
            kind: bytes,
            data: bytes,
        ) -> bytes:
            body = kind + data

            return (
                struct.pack(
                    ">I",
                    len(data),
                )
                + body
                + struct.pack(
                    ">I",
                    zlib.crc32(body)
                    & 0xFFFFFFFF,
                )
            )

        png = bytearray(
            b"\x89PNG\r\n\x1a\n"
        )

        png.extend(
            chunk(
                b"IHDR",
                struct.pack(
                    ">IIBBBBB",
                    self.width,
                    self.height,
                    8,
                    2,
                    0,
                    0,
                    0,
                ),
            )
        )

        png.extend(
            chunk(
                b"IDAT",
                zlib.compress(
                    bytes(raw),
                    level=9,
                ),
            )
        )

        png.extend(
            chunk(
                b"IEND",
                b"",
            )
        )

        path.write_bytes(png)


FONT = {
    "W": (
        "10001",
        "10001",
        "10001",
        "10101",
        "10101",
        "11111",
        "01010",
    ),
    "I": (
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "11111",
    ),
    "L": (
        "10000",
        "10000",
        "10000",
        "10000",
        "10000",
        "10000",
        "11111",
    ),
    "F": (
        "11111",
        "10000",
        "10000",
        "11110",
        "10000",
        "10000",
        "10000",
    ),
    "R": (
        "11110",
        "10001",
        "10001",
        "11110",
        "10100",
        "10010",
        "10001",
    ),
    "E": (
        "11111",
        "10000",
        "10000",
        "11110",
        "10000",
        "10000",
        "11111",
    ),
    "D": (
        "11110",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "11110",
    ),
}


def text(
    canvas: Canvas,
    value: str,
    *,
    x: int,
    y: int,
    scale: int,
    color: tuple[int, int, int],
) -> None:
    cursor = x

    for char in value:
        glyph = FONT[char]

        for gy, row in enumerate(glyph):
            for gx, cell in enumerate(row):
                if cell != "1":
                    continue

                canvas.rectangle(
                    cursor + gx * scale,
                    y + gy * scale,
                    cursor + (gx + 1) * scale,
                    y + (gy + 1) * scale,
                    color,
                )

        cursor += 6 * scale


def mark(
    canvas: Canvas,
    *,
    cx: int,
    cy: int,
    size: int,
) -> None:
    half = size // 2

    points = (
        (
            cx - half,
            cy - half // 2,
        ),
        (
            cx - half // 2,
            cy + half,
        ),
        (
            cx,
            cy,
        ),
        (
            cx + half // 2,
            cy + half,
        ),
        (
            cx + half,
            cy - half // 2,
        ),
    )

    width = max(
        4,
        size // 14,
    )

    for left, right in zip(
        points,
        points[1:],
    ):
        canvas.line(
            *left,
            *right,
            width,
            ACCENT,
        )

    radius = max(
        5,
        size // 11,
    )

    for point in points:
        canvas.circle(
            *point,
            radius,
            FOREGROUND,
        )


def avatar(
    width: int,
    height: int,
) -> Canvas:
    canvas = Canvas(
        width,
        height,
    )

    size = min(
        width,
        height,
    )

    canvas.circle(
        width // 2,
        height // 2,
        int(size * 0.40),
        SURFACE,
    )

    mark(
        canvas,
        cx=width // 2,
        cy=height // 2,
        size=int(size * 0.48),
    )

    return canvas


def cover(
    width: int,
    height: int,
) -> Canvas:
    canvas = Canvas(
        width,
        height,
    )

    margin = int(
        height * 0.18
    )

    canvas.rectangle(
        0,
        0,
        width,
        height,
        BACKGROUND,
    )

    mark_size = int(
        height * 0.50
    )

    mark(
        canvas,
        cx=int(width * 0.36),
        cy=height // 2,
        size=mark_size,
    )

    scale = max(
        4,
        int(height * 0.055),
    )

    word_width = (
        len("WILFRED")
        * 6
        * scale
    )

    text(
        canvas,
        "WILFRED",
        x=min(
            width - word_width - margin,
            int(width * 0.47),
        ),
        y=(
            height
            - 7 * scale
        ) // 2,
        scale=scale,
        color=FOREGROUND,
    )

    return canvas


def main() -> int:
    OUTPUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    specifications = {
        "facebook-profile.png":
            avatar(320, 320),
        "facebook-cover.png":
            cover(851, 315),
    }

    for name, canvas in specifications.items():
        path = OUTPUT / name

        canvas.write_png(path)

        print(
            f"{name}: "
            f"{canvas.width}x{canvas.height}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
