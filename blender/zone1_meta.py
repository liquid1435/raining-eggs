r"""Zone 1 (Sunny Meadow) pets, smooth professional versions (metaballs) + pixelated copies.
  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P zone1_meta.py -- [index ...]
"""
import bpy, math, sys, pathlib, hashlib
from mathutils import Vector
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lowpoly_lib as LL
from metapet import MB, pixelate, rgb, WHITE, BLACK

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'out' / 'zone1m'
OUT.mkdir(parents=True, exist_ok=True)
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def legs4(m, col, front_y, back_y, x, top_z, r=0.2, foot=None, foot_col=None, splay=0.0):
    for y in (front_y, back_y):
        m.sym(m.cap, (x, y, top_z), (x + splay, y + 0.02, r * 0.9), r, col)
        if foot:
            m.sym(m.ell, (x + splay, y - 0.04, r * 0.5), r * 1.0, (1.0, 1.25, 0.6), foot_col or col)


def bunny():
    m = MB('Meadow Bunny')
    W_, PK = rgb(250, 250, 252), rgb(255, 160, 190)
    m.ell((0, 0.25, 0.85), 0.8, (0.85, 1.05, 0.85), W_)                        # body
    m.sym(m.ball, (0.42, 0.55, 0.62), 0.5, W_)                                 # haunches
    m.sym(m.ell, (0.42, 0.25, 0.14), 0.36, (0.9, 1.6, 0.5), W_)                # big back feet
    m.sym(m.cap, (0.28, -0.35, 0.75), (0.3, -0.45, 0.15), 0.17, W_)            # front legs
    m.ball((0, -0.65, 1.55), 0.62, W_)                                         # head
    m.sym(m.ball, (0.3, -0.95, 1.35), 0.3, W_)                                 # cheeks
    m.sym(m.cap, (0.2, -0.55, 2.0), (0.32, -0.4, 2.95), 0.17, W_)              # ears
    m.ball((0, 1.0, 1.0), 0.32, W_)                                            # tail
    for s in (-1, 1):
        m.sphere((s * 0.3, -0.53, 2.45), 0.1, PK, (0.75, 0.25, 3.3), (0, s * 8, s * 7))   # inner ears
        m.eye((s * 0.36, -1.08, 1.68), s, 0.17)
    m.sphere((0, -1.24, 1.42), 0.08, PK, (1.3, 0.8, 0.9))                      # nose
    return m


def sheep():
    m = MB('Fluffy Sheep')
    WOOL, SK, HF = rgb(252, 248, 236), rgb(70, 62, 66), rgb(40, 36, 40)
    for (x, y, z, r) in ((0, -0.5, 1.35, 0.62), (0, 0.3, 1.4, 0.68), (0, 1.0, 1.3, 0.55), (0.45, -0.1, 1.15, 0.5), (-0.45, -0.1, 1.15, 0.5),
                         (0.45, 0.7, 1.15, 0.45), (-0.45, 0.7, 1.15, 0.45), (0, -0.1, 1.8, 0.5), (0, 0.65, 1.75, 0.45), (0.3, 0.25, 1.7, 0.42),
                         (-0.3, 0.25, 1.7, 0.42), (0, -0.85, 1.6, 0.42)):
        m.ball((x, y, z), r, WOOL)
    legs4(m, SK, -0.45, 0.75, 0.35, 1.0, 0.13, foot=True, foot_col=HF)
    m.ell((0, -1.15, 1.55), 0.42, (0.85, 1.25, 1.0), SK, rot=(-20, 0, 0))      # face
    m.sym(m.ell, (0.42, -0.95, 1.65), 0.2, (1.5, 0.6, 0.5), SK, rot=(0, 0, -25))   # ears
    for s in (-1, 1):
        m.eye((s * 0.22, -1.45, 1.75), s, 0.13)
    m.sphere((0, -1.67, 1.42), 0.07, rgb(255, 170, 180))
    return m


