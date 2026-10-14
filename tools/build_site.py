"""Tide Mobile alt sayfa üreticisi.

content/ klasöründeki içerikten blog yazılarını, blog listelerini, teknik ortaklık
ve hukuki sayfaları ana sayfayla aynı tasarım sisteminde üretir. Ayrıca her yazı
için paylaşım görseli (OG) ve sitemap.xml oluşturur.

Kurallar:
  - Em dash (U+2014) veya en dash (U+2013) içeren bir çıktı üretilirse durur.
  - Görünen marka adı her zaman "Tide Mobile".

Kullanım: python tools/build_site.py
"""
import html
import json
import math
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
C = ROOT / "content"
SITE = "https://tidemobileapp.com"
TODAY = date.today().isoformat()
ORG = SITE + "/#org"

T = {
 "tr": {
  "home": "index.html", "skip": "İçeriğe geç", "menu": "Menüyü aç", "home_label": "Tide Mobile ana sayfa",
  "nav": [("#hakkimizda", "Hakkımızda"), ("#vizyon", "Vizyon"), ("#ekip", "Ekip"), ("#yol-haritasi", "Yol Haritası"), ("#uygulamalar", "Uygulamalar"), ("teknik-ortaklik.html", "Teknik Ortaklık"), ("blog.html", "Blog"), ("#iletisim", "İletişim")],
  "lang_btn": "EN", "lang_label": "English version", "crumb_home": "Ana Sayfa",
  "legal": [("kvkk.html", "KVKK Aydınlatma Metni"), ("gizlilik.html", "Gizlilik Politikası"), ("modi-kullanim-kosullari.html", "Modi Kullanım Koşulları"), ("gizlilik.html#3-cerezler-ve-benzeri-teknolojiler", "Çerez Tercihleri")],
  "rights": "© 2026 Tide Mobile. Tüm hakları saklıdır.", "city": "Adana, Türkiye",
  "months": ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"],
  "read": "{} dk okuma", "toc": "Bu yazıda", "author": "Yazar", "related_label": "Okumaya devam et", "related_h": "Benzer <em>yazılar.</em>",
  "all_posts": "Tüm yazılar", "blog": "Blog", "updated": "Son güncelleme", "contents": "İçindekiler", "locale": "tr_TR",
  "roles": {"Cansun Tanıl Tabakoğlu": "Kurucu Ortak, Ürün ve Büyüme", "İlknur Yılmazgil": "Kurucu Ortak, Psikoloji ve İçerik"},
  "all": "Tümü",
 },
 "en": {
  "home": "index-en.html", "skip": "Skip to content", "menu": "Open menu", "home_label": "Tide Mobile home",
  "nav": [("#about", "About"), ("#vision", "Vision"), ("#team", "Team"), ("#roadmap", "Roadmap"), ("#apps", "Apps"), ("teknik-ortaklik-en.html", "Technical Partnership"), ("blog-en.html", "Blog"), ("#contact", "Contact")],
  "lang_btn": "TR", "lang_label": "Türkçe sürüm", "crumb_home": "Home",
  "legal": [("kvkk.html", "KVKK Privacy Notice (TR)"), ("gizlilik.html", "Privacy Policy (TR)"), ("modi-kullanim-kosullari.html", "Modi Terms of Use (TR)"), ("gizlilik.html#3-cerezler-ve-benzeri-teknolojiler", "Cookie Settings")],
  "rights": "© 2026 Tide Mobile. All rights reserved.", "city": "Adana, Türkiye",
  "months": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
  "read": "{} min read", "toc": "In this article", "author": "Author", "related_label": "Keep reading", "related_h": "Related <em>articles.</em>",
  "all_posts": "All articles", "blog": "Blog", "updated": "Last updated", "contents": "Contents", "locale": "en_US",
  "roles": {"Cansun Tanıl Tabakoğlu": "Co-Founder, Product & Growth", "İlknur Yılmazgil": "Co-Founder, Psychology & Content"},
  "all": "All",
 },
}

ICON = '''<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
  <symbol id="i-arrow" viewBox="0 0 24 24"><path d="M4.5 12h15M13.5 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  <symbol id="i-globe" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.8 3.8 5.8 3.8 9s-1.2 6.2-3.8 9c-2.6-2.8-3.8-5.8-3.8-9S9.4 5.8 12 3z"/></g></symbol>
  <symbol id="i-user" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="8.5" r="3.8"/><path d="M4.5 20c.8-3.6 3.8-5.8 7.5-5.8s6.7 2.2 7.5 5.8" stroke-linecap="round"/></g></symbol>
  <symbol id="i-cal" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/></g></symbol>
  <symbol id="i-clock" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/></g></symbol>
  <symbol id="i-check" viewBox="0 0 24 24"><path d="m5 12.5 4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></symbol>
</defs></svg>'''

