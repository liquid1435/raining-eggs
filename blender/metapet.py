r"""Professional smooth pets: one seamless body made from metaballs (they melt into each other),
then detail meshes (eyes, nose, horns...). Then the pixelated copy (low-poly facets + aligned studs).
Blender axes: x right, y back (pets look towards -y), z up.
"""
import bpy, bmesh, math, pathlib, sys
from mathutils import Vector, Euler, Quaternion
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lowpoly_lib as LL

WHITE = (0.96, 0.96, 0.97)
RM = 1.55          # metaball radius boost: the visible surface sits well inside the influence radius
BLACK = (0.03, 0.03, 0.05)


def rgb(r, g, b):
    return (r / 255, g / 255, b / 255)


class MB:
    def __init__(self, name):
        self.name = name
        self.els = []          # (kind, co, r, size, rot, col, neg)
        self.det = bmesh.new()  # detail meshes
        self.dcl = self.det.loops.layers.color.new('Col')
        self.glow_cols = []    # colours that should glow
        self.paint_fn = None   # optional override: f(point, normal, colour) -> colour

    # ---------------- metaball elements
    def ball(self, co, r, col, neg=False):
        self.els.append(('BALL', Vector(co), r, Vector((1, 1, 1)), Euler(), col, neg))

    def ell(self, co, r, size, col, rot=(0, 0, 0), neg=False):
        self.els.append(('ELLIPSOID', Vector(co), r, Vector(size), Euler([math.radians(a) for a in rot]), col, neg))

    def cap(self, p0, p1, r, col, neg=False):
        """capsule between two points"""
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        q = Vector((1, 0, 0)).rotation_difference(d.normalized())
        self.els.append(('CAPSULE', (p0 + p1) / 2, r, Vector((d.length / 2, 1, 1)), q.to_euler(), col, neg))

    def sym(self, fn, *a, **k):
        """call fn for x>0 and the mirrored copy"""
        fn(*a, **k)
        a2, lead = [], True
        for v in a:                      # mirror only the leading point arguments (never sizes or colours)
            if lead and isinstance(v, (tuple, list)) and len(v) == 3:
                a2.append((-v[0], v[1], v[2]))
            else:
                lead = False
                a2.append(v)
        if 'rot' in k:
            r = k['rot']
            k = dict(k, rot=(r[0], -r[1], -r[2]))
        fn(*a2, **k)

    # ---------------- detail meshes (smooth spheres / cones), painted
    def _paint(self, faces, col):
        for f in faces:
            for lp in f.loops:
                lp[self.dcl] = tuple(col) + (1,)

    def sphere(self, c, r, col, scale=(1, 1, 1), rot=(0, 0, 0)):
        res = bmesh.ops.create_uvsphere(self.det, u_segments=20, v_segments=14, radius=r)
        R = Euler([math.radians(a) for a in rot]).to_matrix()
        for v in res['verts']:
            v.co = R @ Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2])) + Vector(c)
        self._paint(list({f for v in res['verts'] for f in v.link_faces}), col)

    def cone(self, base, tip, r, col, segs=12, bend=None, rings=6):
        """curved horn/claw: rings along base->tip (optionally bent towards 'bend'), radius to ~0"""
        base, tip = Vector(base), Vector(tip)
        pts = []
        for i in range(rings + 1):
            t = i / rings
            p = base.lerp(tip, t)
            if bend is not None:
                p = p + Vector(bend) * math.sin(t * math.pi) * 1.0
            pts.append(p)
        rr = [r * (1 - t / (rings + 0.6)) ** 1.1 for t in range(rings + 1)]
        self.tube(pts, rr, col, segs, tip_point=True)

    def tube(self, pts, radii, col, segs=12, tip_point=False):
        pts = [Vector(p) for p in pts]
        rings = []
        side = None
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            if side is None:
                side = t.cross(Vector((0, 0, 1)))
                if side.length < 1e-3:
                    side = Vector((1, 0, 0))
            side = (side - t * side.dot(t)).normalized()
            up = side.cross(t).normalized()
            rings.append([self.det.verts.new(p + side * math.cos(2 * math.pi * k / segs) * radii[i] + up * math.sin(2 * math.pi * k / segs) * radii[i])
                          for k in range(segs)])
        fs = []
        for r0, r1 in zip(rings, rings[1:]):
            for k in range(segs):
                j = (k + 1) % segs
                fs.append(self.det.faces.new((r0[k], r0[j], r1[j], r1[k])))
        fs.append(self.det.faces.new(list(reversed(rings[0]))))
        if tip_point:
            tv = self.det.verts.new(pts[-1] + (pts[-1] - pts[-2]).normalized() * radii[-1] * 2)
            for k in range(segs):
                fs.append(self.det.faces.new((rings[-1][k], rings[-1][(k + 1) % segs], tv)))
        else:
            fs.append(self.det.faces.new(rings[-1]))
        bmesh.ops.recalc_face_normals(self.det, faces=fs)
        self._paint(fs, col)

    def eye(self, c, side, r=0.17, look=(0, -1, 0), iris=None):
        """glossy cartoon eye: white ball, black (or coloured) pupil turned outwards-forwards, sparkle"""
        c = Vector(c)
        d = Vector((side * 0.55, -0.83, 0.05)).normalized()
        self.sphere(c, r, WHITE)
        if iris:
            self.sphere(c + d * r * 0.62, r * 0.55, iris, (1, 1, 1))
        self.sphere(c + d * r * 0.72, r * 0.44, BLACK)
        self.sphere(c + d * r * 0.95 + Vector((0, 0, r * 0.32)), r * 0.13, WHITE)

    # ---------------- build
    def build(self, res=0.045, remesh=0.03):
        mb = bpy.data.metaballs.new(self.name + '_mb')
        mb.resolution = res
        mb.render_resolution = res
        mb.threshold = 0.6
        for kind, co, r, size, rot, col, neg in self.els:
            e = mb.elements.new(type=kind)
            e.co = co
            e.radius = r * RM
            e.use_negative = neg
            e.stiffness = 2.0
            if kind in ('ELLIPSOID', 'CAPSULE'):
                e.size_x, e.size_y, e.size_z = size
                e.rotation = rot.to_quaternion()
        ob = bpy.data.objects.new(self.name + '_mbo', mb)
        bpy.context.scene.collection.objects.link(ob)
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        bpy.data.objects.remove(ob, do_unlink=True)
        body = bpy.data.objects.new(self.name + '_3D', me)
        bpy.context.scene.collection.objects.link(body)
        rm = body.modifiers.new('R', 'REMESH')
        rm.mode = 'VOXEL'
        rm.voxel_size = remesh
        cs = body.modifiers.new('S', 'SMOOTH')
        cs.factor = 0.6
        cs.iterations = 4
        dg = bpy.context.evaluated_depsgraph_get()
        me2 = bpy.data.meshes.new_from_object(body.evaluated_get(dg))
        body.modifiers.clear()
        body.data = me2
        # colour every vertex by the element that owns it (strongest field)
        bm = bmesh.new()
        bm.from_mesh(me2)
        cl = bm.loops.layers.color.new('Col')
        pos = [e for e in self.els if not e[6]]
        cache = {}
        bm.normal_update()
        for v in bm.verts:
            best, bc = -1e9, (1, 0, 1)
            for kind, co, r, size, rot, col, neg in pos:
                d = v.co - co
                if kind != 'BALL':
                    d = rot.to_matrix().inverted() @ d
                if kind == 'CAPSULE':
                    x = max(-size.x, min(size.x, d.x))
                    dist = (d - Vector((x, 0, 0))).length / r
                elif kind == 'ELLIPSOID':
                    dist = Vector((d.x / size.x, d.y / size.y, d.z / size.z)).length / r
                else:
                    dist = d.length / r
                s = 1 - dist
                if s > best:
                    best, bc = s, col
            if self.paint_fn:
                bc = self.paint_fn(v.co, v.normal, bc)
            cache[v.index] = bc
        for f in bm.faces:
            for lp in f.loops:
                lp[cl] = tuple(cache[lp.vert.index]) + (1,)
        # keep the body and the details apart too (for the pixelated copy)
        self.body_mesh = bpy.data.meshes.new(self.name + '_body')
        bm.to_mesh(self.body_mesh)
        self.det_mesh = bpy.data.meshes.new(self.name + '_det')
        self.det.to_mesh(self.det_mesh)
        # add the detail meshes
        bm.from_mesh(self.det_mesh)
        self.det.free()
        bm.to_mesh(me2)
        bm.free()
        for p in me2.polygons:
            p.use_smooth = True
        me2.materials.clear()
        me2.materials.append(LL.smooth_material())
        me2.materials.append(LL.glow_material())
        if self.glow_cols:
            ca = me2.color_attributes['Col']
            for p in me2.polygons:
                c = ca.data[p.loop_start].color
                if any(abs(c[0] - g[0]) + abs(c[1] - g[1]) + abs(c[2] - g[2]) < 0.06 for g in self.glow_cols):
                    p.material_index = 1
        # orient: sit on the ground
        z0 = min(v.co.z for v in me2.vertices)
        for v in me2.vertices:
            v.co.z -= z0
        return body


