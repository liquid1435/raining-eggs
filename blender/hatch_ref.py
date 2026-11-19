"""PREVIEW v2 of the in-world hatch, made to MATCH the reference clip the user sent (16 Nov):
night castle + big moon, round stone floor, ring of goblet braziers, black egg with gold bands held by gold claws,
thin glowing lightning on the egg + 2 side orbs, background flood of the rarity colour at every step,
COMMON -> UNCOMMON -> RARE -> EPIC (light petals) -> LEGENDARY (gold spike crown + turning square) ->
white egg -> POP (star-line burst, dashed ring, diamond shards, rays) -> pet on the stand, serif name.
  blender -b -P hatch_ref.py -- [t=s,s,..] [every=N]  -> out/hr3d/f0000.png + meta.json ; then py hatch_ref_overlay.py"""
import bpy, bmesh, math, sys, json, random, pathlib, colorsys
from mathutils import Matrix, Vector

HERE = pathlib.Path(__file__).resolve().parent
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
EVERY = int(next((a.split('=')[1] for a in ARGS if a.startswith('every=')), 1))
TIMES = next((a.split('=')[1] for a in ARGS if a.startswith('t=')), None)
OUT = HERE / 'out' / 'hr3d'
OUT.mkdir(parents=True, exist_ok=True)

_src = (HERE / 'hatch_preview.py').read_text(encoding='utf-8')
_src = _src[:_src.index('# ---------------------------------------------------------------- scene (the hatch')]
_argv = sys.argv
G = {'__file__': str(HERE / 'hatch_preview.py'), '__name__': 'hp'}
exec(compile(_src, 'hatch_preview.py', 'exec'), G)
sys.argv = _argv
for _k in ('A', 'AI', 'RT', 'RX', 'RY', 'RZ', 'SC', 'look_at', 'place', 'lin', 'neon_mat', 'set_neon', 'plastic_mat', 'prim', 'neon_obj', 'EGG', 'PETS', 'PET_NAMES'):
    globals()[_k] = G[_k]
bpy.data.objects.remove(EGG, do_unlink=True)  # the reference uses its own black + gold egg

FPS = 30
RAR6 = ('???', 600000000, (255, 255, 255))
RAR = [('COMMON', 2, (240, 242, 255)), ('UNCOMMON', 4, (80, 255, 120)), ('RARE', 20, (40, 200, 255)),
       ('EPIC', 150, (200, 60, 255)), ('LEGENDARY', 2000, (255, 190, 20))]
STAND_TOP = 3.4
EGG_RX, EGG_RY = 1.45, 2.05          # egg half width / half height
EC = Vector((0, STAND_TOP + 0.4 + EGG_RY, 0))  # egg centre

# timeline: one LEGENDARY hatch that climbs through every rarity (like the clip)
INTRO, LVL, CHARGE, WHITE_T = 1.4, 1.7, 0.6, 0.7
STEPS = [LVL] * 5 + [3.2]               # the ??? step lasts longer: the odds counter climbs there
ST0 = [INTRO + sum(STEPS[:i]) for i in range(6)]
TOT = sum(STEPS)
T_POP = INTRO + TOT + CHARGE + WHITE_T
END = T_POP + 5.6


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def mixc(a, b, u):
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))


def eo(u):
    return 1 - (1 - clamp(u)) ** 3


def back_out(u, s=1.7):
    u = clamp(u) - 1
    return u * u * ((s + 1) * u + s) + 1


# ================================================================ scene setup
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
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
W = bpy.data.worlds.new('W')
sc.world = W
W.use_nodes = True
BG = next(n for n in W.node_tree.nodes if n.type == 'BACKGROUND')
BG.inputs[0].default_value = lin((4, 5, 14))
BG.inputs[1].default_value = 1.0
sc.use_nodes = True
nt = sc.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
rl = nt.nodes.new('CompositorNodeRLayers')
g1 = nt.nodes.new('CompositorNodeGlare')
g1.glare_type = 'FOG_GLOW'
g1.quality = 'HIGH'
g1.threshold = 0.7
g1.size = 9
g2 = nt.nodes.new('CompositorNodeGlare')
g2.glare_type = 'FOG_GLOW'
g2.quality = 'MEDIUM'
g2.threshold = 1.2
g2.size = 7
comp = nt.nodes.new('CompositorNodeComposite')
nt.links.new(rl.outputs['Image'], g1.inputs['Image'])
nt.links.new(g1.outputs['Image'], g2.inputs['Image'])
nt.links.new(g2.outputs['Image'], comp.inputs['Image'])

moonL = bpy.data.objects.new('MoonL', bpy.data.lights.new('MoonL', 'SUN'))
moonL.data.energy = 0.35
moonL.data.color = lin((140, 150, 255))[:3]
moonL.rotation_euler = (math.radians(50), 0, math.radians(160))
sc.collection.objects.link(moonL)
EL = bpy.data.objects.new('EggLight', bpy.data.lights.new('EggLight', 'POINT'))
EL.data.shadow_soft_size = 1.0
sc.collection.objects.link(EL)
BL = bpy.data.objects.new('BackLight', bpy.data.lights.new('BackLight', 'POINT'))  # floods the wall behind
BL.data.shadow_soft_size = 4
sc.collection.objects.link(BL)
BL.location = (A @ Vector((0, 9, 24, 1))).to_3d()
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
sc.collection.objects.link(cam)
sc.camera = cam


def nstr(m, v):
    m.node_tree.nodes[m['em']].inputs['Strength'].default_value = v


def mesh_rb(name, verts, faces, mat):
    """mesh authored in Roblox-local coords (x right, y up, z away from the camera)"""
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x, -z, y) for x, y, z in verts], [], faces)
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


