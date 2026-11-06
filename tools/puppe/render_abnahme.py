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


def head_center(ob):
    rank, roots = island_ids(ob.data)
    isl = np.array([rank[int(r)] for r in roots])
    return world_coords(ob)[isl == 1].mean(axis=0)


def sit_cam(hc, dof=False):
    """Kamera wie RED-EYE P1 110 s (Kopf ≈ 30 % der Bildbreite, leicht von unten), relativ zum sitzenden Kopf."""
    z = float(hc[2])
    return camera((0.54, -1.50, z - 0.331), (0.15, -0.10, z - 0.10), 34, 2.8 if dof else None, (0, -0.1, z - 0.02) if dof else None)


def do_posen():
    """Körper sitzend + stehend für den Vergleich (Hilfs-Skelett aus pose_test.py, nicht das Mixamo-Rig)."""
    cleanup()
    scn, P = base()
    only()
    set_look("warm")
    ob, rig = make_posed("Erwachsen")
    # stehend wie RED-EYE P2 31,3 s (von hinten, ein Arm ausgestreckt)
    apply_pose(rig, pose_stehen(rig, reach=True))
    ground(ob, rig)
    rig.rotation_euler.z = math.pi
    dz = VARIANTS["Erwachsen"]["H"] - 1.75
    camera((-0.24, -0.90, 1.30 + dz), (0.05, 0, 1.24 + dz), 26, 2.8, (0, 0.05, 1.45 + dz))
    render(f"{R}/pose_steh_p2.png", 1080, 1920, 64)
    rig.rotation_euler.z = 0
    # stehend, Arme hängen: vorn / Seite / Rücken
    apply_pose(rig, pose_stehen(rig))
    ground(ob, rig)
    za = rig_joints(VARIANTS["Erwachsen"])["za"]
    w = world_coords(ob)
    band = (w[:, 2] > za - 0.06) & (w[:, 2] < za + 0.07)
    print("Schulterbreite stehend /D:", round(float(w[band, 0].max() - w[band, 0].min()) / 0.29, 3))
    camera((0, -3.9, 0.88), (0, 0, 0.81), 50).data.dof.use_dof = False
    for nm, rz in (("vorn", 0), ("seite", 90), ("ruecken", 180)):
        rig.rotation_euler.z = math.radians(rz)
        render(f"{R}/pose_steh_{nm}.png", 900, 900, 48)
    rig.rotation_euler.z = 0
    # sitzend wie RED-EYE P1 110 s
    apply_pose(rig, pose_sitzen(rig))
    ground(ob, rig)
    print("Sitz:", seat_for(ob, rig))
    ob["ausdruck"] = 1
    sit_cam(head_center(ob), dof=True)
    render(f"{R}/pose_sitz_p1.png", 1080, 1920, 64)
    camera((0, -3.8, 0.76), (0, -0.05, 0.64), 50).data.dof.use_dof = False
    for nm, rz in (("dreiviertel", 35), ("seite", 90)):
        rig.rotation_euler.z = math.radians(rz)
        render(f"{R}/pose_sitz_{nm}.png", 900, 900, 48)
    cleanup()


def do_hoodie():
    """Hoodie-Proxy sitzend im Nachtlicht, gleiche Kamera wie der Körper-Vergleich zu RED-EYE P1 110 s."""
    cleanup()
    scn, P = base()
    only()
    set_look("nacht")
    p = VARIANTS["Erwachsen"]
    ob, rig = make_posed("Erwachsen")
    make_hoodie(ob, rig, rig_joints(p))
    apply_pose(rig, pose_sitzen(rig))
    ground(ob, rig)
    print("Sitz:", seat_for(ob, rig, pad=0.03))
    ob["ausdruck"] = 1
    hc = head_center(ob)
    # Nacht-Licht wandert mit dem Kopf nach unten; Kabinen-Leiste aus dem Bild, Wand als ruhiger Hintergrund nah heran
    dz = float(hc[2]) - HEAD_Z
    for nm in ("Licht_Key", "Licht_Fill", "Licht_Rim"):
        bpy.data.objects[nm].location.z += dz
    bpy.data.objects["Licht_Fill"].data.energy = 24.0
    for nm in ("Set_Decke", "Set_Lichtband"):
        bpy.data.objects[nm].hide_render = True
    bpy.data.objects["Set_Wand"].location.y = 2.4
    sit_cam(hc, dof=True)
    render(f"{R}/hoodie_nacht_p1.png", 1080, 1920, 64)
    camera((1.15, -2.75, 0.82), (0.0, -0.04, 0.70), 50).data.dof.use_dof = False
    render(f"{R}/hoodie_nacht_ganz.png", 1080, 1920, 64)
    cleanup()


RIG_ANIMS = [("Sitting Idle", 44), ("Laying Sleeping", 1), ("Walking", 11), ("Look Over Shoulder", 76)]


def _rig_setup():
    scn = bpy.context.scene
    setup_render(scn)
    set_look("warm")
    statisten(False)
    for o in bpy.data.collections["Puppe"].objects:
        if o.type == "MESH":
            face(o)
    return scn


