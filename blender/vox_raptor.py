r"""Blue sky raptor v2 (crystal-feather wings with glowing tips) made of voxels, brick tile on every face.
Run inside live Blender:  exec(open(p).read(), {'__file__': p})
Design units: x = right, y = back (looks towards -y), z = up. S voxels per unit (gen_voxel_pets2.S = 2)."""
import bpy, bmesh, math, sys, pathlib, hashlib, random
from mathutils import Vector
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import importlib, gen_voxel_pets2 as V2
importlib.reload(V2)
from gen_voxel_pets2 import Vox, INK, WHITE, DIRS
S = V2.S

TILE = 8
SMOOTH = globals().get("SMOOTH", True)    # True: colours without fake per-face light (the smooth remesh gets real light)
TEETH = []                                # smooth mode: (base design point, +1 up / -1 down, length) -> real cone teeth
B, B2, B3, Bd = (32, 92, 226), (24, 72, 200), (58, 124, 244), (18, 46, 150)   # blues
Bl, Wb = (110, 168, 252), (226, 236, 252)                                     # light blue, white-blue belly
C0, C1, C2 = (60, 165, 255), (90, 210, 255), (150, 238, 255)                 # glow ramp
W, Wd = (246, 246, 250), (205, 210, 225)                                     # head white
MOUTH, GUM, TONGUE = (120, 18, 40), (232, 96, 130), (226, 80, 110)
EYE, EYE2 = (255, 236, 90), (255, 176, 20)        # glowing eyes
CLAW = (36, 32, 48)
GLOW = {C0, C1, C2, EYE, EYE2}


def H(*k):
    return int(hashlib.md5(str(k).encode()).hexdigest()[:6], 16) / 0xFFFFFF


def put(v, p, col):
    v.g[(math.floor(p[0] * S), math.floor(p[1] * S), math.floor(p[2] * S))] = col


def blade(v, root, d, side, length, width, ramp, thick=1, peak=0.3):
    """flat leaf/shard: root -> root + d*length, widest at `peak`, colour by distance along it"""
    d = Vector(d).normalized()
    side = Vector(side)
    side = (side - d * side.dot(d)).normalized()
    n = d.cross(side).normalized()
    root = Vector(root)
    st = 0.5 / S
    a = 0.0
    while a <= length:
        t = a / length
        if t < peak:
            w = width * min(1, t / peak) ** 0.6
        else:                                            # rounded, feather-like tip (no sharp triangle)
            w = width * max(0.0, 1 - ((t - peak) / (1 - peak)) ** 2) ** 0.5
        col = ramp[min(len(ramp) - 1, int(t * len(ramp)))]
        b = -w
        while b <= w:
            p = root + d * a + side * b
            for k in range(thick):
                put(v, p + n * (k * 0.5 - (thick - 1) * 0.25), col)
            b += st
        a += st


