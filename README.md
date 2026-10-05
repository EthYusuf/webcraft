# ✦ WebCraft

**Basit Python komutlarıyla profesyonel web siteleri yapın.**
*Build professional websites with simple Python commands.*

WebCraft iki katmandan oluşur:

| Katman | Görev |
|---|---|
| **WebCraft.js** (`webcraft/static/webcraft.js` + `.css`) | Tarayıcıda çalışan bileşen kütüphanesi: menü, hero, kartlar, fiyat tablosu, SSS, form… Tema motoru, Google Fonts yükleme, kaydırma animasyonları, sayaçlar, mobil menü. |
| **webcraft** (Python) | Siteyi basit komutlarla tanımlar (`arka_plan`, `yazi_tipi`, `baslik`…), görselleri kontrol/optimize eder, JSON'a çevirir ve statik HTML üretir. |

### Nasıl çalışır?

```
 site.py (Python)                 dist/ (statik dosyalar)                 Tarayıcı
 ─────────────────                ───────────────────────                ─────────
 site.giris(...)      build()     index.html                              WebCraft.js
 site.kartlar(...)  ─────────►    ├─ <script type=application/json>  ──►  JSON'u okur,
 site.arka_plan(...)              │    { tema, bileşenler }               DOM'u kurar,
                                  ├─ assets/webcraft.js / .css            tema + animasyon +
   görsel analizi ✓               └─ assets/media/*.webp                  parallax uygular
```

- **Python** siteyi *tarif eder*: hangi bileşenler, hangi sırada, hangi renk/font/görsellerle. Bu tarifi JSON olarak HTML'in içine gömer, görselleri kontrol edip kopyalar/optimize eder.
- **JavaScript (WebCraft.js)** sayfa açıldığında bu JSON'u okuyup sayfayı **tarayıcıda kurar**: HTML elemanlarını oluşturur, temayı (CSS değişkenleri) uygular, fontları yükler, kaydırma animasyonlarını, sayaçları, parallax/Ken Burns efektlerini ve mobil menüyü çalıştırır, ekrana uygun görsel boyutunu seçer.
- Sonuç tamamen **statik**: sunucuda Python çalışmaz. `dist/` klasörünü GitHub Pages, Netlify, Vercel gibi her yere yükleyebilirsiniz.

Bağımlılık yok: sadece Python 3.9+ standart kütüphanesi. Görsel optimizasyonu için isteğe bağlı Pillow (`pip install -e .[images]`).

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

## Arka planlar

Arka plan; düz renk, gradyan veya **fotoğraf** olabilir. Fotoğraf ve karartma ayrı katmanlarda çizilir; bulanıklık gibi filtreler yazıyı asla etkilemez.

```python
from webcraft import Site, ArkaPlan, Background

site.arka_plan("#0b1120")                                         # renk
site.arka_plan("linear-gradient(135deg, #667eea, #764ba2)")       # gradyan
site.arka_plan(image="sehir.jpg", overlay="dark", blur=4)         # tüm sayfa (sabit durur)

# Hero / bölüm / herhangi bir bileşen:
site.giris("Başlık", background=ArkaPlan(
    resim="dag.jpg",              # dosya yolu veya URL
    mobil_resim="dag-dikey.jpg",  # 768 px altı ekranlarda bu kullanılır
    konum="orta alt",             # görselin hangi kısmı görünsün  (veya (30, 70) = %30 soldan, %70 üstten)
    boyut="kapla",                # kapla (cover) | sigdir (contain) | 1200 (px) | "50%"
    karartma="bottom",            # dark darker light top bottom vignette primary brand  veya CSS
    bulaniklik=3, parlaklik=0.9,  # filtreler: blur, brightness, contrast, saturate, grayscale
    hareket="kenburns",           # kenburns (yavaş yakınlaşma) | parallax (kaydırma efekti)
    yazi="light",                 # üstteki yazıyı açık renk yap
))

with site.bolum("Başlık", background=Background(image="ofis.jpg", motion="parallax", overlay="vignette",
                                                 text="light"), padding=140) as b:
    b.yazi("...")
```

| Seçenek | Türkçe | Değerler |
|---|---|---|
| `image` | `resim` | dosya yolu / URL |
| `mobile_image` | `mobil_resim` | dikey görsel (1080×1920 önerilir) |
| `position` / `mobile_position` | `konum` / `mobil_konum` | `"center"`, `"top"`, `"left bottom"`, `"orta üst"`, `(x%, y%)` |
| `size` | `boyut` | `cover`, `contain`, `auto`, `1200`, `"50%"` |
| `repeat` | `tekrar` | `True` (desen/doku için) |
| `fixed` | `sabit` | `True` → kaydırırken sabit durur (mobilde otomatik kapanır) |
| `overlay` | `karartma` | `dark`, `darker`, `light`, `top`, `bottom`, `vignette`, `primary`, `brand`, CSS renk/gradyan |
| `overlay_opacity` | `opaklik` | 0–1 |
| `blur`, `brightness`, `contrast`, `saturate`, `grayscale` | `bulaniklik`, `parlaklik`, `kontrast`, `doygunluk`, `siyah_beyaz` | sayılar |
| `motion` | `hareket` | `kenburns`, `parallax` (+ `parallax_speed`) |
| `text` | `yazi` | `light`, `dark` veya renk |
| `color`, `gradient` | `renk`, `gradyan` | görselin arkasındaki yedek renk / gradyan |
| `min_height` | `min_yukseklik` | `600` veya `"80vh"` |
| `focus` | `odak` | optimizasyonda kırpma odağı (varsayılan: `position`) |

