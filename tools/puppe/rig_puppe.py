"""Schritt 5: Mixamo-Skelett auf die Grund-Puppe (das Original mit FaceUV, Material und Gesichts-Schaltern) + Varianten + Test-Animationen.
- Erwachsen: Skelett aus assets/mixamo/puppe_rigged.fbx, Gewichte vom Mixamo-Mesh aufs Original übertragen (nächste Fläche, baryzentrisch).
  Kopf + Halskugel hängen starr am Kopf-Knochen (Kopf bleibt rund), Ring + Körper behalten die Mixamo-Gewichte.
- Schmal/Kind: gleiche Topologie -> Gewichte 1:1 übernehmen, Knochen an den Varianten-Körper angepasst (kein eigener Mixamo-Upload nötig).
- Animationen (Y Bot, „Without Skin“): Rotationen passen direkt; die Hüft-Bewegung wird auf die kürzeren Beine skaliert.
Läuft nach build_puppe.py + abnahme.py + pose_test.py im selben Namensraum."""
import bpy
import numpy as np
from bpy_extras import anim_utils
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree
from mathutils.interpolate import poly_3d_calc
from mathutils.kdtree import KDTree

MIXAMO = "C:/ProjectTikTok/assets/mixamo/"
RIG_FBX = MIXAMO + "puppe_rigged.fbx"
# Name = Dateiname im Asset-Ordner (Aktion heißt „Mixamo_<Name mit _>“, z. B. Mixamo_Laying_Sleeping)
ANIMS = {n: n + ".fbx" for n in ("Sitting Idle", "Laying Sleeping", "Walking", "Look Over Shoulder", "Sitting Talking",
                                  "Standing W_Briefcase Idle", "Crouched Walking", "Terrified", "Crawling")}
RENAMED = {"Mixamo_Sleeping_Idle": "Mixamo_Laying_Sleeping"}
HIPS, HEAD = "mixamorig:Hips", "mixamorig:Head"
MAX_INFL = 4


def _import(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=False)
    return [o for o in bpy.data.objects if o not in before]


def _remove(obs):
    for o in obs:
        data = o.data
        bpy.data.objects.remove(o)
        if data is not None and data.users == 0:
            (bpy.data.armatures if isinstance(data, bpy.types.Armature) else bpy.data.meshes).remove(data)


def _islands(ob):
    rank, roots = island_ids(ob.data)
    isl = np.array([rank[int(r)] for r in roots])
    z = np.array([v.co.z for v in ob.data.vertices])
    ids = [i for i in np.unique(isl) if i >= 2]
    ball = max(ids, key=lambda i: z[isl == i].max())  # Kugel liegt höher als der Ring
    return isl, ball


def _coords(ob, world=True):
    co = np.zeros(len(ob.data.vertices) * 3, np.float32)
    ob.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    if world:
        M = np.array(ob.matrix_world)
        co = co @ M[:3, :3].T + M[:3, 3]
    return co


def _write_groups(ob, names, W):
    ob.vertex_groups.clear()
    for k, nm in enumerate(names):
        col = W[:, k]
        if not (col > 0).any():
            continue
        g = ob.vertex_groups.new(name=nm)
        for w_val in np.unique(np.round(col[col > 0], 4)):
            idx = np.nonzero(np.abs(np.round(col, 4) - w_val) < 1e-7)[0].tolist()
            g.add(idx, float(w_val), "REPLACE")


def _read_groups(ob, names=None):
    names = names or [g.name for g in ob.vertex_groups]
    pos = {g.index: names.index(g.name) for g in ob.vertex_groups if g.name in names}
    W = np.zeros((len(ob.data.vertices), len(names)))
    for v in ob.data.vertices:
        for ge in v.groups:
            if ge.group in pos:
                W[v.index, pos[ge.group]] = ge.weight
    return names, W


def _clean(W):
    """Höchstens 4 Einflüsse, kleine Reste weg, Summe 1."""
    W = W.copy()
    if W.shape[1] > MAX_INFL:
        cut = -np.sort(-W, axis=1)[:, MAX_INFL - 1:MAX_INFL]
        W[W < cut] = 0
    W[W < 0.01] = 0
    s = W.sum(axis=1, keepdims=True)
    s[s == 0] = 1
    return W / s


def transfer_weights(src, dst):
    sm = src.data
    sm.calc_loop_triangles()
    sco = [Vector(p) for p in _coords(src)]
    tris = [tuple(t.vertices) for t in sm.loop_triangles]
    bvh = BVHTree.FromPolygons(sco, tris)
    names, Ws = _read_groups(src)
    dco = _coords(dst)
    W = np.zeros((len(dco), len(names)))
    far = 0.0
    for i, p in enumerate(dco):
        loc, _n, ti, dist = bvh.find_nearest(Vector(p))
        far = max(far, dist)
        a, b, c = tris[ti]
        wa, wb, wc = poly_3d_calc([sco[a], sco[b], sco[c]], loc)
        W[i] = wa * Ws[a] + wb * Ws[b] + wc * Ws[c]
    isl, ball = _islands(dst)
    rigid = (isl == 1) | (isl == ball)
    h = names.index(HEAD)
    W[rigid] = 0
    W[rigid, h] = 1.0
    W = _clean(W)
    _write_groups(dst, names, W)
    return dict(groups=len(names), max_abstand_mm=round(far * 1000, 1), starr=int(rigid.sum()))


