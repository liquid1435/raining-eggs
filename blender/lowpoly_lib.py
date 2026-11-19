r"""Low-poly faceted pet toolkit (the reference "studded shark" style).
Blender axes: x = right, y = back (the pet looks towards -y), z = up. Units ~ studs/2.
Every shape is a loft of 6-8 sided rings or a tapered prism -> flat faces; colours are vertex colours;
the stud tiles come from the material (box projection of tex/stud.png).
"""
import bpy, bmesh, math, pathlib
from mathutils import Vector

HERE = pathlib.Path(__file__).resolve().parent
WHITE = (0.95, 0.95, 0.96)
BLACK = (0.04, 0.04, 0.06)


def rgb(r, g, b):
    return (r / 255, g / 255, b / 255)


class LP:
    def __init__(self, name, smooth=False):
        self.name = name
        self.smooth = smooth          # True: more sides per ring, made for subdivision (the nice 3D model)
        self.bm = bmesh.new()
        self.cl = self.bm.loops.layers.color.new('Col')
        self.glow = False          # set True around calls whose faces should glow (Neon in Roblox)

    # ------------------------------------------------------------ primitives
    def _paint(self, faces, col):
        for f in faces:
            f.normal_update()
            c = col(f.calc_center_median(), f.normal) if callable(col) else col
            for lp in f.loops:
                lp[self.cl] = tuple(c) + (1.0,)
            if self.glow:
                f.material_index = 1

    def loft(self, sects, col, n=8, cap0=True, cap1=True, rot=0.0):
        """sects: list of (centre, half width, half height). Rings are perpendicular to the path, x stays sideways."""
        if self.smooth:
            n = max(n, 12)
        rings = []
        pts = [Vector(s[0]) for s in sects]
        for i, (c, w, h) in enumerate(sects):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            X = Vector((1, 0, 0))
            U = t.cross(X).normalized()
            if U.z < 0:
                U = -U
            ring = []
            for k in range(n):
                a = 2 * math.pi * k / n + math.pi / n + rot
                ring.append(self.bm.verts.new(Vector(c) + X * math.cos(a) * w + U * math.sin(a) * h))
            rings.append(ring)
        faces = []
        for r0, r1 in zip(rings, rings[1:]):
            for k in range(n):
                j = (k + 1) % n
                faces.append(self.bm.faces.new((r0[k], r0[j], r1[j], r1[k])))
        if cap0:
            faces.append(self.bm.faces.new(list(reversed(rings[0]))))
        if cap1:
            faces.append(self.bm.faces.new(rings[-1]))
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)
        self._paint(faces, col)
        return faces

    def limb(self, p0, p1, r0, r1, col, n=6):
        return self.loft([(p0, r0, r0), (p1, r1, r1)], col, n)

    def chain(self, pts, radii, col, n=6):
        return self.loft([(p, r, r) for p, r in zip(pts, radii)], col, n)

    def cone(self, base, tip, r, col, n=5):
        if self.smooth:
            n = max(n, 8)
        base, tip = Vector(base), Vector(tip)
        t = (tip - base).normalized()
        X = Vector((1, 0, 0)) if abs(t.x) < 0.9 else Vector((0, 1, 0))
        U = t.cross(X).normalized()
        X = U.cross(t).normalized()
        ring = [self.bm.verts.new(base + X * math.cos(2 * math.pi * k / n) * r + U * math.sin(2 * math.pi * k / n) * r) for k in range(n)]
        tv = self.bm.verts.new(tip)
        faces = [self.bm.faces.new((ring[k], ring[(k + 1) % n], tv)) for k in range(n)]
        faces.append(self.bm.faces.new(list(reversed(ring))))
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)
        self._paint(faces, col)
        return faces

    def box(self, c, s, col):
        c = Vector(c)
        v = [self.bm.verts.new(c + Vector((sx * s[0], sy * s[1], sz * s[2]))) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
        idx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        faces = [self.bm.faces.new([v[i] for i in q]) for q in idx]
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)
        self._paint(faces, col)
        return faces

    def tri(self, p0, p1, p2, col, thick=0.08):
        a = [self.bm.verts.new(p) for p in (p0, p1, p2)]
        nrm = (Vector(p1) - Vector(p0)).cross(Vector(p2) - Vector(p0)).normalized() * thick
        b = [self.bm.verts.new(Vector(p) + nrm) for p in (p0, p1, p2)]
        fs = [self.bm.faces.new(a), self.bm.faces.new((b[2], b[1], b[0]))]
        for i in range(3):
            j = (i + 1) % 3
            fs.append(self.bm.faces.new((a[i], a[j], b[j], b[i])))
        bmesh.ops.recalc_face_normals(self.bm, faces=fs)
        self._paint(fs, col)
        return fs

    def eye(self, c, side, size=0.16, look=(0, -1, 0)):
        """black eye with a white sparkle, sitting on the surface facing 'side' (+1 right, -1 left)"""
        c = Vector(c)
        if self.smooth:
            self.sphere(c, size * 1.05, BLACK, (0.7, 1.0, 1.15))
            self.sphere(c + Vector((side * size * 0.32, -size * 0.55, size * 0.4)), size * 0.3, WHITE)
            return
        self.box(c, (size * 0.35, size, size * 1.1), BLACK)
        self.box(c + Vector((side * size * 0.3, -size * 0.35, size * 0.4)), (size * 0.12, size * 0.28, size * 0.3), WHITE)

    def sphere(self, c, r, col, scale=(1, 1, 1)):
        res = bmesh.ops.create_uvsphere(self.bm, u_segments=12, v_segments=8, radius=r)
        for v in res['verts']:
            v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2])) + Vector(c)
        fs = list({f for v in res['verts'] for f in v.link_faces})
        self._paint(fs, col)
        return fs

    def mirror(self, fn, *a, **k):
        """call a primitive for the right side and a mirrored copy for the left (first point args are mirrored in x)"""
        def mx(v):
            return (-v[0], v[1], v[2]) if isinstance(v, (tuple, list, Vector)) and len(v) == 3 and not isinstance(v[0], (tuple, list, Vector)) else v
        fn(*a, **k)
        a2 = []
        for v in a:
            if isinstance(v, list) and v and isinstance(v[0], (tuple, list)) and len(v[0]) == 3 and not isinstance(v[0][0], (tuple, list)):
                a2.append([mx(p) for p in v])
            elif isinstance(v, list) and v and isinstance(v[0], tuple) and isinstance(v[0][0], (tuple, list)):
                a2.append([(mx(s[0]),) + tuple(s[1:]) for s in v])
            else:
                a2.append(mx(v))
        fn(*a2, **k)

    # ------------------------------------------------------------ finish
    def face_uvs(self, per_unit=4.5):
        """each face gets its own UV grid, lined up with its longest edge, stretched to a whole number of studs
        -> straight rows on every facet, no half studs at the edges"""
        uvl = self.bm.loops.layers.uv.verify()
        for f in self.bm.faces:
            vs = [lp.vert.co for lp in f.loops]
            edges = [(vs[(i + 1) % len(vs)] - vs[i]) for i in range(len(vs))]
            e = max(edges, key=lambda v: v.length)
            if e.length < 1e-6:
                continue
            U = e.normalized()
            n = f.normal if f.normal.length > 0 else Vector((0, 0, 1))
            V = n.cross(U).normalized()
            us = [(v - vs[0]).dot(U) for v in vs]
            ws = [(v - vs[0]).dot(V) for v in vs]
            u0, u1, w0, w1 = min(us), max(us), min(ws), max(ws)
            nu = max(1, round((u1 - u0) * per_unit))
            nw = max(1, round((w1 - w0) * per_unit))
            for lp, uu, ww in zip(f.loops, us, ws):
                lp[uvl].uv = ((uu - u0) / max(u1 - u0, 1e-6) * nu, (ww - w0) / max(w1 - w0, 1e-6) * nw)

    def done(self, stud_scale=4.5):
        self.face_uvs(stud_scale)
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        o = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(o)
        for p in me.polygons:
            p.use_smooth = False
        me.materials.append(stud_material(stud_scale))
        me.materials.append(glow_material())
        return o


