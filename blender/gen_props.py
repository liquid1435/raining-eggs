r"""Raining Eggs: fence + 20 treadmills as bevelled vertex-coloured meshes.

  blender -b -P gen_props.py            -> out\RainingEggsProps.fbx + out\props_*.png + ..\game\props_meta.json
  blender -b -P gen_props.py -- nofbx

Meshes: Fence_Post, Fence_Rail (two planks, 10 studs long, stretch it to the length you need),
        Tread_<Id> (body) and TreadNeon_<Id> (glowing pieces, Material Neon in the game) for the 20 treadmills.
Treadmill data = ..\game\treadmills\treadmills.json (Roblox axes: X length, Y up). Blender (x, y, z) = Roblox (x, -z, y).
props_meta.json keeps, for every mesh, where its box centre sits from the model origin (Roblox axes) and its size.
"""
import bpy, bmesh, math, sys, pathlib, json, shutil, os, random
from mathutils import Matrix, Vector

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'out'
OUT.mkdir(exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
TREADS = json.loads((HERE.parent / 'game' / 'treadmills' / 'treadmills.json').read_text(encoding='utf-8'))


def lin(c):
    f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (f(c[0] / 255), f(c[1] / 255), f(c[2] / 255), 1.0)


def hexc(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


class B:
    def __init__(self):
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.color.new('Col')
        self.n = 0

    def box(self, size, mat, c, bevel=0.1):
        """box with chamfered edges; size in Blender axes, mat = its transform. Top faces get a lighter tone."""
        res = bmesh.ops.create_cube(self.bm, size=1, matrix=mat @ Matrix.Diagonal((*size, 1)))
        verts = res['verts']
        w = min(bevel, min(size) * 0.3)
        if w > 0.015:
            edges = list({e for v in verts for e in v.link_edges})
            r = bmesh.ops.bevel(self.bm, geom=edges, offset=w, offset_type='OFFSET', segments=1, affect='EDGES', profile=0.5)
            verts = r['verts']
        cl, top, low = lin(c), lin(shade(c, 1.12)), lin(shade(c, 0.86))
        for f in {f for v in verts for f in v.link_faces}:
            f.normal_update()
            k = f.normal.z
            for l in f.loops:
                l[self.col] = top if k > 0.6 else low if k < -0.3 else cl
        self.n += 1

    def finish(self, name, loc):
        bm = self.bm
        bmesh.ops.triangulate(bm, faces=bm.faces)
        lo = Vector((min(v.co.x for v in bm.verts), min(v.co.y for v in bm.verts), min(v.co.z for v in bm.verts)))
        hi = Vector((max(v.co.x for v in bm.verts), max(v.co.y for v in bm.verts), max(v.co.z for v in bm.verts)))
        c, s = (lo + hi) / 2, hi - lo
        META[name] = {'centre': [round(c.x, 4), round(c.z, 4), round(-c.y, 4)], 'size': [round(s.x, 4), round(s.z, 4), round(s.y, 4)]}
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        ob.location = loc
        bpy.context.scene.collection.objects.link(ob)
        me.materials.append(MAT)
        return ob


META, EXTRA = {}, {}
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
MAT = bpy.data.materials.new('VertexColour')
MAT.use_nodes = True
nt = MAT.node_tree
attr = nt.nodes.new('ShaderNodeVertexColor')
attr.layer_name = 'Col'
nt.links.new(attr.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
nt.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.6
objs = []
T = Matrix.Translation

# ---------------------------------------------------------------- fence (same sizes and colours as the user's gard.lua)
POST, RAIL, DET = (170, 116, 58), (228, 180, 86), (190, 140, 52)
b = B()
b.box((2, 2, 6), T((0, 0, 3)), POST, 0.16)
b.box((2.3, 2.3, 0.4), T((0, 0, 6.2)), RAIL, 0.1)
b.box((1.5, 1.5, 0.3), T((0, 0, 6.5)), shade(RAIL, 0.92), 0.08)
b.box((2.2, 2.2, 0.35), T((0, 0, 0.175)), shade(POST, 0.8), 0.08)           # foot
for z in (2, 4.2):
    b.box((2.14, 0.7, 0.7), T((0, 0, z)), DET, 0.07)
    b.box((0.7, 2.14, 0.7), T((0, 0, z)), DET, 0.07)
objs.append(b.finish('Fence_Post', (-8, 14, 0)))
b = B()
for z in (2, 4.2):                                                             # two planks along X, 10 long
    b.box((10, 0.8, 1.2), T((0, 0, z)), RAIL, 0.12)
    b.box((10.02, 0.84, 0.12), T((0, 0, z)), shade(RAIL, 0.86), 0)            # groove line along the plank
    for k in range(5):
        x = -4 + k * 2
        b.box((0.5, 0.94, 0.5), T((x, 0, z)), DET, 0.06)
objs.append(b.finish('Fence_Rail', (0, 14, 0)))

# ---------------------------------------------------------------- treadmills
AX = {'X': Vector((1, 0, 0)), 'Y': Vector((0, 0, 1)), 'Z': Vector((0, -1, 0))}    # Roblox axis -> Blender axis
for i, t in enumerate(TREADS):
    body, neon = B(), B()
    for p in t['parts']:
        x, y, z = p['pos']
        m = T((x, -z, y))
        for ax, deg in p['rot']:
            m = m @ Matrix.Rotation(math.radians(deg), 4, AX[ax])
        sx, sy, sz = p['size']
        big = max(sx, sy, sz)
        (neon if p['neon'] else body).box((sx, sz, sy), m, hexc(p['color']), 0.05 if p['neon'] else (0.14 if big > 4 else 0.08))
    # ---- "epic" extras in the look of the user's reference video: dark rubble full of glowing specks around the base,
    #      glowing strips along the belt, a glowing orb on a pedestal over the console, neon fan wings for the best ones.
    #      (the spinning ring, orbiting cubes, moving belt stripes and sparkles are animated by the game client)
    rng = random.Random(900 + i)
    nc = hexc(t['neon'])
    tier = i // 4                                                  # 0 Comun .. 4 Mitic
    rub = tuple(int(10 + v * 0.10) for v in nc)
    belt = next(p for p in t['parts'] if p['role'] == 'Belt')
    bx, by, bz = belt['pos']
    bl, bh, bw = belt['size']
    top_y = max(p['pos'][1] + p['size'][1] / 2 for p in t['parts'] if p['pos'][0] > 3 and abs(p['pos'][2]) < 3 and max(p['size']) < 9)
    con_x = max(3.5, min(6.5, sum(p['pos'][0] for p in t['parts'] if p['pos'][0] > 3 and p['pos'][1] > top_y - 2) /
                         max(1, sum(1 for p in t['parts'] if p['pos'][0] > 3 and p['pos'][1] > top_y - 2))))

    def rb(pos, size, c, target, yaw=0.0, roll=0.0, bevel=0.0):                     # box given in Roblox axes
        x, y, z = pos
        m = T((x, -z, y)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(roll, 4, 'X')
        target.box((size[0], size[2], size[1]), m, c, bevel)

    for _ in range(22 + 9 * tier):
        while True:
            x, z = rng.uniform(-8.6, 9.2), rng.uniform(-5.6, 5.6)
            inside = abs(x) < 7.0 and abs(z) < 3.6
            entrance = x < -5.5 and abs(z) < 3.4                      # keep the way onto the belt free
            if not inside and not entrance:
                break
        s = rng.uniform(0.8, 1.9 + 0.2 * tier)
        y = rng.choice((0, 0, 0, 0.7))
        yaw = rng.uniform(0, 1.5)
        rb((x, y + s / 2, z), (s, s, s), shade(rub, rng.uniform(0.8, 1.5)), body, yaw, 0.0, 0.1)
        for _ in range(3 + tier):
            d = rng.choice(((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0)))
            u, v = rng.uniform(-0.38, 0.38) * s, rng.uniform(-0.38, 0.38) * s
            off = (d[0] * s / 2 + (0 if d[0] else u), d[1] * s / 2 + (0 if d[1] else (v if d[0] or d[2] else 0)), d[2] * s / 2 + (0 if d[2] else (u if d[0] == 0 and d[1] else v if d[1] == 0 and d[0] == 0 else 0)))
            c, sn = math.cos(yaw), math.sin(yaw)
            ox, oz = off[0] * c + off[2] * sn, -off[0] * sn + off[2] * c           # same yaw as the cube (Blender Z turn = Roblox -Y turn)
            k = rng.uniform(0.16, 0.3)
            rb((x + ox, y + s / 2 + off[1], z + oz), (k, k, k), nc, neon, yaw)
    for sz in (-1, 1):                                                 # glowing strips along both sides of the belt + front lights
        rb((bx, by + bh / 2 + 0.03, bz + sz * (bw / 2 - 0.18)), (bl, 0.08, 0.2), nc, neon)
        rb((bx - bl / 2 - 0.5, 0.75, sz * 2.6), (0.5, 0.7, 0.9), tuple(int(v + (255 - v) * 0.6) for v in nc), neon)
    orb_r = 0.75 + 0.14 * tier
    orb_y = top_y + 0.9 + orb_r
    rb((con_x, top_y + 0.35, 0), (1.5, 0.7, 1.5), shade(rub, 1.6), body, 0, 0, 0.1)        # pedestal
    rb((con_x, top_y + 0.8, 0), (0.9, 0.5, 0.9), shade(rub, 2.2), body, 0, 0, 0.08)
    for yaw, roll in ((0, 0), (math.pi / 4, 0), (0, math.pi / 4), (math.pi / 4, math.pi / 4)):   # blocky glowing ball
        rb((con_x, orb_y, 0), (orb_r * 1.5,) * 3, tuple(int(v + (255 - v) * 0.35) for v in nc), neon, yaw, roll)
    if tier >= 2:                                                      # neon fan wings (Epic and up)
        for sz in (-1, 1):
            for ring in range(3 + tier - 2):
                rr = 1.6 + 0.75 * ring
                for k in range(6 + ring * 2):
                    a = math.radians(8 + 78 * k / (5 + ring * 2))
                    rb((con_x + 0.2, top_y - 0.4 + rr * math.sin(a), sz * (1.3 + rr * math.cos(a))), (0.26, 0.32, 0.32), nc, neon)
    EXTRA['Tread_' + t['id']] = {'belt': [bx, round(by + bh / 2, 3), bl, bw], 'orb': [round(con_x, 3), round(orb_y, 3), round(orb_r, 3)], 'tier': tier}
    loc = (i % 5 * 26, -(i // 5) * 20, 0)
    objs.append(body.finish('Tread_' + t['id'], loc))
    if neon.n:
        objs.append(neon.finish('TreadNeon_' + t['id'], loc))
    else:
        neon.bm.free()

for k, v in EXTRA.items():
    META[k].update(v)
(HERE.parent / 'game' / 'props_meta.json').write_text(json.dumps(META, indent=1), encoding='utf-8')
print(f'{len(objs)} meshes, {sum(len(o.data.polygons) for o in objs)} triangles, biggest {max(len(o.data.polygons) for o in objs)}')

if 'nofbx' not in ARGS:
    for o in bpy.data.objects:
        o.select_set(o in objs)
    bpy.context.view_layer.objects.active = objs[0]
    fbx = OUT / 'RainingEggsProps.fbx'
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'MESH'}, apply_scale_options='FBX_SCALE_UNITS',
                             mesh_smooth_type='FACE', colors_type='SRGB', add_leaf_bones=False, bake_anim=False)
    desk = pathlib.Path(os.environ['USERPROFILE']) / 'Desktop' / 'RAINING EGGS NOU' / fbx.name
    shutil.copyfile(fbx, desk)
    print('wrote', fbx.stat().st_size // 1024, 'KB ->', desk)

# ---------------------------------------------------------------- preview
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.view_settings.view_transform = 'Standard'
sc.world = bpy.data.worlds.new('W')
sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.75, 0.86, 1.0, 1)
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
sun.data.energy = 3.2
sun.rotation_euler = (math.radians(50), 0, math.radians(-150))
sc.collection.objects.link(sun)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
cam.data.type = 'ORTHO'
sc.collection.objects.link(cam)
sc.camera = cam
gm = bpy.data.meshes.new('G')
gb = bmesh.new()
bmesh.ops.create_grid(gb, x_segments=1, y_segments=1, size=300)
gb.to_mesh(gm)
gb.free()
gmat = bpy.data.materials.new('G')
gmat.diffuse_color = (0.33, 0.62, 0.25, 1)
gm.materials.append(gmat)
sc.collection.objects.link(bpy.data.objects.new('Ground', gm))


def shot(name, cx, cy, width, res=(1600, 900)):
    d = Vector((0.5, -1.0, 0.6)).normalized()
    tgt = Vector((cx, cy, 3.0))
    cam.location = tgt + d * 150
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = width
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = str(OUT / f'props_{name}.png')
    bpy.ops.render.render(write_still=True)


sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.05, 0.06, 0.14, 1)     # night, so the glow shows
sun.data.energy = 1.2
gmat.diffuse_color = (0.09, 0.1, 0.16, 1)
for o in objs:                                                         # glowing preview material for the neon meshes
    if o.name.startswith('TreadNeon_'):
        if 'Glow' not in bpy.data.materials:
            g = bpy.data.materials.new('Glow')
            g.use_nodes = True
            a = g.node_tree.nodes.new('ShaderNodeVertexColor')
            a.layer_name = 'Col'
            em = g.node_tree.nodes.new('ShaderNodeEmission')
            em.inputs['Strength'].default_value = 4
            g.node_tree.links.new(a.outputs['Color'], em.inputs['Color'])
            g.node_tree.links.new(em.outputs['Emission'], g.node_tree.nodes['Material Output'].inputs['Surface'])
        o.data.materials.clear()
        o.data.materials.append(bpy.data.materials['Glow'])
shot('all', 52, -30, 150, (1600, 1100))
shot('near', 96, -64, 62)