def bind(mesh, rig):
    for m in [m for m in mesh.modifiers if m.type == "ARMATURE"]:
        mesh.modifiers.remove(m)
    # klassisch „Parent, Transform behalten“: die eigene Lage der Puppe bleibt unangetastet, auch wenn das Skelett später entfernt wird
    mesh.parent = rig
    mesh.matrix_parent_inverse = rig.matrix_world.inverted()
    mod = mesh.modifiers.new("Skelett", "ARMATURE")
    mod.object = rig
    mod.use_deform_preserve_volume = False  # Mixamo-Gewichte sind für normales Linear-Skinning gemacht


def _puppe_coll():
    return bpy.data.collections["Puppe"]


def _link_only(ob, coll):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)


def build_rig_adult():
    """Importiert Nicks Mixamo-Rig, überträgt die Gewichte aufs Original und entfernt das Mixamo-Mesh wieder."""
    # alte Skelette lösen: Puppen zurück in ihre Grund-Lage (T-Pose, eigener Ort aus VARIANTS)
    for nm, p in VARIANTS.items():
        m = bpy.data.objects["Puppe_" + nm]
        m.parent = None
        m.matrix_parent_inverse.identity()
        m.location, m.rotation_euler, m.scale = p["loc"], (0, 0, 0), (1, 1, 1)
        for mod in [x for x in m.modifiers if x.type == "ARMATURE"]:
            m.modifiers.remove(mod)
    for nm in ("Rig_Erwachsen", "Rig_Schmal", "Rig_Kind"):
        if nm in bpy.data.objects:
            r = bpy.data.objects[nm]
            if r.animation_data and r.animation_data.action:
                r.animation_data.action = None
            _remove([r])
    for a in [a for a in bpy.data.actions if "__Rig_" in a.name and a.users == 0]:
        bpy.data.actions.remove(a)
    obs = _import(RIG_FBX)
    rig = next(o for o in obs if o.type == "ARMATURE")
    src = next(o for o in obs if o.type == "MESH")
    rig.name = rig.data.name = "Rig_Erwachsen"
    if rig.animation_data and rig.animation_data.action:  # leere Ruhe-Aktion aus der Mixamo-Datei nicht mitschleppen
        a = rig.animation_data.action
        rig.animation_data.action = None
        bpy.data.actions.remove(a)
    _link_only(rig, _puppe_coll())
    rig.show_in_front = True
    dst = bpy.data.objects["Puppe_Erwachsen"]
    rep = transfer_weights(src, dst)
    _remove([src])
    bind(dst, rig)
    return rig, rep


def _disp_field(adult, var):
    a = _coords(adult, world=False)
    v = _coords(var, world=False)
    kd = KDTree(len(a))
    for i, p in enumerate(a):
        kd.insert(p, i)
    kd.balance()

    def f(p):
        hits = kd.find_n(p, 16)
        w = np.array([1.0 / (d + 1e-3) ** 2 for _c, _i, d in hits])
        dv = np.array([v[i] - a[i] for _c, i, _d in hits])
        return Vector((w[:, None] * dv).sum(0) / w.sum())

    return f


def build_rig_variant(nm, base_rig):
    adult = bpy.data.objects["Puppe_Erwachsen"]
    var = bpy.data.objects["Puppe_" + nm]
    assert len(var.data.vertices) == len(adult.data.vertices), "Varianten brauchen dieselbe Topologie"
    f = _disp_field(adult, var)
    rig = base_rig.copy()
    rig.data = base_rig.data.copy()
    rig.name = rig.data.name = "Rig_" + nm
    rig.animation_data_clear()
    _puppe_coll().objects.link(rig)
    base_mw = base_rig.matrix_world.copy()
    rig.location = base_rig.location + Vector(var.location) - Vector(adult.location)
    bpy.context.view_layer.update()
    inv = rig.matrix_world.inverted()
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    rig.select_set(True)
    vl.objects.active = rig
    # Ziel-Positionen vorher aus dem Erwachsenen-Skelett berechnen: verbundene Knochen teilen sich Punkte,
    # sonst würde ein Kind-Kopf doppelt verschoben (Eltern-Spitze zieht ihn schon mit)
    target = {}
    for b in base_rig.data.bones:
        for attr, local in (("head", b.head_local), ("tail", b.tail_local)):
            pw = base_mw @ local  # Position im Erwachsenen (Welt = lokal, Puppe steht im Ursprung)
            target[b.name, attr] = inv @ (pw + f(pw) + Vector(var.location))
    bpy.ops.object.mode_set(mode="EDIT")
    for eb in rig.data.edit_bones:
        eb.head = target[eb.name, "head"]
        eb.tail = target[eb.name, "tail"]
    bpy.ops.object.mode_set(mode="OBJECT")
    names, W = _read_groups(adult)
    _write_groups(var, names, W)
    bind(var, rig)
    return rig


def build_rigs():
    rig, rep = build_rig_adult()
    print("Gewichte Erwachsen:", rep)
    for nm in ("Schmal", "Kind"):
        build_rig_variant(nm, rig)
    return rig


# ------------------------------------------------------------------ Animationen
def action_key(name):
    return "Mixamo_" + name.replace(" ", "_")


