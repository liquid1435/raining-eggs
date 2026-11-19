r"""Existing smooth 3D pets (RainingEggsAssets.fbx) + a stud/tile texture projected on every side (box projection).
  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P tiles_preview.py
"""
import bpy, math, pathlib
from mathutils import Vector

HERE = pathlib.Path(__file__).resolve().parent
PICK = ['Pet_1_5', 'Pet_3_4', 'Pet_5_5', 'Pet_6_5', 'Pet_8_5', 'Pet_10_5']
TILE = 0.18          # tile size in model units (smaller = more tiles)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.fbx(filepath=str(HERE / 'out' / 'RainingEggsAssets.fbx'))
objs = [o for o in bpy.data.objects if o.name in PICK]
for o in list(bpy.data.objects):
    if o not in objs:
        bpy.data.objects.remove(o, do_unlink=True)
img = bpy.data.images.load(str(HERE / 'tex' / 'stud.png'))


def tiled_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    vc = nt.nodes.new('ShaderNodeVertexColor')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1 / TILE,) * 3
    tx = nt.nodes.new('ShaderNodeTexImage')
    tx.image = img
    tx.projection = 'BOX'
    tx.projection_blend = 0.15
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], tx.inputs['Vector'])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 0.85
    nt.links.new(vc.outputs['Color'], mix.inputs['A'])
    nt.links.new(tx.outputs['Color'], mix.inputs['B'])
    br = nt.nodes.new('ShaderNodeBrightContrast')
    br.inputs['Bright'].default_value = 0.06
    nt.links.new(mix.outputs['Result'], br.inputs['Color'])
    nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.45
    return m


x = 0
for o in sorted(objs, key=lambda o: PICK.index(o.name)):
    o.data.materials.clear()
    o.data.materials.append(tiled_mat(o.name))
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    o.select_set(False)
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    h = max(v.z for v in bb) - min(v.z for v in bb)
    k = 2.4 / h
    o.scale = (k, k, k)
    bpy.context.view_layer.update()
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    o.location -= Vector(((sum(v.x for v in bb) / 8) - x, sum(v.y for v in bb) / 8, min(v.z for v in bb)))
    o.rotation_euler = (0, 0, math.radians(200))
    x += 3.0

sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.eevee.taa_render_samples = 48
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('W')
sc.world = w
w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.78, 1.0, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.8
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-150))
sc.collection.objects.link(sun)
bpy.ops.mesh.primitive_plane_add(size=200)
g = bpy.context.object
gm = bpy.data.materials.new('G')
gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.25, 0.6, 0.18, 1)
g.data.materials.append(gm)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
cam.data.type = 'ORTHO'
cam.data.ortho_scale = x + 0.5
sc.collection.objects.link(cam)
sc.camera = cam
cam.rotation_euler = (math.radians(75), 0, math.radians(0))
fwd = cam.rotation_euler.to_matrix() @ Vector((0, 0, -1))
cam.location = Vector(((x - 3.0) / 2, 0, 1.3)) - fwd * 30
sc.render.resolution_x, sc.render.resolution_y = 2400, 640
sc.render.filepath = str(HERE / 'out' / 'tiles_preview.png')
bpy.ops.render.render(write_still=True)
print('done', [o.name for o in objs])
