"""Look-Licht + Kamera + Render-Helfer für Abnahme 1 (STILBIBEL §3 / §9). Läuft nach build_puppe.py im selben Namensraum."""
import math
import os

import bpy
from mathutils import Vector

RENDERS = "C:/ProjectTikTok/studio/renders/_puppe"
ABNAHME = "C:/ProjectTikTok/studio/reference/abnahme"
HEAD_Z = VARIANTS["Erwachsen"]["H"] - VARIANTS["Erwachsen"]["D"] / 2


def setup_render(scn):
    scn.render.engine = "BLENDER_EEVEE"
    e = scn.eevee
    e.taa_render_samples = 64
    e.use_raytracing = True
    e.ray_tracing_method = "SCREEN"
    e.ray_tracing_options.resolution_scale = "2"
    e.ray_tracing_options.use_denoise = True
    e.use_shadows = True
    e.shadow_ray_count = 2
    e.shadow_step_count = 8
    e.volumetric_tile_size = "4"
    e.volumetric_samples = 64
    e.volumetric_start = 0.1
    e.volumetric_end = 12.0
    vs = scn.view_settings
    vs.view_transform = "AgX"
    vs.look = "AgX - Medium High Contrast"
    scn.render.fps = 30
    scn.render.use_motion_blur = True
    scn.render.motion_blur_shutter = 0.5
    scn.render.film_transparent = False
    scn.render.image_settings.file_format = "PNG"
    scn.render.image_settings.color_mode = "RGB"
    scn.render.use_compositing = True
    scn.compositing_node_group = post_group()


def post_group():
    name = "Look_Post"
    old = bpy.data.node_groups.get(name)
    if old:
        bpy.data.node_groups.remove(old)
    g = bpy.data.node_groups.new(name, "CompositorNodeTree")
    g.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    n, l = g.nodes, g.links
    rl = n.new("CompositorNodeRLayers"); rl.location = (-900, 0)
    gl = n.new("CompositorNodeGlare"); gl.location = (-650, 0)
    gl.inputs["Type"].default_value = "Fog Glow"
    gl.inputs["Quality"].default_value = "High"
    gl.inputs["Threshold"].default_value = 1.0
    gl.inputs["Strength"].default_value = 0.35
    gl.inputs["Size"].default_value = 0.6
    l.new(rl.outputs["Image"], gl.inputs["Image"])
    # Vignette
    el = n.new("CompositorNodeEllipseMask"); el.location = (-650, -400)
    el.inputs["Size"].default_value = (1.05, 1.05)
    bl = n.new("CompositorNodeBlur"); bl.location = (-400, -400)
    bl.inputs["Size"].default_value = (260, 260)
    l.new(el.outputs[0], bl.inputs["Image"])
    vg = n.new("ShaderNodeMix"); vg.data_type = "RGBA"; vg.blend_type = "MULTIPLY"; vg.location = (-150, 0)
    vg.inputs[0].default_value = 0.42
    l.new(gl.outputs["Image"], vg.inputs[6])
    l.new(bl.outputs[0], vg.inputs[7])
    # Filmkorn: pro Bild neues Rauschen, sehr dezent
    tm = n.new("CompositorNodeSceneTime"); tm.location = (-400, -700)
    wn = n.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "4D"; wn.location = (-150, -600)
    l.new(tm.outputs["Frame"], wn.inputs["W"])
    gr = n.new("ShaderNodeMix"); gr.data_type = "RGBA"; gr.blend_type = "MULTIPLY"; gr.location = (100, 0)
    gr.inputs[0].default_value = 0.035
    l.new(vg.outputs[2], gr.inputs[6])
    l.new(wn.outputs["Value"], gr.inputs[7])
    o = n.new("NodeGroupOutput"); o.location = (350, 0)
    l.new(gr.outputs[2], o.inputs[0])
    return g


def col_set():
    scn = bpy.context.scene
    c = bpy.data.collections.get("Abnahme_Set")
    if not c:
        c = bpy.data.collections.new("Abnahme_Set")
        scn.collection.children.link(c)
    return c