def load_actions(names=None, reload=False):
    """Lädt Mixamo-Animationen als Basis-Aktionen (Fake-User) und vergleicht die Ruhe-Haltung mit unserem Skelett.
    Ohne reload werden schon vorhandene Aktionen nicht neu geladen; alte Namen werden umbenannt."""
    for old, new in RENAMED.items():
        a = bpy.data.actions.get(old)
        if a and new not in bpy.data.actions:
            a.name = new
    ours = bpy.data.objects["Rig_Erwachsen"]
    report = {}
    for name in names or ANIMS:
        fn = ANIMS[name]
        key = action_key(name)
        old = bpy.data.actions.get(key)
        if old and not reload:
            continue
        if old:
            bpy.data.actions.remove(old)
        obs = _import(MIXAMO + fn)
        arm = next(o for o in obs if o.type == "ARMATURE")
        act = arm.animation_data.action
        act.name = key
        act.use_fake_user = True
        act["ybot_hips_m"] = float((arm.matrix_world @ arm.data.bones[HIPS].head_local).z)
        act["ybot_scale"] = float(arm.scale.x)
        # Ruhe-Ausrichtung jedes Y-Bot-Knochens (Welt) merken: Schlüsselbeine/Füße stehen ≈ 20° anders als in unserem Rig
        act["rest_q"] = {b.name: list(arm.matrix_world.to_quaternion() @ b.matrix_local.to_quaternion()) for b in arm.data.bones}
        worst = 0.0
        for b in ours.data.bones:
            yb = arm.data.bones.get(b.name)
            if yb:
                q = (ours.matrix_world.to_quaternion() @ b.matrix_local.to_quaternion()).rotation_difference(
                    arm.matrix_world.to_quaternion() @ yb.matrix_local.to_quaternion())
                ang = math.degrees(q.angle)
                worst = max(worst, min(ang, 360 - ang))
        slim_action(act, {b.name for b in ours.data.bones})
        report[name] = dict(bilder=tuple(int(x) for x in act.frame_range), ruhe_abweichung_grad=round(worst, 1))
        arm.animation_data.action = None
        _remove(obs)
    return report


def slim_action(act, bones):
    """Nur behalten, was unser Rig nutzt: Drehungen der 25 Knochen + Hüft-Weg (Y Bot hat 65 Knochen, Ort/Größe für alle)."""
    bag = anim_utils.action_get_channelbag_for_slot(act, act.slots[0])
    drop = []
    for fc in bag.fcurves:
        nm = fc.data_path.split('"')[1] if '"' in fc.data_path else ""
        prop = fc.data_path.rsplit(".", 1)[-1]
        if nm not in bones or prop == "scale" or (prop == "location" and nm != HIPS):
            drop.append(fc)
    for fc in drop:
        bag.fcurves.remove(fc)
    return len(drop)


ARM_SPREAD = 5.0  # Grad: unsere Puppe ist klobiger als der Y Bot -> Oberarme etwas abspreizen, damit die Hände nicht in die Hüfte tauchen


def spread_arms(rig, bag, deg):
    """Dreht beide Oberarme in jedem Schlüsselbild um `deg` vom Körper weg (um die Blick-Achse, im Raum des Eltern-Knochens)."""
    for side in ("Left", "Right"):
        nm = f"mixamorig:{side}Arm"
        b = rig.data.bones[nm]
        B = rig.matrix_world.to_quaternion() @ b.matrix_local.to_quaternion()
        d = (rig.matrix_world @ b.tail_local) - (rig.matrix_world @ b.head_local)
        sign = 1.0 if (Quaternion((0, 1, 0), math.radians(deg)) @ d).z > d.z else -1.0
        off = B.inverted() @ Quaternion((0, 1, 0), math.radians(sign * deg)) @ B
        path = f'pose.bones["{nm}"].rotation_quaternion'
        ch = sorted([fc for fc in bag.fcurves if fc.data_path == path], key=lambda fc: fc.array_index)
        if len(ch) != 4:
            continue
        for i in range(len(ch[0].keyframe_points)):
            q = Quaternion([fc.keyframe_points[i].co.y for fc in ch])
            q2 = off @ q
            for k, fc in enumerate(ch):
                kp = fc.keyframe_points[i]
                dv = q2[k] - kp.co.y
                kp.co.y += dv
                kp.handle_left.y += dv
                kp.handle_right.y += dv
        for fc in ch:
            fc.update()


def hips_height(rig):
    return float((rig.matrix_world @ rig.data.bones[HIPS].head_local).z - rig.matrix_world.translation.z)


def _channels(bag, nm, prop, n):
    ch = sorted([fc for fc in bag.fcurves if fc.data_path == f'pose.bones["{nm}"].{prop}'], key=lambda fc: fc.array_index)
    if len(ch) != n or len({len(fc.keyframe_points) for fc in ch}) != 1:
        return None
    return ch


def _set_key(ch, i, values):
    for k, fc in enumerate(ch):
        kp = fc.keyframe_points[i]
        dv = values[k] - kp.co.y
        kp.co.y += dv
        kp.handle_left.y += dv
        kp.handle_right.y += dv


