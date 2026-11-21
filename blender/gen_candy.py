r"""Raining Eggs, zone 3 (Candy Canyon) as Blender meshes.

  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P gen_candy.py   -> out\RainingEggsCandy.fbx + out\candy_*.png

Meshes (Roblox axes, origin on the ground, front = -Z):
  Map_LolliStick (10 tall, the game stretches it), Map_LolliTop1..6 (10 wide disc, centre at its own origin, faces Z),
  Map_CandyCane (n = 6 size), Map_Gumdrop1..6 (4 wide), Map_IceCream1..3, Map_Cake + Map_CakeNeon,
  Map_ChocoRiver (174 x 20 along X), Map_WaferBridge (22 x 24, deck top at 1.6)
"""
import bpy, bmesh, math, sys, pathlib, random

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from blib import *          # noqa: F401,F403
import blib

OUT = HERE / 'out'
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MAT = reset()
R = random.Random(21)
CS = [(255, 90, 120), (120, 200, 255), (255, 214, 60), (150, 230, 120), (190, 130, 255), (255, 150, 50)]
CHOC, CHOC2, WAFER, CONE = (110, 66, 40), (140, 88, 52), (240, 200, 130), (226, 170, 100)
PINK, CREAMY = (255, 150, 180), (255, 240, 230)


def dome(b, pos, r, h, c, segs=16, rings=8):
    x, y, z = pos
    vs = bmesh.ops.create_uvsphere(b.bm, u_segments=segs, v_segments=rings, radius=1, matrix=M(pos, scale=(r, h, r)))['verts']
    bmesh.ops.delete(b.bm, geom=[v for v in vs if v.co.z < y - 1e-4], context='VERTS')
    vs = [v for v in vs if v.is_valid]
    bmesh.ops.holes_fill(b.bm, edges=[e for e in {e for v in vs for e in v.link_edges} if e.is_boundary], sides=0)
    b.paint(vs, c)


def sprinkles(b, centre, r, n, rng, ylo=0.2, yhi=1.0, h=None):
    x0, y0, z0 = centre
    h = h or r
    for _ in range(n):
        th, ph = rng.uniform(0.1, 1.2), rng.uniform(0, math.tau)
        x, y, z = r * math.sin(th) * math.cos(ph), h * math.cos(th), r * math.sin(th) * math.sin(ph)
        rbox(b, (x0 + x * 1.02, y0 + y * 1.02, z0 + z * 1.02), (0.5, 0.16, 0.16), rng.choice(CS + [WHITE]), 0.04,
             yaw=rng.uniform(0, 180), rz=rng.uniform(-40, 40))


# ---------------------------------------------------------------- lollipop
def lolli_stick():
    b = B()
    rcyl(b, (0, 5, 0), 0.45, 10, WHITE, segs=10)
    return b.finish('Map_LolliStick', (0, 0, 0), MAT)


