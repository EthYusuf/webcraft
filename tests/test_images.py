import json
import re
import struct
import zlib

import pytest

from webcraft import ArkaPlan, Background, ImageQualityError, Site
from webcraft.builder import find_media
from webcraft.cli import main as cli_main
from webcraft.images import (SLOTS, analyze_image, crop_to_aspect, get_slot, image_guide, probe, probe_bytes,
                             suggest_placement)
from webcraft.images.analyze import analyze_info
from webcraft.images.probe import ImageInfo

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

needs_pillow = pytest.mark.skipif(Image is None, reason="Pillow not installed")


# ----------------------------------------------------------------------
# Helpers: write tiny but valid image headers without Pillow
# ----------------------------------------------------------------------
def png_bytes(w, h, color_type=2):
    ihdr = struct.pack(">IIBBBBB", w, h, 8, color_type, 0, 0, 0)
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))  # noqa: E731
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IEND", b"")


def write(tmp_path, name, data):
    p = tmp_path / name
    p.write_bytes(data)
    return p


def spec_of(html):
    return json.loads(re.search(r"data-webcraft[^>]*>(.*?)</script>", html, re.S).group(1))


# ----------------------------------------------------------------------
# probe
# ----------------------------------------------------------------------
def test_probe_png_gif_bmp_svg_without_pillow(tmp_path):
    assert probe(write(tmp_path, "a.png", png_bytes(1920, 1080))).aspect == pytest.approx(16 / 9)
    assert probe(write(tmp_path, "b.png", png_bytes(10, 10, color_type=6))).has_alpha is True
    gif = b"GIF89a" + struct.pack("<HH", 320, 240) + b"\x00" * 20
    assert (probe_bytes(gif)["width"], probe_bytes(gif)["height"]) == (320, 240)
    bmp = b"BM" + b"\x00" * 12 + struct.pack("<I", 40) + struct.pack("<ii", 800, -600) + b"\x00" * 30
    assert probe_bytes(bmp)["height"] == 600
    svg = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 60"></svg>'
    info = probe_bytes(svg)
    assert (info["width"], info["height"], info["vector"]) == (240, 60, True)
    assert probe_bytes(b'<svg width="2in" viewBox="0 0 100 50"/>')["height"] == 96


def test_probe_rejects_garbage(tmp_path):
    from webcraft.images import ImageProbeError

    with pytest.raises(ImageProbeError):
        probe(write(tmp_path, "x.png", b"not an image at all"))
    with pytest.raises(FileNotFoundError):
        probe(tmp_path / "missing.jpg")


@needs_pillow
def test_probe_jpeg_webp_and_exif_rotation(tmp_path):
    Image.new("RGB", (1600, 900)).save(tmp_path / "a.jpg", quality=80)
    Image.new("RGB", (1200, 630)).save(tmp_path / "a.webp", quality=80)
    Image.new("RGBA", (300, 200)).save(tmp_path / "b.webp", lossless=True)
    exif = Image.Exif()
    exif[0x0112] = 6
    Image.new("RGB", (2000, 1500)).save(tmp_path / "rot.jpg", exif=exif)

    assert (probe(tmp_path / "a.jpg").width, probe(tmp_path / "a.jpg").format) == (1600, "jpeg")
    assert probe(tmp_path / "a.webp").height == 630
    assert probe(tmp_path / "b.webp").has_alpha is True
    rot = probe(tmp_path / "rot.jpg")
    assert (rot.width, rot.height, rot.orientation) == (1500, 2000, 6)


# ----------------------------------------------------------------------
# specs & analysis
# ----------------------------------------------------------------------
def test_every_slot_is_documented_in_both_languages():
    for slot in SLOTS.values():
        for field in (slot.name, slot.where, slot.safe_zone):
            assert field["tr"] and field["en"]
        assert slot.minimum[1] is not None
    assert get_slot("giris") is SLOTS["hero_background"]
    assert "2400×1350" in image_guide("hero_background")
    assert "Hero background" in image_guide("hero", lang="en")
    with pytest.raises(KeyError):
        get_slot("nope")


def test_crop_to_aspect_math_and_focus():
    crop = crop_to_aspect(3000, 2000, 16 / 9)
    assert (crop.width, crop.height, crop.left, crop.top) == (3000, 1688, 0, 156)
    assert crop_to_aspect(3000, 2000, 16 / 9, "top").top == 0
    assert crop_to_aspect(3000, 2000, 1, "right").left == 1000
    assert crop_to_aspect(3000, 2000, 1, (0, 50)).left == 0