def retarget(rig, bag, base, fac):
    """Y-Bot-Bewegung auf unsere Knochen umrechnen: q' = C⁻¹·q·C mit C = Ruhe(Y Bot)⁻¹·Ruhe(unser Rig).
    So zeigt jeder Knochen in dieselbe Welt-Richtung wie beim Y Bot, auch wo die Ruhe-Haltungen abweichen. Hüft-Weg × fac."""
    rest = base.get("rest_q")
    mq = rig.matrix_world.to_quaternion()
    for b in rig.data.bones:
        C = Quaternion()
        if rest and b.name in rest:
            C = Quaternion(rest[b.name]).inverted() @ (mq @ b.matrix_local.to_quaternion())
        Ci = C.inverted()
        ch = _channels(bag, b.name, "rotation_quaternion", 4)
        if ch and rest:
            for i in range(len(ch[0].keyframe_points)):
                _set_key(ch, i, Ci @ Quaternion([fc.keyframe_points[i].co.y for fc in ch]) @ C)
            for fc in ch:
                fc.update()
        if b.name == HIPS:
            ch = _channels(bag, b.name, "location", 3)
            if ch:
                for i in range(len(ch[0].keyframe_points)):
                    v = Vector([fc.keyframe_points[i].co.y for fc in ch])
                    _set_key(ch, i, (Ci @ v) * fac)
                for fc in ch:
                    fc.update()


def apply_action(rig, name):
    """Hängt eine Kopie der Basis-Aktion an das Skelett: auf unsere Knochen umgerechnet, Hüft-Weg auf die Beinlänge skaliert,
    Oberarme leicht abgespreizt. Gibt es eine korrigierte Fassung (Fix_…, Hände aus Körper/Kopf geschoben), wird die genommen."""
    ensure_actions([action_key(name), fix_key(name, rig)])
    base = bpy.data.actions[action_key(name)]
    for a in [a for a in bpy.data.actions if a.name.startswith(base.name + "__" + rig.name)]:
        bpy.data.actions.remove(a)
    fixed = bpy.data.actions.get(fix_key(name, rig))
    act = base.copy()
    act.name = base.name + "__" + rig.name
    act.use_fake_user = False
    bag = anim_utils.action_get_channelbag_for_slot(act, act.slots[0])
    fac = base["ybot_scale"] / rig.scale.x * hips_height(rig) / base["ybot_hips_m"]
    retarget(rig, bag, base, fac)
    spread_arms(rig, bag, ARM_SPREAD)
    if fixed:
        _overlay(act, fixed)
    ad = rig.animation_data_create()
    ad.action = act
    if ad.action_slot is None:
        ad.action_slot = act.slots[0]
    lo, hi = act.frame_range
    return int(lo), int(hi)


def fix_key(name, rig):
    return "Fix_" + action_key(name) + "__" + rig.name


def _hand_push(rig, mesh, variant):
    """Pro Hand: Welt-Vektor, um den die Hand verschoben werden muss, damit sie nicht in Rumpf/Beinen/Kopf steckt."""
    data = _pen_data(mesh, variant)
    co, bvh = _pen_bvh(mesh, data)
    out = {}
    for side, idx in (("Left", data["hand_l"]), ("Right", data["hand_r"])):
        best = None
        for i in idx:
            p = Vector(co[i])
            loc, nrm, _f, d = bvh.find_nearest(p)
            if loc is not None and (p - loc).dot(nrm) < 0:
                v = (loc - p) + nrm * 0.008
                if best is None or v.length > best.length:
                    best = v
        out[side] = best
    return out


def make_fixed(rig, mesh, variant, name, rounds=3, sigma=3.0):
    """Korrigiert eine Animation für diese Puppe: Hände, die in Körper oder Kopf tauchen (großer Kopf, klobiger Körper),
    werden per IK nach außen geschoben. Die Korrektur wird über die Zeit weich ein- und ausgeblendet. Ergebnis: Fix_…-Aktion."""
    scn = bpy.context.scene
    old = bpy.data.actions.get(fix_key(name, rig))
    if old:
        bpy.data.actions.remove(old)
    lo, hi = apply_action(rig, name)
    act = rig.animation_data.action
    n = hi - lo + 1
    for r in range(rounds):
        push = {s: np.zeros((n, 3)) for s in ("Left", "Right")}
        for f in range(lo, hi + 1):
            scn.frame_set(f)
            for s, v in _hand_push(rig, mesh, variant).items():
                if v is not None:
                    push[s][f - lo] = tuple(v)
        hits = sum(int(np.any(push[s] != 0, axis=1).sum()) for s in push)
        if hits == 0:
            break
        # weich machen: erst Maximum über ±3 Bilder halten, dann Gauß – kein Springen der Hand
        k = np.exp(-0.5 * (np.arange(-9, 10) / sigma) ** 2)
        k /= k.sum()
        for s in push:
            mag = np.linalg.norm(push[s], axis=1)
            held = np.array([push[s][max(0, i - 3):i + 4][np.argmax(mag[max(0, i - 3):i + 4])] for i in range(n)])
            push[s] = np.stack([np.convolve(np.pad(held[:, c], 9, mode="edge"), k, mode="valid") for c in range(3)], axis=1)
        for f in range(lo, hi + 1):
            todo = [s for s in push if np.linalg.norm(push[s][f - lo]) > 0.0005]
            if not todo:
                continue
            scn.frame_set(f)
            for s in todo:
                S = _head_w(rig, s + "Arm")
                E = _head_w(rig, s + "ForeArm")
                W = _head_w(rig, s + "Hand")
                hd = (rig.matrix_world.to_3x3() @ rig.pose.bones[f"mixamorig:{s}Hand"].matrix.to_3x3() @ Vector((0, 1, 0)))
                axis = (W - S).normalized()
                pole = (E - S) - axis * (E - S).dot(axis)
                place_arm(rig, s, W + Vector(push[s][f - lo]), hd, pole if pole.length > 1e-4 else Vector((0, 0.3, -1)))
                for nm in (f"mixamorig:{s}Arm", f"mixamorig:{s}ForeArm", f"mixamorig:{s}Hand"):
                    rig.pose.bones[nm].keyframe_insert("rotation_quaternion", frame=f)
        print(f"  Runde {r + 1}: {hits} Hand-Bilder korrigiert")
    left = 0
    for f in range(lo, hi + 1, 2):
        scn.frame_set(f)
        left += int(penetration(mesh, variant)["hand_innen"] > 0)
    act.name = fix_key(name, rig)
    act.use_fake_user = True
    act["fix_ok"] = left == 0
    slim_fix(act)
    clear_action(rig)
    return left


