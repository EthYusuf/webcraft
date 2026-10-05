"""Component methods shared by pages and sections.

Every method appends one component node (``{"type", "props"}``) to the
container and returns ``self`` so calls can be chained::

    site.heading("Hello").text("World").button("Start", "#start")

Common keyword options accepted by every component:
    id, background, color, padding, align, animate, class_, style

``background`` may be a CSS colour/gradient string or a :class:`~webcraft.Background`
(image + size/position/overlay/blur/parallax ...).
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional, Sequence, Union

from .background import Background, normalize_background

LinkSpec = Union[Mapping[str, str], Sequence[Any], None]
ButtonSpec = Union[str, Mapping[str, Any], Sequence[Any], None]

COMMON_OPTIONS = ("id", "background", "color", "padding", "align", "animate", "class_", "style")


# ----------------------------------------------------------------------
# Normalisers: accept friendly Python shapes, emit the JSON the JS expects
# ----------------------------------------------------------------------
def _links(links: LinkSpec) -> list[dict]:
    """``{"Home": "#"}``, ``[("Home", "#")]`` or ``[{"text":..,"href":..}]`` -> list of dicts."""
    if not links:
        return []
    if isinstance(links, Mapping):
        return [{"text": str(k), "href": str(v)} for k, v in links.items()]
    out = []
    for item in links:
        if isinstance(item, Mapping):
            out.append(dict(item))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            out.append({"text": str(item[0]), "href": str(item[1])})
        else:
            raise TypeError(f"Invalid link: {item!r} (use ('Text', 'href') or a dict)")
    return out


def _button(btn: ButtonSpec, default_style: Optional[str] = None) -> Optional[dict]:
    """``"Text"``, ``("Text", "href")``, ``("Text", "href", "outline")`` or a dict -> dict."""
    if btn is None:
        return None
    if isinstance(btn, str):
        out = {"text": btn, "href": "#"}
    elif isinstance(btn, Mapping):
        out = dict(btn)
    elif isinstance(btn, (list, tuple)) and 1 <= len(btn) <= 3:
        out = {"text": str(btn[0]), "href": str(btn[1]) if len(btn) > 1 else "#"}
        if len(btn) == 3:
            out["style"] = str(btn[2])
    else:
        raise TypeError(f"Invalid button: {btn!r}")
    if default_style and "style" not in out:
        out["style"] = default_style
    return out


def _items(items: Any, keys: Sequence[str]) -> list[dict]:
    """Tuples are mapped positionally onto ``keys``; dicts pass through; a mapping
    becomes ``(key, value)`` pairs."""
    if not items:
        return []
    if isinstance(items, Mapping):
        items = list(items.items())
    out = []
    for item in items:
        if isinstance(item, Mapping):
            out.append(dict(item))
        elif isinstance(item, (list, tuple)):
            if len(item) > len(keys):
                raise TypeError(f"Too many values in {item!r}; expected at most {len(keys)}: {keys}")
            out.append({k: v for k, v in zip(keys, item) if v is not None})
        elif isinstance(item, str):
            out.append({keys[0]: item})
        else:
            raise TypeError(f"Invalid item: {item!r}")
    return out


def _valid_aspect(value: str) -> bool:
    parts = str(value).replace("/", ":").split(":")
    try:
        return len(parts) == 2 and float(parts[0]) > 0 and float(parts[1]) > 0
    except ValueError:
        return False


def _common(opts: dict) -> dict:
    unknown = set(opts) - set(COMMON_OPTIONS)
    if unknown:
        raise TypeError(f"Unknown option(s): {', '.join(sorted(unknown))}. Allowed: {', '.join(COMMON_OPTIONS)}")
    props = {}
    for key, value in opts.items():
        if value is None:
            continue
        if key == "background":
            value = normalize_background(value)
        props["class" if key == "class_" else key] = value
    if props.get("animate") is False:
        props["animate"] = "none"
    return props


def _clean(props: dict) -> dict:
    return {k: v for k, v in props.items() if v is not None and v != [] and v != {}}


# ----------------------------------------------------------------------
# Container
# ----------------------------------------------------------------------
class Container:
    """Base class holding an ordered list of components."""

    def __init__(self) -> None:
        self.components: list[dict] = []

    # -- low level -----------------------------------------------------
    def add(self, type: str, props: Optional[dict] = None, **extra: Any) -> "Container":
        """Append any component, including custom ones registered with ``WebCraft.register`` in JS."""
        node = {"type": type, "props": _clean(props or {})}
        node.update(extra)
        self.components.append(node)
        return self

    def _add(self, type: str, props: dict, opts: dict) -> "Container":
        merged = _clean(props)
        merged.update(_common(opts))
        self.components.append({"type": type, "props": merged})
        return self

    # -- layout --------------------------------------------------------
    def navbar(self, logo: Optional[str] = None, links: LinkSpec = None, cta: ButtonSpec = None, *,
               logo_image: Optional[str] = None, logo_href: str = "#", sticky: bool = True, **opts: Any) -> "Container":
        """Top navigation bar. ``links`` may be a dict ``{"Home": "#home"}`` or a list of pairs."""
        return self._add("navbar", {
            "logo": logo, "links": _links(links), "cta": _button(cta), "logo_image": logo_image,
            "logo_href": logo_href, "sticky": sticky,
        }, opts)

    def hero(self, title: str, subtitle: Optional[str] = None, button: ButtonSpec = None, *,
             buttons: Optional[Iterable[ButtonSpec]] = None, badge: Optional[str] = None, image: Optional[str] = None,
             image_alt: str = "", background_image: Optional[str] = None, overlay: Optional[str] = None,
             align: str = "center", full_height: bool = False, min_height: Union[int, str, None] = None,
             **opts: Any) -> "Container":
        """Big header section. Wrap words in ``**double stars**`` to give them a gradient highlight.

        Background photo — short form::

            site.hero("Title", background_image="beach.jpg", overlay="dark")

        Full control::

            site.hero("Title", background=Background(image="beach.jpg", position="center bottom",
                                                     overlay="bottom", motion="kenburns", mobile_image="beach-m.jpg"))

        Recommended sizes: background 2400×1350 (16:9), side ``image`` 1200×900 (4:3).
        See ``webcraft.images.image_guide("hero_background")``."""
        all_buttons = [_button(button)] if button is not None else []
        for b in buttons or []:
            # Secondary buttons default to the outline style for a clear hierarchy.
            all_buttons.append(_button(b, default_style="outline" if all_buttons else None))
        if background_image is not None:
            if opts.get("background") is not None:
                raise TypeError("Use either background_image= or background=, not both")
            opts["background"] = Background(image=background_image, overlay=overlay or "dark", text="light")
        elif overlay is not None:
            raise TypeError("overlay= needs background_image= (or use Background(overlay=...))")
        return self._add("hero", {
            "title": title, "subtitle": subtitle, "buttons": all_buttons, "badge": badge, "image": image,
            "image_alt": image_alt or None, "full_height": full_height or None, "align": align,
            "min_height": f"{min_height}px" if isinstance(min_height, (int, float)) else min_height,
        }, opts)

    def section(self, title: Optional[str] = None, subtitle: Optional[str] = None, *,
                full_width: bool = False, **opts: Any) -> "Section":
        """Group components with a shared background. Use as a context manager::

            with site.section(background="#111", color="#fff") as s:
                s.heading("Inside").text("...")
        """
        sec = Section(_clean({"title": title, "subtitle": subtitle, "full_width": full_width or None, **_common(opts)}))
        self.components.append(sec.node)
        return sec

    def columns(self, count: int = 2, *, gap: Optional[int] = None, vertical_align: Optional[str] = None,
                **opts: Any) -> "Columns":
        """Side-by-side columns::

            with site.columns(2) as (left, right):
                left.image("photo.jpg")
                right.heading("About").text("...")
        """
        if count < 1:
            raise ValueError("columns() needs at least 1 column")
        cols = Columns(count, _clean({"gap": gap, "vertical_align": vertical_align, **_common(opts)}))
        self.components.append(cols.node)
        return cols

    def footer(self, text: Optional[str] = None, links: LinkSpec = None, *, logo: Optional[str] = None,
               socials: LinkSpec = None, copyright: Optional[str] = None, **opts: Any) -> "Container":
        """Page footer. ``socials`` uses the same shape as links: ``{"GitHub": "https://github.com/..."}``."""
        social_items = [{"name": s["text"], "href": s["href"], **({"icon": s["icon"]} if "icon" in s else {})}
                        for s in _links(socials)]
        return self._add("footer", {
            "text": text, "links": _links(links), "logo": logo, "socials": social_items, "copyright": copyright,
        }, opts)

    # -- content -------------------------------------------------------
    def heading(self, text: str, level: int = 2, *, subtitle: Optional[str] = None, **opts: Any) -> "Container":
        return self._add("heading", {"text": text, "level": level, "subtitle": subtitle}, opts)

    def text(self, text: str, *, size: Optional[str] = None, **opts: Any) -> "Container":
        """Paragraph text. Blank lines start new paragraphs; supports **bold**, *italic*,
        `code` and [links](https://...). ``size``: "sm", "lg" or "xl"."""
        return self._add("text", {"text": text, "size": size}, opts)

    def button(self, text: str, href: str = "#", style: str = "primary", *, new_tab: bool = False,
               icon: Optional[str] = None, **opts: Any) -> "Container":
        """``style``: primary, secondary, outline, ghost, light or link."""
        return self._add("button", {"text": text, "href": href, "style": style, "new_tab": new_tab or None,
                                    "icon": icon}, opts)

    def image(self, src: str, alt: str = "", *, caption: Optional[str] = None, width: Union[int, str, None] = None,
              height: Union[int, str, None] = None, aspect: Optional[str] = None, fit: str = "cover",
              position: Union[str, tuple, None] = None, link: Optional[str] = None, rounded: bool = True,
              shadow: bool = True, **opts: Any) -> "Container":
        """Image from a URL or a local file (local files are copied into the build automatically).

        width/height  display size in px (or any CSS length); recommended file width = 2× display width
        aspect        force a ratio, e.g. "16:9", "4:3", "1:1" (the image is cropped with ``fit="cover"``)
        fit           "cover" (fill & crop) or "contain" (show everything)
        position      which part stays visible when cropped: "top", "left center", (30, 70) ...
        link          make the image clickable
        """
        if aspect is not None and not _valid_aspect(aspect):
            raise ValueError(f"aspect must look like '16:9' (got {aspect!r})")
        if fit not in ("cover", "contain", "fill", "none", "scale-down"):
            raise ValueError("fit must be 'cover', 'contain', 'fill', 'none' or 'scale-down'")
        pos = f"{position[0]}% {position[1]}%" if isinstance(position, (tuple, list)) else position
        return self._add("image", {
            "src": src, "alt": alt, "caption": caption, "width": width, "height": height, "aspect": aspect,
            "fit": None if fit == "cover" else fit, "position": pos, "link": link,
            "rounded": None if rounded else False, "shadow": None if shadow else False,
        }, opts)

    def video(self, src: str, *, title: Optional[str] = None, subtitle: Optional[str] = None,
              poster: Optional[str] = None, **opts: Any) -> "Container":
        """YouTube / Vimeo link or a video file."""
        return self._add("video", {"src": src, "title": title, "subtitle": subtitle, "poster": poster}, opts)

    def features(self, items: Any, *, title: Optional[str] = None, subtitle: Optional[str] = None,
                 columns: int = 3, **opts: Any) -> "Container":
        """Card grid. Items: ``(icon, title, text)`` tuples or dicts with
        icon/title/text/image/link keys."""
        parsed = _items(items, ("icon", "title", "text"))
        for it in parsed:
            if "link" in it:
                it["link"] = _button(it["link"])
        return self._add("features", {"items": parsed, "title": title, "subtitle": subtitle, "columns": columns}, opts)

    cards = features

    def stats(self, items: Any, *, title: Optional[str] = None, subtitle: Optional[str] = None,
              columns: Optional[int] = None, **opts: Any) -> "Container":
        """Animated counters: ``{"10K+": "Users", "%99": "Uptime"}`` or ``[("10K+", "Users")]``."""
        parsed = [{"value": str(i["value"]), "label": str(i.get("label", ""))}
                  for i in _items(items, ("value", "label"))]
        return self._add("stats", {"items": parsed, "title": title, "subtitle": subtitle, "columns": columns}, opts)

    def gallery(self, images: Iterable[Any], *, title: Optional[str] = None, subtitle: Optional[str] = None,
                columns: int = 3, **opts: Any) -> "Container":
        """Images as paths/URLs, ``(src, caption)`` tuples or dicts."""
        parsed = _items(list(images), ("src", "caption"))
        return self._add("gallery", {"images": parsed, "title": title, "subtitle": subtitle, "columns": columns}, opts)

    def testimonials(self, items: Any, *, title: Optional[str] = None, subtitle: Optional[str] = None,
                     columns: int = 3, **opts: Any) -> "Container":
        """Items: ``(quote, name, role, avatar)`` tuples or dicts (also ``rating`` 1-5)."""
        parsed = _items(items, ("quote", "name", "role", "avatar"))
        return self._add("testimonials", {"items": parsed, "title": title, "subtitle": subtitle,
                                          "columns": columns}, opts)

    def pricing(self, plans: Iterable[Mapping[str, Any]], *, title: Optional[str] = None,
                subtitle: Optional[str] = None, **opts: Any) -> "Container":
        """Plans: dicts with name, price, period, description, features (list), button, highlight."""
        parsed = []
        for plan in plans:
            plan = dict(plan)
            if "button" in plan:
                plan["button"] = _button(plan["button"])
            parsed.append(plan)
        return self._add("pricing", {"plans": parsed, "title": title, "subtitle": subtitle}, opts)

    def faq(self, items: Any, *, title: Optional[str] = None, subtitle: Optional[str] = None,
            **opts: Any) -> "Container":
        """Accordion: ``{"Question?": "Answer"}`` or ``[("Question?", "Answer")]``."""
        return self._add("faq", {"items": _items(items, ("question", "answer")), "title": title,
                                 "subtitle": subtitle}, opts)

    def cta(self, title: str, text: Optional[str] = None, button: ButtonSpec = None, *,
            buttons: Optional[Iterable[ButtonSpec]] = None, **opts: Any) -> "Container":
        """Highlighted call-to-action banner."""
        all_buttons = ([_button(button)] if button is not None else []) + [_button(b) for b in (buttons or [])]
        return self._add("cta", {"title": title, "text": text, "buttons": all_buttons}, opts)

    def contact(self, title: Optional[str] = None, subtitle: Optional[str] = None, *, email: Optional[str] = None,
                action: Optional[str] = None, fields: Optional[Iterable[Any]] = None, button: str = "Send",
                info: Any = None, success: Optional[str] = None, **opts: Any) -> "Container":
        """Contact form. With ``email`` it opens the visitor's mail app; with ``action``
        (e.g. a Formspree URL) it POSTs the form. ``fields``: ``(name, label, type)`` tuples.
        ``info``: ``(icon, label, value)`` tuples shown beside the form."""
        parsed_fields = _items(list(fields), ("name", "label", "type")) if fields else None
        return self._add("contact", {
            "title": title, "subtitle": subtitle, "email": email, "action": action, "fields": parsed_fields,
            "button": button, "info": _items(info, ("icon", "label", "value")), "success": success,
        }, opts)

    def divider(self, **opts: Any) -> "Container":
        return self._add("divider", {}, opts)

    def spacer(self, size: Union[int, str] = 48, **opts: Any) -> "Container":
        return self._add("spacer", {"size": size}, opts)

    def html(self, raw_html: str, **opts: Any) -> "Container":
        """Insert raw HTML (not escaped — only use trusted content)."""
        return self._add("html", {"html": raw_html}, opts)

    # -- Turkish aliases (Türkçe komutlar) ------------------------------
    menu = navbar
    giris = hero
    bolum = section
    sutunlar = columns
    alt_bilgi = footer
    baslik = heading
    yazi = text
    buton = button
    resim = image
    ozellikler = features
    kartlar = features
    istatistikler = stats
    galeri = gallery
    yorumlar = testimonials
    fiyatlar = pricing
    sss = faq
    cagri = cta
    iletisim = contact
    ayrac = divider
    bosluk = spacer


class Section(Container):
    """A container rendered as one ``<section>`` with its own background."""

    def __init__(self, props: dict) -> None:
        super().__init__()
        self.node = {"type": "section", "props": props, "children": self.components}

    def __enter__(self) -> "Section":
        return self

    def __exit__(self, *exc: Any) -> None:
        return None


class Columns:
    """A row of :class:`Container` columns. Index it or unpack it in a ``with`` block."""

    def __init__(self, count: int, props: dict) -> None:
        self.cols = [Container() for _ in range(count)]
        self.node = {"type": "columns", "props": props, "columns": [c.components for c in self.cols]}

    def __getitem__(self, index: int) -> Container:
        return self.cols[index]

    def __iter__(self):
        return iter(self.cols)

    def __len__(self) -> int:
        return len(self.cols)

    def __enter__(self) -> list[Container]:
        return self.cols

    def __exit__(self, *exc: Any) -> None:
        return None
