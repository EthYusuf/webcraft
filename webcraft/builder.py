"""Turns a :class:`~webcraft.site.Site` into static HTML files."""

from __future__ import annotations

import hashlib
import html
import json
import shutil
import sys
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import quote_plus

if TYPE_CHECKING:  # pragma: no cover
    from .site import Page, Site

ASSETS_DIR = "assets"
MEDIA_KEYS = {"src", "image", "background_image", "avatar", "logo_image", "poster"}
SYSTEM_FONTS = {
    "system-ui", "sans-serif", "serif", "monospace", "arial", "helvetica", "georgia",
    "times new roman", "verdana", "tahoma", "courier new", "segoe ui",
}
PRESET_FONTS = {
    "light": "Inter", "dark": "Inter", "ocean": "Poppins", "sunset": "Poppins",
    "forest": "Nunito", "midnight": "Space Grotesk", "minimal": "DM Sans",
}


def static_file(name: str) -> str:
    return resources.files("webcraft").joinpath("static", name).read_text(encoding="utf-8")


def _safe_json(data: Any) -> str:
    """JSON that is safe to embed inside a ``<script>`` tag."""
    return (json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


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


def render_page(site: "Site", page: "Page", *, inline: bool = False, spec: dict | None = None) -> str:
    spec = spec if spec is not None else page.to_dict()
    title = html.escape(spec["title"])
    description = page.description or site.description
    meta = [f'<meta name="description" content="{html.escape(description)}">' if description else "",
            f'<meta property="og:title" content="{title}">',
            f'<link rel="icon" href="{html.escape(site.favicon)}">' if site.favicon else
            '<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22>'
            '<text y=%22.9em%22 font-size=%2290%22>✦</text></svg>">']
    if inline:
        css = f"<style>\n{static_file('webcraft.css')}\n</style>"
        js = f"<script>\n{static_file('webcraft.js')}\n</script>"
    else:
        css = f'<link rel="stylesheet" href="{ASSETS_DIR}/webcraft.css">'
        js = f'<script src="{ASSETS_DIR}/webcraft.js"></script>'
    head_extra = "\n  ".join(site.head_html)

    return f"""<!doctype html>
<html lang="{html.escape(site.lang)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="generator" content="WebCraft">
  <title>{title}</title>
  {chr(10).join("  " + m for m in meta if m).lstrip()}
  {_font_links(spec["theme"])}
  {css}
  {head_extra}
</head>
<body>
  <div id="app"></div>
  <noscript><p style="padding:2rem;text-align:center">Bu site JavaScript gerektirir. / This site requires JavaScript.</p></noscript>
  <script type="application/json" data-webcraft data-target="#app">{_safe_json(spec)}</script>
  {js}
</body>
</html>
"""


def _find_local(value: str, base_dirs: list[Path]) -> Path | None:
    for base in base_dirs:
        candidate = (base / value).resolve()
        if candidate.is_file():
            return candidate
    return None


def _collect_media(node: Any, out_dir: Path, base_dirs: list[Path], copied: dict[str, str]) -> Any:
    """Copy local media files referenced in the spec into ``assets/`` and rewrite their paths."""
    if isinstance(node, list):
        return [_collect_media(item, out_dir, base_dirs, copied) for item in node]
    if not isinstance(node, dict):
        return node
    result = {}
    for key, value in node.items():
        if key in MEDIA_KEYS and isinstance(value, str) and "://" not in value and not value.startswith(("data:", "#", "/")):
            source = _find_local(value, base_dirs)
            if source is not None:
                if str(source) not in copied:
                    digest = hashlib.sha1(str(source).encode()).hexdigest()[:8]
                    target = Path(ASSETS_DIR) / "media" / f"{source.stem}-{digest}{source.suffix.lower()}"
                    (out_dir / target).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, out_dir / target)
                    copied[str(source)] = target.as_posix()
                value = copied[str(source)]
        result[key] = _collect_media(value, out_dir, base_dirs, copied)
    return result


def build_site(site: "Site", out_dir: Path, *, inline: bool = False, base_dir: Path | None = None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    # Relative media paths are looked up next to the working directory, then next to the running script.
    base_dirs = [base_dir] if base_dir else [Path.cwd()]
    if not base_dir and sys.argv and sys.argv[0]:
        base_dirs.append(Path(sys.argv[0]).resolve().parent)
    if not inline:
        (out_dir / ASSETS_DIR).mkdir(exist_ok=True)
        for name in ("webcraft.js", "webcraft.css"):
            (out_dir / ASSETS_DIR / name).write_text(static_file(name), encoding="utf-8")

    copied: dict[str, str] = {}
    for page in site.pages.values():
        spec = _collect_media(page.to_dict(), out_dir, base_dirs, copied)
        (out_dir / page.filename).write_text(render_page(site, page, inline=inline, spec=spec), encoding="utf-8")
    return (out_dir / "index.html").resolve()
