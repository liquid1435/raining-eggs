r"""Raining Eggs, zone 4 (Toy Town) as Blender meshes.

  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P gen_toy.py   -> out\RainingEggsToy.fbx + out\toy_*.png

Meshes (Roblox axes, origin on the ground at the model centre, front = -Z):
  Map_ToyBlock1..6 (10 cube with letters), Map_Dice (7 cube), Map_StackRings, Map_Crayon1..6 (16 tall),
  Map_Ball1..6 (1 wide, centre origin), Map_TrainTrack, Map_TrainEngine, Map_TrainCar1..4 (along Z),
  Map_Teddy, Map_DuckTub, Map_DuckTubWater
"""
import bpy, bmesh, math, sys, pathlib, random

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from blib import *          # noqa: F401,F403
import blib

OUT = HERE / 'out'
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MAT = reset()
R = random.Random(31)
TOY = [(240, 70, 70), (255, 204, 40), (70, 190, 90), (70, 130, 250), (255, 140, 40), (190, 100, 250)]
TB, TB2 = (176, 120, 70), (226, 180, 130)

# 5 x 5 pixel letters for the toy blocks
LET = {'A': ['01110', '10001', '11111', '10001', '10001'], 'B': ['11110', '10001', '11110', '10001', '11110'],
       'C': ['01111', '10000', '10000', '10000', '01111'], '1': ['00100', '01100', '00100', '00100', '01110'],
       '2': ['11110', '00001', '01110', '10000', '11111'], '3': ['11110', '00001', '00110', '00001', '11110']}


def letter(b, ch, centre, face, size, c):
    """raised pixel letter on a cube face: face = '-Z', '+Z', '-X', '+X', '+Y'"""
    x0, y0, z0 = centre
    px = size / 5
    for row, line in enumerate(LET[ch]):
        for col, on in enumerate(line):
            if on == '1':
                u, v = (col - 2) * px, (2 - row) * px
                p = {'-Z': (x0 - u, y0 + v, z0), '+Z': (x0 + u, y0 + v, z0), '-X': (x0, y0 + v, z0 + u),
                     '+X': (x0, y0 + v, z0 - u), '+Y': (x0 + u, y0, z0 + v)}[face]
                sz = {'-Z': (px, px, 0.3), '+Z': (px, px, 0.3), '-X': (0.3, px, px), '+X': (0.3, px, px), '+Y': (px, 0.3, px)}[face]
                rbox(b, p, sz, c, 0)


def toy_block(k):
    b = B()
    c = TOY[k]
    rbox(b, (0, 5, 0), (10, 10, 10), c, 0.6)
    lt = mix(c, WHITE, 0.55)
    for face, pos in (('-Z', (0, 5, -5.1)), ('+Z', (0, 5, 5.1)), ('-X', (-5.1, 5, 0)), ('+X', (5.1, 5, 0))):
        x, y, z = pos
        fr = (8.4, 8.4, 0.25) if face in ('-Z', '+Z') else (0.25, 8.4, 8.4)
        rbox(b, pos, fr, lt, 0.1)
        inner = (7.4, 7.4, 0.3) if face in ('-Z', '+Z') else (0.3, 7.4, 7.4)
        rbox(b, pos, inner, c, 0.05)
        ch = 'ABC123'[(k + 'ZX'.index(face[1]) * 2 + (face[0] == '+')) % 6]
        off = {'-Z': (0, 0, -0.2), '+Z': (0, 0, 0.2), '-X': (-0.2, 0, 0), '+X': (0.2, 0, 0)}[face]
        letter(b, ch, (x + off[0], y + off[1], z + off[2]), face, 5, WHITE)
    rbox(b, (0, 10.1, 0), (7.4, 0.25, 7.4), lt, 0.05)
    letter(b, 'ABC123'[k], (0, 10.3, 0), '+Y', 4.5, WHITE)
    return b.finish(f'Map_ToyBlock{k + 1}', (0, 0, 0), MAT)


