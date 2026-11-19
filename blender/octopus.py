r"""Big octopus: 1) a smooth, good-looking 3D model, 2) the same model made low-poly + stud tiles ("pixelated").
  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P octopus.py
-> out\octopus_smooth.png, out\octopus_studs.png
"""
import bpy, bmesh, math, sys, pathlib, hashlib
from mathutils import Vector
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lowpoly_lib as LL

HERE = pathlib.Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

TOP = (0.62, 0.16, 0.62)       # deep magenta-purple
SPOT = (0.95, 0.45, 0.85)
UNDER = (1.0, 0.72, 0.82)
SUCK = (1.0, 0.86, 0.9)

bm = bmesh.new()
cl = bm.loops.layers.color.new('Col')


def paint(faces, fn):
    for f in faces:
        f.normal_update()
        c = fn(f.calc_center_median(), f.normal) if callable(fn) else fn
        for lp in f.loops:
            lp[cl] = tuple(c) + (1.0,)


def tube(pts, radii, col, n=12, cap_end=True):
    """tube along a path with a rotation-minimising frame (no twisting)"""
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
        rings.append([bm.verts.new(p + side * math.cos(2 * math.pi * k / n) * radii[i] + up * math.sin(2 * math.pi * k / n) * radii[i]) for k in range(n)])
    faces = []
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(n):
            j = (k + 1) % n
            faces.append(bm.faces.new((r0[k], r0[j], r1[j], r1[k])))
    if cap_end:
        faces.append(bm.faces.new(rings[-1]))
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    paint(faces, col)
    return faces


def spotty(c, n):
    h = int(hashlib.md5(f'{round(c.x * 1.6)},{round(c.y * 1.6)},{round(c.z * 1.6)}'.encode()).hexdigest()[:2], 16)
    return SPOT if (h < 40 and c.z > 2.2) else TOP


# --- mantle (the big head), slightly tilted back
prof = [(1.0, 0.0), (1.45, 1.75), (2.2, 2.2), (3.0, 2.35), (3.8, 2.2), (4.6, 1.85), (5.3, 1.3), (5.8, 0.7), (6.05, 0.05)]
rings = []
N = 20
for z, r in prof:
    back = (z - 1.0) * 0.28
    rings.append([bm.verts.new((math.cos(2 * math.pi * k / N) * r, math.sin(2 * math.pi * k / N) * r * 1.05 + back, z)) for k in range(N)])
mf = []
for r0, r1 in zip(rings, rings[1:]):
    for k in range(N):
        j = (k + 1) % N
        mf.append(bm.faces.new((r0[k], r0[j], r1[j], r1[k])))
bmesh.ops.recalc_face_normals(bm, faces=mf)
paint(mf, spotty)
# skirt under the mantle, where the arms meet
sk = []
skr = [bm.verts.new((math.cos(2 * math.pi * k / N) * 1.9, math.sin(2 * math.pi * k / N) * 1.9, 0.75)) for k in range(N)]
for k in range(N):
    j = (k + 1) % N
    sk.append(bm.faces.new((skr[k], skr[j], rings[0][j], rings[0][k])))
c0 = bm.verts.new((0, 0, 0.55))
for k in range(N):
    sk.append(bm.faces.new((skr[(k + 1) % N], skr[k], c0)))
bmesh.ops.recalc_face_normals(bm, faces=sk)
paint(sk, UNDER)

# --- 8 arms: out across the ground, tips curl up
for i in range(8):
    a = 2 * math.pi * i / 8 + math.pi / 8
    d = Vector((math.cos(a), math.sin(a), 0))
    pts, rad = [], []
    for k in range(15):
        t = k / 14
        p = d * (1.4 + 3.6 * t) + Vector((0, 0, max(0.32, 1.05 - 1.6 * t)))
        pts.append(p)
        rad.append(0.62 * (1 - t) + 0.22)
    c = pts[-1] + d * 0.55 + Vector((0, 0, 0.35))
    for k in range(1, 12):
        u = k / 11
        ang = math.pi * 1.35 * u
        v = -d * math.cos(ang) * 0.55 * (1 - u * 0.45) + Vector((0, 0, -math.sin(ang) * 0.55 * (1 - u * 0.45)))
        side_curl = Vector((-d.y, d.x, 0)) * math.sin(u * math.pi) * 0.15
        pts.append(c + v * -1 + side_curl)
        rad.append(0.22 * (1 - u) + 0.04)
    # alternate arm colour: purple top, pink underside
    fs = tube(pts, rad, lambda cc, nn: UNDER if nn.z < -0.25 else TOP, n=12)
    # suckers: little pale discs under each arm
    for k in range(2, 13, 2):
        p, r = pts[k], rad[k]
        for s in (-1, 1):
            q = p + Vector((-d.y, d.x, 0)) * r * 0.45 * s + Vector((0, 0, -r * 0.82))
            tube([q + Vector((0, 0, 0.06)), q - Vector((0, 0, 0.05))], [r * 0.32, r * 0.3], SUCK, n=8)

