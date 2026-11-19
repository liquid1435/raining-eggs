"""Blocky Sun Lion after the Gemini reference (meshy/p001_sun_lion.jpg), v2.
  E:\\tools\\blender-4.2.3-windows-x64\\blender.exe -b -P lion_block.py  -> out/lion_block_a.png, out/lion_block_b.png, out/SunLion.fbx
Head faces +X."""
import bpy, math, os, random
from mathutils import Vector, Matrix

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
random.seed(11)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def rgb(c):  # sRGB 0-255 -> linear (what Blender colour sockets expect)
    def lin(v):
        v = v / 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(lin(x) for x in c) + (1,)

MATS = {}
BRICK = bpy.data.images.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tex", "brick.png"))
BRICK.colorspace_settings.name = "Non-Color"
def mat(name, col, emit=0.0, rough=0.6, pixel=None, brick=True):
    """pixel = second colour: object-space voxel grid of random shades between col and pixel (the 'pixel art' skin)"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    b.inputs["Base Color"].default_value = rgb(col)
    if pixel:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sn = nt.nodes.new("ShaderNodeVectorMath")
        sn.operation = "SNAP"
        sn.inputs[1].default_value = (0.11, 0.11, 0.11)
        wn = nt.nodes.new("ShaderNodeTexWhiteNoise")
        wn.noise_dimensions = "3D"
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.interpolation = "CONSTANT"
        e = ramp.color_ramp.elements
        e[0].color = rgb(col)
        e[1].position = 0.62
        e[1].color = rgb(pixel)
        nt.links.new(tc.outputs["Object"], sn.inputs[0])
        nt.links.new(sn.outputs["Vector"], wn.inputs["Vector"])
        nt.links.new(wn.outputs["Value"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    if brick:  # LEGO bricks with studs on every side (box projection in object space), multiplied with the colour
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1.3, 1.3, 1.3)
        tx = nt.nodes.new("ShaderNodeTexImage")
        tx.image = BRICK
        tx.projection = "BOX"
        tx.projection_blend = 0.15
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
        src = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].is_linked else None
        if src:
            nt.links.new(src, mul.inputs[6])
        else:
            mul.inputs[6].default_value = rgb(col)
        bright = nt.nodes.new("ShaderNodeMath")
        bright.operation = "MULTIPLY"
        bright.inputs[1].default_value = 1.2
        nt.links.new(tx.outputs["Color"], bright.inputs[0])
        nt.links.new(bright.outputs[0], mul.inputs[7])
        nt.links.new(mul.outputs[2], b.inputs["Base Color"])
    if emit:
        b.inputs["Emission Color"].default_value = rgb(col)
        b.inputs["Emission Strength"].default_value = emit
    MATS[name] = m
    return m

GOLD = mat("Body", (240, 170, 36))
GOLD_D = mat("BodyDark", (220, 140, 24))
CREAM = mat("Cream", (252, 232, 180))
NOSE = mat("Nose", (60, 34, 30), rough=0.4, brick=False)
EYE = mat("Eye", (255, 255, 255), rough=0.2, brick=False)
PUPIL = mat("Pupil", (14, 12, 16), rough=0.2, brick=False)
WHITE = mat("Shine", (255, 255, 255), emit=1.0, brick=False)
INNER = mat("EarIn", (200, 112, 40))
MANE = [mat("Mane0", (255, 240, 120), 1.1, 0.25), mat("Mane1", (255, 210, 30), 0.8, 0.25),
        mat("Mane2", (255, 168, 10), 0.6, 0.3), mat("Mane3", (248, 122, 6), 0.45, 0.3), mat("Mane4", (226, 92, 4), 0.35, 0.35)]
TUFT = mat("Tuft", (176, 96, 34))
SPARK = mat("Spark", (255, 236, 110), 4.0, brick=False)

parts = []
def box(name, size, loc, m, bevel=0.05, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    if bevel:
        md = o.modifiers.new("bev", "BEVEL")
        md.width = bevel
        md.segments = 2
        md.limit_method = "ANGLE"
    parts.append(o)
    return o

def shard(name, base, length, origin, direction, m, flat=0.45, twist=0.0, dark=None):
    """faceted crystal blade from origin along direction (diamond cross-section, flattened)"""
    d = Vector(direction).normalized()
    up = Vector((1, 0, 0)) if abs(d.x) < 0.9 else Vector((0, 0, 1))
    s1 = d.cross(up).normalized()
    s2 = d.cross(s1).normalized()
    rot = Matrix.Rotation(twist, 3, d)
    s1, s2 = rot @ s1, rot @ s2
    o = Vector(origin)
    mid = o + d * length * 0.32
    v = [o - d * 0.15, mid + s1 * base, mid + s2 * base * flat, mid - s1 * base, mid - s2 * base * flat, o + d * length]
    f = [(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1), (5, 2, 1), (5, 3, 2), (5, 4, 3), (5, 1, 4)]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(x) for x in v], [], f)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(m)
    if dark:
        ob.data.materials.append(dark)
        for poly in ob.data.polygons:
            poly.material_index = 0 if 1 in poly.vertices else 1
    parts.append(ob)
    return ob

# ---------------- body (deep chest, slimmer waist, slightly lower hips)
box("Chest", (1.15, 1.15, 1.25), (0.75, 0, 2.05), GOLD, 0.1)
box("Ribs", (1.0, 1.02, 1.05), (-0.15, 0, 2.08), GOLD, 0.1)
box("Waist", (1.2, 0.9, 0.85), (-1.0, 0, 2.12), GOLD, 0.08)
box("Hips", (0.8, 1.0, 1.0), (-1.85, 0, 2.05), GOLD, 0.1)
box("BellyFront", (1.2, 0.8, 0.22), (0.45, 0, 1.43), CREAM, 0.05)
box("BellyBack", (1.0, 0.62, 0.16), (-0.6, 0, 1.66), CREAM, 0.04)
box("Spine", (2.8, 0.5, 0.1), (-0.6, 0, 2.6), GOLD_D, 0.03)
# legs: shoulder/thigh + leg + paw with toes
LEGS = [(0.85, 0.36, True), (0.85, -0.36, True), (-1.85, 0.38, False), (-1.85, -0.38, False)]
for i, (x, y, front) in enumerate(LEGS):
    if front:
        box(f"Shoulder{i}", (0.7, 0.42, 0.95), (x, y * 1.05, 1.75), GOLD, 0.07)
        box(f"Leg{i}", (0.5, 0.42, 1.15), (x + 0.05, y, 0.78), GOLD_D if y > 0 else GOLD, 0.05)
    else:
        box(f"Thigh{i}", (0.9, 0.44, 1.05), (x - 0.05, y, 1.7), GOLD, 0.08)
        box(f"Hock{i}", (0.48, 0.4, 0.7), (x - 0.15, y, 0.95), GOLD_D if y > 0 else GOLD, 0.05)
        box(f"Shin{i}", (0.44, 0.4, 0.55), (x - 0.05, y, 0.42), GOLD_D if y > 0 else GOLD, 0.05)
    px = x + (0.1 if front else 0.0)
    box(f"Paw{i}", (0.66, 0.5, 0.24), (px + 0.06, y, 0.11), GOLD, 0.06)
    for t in (-0.12, 0.0, 0.12):
        box(f"Toe{i}{t}", (0.04, 0.025, 0.12), (px + 0.4, y + t, 0.1), GOLD_D, 0)

# ---------------- head
HX, HZ = 1.6, 3.15
box("Neck", (0.8, 0.9, 1.0), (1.2, 0, 2.7), GOLD, 0.08)
box("Head", (1.1, 1.15, 1.1), (HX + 0.05, 0, HZ), GOLD, 0.1)
box("Brow", (0.3, 0.6, 0.2), (HX + 0.5, 0, HZ + 0.4), GOLD_D, 0.05)
box("Muzzle", (0.55, 0.62, 0.3), (HX + 0.63, 0, HZ - 0.08), GOLD, 0.08)
box("Jaw", (0.5, 0.56, 0.24), (HX + 0.6, 0, HZ - 0.32), CREAM, 0.07)
box("Bridge", (0.45, 0.32, 0.25), (HX + 0.55, 0, HZ + 0.12), GOLD, 0.06)
box("Chin", (0.42, 0.44, 0.2), (HX + 0.55, 0, HZ - 0.46), CREAM, 0.05)
box("Nose", (0.2, 0.3, 0.16), (HX + 0.9, 0, HZ + 0.03), NOSE, 0.05)
box("MouthV", (0.03, 0.035, 0.14), (HX + 0.905, 0, HZ - 0.13), NOSE, 0)
box("MouthL", (0.03, 0.2, 0.035), (HX + 0.905, 0.1, HZ - 0.22), NOSE, 0, rot=(-0.35, 0, 0))
box("MouthR", (0.03, 0.2, 0.035), (HX + 0.905, -0.1, HZ - 0.22), NOSE, 0, rot=(0.35, 0, 0))
for s in (1, -1):
    box(f"Eye{s}", (0.06, 0.34, 0.24), (HX + 0.62, 0.27 * s, HZ + 0.13), EYE, 0.03, rot=(-0.22 * s, 0, 0))
    box(f"Pupil{s}", (0.05, 0.15, 0.2), (HX + 0.645, 0.2 * s, HZ + 0.11), PUPIL, 0.02)
    box(f"EyeShine{s}", (0.02, 0.05, 0.05), (HX + 0.67, 0.18 * s, HZ + 0.16), EYE, 0)
    box(f"Ear{s}", (0.22, 0.26, 0.26), (HX - 0.05, 0.4 * s, HZ + 0.6), GOLD, 0.05)
    box(f"EarIn{s}", (0.04, 0.14, 0.16), (HX + 0.07, 0.4 * s, HZ + 0.58), INNER, 0)
    box(f"Cheek{s}", (0.4, 0.2, 0.3), (HX + 0.4, 0.5 * s, HZ - 0.22), GOLD_D, 0.05)

# ---------------- sun mane: big crystal sunburst around the head (5 layers, inner = light, outer = orange)
centre = Vector((HX - 0.05, 0, HZ - 0.02))
layers = [
    # count, radius, length, base, x offset, lean back, first colour
    (18, 0.72, 0.95, 0.42, -0.5, 0.22, 2),
    (18, 0.66, 0.85, 0.42, -0.32, 0.12, 1),
    (16, 0.62, 0.72, 0.38, -0.14, 0.04, 1),
    (15, 0.6, 0.58, 0.34, 0.04, -0.04, 0),
]
for li, (n, rad, length, base, dx, lean, c0) in enumerate(layers):
    off = random.random()
    for k in range(n):
        a = 2 * math.pi * (k + off) / n
        out = Vector((0, math.cos(a), math.sin(a)))
        if li >= 3 and math.sin(a) < -0.2 and abs(math.cos(a)) < 0.75:
            continue  # front layer: keep the muzzle and chin clear
        d = (out + Vector((-lean, 0, 0))).normalized()
        L = length * random.uniform(0.82, 1.15) * (0.75 if math.sin(a) < -0.6 else 1)
        ci = min(4, c0 + (1 if random.random() < 0.3 else 0))
        org = centre + Vector((dx, 0, 0)) + out * rad
        shard(f"Mane{li}_{k}", base, L, org, d, MANE[ci], flat=random.uniform(0.18, 0.3), twist=random.uniform(-0.3, 0.3), dark=MANE[min(4, ci + 1)])
# shards down the chest and over the shoulders
for row, (cx, cz, n, ln) in enumerate(((1.25, 2.55, 9, 1.0), (1.05, 2.15, 8, 0.85))):
    for k in range(n):
        a = math.pi * (1.05 + 0.9 * k / (n - 1))
        out = Vector((0.35, math.cos(a) * 1.2, math.sin(a)))
        ci = 1 + row + (k % 2)
        shard(f"Collar{row}_{k}", 0.4, ln * random.uniform(0.85, 1.1), Vector((cx, 0, cz)) + Vector((0, math.cos(a) * 0.55, math.sin(a) * 0.35)), out, MANE[ci], flat=0.22, dark=MANE[min(4, ci + 1)])

# ---------------- tail: thin blocks, down then up, crystal tuft
p = Vector((-2.25, 0, 2.45))
d = Vector((-0.75, 0, -0.66)).normalized()
for k in range(13):
    box(f"Tail{k}", (0.2, 0.18, 0.18), tuple(p), GOLD if k % 2 else GOLD_D, 0.03, rot=(0, -math.atan2(d.z, -d.x), 0))
    p = p + d * 0.2
    d = (d + Vector((-0.03, 0, 0.13 if k > 5 else -0.02))).normalized()
for k in range(8):
    a = 2 * math.pi * k / 8
    shard(f"Tuft{k}", 0.17, 0.55, tuple(p), d * 0.8 + Vector((0, math.cos(a), math.sin(a))), TUFT)

# ---------------- floating pixel sparkles around the mane
for k in range(16):
    a = random.uniform(0.1, math.pi - 0.1)
    r = random.uniform(2.0, 2.7)
    s = random.uniform(0.08, 0.16)
    box(f"Spark{k}", (s, s, s), (HX - 0.4 + random.uniform(-0.4, 0.4), math.cos(a) * r, HZ + math.sin(a) * r * 0.9), SPARK, 0)

# ---------------- render setup (bright, soft, high-key like the reference)
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.eevee.use_raytracing = True
sc.eevee.use_gtao = True
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 1200
sc.view_settings.view_transform = "Standard"
sc.view_settings.exposure = 0.0
world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (1.0, 1.0, 1.0, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.3
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(45), math.radians(15), math.radians(-40)))
bpy.context.object.data.energy = 3.2
bpy.context.object.data.angle = math.radians(12)
bpy.ops.object.light_add(type="AREA", location=(6, -5, 6))
L = bpy.context.object
L.data.energy = 110
L.data.size = 7
L.rotation_euler = (Vector((0, 0, 2)) - L.location).to_track_quat("-Z", "Y").to_euler()

sc.use_nodes = True
nt = sc.node_tree
rl, comp = nt.nodes["Render Layers"], nt.nodes["Composite"]
gl = nt.nodes.new("CompositorNodeGlare")
gl.glare_type = "FOG_GLOW"
gl.threshold = 0.85
gl.size = 9
nt.links.new(rl.outputs["Image"], gl.inputs["Image"])
nt.links.new(gl.outputs["Image"], comp.inputs["Image"])

bpy.ops.object.camera_add()
cam = bpy.context.object
sc.camera = cam
cam.data.lens = 72
target = Vector((-0.1, 0, 2.0))
for tag, pos in (("a", (9.6, -10.0, 4.4)), ("b", (3.0, -14.0, 3.8))):
    cam.location = pos
    cam.rotation_euler = (target - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, f"lion_block_{tag}.png")
    bpy.ops.render.render(write_still=True)

bpy.ops.object.select_all(action="DESELECT")
for o in parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.convert(target="MESH")
bpy.ops.object.join()
bpy.context.object.name = "Pet_SunLion"
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "SunLion.fbx"), use_selection=True, apply_scale_options="FBX_SCALE_ALL")
print("faces", len(bpy.context.object.data.polygons))

# ---------------- bake everything into ONE texture (Roblox MeshPart = 1 mesh + 1 TextureID)
ob = bpy.context.object
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004)
bpy.ops.object.mode_set(mode="OBJECT")
img = bpy.data.images.new("SunLion_tex", 1024, 1024)
for m in ob.data.materials:
    n = m.node_tree.nodes.new("ShaderNodeTexImage")
    n.image = img
    m.node_tree.nodes.active = n
sc.render.engine = "CYCLES"
sc.cycles.samples = 4
sc.cycles.device = "CPU"
sc.render.bake.use_pass_direct = False
sc.render.bake.use_pass_indirect = False
sc.render.bake.margin = 4
bpy.ops.object.bake(type="DIFFUSE")
img.filepath_raw = os.path.join(OUT, "SunLion_tex.png")
img.file_format = "PNG"
img.save()
# one plain material with the baked image
nm = bpy.data.materials.new("SunLion")
nm.use_nodes = True
b = nm.node_tree.nodes["Principled BSDF"]
b.inputs["Roughness"].default_value = 0.6
t = nm.node_tree.nodes.new("ShaderNodeTexImage")
t.image = img
t.interpolation = "Closest"
nm.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
ob.data.materials.clear()
ob.data.materials.append(nm)
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "SunLion.fbx"), use_selection=True, apply_scale_options="FBX_SCALE_ALL",
                         path_mode="COPY", embed_textures=True)
print("baked + exported")

# ---------------- Roblox-like preview: baseplate, sky, plain sun, no glow
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.film_transparent = False
sc.use_nodes = False
wn = world.node_tree
bg_light = wn.nodes["Background"]
bg_light.inputs[0].default_value = rgb((235, 238, 245))
bg_light.inputs[1].default_value = 0.8
bg_sky = wn.nodes.new("ShaderNodeBackground")
bg_sky.inputs[0].default_value = rgb((140, 195, 245))
lp = wn.nodes.new("ShaderNodeLightPath")
mx = wn.nodes.new("ShaderNodeMixShader")
wn.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0])
wn.links.new(bg_light.outputs[0], mx.inputs[1])
wn.links.new(bg_sky.outputs[0], mx.inputs[2])
wn.links.new(mx.outputs[0], wn.nodes["World Output"].inputs[0])
for o in list(bpy.data.objects):
    if o.type == "LIGHT" and o.data.type == "AREA":
        bpy.data.objects.remove(o)
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
bp = bpy.context.object
gm = bpy.data.materials.new("Baseplate")
gm.use_nodes = True
gn = gm.node_tree
gb = gn.nodes["Principled BSDF"]
chk = gn.nodes.new("ShaderNodeTexChecker")
chk.inputs["Scale"].default_value = 15
chk.inputs["Color1"].default_value = rgb((92, 160, 70))
chk.inputs["Color2"].default_value = rgb((86, 150, 64))
gn.links.new(chk.outputs["Color"], gb.inputs["Base Color"])
bp.data.materials.append(gm)
for tag, pos in (("roblox_a", (9.6, -10.0, 4.4)), ("roblox_b", (-6.0, -11.0, 5.0))):
    cam.location = pos
    cam.rotation_euler = (target - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, f"lion_{tag}.png")
    bpy.ops.render.render(write_still=True)
