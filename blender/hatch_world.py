"""PREVIEW of the new IN-WORLD hatch (style of the reference clip the user sent 16 Nov):
egg floats over a stone pedestal at night, rune circle on the ground, the whole scene climbs through the
rarity colours (COMMON -> UNCOMMON -> RARE -> EPIC -> LEGENDARY) with lightning on the egg, crystal crown,
rising sparks; charge -> (legendary: blackout) -> POP (flash, ground shock ring, light blades, shards,
light pillars) -> pet lands on the pedestal. Everything here is buildable in Roblox from parts
(Neon parts, PointLight, ColorCorrection, Bloom, SurfaceGui text).
  blender -b -P hatch_world.py -- [every=N] [only=K] [t=sec,sec]   -> out/hw3d/f0000.png + meta.json
then: py hatch_world_overlay.py"""
import bpy, bmesh, math, sys, json, random, pathlib
from mathutils import Matrix, Vector

HERE = pathlib.Path(__file__).resolve().parent
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
EVERY = int(next((a.split('=')[1] for a in ARGS if a.startswith('every=')), 1))
ONLY = int(next((a.split('=')[1] for a in ARGS if a.startswith('only=')), 0))
TIMES = next((a.split('=')[1] for a in ARGS if a.startswith('t=')), None)
OUT = HERE / 'out' / 'hw3d'
OUT.mkdir(parents=True, exist_ok=True)

# egg, pets and the Roblox->Blender helpers come from the old preview script (everything before its scene part)
_src = (HERE / 'hatch_preview.py').read_text(encoding='utf-8')
_src = _src[:_src.index('# ---------------------------------------------------------------- scene (the hatch')]
_argv = sys.argv
G = {'__file__': str(HERE / 'hatch_preview.py'), '__name__': 'hp'}
exec(compile(_src, 'hatch_preview.py', 'exec'), G)
sys.argv = _argv
for _k in ('A', 'AI', 'RT', 'RX', 'RY', 'RZ', 'SC', 'look_at', 'place', 'lin', 'neon_mat', 'set_neon', 'plastic_mat', 'prim', 'neon_obj', 'EGG', 'PETS', 'PET_NAMES'):
    globals()[_k] = G[_k]
TL = G['TL']

FPS = 30
EGG_H = 4.0
TOP = 3.4                     # pedestal top (studs)
FLOAT_Y = TOP + 1.2           # egg bottom while floating
RAR = [('COMMON', 2, (235, 238, 248)), ('UNCOMMON', 4, (96, 230, 96)), ('RARE', 20, (70, 160, 255)),
       ('EPIC', 150, (190, 90, 255)), ('LEGENDARY', 2000, (255, 196, 30))]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def mixc(a, b, u):
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))


def ease_out(u):
    return 1 - (1 - clamp(u)) ** 3


def ease_in(u):
    return clamp(u) ** 2


def back_out(u, s=1.7):
    u = clamp(u) - 1
    return u * u * ((s + 1) * u + s) + 1


def bounce_out(t):
    t = clamp(t)
    n, d = 7.5625, 2.75
    if t < 1 / d:
        return n * t * t
    if t < 2 / d:
        t -= 1.5 / d
        return n * t * t + 0.75
    if t < 2.5 / d:
        t -= 2.25 / d
        return n * t * t + 0.9375
    t -= 2.625 / d
    return n * t * t + 0.984375


# ================================================================ TIMELINE (same numbers will go into the Lua)
class Demo:
    INTRO = 0.9
    def __init__(self, r):
        self.r = r
        self.lvl = 1.0 if r <= 3 else 1.1           # seconds per rarity step
        self.t_lv = self.INTRO                       # first step starts
        self.t_charge = self.t_lv + r * self.lvl
        self.charge = 0.55 + 0.1 * r
        self.black = 0.45 if r >= 5 else 0.0
        self.P = self.t_charge + self.charge + self.black   # POP
        self.hold = [1.6, 1.8, 2.2, 2.8, 3.4][r - 1]
        self.end = self.P + 0.5 + self.hold + 0.35
        rnd = random.Random(r * 7)
        self.shards = [dict(d=Vector((rnd.uniform(-1, 1), rnd.uniform(0.2, 1.3), rnd.uniform(-1, 0.6))).normalized() * rnd.uniform(9, 17),
                            s=rnd.uniform(0.35, 0.8), rot=Vector((rnd.uniform(-9, 9), rnd.uniform(-9, 9), rnd.uniform(-9, 9))),
                            star=(k % 3 == 0)) for k in range(14 + 6 * r)]
        self.sparks = [dict(a=rnd.uniform(0, math.tau), rad=rnd.uniform(2, 8.5), t0=rnd.uniform(0, 40), sp=rnd.uniform(2.5, 5),
                            s=rnd.uniform(0.12, 0.28)) for _ in range(70)]

    def level(self, t):  # current rarity step 1..r (0 before the first)
        if t < self.t_lv:
            return 0
        return min(self.r, 1 + int((t - self.t_lv) / self.lvl))

    def level_age(self, t):
        L = self.level(t)
        return t - (self.t_lv + (L - 1) * self.lvl) if L else 0

    def charge_u(self, t):  # 0..1 over the whole build-up (levels + charge)
        return clamp((t - self.t_lv) / (self.t_charge + self.charge - self.t_lv))