ARM_BONES = {f"mixamorig:{s}{n}" for s in ("Left", "Right") for n in ("Arm", "ForeArm", "Hand")}


def slim_fix(act):
    """Eine Korrektur ändert nur die Arme: nur deren Drehungen speichern (der Rest kommt beim Anhängen aus der Basis-Aktion)."""
    bag = anim_utils.action_get_channelbag_for_slot(act, act.slots[0])
    for fc in [fc for fc in bag.fcurves if not (fc.data_path.endswith("rotation_quaternion") and fc.data_path.split('"')[1] in ARM_BONES)]:
        bag.fcurves.remove(fc)


def _overlay(act, fixed):
    """Arm-Kurven der Korrektur in die frisch umgerechnete Aktion übernehmen."""
    dst = anim_utils.action_get_channelbag_for_slot(act, act.slots[0])
    src = anim_utils.action_get_channelbag_for_slot(fixed, fixed.slots[0])
    for fs in src.fcurves:
        fd = next((f for f in dst.fcurves if f.data_path == fs.data_path and f.array_index == fs.array_index), None)
        if fd is None:
            fd = dst.fcurves.new(fs.data_path, index=fs.array_index)
        n = len(fs.keyframe_points)
        if len(fd.keyframe_points) != n:
            fd.keyframe_points.clear()
            fd.keyframe_points.add(n)
        for attr in ("co", "handle_left", "handle_right"):
            buf = np.zeros(n * 2, np.float32)
            fs.keyframe_points.foreach_get(attr, buf)
            fd.keyframe_points.foreach_set(attr, buf)
        fd.update()


# Animationen liegen in einer eigenen Datei (die Figuren-Bibliothek bleibt klein; Szenen hängen sie bei Bedarf an)
ANIM_BLEND = CHAR_DIR + "/animations.blend"
ANIM_PREFIX = ("Mixamo_", "Fix_", "Pose_")


def ensure_actions(names):
    """Holt fehlende Aktionen aus animations.blend in die aktuelle Datei."""
    import os
    want = [n for n in names if n not in bpy.data.actions]
    if not want or not os.path.exists(ANIM_BLEND):
        return
    with bpy.data.libraries.load(ANIM_BLEND, link=False) as (src, dst):
        dst.actions = [n for n in src.actions if n in want]


def export_animations(remove=True):
    """Schreibt alle Basis-, Korrektur- und Posen-Aktionen nach animations.blend und nimmt sie aus der aktuellen Datei."""
    acts = {a for a in bpy.data.actions if a.name.startswith(ANIM_PREFIX)}
    bpy.data.libraries.write(ANIM_BLEND, acts, fake_user=True, compress=True)
    if remove:
        for o in bpy.data.objects:
            if o.animation_data and o.animation_data.action in acts:
                o.animation_data.action = None
        for a in acts:
            bpy.data.actions.remove(a)
    return len(acts)


def clear_action(rig):
    ad = rig.animation_data
    if ad and ad.action:
        a = ad.action
        ad.action = None
        if a.users == 0 and not a.use_fake_user:
            bpy.data.actions.remove(a)
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.scale = (1, 1, 1)


def hold_pose(rig, name, frame):
    """Statische Pose aus einem Animations-Bild (z. B. für Gesichter-Board und Sprechtest), danach ohne Aktion."""
    apply_action(rig, name)
    bpy.context.scene.frame_set(frame)
    vals = {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy(), pb.rotation_euler.copy(), pb.scale.copy()) for pb in rig.pose.bones}
    a = rig.animation_data.action
    rig.animation_data.action = None
    bpy.data.actions.remove(a)
    for pb in rig.pose.bones:
        pb.location, pb.rotation_quaternion, pb.rotation_euler, pb.scale = vals[pb.name]
    bpy.context.view_layer.update()


