"""Round-trip validation. Run in a fresh Blender process."""
from mathutils import Vector
from bpy_extras.io_utils import axis_conversion
import bpy
from pathlib import Path
root = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(root/'models/StarlightDragon.fbx'))
rig, = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
pet, = [o for o in bpy.context.scene.objects if o.type == 'MESH']
pet.data.calc_loop_triangles()
assert len(pet.data.loop_triangles) == 7884 and len(pet.data.uv_layers) == 1
assert all(len(p.vertices) == 3 and p.area > 1e-10 for p in pet.data.polygons)
assert all(0 <= min(loop.uv) <= max(loop.uv) <= 1 for loop in pet.data.uv_layers.active.data)
assert abs(max(pet.dimensions) - 5) < .05
assert rig.data.bones.get('GlowSocket') and rig.data.bones.get('Root')
assert any(m.type == 'ARMATURE' and m.object == rig for m in pet.modifiers)
assert all(abs(sum(g.weight for g in v.groups)-1) < .0001 for v in pet.data.vertices)
print('Skin verified:', len(pet.data.vertices), 'vertices;', len(
    rig.data.bones), 'bones. Size:', tuple(round(x, 3) for x in pet.dimensions))
scene = bpy.context.scene
assert len(bpy.data.actions) == 3
for action in bpy.data.actions:
    name = action.name.split('|')[-1]
    print(name, list(action.frame_range))
    assert int(action.frame_range[1]-action.frame_range[0]) == {'Idle': 48, 'Hop': 24, 'Hatch': 48}[name]
    rig.animation_data.action = action
    positions = []
    for f in range(1, int(action.frame_range[1])+1, 3):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        p = pet.evaluated_get(dg)
        positions.append([p.matrix_world@v.co for v in list(p.data.vertices)[::31]])
    delta = max((a-b).length for pose in positions for a, b in zip(positions[0], pose))
    assert delta > .02
    if name in ('Idle', 'Hop'):
        seam = max((a-b).length for a, b in zip(positions[0], positions[-1]))
        assert seam < .0001, (name, seam)
    print('Sampled skinned-vertex displacement', round(delta, 3))
print('Authoring muzzle maps to FBX vector', axis_conversion(
    to_forward='-Z', to_up='Y')@Vector((0, -1, 0)))

for name, end in [('Idle', 49), ('Hop', 25), ('Hatch', 49)]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(root/'models'/'animations'/f'{name}.fbx'))
    clip, = bpy.data.actions
    assert list(clip.frame_range) == [1.0, float(end)], (name, list(clip.frame_range))
    print('Single-take FBX verified', name, list(clip.frame_range))
