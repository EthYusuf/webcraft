"""Regenerate the screenshots and GIFs used in the README (docs/media/).

    pip install -e .[dev] pygments
    python tools/make_media.py              # everything
    python tools/make_media.py quickstart   # only some: quickstart backgrounds terminal stills

Every image is produced from real WebCraft builds rendered by a headless Chromium
(Chrome or Edge). Set WEBCRAFT_BROWSER to the browser executable if it is not found.
"""

from __future__ import annotations

import html
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "media"
WORK = ROOT / "tools" / ".cache"
sys.path.insert(0, str(ROOT))

PHOTOS = {
    "kahve.jpg": "photo-1442512595331-e89e73853f31",
    "latte.jpg": "photo-1509042239860-f550ce710b93",
    "dag.jpg": "photo-1506905925346-21bda4d32df4",
}
FONTS = ("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800"
         "&family=JetBrains+Mono:wght@400;500;700&display=swap")


# ----------------------------------------------------------------------
# Browser
# ----------------------------------------------------------------------
def find_browser() -> str:
    env = os.environ.get("WEBCRAFT_BROWSER")
    if env:
        return env
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    for name in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge", "msedge", "chrome"):
        if shutil.which(name):
            return shutil.which(name)
    sys.exit("No Chromium browser found. Set WEBCRAFT_BROWSER=/path/to/chrome")


BROWSER = None
PROFILE = Path(tempfile.mkdtemp(prefix="wc-media-"))


def shot(target: Path, out: Path, width: int, height: int, budget: int = 6000, still: bool = True) -> Path:
    """Screenshot a local HTML file at an exact window size.

    ``still`` asks the page for reduced motion, so WebCraft shows content without
    entrance animations — screenshots never catch a half-faded section."""
    global BROWSER
    BROWSER = BROWSER or find_browser()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    cmd = [BROWSER, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
           "--allow-file-access-from-files", f"--user-data-dir={PROFILE}", "--force-device-scale-factor=1",
           f"--window-size={width},{height}", f"--virtual-time-budget={budget}",
           f"--screenshot={out.resolve()}", target.resolve().as_uri()]
    if still:
        cmd.insert(1, "--force-prefers-reduced-motion")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    if not out.exists():
        raise RuntimeError(f"Screenshot failed for {target}")
    return out


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def download_photos() -> Path:
    img = WORK / "img"
    img.mkdir(parents=True, exist_ok=True)
    for name, pid in PHOTOS.items():
        target = img / name
        if not target.exists():
            url = f"https://images.unsplash.com/{pid}?auto=format&fit=crop&w=2400&q=82"
            print("  downloading", name)
            urllib.request.urlretrieve(url, target)
    small = img / "kucuk.jpg"
    if not small.exists():
        from PIL import Image

        with Image.open(img / "kahve.jpg") as im:
            im.convert("RGB").resize((900, 600)).save(small, quality=85)
    return img


def build_site(code: str, out_dir: Path, *, optimize: bool = False) -> Path:
    """Execute site code (without its build line) inside the photo folder and build it."""
    runnable = "\n".join(line for line in code.splitlines() if "site.olustur(" not in line)
    cwd = os.getcwd()
    os.chdir(WORK / "img")
    try:
        ns: dict = {}
        exec(compile(runnable, "<site>", "exec"), ns)  # noqa: S102 - our own demo code
        return ns["site"].build(out_dir, quiet=True, optimize_images=optimize)
    finally:
        os.chdir(cwd)


def highlight_lines(code: str) -> list[str]:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import PythonLexer

    out = highlight(code, PythonLexer(), HtmlFormatter(nowrap=True, noclasses=True, style="github-dark"))
    return out.rstrip("\n").split("\n")


def changed_lines(prev: str, cur: str) -> list[int]:
    import difflib

    a, b = prev.splitlines(), cur.splitlines()
    result = []
    for tag, _i1, _i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag in ("replace", "insert"):
            result.extend(range(j1, j2))
    return result


