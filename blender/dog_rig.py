"""
Brick Pup - stylized quadruped dog + quadruped armature + looping 60-frame idle animation.
Blender 4.x (tested on 4.2). Text Editor -> New -> paste -> Run Script (Alt+P),
then hover the 3D viewport and press Spacebar.  WARNING: clears the objects of the current scene.
The dog faces -Y (looks at you in Front view, Numpad 1). Units: metres, ~1.5 m tall.
"""
import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree
from mathutils.geometry import intersect_point_line

BRICK_SIZE = 0.11
BONES = ["Root", "Spine", "Chest", "Neck", "Head", "Jaw", "Tail_1", "Tail_2",
         "Leg_FL", "Leg_FR", "Leg_BL", "Leg_BR"]
JAW_OPEN = math.radians(10)


# ------------------------------------------------------------------ scene
def clear_scene():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in list(bpy.context.scene.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.metaballs, bpy.data.armatures, bpy.data.actions):
        for d in list(coll):
            if d.users == 0:
                coll.remove(d)


def link(o):
    bpy.context.scene.collection.objects.link(o)
    return o


# ------------------------------------------------------------------ materials
def brick_material(name, base, mortar_mul=0.6, emit=None, emit_strength=0.0, rough=0.5):
    """Principled BSDF + tri-planar procedural Brick Texture on Generated coordinates
    (the bricks follow every curve of the body and stay glued to it while the rig deforms it)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    bsdf = N("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = rough
    tc = N("ShaderNodeTexCoord")
    mp = N("ShaderNodeMapping")
    mp.name = "BrickMapping"
    L(tc.outputs["Generated"], mp.inputs["Vector"])
    sep = N("ShaderNodeSeparateXYZ")
    L(mp.outputs["Vector"], sep.inputs["Vector"])
    geo = N("ShaderNodeNewGeometry")
    ab = N("ShaderNodeVectorMath")
    ab.operation = 'ABSOLUTE'
    L(geo.outputs["Normal"], ab.inputs[0])
    nsep = N("ShaderNodeSeparateXYZ")
    L(ab.outputs["Vector"], nsep.inputs["Vector"])
    weights = []
    for axis in ("X", "Y", "Z"):
        pw = N("ShaderNodeMath")
        pw.operation = 'POWER'
        L(nsep.outputs[axis], pw.inputs[0])
        pw.inputs[1].default_value = 4.0
        weights.append(pw)
    facs = []
    for a, b in (("Y", "Z"), ("X", "Z"), ("X", "Y")):
        cb = N("ShaderNodeCombineXYZ")
        L(sep.outputs[a], cb.inputs["X"])
        L(sep.outputs[b], cb.inputs["Y"])
        br = N("ShaderNodeTexBrick")
        br.offset = 0.5
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Mortar Size"].default_value = 0.035
        br.inputs["Mortar Smooth"].default_value = 0.3
        br.inputs["Brick Width"].default_value = 1.0
        br.inputs["Row Height"].default_value = 0.5
        L(cb.outputs["Vector"], br.inputs["Vector"])
        facs.append(br)
    num, den = None, None
    for br, w in zip(facs, weights):
        mul = N("ShaderNodeMath")
        mul.operation = 'MULTIPLY'
        L(br.outputs["Fac"], mul.inputs[0])
        L(w.outputs[0], mul.inputs[1])
        if num is None:
            num, den = mul, w
        else:
            a1 = N("ShaderNodeMath"); a1.operation = 'ADD'
            L(num.outputs[0], a1.inputs[0]); L(mul.outputs[0], a1.inputs[1]); num = a1
            a2 = N("ShaderNodeMath"); a2.operation = 'ADD'
            L(den.outputs[0], a2.inputs[0]); L(w.outputs[0], a2.inputs[1]); den = a2
    div = N("ShaderNodeMath")
    div.operation = 'DIVIDE'
    L(num.outputs[0], div.inputs[0])
    L(den.outputs[0], div.inputs[1])
    mix = N("ShaderNodeMix")                 # inputs 0 Factor, 6 A colour, 7 B colour; output 2 colour
    mix.data_type = 'RGBA'
    mix.blend_type = 'MIX'
    L(div.outputs[0], mix.inputs[0])
    mix.inputs[6].default_value = (base[0], base[1], base[2], 1.0)
    mix.inputs[7].default_value = (base[0] * mortar_mul, base[1] * mortar_mul, base[2] * mortar_mul, 1.0)
    L(mix.outputs[2], bsdf.inputs["Base Color"])
    bump = N("ShaderNodeBump")
    bump.invert = True
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.015
    L(div.outputs[0], bump.inputs["Height"])
    L(bump.outputs["Normal"], bsdf.inputs["Normal"])
    if emit is not None:
        em = N("ShaderNodeEmission")
        em.inputs["Color"].default_value = (emit[0], emit[1], emit[2], 1.0)
        em.inputs["Strength"].default_value = emit_strength
        ms = N("ShaderNodeMixShader")
        ms.inputs[0].default_value = 0.6
        L(bsdf.outputs[0], ms.inputs[1])
        L(em.outputs[0], ms.inputs[2])
        L(ms.outputs[0], out.inputs["Surface"])
    else:
        L(bsdf.outputs[0], out.inputs["Surface"])
    return m


def flat_material(name, color, rough=0.6, emit_strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    b.inputs["Roughness"].default_value = rough
    if emit_strength > 0:
        b.inputs["Emission Color"].default_value = (color[0], color[1], color[2], 1.0)
        b.inputs["Emission Strength"].default_value = emit_strength
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


MAT = {}


def make_materials():
    MAT["fur"] = brick_material("Pup_Fur", (0.85, 0.36, 0.05), mortar_mul=0.6)
    MAT["cream"] = brick_material("Pup_Cream", (0.9, 0.84, 0.7), mortar_mul=0.74)
    MAT["glow"] = brick_material("Pup_Glow", (0.35, 0.88, 1.0), mortar_mul=0.7,
                                 emit=(0.3, 0.85, 1.0), emit_strength=3.5, rough=0.3)
    MAT["black"] = flat_material("Pup_Black", (0.012, 0.012, 0.014), rough=0.35)
    MAT["eye"] = flat_material("Pup_Eye", (1.0, 0.78, 0.03), rough=0.15, emit_strength=1.2)
    MAT["shine"] = flat_material("Pup_Shine", (1.0, 1.0, 1.0), rough=0.1, emit_strength=1.5)
    MAT["mouth"] = flat_material("Pup_Mouth", (0.3, 0.01, 0.03), rough=0.5)
    MAT["tongue"] = flat_material("Pup_Tongue", (0.9, 0.22, 0.3), rough=0.35)
    MAT["tooth"] = flat_material("Pup_Tooth", (0.95, 0.95, 0.92), rough=0.3)
    MAT["collar"] = flat_material("Pup_Collar", (0.05, 0.06, 0.12), rough=0.4)


# ------------------------------------------------------------------ mesh helpers
def mesh_from_bm(name, bm, mat, marker=None, smooth=True):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = smooth
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    o = link(bpy.data.objects.new(name, me))
    if marker:
        vg = o.vertex_groups.new(name=marker)
        vg.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    return o


def ellipsoid(name, loc, size, mat, rot=(0, 0, 0), marker=None, seg=20, rings=12):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Euler(rot).to_matrix(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)
    return mesh_from_bm(name, bm, mat, marker)


def cone_between(name, base, tip, r, mat, marker=None, seg=8):
    base, tip = Vector(base), Vector(tip)
    d = tip - base
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=0.0, depth=d.length)
    bmesh.ops.translate(bm, vec=(0, 0, d.length / 2), verts=bm.verts)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=q.to_matrix(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=base, verts=bm.verts)
    return mesh_from_bm(name, bm, mat, marker, smooth=False)


def tube(name, pts, radii, mat, marker=None, seg=10, closed=False):
    """tapered round tube; radius 0 at the end = pointed tip; closed=True = ring (collar)"""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    bm = bmesh.new()
    rings = []
    prev_a = None
    for i, p in enumerate(pts):
        if closed:
            d = pts[(i + 1) % n] - pts[(i - 1) % n]
        elif i == 0:
            d = pts[1] - pts[0]
        elif i == n - 1:
            d = pts[-1] - pts[-2]
        else:
            d = pts[i + 1] - pts[i - 1]
        d.normalize()
        if prev_a is None:
            up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
            a = d.cross(up).normalized()
        else:
            a = (prev_a - d * prev_a.dot(d)).normalized()
        prev_a = a
        b = d.cross(a).normalized()
        r = radii[i]
        if r <= 1e-5:
            rings.append([bm.verts.new(p)])
        else:
            rings.append([bm.verts.new(p + (a * math.cos(t) + b * math.sin(t)) * r)
                          for t in (2 * math.pi * k / seg for k in range(seg))])
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
    for r0, r1 in pairs:
        if len(r1) == 1:
            for k in range(seg):
                bm.faces.new((r0[k], r0[(k + 1) % seg], r1[0]))
        else:
            # closed ring: match the start of the last ring to the nearest vertex of the first ring
            off = 0
            if closed and r1 is rings[0]:
                off = min(range(seg), key=lambda k: (r1[k].co - r0[0].co).length)
            for k in range(seg):
                bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1 + off) % seg], r1[(k + off) % seg]))
    if not closed:
        if len(rings[0]) > 1:
            bm.faces.new(list(reversed(rings[0])))
        if len(rings[-1]) > 1:
            bm.faces.new(rings[-1])
    return mesh_from_bm(name, bm, mat, marker)


def loft(name, sections, mat, marker=None, seg=16, xf=None):
    """rounded-box loft along [(centre, half_width, half_height)], cross-section in the XZ plane"""
    bm = bmesh.new()
    rings = []
    for c, hw, hh in sections:
        ring = []
        for k in range(seg):
            t = 2 * math.pi * k / seg
            ct, st = math.cos(t), math.sin(t)
            p = Vector(c) + Vector((hw * math.copysign(abs(ct) ** 0.6, ct), 0, hh * math.copysign(abs(st) ** 0.6, st)))
            ring.append(bm.verts.new(xf(p) if xf else p))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    return mesh_from_bm(name, bm, mat, marker)


# ------------------------------------------------------------------ body: one smooth closed surface (metaballs)
def build_body():
    mb = bpy.data.metaballs.new("PupMB")
    mb.resolution = mb.render_resolution = 0.03
    mb.threshold = 0.6
    ob = link(bpy.data.objects.new("PupBody", mb))

    def ball(co, r):
        e = mb.elements.new(type='BALL'); e.co, e.radius, e.stiffness = co, r, 2.0

    def ell(co, size, rot=(0, 0, 0)):
        e = mb.elements.new(type='ELLIPSOID'); e.co, e.radius, e.stiffness = co, 1.0, 2.0
        e.size_x, e.size_y, e.size_z = size
        e.rotation = Euler(rot).to_quaternion()

    def box(co, size, r):
        e = mb.elements.new(type='CUBE'); e.co, e.radius, e.stiffness = co, r, 2.0
        e.size_x, e.size_y, e.size_z = size

    def cap(a, b, r):
        a, b = Vector(a), Vector(b); d = b - a
        e = mb.elements.new(type='CAPSULE'); e.co = (a + b) / 2
        e.radius, e.stiffness, e.size_x = r, 2.0, d.length / 2
        e.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized())

    ell((0, 0.1, 0.72), (0.42, 0.6, 0.4))                 # chunky body
    ball((0, -0.32, 0.82), 0.6)                           # deep chest
    cap((0, -0.4, 0.95), (0, -0.55, 1.2), 0.38)           # neck
    box((0, -0.6, 1.36), (0.2, 0.17, 0.15), 0.32)         # boxy head
    box((0, -0.95, 1.25), (0.1, 0.12, 0.04), 0.2)         # pronounced muzzle
    for s in (-1, 1):
        ell((s * 0.27, -0.66, 1.3), (0.13, 0.13, 0.12))   # cheeks
        cap((s * 0.2, -0.36, 0.6), (s * 0.21, -0.4, 0.15), 0.22)     # front legs
        ell((s * 0.21, -0.47, 0.09), (0.15, 0.2, 0.1))              # front paws
        ell((s * 0.23, 0.36, 0.62), (0.2, 0.27, 0.3))               # thighs
        cap((s * 0.23, 0.42, 0.5), (s * 0.22, 0.38, 0.15), 0.2)     # back legs
        ell((s * 0.22, 0.31, 0.09), (0.15, 0.2, 0.1))               # back paws
    cap((0, 0.6, 0.86), (0, 0.76, 1.03), 0.15)            # upturned tail
    cap((0, 0.76, 1.03), (0, 0.82, 1.28), 0.12)
    ball((0, 0.82, 1.32), 0.17)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target='MESH')
    body = bpy.context.view_layer.objects.active
    body.name = "Pup"
    body.data.materials.clear()
    body.data.materials.append(MAT["fur"])
    body.data.materials.append(MAT["cream"])
    for p in body.data.polygons:
        p.use_smooth = True
    return body


def make_caster(body):
    me = body.data
    bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])

    def hit(origin, direction, fallback):
        loc, nrm, idx, dist = bvh.ray_cast(Vector(origin), Vector(direction).normalized())
        if loc is None:
            return Vector(fallback), -Vector(direction).normalized()
        return loc, nrm
    return hit


def paint_zones(body, K):
    """flat colour zones (no blending): cream muzzle, chest, belly, paws, tail tip and forehead blaze"""
    for p in body.data.polygons:
        c, n = p.center, p.normal
        cream = (c.y < K["muzzle_front"] + 0.2 and c.z < K["muzzle_bot"] + 0.14) \
            or (n.y < -0.3 and abs(c.x) < 0.22 and 0.45 < c.z < 1.08 and c.y < -0.3) \
            or (n.z < -0.4 and abs(c.x) < 0.26 and -0.35 < c.y < 0.45 and c.z > 0.3) \
            or c.z < 0.17 \
            or (c.y > 0.78 and c.z > 1.22) \
            or (abs(c.x) < 0.055 and n.y < -0.3 and c.z > K["eye_z"] + 0.04 and c.y < -0.6)
        p.material_index = 1 if cream else 0


# ------------------------------------------------------------------ face, ears, mouth, collar, claws
def build_details(body):
    hit = make_caster(body)
    K = {}
    mbot, _ = hit((0, -0.95, 0.3), (0, 0, 1), (0, -0.95, 1.12))
    K["muzzle_bot"] = mbot.z
    mfront, _ = hit((0, -3, mbot.z + 0.07), (0, 1, 0), (0, -1.2, mbot.z + 0.07))
    K["muzzle_front"] = mfront.y
    K["eye_z"] = 1.43
    K["hinge"] = Vector((0, -0.74, mbot.z))
    hinge = K["hinge"]
    R = Matrix.Rotation(JAW_OPEN, 3, 'X')
    jaw_xf = lambda p: hinge + R @ (Vector(p) - hinge)
    K["jaw_xf"] = jaw_xf
    zb, yf = mbot.z, mfront.y

    # eyes: bright yellow, dark pupil, white glint
    for s in (-1, 1):
        p, n = hit((s * 0.16, -3, K["eye_z"]), (0, 1, 0), (s * 0.16, -0.95, K["eye_z"]))
        ellipsoid("Eye", p - n * 0.015, (0.075, 0.045, 0.085), MAT["eye"], marker="_head")
        ellipsoid("Pupil", p + n * 0.026 + Vector((s * -0.01, 0, -0.005)), (0.04, 0.012, 0.05), MAT["black"], marker="_head")
        ellipsoid("Glint", p + n * 0.04 + Vector((s * -0.025, 0, 0.025)), (0.014, 0.006, 0.016), MAT["shine"], marker="_head")
        ellipsoid("Brow", p + n * 0.01 + Vector((0, 0, 0.11)), (0.075, 0.03, 0.022), MAT["fur"],
                  rot=(0, s * math.radians(-14), 0), marker="_head")

    # nose
    p, n = hit((0, -3, zb + 0.1), (0, 1, 0), (0, yf, zb + 0.1))
    ellipsoid("Nose", p + n * 0.01, (0.085, 0.055, 0.055), MAT["black"], marker="_head")
    ellipsoid("NoseGlint", p + n * 0.06 + Vector((0.03, 0, 0.02)), (0.02, 0.008, 0.012), MAT["shine"], marker="_head")

    # pointed ears with glowing tips
    for s in (-1, 1):
        top, _ = hit((s * 0.19, -0.55, 3), (0, 0, -1), (s * 0.19, -0.55, 1.75))
        base = top + Vector((0, 0, -0.08))
        mid = top + Vector((s * 0.06, 0.03, 0.17))
        tip = top + Vector((s * 0.1, 0.06, 0.36))
        tube("Ear", [base, mid, mid.lerp(tip, 0.45)], [0.12, 0.08, 0.055], MAT["fur"], marker="_head", seg=12)
        tube("EarTip", [mid.lerp(tip, 0.35), tip], [0.06, 0.0], MAT["glow"], marker="_head", seg=12)

    # mouth: dark palate + throat (head), lower jaw + tongue + teeth (jaw)
    ellipsoid("Palate", (0, (yf - 0.74) / 2 + 0.02, zb + 0.004), (0.12, (-0.74 - yf) / 2, 0.012), MAT["mouth"], marker="_head")
    ellipsoid("Throat", (0, -0.76, zb - 0.02), (0.12, 0.06, 0.06), MAT["mouth"], marker="_head")
    secs, n = [], 8
    for i in range(n + 1):
        t = i / n
        y = -0.74 + (yf + 0.03 + 0.74) * t
        secs.append(((0, y, zb - 0.04), 0.16 - 0.05 * t, 0.042 - 0.008 * t))
    loft("LowerJaw", secs, MAT["cream"], marker="_jaw", xf=jaw_xf)
    ellipsoid("Tongue", jaw_xf((0.0, yf + 0.06, zb + 0.0)), (0.075, 0.13, 0.022), MAT["tongue"],
              rot=(JAW_OPEN, 0, 0), marker="_jaw")
    ellipsoid("TongueTip", jaw_xf((0.02, yf - 0.05, zb - 0.06)), (0.06, 0.03, 0.08), MAT["tongue"],
              rot=(math.radians(20), 0, 0), marker="_jaw")
    for x in (-0.07, -0.025, 0.025, 0.07):
        b = Vector((x, yf + 0.07, zb + 0.012))
        cone_between("ToothU", b, b + Vector((0, 0, -0.04)), 0.014, MAT["tooth"], marker="_head", seg=6)
    for s in (-1, 1):
        b = Vector((s * 0.105, yf + 0.11, zb + 0.012))
        cone_between("Fang", b, b + Vector((0, -0.005, -0.065)), 0.019, MAT["tooth"], marker="_head", seg=6)
        b = Vector((s * 0.09, yf + 0.09, zb - 0.005))
        cone_between("FangL", jaw_xf(b), jaw_xf(b + Vector((0, 0, 0.05))), 0.017, MAT["tooth"], marker="_jaw", seg=6)

    # thick collar with glowing spikes and tag
    cz = 1.04
    cy = -0.4 + (-0.15) * (cz - 0.95) / 0.25
    ctr = Vector((0, cy, cz))
    ring = []
    for k in range(20):
        a = 2 * math.pi * k / 20
        d = Vector((math.cos(a), math.sin(a), 0))
        p, _ = hit(ctr, d, ctr + d * 0.35)
        ring.append(ctr + d * ((p - ctr).length + 0.03))
    tube("Collar", ring, [0.065] * len(ring), MAT["collar"], marker="_neck", seg=10, closed=True)
    for k in range(0, 20, 2):
        p = ring[k]
        d = (p - ctr).normalized()
        if d.y < -0.85:
            continue                                        # leave room for the tag
        cone_between("Spike", p + d * 0.03, p + d * 0.14, 0.035, MAT["glow"], marker="_neck", seg=8)
    front = min(ring, key=lambda q: q.y)
    ellipsoid("TagRing", front + Vector((0, -0.04, -0.05)), (0.025, 0.012, 0.025), MAT["collar"], marker="_neck")
    ellipsoid("Tag", front + Vector((0, -0.05, -0.13)), (0.07, 0.022, 0.08), MAT["glow"],
              rot=(0, math.radians(45), 0), marker="_neck")

    # dark claws on every paw
    for leg, x, yc in (("FL", 0.21, -0.47), ("FR", -0.21, -0.47), ("BL", 0.22, 0.31), ("BR", -0.22, 0.31)):
        for dx in (-0.065, 0.0, 0.065):
            p, _ = hit((x + dx, -3, 0.06), (0, 1, 0), (x + dx, yc - 0.18, 0.06))
            tube("Claw", [p + Vector((0, 0.03, 0.01)), p + Vector((0, -0.03, -0.005)), p + Vector((0, -0.07, -0.04))],
                 [0.024, 0.016, 0.0], MAT["black"], marker="_leg" + leg, seg=8)
    return K


# ------------------------------------------------------------------ armature
def build_armature(K):
    arm = bpy.data.armatures.new("PupRig")
    ob = link(bpy.data.objects.new("PupRig", arm))
    ob.show_in_front = True
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    def eb(name, head, tail, parent=None, connect=False, deform=True):
        b = arm.edit_bones.new(name)
        b.head, b.tail, b.roll = Vector(head), Vector(tail), 0.0
        b.use_deform = deform
        if parent:
            b.parent = arm.edit_bones[parent]
            b.use_connect = connect

    hinge = K["hinge"]
    eb("Root", (0, 0, 0), (0, 0, 0.25), deform=False)
    eb("Spine", (0, 0.55, 0.8), (0, 0.0, 0.82), "Root")
    eb("Chest", (0, 0.0, 0.82), (0, -0.42, 0.9), "Spine", connect=True)
    eb("Neck", (0, -0.42, 0.9), (0, -0.56, 1.2), "Chest", connect=True)
    eb("Head", (0, -0.56, 1.2), (0, -0.58, 1.62), "Neck", connect=True)
    eb("Jaw", hinge, K["jaw_xf"]((0, K["muzzle_front"] + 0.03, hinge.z)), "Head")
    eb("Tail_1", (0, 0.6, 0.86), (0, 0.76, 1.03), "Spine")
    eb("Tail_2", (0, 0.76, 1.03), (0, 0.84, 1.42), "Tail_1", connect=True)
    eb("Leg_FL", (0.2, -0.36, 0.72), (0.21, -0.44, 0.06), "Root")
    eb("Leg_FR", (-0.2, -0.36, 0.72), (-0.21, -0.44, 0.06), "Root")
    eb("Leg_BL", (0.23, 0.38, 0.72), (0.22, 0.33, 0.06), "Root")
    eb("Leg_BR", (-0.23, 0.38, 0.72), (-0.22, 0.33, 0.06), "Root")
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob


def auto_weights(body, arm_ob):
    """Parent With Automatic Weights - on the closed one-piece body, where the heat solver works best"""
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    arm_ob.select_set(True)
    bpy.context.view_layer.objects.active = arm_ob
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    # the upper muzzle is part of the head: only the separate lower-jaw parts may follow the Jaw bone
    jg, hg = body.vertex_groups.get("Jaw"), body.vertex_groups.get("Head")
    if jg is not None:
        hg = hg or body.vertex_groups.new(name="Head")
        moved = {}
        for v in body.data.vertices:
            for g in v.groups:
                if g.group == jg.index and g.weight > 0:
                    moved[v.index] = g.weight
        for i, w in moved.items():
            hw = 0.0
            for g in body.data.vertices[i].groups:
                if g.group == hg.index:
                    hw = g.weight
            hg.add([i], min(1.0, hw + w), 'REPLACE')
        jg.remove(list(moved.keys()))


def lock_to_bone(ob, marker, bone):
    mg = ob.vertex_groups.get(marker)
    if mg is None:
        return
    idx = [v.index for v in ob.data.vertices if any(g.group == mg.index and g.weight > 0.5 for g in v.groups)]
    if not idx:
        return
    for vg in ob.vertex_groups:
        if vg.name in BONES and vg.name != bone:
            vg.remove(idx)
    tg = ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)
    tg.add(idx, 1.0, 'REPLACE')


def nearest_bone_weights(ob, arm_ob, idx):
    segs = [(b.name, b.head_local.copy(), b.tail_local.copy()) for b in arm_ob.data.bones if b.use_deform]
    groups = {n: (ob.vertex_groups.get(n) or ob.vertex_groups.new(name=n)) for n, _, _ in segs}
    buckets = {n: [] for n, _, _ in segs}
    for i in idx:
        co = ob.data.vertices[i].co
        best, bd = None, 1e9
        for n, h, t in segs:
            q, f = intersect_point_line(co, h, t)
            f = min(max(f, 0.0), 1.0)
            dist = (co - h.lerp(t, f)).length
            if dist < bd:
                best, bd = n, dist
        buckets[best].append(i)
    for n, lst in buckets.items():
        if lst:
            groups[n].add(lst, 1.0, 'REPLACE')


def finish_weights(body, arm_ob):
    for marker, bone in (("_head", "Head"), ("_jaw", "Jaw"), ("_neck", "Neck"),
                         ("_legFL", "Leg_FL"), ("_legFR", "Leg_FR"), ("_legBL", "Leg_BL"), ("_legBR", "Leg_BR")):
        lock_to_bone(body, marker, bone)
    bone_ids = {vg.index for vg in body.vertex_groups if vg.name in BONES}
    lost = [v.index for v in body.data.vertices if not any(g.group in bone_ids and g.weight > 0.001 for g in v.groups)]
    if lost:
        nearest_bone_weights(body, arm_ob, lost)
    for vg in list(body.vertex_groups):
        if vg.name.startswith("_"):
            body.vertex_groups.remove(vg)
    print("rig: %d vertices not reached by the heat solver -> nearest bone" % len(lost))


# ------------------------------------------------------------------ animation
def get_fcurves(action):
    try:
        fcs = list(action.fcurves)
        if fcs:
            return fcs
    except AttributeError:
        pass
    out = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                out.extend(cb.fcurves)
    return out


def animate(arm_ob, frames=60):
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, frames
    sc.render.fps = 30
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = arm_ob
    arm_ob.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    pbs = arm_ob.pose.bones
    for pb in pbs:
        pb.rotation_mode = 'QUATERNION'

    def rot_world(name, f, *axis_deg):
        pb = pbs[name]
        M = pb.bone.matrix_local.to_3x3()
        Rw = Matrix.Identity(3)
        for axis, deg in axis_deg:
            Rw = Matrix.Rotation(math.radians(deg), 3, axis) @ Rw
        pb.rotation_quaternion = (M.inverted() @ Rw @ M).to_quaternion()
        pb.keyframe_insert(data_path="rotation_quaternion", frame=f)

    def move_world(name, vec, f):
        pb = pbs[name]
        pb.location = pb.bone.matrix_local.to_3x3().inverted() @ Vector(vec)
        pb.keyframe_insert(data_path="location", frame=f)

    TAU = 2 * math.pi
    for f in range(1, frames + 2, 2):            # key 61 = key 1 -> seamless loop
        t = (f - 1) / frames
        rot_world("Tail_1", f, ('Z', 28 * math.sin(3 * TAU * t)))                 # energetic wag, 3 per loop
        rot_world("Tail_2", f, ('Z', 34 * math.sin(3 * TAU * t - 0.9)))
        move_world("Spine", (0, 0, 0.018 * math.sin(4 * TAU * t)), f)             # panting breath
        rot_world("Chest", f, ('X', 1.5 * math.sin(4 * TAU * t)))
        rot_world("Neck", f, ('X', 3 * math.sin(TAU * t + 0.4)))
        rot_world("Head", f, ('Y', 13 * math.sin(TAU * t)), ('X', -4 * math.sin(2 * TAU * t)))   # playful tilt
        rot_world("Jaw", f, ('X', 9 * (0.5 - 0.5 * math.cos(4 * TAU * t))))       # panting
    act = arm_ob.animation_data.action
    act.name = "Pup_Idle"
    for fc in get_fcurves(act):
        if not any(m.type == 'CYCLES' for m in fc.modifiers):
            fc.modifiers.new(type='CYCLES')
    bpy.ops.object.mode_set(mode='OBJECT')
    sc.frame_set(1)


# ------------------------------------------------------------------ main
def main():
    clear_scene()
    make_materials()
    body = build_body()
    K = build_details(body)
    paint_zones(body, K)
    arm_ob = build_armature(K)
    auto_weights(body, arm_ob)

    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            o.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body = bpy.context.view_layer.objects.active
    body.name = body.data.name = "Pup"
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))      # Blender 4.1+
    except (AttributeError, RuntimeError):
        bpy.ops.object.shade_smooth()
    d = body.dimensions
    for key in ("fur", "cream", "glow"):
        MAT[key].node_tree.nodes["BrickMapping"].inputs["Scale"].default_value = \
            (d.x / BRICK_SIZE, d.y / BRICK_SIZE, d.z / BRICK_SIZE)

    finish_weights(body, arm_ob)
    animate(arm_ob, 60)

    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'MATERIAL'
    bpy.ops.object.select_all(action='DESELECT')
    arm_ob.select_set(True)
    bpy.context.view_layer.objects.active = arm_ob
    print("Pup done: %d faces, rig + 60-frame idle loop. Press Spacebar to play." % len(body.data.polygons))


if __name__ == "__main__":
    main()