SOCIAL = '''<a href="https://www.linkedin.com/company/tide-mobile/" rel="noopener" aria-label="LinkedIn"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4.98 3.5A1.98 1.98 0 1 1 3 5.48 1.98 1.98 0 0 1 4.98 3.5ZM3.25 8h3.46v12H3.25Zm5.65 0h3.32v1.64h.05A3.64 3.64 0 0 1 15.55 7.7c3.5 0 4.15 2.3 4.15 5.29V20h-3.46v-6.19c0-1.48-.03-3.38-2.06-3.38-2.06 0-2.38 1.61-2.38 3.27V20H8.9Z"/></svg></a>
            <a href="https://www.instagram.com/tidemobile" rel="noopener" aria-label="Instagram"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7.75 2h8.5A5.75 5.75 0 0 1 22 7.75v8.5A5.75 5.75 0 0 1 16.25 22h-8.5A5.75 5.75 0 0 1 2 16.25v-8.5A5.75 5.75 0 0 1 7.75 2Zm0 1.8A3.95 3.95 0 0 0 3.8 7.75v8.5A3.95 3.95 0 0 0 7.75 20.2h8.5a3.95 3.95 0 0 0 3.95-3.95v-8.5A3.95 3.95 0 0 0 16.25 3.8h-8.5Zm8.95 1.35a1.15 1.15 0 1 1 0 2.3 1.15 1.15 0 0 1 0-2.3ZM12 6.85A5.15 5.15 0 1 1 6.85 12 5.16 5.16 0 0 1 12 6.85Zm0 1.8A3.35 3.35 0 1 0 15.35 12 3.35 3.35 0 0 0 12 8.65Z"/></svg></a>
            <a href="https://www.tiktok.com/@tidemobile" rel="noopener" aria-label="TikTok"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14.2 3h2.38a4.9 4.9 0 0 0 4.17 4.15v2.43a7.27 7.27 0 0 1-4.15-1.3v6.32a5.6 5.6 0 1 1-5.6-5.6c.3 0 .6.03.88.08v2.47a3.14 3.14 0 0 0-.88-.13 3.18 3.18 0 1 0 3.2 3.18Z"/></svg></a>'''

V = "9"  # önbellek sürümü


def esc(s):
    return html.escape(s, quote=True)


def strip_tags(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def slugify(s):
    tr = str.maketrans("çğıöşüÇĞİÖŞÜâîû", "cgiosuCGIOSUaiu")
    s = strip_tags(s).translate(tr).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60]


def fmt_date(iso, lang):
    y, m, d = iso.split("-")
    mo = T[lang]["months"][int(m) - 1]
    return f"{int(d)} {mo} {y}" if lang == "tr" else f"{mo} {int(d)}, {y}"


def git_dates(name):
    def run(*a):
        return subprocess.run(["git", "log", *a, "--", name], cwd=ROOT, capture_output=True, text=True).stdout.split()
    first = run("--diff-filter=A", "--format=%as")
    last = run("-1", "--format=%as")
    return (first[-1] if first else TODAY), (last[0] if last else TODAY)


