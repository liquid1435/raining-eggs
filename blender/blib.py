"""Shared Blender helpers for the Raining Eggs map models: bevelled vertex-coloured meshes built in Roblox axes.
Blender (x, y, z) = Roblox (x, -z, y). Every finished mesh records its box centre + size (Roblox axes) in META."""
import bpy, bmesh, math, json, pathlib, shutil, os
from mathutils import Matrix, Vector

T = Matrix.Translation
META = {}
WHITE, CREAM, INK = (245, 247, 252), (250, 240, 214), (34, 30, 48)
WOOD, WOOD2, GOLD = (184, 124, 70), (138, 90, 50), (255, 200, 40)
RAINBOW = [(255, 90, 90), (255, 160, 50), (255, 220, 60), (110, 220, 90), (80, 180, 255), (170, 110, 255), (255, 120, 200)]


def lin(c):
    f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (f(c[0] / 255), f(c[1] / 255), f(c[2] / 255), 1.0)


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def mix(c, d, k):
    return tuple(int(a + (b - a) * k) for a, b in zip(c, d))


def reset():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    m = bpy.data.materials.new('VertexColour')
    m.use_nodes = True
    nt = m.node_tree
    a = nt.nodes.new('ShaderNodeVertexColor')
    a.layer_name = 'Col'
    nt.links.new(a.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    nt.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.6
    return m


class B:
    def __init__(self):
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.color.new('Col')
        self.n = 0

    def paint(self, verts, c, flat=False):
        cl, top, low = lin(c), lin(shade(c, 1.12)), lin(shade(c, 0.84))
        for f in {f for v in verts for f in v.link_faces}:
            f.normal_update()
            k = f.normal.z
            for l in f.loops:
                l[self.col] = cl if flat else (top if k > 0.6 else low if k < -0.3 else cl)
        self.n += 1

    def box(self, size, mat, c, bevel=0.1):
        verts = bmesh.ops.create_cube(self.bm, size=1, matrix=mat @ Matrix.Diagonal((*size, 1)))['verts']
        w = min(bevel, min(size) * 0.3)
        if w > 0.015:
            edges = list({e for v in verts for e in v.link_edges})
            verts = bmesh.ops.bevel(self.bm, geom=edges, offset=w, offset_type='OFFSET', segments=1, affect='EDGES', profile=0.5)['verts']
            verts = list(set(verts) | {v for f in {f for v in verts for f in v.link_faces} for v in f.verts})
        self.paint(verts, c)

    def cyl(self, r, h, mat, c, segs=10, r2=None):
        verts = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h, matrix=mat)['verts']
        self.paint(verts, c)

    def ball(self, r, mat, c, segs=10, rings=7):
        verts = bmesh.ops.create_uvsphere(self.bm, u_segments=segs, v_segments=rings, radius=r, matrix=mat)['verts']
        self.paint(verts, c)

    def ico(self, r, mat, c, sub=1):
        verts = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r, matrix=mat)['verts']
        self.paint(verts, c)

    def finish(self, name, loc, mat):
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
        me.materials.append(mat)
        return ob


def M(pos, yaw=0.0, rx=0.0, rz=0.0, scale=None):
    """matrix from a Roblox position (+ yaw about Y, tilt about X, roll about Z, degrees); scale in Roblox axes"""
    x, y, z = pos
    m = T((x, -z, y)) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(rx), 4, 'X') @ Matrix.Rotation(math.radians(-rz), 4, 'Y')
    if scale:
        sx, sy, sz = scale
        m = m @ Matrix.Diagonal((sx, sz, sy, 1))
    return m


def rbox(b, pos, size, c, bevel=0.1, **rot):
    b.box((size[0], size[2], size[1]), M(pos, **rot), c, bevel)


def rcyl(b, pos, r, h, c, axis='Y', segs=10, r2=None, scale=None, **rot):
    m = M(pos, scale=scale, **rot)
    if axis == 'Z':
        m = m @ Matrix.Rotation(math.radians(90), 4, 'X')
    elif axis == 'X':
        m = m @ Matrix.Rotation(math.radians(90), 4, 'Y')
    b.cyl(r, h, m, c, segs, r2)


def rball(b, pos, r, c, scale=(1, 1, 1), segs=10, rings=7, **rot):
    b.ball(r, M(pos, scale=scale, **rot), c, segs, rings)


def rico(b, pos, r, c, scale=(1, 1, 1), sub=1, **rot):
    b.ico(r, M(pos, scale=scale, **rot), c, sub)


