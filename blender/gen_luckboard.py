r"""Raining Eggs: the TOP LUCK leaderboard as a pretty wall panel (stone wall + gold frame + purple clover crest).

  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P gen_luckboard.py   -> out\RainingEggsLuckBoard.fbx + out\luckboard.png

Meshes (Roblox axes, origin on the ground at the middle of the wall, FRONT = -Z):
  Map_LuckBoard (wall, pillars, frame, crest), Map_LuckBoardNeon (lanterns, gems, star glow).
  The game screen (part 'Leaderboard', 20 x 13) sits in the frame: centre (0, 10.6, -1.15), front face -Z.
"""
import bpy, math, sys, pathlib, random

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from blib import *          # noqa: F401,F403
import blib

OUT = HERE / 'out'
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MAT = reset()
R = random.Random(7)
PUR, PUR2, PUR3 = (150, 90, 245), (110, 60, 200), (200, 160, 255)
STONE = [(236, 230, 214), (226, 218, 200), (244, 238, 224), (214, 206, 188)]
MORTAR = (150, 140, 128)
CLOVER, CLOVER2 = (80, 200, 90), (130, 235, 120)
SW, SH, SY = 20.0, 13.0, 10.6          # screen size + centre height


def clover(b, x, y, z, r, c=CLOVER, c2=CLOVER2, face=-1):
    """four heart-ish leaves lying in the wall plane (facing -Z)"""
    for k in range(4):
        a = math.radians(45 + 90 * k)
        for side in (-1, 1):
            aa = a + side * 0.42
            rball(b, (x + math.cos(aa) * r * 0.62, y + math.sin(aa) * r * 0.62, z), r * 0.5, c, (1, 1, 0.35), 12, 8)
    rball(b, (x, y, z + face * 0.1), r * 0.28, shade(c, 0.85), (1, 1, 0.4), 10, 6)
    rbox(b, (x + r * 0.25, y - r * 1.0, z), (r * 0.18, r * 0.9, r * 0.18), shade(c, 0.75), 0.04, rz=-20)


def star(b, x, y, z, s, c):
    for rz in (0, 36, 72, 108, 144):
        rbox(b, (x, y, z), (s * 2, s * 0.5, s * 0.4), c, 0.04, rz=rz)


def board(key, PUR, PUR2, PUR3, crest, bush):
    b, n = B(), B()
    # plinth + wall core (mortar colour) + stone blocks sticking out a little
    rbox(b, (0, 0.5, 0), (31, 1.0, 3.4), (190, 182, 166), 0.15)
    rbox(b, (0, 10.5, 0), (27.6, 19.0, 1.8), MORTAR, 0.05)
    rows = 19
    for i in range(rows):
        y = 1.0 + 0.5 + i * 1.0
        off = 1.0 if i % 2 else 0.0
        x = -13.8 + off
        while x < 13.8:
            w = min(2.0, 13.8 - x)
            if w > 0.3:
                cx = x + w / 2
                inside = abs(cx) < SW / 2 + 0.6 and abs(y - SY) < SH / 2 + 0.6     # hidden behind the screen anyway
                if not inside:
                    for zz in (-0.92, 0.92):                                         # front + back faces
                        rbox(b, (cx, y, zz), (w - 0.12, 0.88, 0.2), R.choice(STONE), 0.05)
            x += w
    # stone pillars at the ends with gold caps + glowing lanterns
    for sx in (-1, 1):
        x = sx * 14.6
        rbox(b, (x, 11, 0), (3.2, 20, 3.2), (238, 232, 218), 0.2)
        for yy in (2.0, 8.0, 14.0):
            rbox(b, (x, yy, 0), (3.5, 0.6, 3.5), (210, 200, 182), 0.1)
        rbox(b, (x, 21.3, 0), (3.8, 0.8, 3.8), GOLD, 0.15)
        rbox(b, (x, 22.5, 0), (1.8, 1.8, 1.8), (90, 70, 50), 0.12)                 # lantern box
        rbox(n, (x, 22.5, 0), (1.4, 1.3, 1.95), (255, 226, 140), 0.08)
        rbox(n, (x, 22.5, 0), (1.95, 1.3, 1.4), (255, 226, 140), 0.08)
        rbox(b, (x, 23.6, 0), (2.2, 0.4, 2.2), (90, 70, 50), 0.1)
        rcyl(b, (x, 24.1, 0), 0.5, 0.6, GOLD, segs=8, r2=0.1)
    # top of the wall: purple tiles
    rbox(b, (0, 20.2, 0), (28.4, 0.6, 2.6), PUR2, 0.12)
    # gold frame round the screen (front), purple inner border
    fz = -1.35
    rbox(b, (0, SY, -1.0), (SW + 1.4, SH + 1.4, 0.4), PUR2, 0.1)
    for sy in (-1, 1):
        rbox(b, (0, SY + sy * (SH / 2 + 0.75), fz), (SW + 2.6, 1.0, 0.9), GOLD, 0.22)
    for sx in (-1, 1):
        rbox(b, (sx * (SW / 2 + 0.75), SY, fz), (1.0, SH + 2.6, 0.9), GOLD, 0.22)
        for sy in (-1, 1):
            rico(n, (sx * (SW / 2 + 0.75), SY + sy * (SH / 2 + 0.75), fz - 0.45), 0.55, (130, 230, 255) if sx * sy > 0 else (255, 120, 220), (1, 1, 0.6), 1)
    for k in range(9):                                                               # gold studs on the frame
        x = -SW / 2 + 1.2 + k * (SW - 2.4) / 8
        rcyl(b, (x, SY - SH / 2 - 0.75, fz - 0.5), 0.22, 0.2, (255, 236, 150), axis='Z', segs=8)
    # crest on top: purple rounded banner + big clover + stars
    rbox(b, (0, 22.0, -0.4), (15, 3.4, 1.2), PUR, 0.5)
    rbox(b, (0, 22.0, -0.75), (14.2, 2.6, 0.6), PUR3, 0.4)
    rbox(b, (0, 20.4, -0.6), (16, 0.5, 1.4), GOLD, 0.15)
    crest(b, n)
    for sx in (-1, 1):
        star(b, sx * 9.2, 23.2, -0.6, 0.7, GOLD)
        star(n, sx * 5.8, 25.0, -0.9, 0.45, (255, 246, 170))
    # clover bushes and little flowers at the foot of the wall
    for k in range(14):
        x = -12.5 + k * (25 / 13) + R.uniform(-0.4, 0.4)
        rball(b, (x, 1.4, -1.9), R.uniform(0.7, 1.0), R.choice((CLOVER, (70, 180, 80), (100, 210, 90))), (1.2, 0.8, 0.9), 10, 6)
        if k % 3 == 1:
            bush(b, x)
    nm = 'Map_LuckBoard2' if key == 'Luck' else f'Map_{key}Board'                  # v2 = clover without the green dots
    return [b.finish(nm, (0, 0, 0), MAT), n.finish(nm.replace('Board', 'BoardNeon'), (0, 0, 0), MAT)]


