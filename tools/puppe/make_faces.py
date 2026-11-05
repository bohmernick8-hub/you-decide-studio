"""Erzeugt alle Gesichts-Texturen per Code (PNG 2K, transparent, gleiches Raster).

Raster = azimutale Projektion der Kopf-Vorderseite: Bildmitte = Blickrichtung, Bildrand = 90°
(siehe FaceUV in build_puppe.py).
UDIM-Kacheln: 1001-1015 Ausdrücke | 1021-1025 Mund-Formen | 1031-1033 Augenbrauen.
Augen-Teil (oberhalb SPLIT_Y) und Mund-Teil (unterhalb) liest der Shader getrennt.
Weißer Glanzpunkt liegt als weiße Pixel in der Kachel; der Shader schaltet ihn über `glanz`.
"""
import os
import sys

import numpy as np
from PIL import Image

S = 2048
C = S / 2
INK = (0x1A, 0x1A, 0x1A)
SOFT = 2.5        # weiche Kante (px)
LW = 40           # einheitliche Linienstärke (px)
EX, EY = 372, 41  # Augen-Mitte relativ zur Bildmitte (Bild-y nach unten)
A0, B0 = 80, 104  # Kapsel: halbe Breite / halbe Höhe im Raster (von vorn ≈ 1:1,5)
MY, MW = 430, 119 # Mund: Höhe + halbe Länge
SAG = 10          # „ganz leicht gebogen“
BY = -140         # Augenbrauen-Höhe
SPLIT_Y = 300     # Trennlinie Augen/Mund (relativ zur Mitte)


class Cv:
    def __init__(self):
        self.ink = np.zeros((S, S), np.float32)
        self.gl = np.zeros((S, S), np.float32)

    def _win(self, x0, y0, x1, y1, pad=8):
        x0, x1 = int(max(C + x0 - pad, 0)), int(min(C + x1 + pad, S))
        y0, y1 = int(max(C + y0 - pad, 0)), int(min(C + y1 + pad, S))
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        return (x0, y0, x1, y1), xx - C + 0.5, yy - C + 0.5

    def _put(self, arr, w, d):
        a = np.clip(0.5 - d / (2 * SOFT), 0, 1)
        x0, y0, x1, y1 = w
        arr[y0:y1, x0:x1] = np.maximum(arr[y0:y1, x0:x1], a)

    def capsule(self, cx, cy, a, b, clip=None, ring=None):
        w, x, y = self._win(cx - a, cy - b, cx + a, cy + b)
        qx = np.abs(x - cx)
        qy = np.maximum(np.abs(y - cy) - (b - a), 0)
        d = np.hypot(qx, qy) - a
        if ring:
            d = np.abs(d + ring / 2) - ring / 2
        if clip is not None:
            d = np.maximum(d, clip(x, y))
        self._put(self.ink, w, d)

    def ellipse(self, cx, cy, a, b, glint=False):
        w, x, y = self._win(cx - a, cy - b, cx + a, cy + b)
        k = np.hypot((x - cx) / a, (y - cy) / b)
        self._put(self.gl if glint else self.ink, w, (k - 1) * min(a, b))

    def stroke(self, pts, lw=LW):
        pts = np.asarray(pts, np.float32)
        r = lw / 2
        w, x, y = self._win(pts[:, 0].min() - r, pts[:, 1].min() - r, pts[:, 0].max() + r, pts[:, 1].max() + r)
        best = np.full(x.shape, 1e9, np.float32)
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            dx, dy = bx - ax, by - ay
            t = np.clip(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy + 1e-6), 0, 1)
            best = np.minimum(best, np.hypot(x - ax - t * dx, y - ay - t * dy))
        self._put(self.ink, w, best - r)

    def save(self, path):
        a = np.maximum(self.ink, self.gl)
        k = np.where(a > 0, self.gl / np.maximum(a, 1e-4), 0)
        rgb = np.stack([INK[i] + (255 - INK[i]) * k for i in range(3)], -1)
        out = np.dstack([rgb, a * 255]).round().astype(np.uint8)
        Image.fromarray(out, "RGBA").save(path, optimize=True)


def line(cx, cy, hw, sag=0, tilt=0, n=40):
    t = np.linspace(-1, 1, n)
    return np.stack([cx + hw * t, cy + sag * (1 - t * t) + tilt * t], -1)


def wave(cx, cy, hw, amp, turns=1.5, n=90):
    t = np.linspace(-1, 1, n)
    return np.stack([cx + hw * t, cy + amp * np.sin(t * np.pi * turns)], -1)


# --- Mund-Bausteine ---
def m_neutral(c): c.stroke(line(0, MY, MW, SAG))
def m_gerade(c): c.stroke(line(0, MY, MW))
def m_o(a, b): return lambda c: c.ellipse(0, MY, a, b)
def m_wellig(c): c.stroke(wave(0, MY, MW, 22))
def m_lachen(c): c.stroke(line(0, MY - 14, MW, 46))
def m_traurig(c): c.stroke(line(0, MY + 14, MW * .86, -36))
def m_schief(c): c.stroke(line(0, MY, MW * .92, 0, 13))
def m_klein_schief(c): c.stroke(line(0, MY, MW * .45, 0, 15))
def m_panik(c): c.stroke(wave(0, MY, MW * 1.05, 20), lw=70)
def m_breit(c): c.stroke(line(0, MY, MW * .98, 8), lw=60)