def pixelate(body, target=1400, stud=4.0):
    """low-poly facets + whole studs on every face (the reference look)"""
    me = body.data.copy()
    px = bpy.data.objects.new(body.name.replace('_3D', '') + '_PX', me)
    bpy.context.scene.collection.objects.link(px)
    dec = px.modifiers.new('D', 'DECIMATE')
    dec.ratio = min(1.0, target / max(1, len(me.polygons)))
    dg = bpy.context.evaluated_depsgraph_get()
    low = bpy.data.meshes.new_from_object(px.evaluated_get(dg))
    px.modifiers.clear()
    px.data = low
    bm = bmesh.new()
    bm.from_mesh(low)
    LL.face_uvs_bm(bm, stud)
    bm.to_mesh(low)
    bm.free()
    mats = [LL.stud_material(stud), LL.glow_material()]
    low.materials.clear()
    for m in mats:
        low.materials.append(m)
    for p in low.polygons:
        p.use_smooth = False
    return px


def pixelate2(body, voxel=0.13, glow_cols=()):
    """regular pixel skin: voxel-remesh copy (even square faces), colours copied from the smooth model,
    flat shading and exactly one stud per face"""
    px = bpy.data.objects.new(body.name.replace('_3D', '') + '_PX', body.data.copy())
    bpy.context.scene.collection.objects.link(px)
    rm = px.modifiers.new('R', 'REMESH')
    rm.mode = 'VOXEL'
    rm.voxel_size = voxel
    dt = px.modifiers.new('T', 'DATA_TRANSFER')
    dt.object = body
    dt.use_loop_data = True
    dt.data_types_loops = {'COLOR_CORNER'}
    dt.loop_mapping = 'POLYINTERP_NEAREST'
    dg = bpy.context.evaluated_depsgraph_get()
    low = bpy.data.meshes.new_from_object(px.evaluated_get(dg))
    px.modifiers.clear()
    px.data = low
    bm = bmesh.new()
    bm.from_mesh(low)
    LL.face_uvs_bm(bm, 1.0 / voxel)
    bm.to_mesh(low)
    bm.free()
    low.materials.clear()
    low.materials.append(LL.stud_material(1.0))
    low.materials.append(LL.glow_material())
    ca = low.color_attributes.get('Col') or (low.color_attributes[0] if len(low.color_attributes) else None)
    for p in low.polygons:
        p.use_smooth = False
        if ca and glow_cols:
            c = ca.data[p.loop_start].color
            if any(abs(c[0] - g[0]) + abs(c[1] - g[1]) + abs(c[2] - g[2]) < 0.12 for g in glow_cols):
                p.material_index = 1
    return px



