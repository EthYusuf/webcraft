"""Optional image optimisation (requires Pillow: ``pip install webcraft[images]``).

For each image this module:
  1. applies EXIF rotation to the pixels,
  2. crops to the slot's aspect ratio around a focus point (only for cropping slots),
  3. writes responsive WebP variants (e.g. 640w, 1280w, 1920w) never larger than needed,
  4. returns a ``srcset`` string so browsers download the right size.
Results are cached by content hash, so rebuilding is fast.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from .analyze import crop_to_aspect, recommended_size
from .specs import ImageSlot, get_slot

STANDARD_WIDTHS = (320, 480, 640, 800, 960, 1280, 1600, 1920, 2560)
SKIP_FORMATS = {"SVG", "ICO"}


class PillowMissing(RuntimeError):
    pass


def has_pillow() -> bool:
    try:
        import PIL  # noqa: F401
    except ImportError:
        return False
    return True


@dataclass
class OptimizedImage:
    src: str                 # relative path of the largest variant
    srcset: str              # "a-640.webp 640w, a-1280.webp 1280w"
    width: int
    height: int
    files: list[Path]
    original_bytes: int
    optimized_bytes: int

    @property
    def saved_pct(self) -> int:
        if not self.original_bytes:
            return 0
        return max(0, min(99, round(100 * (1 - self.optimized_bytes / self.original_bytes))))


def _widths_for(target_w: int, available_w: int, slot: ImageSlot) -> list[int]:
    top = min(target_w, available_w)
    smallest = 320 if (slot.display_width or 0) >= 300 else 64
    widths = [w for w in STANDARD_WIDTHS if smallest <= w < top * 0.9]
    return widths + [top]


def optimize_image(path: Union[str, os.PathLike], slot: Union[str, ImageSlot], out_dir: Union[str, os.PathLike], *,
                   rel_prefix: str = "", focus: Union[str, tuple, None] = "center", quality: int = 80,
                   display_width: Optional[int] = None, fmt: str = "webp") -> Optional[OptimizedImage]:
    """Create responsive, compressed variants of ``path`` for ``slot`` inside ``out_dir``.

    Returns ``None`` for formats that should be copied as-is (SVG, ICO, animated GIF/WebP)."""
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise PillowMissing("Image optimisation needs Pillow:  pip install pillow") from exc

    slot = get_slot(slot) if isinstance(slot, str) else slot
    source = Path(path)
    out_dir = Path(out_dir)
    raw = source.read_bytes()

    with Image.open(source) as img:
        if img.format in SKIP_FORMATS or getattr(img, "is_animated", False):
            return None
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "A" in img.getbands() or "transparency" in img.info else "RGB")

        if slot.crops and slot.aspect_value:
            crop = crop_to_aspect(img.width, img.height, slot.aspect_value, focus)
            if crop.removed_pct > 0.5:
                img = img.crop(crop.box)

        rec_w, _ = recommended_size(slot, display_width)
        if rec_w is None:  # height-driven slot (logo)
            rec_h = slot.recommended[1] or img.height
            rec_w = round(img.width * min(1.0, rec_h / img.height))
        widths = _widths_for(rec_w, img.width, slot)

        key = hashlib.sha1(raw + repr((slot.key, focus, quality, display_width, fmt)).encode()).hexdigest()[:10]
        out_dir.mkdir(parents=True, exist_ok=True)
        files, entries, total = [], [], 0
        for w in widths:
            h = round(img.height * w / img.width)
            name = f"{source.stem}-{key}-{w}.{fmt}"
            target = out_dir / name
            if not target.exists():
                variant = img if w == img.width else img.resize((w, h), Image.LANCZOS)
                if fmt == "webp":
                    variant.save(target, "WEBP", quality=quality, method=6)
                elif fmt == "avif":
                    variant.save(target, "AVIF", quality=quality)
                else:
                    variant.convert("RGB").save(target, "JPEG", quality=quality, optimize=True, progressive=True)
            files.append(target)
            total = target.stat().st_size  # size of the largest (last) variant is what desktop users load
            entries.append(f"{rel_prefix}{name} {w}w")
        final_w = widths[-1]
        final_h = round(img.height * final_w / img.width)

    return OptimizedImage(src=f"{rel_prefix}{files[-1].name}", srcset=", ".join(entries), width=final_w,
                          height=final_h, files=files, original_bytes=len(raw), optimized_bytes=total)