# --- Augen-Bausteine: f(c, sd) mit sd=-1 (Bild links) / +1 (Bild rechts) ---
def glint(c, cx, cy, r=15):
    c.ellipse(cx, cy, r, r, glint=True)


def kapsel(a=A0, b=B0, dy=0, gl=(-.30, -.46), gr=15):
    def f(c, sd):
        cx, cy = sd * EX, EY + (dy if sd > 0 else 0)
        c.capsule(cx, cy, a, b)
        glint(c, cx + gl[0] * a, cy + gl[1] * b, gr)
    return f


def bogen(sag):
    def f(c, sd):
        c.stroke(line(sd * EX, EY - sag * .4, A0 * 1.12, sag))
    return f


def strich(c, sd):
    c.stroke(line(sd * EX, EY, A0 * 1.02, 0))


def schlaefrig(c, sd):
    cx, cy = sd * EX, EY
    c.capsule(cx, cy, A0, B0, clip=lambda x, y: cy - y)
    c.stroke(line(cx, cy, A0 * 1.14, 0))
    glint(c, cx - .3 * A0, cy + .34 * B0)


def lid(k, y0, gl_y=.10):
    """Lid-Linie: k>0 = außen tiefer (innen hochgezogen), k<0 = innen tiefer."""
    def f(c, sd):
        cx, cy = sd * EX, EY
        L = cy + y0 * B0
        c.capsule(cx, cy, A0, B0, clip=lambda x, y: (L + k * (x - cx) * sd) - y)
        hw = A0 * 1.2
        c.stroke([(cx - hw, L - k * hw * sd), (cx + hw, L + k * hw * sd)])
        glint(c, cx - .3 * A0, cy + gl_y * B0)
    return f


def erschrocken(c, sd):
    cx, cy = sd * EX, EY
    c.capsule(cx, cy, A0 * 1.18, B0 * 1.26, ring=LW * .8)
    c.capsule(cx, cy, 30, 40)
    glint(c, cx - 8, cy - 16, 8)


def punkt(c, sd):
    c.ellipse(sd * EX, EY, 13, 13)


EXPR = [  # Reihenfolge = Index des Schalters „ausdruck“
    ("neutral", kapsel(), m_neutral),
    ("augen-zu", bogen(40), m_neutral),
    ("schlaefrig", schlaefrig, m_neutral),
    ("blinzeln", strich, m_neutral),
    ("wach-starr", kapsel(gl=(-.28, -.42), gr=22), m_gerade),
    ("neugierig", kapsel(A0 * 1.1, B0 * 1.1, dy=-24), m_o(42, 50)),
    ("aufgeregt", kapsel(A0 * 1.2, B0 * 1.2), m_o(56, 74)),
    ("gluecklich", bogen(-40), m_lachen),
    ("aengstlich", lid(.34, -.46, .12), m_wellig),
    ("erschrocken", erschrocken, m_o(42, 46)),
    ("panisch", kapsel(A0 * 1.42, B0 * 1.46), m_panik),
    ("traurig", lid(.62, -.26, .22), m_traurig),
    ("misstrauisch", lid(-.40, -.34, .20), m_schief),
    ("fluestern", kapsel(A0 * .8, B0 * .92), m_klein_schief),
    ("leer", punkt, None),
]
MOUTHS = [("m-zu", m_neutral), ("m-klein", m_o(44, 52)), ("m-offen", m_o(66, 88)),
          ("m-wellig", m_wellig), ("m-breit", m_breit)]


def brow(fn):
    def f(c):
        for sd in (-1, 1):
            c.stroke(fn(sd), lw=LW * .9)
    return f


BROWS = [
    ("besorgt", brow(lambda sd: [(sd * (EX - 94), BY - 30), (sd * (EX + 94), BY + 22)])),
    ("wuetend", brow(lambda sd: [(sd * (EX - 94), BY + 30), (sd * (EX + 94), BY - 20)])),
    ("ueberrascht", brow(lambda sd: line(sd * EX, BY - 20, 94, -26))),
]


def udim(i):
    return 1001 + i % 10 + 10 * (i // 10)


def main(out):
    os.makedirs(out, exist_ok=True)
    tiles = {}
    for i, (n, eyes, mouth) in enumerate(EXPR):
        c = Cv()
        for sd in (-1, 1):
            eyes(c, sd)
        if mouth:
            mouth(c)
        c.save(f"{out}/gesicht.{udim(i)}.png")
        tiles[n] = udim(i)
    for i, (n, mouth) in enumerate(MOUTHS):
        c = Cv()
        mouth(c)
        c.save(f"{out}/gesicht.{udim(20 + i)}.png")
        tiles[n] = udim(20 + i)
    for i, (n, b) in enumerate(BROWS):
        c = Cv()
        b(c)
        c.save(f"{out}/gesicht.{udim(30 + i)}.png")
        tiles[n] = udim(30 + i)
    return tiles


if __name__ == "__main__":
    print(main(sys.argv[1] if len(sys.argv) > 1 else "C:/ProjectTikTok/studio/assets/characters/faces"))
