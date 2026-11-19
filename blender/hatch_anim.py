r"""Hatch animation preview (concept for the game): egg drops, wobbles, light leaks through a zigzag crack,
the shell bursts, the pet pops out with squash & stretch and a spin.
  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P hatch_anim.py -- [frame]   (frame = single test frame)
Frames -> out\hatch\####.png ; text overlay + video: hatch_video.py
"""
import bpy, bmesh, math, sys, random, pathlib
from mathutils import Vector

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'out' / 'hatch'
OUT.mkdir(parents=True, exist_ok=True)
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
TEST = int(args[0]) if args else None
EGG, PET = 'Egg_1', 'Pet_1_5'
FPS, END = 30, 165
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.fbx(filepath=str(HERE / 'out' / 'RainingEggsAssets.fbx'))
objs = {o.name: o for o in bpy.data.objects}
for o in list(bpy.data.objects):
    if o.name not in (EGG, PET):
        bpy.data.objects.remove(o, do_unlink=True)
egg, pet = objs[EGG], objs[PET]


def vcol_mat(name, rough=0.42, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough
    if emit is None:
        a = nt.nodes.new('ShaderNodeVertexColor')
        nt.links.new(a.outputs['Color'], b.inputs['Base Color'])
    return m


def flat_mat(name, col, emit=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Emission Color'].default_value = (*col, 1)
    b.inputs['Emission Strength'].default_value = emit
    b.inputs['Roughness'].default_value = 0.5
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        m.surface_render_method = 'BLENDED'
    return m


for o in (egg, pet):
    o.data.materials.clear()
    o.data.materials.append(vcol_mat(o.name + '_M'))
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    o.select_set(False)


def ground_it(o, height):
    """scale to a height, put the bottom centre at the origin"""
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    h = max(v.z for v in bb) - min(v.z for v in bb)
    k = height / h
    o.scale = (k, k, k)
    bpy.context.view_layer.update()
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    cx = sum(v.x for v in bb) / 8
    cy = sum(v.y for v in bb) / 8
    o.location -= Vector((cx, cy, min(v.z for v in bb)))
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
    o.select_set(False)


ground_it(egg, 3.0)
ground_it(pet, 2.6)
pet.rotation_euler = (0, 0, math.radians(180))   # face the camera (-Y)
bpy.context.view_layer.objects.active = pet
pet.select_set(True)
bpy.ops.object.transform_apply(rotation=True)
pet.select_set(False)

# ---------------------------------------------------------------- crack the egg: zigzag cutter -> top + bottom shell
INNER = flat_mat('ShellInside', (1.0, 0.96, 0.86), emit=0.6)
H0, AMP, TEETH = 1.62, 0.2, 9


def split_egg():
    """split the egg surface by faces along a zigzag line -> two open shells with a jagged edge"""
    bpy.context.view_layer.objects.active = egg
    egg.select_set(True)
    m = egg.modifiers.new('Sub', 'SUBSURF')
    m.subdivision_type = 'SIMPLE'
    m.levels = m.render_levels = 2
    bpy.ops.object.modifier_apply(modifier='Sub')
    egg.select_set(False)

    def zline(x, y):
        a = math.atan2(y, x) % (2 * math.pi)
        u = (a / (2 * math.pi) * TEETH * 2) % 2           # 0..2 per tooth
        tri = u if u < 1 else 2 - u                       # 0..1..0 zigzag
        return H0 - AMP + 2 * AMP * tri

    parts = {}
    for name, keep_top in (('ShellTop', True), ('ShellBot', False)):
        o = egg.copy()
        o.data = egg.data.copy()
        o.name = name
        sc.collection.objects.link(o)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        kill = [f for f in bm.faces if (f.calc_center_median().z > zline(*f.calc_center_median().xy)) != keep_top]
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        bm.to_mesh(o.data)
        bm.free()
        parts[name] = o
    return parts['ShellTop'], parts['ShellBot']


top, bot = split_egg()
bpy.data.objects.remove(egg, do_unlink=True)

# pivots: top piece turns around its crack edge, bottom around its base
for o, p in ((top, (0, -1.0, H0)), (bot, (0, 0, 0))):
    sc.cursor.location = p
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    o.select_set(False)

# everything that moves with the egg hangs on one empty
rig = bpy.data.objects.new('EggRig', None)
sc.collection.objects.link(rig)
for o in (top, bot):
    o.parent = rig

# light inside the egg (seen through the crack)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.95, location=(0, 0, H0), segments=24, ring_count=12)
core = bpy.context.object
core.name = 'Core'
core.scale = (1, 1, 1.15)
CORE_M = flat_mat('CoreM', (1.0, 0.85, 0.35), emit=0.0)
core.data.materials.append(CORE_M)
core.parent = rig

# ---------------------------------------------------------------- stage
WORLD = bpy.data.worlds.new('W')
sc.world = WORLD
WORLD.use_nodes = True
WORLD.node_tree.nodes['Background'].inputs[0].default_value = (0.05, 0.03, 0.12, 1)
WORLD.node_tree.nodes['Background'].inputs[1].default_value = 1.0

# backdrop: big plane with a soft radial glow
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 14, 6), rotation=(math.radians(90), 0, 0))
back = bpy.context.object
bm_ = bpy.data.materials.new('Back')
bm_.use_nodes = True
nt = bm_.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
outn = nt.nodes.new('ShaderNodeOutputMaterial')
em = nt.nodes.new('ShaderNodeEmission')
tc = nt.nodes.new('ShaderNodeTexCoord')
mp = nt.nodes.new('ShaderNodeMapping')
mp.inputs['Location'].default_value = (-0.5, -0.5, 0)
gr = nt.nodes.new('ShaderNodeTexGradient')
gr.gradient_type = 'SPHERICAL'
mp.inputs['Scale'].default_value = (1.6, 1.6, 1)
ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = (0.04, 0.02, 0.10, 1)
ramp.color_ramp.elements[1].position = 0.75
ramp.color_ramp.elements[1].color = (0.45, 0.22, 0.85, 1)
nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
nt.links.new(mp.outputs['Vector'], gr.inputs['Vector'])
nt.links.new(gr.outputs['Fac'], ramp.inputs['Fac'])
nt.links.new(ramp.outputs['Color'], em.inputs['Color'])
em.inputs['Strength'].default_value = 1.0
nt.links.new(em.outputs['Emission'], outn.inputs['Surface'])
back.data.materials.append(bm_)
BACK_STRENGTH = em.inputs['Strength']

