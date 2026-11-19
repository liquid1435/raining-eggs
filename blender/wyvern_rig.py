"""
Crystal Wyvern - procedural creature + armature + looping 60-frame idle/flap animation.
Blender 4.x (tested on 4.2). Paste into the Text Editor and press Run Script (Alt+P),
then press Spacebar in the 3D viewport to play the animation.
The creature faces -Y (it looks at you in Front view, Numpad 1). Units: metres, ~2.5 m tall.
"""
import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler
from mathutils.geometry import intersect_point_line

BRICK_SIZE = 0.16          # length of one brick in metres
BONES = ["Root", "Spine", "Neck", "Head", "Jaw", "Tail_1", "Tail_2", "Wing_L", "Wing_R", "Leg_L", "Leg_R"]


# ------------------------------------------------------------------ scene cleanup
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
    """Principled BSDF with a tri-planar procedural Brick Texture (mortar lines darkened + bumped).
    Uses Generated coordinates, so the bricks stay glued to the mesh while the rig deforms it."""
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
    for a, b in (("Y", "Z"), ("X", "Z"), ("X", "Y")):   # plane seen along X, Y, Z
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

    mix = N("ShaderNodeMix")              # inputs: 0 Factor, 6 A (colour), 7 B (colour); output 2 = colour
    mix.data_type = 'RGBA'
    mix.blend_type = 'MIX'
    L(div.outputs[0], mix.inputs[0])
    mix.inputs[6].default_value = (base[0], base[1], base[2], 1.0)
    mix.inputs[7].default_value = (base[0] * mortar_mul, base[1] * mortar_mul, base[2] * mortar_mul, 1.0)
    L(mix.outputs[2], bsdf.inputs["Base Color"])

    bump = N("ShaderNodeBump")
    bump.invert = True
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.02
    L(div.outputs[0], bump.inputs["Height"])
    L(bump.outputs["Normal"], bsdf.inputs["Normal"])

    if emit is not None:
        em = N("ShaderNodeEmission")
        em.inputs["Color"].default_value = (emit[0], emit[1], emit[2], 1.0)
        em.inputs["Strength"].default_value = emit_strength
        ms = N("ShaderNodeMixShader")
        ms.inputs[0].default_value = 0.55
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
    MAT["body"] = brick_material("Wyvern_Body", (0.03, 0.12, 0.75), mortar_mul=0.55)
    MAT["white"] = brick_material("Wyvern_SkullBelly", (0.88, 0.89, 0.92), mortar_mul=0.72)
    MAT["glow"] = brick_material("Wyvern_GlowCyan", (0.35, 0.85, 1.0), mortar_mul=0.7,
                                 emit=(0.3, 0.85, 1.0), emit_strength=3.0, rough=0.3)
    MAT["claw"] = flat_material("Wyvern_Claw", (0.01, 0.01, 0.012), rough=0.45)
    MAT["mouth"] = flat_material("Wyvern_Mouth", (0.25, 0.01, 0.03), rough=0.5)
    MAT["eye"] = flat_material("Wyvern_Eye", (1.0, 0.75, 0.02), rough=0.2, emit_strength=2.5)
    MAT["tooth"] = flat_material("Wyvern_Tooth", (0.95, 0.95, 0.92), rough=0.3)


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
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return mesh_from_bm(name, bm, mat, marker)


def cone_between(name, base, tip, r, mat, marker=None, seg=6, smooth=False):
    base, tip = Vector(base), Vector(tip)
    d = tip - base
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=0.0, depth=d.length)
    bmesh.ops.translate(bm, vec=(0, 0, d.length / 2), verts=bm.verts)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=q.to_matrix(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=base, verts=bm.verts)
    return mesh_from_bm(name, bm, mat, marker, smooth)


