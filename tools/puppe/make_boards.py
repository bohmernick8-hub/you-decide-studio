"""Montiert gesichter_board.jpg, puppe_vergleich.jpg und puppe_hoodie_test.jpg aus den Renders + RED-EYE-Vorbildern."""
import json

from PIL import Image, ImageDraw, ImageFont

ROOT = "C:/ProjectTikTok/studio/"
RN = ROOT + "renders/_puppe/"
AB = ROOT + "reference/abnahme/"
RE = ROOT + "reference/redeye/"
BG = (16, 18, 24)
FG = (236, 236, 236)
DIM = (170, 176, 188)
YEL = (245, 197, 24)
MASSE = "NACKT, 1,62 m: OBERARM 0,26 D · SCHULTERN 1,41 D · HALS 13 % D · SCHRITT 0,64 m · RUMPF SITZEND 1,99 D"


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


def re_tile(p, row, col):
    """Einstellung aus dem RED-EYE-Board (nur dort vorhanden), gelbe Zeitmarke überdeckt."""
    W, H = 1942 / 12, 1142 / 4
    b = Image.open(RE + f"boards/redeye-p{p}.jpg").convert("RGB")
    t = b.crop((int(col * W) + 3, int(row * H) + 2, int(col * W + W), int(row * H + H))).resize((540, 960), Image.LANCZOS)
    # Zeile unter der Marke nach oben ziehen: nahtlos, weil die Wand dort einfarbig ist
    t.paste(t.crop((0, 66, 320, 67)).resize((320, 66)), (0, 0))
    return t


def vergleich():
    PW, PH = 540, 960
    RED, WIR = (255, 110, 90), (120, 230, 140)
    T = 76
    big = lambda n: Image.open(f"{RN}{n}.png").convert("RGB").resize((PW, PH), Image.LANCZOS)
    sq = lambda n: Image.open(f"{RN}{n}.png").convert("RGB").resize((PW, PW), Image.LANCZOS)
    row1 = [tag(Image.open(RE + "frames/p1_110.jpg").convert("RGB").resize((PW, PH)), "RED-EYE  P1 110 s", RED),
            tag(big("pose_sitz_p1"), "WIR  sitzend", WIR),
            tag(re_tile(2, 0, 10), "RED-EYE  P2 31,3 s", RED),
            tag(big("pose_steh_p2"), "WIR  stehend", WIR)]
    row2 = [tag(sq("pose_steh_vorn"), "stehend vorn", WIR), tag(sq("pose_steh_seite"), "stehend Seite", WIR),
            tag(sq("pose_steh_ruecken"), "stehend Rücken", WIR), tag(sq("pose_sitz_dreiviertel"), "sitzend ¾", WIR)]
    row3 = [tag(sq("pose_sitz_seite"), "sitzend Seite", WIR), tag(sq("t_vorn"), "T-Pose für Mixamo", WIR),
            tag(sq("detail_hand"), "Fäustling + Daumen", WIR), tag(sq("detail_hals"), "Hals: Kugel + Ring", WIR)]
    var = Image.open(RN + "varianten.png").convert("RGB")
    VH = int(PW * 4 * var.size[1] / var.size[0])
    H = T + PH + T + PW + PW + T + VH
    S = Image.new("RGB", (PW * 4, H), BG)
    d = ImageDraw.Draw(S)
    d.text((16, 18), MASSE, font=F(30), fill=YEL)
    for i, im in enumerate(row1):
        S.paste(im, (i * PW, T))
    y = T + PH
    d.text((16, y + 18), "ERWACHSEN 1,62 m, OHNE KLEIDUNG  (Posen über Hilfs-Skelett, noch nicht Mixamo)", font=F(30), fill=YEL)
    y += T
    for i, im in enumerate(row2):
        S.paste(im, (i * PW, y))
    y += PW
    for i, im in enumerate(row3):
        S.paste(im, (i * PW, y))
    y += PW
    d.text((16, y + 18), "3 VARIANTEN: KIND 1,15 m · ERWACHSEN 1,62 m · SCHMAL 1,55 m", font=F(30), fill=YEL)
    S.paste(var.resize((PW * 4, VH), Image.LANCZOS), (0, y + T))
    S.save(AB + "puppe_vergleich.jpg", quality=90)
    print("vergleich", S.size)


