"""Turns a :class:`~webcraft.site.Site` into static HTML files.

Build pipeline per page:
  1. ``page.to_dict()``  -> JSON spec (deep-copied, so the Site is never mutated)
  2. find every image reference and the *slot* (placement) it is used in
  3. analyse local images against their slot (size, ratio, crop, weight, format)
  4. copy or optimise them into ``assets/media`` and rewrite the paths (+ srcset / intrinsic size)
  5. render HTML with SEO / Open Graph tags and an LCP preload for the hero image
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import html
import json
import shutil
import sys
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import quote_plus

from .images.analyze import INFO, ImageReport, analyze_info
from .images.optimize import OptimizedImage, PillowMissing, has_pillow, optimize_image
from .images.probe import ImageInfo, ImageProbeError, probe, probe_url
from .images.specs import ImageSlot, get_slot

if TYPE_CHECKING:  # pragma: no cover
    from .site import Page, Site

ASSETS_DIR = "assets"
MEDIA_DIR = f"{ASSETS_DIR}/media"
MEDIA_KEYS = {"src", "image", "background_image", "avatar", "logo_image", "poster", "mobile_image"}
SYSTEM_FONTS = {
    "system-ui", "sans-serif", "serif", "monospace", "arial", "helvetica", "georgia",
    "times new roman", "verdana", "tahoma", "courier new", "segoe ui",
}
PRESET_FONTS = {
    "light": "Inter", "dark": "Inter", "ocean": "Poppins", "sunset": "Poppins",
    "forest": "Nunito", "midnight": "Space Grotesk", "minimal": "DM Sans",
}

# component type -> [(path, slot)]; "items[].image" walks a list of dicts
COMPONENT_MEDIA = {
    "hero": [("image", "hero_image")],
    "image": [("src", "content_image")],
    "navbar": [("logo_image", "logo")],
    "video": [("poster", "video_poster")],
    "features": [("items[].image", "card_image")],
    "gallery": [("images[].src", "gallery")],
    "testimonials": [("items[].avatar", "avatar")],
}


class ImageQualityError(RuntimeError):
    """Raised by ``build(strict=True)`` when an image has an error-level issue."""

    def __init__(self, report: "SiteImageReport") -> None:
        self.report = report
        super().__init__(f"{report.error_count} image error(s):\n{report}")


def _echo(text: str) -> None:
    """print() that never crashes on consoles without UTF-8."""
    try:
        print(text)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "ascii"
        print(text.encode(enc, "replace").decode(enc))


def static_file(name: str) -> str:
    return resources.files("webcraft").joinpath("static", name).read_text(encoding="utf-8")


def _safe_json(data: Any) -> str:
    """JSON that is safe to embed inside a ``<script>`` tag."""
    return (json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def _is_remote(value: str) -> bool:
    return value.startswith(("http://", "https://", "//"))


def _is_local_candidate(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and not _is_remote(value) \
        and not value.startswith(("data:", "#", "/", "blob:"))


# ----------------------------------------------------------------------
# Finding media references
# ----------------------------------------------------------------------
@dataclass
class MediaRef:
    holder: dict
    key: str
    slot: Optional[str]
    where: str
    display_width: Optional[int] = None
    focus: Any = None
    overrides: dict = field(default_factory=dict)   # e.g. a user-forced aspect ratio

    @property
    def value(self) -> str:
        return self.holder[self.key]

    def resolve_slot(self) -> Optional[ImageSlot]:
        if not self.slot:
            return None
        slot = get_slot(self.slot)
        return dataclasses.replace(slot, **self.overrides) if self.overrides else slot


# Issues that optimize_images=True removes by itself
FIXED_BY_OPTIMIZE = {"bad_format", "heavy", "oversized", "png_photo", "exif_rotated"}
# Site-level images that must stay a single, unchanged file
SINGLE_FILE_KEYS = {"favicon", "og_image"}


def _parse_aspect(value: Any) -> Optional[tuple]:
    try:
        a, b = (float(x) for x in str(value).replace("/", ":").split(":"))
    except ValueError:
        return None
    if a <= 0 or b <= 0:
        return None
    return tuple(int(x) if x.is_integer() else x for x in (a, b))


def _px(value: Any) -> Optional[int]:
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.endswith("px") and value[:-2].strip().isdigit():
        return int(value[:-2])
    return None


def _walk_path(props: dict, path: str):
    """Yield (holder_dict, key, index) for 'key' or 'list[].key' paths."""
    if "[]." in path:
        list_key, key = path.split("[].", 1)
        for i, item in enumerate(props.get(list_key) or []):
            if isinstance(item, dict) and item.get(key):
                yield item, key, i
    elif props.get(path):
        yield props, path, None


def _background_refs(holder: dict, where: str, slot: str, out: list) -> None:
    bg = holder.get("background")
    if not isinstance(bg, dict):
        return
    focus = bg.get("focus") or bg.get("position")
    if bg.get("image"):
        out.append(MediaRef(bg, "image", slot, f"{where} › background", focus=focus))
    if bg.get("mobile_image"):
        out.append(MediaRef(bg, "mobile_image", "mobile_background", f"{where} › background (mobile)",
                            focus=bg.get("mobile_position") or focus))


def find_media(spec: dict, page_label: str) -> list[MediaRef]:
    """Every image reference in a page spec, with the slot it is displayed in."""
    refs: list[MediaRef] = []
    theme = spec.get("theme") or {}
    layer = theme.get("background_layer")
    if isinstance(layer, dict):
        _background_refs({"background": layer}, f"{page_label} › page", "page_background", refs)

    def visit(nodes: list, trail: str, in_columns: bool) -> None:
        for idx, node in enumerate(nodes or []):
            if not isinstance(node, dict):
                continue
            ctype = node.get("type", "?")
            props = node.get("props") or {}
            label = f"{trail} › {ctype}" + ("" if ctype in ("hero", "navbar", "footer") else f" #{idx + 1}")
            _background_refs(props, label, "hero_background" if ctype == "hero" else "section_background", refs)
            for path, slot in COMPONENT_MEDIA.get(ctype, []):
                if ctype == "image" and in_columns:
                    slot = "column_image"
                for holder, key, i in _walk_path(props, path):
                    where = label + (f" › item {i + 1}" if i is not None else "") + f" › {key}"
                    display, focus, overrides = None, None, {}
                    if ctype == "image":
                        display, focus = _px(props.get("width")), holder.get("position")
                        aspect = _parse_aspect(props.get("aspect")) if props.get("aspect") else None
                        if aspect:  # the user forced a ratio: judge against it, not the slot default
                            overrides = {"aspect": aspect, "crops": props.get("fit", "cover") == "cover",
                                         "aspect_tolerance": 0.03}
                    refs.append(MediaRef(holder, key, slot, where, display, focus, overrides))
            visit(node.get("children") or [], label, in_columns)
            for c_idx, col in enumerate(node.get("columns") or []):
                visit(col, f"{label} › col {c_idx + 1}", True)

    visit(spec.get("components") or [], page_label, False)

    # Anything else that looks like a local media path (custom components) is copied, not analysed.
    known = {(id(r.holder), r.key) for r in refs}

    def generic(node: Any, trail: str) -> None:
        if isinstance(node, list):
            for item in node:
                generic(item, trail)
        elif isinstance(node, dict):
            for key, value in node.items():
                if key in MEDIA_KEYS and _is_local_candidate(value) and (id(node), key) not in known:
                    refs.append(MediaRef(node, key, None, f"{trail} › {key}"))
                else:
                    generic(value, trail)

    generic(spec.get("components"), page_label)
    return refs


# ----------------------------------------------------------------------
# Reports
# ----------------------------------------------------------------------
@dataclass
class ImageEntry:
    where: str
    value: str
    slot: Optional[str]
    report: Optional[ImageReport] = None
    status: str = "ok"            # ok | missing | remote | unreadable | unchecked
    detail: str = ""
    optimized: Optional[OptimizedImage] = None


@dataclass
class SiteImageReport:
    """All images of a site with their per-slot analysis. ``print()`` it for a readable report."""

    entries: list[ImageEntry] = field(default_factory=list)
    lang: str = "tr"
    notes: list[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for e in self.entries if e.status in ("missing", "unreadable")
                   or (e.report and not e.report.ok))

    @property
    def warning_count(self) -> int:
        return sum(len(e.report.warnings) for e in self.entries if e.report)

    @property
    def ok(self) -> bool:
        return self.error_count == 0

    def to_dict(self) -> dict:
        return {"errors": self.error_count, "warnings": self.warning_count, "images": [
            {"where": e.where, "value": e.value, "slot": e.slot, "status": e.status, "detail": e.detail,
             "report": e.report.to_dict() if e.report else None,
             "optimized": {"src": e.optimized.src, "saved_pct": e.optimized.saved_pct} if e.optimized else None}
            for e in self.entries]}

    def __str__(self) -> str:
        tr = self.lang == "tr"
        if not self.entries:
            return "Görsel yok." if tr else "No images."
        lines = [("Görsel raporu" if tr else "Image report") + f" — {len(self.entries)} "
                 + ("görsel" if tr else "image(s)"), ""]
        for e in self.entries:
            lines.append(f"• {e.where}")
            if e.report:
                lines += ["  " + line for line in str(e.report).splitlines()]
            elif e.status == "missing":
                lines.append(f"  ✗ {'Dosya bulunamadı' if tr else 'File not found'}: {e.value}")
            elif e.status == "unreadable":
                lines.append(f"  ✗ {'Okunamadı' if tr else 'Unreadable'}: {e.value} ({e.detail})")
            elif e.status == "remote":
                lines.append(f"  ℹ {e.value}\n    {e.detail}")
            else:
                lines.append(f"  · {e.value}" + (f" ({e.detail})" if e.detail else ""))
            if e.optimized:
                o = e.optimized
                saved = f"%{o.saved_pct} daha küçük" if tr else f"{o.saved_pct}% smaller"
                lines.append(f"  ⚡ {'Optimize edildi' if tr else 'Optimised'}: {o.width}×{o.height} WebP, "
                             f"{len(o.files)} {'boyut' if tr else 'sizes'}, {o.optimized_bytes // 1024} KB ({saved})")
            lines.append("")
        lines += self.notes
        lines.append(f"Toplam: {self.error_count} hata, {self.warning_count} uyarı" if tr
                     else f"Total: {self.error_count} error(s), {self.warning_count} warning(s)")
        return "\n".join(lines)


def _base_dirs(base_dir: Optional[Path]) -> list[Path]:
    # Relative media paths are looked up next to the working directory, then next to the running script.
    dirs = [base_dir] if base_dir else [Path.cwd()]
    if not base_dir and sys.argv and sys.argv[0]:
        dirs.append(Path(sys.argv[0]).resolve().parent)
    return dirs


def _find_local(value: str, base_dirs: list[Path]) -> Optional[Path]:
    for base in base_dirs:
        candidate = (base / value).resolve()
        if candidate.is_file():
            return candidate
    return None


def _inspect(ref: MediaRef, base_dirs: list[Path], lang: str,
             check_remote: bool) -> tuple[ImageEntry, Optional[Path], Optional[ImageInfo]]:
    """Locate, probe and analyse one reference."""
    value = ref.value
    entry = ImageEntry(ref.where, value, ref.slot)
    if _is_remote(value):
        entry.status = "remote"
        if not (check_remote and ref.slot):
            entry.detail = ("Uzak görsel; analiz için check_remote=True" if lang == "tr"
                            else "Remote image; use check_remote=True to analyse")
            return entry, None, None
        try:
            info = probe_url(value if not value.startswith("//") else "https:" + value)
        except Exception as exc:  # noqa: BLE001 - any network/parse error is reported, not raised
            entry.detail = f"{'İndirilemedi' if lang == 'tr' else 'Could not fetch'}: {exc}"
            return entry, None, None
        entry.status = "ok"
        entry.report = analyze_info(info, ref.resolve_slot(), lang=lang, display_width=ref.display_width,
                                    focus=ref.focus, source=value)
        return entry, None, info
    if not _is_local_candidate(value):
        entry.status = "unchecked"
        return entry, None, None
    source = _find_local(value, base_dirs)
    if source is None:
        entry.status = "missing"
        return entry, None, None
    try:
        info = probe(source)
    except (ImageProbeError, OSError) as exc:
        entry.status = "unreadable"
        entry.detail = str(exc)
        return entry, source, None
    if ref.slot:
        entry.report = analyze_info(info, ref.resolve_slot(), lang=lang, display_width=ref.display_width,
                                    focus=ref.focus, source=value)
    else:
        entry.status = "unchecked"
        entry.detail = f"{info.width}×{info.height}"
    return entry, source, info


def _site_meta_refs(holder: dict) -> list[MediaRef]:
    refs = []
    if holder.get("favicon"):
        refs.append(MediaRef(holder, "favicon", "favicon", "site › favicon"))
    if holder.get("og_image"):
        refs.append(MediaRef(holder, "og_image", "og_image", "site › og_image"))
    return refs


def _report_lang(site: "Site") -> str:
    return site.lang if site.lang in ("tr", "en") else "en"


def collect_image_reports(site: "Site", *, check_remote: bool = False,
                          base_dir: Optional[Path] = None) -> SiteImageReport:
    """Analyse all images of a site without writing anything."""
    report = SiteImageReport(lang=_report_lang(site))
    dirs = _base_dirs(base_dir)
    refs = _site_meta_refs({"favicon": site.favicon, "og_image": site.og_image})
    for page in site.pages.values():
        refs += find_media(copy.deepcopy(page.to_dict()), page.filename)
    for ref in refs:
        report.entries.append(_inspect(ref, dirs, report.lang, check_remote)[0])
    return report


# ----------------------------------------------------------------------
# HTML
# ----------------------------------------------------------------------
def _font_links(theme: dict) -> str:
    fonts = []
    for name in (theme.get("font") or PRESET_FONTS.get(theme.get("preset", "light")), theme.get("heading_font")):
        if name and name.lower() not in SYSTEM_FONTS and name not in fonts:
            fonts.append(name)
    if not fonts:
        return ""
    tags = ['<link rel="preconnect" href="https://fonts.googleapis.com">',
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>']
    for name in fonts:
        url = f"https://fonts.googleapis.com/css2?family={quote_plus(name)}:wght@400;500;600;700;800&display=swap"
        tags.append(f'<link rel="stylesheet" href="{html.escape(url)}" data-wc-font="{html.escape(name)}">')
    return "\n  ".join(tags)


def _lcp_preload(spec: dict) -> str:
    """Preload the largest above-the-fold image so it downloads before the JS runs."""
    candidates = []
    layer = (spec.get("theme") or {}).get("background_layer")
    if isinstance(layer, dict) and layer.get("image"):
        candidates.append(layer)
    for node in (spec.get("components") or [])[:2]:
        props = node.get("props") or {}
        bg = props.get("background")
        if node.get("type") == "hero":
            if isinstance(bg, dict) and bg.get("image"):
                candidates.append(bg)
            elif props.get("image"):
                candidates.append(props)
    if not candidates:
        return ""
    holder = candidates[0]
    attrs = f'rel="preload" as="image" href="{html.escape(holder["image"])}"'
    if holder.get("image_srcset"):
        attrs += f' imagesrcset="{html.escape(holder["image_srcset"])}" imagesizes="100vw"'
    return f'<link {attrs} fetchpriority="high">'


def _absolute(site: "Site", path: str) -> str:
    if _is_remote(path) or not site.url:
        return path
    return f"{site.url}/{path.lstrip('./')}"


def render_page(site: "Site", page: "Page", *, inline: bool = False, spec: Optional[dict] = None,
                meta_media: Optional[dict] = None) -> str:
    spec = spec if spec is not None else page.to_dict()
    meta_media = meta_media or {"favicon": site.favicon, "og_image": site.og_image}
    title = html.escape(spec["title"])
    description = page.description or site.description
    favicon, og_image = meta_media.get("favicon"), meta_media.get("og_image")

    meta = []
    if description:
        meta.append(f'<meta name="description" content="{html.escape(description)}">')
        meta.append(f'<meta property="og:description" content="{html.escape(description)}">')
    meta.append(f'<meta property="og:title" content="{title}">')
    meta.append('<meta property="og:type" content="website">')
    if site.url:
        page_url = site.url + ("/" if page.filename == "index.html" else f"/{page.filename}")
        meta.append(f'<link rel="canonical" href="{html.escape(page_url)}">')
        meta.append(f'<meta property="og:url" content="{html.escape(page_url)}">')
    if og_image:
        meta.append(f'<meta property="og:image" content="{html.escape(_absolute(site, og_image))}">')
        meta.append('<meta name="twitter:card" content="summary_large_image">')
    if site.theme_color:
        meta.append(f'<meta name="theme-color" content="{html.escape(site.theme_color)}">')
    if favicon:
        meta.append(f'<link rel="icon" href="{html.escape(favicon)}">')
        meta.append(f'<link rel="apple-touch-icon" href="{html.escape(favicon)}">')
    else:
        meta.append('<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 '
                    'viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>✦</text></svg>">')
    preload = _lcp_preload(spec)
    if preload:
        meta.append(preload)

    if inline:
        css = f"<style>\n{static_file('webcraft.css')}\n</style>"
        js = f"<script>\n{static_file('webcraft.js')}\n</script>"
    else:
        css = f'<link rel="stylesheet" href="{ASSETS_DIR}/webcraft.css">'
        js = f'<script src="{ASSETS_DIR}/webcraft.js"></script>'
    head = "\n  ".join(part for part in [*meta, _font_links(spec["theme"]), css, *site.head_html] if part)

    return f"""<!doctype html>
