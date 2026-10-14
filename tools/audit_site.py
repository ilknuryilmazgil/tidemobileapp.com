"""Site denetimi: SEO, bağlantılar, em dash ve kalıp ifade taraması.

Kullanım: python tools/audit_site.py
"""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.glob("*.html") if not p.name.startswith("_"))
SLOP = [
    "seamless", "elevate", "unlock", "cutting-edge", "game-changer", "game changer", "delve", "tapestry", "harness the",
    "in today's", "revolutioniz", "next-level", "next level", "unleash", "empower", "supercharge", "world-class", "state-of-the-art",
    "premium execution", "bir sonraki seviye", "yeniden tanımlıyor", "sınırları zorlayan", "dijital dönüşüm yolculuğu",
    "kod yığını", "insani dokunuş", "standartların üzerine", "rafine bir uzantı", "eşsiz deneyim", "benzersiz deneyim",
]
errors, warns = [], []


def visible(s):
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", s, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", s))


ids_cache = {}


def ids_of(path):
    if path not in ids_cache:
        ids_cache[path] = set(re.findall(r'\bid="([^"]+)"', path.read_text(encoding="utf-8")))
    return ids_cache[path]


for p in PAGES:
    s = p.read_text(encoding="utf-8")
    n = p.name
    if "—" in s or "–" in s:
        errors.append(f"{n}: em/en dash")
    h1 = re.findall(r"<h1[\s>]", s)
    if len(h1) != 1:
        errors.append(f"{n}: {len(h1)} adet h1")
    t = re.search(r"<title>(.*?)</title>", s, re.S)
    d = re.search(r'<meta name="description" content="([^"]*)"', s)
    if not t:
        errors.append(f"{n}: title yok")
    elif not 20 <= len(html.unescape(t.group(1))) <= 75:
        warns.append(f"{n}: title {len(html.unescape(t.group(1)))} karakter")
    if not d:
        errors.append(f"{n}: description yok")
    elif not 70 <= len(html.unescape(d.group(1))) <= 175:
        warns.append(f"{n}: description {len(html.unescape(d.group(1)))} karakter")
    if 'rel="canonical"' not in s:
        errors.append(f"{n}: canonical yok")
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            json.loads(m.group(1))
        except Exception as e:
            errors.append(f"{n}: JSON-LD bozuk ({e})")
    for img in re.findall(r'<img\b[^>]*>', s):
        if "alt=" not in img:
            errors.append(f"{n}: alt'sız görsel {img[:60]}")
    for attr in re.findall(r'(?:href|src|srcset|poster)="([^"]+)"', s):
        for ref in attr.split(","):
            ref = ref.strip().split(" ")[0]
            if not ref or ref.startswith(("http", "mailto:", "tel:", "data:", "//")):
                continue
            u = urlparse(ref)
            target = ROOT / (u.path.lstrip("/") if u.path.startswith("/") else u.path) if u.path else p
            if u.path in ("", "/"):
                target = p if u.path == "" else ROOT / "index.html"
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                errors.append(f"{n}: kırık bağlantı {ref}")
            elif u.fragment and target.suffix == ".html" and u.fragment not in ids_of(target):
                errors.append(f"{n}: olmayan çapa {ref}")
    low = visible(s).lower()
    for w in SLOP:
        if w in low:
            warns.append(f"{n}: kalıp ifade '{w}'")
    if re.search(r"\bTidw\b", visible(s)):
        errors.append(f"{n}: Tidw yazımı")

print(f"{len(PAGES)} sayfa denetlendi")
for e in errors:
    print("HATA ", e)
for w in warns:
    print("UYARI", w)
sys.exit(1 if errors else 0)
