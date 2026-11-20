r"""Preview renders of map.json in Blender (Cycles GPU).

  E:\tools\blender-4.2.3-windows-x64\blender.exe -b --python render_map.py -- all|overview|walk|base|plaza|factory|side
-> renders\<view>.png
Roblox coords (Y up) -> Blender (Z up): (x, y, z) -> (x, -z, y).
"""
import json
import math
import pathlib
import sys

import bpy
from mathutils import Matrix, Vector

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'renders'
OUT.mkdir(exist_ok=True)
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['all']
FAST = '--fast' in args
args = [a for a in args if not a.startswith('--')]

P = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
PI = P.inverted()


def tob(v):
    return Vector((v[0], -v[2], v[1]))


# ---------------------------------------------------------------- scene setup
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'CUDA'
prefs.get_devices()
for d in prefs.devices:
    d.use = True
sc.cycles.device = 'GPU'
sc.cycles.samples = 24 if FAST else 64
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4
sc.render.resolution_x, sc.render.resolution_y = (1280, 720) if FAST else (1920, 1080)
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'Medium High Contrast'
sc.view_settings.exposure = -1.85

world = bpy.data.worlds.new('W')
sc.world = world
world.use_nodes = True
nt = world.node_tree
nt.nodes.clear()
sky = nt.nodes.new('ShaderNodeTexSky')
sky.sky_type = 'NISHITA'
sky.sun_elevation = math.radians(48)
sky.sun_rotation = math.radians(200)
sky.altitude = 200
sky.air_density = 1.2
sky.dust_density = 0.1
bg = nt.nodes.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = 0.22
out = nt.nodes.new('ShaderNodeOutputWorld')
nt.links.new(sky.outputs[0], bg.inputs[0])
nt.links.new(bg.outputs[0], out.inputs[0])
sun = bpy.data.lights.new('Sun', 'SUN')
sun.energy = 3.0
sun.angle = math.radians(2.5)
sun.color = (1.0, 0.96, 0.9)
so = bpy.data.objects.new('Sun', sun)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(42), 0, math.radians(200 - 180 + 25))
# volumetric-free haze: mist pass is overkill; use a light world strength + AgX

# ---------------------------------------------------------------- shared meshes
def make_mesh(kind):
    import bmesh
    me = bpy.data.meshes.new(kind)
    bm = bmesh.new()
    if kind == 'Block':
        bmesh.ops.create_cube(bm, size=1.0)
    elif kind == 'Ball':
        bmesh.ops.create_uvsphere(bm, u_segments=28, v_segments=16, radius=0.5)
        for f in bm.faces:
            f.smooth = True
    else:  # Cylinder along local X (Roblox), before the axis swap
        bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.5, radius2=0.5, depth=1.0)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'Y'))
        for f in bm.faces:
            if abs(f.normal.x) < 0.5:
                f.smooth = True
    bm.to_mesh(me)
    bm.free()
    return me


MESH = {k: make_mesh(k) for k in ('Block', 'Ball', 'Cylinder')}
for _m in MESH.values():
    _m.materials.append(None)          # one slot, filled per object (link = OBJECT)
# the mesh is authored in Roblox-local axes (x, y, z) -> we bake the axis swap into the object matrix

MATS = {}


def srgb(c):
    def f(v):
        v = v / 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1)


def material(col, m, tr):
    key = (tuple(col), m, round(tr, 2))
    if key in MATS:
        return MATS[key]
    mat = bpy.data.materials.new(f'{m}_{col}')
    mat.use_nodes = True
    n = mat.node_tree.nodes
    bsdf = n['Principled BSDF']
    c = srgb(col)
    bsdf.inputs['Base Color'].default_value = c
    rough, metal = 0.4, 0.0
    if m == 'Neon':
        bsdf.inputs['Emission Color'].default_value = c
        bsdf.inputs['Emission Strength'].default_value = 5.0
        rough = 0.5
    elif m in ('Metal', 'DiamondPlate'):
        rough, metal = 0.32, 0.45
    elif m == 'Foil':
        rough, metal = 0.18, 0.9
    elif m == 'Glass':
        rough = 0.04
        bsdf.inputs['Transmission Weight'].default_value = 0.9
        bsdf.inputs['IOR'].default_value = 1.2
    elif m in ('Grass', 'Fabric', 'Rock', 'Concrete', 'Pavement', 'Sand', 'Slate'):
        rough = 0.92
        # subtle colour variation
        noise = n.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 0.6 if m == 'Grass' else 3.0
        mix = n.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 0.22 if m == 'Grass' else 0.12
        mix.inputs[6].default_value = c
        mat.node_tree.links.new(noise.outputs['Color'], mix.inputs[7])
        mat.node_tree.links.new(mix.outputs[2], bsdf.inputs['Base Color'])
    elif m in ('Wood', 'WoodPlanks'):
        rough = 0.7
    elif m == 'Marble':
        rough = 0.2
    elif m == 'SmoothPlastic':
        rough = 0.3
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if tr > 0:
        bsdf.inputs['Alpha'].default_value = max(0.0, 1 - tr)
        mat.blend_method = 'BLEND'
    MATS[key] = mat
    return mat


