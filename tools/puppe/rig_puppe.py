"""Schritt 5: Mixamo-Skelett auf die Grund-Puppe (das Original mit FaceUV, Material und Gesichts-Schaltern) + Varianten + Test-Animationen.
- Erwachsen: Skelett aus assets/mixamo/puppe_rigged.fbx, Gewichte vom Mixamo-Mesh aufs Original übertragen (nächste Fläche, baryzentrisch).
  Kopf + Halskugel hängen starr am Kopf-Knochen (Kopf bleibt rund), Ring + Körper behalten die Mixamo-Gewichte.
- Schmal/Kind: gleiche Topologie -> Gewichte 1:1 übernehmen, Knochen an den Varianten-Körper angepasst (kein eigener Mixamo-Upload nötig).
- Animationen (Y Bot, „Without Skin“): Rotationen passen direkt; die Hüft-Bewegung wird auf die kürzeren Beine skaliert.
Läuft nach build_puppe.py + abnahme.py + pose_test.py im selben Namensraum."""
import bpy
import numpy as np
from bpy_extras import anim_utils
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree
from mathutils.interpolate import poly_3d_calc
from mathutils.kdtree import KDTree

MIXAMO = "C:/ProjectTikTok/assets/mixamo/"
RIG_FBX = MIXAMO + "puppe_rigged.fbx"
# „Sleeping Idle“ liegt als „Laying Sleeping“ im Asset-Ordner
ANIMS = {"Sitting Idle": "Sitting Idle.fbx", "Sleeping Idle": "Laying Sleeping.fbx", "Walking": "Walking.fbx",
         "Look Over Shoulder": "Look Over Shoulder.fbx"}
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
def load_actions():
    """Lädt die 4 Test-Animationen einmal als Basis-Aktionen (Fake-User) und vergleicht die Ruhe-Haltung mit unserem Skelett."""
    ours = bpy.data.objects["Rig_Erwachsen"]
    report = {}
    for name, fn in ANIMS.items():
        key = "Mixamo_" + name.replace(" ", "_")
        old = bpy.data.actions.get(key)
        if old:
            bpy.data.actions.remove(old)
        obs = _import(MIXAMO + fn)
        arm = next(o for o in obs if o.type == "ARMATURE")
        act = arm.animation_data.action
        act.name = key
        act.use_fake_user = True
        act["ybot_hips_m"] = float((arm.matrix_world @ arm.data.bones[HIPS].head_local).z)
        act["ybot_scale"] = float(arm.scale.x)
        worst = 0.0
        for b in ours.data.bones:
            yb = arm.data.bones.get(b.name)
            if yb:
                q = (ours.matrix_world.to_quaternion() @ b.matrix_local.to_quaternion()).rotation_difference(
                    arm.matrix_world.to_quaternion() @ yb.matrix_local.to_quaternion())
                worst = max(worst, math.degrees(q.angle))
        report[name] = dict(bilder=tuple(int(x) for x in act.frame_range), ruhe_abweichung_grad=round(worst, 1))
        arm.animation_data.action = None
        _remove(obs)
    return report


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


def apply_action(rig, name):
    """Hängt eine Kopie der Basis-Aktion an das Skelett; Hüft-Weg wird auf die Beinlänge dieser Puppe skaliert."""
    base = bpy.data.actions["Mixamo_" + name.replace(" ", "_")]
    for a in [a for a in bpy.data.actions if a.name.startswith(base.name + "__" + rig.name)]:
        bpy.data.actions.remove(a)
    act = base.copy()
    act.name = base.name + "__" + rig.name
    act.use_fake_user = False
    fac = base["ybot_scale"] / rig.scale.x * hips_height(rig) / base["ybot_hips_m"]
    bag = anim_utils.action_get_channelbag_for_slot(act, act.slots[0])
    for fc in bag.fcurves:
        if fc.data_path == f'pose.bones["{HIPS}"].location':
            for kp in fc.keyframe_points:
                kp.co.y *= fac
                kp.handle_left.y *= fac
                kp.handle_right.y *= fac
            fc.update()
    spread_arms(rig, bag, ARM_SPREAD)
    ad = rig.animation_data_create()
    ad.action = act
    if ad.action_slot is None:
        ad.action_slot = act.slots[0]
    lo, hi = act.frame_range
    return int(lo), int(hi)


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
    return dict(hand=hand, arm=arm, rest=body & ~arm & ~shoulder, head=isl == 1)


def penetration(mesh, variant):
    """Wie tief stecken die Hände im Rumpf/in den Beinen? (mm, 0 = keine Durchdringung)."""
    m = _part_masks(mesh, variant)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    me = ev.to_mesh()
    M = mesh.matrix_world
    co = [M @ v.co for v in me.vertices]
    keep = m["rest"]
    polys = [tuple(pl.vertices) for pl in me.polygons if all(keep[i] for i in pl.vertices)]
    bvh = BVHTree.FromPolygons(co, polys)
    deep = 0.0
    n_in = 0
    for i in np.nonzero(m["hand"])[0].tolist():
        loc, nrm, _idx, d = bvh.find_nearest(co[i])
        if loc is not None and (co[i] - loc).dot(nrm) < 0:
            n_in += 1
            deep = max(deep, d)
    hc = np.array([tuple(co[i]) for i in np.nonzero(m["head"])[0]])
    r = np.linalg.norm(hc - hc.mean(0), axis=1)
    ev.to_mesh_clear()
    return dict(hand_innen=n_in, tiefe_mm=round(deep * 1000, 1), kopf_rund_mm=round(float(r.max() - r.min()) * 1000 - 1.0, 1))
