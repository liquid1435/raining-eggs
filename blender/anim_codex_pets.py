import os
r"""Codex voxel pets WITH their animations, for Roblox without uploading animations.

Every Codex rig is rigid (each vertex follows one bone). This script cuts every pet into one mesh per bone
(Pet_<z>_<i>__<k>, rest pose, no texture: the game puts the pet's uploaded texture on it, same UV atlas) and samples
the 4 clips (Idle, Walk, HappyHatch, PenLife) at FPS frames per second as one rigid transform per part and frame.
The game (game/PetAnim.lua) plays them by moving the parts.

  E:\tools\blender-4.2.3-windows-x64\blender.exe -b --python anim_codex_pets.py
-> blender\out\RainingEggsPetParts.fbx   (import once in Studio, then blender\harvest_meshes.py)
-> game\PetAnimData.lua                  (rest offsets + packed frames, base64)

Coordinates: Blender (head turned to -Y like the old pets) -> Roblox mesh space r = (x, z, -y).
Per frame and part we store D = the transform that moves the rest part to its posed place, written relative to the
pet's bottom centre bc: rotation quaternion (4 x int8) + translation t = R*bc + T - bc (3 x int16, 1/1000 stud).
"""
import base64, bpy, bmesh, json, math, pathlib, struct
from mathutils import Matrix, Vector

SRC = pathlib.Path(os.environ.get('PETS_SRC', r'E:\rainingeggs\codex_pets_all'))
HERE = pathlib.Path(__file__).resolve().parent
OUT_FBX = HERE / 'out' / 'RainingEggsPetParts.fbx'
OUT_LUA = HERE.parent / 'game' / 'PetAnimData.lua'
RARITY = {'Common': 1, 'Uncommon': 2, 'Rare': 3, 'Epic': 4, 'Legendary': 5}
CLIPS = ('Idle', 'Walk', 'HappyHatch', 'PenLife')
SRC_FPS, FPS = 24, 8

ROT = Matrix.Rotation(math.pi, 4, 'Z')                                    # head +Y -> -Y (like pack_codex_pets.py)
M = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))     # Blender -> Roblox mesh space
CONV = M @ ROT
CONV_INV = CONV.inverted()


def to_r(v):
    return (CONV @ Vector((v[0], v[1], v[2], 1.0))).xyz


bpy.ops.wm.read_factory_settings(use_empty=True)
keep = bpy.data.scenes[0]
manifest = json.loads((SRC / 'manifest.json').read_text(encoding='utf-8'))
data = {}
parts_total = 0

for e in manifest:
    # clean scene for the import
    for o in list(bpy.data.objects):
        if o.get('cut') is None:
            bpy.data.objects.remove(o, do_unlink=True)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(SRC / e['folder'] / e['files'][0]))
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == 'ARMATURE')
    src = next(o for o in new if o.type == 'MESH')
    z, i = e['zone_number'], RARITY[e['rarity']]
    key = f'{z}_{i}' + (f"_{e['variant']}" if e.get('variant', 1) > 1 else '')   # v153: variants
    arm.animation_data_create()
    arm.animation_data.action = None
    bpy.context.scene.frame_set(0)
    # rest pose world vertices (armature in rest position)
    arm.data.pose_position = 'REST'
    bpy.context.view_layer.update()
    mw = src.matrix_world.copy()
    names = [g.name for g in src.vertex_groups]
    me = src.data
    bm = bmesh.new()
    bm.from_mesh(me)
    dl = bm.verts.layers.deform.active
    uvl = bm.loops.layers.uv.active
    # bone of each face = bone with the largest weight on its first vertex
    def bone_of(f):
        w = f.verts[0][dl] if dl else {}
        return names[max(w.items(), key=lambda kv: kv[1])[0]] if w else None
    groups = {}
    for f in bm.faces:
        groups.setdefault(bone_of(f), []).append(f)
    # pet bottom centre (Roblox space) over all vertices
    allr = [to_r(mw @ v.co) for v in bm.verts]
    lo = Vector((min(p.x for p in allr), min(p.y for p in allr), min(p.z for p in allr)))
    hi = Vector((max(p.x for p in allr), max(p.y for p in allr), max(p.z for p in allr)))
    bc = Vector(((lo.x + hi.x) / 2, lo.y, (lo.z + hi.z) / 2))
    longest = max(hi - lo)
    order = [b for b in groups if b is not None]
    rest = []
    for k, bone in enumerate(order, 1):
        nm = bpy.data.meshes.new(f'Pet_{key}__{k}')
        nb = bmesh.new()
        nuv = nb.loops.layers.uv.new('UVMap')
        vmap = {}
        for f in groups[bone]:
            vs = []
            for v in f.verts:
                if v not in vmap:
                    vmap[v] = nb.verts.new((CONV_INV @ M) @ (mw @ v.co))   # world, turned head -Y (Blender space)
                vs.append(vmap[v])
            try:
                nf = nb.faces.new(vs)
            except ValueError:
                continue
            for l_new, l_old in zip(nf.loops, f.loops):
                l_new[nuv].uv = l_old[uvl].uv if uvl else (0, 0)
        nb.to_mesh(nm)
        nb.free()
        ob = bpy.data.objects.new(f'Pet_{key}__{k}', nm)
        ob['cut'] = 1
        keep.collection.objects.link(ob)
        rp = [to_r(mw @ v.co) for v in vmap]
        plo = Vector((min(p.x for p in rp), min(p.y for p in rp), min(p.z for p in rp)))
        phi = Vector((max(p.x for p in rp), max(p.y for p in rp), max(p.z for p in rp)))
        c = (plo + phi) / 2 - bc
        rest.append([round(c.x, 4), round(c.y, 4), round(c.z, 4)])
        # keep the cut mesh centred on its own box (Roblox centres imported meshes the same way)
        ob.location = ((z - 1) * 12, (i - 1) * 12, k * 0.0)
    bm.free()
    parts_total += len(order)
    # animation: world delta per bone per frame
    arm.data.pose_position = 'POSE'
    clips = {}
    acts = {a.name.split('|')[-1]: a for a in bpy.data.actions}
    for clip in CLIPS:
        act = acts.get(clip)
        if not act:
            continue
        arm.animation_data.action = act
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        n = max(2, int(round((f1 - f0) / SRC_FPS * FPS)) + 1)
        buf = bytearray()
        for s in range(n):
            fr = f0 + (f1 - f0) * s / (n - 1)
            bpy.context.scene.frame_set(int(fr), subframe=fr - int(fr))
            for bone in order:
                pb = arm.pose.bones[bone]
                D = arm.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted() @ arm.matrix_world.inverted()
                Dr = CONV @ D @ CONV_INV
                R = Dr.to_3x3()
                T = Dr.translation
                t = R @ bc + T - bc
                q = R.to_quaternion().normalized()
                if q.w < 0:
                    q = -q
                buf += struct.pack('<4b', *[max(-127, min(127, round(v * 127))) for v in (q.x, q.y, q.z, q.w)])
                buf += struct.pack('<3h', *[max(-32767, min(32767, round(v * 1000))) for v in t])
        clips[clip] = {'n': n, 'len': round((f1 - f0) / SRC_FPS, 4), 'd': base64.b64encode(bytes(buf)).decode()}
    arm.animation_data.action = None
    data[key] = {'parts': len(order), 'rest': rest, 'longest': round(longest, 4), 'clips': clips}
    print('pet', key, e['name'], len(order), 'parts')

