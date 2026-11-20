"""Render the Starlight Dragon hero, movie or proof frames in Blender."""
import bpy
import random
import sys
from math import cos, pi, sin
from mathutils import Vector
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dragon import ROOT, actions, rig, scene

random.seed(19)
R = ROOT/'renders'
R.mkdir(exist_ok=True)
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.taa_render_samples = 16
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.fps = 20
scene.frame_end = 400
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
world = bpy.data.worlds.new('Lilac studio')
scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.68, .72, .88, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .42


def material(name, col, em=0, metal=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*col, 1)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = .42
    b.inputs['Metallic'].default_value = metal
    if em:
        b.inputs['Emission Color'].default_value = (*col, 1)
        b.inputs['Emission Strength'].default_value = em
    return m


gold = material('Champagne foil', (1, .62, .19), .62, .40)
light = material('Starfire', (1, .86, .49), 2)
pearl = material('Sea glass', (.53, .86, .82))
lilac = material('Lavender enamel', (.59, .53, .79))


def floor_disc(name, r, depth, z, m, bevel=.04):
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=r, depth=depth, location=(0, 0, z))
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    b = o.modifiers.new('Soft rim', 'BEVEL')
    b.width = bevel
    b.segments = 3
    o.modifiers.new('Face normals', 'WEIGHTED_NORMAL')
    return o


floor_disc('Porcelain dais', 2.64, .22, -.15, pearl, .09)
floor_disc('Gilded edge', 2.65, .034, -.15, gold, .016)
floor_disc('Top enamel', 2.48, .04, -.043, lilac, .019)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.275))
floor = bpy.context.object
floor.data.materials.append(material('Periwinkle cyclorama', (.61, .58, .85)))
# Broad lavender-to-seafoam wash across the cyclorama.
floor_mat = floor.data.materials[0]
nd = floor_mat.node_tree.nodes
lk = floor_mat.node_tree.links
geom = nd.new('ShaderNodeNewGeometry')
sep = nd.new('ShaderNodeSeparateXYZ')
lk.new(geom.outputs['Position'], sep.inputs[0])
rng = nd.new('ShaderNodeMapRange')
rng.inputs['From Min'].default_value = -7
rng.inputs['From Max'].default_value = 7
lk.new(sep.outputs['X'], rng.inputs['Value'])
wash = nd.new('ShaderNodeValToRGB')
wash.color_ramp.elements[0].color = (.76, .57, .80, 1)
wash.color_ramp.elements[1].color = (.38, .74, .71, 1)
lk.new(rng.outputs[0], wash.inputs[0])
lk.new(wash.outputs[0], nd.get('Principled BSDF').inputs['Base Color'])


def line(name, points, rad, mat, parent=None, closed=False):
    c = bpy.data.curves.new(name, 'CURVE')
    c.dimensions = '3D'
    c.bevel_depth = rad
    c.bevel_resolution = 2
    s = c.splines.new('POLY')
    s.points.add(len(points)-1)
    for p, co in zip(s.points, points):
        p.co = (*co, 1)
    s.use_cyclic_u = closed
    o = bpy.data.objects.new(name, c)
    scene.collection.objects.link(o)
    o.data.materials.append(mat)
    o.parent = parent
    return o


for rad, width in [(2.18, .013), (2.37, .009)]:
    line('Aura orbit', [(rad*cos(j*pi/64), rad*sin(j*pi/64), -.012)
         for j in range(128)], width, gold, closed=True)
for j in range(32):
    a = 2*pi*j/32
    r = 2.27
    d = .066 if j % 4 == 0 else .026
    line('Astrolabe graduation', [(r*cos(a)-d*cos(a), r*sin(a)-d *
         sin(a), -.008), ((r+d)*cos(a), (r+d)*sin(a), -.008)], .011, gold)


def empty(name):
    o = bpy.data.objects.new(name, None)
    scene.collection.objects.link(o)
    return o


turn = empty('Turntable')
rig.parent = turn
def aim(o, point): o.rotation_euler = (Vector(point)-o.location).to_track_quat('-Z', 'Y').to_euler()


def area(name, loc, power, size, col):
    d = bpy.data.lights.new(name, 'AREA')
    d.energy = power
    d.shape = 'DISK'
    d.size = size
    d.color = col
    o = bpy.data.objects.new(name, d)
    scene.collection.objects.link(o)
    o.location = loc
    aim(o, (0, 0, 1.7))