def tube(name, pts, radii, mat, marker=None, seg=10):
    """tapered round tube through pts; radius 0 at the end gives a pointed tip"""
    pts = [Vector(p) for p in pts]
    bm = bmesh.new()
    rings = []
    prev_a = None
    for i, p in enumerate(pts):
        if i == 0:
            d = pts[1] - pts[0]
        elif i == len(pts) - 1:
            d = pts[-1] - pts[-2]
        else:
            d = pts[i + 1] - pts[i - 1]
        d.normalize()
        if prev_a is None:
            up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
            a = d.cross(up).normalized()
        else:
            a = (prev_a - d * prev_a.dot(d)).normalized()     # parallel transport: no twisting
        prev_a = a
        b = d.cross(a).normalized()
        r = radii[i]
        if r <= 1e-5:
            rings.append([bm.verts.new(p)])
        else:
            rings.append([bm.verts.new(p + (a * math.cos(t) + b * math.sin(t)) * r)
                          for t in (2 * math.pi * k / seg for k in range(seg))])
    for r0, r1 in zip(rings, rings[1:]):
        if len(r1) == 1:
            for k in range(seg):
                bm.faces.new((r0[k], r0[(k + 1) % seg], r1[0]))
        else:
            for k in range(seg):
                bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
    if len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    return mesh_from_bm(name, bm, mat, marker)


def loft(name, sections, mat, marker=None, seg=16, xf=None):
    """rounded-box loft along the sections [(centre, half_width, half_height)], cross-section in the XZ plane"""
    bm = bmesh.new()
    rings = []
    for c, hw, hh in sections:
        ring = []
        for k in range(seg):
            t = 2 * math.pi * k / seg
            ct, st = math.cos(t), math.sin(t)
            x = hw * math.copysign(abs(ct) ** 0.6, ct)
            z = hh * math.copysign(abs(st) ** 0.6, st)
            p = Vector(c) + Vector((x, 0, z))
            if xf:
                p = xf(p)
            ring.append(bm.verts.new(p))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    return mesh_from_bm(name, bm, mat, marker)


def plate(name, pts, thick, mat, marker=None):
    """flat polygon (wing membrane) with thickness, centred on the polygon"""
    bm = bmesh.new()
    vs = [bm.verts.new(Vector(p)) for p in pts]
    f = bm.faces.new(vs)
    f.normal_update()
    n = f.normal.copy()
    bmesh.ops.translate(bm, vec=-n * thick / 2, verts=bm.verts)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thick)
    return mesh_from_bm(name, bm, mat, marker, smooth=False)


# ------------------------------------------------------------------ body (metaballs = one smooth organic surface)
def build_body():
    mb = bpy.data.metaballs.new("WyvernBodyMB")
    mb.resolution = 0.035
    mb.render_resolution = 0.035
    mb.threshold = 0.6
    ob = link(bpy.data.objects.new("WyvernBody", mb))

    def ball(co, r, stiff=2.0):
        e = mb.elements.new(type='BALL')
        e.co, e.radius, e.stiffness = co, r, stiff

    def ell(co, r, size, rot=(0, 0, 0)):
        e = mb.elements.new(type='ELLIPSOID')
        e.co, e.radius, e.stiffness = co, r, 2.0
        e.size_x, e.size_y, e.size_z = size
        e.rotation = Euler(rot).to_quaternion()

    def cap(a, b, r, stiff=2.0):
        a, b = Vector(a), Vector(b)
        d = b - a
        e = mb.elements.new(type='CAPSULE')
        e.co = (a + b) / 2
        e.radius, e.stiffness = r, stiff
        e.size_x = d.length / 2
        e.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized())

    # torso, chest, neck
    ell((0, 0.15, 1.22), 1.0, (0.36, 0.55, 0.38), rot=(math.radians(-12), 0, 0))
    ball((0, -0.18, 1.42), 0.48)
    cap((0, -0.2, 1.5), (0, -0.33, 1.82), 0.3)
    cap((0, -0.33, 1.82), (0, -0.4, 2.0), 0.24)
    # tail
    cap((0, 0.55, 1.18), (0, 1.0, 1.08), 0.26)
    cap((0, 1.0, 1.08), (0, 1.45, 1.12), 0.17)
    cap((0, 1.45, 1.12), (0, 1.85, 1.3), 0.09)
    for s in (-1, 1):
        # legs: thigh, shin, ankle, foot
        ell((s * 0.27, 0.22, 0.98), 1.0, (0.17, 0.24, 0.3))
        cap((s * 0.29, 0.3, 0.8), (s * 0.3, 0.42, 0.38), 0.13)
        cap((s * 0.3, 0.42, 0.38), (s * 0.3, 0.32, 0.1), 0.1)
        cap((s * 0.3, 0.38, 0.08), (s * 0.3, 0.08, 0.07), 0.11)
        # small front arms
        cap((s * 0.24, -0.3, 1.32), (s * 0.34, -0.48, 1.12), 0.09)
        cap((s * 0.34, -0.48, 1.12), (s * 0.31, -0.56, 0.95), 0.075)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target='MESH')
    body = bpy.context.view_layer.objects.active
    body.name = "Wyvern"
    me = body.data
    me.materials.clear()
    me.materials.append(MAT["body"])
    me.materials.append(MAT["white"])
    for p in me.polygons:
        c, n = p.center, p.normal
        belly = n.z < -0.2 and abs(c.x) < 0.22 and 0.8 < c.z < 1.55 and -0.45 < c.y < 0.55
        throat = n.y < -0.35 and abs(c.x) < 0.17 and 1.2 < c.z < 2.05 and c.y < -0.15
        p.material_index = 1 if (belly or throat) else 0
        p.use_smooth = True
    return body


