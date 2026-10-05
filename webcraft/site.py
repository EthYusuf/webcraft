"""The :class:`Site` object: theme settings, pages and the build step."""

from __future__ import annotations

import json
import os
import webbrowser
from pathlib import Path
from typing import Any, Optional, Union

from .builder import build_site, render_page
from .components import Container

THEMES = ("light", "dark", "ocean", "sunset", "forest", "midnight", "minimal")

_COLOR_KEYS = ("primary", "secondary", "surface", "text", "muted", "border")


class Page(Container):
    """A single HTML page of a :class:`Site`."""

    def __init__(self, site: "Site", name: str, title: Optional[str] = None,
                 description: Optional[str] = None) -> None:
        super().__init__()
        self.site = site
        self.name = name
        self.title = title
        self.description = description

    @property
    def filename(self) -> str:
        return "index.html" if self.name == "index" else f"{self.name}.html"

    def to_dict(self) -> dict:
        """The JSON spec consumed by ``WebCraft.render`` in the browser."""
        return {
            "title": self.title or self.site.title,
            "theme": dict(self.site._theme),
            "components": self.components,
        }

    def to_html(self, inline: bool = False) -> str:
        return render_page(self.site, self, inline=inline)


class Site(Page):
    """A website. The site itself is the home page (``index.html``)::

        from webcraft import Site

        site = Site("My Site", theme="dark")
        site.background("#0b1120").font("Poppins")
        site.hero("Hello **world**", "Built with Python")
        site.build()
    """

    def __init__(self, title: str = "WebCraft Site", *, theme: Union[str, dict] = "light", lang: str = "tr",
                 description: Optional[str] = None, favicon: Optional[str] = None) -> None:
        self._theme: dict[str, Any] = {}
        self.lang = lang
        self.favicon = favicon
        self.head_html: list[str] = []
        self.pages: dict[str, Page] = {}
        super().__init__(self, "index", title, description)
        self.pages["index"] = self
        self.theme(theme)

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------
    def page(self, name: str, title: Optional[str] = None, description: Optional[str] = None) -> Page:
        """Get or create another page, written to ``<name>.html``."""
        name = name.strip().strip("/").removesuffix(".html") or "index"
        if name not in self.pages:
            self.pages[name] = Page(self, name, title, description)
        return self.pages[name]

    # ------------------------------------------------------------------
    # Theme / styling — all chainable
    # ------------------------------------------------------------------
    def theme(self, preset: Union[str, dict, None] = None, **overrides: Any) -> "Site":
        """Choose a preset (``light, dark, ocean, sunset, forest, midnight, minimal``)
        and/or override individual theme values."""
        if isinstance(preset, dict):
            overrides = {**preset, **overrides}
            preset = overrides.pop("preset", None)
        if preset is not None:
            if preset not in THEMES:
                raise ValueError(f"Unknown theme {preset!r}. Choose one of: {', '.join(THEMES)}")
            self._theme = {"preset": preset, **{k: v for k, v in self._theme.items() if k != "preset"}}
        self._theme.update({k: v for k, v in overrides.items() if v is not None})
        return self

    def background(self, value: Optional[str] = None, *, image: Optional[str] = None,
                   overlay: Optional[str] = None, color: Optional[str] = None) -> "Site":
        """Page background: a colour (``"#101010"``), any CSS gradient, or ``image=`` a picture.

        ``overlay`` darkens/tints an image, e.g. ``"rgba(0,0,0,.5)"``.
        ``color`` is the solid fallback used behind gradients and by the navbar."""
        if value is not None:
            self._theme["background"] = value
        if image is not None:
            self._theme["background_image"] = image
        if overlay is not None:
            self._theme["background_overlay"] = overlay
        if color is not None:
            self._theme["background_color"] = color
        return self

    def font(self, name: str, heading: Optional[str] = None, *, size: Union[int, str, None] = None) -> "Site":
        """Any Google Font name (``"Poppins"``, ``"Playfair Display"`` ...) — loaded automatically.
        ``heading`` sets a separate font for titles; ``size`` the base text size in px."""
        self._theme["font"] = name
        if heading:
            self._theme["heading_font"] = heading
        if size is not None:
            self._theme["font_size"] = f"{size}px" if isinstance(size, (int, float)) else size
        return self

    def colors(self, primary: Optional[str] = None, secondary: Optional[str] = None, *,
               text: Optional[str] = None, muted: Optional[str] = None, surface: Optional[str] = None,
               border: Optional[str] = None) -> "Site":
        """Brand colours. ``primary`` drives buttons, links and highlights."""
        values = dict(primary=primary, secondary=secondary, text=text, muted=muted, surface=surface, border=border)
        self._theme.update({k: v for k, v in values.items() if v is not None})
        return self

    def text_color(self, color: str) -> "Site":
        self._theme["text"] = color
        return self

    def primary_color(self, color: str) -> "Site":
        self._theme["primary"] = color
        return self

    def radius(self, value: Union[int, str]) -> "Site":
        """Corner roundness of cards and buttons (``0`` for sharp corners)."""
        self._theme["radius"] = f"{value}px" if isinstance(value, (int, float)) else value
        return self

    def width(self, value: Union[int, str]) -> "Site":
        """Maximum content width."""
        self._theme["max_width"] = f"{value}px" if isinstance(value, (int, float)) else value
        return self

    def head(self, raw_html: str) -> "Site":
        """Inject extra HTML into ``<head>`` (analytics, meta tags ...)."""
        self.head_html.append(raw_html)
        return self

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    def to_json(self, indent: Optional[int] = 2) -> str:
        return json.dumps({name: p.to_dict() for name, p in self.pages.items()}, indent=indent, ensure_ascii=False)

    def build(self, out_dir: Union[str, os.PathLike] = "dist", *, inline: bool = False) -> Path:
        """Write every page to ``out_dir``. With ``inline=True`` each page is a single
        self-contained HTML file (CSS and JS embedded). Returns the path of ``index.html``."""
        return build_site(self, Path(out_dir), inline=inline)

    def preview(self, out_dir: Union[str, os.PathLike] = "dist") -> Path:
        """Build and open the home page in the default browser (no server needed)."""
        index = self.build(out_dir)
        webbrowser.open(index.resolve().as_uri())
        return index

    def serve(self, port: int = 8000, out_dir: Union[str, os.PathLike] = "dist", *, open_browser: bool = True) -> None:
        """Build, then serve the site on ``http://localhost:<port>`` until Ctrl+C."""
        from .server import serve

        self.build(out_dir)
        serve(out_dir, port=port, open_browser=open_browser)

    # -- Turkish aliases (Türkçe komutlar) ------------------------------
    sayfa = page
    tema = theme
    arka_plan = background
    yazi_tipi = font
    renkler = colors
    yazi_rengi = text_color
    ana_renk = primary_color
    kose = radius
    genislik = width
    olustur = build
    onizle = preview
    yayinla = serve