def raptor():
    v = Vox()
    tl = lambda r0, r1: (lambda t: r0 + (r1 - r0) * t)

    # ---------------- body
    v.ell(0, 6, 13.2, 4.6, 5.2, 4.6, B)          # hips
    v.ell(0, 0.5, 14.2, 4.9, 5.5, 5.0, B)        # belly
    v.ell(0, -4.5, 16.4, 4.6, 4.2, 5.0, B)       # chest
    v.line((0, -5.5, 18.5), (0, -8.5, 23.5), tl(3.6, 2.8), B)     # neck
    v.line((0, -8.5, 23.5), (0, -10.5, 26), tl(2.8, 2.7), B)
    # light belly / throat stripe underneath
    v.paint(lambda X, Y, Z, o: o == B and abs(X) < 3.0 and Z < 12.0 and -7 < Y < 9, Wb)
    v.paint(lambda X, Y, Z, o: o == B and abs(X) < 2.6 and Y < -5 and Z < 0.95 * (-Y) + 10.5 and Z < 24, Wb)

    # ---------------- legs (strong raptor legs, 3 toes + sickle claw)
    for sx in (-1, 1):
        x = sx * 3.9
        v.ell(x, 5.5, 11.2, 2.7, 4.2, 4.4, B)                        # thigh
        v.line((x, 7.5, 8.5), (x, 9.6, 4.0), tl(1.8, 1.3), B)        # shin
        v.line((x, 9.6, 4.0), (x, 8.0, 1.3), tl(1.2, 1.0), B2)       # ankle
        v.ell(x, 6.5, 0.9, 1.7, 2.6, 0.9, B2)                         # foot pad
        for tx, dy in ((-1.1, -3.6), (0, -4.2), (1.1, -3.6)):          # toes + claws
            v.line((x + tx * 0.6, 6.0, 0.9), (x + tx, 6.0 + dy, 0.8), 0.7, B2)
            v.line((x + tx, 5.6 + dy, 0.9), (x + tx * 1.05, 4.4 + dy, 0.3), tl(0.5, 0.2), CLAW)
        v.line((x - sx * 1.2, 5.6, 1.6), (x - sx * 1.6, 4.0, 3.2), tl(0.55, 0.25), CLAW)  # sickle claw (raised)
        # small arms with 3 claws
        v.line((sx * 4.0, -6.0, 14.5), (sx * 4.8, -8.6, 12.4), tl(1.25, 1.0), B)
        v.line((sx * 4.8, -8.6, 12.4), (sx * 4.4, -10.2, 10.6), tl(0.95, 0.8), B3)
        for cz in (-0.7, 0, 0.7):
            v.line((sx * 4.4, -10.6, 10.6 + cz), (sx * 4.2, -11.8, 9.6 + cz * 1.2), tl(0.4, 0.2), CLAW)

    # ---------------- tail (long, tapering, lifted at the tip)
    tp = [(0, 9.5, 13.5), (0, 15, 12.8), (0, 21, 13.0), (0, 27, 14.4), (0, 32, 16.4)]
    tr = [3.6, 2.7, 1.9, 1.2, 0.5]
    for i in range(4):
        v.line(tp[i], tp[i + 1], tl(tr[i], tr[i + 1]), B)
    v.paint(lambda X, Y, Z, o: o == B and Y > 9 and Z < 13.0 - 0.0 * Y - (2.0 if Y < 15 else 1.2), Bl)

    # ---------------- head: big white skull, long snout, jaws wide open
    hx0 = -11.0
    for i in range(int(13 * S) + 1):                                  # upper jaw, slice by slice
        y = hx0 - i / S
        f = (hx0 - y) / 12.5
        hw = 3.4 - 1.5 * f
        top = 29.6 - 2.9 * f
        bot = 24.8 + 0.4 * f
        v.box(-hw + 0.5, y - 0.5, bot, hw - 0.5, y, top, W)
        v.box(-hw, y - 0.5, bot, hw, y, top - 0.5, W)
        if y < -11.5:
            v.box(-hw + 0.5, y - 0.5, bot, hw - 0.5, y, bot + (1.0 if SMOOTH else 0.5), MOUTH)   # palate
    v.ell(0, -10.0, 27.4, 3.6, 3.2, 3.0, W)                            # back of skull
    v.box(-1.6, -24.4, 26.2, 1.6, -23.4, 27.2, W)                      # snout tip
    # lower jaw, hinged at the back, open ~30 deg
    ang = math.radians(31)
    L = 11.5
    for i in range(int(L * S) + 1):
        dd = i / S
        y = -11.0 - dd * math.cos(ang)
        zt = 24.2 - dd * math.sin(ang)
        hw = 3.0 - 1.4 * dd / L
        v.box(-hw, y - 0.6, zt - 1.9, hw, y, zt - 0.7, W)
        v.box(-hw, y - 0.6, zt - 0.7, -hw + 0.5, y, zt, W)                 # white lips on the sides
        v.box(hw - 0.5, y - 0.6, zt - 0.7, hw, y, zt, W)
        v.box(-hw + 0.5, y - 0.6, zt - 0.7, hw - 0.5, y, zt, MOUTH if dd < L - 0.8 else W)
        if 1.5 < dd < 8.0:
            v.box(-1.3, y - 0.6, zt - 0.5, 1.3, y, zt + (0.3 if SMOOTH else 0.5), TONGUE)
        # dark red cheek walls closing the back of the open mouth (reads as a cavity from the side)
        if dd < 6.0:
            ubot = 24.8 + 0.4 * (hx0 - y) / 12.5
            ztop = ubot - (dd / 6.0) * (ubot - zt) * 0.95
            v.box(-hw + 0.6, y - 0.6, zt, hw - 0.6, y, ztop, MOUTH)
    v.box(-2.8, -12.0, 22.0, 2.8, -10.5, 25.0, MOUTH)                  # throat back wall
    # teeth: upper row hangs down, lower row points up
    for i in range(9):
        y = -12.4 - i * 1.25
        f = (hx0 - y) / 12.5
        hw = 3.4 - 1.5 * f
        bot = 24.8 + 0.4 * f
        ln = 1.4 + (0.6 if i in (2, 6) else 0)
        for sx in (-1, 1):
            x = sx * (hw - 0.65)
            if SMOOTH:
                TEETH.append(((x, y - 0.25, bot + 0.3), -1, ln + 0.3))
                continue
            v.box(x - 0.5, y - 0.5, bot - 0.5, x + 0.5, y, bot, WHITE)
            v.box(x - 0.25, y - 0.5, bot - ln, x + 0.25, y, bot - 0.5, WHITE)
    for i in range(7):
        dd = 1.6 + i * 1.3
        y = -11.0 - dd * math.cos(ang)
        zt = 24.2 - dd * math.sin(ang)
        hw = 3.0 - 1.4 * dd / L
        for sx in (-1, 1):
            x = sx * (hw - 0.55)
            if SMOOTH:
                TEETH.append(((x, y - 0.25, zt - 0.3), 1, 1.6))
                continue
            v.box(x - 0.5, y - 0.5, zt - 0.1, x + 0.5, y, zt + 0.5, WHITE)
            v.box(x - 0.25, y - 0.5, zt + 0.5, x + 0.25, y, zt + 1.4, WHITE)
    # blue armour on top of the head + stripe behind the eye
    v.paint(lambda X, Y, Z, o: o == W and Y > -17.5 and Z > 29.4 - 2.9 * (-11 - Y) / 12.5 - 1.1 and Z > 27.5, B)
    v.paint(lambda X, Y, Z, o: o == W and Y > -10.5 and Z > 25.6, B)
    v.paint(lambda X, Y, Z, o: o == W and -12.8 < Y < -11.2 and Z > 25.4 and abs(X) > 2.4, B2)
    for sx in (-1, 1):
        v.box(sx * 2.3 if sx > 0 else -3.7, -17.2, 28.6, 3.7 if sx > 0 else -2.3, -12.6, 29.4, Bd)   # brow ridge
        v.line((sx * 2.1, -9.5, 29.6), (sx * 3.0, -4.5, 31.6), tl(1.2, 0.6), B)                     # horn, swept back
        v.line((sx * 3.0, -4.5, 31.6), (sx * 3.4, -0.5, 32.4), tl(0.6, 0.25), C1)
        v.line((sx * 3.0, -11.0, 28.8), (sx * 4.2, -7.0, 30.6), tl(0.8, 0.3), C0)                   # small horn
        v.line((sx * 3.2, -9.0, 25.8), (sx * 5.4, -6.0, 26.4), tl(0.8, 0.3), B3)                    # cheek spike
        v.line((sx * 3.0, -9.0, 24.4), (sx * 5.0, -6.6, 23.6), tl(0.7, 0.25), B3)

    # ---------------- crystal-feather wings
    for sx in (-1, 1):
        sh = Vector((sx * 3.6, -2.5, 19.5))
        el = Vector((sx * 10.0, -0.5, 27.5))
        wr = Vector((sx * 16.5, 2.5, 33.0))
        tip = Vector((sx * 20.5, 4.0, 36.0))
        v.line(tuple(sh), tuple(el), tl(1.7, 1.3), B2)
        v.line(tuple(el), tuple(wr), tl(1.3, 1.0), B2)
        v.line(tuple(wr), tuple(tip), tl(1.0, 0.4), B)
        bone = [sh.lerp(el, t) for t in (0.1, 0.3, 0.5, 0.7, 0.9)] + [el.lerp(wr, t) for t in (0.1, 0.3, 0.5, 0.7, 0.9)] + [wr.lerp(tip, t) for t in (0.2, 0.5, 0.8)]
        nb = len(bone)
        for k, r in enumerate(bone):
            t = k / (nb - 1)
            d = Vector((sx * (0.15 + 0.75 * t), 0.75 - 0.25 * t, -0.95 + 1.15 * t))
            ln = 8.5 + 6.0 * math.sin(t * math.pi * 0.85)
            arm = (wr - sh).normalized()
            # main primary feather: blue root -> glowing tip
            blade(v, r, d, arm, ln, 2.2, [B, B, B, B3, B3, C1, C1, C2], thick=2, peak=0.35)
            # covert feather on top (shorter, darker)
            blade(v, r + Vector((0, -0.6, 0.3)), d, arm, ln * 0.55, 2.0, [B, B, B, B], thick=2, peak=0.45)
        # leading edge spikes
        for t in (0.35, 0.75):
            p = el.lerp(wr, t)
            v.line(tuple(p), tuple(p + Vector((sx * 0.4, -1.2, 1.6)) * 1.6), tl(0.7, 0.2), C1)

    # ---------------- glowing dorsal spikes along neck, back and tail
    spine = [(-9.0, 27.6), (-6.5, 25.5), (-4.0, 22.0), (-1.0, 20.0), (2.5, 19.0), (6.0, 18.4), (10.0, 17.6),
             (14.5, 16.2), (19.0, 15.4), (23.5, 15.8), (27.5, 16.2), (31.0, 17.2)]
    for i, (y, z) in enumerate(spine):
        s = 1.0 - 0.45 * abs(i - 4) / 7
        ln = 3.0 * s + 0.6
        # round spike curving backwards (like a claw), thick at the root, soft tip
        pts = [Vector((0, y, z - 0.8))]
        for k in range(1, 7):
            t = k / 6
            pts.append(Vector((0, y + ln * (0.15 * t + 0.75 * t * t), z - 0.8 + ln * (1.05 * t - 0.25 * t * t))))
        r0 = 0.95 * s + 0.3
        for k in range(6):
            t0, t1 = k / 6, (k + 1) / 6
            v.line(tuple(pts[k]), tuple(pts[k + 1]), (lambda tt, t0=t0, t1=t1: r0 * (1 - (t0 + (t1 - t0) * tt)) + 0.2), C1 if k < 3 else C2)

    # scale texture: mix three blues on the body
    for k, c in list(v.g.items()):
        if c == B and not SMOOTH:
            h = H(*k)
            v.g[k] = B2 if h < 0.08 else (B3 if h > 0.95 else B)
    v.sym()
    if not SMOOTH:            # smooth model gets real round eyes in smooth_pet.add_eyes
        side_eyes(v)
    return v


