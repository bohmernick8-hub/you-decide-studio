# FIGUREN – einheitliche Puppen (Nick 05.11.: Qualität vor Menge)

## Was RED-EYE macht (gemessen an den 5 Teilen)
- **Alle Menschen = dieselbe Grund-Puppe**: weiße Kugel, gleiche Augen/Mund, gleiche Fäustlings-Hände. **Keine Haare, keine Körperformen für Mann/Frau.**
- Unterschiede nur über **Größe + Kleidung + Kopfbedeckung + eine Akzentfarbe**:
  - „du“: grauer Hoodie, Schlafmaske hochgeschoben
  - „das kleine Mädchen“: **kleiner (≈ 0,7)**, rote Mütze, ärmelloses blaues Top, Maske
  - Passagiere: Hoodies/Jacken in gedeckten Farben, Caps/Mützen, alle mit derselben Airline-Schlafmaske
  - **Crew (Monster)**: identische Uniform (dunkel, Mütze, goldene Schwingen), schwarzer Filz-Kopf + leuchtendes Grinsen – viele sehen gleich aus (unheimlich durch Gleichheit)
  - Piloten: Uniform von hinten, kein Gesicht
- Geschlecht/Alter wird **gesagt** („the little girl“) und mit Größe/Kleidung unterstützt – nicht modelliert.

## Unsere Regeln
1. **Eine Grund-Puppe** (Kugel-Kopf ⌀ ≈ 0,26 m, weicher Körper, Fäustlinge), mattes Off-White. Drei Körper-Varianten aus demselben Modell: **Erwachsen** (1,75 m), **Erwachsen schmal** (1,65 m, schmalere Schultern), **Kind** (≈ 1,20 m, Kopf relativ größer).
2. **Geschlecht über Kleidung, nicht über Körper**: z. B. Rock/Kleid, Mantel mit Gürtel, Haarband/Spange als feste Form, kleine Ohrstecker – sparsam, nur wenn die Story es braucht. **Keine echten Haare.**
3. **Hauptfiguren** bekommen je **eine eindeutige Akzentfarbe + ein Merkmal**, das in jeder Einstellung sichtbar ist (z. B. gelbe Regenjacke, rote Mütze). So erkennt man sie auch im Dunkeln.
4. **Serien-Requisit** an allen Statisten (wie die Schlafmasken): macht den Ort sofort lesbar.
5. **Monster** = gleiche Bauweise, eigene leuchtende Signatur (emissiv), Berufs-Outfit des Ortes, oft mehrere identische.
6. **Gesichter** als austauschbare Texturen: neutral · Augen zu · erschrocken (größere Ovale) · schläfrig (halbe Bögen). Pro Einstellung festgelegt, nie animiert.

## Outfit-Baukasten (in `assets/characters/characters.blend`)
| Teil | Varianten |
|---|---|
| Oberteil | Hoodie (mit Kordeln), Jacke, Pullover, Hemd, ärmelloses Top, Regenjacke |
| Unten | Jogginghose, Jeans, Rock |
| Kopf | Mütze, Cap, Kapuze auf, Haarband |
| Berufe | Uniform (Mütze + Abzeichen), Kittel, Hotel-Livree, Hausmeister-Overall |
| Serien-Requisit | pro Serie neu (Maske, Armband, Namensschild …) |
| Stoffe | matt, leichte Falten als Normal-Map, Farben gedeckt, 1 Akzentfarbe pro Hauptfigur |

## Ablauf
1. Grund-Puppe modellieren → Standbild neben RED-EYE-Figur (`reference/redeye/frames/p1_1.2.jpg`) → Nick-OK.
2. Export FBX → Nick lädt sie bei **Mixamo** hoch (Auto-Rigger) → gerigged zurück → Animationen aus `C:\ProjectTikTok\assets\mixamo\` testen.
3. Outfits als eigene Objekte, an das Skelett gebunden → in `characters.blend` sammeln.
4. Pro Serie: Steckbrief jeder Figur hier ergänzen (Name, Körper-Variante, Outfit, Akzentfarbe, Merkmal, Gesichter).