def obj_matrix(p):
    r = Matrix((p['r'][0:3], p['r'][3:6], p['r'][6:9]))
    rb = P @ r                       # roblox-local axes -> world (blender)
    m = rb.to_4x4()
    m = m @ Matrix.Diagonal((p['size'][0], p['size'][1], p['size'][2], 1))
    m.translation = tob(p['p'])
    return m


data = json.loads((HERE / 'map.json').read_text(encoding='utf-8'))
col = bpy.data.collections.new('Map')
sc.collection.children.link(col)
FONT = None
for fp in (r'C:\Windows\Fonts\ariblk.ttf', r'C:\Windows\Fonts\arialbd.ttf'):
    if pathlib.Path(fp).exists():
        FONT = bpy.data.fonts.load(fp)
        break

FACES = {'Front': (0, 0, -1), 'Back': (0, 0, 1), 'Right': (1, 0, 0), 'Left': (-1, 0, 0), 'Top': (0, 1, 0)}


def add_sign(p, s):
    r = Matrix((p['r'][0:3], p['r'][3:6], p['r'][6:9]))
    nl = Vector(FACES[s['face']])
    sx, sy, sz = p['size']
    if s['face'] in ('Front', 'Back'):
        w, h = sx, sy
    else:
        w, h = sz, sy
    up_l = Vector((0, 1, 0))
    right_l = up_l.cross(nl)
    center_l = Vector((nl.x * sx / 2, nl.y * sy / 2, nl.z * sz / 2)) * 1.0 + nl * 0.04
    # basis in roblox world, then to blender
    R3 = Matrix((right_l, up_l, nl)).transposed()          # columns = right, up, normal (local)
    W3 = P @ r @ R3
    base = W3.to_4x4()
    base.translation = tob(p['p']) + (P @ r) @ center_l
    # background plane
    me = bpy.data.meshes.new('signbg')
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new('signbg', me)
    ob.matrix_world = base
    mat = bpy.data.materials.new('signbg')
    mat.use_nodes = True
    b = mat.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb(s['bg1'])
    b.inputs['Emission Color'].default_value = srgb(s['bg1'])
    b.inputs['Emission Strength'].default_value = 0.6
    me.materials.append(mat)
    col.objects.link(ob)
    # border (stroke)
    for (bx, by, bw, bh) in ((0, h / 2 - 0.08 * h / 2, w, 0.08 * h), (0, -h / 2 + 0.08 * h / 2, w, 0.08 * h),
                             (-w / 2 + 0.04 * h, 0, 0.08 * h, h), (w / 2 - 0.04 * h, 0, 0.08 * h, h)):
        me2 = bpy.data.meshes.new('stroke')
        me2.from_pydata([(bx - bw / 2, by - bh / 2, 0.01), (bx + bw / 2, by - bh / 2, 0.01), (bx + bw / 2, by + bh / 2, 0.01), (bx - bw / 2, by + bh / 2, 0.01)], [], [(0, 1, 2, 3)])
        o2 = bpy.data.objects.new('stroke', me2)
        o2.matrix_world = base
        me2.materials.append(material(s['stroke'], 'SmoothPlastic', 0))
        col.objects.link(o2)

    def text(body, cy, maxh, color):
        cu = bpy.data.curves.new('t', 'FONT')
        cu.body = body
        cu.align_x = 'CENTER'
        cu.align_y = 'CENTER'
        if FONT:
            cu.font = FONT
        cu.size = 1.0
        cu.extrude = 0.0
        to = bpy.data.objects.new('t', cu)
        col.objects.link(to)
        bpy.context.view_layer.update()
        dw, dh = max(to.dimensions.x, 0.01), max(to.dimensions.y, 0.01)
        k = min(w * 0.88 / dw, maxh / dh)
        to.matrix_world = base @ Matrix.Translation((0, cy, 0.03)) @ Matrix.Diagonal((k, k, k, 1))
        m = bpy.data.materials.new('txt')
        m.use_nodes = True
        bb = m.node_tree.nodes['Principled BSDF']
        bb.inputs['Base Color'].default_value = srgb(color)
        bb.inputs['Emission Color'].default_value = srgb(color)
        bb.inputs['Emission Strength'].default_value = 1.0
        cu.materials.append(m)
    if s.get('sub'):
        text(s['title'], h * 0.14, h * 0.5, s['fg'])
        text(s['sub'], -h * 0.3, h * 0.2, (230, 236, 250))
    else:
        text(s['title'], 0, h * 0.62, s['fg'])


