"""Baut die Grund-Puppe (3 Varianten) + Material + Gesichts-Schalter in Blender 5.2.
Läuft im offenen Blender (über den MCP-Socket) oder per `blender -b -P`.
Konventionen: T-Pose, Füße auf Z=0, Blick nach -Y, X = Bild rechts von vorn, Maße in Metern.
"""
import math

import bmesh
import bpy
import numpy as np

CHAR_DIR = "C:/ProjectTikTok/studio/assets/characters"

# Basis-Maße: siehe bible/FIGUREN.md -> „Maße Grund-Puppe“ (D = Kopf-Ø, Figur ≈ 6 D)
VARIANTS = {
    "Erwachsen": dict(H=1.75, D=0.29, sx=1.00, sy=1.00, th=1.00, loc=(0.0, 0.0, 0.0)),
    "Schmal": dict(H=1.65, D=0.275, sx=0.87, sy=0.92, th=0.88, loc=(2.0, 0.0, 0.0)),
    "Kind": dict(H=1.20, D=0.255, sx=0.70, sy=0.72, th=0.70, loc=(-1.8, 0.0, 0.0)),
}
BODY_TOP = 1.43     # Oberkante Körper-Käfig bei 1,75 m
SHOULDER_X = 0.215  # Arm-Ansatz
XL = 0.098          # Bein-Mitte
HEAD_GRID = 24      # Kacheln pro Würfel-Kante der Kopf-Kugel
SEAM_DEPTH = 0.0010  # Guss-Naht: Tiefe (m) bei D=0,29
SEAM_A = (0.0085, 0.019)  # Naht: Stützkanten (Würfel-Parameter, ±1,2 mm / ±2,8 mm)
SEAM_START, SEAM_END = 34.0, 150.0  # Stirn -> Hinterkopf (0° = Blickrichtung, 90° = Scheitel)
FACE_THETA_MAX = math.radians(90.0)  # Raster der Gesichts-Texturen


# ------------------------------------------------------------------ Körper-Käfig
class Cage:
    def __init__(self):
        self.v = []
        self.f = []

    def add(self, x, y, z):
        self.v.append((x, y, z))
        return len(self.v) - 1

    def tube(self, a, b, skip=()):
        n = len(a)
        for k in range(n):
            if k in skip:
                continue
            self.f.append((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))

    def cap(self, ring, c):
        self.f += [(ring[0], ring[1], ring[2], c), (ring[2], ring[3], ring[4], c),
                   (ring[4], ring[5], ring[6], c), (ring[6], ring[7], ring[0], c)]


C45 = 0.72
ARM_K = [(-C45, -C45), (0, -1), (C45, -C45), (1, 0), (C45, C45), (0, 1), (-C45, C45), (-1, 0)]  # (y, z)
THUMB_K = [(-C45, -C45), (0, -1), (C45, -C45), (1, 0), (C45, C45), (0, 1), (-C45, C45), (-1, 0)]  # (x, z)
LEG_A = [math.radians(a) for a in (-125, -65, 0, 65, 125, 155, 180, -155)]