# ------------------------------------------------------------------ head
HINGE = Vector((0, -0.4, 1.93))
JAW_OPEN = math.radians(22)
JAW_R = Matrix.Rotation(JAW_OPEN, 3, 'X')


def jaw_xf(p):
    return HINGE + JAW_R @ (Vector(p) - HINGE)


def build_head():
    W, BODY, GLOW = MAT["white"], MAT["body"], MAT["glow"]
    ellipsoid("Cranium", (0, -0.36, 2.03), (0.2, 0.22, 0.17), BODY, marker="_head")
    ellipsoid("HeadTop", (0, -0.52, 2.1), (0.12, 0.2, 0.06), BODY, rot=(math.radians(6), 0, 0), marker="_head")

    up, palate = [], []
    n = 10
    for i in range(n + 1):
        t = i / n
        y = -0.36 - 0.72 * t
        hw = 0.16 - 0.075 * t
        hh = 0.085 - 0.032 * t
        cz = 2.03 - 0.03 * t - (0.02 * (t - 0.8) / 0.2 if t > 0.8 else 0)
        up.append(((0, y, cz), hw, hh))
        palate.append(((0, y, cz - hh + 0.003), max(hw - 0.035, 0.02), 0.012))
    loft("UpperJaw", up, W, marker="_head")
    loft("Palate", palate[1:-1], MAT["mouth"], marker="_head")

    low, floor = [], []
    for i in range(n + 1):
        t = i / n
        y = -0.38 - 0.62 * t
        hw = 0.14 - 0.07 * t
        hh = 0.045 - 0.015 * t
        low.append(((0, y, 1.9), hw, hh))
        floor.append(((0, y, 1.9 + hh - 0.002), max(hw - 0.035, 0.02), 0.012))
    loft("LowerJaw", low, W, marker="_jaw", xf=jaw_xf)
    loft("MouthFloor", floor[1:-1], MAT["mouth"], marker="_jaw", xf=jaw_xf)
    ellipsoid("Tongue", jaw_xf((0, -0.62, 1.95)), (0.06, 0.2, 0.025), MAT["mouth"],
              rot=(JAW_OPEN, 0, 0), marker="_jaw")
    ellipsoid("Throat", (0, -0.47, 1.9), (0.11, 0.1, 0.07), MAT["mouth"], marker="_head")

    # teeth (upper hang down, lower point up)
    for i in range(8):
        t = 0.08 + i * 0.12
        y = -0.36 - 0.72 * t
        hw = 0.16 - 0.075 * t
        hh = 0.085 - 0.032 * t
        cz = 2.03 - 0.03 * t - (0.02 * (t - 0.8) / 0.2 if t > 0.8 else 0)
        ln = 0.07 if i in (1, 5) else 0.05
        for s in (-1, 1):
            b = Vector((s * (hw - 0.025), y, cz - hh + 0.01))
            cone_between("ToothU", b, b + Vector((0, -0.005, -ln)), 0.017, MAT["tooth"], marker="_head")
    for i in range(7):
        t = 0.1 + i * 0.13
        y = -0.38 - 0.62 * t
        hw = 0.14 - 0.07 * t
        hh = 0.045 - 0.015 * t
        for s in (-1, 1):
            b = Vector((s * (hw - 0.022), y, 1.9 + hh - 0.01))
            cone_between("ToothL", jaw_xf(b), jaw_xf(b + Vector((0, -0.004, 0.05))), 0.015, MAT["tooth"], marker="_jaw")

    # eyes: yellow, vertical black slit pupil, angry blue brow
    for s in (-1, 1):
        ellipsoid("Eye", (s * 0.158, -0.5, 2.075), (0.03, 0.062, 0.042), MAT["eye"], marker="_head")
        ellipsoid("Pupil", (s * 0.184, -0.5, 2.075), (0.008, 0.011, 0.034), MAT["claw"], marker="_head")
        ellipsoid("Brow", (s * 0.14, -0.53, 2.125), (0.05, 0.1, 0.022), BODY,
                  rot=(math.radians(-14), 0, s * math.radians(-6)), marker="_head")
        # cyan crests sweeping back
        tube("Crest", [(s * 0.07, -0.36, 2.16), (s * 0.11, -0.22, 2.3), (s * 0.14, -0.02, 2.39), (s * 0.15, 0.1, 2.4)],
             [0.045, 0.035, 0.018, 0.0], GLOW, marker="_head")
        tube("Crest2", [(s * 0.14, -0.4, 2.1), (s * 0.2, -0.28, 2.19), (s * 0.24, -0.14, 2.22)],
             [0.03, 0.018, 0.0], GLOW, marker="_head")
        tube("Cheek", [(s * 0.17, -0.34, 1.98), (s * 0.25, -0.24, 2.0), (s * 0.3, -0.14, 2.0)],
             [0.03, 0.018, 0.0], GLOW, marker="_head")


