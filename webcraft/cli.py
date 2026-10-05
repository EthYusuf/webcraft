"""Command line interface: ``webcraft new | build | serve``."""

from __future__ import annotations

import argparse
import json
import os
import runpy
import sys
from pathlib import Path

from . import __version__
from .builder import ImageQualityError, _echo

STARTER = '''from webcraft import Site

site = Site("{title}", theme="dark")
site.arka_plan("linear-gradient(160deg, #0b1120, #1e1b4b)", color="#0b1120")
site.yazi_tipi("Poppins")
site.renkler(primary="#818cf8", secondary="#22d3ee")

site.menu("{title}", {{"Özellikler": "#ozellikler", "İletişim": "#iletisim"}}, cta=("Başla", "#iletisim"))
site.giris(
    "Python ile **profesyonel** web siteleri",
    "Birkaç satır kodla modern, hızlı ve mobil uyumlu bir site.",
    button=("Hemen Başla", "#ozellikler"),
    badge="✨ WebCraft",
)
site.ozellikler([
    ("⚡", "Hızlı", "Saniyeler içinde statik HTML üretir."),
    ("🎨", "Şık", "Hazır temalar, fontlar ve animasyonlar."),
    ("📱", "Mobil uyumlu", "Her ekranda kusursuz görünür."),
], title="Neden WebCraft?", id="ozellikler")
site.iletisim("Bize ulaşın", email="ornek@mail.com", id="iletisim",
              fields=[("name", "Adınız"), ("email", "E-posta", "email"), ("message", "Mesajınız", "textarea")],
              button="Gönder")
site.alt_bilgi("Python + WebCraft ile yapıldı.", copyright="© 2026 {title}")

if __name__ == "__main__":
    site.yayinla()  # http://localhost:8000
'''


def cmd_new(args: argparse.Namespace) -> int:
    folder = Path(args.name)
    target = folder / "site.py"
    if target.exists():
        print(f"error: {target} already exists", file=sys.stderr)
        return 1
    folder.mkdir(parents=True, exist_ok=True)
    target.write_text(STARTER.format(title=folder.name.replace("-", " ").title()), encoding="utf-8")
    print(f"Created {target}\nNext:  cd {folder}  &&  python site.py")
    return 0


def _load_site(script: Path):
    """Run a site script without triggering its ``__main__`` block and return its Site."""
    from .site import Site

    sys.path.insert(0, str(script.parent.resolve()))
    namespace = runpy.run_path(str(script), run_name="webcraft_build")
    sites = [v for v in namespace.values() if isinstance(v, Site)]
    if not sites:
        raise SystemExit(f"error: no Site object found in {script}")
    return sites[0]


def cmd_build(args: argparse.Namespace) -> int:
    script = Path(args.script)
    os.chdir(script.parent.resolve())
    site = _load_site(Path(script.name))
    try:
        index = site.build(args.out, inline=args.inline, optimize_images=args.optimize, strict=args.strict,
                           check_remote=args.remote, quiet=args.quiet)
    except ImageQualityError as exc:
        _echo(f"\nBuild failed (--strict): {exc.report.error_count} image error(s).")
        return 1
    print(f"Built {len(site.pages)} page(s) -> {index.parent.resolve()}")
    return 0


def _parse_focus(value):
    if value and "," in value:
        x, y = value.split(",", 1)
        return (float(x), float(y))
    return value or "center"


def cmd_guide(args: argparse.Namespace) -> int:
    from .images import guide_table, image_guide

    _echo(guide_table(args.lang) if args.table else image_guide(args.slot, args.lang))
    return 0


def cmd_check_image(args: argparse.Namespace) -> int:
    from .images import analyze_image, suggest_placement

    tr = args.lang == "tr"
    if args.slot:
        report = analyze_image(args.path, args.slot, lang=args.lang, display_width=args.width,
                               focus=_parse_focus(args.focus))
        if args.json:
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            _echo(str(report))
        return 0 if report.ok else 1
    placements = suggest_placement(args.path, lang=args.lang, top=args.top)
    if args.json:
        print(json.dumps([{"slot": p.slot.key, "score": p.score, "report": p.report.to_dict()} for p in placements],
                         ensure_ascii=False, indent=2))
        return 0
    info = placements[0].report.info
    kb = f", {info.file_size / 1024:.0f} KB" if info.file_size else ""
    _echo(f"{Path(args.path).name}: {info.width}×{info.height} px, {info.format.upper()}{kb}\n")
    _echo("Bu görsel en çok şu alanlara uygun:" if tr else "This image fits best in:")
    for p in placements:
        _echo("  " + str(p))
    best = placements[0]
    _echo("\n" + ("En iyi eşleşme için ayrıntı:" if tr else "Details for the best match:"))
    _echo(str(best.report))
    _echo("\n" + best.slot.describe(args.lang))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    script = Path(args.script)
    os.chdir(script.parent.resolve())
    site = _load_site(Path(script.name))
    report = site.image_report(check_remote=args.remote)
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        _echo(str(report))
    return 0 if report.ok else 1