def flat_shape(name, outline, mat):  # filled 2D shape in the XY (screen) plane, fan from the centre
    vs = [(0, sum(p[1] for p in outline) / len(outline), 0)] + [(x, y, 0) for x, y in outline]
    fs = [(0, i + 1, (i + 1) % len(outline) + 1) for i in range(len(outline))]
    return mesh_rb(name, vs, fs, mat)


def ring_xy(name, r_in, r_out, seg=128, dash=0, mat=None):
    vs, fs = [], []
    for k in range(seg):
        a = k * math.tau / seg
        vs += [(math.cos(a) * r_in, math.sin(a) * r_in, 0), (math.cos(a) * r_out, math.sin(a) * r_out, 0)]
    for k in range(seg):
        if dash and (k // dash) % 2:
            continue
        k2 = (k + 1) % seg
        fs.append((2 * k, 2 * k + 1, 2 * k2 + 1, 2 * k2))
    return mesh_rb(name, vs, fs, mat or neon_mat('N_' + name))


def ring_xz(name, r_in, r_out, seg=128, dash=0):
    o = ring_xy(name, r_in, r_out, seg, dash)
    return o


STONE = plastic_mat('Stone', (46, 50, 78))
STONE_D = plastic_mat('StoneD', (30, 32, 52))
FLOOR = plastic_mat('Floor', (70, 74, 100))
CLAY = plastic_mat('Clay', (150, 82, 52))
GOLD = plastic_mat('Gold', (230, 170, 50))
_b = next(n for n in GOLD.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
_b.inputs['Metallic'].default_value = 0.35
_b.inputs['Roughness'].default_value = 0.3
EGGM = plastic_mat('EggBlack', (12, 12, 16))
_b = next(n for n in EGGM.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
_b.inputs['Roughness'].default_value = 0.18
_EGG_EM = _b.inputs['Emission Color']
_EGG_ES = _b.inputs['Emission Strength']


def box(name, mat, m):
    o = prim(name, 'cube', mat)
    place(o, m)
    return o


def cyl(name, mat, x, y, z, r, h):
    o = prim(name, 'cylx', mat)
    place(o, RT(x, y, z) @ RZ(math.pi / 2) @ SC(h, r * 2, r * 2))
    return o


# --- castle at night: back wall with crenels, towers, big moon with a tower in front of it
rnd = random.Random(3)
for k in range(-6, 7):
    h = 10 + rnd.uniform(-1, 2.5)
    box(f'Wall{k}', STONE if k % 2 else STONE_D, RT(k * 5, h / 2, 34 + rnd.uniform(-1, 1)) @ SC(5.05, h, 3))
    if k % 2 == 0:
        box(f'Cren{k}', STONE, RT(k * 5, h + 1, 34) @ SC(2.5, 2, 3))
for x in (-26, 26):
    box(f'Tower{x}', STONE_D, RT(x, 14, 26) @ SC(9, 28, 9))
    for c in (-3, 0, 3):
        box(f'TC{x}{c}', STONE_D, RT(x + c, 29, 26) @ SC(2, 2.4, 9))
for k in range(-3, 4):  # side walls left/right
    for x in (-24, 24):
        box(f'Side{x}{k}', STONE_D, RT(x, 9, k * 6 + 6) @ SC(3, 18, 6.05))
moon = neon_obj('Moon', 'ball')
set_neon(moon, (235, 235, 250), 1)
place(moon, RT(-17, 21, 62) @ SC(13, 13, 1))
box('MoonTower', STONE_D, RT(-19.5, 8.5, 55) @ SC(4, 25, 4))
for c in (-1.3, 1.3):
    box(f'MTC{c}', STONE_D, RT(-19.5 + c, 22, 55) @ SC(1.1, 2, 4))
WIN = neon_obj('Window', 'cube')
set_neon(WIN, (150, 110, 255), 1)
place(WIN, RT(-7, 15, 32.4) @ SC(0.7, 1.6, 0.2))

# --- round stone floor + platform ring + tiles
cyl('Floor', FLOOR, 0, -0.25, 0, 16, 0.5)
for k in range(24):
    a = k * math.tau / 24
    box(f'Tile{k}', STONE if k % 2 else FLOOR, RT(math.cos(a) * 13.5, 0.02, math.sin(a) * 13.5) @ RY(-a) @ SC(4.5, 0.06, 3.3))
RIM = ring_xy('Rim', 15.6, 16.0, 160)
place(RIM, RT(0, 0.06, 0) @ RX(math.pi / 2))
# --- goblet braziers round the egg (bowl on three legs)
GOBLETS = []
for k in range(10):
    a = math.radians(-90 + 18 + k * 36)
    x, z = math.cos(a) * 9.5, math.sin(a) * 9.5 + 1
    cyl(f'GBowl{k}', CLAY, x, 3.0, z, 1.0, 1.2)
    cyl(f'GBowlB{k}', CLAY, x, 2.3, z, 0.6, 0.4)
    cyl(f'GRim{k}', CLAY, x, 3.62, z, 1.12, 0.12)
    for l in range(3):
        b = l * math.tau / 3 + a
        box(f'GLeg{k}{l}', CLAY, RT(x + math.cos(b) * 0.6, 1.3, z + math.sin(b) * 0.6) @ RX(math.sin(b) * 0.25) @ RZ(-math.cos(b) * 0.25) @ SC(0.18, 2.7, 0.18))
    GOBLETS.append((x, z))
# --- central stand: white base + gold claws
cyl('Stand0', FLOOR, 0, 0.5, 0, 2.4, 1.0)
cyl('Stand1', plastic_mat('White', (225, 225, 235)), 0, 1.3, 0, 1.7, 0.6)
STAND_GLOW = cyl('StandGlow', neon_mat('N_StandGlow'), 0, 1.66, 0, 1.75, 0.12)
for k in range(4):
    a = k * math.tau / 4 + math.pi / 4
    box(f'Claw{k}', GOLD, RT(math.cos(a) * 1.25, STAND_TOP + 0.1, math.sin(a) * 1.25) @ Matrix.Rotation(-0.3, 4, Vector((math.sin(a), 0, -math.cos(a)))) @ SC(0.2, 2.4, 0.2))

# --- the egg: black, gold bands + gold studs
EGG_O = prim('Egg', 'ball', EGGM)
BANDS = []
for yb, sx in ((-0.95, 0.88), (0.0, 1.0), (0.95, 0.88)):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.045, major_segments=64, minor_segments=8)
    t = bpy.context.active_object
    t.data.materials.append(GOLD)
    BANDS.append((t, yb, sx))
STUDS = []
for col_i in range(8):
    a = col_i * math.tau / 8
    for yv in (-0.6, -0.3, 0.3, 0.6):
        s = prim(f'Stud{col_i}{yv}', 'cube', GOLD)
        STUDS.append((s, a, yv))
TOPKNOB = prim('Knob', 'ball', GOLD)

# --- VFX pools (all in the screen plane at the egg, or round it)
ORBS = [neon_obj(f'SideOrb{k}', 'ball') for k in range(2)]
ORB_CORE = [neon_obj(f'SideCore{k}', 'ball') for k in range(2)]
BOLT_G = [neon_obj(f'BoltG{k}', 'cube') for k in range(140)]   # coloured glow of the lightning
BOLT_C = [neon_obj(f'BoltC{k}', 'cube') for k in range(140)]   # white-hot core
LEAF_OUT = [(0.32 * math.sin(math.pi * u) * (1 - 0.3 * u), u) for u in [i / 10 for i in range(11)]]
LEAF_OUT = LEAF_OUT + [(-x, y) for x, y in reversed(LEAF_OUT[1:-1])]
PETALS = [flat_shape(f'Petal{k}', LEAF_OUT, neon_mat(f'N_Petal{k}')) for k in range(10)]
PETAL_C = [flat_shape(f'PetalC{k}', [(x * 0.45, y * 0.8 + 0.1) for x, y in LEAF_OUT], neon_mat(f'N_PetalC{k}')) for k in range(10)]
SPIKES = [flat_shape(f'Spike{k}', [(-0.2, 0), (0.2, 0), (0.02, 1), (-0.02, 1)], neon_mat(f'N_Spike{k}')) for k in range(18)]
SQUARE = [neon_obj(f'Sq{k}', 'cube') for k in range(4)]
DASH = [ring_xy(f'Dash{k}', 0.985, 1.0, 160, 2) for k in range(3)]
STARL = [neon_obj(f'StarL{k}', 'cube') for k in range(24)]
RAYS = [neon_obj(f'Ray{k}', 'cube') for k in range(20)]
SHARDS = [flat_shape(f'Shard{k}', [(0, -0.5), (0.22, 0), (0, 0.5), (-0.22, 0)], neon_mat(f'N_Shard{k}')) for k in range(26)]
DUST = [neon_obj(f'Dust{k}', 'ball') for k in range(110)]
FLOOD = flat_shape('Flood', [(math.cos(a) * 1, math.sin(a) * 1) for a in [i * math.tau / 48 for i in range(48)]], neon_mat('N_Flood'))
GROUNDRING = ring_xy('GroundRing', 0.97, 1.0, 160)
LABELS = {}
FNT = bpy.data.fonts.load(r'C:\Windows\Fonts\georgiab.ttf')
for name, _, _ in RAR + [RAR6, ('RARITY', 0, 0)]:
    cu = bpy.data.curves.new('L_' + name, 'FONT')
    cu.body = name
    cu.font = FNT
    cu.align_x, cu.align_y = 'CENTER', 'CENTER'
    cu.size = 1.0
    cu.space_character = 1.15
    ob = bpy.data.objects.new('L_' + name, cu)
    sc.collection.objects.link(ob)
    cu.materials.append(neon_mat('NL_' + name))
    LABELS[name] = ob
for m in bpy.data.materials:
    if 'em' in m.keys():
        nstr(m, 3.0)

PET_FIT, PET_OFF = [], []
for p in PETS:
    bb = [Vector(c) for c in p.bound_box]
    lo = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    hi = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    PET_FIT.append(5.0 / max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, 0.5))
    PET_OFF.append(Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)))