def info(w, h, fmt="jpeg", kb=100, **kw):
    return ImageInfo(format=fmt, width=w, height=h, file_size=kb * 1024, **kw)


def codes(report):
    return {i.code: i.level for i in report.issues}


def test_analysis_flags_size_ratio_weight_and_format():
    small = analyze_info(info(900, 600), "hero_background")
    assert codes(small)["too_small"] == "error" and not small.ok
    assert small.crop and (small.crop.width, small.crop.height) == (900, 506)

    ideal = analyze_info(info(2400, 1350, kb=300), "hero_background")
    assert ideal.issues == [] and ideal.score == 100 and ideal.grade == "A"

    huge = analyze_info(info(6000, 3375, kb=3000), "hero_background")
    assert {"oversized", "heavy"} <= set(codes(huge))

    portrait = analyze_info(info(1080, 1920), "page_background")
    assert "wrong_orientation" in codes(portrait)

    assert codes(analyze_info(info(1200, 800, fmt="bmp"), "gallery"))["bad_format"] == "error"
    assert "vector_ok" in codes(analyze_info(info(240, 60, fmt="svg", vector=True, has_alpha=True), "logo"))
    assert "logo_alpha" in codes(analyze_info(info(400, 100, fmt="png", has_alpha=False), "logo"))
    assert "png_photo" in codes(analyze_info(info(1600, 900, fmt="png", kb=900, has_alpha=False), "content_image"))


def test_display_width_changes_the_recommendation():
    report = analyze_info(info(900, 506), "content_image", display_width=400)
    assert report.recommended == (800, 450)
    assert report.ok


def test_report_text_is_localised():
    tr = str(analyze_info(info(900, 600), "hero_background", lang="tr"))
    en = str(analyze_info(info(900, 600), "hero_background", lang="en"))
    assert "Çok küçük" in tr and "Too small" in en


def test_suggest_placement_ranks_sensibly(tmp_path):
    portrait = write(tmp_path, "p.png", png_bytes(1080, 1920))
    square = write(tmp_path, "s.png", png_bytes(256, 256))
    wide = write(tmp_path, "w.png", png_bytes(1200, 630))
    assert suggest_placement(portrait)[0].slot.key == "mobile_background"
    assert suggest_placement(square)[0].slot.key == "avatar"
    assert suggest_placement(wide)[0].slot.key == "og_image"
    assert "%" in str(suggest_placement(wide)[0])


# ----------------------------------------------------------------------
# Background
# ----------------------------------------------------------------------
def test_background_serialisation_and_turkish_names():
    bg = Background(image="a.jpg", position=(30, 70), size=1200, overlay="dark", blur=3, fixed=True)
    assert bg.to_dict() == {"image": "a.jpg", "size": "1200px", "position": "30% 70%", "fixed": True,
                            "overlay": "dark", "blur": 3}
    tr = ArkaPlan(resim="a.jpg", konum="orta üst", karartma="bottom", bulaniklik=2, boyut="kapla", sabit=True)
    assert tr.to_dict() == {"image": "a.jpg", "size": "cover", "position": "center top", "fixed": True,
                            "overlay": "bottom", "blur": 2}


def test_background_validation():
    with pytest.raises(ValueError):
        Background()
    with pytest.raises(ValueError):
        Background(image="a.jpg", motion="spin")
    with pytest.raises(ValueError):
        Background(image="a.jpg", overlay_opacity=2)
    with pytest.raises(TypeError):
        Site().text("x", background=42)


def test_site_background_layer_and_hero_shorthand():
    site = Site().background(image="bg.jpg", overlay="dark", blur=2, color="#000")
    theme = site.to_dict()["theme"]
    assert theme["background_layer"]["image"] == "bg.jpg" and theme["background_color"] == "#000"
    site.background("#111")
    assert "background_layer" not in site.to_dict()["theme"]

    site.hero("Hi", background_image="h.jpg")
    assert site.components[-1]["props"]["background"] == {
        "image": "h.jpg", "size": "cover", "position": "center", "overlay": "dark", "text": "light"}
    with pytest.raises(TypeError):
        site.hero("Hi", overlay="dark")