def dice():
    b = B()
    rbox(b, (0, 3.5, 0), (7, 7, 7), WHITE, 1.0)
    pip = lambda p: rball(b, p, 0.6, INK, (1, 1, 1), 8, 5)
    o = 1.8
    faces = {'+Y': [(0, 0)], '-Z': [(-o, o), (o, -o)], '+X': [(-o, o), (0, 0), (o, -o)], '-X': [(-o, o), (o, o), (-o, -o), (o, -o)],
             '+Z': [(-o, o), (o, o), (0, 0), (-o, -o), (o, -o)]}
    for f, pts in faces.items():
        for u, v in pts:
            pip({'+Y': (u, 7.05, v), '-Z': (u, 3.5 + v, -3.55), '+Z': (u, 3.5 + v, 3.55), '-X': (-3.55, 3.5 + v, u), '+X': (3.55, 3.5 + v, u)}[f])
    return b.finish('Map_Dice', (0, 0, 0), MAT)


def stack_rings():
    b = B()
    rcyl(b, (0, 0.6, 0), 6.2, 1.2, (240, 90, 80), segs=20)
    rcyl(b, (0, 8, 0), 0.8, 15, (250, 240, 214), segs=10)
    for k in range(5):
        r = 5.6 - k * 0.9
        rball(b, (0, 2.4 + k * 2.6, 0), r, TOY[k % 6], (1, 0.26, 1), 20, 8)
    rball(b, (0, 16.4, 0), 1.9, TOY[5], segs=14, rings=8)
    rball(b, (-0.6, 17.1, -1.2), 0.5, WHITE, (1, 0.6, 0.6), 6, 4)
    return b.finish('Map_StackRings', (0, 0, 0), MAT)


def crayon(k):
    b = B()
    c = TOY[k]
    rcyl(b, (0, 6.5, 0), 1.6, 13, c, segs=6)
    rcyl(b, (0, 6.5, 0), 1.66, 9, mix(c, WHITE, 0.35), segs=6)              # paper wrapper
    for y in (2.6, 10.4):
        rcyl(b, (0, y, 0), 1.7, 0.5, shade(c, 0.7), segs=6)
    for y in (5, 6.5, 8):
        rcyl(b, (0, y, 0), 1.69, 0.18, WHITE, segs=6)
    rcyl(b, (0, 14.2, 0), 1.6, 2.4, shade(c, 1.05), segs=6, r2=0.35)       # tip
    return b.finish(f'Map_Crayon{k + 1}', (0, 0, 0), MAT)


def ball(k):
    b = B()
    c = TOY[k]
    rball(b, (0, 0, 0), 0.5, c, segs=18, rings=10)
    rball(b, (0, 0, 0), 0.505, WHITE, (1, 0.22, 1), 18, 4)
    rball(b, (-0.18, 0.24, -0.3), 0.1, WHITE, (1, 0.6, 0.6), 6, 4)
    return b.finish(f'Map_Ball{k + 1}', (0, 0, 0), MAT)


def track():
    b = B()
    rcyl(b, (0, 0.15, 0), 37, 0.3, (120, 84, 56), segs=48)
    rcyl(b, (0, 0.2, 0), 29, 0.32, (130, 200, 255), segs=40)
    for k in range(48):                                                       # sleepers
        a = k * math.tau / 48
        rbox(b, (33 * math.cos(a), 0.45, 33 * math.sin(a)), (1.2, 0.35, 9), (160, 112, 70), 0.06, yaw=-math.degrees(a) + 90)
    for rr in (29.6, 36.4):                                                   # rails
        for k in range(48):
            a0, a1 = k * math.tau / 48, (k + 1) * math.tau / 48
            rbeam(b, (rr * math.cos(a0), 0.85, rr * math.sin(a0)), (rr * math.cos(a1), 0.85, rr * math.sin(a1)), 0.45, (190, 190, 205), 0.05)
    return b.finish('Map_TrainTrack', (0, 0, 0), MAT)


