r"""Merges every out\RainingEggs<Part>.fbx (shops + map zones) into one file, so the user imports only once.
  blender -b -P combine_fbx.py   -> out\RainingEggsAllModels.fbx (+ copy on the Desktop)"""
import bpy, pathlib, os, shutil
OUT = pathlib.Path(__file__).resolve().parent / 'out'
NAMES = ['Shops', 'Meadow', 'Mushroom', 'Candy', 'Toy', 'Crystal', 'Spooky', 'Thunder', 'Neon', 'Cloud', 'Golden']
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for n in NAMES:
    bpy.ops.import_scene.fbx(filepath=str(OUT / f'RainingEggs{n}.fbx'))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects:
    o.select_set(o in meshes)
for o in meshes:                                   # FBX import adds ".001" on clashes: keep the clean names
    o.name = o.name.split('.')[0]
    o.data.name = o.name
bpy.context.view_layer.objects.active = meshes[0]
fbx = OUT / 'RainingEggsAllModels.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'MESH'}, apply_scale_options='FBX_SCALE_UNITS',
                         mesh_smooth_type='FACE', colors_type='SRGB', add_leaf_bones=False, bake_anim=False)
desk = pathlib.Path(os.environ['USERPROFILE']) / 'Desktop' / 'RAINING EGGS NOU' / fbx.name
shutil.copyfile(fbx, desk)
print('combined', len(meshes), 'meshes,', fbx.stat().st_size // 1024, 'KB ->', desk)
print('names', sorted(o.name for o in meshes)[:5], 'colours:', all(len(o.data.color_attributes) > 0 for o in meshes))