def body_cage(p):
    sz = (p["H"] - p["D"] - 0.03 * p["D"] / 0.29) / BODY_TOP
    sx, sy, th = p["sx"], p["sy"], p["th"]
    sa = sz  # Arm-Länge skaliert mit der Höhe
    c = Cage()

    # Rumpf: z, Seite, vorn/hinten-x, vorn/hinten-y, Mitte vorn, Mitte hinten
    T = [
        (0.85, 0.172, 0.116, 0.106, 0.106, 0.110),
        (0.93, 0.174, 0.120, 0.112, 0.112, 0.120),
        (1.06, 0.160, 0.108, 0.102, 0.104, 0.106),
        (1.17, 0.172, 0.116, 0.114, 0.118, 0.118),
        (1.26, 0.192, 0.130, 0.120, 0.122, 0.124),
        (1.335, 0.205, 0.138, 0.112, 0.114, 0.116),
        (1.395, 0.168, 0.112, 0.088, 0.090, 0.092),
        (1.425, 0.066, 0.046, 0.054, 0.056, 0.058),
    ]
    rings = []
    for z, w, x1, d1, d0f, d0b in T:
        z *= sz
        rings.append([
            c.add(0.0, -d0f * sy, z), c.add(x1 * sx, -d1 * sy, z), c.add(w * sx, 0.0, z),
            c.add(x1 * sx, d1 * sy, z), c.add(0.0, d0b * sy, z)])
    for i in range(len(rings) - 1):
        lo, up = rings[i], rings[i + 1]
        for k in range(4):
            if i in (4, 5) and k in (1, 2):  # Arm-Öffnung
                continue
            c.f.append((lo[k], lo[k + 1], up[k + 1], up[k]))
    top = rings[-1]
    cc = c.add(0.0, 0.0, 1.43 * sz)
    c.f += [(top[0], top[1], top[2], cc), (top[2], top[3], top[4], cc)]  # halber Deckel

    # Arm + Fäustling (T-Pose, Handfläche unten)
    t4, t5, t6 = rings[4], rings[5], rings[6]
    root = [t4[1], t4[2], t4[3], t5[3], t6[3], t6[2], t6[1], t5[1]]
    za = 1.335 * sz

    def arm_x(x):
        return SHOULDER_X * sx + (x - SHOULDER_X) * sa

    def arm_ring(x, ry, rz):
        ry *= th
        rz *= th
        return [c.add(arm_x(x), ky * ry, za + kz * rz) for ky, kz in ARM_K]

    A = [(0.262, 0.060, 0.068), (0.31, 0.053, 0.057), (0.39, 0.050, 0.052), (0.45, 0.047, 0.048), (0.49, 0.046, 0.047),
         (0.53, 0.047, 0.048), (0.61, 0.046, 0.046), (0.69, 0.041, 0.041), (0.735, 0.037, 0.037)]
    prev = root
    for x, ry, rz in A:
        r = arm_ring(x, ry, rz)
        c.tube(prev, r)
        prev = r
    H = [(0.765, 0.052, 0.036), (0.81, 0.064, 0.038), (0.855, 0.064, 0.036), (0.895, 0.050, 0.030), (0.915, 0.026, 0.017)]
    hr = [arm_ring(*h) for h in H]
    c.tube(prev, hr[0])
    c.tube(hr[0], hr[1], skip=(6, 7))  # Daumen-Öffnung
    c.tube(hr[1], hr[2], skip=(6, 7))
    c.tube(hr[2], hr[3])
    c.tube(hr[3], hr[4])
    c.cap(hr[4], c.add(arm_x(0.92), 0.0, za))
    # Daumen-Stummel nach vorn (-Y)
    loop = [hr[0][0], hr[1][0], hr[2][0], hr[2][7], hr[2][6], hr[1][6], hr[0][6], hr[0][7]]
    hx = arm_x(0.81)
    prev = loop
    for dy, dx, ru, rw in ((0.012, 0.004, 0.034, 0.027), (0.040, 0.016, 0.028, 0.025), (0.066, 0.028, 0.022, 0.020)):
        r = [c.add(hx + dx * sa + kx * ru * th, -(0.064 * th + dy * th), za + kz * rw * th - 0.003 * th) for kx, kz in THUMB_K]
        c.tube(prev, r)
        prev = r
    c.cap(prev, c.add(hx + 0.033 * sa, -(0.064 * th + 0.077 * th), za - 0.003 * th))

    # Bein + Fuß
    t0 = rings[0]
    cf, c0, cb = c.add(0.0, -0.070 * sy, 0.785 * sz), c.add(0.0, 0.0, 0.755 * sz), c.add(0.0, 0.070 * sy, 0.785 * sz)
    root = [t0[0], t0[1], t0[2], t0[3], t0[4], cb, c0, cf]
    xl = XL * sx

    def leg_ring(z, rx, ry, yc=0.0, scale_z=True):
        z = z * sz if scale_z else z
        rx *= th
        ry *= th
        return [c.add(xl + rx * math.cos(a), yc * th + ry * math.sin(a), z) for a in LEG_A]

    L = [(0.70, 0.076, 0.098), (0.60, 0.074, 0.088), (0.51, 0.066, 0.074), (0.465, 0.063, 0.069), (0.42, 0.063, 0.069),
         (0.30, 0.060, 0.065), (0.17, 0.050, 0.053), (0.10, 0.045, 0.048)]
    prev = root
    for z, rx, ry in L:
        r = leg_ring(z, rx, ry)
        c.tube(prev, r)
        prev = r
    Fo = [(0.058, 0.056, 0.098, -0.035), (0.024, 0.064, 0.125, -0.050), (0.0, 0.056, 0.110, -0.050)]
    for z, rx, ry, yc in Fo:
        r = leg_ring(z, rx, ry, yc)
        c.tube(prev, r)
        prev = r
    c.cap(prev, c.add(xl, -0.050 * th, 0.0))
    return c