def cmd_optimize(args: argparse.Namespace) -> int:
    from .images import has_pillow, optimize_image

    if not has_pillow():
        print("error: Pillow is required:  pip install pillow", file=sys.stderr)
        return 1
    result = optimize_image(args.path, args.slot, args.out, focus=_parse_focus(args.focus),
                            quality=args.quality, display_width=args.width)
    if result is None:
        print("Nothing to do (vector, icon or animated image).")
        return 0
    for f in result.files:
        print(f"  {f}  ({f.stat().st_size // 1024} KB)")
    print(f"srcset: {result.srcset}")
    print(f"{result.width}×{result.height}, {result.saved_pct}% smaller than the original")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .server import serve

    path = Path(args.target)
    if path.suffix == ".py":
        os.chdir(path.parent.resolve())
        _load_site(Path(path.name)).build(args.out)
        path = Path(args.out)
    serve(path, port=args.port, open_browser=not args.no_browser)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="webcraft", description="Build websites with Python.")
    parser.add_argument("--version", action="version", version=f"webcraft {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="create a starter site.py in a new folder")
    p_new.add_argument("name")
    p_new.set_defaults(func=cmd_new)

    p_build = sub.add_parser("build", help="build a site script into static HTML")
    p_build.add_argument("script", nargs="?", default="site.py")
    p_build.add_argument("-o", "--out", default="dist")
    p_build.add_argument("--inline", action="store_true", help="single self-contained HTML file per page")
    p_build.add_argument("--optimize", action="store_true", help="crop/compress images, responsive WebP (Pillow)")
    p_build.add_argument("--strict", action="store_true", help="fail when an image has an error")
    p_build.add_argument("--remote", action="store_true", help="also analyse http(s) images")
    p_build.add_argument("-q", "--quiet", action="store_true", help="don't print the image report")
    p_build.set_defaults(func=cmd_build)

    from .images.specs import SLOTS

    p_guide = sub.add_parser("guide", help="recommended image sizes per placement")
    p_guide.add_argument("slot", nargs="?", help=f"one of: {', '.join(SLOTS)}")
    p_guide.add_argument("--table", action="store_true", help="compact markdown table")
    p_guide.add_argument("--lang", default="tr", choices=("tr", "en"))
    p_guide.set_defaults(func=cmd_guide)

    p_img = sub.add_parser("check-image", help="analyse one image (and suggest where it fits)")
    p_img.add_argument("path", help="file path or http(s) URL")
    p_img.add_argument("-s", "--slot", help="placement to check against; omit to get suggestions")
    p_img.add_argument("-w", "--width", type=int, help="display width in CSS px")
    p_img.add_argument("--focus", help="crop focus: center | top | 'left top' | '30,70'")
    p_img.add_argument("--top", type=int, default=5)
    p_img.add_argument("--json", action="store_true")
    p_img.add_argument("--lang", default="tr", choices=("tr", "en"))
    p_img.set_defaults(func=cmd_check_image)

    p_check = sub.add_parser("check", help="image report for every image of a site script")
    p_check.add_argument("script", nargs="?", default="site.py")
    p_check.add_argument("--remote", action="store_true")
    p_check.add_argument("--json", action="store_true")
    p_check.set_defaults(func=cmd_check)

    p_opt = sub.add_parser("optimize", help="crop + compress one image into responsive WebP files")
    p_opt.add_argument("path")
    p_opt.add_argument("-s", "--slot", required=True)
    p_opt.add_argument("-o", "--out", default="optimized")
    p_opt.add_argument("-w", "--width", type=int)
    p_opt.add_argument("--focus")
    p_opt.add_argument("-q", "--quality", type=int, default=80)
    p_opt.set_defaults(func=cmd_optimize)

    p_serve = sub.add_parser("serve", help="serve a built folder or a site script")
    p_serve.add_argument("target", nargs="?", default="site.py")
    p_serve.add_argument("-p", "--port", type=int, default=8000)
    p_serve.add_argument("-o", "--out", default="dist")
    p_serve.add_argument("--no-browser", action="store_true")
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