# ------------------------------------------------------------------ wings
def build_wing(s):
    side = "L" if s > 0 else "R"
    mk = "_wing" + side
    P = lambda x, y, z: Vector((s * x, y, z))
    lead = [P(0.2, 0.0, 1.52), P(0.85, 0.18, 2.05), P(1.45, 0.38, 2.32), P(1.95, 0.55, 2.48)]
    trail = [P(1.8, 0.82, 2.05), P(1.63, 0.74, 2.1), P(1.5, 1.0, 1.72), P(1.33, 0.88, 1.8),
             P(1.13, 1.02, 1.45), P(0.96, 0.9, 1.55), P(0.74, 0.94, 1.25), P(0.52, 0.8, 1.33), P(0.24, 0.56, 1.2)]
    a, b = lead[0], lead[-1]
    inner = []
    for p in trail:
        q, t = intersect_point_line(p, a, b)
        t = min(max(t, 0.0), 1.0)
        inner.append(p.lerp(a.lerp(b, t), 0.3))
    plate("WingEdge_" + side, lead + trail, 0.03, MAT["glow"], marker=mk)
    plate("WingMembrane_" + side, lead + inner, 0.05, MAT["body"], marker=mk)
    tube("WingArm_" + side, lead, [0.075, 0.06, 0.045, 0.0], MAT["body"], marker=mk)
    # glowing crystal shards on the outer edge
    for i, p in enumerate(trail[:-1]):
        if i % 2 == 0:
            d = (p - inner[i]).normalized()
            cone_between("Shard", p - d * 0.1, p + d * (0.3 + 0.03 * i), 0.055, MAT["glow"], marker=mk, seg=4)
    cone_between("Shard", lead[-1] - (lead[-1] - lead[-2]).normalized() * 0.1,
                 lead[-1] + (lead[-1] - lead[-2]).normalized() * 0.3, 0.05, MAT["glow"], marker=mk, seg=4)
    # wrist claw
    w = lead[2]
    tube("WingClaw_" + side, [w, w + P(0.02, -0.12, 0.1), w + P(0.0, -0.22, 0.08)], [0.03, 0.02, 0.0], MAT["claw"], marker=mk)