def mirror(c):
    """Rechte Hälfte -> ganze Figur; Mittel-Vertices (x=0) werden geteilt."""
    used = sorted({i for f in c.f for i in f})
    remap = {old: n for n, old in enumerate(used)}
    verts = [c.v[i] for i in used]
    m = {}
    for old in used:
        x, y, z = c.v[old]
        if abs(x) < 1e-9:
            m[old] = remap[old]
        else:
            verts.append((-x, y, z))
            m[old] = len(verts) - 1
    faces = [tuple(remap[i] for i in f) for f in c.f]
    faces += [tuple(m[i] for i in reversed(f)) for f in c.f]
    return verts, faces


def subdivide(verts, faces, levels=2):
    me = bpy.data.meshes.new("_tmp")
    me.from_pydata(verts, [], faces)
    # Einheitliche Flächen-Richtung ist Pflicht: sonst wertet OpenSubdiv die Ränder als harte Kante (Knick an Hüfte/Schulter)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("_tmp", me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("s", "SUBSURF")
    mod.levels = mod.render_levels = levels
    dg = bpy.context.evaluated_depsgraph_get()
    res = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    out_v = [tuple(v.co) for v in res.vertices]
    out_f = [tuple(p.vertices) for p in res.polygons]
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    bpy.data.meshes.remove(res)
    return out_v, out_f


