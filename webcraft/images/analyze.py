"""Image quality analysis against a placement slot, plus placement suggestions."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional, Union

from .probe import ImageInfo, probe, probe_url
from .specs import SLOTS, ImageSlot, get_slot, ratio_text, size_text

ERROR, WARNING, INFO = "error", "warning", "info"
_ICON = {ERROR: "✗", WARNING: "⚠", INFO: "ℹ"}
_PENALTY = {ERROR: 35, WARNING: 12, INFO: 3}

WEB_FORMATS = {"jpeg", "png", "webp", "avif", "gif", "svg", "ico"}

# Message templates: code -> (tr, en). Formatted with str.format(**values).
MESSAGES = {
    "too_small": (
        "Çok küçük: {size}. Bu alan en az {min} ister; büyük ekranlarda bulanık görünecek.",
        "Too small: {size}. This slot needs at least {min}; it will look blurry on large screens."),
    "too_small_fix": ("En az {min} boyutunda bir görsel kullanın (ideal: {rec}).",
                      "Use an image of at least {min} (ideal: {rec})."),
    "below_rec": (
        "Önerilenin altında: {size} (önerilen {rec}, %{pct}). Retina ekranlarda hafif yumuşak görünebilir.",
        "Below recommended: {size} (recommended {rec}, {pct}%). May look slightly soft on retina screens."),
    "below_rec_fix": ("Mümkünse {rec} çözünürlükte bir sürüm kullanın.", "Use a {rec} version if available."),
    "oversized": (
        "Gereğinden büyük: {size}. {rec} yeterli; küçültmek pikselleri ~%{save} azaltır.",
        "Larger than needed: {size}. {rec} is enough; resizing removes ~{save}% of the pixels."),
    "oversized_fix": ("{rec} boyutuna küçültün veya optimize_images=True ile derleyin.",
                      "Resize to {rec} or build with optimize_images=True."),
    "aspect_crop": (
        "Oran {ratio} ({actual:.2f}), alan {target} ({expected:.2f}) istiyor: {side} toplam {px} px (%{pct}) kırpılacak.",
        "Ratio {ratio} ({actual:.2f}) but the slot wants {target} ({expected:.2f}): {px} px ({pct}%) will be cropped from the {side}."),
    "aspect_crop_fix": (
        "Önceden {crop} olarak kırpın ki ne kesileceğini siz seçin (veya focus='top' gibi odak verin).",
        "Pre-crop to {crop} so you choose what gets cut (or set a focus such as focus='top')."),
    "aspect_layout": (
        "Oran {ratio} ({actual:.2f}); bu alan için {target} önerilir. Kırpılmaz ama sayfa düzeni dengesiz görünebilir.",
        "Ratio {ratio} ({actual:.2f}); {target} is recommended here. Not cropped, but the layout may look unbalanced."),
    "aspect_layout_fix": ("{crop} olarak kırpmayı veya aspect='{target}' fit='cover' kullanmayı düşünün.",
                          "Consider cropping to {crop} or using aspect='{target}' fit='cover'."),
    "wrong_orientation": (
        "{orient} görsel yatay bir alana konuyor; büyük kısmı kırpılacak.",
        "{orient} image used in a landscape slot; most of it will be cropped."),
    "wrong_orientation_fix": (
        "Yatay bir görsel seçin; bu görseli mobile_image olarak kullanabilirsiniz.",
        "Pick a landscape image; this one could serve as mobile_image."),
    "heavy": ("Dosya ağır: {kb} KB (bu alan için hedef ≤ {max} KB). Sayfa yavaş açılır.",
              "Heavy file: {kb} KB (target ≤ {max} KB for this slot). Slows down the page."),
    "heavy_fix": ("WebP/AVIF'e çevirin (kalite 75-82) veya optimize_images=True ile derleyin.",
                  "Convert to WebP/AVIF (quality 75-82) or build with optimize_images=True."),
    "bad_format": ("{fmt} formatı web için uygun değil; tarayıcıların çoğu göstermez veya çok büyüktür.",
                   "{fmt} is not a web format; most browsers won't show it or it is huge."),
    "bad_format_fix": ("WebP, AVIF veya JPEG'e dönüştürün.", "Convert to WebP, AVIF or JPEG."),
    "png_photo": ("Şeffaflığı olmayan PNG fotoğraf: WebP/JPEG'e çevirmek dosyayı genellikle %60-80 küçültür.",
                  "Opaque PNG photo: converting to WebP/JPEG usually saves 60-80%."),
    "png_photo_fix": ("WebP (kalite 80) veya JPEG (kalite 82) kullanın.", "Use WebP (quality 80) or JPEG (quality 82)."),
    "animated_gif": ("Animasyonlu GIF ({kb} KB): aynı animasyon MP4/WebM veya animasyonlu WebP olarak ~%80 küçük olur.",
                     "Animated GIF ({kb} KB): the same animation as MP4/WebM or animated WebP is ~80% smaller."),
    "animated_gif_fix": ("site.video(...) ile MP4 kullanın veya animasyonlu WebP'ye çevirin.",
                         "Use site.video(...) with an MP4 or convert to animated WebP."),
    "prefer_svg": ("Logo/ikon için SVG her ekranda keskin kalır ve çok küçüktür.",
                   "For logos/icons SVG stays sharp on every screen and is tiny."),
    "prefer_svg_fix": ("Logonun SVG sürümünü kullanın.", "Use an SVG version of the logo."),
    "logo_alpha": ("Logoda şeffaflık yok; renkli/koyu arka planlarda kutu gibi görünür.",
                   "Logo has no transparency; it will look like a box on coloured/dark backgrounds."),
    "logo_alpha_fix": ("Arka planı şeffaf PNG/WebP veya SVG kullanın.", "Use a transparent PNG/WebP or an SVG."),
    "exif_rotated": ("Fotoğraf EXIF ile döndürülmüş (yön={o}); bazı araçlarda yan görünebilir.",
                     "Photo is rotated via EXIF (orientation={o}); some tools may show it sideways."),
    "exif_rotated_fix": ("optimize_images=True pikselleri gerçekten döndürür.", "optimize_images=True rotates the pixels for real."),
    "not_square": ("Kare değil ({size}); kare olarak gösterilecek.", "Not square ({size}); it will be shown as a square."),
    "not_square_fix": ("{crop} olarak kare kırpın.", "Crop to a {crop} square."),
    "vector_ok": ("Vektör (SVG): her boyutta keskin.", "Vector (SVG): sharp at any size."),
    "remote_skipped": ("Uzak görsel analiz edilmedi (check_remote=True ile edilir).",
                       "Remote image not analysed (enable with check_remote=True)."),
}

_SIDES = {"tr": {"x": "sağ/sol kenarlardan", "y": "üst/alt kenarlardan"},
          "en": {"x": "left/right edges", "y": "top/bottom edges"}}
_ORIENT = {"tr": {"portrait": "Dikey", "square": "Kare", "landscape": "Yatay"},
           "en": {"portrait": "Portrait", "square": "Square", "landscape": "Landscape"}}


def _msg(code: str, lang: str, **values) -> str:
    tr, en = MESSAGES[code]
    return (tr if lang == "tr" else en).format(**values)


@dataclass
class Issue:
    level: str
    code: str
    message: str
    fix: str = ""

    def __str__(self) -> str:
        return f"{_ICON[self.level]} {self.message}" + (f"\n      → {self.fix}" if self.fix else "")


@dataclass
class CropSuggestion:
    width: int
    height: int
    left: int
    top: int
    removed_pct: float

    @property
    def box(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.left + self.width, self.top + self.height)

    def __str__(self) -> str:
        return f"{self.width}×{self.height} px"


@dataclass
class ImageReport:
    """Result of :func:`analyze_image`."""

    slot: ImageSlot
    info: ImageInfo
    issues: list[Issue] = field(default_factory=list)
    recommended: tuple[Optional[int], Optional[int]] = (None, None)
    crop: Optional[CropSuggestion] = None
    lang: str = "tr"
    source: Optional[str] = None
    resolved: list[Issue] = field(default_factory=list)   # issues fixed by optimize_images

    @property
    def score(self) -> int:
        return max(0, 100 - sum(_PENALTY[i.level] for i in self.issues))

    @property
    def ok(self) -> bool:
        return not any(i.level == ERROR for i in self.issues)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == ERROR]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.level == WARNING]

    @property
    def grade(self) -> str:
        s = self.score
        return "A" if s >= 90 else "B" if s >= 75 else "C" if s >= 55 else "D" if s >= 35 else "F"

    def to_dict(self) -> dict:
        return {
            "source": self.source or self.info.path, "slot": self.slot.key,
            "format": self.info.format, "width": self.info.width, "height": self.info.height,
            "file_size": self.info.file_size, "score": self.score, "grade": self.grade,
            "recommended": list(self.recommended),
            "crop": {"width": self.crop.width, "height": self.crop.height, "box": list(self.crop.box)} if self.crop else None,
            "issues": [{"level": i.level, "code": i.code, "message": i.message, "fix": i.fix} for i in self.issues],
            "resolved": [i.code for i in self.resolved],
        }

    def summary(self) -> str:
        name = os.path.basename(self.source or self.info.path or "?")
        kb = f" · {self.info.file_size / 1024:.0f} KB" if self.info.file_size else ""
        return (f"{name}  →  {self.slot.label(self.lang)}  ·  {self.info.width}×{self.info.height}"
                f"{kb}  ·  {self.grade} ({self.score}/100)")

    def __str__(self) -> str:
        tr = self.lang == "tr"
        lines = [self.summary()]
        lines.append(f"   {'Önerilen' if tr else 'Recommended'}: {size_text(self.recommended)}  ·  "
                     f"{'oran' if tr else 'ratio'} {ratio_text(self.slot.aspect)}  ·  ≤ {self.slot.max_kb} KB")
        if not self.issues:
            lines.append("   ✓ " + ("Bu alan için ideal." if tr else "Ideal for this slot."))
        lines += [f"   {issue}" for issue in self.issues]
        for issue in self.resolved:
            lines.append(f"   ✓ {'Optimizasyonla düzeltildi' if tr else 'Fixed by optimisation'}: {issue.message}")
        return "\n".join(lines)


# ----------------------------------------------------------------------
# Geometry helpers
# ----------------------------------------------------------------------
def _gcd_ratio(w: int, h: int) -> str:
    from math import gcd

    g = gcd(w, h) or 1
    a, b = w // g, h // g
    if a > 50 or b > 50:  # not a "nice" ratio — show the decimal form
        return f"{w / h:.2f}:1"
    return f"{a}:{b}"


def _focus_fraction(focus: Union[str, tuple, None]) -> tuple[float, float]:
    """'center', 'top', 'bottom left', (30, 70) in percent -> (fx, fy) in 0..1."""
    if isinstance(focus, (tuple, list)) and len(focus) == 2:
        return max(0.0, min(1.0, focus[0] / 100)), max(0.0, min(1.0, focus[1] / 100))
    fx = fy = 0.5
    for word in str(focus or "center").lower().split():
        if word in ("left", "sol"):
            fx = 0.0
        elif word in ("right", "sag", "sağ"):
            fx = 1.0
        elif word in ("top", "ust", "üst"):
            fy = 0.0
        elif word in ("bottom", "alt"):
            fy = 1.0
    return fx, fy


def crop_to_aspect(width: int, height: int, aspect: float,
                   focus: Union[str, tuple, None] = "center") -> CropSuggestion:
    """Largest box with ``aspect`` inside ``width×height``, positioned by ``focus``."""
    fx, fy = _focus_fraction(focus)
    if width / height > aspect:
        cw, ch = round(height * aspect), height
    else:
        cw, ch = width, round(width / aspect)
    left, top = round((width - cw) * fx), round((height - ch) * fy)
    removed = 100 * (1 - (cw * ch) / (width * height))
    return CropSuggestion(cw, ch, left, top, round(removed, 1))


def recommended_size(slot: ImageSlot, display_width: Optional[int] = None) -> tuple[Optional[int], Optional[int]]:
    """Slot recommendation, adapted to an explicit display width (2× for retina)."""
    if display_width and slot.aspect_value:
        w = 2 * int(display_width)
        return w, round(w / slot.aspect_value)
    return slot.recommended


# ----------------------------------------------------------------------
# Analysis
# ----------------------------------------------------------------------
def analyze_info(info: ImageInfo, slot: Union[str, ImageSlot], *, lang: str = "tr",
                 display_width: Optional[int] = None, focus: Union[str, tuple, None] = "center",
                 cropped: Optional[bool] = None, source: Optional[str] = None) -> ImageReport:
    """Analyse already-probed image facts against a slot."""
    slot = get_slot(slot) if isinstance(slot, str) else slot
    rec = recommended_size(slot, display_width)
    min_w, min_h = slot.minimum
    if display_width and slot.aspect_value and rec[0]:
        min_w = min(min_w or rec[0], max(int(display_width * 1.25), 1))
        min_h = round(min_w / slot.aspect_value)
    report = ImageReport(slot=slot, info=info, recommended=rec, lang=lang, source=source)
    add = report.issues.append
    W, H = info.width, info.height
    size = f"{W}×{H} px"
    will_crop = slot.crops if cropped is None else cropped

    # --- format -------------------------------------------------------
    if info.format not in WEB_FORMATS:
        add(Issue(ERROR, "bad_format", _msg("bad_format", lang, fmt=info.format.upper()), _msg("bad_format_fix", lang)))

    if info.vector:
        add(Issue(INFO, "vector_ok", _msg("vector_ok", lang)))
    else:
        # --- orientation & aspect ---------------------------------------
        target = slot.aspect_value
        eff_w, eff_h = W, H
        if target:
            deviation = abs(info.aspect - target) / target
            crop = crop_to_aspect(W, H, target, focus)
            if slot.landscape_only and info.aspect < 1:
                add(Issue(WARNING, "wrong_orientation",
                          _msg("wrong_orientation", lang, orient=_ORIENT[lang if lang in _ORIENT else "en"][info.orientation_name]),
                          _msg("wrong_orientation_fix", lang)))
            if deviation > slot.aspect_tolerance:
                report.crop = crop
                if slot.aspect == (1, 1):
                    add(Issue(WARNING if will_crop else INFO, "not_square", _msg("not_square", lang, size=size),
                              _msg("not_square_fix", lang, crop=str(crop))))
                elif will_crop:
                    side = "x" if info.aspect > target else "y"
                    px = (W - crop.width) if side == "x" else (H - crop.height)
                    add(Issue(WARNING if deviation > 0.15 else INFO, "aspect_crop",
                              _msg("aspect_crop", lang, ratio=_gcd_ratio(W, H), actual=info.aspect,
                                   target=ratio_text(slot.aspect), expected=target,
                                   side=_SIDES.get(lang, _SIDES["en"])[side], px=px, pct=round(crop.removed_pct)),
                              _msg("aspect_crop_fix", lang, crop=str(crop))))
                else:
                    add(Issue(INFO, "aspect_layout",
                              _msg("aspect_layout", lang, ratio=_gcd_ratio(W, H), actual=info.aspect,
                                   target=ratio_text(slot.aspect)),
                              _msg("aspect_layout_fix", lang, crop=str(crop), target=ratio_text(slot.aspect))))
            if will_crop:
                eff_w, eff_h = crop.width, crop.height

        # --- resolution -------------------------------------------------
        rec_w, rec_h = rec
        if slot.aspect is None:  # height-driven (logo)
            if min_h and eff_h < min_h:
                add(Issue(ERROR, "too_small", _msg("too_small", lang, size=size, min=size_text((None, min_h))),
                          _msg("too_small_fix", lang, min=size_text((None, min_h)), rec=size_text(rec))))
            elif rec_h and eff_h < rec_h * 0.95:
                add(Issue(INFO, "below_rec", _msg("below_rec", lang, size=size, rec=size_text(rec),
                                                  pct=round(100 * eff_h / rec_h)), _msg("below_rec_fix", lang, rec=size_text(rec))))
        else:
            too_small = (min_w and eff_w < min_w * 0.98) or (min_h and eff_h < min_h * 0.98)
            if too_small:
                add(Issue(ERROR, "too_small", _msg("too_small", lang, size=size, min=size_text((min_w, min_h))),
                          _msg("too_small_fix", lang, min=size_text((min_w, min_h)), rec=size_text(rec))))
            elif rec_w and eff_w < rec_w * 0.95:
                add(Issue(WARNING if eff_w < rec_w * 0.75 else INFO, "below_rec",
                          _msg("below_rec", lang, size=size, rec=size_text(rec), pct=round(100 * eff_w / rec_w)),
                          _msg("below_rec_fix", lang, rec=size_text(rec))))
            elif rec_w and rec_h and eff_w > rec_w * 1.6:
                save = round(100 * (1 - (rec_w * rec_h) / (eff_w * eff_h)))
                add(Issue(INFO, "oversized", _msg("oversized", lang, size=size, rec=size_text(rec), save=save),
                          _msg("oversized_fix", lang, rec=size_text(rec))))

        if info.orientation != 1:
            add(Issue(INFO, "exif_rotated", _msg("exif_rotated", lang, o=info.orientation), _msg("exif_rotated_fix", lang)))

    # --- weight & format advice ------------------------------------------
    kb = round(info.file_size / 1024) if info.file_size else None
    if kb is not None and kb > slot.max_kb:
        add(Issue(WARNING if kb > slot.max_kb * 2 else INFO, "heavy", _msg("heavy", lang, kb=kb, max=slot.max_kb),
                  _msg("heavy_fix", lang)))
    if info.format == "png" and slot.photo and info.has_alpha is False and kb and kb > slot.max_kb * 0.6:
        add(Issue(INFO, "png_photo", _msg("png_photo", lang), _msg("png_photo_fix", lang)))
    if info.format == "gif" and info.animated and kb and kb > 300:
        add(Issue(WARNING, "animated_gif", _msg("animated_gif", lang, kb=kb), _msg("animated_gif_fix", lang)))
    if slot.key in ("logo", "favicon") and not info.vector:
        add(Issue(INFO, "prefer_svg", _msg("prefer_svg", lang), _msg("prefer_svg_fix", lang)))
        if slot.key == "logo" and info.has_alpha is False:
            add(Issue(WARNING, "logo_alpha", _msg("logo_alpha", lang), _msg("logo_alpha_fix", lang)))

    order = {ERROR: 0, WARNING: 1, INFO: 2}
    report.issues.sort(key=lambda i: order[i.level])
    return report


def analyze_image(path: Union[str, os.PathLike], slot: Union[str, ImageSlot] = "content_image", *,
                  lang: str = "tr", display_width: Optional[int] = None,
                  focus: Union[str, tuple, None] = "center") -> ImageReport:
    """Check an image file (or http(s) URL) against a placement slot.

    >>> print(analyze_image("photo.jpg", "hero_background"))
    """
    p = os.fspath(path)
    info = probe_url(p) if p.startswith(("http://", "https://")) else probe(p)
    return analyze_info(info, slot, lang=lang, display_width=display_width, focus=focus, source=p)


@dataclass
class Placement:
    slot: ImageSlot
    score: int
    report: ImageReport
    lang: str = "tr"

    def __str__(self) -> str:
        bar = "█" * (self.score // 10) + "░" * (10 - self.score // 10)
        return f"{bar} {self.score:>3}%  {self.slot.label(self.lang)}  [{self.slot.key}]"


def suggest_placement(path: Union[str, os.PathLike], *, lang: str = "tr", top: int = 5) -> list[Placement]:
    """Rank the slots an image fits best, by aspect ratio, resolution and weight.

    >>> for p in suggest_placement("photo.jpg"): print(p)
    """
    p = os.fspath(path)
    info = probe_url(p) if p.startswith(("http://", "https://")) else probe(p)
    results = []
    for slot in SLOTS.values():
        report = analyze_info(info, slot, lang=lang, source=p)
        if slot.aspect_value and not info.vector:
            deviation = abs(info.aspect - slot.aspect_value) / slot.aspect_value
            aspect_fit = max(0.0, 1 - max(0.0, deviation - slot.aspect_tolerance) * (1.5 if slot.crops else 1.2))
        else:
            aspect_fit = 0.85
        rec_w = slot.recommended[0]
        if info.vector:
            res_fit = 1.0
        elif rec_w:
            eff_w = report.crop.width if (report.crop and slot.crops) else info.width
            res_fit = min(1.0, eff_w / rec_w)
            if eff_w > rec_w * 3:  # a 4000px photo is not an avatar
                res_fit *= 0.6
            elif eff_w > rec_w * 1.6:  # works, but the slot does not need that much
                res_fit *= 0.9
        else:
            res_fit = min(1.0, info.height / (slot.recommended[1] or 1))
        score = 100 * (0.55 * aspect_fit + 0.45 * res_fit)
        if not report.ok:
            score *= 0.5
        if slot.key in ("logo", "favicon") and slot.photo is False and not info.vector and info.has_alpha is False:
            score *= 0.6
        results.append(Placement(slot, round(score), report, lang))
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top]