def cow():
    m = MB('Spotted Cow')
    WH, BK, PK, HN = rgb(250, 250, 250), rgb(38, 36, 42), rgb(255, 172, 182), rgb(240, 230, 205)
    m.ell((0, 0.15, 1.55), 0.75, (1.0, 1.6, 0.95), WH)                          # body
    legs4(m, WH, -0.75, 0.95, 0.42, 1.2, 0.17, foot=True, foot_col=BK)
    m.ball((0, -1.15, 1.95), 0.5, WH)                                          # head
    m.ell((0, -1.6, 1.7), 0.38, (1.0, 0.8, 0.8), PK)                           # muzzle
    m.sym(m.ell, (0.55, -1.05, 2.15), 0.2, (1.6, 0.5, 0.6), WH, rot=(0, 0, -15))   # ears
    m.ell((0, 0.65, 0.95), 0.25, (1.0, 1.0, 0.8), PK)                           # udder
    m.cap((0, 1.05, 1.9), (0, 1.25, 1.0), 0.06, WH)                             # tail
    for s in (-1, 1):
        m.cone((s * 0.32, -1.1, 2.35), (s * 0.55, -1.15, 2.75), 0.09, HN, bend=(s * 0.15, 0, 0))
        m.eye((s * 0.3, -1.52, 2.1), s, 0.14)
        m.sphere((s * 0.13, -1.93, 1.72), 0.05, rgb(120, 60, 70))
    m.sphere((0, 1.28, 0.95), 0.12, BK, (1, 1, 1.4))                            # tail tuft

    def spots(p, n, c):
        if c != WH or p.z < 0.9 or p.y < -0.9:
            return c
        h = int(hashlib.md5(f'{round(p.x * 1.1)},{round(p.y * 0.9)},{round(p.z * 1.1)}'.encode()).hexdigest()[:2], 16)
        return BK if h < 85 else c
    m.paint_fn = spots
    return m


def bee():
    m = MB('Bumble Bee')
    Y, K, WG = rgb(255, 205, 40), rgb(38, 32, 38), rgb(205, 235, 255)
    z = 1.9
    m.ell((0, 0.45, z), 0.85, (0.95, 1.2, 0.95), Y)                            # abdomen
    m.ball((0, -0.55, z + 0.15), 0.6, K)                                        # thorax
    m.ball((0, -1.15, z + 0.25), 0.5, K)                                        # head
    m.cone((0, 1.45, z - 0.05), (0, 1.85, z - 0.2), 0.1, K, segs=10)
    for k in range(3):
        m.sym(m.cap, (0.35, -0.75 + k * 0.4, z - 0.4), (0.55, -0.85 + k * 0.4, z - 1.25), 0.06, K)
    for s in (-1, 1):
        m.eye((s * 0.3, -1.5, z + 0.38), s, 0.15)
        m.tube([(s * 0.18, -1.3, z + 0.65), (s * 0.35, -1.55, z + 1.15), (s * 0.55, -1.6, z + 1.4)], [0.035, 0.03, 0.03], K, 8)
        m.sphere((s * 0.57, -1.62, z + 1.45), 0.08, K)
        m.sphere((s * 0.85, 0.0, z + 0.85), 0.45, WG, (1.9, 0.9, 0.12), (0, s * -35, s * 20))
        m.sphere((s * 0.65, 0.4, z + 0.55), 0.35, WG, (1.6, 0.8, 0.12), (0, s * -25, s * 10))

    def stripes(p, n, c):
        if c == Y and p.y > 0.0 and int((p.y + 0.15) / 0.38) % 2 == 1:
            return K
        return c
    m.paint_fn = stripes
    m.glow_cols = []
    return m


