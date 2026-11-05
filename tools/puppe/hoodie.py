"""Hoodie-Proxy NUR für den Look-Test (keine finale Kleidung): Hülle aus dem Körper-Mesh, darum folgt sie denselben Gewichten.
Landet in `_pose_tmp` und verschwindet mit cleanup(); die Grund-Puppe und die FBX bleiben ohne Hoodie.
Läuft nach build_puppe.py + abnahme.py + pose_test.py im selben Namensraum."""
import bmesh
import bpy
import numpy as np
from mathutils import Vector

HOOD_TORSO = 0.026   # Abstand Stoff <-> Körper an der Brust
HOOD_SLEEVE = 0.014  # am Oberarm
HOOD_WALL = 0.006    # Stoff-Dicke


def hoodie_material():
    m = flat_mat("Hoodie_Grau", "#83837F", 0.9)
    nt = m.node_tree
    b = next(x for x in nt.nodes if x.type == "BSDF_PRINCIPLED")
    b.inputs["Sheen Weight"].default_value = 0.6
    b.inputs["Sheen Roughness"].default_value = 0.7
    b.inputs["Specular IOR Level"].default_value = 0.25
    if not any(x.type == "BUMP" for x in nt.nodes):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        no = nt.nodes.new("ShaderNodeTexNoise")
        no.inputs["Scale"].default_value = 700.0
        no.inputs["Detail"].default_value = 3.0
        bu = nt.nodes.new("ShaderNodeBump")
        bu.inputs["Strength"].default_value = 0.22
        bu.inputs["Distance"].default_value = 0.0015
        nt.links.new(tc.outputs["Object"], no.inputs["Vector"])
        nt.links.new(no.outputs[0], bu.inputs["Height"])
        nt.links.new(bu.outputs[0], b.inputs["Normal"])
    return m


def hoodie_shell(ob, j, mat):
    """Stoff-Hülle: Rumpf bis zur Hüfte + Ärmel bis zum Handgelenk, nach außen versetzt, mit weichen Falten und Bündchen."""
    src = ob.data
    n = len(src.vertices)
    co = np.zeros(n * 3, np.float32)
    src.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    nr = np.zeros(n * 3, np.float32)
    src.vertex_normals.foreach_get("vector", nr)
    nr = nr.reshape(-1, 3)
    rank, roots = island_ids(src)
    isl = np.array([rank[int(r)] for r in roots])
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    ax = np.abs(x)
    sz = j["sz"]
    hem = j["hip"] - 0.012
    cuff = j["wrist"] + 0.002
    arm = smooth_np(j["jx"], j["jx"] + 0.06, ax) * smooth_np(j["za"] - 0.10 * sz, j["za"] - 0.065 * sz, z)
    # Rumpf: Brust lockerer als Bauch, Schulter-Dach flach; Ärmel zum Ellbogen hin etwas weiter (gleichmäßige Stoff-Röhre)
    chest_off = HOOD_TORSO * (0.72 + 0.28 * smooth_np(j["belly"], j["spine"], z)) * (1 - 0.35 * smooth_np(j["za"] + 0.01, j["za"] + 0.06, z))
    sleeve_off = HOOD_SLEEVE + 0.003 * smooth_np(j["elbow"] - 0.06, j["elbow"] + 0.04, ax)
    off = chest_off * (1 - arm) + sleeve_off * arm
    # Bündchen: am Saum und an den Handgelenken enger, mit kleiner Stufe
    off *= 1 - 0.34 * smooth_np(hem + 0.042, hem + 0.030, z) * (1 - arm)
    off *= 1 - 0.34 * smooth_np(cuff - 0.040, cuff - 0.028, ax) * arm
    # Falten: großflächige Weichheit + quer laufend am Bauch und am Ellbogen
    soft = sum(a * np.sin(kx * x + ky * y + kz * z + ph) for a, kx, ky, kz, ph in (
        (0.0016, 13, 5, 19, 0.4), (0.0012, -9, 17, 24, 2.1), (0.0009, 31, -11, 37, 4.0)))
    belly = np.exp(-(((z - (j["hip"] + 0.085)) / 0.075) ** 2)) * (1 - arm) * np.sin(z * 118 + x * 17 + 0.8) * 0.0034
    elbow = np.exp(-(((ax - j["elbow"]) / 0.055) ** 2)) * arm * np.sin(ax * 150 + y * 25) * 0.0024
    p = co + nr * (off + soft + belly + elbow)[:, None]
    # Stoff fällt vom Bauch gerade nach unten, statt der Hüfte zu folgen (sonst wirkt der Rumpf wie ein Ei)
    torso = (isl == 0) & (arm < 0.5) & (ax < 0.30)
    zb0 = j["belly"] + 0.10 * sz
    ref = torso & (np.abs(z - zb0) < 0.02)
    wx, wy = float(np.abs(p[ref, 0]).max()), float(np.abs(p[ref, 1]).max())
    low = torso & (z < zb0)
    bins = np.linspace(hem - 0.01, zb0, 16)
    for a0, a1 in zip(bins, bins[1:]):
        m = low & (z >= a0) & (z < a1)
        if not m.any():
            continue
        lx, ly = float(np.abs(p[m, 0]).max()), float(np.abs(p[m, 1]).max())
        p[m, 0] *= max(1.0, 0.985 * wx / lx)
        p[m, 1] *= max(1.0, 0.97 * wy / ly)

    me = src.copy()
    me.name = "_hoodie_shell"
    me.vertices.foreach_set("co", p.ravel())
    drop = (isl != 0) | (z < hem) | ((ax > cuff) & (z > j["za"] - 0.12 * sz))
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.nonzero(drop)[0].tolist()], context="VERTS")
    bm.to_mesh(me)
    bm.free()
    me.materials.clear()
    me.materials.append(mat)
    sh = ob.copy()
    sh.data = me
    sh.name = "Hoodie_Stoff"
    tmp_coll().objects.link(sh)
    # Stoff folgt dem Becken, nicht den Oberschenkeln: fällt beim Sitzen gerade in den Schoß, statt sich mit den Beinen zu biegen
    legs = {g.index for g in sh.vertex_groups if g.name.startswith(("thigh", "shin", "foot"))}
    hips = sh.vertex_groups["hips"]
    for v in me.vertices:
        moved = 0.0
        for ge in v.groups:
            if ge.group in legs and ge.weight > 0:
                moved += ge.weight
                ge.weight = 0.0
        if moved > 0:
            hips.add([v.index], moved, "ADD")
    so = sh.modifiers.new("dicke", "SOLIDIFY")
    so.thickness = HOOD_WALL
    so.offset = -1.0
    so.use_rim = True
    left = p[~drop]
    return sh, left


