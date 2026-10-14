"""Bir kerelik: eski sayfalardaki içeriği content/ klasörüne JSON olarak çıkarır.

Sonrasında sayfalar yalnızca tools/build_site.py ile content/ üzerinden üretilir.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content"
OUT.mkdir(exist_ok=True)


def meta(s, name, attr="name"):
    m = re.search(r'<meta\s+%s="%s"\s+content="([^"]*)"' % (attr, re.escape(name)), s)
    return html.unescape(m.group(1)) if m else ""


def text(fragment):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", fragment))).strip()


def first(pattern, s, flags=re.S):
    m = re.search(pattern, s, flags)
    return m.group(1).strip() if m else ""


POSTS = ["siber-psikoloji", "dijital-cagda-psikoloji", "terravisa", "lunapara", "altin-vize", "dijital-gocebe"]

for slug in POSTS:
    for lang, suffix in (("tr", ""), ("en", "-en")):
        f = ROOT / f"blog-{slug}{suffix}.html"
        s = f.read_text(encoding="utf-8")
        art = first(r'<article class="article-shell">(.*)</article>', s)
        body = art
        lede = first(r'<p class="lede">(.*?)</p>', art)
        # gövde: lede sonrası
        i = art.find('<p class="lede">')
        if i >= 0:
            body = art[art.find("</p>", i) + 4:]
        metas = [text(x) for x in re.findall(r"<span>(.*?)</span>", first(r'<div class="article-meta">(.*?)</div>', art))]
        data = {
            "slug": slug,
            "lang": lang,
            "file": f.name,
            "title": text(first(r"<h1>(.*?)</h1>", art)),
            "seo_title": html.unescape(first(r"<title>(.*?)</title>", s)),
            "description": meta(s, "description"),
            "category": text(first(r'<div class="category-tag">(.*?)</div>', art)),
            "meta": metas,
            "author": meta(s, "author"),
            "lede": lede,
            "body": body.strip(),
        }
        (OUT / f"blog-{slug}-{lang}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f.name, len(body))

for lang, name in (("tr", "blog.html"), ("en", "blog-en.html")):
    s = (ROOT / name).read_text(encoding="utf-8")
    cards = []
    for m in re.finditer(r'<article class="post-card[^"]*" data-category="([^"]+)">(.*?)</article>', s, re.S):
        cat, c = m.groups()
        cards.append({
            "category_key": cat,
            "kicker": text(first(r'<div class="post-kicker">(.*?)</div>', c)),
            "title": text(first(r"<h3>(.*?)</h3>", c)),
            "meta": [text(x) for x in re.findall(r"<span>(.*?)</span>", first(r'<div class="post-meta">(.*?)</div>', c))],
            "summary": text(first(r"<p>(.*?)</p>", c)),
            "href": first(r'href="([^"]+)"', c),
        })
    (OUT / f"blog-index-{lang}.json").write_text(json.dumps({"title": html.unescape(first(r"<title>(.*?)</title>", s)), "description": meta(s, "description"), "cards": cards}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(name, len(cards))

for name in ("gizlilik.html", "kvkk.html", "modi-kullanim-kosullari.html"):
    s = (ROOT / name).read_text(encoding="utf-8")
    main = first(r"<main>(.*)</main>", s)
    (OUT / name.replace(".html", ".json")).write_text(json.dumps({
        "file": name,
        "title": html.unescape(first(r"<title>(.*?)</title>", s)),
        "description": meta(s, "description"),
        "main": main,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(name, len(main))
