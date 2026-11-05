"""Montiert gesichter_board.jpg und puppe_vergleich.jpg aus den Renders + RED-EYE-Vorbildern."""
from PIL import Image, ImageDraw, ImageFont

ROOT = "C:/ProjectTikTok/studio/"
RN = ROOT + "renders/_puppe/"
AB = ROOT + "reference/abnahme/"
RE = ROOT + "reference/redeye/"
BG = (16, 18, 24)
FG = (236, 236, 236)
DIM = (170, 176, 188)
YEL = (245, 197, 24)


def F(s):
    return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", s)


def board():
    T, GAP, LBL = 480, 8, 46
    cols = 5
    NAMES = ["neutral (MAIN)", "augen-zu", "schlaefrig", "blinzeln", "wach-starr", "neugierig", "aufgeregt", "gluecklich",
             "aengstlich", "erschrocken", "panisch", "traurig", "misstrauisch", "fluestern", "leer"]
    sections = [
        ("15 AUSDRÜCKE  (Schalter „ausdruck“)", [(f"a{i:02d}", f"{i}  {n}") for i, n in enumerate(NAMES)]),
        ("5 MUND-FORMEN FÜRS SPRECHEN  (Schalter „mund“, Augen bleiben)",
         [(f"m{i}", f"{i + 1}  {n}") for i, n in enumerate(["m-zu", "m-klein", "m-offen", "m-wellig", "m-breit"])]),
        ("AUGENBRAUEN + GLANZPUNKT FÜR GROSS  (Schalter „brauen“, „glanz“)",
         [("b0", "brauen 1  besorgt"), ("b1", "brauen 2  wuetend"), ("b2", "brauen 3  ueberrascht"),
          ("g0", "glanz 1  neutral"), ("g1", "wach-starr (immer, größer)")]),
    ]
    head = 92
    h = 0
    for _, items in sections:
        rows = (len(items) + cols - 1) // cols
        h += head + rows * (T + LBL + GAP)
    W = cols * T + (cols + 1) * GAP
    S = Image.new("RGB", (W, h + GAP), BG)
    d = ImageDraw.Draw(S)
    y = 0
    for title, items in sections:
        d.text((GAP + 6, y + 30), title, font=F(34), fill=YEL)
        y += head
        for i, (nm, label) in enumerate(items):
            x = GAP + (i % cols) * (T + GAP)
            yy = y + (i // cols) * (T + LBL + GAP)
            S.paste(Image.open(f"{RN}board/{nm}.png").convert("RGB").resize((T, T), Image.LANCZOS), (x, yy))
            d.text((x + 8, yy + T + 6), label, font=F(28), fill=FG)
        y += ((len(items) + cols - 1) // cols) * (T + LBL + GAP)
    S.save(AB + "gesichter_board.jpg", quality=90)
    print("board", S.size)


def tag(im, text, col):
    d = ImageDraw.Draw(im)
    w = d.textlength(text, font=F(26)) + 28
    d.rounded_rectangle((14, im.size[1] - 58, 14 + w, im.size[1] - 14), 12, fill=(0, 0, 0))
    d.text((28, im.size[1] - 54), text, font=F(26), fill=col)
    return im


def vergleich():
    PW, PH = 540, 960
    RED, WIR = (255, 110, 90), (120, 230, 140)
    a1 = tag(Image.open(RE + "frames/p1_1.2.jpg").convert("RGB").resize((PW, PH)), "RED-EYE  P1 1,2 s", RED)
    b1 = tag(Image.open(RN + "gross_main_nacht.png").convert("RGB").resize((PW, PH), Image.LANCZOS), "WIR  Nacht, 70 mm f/2", WIR)
    a2 = tag(Image.open(RE + "frames/p3_54_sprechen.jpg").convert("RGB").resize((PW, PH), Image.LANCZOS), "RED-EYE  P3 55,2 s", RED)
    b2 = tag(Image.open(RN + "gross_main_warm.png").convert("RGB").resize((PW, PH), Image.LANCZOS), "WIR  warm, 85 mm f/1,8", WIR)
    T = 76
    views = ["front", "dreiviertel", "seite", "ruecken"]
    V = PW
    y2 = T + PH + T
    y3 = y2 + V + T + V + T
    S = Image.new("RGB", (PW * 4, y3 + V // 1 + 0), BG)
    d = ImageDraw.Draw(S)
    d.text((16, 18), "GROSS-GESICHT: LINKS RED-EYE, RECHTS WIR", font=F(34), fill=YEL)
    for i, im in enumerate((a1, b1, a2, b2)):
        S.paste(im, (i * PW, T))
    d.text((16, T + PH + 18), "VORDERANSICHT · ¾ · SEITE · RÜCKEN  (Nacht-Licht)", font=F(34), fill=YEL)
    for i, v in enumerate(views):
        S.paste(Image.open(f"{RN}view_nacht_{v}.png").convert("RGB").resize((V, V), Image.LANCZOS), (i * PW, y2))
    d.text((16, y2 + V + 18), "VORDERANSICHT · ¾ · SEITE · RÜCKEN  („Licht an“)", font=F(34), fill=YEL)
    for i, v in enumerate(views):
        S.paste(Image.open(f"{RN}view_warm_{v}.png").convert("RGB").resize((V, V), Image.LANCZOS), (i * PW, y2 + V + T))
    d.text((16, y2 + 2 * V + T + 18), "KÖRPER: LINKS RED-EYE, RECHTS WIR  ·  3 VARIANTEN: KIND 1,20 m · ERWACHSEN 1,75 m · SCHMAL 1,65 m", font=F(34), fill=YEL)
    c1 = Image.open(RE + "frames/p1_110.jpg").convert("RGB").resize((576, 1024)).crop((18, 340, 558, 880))
    c2 = Image.open(RN + "koerper_warm.png").convert("RGB").resize((V, V), Image.LANCZOS)
    S.paste(tag(c1, "RED-EYE  P1 110 s", RED), (0, y3))
    S.paste(tag(c2, "WIR  (T-Pose, ohne Kleidung)", WIR), (PW, y3))
    v3 = Image.open(RN + "varianten.png").convert("RGB")
    S.paste(v3.resize((PW * 2, PW)), (PW * 2, y3))
    S.save(AB + "puppe_vergleich.jpg", quality=90)
    print("vergleich", S.size)


def marker():
    """Marker-Hilfe für den Mixamo-Auto-Rigger: Punkte aus den echten Modell-Maßen (Ortho-Kamera, 2,2 m Bildbreite)."""
    im = Image.open(RN + "mixamo_vorn.png").convert("RGB")
    W = im.size[0]
    px = lambda x, z: (W / 2 + x / 2.2 * W, W / 2 - (z - 0.9) / 2.2 * W)
    d = ImageDraw.Draw(im)
    pts = [("1  KINN (Chin)", [(0, 1.475)], (1, -1), (245, 197, 24)),
           ("2  HANDGELENKE (Wrists)", [(-0.735, 1.335), (0.735, 1.335)], (0, -1), (47, 107, 255)),
           ("3  ELLBOGEN (Elbows)", [(-0.49, 1.335), (0.49, 1.335)], (0, 1), (46, 180, 90)),
           ("4  KNIE (Knees)", [(-0.098, 0.465), (0.098, 0.465)], (1, 0), (230, 70, 60)),
           ("5  LEISTE (Groin)", [(0, 0.78)], (1, 0), (190, 80, 220))]
    for text, ps, (dx, dy), col in pts:
        for x, z in ps:
            X, Y = px(x, z)
            d.ellipse((X - 15, Y - 15, X + 15, Y + 15), fill=col, outline=(255, 255, 255), width=4)
        X, Y = px(*ps[-1])
        if dy == -1 and dx == 0:
            tx, ty = X - 250, Y - 76
        elif dy == 1 and dx == 0:
            tx, ty = X - 210, Y + 32
        elif dy == -1:
            tx, ty = X + 60, Y - 96
        else:
            tx, ty = X + 170, Y - 22
        w = d.textlength(text, font=F(36))
        d.rounded_rectangle((tx - 12, ty - 6, tx + w + 12, ty + 50), 10, fill=(0, 0, 0))
        d.text((tx, ty), text, font=F(36), fill=col if col[2] < 240 else (120, 165, 255))
    d.text((30, 26), "MIXAMO: KREISE SO SETZEN (Blick von vorn)", font=F(44), fill=(20, 20, 20))
    im.save(AB + "mixamo_marker.jpg", quality=90)
    print("marker", im.size)


if __name__ == "__main__":
    board()
    vergleich()
    marker()