def pixelate3(mb, body_faces=700, stud=3.2):
    """the reference look: the body becomes big flat facets with several studs each; details stay recognisable"""
    z0 = min([v.co.z for v in mb.body_mesh.vertices] + [v.co.z for v in mb.det_mesh.vertices])
    def low(me, ratio):
        o = bpy.data.objects.new('tmp', me.copy())
        bpy.context.scene.collection.objects.link(o)
        d = o.modifiers.new('D', 'DECIMATE')
        d.ratio = ratio
        d.use_symmetry = True
        d.symmetry_axis = 'X'
        dg = bpy.context.evaluated_depsgraph_get()
        out = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        bpy.data.objects.remove(o, do_unlink=True)
        return out
    b = low(mb.body_mesh, min(1.0, body_faces / max(1, len(mb.body_mesh.polygons))))
    d = mb.det_mesh.copy() if len(mb.det_mesh.polygons) else None
    bm = bmesh.new()
    bm.from_mesh(b)
    if d:
        bm.from_mesh(d)
    for v in bm.verts:
        v.co.z -= z0
    bmesh.ops.join_triangles(bm, faces=bm.faces[:], angle_face_threshold=math.radians(25), angle_shape_threshold=math.radians(60))
    LL.face_uvs_bm(bm, stud)
    me = bpy.data.meshes.new(mb.name + '_PX')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(LL.stud_material(1.0))
    me.materials.append(LL.glow_material())
    ca = me.color_attributes.get('Col')
    for p in me.polygons:
        p.use_smooth = False
        if ca and mb.glow_cols:
            c = ca.data[p.loop_start].color
            if any(abs(c[0] - g[0]) + abs(c[1] - g[1]) + abs(c[2] - g[2]) < 0.12 for g in mb.glow_cols):
                p.material_index = 1
    px = bpy.data.objects.new(mb.name + '_PX', me)
    bpy.context.scene.collection.objects.link(px)
    return px


def world_uvs(bm, per_unit):
    """stud rows run horizontally on every face and continue from face to face (world-anchored grid)"""
    uvl = bm.loops.layers.uv.verify()
    bm.normal_update()
    for f in bm.faces:
        n = f.normal
        if abs(n.z) > 0.92:                       # flat tops / bottoms: plain x/y grid
            U, V = Vector((1, 0, 0)), Vector((0, 1, 0))
        else:
            U = Vector((0, 0, 1)).cross(n).normalized()
            V = n.cross(U).normalized()
        for lp in f.loops:
            co = lp.vert.co
            lp[uvl].uv = (co.dot(U) * per_unit, co.dot(V) * per_unit)
