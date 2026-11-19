r"""Example pet in the reference style: low-poly faceted shark + stud tiles on every face.
  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P lowpoly_shark.py
"""
import bpy, bmesh, math, pathlib, random
from mathutils import Vector

HERE = pathlib.Path(__file__).resolve().parent
random.seed(4)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

TOP, MID, BELLY, MOUTH, TOOTH, EYE = (0.10, 0.30, 0.85), (0.16, 0.42, 0.95), (0.78, 0.84, 0.92), (0.35, 0.05, 0.08), (0.95, 0.95, 0.95), (0.03, 0.03, 0.06)

bm = bmesh.new()
cl = bm.loops.layers.color.new('Col')
N = 8                                         # verts per cross-section (faceted look)
# (y along the body: -front .. +back, half width, half height, z centre)
SECT = [(-3.3, 0.0, 0.0, 0.55), (-3.0, 0.45, 0.42, 0.6), (-2.4, 0.85, 0.75, 0.7), (-1.5, 1.1, 0.95, 0.8),
        (-0.4, 1.15, 1.0, 0.85), (0.8, 0.95, 0.85, 0.85), (1.9, 0.62, 0.6, 0.85), (2.8, 0.32, 0.36, 0.88), (3.4, 0.18, 0.22, 0.9)]
rings = []
for y, w, h, zc in SECT:
    ring = []
    for i in range(N):
        a = 2 * math.pi * i / N + math.pi / N
        jx = 1 + random.uniform(-0.04, 0.04)
        x = math.cos(a) * w * jx
        z = zc + math.sin(a) * h * (0.85 if math.sin(a) < 0 else 1.0)
        ring.append(bm.verts.new((x, y, z)))
    rings.append(ring)
faces = []
for r0, r1 in zip(rings, rings[1:]):
    for i in range(N):
        j = (i + 1) % N
        faces.append(bm.faces.new((r0[i], r0[j], r1[j], r1[i])))
tip = rings[-1]
tc = bm.verts.new((0, 3.55, 0.92))
for i in range(N):
    faces.append(bm.faces.new((tip[i], tip[(i + 1) % N], tc)))
bmesh.ops.recalc_face_normals(bm, faces=faces)
bm.normal_update()


def colour_body(f):
    c = f.calc_center_median()
    n = f.normal
    y = c.y
    if y < -2.2 and n.z < -0.2:
        return MOUTH                                   # open mouth under the snout
    if n.z < -0.25:
        return BELLY
    if n.z > 0.55:
        return TOP
    return MID


def tri(p0, p1, p2, col, thick=0.08):
    """flat fin with a little thickness"""
    a = [bm.verts.new(p) for p in (p0, p1, p2)]
    nrm = (Vector(p1) - Vector(p0)).cross(Vector(p2) - Vector(p0)).normalized() * thick
    b = [bm.verts.new(Vector(p) + nrm) for p in (p0, p1, p2)]
    fs = [bm.faces.new(a), bm.faces.new((b[2], b[1], b[0]))]
    for i in range(3):
        j = (i + 1) % 3
        fs.append(bm.faces.new((a[i], a[j], b[j], b[i])))
    for f in fs:
        for lp in f.loops:
            lp[cl] = col + (1,)


for f in faces:
    for lp in f.loops:
        lp[cl] = colour_body(f) + (1,)
# fins
tri((0, -0.6, 1.75), (0, 0.7, 1.7), (0, 0.9, 3.0), TOP)                      # dorsal
tri((0, 2.2, 1.2), (0, 2.8, 1.15), (0, 2.85, 1.6), TOP)                      # second dorsal
for sx in (-1, 1):
    tri((sx * 0.95, -1.4, 0.35), (sx * 1.0, -0.4, 0.4), (sx * 2.4, 0.4, -0.35), MID)   # pectorals
