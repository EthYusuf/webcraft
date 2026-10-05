"""Görsel araçları — hangi görsel nereye, hangi boyutta?

Çalıştır:  python examples/image_check.py  [görsel.jpg]
"""

import sys

from webcraft import analyze_image, guide_table, image_guide, suggest_placement

# 1) Tüm alanların özet tablosu
print(guide_table())
print()

# 2) Tek bir alanın ayrıntılı rehberi
print(image_guide("hero_background"))
print()

# 3) Elinizdeki bir görseli analiz edin
if len(sys.argv) > 1:
    path = sys.argv[1]

    print("Bu görsel nereye uygun?")
    for placement in suggest_placement(path):
        print("  ", placement)
    print()

    report = analyze_image(path, "hero_background")
    print(report)                       # okunur rapor
    if report.crop:
        print("Önerilen kırpma kutusu (sol, üst, sağ, alt):", report.crop.box)
else:
    print("İpucu: python examples/image_check.py fotograf.jpg")
