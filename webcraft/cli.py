"""Command line interface: ``webcraft new | build | serve``."""

from __future__ import annotations

import argparse
import os
import runpy
import sys
from pathlib import Path

from . import __version__

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
    index = site.build(args.out, inline=args.inline)
    print(f"Built {len(site.pages)} page(s) -> {index.parent.resolve()}")
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
    p_build.set_defaults(func=cmd_build)

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