# round pedestal
bpy.ops.mesh.primitive_cylinder_add(radius=2.6, depth=0.5, location=(0, 0, -0.25), vertices=48)
ped = bpy.context.object
ped.data.materials.append(flat_mat('Ped', (0.36, 0.22, 0.7)))
bpy.ops.mesh.primitive_torus_add(major_radius=2.6, minor_radius=0.09, location=(0, 0, 0.0))
ring = bpy.context.object
ring.data.materials.append(flat_mat('Ring', (1.0, 0.82, 0.3), emit=6))

# light rays: a fan of thin triangles behind the egg
bm = bmesh.new()
for i in range(14):
    a = 2 * math.pi * i / 14
    w = 0.045
    v0 = bm.verts.new((0, 0, 0))
    v1 = bm.verts.new((9 * math.cos(a - w), 0, 9 * math.sin(a - w)))
    v2 = bm.verts.new((9 * math.cos(a + w), 0, 9 * math.sin(a + w)))
    bm.faces.new((v0, v1, v2))
rme = bpy.data.meshes.new('Rays')
bm.to_mesh(rme)
rays = bpy.data.objects.new('Rays', rme)
sc.collection.objects.link(rays)
rays.location = (0, 2.5, 2.4)
RAY_M = flat_mat('RayM', (1.0, 0.86, 0.45), emit=2, alpha=0.16)
rme.materials.append(RAY_M)
rays.scale = (0, 0, 0)

# flash sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1.8), segments=24, ring_count=12)
flash = bpy.context.object
FLASH_M = flat_mat('FlashM', (1.0, 0.95, 0.8), emit=20, alpha=0.0)
flash.data.materials.append(FLASH_M)
flash.scale = (0.01, 0.01, 0.01)

# lights + camera
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
sun.data.energy = 4.2
sun.rotation_euler = (math.radians(55), math.radians(10), math.radians(-25))
sc.collection.objects.link(sun)
rim = bpy.data.objects.new('Rim', bpy.data.lights.new('Rim', 'AREA'))
rim.data.energy = 900
rim.data.size = 6
rim.data.color = (0.7, 0.6, 1.0)
rim.location = (0, 6, 6)
rim.rotation_euler = (math.radians(-130), 0, 0)
sc.collection.objects.link(rim)
fill = bpy.data.objects.new('Fill', bpy.data.lights.new('Fill', 'AREA'))
fill.data.energy = 500
fill.data.size = 8
fill.location = (-3, -9, 5)
fill.rotation_euler = (math.radians(60), 0, math.radians(-20))
sc.collection.objects.link(fill)
glow = bpy.data.objects.new('Glow', bpy.data.lights.new('Glow', 'POINT'))
glow.data.color = (1.0, 0.8, 0.4)
glow.data.energy = 0
glow.location = (0, -1.2, 2.0)
sc.collection.objects.link(glow)

cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
cam.data.lens = 50
sc.collection.objects.link(cam)
sc.camera = cam

# ---------------------------------------------------------------- animation helpers
def key(o, path, f, val):
    setattr(o, path, val) if not isinstance(val, (tuple, list)) else setattr(o, path, val)
    o.keyframe_insert(data_path=path, frame=f)


def lerp(a, b, t):
    return a + (b - a) * t


def ease_out(t):
    return 1 - (1 - t) ** 3


def back_out(t, s=2.2):
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def socket_key(sock, f, v):
    sock.default_value = v
    sock.keyframe_insert('default_value', frame=f)


P = lambda name: CORE_M.node_tree.nodes['Principled BSDF'].inputs[name]
F = lambda name: FLASH_M.node_tree.nodes['Principled BSDF'].inputs[name]
R = lambda name: RAY_M.node_tree.nodes['Principled BSDF'].inputs[name]

LAND, CRACK1, CRACK2, CRACK3, POP = 16, 46, 64, 80, 96

# chips that fly off at each crack
CHIP_M = flat_mat('Chip', (0.98, 0.95, 0.84))
SPOT_M = flat_mat('ChipSpot', (0.45, 0.75, 0.38))
chips = []


def chip_burst(f0, n, speed, life=24):
    for _ in range(n):
        bpy.ops.mesh.primitive_ico_sphere_add(radius=random.uniform(0.09, 0.2), subdivisions=1)
        c = bpy.context.object
        c.scale = (1, 1, 0.45)
        c.data.materials.append(random.choice((CHIP_M, CHIP_M, SPOT_M)))
        a = random.uniform(0, 2 * math.pi)
        vx, vy, vz = math.cos(a) * speed, math.sin(a) * speed * 0.6 - 0.4 * speed, random.uniform(2.5, 5.0)
        x0, y0, z0 = math.cos(a) * 1.05, math.sin(a) * 1.05, H0 + random.uniform(-0.15, 0.15)
        c.scale = (0, 0, 0)
        c.keyframe_insert('scale', frame=f0 - 1)
        for k in range(0, life + 1, 2):
            t = k / FPS
            c.location = (x0 + vx * t, y0 + vy * t, max(0.08, z0 + vz * t - 9.8 * t * t))
            c.rotation_euler = (t * 9, t * 7, t * 5)
            s = 1 if k < life - 6 else max(0, (life - k) / 6)
            c.scale = (s, s, s * 0.45)
            c.keyframe_insert('location', frame=f0 + k)
            c.keyframe_insert('rotation_euler', frame=f0 + k)
            c.keyframe_insert('scale', frame=f0 + k)
        chips.append(c)


# 1) drop in with a bounce + squash
for f in range(1, LAND + 12):
    if f <= LAND:
        t = f / LAND
        rig.location = (0, 0, 7 * (1 - t * t))
        rig.scale = (0.92, 0.92, 1.1)
    else:
        u = (f - LAND) / 11
        sq = math.exp(-u * 4) * math.cos(u * 9)
        rig.location = (0, 0, max(0, 0.5 * math.sin(u * math.pi) * math.exp(-u * 3)))
        rig.scale = (1 + 0.16 * sq, 1 + 0.16 * sq, 1 - 0.24 * sq)
    rig.keyframe_insert('location', frame=f)
    rig.keyframe_insert('scale', frame=f)

# 2) wobble, harder and faster, with jolts at each crack
for f in range(LAND + 12, POP):
    u = (f - LAND - 12) / (POP - LAND - 12)
    amp = math.radians(4 + 16 * u * u)
    w = 0.35 + 0.55 * u
    rig.rotation_euler = (0, amp * math.sin(f * w), amp * 0.35 * math.sin(f * w * 1.7))
    j = 0
    for cf in (CRACK1, CRACK2, CRACK3):
        if 0 <= f - cf < 6:
            j = math.sin((f - cf) / 6 * math.pi) * 0.12
    pre = max(0, (f - (POP - 10)) / 10)           # anticipation squash just before the pop
    rig.scale = (1 + j + 0.12 * pre, 1 + j + 0.12 * pre, 1 - j * 1.4 - 0.2 * pre)
    rig.location = (0, 0, j * 1.2)
    rig.keyframe_insert('rotation_euler', frame=f)
    rig.keyframe_insert('scale', frame=f)
    rig.keyframe_insert('location', frame=f)

