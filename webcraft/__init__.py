"""WebCraft — build professional websites with simple Python commands.

    from webcraft import Site, ArkaPlan

    site = Site("Benim Sitem", theme="dark")
    site.arka_plan(image="manzara.jpg", overlay="dark", blur=3)
    site.yazi_tipi("Poppins")
    site.giris("Merhaba **Dünya**", "Python ile yapıldı",
               background=ArkaPlan(resim="hero.jpg", karartma="bottom", hareket="kenburns"))
    site.olustur(optimize_images=True)   # + automatic image quality report

Image size advice for every placement::

    from webcraft import image_guide, analyze_image, suggest_placement
    print(image_guide("hero_background"))
"""

from .background import ArkaPlan, Background
from .builder import ImageQualityError, SiteImageReport
from .components import Columns, Container, Section
from .images import (analyze_image, guide_table, image_guide, resim_analiz, resim_nereye, resim_rehberi,
                     suggest_placement)
from .site import THEMES, Page, Site

__version__ = "0.2.0"
__all__ = [
    "Site", "Page", "Section", "Columns", "Container", "THEMES",
    "Background", "ArkaPlan",
    "image_guide", "guide_table", "analyze_image", "suggest_placement",
    "resim_rehberi", "resim_analiz", "resim_nereye",
    "SiteImageReport", "ImageQualityError", "__version__",
]