area('Warm softbox', (-4, -6, 8), 610, 5, (1, .83, .75))
area('Cool fill', (5, -3, 5), 350, 4, (.72, .89, 1))
area('Pearl rim', (2, 4, 7), 840, 3, (.87, 1, .92))
camera = bpy.data.cameras.new('Catalog lens')
cam = bpy.data.objects.new('Catalog camera', camera)
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = (4.6, -11, 5.0)
aim(cam, (0, 0, 1.98))
camera.type = 'ORTHO'
camera.ortho_scale = 11.9
right = cam.rotation_euler.to_matrix()@Vector((1, 0, 0))
cam.location -= right*1.75
# Typeset specimen card fixed in screen space. Emission ink is light-independent.


def ink(name, col):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    e = n.new('ShaderNodeEmission')
    e.inputs[0].default_value = (*col, 1)
    m.node_tree.links.new(e.outputs[0], n.get('Material Output').inputs[0])
    return m


navy = ink('Plum ink', (.059, .038, .122))
sub = ink('Secondary ink', (.109, .079, .178))
foil = ink('Cloud ink', (.98, .90, .74))
typedir = Path('C:/Windows/Fonts')
serif = bpy.data.fonts.load(str(typedir/'georgia.ttf'))
italic = bpy.data.fonts.load(str(typedir/'georgiai.ttf'))
sans = bpy.data.fonts.load(str(typedir/'calibrib.ttf'))


def label(value, x, y, size, font, mat, spacing=1):
    cu = bpy.data.curves.new(value, 'FONT')
    cu.body = value
    cu.size = size
    cu.font = font
    cu.space_character = spacing
    o = bpy.data.objects.new(value, cu)
    scene.collection.objects.link(o)
    o.parent = cam
    o.location = (x*1.105, y*1.105, -2)
    o.scale = (1.105,)*3
    cu.materials.append(mat)
    return o


label('RAINING EGGS', -4.89, 2.51, .165, sans, navy, 1.24)
label('CELESTIAL COLLECTION', -3.32, 2.51, .11, sans, sub, 1.18)


def rule(x1, x2, y, mat): line('Hairline', [
    (x1*1.105, y*1.105, -2), (x2*1.105, y*1.105, -2)], .004, mat, cam)


rule(-4.88, 4.88, 2.36, sub)
label('LEGENDARY', -4.65, .94, .165, sans, navy, 1.29)
line('Rarity diamond', [(-5.403, 1.105, -2), (-5.326, 1.204, -2),
     (-5.249, 1.105, -2), (-5.326, 1.006, -2)], .012, foil, cam, True)
label('Starlight', -4.93, .10, .92, serif, navy)
label('Dragon', -4.93, -.71, .96, italic, navy)
rule(-4.87, -3.30, -1.02, foil)
label('HATCHLING', -4.87, -1.31, .137, sans, sub, 1.22)
rule(-4.88, 4.88, -2.45, sub)
label('RAINING EGGS   /   PET FIELD GUIDE', -4.88, -2.70, .123, sans, navy, 1.08)
label('FIG.  01', 4.36, -2.70, .13, sans, navy, 1.15)
# Animated floating four-point stars, in several depths around the silhouette.
for i in range(18):
    a = i*2.39996
    r = random.uniform(1.52, 2.39)
    x, y = r*cos(a), r*sin(a)
    z = random.uniform(.65, 3.92)
    w = random.uniform(.026, .085)
    if y < -.55 and abs(x) < 1.05:
        y = 1.7
    pts = [(0, -.025, 0)]+[(w*sin(k*pi/4)*(.27 if k % 2 else 1), 0, w *
                            1.38*cos(k*pi/4)*(.27 if k % 2 else 1)) for k in range(8)]
    me = bpy.data.meshes.new('Glint')
    me.from_pydata(pts, [], [(0, k+1, (k+1) % 8+1) for k in range(8)])
    o = bpy.data.objects.new('Drifting star', me)
    scene.collection.objects.link(o)
    me.materials.append(light if i % 3 else gold)
    o.rotation_euler.z = .43
    for f in range(-50, 452, 10):
        phase = f/32+i
        o.location = (x+.075*sin(phase), y, z+.14*sin(phase*.8))
        s = .56+.43*sin(phase*1.46)
        o.scale = (s, s, s)
        o.keyframe_insert(data_path='location', frame=f)
        o.keyframe_insert(data_path='scale', frame=f)