_MAT = {}


def glow_material():
    if 'glow' in _MAT and _MAT['glow'].name in bpy.data.materials:
        return _MAT['glow']
    m = bpy.data.materials.new('Glow')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    vc = nt.nodes.new('ShaderNodeVertexColor')
    vc.layer_name = 'Col'
    nt.links.new(vc.outputs['Color'], b.inputs['Base Color'])
    nt.links.new(vc.outputs['Color'], b.inputs['Emission Color'])
    b.inputs['Emission Strength'].default_value = 4.0
    _MAT['glow'] = m
    return m


def stud_material(scale):
    if scale in _MAT and _MAT[scale].name in bpy.data.materials:
        return _MAT[scale]
    img = bpy.data.images.load(str(HERE / 'tex' / 'stud.png'), check_existing=True)
    m = bpy.data.materials.new('Stud')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    vc = nt.nodes.new('ShaderNodeVertexColor')
    vc.layer_name = 'Col'
    tcn = nt.nodes.new('ShaderNodeTexCoord')
    tx = nt.nodes.new('ShaderNodeTexImage')
    tx.image = img
    tx.interpolation = 'Linear'
    nt.links.new(tcn.outputs['UV'], tx.inputs['Vector'])        # per-face UVs (face_uvs): whole studs, aligned to each facet
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 1.0
    nt.links.new(vc.outputs['Color'], mix.inputs['A'])
    nt.links.new(tx.outputs['Color'], mix.inputs['B'])
    br = nt.nodes.new('ShaderNodeBrightContrast')
    br.inputs['Bright'].default_value = 0.05
    nt.links.new(mix.outputs['Result'], br.inputs['Color'])
    nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.5
    _MAT[scale] = m
    return m