# ================================================================ SCENE
sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
try:
    sc.eevee.taa_render_samples = 16
except Exception:
    pass
sc.view_settings.view_transform = 'Standard'
sc.render.film_transparent = False
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
W = bpy.data.worlds.new('W')
sc.world = W
W.use_nodes = True
BG = next(n for n in W.node_tree.nodes if n.type == 'BACKGROUND')

# bloom = Roblox BloomEffect: compositor glare
sc.use_nodes = True
nt = sc.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
rl = nt.nodes.new('CompositorNodeRLayers')
gl = nt.nodes.new('CompositorNodeGlare')
gl.glare_type = 'FOG_GLOW'
gl.quality = 'MEDIUM'
gl.threshold = 0.85
gl.size = 8
comp = nt.nodes.new('CompositorNodeComposite')
nt.links.new(rl.outputs['Image'], gl.inputs['Image'])
nt.links.new(gl.outputs['Image'], comp.inputs['Image'])

moon = bpy.data.objects.new('Moon', bpy.data.lights.new('Moon', 'SUN'))
moon.data.energy = 0.6
moon.data.color = lin((150, 160, 255))[:3]
moon.rotation_euler = (math.radians(55), 0, math.radians(200))
sc.collection.objects.link(moon)
glow = bpy.data.objects.new('EggLight', bpy.data.lights.new('EggLight', 'POINT'))
glow.data.shadow_soft_size = 1.5
sc.collection.objects.link(glow)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens_unit = 'FOV'

STONE = plastic_mat('Stone', (70, 74, 96))
STONE2 = plastic_mat('Stone2', (96, 100, 126))
DARK = plastic_mat('Ground', (34, 36, 52))


def box(name, mat, m):
    o = prim(name, 'cube', mat)
    place(o, m)
    return o


def cyl(name, mat, x, y, z, r, h):
    o = prim(name, 'cylx', mat)
    place(o, RT(x, y, z) @ RZ(math.pi / 2) @ SC(h, r * 2, r * 2))
    return o


# ground + checker tiles (game style) + ruins around
box('Ground', DARK, RT(0, -0.5, 0) @ SC(140, 1, 140))
for i in range(-6, 7):
    for j in range(-6, 7):
        if (i + j) % 2 == 0 and i * i + j * j < 40:
            box(f'T{i}_{j}', STONE, RT(i * 4, 0.02, j * 4) @ SC(4, 0.06, 4))
BRAZ = []
for k in range(8):
    a = k * math.tau / 8 + math.pi / 8
    x, z = math.sin(a) * 15, math.cos(a) * 15
    if z < -9:  # keep the front open for the camera
        continue
    cyl(f'Col{k}', STONE2, x, 3, z, 1.1, 6)
    cyl(f'ColTop{k}', STONE, x, 6.3, z, 1.5, 0.6)
    bowl = cyl(f'Bowl{k}', STONE, x, 6.9, z, 1.2, 0.6)
    fl = neon_obj(f'Flame{k}', 'ball')
    BRAZ.append((fl, x, z, k))
for k in range(5):  # back wall ruins
    box(f'Wall{k}', STONE2, RT(-20 + k * 10, 4 + (k % 2) * 2, 26) @ SC(9.6, 8 + (k % 2) * 4, 2))

