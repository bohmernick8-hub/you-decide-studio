"""Stimmspur -> Mund-Formen pro Bild (FIGUREN.md „Sprechen“): Lautstärke + Zischlaute, ≈ 10 Wechsel/s, nie öfter als alle 2 Bilder.
Aufruf: python sprech_mund.py stimme.wav aus.json [bilder]
Formen: 1 m-zu, 2 m-klein, 3 m-offen, 4 m-wellig (nur Angst, hier ungenutzt), 5 m-breit."""
import json
import sys
import wave

import numpy as np

FPS = 30
HOLD = 3  # Bilder pro Mund-Takt -> 10 Wechsel/s


def analyse(path, frames=None):
    with wave.open(path) as w:
        sr, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
        a = np.frombuffer(w.readframes(n), np.int16).astype(np.float32) / 32768
    if ch > 1:
        a = a[::ch]
    total = frames or int(np.ceil(len(a) / sr * FPS))
    hop = sr / FPS
    rms, zcr = np.zeros(total), np.zeros(total)
    for f in range(total):
        s = a[int(f * hop):int((f + 1) * hop)]
        if len(s) > 1:
            rms[f] = np.sqrt((s * s).mean())
            zcr[f] = (np.abs(np.diff(np.sign(s))) > 0).mean()
    return rms, zcr, total


def to_mouth(rms, zcr, total):
    peak = max(np.percentile(rms, 97), 1e-4)
    level = rms / peak
    out = []
    prev = 1
    for f in range(0, total, HOLD):
        lv = level[f:f + HOLD].mean()
        zc = zcr[f:f + HOLD].mean()
        if lv < 0.08:
            m = 1           # Stille: zu
        elif zc > 0.28:
            m = 5           # Zischlaut/E/I: breit
        elif lv > 0.45:
            m = 3           # laut: offen
        else:
            m = 2           # mittel: klein
        # Beim Sprechen nie zweimal dieselbe Form: sonst steht der Mund statt zu „plappern“
        if lv >= 0.08 and m == prev:
            m = {3: 2, 2: 5, 5: 2}[m]
        out += [m] * HOLD
        prev = m
    return out[:total], level


if __name__ == "__main__":
    rms, zcr, total = analyse(sys.argv[1], int(sys.argv[3]) if len(sys.argv) > 3 else None)
    mund, level = to_mouth(rms, zcr, total)
    changes = sum(1 for a, b in zip(mund, mund[1:]) if a != b)
    json.dump({"mund": mund}, open(sys.argv[2], "w"))
    print("Bilder", total, "Wechsel", changes, f"= {changes / (total / FPS):.1f}/s", "Formen", {k: mund.count(k) for k in sorted(set(mund))})
