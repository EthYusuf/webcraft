"""Layered backgrounds: colour, gradient, image, overlay, filters, motion.

    from webcraft import Background

    Background(
        image="mountains.jpg",        # local file or URL
        size="cover",                 # cover | contain | auto | 1200 (px) | "50%"
        position="center top",        # or (30, 70) = 30% from left, 70% from top
        overlay="dark",               # dark | darker | light | top | bottom | vignette | primary | brand | any CSS
        blur=4, brightness=0.9,       # CSS filters applied to the image only, never to the text
        fixed=True,                   # parallax-like fixed background (auto-disabled on phones)
        mobile_image="mountains-portrait.jpg",
        motion="kenburns",            # kenburns (slow zoom) | parallax (scroll effect)
    )

Turkish: ``ArkaPlan(resim=..., boyut=..., konum=..., karartma=..., bulaniklik=..., sabit=True, ...)``
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional, Union

OVERLAY_PRESETS = ("dark", "darker", "light", "top", "bottom", "vignette", "primary", "brand")
MOTIONS = ("parallax", "kenburns")
_SIZE_KEYWORDS = ("cover", "contain", "auto")
_POSITION_WORDS = {
    "orta": "center", "merkez": "center", "ust": "top", "üst": "top", "alt": "bottom",
    "sol": "left", "sag": "right", "sağ": "right",
}

Number = Union[int, float]


def _css_size(value: Union[str, Number, None]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return f"{value}px"
    v = str(value).strip()
    tr = {"kapla": "cover", "sigdir": "contain", "sığdır": "contain", "otomatik": "auto"}
    return tr.get(v.lower(), v)


def _css_position(value: Union[str, tuple, list, None]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (tuple, list)):
        if len(value) != 2:
            raise ValueError("position tuple must be (x%, y%)")
        return f"{value[0]}% {value[1]}%"
    words = [_POSITION_WORDS.get(w.lower(), w) for w in str(value).replace("-", " ").split()]
    return " ".join(words)


def _check_range(name: str, value: Optional[Number], lo: float, hi: float) -> None:
    if value is not None and not (lo <= value <= hi):
        raise ValueError(f"{name} must be between {lo} and {hi} (got {value})")


@dataclass
class Background:
    image: Optional[str] = None
    color: Optional[str] = None
    gradient: Optional[str] = None
    size: Union[str, Number, None] = "cover"
    position: Union[str, tuple, None] = "center"
    repeat: Union[bool, str] = False
    fixed: bool = False
    overlay: Optional[str] = None
    overlay_opacity: Optional[float] = None
    blur: Optional[Number] = None
    brightness: Optional[float] = None
    contrast: Optional[float] = None
    saturate: Optional[float] = None
    grayscale: Optional[float] = None
    mobile_image: Optional[str] = None
    mobile_position: Union[str, tuple, None] = None
    min_height: Union[str, Number, None] = None
    motion: Optional[str] = None
    parallax_speed: float = 0.35
    text: Optional[str] = None            # "light" | "dark" | any CSS colour for text on this background
    focus: Union[str, tuple, None] = None  # crop focus used by optimize_images (defaults to position)
    alt: Optional[str] = None             # description for screen readers (backgrounds are decorative by default)

    def __post_init__(self) -> None:
        if not (self.image or self.color or self.gradient):
            raise ValueError("Background needs at least one of image, color or gradient")
        if self.motion is not None and self.motion not in MOTIONS:
            raise ValueError(f"motion must be one of {MOTIONS}")
        _check_range("overlay_opacity", self.overlay_opacity, 0, 1)
        _check_range("blur", self.blur, 0, 60)
        for name in ("brightness", "contrast", "saturate"):
            _check_range(name, getattr(self, name), 0, 3)
        _check_range("grayscale", self.grayscale, 0, 1)
        _check_range("parallax_speed", self.parallax_speed, -1, 1)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["size"] = _css_size(self.size)
        data["position"] = _css_position(self.position)
        data["mobile_position"] = _css_position(self.mobile_position)
        data["min_height"] = _css_size(self.min_height)
        if isinstance(self.repeat, bool):
            data["repeat"] = "repeat" if self.repeat else None
        if self.focus is None:
            data["focus"] = None
        elif isinstance(self.focus, (tuple, list)):
            data["focus"] = list(self.focus)
        if self.parallax_speed == 0.35:
            data["parallax_speed"] = None
        if not self.fixed:
            data["fixed"] = None
        return {k: v for k, v in data.items() if v is not None}

    # Pretty name in reprs/errors
    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"Background({', '.join(f'{k}={v!r}' for k, v in self.to_dict().items())})"


_TR_KEYS = {
    "resim": "image", "gorsel": "image", "görsel": "image", "renk": "color", "gradyan": "gradient",
    "boyut": "size", "konum": "position", "tekrar": "repeat", "sabit": "fixed",
    "karartma": "overlay", "kaplama": "overlay", "karartma_opaklik": "overlay_opacity", "opaklik": "overlay_opacity",
    "bulaniklik": "blur", "bulanıklık": "blur", "parlaklik": "brightness", "parlaklık": "brightness",
    "kontrast": "contrast", "doygunluk": "saturate", "siyah_beyaz": "grayscale",
    "mobil_resim": "mobile_image", "mobil_konum": "mobile_position", "min_yukseklik": "min_height",
    "hareket": "motion", "parallax_hiz": "parallax_speed", "yazi": "text", "yazı": "text",
    "odak": "focus", "aciklama": "alt",
}


def ArkaPlan(**kwargs: Any) -> Background:  # noqa: N802 - reads like a class for Turkish users
    """Türkçe parametrelerle :class:`Background`:

    ArkaPlan(resim="dag.jpg", konum="orta ust", karartma="dark", bulaniklik=3, sabit=True)
    """
    return Background(**{_TR_KEYS.get(k, k): v for k, v in kwargs.items()})


def normalize_background(value: Any) -> Any:
    """Accept a CSS string, a :class:`Background`, or a dict -> JSON-ready value."""
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, Background):
        return value.to_dict()
    if isinstance(value, dict):
        return Background(**{_TR_KEYS.get(k, k): v for k, v in value.items()}).to_dict()
    raise TypeError(f"background must be a CSS string, Background or dict, not {type(value).__name__}")