def lolli_top(k):
    """v137: one smooth domed candy disc per side, the swirl PAINTED on its own faces (no boxes lying on top =
    nothing can flicker), 3-colour spiral, a glossy round rim and a soft shine spot."""
    b = B()
    bm, col = b.bm, b.col
    c1, c2 = CS[k], CS[(k + 2) % 6]
    cols = [lin(c1), lin(WHITE), lin(c2), lin(WHITE)]
    RINGS, SEGS, RAD, TH = 24, 112, 5.0, 0.8

    def colour(r, a, side):
        v = (a / math.tau) * 4 - r / 0.95                       # 4 spiral bands
        c = cols[int(math.floor(v)) % 4]
        # shine: lighter spot up-left on the front face
        sx, sy = r * math.cos(a) + 1.7, r * math.sin(a) - 1.9
        if side < 0 and sx * sx + sy * sy < 1.1:
            c = tuple(min(1.0, ch * 0.45 + 0.55) for ch in c[:3]) + (1.0,)
        return c

    # grid laid ALONG the spiral: column v (0..4) is a spiral line, so every band edge is a smooth curve of the mesh
    K = 16                                                      # columns per band
    NC = 4 * K
    for side in (-1, 1):
        grid = []
        for i in range(RINGS + 1):
            r = RAD * i / RINGS
            z = side * (TH + 0.35 * (1 - (r / RAD) ** 2))       # gently domed
            row = []
            for j in range(NC if i else 1):
                a = math.tau * (j / K + r / 0.95) / 4
                row.append(bm.verts.new((r * math.cos(a), -z, r * math.sin(a))))
            grid.append(row)
        for i in range(RINGS):
            for j in range(NC):
                j2 = (j + 1) % NC
                if i == 0:
                    vs = [grid[0][0], grid[1][j], grid[1][j2]]
                else:
                    vs = [grid[i][j], grid[i + 1][j], grid[i + 1][j2], grid[i][j2]]
                if side > 0:
                    vs.reverse()
                f = bm.faces.new(vs)
                c = cols[(j // K) % 4]
                if side < 0:                                    # soft shine spot up-left on the front
                    cx = sum(v.co.x for v in vs) / len(vs) + 1.7
                    cy = sum(v.co.z for v in vs) / len(vs) - 1.9
                    if cx * cx + cy * cy < 1.1:
                        c = tuple(min(1.0, ch * 0.45 + 0.55) for ch in c[:3]) + (1.0,)
                for l in f.loops:
                    l[col] = c
    # glossy rim: a torus round the edge (hides the seam between the two faces)
    rim = lin(mix(c1, WHITE, 0.25))
    RS_, MS = 64, 10
    ring = []
    for j in range(RS_):
        a = j * math.tau / RS_
        row = []
        for m in range(MS):
            t = m * math.tau / MS
            rr = RAD + 0.05 + 0.5 * math.cos(t)
            row.append(bm.verts.new((rr * math.cos(a), 1.0 * math.sin(t), rr * math.sin(a))))
        ring.append(row)
    for j in range(RS_):
        for m in range(MS):
            f = bm.faces.new([ring[j][m], ring[(j + 1) % RS_][m], ring[(j + 1) % RS_][(m + 1) % MS], ring[j][(m + 1) % MS]])
            for l in f.loops:
                l[col] = rim
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    b.n += 1
    return b.finish(f'Map_LolliTop{k + 1}', (0, 0, 0), MAT)


def lolli_top_old(k):
    b = B()
    c1, c2 = CS[k], CS[(k + 2) % 6]
    rcyl(b, (0, 0, 0), 5, 1.6, c1, axis='Z', segs=28)
    rcyl(b, (0, 0, 0), 5.15, 1.2, mix(c1, WHITE, 0.4), axis='Z', segs=28)          # glossy rim
    for side in (-1, 1):                                                          # swirl on both faces
        # one box per step, exactly as long as the step and turned along the spiral, every other box a bit higher:
        # no two faces in the same place (before they overlapped flat = the colours flickered in Roblox)
        pts = []
        for j in range(71):
            t = j / 70
            a, rr = t * math.tau * 2.6, 0.4 + t * 4.3
            pts.append((rr * math.cos(a), rr * math.sin(a)))
        for j in range(70):
            (x0, y0), (x1, y1) = pts[j], pts[j + 1]
            ln = math.hypot(x1 - x0, y1 - y0)
            z = side * (0.84 + (j % 2) * 0.05)
            rbox(b, ((x0 + x1) / 2, (y0 + y1) / 2, z), (ln + 0.04, 0.75, 0.1), c2 if (j // 4) % 2 == 0 else WHITE, 0, rz=math.degrees(math.atan2(y1 - y0, x1 - x0)))
    rball(b, (-1.6, 2.0, -0.85), 0.9, WHITE, (1, 0.6, 0.15), 8, 5)                # shine
    return b.finish(f'Map_LolliTop{k + 1}', (0, 0, 0), MAT)


# ---------------------------------------------------------------- candy cane (n = 6: 13 tall)
def candy_cane():
    b = B()
    pts = [(0, y, 0) for y in (0, 1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9, 11.0)]
    for k in range(9):
        a = math.radians(180 - k * 22.5)
        pts.append((2.6 + 2.6 * math.cos(a), 11.0 + 2.6 * math.sin(a), 0))
    pts.append((5.2, 9.6, 0))
    for k in range(len(pts) - 1):
        rtube(b, pts[k], pts[k + 1], 1.05, (236, 50, 60) if k % 2 == 0 else WHITE, segs=12)
        rball(b, pts[k + 1], 1.05, (236, 50, 60) if k % 2 == 0 else WHITE, segs=12, rings=6)
    rball(b, (5.2, 9.6, 0), 1.05, WHITE, segs=12, rings=6)
    return b.finish('Map_CandyCane', (0, 0, 0), MAT)


# ---------------------------------------------------------------- gumdrops
def gumdrop(k):
    b = B()
    rng = random.Random(k)
    c = CS[k]
    rcyl(b, (0, 0.6, 0), 2, 1.2, c, segs=16, r2=1.9)
    dome(b, (0, 1.2, 0), 1.9, 1.6, c)
    for _ in range(18):
        th, ph = rng.uniform(0, 1.3), rng.uniform(0, math.tau)
        rbox(b, (1.95 * math.sin(th) * math.cos(ph), 1.2 + 1.62 * math.cos(th), 1.95 * math.sin(th) * math.sin(ph)), (0.22, 0.22, 0.22), mix(c, WHITE, 0.7), 0, yaw=rng.uniform(0, 90))
    rball(b, (-0.7, 2.3, -0.9), 0.45, mix(c, WHITE, 0.6), (1, 0.6, 0.6), 6, 4)
    return b.finish(f'Map_Gumdrop{k + 1}', (0, 0, 0), MAT)


# ---------------------------------------------------------------- ice cream
def ice_cream(k):
    b = B()
    rng = random.Random(40 + k)
    rcyl(b, (0, 4.6, 0), 1.0, 9.2, CONE, segs=12, r2=3.3)
    for j in range(8):                                                           # waffle grid
        a = j * math.tau / 8
        rbeam(b, (0.95 * math.cos(a), 0.2, 0.95 * math.sin(a)), (3.25 * math.cos(a + 0.5), 9.1, 3.25 * math.sin(a + 0.5)), 0.22, shade(CONE, 0.78), 0.02)
        rbeam(b, (0.95 * math.cos(a), 0.2, 0.95 * math.sin(a)), (3.25 * math.cos(a - 0.5), 9.1, 3.25 * math.sin(a - 0.5)), 0.22, shade(CONE, 0.78), 0.02)
    rcyl(b, (0, 9.3, 0), 3.5, 0.6, mix(CONE, WHITE, 0.25), segs=14)
    cols = [CS[(k + j * 2) % 6] for j in range(3)]
    y = 9.6
    for j, (rr, c) in enumerate(zip((3.6, 3.1, 2.5), cols)):
        rball(b, (0, y + rr * 0.7, 0), rr, c, (1, 0.85, 1), 14, 8)
        for d in range(7):                                                        # drips over the edge
            a = d * math.tau / 7 + j
            rball(b, ((rr - 0.15) * math.cos(a), y + 0.25, (rr - 0.15) * math.sin(a)), 0.45, c, (1, rng.uniform(1.1, 1.6), 1), 6, 5)
        sprinkles(b, (0, y + rr * 0.7, 0), rr, 10, rng, h=rr * 0.85)
        y += rr * 1.25
    rball(b, (0, y + 0.6, 0), 0.8, (220, 30, 50), segs=10, rings=6)
    rbeam(b, (0, y + 1.3, 0), (0.6, y + 2.6, 0.2), 0.14, (60, 140, 50), 0.02)
    return b.finish(f'Map_IceCream{k + 1}', (0, 0, 0), MAT)


# ---------------------------------------------------------------- giant cake
def torus(b, y, R, r, c, segs=48, msegs=8, sy=1.0):
    """horizontal ring round the Y axis at height y (Roblox axes)"""
    bm, col, cl = b.bm, b.col, lin(c)
    ring = []
    for j in range(segs):
        a = j * math.tau / segs
        row = []
        for m in range(msegs):
            t = m * math.tau / msegs
            rr = R + r * math.cos(t)
            row.append(bm.verts.new((rr * math.cos(a), -rr * math.sin(a), y + r * sy * math.sin(t))))
        ring.append(row)
    for j in range(segs):
        for m in range(msegs):
            f = bm.faces.new([ring[j][m], ring[j][(m + 1) % msegs], ring[(j + 1) % segs][(m + 1) % msegs], ring[(j + 1) % segs][m]])
            f.smooth = True
            for l in f.loops:
                l[col] = cl
    b.n += 1


def cake():
    """v137: smoother professional cake - round tier edges, glossy glaze with real drips, piped cream rosettes,
    strawberries, sprinkles, striped candles with teardrop flames. Same footprint (44/34/24 wide, tiers 9 high)."""
    b, n = B(), B()
    rng = random.Random(9)
    GLAZE = [(122, 66, 38), (255, 120, 160), (122, 66, 38)]
    rcyl(b, (0, 0.2, 0), 25.5, 0.4, (250, 250, 255), segs=56)                     # plate
    torus(b, 0.4, 25.5, 0.45, (235, 238, 250), 40, 6)
    for k, (d, c) in enumerate(((44, CREAMY), (34, PINK), (24, CREAMY))):
        y, R = k * 9, d / 2
        rcyl(b, (0, y + 4.4, 0), R, 8.6, c, segs=56)                                # sponge + icing
        torus(b, y + 8.6, R - 0.6, 0.6, c, 40, 6)                                   # rounded top edge
        g = GLAZE[k]
        rcyl(b, (0, y + 9.15, 0), R - 0.7, 0.3, g, segs=56)                         # glaze on top (above the edge)
        torus(b, y + 8.85, R - 0.2, 0.45, g, 40, 5, 0.8)                            # glaze lip
        for j in range(14):                                                         # drips: different lengths
            a = j * math.tau / 14 + k * 0.13
            ln = rng.uniform(1.2, 3.6)
            x, z = (R + 0.05) * math.cos(a), (R + 0.05) * math.sin(a)
            rball(b, (x, y + 8.6 - ln * 0.5, z), 0.55, g, (1, ln, 1), 6, 4)
            rball(b, (x, y + 8.6 - ln * 0.95, z), 0.62, g, (1, 1, 1), 6, 4)
        for j in range(20 - k * 4):                                                # piped cream rosettes on the base
            a = j * math.tau / (20 - k * 4)
            rball(b, ((R + 0.2) * math.cos(a), y + 0.7, (R + 0.2) * math.sin(a)), 0.85, WHITE, (1, 0.8, 1), 6, 4)
            rball(b, ((R + 0.2) * math.cos(a), y + 1.35, (R + 0.2) * math.sin(a)), 0.45, WHITE, (1, 1.2, 1), 5, 3)
        for j in range(10):                                                         # strawberries round the top
            a = j * math.tau / 10 + k * 0.3
            sx, sz = (R - 2.0) * math.cos(a), (R - 2.0) * math.sin(a)
            if k < 2 and R - 2.0 < d / 2 - 0.1:
                rball(b, (sx, y + 10.2, sz), 1.05, (226, 34, 52), (1, 1.25, 1), 8, 5)
                for q in range(4):
                    rbox(b, (sx + 0.5 * math.cos(q * 1.57), y + 11.45, sz + 0.5 * math.sin(q * 1.57)), (0.9, 0.12, 0.35), (70, 160, 60), 0, yaw=q * 90)
        for j in range(30 + k * 5):                                                # sprinkles on the glaze
            r, a = rng.uniform(1.5, R - 3.2), rng.uniform(0, math.tau)
            rbox(b, (r * math.cos(a), y + 9.33, r * math.sin(a)), (0.55, 0.14, 0.18), rng.choice(CS + [WHITE]), 0.04, yaw=rng.uniform(0, 180))
    rball(b, (0, 30.2, 0), 3, (236, 40, 60), segs=18, rings=12)                     # cherry
    rbeam(b, (0, 32.8, 0), (1.2, 35.5, 0.4), 0.3, (60, 140, 50), 0.04)
    for a in range(0, 360, 60):                                                     # striped candles + flames
        x, z = 8 * math.cos(math.radians(a)), 8 * math.sin(math.radians(a))
        c = CS[a // 60]
        for j in range(6):
            rcyl(b, (x, 27.6 + j * 0.8, z), 0.45, 0.8, c if j % 2 == 0 else WHITE, segs=8)
        rcyl(b, (x, 32.35, z), 0.06, 0.7, INK, segs=4)
        rball(n, (x, 33.2, z), 0.5, (255, 200, 80), (1, 1.7, 1), 10, 7)
        rball(n, (x, 33.85, z), 0.22, (255, 235, 150), (1, 1.6, 1), 6, 4)
    return [b.finish('Map_Cake', (0, 0, 0), MAT), n.finish('Map_CakeNeon', (0, 0, 0), MAT)]


def cake_old():
    b, n = B(), B()
    rng = random.Random(9)
    for k, (d, c) in enumerate(((44, CREAMY), (34, PINK), (24, CREAMY))):
        y = k * 9
        rcyl(b, (0, y + 4.5, 0), d / 2, 9, c, segs=28)
        band = CHOC if k % 2 == 0 else WHITE
        rcyl(b, (0, y + 8.15, 0), d / 2 + 0.5, 1.2, band, segs=28)  # top 8.75: not coplanar with tier top (z-fight fix)
        for j in range(18):                                                      # frosting drips
            a = j * math.tau / 18 + k * 0.2
            rball(b, ((d / 2 + 0.3) * math.cos(a), y + 7.4, (d / 2 + 0.3) * math.sin(a)), 0.9, band, (0.8, rng.uniform(1.6, 3), 0.8), 6, 5)
        for j in range(10):                                                      # candy balls on the rim
            a = j * math.tau / 10 + k * 0.35
            rball(b, ((d / 2 - 1.2) * math.cos(a), y + 9.7, (d / 2 - 1.2) * math.sin(a)), 1.3, CS[(j + k) % 6], segs=10, rings=6)
        rcyl(b, (0, y + 0.7, 0), d / 2 + 0.6, 1.2, mix(band, WHITE, 0.3), segs=28)
    rball(b, (0, 30, 0), 3, (236, 40, 60), segs=14, rings=8)
    rbeam(b, (0, 32.5, 0), (1.2, 35.5, 0.4), 0.3, (60, 140, 50), 0.04)
    rball(b, (-1, 31.2, -1.6), 0.7, (255, 140, 150), (1, 0.6, 0.6), 6, 4)
    for a in range(0, 360, 60):
        x, z = 8 * math.cos(math.radians(a)), 8 * math.sin(math.radians(a))
        c = CS[a // 60]
        rcyl(b, (x, 29.5, z), 0.45, 5, c, segs=8)
        for j in range(3):
            rcyl(b, (x, 27.8 + j * 1.5, z), 0.47, 0.35, WHITE, segs=8, rx=12)
        rcyl(b, (x, 32.2, z), 0.06, 0.6, INK, segs=4)
        rball(n, (x, 33.1, z), 0.5, (255, 200, 80), (1, 1.6, 1), 8, 5)
    rcyl(b, (0, 0.15, 0), 25, 0.3, (250, 250, 255), segs=28)                    # plate
    return [b.finish('Map_Cake', (0, 0, 0), MAT), n.finish('Map_CakeNeon', (0, 0, 0), MAT)]


# ---------------------------------------------------------------- chocolate river + wafer bridge
def river():
    b = B()
    rng = random.Random(3)
    rbox(b, (0, 0.1, 0), (174, 0.2, 20), (200, 160, 110), 0)                   # biscuit banks
    rbox(b, (0, 0.2, 0), (174, 0.25, 15.4), CHOC2, 0)
    for k in range(40):                                                          # flowing swirls
        x = -84 + k * 4.3
        for zz in (-4.5, 0, 4.5):
            rbox(b, (x + rng.uniform(-1, 1), 0.36, zz + rng.uniform(-1, 1)), (rng.uniform(2, 3.5), 0.06, 0.45), mix(CHOC2, WHITE, 0.25), 0.02, yaw=rng.uniform(-14, 14))
    for k in range(70):                                                          # crumbs on the banks
        x, zz = rng.uniform(-86, 86), rng.choice((-1, 1)) * rng.uniform(7.9, 9.8)
        rbox(b, (x, 0.35, zz), (rng.uniform(0.6, 1.4),) * 3, shade((210, 160, 100), rng.uniform(0.85, 1.1)), 0.15, yaw=rng.uniform(0, 90))
    for k in range(9):                                                           # floating marshmallows
        x, zz = rng.uniform(-80, 80), rng.uniform(-5, 5)
        rcyl(b, (x, 0.75, zz), 1.0, 1.2, (255, 238, 245) if k % 2 else (255, 200, 220), segs=12)
    return b.finish('Map_ChocoRiver', (0, 0, 0), MAT)


def bridge():
    b = B()
    for k in range(6):                                                           # wafer slabs across the road
        z = -10 + k * 4
        rbox(b, (0, 0.8, z), (22, 1.6, 3.9), WAFER, 0.15)
        for j in range(10):
            rbox(b, (-9.9 + j * 2.2, 1.62, z), (0.16, 0.06, 3.7), shade(WAFER, 0.8), 0)
        rbox(b, (0, 1.62, z), (21.6, 0.06, 0.16), shade(WAFER, 0.8), 0)
    for sx in (-1, 1):
        x = sx * 10.5
        for z in (-11, -5.5, 0, 5.5, 11):
            rcyl(b, (x, 3.2, z), 0.45, 3.2, PINK, segs=10)
            dome(b, (x, 4.8, z), 0.9, 0.8, CS[int(z + 11) % 6], 10, 5)
        rtube(b, (x, 4.1, -11), (x, 4.1, 11), 0.35, (255, 120, 150), segs=8)
        for z in range(-10, 11, 2):
            rcyl(b, (x, 4.1, z), 0.38, 0.6, WHITE, axis='Z', segs=8)
    return b.finish('Map_WaferBridge', (0, 0, 0), MAT)


objs = [lolli_stick()] + [lolli_top(k) for k in range(6)] + [candy_cane()] + [gumdrop(k) for k in range(6)] + \
       [ice_cream(k) for k in range(3)] + cake() + [river(), bridge()]
save_meta(HERE.parent / 'game')
print('triangles:', {o.name: len(o.data.polygons) for o in objs})
if 'cakeonly' in ARGS:   # the fixed models only (cake + lollipop tops): delete the old ones in Studio, import this
    print('wrote', blib.export([o for o in objs if o.name.startswith(('Map_Cake', 'Map_LolliTop'))], OUT / 'RainingEggsCandyFix.fbx'))
elif 'nofbx' not in ARGS:
    print('wrote', blib.export(objs, OUT / 'RainingEggsCandy.fbx'))

# ---------------------------------------------------------------- preview scene
sc, cam = scene_setup(sky=(0.85, 0.8, 1.0, 1), ground=(1.0, 0.45, 0.62, 1))
for o in objs:
    o.hide_render = True
by = {o.name: o for o in objs}
glow = glow_material(4)
road = B()
rbox(road, (0, 0.05, 40), (18, 0.1, 240), (255, 244, 220), 0)
road.finish('Road', (0, 0, 0), MAT)
blib.META.pop('Road', None)


def put(name, pos, yaw=0, s=1.0, sv=None, neon=False):
    o = place(by[name], name + '_p', pos, yaw, s)
    if sv:
        o.scale = (sv[0], sv[2], sv[1])
    if neon:
        o.data = o.data.copy()
        o.data.materials.clear()
        o.data.materials.append(glow)
    return o


put('Map_ChocoRiver', (-96, 0, 50))
put('Map_ChocoRiver', (96, 0, 50))
put('Map_WaferBridge', (0, 0, 50))
put('Map_Cake', (-46, 0, 92))
put('Map_CakeNeon', (-46, 0, 92), neon=True)
for k, (x, z, h, d) in enumerate(((-24, 10, 14, 12), (34, 20, 18, 14), (52, 80, 12, 10), (-70, 30, 16, 13), (24, 104, 15, 12))):
    put('Map_LolliStick', (x, 0, z), sv=(1, h / 10, 1))
    put(f'Map_LolliTop{k + 1}', (x, h + d / 2 - 1, z), 20 * k, d / 10)
for k, (x, z, yaw) in enumerate(((16, -6, 30), (-36, 70, 160), (60, 36, 90), (14, 74, 220))):
    put('Map_CandyCane', (x, 0, z), yaw, 1.0)
for k, (x, z) in enumerate(((40, 0), (-16, 76), (70, 60))):
    put(f'Map_IceCream{k + 1}', (x, 0, z), k * 50)
for k in range(30):
    put(f'Map_Gumdrop{k % 6 + 1}', (R.choice((-1, 1)) * R.uniform(11, 80), 0, R.choice((R.uniform(-30, 36), R.uniform(64, 110)))), R.uniform(0, 360), R.uniform(0.6, 1.4))
if 'norender' not in ARGS:
    shot(sc, cam, OUT / 'candy_scene.png', (4, 42, -60), (-4, 6, 50), (1800, 1000), 26)
    shot(sc, cam, OUT / 'candy_cake.png', (-12, 30, 50), (-46, 14, 92), (1400, 1000), 32)