def egg(b, pos, s, c, spot=None):
    rball(b, pos, s, c, (1, 1.3, 1), 10, 8)
    if spot:
        x, y, z = pos
        rball(b, (x - 0.35 * s, y + 0.35 * s, z - 0.75 * s), 0.25 * s, spot, segs=6, rings=4)
        rball(b, (x + 0.4 * s, y - 0.1 * s, z - 0.78 * s), 0.2 * s, spot, segs=6, rings=4)


def save_meta(game_dir):
    p = pathlib.Path(game_dir) / 'props_meta.json'
    pm = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    pm.update(META)
    p.write_text(json.dumps(pm, indent=1), encoding='utf-8')


def export(objs, fbx):
    for o in bpy.data.objects:
        o.select_set(o in objs)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'MESH'}, apply_scale_options='FBX_SCALE_UNITS',
                             mesh_smooth_type='FACE', colors_type='SRGB', add_leaf_bones=False, bake_anim=False)
    desk = pathlib.Path(os.environ['USERPROFILE']) / 'Desktop' / 'RAINING EGGS NOU' / pathlib.Path(fbx).name
    shutil.copyfile(fbx, desk)
    return desk


def scene_setup(sky=(0.55, 0.78, 1.0, 1), ground=(0.25, 0.55, 0.16, 1)):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.view_settings.view_transform = 'Standard'
    sc.world = bpy.data.worlds.new('W')
    sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = sky
    sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.9
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
    sun.data.energy = 3.4
    sun.data.angle = math.radians(8)
    sun.rotation_euler = (math.radians(48), 0, math.radians(200))
    sc.collection.objects.link(sun)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    cam.data.lens = 35
    cam.data.clip_end = 3000
    sc.collection.objects.link(cam)
    sc.camera = cam
    gm = bpy.data.meshes.new('G')
    gb = bmesh.new()
    bmesh.ops.create_grid(gb, x_segments=1, y_segments=1, size=1500)
    gb.to_mesh(gm)
    gb.free()
    gmat = bpy.data.materials.new('G')
    gmat.use_nodes = True
    gmat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = ground
    gm.materials.append(gmat)
    gob = bpy.data.objects.new('Ground', gm)
    gob.location.z = -0.02
    sc.collection.objects.link(gob)
    return sc, cam


def glow_material(strength=3):
    g = bpy.data.materials.new('Glow')
    g.use_nodes = True
    a = g.node_tree.nodes.new('ShaderNodeVertexColor')
    a.layer_name = 'Col'
    em = g.node_tree.nodes.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = strength
    g.node_tree.links.new(a.outputs['Color'], em.inputs['Color'])
    g.node_tree.links.new(em.outputs['Emission'], g.node_tree.nodes['Material Output'].inputs['Surface'])
    return g


def place(src, name, roblox_pos, yaw=0.0, s=1.0):
    """a linked copy of a mesh object at a Roblox position (for preview scenes)"""
    o = bpy.data.objects.new(name, src.data)
    x, y, z = roblox_pos
    o.location = (x, -z, y)
    o.rotation_euler = (0, 0, math.radians(yaw))
    o.scale = (s, s, s)
    bpy.context.scene.collection.objects.link(o)
    return o


def shot(sc, cam, path, eye, target, res=(1600, 900), lens=35):
    """eye / target in Roblox coordinates"""
    e = Vector((eye[0], -eye[2], eye[1]))
    t = Vector((target[0], -target[2], target[1]))
    cam.location = e
    cam.rotation_euler = (t - e).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def rbeam(b, p0, p1, w, c, bevel=0.05):
    """square beam from Roblox point p0 to p1"""
    a = Vector((p0[0], -p0[2], p0[1]))
    e = Vector((p1[0], -p1[2], p1[1]))
    d = e - a
    m = T((a + e) / 2) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    b.box((w, w, d.length), m, c, bevel)


def rtube(b, p0, p1, r, c, segs=10, r2=None):
    """round tube from Roblox point p0 to p1"""
    a = Vector((p0[0], -p0[2], p0[1]))
    e = Vector((p1[0], -p1[2], p1[1]))
    d = e - a
    m = T((a + e) / 2) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    b.cyl(r, d.length, m, c, segs, r2)


def rplank(b, p0, p1, w, thick, c, bevel=0.02):
    """flat board from Roblox point p0 to p1, width w lying sideways, thickness up"""
    a = Vector((p0[0], -p0[2], p0[1]))
    e = Vector((p1[0], -p1[2], p1[1]))
    d = e - a
    m = T((a + e) / 2) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    b.box((w, thick, d.length), m, c, bevel)