# --- big eyes with bulging lids
for s in (-1, 1):
    ec = Vector((s * 1.55, -1.3, 2.75))
    res = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.62)
    for v in res['verts']:
        v.co = v.co + ec
    ef = list({f for v in res['verts'] for f in v.link_faces})
    paint(ef, lambda cc, nn, ec=ec: (0.05, 0.05, 0.08) if ((cc - ec).normalized().dot(Vector((s * 0.55, -0.83, 0.05)).normalized()) > 0.82 and abs(cc.z - ec.z) < 0.18)
          else (1.0, 0.86, 0.3))
    res = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.72)
    for v in res['verts']:
        v.co = Vector((v.co.x, v.co.y, max(v.co.z, 0.12) * 1.0)) + ec + Vector((0, 0.05, 0.08))
    lf = list({f for v in res['verts'] for f in v.link_faces})
    paint(lf, TOP)
    hi = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.11)
    for v in hi['verts']:
        v.co = v.co + ec + Vector((s * 0.2, -0.55, 0.18))
    paint(list({f for v in hi['verts'] for f in v.link_faces}), (1, 1, 1))

me = bpy.data.meshes.new('Octopus')
bm.to_mesh(me)
bm.free()
octo = bpy.data.objects.new('Octopus', me)
sc.collection.objects.link(octo)

# ---------------------------------------------------------------- 1) smooth version
m = bpy.data.materials.new('Smooth')
m.use_nodes = True
nt = m.node_tree
vc = nt.nodes.new('ShaderNodeVertexColor')
vc.layer_name = 'Col'
b = nt.nodes['Principled BSDF']
nt.links.new(vc.outputs['Color'], b.inputs['Base Color'])
b.inputs['Roughness'].default_value = 0.35
b.inputs['Subsurface Weight'].default_value = 0.15
b.inputs['Coat Weight'].default_value = 0.3
me.materials.append(m)
for p in me.polygons:
    p.use_smooth = True
sub = octo.modifiers.new('Sub', 'SUBSURF')
sub.levels = sub.render_levels = 2

scn, cam = LL.stage((0.45, 0.72, 0.98))
cam.data.lens = 40


def shoot(path):
    cam.location = Vector((-9.5, -12.5, 8.5))
    cam.rotation_euler = (Vector((0, 0, 2.2)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.resolution_x, scn.render.resolution_y = 1400, 1050
    scn.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


shoot(HERE / 'out' / 'octopus_smooth.png')

# ---------------------------------------------------------------- 2) "pixelated": same model, low-poly facets + aligned stud tiles
sub.levels = 1
dec = octo.modifiers.new('Dec', 'DECIMATE')
dec.ratio = 0.22
dg = bpy.context.evaluated_depsgraph_get()
low = bpy.data.meshes.new_from_object(octo.evaluated_get(dg))
octo.hide_render = True
lo = bpy.data.objects.new('OctoLow', low)
sc.collection.objects.link(lo)
low.materials.clear()
for p in low.polygons:
    p.use_smooth = False
P = LL.LP('tmp')
P.bm.free()
P.bm = bmesh.new()
P.bm.from_mesh(low)
P.face_uvs(4.0)
P.bm.to_mesh(low)
P.bm.free()
low.materials.append(LL.stud_material(4.0))
print('low-poly faces', len(low.polygons))
shoot(HERE / 'out' / 'octopus_studs.png')
print('done')
