r"""100 blocky studded pets for Raining Eggs, defined once here.
  py gen_pets.py      -> pets.json + ..\game\PetData.lua (data for PetBuilder.lua)
Units are studs. Pet origin = ground centre, the pet looks towards -Z (Roblox front).
Each part: size, position, rotation (degrees), colour, material, tag (Head/Tail/WingL/WingR/Float/Spin/Glow), all surfaces studded.
"""
import json, math, pathlib, random

HERE = pathlib.Path(__file__).resolve().parent
RARITIES = ['Common', 'Uncommon', 'Rare', 'Epic', 'Legendary', 'Mythic', 'Secret', 'Divine']
BASE = 2.0   # pets are built big so the 1-stud studs look fine and detailed (like the reference games)
SCALE = {k: v * BASE for k, v in {'Common': 1.0, 'Uncommon': 1.08, 'Rare': 1.18, 'Epic': 1.3, 'Legendary': 1.45, 'Mythic': 1.8, 'Secret': 2.0, 'Divine': 2.1}.items()}
INK = (24, 20, 30)
WHITE = (248, 248, 252)


def sh(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


class Pet:
    def __init__(self, pal):
        self.parts = []
        self.pal = pal
        self.a = {}            # anchor points for the extras

    def B(self, size, pos, col, mat='Plastic', rot=(0, 0, 0), tag='', glow=False, alpha=0.0):
        self.parts.append({'s': [round(v, 3) for v in size], 'p': [round(v, 3) for v in pos], 'r': [round(v, 2) for v in rot],
                           'c': list(col), 'm': 'Neon' if glow else mat, 't': tag, 'a': alpha})

    def mirror(self, size, pos, col, mat='Plastic', rot=(0, 0, 0), tag='', glow=False, alpha=0.0):
        """the same block on both sides (x and -x); tags *L/*R are swapped automatically"""
        for sx in (-1, 1):
            t = tag
            if tag.endswith('L') or tag.endswith('R'):
                t = tag[:-1] + ('L' if sx < 0 else 'R')
            self.B(size, (pos[0] * sx, pos[1], pos[2]), col, mat, (rot[0], rot[1] * sx, rot[2] * sx), t, glow, alpha)


# ---------------------------------------------------------------- faces
def face(P, hc, hs, style='angry', mouth=None, eye=WHITE, pupil=INK, snout=None, eyes_glow=False):
    fz = hc[2] - hs[2] / 2
    e = min(hs[0], hs[1]) * 0.26
    ey = hc[1] + hs[1] * 0.12
    ex = hs[0] * 0.24
    for sx in (-1, 1):
        x = sx * ex
        P.B((e, e * 1.1, 0.16), (x, ey, fz - 0.05), eye, glow=eyes_glow)
        P.B((e * 0.5, e * 0.62, 0.14), (x - sx * e * 0.17, ey - e * 0.12, fz - 0.14), pupil)
        P.B((e * 0.18, e * 0.2, 0.12), (x - sx * e * 0.27, ey + e * 0.06, fz - 0.22), WHITE)
        if style == 'angry':
            P.B((e * 1.25, e * 0.26, 0.18), (x, ey + e * 0.72, fz - 0.08), INK, rot=(0, 0, 20 * sx))
        elif style == 'sleepy':
            P.B((e * 1.1, e * 0.3, 0.18), (x, ey + e * 0.38, fz - 0.1), P.pal[0])
    if snout:
        ss = (hs[0] * snout[0], hs[1] * snout[1], hs[2] * snout[2])
        sc = (0, hc[1] - hs[1] * 0.22, fz - ss[2] / 2 + 0.05)
        P.B(ss, sc, P.pal[2])
        P.B((ss[0] * 0.38, ss[1] * 0.28, 0.16), (0, sc[1] + ss[1] * 0.28, sc[2] - ss[2] / 2 - 0.05), INK)    # nose
        fz2, my = sc[2] - ss[2] / 2, sc[1] - ss[1] * 0.3
    else:
        fz2, my = fz, hc[1] - hs[1] * 0.3
    if mouth == 'teeth':
        n = 4
        w = (hs[0] * 0.5) / n
        for k in range(n):
            P.B((w * 0.7, w * 1.1, 0.14), (-hs[0] * 0.25 + w * (k + 0.5), my - 0.05, fz2 - 0.06), WHITE)
    elif mouth == 'fangs':
        P.mirror((0.22, 0.6, 0.18), (hs[0] * 0.14, my - 0.35, fz2 - 0.05), WHITE)
    elif mouth == 'sabers':
        P.mirror((0.28, 1.5, 0.28), (hs[0] * 0.16, my - 0.8, fz2 + 0.1), WHITE)
    elif mouth == 'smile':
        P.B((hs[0] * 0.3, 0.14, 0.12), (0, my, fz2 - 0.05), INK)
    elif mouth == 'beak':
        P.B((hs[0] * 0.36, hs[1] * 0.18, hs[2] * 0.4), (0, hc[1] - hs[1] * 0.08, fz - hs[2] * 0.18), (255, 176, 40))
        P.B((hs[0] * 0.28, hs[1] * 0.12, hs[2] * 0.3), (0, hc[1] - hs[1] * 0.24, fz - hs[2] * 0.12), (230, 140, 30))


# ---------------------------------------------------------------- archetypes (each sets anchors in P.a)
def quad(P, W=3.0, H=2.4, L=4.4, lh=1.6, lw=0.9, hk=1.0, snout=(0.6, 0.42, 0.36), mouth=None, ears='pointy',
         tail='thin', style='angry', neck=False, eyes_glow=False):
    m, d, l, acc = P.pal
    by = lh + H / 2
    P.B((W, H, L), (0, by, 0), m)
    P.B((W * 1.06, H * 0.9, L * 0.32), (0, by + 0.05, -L * 0.3), m)                          # chest
    P.B((W * 0.86, H * 0.28, L * 0.8), (0, lh + H * 0.12, 0), l)                              # belly
    P.B((W * 0.7, H * 0.16, L * 0.7), (0, by + H / 2 + 0.06, 0.1), d)                         # back stripe
    for zz in (-L / 2 + lw * 0.75, L / 2 - lw * 0.75):
        P.mirror((lw, lh + 0.2, lw), (W / 2 - lw / 2, lh / 2 + 0.1, zz), m)
        P.mirror((lw * 1.12, 0.36, lw * 1.25), (W / 2 - lw / 2, 0.18, zz - 0.08), d)
    hs = (W * 1.02 * hk, H * 1.0 * hk, W * 0.9 * hk)
    hc = (0, lh + H * 0.8 + hs[1] * 0.18 + (0.7 if neck else 0), -L / 2 - hs[2] * 0.28 - (0.5 if neck else 0))
    if neck:
        P.B((W * 0.6, H * 0.9, W * 0.6), (0, hc[1] - hs[1] * 0.45, hc[2] + hs[2] * 0.25), m, rot=(-25, 0, 0))
    P.B(hs, hc, m, tag='Head')
    P.B((hs[0] * 0.92, hs[1] * 0.18, hs[2] * 0.9), (0, hc[1] + hs[1] / 2 + 0.05, hc[2] + 0.05), d, tag='Head')
    face(P, hc, hs, style, mouth, snout=snout, eyes_glow=eyes_glow)
    if ears == 'pointy':
        P.mirror((hs[0] * 0.24, hs[1] * 0.42, 0.4), (hs[0] * 0.32, hc[1] + hs[1] / 2 + hs[1] * 0.16, hc[2] + 0.2), m, rot=(0, 0, 12), tag='Head')
        P.mirror((hs[0] * 0.12, hs[1] * 0.26, 0.2), (hs[0] * 0.32, hc[1] + hs[1] / 2 + hs[1] * 0.12, hc[2] - 0.05), acc, rot=(0, 0, 12), tag='Head')
    elif ears == 'round':
        P.mirror((hs[0] * 0.28, hs[1] * 0.28, 0.4), (hs[0] * 0.36, hc[1] + hs[1] / 2 + 0.05, hc[2] + 0.2), d, tag='Head')
    elif ears == 'long':
        P.mirror((hs[0] * 0.2, hs[1] * 0.95, 0.35), (hs[0] * 0.24, hc[1] + hs[1] * 0.95, hc[2] + 0.3), m, rot=(-8, 0, 6), tag='Head')
        P.mirror((hs[0] * 0.1, hs[1] * 0.7, 0.2), (hs[0] * 0.24, hc[1] + hs[1] * 0.92, hc[2] + 0.12), acc, rot=(-8, 0, 6), tag='Head')
    elif ears == 'floppy':
        P.mirror((0.35, hs[1] * 0.6, hs[2] * 0.4), (hs[0] / 2 + 0.12, hc[1] + hs[1] * 0.05, hc[2]), d, rot=(0, 0, -10), tag='Head')
    tb = (0, by + H * 0.25, L / 2)
    if tail == 'thin':
        P.B((0.4, 0.4, 1.4), (0, tb[1] + 0.3, tb[2] + 0.6), m, rot=(-35, 0, 0), tag='Tail')
        P.B((0.45, 0.45, 0.6), (0, tb[1] + 0.95, tb[2] + 1.15), d, tag='Tail')
    elif tail == 'fluffy':
        P.B((0.9, 0.9, 1.6), (0, tb[1] + 0.4, tb[2] + 0.7), m, rot=(-40, 0, 0), tag='Tail')
        P.B((0.95, 0.95, 0.7), (0, tb[1] + 1.2, tb[2] + 1.25), l, rot=(-40, 0, 0), tag='Tail')
    elif tail == 'stub':
        P.B((0.6, 0.6, 0.5), (0, tb[1], tb[2] + 0.2), d, tag='Tail')
    elif tail == 'long':
        for k in range(4):
            P.B((0.5 - k * 0.07,) * 2 + (0.9,), (0, tb[1] - k * 0.15, tb[2] + 0.4 + k * 0.8), m if k < 3 else d, tag='Tail')
    P.a.update(hc=hc, hs=hs, body=(0, by, 0), bs=(W, H, L), top=by + H / 2, tail=(0, tb[1] + 1.0, tb[2] + 1.2), lh=lh)


def biped(P, W=3.2, H=3.0, D=2.4, lh=1.2, arm=2.6, hk=0.85, snout=(0.5, 0.4, 0.3), mouth='fangs', ears='round', style='angry',
          eyes_glow=False, tail=None):
    m, d, l, acc = P.pal
    by = lh + H / 2
    P.B((W, H, D), (0, by, 0), m)
    P.B((W * 0.62, H * 0.6, 0.2), (0, by - H * 0.05, -D / 2 - 0.08), l)                         # chest plate
    P.B((W * 1.18, H * 0.38, D * 0.95), (0, by + H * 0.32, 0.05), m)                            # big shoulders
    P.mirror((W * 0.32, lh + 0.2, D * 0.55), (W * 0.28, lh / 2, 0.1), d)                          # legs
    P.mirror((W * 0.36, 0.35, D * 0.7), (W * 0.28, 0.17, -0.1), INK)
    P.mirror((W * 0.3, arm, W * 0.3), (W / 2 + W * 0.18, by + H * 0.28 - arm / 2, -0.1), m, tag='ArmL')
    P.mirror((W * 0.38, 0.6, W * 0.38), (W / 2 + W * 0.18, by + H * 0.28 - arm, -0.15), d, tag='ArmL')
    hs = (W * hk, W * hk * 0.95, W * hk * 0.85)
    hc = (0, by + H / 2 + hs[1] * 0.42, -D * 0.12)
    P.B(hs, hc, m, tag='Head')
    P.B((hs[0] * 0.9, hs[1] * 0.2, hs[2] * 0.9), (0, hc[1] + hs[1] / 2 + 0.05, hc[2] + 0.05), d, tag='Head')
    face(P, hc, hs, style, mouth, snout=snout, eyes_glow=eyes_glow)
    if ears == 'round':
        P.mirror((hs[0] * 0.26, hs[1] * 0.26, 0.4), (hs[0] * 0.42, hc[1] + hs[1] / 2, hc[2] + 0.1), d, tag='Head')
    elif ears == 'pointy':
        P.mirror((hs[0] * 0.2, hs[1] * 0.4, 0.4), (hs[0] * 0.34, hc[1] + hs[1] * 0.62, hc[2] + 0.1), m, rot=(0, 0, 12), tag='Head')
    if tail == 'dino':
        for k in range(4):
            P.B((1.2 - k * 0.24, 1.0 - k * 0.18, 1.2), (0, by - 0.5 - k * 0.25, D / 2 + 0.4 + k * 1.0), m, tag='Tail')
    P.a.update(hc=hc, hs=hs, body=(0, by, 0), bs=(W, H, D), top=by + H / 2 + 0.2, tail=(0, by, D / 2 + 1.5), lh=lh)


def dino(P, **kw):
    """T-rex style: big head forward, tiny arms, thick tail"""
    m, d, l, acc = P.pal
    lh, W, H, L = 2.0, 2.8, 2.8, 4.0
    by = lh + H / 2
    P.B((W, H, L), (0, by, 0), m, rot=(-12, 0, 0))
    P.B((W * 0.8, H * 0.4, L * 0.8), (0, by - H * 0.38, -0.2), l, rot=(-12, 0, 0))
    P.mirror((1.1, lh + 0.6, 1.3), (W * 0.32, lh / 2 + 0.2, 0.6), m)
    P.mirror((1.3, 0.4, 1.8), (W * 0.32, 0.2, 0.2), d)
    P.mirror((0.4, 0.9, 0.4), (W * 0.45, by - 0.1, -L / 2 + 0.2), m, rot=(30, 0, 0), tag='ArmL')
    hs = (2.6, 2.2, 3.2)
    hc = (0, by + H * 0.65, -L / 2 - 0.9)
    P.B(hs, hc, m, tag='Head')
    P.B((hs[0] * 0.92, 0.7, hs[2] * 0.9), (0, hc[1] - hs[1] / 2 - 0.25, hc[2] - 0.1), d, tag='Head')     # jaw
    for k in range(5):
        P.B((0.22, 0.4, 0.22), (-0.9 + k * 0.45, hc[1] - hs[1] / 2 + 0.02, hc[2] - hs[2] / 2 + 0.25), WHITE, tag='Head')
    face(P, (0, hc[1] + 0.4, hc[2] + 0.6), (hs[0], hs[1] * 0.7, hs[2] * 0.6), 'angry', None, eyes_glow=kw.get('eyes_glow'))
    for k in range(5):
        P.B((1.6 - k * 0.3, 1.5 - k * 0.27, 1.3), (0, by + 0.2 - k * 0.3, L / 2 + 0.3 + k * 1.1), m, tag='Tail')
    P.a.update(hc=hc, hs=hs, body=(0, by, 0), bs=(W, H, L), top=by + H / 2 + 0.3, tail=(0, by - 0.8, L / 2 + 5), lh=lh)


def fish(P, W=2.2, H=2.6, L=5.0, mouth='teeth', fin='shark', hover=1.2, style='angry', eyes_glow=False):
    m, d, l, acc = P.pal
    y = hover + H / 2
    P.B((W, H, L), (0, y, 0), m, tag='Float')
    P.B((W * 0.9, H * 0.4, L * 0.92), (0, y - H * 0.32, -0.05), l, tag='Float')               # light belly
    P.B((W * 0.82, H * 0.82, 1.2), (0, y - 0.05, -L / 2 - 0.5), m, tag='Float')                 # snout
    P.B((W * 0.76, H * 0.3, 1.1), (0, y - H * 0.3, -L / 2 - 0.45), l, tag='Float')
    P.B((W * 0.6, H * 0.6, 1.0), (0, y, L / 2 + 0.45), m, tag='Float')                         # tail stalk
    P.B((0.4, H * 1.0, 1.1), (0, y + H * 0.42, L / 2 + 1.1), d, rot=(-35, 0, 0), tag='Tail')   # tail fin up
    P.B((0.4, H * 0.7, 1.0), (0, y - H * 0.3, L / 2 + 1.0), d, rot=(35, 0, 0), tag='Tail')     # tail fin down
    if fin == 'shark':
        P.B((0.4, H * 0.9, 1.4), (0, y + H * 0.75, 0.1), d, rot=(-28, 0, 0), tag='Float')
    elif fin == 'sail':
        P.B((0.3, H * 1.0, L * 0.7), (0, y + H * 0.85, 0.2), acc, tag='Float')
    P.mirror((1.4, 0.3, 1.0), (W / 2 + 0.6, y - H * 0.25, -0.6), d, rot=(0, 15, -25), tag='WingL')
    for k in range(3):                                                                          # gills
        P.mirror((0.06, H * 0.42, 0.14), (W / 2 + 0.02, y + 0.05, -L / 2 + 0.6 + k * 0.32), d, tag='Float')
    hc, hs = (0, y + 0.1, -L / 2 - 0.2), (W * 0.9, H * 0.9, 1.6)
    face(P, hc, hs, style, mouth, eyes_glow=eyes_glow)
    for p in P.parts:
        if p['t'] == '' and p['p'][1] > hover * 0.5:
            p['t'] = 'Float'
    P.a.update(hc=hc, hs=hs, body=(0, y, 0), bs=(W, H, L), top=y + H / 2, tail=(0, y, L / 2 + 1.4), lh=hover)


def bird(P, W=2.4, H=2.6, D=2.4, wing='feather', tailf=True, style='angry', mouth='beak', crest=True, eyes_glow=False, legs=True):
    m, d, l, acc = P.pal
    lh = 0.9 if legs else 0.4
    by = lh + H / 2
    P.B((W, H, D), (0, by, 0), m)
    P.B((W * 0.75, H * 0.62, 0.2), (0, by - H * 0.1, -D / 2 - 0.08), l)
    if legs:
        P.mirror((0.3, lh + 0.2, 0.3), (W * 0.22, lh / 2, 0), (255, 176, 40))
        P.mirror((0.6, 0.18, 0.8), (W * 0.22, 0.09, -0.2), (255, 176, 40))
    hs = (W * 0.86, W * 0.8, W * 0.8)
    hc = (0, by + H / 2 + hs[1] * 0.38, -D * 0.12)
    P.B(hs, hc, m, tag='Head')
    face(P, hc, hs, style, mouth, eyes_glow=eyes_glow)
    if crest:
        for k in range(3):
            P.B((0.3, 0.9 - k * 0.15, 0.3), (0, hc[1] + hs[1] / 2 + 0.35, hc[2] + 0.1 + k * 0.4), acc, rot=(-20 - k * 15, 0, 0), tag='Head')
    if wing in ('feather', 'flame', 'angel'):
        n = 4
        for k in range(n):
            c = (acc if k == n - 1 else (l if k % 2 else m)) if wing == 'feather' else (acc if k % 2 else d)
            P.mirror((1.0 + k * 0.55, 0.3, 1.8 - k * 0.25), (W / 2 + 0.45 + k * 0.25, by + 0.3 + k * 0.32, 0.1 + k * 0.12),
                     c, rot=(0, 0, -18 - k * 6), tag='WingL', glow=(wing == 'flame' and k % 2 == 1))
    if tailf:
        for k, a in enumerate((-20, 0, 20)):
            P.B((0.5, 0.25, 1.8), (math.sin(math.radians(a)) * 0.6, by - 0.2, D / 2 + 0.8), d if k != 1 else acc, rot=(20, a, 0), tag='Tail')
    P.a.update(hc=hc, hs=hs, body=(0, by, 0), bs=(W, H, D), top=hc[1] + hs[1] / 2, tail=(0, by, D / 2 + 1.5), lh=lh)


def reptile(P, W=2.6, H=1.4, L=5.0, kind='croc', style='angry', eyes_glow=False):
    m, d, l, acc = P.pal
    lh = 0.7
    by = lh + H / 2
    P.B((W, H, L), (0, by, 0), m)
    P.B((W * 0.9, H * 0.3, L * 0.9), (0, lh + H * 0.12, 0), l)
    for zz in (-L / 2 + 0.6, L / 2 - 0.7):
        P.mirror((0.8, 0.9, 0.8), (W / 2 + 0.15, 0.45, zz), m, rot=(0, 0, 15))
    if kind == 'croc':
        hs = (W * 0.9, H * 0.95, 2.0)
        hc = (0, by + 0.1, -L / 2 - 0.9)
        P.B(hs, hc, m, tag='Head')
        P.B((W * 0.7, H * 0.5, 2.0), (0, by - 0.05, hc[2] - 1.7), m, tag='Head')                 # long jaw
        P.B((W * 0.66, 0.3, 1.9), (0, by - 0.4, hc[2] - 1.7), l, tag='Head')
        for k in range(6):
            P.mirror((0.16, 0.3, 0.16), (W * 0.3, by - 0.28, hc[2] - 0.9 - k * 0.32), WHITE, tag='Head')
        face(P, (0, hc[1] + 0.4, hc[2] + 0.2), (hs[0], hs[1], hs[2] * 0.6), style, None, eyes_glow=eyes_glow)
        for k in range(6):                                                                     # back ridges
            P.B((0.4, 0.35, 0.4), (0, by + H / 2 + 0.15, -L / 2 + 0.5 + k * 0.85), d)
        for k in range(4):
            P.B((W * 0.6 - k * 0.15, H * 0.8 - k * 0.15, 1.3), (0, by - k * 0.1, L / 2 + 0.6 + k * 1.2), m, tag='Tail')
    elif kind == 'axolotl':
        hs = (W * 1.25, H * 1.6, 2.0)
        hc = (0, by + 0.35, -L / 2 - 0.7)
        P.B(hs, hc, m, tag='Head')
        face(P, hc, hs, 'happy', 'smile', eyes_glow=eyes_glow)
        for k, (yy, a) in enumerate(((0.6, 30), (0.0, 5), (-0.6, -20))):
            P.mirror((1.5, 0.3, 0.3), (hs[0] / 2 + 0.6, hc[1] + yy, hc[2] + 0.3), acc, rot=(0, 0, a), glow=P.a.get('glowgills', False), tag='Head')
        P.B((0.3, 0.9, 3.0), (0, by + 0.2, L / 2 + 1.3), acc, tag='Tail')
        P.B((W * 0.5, H * 0.6, 2.4), (0, by, L / 2 + 1.1), m, tag='Tail')
    elif kind == 'frog':
        hs = (W * 1.3, H * 1.6, 2.4)
        hc = (0, by + 0.6, -L / 2 + 0.4)
        P.B(hs, hc, m, tag='Head')
        P.mirror((0.9, 0.9, 0.9), (hs[0] * 0.3, hc[1] + hs[1] / 2 + 0.3, hc[2]), m, tag='Head')
        face(P, (0, hc[1] + 0.9, hc[2] - 0.05), (hs[0] * 0.95, 1.2, hs[2]), 'angry', None, eyes_glow=eyes_glow)
        P.B((hs[0] * 0.7, 0.18, 0.12), (0, hc[1] - 0.3, hc[2] - hs[2] / 2 - 0.04), INK)
        P.mirror((1.0, 0.8, 1.8), (W / 2 + 0.3, 0.5, L / 2 - 0.6), m)
    elif kind == 'turtle':
        hs = (1.4, 1.3, 1.4)
        hc = (0, by + 0.2, -L / 2 - 0.5)
        P.B(hs, hc, l, tag='Head')
        face(P, hc, hs, style, 'smile', eyes_glow=eyes_glow)
        P.B((W * 1.25, H * 0.9, L * 1.0), (0, by + H * 0.7, 0), d)                              # shell, layered
        P.B((W * 1.0, H * 0.7, L * 0.8), (0, by + H * 1.3, 0), acc)
        P.B((W * 0.6, H * 0.5, L * 0.5), (0, by + H * 1.75, 0), d)
    P.a.update(hc=hc, hs=hs, body=(0, by, 0), bs=(W, H, L), top=by + H / 2 + (H * 1.4 if kind == 'turtle' else 0), tail=(0, by, L / 2 + 3), lh=lh)


def serpent(P, segs=8, R=1.4, heads=1, style='angry', eyes_glow=False, mouth='fangs'):
    m, d, l, acc = P.pal
    pts = []
    for k in range(segs):
        t = k / (segs - 1)
        pts.append((math.sin(t * 5.0) * 1.6, R / 2 + t * t * 4.5, 3.5 - t * 6.0))
    for k, p in enumerate(pts):
        s = R * (0.65 + 0.35 * k / segs)
        P.B((s, s, s * 1.2), p, m if k % 2 else d, tag='Tail' if k < 3 else '')
        P.B((s * 0.7, s * 0.2, s * 1.1), (p[0], p[1] - s * 0.45, p[2]), l)
        if k % 2 == 0:
            P.B((0.3, s * 0.5, 0.3), (p[0], p[1] + s * 0.6, p[2]), acc, rot=(-25, 0, 0))
    top = pts[-1]
    offs = [0] if heads == 1 else [(-1.6 + 3.2 * i / (heads - 1)) for i in range(heads)]
    for ox in offs:
        hc = (top[0] + ox, top[1] + 1.2 + (0 if ox == 0 else -0.4), top[2] - 1.0)
        hs = (R * 1.5, R * 1.25, R * 1.8)
        if ox:
            P.B((0.9, 1.6, 0.9), (top[0] + ox * 0.5, top[1] + 0.4, top[2] - 0.4), m, rot=(0, 0, -ox * 12))
        P.B(hs, hc, m, tag='Head')
        P.B((hs[0] * 0.8, hs[1] * 0.35, hs[2] * 0.8), (hc[0], hc[1] - hs[1] * 0.55, hc[2] - 0.2), d, tag='Head')
        face(P, hc, hs, style, mouth, eyes_glow=eyes_glow)
        P.mirror((0.3, 1.0, 0.3), (hs[0] * 0.3, hc[1] + hs[1] / 2 + 0.4, hc[2] + 0.4), acc, rot=(-25, 0, 10), tag='Head')
        P.a.setdefault('hc', hc)
        P.a.setdefault('hs', hs)
    P.a.update(body=(0, 2.5, 0), bs=(2.5, 4, 6), top=top[1] + 2.2, tail=pts[0], lh=0.5)


def spider(P, W=2.6, H=1.6, L=2.4, kind='spider', style='angry', eyes_glow=False):
    m, d, l, acc = P.pal
    by = 1.6
    P.B((W, H, L), (0, by, 0), m)
    P.B((W * 1.3, H * 1.4, L * 1.3), (0, by + 0.3, L * 1.05), d)                                 # abdomen
    P.B((W * 0.8, 0.2, L * 0.9), (0, by + 0.3 + H * 0.7 + 0.05, L * 1.05), acc)
    nl = 4 if kind != 'crab' else 3
    for k in range(nl):
        zz = -L / 2 + 0.3 + k * (L / (nl - 0.6))
        P.mirror((1.8, 0.35, 0.35), (W / 2 + 0.75, by + 0.35, zz), m, rot=(0, -10 + k * 8, 30))
        P.mirror((0.35, 1.8, 0.35), (W / 2 + 1.55, by - 0.6, zz), d, rot=(0, 0, -10))
    hs = (W * 0.8, H * 0.95, 1.2)
    hc = (0, by + 0.1, -L / 2 - 0.4)
    P.B(hs, hc, m, tag='Head')
    face(P, hc, hs, style, 'fangs', eyes_glow=eyes_glow)
    if kind == 'crab':
        for sx in (-1, 1):
            P.B((0.5, 0.5, 1.4), (sx * (W / 2 + 0.6), by + 0.3, -L / 2 - 0.4), m, rot=(0, sx * 20, 0), tag='Arm' + ('L' if sx < 0 else 'R'))
            P.B((1.1, 1.0, 1.0), (sx * (W / 2 + 1.0), by + 0.5, -L / 2 - 1.3), acc, tag='Arm' + ('L' if sx < 0 else 'R'))
    if kind == 'scorpion':
        for k in range(5):
            P.B((0.7 - k * 0.06,) * 2 + (0.8,), (0, by + 0.8 + k * 0.75, L * 1.5 + 0.4 - k * 0.35 * (k > 2)), m, tag='Tail')
        P.B((0.5, 0.9, 0.5), (0, by + 4.6, L * 1.2), acc, rot=(40, 0, 0), glow=True, tag='Tail')
        for sx in (-1, 1):
            P.B((1.1, 0.8, 1.2), (sx * (W / 2 + 0.8), by + 0.2, -L / 2 - 1.1), acc, tag='Arm' + ('L' if sx < 0 else 'R'))
    P.a.update(hc=hc, hs=hs, body=(0, by, 0), bs=(W, H, L), top=by + H, tail=(0, by + 1, L * 1.6), lh=by - H / 2)


def blob(P, S_=3.0, style='happy', mouth='smile', eyes_glow=False, kind='slime'):
    m, d, l, acc = P.pal
    P.B((S_, S_ * 0.7, S_), (0, S_ * 0.35, 0), m)
    P.B((S_ * 0.8, S_ * 0.3, S_ * 0.8), (0, S_ * 0.85, 0), m)
    P.B((S_ * 0.5, S_ * 0.2, S_ * 0.5), (0, S_ * 1.08, 0), l)
    if kind == 'shell':
        P.B((S_ * 0.9, S_ * 0.9, S_ * 0.9), (0, S_ * 0.85, S_ * 0.45), acc)
        P.B((S_ * 0.6, S_ * 0.6, S_ * 0.95), (0, S_ * 0.95, S_ * 0.45), d)
    hc, hs = (0, S_ * 0.45, 0), (S_, S_ * 0.7, S_)
    face(P, hc, hs, style, mouth, eyes_glow=eyes_glow)
    P.a.update(hc=hc, hs=hs, body=(0, S_ * 0.4, 0), bs=(S_, S_, S_), top=S_ * 1.2, tail=(0, S_ * 0.4, S_ / 2 + 0.5), lh=0.2)


def octopus(P, S_=3.2, style='angry', eyes_glow=False):
    m, d, l, acc = P.pal
    y = 2.2
    P.B((S_, S_ * 1.1, S_), (0, y + S_ * 0.55, 0), m, tag='Float')
    P.B((S_ * 0.8, S_ * 0.4, S_ * 0.8), (0, y + S_ * 1.25, 0.15), m, tag='Float')
    P.B((S_ * 0.5, S_ * 0.25, S_ * 0.5), (0, y + S_ * 1.55, 0.3), d, tag='Float')
    for k in range(8):
        a = k / 8 * math.tau
        for j in range(3):
            r = S_ * 0.45 + j * 0.55
            P.B((0.6 - j * 0.1,) * 2 + (0.9,), (math.cos(a) * r, y - j * 0.55, math.sin(a) * r), m if j < 2 else acc,
                rot=(0, -math.degrees(a) + 90, 0), tag='Tail')
    for k in range(5):
        P.B((0.35, 0.35, 0.1), (-S_ * 0.3 + k * S_ * 0.15, y + S_ * 0.25, -S_ / 2 - 0.05), l, tag='Float')
    hc, hs = (0, y + S_ * 0.6, 0), (S_, S_ * 0.9, S_)
    face(P, hc, hs, style, None, eyes_glow=eyes_glow)
    for p in P.parts:
        if p['t'] == '':
            p['t'] = 'Float'
    P.a.update(hc=hc, hs=hs, body=(0, y + 1, 0), bs=(S_, S_, S_), top=y + S_ * 1.7, tail=(0, y, 2), lh=y)


# ---------------------------------------------------------------- extras
def X(P, kind, *a):
    m, d, l, acc = P.pal
    hc, hs, top = P.a['hc'], P.a['hs'], P.a['top']
    bx, by, bz = P.a['body']
    bs = P.a['bs']
    if kind == 'horns_bull':
        P.mirror((1.6, 0.5, 0.5), (hs[0] / 2 + 0.6, hc[1] + hs[1] * 0.38, hc[2] + 0.2), (240, 232, 214), tag='Head')
        P.mirror((0.45, 1.2, 0.45), (hs[0] / 2 + 1.3, hc[1] + hs[1] * 0.38 + 0.6, hc[2] + 0.1), (240, 232, 214), rot=(0, 0, -18), tag='Head')
    elif kind == 'horns_ram':
        for k in range(4):
            a = k * 80
            P.mirror((0.6, 0.6, 0.6), (hs[0] / 2 + 0.3 + math.sin(math.radians(a)) * 0.6, hc[1] + 0.3 + math.cos(math.radians(a)) * 0.6, hc[2] + 0.3),
                     a and acc or acc, tag='Head')
    elif kind == 'horn_uni':
        for k in range(4):
            P.B((0.5 - k * 0.1,) * 2 + (0.5,), (0, hc[1] + hs[1] / 2 + 0.3 + k * 0.45, hc[2] - 0.2 - k * 0.12), acc, glow=bool(a and a[0]), tag='Head')
    elif kind == 'horns_devil':
        P.mirror((0.45, 1.3, 0.45), (hs[0] * 0.32, hc[1] + hs[1] / 2 + 0.55, hc[2] + 0.1), a[0] if a else INK, rot=(-15, 0, -20), tag='Head')
    elif kind == 'antlers':
        for side in (-1, 1):
            base = (side * hs[0] * 0.3, hc[1] + hs[1] / 2, hc[2] + 0.2)
            P.B((0.3, 1.4, 0.3), (base[0] + side * 0.2, base[1] + 0.7, base[2]), acc, rot=(0, 0, -side * 20), tag='Head', glow=bool(a and a[0]))
            P.B((0.25, 1.0, 0.25), (base[0] + side * 0.9, base[1] + 1.4, base[2]), acc, rot=(0, 0, -side * 55), tag='Head', glow=bool(a and a[0]))
            P.B((0.25, 0.9, 0.25), (base[0] + side * 0.35, base[1] + 1.7, base[2] - 0.2), acc, rot=(20, 0, side * 10), tag='Head', glow=bool(a and a[0]))
    elif kind == 'mane':
        col = a[0] if a else d
        P.B((hs[0] * 1.45, hs[1] * 1.4, hs[2] * 0.5), (0, hc[1], hc[2] + hs[2] * 0.42), col, tag='Head')
        P.B((hs[0] * 1.2, hs[1] * 0.4, hs[2] * 0.8), (0, hc[1] + hs[1] * 0.6, hc[2] + hs[2] * 0.2), col, tag='Head')
        if len(a) > 1 and a[1]:                                                   # glowing rim around the mane
            P.B((hs[0] * 1.55, 0.25, 0.3), (0, hc[1] + hs[1] * 0.72, hc[2] + hs[2] * 0.15), sh(col, 1.3), tag='Head', glow=True)
            P.mirror((0.25, hs[1] * 1.3, 0.3), (hs[0] * 0.76, hc[1], hc[2] + hs[2] * 0.15), sh(col, 1.3), tag='Head', glow=True)
    elif kind == 'stripes':
        col = a[0] if a else INK
        for k in range(4):
            P.B((bs[0] + 0.12, bs[1] * 0.55, 0.32), (0, by + bs[1] * 0.2, -bs[2] * 0.35 + k * bs[2] * 0.25), col)
    elif kind == 'spikes':
        col = a[0] if a else acc
        n = a[1] if len(a) > 1 else 5
        g = len(a) > 2 and a[2]
        for k in range(n):
            z = -bs[2] * 0.4 + k * (bs[2] * 0.8 / max(1, n - 1))
            P.B((0.4, 0.9 - (k % 2) * 0.3, 0.4), (0, top + 0.35, z), col, rot=(-20, 0, 0), glow=g)
    elif kind == 'crystals':
        col = a[0] if a else (140, 230, 255)
        rng = random.Random(len(P.parts))
        for k in range(a[1] if len(a) > 1 else 5):
            x = rng.uniform(-bs[0] * 0.3, bs[0] * 0.3)
            z = rng.uniform(-bs[2] * 0.35, bs[2] * 0.35)
            h = rng.uniform(0.8, 1.8)
            P.B((0.5, h, 0.5), (x, top + h / 2 - 0.1, z), col, rot=(rng.uniform(-20, 20), 45, rng.uniform(-20, 20)), glow=True)
    elif kind == 'flames':
        rng = random.Random(len(P.parts) + 3)
        for k in range(a[0] if a else 6):
            x = rng.uniform(-bs[0] * 0.3, bs[0] * 0.3)
            z = rng.uniform(-bs[2] * 0.4, bs[2] * 0.3)
            h = rng.uniform(0.8, 1.6)
            P.B((0.6, h, 0.6), (x, top + h / 2, z), (255, 110, 20), glow=True, tag='Glow')
            P.B((0.35, h * 0.6, 0.35), (x, top + h * 0.75, z - 0.1), (255, 220, 60), glow=True, tag='Glow')
    elif kind == 'halo':
        col = a[0] if a else (255, 236, 120)
        y = hc[1] + hs[1] / 2 + 1.0
        for k in range(8):
            ang = k / 8 * math.tau
            P.B((0.7, 0.18, 0.3), (hc[0] + math.cos(ang) * 1.0, y, hc[2] + math.sin(ang) * 1.0), col, rot=(0, -math.degrees(ang), 0), glow=True, tag='Spin')
    elif kind == 'crown':
        col = a[0] if a else (255, 200, 40)
        y = hc[1] + hs[1] / 2 + 0.2
        P.B((hs[0] * 0.6, 0.35, hs[2] * 0.6), (0, y, hc[2]), col, tag='Head')
        for k in range(4):
            ang = k / 4 * math.tau + 0.78
            P.B((0.25, 0.5, 0.25), (math.cos(ang) * hs[0] * 0.25, y + 0.4, hc[2] + math.sin(ang) * hs[2] * 0.25), col, tag='Head')
        P.B((0.3, 0.3, 0.12), (0, y + 0.05, hc[2] - hs[2] * 0.3 - 0.05), (255, 60, 90), glow=True, tag='Head')
    elif kind == 'armor':
        col = a[0] if a else (180, 186, 200)
        P.B((bs[0] + 0.25, bs[1] * 0.5, bs[2] * 0.7), (0, by + bs[1] * 0.3, -0.1), col)
        P.B((hs[0] + 0.2, hs[1] * 0.3, hs[2] * 0.7), (0, hc[1] + hs[1] * 0.4, hc[2] + 0.1), col, tag='Head')
    elif kind == 'cap':
        col = a[0] if a else (230, 60, 60)
        y = hc[1] + hs[1] / 2
        P.B((hs[0] * 1.5, 0.6, hs[2] * 1.4), (0, y + 0.35, hc[2]), col, tag='Head')
        P.B((hs[0] * 1.1, 0.5, hs[2] * 1.0), (0, y + 0.85, hc[2]), col, tag='Head')
        for dx, dz in ((-0.5, -0.3), (0.4, 0.2), (0.0, 0.5)):
            P.B((0.3, 0.12, 0.3), (dx, y + 1.12, hc[2] + dz), WHITE, tag='Head')
    elif kind == 'tusks':
        P.mirror((0.3, 0.9, 0.3), (hs[0] * 0.3, hc[1] - hs[1] * 0.25, hc[2] - hs[2] / 2 - 0.35), (255, 246, 222), rot=(-30, 0, 10), tag='Head')
    elif kind == 'wings_bat':
        col = a[0] if a else d
        for k in range(3):
            P.mirror((1.4 + k * 0.4, 0.2, 2.0 - k * 0.4), (bs[0] / 2 + 0.7 + k * 0.6, top + 0.3 + k * 0.45, 0.2 + k * 0.2), col if k != 1 else sh(col, 1.3),
                     rot=(0, 0, -25 - k * 10), tag='WingL')
    elif kind == 'wings_feather' or kind == 'wings_angel' or kind == 'wings_fire' or kind == 'wings_crystal':
        cols = {'wings_feather': (m, l, acc), 'wings_angel': (WHITE, (255, 246, 210), (255, 230, 140)),
                'wings_fire': ((255, 110, 20), (255, 200, 40), (255, 80, 10)), 'wings_crystal': ((150, 230, 255), (210, 250, 255), (120, 180, 255))}[kind]
        glow = kind in ('wings_fire', 'wings_crystal', 'wings_angel')
        for k in range(4):
            P.mirror((1.2 + k * 0.6, 0.25, 2.0 - k * 0.3), (bs[0] / 2 + 0.5 + k * 0.45, top + 0.2 + k * 0.4, 0.1 + k * 0.1),
                     cols[k % 3], rot=(0, 0, -22 - k * 8), tag='WingL', glow=glow and k % 2 == 1)
    elif kind == 'dragon_wings':
        col = a[0] if a else d
        mem = a[1] if len(a) > 1 else acc
        g = len(a) > 2 and a[2]
        P.mirror((3.2, 0.35, 0.35), (bs[0] / 2 + 1.5, top + 1.0, 0.0), col, rot=(0, 0, -30), tag='WingL')
        for k in range(3):
            P.mirror((0.3, 2.6 - k * 0.5, 0.3), (bs[0] / 2 + 1.0 + k * 1.0, top + 1.0 + k * 0.6 - 1.0, 0.3), col, rot=(0, 0, 10), tag='WingL')
            P.mirror((0.9, 2.2 - k * 0.5, 0.15), (bs[0] / 2 + 1.5 + k * 1.0, top + 0.6 + k * 0.6 - 0.8, 0.35), mem, tag='WingL', glow=g)
    elif kind == 'tail_flame':
        t = P.a['tail']
        P.B((0.8, 1.2, 0.8), (t[0], t[1] + 0.4, t[2]), (255, 110, 20), glow=True, tag='Tail')
        P.B((0.45, 0.8, 0.45), (t[0], t[1] + 0.9, t[2] - 0.1), (255, 220, 60), glow=True, tag='Tail')
    elif kind == 'tail_orb':
        t = P.a['tail']
        P.B((0.9, 0.9, 0.9), (t[0], t[1] + 0.3, t[2]), a[0] if a else acc, glow=True, tag='Tail')
    elif kind == 'bolts':
        col = a[0] if a else (255, 236, 60)
        for sx in (-1, 1):
            P.B((0.3, 1.2, 0.3), (sx * bs[0] * 0.3, top + 0.5, -0.3), col, rot=(0, 0, 25), glow=True, tag='Glow')
            P.B((0.3, 1.0, 0.3), (sx * bs[0] * 0.3 + 0.35, top + 1.3, -0.3), col, rot=(0, 0, -25), glow=True, tag='Glow')
    elif kind == 'gem':
        P.B((0.6, 0.6, 0.2), (0, hc[1] + hs[1] * 0.32, hc[2] - hs[2] / 2 - 0.1), a[0] if a else (255, 60, 120), glow=True, tag='Head')
    elif kind == 'orbit':
        col = a[0] if a else acc
        for k in range(3):
            ang = k / 3 * math.tau
            P.B((0.6, 0.6, 0.6), (math.cos(ang) * 2.6, top + 0.6, math.sin(ang) * 2.6), col, glow=True, tag='Spin')
    elif kind == 'glass':
        for p in P.parts:
            if p['m'] != 'Neon' and p['c'] not in (list(WHITE), list(INK)):
                p['a'] = a[0] if a else 0.35
    elif kind == 'material':
        for p in P.parts:
            if p['m'] == 'Plastic' and p['c'] not in (list(WHITE), list(INK)):
                p['m'] = a[0]
    elif kind == 'mush':
        rng = random.Random(7)
        for k in range(a[0] if a else 3):
            x, z = rng.uniform(-bs[0] * 0.3, bs[0] * 0.3), rng.uniform(-bs[2] * 0.3, bs[2] * 0.3)
            P.B((0.3, 0.7, 0.3), (x, top + 0.3, z), (240, 230, 210))
            P.B((0.9, 0.35, 0.9), (x, top + 0.75, z), (230, 70, 70) if k % 2 else (190, 110, 255), glow=(k % 2 == 0))
    elif kind == 'sprinkles':
        rng = random.Random(11)
        cols = [(255, 90, 140), (90, 200, 255), (255, 230, 70), (120, 240, 120)]
        for k in range(10):
            P.B((0.3, 0.12, 0.12), (rng.uniform(-bs[0] * 0.4, bs[0] * 0.4), top + 0.04, rng.uniform(-bs[2] * 0.4, bs[2] * 0.4)), cols[k % 4],
                rot=(0, rng.uniform(0, 180), 0))
    elif kind == 'bolts_eyes':
        pass


# ---------------------------------------------------------------- the 100 pets
C = {
    'grass': (110, 200, 80), 'brown': (170, 110, 70), 'pink': (255, 150, 180), 'orange': (250, 150, 50), 'red': (230, 60, 50),
    'black': (48, 42, 52), 'white': (238, 240, 248), 'gold': (255, 200, 40), 'blue': (70, 150, 240), 'cyan': (80, 220, 240),
    'purple': (150, 100, 240), 'green': (90, 200, 90), 'lime': (160, 240, 70), 'grey': (150, 156, 170), 'navy': (50, 60, 120),
    'teal': (40, 170, 160), 'yellow': (255, 220, 60), 'cream': (250, 236, 200), 'magenta': (230, 70, 200), 'mint': (150, 240, 200),
}


def pal(main, dark=None, light=None, acc=None):
    return (main, dark or sh(main, 0.7), light or tuple(min(255, int(v * 0.55 + 115)) for v in main), acc or sh(main, 1.2))


PETS = []


def pet(zone, rarity, name, fx, build):
    PETS.append({'zone': zone, 'rarity': rarity, 'name': name, 'fx': fx, 'build': build})


Z = ['Sunny Meadow', 'Mushroom Grove', 'Candy Canyon', 'Toy Town', 'Crystal Coast', 'Spooky Hollow', 'Thunder Peaks', 'Neon City',
     'Cloud Kingdom', 'Golden Nest']

# zone 1 - Sunny Meadow
pet(1, 'Common', 'Pixel Pup', [], lambda P: quad(P, ears='floppy', tail='thin', style='happy', mouth='smile'))
pet(1, 'Common', 'Mud Piglet', [], lambda P: (quad(P, W=3.2, H=2.6, L=3.8, lh=1.1, ears='pointy', tail='stub', snout=(0.5, 0.4, 0.3), style='happy'),))
pet(1, 'Uncommon', 'Hay Ram', [], lambda P: (quad(P, ears='none', tail='stub', mouth='smile'), X(P, 'horns_ram')))
pet(1, 'Uncommon', 'Ember Fox', ['ember'], lambda P: (quad(P, W=2.6, H=2.2, ears='pointy', tail='fluffy', snout=(0.5, 0.36, 0.5)), X(P, 'tail_flame')))
pet(1, 'Rare', 'Thorn Boar', ['sparkle'], lambda P: (quad(P, W=3.4, H=2.8, L=4.6, lh=1.3, ears='pointy', tail='thin', snout=(0.55, 0.42, 0.4)),
                                                    X(P, 'tusks'), X(P, 'spikes', (90, 60, 40), 6)))
pet(1, 'Rare', 'Saber Tiger', ['sparkle'], lambda P: (quad(P, W=2.9, H=2.5, L=5.0, lh=2.0, ears='round', tail='long', mouth='sabers', snout=(0.6, 0.4, 0.42)),
                                                     X(P, 'stripes')))
pet(1, 'Epic', 'Flaming Bull', ['fire', 'light'], lambda P: (quad(P, W=3.6, H=3.0, L=5.0, lh=2.0, hk=0.9, ears='none', tail='thin', snout=(0.7, 0.45, 0.4)),
                                                            X(P, 'horns_bull'), X(P, 'flames', 7), X(P, 'tail_flame')))
pet(1, 'Legendary', 'Golden Axolotl', ['sparkle', 'aura', 'light'], lambda P: (P.a.__setitem__('glowgills', True), reptile(P, W=2.6, H=1.6, L=4.4, kind='axolotl'),
                                                                               X(P, 'crown')))
pet(1, 'Mythic', 'Solar Lion', ['fire', 'aura', 'light', 'rays'], lambda P: (quad(P, W=3.4, H=3.0, L=5.2, lh=2.2, ears='round', tail='long', mouth='fangs'),
                                                                            X(P, 'mane', (255, 140, 30), True), X(P, 'tail_flame'), X(P, 'halo')))
pet(1, 'Secret', 'Meadow Colossus', ['aura', 'leaves', 'light', 'rays'], lambda P: (biped(P, W=4.4, H=4.0, D=3.0, lh=1.6, arm=4.0, hk=0.7, snout=None, mouth='teeth'),
                                                                                    X(P, 'crystals', (150, 255, 120), 6), X(P, 'mush', 4), X(P, 'orbit', (180, 255, 120))))
# zone 2 - Mushroom Grove
pet(2, 'Common', 'Spore Frog', [], lambda P: reptile(P, W=2.8, H=1.4, L=3.0, kind='frog'))
pet(2, 'Common', 'Truffle Mole', [], lambda P: quad(P, W=3.0, H=2.0, L=3.6, lh=0.8, ears='none', tail='stub', snout=(0.45, 0.35, 0.45), style='sleepy', mouth='teeth'))
pet(2, 'Uncommon', 'Glow Snail', ['glow'], lambda P: blob(P, 2.6, kind='shell'))
pet(2, 'Uncommon', 'Moss Turtle', [], lambda P: (reptile(P, W=2.8, H=1.2, L=3.6, kind='turtle'), X(P, 'mush', 2)))
pet(2, 'Rare', 'Fungi Bear', ['spores'], lambda P: (biped(P, W=3.0, H=2.8, ears='round'), X(P, 'cap')))
pet(2, 'Rare', 'Shroom Stag', ['spores'], lambda P: (quad(P, W=2.6, H=2.4, L=4.6, lh=2.4, ears='pointy', tail='stub', neck=True, snout=(0.5, 0.4, 0.4)),
                                                    X(P, 'antlers', True), X(P, 'mush', 3)))
pet(2, 'Epic', 'Toxic Crocodile', ['toxic', 'light'], lambda P: (reptile(P, W=3.0, H=1.6, L=6.0, kind='croc', eyes_glow=True), X(P, 'spikes', (160, 255, 60), 6, True)))
pet(2, 'Legendary', 'Mycelium Wyrm', ['spores', 'aura', 'light'], lambda P: (serpent(P, segs=9, R=1.5, eyes_glow=True), X(P, 'cap', (190, 110, 255))))
pet(2, 'Mythic', 'Spore Titan', ['spores', 'aura', 'light', 'rays'], lambda P: (biped(P, W=4.4, H=3.8, D=3.0, lh=1.4, arm=3.8, hk=0.72, snout=(0.5, 0.35, 0.3)),
                                                                               X(P, 'mush', 5), X(P, 'cap', (190, 110, 255)), X(P, 'gem', (190, 110, 255))))
pet(2, 'Secret', 'Fungal Hydra', ['spores', 'aura', 'light', 'rays', 'toxic'], lambda P: (serpent(P, segs=8, R=1.6, heads=3, eyes_glow=True),
                                                                                         X(P, 'crystals', (190, 110, 255), 6)))
# zone 3 - Candy Canyon
pet(3, 'Common', 'Gummy Bear', [], lambda P: (biped(P, W=2.6, H=2.6, lh=1.0, arm=1.8, hk=0.9, snout=(0.45, 0.35, 0.3), mouth='smile', style='happy'), X(P, 'glass', 0.3)))
pet(3, 'Common', 'Lolli Lamb', [], lambda P: (quad(P, W=3.2, H=2.6, L=3.8, lh=1.3, ears='floppy', tail='stub', style='happy', mouth='smile'), X(P, 'sprinkles')))
pet(3, 'Uncommon', 'Cotton Candy Cat', ['sparkle'], lambda P: (quad(P, W=2.6, H=2.2, L=4.0, ears='pointy', tail='fluffy', style='happy', mouth='smile'),))
pet(3, 'Uncommon', 'Choco Bunny', [], lambda P: (quad(P, W=2.6, H=2.4, L=3.4, lh=1.0, ears='long', tail='fluffy', style='happy', snout=(0.4, 0.3, 0.3)),))
pet(3, 'Rare', 'Candy Cane Croc', ['sparkle'], lambda P: (reptile(P, kind='croc'), X(P, 'stripes', WHITE)))
pet(3, 'Rare', 'Jelly Octopus', ['bubbles'], lambda P: (octopus(P, 3.0), X(P, 'glass', 0.3)))
pet(3, 'Epic', 'Sugar Unicorn', ['rainbow', 'sparkle', 'light'], lambda P: (quad(P, W=2.6, H=2.6, L=4.6, lh=2.4, ears='pointy', tail='fluffy', neck=True, snout=(0.5, 0.4, 0.42), style='happy'),
                                                                          X(P, 'horn_uni', True), X(P, 'mane', (255, 120, 220))))
pet(3, 'Legendary', 'Caramel Griffin', ['sparkle', 'aura', 'light'], lambda P: (quad(P, W=3.0, H=2.6, L=4.8, lh=2.0, ears='none', tail='long', snout=None, mouth='beak'),
                                                                                X(P, 'wings_feather'), X(P, 'mane', (255, 236, 200))))
pet(3, 'Mythic', 'Gumball Golem', ['sparkle', 'aura', 'light', 'rays'], lambda P: (biped(P, W=4.6, H=4.0, D=3.2, lh=1.6, arm=4.0, hk=0.75, snout=None, mouth='teeth'),
                                                                                  X(P, 'sprinkles'), X(P, 'glass', 0.25), X(P, 'orbit', (255, 90, 140))))
pet(3, 'Secret', 'Sugar Queen Dragon', ['rainbow', 'aura', 'light', 'rays', 'sparkle'], lambda P: (quad(P, W=3.4, H=3.0, L=5.4, lh=2.0, ears='none', tail='long', neck=True, mouth='fangs'),
                                                                                                   X(P, 'dragon_wings', (255, 120, 200), (255, 200, 240), True), X(P, 'crown'), X(P, 'spikes', (255, 236, 120), 6, True)))
# zone 4 - Toy Town
pet(4, 'Common', 'Brick Dog', [], lambda P: quad(P, ears='floppy', tail='thin', mouth='smile'))
pet(4, 'Common', 'Windup Mouse', [], lambda P: (quad(P, W=2.4, H=1.8, L=3.2, lh=0.8, ears='round', tail='long', snout=(0.4, 0.3, 0.4), style='happy'),
                                                 X(P, 'orbit', (255, 200, 60))))
pet(4, 'Uncommon', 'Robo Pup', ['electric'], lambda P: (quad(P, ears='pointy', tail='thin', eyes_glow=True), X(P, 'material', 'Metal'), X(P, 'gem', (80, 220, 255))))
pet(4, 'Uncommon', 'Block Penguin', [], lambda P: bird(P, W=2.4, H=2.8, wing='feather', crest=False, tailf=False, style='happy'))
pet(4, 'Rare', 'Tin Soldier Bear', ['sparkle'], lambda P: (biped(P, W=3.0, H=2.8, ears='round', mouth='smile'), X(P, 'armor', (220, 40, 50)), X(P, 'crown', (40, 60, 200))))
pet(4, 'Rare', 'Mecha Rhino', ['electric'], lambda P: (quad(P, W=3.6, H=2.8, L=5.0, lh=1.6, ears='round', tail='stub', snout=(0.6, 0.45, 0.42), eyes_glow=True),
                                                      X(P, 'horn_uni', True), X(P, 'material', 'Metal'), X(P, 'armor', (90, 96, 110))))
pet(4, 'Epic', 'Laser Scorpion', ['electric', 'light'], lambda P: spider(P, kind='scorpion', eyes_glow=True))
pet(4, 'Legendary', 'Clockwork Raptor', ['electric', 'aura', 'light'], lambda P: (dino(P, eyes_glow=True), X(P, 'material', 'Metal'), X(P, 'spikes', (255, 200, 40), 5, True)))
pet(4, 'Mythic', 'Titan Mech Gorilla', ['electric', 'aura', 'light', 'rays'], lambda P: (biped(P, W=4.8, H=4.0, D=3.2, lh=1.4, arm=4.2, hk=0.7, snout=(0.55, 0.4, 0.3), eyes_glow=True),
                                                                                        X(P, 'material', 'DiamondPlate'), X(P, 'bolts', (80, 220, 255)), X(P, 'gem', (80, 220, 255))))
pet(4, 'Secret', 'Glitch Cube', ['glitch', 'aura', 'light', 'rays'], lambda P: (blob(P, 3.6, style='angry', mouth='teeth', eyes_glow=True), X(P, 'orbit', (0, 255, 120)),
                                                                                X(P, 'crystals', (255, 0, 200), 5)))
# zone 5 - Crystal Coast
pet(5, 'Common', 'Pixel Shark', [], lambda P: fish(P))
pet(5, 'Common', 'Coral Crab', [], lambda P: spider(P, W=2.8, H=1.4, L=2.0, kind='crab'))
pet(5, 'Uncommon', 'Bubble Seal', ['bubbles'], lambda P: quad(P, W=2.6, H=2.0, L=4.2, lh=0.5, lw=1.0, ears='none', tail='stub', style='happy', mouth='smile', snout=(0.5, 0.4, 0.4)))
pet(5, 'Uncommon', 'Seahorse Knight', ['bubbles'], lambda P: (bird(P, W=2.0, H=3.0, D=2.0, wing='none', crest=True, tailf=False, mouth='smile', legs=False), X(P, 'armor', (230, 200, 80))))
pet(5, 'Rare', 'Hammer Shark', ['bubbles'], lambda P: (fish(P, W=2.4, H=2.4, L=5.4), P.B((4.4, 0.9, 1.2), (0, 2.6, -3.4), P.pal[1], tag='Float')))
pet(5, 'Rare', 'Crystal Manta', ['sparkle', 'bubbles'], lambda P: (fish(P, W=4.4, H=1.2, L=3.6, fin='none', mouth='smile', style='happy'), X(P, 'wings_crystal')))
pet(5, 'Epic', 'Tidal Serpent', ['bubbles', 'light', 'water'], lambda P: (serpent(P, segs=9, R=1.4, eyes_glow=True), X(P, 'crystals', (120, 220, 255), 4)))
pet(5, 'Legendary', 'Crystal Dragon', ['sparkle', 'aura', 'light'], lambda P: (quad(P, W=3.2, H=2.8, L=5.4, lh=2.0, ears='none', tail='long', neck=True, mouth='fangs', eyes_glow=True),
                                                                               X(P, 'dragon_wings', (90, 160, 255), (160, 240, 255), True), X(P, 'crystals', (160, 240, 255), 6),
                                                                               X(P, 'material', 'Glass')))
pet(5, 'Mythic', 'Cosmic Kraken', ['cosmic', 'aura', 'light', 'rays'], lambda P: (octopus(P, 4.4, eyes_glow=True), X(P, 'orbit', (180, 120, 255)), X(P, 'crown', (180, 120, 255))))
pet(5, 'Secret', 'Abyss Leviathan', ['water', 'aura', 'light', 'rays', 'cosmic'], lambda P: (serpent(P, segs=11, R=2.0, eyes_glow=True, mouth='teeth'),
                                                                                              X(P, 'crystals', (60, 255, 220), 8), X(P, 'dragon_wings', (20, 40, 80), (60, 255, 220), True)))
# zone 6 - Spooky Hollow
pet(6, 'Common', 'Bat Pup', [], lambda P: (quad(P, W=2.4, H=2.0, L=3.0, lh=1.0, ears='pointy', tail='stub', mouth='fangs'), X(P, 'wings_bat')))
pet(6, 'Common', 'Pumpkin Cat', [], lambda P: (quad(P, W=2.6, H=2.2, L=3.8, ears='pointy', tail='long', mouth='fangs'),))
pet(6, 'Uncommon', 'Ghost Fox', ['ghost'], lambda P: (quad(P, W=2.6, H=2.2, L=4.0, ears='pointy', tail='fluffy', eyes_glow=True), X(P, 'glass', 0.45)))
pet(6, 'Uncommon', 'Bone Raven', ['ghost'], lambda P: bird(P, wing='feather', eyes_glow=True))
pet(6, 'Rare', 'Zombie Bear', ['toxic'], lambda P: (biped(P, W=3.2, H=3.0, ears='round', mouth='teeth', eyes_glow=True), X(P, 'stripes', (90, 140, 60))))
pet(6, 'Rare', 'Grave Spider', ['ghost'], lambda P: spider(P, eyes_glow=True))
pet(6, 'Epic', 'Wraith Stag', ['ghost', 'light'], lambda P: (quad(P, W=2.6, H=2.4, L=4.6, lh=2.6, ears='pointy', tail='stub', neck=True, eyes_glow=True),
                                                            X(P, 'antlers', True), X(P, 'glass', 0.4)))
pet(6, 'Legendary', 'Phantom Panther', ['ghost', 'aura', 'light'], lambda P: (quad(P, W=2.8, H=2.4, L=5.0, lh=2.0, ears='pointy', tail='long', mouth='fangs', eyes_glow=True),
                                                                              X(P, 'stripes', (160, 80, 255)), X(P, 'tail_orb', (160, 80, 255))))
pet(6, 'Mythic', 'Shadow Titan', ['shadow', 'aura', 'light', 'rays'], lambda P: (biped(P, W=4.8, H=4.2, D=3.2, lh=1.6, arm=4.4, hk=0.7, snout=None, mouth='teeth', eyes_glow=True),
                                                                                X(P, 'horns_devil', (160, 80, 255)), X(P, 'crystals', (160, 80, 255), 6)))
pet(6, 'Secret', 'Void Serpent', ['shadow', 'aura', 'light', 'rays', 'cosmic'], lambda P: (serpent(P, segs=11, R=1.8, eyes_glow=True), X(P, 'halo', (160, 80, 255)),
                                                                                           X(P, 'orbit', (255, 0, 160))))
# zone 7 - Thunder Peaks
pet(7, 'Common', 'Storm Goat', [], lambda P: (quad(P, W=2.6, H=2.4, L=3.8, lh=1.8, ears='pointy', tail='stub'), X(P, 'horns_ram')))
pet(7, 'Common', 'Volt Hamster', ['electric'], lambda P: (blob(P, 2.6, style='happy'), X(P, 'bolts')))
pet(7, 'Uncommon', 'Thunder Owl', ['electric'], lambda P: bird(P, W=2.8, H=2.8, wing='feather', eyes_glow=True))
pet(7, 'Uncommon', 'Static Hedgehog', ['electric'], lambda P: (quad(P, W=2.8, H=2.0, L=3.2, lh=0.7, ears='none', tail='stub', snout=(0.4, 0.35, 0.45)),
                                                               X(P, 'spikes', (255, 236, 60), 7, True)))
pet(7, 'Rare', 'Lightning Lynx', ['electric'], lambda P: (quad(P, W=2.6, H=2.2, L=4.4, lh=2.0, ears='pointy', tail='stub', mouth='fangs', eyes_glow=True), X(P, 'bolts')))
pet(7, 'Rare', 'Rock Rhino', ['dust'], lambda P: (quad(P, W=3.8, H=3.0, L=5.0, lh=1.6, ears='round', tail='stub', snout=(0.6, 0.45, 0.42)), X(P, 'horn_uni'),
                                                 X(P, 'material', 'Slate')))
pet(7, 'Epic', 'Lava Gorilla', ['fire', 'light'], lambda P: (biped(P, W=4.0, H=3.4, D=2.8, lh=1.2, arm=3.6, hk=0.75, eyes_glow=True), X(P, 'flames', 6)))
pet(7, 'Legendary', 'Storm Dragon', ['electric', 'aura', 'light'], lambda P: (quad(P, W=3.2, H=2.8, L=5.4, lh=2.0, ears='none', tail='long', neck=True, mouth='fangs', eyes_glow=True),
                                                                             X(P, 'dragon_wings', (60, 50, 140), (120, 230, 255), True), X(P, 'bolts'), X(P, 'tail_orb', (120, 230, 255))))
pet(7, 'Mythic', 'Thunder Behemoth', ['electric', 'aura', 'light', 'rays'], lambda P: (quad(P, W=4.6, H=3.8, L=6.0, lh=2.6, ears='round', tail='thin', mouth='teeth', eyes_glow=True),
                                                                                      X(P, 'tusks'), X(P, 'horns_bull'), X(P, 'bolts'), X(P, 'spikes', (255, 236, 60), 7, True)))
pet(7, 'Divine', 'Zeus Eagle', ['electric', 'aura', 'light', 'rays', 'divine'], lambda P: (bird(P, W=3.2, H=3.2, D=3.0, wing='angel', eyes_glow=True), X(P, 'halo'),
                                                                                           X(P, 'bolts'), X(P, 'wings_angel')))
# zone 8 - Neon City
pet(8, 'Common', 'Neon Rat', ['glow'], lambda P: (quad(P, W=2.2, H=1.8, L=3.4, lh=0.8, ears='round', tail='long', snout=(0.4, 0.3, 0.45)), X(P, 'stripes', (0, 255, 200))))
pet(8, 'Common', 'Disco Duck', ['glow'], lambda P: (bird(P, wing='feather', crest=False, style='happy'), X(P, 'gem', (255, 0, 200))))
pet(8, 'Uncommon', 'Laser Cat', ['glow'], lambda P: (quad(P, W=2.6, H=2.2, L=4.0, ears='pointy', tail='long', eyes_glow=True), X(P, 'stripes', (255, 0, 200))))
pet(8, 'Uncommon', 'Cyber Bunny', ['glow'], lambda P: (quad(P, W=2.6, H=2.4, L=3.4, lh=1.0, ears='long', tail='fluffy', eyes_glow=True), X(P, 'material', 'Metal')))
pet(8, 'Rare', 'Neon Wolf', ['glow', 'sparkle'], lambda P: (quad(P, W=2.8, H=2.4, L=4.8, lh=2.0, ears='pointy', tail='fluffy', mouth='fangs', eyes_glow=True, snout=(0.55, 0.4, 0.5)),
                                                           X(P, 'stripes', (0, 255, 240)), X(P, 'spikes', (0, 255, 240), 5, True)))
pet(8, 'Rare', 'Synth Shark', ['glow'], lambda P: (fish(P, eyes_glow=True), X(P, 'stripes', (255, 0, 200))))
pet(8, 'Epic', 'Glitch Gecko', ['glitch', 'light'], lambda P: (reptile(P, W=2.4, H=1.2, L=4.4, kind='croc', eyes_glow=True), X(P, 'spikes', (0, 255, 120), 6, True)))
pet(8, 'Legendary', 'Cyber Tiger', ['electric', 'aura', 'light'], lambda P: (quad(P, W=3.0, H=2.6, L=5.2, lh=2.0, ears='round', tail='long', mouth='sabers', eyes_glow=True),
                                                                            X(P, 'stripes', (0, 255, 240)), X(P, 'material', 'Metal'), X(P, 'gem', (0, 255, 240))))
pet(8, 'Mythic', 'Diamond T-Rex', ['sparkle', 'aura', 'light', 'rays'], lambda P: (dino(P, eyes_glow=True), X(P, 'material', 'Glass'), X(P, 'crystals', (160, 240, 255), 6),
                                                                                  X(P, 'spikes', (200, 250, 255), 6, True)))
pet(8, 'Divine', 'Quantum Dragon', ['cosmic', 'glitch', 'aura', 'light', 'rays', 'divine'], lambda P: (quad(P, W=3.6, H=3.0, L=6.0, lh=2.2, ears='none', tail='long', neck=True, mouth='fangs', eyes_glow=True),
                                                                                                      X(P, 'dragon_wings', (20, 20, 40), (255, 0, 200), True), X(P, 'halo', (0, 255, 240)),
                                                                                                      X(P, 'orbit', (255, 0, 200)), X(P, 'spikes', (0, 255, 240), 7, True)))
# zone 9 - Cloud Kingdom
pet(9, 'Common', 'Cloud Sheep', [], lambda P: (quad(P, W=3.2, H=2.6, L=3.8, lh=1.2, ears='floppy', tail='stub', style='sleepy', mouth='smile'),))
pet(9, 'Common', 'Puff Pigeon', [], lambda P: bird(P, wing='feather', crest=False, style='sleepy'))
pet(9, 'Uncommon', 'Wind Fox', ['wind'], lambda P: (quad(P, W=2.6, H=2.2, L=4.0, ears='pointy', tail='fluffy'), X(P, 'wings_feather')))
pet(9, 'Uncommon', 'Feather Cat', ['wind'], lambda P: (quad(P, W=2.6, H=2.2, L=4.0, ears='pointy', tail='long', style='happy'), X(P, 'wings_angel')))
pet(9, 'Rare', 'Sky Whale', ['wind', 'bubbles'], lambda P: fish(P, W=3.2, H=3.0, L=6.0, mouth='smile', fin='none', hover=2.0, style='happy'))
pet(9, 'Rare', 'Pegasus', ['wind', 'sparkle'], lambda P: (quad(P, W=2.6, H=2.6, L=4.6, lh=2.4, ears='pointy', tail='fluffy', neck=True, snout=(0.5, 0.4, 0.42)),
                                                         X(P, 'wings_angel'), X(P, 'mane', (200, 230, 255))))
pet(9, 'Epic', 'Celestial Owl', ['sparkle', 'light', 'cosmic'], lambda P: (bird(P, W=3.0, H=3.0, D=2.6, wing='angel', eyes_glow=True), X(P, 'orbit', (255, 236, 140))))
pet(9, 'Legendary', 'Rainbow Phoenix', ['fire', 'rainbow', 'aura', 'light'], lambda P: (bird(P, W=2.8, H=2.8, wing='flame', eyes_glow=True), X(P, 'wings_fire'), X(P, 'tail_flame'),
                                                                                       X(P, 'flames', 4)))
pet(9, 'Mythic', 'Cloud Titan', ['wind', 'aura', 'light', 'rays'], lambda P: (biped(P, W=4.6, H=4.0, D=3.2, lh=1.6, arm=4.0, hk=0.72, snout=None, mouth='teeth', eyes_glow=True),
                                                                             X(P, 'wings_angel'), X(P, 'crown', (200, 230, 255)), X(P, 'halo')))
pet(9, 'Divine', 'Seraph Lion', ['divine', 'aura', 'light', 'rays', 'sparkle'], lambda P: (quad(P, W=3.4, H=3.0, L=5.4, lh=2.2, ears='round', tail='long', mouth='fangs', eyes_glow=True),
                                                                                           X(P, 'mane', (255, 246, 210), True), X(P, 'wings_angel'), X(P, 'halo'), X(P, 'tail_orb', (255, 236, 140))))
# zone 10 - Golden Nest
pet(10, 'Common', 'Gold Chick', [], lambda P: bird(P, W=2.4, H=2.4, wing='feather', style='happy'))
pet(10, 'Common', 'Gilded Pig', ['sparkle'], lambda P: (quad(P, W=3.2, H=2.6, L=3.8, lh=1.1, ears='pointy', tail='stub', snout=(0.5, 0.4, 0.3), style='happy'), X(P, 'gem')))
pet(10, 'Uncommon', 'Treasure Turtle', ['sparkle'], lambda P: (reptile(P, W=2.8, H=1.2, L=3.6, kind='turtle'), X(P, 'crystals', (255, 60, 120), 3)))
pet(10, 'Uncommon', 'Golden Monkey', ['sparkle'], lambda P: (biped(P, W=2.6, H=2.4, lh=1.0, arm=2.6, hk=0.95, ears='round', mouth='smile', style='happy', snout=(0.5, 0.4, 0.3)),))
pet(10, 'Rare', 'Royal Peacock', ['sparkle'], lambda P: (bird(P, wing='feather', tailf=False), [P.B((0.3, 2.8, 0.3), (math.sin(a) * 1.3, 3.4 + math.cos(a) * 0.4, 2.0), (40, 200, 160) if k % 2 else (60, 120, 255),
                                                                                                   rot=(20, 0, math.degrees(a)), glow=(k % 3 == 0), tag='Tail') for k, a in enumerate([(-0.9 + 1.8 * i / 6) for i in range(7)])], X(P, 'crown')))
pet(10, 'Rare', 'Gem Rhino', ['sparkle'], lambda P: (quad(P, W=3.6, H=2.8, L=5.0, lh=1.6, ears='round', tail='stub', snout=(0.6, 0.45, 0.42)), X(P, 'horn_uni', True),
                                                    X(P, 'crystals', (255, 60, 120), 4)))
pet(10, 'Epic', 'Midas Bull', ['sparkle', 'light'], lambda P: (quad(P, W=3.6, H=3.0, L=5.0, lh=2.0, hk=0.9, ears='none', tail='thin', snout=(0.7, 0.45, 0.4)),
                                                              X(P, 'horns_bull'), X(P, 'material', 'Foil'), X(P, 'gem')))
pet(10, 'Legendary', 'Golden Dragon', ['sparkle', 'aura', 'light', 'fire'], lambda P: (quad(P, W=3.4, H=3.0, L=5.6, lh=2.2, ears='none', tail='long', neck=True, mouth='fangs', eyes_glow=True),
                                                                                      X(P, 'dragon_wings', (200, 140, 20), (255, 230, 120), True), X(P, 'crown'), X(P, 'material', 'Foil')))
pet(10, 'Mythic', 'Treasure Titan', ['sparkle', 'aura', 'light', 'rays'], lambda P: (biped(P, W=4.8, H=4.0, D=3.2, lh=1.6, arm=4.2, hk=0.72, snout=None, mouth='teeth', eyes_glow=True),
                                                                                    X(P, 'armor', (255, 210, 60)), X(P, 'crown'), X(P, 'crystals', (255, 60, 120), 5), X(P, 'material', 'Foil')))
pet(10, 'Divine', 'Celestial Godbeast', ['divine', 'cosmic', 'aura', 'light', 'rays', 'sparkle'], lambda P: (quad(P, W=3.8, H=3.2, L=6.0, lh=2.4, ears='round', tail='long', neck=True, mouth='fangs', eyes_glow=True),
                                                                                                            X(P, 'mane', (255, 240, 180), True), X(P, 'dragon_wings', (255, 236, 160), (255, 255, 230), True),
                                                                                                            X(P, 'halo'), X(P, 'orbit', (255, 236, 140)), X(P, 'horn_uni', True)))

PALETTES = {
    'Pixel Pup': pal(C['brown'], acc=(255, 150, 160)), 'Mud Piglet': pal(C['pink'], acc=(240, 110, 140)), 'Hay Ram': pal(C['cream'], (200, 180, 140), WHITE, (240, 190, 90)),
    'Ember Fox': pal(C['orange'], acc=(255, 240, 220)), 'Thorn Boar': pal((150, 100, 70)), 'Saber Tiger': pal(C['orange'], light=(255, 240, 220)),
    'Flaming Bull': pal((60, 50, 58), light=(110, 100, 110), acc=(255, 120, 30)), 'Golden Axolotl': pal(C['gold'], acc=(255, 120, 60)),
    'Solar Lion': pal((255, 190, 60), acc=(255, 120, 30)), 'Meadow Colossus': pal((110, 150, 90), (70, 100, 60), (200, 220, 160), (150, 255, 120)),
    'Spore Frog': pal((120, 200, 90)), 'Truffle Mole': pal((110, 80, 70)), 'Glow Snail': pal((200, 160, 230), acc=(150, 255, 200)),
    'Moss Turtle': pal((120, 190, 90), (70, 120, 60), (210, 230, 170), (90, 160, 70)), 'Fungi Bear': pal((170, 120, 80)),
    'Shroom Stag': pal((190, 140, 100), acc=(190, 110, 255)), 'Toxic Crocodile': pal((70, 150, 60), acc=(160, 255, 60)),
    'Mycelium Wyrm': pal((150, 110, 200), acc=(200, 255, 120)), 'Spore Titan': pal((100, 80, 120), acc=(190, 110, 255)),
    'Fungal Hydra': pal((90, 70, 130), acc=(190, 255, 120)), 'Gummy Bear': pal((255, 90, 120)), 'Lolli Lamb': pal((255, 220, 240), acc=(255, 120, 200)),
    'Cotton Candy Cat': pal((255, 180, 230), acc=(150, 220, 255)), 'Choco Bunny': pal((130, 80, 50), light=(240, 200, 160)),
    'Candy Cane Croc': pal((230, 40, 60)), 'Jelly Octopus': pal((120, 220, 255), acc=(255, 120, 220)), 'Sugar Unicorn': pal(WHITE, (220, 200, 240), (255, 230, 250), (255, 120, 220)),
    'Caramel Griffin': pal((210, 140, 60), acc=(255, 236, 200)), 'Gumball Golem': pal((80, 200, 255), acc=(255, 90, 140)),
    'Sugar Queen Dragon': pal((255, 140, 210), acc=(255, 236, 120)), 'Brick Dog': pal((220, 60, 50), acc=(255, 220, 60)),
    'Windup Mouse': pal((170, 176, 190), acc=(255, 160, 180)), 'Robo Pup': pal((150, 160, 180), acc=(80, 220, 255)), 'Block Penguin': pal((40, 44, 60), light=WHITE, acc=(255, 176, 40)),
    'Tin Soldier Bear': pal((150, 100, 60)), 'Mecha Rhino': pal((110, 120, 140), acc=(255, 120, 30)), 'Laser Scorpion': pal((60, 60, 80), acc=(255, 40, 60)),
    'Clockwork Raptor': pal((200, 150, 70), acc=(80, 220, 255)), 'Titan Mech Gorilla': pal((90, 96, 120), acc=(80, 220, 255)),
    'Glitch Cube': pal((30, 30, 40), acc=(0, 255, 120)), 'Pixel Shark': pal(C['blue']), 'Coral Crab': pal((255, 110, 80)),
    'Bubble Seal': pal((150, 170, 200)), 'Seahorse Knight': pal((255, 170, 60), acc=(255, 120, 60)), 'Hammer Shark': pal((110, 130, 160)),
    'Crystal Manta': pal((60, 90, 170), acc=(160, 240, 255)), 'Tidal Serpent': pal((40, 120, 200), acc=(120, 240, 255)),
    'Crystal Dragon': pal((120, 190, 255), acc=(200, 250, 255)), 'Cosmic Kraken': pal((70, 40, 140), acc=(200, 120, 255)),
    'Abyss Leviathan': pal((20, 40, 70), acc=(60, 255, 220)), 'Bat Pup': pal((80, 60, 100)), 'Pumpkin Cat': pal((255, 130, 30), (60, 40, 30), acc=(80, 200, 60)),
    'Ghost Fox': pal((220, 230, 255), acc=(150, 255, 230)), 'Bone Raven': pal((40, 36, 50), light=(230, 230, 230), acc=(160, 80, 255)),
    'Zombie Bear': pal((120, 160, 100)), 'Grave Spider': pal((50, 46, 60), acc=(160, 80, 255)), 'Wraith Stag': pal((140, 150, 190), acc=(150, 255, 230)),
    'Phantom Panther': pal((40, 36, 60), acc=(160, 80, 255)), 'Shadow Titan': pal((40, 36, 56), acc=(160, 80, 255)),
    'Void Serpent': pal((25, 20, 40), acc=(255, 0, 160)), 'Storm Goat': pal((200, 205, 220), acc=(255, 220, 60)),
    'Volt Hamster': pal((255, 210, 80)), 'Thunder Owl': pal((90, 100, 140), acc=(255, 236, 60)), 'Static Hedgehog': pal((140, 110, 90)),
    'Lightning Lynx': pal((210, 200, 140), acc=(255, 236, 60)), 'Rock Rhino': pal((130, 125, 120)), 'Lava Gorilla': pal((50, 40, 40), light=(255, 100, 30), acc=(255, 160, 40)),
    'Storm Dragon': pal((110, 90, 220), acc=(120, 230, 255)), 'Thunder Behemoth': pal((70, 70, 90), acc=(255, 236, 60)),
    'Zeus Eagle': pal((250, 250, 255), (200, 200, 220), WHITE, (255, 230, 80)), 'Neon Rat': pal((60, 60, 80), acc=(0, 255, 200)),
    'Disco Duck': pal((255, 90, 200), acc=(80, 220, 255)), 'Laser Cat': pal((40, 40, 60), acc=(255, 0, 200)), 'Cyber Bunny': pal((200, 210, 230), acc=(0, 255, 240)),
    'Neon Wolf': pal((40, 44, 70), acc=(0, 255, 240)), 'Synth Shark': pal((70, 40, 120), acc=(255, 0, 200)), 'Glitch Gecko': pal((40, 220, 120), acc=(255, 0, 200)),
    'Cyber Tiger': pal((60, 64, 90), acc=(0, 255, 240)), 'Diamond T-Rex': pal((170, 230, 255), acc=(255, 255, 255)),
    'Quantum Dragon': pal((30, 26, 60), acc=(0, 255, 240)), 'Cloud Sheep': pal(WHITE, (210, 220, 240), WHITE, (180, 210, 255)),
    'Puff Pigeon': pal((190, 200, 230), acc=(150, 240, 200)), 'Wind Fox': pal((150, 220, 255), acc=WHITE), 'Feather Cat': pal((255, 236, 210), acc=(150, 200, 255)),
    'Sky Whale': pal((110, 170, 255), light=WHITE), 'Pegasus': pal(WHITE, (210, 220, 240), WHITE, (150, 200, 255)),
    'Celestial Owl': pal((70, 60, 150), acc=(255, 236, 140)), 'Rainbow Phoenix': pal((255, 90, 60), acc=(255, 220, 60)),
    'Cloud Titan': pal((220, 230, 250), acc=(150, 200, 255)), 'Seraph Lion': pal((255, 240, 210), acc=(255, 220, 120)),
    'Gold Chick': pal(C['yellow'], acc=(255, 150, 40)), 'Gilded Pig': pal((255, 210, 120), acc=(255, 170, 60)),
    'Treasure Turtle': pal((90, 160, 120), (200, 150, 40), (220, 240, 200), (255, 210, 60)), 'Golden Monkey': pal((230, 170, 60)),
    'Royal Peacock': pal((60, 120, 255), acc=(40, 200, 160)), 'Gem Rhino': pal((150, 140, 160), acc=(255, 60, 120)),
    'Midas Bull': pal((255, 200, 40), acc=(255, 150, 20)), 'Golden Dragon': pal((255, 200, 40), acc=(255, 120, 30)),
    'Treasure Titan': pal((200, 150, 40), acc=(255, 60, 120)), 'Celestial Godbeast': pal((255, 246, 220), acc=(255, 210, 90)),
}


def main():
    assert len(PETS) == 100, len(PETS)
    names = [p['name'] for p in PETS]
    assert len(set(names)) == 100
    out = []
    for i, d in enumerate(PETS):
        P = Pet(PALETTES[d['name']])
        d['build'](P)
        k = SCALE[d['rarity']]
        parts = []
        for q in P.parts:
            q = dict(q)
            q['s'] = [round(v * k, 3) for v in q['s']]
            q['p'] = [round(v * k, 3) for v in q['p']]
            parts.append(q)
        out.append({'id': i + 1, 'zone': d['zone'], 'rarity': d['rarity'], 'name': d['name'], 'fx': d['fx'], 'parts': parts})
    (HERE / 'pets.json').write_text(json.dumps(out), encoding='utf-8')
    # Lua data module: compact arrays per part
    lines = ['-- generated by pets\\gen_pets.py: 100 blocky pets. part = {sx,sy,sz, px,py,pz, rx,ry,rz, r,g,b, material, tag, transparency}',
             'return {']
    for p in out:
        ps = ','.join('{%s,%s,%s,%s,%s,%s,%s,%s,%s,%d,%d,%d,"%s","%s",%s}' % (*q['s'], *q['p'], *q['r'], *q['c'], q['m'], q['t'], q['a']) for q in p['parts'])
        lines.append('\t{id=%d,zone=%d,rarity="%s",name="%s",fx={%s},parts={%s}},' % (p['id'], p['zone'], p['rarity'], p['name'],
                                                                                    ','.join('"%s"' % f for f in p['fx']), ps))
    lines.append('}')
    (HERE.parent / 'game' / 'PetData.lua').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    counts = {}
    for p in out:
        counts[p['rarity']] = counts.get(p['rarity'], 0) + 1
    print('pets', len(out), counts, 'parts min/avg/max', min(len(p['parts']) for p in out), sum(len(p['parts']) for p in out) // 100,
          max(len(p['parts']) for p in out))


if __name__ == '__main__':
    main()
