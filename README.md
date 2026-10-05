# ✦ WebCraft

**Basit Python komutlarıyla profesyonel web siteleri yapın.**
*Build professional websites with simple Python commands.*

WebCraft iki katmandan oluşur:

| Katman | Görev |
|---|---|
| **WebCraft.js** (`webcraft/static/webcraft.js` + `.css`) | Tarayıcıda çalışan bileşen kütüphanesi: menü, hero, kartlar, fiyat tablosu, SSS, form… Tema motoru, Google Fonts yükleme, kaydırma animasyonları, sayaçlar, mobil menü. |
| **webcraft** (Python) | Siteyi basit komutlarla tanımlar (`arka_plan`, `yazi_tipi`, `baslik`…), JSON'a çevirir ve statik HTML üretir. |

```
Python komutları  ──►  JSON spec  ──►  index.html + WebCraft.js  ──►  tarayıcıda render
```

Bağımlılık yok: sadece Python 3.9+ standart kütüphanesi.

---

## Kurulum

```bash
git clone https://github.com/EthYusuf/webcraft.git
cd webcraft
pip install -e .
```

## 30 saniyede ilk site

```python
from webcraft import Site

site = Site("Benim Sitem")
site.arka_plan("#0f172a")          # arka plan rengi (veya gradient / resim)
site.yazi_tipi("Poppins")          # herhangi bir Google Font
site.yazi_rengi("#e2e8f0")         # yazı rengi
site.ana_renk("#6366f1")           # buton ve link rengi

site.menu("Logo", {"Ana Sayfa": "#", "İletişim": "#iletisim"})
site.giris("Merhaba **Dünya**", "Python ile yapılmış bir site", button=("Başla", "#"))
site.yazi("Bu bir **paragraf**. [Link](https://github.com) de olabilir.")
site.alt_bilgi("© 2026 Benim Sitem")

site.yayinla()      # derle + http://localhost:8000 aç
# site.olustur()    # sadece dist/ klasörüne derle
# site.onizle()     # derle + dosyayı tarayıcıda aç
```

> `**kalın**`, `*italik*`, `` `kod` `` ve `[link](url)` tüm yazılarda çalışır. Hero başlığında `**...**` gradyan vurgu olur.

## Stil komutları

| Türkçe | English | Örnek |
|---|---|---|
| `tema` | `theme` | `site.tema("dark")` — `light, dark, ocean, sunset, forest, midnight, minimal` |
| `arka_plan` | `background` | `site.arka_plan("linear-gradient(135deg,#667eea,#764ba2)")` / `site.arka_plan(image="bg.jpg", overlay="rgba(0,0,0,.5)")` |
| `yazi_tipi` | `font` | `site.yazi_tipi("Inter", heading="Playfair Display", size=18)` |
| `renkler` | `colors` | `site.renkler(primary="#e11d48", secondary="#f59e0b", text="#111")` |
| `yazi_rengi` | `text_color` | `site.yazi_rengi("#222")` |
| `ana_renk` | `primary_color` | `site.ana_renk("#16a34a")` |
| `kose` | `radius` | `site.kose(0)` — keskin köşeler |
| `genislik` | `width` | `site.genislik(1280)` |

Tüm komutlar zincirlenebilir: `site.tema("dark").yazi_tipi("Poppins").ana_renk("#f43f5e")`

## Bileşenler

| Türkçe | English | Ne yapar |
|---|---|---|
| `menu` | `navbar` | Yapışkan menü, mobilde hamburger |
| `giris` | `hero` | Büyük başlık alanı (rozet, butonlar, yan görsel veya arka plan fotoğrafı) |
| `baslik` / `yazi` / `buton` | `heading` / `text` / `button` | Temel içerik |
| `resim` / — | `image` / `video` | Görsel (yerel dosyalar otomatik kopyalanır), YouTube/Vimeo |
| `ozellikler` / `kartlar` | `features` / `cards` | İkonlu kart ızgarası |
| `istatistikler` | `stats` | Sayarak artan sayaçlar |
| `galeri` | `gallery` | Görsel ızgarası |
| `yorumlar` | `testimonials` | Müşteri yorumları |
| `fiyatlar` | `pricing` | Fiyat tablosu |
| `sss` | `faq` | Açılır soru-cevap |
| `cagri` | `cta` | Renkli çağrı bandı |
| `iletisim` | `contact` | İletişim formu (mailto veya Formspree `action=`) |
| `bolum` | `section` | Kendi arka planı olan grup (`with` ile) |
| `sutunlar` | `columns` | Yan yana sütunlar (`with` ile) |
| `ayrac` / `bosluk` | `divider` / `spacer` | Boşluk düzenleme |
| — | `html` | Ham HTML |
| `alt_bilgi` | `footer` | Alt bilgi, linkler, sosyal medya |

Her bileşen ortak seçenekleri kabul eder: `id`, `background`, `color`, `padding`, `align`, `animate` (`fade-up`, `fade-left`, `zoom`, `False`…), `class_`, `style`.

```python
with site.bolum(background="#111827", color="#fff", padding=100) as b:
    b.baslik("Koyu bölüm", align="center")
    b.yazi("İçerik...", align="center")

with site.sutunlar(2) as (sol, sag):
    sol.resim("foto.jpg")
    sag.baslik("Hakkımızda").yazi("...")

hakkinda = site.sayfa("hakkinda", title="Hakkımızda")   # -> hakkinda.html
hakkinda.menu("Logo", {"Ana Sayfa": "index.html"}).baslik("Hakkımızda", level=1)
```

## Komut satırı

```bash
webcraft new projem          # projem/site.py başlangıç şablonu
webcraft build projem/site.py  # -> projem/dist/
webcraft build site.py --inline   # her sayfa tek dosya (CSS+JS gömülü)
webcraft serve site.py -p 8080
```

(`webcraft` komutu PATH'te değilse `python -m webcraft ...` kullanın.)

## WebCraft.js'i doğrudan JavaScript ile kullanmak

```html
<link rel="stylesheet" href="webcraft.css">
<div id="app"></div>
<script src="webcraft.js"></script>
<script>
  WebCraft.site("JS Sitesi")
    .theme("ocean").font("Poppins")
    .hero({ title: "Merhaba **JS**", buttons: [{ text: "Başla", href: "#" }] })
    .features({ items: [{ icon: "⚡", title: "Hızlı", text: "..." }] })
    .mount("#app");

  // Kendi bileşenini ekle — Python'dan site.add("rozet", {...}) ile kullanılabilir
  WebCraft.register("rozet", (p) => WebCraft.utils.h("div", { class: "wc-badge" }, p.text));
</script>
```

## Örnekler

```bash
python examples/minimal.py    # 10 satırlık site
python examples/landing.py    # tam bir ajans açılış sayfası
```

## Geliştirme

```bash
pip install -e . pytest
pytest
```

## Lisans

MIT
