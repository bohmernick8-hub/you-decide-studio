# STILBIBEL v1 – You Decide Studio (Look = RED-EYE 1:1, Inhalte eigen)

> Grundlage: `reference/redeye/ANALYSE.md` + `boards/` + `frames/`. Diese Datei schlägt jede andere.
> Ziel: Ein Standbild von uns muss neben einem RED-EYE-Standbild wie aus derselben Produktion aussehen. Inhalte (Orte, Monster, Regeln, Sätze) sind immer **unsere eigenen**.

## 1. Format
- 1080×1920, 30 fps, Länge **Part 1: 100–125 s**, Part 2+: 95–135 s. Sprache: Englisch (Deutsch als zweite Fassung möglich, gleiche Bilder).
- Ein Ort pro Serie, ein Monster pro Serie, eine Regel-Mechanik pro Serie, 4–5 Teile. Teile schnell nacheinander (läuft Part 1: Part 2 innerhalb von 12–24 h).

## 2. Dramaturgie
**Part 1** (Zeiten Richtwert): Hook „Imagine you …“ (0–4 s) → 5–6 unheimliche Details, je eine Einstellung (4–20 s) → Uhr/Anker als Insert (20–27 s) → **Regel-Dokument** mit nummerierten, illustrierten Regeln (27–42 s) → Unglaube (1 Satz) → **Monster mit festem Ablauf** (44–63 s) → **Countdown über Distanz/Zeit** (63–77 s) → Höhepunkt mit Sinnesdetails, du darfst dich nicht rühren (77–93 s) → **Doppel-Twist**: Regel scheint aufgehoben + eine Person widerspricht (93–107 s) → „Two choices. [A + guter Grund]. Or [B + guter Grund]. So, what would you do?“ mit A/B-Labels, letzte Einstellung 10–13 s halten.
**Part 2+**: „So, did you [A] … or did you [B]?“ → „If you [falsche Wahl] …“ kurzes schlechtes Ende (10–15 s, ohne Gewalt) → „Let's rewind.“ → richtige Wahl geht weiter → **Lore mit konkreten Zahlen** → neue Bedrohung mit neuem Ablauf → neue Zweier-Wahl.
- Erzähler in Du-Form, Gegenwart, kurze Sätze (2–8 Wörter), ≈ 2,5 Wörter/s, ≈ 290–320 Wörter bei 120 s.
- Hook-Regel aus Nicks Daten (bible/HOOKS.md im story-studio): **erste 3 s nur Bild + Untertitel**, eine Information, Alltag, Du-Form.