# ---- crack events: every one = a new glowing crack on the shell + a crack sound + a jolt (rarer step = bigger crack)
CRACK_EV = []
for _L in range(1, 7):
    _t0 = ST0[_L - 1]
    _d = STEPS[_L - 1]
    CRACK_EV.append((_t0 + 0.02, min(_L, 5)))
    if _L < 6:
        CRACK_EV.append((_t0 + _d * 0.55, 1))
        if _L >= 3:
            CRACK_EV.append((_t0 + _d * 0.82, 2))
    else:
        for _k, _f in enumerate((0.3, 0.5, 0.68, 0.82, 0.93)):
            CRACK_EV.append((_t0 + _d * _f, 2 + min(_k, 3)))
_tc = INTRO + TOT
CRACK_EV += [(_tc, 3), (_tc + 0.2, 3), (_tc + 0.4, 4), (_tc + CHARGE + 0.2, 4), (_tc + CHARGE + 0.5, 5)]
CRACK_EV.sort()


def _egg_local(u, v):
    c = math.sqrt(max(1 - v * v, 0.0))
    return Vector((math.sin(u) * EGG_RX * c, v * EGG_RY, -math.cos(u) * EGG_RX * c))


_cr = random.Random(11)
CRACK_SEGS = []  # (event index, p, q, order inside the event)
_ends = [(0.0, 0.15)]
for _i, (_te, _size) in enumerate(CRACK_EV):
    u, v = _ends[_cr.randrange(len(_ends))] if (_i and _cr.random() < 0.5) else (_cr.uniform(-1.0, 1.0), _cr.uniform(-0.7, 0.75))
    for _b in range(1 + (_size >= 3)):
        uu, vv = u, v
        d = _cr.choice((-1, 1))
        for _k in range(2 + _size):
            u2 = clamp(uu + d * _cr.uniform(0.12, 0.3), -1.35, 1.35)
            v2 = clamp(vv + _cr.uniform(-0.28, 0.28), -0.92, 0.92)
            CRACK_SEGS.append((_i, _egg_local(uu, vv), _egg_local(u2, v2), _k))
            uu, vv = u2, v2
            if _cr.random() < 0.3:
                d = -d
        _ends.append((uu, vv))
        d = -d
