# LEARNINGS

Fehler und Erkenntnisse – vor jeder Folge lesen, nach jeder Folge ergänzen.

## Grund-Puppe (05.11.)
- **Proportionen nie von Hand aus dem Bild schätzen**, wenn es exakt geht: Augenmaß ergab „Rumpf 2,35 D“, projiziert waren es 2,46 D (anderes Maß) bzw. 2,19 D am Modell. Immer Kamera wie im Vorbild nachstellen und Punkte projizieren, dazu den echten 3D-Wert angeben.
- **Maße am Mesh exakt per Querschnitt** (Kanten mit Ebene schneiden), nicht per Punkt-Stichprobe: die Stichprobe lag bis 0,03 D daneben.
- **Ein Maß zuerst definieren, dann messen** – „Rumpf bis Hände“ hängt von der Pose ab, „Kopf-Unterkante → Oberschenkel“ nicht.
- **Subdivision**: Flächen vorher einheitlich ausrichten (`recalc_face_normals`), sonst entstehen harte Knicke an Hüfte/Schulter.
- **Gesichts-Schalter brauchen CONSTANT-Keyframes**; linear überblendet zeigt Blender Zwischen-Gesichter.
- **Aufdruck (Augen/Mund) ohne Glanz, Sheen und Subsurface**, sonst wird er im Streiflicht grau.
- **Blender ohne Oberfläche (`-b`) liest die gespeicherte Datei**: Bauen und Messen im selben Lauf, sonst misst man das alte Modell.
- **Mittellinien-Suche**: Schritt = tiefster Punkt der Mittellinie (min), nicht der höchste – der Leisten-Marker saß sonst am Bauch.
- **Verbundene Knochen teilen Punkte**: beim Anpassen eines Skeletts alle Zielpunkte vorher berechnen, sonst wird ein Kind-Knochen doppelt verschoben.
- **Parent „Transform behalten“** über `matrix_parent_inverse`, nicht über `matrix_world` – sonst kippt die Puppe, sobald das Skelett entfernt wird.
- **Mixamo-Animationen vom Y Bot**: Hüft-Weg ist in cm und für 1 m Hüfthöhe gemacht → auf unsere Beinlänge skalieren. Unsere Puppe ist breiter → Oberarme leicht abspreizen; Hände können trotzdem bei schnellen Arm-Bewegungen streifen (Look Over Shoulder).
- **Kleidung zum Prüfen von Proportionen**: nackt wirkt die Puppe schlanker als angezogene Vorbilder; ein einfacher Hoodie-Proxy (Hülle aus dem Körper, gleiche Gewichte) reicht für den Vergleich.