n = 0
for p in data['parts']:
    if p.get('transparency', 0) >= 0.99:
        continue
    ob = bpy.data.objects.new('p', MESH[p['shape']])
    ob.matrix_world = obj_matrix(p)
    mat = material(p['c'], p['m'], p.get('transparency', 0))
    col.objects.link(ob)
    ob.material_slots[0].link = 'OBJECT'
    ob.material_slots[0].material = mat
    for s_ in p.get('signs', []):
        add_sign(p, s_)
    n += 1
print('objects', n)


# ---------------------------------------------------------------- dummy players for scale (blocky R6-like, 5 studs)
def dummy(x, z, yaw=0, shirt=(60, 120, 255), y0=0.0):
    parts = [((2, 2, 1), (0, 3, 0), shirt), ((1, 2, 1), (-0.5, 1, 0), (40, 50, 80)), ((1, 2, 1), (0.5, 1, 0), (40, 50, 80)),
             ((1, 2, 1), (-1.5, 3, 0), (255, 214, 160)), ((1, 2, 1), (1.5, 3, 0), (255, 214, 160)), ((1.2, 1.2, 1.2), (0, 4.6, 0), (255, 214, 160))]
    rr = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    for size, off, c in parts:
        ob = bpy.data.objects.new('dummy', MESH['Block'])
        o = rr @ Vector(off)
        r = [v for row in rr for v in row]
        ob.matrix_world = obj_matrix({'r': r, 'size': size, 'p': (x + o.x, y0 + o.y, z + o.z)})
        col.objects.link(ob)
        ob.material_slots[0].link = 'OBJECT'
        ob.material_slots[0].material = material(c, 'SmoothPlastic', 0)


for (x, z, yaw, c) in [(4, -40, 0, (255, 74, 74)), (-10, -34, 30, (72, 214, 96)), (-60, -86, 180, (255, 214, 40)),
                       (-24, -50, 90, (72, 124, 255)), (3, 30, 0, (162, 96, 255)), (-30, 60, 20, (255, 150, 40)),
                       (40, 190, 200, (40, 214, 232)), (-4, 200, 0, (255, 102, 190)), (30, 330, 0, (255, 74, 74)),
                       (-3, 470, 0, (72, 214, 96)), (36, 480, 40, (255, 214, 40)), (2, 610, 0, (72, 124, 255)),
                       (-40, 620, 0, (255, 150, 40)), (4, 750, 0, (162, 96, 255)), (-34, 770, 0, (40, 214, 232)),
                       (3, 880, 0, (255, 102, 190)), (-20, 890, 0, (255, 74, 74))]:
    dummy(x, z, yaw, c, 1.0 if z < -58 else 0.3)

# ---------------------------------------------------------------- cameras
VIEWS = {
    'overview': ((-660, 540, 430), (40, 0, 650), 20),
    'start': ((0, 120, -250), (0, 0, 60), 24),
    'bases': ((-6, 52, 4), (-56, 4, -86), 20),
    'base': ((-78, 26, -30), (-63, 4, -84), 20),
    'plaza': ((0, 26, -78), (0, 14, 30), 20),
    'shop': ((-40, 13, -50), (-54, 8, -16), 26),
    'z1_meadow': ((-46, 40, -30), (14, 8, 80), 20),
    'z2_mushroom': ((-46, 40, 112), (20, 10, 222), 20),
    'z3_candy': ((46, 40, 252), (-20, 10, 362), 20),
    'z4_crystal': ((46, 40, 392), (-16, 10, 502), 20),
    'z5_thunder': ((-46, 40, 532), (20, 12, 642), 20),
    'z6_cloud': ((40, 44, 664), (-16, 14, 782), 20),
    'z7_golden': ((-30, 44, 806), (4, 22, 930), 20),
}
for _k in [k for k in VIEWS if k.startswith('z')]:
    del VIEWS[_k]
for _i in range(10):
    _sx = -1 if _i % 2 == 0 else 1
    VIEWS[f'zone{_i + 1}'] = ((_sx * 64, 58, _i * 140 - 34), (-_sx * 18, 8, _i * 140 + 84), 19)
VIEWS['cosmic'] = ((-95, 960, 560), (0, 905, 720), 20)   # v116 Cosmic Nest island
VIEWS['cosmic2'] = ((0, 915, 640), (0, 915, 790), 24)
todo = list(VIEWS) if args == ['all'] else args
cam_data = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_data)
sc.collection.objects.link(cam)
sc.camera = cam
cam_data.clip_end = 3000
for v in todo:
    eye, tgt, lens = VIEWS[v]
    e, t = tob(eye), tob(tgt)
    cam.location = e
    cam.rotation_euler = (t - e).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = lens
    sc.render.filepath = str(OUT / f'{v}.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', v)