# pedestal
cyl('Ped0', STONE, 0, 0.3, 0, 3.4, 0.6)
cyl('Ped1', STONE2, 0, 1.6, 0, 2.3, 2.0)
cyl('Ped2', STONE, 0, 3.0, 0, 3.0, 0.8)
PED_PRONG = []
for k in range(4):
    a = k * math.tau / 4 + math.pi / 4
    p = neon_obj(f'Prong{k}', 'cube')
    PED_PRONG.append((p, a))


def annulus(name, r_in, r_out, seg=96, dash=0):
    bm = bmesh.new()
    vi, vo = [], []
    for k in range(seg):
        a = k * math.tau / seg
        vi.append(bm.verts.new((math.cos(a) * r_in, math.sin(a) * r_in, 0)))
        vo.append(bm.verts.new((math.cos(a) * r_out, math.sin(a) * r_out, 0)))
    for k in range(seg):
        if dash and (k // dash) % 2:
            continue
        k2 = (k + 1) % seg
        bm.faces.new((vi[k], vo[k], vo[k2], vi[k2]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    me.materials.append(neon_mat('N_' + name))
    return ob


# rune circle (flat on the ground): outer ring, dashed ring, inner ring, 12 runes, star lines
RUNE = [annulus('RuneOuter', 8.6, 9.0), annulus('RuneDash', 7.7, 8.0, 96, 3), annulus('RuneInner', 5.0, 5.25)]
RUNE_TICKS = [neon_obj(f'Rune{k}', 'cube') for k in range(12)]
RUNE_STAR = [neon_obj(f'Star{k}', 'cube') for k in range(6)]
SHOCK = annulus('Shock', 0.9, 1.0, 96)
PED_TRIM = annulus('PedTrim', 2.75, 3.05, 64)
place(PED_TRIM, RT(0, 3.43, 0))

# 3D ground label (SurfaceGui in Roblox): rarity name in front of the pedestal
LABEL = {}
fnt = bpy.data.fonts.load(str(HERE / 'fonts' / 'LuckiestGuy.ttf'))
for name, _, col in RAR:
    cu = bpy.data.curves.new('L_' + name, 'FONT')
    cu.body = name
    cu.font = fnt
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.size = 1.25
    ob = bpy.data.objects.new('L_' + name, cu)
    sc.collection.objects.link(ob)
    cu.materials.append(neon_mat('NL_' + name))
    LABEL[name] = ob

# egg + aura + cracks
EGG_SC = EGG_H / EGG.dimensions.z
EGG_W = EGG.dimensions.x * EGG_SC
AURA = neon_obj('Aura', 'ball')
pts, n = [], 14
_cr = random.Random(5)
for k in range(n + 1):
    a = math.radians(195 + 150 * k / n + _cr.uniform(-4, 4))
    dy = EGG_H * 0.08 + _cr.uniform(-0.28, 0.28) + 0.15 * math.sin(k * 0.9)
    r = EGG_W / 2 * math.sqrt(max(1 - (dy / (EGG_H / 2)) ** 2, 0.05)) * 1.03
    pts.append(Vector((math.cos(a) * r, dy, math.sin(a) * r)))
CRACKS = []
for k in range(n):
    ob = neon_obj(f'Crack{k}', 'cube')
    CRACKS.append((ob, look_at((pts[k] + pts[k + 1]) * 0.5, pts[k + 1]), (pts[k] - pts[k + 1]).length + 0.1))

BOLT = [neon_obj(f'Bolt{k}', 'cube') for k in range(64)]           # lightning segments
CRYST = []                                                         # crystal crown shards
for k in range(12):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.5, radius2=0, depth=1, matrix=Matrix.Translation((0, 0, 0.5)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.5, radius2=0, depth=0.35, matrix=Matrix.Translation((0, 0, -0.175)) @ Matrix.Rotation(math.pi, 4, 'X'))
    me = bpy.data.meshes.new(f'Cr{k}')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(f'Cr{k}', me)
    sc.collection.objects.link(ob)
    me.materials.append(neon_mat(f'NCr{k}'))
    CRYST.append(ob)
SPARK = [neon_obj(f'Spark{k}', 'cube') for k in range(70)]
BLADE = [neon_obj(f'Blade{k}', 'cube') for k in range(16)]          # light blades of the pop
PILLAR = [neon_obj(f'Pillar{k}', 'cylx') for k in range(6)]          # legendary light pillars
BEAM_UP = neon_obj('BeamUp', 'cylx')                                # sky beam on every rarity step
SHARD_EGG = plastic_mat('ShardEgg', (250, 240, 214))
SHARDS = [prim(f'Shard{k}', 'cube', SHARD_EGG) for k in range(44)]
SHARDN = [neon_obj(f'ShardN{k}', 'cube') for k in range(44)]
HALO = annulus('Halo', 3.1, 3.4, 96)

PET_FIT, PET_OFF = [], []
for p in PETS:
    bb = [Vector(c) for c in p.bound_box]
    lo = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    hi = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    PET_FIT.append(5.4 / max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, 0.5))
    PET_OFF.append(Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)))