def pose_arms_down(rig, deg=72.0, bend=12.0):
    """Ruhige Stand-Pose ohne Animation: Oberarme hängen, Ellbogen leicht gebeugt, Kopf gerade (für Gesichter-Board + Sprechtest)."""
    clear_action(rig)
    for side in ("Left", "Right"):
        for nm, a in ((f"mixamorig:{side}Arm", deg), (f"mixamorig:{side}ForeArm", bend)):
            b = rig.data.bones[nm]
            B = rig.matrix_world.to_quaternion() @ b.matrix_local.to_quaternion()
            d = (rig.matrix_world @ b.tail_local) - (rig.matrix_world @ b.head_local)
            sign = -1.0 if (Quaternion((0, 1, 0), math.radians(a)) @ d).z > d.z else 1.0
            pb = rig.pose.bones[nm]
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = B.inverted() @ Quaternion((0, 1, 0), math.radians(sign * a)) @ B
    bpy.context.view_layer.update()


# ------------------------------------------------------------------ eigene Posen (Sitzen_Schlafen, Kind mit hängenden Beinen)
KIND_SEAT = 0.40  # Sitzhöhe für das Kind mit hängenden Beinen


def _mw3(rig):
    return rig.matrix_world.to_3x3()


def _rotate_bone_world(rig, nm, R):
    """Dreht einen Pose-Knochen um seinen eigenen Kopf mit einer Welt-Rotation (3×3)."""
    pb = rig.pose.bones[nm]
    W = _mw3(rig)
    Rarm = W.inverted() @ R @ W
    m = pb.matrix.copy()
    pb.matrix = Matrix.Translation(m.translation) @ (Rarm @ m.to_3x3()).to_4x4()
    bpy.context.view_layer.update()


def _aim_bone(rig, nm, direction):
    """Richtet einen Knochen auf kürzestem Weg auf eine Welt-Richtung aus."""
    pb = rig.pose.bones[nm]
    cur = (_mw3(rig) @ pb.matrix.to_3x3() @ Vector((0, 1, 0))).normalized()
    _rotate_bone_world(rig, nm, cur.rotation_difference(Vector(direction).normalized()).to_matrix())


def _turn(rig, nm, axis, deg):
    _rotate_bone_world(rig, nm, Matrix.Rotation(math.radians(deg), 3, axis))


def _head_w(rig, nm):
    return rig.matrix_world @ rig.pose.bones["mixamorig:" + nm].head


def _shift_hips(rig, dw):
    """Verschiebt die ganze Figur über die Hüfte (Welt-Vektor), bleibt in der Aktion gespeichert."""
    pb = rig.pose.bones[HIPS]
    m = pb.matrix.copy()
    pb.matrix = Matrix.Translation(m.translation + _mw3(rig).inverted() @ Vector(dw)) @ m.to_3x3().to_4x4()
    bpy.context.view_layer.update()


def place_arm(rig, side, wrist, hand_dir, pole):
    """Zwei-Knochen-IK: Handgelenk an `wrist`, Ellbogen Richtung `pole`, Hand zeigt in `hand_dir` (alles Welt)."""
    arm, fore, hand = (f"mixamorig:{side}{n}" for n in ("Arm", "ForeArm", "Hand"))
    S = _head_w(rig, side + "Arm")
    a, b = rig.data.bones[arm].length, rig.data.bones[fore].length
    d = Vector(wrist) - S
    dist = min(d.length, (a + b) * 0.995)
    dn = d.normalized()
    ca = max(-1.0, min(1.0, (a * a + dist * dist - b * b) / (2 * a * dist)))
    p = Vector(pole) - dn * Vector(pole).dot(dn)
    p.normalize()
    E = S + dn * (a * ca) + p * (a * math.sqrt(1 - ca * ca))
    _aim_bone(rig, arm, E - S)
    _aim_bone(rig, fore, S + dn * dist - E)
    _aim_bone(rig, hand, hand_dir)


def _snapshot(rig):
    return {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy()) for pb in rig.pose.bones}


def _restore(rig, snap):
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.location, pb.rotation_quaternion = snap[pb.name]
    bpy.context.view_layer.update()


def _bake_frame(rig, name, frame):
    """Pose aus einem Bild einer (skalierten) Mixamo-Aktion übernehmen, ohne Aktion weiterarbeiten."""
    apply_action(rig, name)
    bpy.context.scene.frame_set(frame)
    snap = _snapshot(rig)
    clear_action(rig)
    _restore(rig, snap)


def _new_action(rig, name):
    old = bpy.data.actions.get(name)
    if old:
        if rig.animation_data and rig.animation_data.action == old:
            rig.animation_data.action = None
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    ad = rig.animation_data_create()
    ad.action = act
    return act


def _key_all(rig, frame):
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.keyframe_insert("location", frame=frame)
        pb.keyframe_insert("rotation_quaternion", frame=frame)


def _mesh_min_z(mesh, mask=None):
    w = world_coords(mesh)
    return float((w[mask] if mask is not None else w)[:, 2].min())


def _butt_bottom(rig, mesh):
    hp = _head_w(rig, "Hips")
    w = world_coords(mesh)
    under = (np.hypot(w[:, 0] - hp.x, w[:, 1] - hp.y) < 0.13) & (w[:, 2] < hp.z)
    return float(w[under, 2].min())


def _hang_legs(rig):
    """Oberschenkel fast waagerecht, Unterschenkel hängen senkrecht, Füße locker nach unten."""
    for side in ("Left", "Right"):
        hip = _head_w(rig, side + "UpLeg")
        out = 1.0 if hip.x > rig.matrix_world.translation.x else -1.0
        _aim_bone(rig, f"mixamorig:{side}UpLeg", Vector((out * 0.06, -1.0, -0.10)))
        _aim_bone(rig, f"mixamorig:{side}Leg", Vector((out * 0.02, -0.12, -1.0)))
        _aim_bone(rig, f"mixamorig:{side}Foot", Vector((0.0, -0.55, -0.83)))


