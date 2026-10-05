"""WebCraft — build professional websites with simple Python commands.

    from webcraft import Site

    site = Site("Benim Sitem", theme="dark")
    site.arka_plan("#0b1120").yazi_tipi("Poppins")
    site.giris("Merhaba **Dünya**", "Python ile yapıldı")
    site.olustur()
"""

from .components import Columns, Container, Section
from .site import THEMES, Page, Site

__version__ = "0.1.0"
__all__ = ["Site", "Page", "Section", "Columns", "Container", "THEMES", "__version__"]