def wheels(b, c):
    for sx in (-1, 1):
        for sz in (-4, 4):
            rcyl(b, (sx * 4.3, 1.9, sz), 1.7, 1, INK, axis='X', segs=14)
            rcyl(b, (sx * 4.85, 1.9, sz), 0.8, 0.2, c, axis='X', segs=10)
    rbox(b, (0, 2.2, 0), (7, 1.0, 12), (60, 60, 70), 0.1)


def engine():
    b = B()
    c = TOY[0]
    wheels(b, GOLD)
    rbox(b, (0, 3.3, 0), (8, 1.2, 13.4), INK, 0.15)
    rcyl(b, (0, 6.4, -2), 3.2, 9, c, axis='Z', segs=16)                      # boiler
    for z in (-5.5, -2, 1.5):
        rcyl(b, (0, 6.4, z), 3.35, 0.5, GOLD, axis='Z', segs=16)
    rcyl(b, (0, 6.4, -6.6), 2.2, 0.3, (60, 60, 70), axis='Z', segs=14)
    rball(b, (0, 7.4, -6.9), 0.7, (255, 230, 140), segs=8, rings=5)           # lamp
    rcyl(b, (0, 11, -4.2), 0.9, 3.2, INK, segs=10, r2=1.3)                    # chimney
    rcyl(b, (0, 12.8, -4.2), 1.6, 0.6, INK, segs=10)
    rbox(b, (0, 8, 4.2), (7.6, 9, 5), shade(c, 0.85), 0.25)                   # cab
    rbox(b, (0, 12.9, 4.2), (8.6, 0.8, 6), INK, 0.2)
    for sx in (-1, 1):
        rbox(b, (sx * 3.85, 9.4, 4.2), (0.2, 2.6, 2.8), (180, 220, 255), 0.05)
    rbox(b, (0, 9.4, 1.65), (5, 2.4, 0.2), (180, 220, 255), 0.05)
    for k in range(4):                                                        # cow catcher
        rbeam(b, (-2.6 + k * 1.75, 3.4, -6.7), (-1.3 + k * 0.85, 1.0, -8.2), 0.4, GOLD, 0.04)
    for k in range(3):                                                        # puffs of steam
        rball(b, (0.4 * k, 14.4 + k * 1.7, -4.4 + k * 0.8), 1.0 + k * 0.4, WHITE, segs=10, rings=6)
    return b.finish('Map_TrainEngine', (0, 0, 0), MAT)


def car(k):
    b = B()
    c = TOY[k % 6]
    wheels(b, WHITE)
    rbox(b, (0, 4.6, 0), (8, 4.4, 12.6), c, 0.3)
    rbox(b, (0, 6.9, 0), (8.4, 0.6, 13), shade(c, 0.75), 0.15)
    for sx in (-1, 1):
        for z in (-3.6, 0, 3.6):
            rcyl(b, (sx * 4.05, 4.7, z), 1.0, 0.2, mix(c, WHITE, 0.5), axis='X', segs=12)
    load = [(0, 8.6, -3, 3.2, TOY[(k + 2) % 6]), (0, 8.6, 3, 3.2, TOY[(k + 4) % 6])]
    for x, y, z, s, lc in load:                                               # cargo: two toy cubes
        rbox(b, (x, y, z), (s, s, s), lc, 0.35, yaw=20)
    rbox(b, (0, 3.3, -6.9), (1, 0.6, 1.4), INK, 0.05)                        # coupling
    return b.finish(f'Map_TrainCar{k}', (0, 0, 0), MAT)