def build_kind_haengend():
    """Kind sitzend mit hängenden Beinen: Sitting Idle (Oberkörper lebt weiter), Beine fest hängend, Sitzfläche auf 0,40 m.
    Ergebnis: Aktion `Pose_Kind_Sitzen_Haengend` (Fake-User), Skelett bleibt dabei im Ursprung seiner Variante."""
    rig, mesh = bpy.data.objects["Rig_Kind"], bpy.data.objects["Puppe_Kind"]
    scn = bpy.context.scene
    lo, hi = apply_action(rig, "Sitting Idle")
    act = rig.animation_data.action
    scn.frame_set(lo)
    legs = [f"mixamorig:{s}{n}" for s in ("Left", "Right") for n in ("UpLeg", "Leg", "Foot", "ToeBase")]
    _hang_legs(rig)
    leg_q = {nm: rig.pose.bones[nm].rotation_quaternion.copy() for nm in legs}
    dz = KIND_SEAT - _butt_bottom(rig, mesh)
    # Höhen-Ausgleich in Hüft-Koordinaten der Aktion umrechnen
    b = rig.data.bones[HIPS]
    d_loc = b.matrix_local.to_3x3().inverted() @ (_mw3(rig).inverted() @ Vector((0, 0, dz)))
    bag = anim_utils.action_get_channelbag_for_slot(act, act.slots[0])
    for fc in list(bag.fcurves):
        if any(fc.data_path == f'pose.bones["{nm}"].rotation_quaternion' for nm in legs):
            bag.fcurves.remove(fc)
        elif fc.data_path == f'pose.bones["{HIPS}"].location':
            for kp in fc.keyframe_points:
                kp.co.y += d_loc[fc.array_index]
                kp.handle_left.y += d_loc[fc.array_index]
                kp.handle_right.y += d_loc[fc.array_index]
            fc.update()
    for nm in legs:
        pb = rig.pose.bones[nm]
        pb.rotation_quaternion = leg_q[nm]
        pb.keyframe_insert("rotation_quaternion", frame=lo)
    old = bpy.data.actions.get("Pose_Kind_Sitzen_Haengend")
    if old and old != act:
        bpy.data.actions.remove(old)
    act.name = "Pose_Kind_Sitzen_Haengend"
    act.use_fake_user = True
    scn.frame_set(lo)
    return dict(bilder=(lo, hi), sitz=round(_butt_bottom(rig, mesh), 3), fuss_unten=round(_mesh_min_z(mesh), 3))


