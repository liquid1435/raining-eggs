r"""Raining Eggs: pets + eggs as smooth vertex-coloured meshes.

  blender -b -P gen_assets.py            -> out\RainingEggsAssets.fbx + out\preview_*.png
  blender -b -P gen_assets.py -- nofbx   -> preview only

One mesh per pet, named Pet_<zone>_<rarity>; eggs Egg_<zone>, Egg_Gold, Egg_Rotten, Egg_Storm.
1 Blender unit = 1 stud. Pets stand on z = 0 and look to +Y (= Roblox front after FBX export).
Pet list is read from ..\game\Config.lua, so names and colours stay in one place.
"""
import bpy, bmesh, math, re, sys, pathlib, random, shutil, os
from mathutils import Matrix, Euler, Vector

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'out'
OUT.mkdir(exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
CFG = (HERE.parent / 'game' / 'Config.lua').read_text(encoding='utf-8')

W = (245, 247, 252)
BLACK, WHITE, BLUSH, GOLD = (26, 28, 46), (255, 255, 255), (255, 130, 160), (255, 204, 40)


def rgb(s):
    s = s.strip()
    return W if s == 'W' else tuple(int(v) for v in re.findall(r'\d+', s))


C3 = r'(W|\{[^}]*\})'
ZONES = []
for line in CFG.splitlines():
    m = re.match(r'\s*zone\("([^"]+)",\s*[^,]+,\s*[^,]+,\s*' + C3 + r',\s*' + C3, line)
    if m:
        ZONES.append({'name': m.group(1), 'egg': rgb(m.group(2)), 'spot': rgb(m.group(3)), 'pets': []})
        continue
    m = re.match(r'\s*\{\s*"([^"]+)",\s*' + C3 + r',\s*' + C3 + r',\s*(\d),\s*"(\w)"', line)
    if m and ZONES:
        ZONES[-1]['pets'].append((m.group(1), rgb(m.group(2)), rgb(m.group(3)), int(m.group(4)), m.group(5)))
assert len(ZONES) == 10 and all(len(z['pets']) == 5 for z in ZONES), [len(z['pets']) for z in ZONES]


def lin(c):
    f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (f(c[0] / 255), f(c[1] / 255), f(c[2] / 255), 1.0)


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def tint(c, k):
    return tuple(int(v + (255 - v) * k) for v in c)


def lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


class B:
    """collects primitives in one bmesh; every face gets a vertex colour"""

    def __init__(self):
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.color.new('Col')

    def _paint(self, verts, c):
        cl = lin(c)
        for f in {f for v in verts for f in v.link_faces}:
            f.smooth = len(f.verts) <= 4
            for l in f.loops:
                l[self.col] = cl

    @staticmethod
    def M(loc, sc, rot):
        return Matrix.Translation(loc) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4() @ Matrix.Diagonal((*sc, 1))

    def sph(self, loc, r, c, rot=(0, 0, 0), seg=16):
        if not isinstance(r, tuple):
            r = (r, r, r)
        res = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=max(6, seg * 5 // 8), radius=1, matrix=self.M(loc, r, rot))
        self._paint(res['verts'], c)

    def cone(self, loc, r1, r2, h, c, rot=(0, 0, 0), seg=12, sc=(1, 1, 1)):
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=h, matrix=self.M(loc, sc, rot))
        self._paint(res['verts'], c)

    def chain(self, pts, r0, r1, c, seg=10):
        n = len(pts)
        for k, p in enumerate(pts):
            self.sph(p, r0 + (r1 - r0) * k / max(1, n - 1), c, seg=seg)

    def finish(self, name, x, y, flip=True):
        bm = self.bm
        if flip:                                  # built looking to -Y, the game wants +Y
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi, 3, 'Z'), verts=bm.verts)
        zmin = min(v.co.z for v in bm.verts)
        bmesh.ops.translate(bm, vec=(0, 0, -zmin), verts=bm.verts)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        ob.location = (x, y, 0)
        bpy.context.scene.collection.objects.link(ob)
        me.materials.append(MAT)
        return ob