def typing_states(prev: str, cur: str, steps: int = 3) -> list[str]:
    """Intermediate code states where the changed lines appear gradually (typing effect)."""
    lines = cur.splitlines()
    changed = changed_lines(prev, cur)
    if not changed:
        return []
    total = sum(len(lines[i]) for i in changed)
    states = []
    for s in range(1, steps + 1):
        budget = round(total * s / (steps + 1))
        partial = []
        for idx, line in enumerate(lines):
            if idx not in changed:
                partial.append(line)
            elif budget >= len(line):          # already typed
                partial.append(line)
                budget -= len(line)
            elif budget > 0:                   # being typed: show the cursor here only
                partial.append(line[:budget] + "▌")
                budget = 0
        states.append("\n".join(partial))
    return states


BASE_CSS = """
*{box-sizing:border-box} html,body{margin:0;overflow:hidden}
body{font-family:Inter,system-ui,sans-serif;color:#e6edf3;
  background:radial-gradient(900px 500px at 0% 0%,rgba(124,58,237,.35),transparent 60%),
             radial-gradient(800px 500px at 100% 100%,rgba(14,165,233,.28),transparent 60%),#0b1020;}
.win{background:#0d1117;border:1px solid #30363d;border-radius:12px;overflow:hidden;
  box-shadow:0 24px 60px -20px rgba(0,0,0,.7),0 0 0 1px rgba(255,255,255,.03)}
.bar{height:34px;display:flex;align-items:center;gap:8px;padding:0 14px;background:#161b22;
  border-bottom:1px solid #30363d;font-size:12.5px;color:#9aa4b2}
.dot{width:11px;height:11px;border-radius:50%;display:inline-block}
.r{background:#ff5f57}.y{background:#febc2e}.g{background:#28c840}
.url{margin-left:14px;flex:1;max-width:420px;height:22px;border-radius:6px;background:#0d1117;
  border:1px solid #30363d;display:flex;align-items:center;padding:0 10px;font-size:12px;color:#7d8590}
.brand{font-weight:800;font-size:19px;letter-spacing:-.02em}
.brand b{background:linear-gradient(120deg,#a78bfa,#38bdf8);-webkit-background-clip:text;color:transparent}
"""


def page(body: str, width: int, height: int, css: str = "") -> str:
    return (f'<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{FONTS}">'
            f"<style>{BASE_CSS} html,body{{width:{width}px;height:{height}px}} {css}</style></head>"
            f"<body>{body}</body></html>")


def editor_html(code: str, highlight_idx: list[int], filename: str, max_lines: int) -> str:
    rendered = highlight_lines(code)
    start = 0
    if highlight_idx and max(highlight_idx) >= max_lines - 1:
        start = max(highlight_idx) - max_lines + 2
    rows = []
    for i, line in enumerate(rendered[start:start + max_lines], start=start):
        cls = "ln hl" if i in highlight_idx else "ln"
        line = line.replace("▌", '<span class="cur"></span>')
        rows.append(f'<div class="{cls}"><span class="no">{i + 1}</span><span class="tx">{line or " "}</span></div>')
    return (f'<div class="win editor"><div class="bar"><span class="dot r"></span><span class="dot y"></span>'
            f'<span class="dot g"></span><span style="margin-left:10px">🐍 {filename}</span></div>'
            f'<div class="code">{"".join(rows)}</div></div>')


EDITOR_CSS = """
.editor{display:flex;flex-direction:column;width:100%;min-width:0}
.code{flex:1;padding:12px 0;font:12.5px/1.62 'JetBrains Mono',Consolas,monospace;white-space:pre;overflow:hidden}
.ln{display:flex;padding-right:12px;border-left:3px solid transparent}
.ln.hl{background:rgba(56,139,253,.13);border-left-color:#58a6ff}
.no{width:40px;flex-shrink:0;text-align:right;padding-right:14px;color:#484f58;user-select:none}
.ln.hl .no{color:#a5b4c3}
.cur{display:inline-block;width:8px;height:16px;background:#58a6ff;vertical-align:text-bottom;margin-left:1px}
.browser{display:flex;flex-direction:column}
.view{flex:1;background:#fff;overflow:hidden}
.view img{width:100%;display:block}
.caption{display:flex;align-items:center;gap:14px;font-size:19px;font-weight:600}
.pill{font:700 13px Inter;padding:5px 11px;border-radius:999px;background:rgba(167,139,250,.18);color:#c4b5fd;
  border:1px solid rgba(167,139,250,.35)}
.prog{display:flex;gap:6px;margin-left:auto}
.prog i{width:22px;height:5px;border-radius:3px;background:#30363d}.prog i.on{background:linear-gradient(90deg,#a78bfa,#38bdf8)}
.cmd{font:500 13px 'JetBrains Mono',monospace;color:#7ee787;background:#0d1117;border:1px solid #30363d;
  padding:4px 10px;border-radius:6px}
"""