def two_tone(top, belly, split=-0.25, extra=None):
    """colour by face normal: belly colour on faces looking down"""
    def f(c, n):
        if extra:
            r = extra(c, n)
            if r:
                return r
        return belly if n.z < split else top
    return f


# ---------------------------------------------------------------- templates
def quadruped(P, body_col, L=4.0, W=1.3, H=1.25, leg=1.6, legr=0.32, neck=0.5, head=(0.75, 0.8, 0.7), snout=(0.5, 0.42, 0.5),
              snout_col=None, hoof=BLACK, tail=None, ears=None, ear_col=None, eye_z=0.15, head_up=0.35):
    """generic four-legged animal standing on the ground; returns the useful points"""
    z0 = leg + H * 0.9
    body = [((0, -L * 0.5, z0 + 0.05), W * 0.55, H * 0.6), ((0, -L * 0.38, z0 + 0.1), W * 0.95, H * 1.0), ((0, -L * 0.1, z0), W, H),
            ((0, L * 0.2, z0 - 0.05), W * 0.95, H * 0.95), ((0, L * 0.42, z0), W * 0.85, H * 0.9), ((0, L * 0.52, z0 + 0.05), W * 0.45, H * 0.55)]
    P.loft(body, body_col)
    # neck + head + snout as one loft
    hc = Vector((0, -L * 0.5 - head[1] * 0.6 - neck * 0.3, z0 + H * 0.5 + head_up))
    sc_ = snout_col or body_col
    P.loft([((0, -L * 0.36, z0 + H * 0.3), W * 0.55, H * 0.6), ((0, hc.y + head[1] * 0.6, hc.z - head[2] * 0.2), head[0] * 0.9, head[2] * 0.85),
            (tuple(hc), head[0], head[2]), ((0, hc.y - head[1] * 0.75, hc.z - head[2] * 0.12), head[0] * 0.8, head[2] * 0.75)], body_col)
    sn = hc + Vector((0, -head[1] * 0.75, -head[2] * 0.3))
    P.loft([(tuple(sn + Vector((0, 0.1, 0))), snout[0], snout[1]), (tuple(sn + Vector((0, -snout[2], -0.05))), snout[0] * 0.85, snout[1] * 0.8)], sc_)
    nose = sn + Vector((0, -snout[2] - 0.02, snout[1] * 0.35))
    P.box(nose, (snout[0] * 0.35, 0.05, snout[1] * 0.18), BLACK)
    for sx in (-1, 1):
        P.eye((sx * head[0] * 0.82, hc.y - head[1] * 0.35, hc.z + eye_z), sx)
    # legs: shoulder -> knee -> ground, hoof
    for ly in (-L * 0.32, L * 0.34):
        for sx in (-1, 1):
            top = Vector((sx * W * 0.55, ly, z0 - H * 0.4))
            knee = Vector((sx * W * 0.6, ly + (0.12 if ly < 0 else -0.1), leg * 0.5))
            foot = Vector((sx * W * 0.6, ly - 0.05, 0.22))
            P.loft([(tuple(top), legr * 1.35, legr * 1.35), (tuple(knee), legr, legr), (tuple(foot), legr * 0.9, legr * 0.9)], body_col, n=6)
            P.loft([(tuple(foot), legr * 1.05, legr * 1.05), ((foot.x, foot.y - 0.05, 0.0), legr * 1.15, legr * 1.15)], hoof, n=6)
    if ears:
        for sx in (-1, 1):
            b = Vector((sx * head[0] * 0.55, hc.y + head[1] * 0.3, hc.z + head[2] * 0.75))
            P.cone(b, b + Vector((sx * ears[0], ears[1], ears[2])), ears[3], ear_col or body_col, n=4)
    if tail:
        tb = Vector((0, L * 0.52, z0 + 0.1))
        P.chain([tuple(tb), tuple(tb + Vector((0, tail[0] * 0.5, tail[1] * 0.4))), tuple(tb + Vector((0, tail[0], tail[1])))],
                [tail[2], tail[2] * 0.8, tail[2] * 0.4], tail[3] if len(tail) > 3 else body_col, n=5)
    return {'hc': hc, 'head': head, 'z0': z0, 'L': L, 'W': W, 'H': H, 'sn': sn}