def head(lang, title, desc, path, alt=None, og=None, og_type="website", ld=None, extra=""):
    t = T[lang]
    url = f"{SITE}/{path}"
    og = og or f"{SITE}/assets/home/og-tidemobile{'-en' if lang == 'en' else ''}.jpg"
    alts = ""
    if alt:
        tr_p, en_p = (path, alt) if lang == "tr" else (alt, path)
        alts = (f'\n  <link rel="alternate" hreflang="tr" href="{SITE}/{tr_p}" />'
                f'\n  <link rel="alternate" hreflang="en" href="{SITE}/{en_p}" />'
                f'\n  <link rel="alternate" hreflang="x-default" href="{SITE}/{en_p}" />')
    ld_html = f'\n  <script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(",", ":"))}</script>' if ld else ""
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}" />
  <link rel="canonical" href="{url}" />{alts}
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1" />
  <meta name="theme-color" content="#f5ecdb" />
  <link rel="icon" type="image/png" href="favicon.png" />
  <link rel="apple-touch-icon" href="assets/home/apple-touch-icon.png" />
  <meta property="og:type" content="{og_type}" />
  <meta property="og:site_name" content="Tide Mobile" />
  <meta property="og:locale" content="{t['locale']}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(desc)}" />
  <meta property="og:image" content="{og}" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(title)}" />
  <meta name="twitter:description" content="{esc(desc)}" />
  <meta name="twitter:image" content="{og}" />{extra}{ld_html}
  <link rel="preload" as="font" type="font/woff2" href="assets/fonts/general-sans-500.woff2" crossorigin />
  <link rel="preload" as="font" type="font/woff2" href="assets/fonts/switzer-400.woff2" crossorigin />
  <link rel="stylesheet" href="assets/home/home.css?v={V}" />
  <link rel="stylesheet" href="assets/home/page.css?v={V}" />
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('consent','default',{{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied'}});</script>
  <script src="assets/consent.js?v=1" defer></script>
</head>
<body>
  <a class="skip" href="#icerik">{t['skip']}</a>
  {ICON}
'''


def nav(lang, alt, active=None):
    t = T[lang]
    items = []
    for href, label in t["nav"]:
        h = (t["home"] + href) if href.startswith("#") else href
        cur = ' aria-current="page"' if active and href == active else ""
        items.append(f'<li><a href="{h}"{cur}>{label}</a></li>')
    alt_href = alt or (T["en" if lang == "tr" else "tr"]["home"])
    alt_lang = "en" if lang == "tr" else "tr"
    return f'''  <header class="nav is-solid" id="nav">
    <div class="wrap nav-in">
      <a href="{t['home']}" class="wm" aria-label="{t['home_label']}"><img class="wm-logo" src="assets/home/tide-logo-96.webp" srcset="assets/home/tide-logo-96.webp 1x, assets/home/tide-logo-192.webp 2x" width="48" height="48" alt="" /><img class="wm-type" src="assets/home/tide-yazi.svg" width="271" height="174" alt="Tide Mobile" /></a>
      <nav aria-label="{'Ana menü' if lang == 'tr' else 'Main menu'}">
        <ul class="nav-links" id="navLinks">
          {chr(10).join('          ' + i for i in items).strip()}
        </ul>
      </nav>
      <div class="nav-right">
        <a href="{alt_href}" class="nav-lang" hreflang="{alt_lang}" lang="{alt_lang}" aria-label="{t['lang_label']}">{t['lang_btn']} <svg aria-hidden="true"><use href="#i-globe"/></svg></a>
        <button class="nav-toggle" id="navToggle" aria-label="{t['menu']}" aria-expanded="false" aria-controls="navLinks"><span></span><span></span><span></span></button>
      </div>
    </div>
  </header>
'''


def footer(lang):
    t = T[lang]
    links = "\n".join(f'            <li><a href="{(t["home"] + h) if h.startswith("#") else h}">{l}</a></li>' for h, l in t["nav"])
    legal = "\n".join(f'            <li><a href="{h}"{" data-cerez-tercih" if "cerez" in h else ""}>{l}</a></li>' for h, l in t["legal"])
    return f'''  <footer class="footer">
    <svg class="foot-waves" viewBox="0 0 1440 120" preserveAspectRatio="none" aria-hidden="true">
      <path d="M0 60C180 20 360 10 560 40s360 70 560 50 260-60 320-70V120H0z" fill="#329aa1"/>
      <path d="M0 92C220 52 420 50 640 74s380 40 560 20 200-34 240-44V120H0z" fill="#1c475f"/>
    </svg>
    <div class="foot-body">
      <div class="wrap">
        <div class="foot-top">
          <a href="{t['home']}" class="wm" aria-label="{t['home_label']}"><img class="wm-logo" src="assets/home/tide-logo-96.webp" srcset="assets/home/tide-logo-96.webp 1x, assets/home/tide-logo-192.webp 2x" width="48" height="48" alt="" /><img class="wm-type" src="assets/home/tide-yazi-krem.svg" width="271" height="174" alt="Tide Mobile" /></a>
          <ul class="foot-links">
{links}
          </ul>
          <div class="social">
            {SOCIAL}
          </div>
        </div>
        <div class="foot-bottom">
          <p>{t['rights']}</p>
          <ul class="legal">
{legal}
          </ul>
          <p>{t['city']}</p>
        </div>
      </div>
    </div>
  </footer>

  <script src="assets/home/home.js?v={V}" defer></script>
  <script src="assets/home/page.js?v={V}" defer></script>
</body>
</html>
'''


def crumbs(lang, items):
    """items: [(ad, yol veya None)]"""
    t = T[lang]
    full = [(t["crumb_home"], t["home"])] + items
    lis = []
    for name, href in full:
        lis.append(f'<li><a href="{href}">{esc(name)}</a></li>' if href else f'<li aria-current="page">{esc(name)}</li>')
    ld = {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, **({"item": f"{SITE}/{h}"} if h else {})} for i, (n, h) in enumerate(full)]}
    return f'<nav aria-label="{"Konum" if lang == "tr" else "Breadcrumb"}"><ol class="crumbs">{"".join(lis)}</ol></nav>', ld


def org_ref():
    return {"@type": "Organization", "@id": ORG, "name": "Tide Mobile", "url": SITE + "/", "logo": {"@type": "ImageObject", "url": SITE + "/assets/logo.jpg"}}


def add_ids(body):
    """h2 başlıklarına kimlik ekler, içindekiler listesini döndürür."""
    toc, seen = [], set()

    def rep(m):
        attrs, inner = m.group(1), m.group(2)
        if "id=" in attrs:
            i = re.search(r'id="([^"]+)"', attrs).group(1)
        else:
            i = slugify(inner) or "bolum"
            while i in seen:
                i += "-2"
            attrs = f' id="{i}"' + attrs
        seen.add(i)
        toc.append((i, strip_tags(inner)))
        return f"<h2{attrs}>{inner}</h2>"
    return re.sub(r"<h2([^>]*)>(.*?)</h2>", rep, body, flags=re.S), toc


def check(path, s):
    for ch, name in (("—", "em dash"), ("–", "en dash")):
        if ch in s:
            i = s.index(ch)
            sys.exit(f"HATA: {path} içinde {name} var: ...{s[max(0, i - 60):i + 20]}...")
    if re.search(r">[^<]*Tidw", s):
        sys.exit(f"HATA: {path} içinde yanlış marka yazımı")


def write(path, s):
    check(path, s)
    (ROOT / path).write_text(s, encoding="utf-8", newline="\n")
    print("yazıldı", path)


# ---------------------------------------------------------------- OG görselleri
def og_images(posts):
    try:
        from fontTools.ttLib import TTFont
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("OG görselleri atlandı (fontTools/Pillow yok)")
        return
    tmp = ROOT / "tools" / ".fontcache"
    tmp.mkdir(exist_ok=True)

    def ttf(name):
        out = tmp / (name + ".ttf")
        if not out.exists():
            f = TTFont(ROOT / "assets" / "fonts" / (name + ".woff2"))
            f.flavor = None
            f.save(out)
        return str(out)
    head_f, body_f, serif_f = ttf("general-sans-500"), ttf("switzer-500"), ttf("gambetta-300-700-italic")
    wave = Image.open(ROOT / "assets/home/hero-dalga.webp").convert("RGBA")
    logo = Image.open(ROOT / "assets/home/tide-logo-192.webp").convert("RGBA").resize((76, 76), Image.LANCZOS)
    paper = Image.open(ROOT / "assets/home/kagit.webp").convert("L")
    for p in posts:
        W, H = 1200, 630
        im = Image.new("RGBA", (W, H), (246, 237, 220, 255))
        tex = Image.new("L", (W, H))
        for x in range(0, W, paper.width):
            for y in range(0, H, paper.height):
                tex.paste(paper, (x, y))
        shade = Image.new("RGBA", (W, H), (120, 95, 60, 0))
        shade.putalpha(tex.point(lambda v: max(0, 128 - v) // 6))
        im.alpha_composite(shade)
        w2 = wave.resize((900, round(900 * wave.height / wave.width)), Image.LANCZOS)
        a = w2.getchannel("A").point(lambda v: int(v * .8))
        w2.putalpha(a)
        im.alpha_composite(w2, (W - 760, H - w2.height + 40))
        d = ImageDraw.Draw(im)
        im.alpha_composite(logo, (72, 64))
        d.text((166, 78), "Tide Mobile", font=ImageFont.truetype(head_f, 34), fill=(20, 58, 79))
        d.text((166, 118), "tidemobileapp.com", font=ImageFont.truetype(body_f, 20), fill=(93, 116, 128))
        d.text((72, 200), (p["category"].replace("i", "İ").replace("ı", "I") if p["lang"] == "tr" else p["category"]).upper(), font=ImageFont.truetype(head_f, 22), fill=(36, 121, 127))
        size = 60
        words = p["title"].split()
        while True:
            f = ImageFont.truetype(head_f, size)
            lines, cur = [], ""
            for wd in words:
                test = (cur + " " + wd).strip()
                if d.textlength(test, font=f) > 760 and cur:
                    lines.append(cur); cur = wd
                else:
                    cur = test
            lines.append(cur)
            if len(lines) <= 4 or size <= 40:
                break
            size -= 4
        y = 246
        for ln in lines:
            d.text((72, y), ln, font=f, fill=(20, 58, 79))
            y += int(size * 1.14)
        d.text((72, H - 84), p["author_name"], font=ImageFont.truetype(serif_f, 30), fill=(36, 121, 127))
        out = ROOT / "assets" / "og" / f"{p['file'].replace('.html', '')}.jpg"
        out.parent.mkdir(exist_ok=True)
        im.convert("RGB").save(out, "JPEG", quality=86, optimize=True)
    print("OG görselleri:", len(posts))


# ---------------------------------------------------------------- blog yazıları
def load_posts():
    posts = []
    order = json.loads((C / "blog-index-tr.json").read_text(encoding="utf-8"))["cards"]
    slugs = [re.sub(r"^blog-|\.html$", "", c["href"]) for c in order]
    for slug in slugs:
        for lang in ("tr", "en"):
            p = json.loads((C / f"blog-{slug}-{lang}.json").read_text(encoding="utf-8"))
            p["published"], p["modified"] = git_dates(p["file"])
            p["alt"] = f"blog-{slug}{'' if lang == 'en' else '-en'}.html"
            words = len(strip_tags(p["lede"] + " " + p["body"]).split())
            p["words"] = words
            p["minutes"] = max(2, math.ceil(words / 200))
            p["author_name"] = p["author"] or (p["meta"][0] if p["meta"] else "Tide Mobile")
            idx = json.loads((C / f"blog-index-{lang}.json").read_text(encoding="utf-8"))["cards"]
            card = next(c for c in idx if c["href"] == p["file"])
            p["summary"] = card["summary"]
            p["category_key"] = card["category_key"]
            posts.append(p)
    return posts


def clean_body(b):
    b = re.sub(r'\s*target="_blank"', ' rel="noopener"', b)
    b = b.replace('rel="noopener" rel="noopener"', 'rel="noopener"')
    b = re.sub(r"Tidemobile Insights", "Tide Mobile Blog", b)
    b = re.sub(r"\bTidemobile\b", "Tide Mobile", b)
    return b


def post_card(p, lang, feature=False):
    t = T[lang]
    return f'''          <a class="post{' is-feature' if feature else ''} reveal" href="{p['file']}" data-cat="{p['category_key']}">
            <span class="cat">{esc(p['category'])}</span>
            <h3>{esc(p['title'])}</h3>
            <p>{esc(p['summary'])}</p>
            <span class="post-foot"><span>{esc(p['author_name'])} · {t['read'].format(p['minutes'])}</span><span class="go"><svg aria-hidden="true"><use href="#i-arrow"/></svg></span></span>
          </a>'''


def build_post(p, all_posts):
    lang = p["lang"]
    t = T[lang]
    blog_home = "blog.html" if lang == "tr" else "blog-en.html"
    body, toc = add_ids(clean_body(p["body"]))
    cr_html, cr_ld = crumbs(lang, [(t["blog"], blog_home), (p["title"], None)])
    og = f"{SITE}/assets/og/{p['file'].replace('.html', '')}.jpg"
    person = {"@type": "Person", "name": p["author_name"], "jobTitle": t["roles"].get(p["author_name"], ""), "worksFor": {"@id": ORG}}
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BlogPosting", "@id": f"{SITE}/{p['file']}#article", "headline": p["title"], "description": p["description"],
         "image": og, "datePublished": p["published"], "dateModified": p["modified"], "author": person, "publisher": org_ref(),
         "mainEntityOfPage": f"{SITE}/{p['file']}", "inLanguage": lang, "articleSection": p["category"], "wordCount": p["words"],
         "isPartOf": {"@type": "Blog", "@id": f"{SITE}/{blog_home}#blog"}},
        cr_ld]}
    same = [q for q in all_posts if q["lang"] == lang and q["file"] != p["file"]]
    same.sort(key=lambda q: (q["category_key"] != p["category_key"]))
    related = "\n".join(post_card(q, lang) for q in same[:3])
    toc_html = "\n".join(f'            <a href="#{i}">{esc(n)}</a>' for i, n in toc)
    parts = p["author_name"].split()
    initials = parts[0][0] + parts[-1][0] if len(parts) > 2 else "".join(w[0] for w in parts)
    extra = (f'\n  <meta property="article:published_time" content="{p["published"]}" />'
             f'\n  <meta property="article:modified_time" content="{p["modified"]}" />'
             f'\n  <meta property="article:section" content="{esc(p["category"])}" />'
             f'\n  <meta name="author" content="{esc(p["author_name"])}" />')
    title = p["title"] + " | Tide Mobile" if len(p["title"]) <= 56 else p["title"]
    s = head(lang, title, p["description"], p["file"], p["alt"], og, "article", ld, extra)
    s += nav(lang, p["alt"], "blog.html" if lang == "tr" else "blog-en.html")
    s += f'''  <div class="progress" id="readProgress" aria-hidden="true"></div>
  <main id="icerik">
    <header class="page-hero">
      <img class="ph-wave" src="assets/home/hero-dalga.webp" width="1800" height="839" alt="" aria-hidden="true" />
      <div class="wrap">
        {cr_html}
        <p class="label">{esc(p['category'])}</p>
        <h1>{esc(p['title'])}</h1>
        <div class="chips">
          <span class="chip"><svg aria-hidden="true"><use href="#i-user"/></svg>{esc(p['author_name'])}</span>
          <span class="chip"><svg aria-hidden="true"><use href="#i-cal"/></svg><time datetime="{p['published']}">{fmt_date(p['published'], lang)}</time></span>
          <span class="chip"><svg aria-hidden="true"><use href="#i-clock"/></svg>{t['read'].format(p['minutes'])}</span>
        </div>
      </div>
    </header>

    <div class="wrap article-wrap">
      <article class="prose">
        <p class="lede">{p['lede']}</p>
{body}
      </article>
      <aside class="aside">
        <div class="aside-card">
          <p class="label">{t['toc']}</p>
          <nav class="toc" aria-label="{t['toc']}">
{toc_html}
          </nav>
        </div>
        <div class="aside-card author">
          <span class="ava" aria-hidden="true">{initials}</span>
          <div><b>{esc(p['author_name'])}</b><span>{esc(t['roles'].get(p['author_name'], 'Tide Mobile'))}</span></div>
        </div>
      </aside>
    </div>

    <section class="related" aria-labelledby="ilgili">
      <div class="wrap">
        <div class="sec-head">
          <div><p class="label">{t['related_label']}</p><h2 class="h2" id="ilgili">{t['related_h']}</h2></div>
          <a class="link-arrow" href="{blog_home}">{t['all_posts']} <svg aria-hidden="true"><use href="#i-arrow"/></svg></a>
        </div>
        <div class="posts">
{related}
        </div>
      </div>
    </section>
  </main>
'''
    s += footer(lang)
    write(p["file"], s)


BLOG_COPY = {
    "tr": {"file": "blog.html", "alt": "blog-en.html", "title": "Blog: Psikoloji, Vize, Seyahat ve Küresel Ticaret Yazıları | Tide Mobile",
           "desc": "Tide Mobile ekibinden siber psikoloji, dijital iyi oluş, vize politikaları, altın vize, dijital göçebe vizesi ve uluslararası ticaret üzerine yazılar.",
           "label": "Blog", "h1": "Ürünlerimizin arkasındaki <em>düşünce.</em>",
           "lead": "Psikoloji, vize, seyahat ve küresel ticaret üzerine ekibimizin yazıları. Modi ve TerraVisa'yı geliştirirken karşılaştığımız soruları burada açıyoruz."},
    "en": {"file": "blog-en.html", "alt": "blog.html", "title": "Blog: Psychology, Visas, Travel and Global Trade | Tide Mobile",
           "desc": "Articles from the Tide Mobile team on cyberpsychology, digital wellbeing, visa policy, golden visas, digital nomad visas and international trade.",
           "label": "Blog", "h1": "The thinking behind <em>our products.</em>",
           "lead": "Articles from our team on psychology, visas, travel and global trade. Here we open up the questions we run into while building Modi and TerraVisa."},
}


def build_blog_index(lang, posts):
    t = T[lang]
    c = BLOG_COPY[lang]
    mine = [p for p in posts if p["lang"] == lang]
    cats = []
    for p in mine:
        if (p["category_key"], p["category"]) not in cats:
            cats.append((p["category_key"], p["category"]))
    cr_html, cr_ld = crumbs(lang, [(t["blog"], None)])
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Blog", "@id": f"{SITE}/{c['file']}#blog", "name": "Tide Mobile Blog", "url": f"{SITE}/{c['file']}", "inLanguage": lang,
         "description": c["desc"], "publisher": org_ref(),
         "blogPost": [{"@type": "BlogPosting", "headline": p["title"], "url": f"{SITE}/{p['file']}", "datePublished": p["published"],
                       "author": {"@type": "Person", "name": p["author_name"]}} for p in mine]},
        cr_ld]}
    filters = f'<button type="button" aria-pressed="true" data-filter="all">{t["all"]}</button>' + "".join(
        f'<button type="button" aria-pressed="false" data-filter="{k}">{esc(n)}</button>' for k, n in cats)
    cards = "\n".join(post_card(p, lang, feature=(i == 0)) for i, p in enumerate(mine))
    s = head(lang, c["title"], c["desc"], c["file"], c["alt"], None, "website", ld)
    s += nav(lang, c["alt"], c["file"])
    s += f'''  <main id="icerik">
    <header class="page-hero">
      <img class="ph-wave" src="assets/home/hero-dalga.webp" width="1800" height="839" alt="" aria-hidden="true" />
      <div class="wrap">
        {cr_html}
        <p class="label">{c['label']}</p>
        <h1>{c['h1']}</h1>
        <p class="page-lead">{c['lead']}</p>
      </div>
    </header>
    <section class="wrap" style="padding-bottom:110px" aria-label="{c['label']}">
      <div class="filters" role="group" aria-label="{'Kategoriye göre süz' if lang == 'tr' else 'Filter by category'}">{filters}</div>
      <div class="posts" id="postGrid">
{cards}
      </div>
    </section>
  </main>
'''
    s += footer(lang)
    write(c["file"], s)


# ---------------------------------------------------------------- teknik ortaklık
def build_partner(lang):
    t = T[lang]
    c = json.loads((C / "teknik-ortaklik.json").read_text(encoding="utf-8"))[lang]
    cr_html, cr_ld = crumbs(lang, [(strip_tags(c["label"]).capitalize(), None)])
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Service", "@id": f"{SITE}/{c['file']}#service", "name": c["seo_title"].split(" | ")[0], "serviceType": "Mobile app development",
         "description": c["description"], "provider": {"@id": ORG}, "areaServed": ["TR", "Worldwide"], "inLanguage": lang,
         "hasOfferCatalog": {"@type": "OfferCatalog", "name": strip_tags(c["svc_h2"]), "itemListElement": [
             {"@type": "Offer", "itemOffered": {"@type": "Service", "name": s_["h"], "description": s_["p"]}} for s_ in c["services"]]}},
        cr_ld]}
    contact = t["home"] + ("#iletisim" if lang == "tr" else "#contact")
    svc = "\n".join(f'''        <article class="svc-card reveal">
          <span class="svc-no">0{i + 1}</span>
          <h3>{esc(x['h'])}</h3>
          <p>{esc(x['p'])}</p>
          <ul>{''.join(f'<li>{esc(li)}</li>' for li in x['li'])}</ul>
        </article>''' for i, x in enumerate(c["services"]))
    stack = "".join(f'<div><h3>{esc(x["h"])}</h3><p>{esc(x["p"])}</p></div>' for x in c["stack"])
    proc = "".join(f'<li><h3>{esc(x["h"])}</h3><p>{esc(x["p"])}</p></li>' for x in c["process"])
    chips = "".join(f'<span class="chip"><svg aria-hidden="true"><use href="#i-check"/></svg>{esc(x)}</span>' for x in c["chips"])
    s = head(lang, c["seo_title"], c["description"], c["file"], c["alt"], None, "website", ld)
    s += nav(lang, c["alt"], c["file"])
    s += f'''  <main id="icerik">
    <header class="page-hero">
      <img class="ph-wave ph-cubes" src="assets/home/kupler.webp" width="1000" height="464" alt="" aria-hidden="true" />
      <div class="wrap">
        {cr_html}
        <p class="label">{c['label']}</p>
        <h1>{c['h1']}</h1>
        <p class="page-lead">{c['lead']}</p>
        <div class="hero-cta" style="margin-top:32px">
          <a href="{contact}" class="btn btn-fill">{c['cta1']} <svg aria-hidden="true"><use href="#i-arrow"/></svg></a>
          <a href="#hizmetler" class="btn btn-line">{c['cta2']} <svg aria-hidden="true"><use href="#i-arrow"/></svg></a>
        </div>
        <div class="chips">{chips}</div>
      </div>
    </header>

    <section class="section" id="hizmetler" style="padding-top:40px" aria-labelledby="svc-h">
      <div class="wrap">
        <div class="reveal" style="margin-bottom:34px"><p class="label">{c['svc_label']}</p><h2 class="h2" id="svc-h">{c['svc_h2']}</h2></div>
        <div class="svc">
{svc}
        </div>
      </div>
    </section>

    <section class="wrap" aria-labelledby="stack-h">
      <div class="reveal" style="margin-bottom:28px"><p class="label">{c['stack_label']}</p><h2 class="h2" id="stack-h">{c['stack_h2']}</h2></div>
      <div class="stack reveal">{stack}</div>
    </section>

    <section class="section" aria-labelledby="proc-h">
      <div class="wrap">
        <div class="reveal" style="margin-bottom:40px"><p class="label">{c['proc_label']}</p><h2 class="h2" id="proc-h">{c['proc_h2']}</h2></div>
        <ol class="proc reveal">{proc}</ol>
      </div>
    </section>

    <section class="wrap" style="padding-bottom:110px">
      <div class="cta-band reveal">
        <div><h2 class="h2">{c['cta_h2']}</h2><p>{c['cta_p']}</p></div>
        <a href="{contact}" class="btn btn-fill">{c['cta_btn']} <svg aria-hidden="true"><use href="#i-arrow"/></svg></a>
      </div>
    </section>
  </main>
'''
    s += footer(lang)
    write(c["file"], s)


# ---------------------------------------------------------------- hukuki sayfalar
LEGAL = {
    "kvkk": {"file": "kvkk.html", "title": "KVKK Aydınlatma Metni | Tide Mobile", "label": "Kişisel verilerin korunması"},
    "gizlilik": {"file": "gizlilik.html", "title": "Gizlilik Politikası | Tide Mobile", "label": "Gizlilik ve güven"},
    "modi-kullanim-kosullari": {"file": "modi-kullanim-kosullari.html", "title": "Modi Kullanım Koşulları | Tide Mobile", "label": "Modi · Yasal belgeler"},
}
# Ziyaretçiye görünen taslak notları sadeleştirilir; hukuki içerik değişmez.
LEGAL_FIX = [
    (" Bu nedenle canlıya alınan her uygulama sürümünde kullanılan üçüncü taraf servis listesinin ayrıca kontrol edilmesi gerekir.", ""),
    ("Uygulamalarınızda toplanan veri kategorileri, üçüncü taraf servisler ve mağaza gereklilikleri değişirse metnin buna göre güncellenmesi gerekir.",
     "Ürünlerimizde toplanan veri kategorileri, kullanılan üçüncü taraf servisler veya mağaza gereklilikleri değiştiğinde bu metin güncellenir."),
]


def block(s, cls):
    """class="cls" taşıyan ilk div/section bloğunu iç içe etiketleri sayarak bulur."""
    m = re.search(r'<(div|section) class="%s">' % cls, s)
    tag, i, depth = m.group(1), m.end(), 1
    pat = re.compile(r"<(/?)%s\b[^>]*>" % tag)
    while depth:
        x = pat.search(s, i)
        depth += -1 if x.group(1) else 1
        i = x.end()
    return m.start(), i, s[m.end():i - len(f"</{tag}>")]


def build_legal(key):
    meta = LEGAL[key]
    src = json.loads((C / f"{key}.json").read_text(encoding="utf-8"))
    m = src["main"]
    for a, b in LEGAL_FIX:
        m = m.replace(a, b)
    m = re.sub(r"<!--.*?-->", "", m, flags=re.S)
    hs, he, hh = block(m, "hero-card")
    h1 = strip_tags(re.search(r"<h1>(.*?)</h1>", hh, re.S).group(1))
    lead = re.search(r'<p class="lead">(.*?)</p>', hh, re.S).group(1).strip()
    lead = re.sub(r"\s+", " ", lead)
    chips = [strip_tags(x) for x in re.findall(r"<span>(.*?)</span>", re.search(r'<div class="meta">(.*?)</div>', hh, re.S).group(1), re.S)]
    rest = m[he:]
    if 'class="toc-card"' in rest:
        ts, te, _ = block(rest, "toc-card")
        rest = rest[:ts] + rest[te:]
    rest = re.sub(r'</?section class="content-card">|<div class="content-card">|</div><!-- /content-card -->', "", rest)
    rest = re.sub(r'\s*target="_blank"', "", rest)
    body, toc = add_ids(rest.strip())
    desc = strip_tags(lead)[:155].rsplit(" ", 1)[0] + "."
    updated = next((c for c in chips if "güncelleme" in c.lower()), None)
    cr_html, cr_ld = crumbs("tr", [(h1, None)])
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "@id": f"{SITE}/{meta['file']}#page", "name": meta["title"], "url": f"{SITE}/{meta['file']}", "inLanguage": "tr",
         "isPartOf": {"@id": SITE + "/#website"}, "publisher": {"@id": ORG}}, cr_ld]}
    toc_html = "\n".join(f'            <a href="#{i}">{esc(n)}</a>' for i, n in toc)
    chips_html = "".join(f'<span class="chip">{esc(c)}</span>' for c in chips)
    s = head("tr", meta["title"], desc, meta["file"], None, None, "website", ld)
    s += nav("tr", None)
    s += f'''  <main id="icerik">
    <header class="page-hero">
      <div class="wrap">
        {cr_html}
        <p class="label">{esc(meta['label'])}</p>
        <h1>{esc(h1)}</h1>
        <p class="page-lead">{lead}</p>
        <div class="chips">{chips_html}</div>
      </div>
    </header>
    <div class="wrap legal-wrap">
      <aside class="aside">
        <div class="aside-card">
          <p class="label">{T['tr']['contents']}</p>
          <nav class="toc" aria-label="{T['tr']['contents']}">
{toc_html}
          </nav>
        </div>
      </aside>
      <article class="doc prose">
{body}
      </article>
    </div>
  </main>
'''
    s += footer("tr")
    write(meta["file"], s)


# ---------------------------------------------------------------- site haritası
def sitemap(posts):
    pairs = [("index.html", "index-en.html", "1.0"), ("blog.html", "blog-en.html", "0.8"), ("teknik-ortaklik.html", "teknik-ortaklik-en.html", "0.8")]
    pairs += [(p["file"], p["alt"], "0.7") for p in posts if p["lang"] == "tr"]
    singles = [("modi/", "0.9"), ("kvkk.html", "0.3"), ("gizlilik.html", "0.3"), ("modi-kullanim-kosullari.html", "0.3")]
    modi_pages = sorted((ROOT / "modi").rglob("*.html"))

    def loc(p):
        return SITE + "/" + ("" if p == "index.html" else p)

    def lastmod(p):
        return git_dates(p)[1] if (ROOT / p).exists() else TODAY
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for tr, en, pr in pairs:
        for p in (tr, en):
            out.append(f"  <url><loc>{loc(p)}</loc><lastmod>{TODAY if p in ('index.html', 'index-en.html', 'blog.html', 'blog-en.html', 'teknik-ortaklik.html', 'teknik-ortaklik-en.html') else lastmod(p)}</lastmod><priority>{pr}</priority>"
                       f'<xhtml:link rel="alternate" hreflang="tr" href="{loc(tr)}"/><xhtml:link rel="alternate" hreflang="en" href="{loc(en)}"/><xhtml:link rel="alternate" hreflang="x-default" href="{loc(en)}"/></url>')
    for p, pr in singles:
        out.append(f"  <url><loc>{SITE}/{p}</loc><lastmod>{TODAY}</lastmod><priority>{pr}</priority></url>")
    for mp in modi_pages:
        rel = mp.relative_to(ROOT).as_posix()
        if rel == "modi/index.html":
            continue
        out.append(f"  <url><loc>{SITE}/{rel}</loc><lastmod>{lastmod(rel)}</lastmod><priority>0.6</priority></url>")
    out.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print("sitemap.xml", len(out) - 3, "adres")


if __name__ == "__main__":
    posts = load_posts()
    og_images(posts)
    for p in posts:
        build_post(p, posts)
    for lang in ("tr", "en"):
        build_blog_index(lang, posts)
        build_partner(lang)
    for k in LEGAL:
        build_legal(k)
    sitemap(posts)
