"""Ana sayfa görsellerini üretir.

Kaynaklar:
  - Referans tasarım (Real-ESRGAN ile 4x büyütülmüş): ref4.png
  - Logo paleti (kağıt dokusu): logo palet.jfif
  - Gerçek uygulama ekran görüntüleri

Yöntem:
  1. Referanstaki cam dalga, küre ve küpler kırpılır, üstlerine binen yazılar cv2.inpaint ile silinir.
  2. "Renkten alfa": beyaz zemin saydamlığa çevrilir, nesne her zemine oturur.
  3. Gradyan haritası: nesnenin parlaklığı logo paletine (petrol, turkuaz, açık turkuaz, krem) eşlenir.
  4. Çıktılar WebP.

Kullanım: python build_home_assets.py <ref4.png> <logo_palet.jfif> <desktop_dir>
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

REF4, PALET, DESK = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
OUT = Path(__file__).resolve().parent.parent / "assets" / "home"

RAMP = [  # parlaklık -> renk (logo paleti)
    (0.00, (11, 37, 52)),
    (0.30, (28, 71, 95)),
    (0.55, (50, 154, 161)),
    (0.78, (101, 187, 182)),
    (0.92, (200, 232, 224)),
    (1.00, (252, 250, 242)),
]


def ramp_lut():
    xs = np.array([p for p, _ in RAMP])
    cs = np.array([c for _, c in RAMP], dtype=np.float32)
    t = np.linspace(0, 1, 256)
    return np.stack([np.interp(t, xs, cs[:, k]) for k in range(3)], axis=1) / 255.0


LUT = ramp_lut()


def color_to_alpha(rgb, bg, floor=0.035, lighter=True):
    """GIMP 'color to alpha' benzeri: bg rengini saydama çevirir. rgb, bg: 0..1
    lighter=False: zeminden açık pikseller (beyaz hale) saydam sayılır."""
    bg = np.asarray(bg, np.float32).reshape(1, 1, 3)
    if not lighter:
        rgb = np.minimum(rgb, bg)
    d = np.where(rgb < bg, (bg - rgb) / np.maximum(bg, 1e-4), (rgb - bg) / np.maximum(1 - bg, 1e-4))
    a = d.max(axis=2)
    a = np.clip((a - floor) / (1 - floor), 0, 1)
    fg = (rgb - (1 - a[..., None]) * bg) / np.maximum(a[..., None], 1e-4)
    return np.clip(fg, 0, 1), a


def grade(fg, a, keep=0.18, gamma=1.0):
    """Ön plan rengini parlaklığa göre palete eşler, özgün rengin bir kısmını korur."""
    lum = (0.2126 * fg[..., 0] + 0.7152 * fg[..., 1] + 0.0722 * fg[..., 2]) ** gamma
    mapped = LUT[np.clip((lum * 255).astype(int), 0, 255)]
    return mapped * (1 - keep) + fg * keep


def feather(h, w, left=0.0, right=0.0, top=0.0, bottom=0.0):
    m = np.ones((h, w), np.float32)
    def ramp(n):
        return (np.sin(np.linspace(0, np.pi / 2, n)) ** 2).astype(np.float32)
    if left:
        n = int(w * left); m[:, :n] *= ramp(n)[None, :]
    if right:
        n = int(w * right); m[:, w - n:] *= ramp(n)[::-1][None, :]
    if top:
        n = int(h * top); m[:n, :] *= ramp(n)[:, None]
    if bottom:
        n = int(h * bottom); m[h - n:, :] *= ramp(n)[::-1][:, None]
    return m


def save_rgba(rgb, a, name, width=None, q=86, agamma=1.0):
    a = np.clip(a, 0, 1) ** agamma  # zayıf pusu bastırır
    img = np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])
    im = Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGBA")
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(OUT / name, "WEBP", quality=q, method=6, alpha_quality=90)
    print(name, im.size, round((OUT / name).stat().st_size / 1024), "KB")


ref = cv2.imread(str(REF4), cv2.IMREAD_COLOR)  # BGR


def crop(x0, y0, x1, y1, erase=()):
    c = ref[y0:y1, x0:x1].copy()
    if erase:
        mask = np.zeros(c.shape[:2], np.uint8)
        for ex0, ey0, ex1, ey1 in erase:
            mask[ey0 - y0:ey1 - y0, ex0 - x0:ex1 - x0] = 255
        c = cv2.inpaint(c, mask, 9, cv2.INPAINT_TELEA)
    return cv2.cvtColor(c, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0


def bg_of(rgb):
    """Köşelerden zemin rengini tahmin eder (en parlak köşe)."""
    h, w = rgb.shape[:2]
    k = 24
    corners = [rgb[:k, :k], rgb[:k, w - k:], rgb[h - k:, :k], rgb[h - k:, w - k:]]
    means = [c.reshape(-1, 3).mean(0) for c in corners]
    return max(means, key=lambda m: m.sum())


# ---- 1. Hero cam dalgası
rgb = crop(1290, 150, 3296, 1085, erase=[(2640, 280, 3000, 450)])
fg, a = color_to_alpha(rgb, bg_of(rgb), floor=0.05)
h, w = a.shape
a *= feather(h, w, left=0.22, bottom=0.16, top=0.05)
# sol üstteki menü kalıntısı: yumuşak geçişle silinir
yy, xx = np.mgrid[0:h, 0:w]
a *= np.clip(np.maximum((xx - 660) / 160, (yy - 230) / 90), 0, 1)
save_rgba(grade(fg, a, keep=0.15), a, "hero-dalga.webp", width=1800, agamma=1.12)

# ---- 2. Hakkımızda cam küreler
rgb = crop(1300, 1700, 2120, 2500)
fg, a = color_to_alpha(rgb, bg_of(rgb), floor=0.04, lighter=False)
h, w = a.shape
a *= feather(h, w, left=0.08, right=0.08, top=0.08, bottom=0.08)
save_rgba(grade(fg, a, keep=0.15), a, "kureler.webp", width=760, agamma=1.3)

# ---- 3. Teknik ortaklık cam küpler
rgb = crop(2130, 5790, 3250, 6310)
fg, a = color_to_alpha(rgb, bg_of(rgb), floor=0.07, lighter=False)
h, w = a.shape
a *= feather(h, w, left=0.16, right=0.1, top=0.14, bottom=0.16)
save_rgba(grade(fg, a, keep=0.12), a, "kupler.webp", width=1000, agamma=1.6)

# ---- 4. Uzman desteği: oda fotoğrafı, sıcak tona çekilir
room = crop(1190, 5330, 1800, 5785)
cream = np.array([0.975, 0.93, 0.85], np.float32)
lum = room.mean(axis=2, keepdims=True)
sat = room - lum  # renk (koltuk ve bitkiler) korunur, gri duvarlar kreme çekilir
neutral = 1 - np.clip(np.abs(sat).max(axis=2, keepdims=True) * 6, 0, 1)
warm = room * (1 - 0.8 * neutral) + (lum * cream / cream.mean()) * 0.8 * neutral
warm = np.clip(warm * 1.02, 0, 1)
im = Image.fromarray((warm * 255).astype(np.uint8)).resize((610, 455), Image.LANCZOS)
im.save(OUT / "uzman-oda.webp", "WEBP", quality=84, method=6)
print("uzman-oda.webp", im.size)

# ---- 5. Kağıt dokusu (logo paletinden), dikişsiz karo
pal = cv2.imread(str(PALET), cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0
tile = pal[60:60 + 320, 300:300 + 320]
tile = tile - cv2.GaussianBlur(tile, (0, 0), 18)  # yalnızca doku
tile = np.concatenate([tile, tile[:, ::-1]], axis=1)
tile = np.concatenate([tile, tile[::-1, :]], axis=0)
tile = np.clip(0.5 + tile * 3.2, 0, 1)
Image.fromarray((tile * 255).astype(np.uint8), "L").save(OUT / "kagit.webp", "WEBP", quality=70)
print("kagit.webp", tile.shape)

# ---- 6. Gerçek uygulama ekranları (durum çubuğu ve reklam bandı kırpılır)
def screen(src, name, top=0.045, bottom=0.0, width=420):
    im = Image.open(src).convert("RGB")
    W, H = im.size
    im = im.crop((0, int(H * top), W, int(H * (1 - bottom))))
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(OUT / name, "WEBP", quality=84, method=6)
    print(name, im.size)


luna = sorted((DESK / "luna ss").glob("*.jpeg"))
tv = sorted((DESK / "ekran gör").glob("*.jpeg"))
screen(luna[3], "luna-ana.webp")
screen(luna[1], "luna-harcama.webp")
screen(tv[7], "tv-schengen.webp", bottom=0.135)