# ------------------------------------------------------------------ Kopf / Hals
def quad_sphere(px, py, pz):
    """Würfel-Kugel, nur Quads. px/py/pz: Würfel-Parameter je Achse."""
    nx, ny, nz = len(px), len(py), len(pz)
    idx, verts = {}, []

    def vid(i, j, k):
        key = (i, j, k)
        if key not in idx:
            a = np.array((px[i], py[j], pz[k]), float)
            a /= np.linalg.norm(a)
            idx[key] = len(verts)
            verts.append(tuple(a))
        return idx[key]

    faces = []
    for i in range(nx - 1):
        for j in range(ny - 1):
            faces.append((vid(i, j, 0), vid(i, j + 1, 0), vid(i + 1, j + 1, 0), vid(i + 1, j, 0)))
            faces.append((vid(i, j, nz - 1), vid(i + 1, j, nz - 1), vid(i + 1, j + 1, nz - 1), vid(i, j + 1, nz - 1)))
    for i in range(nx - 1):
        for k in range(nz - 1):
            faces.append((vid(i, 0, k), vid(i + 1, 0, k), vid(i + 1, 0, k + 1), vid(i, 0, k + 1)))
            faces.append((vid(i, ny - 1, k), vid(i, ny - 1, k + 1), vid(i + 1, ny - 1, k + 1), vid(i + 1, ny - 1, k)))
    for j in range(ny - 1):
        for k in range(nz - 1):
            faces.append((vid(0, j, k), vid(0, j, k + 1), vid(0, j + 1, k + 1), vid(0, j + 1, k)))
            faces.append((vid(nx - 1, j, k), vid(nx - 1, j + 1, k), vid(nx - 1, j + 1, k + 1), vid(nx - 1, j, k + 1)))
    return verts, faces


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def head_mesh(p):
    R = p["D"] / 2
    zc = p["H"] - R
    base = [math.tan(math.pi / 4 * t) for t in np.linspace(-1, 1, HEAD_GRID + 1)]
    sa, sb = SEAM_A
    px = sorted(set([round(a, 6) for a in base] + [-sa, sa, -sb, sb]))
    verts, faces = quad_sphere(px, base, base)
    out = []
    depth = SEAM_DEPTH * p["D"] / 0.29
    for x, y, z in verts:
        # Winkel in der Mittel-Ebene: 0° = vorn (-Y), 90° = Scheitel, 180° = hinten
        alpha = math.degrees(math.atan2(z, -y))
        if alpha < 0:
            alpha += 360 if alpha < -90 else 0
        fade = smooth((alpha - SEAM_START) / 7.0) * smooth((SEAM_END - alpha) / 12.0)
        q = abs(x)
        prof = 1.0 if q < 1e-5 else (0.28 if q < 0.012 else 0.0)  # V-Nut: Mitte tief, Stütze flach
        r = R - depth * fade * prof
        out.append((x * r, y * r, zc + z * r))
    return out, faces, verts, zc, R


def neck_mesh(p, zc, R):
    k = p["D"] / 0.29
    rb = 0.040 * k
    zb = zc - R  # Kugel-Mitte = Unterkante Kopf -> Kopf wirkt „aufgesteckt“
    g = [math.tan(math.pi / 4 * t) for t in np.linspace(-1, 1, 7)]
    bv, bf = quad_sphere(g, g, g)
    ball = [(x * rb, y * rb, zb + z * rb) for x, y, z in bv]
    # Gelenk-Ring (Rotationskörper, geschlossenes Profil)
    z0 = zb - 0.040 * k
    prof = [(0.034, 0.0), (0.054, 0.0), (0.060, 0.005), (0.061, 0.012), (0.057, 0.019), (0.046, 0.022), (0.036, 0.021)]
    seg = 32
    rv, rf = [], []
    for s in range(seg):
        a = 2 * math.pi * s / seg
        for r, z in prof:
            rv.append((r * k * math.cos(a), r * k * math.sin(a), z0 + z * k))
    n = len(prof)
    for s in range(seg):
        for j in range(n):
            s2 = (s + 1) % seg
            j2 = (j + 1) % n
            rf.append((s * n + j, s2 * n + j, s2 * n + j2, s * n + j2))
    return ball, bf, rv, rf


def build_mesh(name, p):
    bv, bf = subdivide(*mirror(body_cage(p)))
    hv, hf, hdir, zc, R = head_mesh(p)
    nb, nbf, nr, nrf = neck_mesh(p, zc, R)
    verts, faces = list(bv), list(bf)
    h0 = len(verts)
    verts += hv
    faces += [tuple(i + h0 for i in f) for f in hf]
    h1 = len(verts)
    for vv, ff in ((nb, nbf), (nr, nrf)):
        o = len(verts)
        verts += vv
        faces += [tuple(i + o for i in f) for f in ff]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    # FaceUV: azimutale Projektion um die Blickrichtung; Rest liegt außerhalb / in der leeren Ecke
    uv = me.uv_layers.new(name="FaceUV")
    data = np.zeros((len(me.loops), 2), np.float32) + 0.0005
    li = np.zeros(len(me.loops), np.int32)
    me.loops.foreach_get("vertex_index", li)
    hd = np.array(hdir, np.float32)
    for n, vi in enumerate(li):
        if h0 <= vi < h1:
            x, y, z = hd[vi - h0]
            theta = math.acos(max(-1.0, min(1.0, -y)))
            s = math.hypot(x, z)
            k = 0.0 if s < 1e-6 else theta / FACE_THETA_MAX * 0.5 / s
            data[n] = (0.5 + x * k, 0.5 + z * k)
    uv.data.foreach_set("uv", data.ravel())
    return me


