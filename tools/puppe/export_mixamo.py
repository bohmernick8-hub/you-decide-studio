"""Schritt 5: zusammengefügte Kopie der Puppe (ein Mesh, eine geschlossene Hülle, T-Pose) -> assets/characters/puppe_tpose.fbx
+ Marker-Hilfe für Mixamo -> reference/abnahme/mixamo_marker.jpg.
Die Grund-Puppe in characters.blend bleibt unverändert; die Kopie existiert nur während des Exports.
Läuft nach build_puppe.py + abnahme.py im selben Namensraum."""
import bmesh
import numpy as np

FBX_PATH = "C:/ProjectTikTok/studio/assets/characters/puppe_tpose.fbx"
GUIDE_RENDER = "C:/ProjectTikTok/studio/renders/_puppe/mixamo_vorn.png"


def _islands(me):
    """Zerlegt das Mesh in zusammenhängende Teile: [(verts, faces), ...], größtes zuerst."""
    n = len(me.vertices)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for e in me.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b:
            parent[a] = b
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    out = []
    faces = {}
    for p in me.polygons:
        faces.setdefault(find(p.vertices[0]), []).append(tuple(p.vertices))
    for root, vs in groups.items():
        remap = {v: k for k, v in enumerate(vs)}
        out.append(([tuple(me.vertices[v].co) for v in vs], [tuple(remap[i] for i in f) for f in faces[root]]))
    out.sort(key=lambda t: -len(t[0]))
    return out


def _core(k=1.0, zb=1.46):
    """Unsichtbarer Kern im Hals: verbindet Körper, Ring und Kugel zu einer Hülle (steckt komplett im Ring)."""
    seg, r, z0, z1 = 24, 0.045 * k, zb - 0.06 * k, zb - 0.02 * k
    v = [(r * math.cos(2 * math.pi * s / seg), r * math.sin(2 * math.pi * s / seg), z) for z in (z0, z1) for s in range(seg)]
    v += [(0.0, 0.0, z0), (0.0, 0.0, z1)]
    f = []
    for s in range(seg):
        t = (s + 1) % seg
        f.append((s, t, seg + t, seg + s))
        f.append((t, s, 2 * seg))
        f.append((seg + s, seg + t, 2 * seg + 1))
    return v, f


def _obj(name, v, f, coll):
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def make_union():
    src = bpy.data.objects["Puppe_Erwachsen"]
    parts = _islands(src.data)
    print("Teile im Original:", [len(p[0]) for p in parts])
    scn = bpy.context.scene
    tmp = bpy.data.collections.new("_mixamo_tmp")
    scn.collection.children.link(tmp)
    ops = bpy.data.collections.new("_mixamo_ops")
    scn.collection.children.link(ops)
    body = _obj("puppe_tpose_roh", parts[0][0], parts[0][1], tmp)
    for i, (v, f) in enumerate(parts[1:] + [_core()]):
        _obj(f"_op{i}", v, f, ops)
    mod = body.modifiers.new("vereinen", "BOOLEAN")
    mod.operation = "UNION"
    mod.operand_type = "COLLECTION"
    mod.collection = ops
    mod.solver = "MANIFOLD"
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(body.evaluated_get(dg))
    me.name = "puppe_tpose"
    me.shade_smooth()
    ob = bpy.data.objects.new("puppe_tpose", me)
    tmp.objects.link(ob)
    # Aufräumen der Bauteile
    for o in list(ops.objects):
        m = o.data
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(m)
    bpy.data.collections.remove(ops)
    m = body.data
    bpy.data.objects.remove(body)
    bpy.data.meshes.remove(m)
    return ob, tmp


def check(ob):
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bad = sum(1 for e in bm.edges if len(e.link_faces) != 2)
    isl = len(_islands(me))
    co = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    bm.free()
    r = dict(islands=isl, nicht_manifold=bad, tris=tris, verts=len(me.vertices), hoehe=round(float(co[:, 2].max()), 4),
             min_z=round(float(co[:, 2].min()), 4), breite=round(float(co[:, 0].max() - co[:, 0].min()), 3))
    print("Kopie:", r)
    return r


def export_fbx(ob):
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    ob.select_set(True)
    vl.objects.active = ob
    bpy.ops.export_scene.fbx(
        filepath=FBX_PATH, check_existing=False, use_selection=True, object_types={"MESH"},
        use_mesh_modifiers=False, mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False,
        path_mode="AUTO", embed_textures=False, axis_forward="-Z", axis_up="Y",
        global_scale=1.0, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", bake_space_transform=True)
    print("FBX:", FBX_PATH)


def render_guide(ob):
    """Frontalbild der Kopie ohne Gesicht: so ähnlich sieht sie in Mixamo aus."""
    scn = bpy.context.scene
    hidden = []
    for o in bpy.data.collections["Puppe"].objects:
        hidden.append((o, o.hide_render))
        o.hide_render = True
    set_look("warm")
    bpy.data.objects["Set_Leiste"].hide_render = True
    cam = camera((0, -6.0, 0.9), (0, 0, 0.9), 50)
    cam.data.dof.use_dof = False
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 2.2
    render(GUIDE_RENDER, 1400, 1400, 32)
    cam.data.type = "PERSP"
    for o, h in hidden:
        o.hide_render = h


def run():
    ob, tmp = make_union()
    result = check(ob)
    export_fbx(ob)
    render_guide(ob)
    m = ob.data
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(m)
    bpy.data.collections.remove(tmp)
    # Bibliothek sauber halten: alle Varianten wieder sichtbar, leere Standard-Collection weg
    leer = bpy.data.collections.get("Collection")
    if leer and not leer.objects and not leer.children:
        bpy.data.collections.remove(leer)
    print("Grund-Puppe unverändert:", {k: bpy.data.objects["Puppe_Erwachsen"][k] for k in ("ausdruck", "mund", "brauen", "glanz")},
          "Polys", len(bpy.data.objects["Puppe_Erwachsen"].data.polygons))
    bpy.ops.wm.save_mainfile()
    return result
