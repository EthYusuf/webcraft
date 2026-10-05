# Görsel Rehberi

> Bu dosya `python -m webcraft guide` çıktısından üretilmiştir — değerler kodla aynıdır.

WebCraft her görselin **nerede kullanıldığını** bilir ve derleme sırasında o alanın kurallarına göre kontrol eder.
Tüm boyutlar **retina (2x) ekranlar** için hesaplanmıştır: 560 CSS px genişliğinde gösterilen bir görsel ~1120 gerçek piksel ister.

## Özet tablo

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

## Alan alan ayrıntılar

```text
WebCraft görsel boyut rehberi
=============================

▸ Sayfa arka planı  [page_background]
  Nerede:      site.arka_plan(image=...) — tüm sayfanın arkasında sabit durur
  Önerilen:   2560×1440 px
  En az:      1920×1080 px
  Oran:       16:9 (kırpılır)
  Dosya:      ≤ 450 KB  ·  AVIF, WEBP, JPEG
  Mobil:      1080×1920 px
  Kompozisyon: Ana konuyu ortadaki %50'lik alanda tutun; ekran oranına göre kenarlar kırpılır. Üstüne yazı geleceği için sade, düşük detaylı ve düşük kontrastlı görseller seçin.
  İpucu:        Okunabilirlik için overlay='dark' veya blur=2-6 kullanın. Mobilde ayrı dikey görsel (mobile_image) verin.

▸ Giriş (hero) arka planı  [hero_background]
  Nerede:      site.giris(background=ArkaPlan(image=...)) — ilk ekranı kaplayan görsel
  Önerilen:   2400×1350 px
  En az:      1600×900 px
  Oran:       16:9 (kırpılır)
  Dosya:      ≤ 400 KB  ·  AVIF, WEBP, JPEG
  Mobil:      1080×1350 px
  Kompozisyon: Başlık ortada duracağı için konuyu sol/sağ üçte birlik alana ya da alt kısma koyun; yüzler ve ürünler merkezdeki %60'lık alanın içinde kalsın (mobilde kenarlar kesilir).
  İpucu:        full_height=True ise 16:9 yerine 2560×1440 kullanın. Koyu overlay ile beyaz yazı en okunur.

▸ Giriş yan görseli  [hero_image]
  Nerede:      site.giris(..., image=...) — başlığın yanında duran görsel/mockup
  Önerilen:   1200×900 px
  En az:      800×600 px
  Oran:       4:3
  Dosya:      ≤ 250 KB  ·  WEBP, AVIF, PNG, JPEG
  Kompozisyon: Görsel kırpılmaz; tamamı görünür. Ürün ekran görüntüsü veya şeffaf PNG/WebP mockup idealdir.
  İpucu:        Şeffaf arka planlı görseller için WebP (alpha) PNG'den ~%70 daha küçüktür.

▸ Bölüm arka planı  [section_background]
  Nerede:      site.bolum(background=ArkaPlan(image=...)) veya herhangi bir bileşenin background'u
  Önerilen:   1920×800 px
  En az:      1440×600 px
  Oran:       12:5 (kırpılır)
  Dosya:      ≤ 300 KB  ·  AVIF, WEBP, JPEG
  Mobil:      1080×1080 px
  Kompozisyon: Bölüm yüksekliği içeriğe göre değişir; üst-alttan kırpılabilir. Konuyu dikey olarak ortada tutun. Doku, gradyan veya bulanık fotoğraflar en iyi sonucu verir.
  İpucu:        fixed=True ile parallax hissi verir; mobilde otomatik olarak normal kaydırmaya döner.

▸ Mobil arka plan  [mobile_background]
  Nerede:      ArkaPlan(mobile_image=...) — 768 px altındaki ekranlarda kullanılır
  Önerilen:   1080×1920 px
  En az:      750×1334 px
  Oran:       9:16 (kırpılır)
  Dosya:      ≤ 250 KB  ·  AVIF, WEBP, JPEG
  Kompozisyon: Dikey çekim kullanın; konu ekranın ortasında ve üst %20'den aşağıda olsun (üstte menü var).

▸ İçerik görseli  [content_image]
  Nerede:      site.resim(...) — sayfa genişliğinde tek görsel
  Önerilen:   1920×1080 px
  En az:      1100×620 px
  Oran:       16:9
  Dosya:      ≤ 300 KB  ·  AVIF, WEBP, JPEG, PNG
  Kompozisyon: Kırpılmaz; olduğu gibi gösterilir. width= verirseniz önerilen boyut onun 2 katıdır.
  İpucu:        aspect='16:9' ve fit='cover' ile farklı oranlı görselleri aynı yüksekliğe getirebilirsiniz.

▸ Sütun görseli  [column_image]
  Nerede:      site.sutunlar(2) içinde resim — yazının yanında
  Önerilen:   1200×900 px
  En az:      800×600 px
  Oran:       4:3
  Dosya:      ≤ 200 KB  ·  AVIF, WEBP, JPEG
  Kompozisyon: Yazıyla yan yana durduğu için 4:3 veya 1:1 oran dengeli görünür; dikey görseller sütunu uzatır.

▸ Kart görseli  [card_image]
  Nerede:      site.kartlar([{'image': ...}]) — kartın üstü, 16:9'a kırpılır
  Önerilen:   800×450 px
  En az:      640×360 px
  Oran:       16:9 (kırpılır)
  Dosya:      ≤ 120 KB  ·  AVIF, WEBP, JPEG
  Kompozisyon: Kart küçük: tek ve net bir konu seçin, konuyu ortada tutun; yazı içeren görsellerden kaçının.

▸ Galeri görseli  [gallery]
  Nerede:      site.galeri([...]) — 4:3'e kırpılır, tıklanınca tam boyut açılır
  Önerilen:   1200×900 px
  En az:      800×600 px
  Oran:       4:3 (kırpılır)
  Dosya:      ≤ 220 KB  ·  AVIF, WEBP, JPEG
  Kompozisyon: Tüm galeri görsellerini aynı oranda çekin/kırpın; konu ortada olsun.

▸ Profil fotoğrafı  [avatar]
  Nerede:      site.yorumlar([(..., avatar)]) — 46 px yuvarlak
  Önerilen:   256×256 px
  En az:      96×96 px
  Oran:       1:1 (kırpılır)
  Dosya:      ≤ 40 KB  ·  WEBP, JPEG
  Kompozisyon: Yüz ortada ve karenin ~%60'ını kaplasın; daire şeklinde kırpılır.

▸ Logo  [logo]
  Nerede:      site.menu(logo_image=...) — menüde 34 px yükseklik
  Önerilen:   ↕ 102 px
  En az:      ↕ 68 px
  Oran:       serbest / any
  Dosya:      ≤ 30 KB  ·  SVG, WEBP, PNG
  Kompozisyon: Kenarlarda boş alan bırakmayın (kırpın); şeffaf arka plan kullanın. Yatay logolar menüde en iyi durur.
  İpucu:        SVG her ekranda keskin kalır ve genellikle 5 KB altındadır.

▸ Site ikonu (favicon)  [favicon]
  Nerede:      Site(favicon=...) — tarayıcı sekmesi ve ana ekran ikonu
  Önerilen:   512×512 px
  En az:      180×180 px
  Oran:       1:1
  Dosya:      ≤ 50 KB  ·  SVG, PNG, ICO
  Kompozisyon: Basit bir sembol kullanın; 16 px'te de tanınabilir olmalı. Yazı koymayın.

▸ Paylaşım görseli (Open Graph)  [og_image]
  Nerede:      Site(og_image=...) — WhatsApp, X, LinkedIn, Facebook önizlemesi
  Önerilen:   1200×630 px
  En az:      600×315 px
  Oran:       1.91:1 (kırpılır)
  Dosya:      ≤ 300 KB  ·  JPEG, PNG, WEBP
  Kompozisyon: Önemli yazı ve logoyu ortadaki 1000×520 alana koyun; bazı platformlar kenarları ve kareye kırpar.
  İpucu:        WhatsApp 300 KB üstünü göstermeyebilir; JPEG kalite 80-85 idealdir.

▸ Video kapak görseli  [video_poster]
  Nerede:      site.video(..., poster=...) — video oynatılmadan önce
  Önerilen:   1920×1080 px
  En az:      1280×720 px
  Oran:       16:9 (kırpılır)
  Dosya:      ≤ 250 KB  ·  AVIF, WEBP, JPEG
  Kompozisyon: Ortaya oynat düğmesi gelir; yüzleri tam merkeze koymayın.
```