# ------------------------------------------------------------------ claws + back spikes
def build_claws_and_spikes():
    for s in (-1, 1):
        mk = "_leg" + ("L" if s > 0 else "R")
        x = s * 0.3
        for dx in (-0.07, 0.0, 0.07):
            tube("ToeClaw", [(x + dx, 0.0, 0.08), (x + dx * 1.2, -0.1, 0.06), (x + dx * 1.3, -0.17, 0.0)],
                 [0.035, 0.022, 0.0], MAT["claw"], marker=mk)
        tube("HeelClaw", [(x - s * 0.06, 0.08, 0.12), (x - s * 0.1, 0.0, 0.2), (x - s * 0.11, -0.06, 0.24)],
             [0.025, 0.015, 0.0], MAT["claw"], marker=mk)
        for dz in (-0.03, 0.0, 0.03):
            tube("HandClaw", [(s * 0.31, -0.6, 0.92 + dz), (s * 0.32, -0.66, 0.86 + dz), (s * 0.31, -0.7, 0.79 + dz)],
                 [0.018, 0.012, 0.0], MAT["claw"], marker="_spine")
    spine = [(-0.28, 2.05), (-0.18, 1.85), (-0.05, 1.7), (0.12, 1.58), (0.32, 1.52), (0.55, 1.44),
             (0.8, 1.36), (1.05, 1.3), (1.3, 1.28), (1.55, 1.33), (1.75, 1.42)]
    for i, (y, z) in enumerate(spine):
        h = 0.16 - 0.08 * abs(i - 4) / 6
        mk = "_tail1" if 0.55 < y <= 1.1 else ("_tail2" if y > 1.1 else ("_neck" if y < -0.1 else "_spine"))
        tube("BackSpike", [(0, y, z - 0.05), (0, y + h * 0.35, z + h * 0.7), (0, y + h * 0.8, z + h * 1.05)],
             [0.045 * (h / 0.16) + 0.012, 0.025, 0.0], MAT["glow"], marker=mk)


# ------------------------------------------------------------------ armature
def build_armature():
    arm = bpy.data.armatures.new("WyvernRig")
    ob = link(bpy.data.objects.new("WyvernRig", arm))
    ob.show_in_front = True
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    def eb(name, head, tail, parent=None, connect=False, deform=True):
        b = arm.edit_bones.new(name)
        b.head, b.tail, b.roll = head, tail, 0.0
        b.use_deform = deform
        if parent:
            b.parent = arm.edit_bones[parent]
            b.use_connect = connect
        return b

    eb("Root", (0, 0, 0), (0, 0, 0.3), deform=False)
    eb("Spine", (0, 0.4, 1.15), (0, -0.18, 1.45), "Root")
    eb("Neck", (0, -0.18, 1.45), (0, -0.38, 1.95), "Spine", connect=True)
    eb("Head", (0, -0.38, 1.95), (0, -1.05, 2.02), "Neck", connect=True)
    eb("Jaw", tuple(HINGE), tuple(jaw_xf((0, -1.0, 1.9))), "Head")
    eb("Tail_1", (0, 0.5, 1.15), (0, 1.15, 1.08), "Spine")
    eb("Tail_2", (0, 1.15, 1.08), (0, 1.9, 1.32), "Tail_1", connect=True)
    eb("Wing_L", (0.2, 0.0, 1.52), (1.45, 0.38, 2.32), "Spine")
    eb("Wing_R", (-0.2, 0.0, 1.52), (-1.45, 0.38, 2.32), "Spine")
    eb("Leg_L", (0.27, 0.22, 1.05), (0.3, 0.35, 0.1), "Root")
    eb("Leg_R", (-0.27, 0.22, 1.05), (-0.3, 0.35, 0.1), "Root")
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob


def lock_to_bone(ob, marker, bone):
    """give every vertex of a marker group 100% to one bone (rigid parts: skull, jaw, wings, claws)"""
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


def auto_weights(body, arm_ob):
    """With Automatic Weights on the smooth one-piece body only (the heat solver works best on a closed mesh)"""
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    arm_ob.select_set(True)
    bpy.context.view_layer.objects.active = arm_ob
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')