# remove the import leftovers, keep only the cut parts
for o in list(bpy.data.objects):
    if o.get('cut') is None:
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='SELECT')
ZMIN = int(os.environ.get('FBX_ZONE_MIN', '0'))      # v139: export only the parts of zones >= ZMIN (Lua keeps all)
if ZMIN:
    for o in bpy.data.objects:
        if int(o.name.split('_')[1]) < ZMIN:
            o.select_set(False)
    OUT_FBX = OUT_FBX.with_name(OUT_FBX.stem + f'_z{ZMIN}.fbx')
VF = os.environ.get('FBX_PARTS_FILTER', '')          # v153: 'va,vb' = one FBX per half of the variant parts
if VF:
    for tag in VF.split(','):
        lo, hi = {'va': (1, 5), 'vb': (6, 10), 'wa': (11, 15), 'wb': (16, 20)}.get(tag, (6, 10))  # v228: wa / wb = world 2
        only = set(tag[5:].split(';')) if tag.startswith('keys=') else None   # v208: 'keys=10_2;2_1_3' = just these pets
        for o in bpy.data.objects:
            k = o.name[4:].split('__')[0].split('_')      # Pet_<z>_<i>[_<v>]__<j>
            if only is not None:
                o.select_set('_'.join(k) in only)
            else:
                o.select_set(len(k) == 3 and lo <= int(k[0]) <= hi)
        if only is not None:
            tag = 'fix'
        f = OUT_FBX.with_name(OUT_FBX.stem + f'_{tag}.fbx')
        f.parent.mkdir(exist_ok=True)
        bpy.ops.export_scene.fbx(filepath=str(f), use_selection=True, apply_scale_options='FBX_SCALE_ALL',
                                 mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False)
        print('PARTS FBX', tag, sum(o.select_get() for o in bpy.data.objects), '->', f)
else:
    OUT_FBX.parent.mkdir(exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=str(OUT_FBX), use_selection=True, apply_scale_options='FBX_SCALE_ALL',
                             mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False)

# Lua module
lines = ['-- generated by blender/anim_codex_pets.py: Codex pet parts + packed animation frames (see game/PetAnim.lua)',
         'return {']
for key, d in data.items():
    rest = ','.join('{%s,%s,%s}' % tuple(r) for r in d['rest'])
    cl = ','.join('%s={n=%d,len=%s,d="%s"}' % (c, v['n'], v['len'], v['d']) for c, v in d['clips'].items())
    lines.append('\t["%s"]={parts=%d,longest=%s,rest={%s},clips={%s}},' % (key, d['parts'], d['longest'], rest, cl))
lines.append('}')
OUT_LUA.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('DONE', len(data), 'pets', parts_total, 'parts ->', OUT_FBX, OUT_LUA, OUT_LUA.stat().st_size, 'bytes')