def fox():
    m = MB('Red Fox')
    OR, WH, BK = rgb(250, 118, 38), rgb(252, 246, 238), rgb(46, 34, 34)
    m.ell((0, 0.2, 1.25), 0.55, (0.9, 1.75, 0.85), OR)                          # body
    m.ell((0, -0.55, 1.15), 0.42, (0.9, 0.8, 1.0), WH)                          # chest
    legs4(m, OR, -0.55, 0.85, 0.27, 1.0, 0.11, foot=True, foot_col=BK)
    m.paint_fn = lambda p, n, c: BK if (c == OR and p.z < 0.45) else c          # black socks
    m.ball((0, -1.0, 1.75), 0.45, OR)                                           # head
    m.ell((0, -1.45, 1.6), 0.25, (0.8, 1.6, 0.7), WH)                           # snout
    m.sym(m.ball, (0.3, -1.15, 1.55), 0.24, WH)                                 # cheeks
    m.sym(m.cap, (0.22, -0.92, 2.05), (0.32, -0.88, 2.5), 0.15, OR)             # ears
    for k, (y, z, r) in enumerate(((1.1, 1.45, 0.25), (1.45, 1.75, 0.35), (1.8, 2.05, 0.38), (2.1, 2.3, 0.3))):
        m.ball((0, y, z), r, WH if k == 3 else OR)                              # bushy tail
    for s in (-1, 1):
        m.eye((s * 0.24, -1.33, 1.85), s, 0.12, iris=rgb(240, 170, 40))
        m.sphere((s * 0.3, -0.98, 2.38), 0.07, BK, (0.9, 0.4, 2.2))
    m.sphere((0, -1.84, 1.62), 0.06, BK)
    return m


def boar():
    m = MB('Wild Boar')
    BR, LT, DK, TK = rgb(116, 80, 60), rgb(160, 118, 92), rgb(66, 44, 34), rgb(250, 242, 222)
    m.ell((0, 0.2, 1.3), 0.8, (0.95, 1.45, 0.95), BR)                           # body
    m.ell((0, -0.45, 1.55), 0.7, (0.9, 0.9, 0.9), BR)                           # shoulders
    legs4(m, DK, -0.55, 0.9, 0.42, 0.9, 0.16, foot=True, foot_col=BLACK)
    m.ball((0, -1.1, 1.35), 0.52, BR)                                           # head
    m.ell((0, -1.6, 1.15), 0.3, (0.9, 1.2, 0.8), rgb(190, 130, 110))            # snout
    m.sym(m.ell, (0.38, -0.95, 1.85), 0.16, (0.8, 0.5, 1.6), DK, rot=(0, 0, 15))   # ears
    for s in (-1, 1):
        m.cone((s * 0.22, -1.85, 1.05), (s * 0.42, -2.0, 1.55), 0.07, TK, bend=(s * 0.1, -0.05, 0))
        m.eye((s * 0.28, -1.45, 1.55), s, 0.11)
        m.sphere((s * 0.1, -1.95, 1.18), 0.05, BLACK)
    for k in range(8):
        y = -0.9 + k * 0.28
        m.cone((0, y, 2.1 - abs(k - 2) * 0.04), (0, y + 0.18, 2.45 - (k % 2) * 0.1), 0.09, DK, segs=8)
    m.cap((0, 1.3, 1.5), (0, 1.5, 1.15), 0.05, DK)
    return m


