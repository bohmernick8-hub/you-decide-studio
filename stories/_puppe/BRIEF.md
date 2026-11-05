# AUFTRAG 1 (vor dem Look-Test): Die Grund-Puppe – perfekt (Nick 05.11.)

> Die Puppe ist das Element, das in jeder Einstellung vorkommt → sie zuerst perfekt machen, dann alles andere.
> Lies: `CLAUDE.md`, `bible/STILBIBEL.md` §4, `bible/FIGUREN.md`, Vorbilder `reference/redeye/frames/p1_1.2.jpg`, `p1_84.jpg`, `p1_110.jpg`, `p2_*.jpg` und die Gesichts-Einstellungen in `reference/redeye/boards/redeye-p1.jpg`.
> Danach erst `stories/_test/BRIEF.md` (Look-Test) – mit dieser Puppe statt Y Bot.

## 1. Proportionen aus den Vorbildern ableiten (zuerst!)
Aus 4–6 Vorbild-Bildern messen und in `bible/FIGUREN.md` → „Maße Grund-Puppe“ eintragen: Kopf-Ø im Verhältnis zur Schulterbreite und zur Körperhöhe, Augen-Höhe auf dem Kopf (von oben in %), Augen-Abstand, Augen-Größe, Mund-Länge/-Höhe, Hals sichtbar ja/nein, Hand-Form (Fäustling, Daumen ja/nein), Arm-/Bein-Dicke. Vergleichsbild mit Maßlinien → `reference/abnahme/puppe_masse.jpg`.

## 1b. Unsere Signatur (Pflicht)
Die 4 Merkmale aus `bible/FIGUREN.md` → „UNSERE Signatur“: senkrechte Kapsel-Augen, feine Guss-Naht über den Kopf, Kugelgelenk am Hals, leicht gebogener Mund. Proportionen wie RED-EYE, Gesicht + Details eigen. Im Vergleichsbild (Schritt 4) muss man den Unterschied sofort sehen, aber die Stil-Familie muss gleich wirken.

## 2. Modell (Blender, über MCP)
- **Ein** sauberes Mesh in **T-Pose**, Quads, ≈ 10–30k Dreiecke, Maßstab echt (1,75 m), Füße auf Z = 0, Blick nach −Y (Blender-Front).
- Kopf: glatte Kugel (Subdivision, keine Kanten), Größe laut Maßen; Körper weich-klobig, Gelenke (Schulter, Ellbogen, Knie, Hüfte) mit genug Kanten zum Biegen; Fäustlings-Hände laut Vorbild.
- Drei Varianten aus demselben Modell (Shape Keys oder Kopien): **Erwachsen 1,75 m**, **Erwachsen schmal 1,65 m**, **Kind 1,20 m** (Kopf relativ größer).

## 3. Material + Gesicht
- Material: Off-White ≈ #E8E6E1, Roughness 0,5–0,6, ganz leichter Sheen + minimal Subsurface (wirkt wie mattes Vinyl). Im Look-Licht testen, nicht im Standard-Licht.
- Gesichter als **Texturen** (per Code erzeugt, PNG 2K, transparent), auf den Kopf projiziert, austauschbar über einen Schalter: `neutral`, `augen-zu` (Bögen), `schlaefrig` (halbe Lider über den Kapseln), `erschrocken` (größere Kapseln), `wach-starr` (mit winzigem Glanzpunkt) – alle mit den senkrechten Kapsel-Augen. Linienfarbe ≈ #1A1A1A, weiche Kante.

## 4. Abnahme 1 (Standbild, noch ohne Skelett)
- Render EEVEE mit Look-Licht aus STILBIBEL §3: Vorderansicht, ¾, Seite, Rücken + **Groß-Gesicht** in allen 5 Gesichtern.
- Vergleich neben die Vorbild-Bilder → `reference/abnahme/puppe_vergleich.jpg` (links RED-EYE, rechts wir).
- **Stopp → Bild an Nick, auf OK warten.**

## 5. Skelett (nach Nicks OK)
- Export `assets/characters/puppe_tpose.fbx` (nur Mesh, T-Pose).
- **Nick**: auf mixamo.com → „Upload Character“ → Datei hochladen → Marker setzen (Kinn, Handgelenke, Ellbogen, Knie, Leiste) → herunterladen „FBX, With Skin, T-Pose“ → Datei nach `C:\ProjectTikTok\assets\mixamo\puppe_rigged.fbx`. (Claude schreibt ihm die Schritte mit Screenshot-Hinweisen.)
- Import, Animationen aus `C:\ProjectTikTok\assets\mixamo\` drauf: **Sitting Idle, Sleeping Idle, Walking, Look Over Shoulder**. Prüfen: Schultern/Ellbogen/Knie knicken sauber, Hände durchdringen nichts, Kopf bleibt rund. Gewichte bei Bedarf korrigieren.

## 6. Ablage
- Alles in `assets/characters/characters.blend` (Collection „Puppe“ mit Varianten, Gesichts-Schalter, Material). `.blend` committen (Größe < 50 MB), Renders nicht.
- `bible/FIGUREN.md` ergänzen (Maße, Material, Gesichter, Varianten), `bible/LEARNINGS.md` (was schwierig war). Kurzbericht an Nick mit Vergleichsbild.