def make_gif(frames: list[tuple[Path, int]], out: Path, *, dither: bool = False, scale: float = 1.0) -> None:
    from PIL import Image

    images = []
    for path, _ in frames:
        im = Image.open(path).convert("RGB")
        if scale != 1.0:
            im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        images.append(im)
    # One shared palette (built from a sample of frames) keeps colours stable and lets the
    # GIF encoder store only the pixels that change between frames.
    sample = images[:: max(1, len(images) // 6)][:6]
    strip = Image.new("RGB", (images[0].width, images[0].height * len(sample)))
    for i, im in enumerate(sample):
        strip.paste(im, (0, i * im.height))
    palette = strip.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    mode = Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE
    quantized = [im.quantize(palette=palette, dither=mode) for im in images]
    out.parent.mkdir(parents=True, exist_ok=True)
    quantized[0].save(out, save_all=True, append_images=quantized[1:], duration=[d for _, d in frames],
                      loop=0, optimize=True, disposal=1)
    print(f"  ✓ {out.relative_to(ROOT)}  ({out.stat().st_size // 1024} KB, {len(frames)} frames)")


# ----------------------------------------------------------------------
# GIF 1 — step-by-step coding
# ----------------------------------------------------------------------
def _qs_code(menu=True, hero=True, font=False, colors=False, bg=False, photo=False, cards=False,
             footer=False) -> str:
    """Source of the demo site at a given step of the tutorial."""
    lines = ["from webcraft import Site, ArkaPlan", "", 'site = Site("Kahve Evi")']
    if font:
        lines.append('site.yazi_tipi("Poppins", heading="Playfair Display")')
    if colors:
        lines.append('site.renkler(primary="#b45309", secondary="#d97706")')
    if bg:
        lines.append('site.arka_plan("#fffaf5")')
    if menu:
        lines += ["", 'site.menu("☕ Kahve Evi",', '          {"Menü": "#menu", "İletişim": "#iletisim"},',
                  '          cta=("Sipariş Ver", "#iletisim"))']
    if hero:
        lines += ['site.giris("Her yudumda **taze** kahve",',
                  '           "Her sabah kendi kavurduğumuz çekirdekler.",']
        if photo:
            lines += ['           button=("Menüyü Gör", "#menu"),',
                      '           background=ArkaPlan(resim="kahve.jpg",',
                      '                               karartma="dark", yazi="light"))']
        else:
            lines.append('           button=("Menüyü Gör", "#menu"))')
    if cards:
        lines += ["site.kartlar([", '    ("☕", "Espresso", "Yoğun ve kadifemsi."),',
                  '    ("🥛", "Latte", "Bol sütlü, yumuşak içim."),',
                  '    ("🍰", "Tatlılar", "Her gün taze, ev yapımı."),',
                  '], title="Menü", id="menu")']
    if footer:
        lines += ['site.alt_bilgi("© 2026 Kahve Evi")', "", "site.olustur()   # → dist/index.html"]
    return "\n".join(lines) + "\n"


STYLE = dict(font=True, colors=True, bg=True)
QUICKSTART = [
    ("Site oluştur", _qs_code(menu=False, hero=False)),
    ("Menü ekle", _qs_code(hero=False)),
    ("Giriş bölümü", _qs_code()),
    ("Yazı tipi — Google Fonts otomatik yüklenir", _qs_code(font=True)),
    ("Marka renkleri", _qs_code(font=True, colors=True)),
    ("Arka plan rengi", _qs_code(**STYLE)),
    ("Arka plana fotoğraf + karartma", _qs_code(**STYLE, photo=True)),
    ("Kartlar", _qs_code(**STYLE, photo=True, cards=True)),
    ("Derle → statik site hazır", _qs_code(**STYLE, photo=True, cards=True, footer=True)),
]


def gif_quickstart() -> None:
    print("GIF: quickstart")
    W, H = 1180, 664
    work = WORK / "quickstart"
    previews = []
    for i, (_, code) in enumerate(QUICKSTART):
        index = build_site(code, work / f"site{i}")
        previews.append(shot(index, work / f"preview{i}.png", 1280, 1000, budget=7000))

    frames: list[tuple[Path, int]] = []
    prev_code = ""
    n = len(QUICKSTART)
    for i, (caption, code) in enumerate(QUICKSTART):
        states = typing_states(prev_code, code) if prev_code else []
        hl = changed_lines(prev_code, code) if prev_code else list(range(len(code.splitlines())))
        sequence = [(s, previews[i - 1] if i else None, 110) for s in states] + [(code, previews[i], 2300)]
        if i == n - 1:
            sequence[-1] = (code, previews[i], 4200)
        for k, (state, preview, duration) in enumerate(sequence):
            prog = "".join(f'<i class="{"on" if j <= i else ""}"></i>' for j in range(n))
            view = f'<img src="{preview.resolve().as_uri()}">' if preview else ""
            body = f"""
<div style="padding:20px 24px;height:100%;display:flex;flex-direction:column;gap:14px">
  <div class="caption"><span class="brand">✦ Web<b>Craft</b></span>
    <span class="pill">Adım {i + 1}/{n}</span><span>{html.escape(caption)}</span>
    <div class="prog">{prog}</div></div>
  <div style="flex:1;display:flex;gap:18px;min-height:0">
    <div style="width:560px;flex-shrink:0;display:flex">{editor_html(state, hl, "site.py", 26)}</div>
    <div class="win browser" style="flex:1"><div class="bar"><span class="dot r"></span><span class="dot y"></span>
      <span class="dot g"></span><span class="url">🔒 localhost:8000</span></div><div class="view">{view}</div></div>
  </div>
</div>"""
            frame_html = work / f"frame{i:02d}_{k:02d}.html"
            frame_html.write_text(page(body, W, H, EDITOR_CSS), encoding="utf-8")
            frames.append((shot(frame_html, frame_html.with_suffix(".png"), W, H, budget=1500), duration))
        prev_code = code
    make_gif(frames, OUT / "quickstart.gif", dither=True)
    shutil.copy(frames[-1][0], OUT / "quickstart-final.png")


# ----------------------------------------------------------------------
# GIF 2 — background options
# ----------------------------------------------------------------------
BG_STEPS = [
    ("Sadece fotoğraf", ['resim="dag.jpg"', 'yazi="light"']),
    ("karartma — yazı her fotoğrafta okunur", ['resim="dag.jpg"', 'karartma="dark"', 'yazi="light"']),
    ("Alttan gradyan + görünen kısım (konum)", ['resim="dag.jpg"', 'konum="orta alt"', 'karartma="bottom"',
                                                 'yazi="light"']),
    ("Bulanıklık — yazı net kalır", ['resim="dag.jpg"', 'konum="orta alt"', 'karartma="bottom"',
                                     "bulaniklik=6", 'yazi="light"']),
    ("Siyah-beyaz + marka rengi kaplama", ['resim="dag.jpg"', 'konum="orta alt"', 'karartma="brand"',
                                           "siyah_beyaz=1", 'yazi="light"']),
    ("Vinyet + Ken Burns (yavaş yakınlaşma)", ['resim="dag.jpg"', 'konum="orta alt"', 'karartma="vignette"',
                                               "parlaklik=1.1", 'hareket="kenburns"', 'yazi="light"']),
]


def _bg_code(args: list[str]) -> str:
    inner = ",\n".join(f"        {a}" for a in args)
    return (f'site = Site("Vitrin", theme="dark")\n'
            f'site.renkler("#8b5cf6", "#ec4899")\n\n'
            f'site.giris(\n    "Arka plan **sizin** elinizde",\n    "Tek satırla sinematik görünüm",\n'
            f'    button=("Keşfet", "#"),\n    full_height=True,\n'
            f"    background=ArkaPlan(\n{inner},\n    ),\n)\n")


def gif_backgrounds() -> None:
    print("GIF: backgrounds")
    W, H = 1180, 600
    work = WORK / "backgrounds"
    frames = []
    prev = ""
    n = len(BG_STEPS)
    for i, (caption, args) in enumerate(BG_STEPS):
        code = _bg_code(args)
        index = build_site("from webcraft import Site, ArkaPlan\n" + code, work / f"site{i}")
        preview = shot(index, work / f"preview{i}.png", 1280, 900, budget=7000)
        hl = changed_lines(prev, code) if prev else [i2 for i2, line in enumerate(code.splitlines()) if "=" in line and "    " in line and i2 > 9]
        prog = "".join(f'<i class="{"on" if j <= i else ""}"></i>' for j in range(n))
        body = f"""
<div style="padding:20px 24px;height:100%;display:flex;flex-direction:column;gap:14px">
  <div class="caption"><span class="brand">✦ Web<b>Craft</b></span><span class="pill">ArkaPlan</span>
    <span>{html.escape(caption)}</span><div class="prog">{prog}</div></div>
  <div style="flex:1;display:flex;gap:18px;min-height:0">
    <div style="width:430px;flex-shrink:0;display:flex">{editor_html(code, hl, "site.py", 24)}</div>
    <div class="win browser" style="flex:1"><div class="bar"><span class="dot r"></span><span class="dot y"></span>
      <span class="dot g"></span><span class="url">🔒 localhost:8000</span></div>
      <div class="view" style="background:#0b1120"><img src="{preview.resolve().as_uri()}"></div></div>
  </div>
</div>"""
        frame_html = work / f"frame{i:02d}.html"
        frame_html.write_text(page(body, W, H, EDITOR_CSS), encoding="utf-8")
        frames.append((shot(frame_html, frame_html.with_suffix(".png"), W, H, budget=1500), 2600))
        prev = code
    make_gif(frames, OUT / "backgrounds.gif", dither=True)


# ----------------------------------------------------------------------
# GIF 3 — terminal: image tools
# ----------------------------------------------------------------------
TERM_CSS = """
.term{font:13px/1.55 'JetBrains Mono',Consolas,monospace;padding:16px 18px;white-space:pre;color:#c9d1d9}
.pr{color:#7ee787}.pa{color:#79c0ff}.e{color:#ff7b72}.w{color:#e3b341}.i{color:#79c0ff}.ok{color:#7ee787}
.bar2{color:#a78bfa}.dim{color:#7d8590}.cur{display:inline-block;width:8px;height:15px;background:#c9d1d9;
vertical-align:text-bottom}
"""


def colorize(line: str) -> str:
    esc = html.escape(line)
    for sym, cls in (("✗", "e"), ("⚠", "w"), ("ℹ", "i"), ("✓", "ok")):
        if sym in esc:
            return esc.replace(sym, f'<span class="{cls}">{sym}</span>', 1)
    if "█" in esc:
        head, _, tail = esc.partition(" ")
        return f'<span class="bar2">{head}</span> {tail}'
    if esc.strip().startswith("→"):
        return f'<span class="dim">{esc}</span>'
    if esc.startswith("▸"):
        return f'<span class="ok">{esc}</span>'
    return esc


def run_cli(args: list[str]) -> list[str]:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", COLUMNS="110")
    result = subprocess.run([sys.executable, "-m", "webcraft", *args], cwd=WORK / "img", env=env,
                            capture_output=True, text=True, encoding="utf-8")
    # Plain cut (not textwrap.shorten, which would also strip the indentation).
    return [line if len(line) <= 118 else line[:117] + "…" for line in result.stdout.rstrip().splitlines()]


def gif_terminal() -> None:
    print("GIF: terminal")
    W, H = 1180, 640
    work = WORK / "terminal"
    work.mkdir(parents=True, exist_ok=True)
    sessions = [
        ("Bir alan için önerilen boyut", ["guide", "kart"]),
        ("Bu fotoğraf nereye uygun?", ["check-image", "kahve.jpg", "--top", "4"]),
        ("Hero arka planı için yeterli mi?", ["check-image", "kucuk.jpg", "-s", "hero"]),
    ]
    frames = []
    for s_idx, (caption, args) in enumerate(sessions):
        command = "webcraft " + " ".join(args)
        output = run_cli(args)[:28]
        if args[0] == "check-image" and "-s" not in args:
            output = output[:9]  # suggestions + headline are the interesting part
        states = []
        for k in range(1, 6):
            states.append((command[: round(len(command) * k / 5)], [], True, 90))
        chunks = 3
        for c in range(1, chunks + 1):
            states.append((command, output[: round(len(output) * c / chunks)], False, 260 if c < chunks else 3600))
        for k, (typed, out_lines, cursor, duration) in enumerate(states):
            prompt = (f'<span class="pr">➜</span> <span class="pa">~/kahve-evi</span> '
                      f'{html.escape(typed)}{"<span class=cur></span>" if cursor else ""}')
            body_lines = "\n".join(colorize(line) for line in out_lines)
            prog = "".join(f'<i class="{"on" if j <= s_idx else ""}"></i>' for j in range(len(sessions)))
            body = f"""
<div style="padding:20px 24px;height:100%;display:flex;flex-direction:column;gap:14px">
  <div class="caption"><span class="brand">✦ Web<b>Craft</b></span><span class="pill">Görsel araçları</span>
    <span>{html.escape(caption)}</span><div class="prog">{prog}</div></div>
  <div class="win" style="flex:1"><div class="bar"><span class="dot r"></span><span class="dot y"></span>
    <span class="dot g"></span><span style="margin-left:10px">Terminal — webcraft</span></div>
    <div class="term">{prompt}\n{body_lines}</div></div>
</div>"""
            frame_html = work / f"frame{s_idx}_{k:02d}.html"
            frame_html.write_text(page(body, W, H, EDITOR_CSS + TERM_CSS), encoding="utf-8")
            frames.append((shot(frame_html, frame_html.with_suffix(".png"), W, H, budget=1200), duration))
    make_gif(frames, OUT / "image-tools.gif")


# ----------------------------------------------------------------------
# Still images
# ----------------------------------------------------------------------
def framed(img: Path, url: str, width: int, extra_css: str = "") -> str:
    return (f'<div class="win" style="width:{width}px"><div class="bar"><span class="dot r"></span>'
            f'<span class="dot y"></span><span class="dot g"></span><span class="url">🔒 {url}</span></div>'
            f'<img src="{img.resolve().as_uri()}" style="width:100%;display:block;{extra_css}"></div>')


def phone_html(site_index: Path, w: int = 390, h: int = 844, status_bg: str = "#fffaf5") -> str:
    """A phone mockup: status bar (with the camera island) above a live iframe of the site."""
    bar = 48
    return f"""<div style="width:{w + 24}px;height:{h + 24}px;border-radius:52px;background:#0a0a0a;padding:12px;
      box-shadow:0 30px 70px -20px rgba(0,0,0,.8),0 0 0 2px #2a2a2a">
      <div style="width:{w}px;height:{h}px;border-radius:40px;overflow:hidden;background:{status_bg};position:relative">
        <div style="height:{bar}px;display:flex;align-items:center;justify-content:space-between;padding:6px 30px 0;
          font:600 15px Inter;color:#111">
          <span>9:41</span>
          <span style="width:112px;height:32px;border-radius:20px;background:#000"></span>
          <span style="font-size:12px;letter-spacing:1px">▮▮▮ ◔</span></div>
        <iframe src="{site_index.resolve().as_uri()}" style="width:{w}px;height:{h - bar}px;border:0;display:block"></iframe>
      </div></div>"""


def stills() -> None:
    print("Stills")
    work = WORK / "stills"
    work.mkdir(parents=True, exist_ok=True)
    final_code = QUICKSTART[-1][1]
    kahve = build_site(final_code, work / "kahve", optimize=True)

    # Landing example (examples/landing.py)
    os.chdir(ROOT)
    ns: dict = {}
    exec(compile((ROOT / "examples" / "landing.py").read_text(encoding="utf-8").split('if __name__')[0],
                 "landing", "exec"), ns)
    ns["site"].build(work / "landing", quiet=True)
    landing = work / "landing" / "index.html"
    ns2: dict = {}
    exec(compile((ROOT / "examples" / "backgrounds.py").read_text(encoding="utf-8").split('if __name__')[0],
                 "backgrounds", "exec"), ns2)
    ns2["site"].build(work / "bgshow", quiet=True)

    # 1) Banner
    hero_shot = shot(kahve, work / "kahve-desktop.png", 1440, 900, budget=8000)
    banner_body = f"""
<div style="height:100%;display:flex;align-items:center;padding:0 64px;gap:56px">
  <div style="flex:1">
    <div style="font:800 64px/1 Inter;letter-spacing:-.04em">✦ Web<span style="background:linear-gradient(120deg,#a78bfa,#38bdf8);-webkit-background-clip:text;color:transparent">Craft</span></div>
    <div style="font:500 23px/1.45 Inter;color:#c9d1d9;margin:20px 0 26px">Basit Python komutlarıyla<br><b style="color:#fff">profesyonel web siteleri.</b></div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;font:600 13px Inter">
      <span class="pill">Python → JSON → WebCraft.js</span><span class="pill">18 bileşen</span>
      <span class="pill">7 tema</span><span class="pill">Akıllı görsel rehberi</span></div>
  </div>
  <div style="position:relative;width:640px;height:360px">
    <div style="position:absolute;right:0;top:0;transform:perspective(1400px) rotateY(-10deg) rotateX(4deg)">
      {framed(hero_shot, "kahve-evi.dev", 600)}</div>
    <div class="win" style="position:absolute;left:-30px;bottom:-34px;width:330px;font:12.5px/1.6 'JetBrains Mono';padding:14px 16px;white-space:pre;color:#c9d1d9"><span style="color:#ff7b72">from</span> webcraft <span style="color:#ff7b72">import</span> Site
site = Site(<span style="color:#a5d6ff">"Kahve Evi"</span>)
site.yazi_tipi(<span style="color:#a5d6ff">"Poppins"</span>)
site.giris(<span style="color:#a5d6ff">"Her yudumda taze"</span>)
site.olustur()</div>
  </div>
</div>"""
    banner_css = ".pill{padding:7px 13px;border-radius:999px;background:rgba(167,139,250,.14);border:1px solid rgba(167,139,250,.35);color:#ddd6fe}"
    b = work / "banner.html"
    b.write_text(page(banner_body, 1280, 440, banner_css), encoding="utf-8")
    shot(b, OUT / "banner.png", 1280, 440, budget=3000)
    print("  ✓ docs/media/banner.png")

    # 2) Landing page in a browser frame
    landing_shot = shot(landing, work / "landing.png", 1440, 900, budget=8000)
    lf = work / "landing-frame.html"
    lf.write_text(page(f'<div style="padding:40px;display:flex;justify-content:center">{framed(landing_shot, "nova.studio", 1200)}</div>',
                       1280, 840), encoding="utf-8")
    shot(lf, OUT / "landing.png", 1280, 840, budget=3000)
    print("  ✓ docs/media/landing.png")

    # 3) Responsive: desktop + phone
    rf = work / "responsive.html"
    rf.write_text(page(f"""<div style="height:100%;display:flex;align-items:center;justify-content:center;gap:40px;padding:30px">
      {framed(hero_shot, "kahve-evi.dev", 900)}{phone_html(kahve)}</div>""", 1440, 920), encoding="utf-8")
    shot(rf, OUT / "responsive.png", 1440, 920, budget=9000)
    print("  ✓ docs/media/responsive.png")

    # 4) Theme grid
    from webcraft import THEMES

    tiles = []
    for name in THEMES:
        code = f'''from webcraft import Site
site = Site("{name}", theme="{name}")
site.menu("✦ {name.title()}", {{"Ürün": "#", "Fiyat": "#"}}, cta=("Başla", "#"))
site.giris("Tema: **{name}**", "theme=\\"{name}\\" ile tek satırda", button=("Başla", "#"), buttons=[("Daha fazla", "#")])
site.kartlar([("⚡", "Hızlı", "Statik HTML"), ("🎨", "Şık", "Hazır temalar"), ("📱", "Mobil", "Her ekranda")])
'''
        idx = build_site(code, work / f"theme-{name}")
        tiles.append((name, shot(idx, work / f"theme-{name}.png", 1280, 860, budget=7000)))
    grid = "".join(f'<div><div class="win"><img src="{p.resolve().as_uri()}" style="width:100%;display:block"></div>'
                   f'<div style="text-align:center;margin-top:10px;font:600 15px Inter">theme="{n}"</div></div>'
                   for n, p in tiles)
    grid += ('<div style="display:flex;align-items:center;justify-content:center;text-align:center;'
             'font:600 16px/1.6 Inter;color:#9aa4b2;border:1.5px dashed #30363d;border-radius:12px;padding:20px">'
             'site.tema("dark")<br>.renkler(primary=...)<br>.yazi_tipi(...)<br>— ya da kendi temanız</div>')
    tf = work / "themes.html"
    tf.write_text(page(f'<div style="padding:32px;display:grid;grid-template-columns:repeat(4,1fr);gap:26px 22px">{grid}</div>',
                       1440, 640), encoding="utf-8")
    shot(tf, OUT / "themes.png", 1440, 640, budget=4000)
    print("  ✓ docs/media/themes.png")

    # 5) Background showcase hero
    bg_shot = shot(work / "bgshow" / "index.html", work / "bgshow.png", 1440, 860, budget=9000)
    bf = work / "bg-frame.html"
    bf.write_text(page(f'<div style="padding:40px;display:flex;justify-content:center">{framed(bg_shot, "vitrin.dev", 1200)}</div>',
                       1280, 800), encoding="utf-8")
    shot(bf, OUT / "backgrounds.png", 1280, 800, budget=3000)
    print("  ✓ docs/media/backgrounds.png")

    # 6) Build report (real output of an optimised build)
    report_code = final_code.replace('ArkaPlan(resim="kahve.jpg"', 'ArkaPlan(resim="kucuk.jpg"')
    report_code = report_code.replace('("🥛", "Latte", "Bol sütlü, yumuşak içim."),',
                                      '{"icon": "🥛", "title": "Latte", "text": "Bol sütlü.", "image": "latte.jpg"},')
    report_file = work / "report-site.py"
    report_file.write_text(report_code.replace("site.olustur()   # → dist/index.html", ""), encoding="utf-8")
    shutil.copy(report_file, WORK / "img" / "site.py")
    lines = run_cli(["build", "site.py", "--optimize", "-o", str(work / "report-out")])
    term = "\n".join(colorize(line) for line in lines if line.strip() or True)
    prompt = '<span class="pr">➜</span> <span class="pa">~/kahve-evi</span> webcraft build site.py --optimize'
    rpt = work / "report.html"
    height = 120 + 21 * (len(lines) + 1)
    rpt.write_text(page(f'<div style="padding:28px"><div class="win"><div class="bar"><span class="dot r"></span>'
                        f'<span class="dot y"></span><span class="dot g"></span><span style="margin-left:10px">'
                        f'Terminal — derleme raporu</span></div><div class="term">{prompt}\n{term}</div></div></div>',
                        1180, height, EDITOR_CSS + TERM_CSS), encoding="utf-8")
    shot(rpt, OUT / "build-report.png", 1180, height, budget=2500)
    print("  ✓ docs/media/build-report.png")


def main() -> None:
    wanted = set(sys.argv[1:]) or {"quickstart", "backgrounds", "terminal", "stills"}
    OUT.mkdir(parents=True, exist_ok=True)
    print("Photos")
    download_photos()
    if "stills" in wanted:
        stills()
    if "quickstart" in wanted:
        gif_quickstart()
    if "backgrounds" in wanted:
        gif_backgrounds()
    if "terminal" in wanted:
        gif_terminal()
    shutil.rmtree(PROFILE, ignore_errors=True)


if __name__ == "__main__":
    main()