## 3. Look (Blender)
- **Engine: EEVEE** (RTX 3070, 8 GB). Raytracing an (Methode Screen-Trace, Auflösung ½, Denoise an), Schatten hoch (Virtual Shadow Maps, Auflösung hoch, weiche Schatten), **Volumetrie**: World-Volume „Principled Volume“ Dichte 0,005–0,015 für leichten Dunst (Lichtkegel sichtbar), Bewegungsunschärfe an (Shutter 0,5).
- **Farbe**: Color Management **AgX**, Look „Medium High Contrast“, Belichtung −0,3 … −0,8. Nachtstimmung: Schatten Blaugrau (≈ #141821), Lichter kühl (≈ #C8D2E0); „Licht an“: warm (≈ #EDE3D2); Gefahr: Rot.
- **Dunkelheit**: 60–75 % des Bildes in Schatten, Ø Helligkeit ≈ 25 % (Luma 60–70/255). Jede Einstellung hat 1–3 motivierte Lichtquellen (Bildschirm, Bodenleiste, Fensterspalt, Taschenlampe, Leuchtschild).
- **Kamera-Optik**: Tiefenunschärfe an (f/2,0–2,8, Fokus auf Gesicht/Objekt), Brennweiten: Gesicht 50–85 mm, Gang-Totale 24–28 mm zentriert, Inserts 50–100 mm.
- **Nachbearbeitung (Compositor)**: Glare „Fog Glow“ / Bloom nur auf hellen/emissiven Stellen (Grinsen, Bildschirme), leichte Vignette, **Filmkorn** (Rauschen, sehr dezent), keine Schärfung.
- **Leistung**: Texturen ≤ 2K, wiederholte Objekte (Sitze, Passagiere) als Instanzen/Linked Duplicates, Render-Samples EEVEE 32–64. Ziel ≤ 3 s pro Bild. Vor jedem Render: Chrome & Co. schließen (16 GB RAM).

## 4. Figuren
- **Puppe (Passagiere, „du“)**: Kopf = glatte Kugel, mattes Off-White (≈ #E8E6E1, Roughness 0,55, minimal Subsurface), Körper weich-klobig, Fäustlings-Hände. Gesicht als Decal/Textur: zwei kleine dunkle Ovale (offen) bzw. Bögen (geschlossen), kurzer Strich-Mund – **Gesichtsausdrücke als austauschbare Texturen** (neutral, Augen zu, erschrocken, schläfrig), keine Mimik-Animation.
- Kleidung schlicht (Hoodie mit Kordeln, Cap, Mütze), gedeckte Farben; pro Serie ein **Serien-Requisit** an allen (bei RED-EYE: Schlafmasken mit Airline-Logo – bei uns eigenes).
- **Monster**: gleiche Puppen-Bauweise, aber eigene Signatur, die im Dunkeln leuchtet (emissiv, Bloom) und eine Berufs-/Ortsrolle hat. Nie das Grinse-Gesicht von RED-EYE kopieren.
- **Skelett/Animation**: eigene Puppe über **Mixamo-Auto-Rigger** riggen; Animationen aus `C:\ProjectTikTok\assets\mixamo\` (bis die Puppe fertig ist: Y Bot als Platzhalter). Bewegungen langsam: sitzen, schlafen, Kopf drehen, vorbeugen, gehen. Füße/Hintern immer mit Kontakt (Sitz, Boden).

## 5. Kamera + Schnitt
- **Ruhig**: jede Einstellung ein Standbild mit langsamem Heranfahren (2–5 % Größe über die Einstellung) oder ganz still. Keine Wackelkamera, keine schnellen Schwenks, kein Zoom-Ruck.
- Einstellungs-Mix: Groß-Gesicht · zentrierte Gang-/Raum-Totale (Fluchtpunkt mittig) · Insert · POV. Nie zwei gleiche Größen hintereinander.
- Ø 2,5–3,5 s pro Einstellung; Spannungsstellen 1–2 s; Wahl-Einstellung 10–13 s.

## 6. Untertitel + Grafik (Overlay nach dem Render)
- Schrift: **Montserrat ExtraBold** (o. ä. runde Grotesk), Großbuchstaben, Weiß, weicher Schatten (0 2 px 8 px, 60 % Schwarz). Mitte bei **69 % der Bildhöhe**, Großbuchstaben ≈ 58 px, max. 70 % Breite.
- **2–3 Wörter pro Einblendung**, wortgenau aus den Zeitstempeln der Stimme; noch nicht gesprochene Wörter grau (≈ 55 % Weiß), gesprochene weiß.
- **A/B-Labels**: dunkle Pille (≈ #1B1D22, 90 %), 2 px weißer Rand (80 %), Radius 12 px, links Kreis mit Buchstabe (**A gelb #F5C518**, **B blau #2F6BFF**), Text weiß fett groß (≈ 34 px), **2 px weiße Linie** zu einem kleinen Ring am Ziel im Bild. Pillen nie über Gesichtern.
- Inserts als echte Gegenstände (Bildschirm, Karte, Schild) im eigenen Design mit erfundenen Firmennamen.

## 7. Ton
- Erzähler ruhig, nah, tief (ElevenLabs, Stimme legt Nick fest), Figuren-Stimmen sparsam (Durchsage, Flüstern).
- Geräusche aus der Szene (Schritte, Klicks, Atmen, Lüftung), Musik nur leiser Drone, Spannung über Stille. Master −11 bis −12 LUFS.

## 8. Abnahme (jede Einstellung)
Standbild neben ein passendes RED-EYE-Bild aus `reference/redeye/boards/`: gleiche Helligkeit, gleiche Farbstimmung, gleiche Figuren-Größe im Bild, Untertitel/Labels an derselben Stelle. Bugs: nichts schwebt, keine Figur steckt im Sitz, keine Kamera in Wänden, kein Flackern.