def hoodie_test():
    """Hoodie-Proxy sitzend im Nachtlicht neben RED-EYE P1 110 s (Kopf gleich groß im Bild)."""
    PW, PH = 720, 1280
    RED, WIR = (255, 110, 90), (120, 230, 140)
    T = 76
    big = lambda n: Image.open(f"{RN}{n}.png").convert("RGB").resize((PW, PH), Image.LANCZOS)
    tiles = [tag(Image.open(RE + "frames/p1_110.jpg").convert("RGB").resize((PW, PH), Image.LANCZOS), "RED-EYE  P1 110 s", RED),
             tag(big("hoodie_nacht_p1"), "WIR  Hoodie-Proxy, Nacht, gleiche Einstellung", WIR),
             tag(big("hoodie_nacht_ganz"), "WIR  ganze Figur", WIR)]
    S = Image.new("RGB", (PW * 3, T + PH), BG)
    d = ImageDraw.Draw(S)
    d.text((16, 18), "HOODIE-TEST (Proxy, nur für Proportionen): 1,62 m · SCHULTERN MIT HOODIE 1,53 D (RED-EYE 1,6 D) · RUMPF SITZEND 1,99 D", font=F(30), fill=YEL)
    for i, im in enumerate(tiles):
        S.paste(im, (i * PW, T))
    S.save(AB + "puppe_hoodie_test.jpg", quality=90)
    print("hoodie", S.size)


def marker():
    """Marker-Hilfe für den Mixamo-Auto-Rigger: Punkte aus den echten Modell-Maßen (Ortho-Kamera, 2,2 m Bildbreite)."""
    im = Image.open(RN + "mixamo_vorn.png").convert("RGB")
    W = im.size[0]
    # Positionen schreibt export_mixamo.py aus dem echten Modell (rig_joints + gemessener Schritt)
    m = json.load(open(RN + "mixamo_marker.json", encoding="utf-8"))
    px = lambda x, z: (W / 2 + x / m["width"] * W, W / 2 - (z - m["zc"]) / m["width"] * W)
    d = ImageDraw.Draw(im)
    za, wr, el, kx, kz = m["za"], m["wrist"], m["elbow"], m["knee_x"], m["knee_z"]
    pts = [("1  KINN (Chin)", [(0, m["chin"])], (1, -1), (245, 197, 24)),
           ("2  HANDGELENKE (Wrists)", [(-wr, za), (wr, za)], (0, -1), (47, 107, 255)),
           ("3  ELLBOGEN (Elbows)", [(-el, za), (el, za)], (0, 1), (46, 180, 90)),
           ("4  KNIE (Knees)", [(-kx, kz), (kx, kz)], (1, 0), (230, 70, 60)),
           ("5  LEISTE (Groin)", [(0, m["groin"])], (1, 0), (190, 80, 220))]
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


RIG_TEXT = "MIXAMO-RIG AUF DER ORIGINAL-PUPPE (Gesichts-Schalter bleiben) · Y-Bot-Animationen, Hüft-Weg auf unsere Beine skaliert"


def rig_sheet(note):
    """Rig-Test-Blatt: 4 Animationen, Gelenke nah, Varianten."""
    T, LBL = 540, 76
    G = (120, 230, 140)
    rows = [[("a_Sitting_Idle", "Sitting Idle"), ("a_Laying_Sleeping", "Laying Sleeping"), ("a_Walking", "Walking"),
             ("a_Look_Over_Shoulder", "Look Over Shoulder")],
            [("j_1_ellbogen", "Ellbogen (sitzend)"), ("j_2_knie", "Knie + Hüfte (sitzend)"), ("j_3_schultern", "Schultern (gehend)"),
             ("j_4_hals", "Hals: Kugel + Ring (Kopf gedreht)")],
            [("v_Schmal_Walking", "Schmal 1,55 m gehend"), ("v_Schmal_Sitting_Idle", "Schmal sitzend"), ("v_Kind_Walking", "Kind 1,15 m gehend"),
             ("v_Kind_Sitting_Idle", "Kind sitzend")]]
    S = Image.new("RGB", (4 * T, LBL * 2 + 3 * T), BG)
    d = ImageDraw.Draw(S)
    d.text((16, 18), RIG_TEXT, font=F(28), fill=YEL)
    for r, row in enumerate(rows):
        for c, (fn, lab) in enumerate(row):
            im = Image.open(f"{RN}rig/{fn}.png").convert("RGB").resize((T, T), Image.LANCZOS)
            S.paste(tag(im, lab, G), (c * T, LBL + r * T))
    d.text((16, LBL + 3 * T + 18), note, font=F(26), fill=FG)
    S.save(AB + "puppe_rig_test.jpg", quality=90)
    print("rig_sheet", S.size)


