"""Full landing page example — run:  python examples/landing.py"""

from webcraft import Site

site = Site("Nova Studio", theme="midnight", description="Nova Studio — dijital ürün stüdyosu")
site.yazi_tipi("Inter", heading="Space Grotesk")
site.renkler(primary="#a855f7", secondary="#f472b6")

site.menu("✦ Nova", {"Hizmetler": "#hizmetler", "Fiyatlar": "#fiyatlar", "SSS": "#sss"},
          cta=("İletişime Geç", "#iletisim"))

site.giris(
    "Fikirlerinizi **dijital deneyimlere** dönüştürüyoruz",
    "Web siteleri, mobil uygulamalar ve marka kimlikleri — hepsi tek bir ekipten.",
    button=("Projeye Başla", "#iletisim"),
    buttons=[("Çalışmalarımız", "#galeri")],
    badge="🚀 2026'nın en iyi stüdyosu",
    full_height=True,
)

site.istatistikler({"250+": "Tamamlanan proje", "98%": "Mutlu müşteri", "12": "Ödül", "24/7": "Destek"})

site.ozellikler([
    ("🎨", "UI / UX Tasarım", "Kullanıcı odaklı, modern ve erişilebilir arayüzler."),
    ("⚙️", "Web Geliştirme", "Hızlı, güvenli ve ölçeklenebilir web uygulamaları."),
    ("📱", "Mobil Uygulama", "iOS ve Android için yerel performans."),
    ("📈", "SEO & Büyüme", "Arama motorlarında üst sıralara çıkın."),
    ("🛡️", "Güvenlik", "Her katmanda en iyi güvenlik uygulamaları."),
    ("☁️", "Bulut", "Otomatik ölçeklenen bulut altyapısı."),
], title="Hizmetlerimiz", subtitle="Uçtan uca dijital çözümler", id="hizmetler")

with site.sutunlar(2) as (sol, sag):
    sol.resim("https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1200", "Ekip")
    sag.baslik("Biz kimiz?", subtitle="10 yıllık deneyim")
    sag.yazi("Nova Studio, tasarımcı ve yazılımcılardan oluşan **tutkulu** bir ekip.\n\n"
             "Her projeye müşterimizin hedeflerini anlayarak başlıyoruz.")
    sag.buton("Hakkımızda", "#", style="outline")

site.galeri([
    ("https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=900", "E-ticaret"),
    ("https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=900", "SaaS Paneli"),
    ("https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=900", "Analitik"),
], title="Son Çalışmalar", id="galeri")

site.yorumlar([
    ("Harika bir ekip, işimizi 3 kat büyüttük!", "Ayşe Yılmaz", "CEO, ModaX"),
    ("Zamanında ve bütçe dahilinde teslim ettiler.", "Mehmet Kaya", "CTO, FinTech"),
    ("Tasarım anlayışları gerçekten çok iyi.", "Zeynep Demir", "Kurucu, Bloom"),
], title="Müşterilerimiz ne diyor?")

site.fiyatlar([
    {"name": "Başlangıç", "price": "₺4.900", "period": "/proje", "features": ["5 sayfa", "Mobil uyum", "1 ay destek"],
     "button": ("Seç", "#iletisim")},
    {"name": "Profesyonel", "price": "₺12.900", "period": "/proje", "highlight": "En Popüler",
     "features": ["15 sayfa", "CMS", "SEO", "6 ay destek"], "button": ("Seç", "#iletisim")},
    {"name": "Kurumsal", "price": "Özel", "features": ["Sınırsız sayfa", "Özel entegrasyon", "7/24 destek"],
     "button": ("Görüşelim", "#iletisim")},
], title="Fiyatlandırma", id="fiyatlar")

site.sss({
    "Bir proje ne kadar sürer?": "Ortalama 4-8 hafta. Kapsama göre değişir.",
    "Bakım hizmeti veriyor musunuz?": "Evet, tüm paketlerde destek süresi var.",
    "Ödeme nasıl yapılır?": "Proje başında %50, teslimde %50.",
}, title="Sıkça Sorulan Sorular", id="sss")

site.cagri("Projenize başlamaya hazır mısınız?", "İlk görüşme ücretsiz.", button=("Hemen Yazın", "#iletisim"))

site.iletisim(
    "İletişim", "24 saat içinde dönüş yapıyoruz.", email="merhaba@nova.studio", id="iletisim",
    fields=[("name", "Adınız"), ("email", "E-posta", "email"), ("message", "Mesajınız", "textarea")],
    button="Gönder", success="Teşekkürler! Mail uygulamanız açılıyor.",
    info=[("📍", "Adres", "İstanbul, Türkiye"), ("✉️", "E-posta", "merhaba@nova.studio"), ("📞", "Telefon", "+90 555 000 00 00")],
)

site.alt_bilgi("Fikirden ürüne, yanınızdayız.", {"Hizmetler": "#hizmetler", "Fiyatlar": "#fiyatlar"},
               logo="✦ Nova", socials={"GitHub": "https://github.com", "X": "https://x.com"},
               copyright="© 2026 Nova Studio. Tüm hakları saklıdır.")

if __name__ == "__main__":
    site.olustur("examples/dist/landing")
    print("Built -> examples/dist/landing/index.html")