def teddy():
    b = B()
    rball(b, (0, 14, 0), 15, TB, (1, 1, 0.92), 20, 12)                        # body
    rball(b, (0, 12, -11.5), 8.5, TB2, (1, 1.1, 0.35), 16, 8)                 # belly
    rball(b, (0, 34, 0), 10.5, TB, segs=20, rings=12)                         # head
    rball(b, (0, 31, -8.6), 4.6, TB2, (1, 0.8, 0.8), 14, 8)                   # snout
    rball(b, (0, 32.4, -12.2), 1.5, INK, (1.2, 0.8, 0.8), 10, 6)
    rbeam(b, (0, 31.0, -12.4), (0, 29.4, -12.2), 0.3, INK, 0.02)
    rbeam(b, (0, 29.4, -12.2), (-1.4, 28.8, -11.8), 0.3, INK, 0.02)
    rbeam(b, (0, 29.4, -12.2), (1.4, 28.8, -11.8), 0.3, INK, 0.02)
    for sx in (-1, 1):
        rball(b, (sx * 4.2, 36.6, -8.6), 1.6, INK, (1, 1.15, 0.8), 10, 6)
        rball(b, (sx * 4.6, 37.3, -9.8), 0.5, WHITE, segs=6, rings=4)
        rball(b, (sx * 8.4, 42.4, 0), 4.2, TB, (1, 1, 0.7), 14, 8)            # ears
        rball(b, (sx * 8.4, 42.4, -2.2), 2.6, TB2, (1, 1, 0.4), 12, 6)
        rball(b, (sx * 5.8, 32.6, -9.4), 1.3, (255, 150, 160), (1, 0.6, 0.4), 8, 5)
        rball(b, (sx * 15.5, 19, -4), 5.2, TB, (1, 1.5, 1), 14, 8)            # arms
        rball(b, (sx * 9.5, 4.5, -11), 6, TB, (1, 0.8, 1.3), 14, 8)          # legs
        rball(b, (sx * 9.5, 4.6, -18.4), 3.6, TB2, (1, 1, 0.35), 12, 6)      # foot pads
        for j in range(3):
            pass
    rball(b, (0, 24.6, -9.6), 2.0, (230, 50, 70), segs=10, rings=6)           # bow tie
    for sx in (-1, 1):
        rball(b, (sx * 3.2, 24.6, -9.4), 2.6, (230, 50, 70), (1.2, 1, 0.6), 10, 6)
    for k in range(9):                                                        # stitches on the belly
        rbox(b, (0, 6 + k * 1.4, -14.4 + abs(k - 4) * 0.25), (0.9, 0.25, 0.3), shade(TB2, 0.7), 0.03)
    return b.finish('Map_Teddy', (0, 0, 0), MAT)


def duck_tub():
    b, w = B(), B()
    rbox(b, (0, 3, 0), (34, 5, 24), WHITE, 1.4)
    rbox(b, (0, 5.6, 0), (35, 0.8, 25), mix(WHITE, (190, 220, 255), 0.4), 0.4)
    for sx in (-1, 1):
        for sz in (-1, 1):
            rball(b, (sx * 15, 0.6, sz * 10), 1.4, GOLD, (1, 0.9, 1), 10, 6)     # feet
    rcyl(b, (15.5, 9, 0), 0.6, 6, (200, 200, 210), segs=8)                       # tap
    rbeam(b, (15.5, 12, 0), (13, 12.6, 0), 0.9, (200, 200, 210), 0.1)
    rbox(w, (0, 5.0, 0), (31, 0.6, 21), (90, 190, 250), 0.2)
    Y = (255, 220, 50)
    rball(b, (0, 9, 0), 6, Y, (1.1, 0.8, 1.3), 18, 10)
    rball(b, (0, 9.6, 6.6), 2.6, Y, (1, 1, 1), 10, 6)                           # tail
    rball(b, (0, 16, -3), 4.2, Y, segs=16, rings=10)
    rball(b, (0, 15.2, -7.6), 2, (255, 140, 40), (1.2, 0.5, 1.2), 12, 6)
    for sx in (-1, 1):
        rball(b, (sx * 1.8, 17.4, -6.6), 0.7, INK, segs=8, rings=5)
        rball(b, (sx * 1.9, 17.7, -7.1), 0.22, WHITE, segs=6, rings=4)
        rball(b, (sx * 5.8, 10, 0.5), 2.8, shade(Y, 0.93), (0.5, 0.8, 1.4), 10, 6)   # wings
    for k in range(16):                                                           # bubbles
        rball(b, (R.uniform(-14, 14), 5.6 + R.uniform(0, 1.5), R.uniform(-9, 9)), R.uniform(0.6, 1.6), (240, 250, 255), segs=10, rings=6)
    return [b.finish('Map_DuckTub', (0, 0, 0), MAT), w.finish('Map_DuckTubWater', (0, 0, 0), MAT)]