# the crack opens in steps: top shell lifts a little, light leaks out
gap = {LAND + 12: 0.0, CRACK1: 0.0, CRACK1 + 2: 0.035, CRACK2: 0.035, CRACK2 + 2: 0.075, CRACK3: 0.075, CRACK3 + 2: 0.12, POP - 2: 0.14}
for f, g in gap.items():
    top.location = (0, -1.0, H0 + g)
    top.rotation_euler = (math.radians(-g * 40), 0, 0)
    top.keyframe_insert('location', frame=f)
    top.keyframe_insert('rotation_euler', frame=f)
for f, e in ((1, 0), (CRACK1, 0), (CRACK1 + 2, 6), (CRACK2 + 2, 14), (CRACK3 + 2, 26), (POP - 1, 45)):
    socket_key(P('Emission Strength'), f, e)
    glow.data.energy = e * 40
    glow.data.keyframe_insert('energy', frame=f)
for cf, n in ((CRACK1, 4), (CRACK2, 6), (CRACK3, 8)):
    chip_burst(cf + 1, n, 2.2)

# 3) POP: top flies away spinning, bottom drops and shrinks, flash + rays + chips
for k in range(0, 40):
    f = POP + k
    t = k / FPS
    top.location = (3.2 * t * 3, -1.0 + 6 * t, H0 + 0.14 + 11 * t - 9.8 * t * t)   # up, to the side and away from the camera
    top.rotation_euler = (math.radians(-6 - 420 * t), math.radians(180 * t), 0)
    s = max(0, 1 - max(0, k - 18) / 14)
    top.scale = (s, s, s)
    top.keyframe_insert('location', frame=f)
    top.keyframe_insert('rotation_euler', frame=f)
    top.keyframe_insert('scale', frame=f)
for f, s in ((POP, 1.0), (POP + 3, 1.08), (POP + 14, 0.0)):
    bot.scale = (s, s, s * (0.7 if f == POP + 3 else 1))
    bot.keyframe_insert('scale', frame=f)
rig.rotation_euler = (0, 0, 0)
rig.scale = (1, 1, 1)
rig.location = (0, 0, 0)
for p in ('rotation_euler', 'scale', 'location'):
    rig.keyframe_insert(p, frame=POP)
socket_key(P('Emission Strength'), POP + 4, 0)
core.scale = (1, 1, 1.15)
core.keyframe_insert('scale', frame=POP + 1)
core.scale = (0, 0, 0)
core.keyframe_insert('scale', frame=POP + 5)
glow.data.energy = 3000
glow.data.keyframe_insert('energy', frame=POP + 1)
glow.data.energy = 300
glow.data.keyframe_insert('energy', frame=POP + 25)
chip_burst(POP + 1, 18, 4.0, life=30)

for f, s, a in ((POP - 1, 0.01, 0.0), (POP + 1, 1.1, 0.6), (POP + 3, 1.7, 0.25), (POP + 6, 2.1, 0.0)):
    flash.scale = (s, s, s)
    flash.keyframe_insert('scale', frame=f)
    socket_key(F('Alpha'), f, a)
for f, s in ((POP, 0.0), (POP + 8, 1.15), (POP + 14, 1.0)):
    rays.scale = (s, s, s)
    rays.keyframe_insert('scale', frame=f)
for f in range(POP, END + 1, 5):
    rays.rotation_euler = (0, math.radians((f - POP) * 0.9), 0)
    rays.keyframe_insert('rotation_euler', frame=f)
socket_key(BACK_STRENGTH, POP - 1, 1.0)
socket_key(BACK_STRENGTH, POP + 2, 2.6)
socket_key(BACK_STRENGTH, POP + 20, 1.5)

# 4) the pet pops out: grows with overshoot, jumps and spins once, lands with a squash, then happy idle
pet.location = (0, 0, 0.6)
pet.scale = (0, 0, 0)
pet.keyframe_insert('scale', frame=POP)
pet.keyframe_insert('location', frame=POP)
for k in range(1, 26):
    f = POP + k
    u = k / 25
    s = back_out(min(1, k / 12), 2.6)
    hop = 1.5 * math.sin(min(1, k / 22) * math.pi)
    pet.location = (0, 0, 0.6 * (1 - u) + max(0, hop))
    pet.rotation_euler = (0, 0, math.radians(360 * ease_out(min(1, k / 22))))
    st = 1 + 0.18 * math.sin(min(1, k / 12) * math.pi)          # stretch while flying up
    pet.scale = (s / math.sqrt(st), s / math.sqrt(st), s * st)
    for p in ('location', 'rotation_euler', 'scale'):
        pet.keyframe_insert(p, frame=f)