# ---------------------------------------------------------------- pets
def build_pet(name, body, accent, ears, kind):
    n = name.lower()
    has = lambda *w: any(k in n for k in w)
    b = B()
    dark = shade(body, 0.74)
    light = accent if lum(accent) > lum(body) else tint(body, 0.55)
    inner = accent if lum(accent) > 120 else BLUSH

    if kind == 'q':
        hc, hr = Vector((0, -0.75, 2.6)), Vector((1.3, 1.2, 1.15))
        b.sph((0, 0.45, 1.3), (1.0, 1.3, 0.9), body)
        for sx in (-1, 1):
            for y in (-0.2, 1.1):
                b.sph((sx * 0.58, y, 0.5), (0.36, 0.38, 0.52), dark, seg=12)
        ex, ez = 0.56, 0.12
    elif kind == 'b':
        hc, hr = Vector((0, -0.3, 2.95)), Vector((1.05, 1.0, 1.0))
        b.sph((0, 0.15, 1.6), (1.2, 1.25, 1.25), body)
        b.sph((0, -0.35, 1.45), (0.85, 0.95, 0.95), light)                  # belly
        for sx in (-1, 1):
            b.cone((sx * 0.42, 0.05, 0.3), 0.09, 0.09, 0.5, accent, seg=8)
            b.sph((sx * 0.42, -0.15, 0.09), (0.3, 0.42, 0.09), accent, seg=10)
        ex, ez = 0.46, 0.1
    else:
        hc, hr = Vector((0, 0, 1.2)), Vector((1.6, 1.5, 1.2))
        ex, ez = 0.62, 0.22
        if not has('ghost'):
            for sx in (-1, 1):
                b.sph((sx * 0.85, -0.45, 0.16), (0.42, 0.52, 0.16), dark, seg=10)
    b.sph(hc, tuple(hr), body, seg=20)

    def face(x, dz, out=0.0):
        k = max(0.0, 1 - (x / hr.x) ** 2 - (dz / hr.z) ** 2)
        return (x, hc.y - hr.y * math.sqrt(k) - out, hc.z + dz)

    def top(x, dy=0.0, out=0.0):
        k = max(0.0, 1 - (x / hr.x) ** 2 - (dy / hr.y) ** 2)
        return (x, hc.y + dy, hc.z + hr.z * math.sqrt(k) + out)

    # ---- face
    frog, snail, crab = has('frog'), has('snail'), has('crab')
    if frog or snail or crab:                                             # eyes on top
        for sx in (-1, 1):
            p = top(sx * 0.7, -0.5, 0.25 if frog else 0.75)
            if not frog:
                b.cone((p[0], p[1], p[2] - 0.45), 0.1, 0.1, 0.9, body, seg=8)
            b.sph(p, 0.42, WHITE if frog else body, seg=12)
            b.sph((p[0], p[1] - 0.33, p[2] + 0.02), (0.2, 0.12, 0.24), BLACK, seg=10)
            b.sph((p[0] - 0.07, p[1] - 0.43, p[2] + 0.1), 0.07, WHITE, seg=8)
    else:
        for sx in (-1, 1):
            b.sph(face(sx * ex, ez, -0.04), (0.2, 0.1, 0.28), BLACK, seg=12)
            b.sph(face(sx * ex - 0.07, ez + 0.12, 0.05), 0.075, WHITE, seg=8)
    for sx in (-1, 1):
        b.sph(face(sx * (ex + 0.4), ez - 0.36, -0.02), (0.2, 0.07, 0.12), BLUSH, seg=8)
    if kind == 'q':
        mz = face(0, -0.3, -0.1)
        if has('pig'):
            b.cone((mz[0], mz[1] - 0.12, mz[2]), 0.34, 0.34, 0.3, accent, rot=(90, 0, 0), seg=14)
            for sx in (-1, 1):
                b.sph((sx * 0.12, mz[1] - 0.28, mz[2]), (0.06, 0.03, 0.09), shade(accent, 0.6), seg=8)
        else:
            b.sph(mz, (0.46, 0.3, 0.33), light)
            b.sph((0, mz[1] - 0.29, mz[2] + 0.12), (0.14, 0.08, 0.1), BLACK if lum(body) > 90 else BLUSH, seg=8)
    elif kind == 'b':
        p = face(0, -0.14, 0.18)
        if has('duck'):
            b.sph((p[0], p[1] - 0.05, p[2]), (0.42, 0.42, 0.15), accent, seg=12)
        elif not has('bat', 'moth'):
            b.cone(p, 0.28, 0.0, 0.62, accent, rot=(90, 0, 0), seg=10)
        else:
            b.sph(face(0, -0.25, 0.0), (0.1, 0.05, 0.07), BLUSH, seg=8)
    else:
        b.sph(face(0, -0.12, 0.0), (0.16, 0.05, 0.07), shade(body, 0.45), seg=8)   # little mouth
        if not (snail or has('turtle', 'ghost', 'god')):
            b.sph((0, 0.25, hc.z + hr.z * 0.62), (hr.x * 0.62, hr.y * 0.62, hr.z * 0.42), accent)

    # ---- ears
    def ear_long():
        for sx in (-1, 1):
            p = top(sx * 0.5, 0.1, 0.72)
            b.sph(p, (0.26, 0.15, 0.98), body, rot=(-6, sx * 9, 0), seg=12)
            b.sph((p[0], p[1] - 0.09, p[2]), (0.14, 0.09, 0.72), inner, rot=(-6, sx * 9, 0), seg=10)

    def ear_point(sz=1.0):
        for sx in (-1, 1):
            p = top(sx * 0.78, 0.1, 0.22 * sz)
            b.cone(p, 0.44 * sz, 0.0, 0.95 * sz, body, rot=(0, sx * 20, 0), sc=(1, 0.6, 1))
            b.cone((p[0], p[1] - 0.1, p[2] - 0.05), 0.27 * sz, 0.0, 0.65 * sz, inner, rot=(0, sx * 20, 0), sc=(1, 0.6, 1), seg=8)

    def ear_round(r=0.42):
        for sx in (-1, 1):
            p = top(sx * 0.9, 0.1, r * 0.3)
            b.sph(p, (r, r * 0.45, r), body, seg=12)
            b.sph((p[0], p[1] - r * 0.25, p[2]), (r * 0.6, r * 0.3, r * 0.6), inner, seg=10)

    def ear_flop():
        for sx in (-1, 1):
            b.sph((sx * (hr.x + 0.02), hc.y + 0.1, hc.z + 0.15), (0.26, 0.42, 0.72), dark, rot=(0, sx * 14, 0), seg=12)

    def horns(c, curl=False):
        for sx in (-1, 1):
            if curl:
                pts = [top(sx * 0.75, 0.2, 0.1)]
                for k in range(1, 7):
                    a = k * 0.55
                    pts.append((sx * (0.85 + 0.45 * math.sin(a)), hc.y + 0.2 + 0.25 * k / 6, hc.z + hr.z - 0.1 + 0.45 * math.cos(a) - 0.1 * k))
                b.chain(pts, 0.24, 0.1, c)
            else:
                b.cone(top(sx * 0.6, 0.25, 0.3), 0.2, 0.0, 0.9, c, rot=(-18, sx * 22, 0), seg=8)

    if kind == 'q':
        if has('bunny'):
            ear_long()
        elif has('cat', 'fox', 'lynx', 'tiger', 'wolf'):
            ear_point(1.15 if has('fox', 'lynx') else 1.0)
        elif has('pup', 'dog'):
            ear_flop()
        elif has('mouse'):
            ear_round(0.68)
        elif has('goat', 'ram'):
            ear_flop()
            horns(shade(accent, 0.9) if has('goat') else accent, curl=True)
        elif has('dragon'):
            horns(accent)
        elif has('unicorn', 'pegasus'):
            ear_point(0.8)
        elif has('sheep'):
            ear_flop()
        elif ears == 2:
            ear_long()
        else:
            ear_round()
    elif ears == 2:
        if has('moth'):
            for sx in (-1, 1):
                p = top(sx * 0.35, -0.2, 0.0)
                b.chain([(p[0] + sx * 0.12 * k, p[1] - 0.06 * k, p[2] + 0.2 * k) for k in range(5)], 0.07, 0.05, BLACK, seg=8)
                b.sph((p[0] + sx * 0.6, p[1] - 0.3, p[2] + 1.0), 0.14, accent, seg=8)
        elif has('bat'):
            ear_point(1.1)
        elif has('bunny'):
            ear_long()

    # ---- tails (four legs)
    if kind == 'q':
        if has('fox', 'wolf'):
            b.sph((0, 2.0, 1.85), (0.46, 0.85, 0.46), body, rot=(40, 0, 0))
            b.sph((0, 2.5, 2.3), (0.33, 0.45, 0.33), W if has('fox') else accent, rot=(40, 0, 0), seg=12)
        elif has('cat', 'lynx', 'tiger', 'mouse', 'lion'):
            pts = [(0, 1.6 + 0.28 * k, 1.4 + 0.07 * k * k) for k in range(7)]
            b.chain(pts, 0.17, 0.13, accent if has('mouse') else body)
            if has('lion', 'lynx'):
                b.sph(pts[-1], 0.3, shade(body, 0.6) if has('lion') else BLACK, seg=10)
        elif has('pig'):
            b.chain([(0.15 * math.sin(k * 1.3), 1.7 + 0.1 * k, 1.5 + 0.15 * math.cos(k * 1.3)) for k in range(6)], 0.09, 0.07, accent, seg=8)
        elif has('dragon'):
            b.cone((0, 2.2, 1.35), 0.5, 0.05, 1.9, body, rot=(-72, 0, 0))
            b.cone((0, 3.1, 1.75), 0.26, 0.0, 0.5, accent, rot=(-72, 0, 0), seg=6)
        elif has('unicorn', 'pegasus'):
            b.sph((0, 1.95, 1.2), (0.3, 0.45, 0.75), accent, rot=(25, 0, 0))
        elif has('pup', 'dog'):
            b.sph((0, 1.75, 1.95), (0.17, 0.2, 0.5), dark, rot=(25, 0, 0), seg=10)
        else:
            b.sph((0, 1.72, 1.4), 0.36, W if has('bunny') else light, seg=12)

    # ---- wings
    def wings(c, big=1.0, y=0.45, z=2.05):
        for sx in (-1, 1):
            for k in range(3):
                b.sph((sx * (1.15 + 0.42 * k) * big, y + 0.28 * k, z + 0.34 * k * big), ((0.72 - 0.1 * k) * big, 0.12, (0.36 - 0.05 * k) * big),
                      c if k < 2 else tint(c, 0.4), rot=(0, -sx * (22 + 14 * k), sx * 22), seg=12)

    if kind == 'b':
        if has('bat'):
            wings(accent, 1.25, 0.2, 1.7)
        elif has('moth'):
            wings(accent, 1.35, 0.3, 1.6)
            wings(tint(accent, 0.5), 0.8, 0.5, 1.0)
        else:
            for sx in (-1, 1):
                b.sph((sx * 1.2, 0.25, 1.65), (0.2, 0.85, 0.62), dark if not has('owl', 'sky') else accent, rot=(18, 0, -sx * 10), seg=12)
            b.sph((0, 1.4, 1.75), (0.42, 0.5, 0.2), accent, rot=(-35, 0, 0), seg=10)
            if not has('owl'):
                for k in (-1, 0, 1):
                    b.sph(top(k * 0.16, 0.05, 0.12 - abs(k) * 0.06), (0.1, 0.1, 0.24), accent, rot=(0, k * 25, 0), seg=8)
            else:
                for sx in (-1, 1):
                    b.cone(top(sx * 0.6, 0.0, 0.12), 0.22, 0.0, 0.5, dark, rot=(0, sx * 28, 0), seg=8)
    if has('dragon'):
        wings(accent, 1.15)
        for k in range(4):
            b.cone((0, 0.35 + 0.42 * k, 2.25 - 0.06 * k * k), 0.2, 0.0, 0.42, accent, seg=6)
    if has('pegasus', 'angel'):
        wings(W, 1.3)

    # ---- extras by name
    if has('lion'):
        mane = shade(body, 0.62) if not has('crown') else (200, 110, 30)
        for k in range(12):
            a = k * math.tau / 12
            b.sph((1.25 * math.cos(a), hc.y + 0.3, hc.z + 1.12 * math.sin(a)), 0.5, mane, seg=10)
    if has('unicorn', 'pegasus'):
        b.cone(top(0, -0.55, 0.42), 0.17, 0.0, 1.05, GOLD, rot=(22, 0, 0), seg=8)
        for k in range(5):
            b.sph((0, hc.y + 0.5 + 0.2 * k, hc.z + 1.0 - 0.32 * k), 0.34, accent, seg=10)
    if has('sheep'):
        for k in range(9):
            a = k * math.tau / 9
            b.sph((0.75 * math.cos(a), 0.55 + 0.95 * math.sin(a), 1.75), 0.55, W, seg=10)
        b.sph((0, 0.5, 2.05), 0.75, W, seg=12)
        for sx in (-0.4, 0, 0.4):
            b.sph(top(sx, 0.0, 0.05), 0.38, W, seg=10)
    if has('shroom'):
        b.sph(top(0, 0.05, 0.15), (1.25, 1.2, 0.6), body, seg=20)
        for a in range(5):
            b.sph((0.75 * math.cos(a * 1.257), hc.y + 0.05 + 0.75 * math.sin(a * 1.257), hc.z + hr.z + 0.5), (0.22, 0.22, 0.1), W, seg=8)
    if has('pumpkin'):
        b.cone(top(0, 0, 0.2), 0.14, 0.1, 0.5, accent, rot=(10, 12, 0), seg=8)
        b.sph(top(0.3, 0, 0.1), (0.35, 0.18, 0.06), accent, rot=(0, 20, 0), seg=8)
    if has('king', 'crown', 'royal', 'god'):
        cz = top(0, 0.05, 0.12)
        b.cone(cz, 0.52, 0.6, 0.34, GOLD, seg=14)
        for k in range(5):
            a = k * math.tau / 5 + 0.3
            b.cone((cz[0] + 0.5 * math.cos(a), cz[1] + 0.5 * math.sin(a), cz[2] + 0.36), 0.17, 0.0, 0.42, GOLD, seg=6)
            b.sph((cz[0] + 0.58 * math.cos(a + 0.63), cz[1] + 0.58 * math.sin(a + 0.63), cz[2]), 0.1, accent if lum(accent) < 200 else (240, 66, 66), seg=8)
    if has('angel', 'god', 'star'):
        hz = top(0, 0.1, 0.75 if not has('god') else 1.0)
        for k in range(16):
            a = k * math.tau / 16
            b.sph((0.62 * math.cos(a), hz[1] + 0.62 * math.sin(a), hz[2]), 0.1, (255, 236, 110), seg=8)
    if has('robo', 'wind-up', 'pixel', 'cyber', 'laser', 'glitch', 'hologram'):
        p = top(0, 0.15, 0.0)
        b.cone((p[0], p[1], p[2] + 0.3), 0.05, 0.05, 0.6, (60, 64, 84), seg=6)
        b.sph((p[0], p[1], p[2] + 0.68), 0.17, accent, seg=10)
        b.sph(face(0, 0.62, 0.0), (0.5, 0.06, 0.08), accent, seg=8)             # visor line on the forehead
    if has('wind-up'):
        b.cone((0, 1.85, 1.6), 0.07, 0.07, 0.5, accent, rot=(90, 0, 0), seg=6)
        for sx in (-1, 1):
            b.sph((sx * 0.22, 2.12, 1.6), (0.22, 0.07, 0.3), accent, seg=10)
    if has('gem', 'crystal', 'diamond'):
        base_z = hc.z + hr.z * 0.75 if kind == 'o' else 2.1
        for k, (x, y, h, r) in enumerate(((0, 0.75, 1.0, 0.3), (0.5, 0.45, 0.7, 0.24), (-0.5, 0.5, 0.75, 0.24), (0.15, 1.15, 0.6, 0.2), (-0.3, 1.0, 0.5, 0.18))):
            b.cone((x, y, base_z + h * 0.4), r, 0.0, h, accent if k % 2 == 0 else tint(accent, 0.5), rot=(-10 - 8 * y, x * 30, 0), seg=6)
    if has('spark', 'thunder', 'lightning', 'storm'):
        for k in (-1, 0, 1):
            b.cone(top(k * 0.3, 0.2, 0.22 - abs(k) * 0.08), 0.15, 0.0, 0.6 - abs(k) * 0.15, (255, 236, 80), rot=(-15, k * 25, 0), seg=6)
    if has('tiger', 'lynx'):
        for k in range(3):
            b.sph((0, 0.0 + 0.5 * k, 2.14 - 0.03 * k * k), (0.72 - 0.08 * k, 0.09, 0.09), BLACK if has('tiger') else accent, seg=8)
    if snail:
        b.sph((0, 0.55, 2.0), (0.75, 1.25, 1.25), accent, seg=18)
        b.sph((0.72, 0.55, 2.0), (0.12, 0.8, 0.8), shade(accent, 0.75), seg=12)
        b.sph((-0.72, 0.55, 2.0), (0.12, 0.8, 0.8), shade(accent, 0.75), seg=12)
    if has('turtle'):
        b.sph((0, 0.3, 1.5), (1.45, 1.4, 1.0), accent, seg=18)
        for k in range(6):
            a = k * math.tau / 6
            b.sph((0.8 * math.cos(a), 0.3 + 0.8 * math.sin(a), 2.2), (0.36, 0.36, 0.14), tint(accent, 0.45), seg=8)
    if crab:
        for sx in (-1, 1):
            b.chain([(sx * (1.5 + 0.25 * k), -0.3 - 0.25 * k, 0.9 + 0.2 * k) for k in range(3)], 0.2, 0.16, dark, seg=8)
            b.sph((sx * 2.2, -1.05, 1.6), (0.48, 0.4, 0.34), body, seg=12)
            b.sph((sx * 2.05, -1.4, 1.75), (0.2, 0.3, 0.12), accent, seg=8)
            for k in range(3):
                b.sph((sx * (1.5 + 0.12 * k), 0.3 + 0.45 * k, 0.3), (0.4, 0.12, 0.12), dark, rot=(0, sx * 25, 0), seg=8)
    if has('seal', 'whale'):
        for sx in (-1, 1):
            b.sph((sx * 1.55, 0.1, 0.5), (0.6, 0.38, 0.14), dark, rot=(0, sx * 25, sx * 20), seg=10)
        b.cone((0, 1.6, 0.9), 0.4, 0.15, 0.9, body, rot=(-65, 0, 0))
        for sx in (-1, 1):
            b.sph((sx * 0.5, 2.1, 1.35), (0.55, 0.3, 0.14), dark if has('seal') else accent, rot=(0, 0, sx * 35), seg=10)
        if has('whale'):
            for k, (x, z) in enumerate(((0, 0.5), (-0.3, 0.85), (0.3, 0.85), (0, 1.15))):
                b.sph(top(x, 0.1, z), 0.2 - 0.02 * k, (200, 240, 255), seg=8)
            b.sph((0, -0.35, 0.72), (1.25, 1.1, 0.62), accent)
    if has('ghost'):
        for k in range(8):
            a = k * math.tau / 8
            b.sph((1.15 * math.cos(a), 1.1 * math.sin(a), 0.32), 0.42, body, seg=10)
        for sx in (-1, 1):
            b.sph((sx * 1.6, -0.2, 1.2), (0.36, 0.3, 0.26), body, seg=10)
    if has('gummy', 'teddy', 'bear'):
        b.sph((0, -0.35, 1.2), (0.62, 0.5, 0.6), light)                           # tummy
    return b