CRK_G = [neon_obj(f'CrkG{k}', 'cube') for k in range(len(CRACK_SEGS))]
CRK_C = [neon_obj(f'CrkC{k}', 'cube') for k in range(len(CRACK_SEGS))]
for _m in bpy.data.materials:
    if _m.name.startswith('N_Crk'):
        nstr(_m, 3.0)
(OUT / 'crack_events.json').write_text(json.dumps(CRACK_EV), encoding='utf-8')
# ---- flames in the goblet braziers
FLAMES = []
for _k, (_x, _z) in enumerate(GOBLETS):
    for _j in range(2):
        _o = neon_obj(f'Flame{_k}_{_j}', 'ball')
        nstr(_o.data.materials[0], 3.0)
        FLAMES.append((_o, _x, _z, _j, _k))
# ================================================================ CATHEDRAL (the reveal room, like the end of the clip)
OFF = Vector((300, 0, 0))
CSTONE = plastic_mat('CStone', (168, 150, 126))
CSTONE2 = plastic_mat('CStone2', (128, 112, 94))
CDARK = plastic_mat('CDark', (70, 58, 48))
CARPET = plastic_mat('Carpet', (160, 22, 28))
WAX = plastic_mat('Wax', (240, 232, 210))
BANNER = plastic_mat('Banner', (140, 18, 26))


def cbox(name, mat, x, y, z, sx, sy, sz):
    return box(name, mat, RT(OFF.x + x, y, z) @ SC(sx, sy, sz))


def ccyl(name, mat, x, y, z, r, h):
    return cyl(name, mat, OFF.x + x, y, z, r, h)


cbox('CFloor', CSTONE2, 0, -0.5, -4, 46, 1, 60)
for i in range(-5, 6):
    for j in range(-8, 5):
        if (i + j) % 2 == 0:
            cbox(f'CT{i}_{j}', CSTONE, i * 4, 0.01, j * 4, 4, 0.04, 4)
cbox('Carpet', CARPET, 0, 0.06, -12, 5, 0.06, 36)
cbox('CarpetTrimL', GOLD, -2.6, 0.07, -12, 0.25, 0.06, 36)
cbox('CarpetTrimR', GOLD, 2.6, 0.07, -12, 0.25, 0.06, 36)
for k, (w, h, z) in enumerate(((14, 0.8, 4), (11, 0.8, 4.5), (8, 0.8, 5))):  # altar steps
    cbox(f'Step{k}', CSTONE, 0, 0.4 + k * 0.8, z, w, h, 6 - k)
ALTAR_TOP = 2.4
ccyl('Altar', WAX, 0, ALTAR_TOP + 0.5, 4.5, 2.2, 1.0)
ccyl('AltarRim', GOLD, 0, ALTAR_TOP + 1.02, 4.5, 2.3, 0.12)
ECp = Vector((OFF.x, ALTAR_TOP + 1.1 + 2.4, 4.5))
cbox('BackWall', CSTONE2, 0, 15, 17, 46, 32, 2)
for x in (-9.5, 9.5):  # columns along the nave
    for z in (-20, -12, -4, 4):
        ccyl(f'Col{x}{z}', CSTONE, x, 9, z, 1.1, 18)
        cbox(f'ColCap{x}{z}', CSTONE2, x, 18.4, z, 3, 0.8, 3)
        cbox(f'ColBase{x}{z}', CSTONE2, x, 0.4, z, 2.8, 0.8, 2.8)
for x in (-15, 15):
    cbox(f'SideW{x}', CDARK, x, 13, -6, 2, 26, 50)
for x in (-6.5, 6.5):  # red banners with gold trim
    cbox(f'Ban{x}', BANNER, x * 1.4, 9, 15.9, 3, 9, 0.2)
    cbox(f'BanT{x}', GOLD, x * 1.4, 13.6, 15.85, 3.3, 0.3, 0.25)
    cbox(f'BanS{x}', GOLD, x * 1.4, 9, 15.8, 0.4, 7.6, 0.22)
ROSE_C = Vector((OFF.x, 17.2, 15.85))
GLASS = [(220, 40, 40), (40, 90, 230), (250, 200, 40), (40, 170, 90), (150, 60, 210)]


def sector(name, r0, r1, a0, a1, col):
    vs, fs, n = [], [], 6
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        vs += [(math.cos(a) * r0, math.sin(a) * r0, 0), (math.cos(a) * r1, math.sin(a) * r1, 0)]
    for k in range(n):
        fs.append((2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2))
    o = mesh_rb(name, vs, fs, neon_mat('N_' + name))
    set_neon(o, col, 1)
    nstr(o.data.materials[0], 2.2)
    place(o, RT(ROSE_C.x, ROSE_C.y, ROSE_C.z - 0.02))
    return o


sector('RoseCore', 0, 1.2, 0, math.tau, (255, 230, 150))
for k in range(10):
    sector(f'RoseA{k}', 1.35, 3.2, k * math.tau / 10 + 0.04, (k + 1) * math.tau / 10 - 0.04, GLASS[k % 2])
