# You Decide Studio – Projekt-Gedächtnis für Claude Code

Neuer TikTok-Kanal von Nick (Start Nov. 2026): **interaktive Horror-Serien – der Zuschauer entscheidet** (A/B in den Kommentaren, nächster Teil folgt der Mehrheit).
Vorbild-Stil: Kanal „malo“ (@playmalo.com), Serie RED-EYE (P1 8,9 Mio.). **Stil + Handwerk übernehmen, Inhalte/Figuren/Sätze nie** (eigene Serien, eigene Puppe, eigenes Monster).
Mit Nick: **Deutsch, kurz**, unter allem Testbaren eine kurze Test-Anweisung. Nick hat wenig Blender-Kenntnisse → Claude macht die Blender-Arbeit, Nick klickt nur, wenn nötig.

## Die eine Linie
1. `bible/STILBIBEL.md` – Look, Licht, Kamera, Figuren, Schnitt, Untertitel, A/B-Labels, Ton, Dramaturgie (**schlägt jede andere Datei**).
2. `reference/redeye/` – Vorbild-Bilder + Analyse.
3. `bible/LEARNINGS.md` – Fehler aus früheren Folgen (jedes Mal lesen, jedes Mal ergänzen).

## Werkzeuge (Nicks PC, Windows)
- **Blender 5.2** auf dem PC, gesteuert über **MCP for Blender** (`claude mcp add blender uvx mcp-for-blender`; in Blender N-Leiste → BlenderMCP → Start/Connect). Poly Haven an, Sketchfab-Key optional.
- **Hardware:** RTX 3070 (8 GB VRAM), i7-10700K, 16 GB RAM. → Render-Engine **EEVEE** (Raytracing an), Cycles nur für Standbilder/Cover. Texturen ≤ 2K, Wiederholungen als Instanzen, Szenen schlank halten. OptiX ist in den Preferences aktiv.
- Git, Node.js LTS, FFmpeg sind installiert.
- **Assets:** `C:\ProjectTikTok\assets\mixamo\` (Y Bot T-Pose + 9 Animationen: Sitting Idle, Sleeping Idle, Sitting Talking, Standing Idle, Walking, Crouched Walking, Look Over Shoulder, Terrified, Crawling – FBX, 30 fps, Without Skin). Y Bot = nur Test-Dummy/Skelett; finale Figur = eigene Puppe (Kugel-Kopf, mattes Weiß), über den Mixamo-Auto-Rigger geriggt.
- Repo liegt lokal in `C:\ProjectTikTok\studio`.

## Arbeitsteilung
Blender rendert nur die Bilder (PNG-Sequenzen pro Einstellung, 1080×1920, 30 fps). Untertitel, A/B-Labels, Stimme, Musik, Schnitt kommen danach (Remotion oder FFmpeg – wird in der STILBIBEL festgelegt).

## Vor jedem NEUEN Video (Nick 05.11., Pflicht)
**Erst Nick fragen, dann bauen.** Vor jeder neuen Folge eine kurze Liste an Nick: was er erstellen/besorgen muss (Props-Bilder per ChatGPT mit Prompt, 3D-Modelle/Orte, Stimme, Cover-Idee) + was Claude selbst baut. Erst nach Nicks OK und wenn die Dateien in `assets/props/<serie>/` liegen, mit dem Bau anfangen. **Qualität vor Menge.**

## Figuren-Bibliothek (einheitlich, nie pro Folge neu bauen)
Alle Figuren liegen in **einer** Datei `assets/characters/characters.blend` (Basis-Puppe + Körper-Varianten + Outfit-Teile + Gesichts-Texturen) und werden in jede Szene **verlinkt** (Link/Library Override), nicht kopiert. Änderung an der Figur = nur dort. Steckbriefe: `bible/FIGUREN.md`.

## Goldene Regeln
- Keine echten Marken/Firmen/Personen (Airline, Hotel usw. erfunden). Horror durch Andeutung, kein Blut, keine Gewalt-Details.
- **Keine Secrets in Dateien** (ElevenLabs-Key nur als Umgebungsvariable `ELEVENLABS_API_KEY`).
- Jede neue Szene: erst Standbild neben das Vorbild legen, dann animieren, dann rendern.