def egg_big(b, x, y, z, r, c, spot):
    rball(b, (x, y, z), r, c, (1, 1.3, 0.8), 16, 12)
    for (dx, dy, rr) in ((-0.45, 0.35, 0.22), (0.4, -0.1, 0.18), (-0.1, -0.55, 0.2), (0.35, 0.65, 0.14)):
        rball(b, (x + dx * r, y + dy * r * 1.3, z - 0.72 * r), rr * r, spot, (1, 1, 0.4), 10, 6)
    rball(b, (x - 0.35 * r, y + 0.55 * r, z - 0.6 * r), 0.16 * r, (255, 255, 255), (0.8, 1.3, 0.4), 8, 5)


def crest_luck(b, n):
    clover(b, 0, 25.6, -0.9, 2.9)


def crest_catch(b, n):
    # a woven basket with a big spotted egg popping out + two small eggs
    for i in range(3):
        rbox(b, (0, 23.9 + i * 0.75, -1.0), (5.6 + i * 0.5, 0.7, 2.4), (214, 150, 80) if i % 2 == 0 else (176, 112, 52), 0.2)
    rbox(b, (0, 26.2, -1.0), (7.4, 0.5, 2.8), (150, 92, 40), 0.2)
    egg_big(b, 0, 28.0, -1.0, 1.7, (255, 255, 255), (80, 170, 255))
    egg_big(b, -2.5, 27.0, -1.2, 0.95, (255, 214, 60), (255, 120, 150))
    egg_big(b, 2.5, 27.0, -1.2, 0.95, (255, 140, 190), (255, 255, 255))


def bush_luck(b, x):
    clover(b, x, 2.6, -2.35, 0.55)


def bush_catch(b, x):
    c, s = R.choice((((255, 255, 255), (80, 170, 255)), ((255, 214, 60), (255, 120, 150)), ((150, 230, 120), (255, 255, 255))))
    egg_big(b, x, 2.4, -2.3, 0.5, c, s)


luck = board('Luck', (150, 90, 245), (110, 60, 200), (200, 160, 255), crest_luck, bush_luck)
catch = board('Catch', (50, 170, 240), (30, 110, 200), (150, 225, 255), crest_catch, bush_catch)
objs = luck + catch
blib.save_meta(HERE.parent / 'game')
print('triangles:', {o.name: len(o.data.polygons) for o in objs})
if 'nofbx' not in ARGS:
    print('wrote', blib.export(luck, OUT / 'RainingEggsLuckBoard.fbx'))
    print('wrote', blib.export(catch, OUT / 'RainingEggsCatchBoard.fbx'))

# preview: the board + a dark screen like the game's
sc, cam = scene_setup(sky=(0.62, 0.8, 1.0, 1), ground=(0.35, 0.7, 0.3, 1))
sc.eevee.taa_render_samples = 64
glow = glow_material(3)
for o in objs:
    if 'Neon' in o.name:
        o.data.materials.clear()
        o.data.materials.append(glow)
for o in catch:
    o.location.x = 36
scr = B()
for X, col in ((0, (60, 30, 130)), (36, (20, 60, 120))):
    rbox(scr, (X, SY, -1.15), (SW, SH, 0.3), col, 0)
    for i in range(5):
        rbox(scr, (X - 1.5, SY + 4.0 - i * 2.1, -1.32), (14, 1.2, 0.05), (255, 222, 60) if i == 0 else (235, 230, 255), 0)
blib.META.pop('Screen', None)
scr.finish('Screen', (0, 0, 0), MAT)
blib.META.pop('Screen', None)
if 'norender' not in ARGS:
    shot(sc, cam, OUT / 'boards.png', (18, 16, -70), (18, 13, 0), (2000, 1000), 30)