# ----------------------------------------------------------------------
# Build integration
# ----------------------------------------------------------------------
def test_find_media_assigns_slots_by_placement():
    site = Site().background(image="page.jpg", mobile_image="page-m.jpg")
    site.hero("Hi", image="side.png", background=Background(image="hero.jpg"))
    site.features([{"title": "A", "image": "card.jpg"}])
    with site.columns(2) as (left, _right):
        left.image("col.jpg")
    site.image("sq.jpg", aspect="1:1")
    site.gallery(["g.jpg"]).testimonials([("q", "n", "r", "av.jpg")])
    with site.section(background=Background(image="sec.jpg")) as s:
        s.text("x")
    refs = {r.value: r for r in find_media(site.to_dict(), "index.html")}
    expect = {"page.jpg": "page_background", "page-m.jpg": "mobile_background", "side.png": "hero_image",
              "hero.jpg": "hero_background", "card.jpg": "card_image", "col.jpg": "column_image",
              "sq.jpg": "content_image", "g.jpg": "gallery", "av.jpg": "avatar", "sec.jpg": "section_background"}
    assert {k: refs[k].slot for k in expect} == expect
    assert refs["sq.jpg"].resolve_slot().aspect == (1, 1)


def test_build_reports_missing_files_and_strict_mode(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    write(tmp_path, "small.png", png_bytes(900, 600))
    site = Site("R").hero("Hi", background_image="small.png")
    site.image("missing.jpg")
    site.build("out")
    out = capsys.readouterr().out
    assert "Çok küçük" in out and "Dosya bulunamadı" in out
    assert site.last_image_report.error_count == 2

    with pytest.raises(ImageQualityError):
        site.build("out", strict=True, quiet=True)
    site.build("out", check_images=False)
    assert capsys.readouterr().out == ""


def test_build_records_intrinsic_size_for_layout_stability(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write(tmp_path, "pic.png", png_bytes(1600, 900))
    index = Site().image("pic.png").build("out", quiet=True)
    props = spec_of(index.read_text(encoding="utf-8"))["components"][0]["props"]
    assert props["src_size"] == [1600, 900] and props["src"].startswith("assets/media/")


def test_seo_tags(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write(tmp_path, "og.png", png_bytes(1200, 630))
    site = Site("SEO", description="Açıklama", og_image="og.png", url="https://ex.com/", theme_color="#000")
    site.page("about")
    html = site.build("out", quiet=True).read_text(encoding="utf-8")
    assert '<meta property="og:image" content="https://ex.com/assets/media/og-' in html
    assert '<link rel="canonical" href="https://ex.com/">' in html
    assert 'name="theme-color" content="#000"' in html
    assert '"https://ex.com/about.html"' in (tmp_path / "out" / "about.html").read_text(encoding="utf-8")


@needs_pillow
def test_optimize_creates_responsive_webp_and_resolves_issues(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Image.new("RGB", (3000, 2000), (120, 40, 200)).save(tmp_path / "big.bmp")
    site = Site().hero("Hi", background=Background(image="big.bmp", focus="top"))
    index = site.build("out", optimize_images=True, strict=True, quiet=True)
    bg = spec_of(index.read_text(encoding="utf-8"))["components"][0]["props"]["background"]
    assert bg["image"].endswith("-2400.webp") and bg["image_size"] == [2400, 1350]
    widths = [int(part.split()[-1][:-1]) for part in bg["image_srcset"].split(",")]
    assert widths == sorted(widths) and widths[0] == 320 and widths[-1] == 2400
    assert (tmp_path / "out" / bg["image"]).is_file()
    entry = site.last_image_report.entries[0]
    assert {i.code for i in entry.report.resolved} >= {"bad_format", "heavy"}
    html = index.read_text(encoding="utf-8")
    assert 'rel="preload" as="image"' in html and "imagesrcset=" in html


def test_cli_guide_and_check_image(tmp_path, capsys):
    p = write(tmp_path, "p.png", png_bytes(1080, 1920))
    assert cli_main(["guide", "card"]) == 0
    assert "800×450" in capsys.readouterr().out
    assert cli_main(["check-image", str(p)]) == 0
    assert "mobile_background" in capsys.readouterr().out
    assert cli_main(["check-image", str(p), "-s", "page_background", "--json"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert data["slot"] == "page_background" and data["grade"] in "DF"


def test_analyze_image_from_path(tmp_path):
    report = analyze_image(write(tmp_path, "a.png", png_bytes(800, 450)), "card")
    assert report.ok and report.slot.key == "card_image"