def rig_sheet2():
    """puppe_rig_test2.jpg: neue Posen, die 5 weiteren Animationen, Prüf-Tabelle Hand im Körper (vorher -> nach Korrektur)."""
    T, LBL = 540, 70
    G = (120, 230, 140)
    pr = json.load(open(RN + "rig_pruefung.json", encoding="utf-8"))
    fx = json.load(open(RN + "rig_fix.json", encoding="utf-8"))
    po = json.load(open(RN + "rig_posen.json", encoding="utf-8"))
    sections = [
        ("NEUE POSEN  (Sitzen_Schlafen: Kopf gesackt, Hände im Schoß, augen-zu, Atem-Schleife 4 s · Kind sitzt auf 0,40 m)",
         [("p_schlafen_Erwachsen", "Sitzen_Schlafen  Erwachsen"), ("p_schlafen_Schmal", "Sitzen_Schlafen  Schmal"),
          ("p_schlafen_Kind", "Sitzen_Schlafen  Kind"), ("p_kind_haengend", "Kind sitzend, Beine hängen"), ("p_schlafen_nah", "Sitzen_Schlafen nah")]),
        ("DIE 5 WEITEREN ANIMATIONEN  (Erwachsen; Hände nach Korrektur aus Kopf/Körper)",
         [("a_Erwachsen_Sitting_Talking", "Sitting Talking"), ("a_Erwachsen_Standing_W_Briefcase_Idle", "Standing W_Briefcase Idle"),
          ("a_Erwachsen_Crouched_Walking", "Crouched Walking"), ("a_Erwachsen_Terrified", "Terrified"), ("a_Erwachsen_Crawling", "Crawling")]),
        ("VARIANTEN",
         [("a_Kind_Terrified", "Kind  Terrified"), ("a_Schmal_Sitting_Talking", "Schmal  Sitting Talking"), ("a_Kind_Sitting_Talking", "Kind  Sitting Talking"),
          ("a_Schmal_Crouched_Walking", "Schmal  Crouched Walking"), ("a_Kind_Crawling", "Kind  Crawling")]),
    ]
    anims = list(dict.fromkeys(k.split("|")[0] for k in pr))
    lines = []
    for an in anims:
        parts = []
        for nm, short in (("Erwachsen", "E"), ("Schmal", "S"), ("Kind", "K")):
            v = pr[f"{an}|{nm}"]
            k = f"{an}|{nm}"
            if v["treffer"] == 0:
                parts.append(f"{short} 0")
            else:
                parts.append(f"{short} {v['treffer']}→{fx.get(k, '?')} (vorher bis {v['tiefe_mm'] / 10:.1f} cm)".replace(".", ","))
        lines.append(f"{an}:  " + " · ".join(parts))
    lines.append("Eigene Posen:  " + " · ".join(f"{k} {v}".replace(".", ",") for k, v in po.items()))
    TAB = 40 + 34 * len(lines)
    S = Image.new("RGB", (5 * T, 3 * (LBL + T) + TAB + 60), BG)
    d = ImageDraw.Draw(S)
    y = 0
    for title, items in sections:
        d.text((16, y + 20), title, font=F(28), fill=YEL)
        y += LBL
        for c, (fn, lab) in enumerate(items):
            im = Image.open(f"{RN}rig2/{fn}.png").convert("RGB").resize((T, T), Image.LANCZOS)
            S.paste(tag(im, lab, G), (c * T, y))
        y += T
    d.text((16, y + 16), "HAND IM KÖRPER/KOPF – Bilder mit Treffer (jedes 2. Bild geprüft), vorher → nach Korrektur:", font=F(28), fill=YEL)
    for i, ln in enumerate(lines):
        d.text((16, y + 60 + 34 * i), ln, font=F(24), fill=FG)
    S.save(AB + "puppe_rig_test2.jpg", quality=90)
    print("rig_sheet2", S.size)


def rig_video():
    """2×2-Video (je 540×540, 114 Bilder = 3,8 s, kürzere Animationen laufen in Schleife) -> puppe_rig_test.mp4."""
    import os
    import subprocess
    import tempfile
    names = [("Sitting_Idle", "Sitting Idle"), ("Laying_Sleeping", "Laying Sleeping"), ("Walking", "Walking"), ("Look_Over_Shoulder", "Look Over Shoulder")]
    tmp = tempfile.mkdtemp()
    for k in range(1, 115):
        S = Image.new("RGB", (1080, 1080), BG)
        for i, (fn, lab) in enumerate(names):
            im = Image.open(f"{RN}rig/video/{fn}_{k:04d}.png").convert("RGB")
            S.paste(tag(im, lab, (120, 230, 140)), ((i % 2) * 540, (i // 2) * 540))
        S.save(f"{tmp}/f_{k:04d}.png")
    out = AB + "puppe_rig_test.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", f"{tmp}/f_%04d.png", "-c:v", "libx264", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-preset", "medium", out], check=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    print(out, round(os.path.getsize(out) / 1e6, 2), "MB")


if __name__ == "__main__":
    vergleich()
    hoodie_test()
    marker()
