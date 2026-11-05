# AUFTRAG 1 für Claude Code (lokal auf Nicks PC): Look-Test „Sitzreihe bei Nacht“

> Ziel: beweisen, dass wir den RED-EYE-Look in Blender auf Nicks PC hinbekommen, **bevor** wir eine Serie schreiben.
> Lies: `CLAUDE.md`, `bible/STILBIBEL.md`, `reference/redeye/ANALYSE.md`, Bilder in `reference/redeye/frames/` + `boards/redeye-p1.jpg`.
> Hinweis: Das ist ein **Test**. Für den Test darf ein Flugzeug-Innenraum verwendet werden; unsere erste echte Serie bekommt einen eigenen Ort.

## 0. Prüfen
- Blender läuft, MCP verbunden (in Blender N-Leiste → BlenderMCP → Server läuft). Kurztest: Szene-Info abfragen.
- Render-Gerät: Preferences → System → OptiX + RTX 3070 (Nick hat es eingestellt – nur prüfen).

## 1. Ort
- Flugzeugkabine laden: zuerst Sketchfab (falls Key gesetzt, Suche „airplane cabin interior“, frei/CC-Lizenz, ≤ 150k Polygone), sonst Poly Haven/selbst bauen (Gang, 6 Sitzreihen links/rechts, Gepäckfächer, Decken-Bildschirm). Texturen ≤ 2K.
- Licht nach STILBIBEL §3: Nacht, Gangleuchten am Boden, ein blauer Deckenbildschirm (emissiv), Fenster-Rollos zu mit schmalem warmem Spalt, leichter Volumen-Dunst.

## 2. Figuren
- Platzhalter: Mixamo **Y Bot** aus `C:\ProjectTikTok\assets\mixamo\` mit Animation **Sleeping Idle**/**Sitting Idle**, Material mattes Off-White; Kopf durch eine weiße Kugel ersetzen (an den Kopf-Knochen gehängt), Gesicht als einfache Textur (Bögen = Augen zu, Strich-Mund). 6–10 Passagiere als Instanzen, 1 „du“ vorne.

## 3. Drei Test-Einstellungen (je 3 s, langsames Heranfahren 3 %)
1. **Groß-Gesicht** „du“ schläft (wie `frames/p1_1.2.jpg`), 70 mm, f/2.
2. **Gang-Totale zentriert** bis zum Bildschirm (wie Board P1 3,6 s), 26 mm.
3. **Insert** Sitztaschen-Karte (eigenes Design, erfundene Airline „NOCTURNE AIR“) wie Board P1 39 s.
Render EEVEE 1080×1920, 30 fps, PNG-Sequenzen nach `renders/_test/<shot>/`. Renderzeit pro Bild notieren.

## 4. Abnahme
- Je Einstellung Standbild neben das Vorbild → `reference/abnahme/test_<shot>.jpg` (links RED-EYE, rechts wir).
- Messen: Ø Helligkeit (Ziel Luma 55–75/255), Renderzeit pro Bild (Ziel ≤ 3 s).
- Kurzbericht an Nick (Deutsch, kurz): 3 Vergleichsbilder, Renderzeit, was noch fehlt. Dann `git add` (ohne Renders), Commit + Push.