def side_eyes(v):
    """angry yellow eye with a black slit, painted onto the outer side of the head"""
    cy, cz, ry, rz = -14.6, 27.4, 1.7, 1.05
    for zi in range(math.floor((cz - rz - 0.8) * S), math.ceil((cz + rz + 0.8) * S)):
        for yi in range(math.floor((cy - ry - 0.8) * S), math.ceil((cy + ry + 0.8) * S)):
            Y, Z = (yi + 0.5) / S, (zi + 0.5) / S
            e = ((Y - cy) / ry) ** 2 + ((Z - cz) / rz) ** 2
            lid = Z > cz + 0.7 - (Y - cy) * 0.35          # angry lid slopes down to the snout
            xs = [k[0] for k in v.g if k[1] == yi and k[2] == zi]
            if not xs:
                continue
            if e > 1.0 or lid:
                if e < 2.1 or (lid and e < 1.6):
                    for xi in (min(xs), max(xs)):
                        v.g[(xi, yi, zi)] = INK if lid and e < 1.3 else Bd   # dark socket around the glowing eye
                continue
            if abs(Y - (cy + 0.1)) < 0.3:
                col = INK                                   # slit pupil
            elif abs(Y - (cy + 0.9)) < 0.3 and Z > cz + 0.2:
                col = WHITE                                 # glint
            else:
                col = EYE2 if Z < cz - 0.5 else EYE
            for xi in (min(xs), max(xs)):
                v.g[(xi, yi, zi)] = col