## Rapordaki işaretler

| İşaret | Anlamı |
|---|---|
| ✗ hata | Görsel bu alanda kötü görünecek veya hiç görünmeyecek (çok küçük, web dışı format, dosya yok). `build(strict=True)` derlemeyi durdurur. |
| ⚠ uyarı | Belirgin kalite/performans sorunu (çok kırpılacak, çok ağır, yanlış yön). |
| ℹ bilgi | İyileştirme önerisi (gereğinden büyük, SVG kullanın, EXIF döndürmesi). |
| ✓ düzeltildi | `optimize_images=True` bu sorunu otomatik çözdü. |

Not (A–F): 100'den hata başına 35, uyarı başına 12, bilgi başına 3 puan düşülür.

## `optimize_images=True` ne yapar? (Pillow gerekir: `pip install webcraft[images]`)

1. EXIF yönünü piksellere uygular (yan duran telefon fotoğrafları düzelir).
2. Alan kırpıyorsa görseli o orana, **odak noktasına** göre kırpar (`focus="top"`, `position=(30, 70)`).
3. Önerilen boyuttan büyük olmayan **WebP** sürümleri üretir (320w … 2560w).
4. Sayfaya `srcset` + `width/height` yazar: tarayıcı ekranına uygun dosyayı indirir, sayfa kaymaz.
5. İlk ekrandaki hero görselini `<link rel=preload>` ile önceden yükletir.