def flat_mat(name, col, rough=0.8, emit=None, emit_s=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(x for x in m.node_tree.nodes if x.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = hex_col(col)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = hex_col(emit)
        b.inputs["Emission Strength"].default_value = emit_s
    return m


def plane(name, loc, rot, size, mat):
    me = bpy.data.meshes.get(name) or bpy.data.meshes.new(name)
    if not me.vertices:
        s = 0.5
        me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, me)
    if ob.name not in col_set().objects:
        col_set().objects.link(ob)
    ob.location, ob.rotation_euler = loc, rot
    ob.scale = (size[0], size[1], 1)
    me.materials.clear()
    me.materials.append(mat)
    return ob


def area(name, loc, target, size, size_y=None):
    d = bpy.data.lights.get(name) or bpy.data.lights.new(name, "AREA")
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, d)
    if ob.name not in col_set().objects:
        col_set().objects.link(ob)
    d.shape = "RECTANGLE"
    d.size = size
    d.size_y = size_y or size
    d.use_shadow = True
    d.use_shadow_jitter = True
    d.shadow_filter_radius = 2.0
    aim(ob, loc, target)
    return ob


def aim(ob, loc, target):
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def world_setup(col, strength, density):
    w = bpy.data.worlds.get("Look_World") or bpy.data.worlds.new("Look_World")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = hex_col(col)
    bg.inputs[1].default_value = strength
    nt.links.new(bg.outputs[0], o.inputs["Surface"])
    if density > 0:
        v = nt.nodes.new("ShaderNodeVolumePrincipled")
        v.inputs["Density"].default_value = density
        v.inputs["Color"].default_value = (0.8, 0.85, 0.95, 1)
        nt.links.new(v.outputs[0], o.inputs["Volume"])
    bpy.context.scene.world = w


LOOKS = {
    # Nacht: Schatten Blaugrau #141821, Lichter kühl #C8D2E0 (Licht von oben wie Kabinen-Leiste)
    "nacht": dict(exposure=-0.5, world=("#141821", 0.25), density=0.008,
                  wall="#1B2029", floor="#10131A", ceil=True,
                  key=("#C8D2E0", 95.0, (0.75, -0.95, 3.0), 1.6, 0.5),
                  fill=("#7C8AA6", 12.0, (-1.2, -2.3, 1.15), 1.5, 1.5),
                  rim=("#C8D2E0", 26.0, (-0.9, 1.5, 2.25), 1.0, 0.5)),
    # „Licht an“ / Sprech-Einstellung: warm und weich von vorn-seitlich
    "warm": dict(exposure=-0.3, world=("#EDE3D2", 0.34), density=0.0,
                 wall="#D6CCBB", floor="#8A8070", ceil=False,
                 key=("#EDE3D2", 150.0, (1.1, -1.9, 2.3), 1.8, 1.8),
                 fill=("#EDE3D2", 26.0, (-1.8, -1.6, 1.3), 2.0, 2.0),
                 rim=("#EDE3D2", 20.0, (0.2, 1.5, 2.8), 1.5, 0.8)),
}


def set_look(name):
    p = LOOKS[name]
    scn = bpy.context.scene
    scn.view_settings.exposure = p["exposure"]
    world_setup(p["world"][0], p["world"][1], p["density"])
    plane("Set_Boden", (0, 0, 0), (0, 0, 0), (14, 14), flat_mat("Set_Boden_M", p["floor"], 0.75))
    wall_y = 6.3 if p["ceil"] else 2.6
    plane("Set_Wand", (0, wall_y, 3.0), (math.radians(90), 0, 0), (14, 8), flat_mat("Set_Wand_M", p["wall"], 0.85))
    # Warm: dunkle Leiste an der Wand (unscharf im Hintergrund). Nacht: Decke + Lichtband wie eine Kabine.
    plane("Set_Leiste", (0, 2.58, 1.42), (math.radians(90), 0, 0), (14, 0.09), flat_mat("Set_Leiste_M", "#2A2622", 0.6))
    plane("Set_Decke", (0, 3.4, 2.36), (math.radians(180), 0, 0), (5, 5.8), flat_mat("Set_Decke_M", "#3A4150", 0.55))
    plane("Set_Lichtband", (-0.72, 3.4, 2.34), (math.radians(180), 0, 0), (0.10, 5.8),
          flat_mat("Set_Lichtband_M", "#000000", 0.5, "#C8D2E0", 3.2))
    for nm, vis in (("Set_Leiste", not p["ceil"]), ("Set_Decke", p["ceil"]), ("Set_Lichtband", p["ceil"])):
        bpy.data.objects[nm].hide_render = not vis
    target = (0, 0, HEAD_Z - 0.1)
    for nm, key in (("Licht_Key", "key"), ("Licht_Fill", "fill"), ("Licht_Rim", "rim")):
        col, en, loc, sx, sy = p[key]
        ob = area(nm, loc, target, sx, sy)
        ob.data.color = hex_col(col)[:3]
        ob.data.energy = en