def build(name, v, unit=0.07):
    bm = bmesh.new()
    cl = bm.loops.layers.color.new("Col")
    gll = bm.loops.layers.color.new("Gl")          # 1 = glowing part (kept through the smooth remesh)
    uvl = bm.loops.layers.uv.new("UV")
    xs = [k[0] for k in v.g]; ys = [k[1] for k in v.g]; zs = [k[2] for k in v.g]
    ox, oy, oz = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2, min(zs)
    vc = {}

    def vert(p):
        if p not in vc:
            vc[p] = bm.verts.new(((p[0] - ox) * unit, -(p[1] - oy) * unit, (p[2] - oz) * unit))
        return vc[p]

    zmin, zmax = min(zs), max(zs)
    for key, col in v.g.items():
        j = 1.0 if SMOOTH else 0.95 + 0.08 * H(*key)
        hz = 0.82 + 0.25 * (key[2] - zmin) / (zmax - zmin)          # darker towards the feet
        if col in GLOW or SMOOTH:
            hz = 1.0
        for (dx, dy, dz), quad in DIRS:
            if (key[0] + dx, key[1] + dy, key[2] + dz) in v.g:
                continue
            pts = [(key[0] + a, key[1] + b, key[2] + c) for a, b, c in quad]
            f = bm.faces.new([vert(p) for p in pts])
            f.material_index = 1 if col in GLOW else 0
            light = 1.0 if SMOOTH else (1.1 if dz == 1 else (0.96 if dz == 0 else 0.72))
            cc = tuple(min(1.0, (x / 255) * j * light * hz) for x in col) + (1.0,)
            gv = (1.0, 1.0, 1.0, 1.0) if col in GLOW else (0.0, 0.0, 0.0, 1.0)
            for lp, p in zip(f.loops, pts):
                lp[cl] = cc
                lp[gll] = gv
                u, w = (p[1], p[2]) if dx else ((p[0], p[2]) if dy else (p[0], p[1]))
                lp[uvl].uv = (u / TILE, w / TILE)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o["vox_origin"] = (ox, oy, oz)
    o["vox_unit"] = unit
    for glowing in (False, True):
        m = bpy.data.materials.new(name + ("Glow" if glowing else "M"))
        m.use_nodes = True
        nt = m.node_tree
        a = nt.nodes.new("ShaderNodeVertexColor"); a.layer_name = "Col"
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(str(HERE / "tex" / "brick.png"), check_existing=True)
        t.image.colorspace_settings.name = "Non-Color"
        k = nt.nodes.new("ShaderNodeMath"); k.operation = "MULTIPLY"; k.inputs[1].default_value = 1.18
        nt.links.new(t.outputs["Color"], k.inputs[0])
        mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        nt.links.new(a.outputs["Color"], mul.inputs["A"])
        nt.links.new(k.outputs[0], mul.inputs["B"])
        b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        nt.links.new(mul.outputs["Result"], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.6
        if glowing:
            nt.links.new(mul.outputs["Result"], b.inputs["Emission Color"])
            b.inputs["Emission Strength"].default_value = 1.6
        me.materials.append(m)
    return o


old = bpy.data.objects.get("Pet_Raptor")
if old:
    bpy.data.objects.remove(old, do_unlink=True)
ob = build("Pet_Raptor", raptor())
print("faces", len(ob.data.polygons), "dims", tuple(round(d, 2) for d in ob.dimensions))
