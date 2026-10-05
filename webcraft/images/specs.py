"""Image placement specifications ("slots").

Every place an image can appear in a WebCraft site is a *slot* with its own
recommended pixel size, aspect ratio, file-size budget and composition advice.
Numbers are tuned for the WebCraft layout (max content width 1160 css px) and
for 2x (retina) screens: an image displayed 560 css px wide needs ~1120 real px.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

Size = tuple[Optional[int], Optional[int]]


def _t(tr: str, en: str) -> dict:
    return {"tr": tr, "en": en}


@dataclass(frozen=True)
class ImageSlot:
    key: str
    name: dict
    where: dict
    recommended: Size
    minimum: Size
    aspect: Optional[tuple[int, int]]        # None = any ratio is fine
    crops: bool                              # True if CSS crops the image to `aspect` (object-fit/cover)
    max_kb: int
    formats: tuple[str, ...]
    display_width: Optional[int]             # typical rendered width in CSS px on desktop
    safe_zone: dict
    tips: dict = field(default_factory=dict)
    mobile: Optional[Size] = None            # suggested separate mobile image
    aspect_tolerance: float = 0.06
    landscape_only: bool = False
    photo: bool = True                       # photos benefit from lossy formats

    @property
    def aspect_value(self) -> Optional[float]:
        return self.aspect[0] / self.aspect[1] if self.aspect else None

    def label(self, lang: str = "tr") -> str:
        return self.name.get(lang, self.name["en"])

    def describe(self, lang: str = "tr") -> str:
        return format_slot(self, lang)


SLOTS: dict[str, ImageSlot] = {}


def _slot(**kw) -> None:
    slot = ImageSlot(**kw)
    SLOTS[slot.key] = slot


_slot(
    key="page_background",
    name=_t("Sayfa arka planı", "Page background"),
    where=_t("site.arka_plan(image=...) — tüm sayfanın arkasında sabit durur",
             "site.background(image=...) — fixed behind the whole page"),
    recommended=(2560, 1440), minimum=(1920, 1080), aspect=(16, 9), crops=True, max_kb=450,
    formats=("avif", "webp", "jpeg"), display_width=1920, mobile=(1080, 1920), landscape_only=True,
    safe_zone=_t("Ana konuyu ortadaki %50'lik alanda tutun; ekran oranına göre kenarlar kırpılır. "
                 "Üstüne yazı geleceği için sade, düşük detaylı ve düşük kontrastlı görseller seçin.",
                 "Keep the subject inside the central 50%; edges are cropped depending on the screen. "
                 "Text sits on top, so prefer calm, low-detail, low-contrast images."),
    tips=_t("Okunabilirlik için overlay='dark' veya blur=2-6 kullanın. Mobilde ayrı dikey görsel (mobile_image) verin.",
            "Use overlay='dark' or blur=2-6 for readability. Provide a portrait mobile_image for phones."),
)
_slot(
    key="hero_background",
    name=_t("Giriş (hero) arka planı", "Hero background"),
    where=_t("site.giris(background=ArkaPlan(image=...)) — ilk ekranı kaplayan görsel",
             "site.hero(background=Background(image=...)) — the first full-width screen"),
    recommended=(2400, 1350), minimum=(1600, 900), aspect=(16, 9), crops=True, max_kb=400,
    formats=("avif", "webp", "jpeg"), display_width=1920, mobile=(1080, 1350), landscape_only=True,
    safe_zone=_t("Başlık ortada duracağı için konuyu sol/sağ üçte birlik alana ya da alt kısma koyun; "
                 "yüzler ve ürünler merkezdeki %60'lık alanın içinde kalsın (mobilde kenarlar kesilir).",
                 "The headline sits in the middle: place the subject on the left/right third or bottom, "
                 "and keep faces/products inside the central 60% (edges are cut on phones)."),
    tips=_t("full_height=True ise 16:9 yerine 2560×1440 kullanın. Koyu overlay ile beyaz yazı en okunur.",
            "With full_height=True use 2560×1440. A dark overlay with white text reads best."),
)
_slot(
    key="hero_image",
    name=_t("Giriş yan görseli", "Hero side image"),
    where=_t("site.giris(..., image=...) — başlığın yanında duran görsel/mockup",
             "site.hero(..., image=...) — picture/mockup next to the headline"),
    recommended=(1200, 900), minimum=(800, 600), aspect=(4, 3), crops=False, max_kb=250,
    formats=("webp", "avif", "png", "jpeg"), display_width=560, aspect_tolerance=0.25,
    safe_zone=_t("Görsel kırpılmaz; tamamı görünür. Ürün ekran görüntüsü veya şeffaf PNG/WebP mockup idealdir.",
                 "Not cropped; shown in full. Product screenshots or transparent PNG/WebP mockups work best."),
    tips=_t("Şeffaf arka planlı görseller için WebP (alpha) PNG'den ~%70 daha küçüktür.",
            "For transparent images WebP (alpha) is ~70% smaller than PNG."),
)
_slot(
    key="section_background",
    name=_t("Bölüm arka planı", "Section background"),
    where=_t("site.bolum(background=ArkaPlan(image=...)) veya herhangi bir bileşenin background'u",
             "site.section(background=Background(image=...)) or any component background"),
    recommended=(1920, 800), minimum=(1440, 600), aspect=(12, 5), crops=True, max_kb=300,
    formats=("avif", "webp", "jpeg"), display_width=1920, mobile=(1080, 1080), aspect_tolerance=0.2,
    landscape_only=True,
    safe_zone=_t("Bölüm yüksekliği içeriğe göre değişir; üst-alttan kırpılabilir. Konuyu dikey olarak ortada tutun. "
                 "Doku, gradyan veya bulanık fotoğraflar en iyi sonucu verir.",
                 "Section height follows its content, so top/bottom may be cropped. Keep the subject vertically "
                 "centred. Textures, gradients or blurred photos work best."),
    tips=_t("fixed=True ile parallax hissi verir; mobilde otomatik olarak normal kaydırmaya döner.",
            "fixed=True gives a parallax feel; phones automatically fall back to normal scrolling."),
)
_slot(
    key="mobile_background",
    name=_t("Mobil arka plan", "Mobile background"),
    where=_t("ArkaPlan(mobile_image=...) — 768 px altındaki ekranlarda kullanılır",
             "Background(mobile_image=...) — used on screens narrower than 768 px"),
    recommended=(1080, 1920), minimum=(750, 1334), aspect=(9, 16), crops=True, max_kb=250,
    formats=("avif", "webp", "jpeg"), display_width=430, aspect_tolerance=0.2,
    safe_zone=_t("Dikey çekim kullanın; konu ekranın ortasında ve üst %20'den aşağıda olsun (üstte menü var).",
                 "Use a portrait shot; keep the subject centred and below the top 20% (the menu sits there)."),
)
_slot(
    key="content_image",
    name=_t("İçerik görseli", "Content image"),
    where=_t("site.resim(...) — sayfa genişliğinde tek görsel", "site.image(...) — single full-width image"),
    recommended=(1920, 1080), minimum=(1100, 620), aspect=(16, 9), crops=False, max_kb=300,
    formats=("avif", "webp", "jpeg", "png"), display_width=1112, aspect_tolerance=0.35,
    safe_zone=_t("Kırpılmaz; olduğu gibi gösterilir. width= verirseniz önerilen boyut onun 2 katıdır.",
                 "Not cropped; shown as-is. If you pass width=, the recommendation becomes 2× that width."),
    tips=_t("aspect='16:9' ve fit='cover' ile farklı oranlı görselleri aynı yüksekliğe getirebilirsiniz.",
            "Use aspect='16:9' with fit='cover' to make mixed images the same height."),
)
_slot(
    key="column_image",
    name=_t("Sütun görseli", "Column image"),
    where=_t("site.sutunlar(2) içinde resim — yazının yanında", "image inside site.columns(2) — beside text"),
    recommended=(1200, 900), minimum=(800, 600), aspect=(4, 3), crops=False, max_kb=200,
    formats=("avif", "webp", "jpeg"), display_width=532, aspect_tolerance=0.3,
    safe_zone=_t("Yazıyla yan yana durduğu için 4:3 veya 1:1 oran dengeli görünür; dikey görseller sütunu uzatır.",
                 "Next to text, 4:3 or 1:1 look balanced; portrait images make the column tall."),
)
_slot(
    key="card_image",
    name=_t("Kart görseli", "Card image"),
    where=_t("site.kartlar([{'image': ...}]) — kartın üstü, 16:9'a kırpılır",
             "site.features([{'image': ...}]) — top of a card, cropped to 16:9"),
    recommended=(800, 450), minimum=(640, 360), aspect=(16, 9), crops=True, max_kb=120,
    formats=("avif", "webp", "jpeg"), display_width=360,
    safe_zone=_t("Kart küçük: tek ve net bir konu seçin, konuyu ortada tutun; yazı içeren görsellerden kaçının.",
                 "Cards are small: one clear subject, centred; avoid images containing text."),
)
_slot(
    key="gallery",
    name=_t("Galeri görseli", "Gallery image"),
    where=_t("site.galeri([...]) — 4:3'e kırpılır, tıklanınca tam boyut açılır",
             "site.gallery([...]) — cropped to 4:3, full size opens on click"),
    recommended=(1200, 900), minimum=(800, 600), aspect=(4, 3), crops=True, max_kb=220,
    formats=("avif", "webp", "jpeg"), display_width=370,
    safe_zone=_t("Tüm galeri görsellerini aynı oranda çekin/kırpın; konu ortada olsun.",
                 "Shoot/crop all gallery images at the same ratio; keep the subject centred."),
)
_slot(
    key="avatar",
    name=_t("Profil fotoğrafı", "Avatar"),
    where=_t("site.yorumlar([(..., avatar)]) — 46 px yuvarlak", "site.testimonials([(..., avatar)]) — 46 px circle"),
    recommended=(256, 256), minimum=(96, 96), aspect=(1, 1), crops=True, max_kb=40,
    formats=("webp", "jpeg"), display_width=46,
    safe_zone=_t("Yüz ortada ve karenin ~%60'ını kaplasın; daire şeklinde kırpılır.",
                 "Face centred, filling ~60% of the square; it is cropped to a circle."),
)
_slot(
    key="logo",
    name=_t("Logo", "Logo"),
    where=_t("site.menu(logo_image=...) — menüde 34 px yükseklik", "site.navbar(logo_image=...) — 34 px tall"),
    recommended=(None, 102), minimum=(None, 68), aspect=None, crops=False, max_kb=30,
    formats=("svg", "webp", "png"), display_width=None, photo=False,
    safe_zone=_t("Kenarlarda boş alan bırakmayın (kırpın); şeffaf arka plan kullanın. Yatay logolar menüde en iyi durur.",
                 "Trim empty margins; use a transparent background. Horizontal logos fit the navbar best."),
    tips=_t("SVG her ekranda keskin kalır ve genellikle 5 KB altındadır.", "SVG stays sharp everywhere, usually < 5 KB."),
)
_slot(
    key="favicon",
    name=_t("Site ikonu (favicon)", "Favicon"),
    where=_t("Site(favicon=...) — tarayıcı sekmesi ve ana ekran ikonu", "Site(favicon=...) — browser tab & home screen"),
    recommended=(512, 512), minimum=(180, 180), aspect=(1, 1), crops=False, max_kb=50,
    formats=("svg", "png", "ico"), display_width=32, photo=False, aspect_tolerance=0.02,
    safe_zone=_t("Basit bir sembol kullanın; 16 px'te de tanınabilir olmalı. Yazı koymayın.",
                 "Use a simple symbol that is recognisable at 16 px. No text."),
)
_slot(
    key="og_image",
    name=_t("Paylaşım görseli (Open Graph)", "Social share image (Open Graph)"),
    where=_t("Site(og_image=...) — WhatsApp, X, LinkedIn, Facebook önizlemesi",
             "Site(og_image=...) — WhatsApp, X, LinkedIn, Facebook previews"),
    recommended=(1200, 630), minimum=(600, 315), aspect=(40, 21), crops=True, max_kb=300,
    formats=("jpeg", "png", "webp"), display_width=600, aspect_tolerance=0.03,
    safe_zone=_t("Önemli yazı ve logoyu ortadaki 1000×520 alana koyun; bazı platformlar kenarları ve kareye kırpar.",
                 "Put key text/logo inside the central 1000×520 area; some platforms crop edges or to a square."),
    tips=_t("WhatsApp 300 KB üstünü göstermeyebilir; JPEG kalite 80-85 idealdir.",
            "WhatsApp may skip images over 300 KB; JPEG quality 80-85 is ideal."),
)
_slot(
    key="video_poster",
    name=_t("Video kapak görseli", "Video poster"),
    where=_t("site.video(..., poster=...) — video oynatılmadan önce", "site.video(..., poster=...) — shown before playback"),
    recommended=(1920, 1080), minimum=(1280, 720), aspect=(16, 9), crops=True, max_kb=250,
    formats=("avif", "webp", "jpeg"), display_width=1112,
    safe_zone=_t("Ortaya oynat düğmesi gelir; yüzleri tam merkeze koymayın.",
                 "A play button sits in the centre; don't put faces exactly there."),
)

ALIASES = {
    # Turkish & short names -> slot keys
    "arka_plan": "page_background", "sayfa": "page_background", "background": "page_background",
    "giris": "hero_background", "hero": "hero_background", "giris_gorseli": "hero_image",
    "bolum": "section_background", "section": "section_background",
    "mobil": "mobile_background", "mobile": "mobile_background",
    "icerik": "content_image", "resim": "content_image", "image": "content_image",
    "sutun": "column_image", "column": "column_image",
    "kart": "card_image", "card": "card_image", "galeri": "gallery",
    "profil": "avatar", "ikon": "favicon", "paylasim": "og_image", "og": "og_image", "poster": "video_poster",
}


def get_slot(key: str) -> ImageSlot:
    k = key.strip().lower().replace("-", "_").replace(" ", "_")
    k = ALIASES.get(k, k)
    if k not in SLOTS:
        raise KeyError(f"Unknown image slot {key!r}. Available: {', '.join(SLOTS)}")
    return SLOTS[k]


def ratio_text(aspect: Optional[tuple[int, int]]) -> str:
    if not aspect:
        return "serbest / any"
    if aspect == (40, 21):
        return "1.91:1"
    return f"{aspect[0]}:{aspect[1]}"


def size_text(size: Size) -> str:
    w, h = size
    if w and h:
        return f"{w}×{h} px"
    if h:
        return f"↕ {h} px"
    return f"↔ {w} px"


def format_slot(slot: ImageSlot, lang: str = "tr") -> str:
    tr = lang == "tr"
    lines = [
        f"▸ {slot.label(lang)}  [{slot.key}]",
        f"  {'Nerede' if tr else 'Where'}:      {slot.where.get(lang, slot.where['en'])}",
        f"  {'Önerilen' if tr else 'Recommended'}:   {size_text(slot.recommended)}",
        f"  {'En az' if tr else 'Minimum'}:      {size_text(slot.minimum)}",
        f"  {'Oran' if tr else 'Aspect'}:       {ratio_text(slot.aspect)}"
        + ((" (kırpılır)" if tr else " (cropped)") if slot.crops and slot.aspect else ""),
        f"  {'Dosya' if tr else 'File size'}:      ≤ {slot.max_kb} KB  ·  {', '.join(f.upper() for f in slot.formats)}",
    ]
    if slot.mobile:
        lines.append(f"  {'Mobil' if tr else 'Mobile'}:      {size_text(slot.mobile)}")
    lines.append(f"  {'Kompozisyon' if tr else 'Composition'}: {slot.safe_zone.get(lang, slot.safe_zone['en'])}")
    if slot.tips:
        lines.append(f"  {'İpucu' if tr else 'Tip'}:        {slot.tips.get(lang, slot.tips['en'])}")
    return "\n".join(lines)


def image_guide(slot: Optional[str] = None, lang: str = "tr") -> str:
    """Human readable size guide for one slot, or for all of them."""
    if slot:
        return format_slot(get_slot(slot), lang)
    title = "WebCraft görsel boyut rehberi" if lang == "tr" else "WebCraft image size guide"
    return f"{title}\n{'=' * len(title)}\n\n" + "\n\n".join(format_slot(s, lang) for s in SLOTS.values())


def guide_table(lang: str = "tr") -> str:
    """Compact Markdown table of all slots."""
    tr = lang == "tr"
    head = ("| Alan | Önerilen | En az | Oran | Maks. dosya |" if tr
            else "| Slot | Recommended | Minimum | Aspect | Max file |")
    rows = [head, "|---|---|---|---|---|"]
    for s in SLOTS.values():
        rows.append(f"| {s.label(lang)} (`{s.key}`) | {size_text(s.recommended)} | {size_text(s.minimum)} | "
                    f"{ratio_text(s.aspect)} | {s.max_kb} KB |")
    return "\n".join(rows)
