"""Dependency-free image header reader.

Reads only the first bytes of a file to find its format and pixel size, so it is
fast even for huge photos and works without Pillow. Supported formats:
PNG, JPEG (incl. EXIF orientation), GIF, WebP (VP8/VP8L/VP8X), AVIF/HEIC, BMP,
ICO, SVG.
"""

from __future__ import annotations

import os
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

HEADER_BYTES = 512 * 1024  # enough for JPEGs with large EXIF thumbnails


class ImageProbeError(ValueError):
    """Raised when a file is not a readable image."""


@dataclass(frozen=True)
class ImageInfo:
    """Basic facts about an image file."""

    format: str                      # "png", "jpeg", "webp", "gif", "avif", "bmp", "ico", "svg"
    width: int                       # display width (EXIF rotation applied)
    height: int                      # display height
    file_size: Optional[int] = None  # bytes
    path: Optional[str] = None
    has_alpha: Optional[bool] = None
    animated: Optional[bool] = None
    vector: bool = False
    orientation: int = 1             # EXIF orientation tag (1 = normal)
    extra: dict = field(default_factory=dict, compare=False)

    @property
    def aspect(self) -> float:
        return self.width / self.height if self.height else 0.0

    @property
    def megapixels(self) -> float:
        return self.width * self.height / 1_000_000

    @property
    def orientation_name(self) -> str:
        if abs(self.aspect - 1) < 0.03:
            return "square"
        return "landscape" if self.aspect > 1 else "portrait"


# ----------------------------------------------------------------------
# Format parsers — each takes the header bytes and returns a partial dict
# ----------------------------------------------------------------------
def _png(data: bytes) -> dict:
    if len(data) < 33 or data[12:16] != b"IHDR":
        raise ImageProbeError("Truncated PNG header")
    width, height = struct.unpack(">II", data[16:24])
    color_type = data[25]
    has_alpha = color_type in (4, 6) or b"tRNS" in data[:4096]
    return {"format": "png", "width": width, "height": height, "has_alpha": has_alpha,
            "animated": b"acTL" in data[:4096]}


def _exif_orientation(app1: bytes) -> int:
    if not app1.startswith(b"Exif\x00\x00"):
        return 1
    tiff = app1[6:]
    if len(tiff) < 8:
        return 1
    endian = "<" if tiff[:2] == b"II" else ">"
    try:
        ifd_offset = struct.unpack(endian + "I", tiff[4:8])[0]
        (count,) = struct.unpack(endian + "H", tiff[ifd_offset:ifd_offset + 2])
        for i in range(count):
            entry = tiff[ifd_offset + 2 + i * 12: ifd_offset + 14 + i * 12]
            tag, _type, _count, value = struct.unpack(endian + "HHIH", entry[:10])
            if tag == 0x0112:
                return value if 1 <= value <= 8 else 1
    except struct.error:
        pass
    return 1


def _jpeg(data: bytes) -> dict:
    i, orientation, n = 2, 1, len(data)
    while i + 4 <= n:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7 or marker == 0xFF:
            i += 1 if marker == 0xFF else 2
            continue
        (seg_len,) = struct.unpack(">H", data[i + 2:i + 4])
        if marker == 0xE1:
            orientation = _exif_orientation(data[i + 4:i + 2 + seg_len])
        # SOF0..SOF15 except DHT(C4), JPG(C8), DAC(CC)
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            if i + 9 > n:
                break
            height, width = struct.unpack(">HH", data[i + 5:i + 9])
            if orientation in (5, 6, 7, 8):
                width, height = height, width
            return {"format": "jpeg", "width": width, "height": height, "has_alpha": False,
                    "orientation": orientation, "extra": {"progressive": marker == 0xC2}}
        i += 2 + seg_len
    raise ImageProbeError("JPEG size marker not found (file truncated?)")


def _gif(data: bytes) -> dict:
    width, height = struct.unpack("<HH", data[6:10])
    # More than one image descriptor (0x2C after a graphic control block) => animated.
    animated = data.count(b"\x21\xF9\x04") > 1
    return {"format": "gif", "width": width, "height": height, "animated": animated}