def owl():
    m = MB('Barn Owl')
    BR, CR, DK = rgb(190, 136, 82), rgb(252, 244, 228), rgb(120, 82, 54)
    m.ell((0, 0, 1.3), 0.9, (0.85, 0.75, 1.1), BR)                             # body
    m.ell((0, -0.35, 1.15), 0.62, (0.8, 0.6, 1.0), CR)                          # belly
    m.ball((0, -0.15, 2.3), 0.75, BR)                                           # head
    m.ell((0, -0.55, 2.3), 0.55, (1.15, 0.6, 1.0), CR)                          # facial disc
    m.sym(m.ell, (0.8, 0.15, 1.35), 0.55, (0.45, 1.0, 1.35), DK, rot=(0, -10, 0))   # wings
    for s in (-1, 1):
        m.cone((s * 0.45, 0.0, 2.9), (s * 0.65, 0.1, 3.35), 0.13, DK)             # ear tufts
        m.eye((s * 0.27, -0.95, 2.42), s, 0.2, iris=rgb(255, 170, 40))
        m.sphere((s * 0.22, -0.55, 0.15), 0.09, rgb(240, 170, 60), (1.3, 1.6, 0.6))   # feet
    m.cone((0, -1.0, 2.25), (0, -1.15, 1.95), 0.09, rgb(240, 190, 90), segs=8)  # beak
    m.ell((0, 0.75, 0.75), 0.4, (0.8, 0.5, 0.3), DK, rot=(30, 0, 0))            # tail
    return m


def bear():
    m = MB('Honey Grizzly')
    BR, LT, DK, HONEY = rgb(122, 80, 50), rgb(206, 166, 124), rgb(64, 42, 30), rgb(255, 186, 30)
    m.ell((0, 0.25, 1.65), 0.95, (1.0, 1.4, 0.95), BR)                          # body
    m.ball((0, -0.45, 2.2), 0.75, BR)                                           # shoulder hump
    legs4(m, BR, -0.75, 1.0, 0.55, 1.3, 0.3, foot=True, foot_col=DK)
    m.ball((0, -1.3, 2.05), 0.62, BR)                                           # head
    m.ell((0, -1.85, 1.85), 0.3, (1.0, 1.1, 0.8), LT)                           # muzzle
    m.sym(m.ball, (0.48, -1.15, 2.6), 0.2, BR)                                  # ears
    for s in (-1, 1):
        m.eye((s * 0.3, -1.78, 2.22), s, 0.13)
        m.sphere((s * 0.48, -1.22, 2.62), 0.11, LT, (1, 0.6, 1))
    m.sphere((0, -2.17, 1.92), 0.09, BLACK, (1.3, 1, 0.9))
    # Epic: glowing honey on the back + a honey drip
    m.sphere((0.2, -0.3, 2.85), 0.35, HONEY, (1.3, 1.2, 0.45))
    m.sphere((0.55, -0.25, 2.55), 0.12, HONEY, (1, 1, 1.8))
    m.sphere((-0.3, 0.35, 2.55), 0.22, HONEY, (1.2, 1.0, 0.45))
    m.glow_cols = [HONEY]
    return m


def stag():
    m = MB('Golden Stag')
    GD, LT, HF, AN = rgb(255, 196, 70), rgb(255, 240, 205), rgb(140, 96, 40), rgb(255, 248, 200)
    m.ell((0, 0.2, 1.95), 0.55, (0.95, 1.85, 0.9), GD)                          # body
    m.ell((0, 0.2, 1.7), 0.42, (0.85, 1.6, 0.5), LT)                            # belly
    legs4(m, GD, -0.65, 1.05, 0.3, 1.7, 0.11, foot=True, foot_col=HF)
    m.cap((0, -0.65, 2.15), (0, -1.0, 2.85), 0.27, GD)                          # neck
    m.ball((0, -1.15, 3.05), 0.38, GD)                                          # head
    m.ell((0, -1.5, 2.9), 0.22, (0.85, 1.5, 0.8), LT)                           # snout
    m.sym(m.ell, (0.42, -1.0, 3.25), 0.13, (1.9, 0.6, 0.9), GD, rot=(0, 0, 20))     # ears
    m.ball((0, 1.3, 2.2), 0.18, LT)                                             # tail
    for s in (-1, 1):
        m.eye((s * 0.2, -1.42, 3.12), s, 0.1)
        # glowing antlers
        b = Vector((s * 0.15, -1.05, 3.35))
        main = [b, b + Vector((s * 0.25, 0.1, 0.45)), b + Vector((s * 0.55, 0.25, 0.95)), b + Vector((s * 0.8, 0.4, 1.55))]
        m.tube(main, [0.07, 0.06, 0.05, 0.03], AN, 10)
        for k, p in enumerate(main[1:3]):
            m.tube([p, p + Vector((s * 0.05, -0.3, 0.38 + k * 0.1))], [0.045, 0.02], AN, 8)
        m.tube([main[2], main[2] + Vector((s * 0.45, 0.15, 0.2))], [0.045, 0.02], AN, 8)
    m.sphere((0, -1.83, 2.95), 0.05, BLACK)
    m.glow_cols = [AN]
    return m