# ---------------------------------------------------------------- eggs
def build_egg(col, spot, seed, bumps=False):
    b = B()
    R = 1.5
    res = bmesh.ops.create_uvsphere(b.bm, u_segments=24, v_segments=16, radius=R)
    for v in res['verts']:
        if v.co.z > 0:
            k = v.co.z / R
            v.co.z *= 1.38
            v.co.x *= 1 - 0.12 * k * k
            v.co.y *= 1 - 0.12 * k * k
    b._paint(res['verts'], col)
    rng = random.Random(seed)
    if spot:
        for _ in range(9):
            a, t = rng.uniform(0, math.tau), rng.uniform(-0.75, 0.8)
            rr = math.sqrt(max(0.0, 1 - t * t))
            z = t * R * (1.38 if t > 0 else 1.0)
            sq = 1 - 0.12 * t * t if t > 0 else 1.0
            p = Vector((rr * math.cos(a) * R * sq, rr * math.sin(a) * R * sq, z))
            s = rng.uniform(0.26, 0.46)
            if bumps:
                b.sph(tuple(p * 0.97), s * 0.7, spot, seg=8)
            else:
                b.sph(tuple(p * 0.55), 0.45 * p.length + 0.03 + s * 0.12, spot, seg=14)   # big sphere deep inside = flat round spot
    return b