LANDP = POP + 26
for k, (sx, sz) in enumerate(((1.22, 0.74), (0.92, 1.1), (1.05, 0.95), (1.0, 1.0))):
    pet.scale = (sx, sx, sz)
    pet.location = (0, 0, 0)
    pet.keyframe_insert('scale', frame=LANDP + k * 3)
    pet.keyframe_insert('location', frame=LANDP + k * 3)
for f in range(LANDP + 12, END + 1):
    t = (f - LANDP - 12) / FPS
    b = abs(math.sin(t * 5.2))
    pet.location = (0, 0, 0.35 * b)
    pet.rotation_euler = (0, math.radians(5 * math.sin(t * 5.2)), math.radians(14 * math.sin(t * 1.6)))
    sq = 1 - 0.07 * (1 - b)
    pet.scale = (2 - sq, 2 - sq, sq)
    for p in ('location', 'rotation_euler', 'scale'):
        pet.keyframe_insert(p, frame=f)

# sparkles: little stars that burst out and twinkle
bm = bmesh.new()
pts = []
for i in range(8):
    a = math.pi * i / 4
    r = 1.0 if i % 2 == 0 else 0.28
    pts.append(bm.verts.new((r * math.cos(a), 0, r * math.sin(a))))
bm.faces.new(pts)
sme = bpy.data.meshes.new('Star')
bm.to_mesh(sme)
STAR_M = flat_mat('StarM', (1.0, 0.95, 0.6), emit=12)
sme.materials.append(STAR_M)
for i in range(14):
    s = bpy.data.objects.new('Star', sme)
    sc.collection.objects.link(s)
    a = 2 * math.pi * i / 14 + random.uniform(-0.2, 0.2)
    d = random.uniform(2.4, 4.2)
    z0 = 2.0
    size = random.uniform(0.14, 0.32)
    s.scale = (0, 0, 0)
    s.keyframe_insert('scale', frame=POP)
    for k in range(0, END - POP + 1, 3):
        f = POP + k
        u = ease_out(min(1, k / 20))
        s.location = (math.cos(a) * d * u, -1.0, z0 + math.sin(a) * d * u * 0.75)
        tw = 0.6 + 0.4 * math.sin(k * 0.5 + i)
        fade = 1 if k < 40 else max(0, 1 - (k - 40) / 25)
        sz = size * tw * fade * min(1, k / 4)
        s.scale = (sz, sz, sz)
        s.rotation_euler = (0, math.radians(k * 6), 0)
        for p in ('location', 'scale', 'rotation_euler'):
            s.keyframe_insert(p, frame=f)

# camera: slow push in, a little shake on the pop
for f in range(1, END + 1):
    u = f / END
    shake = 0.0
    if POP <= f < POP + 10:
        shake = 0.08 * (1 - (f - POP) / 10)
    late = ease_out(max(0, (f - POP) / (END - POP)))     # after the pop: move in on the pet
    cam.location = (random.uniform(-shake, shake), -17.5 + 2.0 * ease_out(min(1, f / POP)) + 2.5 * late, 2.9 + random.uniform(-shake, shake))
    cam.keyframe_insert('location', frame=f)
cam.rotation_euler = (math.radians(82), 0, 0)

# ---------------------------------------------------------------- render
sc.frame_start, sc.frame_end = 1, END
sc.render.fps = FPS
sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.eevee.taa_render_samples = 32
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.view_settings.view_transform = 'Standard'
sc.view_settings.exposure = -0.15
sc.render.image_settings.file_format = 'PNG'
sc.use_nodes = True
cn = sc.node_tree
rl = cn.nodes['Render Layers']
comp = cn.nodes['Composite']
glare = cn.nodes.new('CompositorNodeGlare')
glare.glare_type = 'FOG_GLOW'
glare.quality = 'HIGH'
glare.threshold = 0.9
glare.size = 8
cn.links.new(rl.outputs['Image'], glare.inputs['Image'])
cn.links.new(glare.outputs['Image'], comp.inputs['Image'])

if TEST:
    sc.frame_set(TEST)
    sc.render.filepath = str(OUT / f'test_{TEST:04d}.png')
    bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath = str(OUT / '')
    bpy.ops.render.render(animation=True)
print('done')