def nearest_bone_weights(ob, arm_ob, idx):
    """fallback for vertices the heat solver could not reach: 100% to the closest deforming bone"""
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
    for marker, bone in (("_head", "Head"), ("_jaw", "Jaw"), ("_wingL", "Wing_L"), ("_wingR", "Wing_R"),
                         ("_legL", "Leg_L"), ("_legR", "Leg_R"), ("_neck", "Neck"), ("_spine", "Spine"),
                         ("_tail1", "Tail_1"), ("_tail2", "Tail_2")):
        lock_to_bone(body, marker, bone)

    # safety: any vertex the heat solver missed follows its nearest bone
    bone_ids = {vg.index for vg in body.vertex_groups if vg.name in BONES}
    lost = [v.index for v in body.data.vertices if not any(g.group in bone_ids and g.weight > 0.001 for g in v.groups)]
    if lost:
        nearest_bone_weights(body, arm_ob, lost)
    for vg in list(body.vertex_groups):
        if vg.name.startswith("_"):
            body.vertex_groups.remove(vg)
    print("rig: %d vertices were not reached by the heat solver -> nearest bone" % len(lost))


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

    def rot_world(name, axis, deg, f):
        pb = pbs[name]
        M = pb.bone.matrix_local.to_3x3()
        R = M.inverted() @ Matrix.Rotation(math.radians(deg), 3, axis) @ M
        pb.rotation_quaternion = R.to_quaternion()
        pb.keyframe_insert(data_path="rotation_quaternion", frame=f)

    def move_world(name, vec, f):
        pb = pbs[name]
        M = pb.bone.matrix_local.to_3x3()
        pb.location = M.inverted() @ Vector(vec)
        pb.keyframe_insert(data_path="location", frame=f)

    TAU = 2 * math.pi
    for f in range(1, frames + 2, 5):          # last key = frame 61 = same pose as frame 1 -> seamless loop
        t = (f - 1) / frames
        flap = 32 * math.sin(TAU * t)
        rot_world("Wing_L", 'Y', -flap, f)                       # + = wing tip up
        rot_world("Wing_R", 'Y', flap, f)
        rot_world("Jaw", 'X', 9 * (0.5 - 0.5 * math.cos(2 * TAU * t)), f)   # opens and closes twice
        move_world("Spine", (0, 0, -0.035 * math.sin(TAU * t)), f)          # body rises on the downstroke
        rot_world("Neck", 'X', 3 * math.sin(TAU * t + 0.6), f)
        rot_world("Head", 'X', -2.5 * math.sin(TAU * t + 1.2), f)
        rot_world("Tail_1", 'Z', 8 * math.sin(TAU * t), f)
        rot_world("Tail_2", 'Z', 13 * math.sin(TAU * t - 0.9), f)

    act = arm_ob.animation_data.action
    act.name = "Wyvern_IdleFlap"
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
    arm_ob = build_armature()
    auto_weights(body, arm_ob)          # Parent With Automatic Weights (ARMATURE_AUTO)
    build_head()
    build_wing(1)
    build_wing(-1)
    build_claws_and_spikes()

    # join every part into ONE mesh (marker vertex groups survive the join)
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            o.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body = bpy.context.view_layer.objects.active
    body.name = "Wyvern"
    body.data.name = "Wyvern"
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))      # Blender 4.1+
    except (AttributeError, RuntimeError):
        bpy.ops.object.shade_smooth()

    # brick size in metres -> Generated coordinates are 0..1 over the bounding box
    d = body.dimensions
    for key in ("body", "white", "glow"):
        mp = MAT[key].node_tree.nodes.get("BrickMapping")
        mp.inputs["Scale"].default_value = (d.x / BRICK_SIZE, d.y / BRICK_SIZE, d.z / BRICK_SIZE)

    finish_weights(body, arm_ob)        # rigid parts locked to their bones + fallback
    animate(arm_ob, 60)

    # Material Preview in every 3D viewport
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'MATERIAL'
    bpy.ops.object.select_all(action='DESELECT')
    arm_ob.select_set(True)
    bpy.context.view_layer.objects.active = arm_ob
    print("Wyvern done: %d faces, rig + 60-frame loop. Press Spacebar to play." % len(body.data.polygons))


if __name__ == "__main__":
    main()