for _m in bpy.data.materials:
    if 'em' in _m.keys():
        _m.node_tree.nodes[_m['em']].inputs['Strength'].default_value = 2.2
DYN = [EGG, AURA, SHOCK, HALO, BEAM_UP] + [c[0] for c in CRACKS] + BOLT + CRYST + SPARK + BLADE + PILLAR + SHARDS + SHARDN + PETS + list(LABEL.values())


def flat(m):  # lay a Blender-XY-plane object flat on the Roblox ground
    return m @ RX(-math.pi / 2)


def place_flat(ob, mr):
    ob.matrix_world = A @ mr @ AI @ Matrix.Rotation(0, 4, 'X')


def egg_point(u, v, s):  # point on the egg surface (u around, v -1..1 up), local to egg centre
    ry = EGG_H / 2 * s
    rx = EGG_W / 2 * s * 1.04
    c = math.sqrt(max(1 - v * v, 0.02))
    return Vector((math.cos(u) * rx * c, v * ry, math.sin(u) * rx * c))


# ================================================================ ONE FRAME
def frame(d, t):
    for o in DYN:
        o.hide_render = True
    r = d.r
    L = d.level(t)
    age = d.level_age(t)
    cu = d.charge_u(t)
    col = (255, 236, 200) if L == 0 else RAR[L - 1][2]
    popped = t >= d.P
    pa = t - d.P
    black = 0.0
    if d.black and d.t_charge + d.charge <= t < d.P:
        black = clamp((t - d.t_charge - d.charge) / 0.15)
    if popped:
        col = RAR[r - 1][2]
    step_flash = math.exp(-age * 5) if L else 0.0          # punch at every new rarity
    meta = dict(level=L, age=age, cu=cu, popped=popped, pa=pa, black=black, col=col, r=r)

    # world + lights: the whole place takes the rarity colour
    tint = 0.15 + 0.35 * cu if not popped else 0.5 * math.exp(-pa * 0.6) + 0.18
    BG.inputs[0].default_value = lin(mixc((10, 12, 30), col, tint * 0.35))
    BG.inputs[1].default_value = (0.9 + 0.6 * step_flash) * (1 - black)
    moon.data.energy = 0.6 * (1 - black)
    glow.data.color = lin(col)[:3]
    gE = (300 + 2600 * cu + 4000 * step_flash) if not popped else 6000 * math.exp(-pa * 2.5) + 900
    glow.data.energy = gE * (1 - 0.92 * black)
    glow.location = (A @ Vector((0, FLOAT_Y + EGG_H / 2, 0, 1))).to_3d()
    for fl, x, z, k in BRAZ:
        fl.hide_render = False
        s = 1.2 + 0.2 * math.sin(t * 13 + k) + 0.6 * cu
        set_neon(fl, mixc((255, 150, 40), col, 0.65 * cu if not popped else 0.65), 1 - black)
        place(fl, RT(x, 7.6 + 0.15 * math.sin(t * 9 + k), z) @ SC(s, s * 1.5, s))

    # camera: slow push-in during the build-up, shake grows, legendary orbit after the pop
    shake = (0.02 + 0.22 * cu ** 2) if not popped else 0.5 * math.exp(-pa * 5)
    rnd = random.Random(int(t * 1000))
    p0 = Vector((0, 15, -36))
    p1 = Vector((0, 12.5, -27))
    pos = p0.lerp(p1, ease_out(clamp(t / (d.t_charge + 0.6))))
    tgt = Vector((0, FLOAT_Y + 0.2, -1.0))
    if popped and r >= 4:
        a = 0.35 * math.sin(pa * 0.7) * ease_out(pa / 1.5)
        pos = (RY(a) @ pos.to_4d()).to_3d()
    pos = pos + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)) * shake
    cam.matrix_world = A @ look_at(pos, tgt)
    fov = 46 - 6 * ease_in(cu) if not popped else 46 - 6 + 10 * math.exp(-pa * 4) * (1 if pa > 0.04 else 0)
    cam.data.angle = math.radians(fov)

    # pedestal trim + prongs
    PED_TRIM.hide_render = False
    set_neon(PED_TRIM, col, 0.5 + 0.5 * cu)
    # rune circle: turns, brightens with each rarity
    spin = t * (0.25 + 1.2 * cu)
    rb = (0.25 + 0.6 * cu + 0.4 * step_flash) * (1 - black) if not popped else 0.9 * math.exp(-pa * 0.5) + 0.25
    for k, ro in enumerate(RUNE):
        ro.hide_render = False
        set_neon(ro, col, clamp(rb * (1 - 0.25 * k)))
        place(ro, RT(0, 0.08 + k * 0.01, 0) @ RY(spin * (1 if k != 1 else -1.6)))
    for k, tk in enumerate(RUNE_TICKS):
        tk.hide_render = False
        a = k * math.tau / 12 + spin
        set_neon(tk, col, clamp(rb))
        place(tk, RT(math.cos(a) * 6.6, 0.1, math.sin(a) * 6.6) @ RY(math.pi / 2 - a) @ SC(0.25, 0.04, 1.1 if k % 3 == 0 else 0.6))
    for k, sl in enumerate(RUNE_STAR):  # hexagram lines between the rings
        sl.hide_render = False
        a = k * math.tau / 6 - spin * 0.6
        p, q = Vector((math.cos(a) * 7.7, 0.09, math.sin(a) * 7.7)), Vector((math.cos(a + math.tau / 3) * 7.7, 0.09, math.sin(a + math.tau / 3) * 7.7))
        m = look_at((p + q) / 2, q)
        set_neon(sl, col, clamp(rb * 0.6))
        place(sl, m @ SC(0.12, 0.03, (p - q).length))
    # rarity name on the ground, slams in at every step (and the final one after the pop)
    show = RAR[(r if popped else L) - 1][0] if (L or popped) else None
    if show:
        lab = LABEL[show]
        lab.hide_render = False
        sa = age if not popped else pa + 1
        k = 1 + 0.8 * math.exp(-sa * 9)
        set_neon(lab, col, 1 - black)
        lab.matrix_world = Matrix.Translation((0, 7.2, 0.7)) @ Matrix.Rotation(math.radians(-58), 4, 'X') @ Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Scale(k, 4)

    # sky beam punch at every rarity step
    if L and not popped and age < 0.5 and L >= 2:
        BEAM_UP.hide_render = False
        w = 2.4 * (1 - age / 0.5) + 0.3
        set_neon(BEAM_UP, col, 0.55 * (1 - age / 0.5))
        place(BEAM_UP, RT(0, 40, 0) @ RZ(math.pi / 2) @ SC(80, w, w))

    # rising sparks (more with every rarity)
    nsp = int(8 + 60 * cu) if not popped else int(70 * math.exp(-pa * 0.4))
    for k, sp in enumerate(d.sparks[:nsp]):
        o = SPARK[k]
        o.hide_render = False
        h = ((t + sp['t0']) * sp['sp']) % 14
        a = sp['a'] + t * 0.4
        set_neon(o, mixc(col, (255, 255, 255), 0.4), clamp(1 - h / 14) * (1 - black))
        s = sp['s']
        place(o, RT(math.cos(a) * sp['rad'], h, math.sin(a) * sp['rad']) @ RY(t * 3 + k) @ SC(s, s, s))

    if not popped:
        # ---------- the egg: rises off the pedestal, floats + sways, then shakes harder and harder
        rise = ease_out(clamp(t / 0.8))
        bob = 0.35 * math.sin(t * 2.3) * (1 - cu * 0.6)
        sway = 0.08 * math.sin(t * 1.6)
        sh = cu ** 1.6
        jit = random.Random(int(t * 60))
        tilt = sway + (math.sin(t * (18 + 22 * sh)) * 0.28 * sh)
        squeeze = 1.0
        ct = t - d.t_charge
        if ct > 0:
            squeeze = 1 + 0.18 * ease_in(ct / d.charge)
        if black:
            squeeze = 1.18 - 0.1 * black
        s = (0.2 + 0.8 * back_out(t / 0.45)) * squeeze * (1 + 0.07 * step_flash)
        y = TOP + 0.1 + (FLOAT_Y - TOP) * rise + bob + jit.uniform(-1, 1) * 0.06 * sh
        base = RT(jit.uniform(-1, 1) * 0.08 * sh, y, 0) @ RZ(tilt) @ RT(0, EGG_H * s / 2, 0)
        EGG.hide_render = False
        EGG.matrix_world = A @ (base @ RY(t * (0.6 + 6 * sh)) @ RT(0, -EGG_H * s / 2, 0)) @ AI @ Matrix.Scale(EGG_SC * s, 4)
        AURA.hide_render = False
        au = 0.15 + 0.45 * cu + 0.3 * step_flash
        set_neon(AURA, col, au * 0.28 * (1 - 0.6 * black))
        asz = EGG_W * s * (1.12 + 0.25 * cu + 0.12 * step_flash)
        place(AURA, base @ SC(asz, asz * EGG_H / EGG_W, asz))
        nc = int(clamp(cu * 1.3) * len(CRACKS))
        ccol = mixc(col, (255, 255, 255), 0.55)
        for k, (ob, cf, ln) in enumerate(CRACKS):
            if k < nc:
                ob.hide_render = False
                set_neon(ob, ccol, 1)
                m = cf.copy()
                m.translation = cf.translation * s
                place(ob, base @ m @ SC(0.09 * s, 0.09 * s, ln * s))
        # lightning crawling over the egg from RARE on (redrawn 15x a second)
        nb = 0 if L < 3 else (L - 2) + int(2 * cu)
        if black:
            nb = 6
        br = random.Random(int(t * 15) + r * 100)
        seg = 0
        for b in range(nb):
            u, v = br.uniform(0, math.tau), br.uniform(-0.8, 0.8)
            p = egg_point(u, v, s * 1.05)
            for _ in range(6):
                if seg >= len(BOLT):
                    break
                u += br.uniform(-0.45, 0.45)
                v = clamp(v + br.uniform(-0.35, 0.35), -0.9, 0.9)
                q = egg_point(u, v, s * (1.05 + br.uniform(0, 0.12)))
                o = BOLT[seg]
                seg += 1
                o.hide_render = False
                set_neon(o, mixc(col, (255, 255, 255), 0.5), 1)
                cb = base @ Matrix.Translation((0, 0, 0))
                pw, qw = (cb @ p.to_4d()).to_3d(), (cb @ q.to_4d()).to_3d()
                place(o, look_at((pw + qw) / 2, qw) @ SC(0.06, 0.06, (pw - qw).length + 0.05))
                p = q
        # crystal crown from EPIC on
        nc = 0 if L < 4 else (6 if L == 4 else 10)
        cen = (base @ Vector((0, 0, 0, 1))).to_3d()
        for k in range(nc):
            o = CRYST[k]
            o.hide_render = False
            a = k * math.tau / nc + t * (0.8 + 2.5 * cu)
            grow = back_out(age / 0.4) if L == (4 if nc == 6 else 5) else 1
            rad = 4.2 + 0.4 * math.sin(t * 3 + k)
            yy = 0.8 * math.sin(a * 2 + t * 2)
            set_neon(o, mixc(col, (255, 255, 255), 0.25 + 0.3 * (k % 2)), 1)
            ln = (1.6 if k % 2 == 0 else 1.1) * grow
            dirv = Vector((math.cos(a), 0.25, math.sin(a))).normalized()
            pos_ = cen + Vector((math.cos(a) * rad, yy, math.sin(a) * rad))
            m = look_at(pos_, pos_ + dirv)  # local -Z points outwards
            place(o, m @ RX(-math.pi / 2) @ SC(0.5 * grow, ln, 0.5 * grow))
    else:
        # ---------- POP: ground shock ring, light blades, shards, (legendary) pillars, pet lands
        ey = FLOAT_Y + EGG_H * 0.6
        if pa < 0.8:
            u = pa / 0.8
            SHOCK.hide_render = False
            R = 1 + 22 * ease_out(u)
            set_neon(SHOCK, mixc(col, (255, 255, 255), 0.3), (1 - u) * 0.9)
            place(SHOCK, RT(0, 0.15, 0) @ SC(R, 1, R))
        nbl = 6 + 2 * r
        if pa < 1.1:
            u = pa / 1.1
            for k in range(nbl):
                o = BLADE[k]
                o.hide_render = False
                a = k * math.tau / nbl + pa * 0.8
                ln = 4 + 26 * ease_out(u * 1.6)
                set_neon(o, mixc(col, (255, 255, 255), 0.5 if k % 2 else 0.1), clamp(1 - u) * 0.85)
                # blades lie in the screen plane round the egg (camera looks along +Z)
                place(o, RT(0, ey, 0) @ RZ(a) @ RT(0, ln / 2 + 1.5, 0) @ SC(0.35 * (1 - u) + 0.08, ln, 0.1))
        for k, shd in enumerate(d.shards):
            if pa > 1.2:
                break
            p = Vector((0, ey, 0)) + shd['d'] * pa + Vector((0, -16 * pa * pa, 0))
            o = SHARDN[k] if shd['star'] else SHARDS[k]
            o.hide_render = False
            if shd['star']:
                set_neon(o, col, clamp(1 - pa / 1.2))
            s = shd['s'] * (1 - 0.5 * pa / 1.2)
            place(o, RT(*p) @ RX(shd['rot'].x * pa) @ RY(shd['rot'].y * pa) @ RZ(shd['rot'].z * pa) @ SC(s, s * 0.45, s))
        if r >= 5:  # legendary: golden pillars of light rise round the circle
            for k in range(6):
                o = PILLAR[k]
                o.hide_render = False
                a = math.radians(15 + k * 30)  # only behind the pedestal, never between egg and camera
                h = 60 * ease_out(pa / 0.6)
                w = 0.9 + 0.2 * math.sin(pa * 6 + k)
                set_neon(o, mixc(col, (255, 255, 255), 0.3), 0.35 * clamp(1.5 - pa / 3))
                place(o, RT(math.cos(a) * 11, h / 2, math.sin(a) * 11 + 2) @ RZ(math.pi / 2) @ SC(h, w, w))
        # the pet: pops out of the egg's place, falls onto the pedestal with a bounce, spins to face the camera
        i = r - 1
        pet = PETS[i]
        pet.hide_render = False
        gk = back_out(pa / 0.45)
        kk = PET_FIT[i] * max(gk, 0.02)
        fall = 1 - bounce_out(pa / 0.7)
        y = TOP + 0.05 + 2.4 * fall
        hop = 0
        if pa > 1.0:  # presentation hop
            hu = (pa - 1.0) / 0.35
            if hu < 1:
                hop = 0.9 * math.sin(math.pi * hu)
        idle = 0.12 * abs(math.sin(pa * 3)) if pa > 1.4 else 0
        spin = math.pi * 3 * (1 - ease_out(pa / 1.1)) + 0.3 * math.sin(pa * 1.8) * clamp(pa - 1.1)
        pet.matrix_world = (A @ RT(0, y + hop + idle, 0) @ AI) @ Matrix.Rotation(spin, 4, 'Z') @ Matrix.Scale(kk, 4) @ Matrix.Translation(-PET_OFF[i])
        if r >= 4:
            HALO.hide_render = False
            hs = 1 + 0.06 * math.sin(pa * 5)
            set_neon(HALO, col, 0.8 * clamp(pa / 0.4))
            place(HALO, RT(0, TOP + 2.6, 2.4) @ RZ(pa * 0.6) @ RX(math.pi / 2) @ SC(hs, 1, hs))
    return meta


# ================================================================ RENDER: a RARE hatch, then a LEGENDARY one
DEMOS = [Demo(3), Demo(5)]
metas, f = [], 0
want = [float(x) for x in TIMES.split(',')] if TIMES else None
start = 0.0
for di, d in enumerate(DEMOS):
    nf = int(round(d.end * FPS))
    for j in range(nf):
        t = j / FPS
        if want is not None:
            if not any(abs((start + t) - w) < 0.5 / FPS for w in want):
                f += 1
                continue
        elif (ONLY and ONLY != di + 1) or f % EVERY:
            f += 1
            continue
        m = frame(d, t)
        m.update(f=f, demo=di, t=t, name=PET_NAMES[d.r - 1], end=d.end, P=d.P)
        metas.append(m)
        sc.render.filepath = str(OUT / f'f{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        f += 1
    start += d.end
(OUT / 'meta.json').write_text(json.dumps(metas), encoding='utf-8')
print('frames', f)
