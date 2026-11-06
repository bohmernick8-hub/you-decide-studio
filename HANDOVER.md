# HANDOVER – Stand You Decide Studio (für einen neuen Chat, 06.11.2026)

> Neuer Chat: zuerst diese Datei lesen, dann `CLAUDE.md`, `bible/FORMEL.md`, `bible/STILBIBEL.md`, `bible/FIGUREN.md`, `reference/redeye/ANALYSE.md`.
> Nick: deutsch, kurz, unter allem Testbaren eine Test-Anweisung. Wenig Blender-Kenntnisse. **Qualität vor Menge. Vor jedem neuen Video Nick zuerst fragen, was er besorgen/erstellen muss.**

## Worum es geht
- Neuer TikTok-Kanal (Name noch offen): **interaktive Horror-Serien, Zuschauer entscheiden A/B**. Vorbild: Kanal „malo“ (@playmalo.com), Serie RED-EYE (P1 8,9 Mio., 7 Teile analysiert).
- **Aufbau 1:1 wie RED-EYE** (Hook „Imagine you…“, Details, Uhr, Regel-Dokument, Monster mit Ablauf, Countdown, Doppel-Twist, zwei Wahlen; Part 2+: Rückblick → schlechtes Ende → „Let's rewind“ → Lore → neue Wahl). Inhalte, Orte, Monster, Sätze **eigen**. Nicht 1:1 übersetzen.
- Sprache: **Englisch zuerst** (US), deutscher Zweitkanal später mit denselben Videos.

## Technik (Nicks PC, Windows)
- Blender 5.2 + **MCP for Blender** (in Claude Code lokal eingetragen, `claude mcp list` = Connected; in Blender N → BlenderMCP → Server starten). RTX 3070 8 GB, i7-10700K, 16 GB RAM → **EEVEE**, Cycles nur Standbilder. OptiX + Studio-Treiber eingerichtet. Git, Node, FFmpeg da.
- Repo lokal: `C:\ProjectTikTok\studio` (Branch `main`). Assets: `C:\ProjectTikTok\assets\mixamo\` (Y Bot + 9 Animationen + `puppe_rigged.fbx`), Modelle später nach `C:\ProjectTikTok\assets\models\<name>\` + `credits.txt`.
- Claude Code läuft **lokal** auf Nicks PC (nicht Cloud), weil Blender-MCP nur lokal geht.

## Erledigt
1. RED-EYE-Tiefenanalyse (P1–P7): `reference/redeye/` (Boards, Frames, OCR-Untertitel, ANALYSE.md).
2. STILBIBEL v1 (+ §9: Sprechen, Spiegel, Rewind-Übergang, Weg-Anzeige), FORMEL (Lückentext mit Zeiten), FIGUREN (Signatur, Gesichter, Kleidung).
3. **Grund-Puppe** in `assets/characters/characters.blend`: 1,62 m, Kopf 0,29 m, unsere Signatur (Kapsel-Augen, Guss-Naht, Hals-Kugelgelenk, gebogener Mund), Varianten Kind 1,15 m / Schmal 1,55 m, 15 Ausdrücke + 5 Mund-Formen + Brauen + Glanzpunkt (Schalter `ausdruck`, `mund`, `brauen`, `glanz`). Hoodie-Test OK von Nick.
4. **Mixamo-Skelett** übertragen + Animationstest (Commit 74c677f) – Bericht dazu bringt Nick in den neuen Chat.

## Offene Entscheidungen / nächste Schritte
1. **Bericht zu Commit 74c677f prüfen** (Animationstest: Sitting Idle, Sleeping Idle, Walking, Look Over Shoulder; Gelenke; neues Gesichter-Board + Sprechtest). Abnahmebilder in `reference/abnahme/` ansehen.
2. **Erste Serie wählen.** Vorschlag: **THE WAITING ROOM** (Notaufnahme 3 Uhr nachts, Nummer 47, Anzeige „NOW SERVING 44“, Regel-Plakat, Schwester mit Klemmbrett ruft auf, Countdown = Nummernanzeige). Alternativen: THE LAST BUS, THE GONDOLA. Kein Flugzeug als erste Serie (zu nah an RED-EYE; Nicks Flugzeugkabine für später).
3. **Räume**: Claude baut Räume selbst (Grundriss, Wände, Türen) + Poly-Haven-Materialien; Nick besorgt pro Serie ein **realistisches PBR-Asset-Paket** (FBX/.blend, nicht low poly/stylized, Lizenz CC0/CC-BY/royalty-free, nicht NonCommercial). Nick sucht auf Sketchfab „realistic hospital waiting room PBR“ und schickt 2–3 Kandidaten.
4. **Kleidung** baut Claude selbst (Hoodie, Jacke, Hosen, Mützen, Uniform), Outfit-Referenzbilder per ChatGPT von Nick; Zubehör (Taschenlampe, Klemmbrett …) gern als freie Modelle.
5. **Props-Paket pro Serie** (Logo, Serien-Requisit, Story-Objekt, Piktogramme) per ChatGPT **ohne Text**, Text setzt Claude per Code. Prompt-Vorlage: „Flat front view of a [OBJEKT] for a fictional [ORT] called [NAME], on a plain light grey background, soft even studio lighting, no shadows, no text, no letters, clean product-design style, colors: […], simple bold logo shape: […]. Square image, high resolution.“
6. **Look-Test** (`stories/_test/BRIEF.md`, Auftrag 2) – mit der fertigen Puppe, aber am besten gleich im Ort der ersten Serie statt im Flugzeug.
7. Später: Monster-Design der ersten Serie, Stimme (ElevenLabs, Key nur als Umgebungsvariable), Overlay-Pipeline (Untertitel, A/B-Labels) mit Remotion oder FFmpeg, Kanalname + Logo.