# ------------------------------------------------------------------ Material + Schalter
def srgb(c):
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92


def hex_col(h):
    return tuple(srgb(int(h[i:i + 2], 16) / 255) for i in (1, 3, 5)) + (1.0,)


def load_tiles():
    name = "gesicht.<UDIM>.png"
    if name in bpy.data.images:
        return bpy.data.images[name]
    before = set(bpy.data.images)
    bpy.ops.image.open(filepath=f"{CHAR_DIR}/faces/gesicht.1001.png", directory=f"{CHAR_DIR}/faces/",
                       files=[{"name": "gesicht.1001.png"}], relative_path=True, use_udim_detecting=True)
    img = (set(bpy.data.images) - before).pop()
    img.name = name
    img.alpha_mode = "STRAIGHT"
    img.colorspace_settings.name = "sRGB"
    return img


def tile_group():
    g = bpy.data.node_groups.get("TileOffset")
    if g:
        return g
    g = bpy.data.node_groups.new("TileOffset", "ShaderNodeTree")
    g.interface.new_socket("Index", in_out="INPUT", socket_type="NodeSocketFloat")
    g.interface.new_socket("UV", in_out="INPUT", socket_type="NodeSocketVector")
    g.interface.new_socket("UV", in_out="OUTPUT", socket_type="NodeSocketVector")
    n, l = g.nodes, g.links
    i, o = n.new("NodeGroupInput"), n.new("NodeGroupOutput")
    rd = n.new("ShaderNodeMath"); rd.operation = "ROUND"
    md = n.new("ShaderNodeMath"); md.operation = "MODULO"; md.inputs[1].default_value = 10
    dv = n.new("ShaderNodeMath"); dv.operation = "DIVIDE"; dv.inputs[1].default_value = 10
    fl = n.new("ShaderNodeMath"); fl.operation = "FLOOR"
    cb = n.new("ShaderNodeCombineXYZ")
    ad = n.new("ShaderNodeVectorMath"); ad.operation = "ADD"
    l.new(i.outputs["Index"], rd.inputs[0])
    l.new(rd.outputs[0], md.inputs[0])
    l.new(rd.outputs[0], dv.inputs[0])
    l.new(dv.outputs[0], fl.inputs[0])
    l.new(md.outputs[0], cb.inputs[0])
    l.new(fl.outputs[0], cb.inputs[1])
    l.new(i.outputs["UV"], ad.inputs[0])
    l.new(cb.outputs[0], ad.inputs[1])
    l.new(ad.outputs[0], o.inputs["UV"])
    return g


