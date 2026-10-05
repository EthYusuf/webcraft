"""Arka plan vitrini — tüm arka plan seçenekleri tek sayfada.

Çalıştır:  python examples/backgrounds.py
Kendi görsellerinizi kullanırken URL yerine dosya yolu verin ("img/dag.jpg");
derleme sırasında her görsel kullanıldığı alana göre kontrol edilir ve rapor basılır.
"""

from webcraft import ArkaPlan, Background, Site

UNSPLASH = "https://images.unsplash.com/{}?auto=format&fit=crop&w={}&q=80"
DAG = UNSPLASH.format("photo-1506905925346-21bda4d32df4", 2400)          # yatay dağ manzarası
DAG_MOBIL = UNSPLASH.format("photo-1464822759023-fed622ff2c3b", 1080)    # dikey (mobil için)
SEHIR = UNSPLASH.format("photo-1477959858617-67f85cf4f1df", 1920)
DOKU = UNSPLASH.format("photo-1557683316-973673baf926", 1920)            # gradyan doku
OFIS = UNSPLASH.format("photo-1497366216548-37526070297c", 1920)

site = Site("Arka Plan Vitrini", theme="dark", description="WebCraft arka plan seçenekleri")
site.yazi_tipi("Inter", heading="Space Grotesk")

# Tüm sayfanın arkasında sabit, hafif bulanık bir görsel (önerilen 2560×1440, 16:9)
site.arka_plan(image=SEHIR, overlay="darker", blur=6, brightness=0.8, color="#0b1120")

site.menu("✦ Vitrin", {"Ken Burns": "#kenburns", "Parallax": "#parallax", "Mobil": "#mobil"})

# 1) Hero: yavaş yakınlaşma (Ken Burns), alttan karartma, mobilde ayrı dikey görsel
site.giris(
    "Arka planlar **sinematik** olabilir",
    "Ken Burns efekti · alttan karartma · mobilde dikey görsel",
    button=("Keşfet", "#parallax"),
    background=ArkaPlan(
        resim=DAG,                 # 2400×1350 önerilir
        mobil_resim=DAG_MOBIL,     # 1080×1920 önerilir
        konum="orta alt",          # görselin hangi kısmı görünsün
        karartma="bottom",         # dark | darker | light | top | bottom | vignette | primary | brand
        hareket="kenburns",
        yazi="light",
    ),
    full_height=True, id="kenburns",
)

# 2) Parallax: kaydırırken arka plan daha yavaş hareket eder
with site.bolum("Parallax bölüm", "Arka plan, içerikten daha yavaş kayar",
                background=Background(image=OFIS, motion="parallax", parallax_speed=0.4,
                                      overlay="vignette", text="light"),
                padding=140, id="parallax") as b:
    b.yazi("Bölüm arka planları için önerilen boyut **1920×800 px** (12:5).", align="center", size="lg")

# 3) Marka renginde kaplama + siyah-beyaz fotoğraf
with site.bolum("Marka kaplaması", "grayscale=1 + overlay='brand'",
                background=Background(image=SEHIR, grayscale=1, overlay="brand", text="light"),
                padding=120) as b:
    b.istatistikler({"2560px": "Sayfa arka planı", "2400px": "Hero", "1920px": "Bölüm", "1080px": "Mobil"})

# 4) Sabit (fixed) arka plan + açık kaplama ve koyu yazı
with site.bolum("Sabit arka plan", "fixed=True — mobilde otomatik normal kaydırma",
                background=Background(image=DOKU, fixed=True, overlay="light", text="dark"),
                padding=120, id="mobil") as b:
    b.yazi("Açık kaplama (overlay='light') ile koyu yazı da okunur kalır.", align="center")

# 5) Görsel bileşeni: oran zorlama, odak noktası, link
with site.sutunlar(2) as (sol, sag):
    sol.resim(DAG, "Dağ", aspect="1:1", position="bottom", caption="aspect='1:1', position='bottom'")
    sag.baslik("Görsel kontrolü", subtitle="Oran, odak ve boyut")
    sag.yazi("`aspect` görseli istediğiniz orana kırpar, `position` hangi kısmın görüneceğini seçer.\n\n"
             "Derlerken `optimize_images=True` verirseniz görseller bu orana göre gerçekten kırpılır, "
             "WebP'ye çevrilir ve her ekran için ayrı boyutlar (srcset) üretilir.")

site.alt_bilgi("WebCraft arka plan vitrini", copyright="© 2026")

if __name__ == "__main__":
    site.olustur("examples/dist/backgrounds")
    print("Built -> examples/dist/backgrounds/index.html")