def _ground_anim(rig, mesh, lo, hi):
    scn = bpy.context.scene
    mins = []
    for f in range(lo, hi + 1, max(1, (hi - lo) // 12)):
        scn.frame_set(f)
        mins.append(float(world_coords(mesh)[:, 2].min()))
    rig.location.z = -min(mins)


def _bone_w(rig, nm):
    return rig.matrix_world @ rig.pose.bones["mixamorig:" + nm].head


def _anim_on(variant, name, seat_frame=44):
    rig, mesh = bpy.data.objects["Rig_" + variant], bpy.data.objects["Puppe_" + variant]
    only("Puppe_" + variant)
    lo, hi = apply_action(rig, name)
    _ground_anim(rig, mesh, lo, hi)
    if name == "Sitting Idle":
        bpy.context.scene.frame_set(seat_frame)
        seat_for(mesh, rig, pad=0.0)
    return rig, mesh, lo, hi


def _anim_off(rig, variant):
    cleanup()
    clear_action(rig)
    rig.location = Vector(VARIANTS[variant]["loc"])


def do_rig_test():
    """Standbilder fürs Rig-Test-Blatt: 4 Animationen, Gelenke nah, Varianten."""
    scn = _rig_setup()
    out = f"{R}/rig"
    shots = []
    for name, f in RIG_ANIMS:
        rig, mesh, lo, hi = _anim_on("Erwachsen", name)
        scn.frame_set(f)
        c = _bone_w(rig, "Spine")
        off = {"Laying Sleeping": (1.1, -2.0, 1.3)}.get(name, (1.2, -2.6, 0.15))
        camera((c.x + off[0], c.y + off[1], c.z + off[2]), tuple(c), 50).data.dof.use_dof = False
        render(f"{out}/a_{name.replace(' ', '_')}.png", 900, 900, 48)
        if name == "Sitting Idle":
            t = _bone_w(rig, "LeftForeArm")
            camera((t.x + 0.9, t.y - 1.3, t.z + 0.35), tuple(t), 50).data.dof.use_dof = False
            render(f"{out}/j_1_ellbogen.png", 900, 900, 48)
            t = _bone_w(rig, "LeftLeg")
            camera((t.x + 1.4, t.y + 0.1, t.z + 0.25), tuple(t), 50).data.dof.use_dof = False
            render(f"{out}/j_2_knie.png", 900, 900, 48)
        if name == "Walking":
            t = _bone_w(rig, "Spine2")
            camera((t.x + 0.2, t.y - 1.6, t.z + 0.1), tuple(t), 50).data.dof.use_dof = False
            render(f"{out}/j_3_schultern.png", 900, 900, 48)
        if name == "Look Over Shoulder":
            t = _bone_w(rig, "Neck")
            camera((t.x + 0.45, t.y - 0.8, t.z + 0.05), tuple(t), 50).data.dof.use_dof = False
            render(f"{out}/j_4_hals.png", 900, 900, 48)
        _anim_off(rig, "Erwachsen")
    for variant in ("Schmal", "Kind"):
        for name, f in (("Walking", 11), ("Sitting Idle", 44)):
            rig, mesh, lo, hi = _anim_on(variant, name)
            scn.frame_set(f)
            c = _bone_w(rig, "Spine")
            camera((c.x + 1.2, c.y - 2.6, c.z + 0.12), tuple(c), 50).data.dof.use_dof = False
            render(f"{out}/v_{variant}_{name.replace(' ', '_')}.png", 900, 900, 48)
            _anim_off(rig, variant)
    only("Puppe_Erwachsen", "Puppe_Schmal", "Puppe_Kind")
    scn.frame_set(1)


SEATED = ("Sitting Idle", "Sitting Talking")


def _pose_on(variant, action_name, seat=True):
    """Eigene Pose (Aktion aus der Bibliothek) anhängen; Sitz unter das Becken."""
    rig, mesh = bpy.data.objects["Rig_" + variant], bpy.data.objects["Puppe_" + variant]
    only("Puppe_" + variant)
    clear_action(rig)
    ensure_actions([action_name])
    ad = rig.animation_data_create()
    ad.action = bpy.data.actions[action_name]
    if ad.action_slot is None:
        ad.action_slot = ad.action.slots[0]
    bpy.context.scene.frame_set(1)
    if seat:
        seat_for(mesh, rig, pad=0.0)
    return rig, mesh


def _shot(rig, path, target_bone, off, lens=50, res=900):
    c = _bone_w(rig, target_bone)
    camera((c.x + off[0], c.y + off[1], c.z + off[2]), tuple(c), lens).data.dof.use_dof = False
    render(path, res, res, 48)


def do_rig_test2():
    """Standbilder für puppe_rig_test2.jpg: neue Posen, die 5 weiteren Animationen, Varianten."""
    scn = _rig_setup()
    out = f"{R}/rig2"
    front = (1.2, -2.6, 0.15)
    # Reihe 1: Sitzen_Schlafen (3 Puppen), Kind mit hängenden Beinen, Nah-Bild
    for variant in ("Erwachsen", "Schmal", "Kind"):
        rig, mesh = _pose_on(variant, "Pose_Sitzen_Schlafen_" + variant)
        face(mesh, ausdruck=1)
        _shot(rig, f"{out}/p_schlafen_{variant}.png", "Spine", front)
        if variant == "Erwachsen":
            _shot(rig, f"{out}/p_schlafen_nah.png", "Spine2", (0.55, -1.25, 0.05))
        face(mesh)
        _anim_off(rig, variant)
    rig, mesh = _pose_on("Kind", "Pose_Kind_Sitzen_Haengend")
    scn.frame_set(44)
    _shot(rig, f"{out}/p_kind_haengend.png", "Spine", (1.9, -1.4, -0.05))
    _anim_off(rig, "Kind")
    # Reihe 2 + 3: die 5 weiteren Animationen
    shots = [("Erwachsen", "Sitting Talking", 263), ("Erwachsen", "Standing W_Briefcase Idle", 100), ("Erwachsen", "Crouched Walking", 11),
             ("Erwachsen", "Terrified", 400), ("Erwachsen", "Crawling", 14),
             ("Kind", "Terrified", 400), ("Schmal", "Sitting Talking", 600), ("Kind", "Sitting Talking", 263), ("Schmal", "Crouched Walking", 21),
             ("Kind", "Crawling", 40)]
    for variant, name, f in shots:
        rig, mesh, lo, hi = _anim_on(variant, name, seat_frame=f)
        if name in SEATED and name != "Sitting Idle":
            scn.frame_set(f)
            seat_for(mesh, rig, pad=0.0)
        scn.frame_set(f)
        off = {"Crawling": (1.5, -2.2, 0.6)}.get(name, front)
        _shot(rig, f"{out}/a_{variant}_{name.replace(' ', '_')}.png", "Spine", off)
        _anim_off(rig, variant)
    only("Puppe_Erwachsen", "Puppe_Schmal", "Puppe_Kind")
    scn.frame_set(1)


def do_rig_video(name, a, b, frames=114):
    """Bilder für das 2×2-Bewegungsvideo (Kamera folgt der Hüfte). a..b = Teilstück, damit ein Aufruf kurz bleibt."""
    scn = _rig_setup()
    rig, mesh, lo, hi = _anim_on("Erwachsen", name)
    span = hi - lo + 1
    off = {"Laying Sleeping": (1.0, -1.9, 1.2)}.get(name, (1.1, -2.5, 0.15))
    for k in range(a, min(b, frames) + 1):
        scn.frame_set(lo + (k - 1) % span)
        c = _bone_w(rig, "Spine")
        if name != "Walking":
            c = Vector((c.x, c.y, c.z))
        camera((c.x + off[0], c.y + off[1], c.z + off[2]), tuple(c), 50).data.dof.use_dof = False
        render(f"{R}/rig/video/{name.replace(' ', '_')}_{k:04d}.png", 540, 540, 16)
    _anim_off(rig, "Erwachsen")
    only("Puppe_Erwachsen", "Puppe_Schmal", "Puppe_Kind")
    scn.frame_set(1)


def do_details():
    scn, P = base()
    set_look("warm")
    camera((0, -3.9, 0.92), (0, 0, 0.82), 50).data.dof.use_dof = False
    render(f"{R}/t_vorn.png", 900, 900, 48)
    # Fäustling von oben (Daumen zeigt zur Bildunterkante)
    j = rig_joints(VARIANTS["Erwachsen"])
    camera((j["wrist"] + 0.05, -0.07, j["za"] + 0.42), (j["wrist"] + 0.05, -0.07, j["za"]), 50).data.dof.use_dof = False
    render(f"{R}/detail_hand.png", 900, 900, 48)
    closeup_cam(0.55, 70, 8.0, yaw=-8, pitch=0, res=(900, 900))
    render(f"{R}/detail_hals.png", 900, 900, 48)


def do_lineup():
    """Alle drei Varianten stehend mit hängenden Armen."""
    cleanup()
    scn, P = base()
    only()
    set_look("warm")
    for nm, x in (("Kind", -0.75), ("Erwachsen", 0.0), ("Schmal", 0.75)):
        ob, rig = make_posed(nm)
        apply_pose(rig, pose_stehen(rig))
        ground(ob, rig)
        rig.location.x = x
        w = world_coords(ob)
        j = rig_joints(VARIANTS[nm])
        band = (w[:, 2] > j["za"] - 0.06) & (w[:, 2] < j["za"] + 0.07)
        D = VARIANTS[nm]["D"]
        print(nm, "Hoehe", round(float(w[:, 2].max()), 3), "Schultern/D", round(float(w[band, 0].max() - w[band, 0].min()) / D, 2))
    camera((0, -5.2, 0.88), (0, 0, 0.81), 50).data.dof.use_dof = False
    render(f"{R}/varianten.png", 1800, 900, 48)
    cleanup()
    only("Puppe_Erwachsen", "Puppe_Schmal", "Puppe_Kind")


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