def _rigid(name, verts, faces, rig, mat, levels=1):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    tmp_coll().objects.link(ob)
    g = ob.vertex_groups.new(name="chest")
    g.add(list(range(len(verts))), 1.0, "REPLACE")
    if levels:
        s = ob.modifiers.new("rund", "SUBSURF")
        s.levels = s.render_levels = levels
    a = ob.modifiers.new("rig", "ARMATURE")
    a.object = rig
    ob.parent = rig  # wie die Puppe: folgt dem Skelett-Objekt, wenn es verschoben wird
    return ob


def hoodie_hood(rig, top_z, mat):
    """Kapuze, die hinter dem Hals liegt: dicke Rolle rund um den Hals + flacher Beutel am Rücken."""
    v, f = [], []
    N, M = 64, 12
    for s in range(N):
        a = 2 * math.pi * s / N
        b = (1 - math.cos(a)) / 2
        rad = Vector((math.sin(a), -math.cos(a), 0))
        cen = Vector((0, 0.008, top_z - 0.004)) + rad * (0.086 + 0.014 * b)
        rr, rz = 0.022 + 0.026 * b, 0.021 + 0.011 * b
        for t in range(M):
            q = 2 * math.pi * t / M
            pt = cen + rad * (rr * math.cos(q)) + Vector((0, 0, rz * math.sin(q)))
            v.append(tuple(pt))
    for s in range(N):
        for t in range(M):
            s2, t2 = (s + 1) % N, (t + 1) % M
            f.append((s * M + t, s2 * M + t, s2 * M + t2, s * M + t2))
    g = [math.tan(math.pi / 4 * t) for t in np.linspace(-1, 1, 7)]
    bv, bf = quad_sphere(g, g, g)
    o = len(v)
    back = Vector((0, 0.100, top_z - 0.105))
    v += [tuple(back + Vector((x * 0.115, y * 0.036, z * 0.100))) for x, y, z in bv]
    f += [tuple(i + o for i in q) for q in bf]
    return _rigid("Hoodie_Kapuze", v, f, rig, mat)


def hoodie_cords(rig, shell_pts, top_z, mat):
    """Zwei helle Kordeln, die vorn auf der Brust liegen (folgen der Stoff-Oberfläche)."""
    v, f = [], []
    M = 8
    L = 0.19
    for sg in (1, -1):
        rings = []
        K = 14
        for i in range(K + 1):
            t = i / K
            zq = top_z - 0.012 - L * t
            xq = sg * (0.030 + 0.010 * t)
            near = (np.abs(shell_pts[:, 0] - xq) < 0.022) & (np.abs(shell_pts[:, 2] - zq) < 0.022) & (shell_pts[:, 1] < 0)
            yq = float(shell_pts[near, 1].min()) - 0.0045 if near.any() else -0.14
            r = 0.0064 if t < 0.87 else 0.0080
            ring = []
            for s in range(M):
                q = 2 * math.pi * s / M
                ring.append(len(v))
                v.append((xq + r * math.cos(q), yq + r * math.sin(q), zq))
            rings.append(ring)
        for a, b in zip(rings, rings[1:]):
            for s in range(M):
                s2 = (s + 1) % M
                f.append((a[s], a[s2], b[s2], b[s]))
        for ring in (rings[0], rings[-1]):
            c = len(v)
            mx = np.mean([v[i] for i in ring], axis=0)
            v.append(tuple(mx))
            for s in range(M):
                f.append((ring[s], ring[(s + 1) % M], c))
    return _rigid("Hoodie_Kordeln", v, f, rig, mat)


def make_hoodie(ob, rig, j):
    grau = hoodie_material()
    weiss = flat_mat("Hoodie_Kordel", "#E8E6E1", 0.6)
    shell, pts = hoodie_shell(ob, j, grau)
    top_z = float(pts[np.hypot(pts[:, 0], pts[:, 1]) < 0.11, 2].max())
    hoodie_hood(rig, top_z, grau)
    hoodie_cords(rig, pts, top_z, weiss)
    return shell