for k in range(20):
    sector(f'RoseB{k}', 3.35, 5.0, k * math.tau / 20 + 0.03, (k + 1) * math.tau / 20 - 0.03, GLASS[[2, 0, 1, 2, 4][k % 5]])
for k in range(30):
    sector(f'RoseC{k}', 5.15, 6.0, k * math.tau / 30 + 0.03, (k + 1) * math.tau / 30 - 0.03, GLASS[[1, 2, 0][k % 3]])
_rf = ring_xy('RoseFrame', 6.0, 6.7, 96, 0, CSTONE)
place(_rf, RT(ROSE_C.x, ROSE_C.y, ROSE_C.z - 0.05))
GODRAYS = []
for k in range(7):
    o = neon_obj(f'GodRay{k}', 'cube')
    nstr(o.data.materials[0], 1.0)
    GODRAYS.append((o, k))
CANDLES = []
_cpos = [(x, z) for z in (-22, -16, -10, -4) for x in (-5.5, 5.5)] + [(-4.5, 2.5), (4.5, 2.5), (-6, 6), (6, 6), (-3.4, 7), (3.4, 7)]
for k, (x, z) in enumerate(_cpos):
    on_altar = z > 0
    y0 = 2.0
    if not on_altar:
        ccyl(f'CStand{k}', GOLD, x, 1.2, z, 0.12, 2.4)
        ccyl(f'CDish{k}', GOLD, x, 2.4, z, 0.5, 0.1)
        y0 = 2.45
    h = 0.9 + (k % 3) * 0.35
    ccyl(f'Candle{k}', WAX, x, y0 + h / 2, z, 0.22, h)
    fl = neon_obj(f'CFlame{k}', 'ball')
    nstr(fl.data.materials[0], 3.0)
    CANDLES.append((fl, OFF.x + x, y0 + h + 0.25, z, k))
CATH_L = []
for k, (pos, colr, e) in enumerate((((0, 9, 1), (255, 200, 140), 2500), ((0, 16, 12), (255, 220, 170), 12000), ((-5, 4, -14), (255, 160, 80), 500), ((5, 4, -14), (255, 160, 80), 500))):
    l = bpy.data.objects.new(f'CathL{k}', bpy.data.lights.new(f'CathL{k}', 'POINT'))
    l.data.color = lin(colr)[:3]
    l.data.energy = e
    l.data.shadow_soft_size = 2
    l.location = (A @ Vector((OFF.x + pos[0], pos[1], pos[2], 1))).to_3d()
    sc.collection.objects.link(l)
    CATH_L.append(l)
SUNB = [flat_shape(f'Sunb{k}', [(-0.12, 0), (0.12, 0), (0, 1)], neon_mat(f'N_Sunb{k}')) for k in range(28)]
DYN = SUNB + CRK_G + CRK_C + ORBS + ORB_CORE + BOLT_G + BOLT_C + PETALS + PETAL_C + SPIKES + SQUARE + DASH + STARL + RAYS + SHARDS + DUST + [FLOOD, GROUNDRING] + list(LABELS.values()) + PETS
EGG_PARTS = [EGG_O, TOPKNOB] + [b[0] for b in BANDS] + [s[0] for s in STUDS]
DUSTS = [dict(x=random.uniform(-16, 16), y=random.uniform(0, 18), z=random.uniform(-6, 10), sp=random.uniform(0.3, 1.2), ph=random.uniform(0, 9), s=random.uniform(0.05, 0.13)) for _ in range(110)]


def egg_surf(u, v, grow=1.0):  # point on the egg (u: around, 0 = facing the camera; v: -1 bottom .. 1 top)
    c = math.sqrt(max(1 - v * v, 0.0))
    return EC + Vector((math.sin(u) * EGG_RX * c * grow, v * EGG_RY * grow, -math.cos(u) * EGG_RX * c * grow))


def bar(o, p, q, w):
    place(o, look_at((p + q) / 2, q) @ SC(w, w, (p - q).length + w * 0.6))


CEN = [EC]


def scr(o, x, y, rot, sx, sy, z=-2.2):  # place a flat screen-plane shape round the current centre
    c = CEN[0]
    place(o, RT(c.x + x, c.y + y, c.z + z) @ RZ(rot) @ SC(sx, sy, 1))