tri((0, 3.3, 0.95), (0, 3.7, 0.9), (0, 4.6, 2.6), TOP)                       # tail, upper lobe
tri((0, 3.3, 0.85), (0, 3.7, 0.9), (0, 4.3, -0.4), MID)                      # tail, lower lobe
tri((0, 1.6, 0.2), (0, 2.3, 0.3), (0, 2.5, -0.25), MID)                      # anal fin
# teeth: little white wedges along the jaw line
for k in range(9):
    t = k / 8
    x = math.cos(math.pi * t) * 0.5
    y = -2.95 + math.sin(math.pi * t) * 0.5
    z = 0.36
    tri((x - 0.07, y, z), (x + 0.07, y, z), (x, y - 0.02, z - 0.2), TOOTH, 0.05)
# eyes: dark triangles on the sides of the head
for sx in (-1, 1):
    tri((sx * 0.86, -2.35, 0.95), (sx * 0.86, -2.0, 0.98), (sx * 0.84, -2.2, 0.82), EYE, 0.03)
    tri((sx * 0.88, -2.28, 0.95), (sx * 0.88, -2.18, 0.97), (sx * 0.87, -2.23, 0.91), TOOTH, 0.03)
# gills
for k in range(3):
    for sx in (-1, 1):
        tri((sx * 1.08, -1.35 + k * 0.22, 1.0), (sx * 1.08, -1.3 + k * 0.22, 1.0), (sx * 1.04, -1.4 + k * 0.22, 0.45), TOP, 0.02)

me = bpy.data.meshes.new('Shark')
bm.to_mesh(me)
bm.free()
shark = bpy.data.objects.new('Shark', me)
sc.collection.objects.link(shark)
for p in me.polygons:
    p.use_smooth = False

# material: vertex colour x square stud tiles (box projection)
img = bpy.data.images.load(str(HERE / 'tex' / 'stud.png'))
m = bpy.data.materials.new('SharkM')
m.use_nodes = True
nt = m.node_tree
b = nt.nodes['Principled BSDF']
vc = nt.nodes.new('ShaderNodeVertexColor')
vc.layer_name = 'Col'
tcn = nt.nodes.new('ShaderNodeTexCoord')
mp = nt.nodes.new('ShaderNodeMapping')
mp.inputs['Scale'].default_value = (4.5, 4.5, 4.5)
tx = nt.nodes.new('ShaderNodeTexImage')
tx.image = img
tx.projection = 'BOX'
tx.projection_blend = 0.0
nt.links.new(tcn.outputs['Object'], mp.inputs['Vector'])
nt.links.new(mp.outputs['Vector'], tx.inputs['Vector'])
mix = nt.nodes.new('ShaderNodeMix')
mix.data_type = 'RGBA'
mix.blend_type = 'MULTIPLY'
mix.inputs['Factor'].default_value = 1.0
nt.links.new(vc.outputs['Color'], mix.inputs['A'])
nt.links.new(tx.outputs['Color'], mix.inputs['B'])
nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
b.inputs['Roughness'].default_value = 0.5
me.materials.append(m)
shark.location = (0, 0, 0.6)

# stage
sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.eevee.taa_render_samples = 64
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('W')
sc.world = w
w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.8, 1.0, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.85
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
sun.data.energy = 3.2
sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(-120))
sc.collection.objects.link(sun)
bpy.ops.mesh.primitive_plane_add(size=100)
g = bpy.context.object
gm = bpy.data.materials.new('G')
gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.2, 0.62, 0.1, 1)
g.data.materials.append(gm)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
cam.data.lens = 40
sc.collection.objects.link(cam)
sc.camera = cam
for name, loc, rot in (('a', (-8.5, -7.5, 4.2), (72, 0, -48)), ('b', (7.0, -8.0, 3.2), (78, 0, 40))):
    cam.location = loc
    cam.rotation_euler = tuple(math.radians(v) for v in rot)
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.render.filepath = str(HERE / 'out' / f'lowpoly_shark_{name}.png')
    bpy.ops.render.render(write_still=True)
print('done', len(me.polygons), 'faces')
