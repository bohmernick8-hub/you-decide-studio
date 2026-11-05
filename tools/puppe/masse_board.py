"""Schritt 1: Maßlinien auf RED-EYE-Vorbilder zeichnen -> reference/abnahme/puppe_masse.jpg
Alle Pixelwerte sind von Hand an den Bildern abgelesen (Kopf-Ø = Bezugsgröße D)."""
from PIL import Image, ImageDraw, ImageFont

R = "C:/ProjectTikTok/studio/reference/redeye/"
OUT = "C:/ProjectTikTok/studio/reference/abnahme/puppe_masse.jpg"
W, H = 1942 / 12, 1142 / 4


def tile(p, row, col):
    b = Image.open(R + f"boards/redeye-p{p}.jpg").convert("RGB")
    return b.crop((int(col * W), int(row * H), int(col * W + W), int(row * H + H))).resize((576, 1024), Image.LANCZOS)


def frame(n):
    return Image.open(R + f"frames/{n}.jpg").convert("RGB").resize((576, 1024))


F = lambda s: ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", s)


def hline(d, x0, x1, y, txt, col, ty=-30):
    d.line((x0, y, x1, y), fill=col, width=3)
    d.line((x0, y - 9, x0, y + 9), fill=col, width=3)
    d.line((x1, y - 9, x1, y + 9), fill=col, width=3)
    d.text((x0 + 4, y + ty), txt, font=F(19), fill=col, stroke_width=3, stroke_fill=(0, 0, 0))


def vline(d, x, y0, y1, txt, col, tx=8):
    d.line((x, y0, x, y1), fill=col, width=3)
    d.line((x - 9, y0, x + 9, y0), fill=col, width=3)
    d.line((x - 9, y1, x + 9, y1), fill=col, width=3)
    d.text((x + tx, (y0 + y1) // 2 - 12), txt, font=F(19), fill=col, stroke_width=3, stroke_fill=(0, 0, 0))


Y, C, G, M = (255, 214, 0), (0, 230, 255), (120, 255, 120), (255, 120, 220)
panels = []

im = frame("p1_1.2"); d = ImageDraw.Draw(im)
hline(d, 138, 443, 625, "Kopf D = 305 px", Y, 8)
hline(d, 262, 392, 448, "Augenabstand 130 = 43 % D", C, 14)
hline(d, 275, 325, 575, "Mund 50 = 16 % D", G, 10)
panels.append(("p1_1.2  Kopf / Augen / Mund", im))

im = tile(1, 1, 2); d = ImageDraw.Draw(im)
hline(d, 104, 487, 690, "Kopf D = 383 px", Y, 8)
hline(d, 212, 406, 470, "Augenabstand 194 = 51 % D", C, -32)
hline(d, 262, 345, 610, "Mund 83 = 22 % D", G, 12)
panels.append(("Board P1 41,9 s  Augen offen", im))

im = tile(3, 1, 8); d = ImageDraw.Draw(im)
hline(d, 61, 531, 600, "Kopf D = 470 px", Y, -34)
vline(d, 385, 415, 528, "Auge H 113 = 24 % D (weit offen)", M, -326)
hline(d, 344, 425, 545, "Auge B 81 = 17 % D", C, 8)
vline(d, 300, 735, 770, "Hals sichtbar ≈ 7 % D (sitzend)", M)
panels.append(("Board P3 54,4 s  Augen frei / Hals", im))

im = frame("p1_110"); d = ImageDraw.Draw(im)
hline(d, 122, 300, 565, "Kopf D = 178 px", Y, 6)
hline(d, 60, 345, 625, "Schulter 285 = 1,6 D (mit Hoodie)", C)
hline(d, 28, 80, 830, "Arm 52 = 0,29 D", G, -32)
hline(d, 92, 215, 1000, "Fäustling + Daumen-Stummel", M, -32)
panels.append(("p1_110  Schulter / Arm / Fäustling", im))

im = tile(2, 0, 10); d = ImageDraw.Draw(im)
hline(d, 120, 379, 225, "Kopf D = 260 px", Y, -32)
vline(d, 142, 385, 980, "Arm-Länge 595 ≈ 2,3 D", C)
hline(d, 180, 255, 362, "Hals 75 = 0,29 D, sichtbar ≈ 15 % D", M, 8)
panels.append(("Board P2 31,3 s  Hals / Armlänge", im))

im = tile(1, 3, 0); d = ImageDraw.Draw(im)
hline(d, 235, 300, 478, "D = 65", Y, 8)
vline(d, 345, 400, 760, "Figur ≈ 5,6 D (vorgebeugt) → aufrecht ≈ 6 D", C, -330)
panels.append(("Board P1 95,7 s  Körperhöhe", im))

PW, PH, T = 576, 1024, 54
sheet = Image.new("RGB", (PW * 3, (PH + T) * 2), (18, 20, 26))
d = ImageDraw.Draw(sheet)
for i, (t, im) in enumerate(panels):
    x, y = (i % 3) * PW, (i // 3) * (PH + T)
    sheet.paste(im, (x, y + T))
    d.text((x + 14, y + 12), t, font=F(26), fill=(235, 235, 235))
sheet.save(OUT, quality=88)
print(sheet.size)