def lion():
    m = MB('Sun Lion')
    GD, LT, MN, MN2, FL = rgb(244, 176, 74), rgb(255, 232, 186), rgb(196, 76, 28), rgb(240, 120, 36), rgb(255, 226, 90)
    m.ell((0, 0.3, 1.9), 0.75, (0.95, 1.75, 0.9), GD)                           # body
    legs4(m, GD, -0.75, 1.15, 0.42, 1.6, 0.2, foot=True, foot_col=LT)
    for k in range(14):                                                         # mane: ring of balls
        a = 2 * math.pi * k / 14
        m.ball((math.cos(a) * 0.72, -0.78 + 0.08, 2.55 + math.sin(a) * 0.72), 0.36, MN if k % 2 else MN2)
    m.ball((0, -0.65, 2.55), 0.62, MN)
    m.ball((0, -1.05, 2.5), 0.5, GD)                                            # face
    m.ell((0, -1.42, 2.3), 0.27, (1.0, 0.9, 0.75), LT)                          # muzzle
    m.sym(m.ball, (0.42, -0.98, 2.98), 0.14, GD)                                # ears
    m.cap((0, 1.6, 2.1), (0, 2.3, 1.7), 0.07, GD)                               # tail
    for s in (-1, 1):
        m.eye((s * 0.24, -1.42, 2.63), s, 0.12, iris=rgb(250, 160, 40))
    m.sphere((0, -1.68, 2.42), 0.08, rgb(120, 60, 50), (1.3, 1, 0.8))
    # Mythic: glowing flame tail tip + a crown of light
    m.sphere((0, 2.38, 1.72), 0.2, FL, (1, 1, 1.6))
    for k in range(7):
        a = math.pi * (0.15 + 0.7 * k / 6)
        m.cone((math.cos(a) * 0.85, -0.7, 2.55 + math.sin(a) * 0.85), (math.cos(a) * 1.2, -0.75, 2.55 + math.sin(a) * 1.2), 0.08, FL, segs=8)
    m.glow_cols = [FL]
    return m


PETS = [('Meadow Bunny', 'Common', bunny), ('Fluffy Sheep', 'Common', sheep), ('Spotted Cow', 'Common', cow),
        ('Bumble Bee', 'Uncommon', bee), ('Red Fox', 'Uncommon', fox), ('Wild Boar', 'Rare', boar), ('Barn Owl', 'Rare', owl),
        ('Honey Grizzly', 'Epic', bear), ('Golden Stag', 'Legendary', stag), ('Sun Lion', 'Mythic', lion)]

if __name__ == '__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc, cam = LL.stage()
    pick = [int(a) for a in args] if args else range(1, 11)
    for i in pick:
        name, rar, fn = PETS[i - 1]
        body = fn().build()
        px = pixelate(body)
        for o in bpy.data.objects:
            if o.type == 'MESH' and o.name != 'Plane':
                o.hide_render = o is not body
        LL.shoot(sc, cam, body, OUT / f'{i:02d}_3d.png')
        body.hide_render, px.hide_render = True, False
        LL.shoot(sc, cam, px, OUT / f'{i:02d}.png')
        px.hide_render = True
        print(name, len(body.data.polygons), '->', len(px.data.polygons))
    print('done')
