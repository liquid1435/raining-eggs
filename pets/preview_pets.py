r"""Blender preview of pets.json: every block gets the stud texture (1 tile per stud, like Roblox Studs surfaces).
  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P preview_pets.py -- [zone|all]
-> renders\zone_N.png
"""
import bpy, bmesh, json, math, sys, pathlib
from mathutils import Vector, Euler, Matrix

HERE = pathlib.Path(__file__).resolve().parent
OUTD = HERE / 'renders'
OUTD.mkdir(exist_ok=True)
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PETS = json.loads((HERE / 'pets.json').read_text())
STUD = str(HERE.parent / 'blender' / 'tex' / 'stud.png')
MATS = {}


def mat(col, kind, alpha):
    key = (tuple(col), kind, round(alpha, 2))
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new('M')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    c = tuple((v / 255) ** 2.2 for v in col) + (1,)
    if kind == 'Neon':
        b.inputs['Base Color'].default_value = c
        b.inputs['Emission Color'].default_value = c
        b.inputs['Emission Strength'].default_value = 3.0
    else:
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = bpy.data.images.load(STUD, check_existing=True)
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        mix.inputs['A'].default_value = c
        nt.links.new(t.outputs['Color'], mix.inputs['B'])
        br = nt.nodes.new('ShaderNodeBrightContrast')
        br.inputs['Bright'].default_value = 0.0
        nt.links.new(mix.outputs['Result'], br.inputs['Color'])
        nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.25 if kind in ('Metal', 'Foil', 'DiamondPlate', 'Glass') else 0.55
        b.inputs['Metallic'].default_value = 0.6 if kind in ('Metal', 'Foil', 'DiamondPlate') else 0.0
    if alpha > 0:
        b.inputs['Alpha'].default_value = 1 - alpha
        m.surface_render_method = 'BLENDED'
    MATS[key] = m
    return m


def block(q, origin):
    sx, sy, sz = q['s']
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sz, v.co.z * sy))      # Roblox (x, y up, z) -> Blender (x, z, y)
    uvl = bm.loops.layers.uv.new()
    for f in bm.faces:
        n = f.normal
        for lp in f.loops:
            co = lp.vert.co
            if abs(n.x) > 0.5:
                u, w = co.y, co.z
            elif abs(n.y) > 0.5:
                u, w = co.x, co.z
            else:
                u, w = co.x, co.y
            lp[uvl].uv = (u + 0.5, w + 0.5)
    me = bpy.data.meshes.new('b')
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new('b', me)
    rx, ry, rz = [math.radians(a) for a in q['r']]
    # Roblox CFrame.Angles(rx, ry, rz) = X then Y then Z (applied as Rx*Ry*Rz); convert axes: Roblox y->Blender z, z->-y
    R = Euler((rx, ry, rz), 'XYZ').to_matrix()
    conv = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
    o.matrix_world = Matrix.Translation(Vector((origin[0] + q['p'][0], origin[1] - q['p'][2], q['p'][1]))) @ (conv @ R @ conv.inverted()).to_4x4()
    me.materials.append(mat(q['c'], q['m'], q['a']))
    bpy.context.scene.collection.objects.link(o)
    return o


def stage():
    MATS.clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.eevee.taa_render_samples = 32
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('W')
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.5, 0.75, 1.0, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
    sun.data.energy = 2.3
    sun.rotation_euler = (math.radians(50), math.radians(8), math.radians(-35))
    sc.collection.objects.link(sun)
    bpy.ops.mesh.primitive_plane_add(size=2000)
    g = bpy.context.object
    gm = bpy.data.materials.new('G')
    gm.use_nodes = True
    gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.2, 0.55, 0.12, 1)
    g.data.materials.append(gm)
    sc.use_nodes = True
    cn = sc.node_tree
    gl = cn.nodes.new('CompositorNodeGlare')
    gl.glare_type = 'FOG_GLOW'
    gl.threshold = 1.0
    gl.size = 7
    cn.links.new(cn.nodes['Render Layers'].outputs['Image'], gl.inputs['Image'])
    cn.links.new(gl.outputs['Image'], cn.nodes['Composite'].inputs['Image'])
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    cam.data.type = 'ORTHO'
    sc.collection.objects.link(cam)
    sc.camera = cam
    return sc, cam


YAW = 150
R_ = (math.cos(math.radians(YAW)), math.sin(math.radians(YAW)))


def render_zone(z):
    sc, cam = stage()
    pets = [p for p in PETS if p['zone'] == z]
    x = 0
    centers = []
    for p in pets:
        xs = [q['p'][0] + q['s'][0] / 2 for q in p['parts']] + [q['p'][0] - q['s'][0] / 2 for q in p['parts']]
        zs = [q['p'][2] for q in p['parts']]
        w = max(max(xs) - min(xs), (max(zs) - min(zs)) * 0.5) + 4
        c = x + w / 2
        org = (R_[0] * c, R_[1] * c)
        for q in p['parts']:
            block(q, org)
        centers.append(c)
        x += w
    mid = x / 2
    cam.rotation_euler = (math.radians(72), 0, math.radians(YAW))
    fwd = cam.rotation_euler.to_matrix() @ Vector((0, 0, -1))
    tgt = Vector((R_[0] * mid, R_[1] * mid, 11))
    cam.location = tgt - fwd * 200
    cam.data.ortho_scale = x * 1.02
    cam.data.clip_end = 1000
    sc.render.resolution_x, sc.render.resolution_y = 3000, 900
    sc.render.filepath = str(OUTD / f'zone_{z}.png')
    bpy.ops.render.render(write_still=True)
    json.dump({'centers': centers, 'width': x}, open(OUTD / f'zone_{z}.json', 'w'))


zones = range(1, 11) if (not args or args[0] == 'all') else [int(args[0])]
for z in zones:
    render_zone(z)
print('done')