objs = [toy_block(k) for k in range(6)] + [dice(), stack_rings()] + [crayon(k) for k in range(6)] + [ball(k) for k in range(6)] + \
       [track(), engine()] + [car(k) for k in range(1, 5)] + [teddy()] + duck_tub()
save_meta(HERE.parent / 'game')
print('triangles:', {o.name: len(o.data.polygons) for o in objs})
if 'nofbx' not in ARGS:
    print('wrote', blib.export(objs, OUT / 'RainingEggsToy.fbx'))

# ---------------------------------------------------------------- preview scene
sc, cam = scene_setup(sky=(0.7, 0.85, 1.0, 1), ground=(0.24, 0.55, 1.0, 1))
for o in objs:
    o.hide_render = True
by = {o.name: o for o in objs}
road = B()
rbox(road, (0, 0.05, 40), (18, 0.1, 240), (255, 250, 236), 0)
road.finish('Road', (0, 0, 0), MAT)
blib.META.pop('Road', None)


def put(name, pos, yaw=0, s=1.0, sv=None):
    o = place(by[name], name + '_p', pos, yaw, s)
    if sv:
        o.scale = (sv[0], sv[2], sv[1])
    return o


put('Map_Teddy', (-52, 0, 70), 20)
put('Map_DuckTub', (-40, 0, 14), -10)
put('Map_DuckTubWater', (-40, 0, 14), -10)
tx, tz = 60, 70
put('Map_TrainTrack', (tx, 0, tz))
for k in range(5):
    a = math.radians(200 + k * 24)
    put('Map_TrainEngine' if k == 0 else f'Map_TrainCar{k}', (tx + 33 * math.cos(a), 0, tz + 33 * math.sin(a)), -math.degrees(a) - 180)
y = 0
for k, s in enumerate((12, 10, 8)):
    put(f'Map_ToyBlock{k + 1}', (26, y, 6), k * 15, s / 10)
    y += s
put('Map_ToyBlock4', (-20, 0, 40), 30, 1)
put('Map_ToyBlock5', (-20, 10, 40), 10, 0.8)
put('Map_Dice', (16, 0, 34), 20, 1.2)
put('Map_Dice', (-16, 0, -6), 60, 1)
put('Map_StackRings', (34, 0, 30))
for k, (x, z) in enumerate(((-26, 0), (40, 12), (-12, 96), (16, 90), (-70, 40), (80, 20))):
    put(f'Map_Crayon{k + 1}', (x, 0, z), k * 40, sv=(1, 1 + 0.08 * k, 1))
for k in range(14):
    d = R.uniform(3, 7)
    put(f'Map_Ball{k % 6 + 1}', (R.choice((-1, 1)) * R.uniform(12, 70), d / 2, R.uniform(-20, 100)), R.uniform(0, 360), d)
if 'norender' not in ARGS:
    shot(sc, cam, OUT / 'toy_scene.png', (6, 44, -64), (0, 8, 46), (1800, 1000), 26)
    shot(sc, cam, OUT / 'toy_teddy.png', (-20, 30, 20), (-52, 22, 70), (1400, 1000), 32)
