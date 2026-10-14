"""Mobil taşma testi: her sayfayı dar genişliklerde açar, ekranın dışına taşan öğeleri listeler.

Yerel sunucu gerekir: python -m http.server 8765 (site kökünde)
Kullanım: python tools/mobile_check.py [sayfa.html ...]
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
WIDTHS = [320, 360, 375, 390, 414]
PROFILE = ROOT / "tools" / ".chrome-profile"

PROBE = r"""
<script>
window.addEventListener('load', function () { setTimeout(function () {
  var f = document.getElementById('f'), d = f.contentDocument, W = d.documentElement.clientWidth, out = [];
  d.querySelectorAll('.reveal').forEach(function (e) { e.classList.add('is-in'); });
  d.querySelectorAll('body *').forEach(function (e) {
    var cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.position === 'fixed') return;
    if (e.closest('svg') && e.tagName.toLowerCase() !== 'svg') return;
    var r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return;
    var tag = e.tagName.toLowerCase();
    var hasText = Array.prototype.some.call(e.childNodes, function (n) { return n.nodeType === 3 && n.textContent.trim(); });
    if (!hasText && ['button','a','input','textarea','select'].indexOf(tag) < 0) return;
    var lim = W, p = e.parentElement;
    while (p && p !== d.body) { var o = getComputedStyle(p); if (o.overflowX !== 'visible') { lim = Math.min(lim, p.getBoundingClientRect().right); } p = p.parentElement; }
    var rng = d.createRange(); rng.selectNodeContents(e); var tr = rng.getBoundingClientRect();
    var right = Math.max(r.right, hasText ? tr.right : 0);
    if (right > lim + 1 || right > W + 1 || r.left < -1)
      out.push(tag + (typeof e.className === 'string' && e.className ? '.' + e.className.split(' ')[0] : '') + '[' + Math.round(r.left) + ',' + Math.round(right) + '>' + Math.round(lim) + '] ' + (e.textContent || '').trim().slice(0, 40));
  });
  var sw = d.documentElement.scrollWidth;
  document.title = 'SONUC|' + W + '|' + sw + '|' + out.slice(0, 12).join(' ;; ');
}, 1500); });
</script>
"""


def check(page, w):
    tmp = ROOT / f"_mc_{w}.html"
    tmp.write_text(f'<!doctype html><html><head><title>x</title></head><body style="margin:0">'
                   f'<iframe id="f" scrolling="no" src="{page}" style="width:{w}px;height:900px;border:0"></iframe>{PROBE}</body></html>', encoding="utf-8")
    try:
        r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", f"--user-data-dir={PROFILE}", "--window-size=800,1000", "--disk-cache-size=1", "--disable-application-cache",
                            "--virtual-time-budget=6000", "--dump-dom", f"http://127.0.0.1:8765/{tmp.name}"],
                           capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=90)
        m = re.search(r"<title>SONUC\|(.*?)</title>", r.stdout, re.S)
        return m.group(1) if m else "OLCULEMEDI"
    except subprocess.TimeoutExpired:
        return "ZAMAN ASIMI"
    finally:
        tmp.unlink(missing_ok=True)


import shutil
shutil.rmtree(PROFILE, ignore_errors=True)
pages = sys.argv[1:] or sorted(p.name for p in ROOT.glob("*.html") if not p.name.startswith("_"))
bad = 0
for page in pages:
    for w in WIDTHS:
        res = check(page, w)
        parts = res.split("|")
        ok = len(parts) >= 3 and parts[1] == parts[0] and not parts[2]
        if not ok:
            bad += 1
            print(f"SORUN {page} @{w}px: {res}")
    print(f"tamam {page}")
print("toplam sorun:", bad)
