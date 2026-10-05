"""The :class:`Site` object: theme settings, pages and the build step."""

from __future__ import annotations

import json
import os
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

from .background import Background
from .builder import build_site, collect_image_reports, render_page
from .components import Container

if TYPE_CHECKING:  # pragma: no cover
    from .builder import SiteImageReport

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
                 description: Optional[str] = None, favicon: Optional[str] = None, og_image: Optional[str] = None,
                 url: Optional[str] = None, theme_color: Optional[str] = None) -> None:
        """
        title        page title (browser tab, search results)
        theme        preset name or dict of theme values
        lang         HTML language and the language of build reports ("tr" or "en")
        description  meta description for search engines and link previews
        favicon      tab icon — 512×512 PNG or SVG recommended
        og_image     link preview image for WhatsApp/X/LinkedIn — 1200×630 px recommended
        url          public address of the site (enables absolute og:image and canonical links)
        theme_color  colour of the mobile browser bar
        """
        self._theme: dict[str, Any] = {}
        self.lang = lang
        self.favicon = favicon
        self.og_image = og_image
        self.url = url.rstrip("/") if url else None
        self.theme_color = theme_color
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

    def background(self, value: Union[str, Background, None] = None, *, image: Optional[str] = None,
                   color: Optional[str] = None, **layer: Any) -> "Site":
        """Page background.

        Colour or gradient::

            site.background("#0b1120")
            site.background("linear-gradient(135deg, #667eea, #764ba2)")

        Picture (recommended 2560×1440 px, 16:9, ≤ 450 KB — see ``image_guide("page_background")``)::

            site.background(image="city.jpg", overlay="dark", blur=3, position="center bottom",
                            mobile_image="city-portrait.jpg")

        Extra keyword options are the :class:`~webcraft.Background` fields: size, position, repeat,
        fixed, overlay, overlay_opacity, blur, brightness, contrast, saturate, grayscale,
        mobile_image, mobile_position, motion, parallax_speed, text, focus.
        ``color`` is the solid fallback shown behind images/gradients and used by the navbar."""
        if isinstance(value, Background):
            layer_obj = value
        elif image is not None or layer:
            layer_obj = Background(image=image, color=color, gradient=value, **layer)
        else:
            layer_obj = None
        if layer_obj is not None:
            data = layer_obj.to_dict()
            if layer_obj.image:
                self._theme["background_layer"] = data
                self._theme.pop("background_image", None)
            else:
                self._theme.pop("background_layer", None)
            if layer_obj.gradient:
                self._theme["background"] = layer_obj.gradient
            if layer_obj.color:
                self._theme["background_color"] = layer_obj.color
            if layer_obj.text:
                self._theme["text"] = {"light": "#f8fafc", "dark": "#0f172a"}.get(layer_obj.text, layer_obj.text)
            return self
        if value is not None:
            self._theme["background"] = value
            self._theme.pop("background_layer", None)
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

    def build(self, out_dir: Union[str, os.PathLike] = "dist", *, inline: bool = False,
              optimize_images: bool = False, check_images: bool = True, strict: bool = False,
              check_remote: bool = False, quiet: bool = False) -> Path:
        """Write every page to ``out_dir`` and return the path of ``index.html``.

        inline           one self-contained HTML file per page (CSS/JS embedded)
        optimize_images  crop, compress and create responsive WebP variants (needs Pillow)
        check_images     analyse every image against the slot it is used in and print a report
        strict           raise :class:`ImageQualityError` if any image has an error (CI usage)
        check_remote     also download the headers of http(s) images to analyse them
        quiet            don't print the report
        """
        return build_site(self, Path(out_dir), inline=inline, optimize_images=optimize_images,
                          check_images=check_images, strict=strict, check_remote=check_remote, quiet=quiet)

    def image_report(self, *, check_remote: bool = False) -> "SiteImageReport":
        """Analyse every image used on the site against its placement — without building.

            print(site.image_report())
        """
        return collect_image_reports(self, check_remote=check_remote)

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
    resim_raporu = image_report
    onizle = preview
    yayinla = serve
