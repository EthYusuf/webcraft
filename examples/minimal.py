"""The smallest possible site — run:  python examples/minimal.py"""

from webcraft import Site

site = Site("Merhaba")
site.arka_plan("#fef3c7")          # arka plan rengi
site.yazi_tipi("Playfair Display")  # font
site.yazi_rengi("#78350f")          # yazı rengi
site.ana_renk("#d97706")            # buton / link rengi

site.baslik("Merhaba Dünya!", level=1, align="center")
site.yazi("Bu site **sadece birkaç satır** Python ile yapıldı.", align="center", size="lg")
site.buton("GitHub", "https://github.com/EthYusuf/webcraft", align="center", new_tab=True)

if __name__ == "__main__":
    site.olustur("examples/dist/minimal", inline=True)  # tek dosyalık HTML
    print("Built -> examples/dist/minimal/index.html")