def build_material():
    name = "Puppe_Vinyl"
    old = bpy.data.materials.get(name)
    if old:
        bpy.data.materials.remove(old)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    n, l = nt.nodes, nt.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial"); out.location = (1500, 0)
    b = n.new("ShaderNodeBsdfPrincipled"); b.location = (1200, 0)
    l.new(b.outputs[0], out.inputs[0])
    white = hex_col("#E8E6E1")
    ink = hex_col("#1A1A1A")
    b.inputs["Roughness"].default_value = 0.55
    b.inputs["Sheen Weight"].default_value = 0.18
    b.inputs["Sheen Roughness"].default_value = 0.6
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.45, 0.3)
    b.inputs["Subsurface Scale"].default_value = 0.006

    def attr(nm, y):
        a = n.new("ShaderNodeAttribute")
        a.attribute_type = "OBJECT"
        a.attribute_name = nm
        a.location = (-1500, y)
        return a.outputs["Fac"]

    ausdruck, mund, brauen, glanz = attr("ausdruck", 300), attr("mund", 120), attr("brauen", -60), attr("glanz", -240)

    def math_node(op, a=None, c=None, x=0, y=0):
        m = n.new("ShaderNodeMath")
        m.operation = op
        m.location = (x, y)
        for i, v in enumerate((a, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                l.new(v, m.inputs[i])
        return m.outputs[0]

    # UV begrenzen, damit Rückseite/Körper transparent bleiben und keine fremde Kachel lesen
    uvm = n.new("ShaderNodeUVMap"); uvm.uv_map = "FaceUV"; uvm.location = (-1500, -500)
    sep = n.new("ShaderNodeSeparateXYZ"); sep.location = (-1300, -500)
    l.new(uvm.outputs[0], sep.inputs[0])
    cu = n.new("ShaderNodeClamp"); cu.inputs[1].default_value = 0.001; cu.inputs[2].default_value = 0.999; cu.location = (-1100, -440)
    cv = n.new("ShaderNodeClamp"); cv.inputs[1].default_value = 0.001; cv.inputs[2].default_value = 0.999; cv.location = (-1100, -580)
    l.new(sep.outputs[0], cu.inputs[0])
    l.new(sep.outputs[1], cv.inputs[0])
    cuv = n.new("ShaderNodeCombineXYZ"); cuv.location = (-900, -500)
    l.new(cu.outputs[0], cuv.inputs[0])
    l.new(cv.outputs[0], cuv.inputs[1])

    img = load_tiles()
    grp = tile_group()

    def sample(idx, y):
        g = n.new("ShaderNodeGroup"); g.node_tree = grp; g.location = (-400, y)
        l.new(idx, g.inputs["Index"])
        l.new(cuv.outputs[0], g.inputs["UV"])
        t = n.new("ShaderNodeTexImage"); t.image = img; t.location = (-150, y)
        t.interpolation = "Linear"
        t.extension = "EXTEND"
        l.new(g.outputs[0], t.inputs[0])
        return t

    # mund 0 = wie Ausdruck, 1-5 = Sprech-Formen (Kacheln ab Index 20)
    use_m = math_node("GREATER_THAN", mund, 0.5, -1000, 100)
    idx_m = math_node("ADD", math_node("MULTIPLY", use_m, math_node("ADD", mund, 19, -1000, -50), -800, 100),
                      math_node("MULTIPLY", math_node("SUBTRACT", 1, use_m, -1000, 240), ausdruck, -800, 240), -600, 150)
    idx_b = math_node("ADD", brauen, 29, -1000, -200)
    t_eye = sample(ausdruck, 500)
    t_mouth = sample(idx_m, 150)
    t_brow = sample(idx_b, -200)

    SPLIT_V = 0.5 - 300 / 2048
    is_eye = math_node("GREATER_THAN", cv.outputs[0], SPLIT_V, 150, -420)
    a_eye = math_node("MULTIPLY", t_eye.outputs["Alpha"], is_eye, 350, 500)
    a_mouth = math_node("MULTIPLY", t_mouth.outputs["Alpha"], math_node("SUBTRACT", 1, is_eye, 150, -560), 350, 200)
    a_brow = math_node("MULTIPLY", t_brow.outputs["Alpha"], math_node("GREATER_THAN", brauen, 0.5, 150, -250), 350, -100)
    alpha = math_node("MAXIMUM", math_node("MAXIMUM", a_eye, a_mouth, 550, 350), a_brow, 750, 250)

    # Glanzpunkt: `glanz`=1 oder Ausdruck wach-starr (Index 4), nur im Augen-Teil
    eq = n.new("ShaderNodeMath"); eq.operation = "COMPARE"; eq.location = (150, 800)
    l.new(ausdruck, eq.inputs[0])
    eq.inputs[1].default_value = 4
    eq.inputs[2].default_value = 0.5
    gon = math_node("MAXIMUM", glanz, eq.outputs[0], 350, 800)
    sc = n.new("ShaderNodeSeparateColor"); sc.location = (150, 650)
    l.new(t_eye.outputs["Color"], sc.inputs[0])
    gamt = math_node("MULTIPLY", math_node("MULTIPLY", sc.outputs[0], gon, 550, 700), is_eye, 750, 700)

    inkmix = n.new("ShaderNodeMix"); inkmix.data_type = "RGBA"; inkmix.location = (950, 600)
    l.new(gamt, inkmix.inputs["Factor"] if "Factor" in inkmix.inputs else inkmix.inputs[0])
    inkmix.inputs[6].default_value = ink
    inkmix.inputs[7].default_value = (1, 1, 1, 1)
    basemix = n.new("ShaderNodeMix"); basemix.data_type = "RGBA"; basemix.location = (950, 300)
    l.new(alpha, basemix.inputs[0])
    basemix.inputs[6].default_value = white
    l.new(inkmix.outputs[2], basemix.inputs[7])
    l.new(basemix.outputs[2], b.inputs["Base Color"])
    # Aufdruck bleibt tiefschwarz: kein Subsurface, kein Glanz, kein Sheen (sonst wird er im Streiflicht grau)
    skin = math_node("SUBTRACT", 1, alpha, 750, -100)
    l.new(math_node("MULTIPLY", skin, 0.05, 950, -100), b.inputs["Subsurface Weight"])
    l.new(math_node("MULTIPLY", skin, 0.5, 950, -250), b.inputs["Specular IOR Level"])
    l.new(math_node("MULTIPLY", skin, 0.18, 950, -400), b.inputs["Sheen Weight"])
    return mat


SWITCHES = {
    "ausdruck": (0, 14, "0 neutral 1 augen-zu 2 schlaefrig 3 blinzeln 4 wach-starr 5 neugierig 6 aufgeregt 7 gluecklich "
                        "8 aengstlich 9 erschrocken 10 panisch 11 traurig 12 misstrauisch 13 fluestern 14 leer"),
    "mund": (0, 5, "0 wie Ausdruck | 1 m-zu 2 m-klein 3 m-offen 4 m-wellig 5 m-breit"),
    "brauen": (0, 3, "0 keine | 1 besorgt 2 wuetend 3 ueberrascht"),
    "glanz": (0, 1, "Glanzpunkt fuer Nah/Gross (wach-starr hat ihn immer)"),
}


def build_all():
    scn = bpy.context.scene
    coll = bpy.data.collections.get("Puppe") or bpy.data.collections.new("Puppe")
    if coll.name not in scn.collection.children:
        scn.collection.children.link(coll)
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob)
    for nm in ("Stat_L", "Stat_R"):  # Statisten nutzen das Mesh mit und werden bei Bedarf neu angelegt
        if nm in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[nm])
    for me in list(bpy.data.meshes):
        if me.name.startswith("Puppe_") and me.users == 0:
            bpy.data.meshes.remove(me)
    mat = build_material()
    report = {}
    for name, p in VARIANTS.items():
        me = build_mesh("Puppe_" + name, p)
        me.materials.append(mat)
        ob = bpy.data.objects.new("Puppe_" + name, me)
        ob.location = p["loc"]
        coll.objects.link(ob)
        for key, (lo, hi, desc) in SWITCHES.items():
            ob[key] = 0
            ui = ob.id_properties_ui(key)
            ui.update(min=lo, max=hi, soft_min=lo, soft_max=hi, description=desc)
        co = np.zeros(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        tris = sum(len(f.vertices) - 2 for f in me.polygons)
        report[name] = dict(verts=len(me.vertices), quads=sum(len(f.vertices) == 4 for f in me.polygons),
                            polys=len(me.polygons), tris=tris, height=round(float(co[:, 2].max()), 4),
                            min_z=round(float(co[:, 2].min()), 4), span_x=round(float(co[:, 0].max() - co[:, 0].min()), 3),
                            front_y=round(float(co[:, 1].min()), 3))
    return report