def build_sitzen_schlafen(variant, base_frame=1, breath=120):
    """Eingeschlafen im Sitzen: Kopf nach vorn + zur Seite gesackt, Rücken leicht rund, Hände im Schoß, ruhiges Atmen (Schleife).
    Kind: auf der Variante mit hängenden Beinen. Ergebnis: Aktion `Pose_Sitzen_Schlafen_<Variante>` (Fake-User).
    Gesicht `ausdruck = 1` (augen-zu) setzt apply_sitzen_schlafen()."""
    rig, mesh = bpy.data.objects["Rig_" + variant], bpy.data.objects["Puppe_" + variant]
    p = VARIANTS[variant]
    scn = bpy.context.scene
    if variant == "Kind":
        clear_action(rig)
        ensure_actions(["Pose_Kind_Sitzen_Haengend"])
        ad = rig.animation_data_create()
        ad.action = bpy.data.actions["Pose_Kind_Sitzen_Haengend"]
        if ad.action_slot is None:
            ad.action_slot = ad.action.slots[0]
        scn.frame_set(base_frame)
        snap = _snapshot(rig)
        ad.action = None
        _restore(rig, snap)
    else:
        _bake_frame(rig, "Sitting Idle", base_frame)
    X, Y = Vector((1, 0, 0)), Vector((0, 1, 0))
    # zusammensacken: Rücken etwas rund, Kopf nach vorn und zur Seite
    _turn(rig, "mixamorig:Spine1", X, 5)
    _turn(rig, "mixamorig:Spine2", X, 5)
    _turn(rig, "mixamorig:Neck", X, 12)
    _turn(rig, "mixamorig:Head", X, 14)
    _turn(rig, "mixamorig:Neck", Y, -7)
    _turn(rig, "mixamorig:Head", Y, -9)
    # Hände im Schoß: auf den Oberschenkeln nahe der Mitte, Finger zeigen nach innen-vorn
    cx = rig.matrix_world.translation.x
    hand_len = rig.data.bones["mixamorig:LeftHand"].length
    w = world_coords(mesh)
    legs_m = _part_masks(mesh, variant)["legs"]  # nur Beine: sonst findet die Suche über dem Schoß den Bauch/die Brust
    for side in ("Left", "Right"):
        hip, knee = _head_w(rig, side + "UpLeg"), _head_w(rig, side + "Leg")
        out = 1.0 if hip.x > cx else -1.0
        q = hip.lerp(knee, 0.60)  # weit genug vorn, sonst liegt die Hand im Bauch
        q.x = cx + (q.x - cx) * 0.5
        hd = Vector((-out * 0.80, -0.55, -0.10)).normalized()  # Hand liegt quer über dem Oberschenkel, Finger nach innen
        lift, fwd = 0.030 * p["th"], 0.0
        for _ in range(10):
            near = legs_m & (np.hypot(w[:, 0] - q.x, w[:, 1] - (q.y - fwd)) < 0.035)
            top = float(w[near, 2].max()) if near.any() else q.z + 0.05
            wrist = Vector((q.x, q.y - fwd, top + lift)) - hd * (hand_len * 0.45)
            place_arm(rig, side, wrist, hd, (out * 0.75, 0.35, -0.55))
            if penetration(mesh, variant)["hand_innen"] == 0:
                break
            lift += 0.005
            fwd += 0.012
    if variant != "Kind":  # Füße auf den Boden (Kind sitzt mit hängenden Beinen auf 0,40 m)
        _shift_hips(rig, (0, 0, -_mesh_min_z(mesh)))
    base = _snapshot(rig)
    act = _new_action(rig, "Pose_Sitzen_Schlafen_" + variant)
    _key_all(rig, 1)
    _key_all(rig, 1 + breath)
    # einatmen: Brust hebt sich minimal, Schultern gehen leicht mit
    _turn(rig, "mixamorig:Spine2", X, -1.4)
    _turn(rig, "mixamorig:Spine1", X, -0.6)
    for side, s in (("Left", 1), ("Right", -1)):
        _turn(rig, f"mixamorig:{side}Shoulder", Y, s * 0.8)
    _key_all(rig, 1 + breath // 2)
    _restore(rig, base)
    bag = anim_utils.action_get_channelbag_for_slot(act, act.slots[0])
    for fc in bag.fcurves:
        fc.modifiers.new("CYCLES")
    scn.frame_set(1)
    return act


def apply_sitzen_schlafen(variant):
    rig, mesh = bpy.data.objects["Rig_" + variant], bpy.data.objects["Puppe_" + variant]
    clear_action(rig)
    ensure_actions(["Pose_Sitzen_Schlafen_" + variant])
    ad = rig.animation_data_create()
    ad.action = bpy.data.actions["Pose_Sitzen_Schlafen_" + variant]
    if ad.action_slot is None:
        ad.action_slot = ad.action.slots[0]
    face(mesh, ausdruck=1)
    return rig, mesh


# ------------------------------------------------------------------ Prüfungen
def _part_masks(mesh, variant):
    """Teile aus der Ruhe-Haltung: Hände, Arme, Rest (Rumpf/Beine), Kopf."""
    p = VARIANTS[variant]
    j = rig_joints(p)
    co = _coords(mesh, world=False)
    isl, ball = _islands(mesh)
    ax = np.abs(co[:, 0])
    body = isl == 0
    arm = body & (ax > j["jx"] + 0.02) & (co[:, 2] > j["za"] - 0.12 * j["sz"])
    hand = body & (ax > j["wrist"])
    shoulder = (ax > j["jx"] - 0.01) & (co[:, 2] > j["za"] - 0.12 * j["sz"])
    legs = body & ~arm & (co[:, 2] < j["hip"] - 0.02)
    return dict(hand=hand, arm=arm, rest=body & ~arm & ~shoulder, head=isl == 1, legs=legs)


_PEN = {}


def _pen_data(mesh, variant):
    """Einmal pro Puppe: Flächen von Rumpf/Beinen/Kopf (Prüf-Körper) und die Hand-Punkte (jeder 2.)."""
    key = mesh.name
    if key not in _PEN:
        m = _part_masks(mesh, variant)
        keep = m["rest"] | m["head"]  # Rumpf, Beine und Kopf (Hand vors Gesicht zählt auch)
        polys = [tuple(pl.vertices) for pl in mesh.data.polygons if all(keep[i] for i in pl.vertices)]
        co = _coords(mesh, world=False)
        cx = 0.0  # Ruhe-Koordinaten sind lokal: links = +X
        hand = np.nonzero(m["hand"])[0]
        _PEN[key] = dict(polys=polys, hand=hand[::2].tolist(), hand_l=hand[co[hand, 0] > cx][::2].tolist(),
                         hand_r=hand[co[hand, 0] <= cx][::2].tolist(), head=np.nonzero(m["head"])[0])
    return _PEN[key]


def _pen_bvh(mesh, data):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    M = np.array(mesh.matrix_world)
    co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    return co, BVHTree.FromPolygons(co.tolist(), data["polys"])


def penetration(mesh, variant):
    """Wie tief stecken die Hände in Rumpf, Beinen oder Kopf? (mm, 0 = keine Durchdringung; jeder 2. Hand-Punkt)."""
    data = _pen_data(mesh, variant)
    co, bvh = _pen_bvh(mesh, data)
    deep = 0.0
    n_in = 0
    for i in data["hand"]:
        p = Vector(co[i])
        loc, nrm, _idx, d = bvh.find_nearest(p)
        if loc is not None and (p - loc).dot(nrm) < 0:
            n_in += 1
            deep = max(deep, d)
    hc = co[data["head"]]
    r = np.linalg.norm(hc - hc.mean(0), axis=1)
    return dict(hand_innen=n_in, tiefe_mm=round(deep * 1000, 1), kopf_rund_mm=round(float(r.max() - r.min()) * 1000 - 1.0, 1))
