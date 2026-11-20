r"""Packs Codex's 50 voxel pets (E:\rainingeggs\codex_pets_all) into ONE FBX for Roblox Studio (File > Import 3D):
Pet_<zone>_<rarity> (normal texture), Pet_<zone>_<rarity>_G (gold), Pet_<zone>_<rarity>_R (rainbow).
Static pose (rig removed), head to -Y like the old pets (the game turns them with C.MESH_YAW), textures embedded.
After the import + save: py blender\harvest_meshes.py "<saved .rbxlx>" -> game\meshes.json, then build the place.

  E:\tools\blender-4.2.3-windows-x64\blender.exe -b --python pack_codex_pets.py
-> blender\out\RainingEggsPets3.fbx
"""
import bpy, json, math, pathlib

SRC = pathlib.Path(r'E:\rainingeggs\codex_pets_all')
OUT = pathlib.Path(__file__).resolve().parent / 'out' / 'RainingEggsPets3.fbx'
RARITY = {'Common': 1, 'Uncommon': 2, 'Rare': 3, 'Epic': 4, 'Legendary': 5}

bpy.ops.wm.read_factory_settings(use_empty=True)
manifest = json.loads((SRC / 'manifest.json').read_text(encoding='utf-8'))


def material(name, png):
    img = bpy.data.images.load(str(png))
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    tex.interpolation = 'Closest'
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    return m


made = []
for k, e in enumerate(manifest):
    folder = SRC / e['folder']
    fbx = folder / e['files'][0]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(fbx))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    for o in meshes:                                   # rest pose geometry, no rig
        for mod in list(o.modifiers):
            if mod.type == 'ARMATURE':
                o.modifiers.remove(mod)
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
        o.animation_data_clear()
    for o in new:
        if o.type != 'MESH':
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.rotation_euler[2] += math.pi                    # Codex: head to +Y -> old pets: head to -Y
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    z, i = e['zone_number'], RARITY[e['rarity']]
    base = f'Pet_{z}_{i}'
    stem = pathlib.Path(e['files'][0]).stem
    for suffix, png in (('', f'{stem}.png'), ('_G', f'{stem}_Gold.png'), ('_R', f'{stem}_Rainbow.png')):
        o = ob if suffix == '' else ob.copy()
        if suffix:
            o.data = ob.data.copy()
            bpy.context.scene.collection.objects.link(o)
        o.name = o.data.name = base + suffix
        o.data.materials.clear()
        o.data.materials.append(material(base + suffix, folder / png))
        o.location = ((k % 10) * 8, (k // 10) * 8, {'': 0, '_G': 20, '_R': 40}[suffix])
        made.append(o.name)

bpy.ops.object.select_all(action='SELECT')
OUT.parent.mkdir(exist_ok=True)
bpy.ops.export_scene.fbx(filepath=str(OUT), use_selection=True, apply_scale_options='FBX_SCALE_ALL',
                         mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False, path_mode='COPY', embed_textures=True)
print('PACKED', len(made), 'objects ->', OUT)