# ================================================================ one frame
def frame(t):
    for o in DYN:
        o.hide_render = True
    CEN[0] = EC
    L = 0 if t < INTRO else max(i + 1 for i in range(6) if t >= ST0[i])
    age = (t - ST0[L - 1]) if L else 0
    popped = t >= T_POP
    pa = t - T_POP
    t_white = INTRO + TOT + CHARGE
    whiten = clamp((t - t_white) / WHITE_T) if not popped else 1
    col = (255, 255, 255) if (popped or whiten > 0.5) else ((200, 210, 255) if L == 0 else RAR[L - 1][2] if L <= 5 else
           tuple(int(c * 255) for c in colorsys.hsv_to_rgb((t * 0.45) % 1, 0.55, 1)))
    hit = math.exp(-age * 6) if L and not popped else 0
    build = clamp((t - INTRO) / (TOT + CHARGE))
    meta = dict(sd=(STEPS[L - 1] if L else 0), t=t, L=L, age=age, popped=popped, pa=pa, whiten=whiten, col=col, build=build)

    # camera: walks up to the egg in the intro, then slow push-in, shake grows; after the pop a slow drift
    rnd = random.Random(int(t * 300))
    p_far, p_near = Vector((0, 7.0, -32)), Vector((0, 6.2, -21))
    pos = p_far.lerp(p_near, eo(t / 2.2))
    if L >= 1:
        pos = pos.lerp(Vector((0, 6.0, -15.5)), eo(build) * 0.8)
    if popped:
        pos = Vector((0, 6.0, -18)).lerp(Vector((0, 5.6, -15.5)), eo(pa / 4))
    kick = sum(min(sz, 4) * math.exp(-(t - te) * 16) for te, sz in CRACK_EV if 0 <= t - te < 0.5) * (0 if popped else 1)
    sh = (0.03 + 0.12 * build ** 2) * (1 - 0.7 * popped) + (0.6 * math.exp(-pa * 6) if popped else 0) + 0.06 * kick
    pos = pos + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)) * sh * 0.5
    cam.matrix_world = A @ look_at(pos, Vector((0, EC.y - 1.1, 0)))
    cam.data.angle = math.radians(56 - 0.5 * kick)
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = (pos - Vector((0, EC.y, 0))).length
    cam.data.dof.aperture_fstop = 2.2
    for o, x, z, j, k in FLAMES:  # brazier flames flicker, take a little of the rarity colour
        fl = 0.75 + 0.25 * math.sin(t * (11 + k) + j * 2) + 0.1 * math.sin(t * 23 + k)
        s = (0.5 if j == 0 else 0.28) * fl * (1 + 0.2 * build)
        set_neon(o, mixc((255, 120, 30) if j == 0 else (255, 200, 90), col, 0.4 * build), 0.75)
        place(o, RT(x, 3.75 + j * 0.45 + 0.08 * math.sin(t * 9 + k), z) @ SC(s, s * 1.6, s))

    # lights / world
    EL.location = (A @ Vector((EC.x, EC.y, EC.z - 2.5, 1))).to_3d()
    EL.data.color = lin(col)[:3]
    EL.data.energy = (120 + 900 * build + 2000 * hit) if not popped else 1500 * math.exp(-pa * 2) + 220
    BL.data.color = lin(col)[:3]
    BL.data.energy = (0 if L == 0 else 30000 * (0.2 + 0.8 * hit) * (0.6 if L >= 4 else 1)) if not popped else 25000 * math.exp(-pa * 1.5) + 4000
    BG.inputs[1].default_value = 1.0
    STAND_GLOW.hide_render = False
    set_neon(STAND_GLOW, col, 0.1 + 0.35 * build)
    set_neon(RIM, col, 0.3 + 0.6 * build + 0.3 * hit)

    # floating dust / star sparkles everywhere (denser as it builds)
    nd = int(25 + 80 * build) if not popped else 110
    for k, d in enumerate(DUSTS[:nd]):
        o = DUST[k]
        o.hide_render = False
        y = (d['y'] + t * d['sp']) % 18
        tw = 0.5 + 0.5 * math.sin(t * 6 + d['ph'])
        set_neon(o, (255, 214, 140) if (popped and pa >= 0.3) else mixc((255, 255, 255), col, 0.4), 0.35 + 0.65 * tw)
        s = d['s'] * (0.6 + 0.6 * tw)
        cx = OFF.x if (popped and pa >= 0.3) else 0
        place(o, RT(cx + d['x'] + math.sin(t * 0.5 + d['ph']) * 0.6, y, d['z']) @ SC(s, s, s))

    # colour flood behind the egg at every step (like the blue / purple fog in the clip)
    if False:
        FLOOD.hide_render = False
        set_neon(FLOOD, col, (0.04 + 0.3 * hit) * (0.6 if L >= 4 else 1))
        fs = 8 + 8 * (1 - hit)
        place(FLOOD, RT(EC.x, EC.y, 6) @ SC(fs * 1.4, fs, 1))

    # rarity name on the floor in front of the stand + small RARITY above it
    if L and not popped and whiten < 0.5:
        name = RAR[L - 1][0] if L <= 5 else '???'
        k = 1 + 0.5 * math.exp(-age * 10)
        for nm, yy, s0 in ((name, 1.15, 0.6), ('RARITY', 1.78, 0.25)):
            ob = LABELS[nm]
            ob.hide_render = False
            set_neon(ob, col if nm != 'RARITY' else (220, 220, 230), 1)
            ob.matrix_world = A @ RT(0, yy, -2.65) @ AI @ Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Rotation(math.pi / 2, 4, 'X') @ Matrix.Scale(s0 * k, 4)
        GROUNDRING.hide_render = False
        gr = 2.5 + 12 * eo(age / 0.9)
        set_neon(GROUNDRING, col, clamp(1 - age / 0.9))
        place(GROUNDRING, RT(0, 0.1, 0) @ RX(math.pi / 2) @ SC(gr, gr, 1))

    if not popped:
        # ---------------- the egg: floats a touch, rocks, shakes hard at the end, turns white before the pop
        bob = 0.12 * math.sin(t * 2.2)
        shake = build ** 2 * 0.12 + 0.05 * hit + 0.25 * whiten
        ox, oy = rnd.uniform(-1, 1) * shake, rnd.uniform(-1, 1) * shake * 0.5
        jolt = sum(math.exp(-(t - te) * 18) * (1 if i % 2 else -1) * min(sz, 4) for i, (te, sz) in enumerate(CRACK_EV) if 0 <= t - te < 0.4)
        tilt = math.sin(t * 2.0) * 0.05 + math.sin(t * 31) * 0.05 * build ** 2 + 0.035 * jolt
        sw = 1 + 0.02 * hit + 0.1 * whiten + 0.012 * abs(jolt)
        Mg = RT(ox, bob + oy, 0) @ RT(*EC) @ RZ(tilt) @ RY(0.12 * math.sin(t * 0.6))
        for o in EGG_PARTS:
            o.hide_render = False
        place(EGG_O, Mg @ SC(EGG_RX * 2 * sw, EGG_RY * 2 * sw, EGG_RX * 2 * sw))
        for tor, yb, sx in BANDS:  # torus mesh lies in Blender XY = Roblox ground plane
            rr = EGG_RX * sw * math.sqrt(max(1 - (yb / EGG_RY) ** 2, 0)) * 1.01
            tor.matrix_world = A @ (Mg @ RT(0, yb * sw, 0)) @ AI @ Matrix.Scale(rr, 4)
        for s, a, yv in STUDS:
            c = math.sqrt(max(1 - yv * yv, 0)) * EGG_RX * sw * 1.01
            place(s, Mg @ RT(math.sin(a) * c, yv * EGG_RY * sw, -math.cos(a) * c) @ RY(-a) @ RZ(math.pi / 4) @ SC(0.12, 0.12, 0.05))
        place(TOPKNOB, Mg @ RT(0, EGG_RY * sw + 0.05, 0) @ SC(0.35, 0.35, 0.35))
        ccol = mixc(col, (255, 255, 255), 0.6)
        for n_, (ei, p_, q_, order) in enumerate(CRACK_SEGS):
            te = CRACK_EV[ei][0]
            g = clamp((t - te - order * 0.02) / 0.05)
            if g <= 0:
                continue
            P = (Mg @ (p_ * sw * 1.012).to_4d()).to_3d()
            Q = (Mg @ ((p_ + (q_ - p_) * g) * sw * 1.012).to_4d()).to_3d()
            fresh = math.exp(-(t - te) * 5)
            for pool, w, cc, aa in ((CRK_G, 0.16 + 0.14 * fresh, col, 0.55 + 0.4 * fresh), (CRK_C, 0.05 + 0.02 * fresh, ccol, 1)):
                o = pool[n_]
                o.hide_render = False
                set_neon(o, cc, aa)
                bar(o, P, Q, w)
        _EGG_EM.default_value = (1, 1, 1, 1)
        _EGG_ES.default_value = 6 * whiten ** 1.5

        if L:
            # two glowing orbs at the egg's sides
            for k, sgn in enumerate((-1, 1)):
                for o, s, a in ((ORBS[k], 0.75 + 0.35 * hit, 0.55), (ORB_CORE[k], 0.32, 1)):
                    o.hide_render = False
                    set_neon(o, col if o in ORBS else (255, 255, 255), a)
                    place(o, RT(EC.x + sgn * (EGG_RX + 0.35) + ox, EC.y + bob, EC.z - 0.4) @ SC(s, s, s))
            # (no lightning / currents: only the cracks on the shell)
            # expanding dashed circle at every step
            if age < 1.0:
                o = DASH[0]
                o.hide_render = False
                r = 3 + 9 * eo(age / 1.0)
                set_neon(o, (255, 255, 255), clamp(1 - age))
                place(o, RT(EC.x, EC.y, EC.z - 1.5) @ RZ(t * 0.6) @ SC(r, r, 1))
        # EPIC: light petals round the egg; LEGENDARY: more petals + golden spike crown + a turning square
        if L >= 4 and whiten < 1:
            n_p = 6 if L == 4 else 10
            g = back_out(age / 0.45) if (L == 4 or (L == 5 and age < 0.45)) else 1
            for k in range(n_p):
                a = k * math.tau / n_p + t * 0.5
                R = (EGG_RY + 0.1) * g
                for o, sc_, cc in ((PETALS[k], 1.3, col), (PETAL_C[k], 1.3, (255, 255, 255))):
                    o.hide_render = False
                    set_neon(o, cc, 1 - whiten)
                    scr(o, math.cos(a) * R * 0.85, math.sin(a) * R, a - math.pi / 2, sc_ * g, sc_ * g, z=-1.6 if o in PETALS else -1.65)
        if L >= 5 and whiten < 1:
            g = back_out(age / 0.5) if L == 5 else 1
            for k in range(18):
                o = SPIKES[k]
                o.hide_render = False
                a = k * math.tau / 18 - t * 0.35
                R = 2.7 * g
                ln = (1.6 if k % 2 == 0 else 1.0) * g
                set_neon(o, mixc(col, (255, 255, 255), 0.15 * (k % 2)), 1 - whiten)
                scr(o, math.cos(a) * R * 0.95, math.sin(a) * R * 1.1, a - math.pi / 2, 1.2 * g, ln, z=-1.4)
            sq = 2.6 * g
            rot = t * 0.7
            corners = [Vector((math.cos(rot + i * math.pi / 2) * sq, math.sin(rot + i * math.pi / 2) * sq, 0)) for i in range(4)]
            for i in range(4):
                o = SQUARE[i]
                o.hide_render = False
                set_neon(o, (255, 255, 255), 0.9 * (1 - whiten))
                p, q = corners[i] + EC + Vector((0, 0, -2.0)), corners[(i + 1) % 4] + EC + Vector((0, 0, -2.0))
                bar(o, p, q, 0.05)
    else:
        # ---------------- POP: burst at the egg, the screen goes white, and when it clears we are in the CATHEDRAL:
        # the burst finishes on the altar, the pet rises out of the light under the rose window, god rays, sunburst
        for o in EGG_PARTS:
            o.hide_render = True
        cath = pa >= 0.3
        BC = ECp if cath else EC
        CEN[0] = BC
        bt = pa if not cath else pa - 0.3
        if cath:
            q = pa - 0.3
            cp = OFF + Vector((0, 4.2, -21)).lerp(Vector((0, 5.6, -13.5)), eo(q / 4.5))
            cp = cp + Vector((math.sin(q * 0.6) * 0.6, 0, 0))
            cam.matrix_world = A @ look_at(cp, OFF + Vector((0, 6.2 + 1.2 * eo(q / 4.5), 4)))
            cam.data.angle = math.radians(58)
            cam.data.dof.focus_distance = (cp - ECp).length
            cam.data.dof.aperture_fstop = 2.8
            BG.inputs[0].default_value = lin((30, 22, 16))
            BG.inputs[1].default_value = 1.0
            for o, x, y, z, k in CANDLES:
                fl = 0.8 + 0.2 * math.sin(t * (10 + k % 5) + k)
                set_neon(o, (255, 170, 70), 0.9)
                place(o, RT(x, y + 0.03 * math.sin(t * 13 + k), z) @ SC(0.32 * fl, 0.55 * fl, 0.32 * fl))
            for o, k in GODRAYS:
                ln = 26
                set_neon(o, (255, 225, 160), 0.07 + 0.03 * math.sin(t * 0.8 + k))
                o.hide_render = False
                place(o, RT(ROSE_C.x + (k - 3) * 1.2, ROSE_C.y, ROSE_C.z) @ RX(-0.62) @ RZ((k - 3) * 0.07) @ RT(0, -ln / 2, 0) @ SC(1.2 + 0.3 * (k % 2), ln, 0.4))
            for l in CATH_L:
                l.hide_render = False
            CATH_L[0].data.energy = 2500 + 12000 * math.exp(-q * 2.5)
        else:
            for l in CATH_L:
                l.hide_render = True
        if bt < 1.8:
            u = bt / 1.8
            g = eo(bt / 0.35)
            pts = [Vector((math.cos(i * math.tau / 12 + bt * 0.4) * 6.5 * g, math.sin(i * math.tau / 12 + bt * 0.4) * 6.5 * g, 0)) for i in range(12)]
            for i in range(12):
                o = STARL[i]
                o.hide_render = False
                set_neon(o, (255, 236, 150) if i % 2 else (255, 255, 255), clamp(1.3 - u))
                bar(o, pts[i] + BC + Vector((0, 0, -1.8)), pts[(i + 5) % 12] + BC + Vector((0, 0, -1.8)), 0.1)
            for k in range(2):
                o = DASH[k]
                o.hide_render = False
                r = (7.2 + 1.2 * k) * g + 3 * u
                set_neon(o, (255, 255, 255) if k == 0 else (255, 220, 120), clamp(1.2 - u))
                place(o, RT(BC.x, BC.y, BC.z - 1.7) @ RZ(bt * (0.5 - k)) @ SC(r, r, 1))
            for k in range(20):
                o = RAYS[k]
                o.hide_render = False
                a = k * math.tau / 20 + 0.1
                ln = 3 + 18 * eo(bt / 0.5)
                set_neon(o, (255, 255, 255) if k % 2 else (255, 240, 170), clamp(1 - u) * 0.8)
                place(o, RT(BC.x, BC.y, BC.z - 1.9) @ RZ(a) @ RT(0, 1.5 + ln / 2, 0) @ SC(0.1 * (1 - u) + 0.03, ln, 0.05))
            sr = random.Random(9)
            for k in range(26):
                o = SHARDS[k]
                o.hide_render = False
                a = sr.uniform(0, math.tau)
                d = sr.uniform(6, 13) * bt
                set_neon(o, (255, 255, 255) if k % 3 else (255, 220, 120), clamp(1.2 - u))
                scr(o, math.cos(a) * d, math.sin(a) * d - 2.5 * bt * bt, a - math.pi / 2 + bt * sr.uniform(-4, 4), 0.8, 0.8, z=-2.4)
        if cath:
            q = pa - 0.3
            for k in range(28):
                o = SUNB[k]
                o.hide_render = False
                a = k * math.tau / 28 + q * 0.15
                R = 2.6 * eo(q / 0.8)
                ln = (5.5 if k % 2 == 0 else 3.4) * eo(q / 1.0)
                set_neon(o, (255, 214, 110) if k % 2 == 0 else (255, 245, 210), 0.55)
                scr(o, math.cos(a) * R, math.sin(a) * R + 0.4, a - math.pi / 2, 1.6, max(ln, 0.01), z=2.2)
            for k in range(18):
                o = SPIKES[k]
                o.hide_render = False
                a = k * math.tau / 18 - q * 0.3
                R = 3.3 * eo(q / 0.7)
                set_neon(o, (255, 205, 60), 0.85)
                scr(o, math.cos(a) * R, math.sin(a) * R + 0.4, a - math.pi / 2, 0.9, 1.3 if k % 2 == 0 else 0.8, z=1.8)
            pet = PETS[4]
            pet.hide_render = False
            g = back_out((q - 0.05) / 0.7) if q > 0.05 else 0.01
            kk = PET_FIT[4] * 1.25 * max(g, 0.01)
            rise = 1.6 * (1 - eo(q / 1.1))
            spin = math.pi * 2 * (1 - eo(q / 1.6)) + 0.22 * math.sin(q * 1.3) * clamp(q - 1.6)
            breathe = 0.08 * math.sin(q * 2.4) * clamp(q - 1.2)
            pet.matrix_world = (A @ RT(OFF.x, ALTAR_TOP + 1.1 + rise + breathe, 4.5) @ AI) @ Matrix.Rotation(spin, 4, 'Z') @ Matrix.Scale(kk, 4) @ Matrix.Translation(-PET_OFF[4])
    return meta


metas = []
nf = int(round(END * FPS))
want = [float(x) for x in TIMES.split(',')] if TIMES else None
for f in range(nf):
    t = f / FPS
    if want is not None:
        if not any(abs(t - w) < 0.5 / FPS for w in want):
            continue
    elif f % EVERY:
        continue
    m = frame(t)
    m.update(f=f, end=END, name=PET_NAMES[4])
    metas.append(m)
    sc.render.filepath = str(OUT / f'f{f:04d}.png')
    bpy.ops.render.render(write_still=True)
(OUT / 'meta.json').write_text(json.dumps(metas), encoding='utf-8')
print('frames', nf)