## Görsel boyut rehberi ve otomatik kontrol

Her görselin kullanıldığı **alana** göre önerilen piksel boyutu, oranı ve dosya boyutu vardır (retina ekranlar için 2x hesaplanmış):

| Alan | Önerilen | En az | Oran | Maks. dosya |
|---|---|---|---|---|
| Sayfa arka planı (`page_background`) | 2560×1440 px | 1920×1080 px | 16:9 | 450 KB |
| Giriş (hero) arka planı (`hero_background`) | 2400×1350 px | 1600×900 px | 16:9 | 400 KB |
| Giriş yan görseli (`hero_image`) | 1200×900 px | 800×600 px | 4:3 | 250 KB |
| Bölüm arka planı (`section_background`) | 1920×800 px | 1440×600 px | 12:5 | 300 KB |
| Mobil arka plan (`mobile_background`) | 1080×1920 px | 750×1334 px | 9:16 | 250 KB |
| İçerik görseli (`content_image`) | 1920×1080 px | 1100×620 px | 16:9 | 300 KB |
| Sütun görseli (`column_image`) | 1200×900 px | 800×600 px | 4:3 | 200 KB |
| Kart görseli (`card_image`) | 800×450 px | 640×360 px | 16:9 | 120 KB |
| Galeri görseli (`gallery`) | 1200×900 px | 800×600 px | 4:3 | 220 KB |
| Profil fotoğrafı (`avatar`) | 256×256 px | 96×96 px | 1:1 | 40 KB |
| Logo (`logo`) | ↕ 102 px | ↕ 68 px | serbest / any | 30 KB |
| Site ikonu (favicon) (`favicon`) | 512×512 px | 180×180 px | 1:1 | 50 KB |
| Paylaşım görseli (Open Graph) (`og_image`) | 1200×630 px | 600×315 px | 1.91:1 | 300 KB |
| Video kapak görseli (`video_poster`) | 1920×1080 px | 1280×720 px | 16:9 | 250 KB |

Ayrıntılı kompozisyon tavsiyeleri (konuyu nereye koymalı, mobilde ne kırpılır): **[docs/GORSEL-REHBERI.md](docs/GORSEL-REHBERI.md)**

### Derlerken otomatik rapor

`site.olustur()` her görseli kullanıldığı yere göre kontrol eder:

```
• index.html › hero › background
  manzara.jpg  →  Giriş (hero) arka planı  ·  900×600 · 112 KB  ·  D (53/100)
     Önerilen: 2400×1350 px  ·  oran 16:9  ·  ≤ 400 KB
     ✗ Çok küçük: 900×600 px. Bu alan en az 1600×900 px ister; büyük ekranlarda bulanık görünecek.
        → En az 1600×900 px boyutunda bir görsel kullanın (ideal: 2400×1350 px).
     ⚠ Oran 3:2 (1.50), alan 16:9 (1.78) istiyor: üst/alt kenarlardan toplam 94 px (%16) kırpılacak.
        → Önceden 900×506 px olarak kırpın ki ne kesileceğini siz seçin (veya focus='top' gibi odak verin).
```

```python
site.olustur(optimize_images=True)   # kırp + WebP + srcset (Pillow) — rapordaki sorunlar ✓ düzeltildi olur
site.olustur(strict=True)            # görsel hatası varsa derleme durur (CI için)
site.olustur(check_remote=True)      # URL görselleri de indirip kontrol et
print(site.resim_raporu())           # derlemeden sadece rapor
```

### Elinizdeki görsel nereye uygun?

```python
from webcraft import resim_rehberi, resim_analiz, resim_nereye

print(resim_rehberi("kart"))                    # kart görseli kaç piksel olmalı?
print(resim_analiz("foto.jpg", "hero_background"))
for p in resim_nereye("foto.jpg"):              # bu foto en çok nereye uyar?
    print(p)
# ██████████ 100%  Mobil arka plan  [mobile_background]
# ███████░░░  77%  Sütun görseli  [column_image]
```

### Görsel bileşeni seçenekleri

```python
site.resim("urun.jpg", "Ürün", width=480, aspect="1:1", position="top", link="https://...", caption="...")
```
`aspect` görseli o orana kırpar, `position` hangi kısmın görüneceğini seçer, `width` verilince önerilen boyut `2 × width` olur.

### SEO ve paylaşım

```python
Site("Başlık", description="...", og_image="paylasim.jpg",    # 1200×630 önerilir
     favicon="ikon.svg", url="https://alanadi.com", theme_color="#0b1120")
```
Open Graph / Twitter kartı, canonical link, tema rengi ve hero görselinin önceden yüklenmesi (LCP preload) otomatik eklenir.

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

webcraft build site.py --optimize --strict   # görselleri optimize et, hata varsa dur
webcraft check site.py                       # sadece görsel raporu
webcraft guide                               # tüm alanların boyut rehberi
webcraft guide hero --lang en
webcraft check-image foto.jpg                # bu görsel nereye uygun?
webcraft check-image foto.jpg -s kart        # kart görseli olarak yeterli mi?
webcraft optimize foto.jpg -s hero --focus top -o out/
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
python examples/backgrounds.py   # tüm arka plan seçenekleri (Ken Burns, parallax, mobil görsel…)
python examples/image_check.py foto.jpg   # görsel rehberi ve analiz
```

## Geliştirme

```bash
pip install -e .[dev]
pytest
```

## Lisans

MIT