def bird_t(P, col, belly, wing_col, H=1.4, W=1.0, beak_col=rgb(255, 170, 40), leg_col=rgb(240, 150, 40), crest=None, flying=False):
    z = 1.2 if not flying else 2.4
    P.loft([((0, 0.9, z + 0.2), W * 0.4, H * 0.35), ((0, 0.3, z + 0.35), W * 0.95, H * 0.9), ((0, -0.4, z + 0.55), W, H),
            ((0, -0.9, z + 1.25), W * 0.8, H * 0.75), ((0, -1.1, z + 1.85), W * 0.75, H * 0.62), ((0, -1.05, z + 2.25), W * 0.4, H * 0.3)],
           two_tone(col, belly, -0.1))
    hc = Vector((0, -1.15, z + 1.8))
    P.cone(hc + Vector((0, -0.6, -0.05)), hc + Vector((0, -1.25, -0.2)), 0.26, beak_col, n=4)
    for sx in (-1, 1):
        P.eye((sx * W * 0.62, hc.y - 0.35, hc.z + 0.12), sx, 0.14)
        # wing: 3 stacked feather blades
        for k in range(3):
            P.tri((sx * W * 0.9, -0.6 + k * 0.1, z + 1.0), (sx * W * 0.95, 0.6 + k * 0.1, z + 0.9 - k * 0.15),
                  (sx * (W * 1.0 + (1.9 if flying else 0.35) - k * 0.3), 1.3 + k * 0.25, z + (1.7 if flying else 0.25) - k * 0.25), wing_col if k else col, 0.1)
        if not flying:
            P.limb((sx * 0.35, -0.3, z - 0.3), (sx * 0.35, -0.35, 0.15), 0.09, 0.08, leg_col, n=4)
            P.tri((sx * 0.35 - 0.2, -0.35, 0.02), (sx * 0.35 + 0.2, -0.35, 0.02), (sx * 0.35, -0.85, 0.02), leg_col, 0.08)
    for k, a in enumerate((-0.35, 0, 0.35)):
        P.tri((a * 0.4, 0.9, z + 0.4), (a * 0.4 + 0.12, 0.9, z + 0.5), (a * 1.4, 2.1, z + 0.2 + abs(a) * 0.3), wing_col, 0.08)
    if crest:
        for k in range(3):
            P.cone(hc + Vector((0, 0.1 + k * 0.2, 0.55)), hc + Vector((0, 0.4 + k * 0.35, 1.2 - k * 0.2)), 0.12, crest, n=4)
    return {'hc': hc}