<html lang="{html.escape(site.lang)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="generator" content="WebCraft">
  <title>{title}</title>
  {head}
</head>
<body>
  <div id="app"></div>
  <noscript><p style="padding:2rem;text-align:center">Bu site JavaScript gerektirir. / This site requires JavaScript.</p></noscript>
  <script type="application/json" data-webcraft data-target="#app">{_safe_json(spec)}</script>
  {js}
</body>
</html>
"""


# ----------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------
def _mark_resolved(report: ImageReport) -> None:
    """Move issues the optimiser fixed out of the active list; pre-crop advice becomes informational."""
    still = []
    for issue in report.issues:
        if issue.code in FIXED_BY_OPTIMIZE:
            report.resolved.append(issue)
        else:
            if issue.code in ("aspect_crop", "not_square"):
                issue.level = INFO
            still.append(issue)
    report.issues = still


def _copy_media(source: Path, out_dir: Path, copied: dict[str, str]) -> str:
    if str(source) not in copied:
        digest = hashlib.sha1(str(source).encode()).hexdigest()[:8]
        target = Path(MEDIA_DIR) / f"{source.stem}-{digest}{source.suffix.lower()}"
        (out_dir / target).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, out_dir / target)
        copied[str(source)] = target.as_posix()
    return copied[str(source)]


def build_site(site: "Site", out_dir: Path, *, inline: bool = False, base_dir: Optional[Path] = None,
               optimize_images: bool = False, check_images: bool = True, strict: bool = False,
               check_remote: bool = False, quiet: bool = False) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    lang = _report_lang(site)
    dirs = _base_dirs(base_dir)
    if not inline:
        (out_dir / ASSETS_DIR).mkdir(exist_ok=True)
        for name in ("webcraft.js", "webcraft.css"):
            (out_dir / ASSETS_DIR / name).write_text(static_file(name), encoding="utf-8")

    report = SiteImageReport(lang=lang)
    if optimize_images and not has_pillow():
        report.notes.append("⚠ optimize_images=True için Pillow gerekli: pip install pillow" if lang == "tr"
                            else "⚠ optimize_images=True needs Pillow: pip install pillow")
        optimize_images = False

    copied: dict[str, str] = {}
    optimized_cache: dict[tuple, Optional[OptimizedImage]] = {}
    reported: set[tuple] = set()

    def process(ref: MediaRef) -> None:
        entry, source, info = _inspect(ref, dirs, lang, check_remote and check_images)
        if check_images and (ref.where, ref.value) not in reported:
            reported.add((ref.where, ref.value))
            report.entries.append(entry)
        if source is None:
            return
        opt = None
        if (optimize_images and ref.slot and info is not None and not info.vector
                and ref.key not in SINGLE_FILE_KEYS):
            key = (str(source), ref.slot, repr(ref.focus), ref.display_width, repr(ref.overrides))
            if key not in optimized_cache:
                try:
                    optimized_cache[key] = optimize_image(
                        source, ref.resolve_slot(), out_dir / MEDIA_DIR, rel_prefix=f"{MEDIA_DIR}/",
                        focus=ref.focus or "center", display_width=ref.display_width)
                except (PillowMissing, OSError) as exc:
                    entry.detail = str(exc)
                    optimized_cache[key] = None
            opt = optimized_cache[key]
        if opt is not None:
            ref.holder[ref.key] = opt.src
            ref.holder[f"{ref.key}_srcset"] = opt.srcset
            ref.holder[f"{ref.key}_size"] = [opt.width, opt.height]
            entry.optimized = opt
            if entry.report:
                _mark_resolved(entry.report)
        else:
            ref.holder[ref.key] = _copy_media(source, out_dir, copied)
            if info is not None and ref.key not in ("favicon", "og_image"):
                ref.holder[f"{ref.key}_size"] = [info.width, info.height]

    meta_media = {"favicon": site.favicon, "og_image": site.og_image}
    for ref in _site_meta_refs(meta_media):
        process(ref)

    for page in site.pages.values():
        spec = copy.deepcopy(page.to_dict())
        for ref in find_media(spec, page.filename):
            process(ref)
        html_text = render_page(site, page, inline=inline, spec=spec, meta_media=meta_media)
        (out_dir / page.filename).write_text(html_text, encoding="utf-8")

    site.last_image_report = report
    if check_images and report.entries and not quiet:
        _echo(str(report))
    if strict and not report.ok:
        raise ImageQualityError(report)
    return (out_dir / "index.html").resolve()