# NLA strips map 24 fps source clips to the 20 fps preview.
rig.animation_data.action = None
track = rig.animation_data.nla_tracks.new()
for name, start, duration in [('Idle', 1, 160), ('Hop', 161, 120), ('Hatch', 281, 40), ('Idle', 321, 80)]:
    strip = track.strips.new(name, start, actions[name])
    strip.scale = 20/24
    strip.repeat = duration/((actions[name].frame_range[1]-1)*20/24)
    strip.extrapolation = 'NOTHING'
for f, a in [(1, .16), (160, 2*pi+.16), (181, 2*pi-.05), (268, 2*pi+.10), (281, 2*pi+.16), (400, 2*pi+.16)]:
    turn.rotation_euler.z = a
    turn.keyframe_insert(data_path='rotation_euler', frame=f)
for f, x in [(1, 0), (161, -.30), (278, .31), (301, 0), (400, 0)]:
    turn.location.x = x
    turn.keyframe_insert(data_path='location', frame=f)
# Sample the socket's actual animated world positions for a tapering light ribbon.
positions = []
for f in range(-8, 401):
    scene.frame_set(max(1, f))
    positions.append(rig.matrix_world@rig.pose.bones['GlowSocket'].head)
ribbon = line('Comet tail ribbon', [tuple(positions[0])]*9, .043, light)
for f in range(1, 401):
    for j, p in enumerate(ribbon.data.splines[0].points):
        pos = positions[f+j]
        p.co = (*pos, 1)
        p.radius = (j/8)**.85
        p.keyframe_insert(data_path='co', frame=f)
# Follow the reveal upward while keeping the field guide fixed on screen.
base_camera = cam.location.copy()
for frame, lift in [(1, 0), (278, 0), (294, .36), (302, .52), (315, .12), (324, 0), (400, 0)]:
    cam.location = base_camera+Vector((0, 0, lift))
    cam.keyframe_insert(data_path='location', frame=frame)
# Comet sparks fan away from the hatchling as it clears the plinth.
for i in range(22):
    a = 2*pi*i/22
    origin = Vector((.20*cos(a), .20*sin(a), 1.55))
    dest = Vector((2.35*cos(a), 2.35*sin(a), 1.8+1.42*sin(i*1.73)))
    spark = line('Hatch spark', [(0, 0, 0), tuple((dest-origin).normalized()*.15)], .018, light)
    for frame, dist, size in [(1, 0, 0), (286+i % 4, 0, 0), (295+i % 4, .55, 1), (309+i % 4, 1, .55), (315+i % 4, 1.15, 0), (400, 1.15, 0)]:
        spark.location = origin.lerp(dest, dist)
        spark.scale = (size,)*3
        spark.keyframe_insert(data_path='location', frame=frame)
        spark.keyframe_insert(data_path='scale', frame=frame)
scene.use_nodes = True
tree = scene.node_tree
tree.nodes.clear()
rl = tree.nodes.new('CompositorNodeRLayers')
glare = tree.nodes.new('CompositorNodeGlare')
glare.glare_type = 'FOG_GLOW'
glare.quality = 'MEDIUM'
glare.threshold = 1.25
glare.size = 7
out = tree.nodes.new('CompositorNodeComposite')
tree.links.new(rl.outputs['Image'], glare.inputs['Image'])
tree.links.new(glare.outputs['Image'], out.inputs['Image'])
mode = sys.argv[-1]
scene.frame_set(1)
if mode == 'movie':
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'HIGH'
    scene.render.filepath = str(R/'preview.mp4')
    bpy.ops.render.render(animation=True)
elif mode == 'proof':
    scene.render.resolution_percentage = 45
    for f in [1, 87, 192, 301]:
        scene.frame_set(f)
        scene.render.filepath = str(R/f'proof_{f}.png')
        bpy.ops.render.render(write_still=True)
else:
    scene.eevee.taa_render_samples = 32
    scene.render.filepath = str(R/'hero.png')
    bpy.ops.render.render(write_still=True)
