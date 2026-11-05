"""Test-Posen (sitzend/stehend) NUR für die Abnahme, vor dem Mixamo-Rig: einfaches Hilfs-Skelett mit berechneten Gewichten.
Legt alles in die Collection `_pose_tmp`; cleanup() entfernt es wieder. Die Grund-Puppe bleibt unverändert in T-Pose.
Läuft nach build_puppe.py + abnahme.py im selben Namensraum."""
import math

import bpy
import numpy as np
from mathutils import Euler, Quaternion, Vector


def tmp_coll():
    c = bpy.data.collections.get("_pose_tmp")
    if not c:
        c = bpy.data.collections.new("_pose_tmp")
        bpy.context.scene.collection.children.link(c)
    return c


def smooth_np(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def island_ids(me):
    n = len(me.vertices)
    parent = np.arange(n)
    ed = np.zeros(len(me.edges) * 2, np.int32)
    me.edges.foreach_get("vertices", ed)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b in ed.reshape(-1, 2):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    roots = np.array([find(i) for i in range(n)])
    uniq, counts = np.unique(roots, return_counts=True)
    order = uniq[np.argsort(-counts)]
    return {int(r): i for i, r in enumerate(order)}, roots


def compute_weights(me, j):
    """Gibt {Knochen: Gewichte[]} zurück. 0 = Körper, 1 = Kopf, 2/3 = Halskugel und Ring."""
    co = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    x, z = co[:, 0], co[:, 2]
    rank, roots = island_ids(me)
    isl = np.array([rank[int(r)] for r in roots])
    ax = np.abs(x)
    side = x >= 0
    w = {}

    def put(name, arr):
        w[name] = w.get(name, 0) + arr

    arm = smooth_np(j["jx"] - 0.02 * j["sz"], j["jx"] + 0.05 * j["sz"], ax) * smooth_np(j["za"] - 0.095 * j["sz"], j["za"] - 0.06 * j["sz"], z)
    fore = smooth_np(j["elbow"] - 0.03, j["elbow"] + 0.03, ax)
    hand = smooth_np(j["wrist"] - 0.012, j["wrist"] + 0.012, ax)
    leg = smooth_np(j["hip"] + 0.03, j["hip"] - 0.06, z)
    shin = smooth_np(j["knee"] + 0.03, j["knee"] - 0.03, z)
    foot = smooth_np(j["ankle"] + 0.02, j["ankle"] - 0.015, z)
    s1 = smooth_np(j["belly"] - 0.06, j["belly"] + 0.06, z)
    s2 = smooth_np(j["spine"] - 0.06, j["spine"] + 0.06, z)
    torso = (1 - arm) * (1 - leg)
    put("hips", torso * (1 - s1))
    put("spine", torso * s1 * (1 - s2))
    put("chest", torso * s1 * s2)
    for nm, mask in ((".L", side), (".R", ~side)):
        put("upper" + nm, arm * (1 - fore) * mask)
        put("fore" + nm, arm * fore * (1 - hand) * mask)
        put("hand" + nm, arm * hand * mask)
        put("thigh" + nm, (1 - arm) * leg * (1 - shin) * mask)
        put("shin" + nm, (1 - arm) * leg * shin * (1 - foot) * mask)
        put("foot" + nm, (1 - arm) * leg * shin * foot * mask)
    body = isl == 0
    for k in w:
        w[k] = w[k] * body
    w["head"] = (isl == 1) * 1.0
    # Halskugel gehört zum Kopf, der Ring zum Oberkörper
    ball_ring = isl >= 2
    if ball_ring.any():
        ids = np.unique(isl[ball_ring])
        heights = {i: z[isl == i].max() for i in ids}
        ball = max(heights, key=heights.get)
        w["head"] = w["head"] + (isl == ball)
        w["chest"] = w["chest"] + np.isin(isl, [i for i in ids if i != ball])
    return w


def make_rig(name, j, th):
    arm = bpy.data.armatures.new(name)
    rig = bpy.data.objects.new(name, arm)
    tmp_coll().objects.link(rig)
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    rig.select_set(True)
    vl.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.edit_bones

    def bone(nm, a, b, parent=None):
        e = eb.new(nm)
        e.head, e.tail = a, b
        if parent:
            e.parent = eb[parent]

    bone("hips", (0, 0, j["pelvis"]), (0, 0, j["belly"]))
    bone("spine", (0, 0, j["belly"]), (0, 0, j["spine"]), "hips")
    bone("chest", (0, 0, j["spine"]), (0, 0, j["chest_top"]), "spine")
    bone("head", (0, 0, j["zb"] - 0.01), (0, 0, j["zb"] + 2 * j["R"]), "chest")
    for nm, sg in ((".L", 1), (".R", -1)):
        za = j["za"]
        bone("upper" + nm, (sg * j["jx"], 0, za), (sg * j["elbow"], 0, za), "chest")
        bone("fore" + nm, (sg * j["elbow"], 0, za), (sg * j["wrist"], 0, za), "upper" + nm)
        bone("hand" + nm, (sg * j["wrist"], 0, za), (sg * j["tip"], 0, za), "fore" + nm)
        bone("thigh" + nm, (sg * j["xl"], 0, j["hip"]), (sg * j["xl"], 0, j["knee"]), "hips")
        bone("shin" + nm, (sg * j["xl"], 0, j["knee"]), (sg * j["xl"], 0, j["ankle"]), "thigh" + nm)
        bone("foot" + nm, (sg * j["xl"], 0, j["ankle"]), (sg * j["xl"], -0.12 * th, 0.02), "shin" + nm)
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


def make_posed(variant):
    p = VARIANTS[variant]
    j = rig_joints(p)
    src = bpy.data.objects["Puppe_" + variant]
    me = src.data.copy()
    me.name = "_pose_" + variant
    ob = bpy.data.objects.new("Pose_" + variant, me)
    tmp_coll().objects.link(ob)
    for k in ("ausdruck", "mund", "brauen", "glanz"):
        ob[k] = 0
    rig = make_rig("Rig_" + variant, j, p["th"])
    rule = compute_weights(me, j)
    rank, roots = island_ids(me)
    isl = np.array([rank[int(r)] for r in roots])
    body = np.nonzero(isl == 0)[0].tolist()
    other = np.nonzero(isl != 0)[0].tolist()
    # Körper: Blender-Automatik (Bone Heat), kommt echten Rig-Gewichten am nächsten. Kopf/Hals: starr nach Regel.
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    ob.select_set(True)
    rig.select_set(True)
    vl.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    heat_ok = len(ob.vertex_groups) > 0
    if heat_ok:
        probe = {g.index: 0 for g in ob.vertex_groups}
        for i in body[::40]:
            for ge in me.vertices[i].groups:
                probe[ge.group] += ge.weight
        heat_ok = sum(v > 0 for v in probe.values()) >= 10
    print(variant, "Bone Heat", "ok" if heat_ok else "fehlgeschlagen, nehme Regel-Gewichte")
    if heat_ok:
        calm_shoulder(ob, j)
    for nm in rule:
        if nm not in ob.vertex_groups:
            ob.vertex_groups.new(name=nm)
    use = other if heat_ok else list(range(len(me.vertices)))
    for g in ob.vertex_groups:
        g.remove(use)
    use_set = np.zeros(len(me.vertices), bool)
    use_set[use] = True
    for nm, arr in rule.items():
        g = ob.vertex_groups[nm]
        arr = np.asarray(arr, float) * use_set
        for w_val in np.unique(np.round(arr[arr > 1e-4], 3)):
            idx = np.nonzero(np.abs(np.round(arr, 3) - w_val) < 1e-6)[0].tolist()
            g.add(idx, float(w_val), "REPLACE")
    mod = next(m for m in ob.modifiers if m.type == "ARMATURE")
    mod.use_deform_preserve_volume = True
    return ob, rig


def calm_shoulder(ob, j):
    """Automatik-Gewichte beruhigen: Hals-Plateau und Brust-Seite folgen dem Rumpf, nicht dem Arm.
    Sonst wölbt sich die Schulter beim Armsenken über den Gelenk-Ring und die Brust wird eingeschnürt."""
    me = ob.data
    names = {g.index: g.name for g in ob.vertex_groups}
    chest = ob.vertex_groups["chest"]
    co = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    ax, z = np.abs(co[:, 0]), co[:, 2]
    sz = j["sz"]
    top = smooth_np(j["za"] - 0.02 * sz, j["za"] + 0.07 * sz, z) * smooth_np(j["jx"] + 0.01 * sz, j["jx"] - 0.08 * sz, ax)
    side = smooth_np(j["za"] - 0.02 * sz, j["za"] - 0.075 * sz, z) * smooth_np(j["jx"] + 0.015 * sz, j["jx"] - 0.02 * sz, ax)
    cut = np.maximum(top, side)
    for i in np.nonzero(cut > 1e-3)[0].tolist():
        v = me.vertices[i]
        moved = 0.0
        for ge in v.groups:
            nm = names[ge.group]
            if nm.startswith("upper") or nm.startswith("fore") or nm.startswith("hand"):
                moved += ge.weight * float(cut[i])
                ge.weight *= 1.0 - float(cut[i])
        if moved > 0:
            chest.add([i], moved, "ADD")


def q_axis(ax, deg):
    return Quaternion({"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}[ax], math.radians(deg))


def apply_pose(rig, spec):
    """spec: {Knochen: Quaternion relativ zum Eltern-Knochen, in den Achsen der T-Pose}."""
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        B = pb.bone.matrix_local.to_quaternion()
        D = spec.get(pb.name, Quaternion())
        pb.rotation_quaternion = B.inverted() @ D @ B
    bpy.context.view_layer.update()


def aim_chain(rig, chain):
    """chain: [(Knochen, Zielrichtung in T-Pose-Achsen)], Eltern zuerst. Dreht jeden Knochen auf kürzestem Weg zum Ziel."""
    out = {}
    P = Quaternion()
    for nm, target in chain:
        b = rig.data.bones[nm]
        rest = (b.tail_local - b.head_local).normalized()
        t = Vector(target).normalized()
        D = rest.rotation_difference(P.inverted() @ t)
        out[nm] = D
        P = P @ D
    return out


def mirror_x(v):
    return (-v[0], v[1], v[2])


def arm_targets(rig, nm, upper, fore, hand):
    return aim_chain(rig, [("upper" + nm, upper), ("fore" + nm, fore), ("hand" + nm, hand)])


HANG = dict(upper=(0.19, -0.03, -0.98), fore=(0.12, -0.13, -0.98), hand=(0.05, -0.08, -1.0))


def pose_stehen(rig, reach=False):
    """Stehend, Arme hängen. reach=True: rechter Arm streckt sich aus (wie RED-EYE P2 31,3 s)."""
    s = {}
    s.update(arm_targets(rig, ".L", **HANG))
    if reach:
        s.update(arm_targets(rig, ".R", upper=(-0.72, -0.36, -0.60), fore=(-0.72, -0.62, -0.30), hand=(-0.74, -0.66, -0.12)))
    else:
        s.update(arm_targets(rig, ".R", **{k: mirror_x(v) for k, v in HANG.items()}))
    return s


SIT_ARM = dict(upper=(0.06, -0.06, -1.0), fore=(-0.22, -0.50, -0.84), hand=(-0.02, -0.90, -0.44))


def pose_sitzen(rig):
    s = {}
    s.update(arm_targets(rig, ".L", **SIT_ARM))
    s.update(arm_targets(rig, ".R", **{k: mirror_x(v) for k, v in SIT_ARM.items()}))
    for nm, sg in ((".L", 1), (".R", -1)):
        s["thigh" + nm] = q_axis("Z", sg * -3) @ q_axis("X", -88)
        s["shin" + nm] = q_axis("X", 88)
    s["head"] = q_axis("X", 3)
    return s


def world_coords(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    e = ob.evaluated_get(dg)
    me = e.to_mesh()
    co = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    M = np.array(ob.matrix_world)
    co = co @ M[:3, :3].T + M[:3, 3]
    e.to_mesh_clear()
    return co


def ground(ob, rig):
    bpy.context.view_layer.update()
    rig.location.z -= float(world_coords(ob)[:, 2].min())
    bpy.context.view_layer.update()


def box(name, x0, x1, y0, y1, z0, z1, mat):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    tmp_coll().objects.link(ob)
    b = ob.modifiers.new("rund", "BEVEL")
    b.width = 0.03
    b.segments = 4
    return ob


def seat_for(ob, rig):
    """Sitz exakt unter Hintern/Oberschenkel, Lehne direkt am Rücken (Kontakt, nichts schwebt, nichts steckt drin)."""
    co = world_coords(ob)
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    lap = (np.abs(x) < 0.25) & (y > -0.24) & (y < 0.14) & (z > 0.2) & (z < 0.8)
    top = float(z[lap].min())
    torso = (np.abs(x) < 0.12) & (z > top + 0.12) & (z < top + 0.6)
    back = float(y[torso].max())
    m = flat_mat("Set_Sitz_M", "#5B5F66", 0.8)
    parts = [box("Sitz_Flaeche", -0.27, 0.27, -0.30, back + 0.02, top - 0.14, top, m),
             box("Sitz_Lehne", -0.27, 0.27, back, back + 0.13, top - 0.14, top + 0.72, m)]
    inv = rig.matrix_world.inverted()
    for o in parts:
        o.parent = rig
        o.matrix_parent_inverse = inv
    return dict(top=round(top, 3), back=round(back, 3))


def cleanup():
    c = bpy.data.collections.get("_pose_tmp")
    if not c:
        return
    meshes, arms = [], []
    for o in list(c.objects):
        if o.type == "MESH":
            meshes.append(o.data)
        elif o.type == "ARMATURE":
            arms.append(o.data)
        bpy.data.objects.remove(o)
    for m in meshes:
        bpy.data.meshes.remove(m)
    for a in arms:
        bpy.data.armatures.remove(a)
    bpy.data.collections.remove(c)
