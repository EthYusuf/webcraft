import json
import re

import pytest

from webcraft import THEMES, Site
from webcraft.cli import main as cli_main


def spec_of(html: str) -> dict:
    match = re.search(r'<script type="application/json" data-webcraft[^>]*>(.*?)</script>', html, re.S)
    assert match, "spec script tag missing"
    return json.loads(match.group(1))


def test_theme_background_font_colors():
    site = Site("Test", theme="dark").background("#101010").font("Poppins", heading="Lora").colors(primary="#f00")
    theme = site.to_dict()["theme"]
    assert theme == {"preset": "dark", "background": "#101010", "font": "Poppins", "heading_font": "Lora",
                     "primary": "#f00"}


def test_turkish_aliases_match_english():
    tr = Site("A").arka_plan("#000").yazi_tipi("Inter").yazi_rengi("#fff")
    tr.baslik("Merhaba").yazi("Dünya").buton("Tıkla", "#x")
    en = Site("A").background("#000").font("Inter").text_color("#fff")
    en.heading("Merhaba").text("Dünya").button("Tıkla", "#x")
    assert tr.to_dict() == en.to_dict()


def test_unknown_theme_and_option_raise():
    with pytest.raises(ValueError):
        Site(theme="nope")
    with pytest.raises(TypeError):
        Site().text("x", colour="red")


def test_friendly_shapes_are_normalised():
    site = Site()
    site.navbar("Logo", {"Home": "#home"}, cta=("Go", "#go"))
    site.hero("Hi", button=("Start", "#s"), buttons=[("More", "#m")])
    site.stats({"10K+": "Users"})
    site.faq({"Q?": "A."})
    nav, hero, stats, faq = site.components
    assert nav["props"]["links"] == [{"text": "Home", "href": "#home"}]
    assert nav["props"]["cta"] == {"text": "Go", "href": "#go"}
    assert hero["props"]["buttons"] == [{"text": "Start", "href": "#s"}, {"text": "More", "href": "#m", "style": "outline"}]
    assert stats["props"]["items"] == [{"value": "10K+", "label": "Users"}]
    assert faq["props"]["items"] == [{"question": "Q?", "answer": "A."}]


def test_section_and_columns_nest_children():
    site = Site()
    with site.section(background="#111", id="about") as s:
        s.heading("Inside")
    with site.columns(2) as (left, right):
        left.text("L")
        right.text("R")
    section, cols = site.components
    assert section["props"] == {"background": "#111", "id": "about"}
    assert section["children"][0]["props"]["text"] == "Inside"
    assert [c[0]["props"]["text"] for c in cols["columns"]] == ["L", "R"]


def test_html_output_is_safe_and_complete():
    site = Site("Başlık </script>", lang="tr").font("Poppins")
    site.text("</script><script>alert(1)</script>")
    html = site.to_html()
    assert "<title>Başlık &lt;/script&gt;</title>" in html
    assert html.count("</script>") == 2  # spec tag + library tag only
    assert "family=Poppins" in html
    assert spec_of(html)["components"][0]["props"]["text"] == "</script><script>alert(1)</script>"


def test_build_writes_pages_assets_and_media(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "photo.png").write_bytes(b"\x89PNG fake")
    site = Site("Multi")
    site.image("photo.png").image("https://example.com/remote.jpg")
    site.page("about", title="About").heading("About us")
    index = site.build("out")

    assert index == tmp_path / "out" / "index.html"
    assert (tmp_path / "out" / "about.html").is_file()
    assert (tmp_path / "out" / "assets" / "webcraft.js").is_file()
    assert (tmp_path / "out" / "assets" / "webcraft.css").is_file()

    images = spec_of(index.read_text(encoding="utf-8"))["components"]
    local_src = images[0]["props"]["src"]
    assert local_src.startswith("assets/media/photo-") and (tmp_path / "out" / local_src).is_file()
    assert images[1]["props"]["src"] == "https://example.com/remote.jpg"
    assert spec_of((tmp_path / "out" / "about.html").read_text(encoding="utf-8"))["title"] == "About"


def test_inline_build_is_single_file(tmp_path):
    index = Site("Inline").build(tmp_path, inline=True)
    html = index.read_text(encoding="utf-8")
    assert "WebCraft.js v" in html and "WebCraft.css v" in html
    assert not (tmp_path / "assets").exists()


def test_all_presets_accepted():
    for name in THEMES:
        assert Site(theme=name).to_dict()["theme"]["preset"] == name


def test_cli_new_and_build(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert cli_main(["new", "demo-site"]) == 0
    assert cli_main(["build", "demo-site/site.py"]) == 0
    html = (tmp_path / "demo-site" / "dist" / "index.html").read_text(encoding="utf-8")
    assert spec_of(html)["components"][0]["type"] == "navbar"