# ---------------------------------------------------------------- scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
MAT = bpy.data.materials.new('VertexColour')
MAT.use_nodes = True
nt = MAT.node_tree
bsdf = nt.nodes['Principled BSDF']
attr = nt.nodes.new('ShaderNodeVertexColor')
attr.layer_name = 'Col'
nt.links.new(attr.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Roughness'].default_value = 0.55

objs = []
for zi, z in enumerate(ZONES):
    for pi, (name, c, a, ears, kind) in enumerate(z['pets']):
        objs.append(build_pet(name, c, a, ears, kind).finish(f'Pet_{zi + 1}_{pi + 1}', pi * 6.5, -zi * 7.0))
    objs.append(build_egg(z['egg'], z['spot'] if z['spot'] != z['egg'] else shade(z['egg'], 0.8), 100 + zi).finish(f'Egg_{zi + 1}', 5 * 6.5 + 1, -zi * 7.0, flip=False))
objs.append(build_egg(GOLD, (255, 244, 170), 1).finish('Egg_Gold', 6 * 6.5 + 1, 0, flip=False))
objs.append(build_egg((122, 138, 70), (70, 84, 40), 2, bumps=True).finish('Egg_Rotten', 6 * 6.5 + 1, -7, flip=False))
objs.append(build_egg((120, 70, 230), (255, 236, 80), 3).finish('Egg_Storm', 6 * 6.5 + 1, -14, flip=False))
tris = sum(len(o.data.polygons) for o in objs)
print(f'{len(objs)} meshes, {tris} triangles, biggest {max(len(o.data.polygons) for o in objs)}')

if 'nofbx' not in ARGS:
    for o in bpy.data.objects:
        o.select_set(o in objs)
    bpy.context.view_layer.objects.active = objs[0]
    fbx = OUT / 'RainingEggsAssets.fbx'
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'MESH'}, apply_scale_options='FBX_SCALE_UNITS',
                             mesh_smooth_type='FACE', colors_type='SRGB', add_leaf_bones=False, bake_anim=False)
    desk = pathlib.Path(os.environ['USERPROFILE']) / 'Desktop' / 'youtube' / 'roblox' / fbx.name
    shutil.copyfile(fbx, desk)
    print('wrote', fbx, fbx.stat().st_size // 1024, 'KB ->', desk)

# ---------------------------------------------------------------- preview renders
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.view_settings.view_transform = 'Standard'
sc.world = bpy.data.worlds.new('W')
sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.75, 0.86, 1.0, 1)
sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.9
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
sun.data.energy = 3.2
sun.rotation_euler = (math.radians(50), 0, math.radians(150))
sc.collection.objects.link(sun)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
cam.data.type = 'ORTHO'
sc.collection.objects.link(cam)
sc.camera = cam
gm = bpy.data.meshes.new('G')
gb = bmesh.new()
bmesh.ops.create_grid(gb, x_segments=1, y_segments=1, size=200)
gb.to_mesh(gm)
gb.free()
ground = bpy.data.objects.new('Ground', gm)
gmat = bpy.data.materials.new('G')
gmat.diffuse_color = (0.33, 0.62, 0.25, 1)
gm.materials.append(gmat)
sc.collection.objects.link(ground)


def shot(name, cx, cy, width, res=(1600, 900)):
    # pets look to +Y, so the camera stands at +Y and looks back, a bit from above and from the side
    d = Vector((0.45, 1.0, 0.55)).normalized()
    cam.location = Vector((cx, cy, 2.0)) + d * 80
    cam.rotation_euler = (Vector((cx, cy, 2.0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = width
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = str(OUT / f'preview_{name}.png')
    bpy.ops.render.render(write_still=True)


views = [a for a in ARGS if a != 'nofbx'] or ['a', 'b']
if 'a' in views:
    shot('a', 15, -14, 44)        # zones 1-5
if 'b' in views:
    shot('b', 15, -49, 44)        # zones 6-10
if 'all' in views:
    shot('all', 18, -31.5, 78, (1600, 1300))