def _webp(data: bytes) -> dict:
    chunk = data[12:16]
    if chunk == b"VP8 ":
        width, height = struct.unpack("<HH", data[26:30])
        return {"format": "webp", "width": width & 0x3FFF, "height": height & 0x3FFF, "has_alpha": False,
                "animated": False}
    if chunk == b"VP8L":
        b = data[21:25]
        width = 1 + (((b[1] & 0x3F) << 8) | b[0])
        height = 1 + (((b[3] & 0x0F) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
        return {"format": "webp", "width": width, "height": height, "has_alpha": bool(b[3] & 0x10),
                "animated": False}
    if chunk == b"VP8X":
        flags = data[20]
        width = 1 + int.from_bytes(data[24:27], "little")
        height = 1 + int.from_bytes(data[27:30], "little")
        return {"format": "webp", "width": width, "height": height, "has_alpha": bool(flags & 0x10),
                "animated": bool(flags & 0x02)}
    raise ImageProbeError(f"Unknown WebP chunk {chunk!r}")


def _isobmff(data: bytes) -> dict:
    """AVIF / HEIC: size lives in the 'ispe' property box."""
    brand = data[8:12].decode("latin-1")
    fmt = "avif" if brand in ("avif", "avis") or b"avif" in data[8:32] else "heic"
    pos = data.find(b"ispe")
    if pos < 0 or pos + 16 > len(data):
        raise ImageProbeError(f"{fmt.upper()} size box not found")
    width, height = struct.unpack(">II", data[pos + 8:pos + 16])
    return {"format": fmt, "width": width, "height": height, "animated": brand == "avis"}


def _bmp(data: bytes) -> dict:
    header_size = struct.unpack("<I", data[14:18])[0]
    if header_size == 12:
        width, height = struct.unpack("<HH", data[18:22])
    else:
        width, height = struct.unpack("<ii", data[18:26])
    return {"format": "bmp", "width": abs(width), "height": abs(height), "has_alpha": False}


def _ico(data: bytes) -> dict:
    count = struct.unpack("<H", data[4:6])[0]
    best = (0, 0)
    for k in range(count):
        entry = data[6 + 16 * k: 22 + 16 * k]
        if len(entry) < 2:
            break
        w, h = entry[0] or 256, entry[1] or 256
        best = max(best, (w, h))
    return {"format": "ico", "width": best[0], "height": best[1], "has_alpha": True,
            "extra": {"sizes": count}}


_LENGTH = re.compile(r"^\s*([\d.]+)\s*(px|pt|mm|cm|in|em)?\s*$")
_UNIT = {None: 1, "px": 1, "pt": 4 / 3, "mm": 96 / 25.4, "cm": 96 / 2.54, "in": 96, "em": 16}


def _svg_len(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    m = _LENGTH.match(value)
    return float(m.group(1)) * _UNIT[m.group(2)] if m else None


def _svg(data: bytes) -> dict:
    text = data[:8192].decode("utf-8", "ignore")
    tag = re.search(r"<svg\b[^>]*>", text, re.S | re.I)
    if not tag:
        raise ImageProbeError("No <svg> element found")
    attrs = dict(re.findall(r'([\w:-]+)\s*=\s*["\']([^"\']*)["\']', tag.group(0)))
    width, height = _svg_len(attrs.get("width")), _svg_len(attrs.get("height"))
    vb = attrs.get("viewBox") or attrs.get("viewbox")
    if vb:
        parts = [float(p) for p in re.split(r"[\s,]+", vb.strip()) if p]
        if len(parts) == 4 and parts[2] > 0 and parts[3] > 0:
            if width and not height:
                height = width * parts[3] / parts[2]
            elif height and not width:
                width = height * parts[2] / parts[3]
            elif not width and not height:
                width, height = parts[2], parts[3]
    return {"format": "svg", "width": round(width or 300), "height": round(height or 150),
            "vector": True, "has_alpha": True}


def probe_bytes(data: bytes) -> dict:
    """Detect format and size from the first bytes of an image."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return _png(data)
    if data.startswith(b"\xff\xd8"):
        return _jpeg(data)
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return _gif(data)
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return _webp(data)
    if data[4:8] == b"ftyp":
        return _isobmff(data)
    if data[:2] == b"BM":
        return _bmp(data)
    if data[:4] == b"\x00\x00\x01\x00":
        return _ico(data)
    head = data[:1024].lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    if head.startswith(b"<?xml") or head.startswith(b"<svg") or b"<svg" in head:
        return _svg(data)
    raise ImageProbeError("Unsupported or unknown image format")


def probe(path: Union[str, os.PathLike]) -> ImageInfo:
    """Read format and pixel size of a local image file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Image not found: {p}")
    with p.open("rb") as fh:
        data = fh.read(HEADER_BYTES)
    try:
        info = probe_bytes(data)
    except (struct.error, IndexError) as exc:
        raise ImageProbeError(f"Corrupt image header in {p.name}: {exc}") from exc
    if not info.get("width") or not info.get("height"):
        raise ImageProbeError(f"Could not read the size of {p.name}")
    return ImageInfo(file_size=p.stat().st_size, path=str(p), **info)


def probe_url(url: str, timeout: float = 10.0) -> ImageInfo:
    """Read format and size of a remote image by downloading only its header."""
    from urllib.request import Request, urlopen

    req = Request(url, headers={"Range": f"bytes=0-{HEADER_BYTES - 1}", "User-Agent": "webcraft-image-probe"})
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 - user supplied image URL
        data = resp.read(HEADER_BYTES)
        total = None
        content_range = resp.headers.get("Content-Range")
        if content_range and "/" in content_range:
            tail = content_range.rsplit("/", 1)[1]
            total = int(tail) if tail.isdigit() else None
        elif resp.headers.get("Content-Length") and resp.status == 200:
            total = int(resp.headers["Content-Length"])
    info = probe_bytes(data)
    return ImageInfo(file_size=total, path=url, **info)
