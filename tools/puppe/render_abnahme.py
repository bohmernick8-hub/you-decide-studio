"""Abnahme-Renders (läuft nach build_puppe.py + abnahme.py im selben Namensraum)."""
import json
import time

from bpy_extras import anim_utils

R = RENDERS
NAMES = ["neutral", "augen-zu", "schlaefrig", "blinzeln", "wach-starr", "neugierig", "aufgeregt", "gluecklich",
         "aengstlich", "erschrocken", "panisch", "traurig", "misstrauisch", "fluestern", "leer"]
MOUTH_NAMES = ["m-zu", "m-klein", "m-offen", "m-wellig", "m-breit"]
BROW_NAMES = ["besorgt", "wuetend", "ueberrascht"]


def clear_anim(ob):
    if ob.animation_data:
        ob.animation_data_clear()


def base():
    scn = bpy.context.scene
    setup_render(scn)
    only("Puppe_Erwachsen")
    P = bpy.data.objects["Puppe_Erwachsen"]
    clear_anim(P)
    P.rotation_euler.z = 0
    face(P)
    statisten(False)
    cam = bpy.data.objects.get("Cam")
    if cam:
        clear_anim(cam)
    scn.frame_set(1)
    return scn, P


def do_views():
    scn, P = base()
    for look in ("nacht", "warm"):
        set_look(look)
        camera((0, -3.7, 1.0), (0, 0, 0.9), 50).data.dof.use_dof = False
        for nm, rz in (("front", 0), ("dreiviertel", 40), ("seite", 90), ("ruecken", 180)):
            P.rotation_euler.z = math.radians(rz)
            render(f"{R}/view_{look}_{nm}.png", 1000, 1000, 48)
    P.rotation_euler.z = 0


def do_hero():
    scn, P = base()
    t = time.time()
    set_look("nacht")
    statisten(True)
    closeup_cam(0.53, 70, 2.0, yaw=9, pitch=-5)
    render(f"{R}/gross_main_nacht.png", 1080, 1920, 64)
    print("nacht s", round(time.time() - t, 1))
    statisten(False)
    t = time.time()
    set_look("warm")
    face(P, 0, 0, 0, 1)
    closeup_cam(0.72, 85, 1.8, yaw=-6, pitch=-2)
    render(f"{R}/gross_main_warm.png", 1080, 1920, 64)
    print("warm s", round(time.time() - t, 1))
    # Körper-Ausschnitt für den Vergleich (etwa wie p1_110)
    face(P)
    camera((1.0, -2.6, 1.42), (0.05, 0, 1.36), 50, 4.0, (0.0, -0.1, 1.5))
    render(f"{R}/koerper_warm.png", 1000, 1000, 48)


def do_lineup():
    scn, P = base()
    only("Puppe_Erwachsen", "Puppe_Schmal", "Puppe_Kind")
    set_look("warm")
    camera((0.1, -8.6, 1.05), (0.1, 0, 0.92), 50).data.dof.use_dof = False
    render(f"{R}/varianten.png", 1600, 800, 48)
    only("Puppe_Erwachsen")


def do_board():
    scn, P = base()
    set_look("nacht")
    # Board: gleiches Nacht-Licht, aber Licht-Band aus dem Bild und mehr Aufhellung, damit jeder Ausdruck lesbar ist
    for nm in ("Set_Decke", "Set_Lichtband"):
        bpy.data.objects[nm].hide_render = True
    aim(bpy.data.objects["Licht_Key"], (0.4, -1.5, 3.0), (0, 0, HEAD_Z - 0.1))
    bpy.data.objects["Licht_Fill"].data.energy = 26.0
    closeup_cam(0.70, 85, 4.0, pitch=-3, res=(720, 720))
    jobs = [(f"a{i:02d}", dict(ausdruck=i)) for i in range(15)]
    jobs += [(f"m{i}", dict(ausdruck=0, mund=i + 1)) for i in range(5)]
    jobs += [(f"b{i}", dict(ausdruck=0, brauen=i + 1)) for i in range(3)]
    jobs += [("g0", dict(ausdruck=0, glanz=1)), ("g1", dict(ausdruck=4))]
    t = time.time()
    for nm, kw in jobs:
        face(P, **kw)
        render(f"{R}/board/{nm}.png", 720, 720, 48)
    print("board s", round(time.time() - t, 1), "je", round((time.time() - t) / len(jobs), 2))
    face(P)


def prep_speech(json_path):
    """Keyframes für den 3-s-Sprechtest: Mund aus der Stimmspur, ein Blinzeln, 3 % Heranfahren."""
    scn, P = base()
    set_look("warm")
    data = json.load(open(json_path))
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = "CONSTANT"
    face(P, 0, 1, 1, 1)
    last = None
    for f, m in enumerate(data["mund"], start=1):
        if m != last:
            P["mund"] = m
            P.keyframe_insert('["mund"]', frame=f)
            last = m
    for f, a in ((1, 0), (36, 3), (39, 0)):
        P["ausdruck"] = a
        P.keyframe_insert('["ausdruck"]', frame=f)
    P["brauen"] = 1
    P.keyframe_insert('["brauen"]', frame=1)
    P["glanz"] = 1
    P.keyframe_insert('["glanz"]', frame=1)
    constant_keys(P)
    cam = closeup_cam(0.72, 85, 1.8, yaw=-6, pitch=-2)
    tgt = Vector((0, 0, HEAD_Z - 0.035))
    start = cam.location.copy()
    prefs.keyframe_new_interpolation_type = "LINEAR"
    cam.keyframe_insert("location", frame=1)
    cam.location = tgt + (start - tgt) * 0.97
    cam.keyframe_insert("location", frame=len(data["mund"]))
    cam.data.dof.focus_distance = cam.data.dof.focus_distance * 0.985
    prefs.keyframe_new_interpolation_type = old
    scn.frame_start, scn.frame_end = 1, len(data["mund"])
    scn.render.resolution_x, scn.render.resolution_y = 1080, 1920
    scn.render.resolution_percentage = 100
    scn.eevee.taa_render_samples = 48
    scn.render.filepath = f"{R}/sprechtest/f_"
    os.makedirs(f"{R}/sprechtest", exist_ok=True)
    # Kontrolle: Schalter-Werte pro Bild
    wrong = []
    for f, m in enumerate(data["mund"], start=1):
        scn.frame_set(f)
        want = 3 if 36 <= f <= 38 else 0
        if P["mund"] != m or P["ausdruck"] != want:
            wrong.append((f, P["mund"], m, P["ausdruck"], want))
    scn.frame_set(1)
    print("Schalter-Fehler:", wrong[:8], "von", len(data["mund"]))


def constant_keys(ob):
    """Schalter springen hart von Form zu Form (kein Überblenden durch die Zwischen-Indizes)."""
    ad = ob.animation_data
    bag = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    for fc in bag.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
        fc.update()


def render_chunk(a, b):
    scn = bpy.context.scene
    scn.frame_start, scn.frame_end = a, b
    t = time.time()
    bpy.ops.render.render(animation=True)
    print(f"frames {a}-{b}: {round((time.time() - t) / (b - a + 1), 2)} s/Bild")