# ---------------------------------------------------------------- render helpers
def stage(sky=(0.55, 0.8, 1.0)):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.eevee.taa_render_samples = 48
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('W')
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = sky + (1,)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.85
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(-130))
    sc.collection.objects.link(sun)
    bpy.ops.mesh.primitive_plane_add(size=400)
    g = bpy.context.object
    gm = bpy.data.materials.new('G')
    gm.use_nodes = True
    gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.2, 0.62, 0.1, 1)
    g.data.materials.append(gm)
    sc.use_nodes = True
    cn = sc.node_tree
    gl = cn.nodes.new('CompositorNodeGlare')
    gl.glare_type = 'FOG_GLOW'
    gl.threshold = 1.2
    gl.size = 6
    cn.links.new(cn.nodes['Render Layers'].outputs['Image'], gl.inputs['Image'])
    cn.links.new(gl.outputs['Image'], cn.nodes['Composite'].inputs['Image'])
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    cam.data.lens = 45
    sc.collection.objects.link(cam)
    sc.camera = cam
    return sc, cam


def shoot(sc, cam, obj, path, w=900, h=760, dist=1.0):
    bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    ctr = sum(bb, Vector()) / 8
    size = max((max(v[i] for v in bb) - min(v[i] for v in bb)) for i in range(3))
    d = size * 1.75 * dist + 2
    cam.location = ctr + Vector((-0.62, -0.7, 0.42)).normalized() * d
    cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


# ---------------------------------------------------------------- the two-step pipeline: nice 3D model -> pixelated copy
def face_uvs_bm(bm, per_unit=4.0):
    tmp = LP.__new__(LP)
    tmp.bm = bm
    LP.face_uvs(tmp, per_unit)


def smooth_material():
    if 'smooth' in _MAT and _MAT['smooth'].name in bpy.data.materials:
        return _MAT['smooth']
    m = bpy.data.materials.new('Smooth')
    m.use_nodes = True
    nt = m.node_tree
    vc = nt.nodes.new('ShaderNodeVertexColor')
    vc.layer_name = 'Col'
    b = nt.nodes['Principled BSDF']
    nt.links.new(vc.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.38
    b.inputs['Coat Weight'].default_value = 0.25
    _MAT['smooth'] = m
    return m


def make_both(P, target_faces=4500, stud=4.0):
    """P (built with smooth=True) -> (smooth object with subdivision, pixelated low-poly object with aligned studs)"""
    me = bpy.data.meshes.new(P.name + '_3D')
    P.bm.to_mesh(me)
    P.bm.free()
    sm = bpy.data.objects.new(P.name + '_3D', me)
    bpy.context.scene.collection.objects.link(sm)
    me.materials.append(smooth_material())
    me.materials.append(glow_material())
    for p in me.polygons:
        p.use_smooth = True
    sub = sm.modifiers.new('Sub', 'SUBSURF')
    sub.levels = sub.render_levels = 1
    dg = bpy.context.evaluated_depsgraph_get()
    n1 = len(sm.evaluated_get(dg).data.polygons)
    dec = sm.modifiers.new('Dec', 'DECIMATE')
    dec.ratio = min(1.0, target_faces / max(1, n1))
    dg = bpy.context.evaluated_depsgraph_get()
    low = bpy.data.meshes.new_from_object(sm.evaluated_get(dg))
    sm.modifiers.remove(dec)
    sub.levels = sub.render_levels = 2
    px = bpy.data.objects.new(P.name + '_PX', low)
    bpy.context.scene.collection.objects.link(px)
    bm = bmesh.new()
    bm.from_mesh(low)
    face_uvs_bm(bm, stud)
    bm.to_mesh(low)
    bm.free()
    mats = [stud_material(stud), glow_material()]
    low.materials.clear()
    for m in mats:
        low.materials.append(m)
    for p in low.polygons:
        p.use_smooth = False
    return sm, px