def statisten(on):
    """Zwei unscharfe Mit-Puppen im Hintergrund (nutzen dasselbe Mesh)."""
    src = bpy.data.objects["Puppe_Erwachsen"]
    for nm, loc, rz, aus in (("Stat_L", (-0.62, 1.05, -0.06), math.radians(10), 1), ("Stat_R", (0.66, 0.75, -0.02), math.radians(-14), 2)):
        ob = bpy.data.objects.get(nm)
        if not ob:
            ob = bpy.data.objects.new(nm, src.data)
            col_set().objects.link(ob)
            for k in ("ausdruck", "mund", "brauen", "glanz"):
                ob[k] = 0
            ob["ausdruck"] = aus
        ob.location, ob.rotation_euler = loc, (0, 0, rz)
        ob.hide_render = not on
        ob.hide_viewport = not on


def camera(loc, target, lens, fstop=None, focus=None):
    scn = bpy.context.scene
    cd = bpy.data.cameras.get("Cam") or bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.get("Cam") or bpy.data.objects.new("Cam", cd)
    if cam.name not in col_set().objects:
        col_set().objects.link(cam)
    cd.lens = lens
    cd.sensor_fit = "AUTO"
    cd.sensor_width = 36
    cd.clip_start, cd.clip_end = 0.05, 40
    aim(cam, loc, target)
    cd.dof.use_dof = fstop is not None
    if fstop:
        cd.dof.aperture_fstop = fstop
        cd.dof.focus_distance = (Vector(loc) - Vector(focus or target)).length
    scn.camera = cam
    return cam


def only(*names):
    for ob in bpy.data.collections["Puppe"].objects:
        ob.hide_render = ob.name not in names


def face(ob, ausdruck=0, mund=0, brauen=0, glanz=0):
    ob["ausdruck"], ob["mund"], ob["brauen"], ob["glanz"] = ausdruck, mund, brauen, glanz
    ob.update_tag()


def render(path, w, h, samples=64):
    scn = bpy.context.scene
    scn.render.resolution_x, scn.render.resolution_y = w, h
    scn.render.resolution_percentage = 100
    scn.eevee.taa_render_samples = samples
    scn.render.filepath = path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.render.render(write_still=True)


EYE_POINT = (0.0, -0.145 * math.cos(math.radians(33)), HEAD_Z - 0.008)  # Tiefe der Augen auf der Kugel


def closeup_cam(fill, lens, fstop, yaw=0.0, pitch=0.0, res=(1080, 1920)):
    """Kamera für Groß-Gesicht: fill = Anteil Kopf-Ø an der Bildbreite."""
    sensor_w = 36.0 * res[0] / max(res)
    d = lens / 1000 * (0.29 / fill) / (sensor_w / 1000)
    y, p = math.radians(yaw), math.radians(pitch)
    tgt = Vector((0, 0, HEAD_Z - 0.035))
    loc = tgt + Vector((math.sin(y) * math.cos(p) * d, -math.cos(y) * math.cos(p) * d, math.sin(p) * d))
    focus = Vector(EYE_POINT)
    forward = (tgt - loc).normalized()
    focus_pt = loc + forward * ((focus - loc).dot(forward))
    return camera(tuple(loc), tuple(tgt), lens, fstop, tuple(focus_pt))
