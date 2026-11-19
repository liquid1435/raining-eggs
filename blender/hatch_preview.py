"""3D layer of the hatch-show preview (same motion as the game's runReveal), 5 demos Common..Legendary.
  blender -b -P hatch_preview.py -- [every=N] [only=K]
-> out/hp3d/f0000.png ... (transparent), then: py hatch_overlay.py"""
import bpy, bmesh, math, sys, pathlib
from mathutils import Matrix, Vector

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hatch_tl as TL

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
EVERY = int(next((a.split('=')[1] for a in ARGS if a.startswith('every=')), 1))
ONLY = int(next((a.split('=')[1] for a in ARGS if a.startswith('only=')), 0))
OUT = HERE / 'out' / 'hp3d'
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- the new egg (textures already made by gen_eggs2.py)
src = (HERE / 'gen_eggs2.py').read_text(encoding='utf-8')
src = src.replace("    def texture(self, name):\n", """    def texture(self, name):
        p = HERE / 'out' / 'eggtex' / f'{name}.png'
        if p.exists():
            img = bpy.data.images.load(str(p))
            m = bpy.data.materials.new('M_' + name)
            m.use_nodes = True
            b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
            b.inputs['Roughness'].default_value = 0.32
            tn = m.node_tree.nodes.new('ShaderNodeTexImage')
            tn.image = img
            m.node_tree.links.new(tn.outputs['Color'], b.inputs['Base Color'])
            return m
""", 1)
sys.argv = [sys.argv[0], '--', 'nofbx', 'norender']
g = {'__file__': str(HERE / 'gen_eggs2.py'), '__name__': 'eggs'}
exec(compile(src, 'gen_eggs2.py', 'exec'), g)
for o in list(bpy.data.objects):
    if o.name != 'Egg_1':
        bpy.data.objects.remove(o, do_unlink=True)
EGG = bpy.data.objects['Egg_1']

# ---------------------------------------------------------------- the five Sunny Meadow pets (gen_assets builder)
src = (HERE / 'gen_assets.py').read_text(encoding='utf-8')
src = src[:src.index('# ---------------------------------------------------------------- scene')]
ga = {'__file__': str(HERE / 'gen_assets.py'), '__name__': 'ga'}
sys.argv = [sys.argv[0], '--', 'nofbx']
exec(compile(src, 'gen_assets.py', 'exec'), ga)
MAT = bpy.data.materials.new('VertexColour')
MAT.use_nodes = True
_b = next(n for n in MAT.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
_a = MAT.node_tree.nodes.new('ShaderNodeVertexColor')
_a.layer_name = 'Col'
MAT.node_tree.links.new(_a.outputs['Color'], _b.inputs['Base Color'])
_b.inputs['Roughness'].default_value = 0.55
ga['MAT'] = MAT
PETS, PET_NAMES = [], []
for pi, (name, c, a, ears, kind) in enumerate(ga['ZONES'][0]['pets'][:5]):
    PETS.append(ga['build_pet'](name, c, a, ears, kind).finish(f'Pet_1_{pi + 1}', 0, 0))
    PET_NAMES.append(name)
(OUT / 'names.txt').write_text('\n'.join(PET_NAMES), encoding='utf-8')

# ---------------------------------------------------------------- helpers: Roblox coords -> Blender
A = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
AI = A.inverted()


def RT(x, y, z):
    return Matrix.Translation((x, y, z))


def RX(a):
    return Matrix.Rotation(a, 4, 'X')


def RY(a):
    return Matrix.Rotation(a, 4, 'Y')


def RZ(a):
    return Matrix.Rotation(a, 4, 'Z')


def SC(x, y, z):
    return Matrix.Diagonal((x, y, z, 1))


def look_at(p, target):
    d = (Vector(target) - Vector(p)).normalized()
    z = -d
    up = Vector((0, 1, 0)) if abs(d.y) < 0.99 else Vector((1, 0, 0))
    x = up.cross(z).normalized()
    y = z.cross(x)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = Vector(p)
    return m


def place(ob, mr):
    ob.matrix_world = A @ mr @ AI


def lin(c):
    f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (f(c[0] / 255), f(c[1] / 255), f(c[2] / 255), 1.0)


def neon_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    em = nt.nodes.new('ShaderNodeEmission')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    for attr, val in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    m['em'], m['mx'] = em.name, mx.name
    return m


def set_neon(ob, col, alpha):
    m = ob.data.materials[0]
    m.node_tree.nodes[m['em']].inputs['Color'].default_value = lin(col)
    m.node_tree.nodes[m['mx']].inputs['Fac'].default_value = max(0.0, min(1.0, alpha))


def plastic_mat(name, col):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = lin(col)
    b.inputs['Roughness'].default_value = 0.5
    return m


def prim(name, kind, mat):
    bm = bmesh.new()
    if kind == 'cube':
        bmesh.ops.create_cube(bm, size=1)
    elif kind == 'ball':
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=0.5)
    elif kind == 'cylx':  # Roblox cylinder: axis along local X
        bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=0.5, radius2=0.5, depth=1, matrix=Matrix.Rotation(math.pi / 2, 4, 'Y'))
    for f in bm.faces:
        f.smooth = kind != 'cube'
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


def neon_obj(name, kind):
    return prim(name, kind, neon_mat('N_' + name))


# ---------------------------------------------------------------- scene (the hatch ViewportFrame)
sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
try:
    sc.eevee.taa_render_samples = 24
except Exception:
    pass
sc.view_settings.view_transform = 'Standard'
sc.render.film_transparent = True
sc.render.resolution_x, sc.render.resolution_y = 1040, 876
w = bpy.data.worlds.new('W')
sc.world = w
w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs[0].default_value = lin((175, 165, 205))
bg.inputs[1].default_value = 0.85
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
sun.data.energy = 2.6
sun.data.angle = math.radians(12)
d = (A @ Vector((0.4, -1, 0.8, 0))).to_3d().normalized()
sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
sc.collection.objects.link(sun)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.sensor_fit = 'VERTICAL'
CAM_P, CAM_T = Vector((0, 4.4, -15)), Vector((0, 2.5, 0))

# stand
stand = prim('Stand', 'cylx', plastic_mat('Stand', (196, 178, 250)))
place(stand, RT(0, -0.3, 0) @ RZ(math.pi / 2) @ SC(0.6, 7.4, 7.4))
ring0 = neon_obj('StandRing', 'cylx')
set_neon(ring0, (255, 255, 255), 1)
place(ring0, RT(0, -0.33, 0) @ RZ(math.pi / 2) @ SC(0.5, 8, 8))

# egg size like eggMesh(): height = EGG_H
EGG_SC = TL.EGG_H / EGG.dimensions.z
EGG_W = EGG.dimensions.x * EGG_SC
aura = neon_obj('Aura', 'ball')
# cracks (makeCracks)
pts, n = [], 11
for k in range(n + 1):
    a = math.radians(200 + 140 * k / n)
    dy = TL.EGG_H * 0.06 + (0.22 if k % 2 == 0 else -0.22)
    r = EGG_W / 2 * math.sqrt(max(1 - (dy / (TL.EGG_H / 2)) ** 2, 0.05)) * 1.03
    pts.append(Vector((math.cos(a) * r, dy, math.sin(a) * r)))
segs = []
for k in range(n):
    segs.append((pts[k], pts[k + 1]))
    for bk, bdy in ((3, 0.7), (6, -0.6), (8, 0.8), (10, -0.5)):
        if bk == k + 1:
            p = pts[k + 1 - 1] if False else pts[k]
            segs.append((p, Vector((p.x * 0.93, p.y + bdy, p.z * 0.93 - 0.05))))
CRACKS = []
for i, (p, q) in enumerate(segs):
    ob = neon_obj(f'Crack{i}', 'cube')
    CRACKS.append((ob, look_at((p + q) * 0.5, q), (p - q).length + 0.1))
BEAMS = [neon_obj(f'Beam{i}', 'cube') for i in range(8)]
ORBS = [neon_obj(f'Orb{i}', 'ball') for i in range(40)]
RINGS = [neon_obj(f'Ring{i}', 'cylx') for i in range(4)]
CHIP_MATS = {'egg': plastic_mat('ChipEgg', (250, 240, 214)), 'white': plastic_mat('ChipWhite', (255, 255, 255))}
CHIPS = []
for i in range(42):
    CHIPS.append(prim(f'Chip{i}', 'cube', CHIP_MATS['egg'].copy()))
STARCHIP = [neon_obj(f'Star{i}', 'cube') for i in range(42)]
halo = neon_obj('Halo', 'ball')

# pets: fit and bottom-centre offset
PET_FIT, PET_OFF = [], []
for p in PETS:
    bb = [Vector(c) for c in p.bound_box]
    lo = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    hi = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    PET_FIT.append(TL.HV['petSize'] / max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, 0.5))
    PET_OFF.append(Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)))


def hide(obs, h=True):
    for o in obs:
        o.hide_render = h


def frame(demo, t):
    i = demo.i
    tr = demo.tier
    rar_col = TL.RARITY[i - 1][2]
    hide([EGG, aura, halo] + [c[0] for c in CRACKS] + BEAMS + ORBS + RINGS + CHIPS + STARCHIP + PETS)
    # camera
    pos = CAM_P
    if tr.get('orbit') and t >= demo.P:
        pos = (RY(math.sin(t * 0.9) * 0.45) @ CAM_P.to_4d()).to_3d()
    cm = look_at(pos, CAM_T)
    cam.matrix_world = A @ cm
    cam.data.angle_y = math.radians(demo.fov(t))
    e = demo.egg(t)
    lv = demo.level(t)
    aura_col = (255, 244, 190) if lv == 1 else TL.RARITY[lv - 1][2]
    if e:
        s = e['scale']
        base = RT(0, e['hop'] + e['lift'], 0) @ RZ(e['tilt']) @ RT(0, TL.EGG_H * s / 2, 0)
        EGG.hide_render = False
        EGG.matrix_world = A @ (base @ RY(e['yaw']) @ RT(0, -TL.EGG_H * s / 2, 0)) @ AI @ Matrix.Scale(EGG_SC * s, 4)
        aura.hide_render = e['aura'] <= 0.001
        set_neon(aura, aura_col, 0.6 * e['aura'])
        a_sz = EGG_W * s * (1.02 + 0.35 * e['aura'] + 0.05 * math.sin(t * 20) * e['aura'])
        place(aura, base @ RT(0, 0, 0.9 * s) @ SC(a_sz, a_sz, a_sz))
        c = e['crack'] * len(CRACKS)
        crack_col = tuple(int(x + (255 - x) * 0.55) for x in aura_col)
        for k, (ob, cf, ln) in enumerate(CRACKS):
            if c >= k + 1:
                ob.hide_render = False
                set_neon(ob, crack_col, 1)
                m = cf.copy()
                m.translation = cf.translation * s
                place(ob, base @ m @ SC(0.14 * s, 0.14 * s, ln * s))
        centre = (base @ Vector((0, 0, 0, 1))).to_3d()
        for k in range(tr['beams']):
            ob = BEAMS[k]
            ob.hide_render = False
            set_neon(ob, aura_col, 0.5 * e['aura'])
            place(ob, RT(*centre) @ RY(k * math.tau / tr['beams'] + t * 1.4) @ RT(0, 0, 4.4) @ RX(0.2) @ SC(0.22, 11, 0.22))
        for k, o in enumerate(demo.orbs):
            u = (t - o['t0']) / o['dur']
            if 0 <= u < 1:
                ob = ORBS[k]
                ob.hide_render = False
                ocol = TL.RARITY[demo.level(o['t0']) - 1][2] if demo.level(o['t0']) > 1 else (255, 244, 190)
                set_neon(ob, ocol, 1)
                dv = (RY(u * 3) @ Vector((*o['d'], 0))).to_3d() * (1 - u) ** 1.5
                sz = 0.25 + 0.35 * (1 - u)
                place(ob, RT(*(centre + dv)) @ SC(sz, sz, sz))
    else:
        dt = t - demo.P
        sw = 1.3 if i >= 4 else 1.18
        ey = tr['float'] + TL.EGG_H * sw / 2
        for k in range(tr['rings']):
            life = dt - k * 0.12
            if 0 <= life <= 0.65:
                u = life / 0.65
                dd = 1 + 22 * (1 - (1 - u) ** 3)
                ob = RINGS[k]
                ob.hide_render = False
                set_neon(ob, rar_col if k % 2 == 0 else (255, 255, 255), 1 - (0.45 + 0.55 * u))
                place(ob, RT(0, ey - 0.6 + k * 0.5, 0) @ RZ(math.pi / 2) @ SC(0.15, dd, dd))
        if dt <= 0.9:
            for k, ch in enumerate(demo.chips):
                p0 = Vector((0, ey, 0))
                v = Vector(ch['v'])
                pos_ = p0 + v * dt + Vector((0, -19 * dt * dt, 0))
                rot = RX(ch['a']) @ RY(ch['a'] * 2) @ RZ(ch['a']) @ RX(ch['r'][0] * dt) @ RY(ch['r'][1] * dt) @ RZ(ch['r'][2] * dt)
                alpha = 1 - min(max((dt - 0.5) / 0.4, 0), 1)
                m = RT(*pos_) @ rot @ SC(ch['s'], ch['s'] * 0.5, ch['s'])
                if ch['kind'] == 'star':
                    ob = STARCHIP[k]
                    set_neon(ob, rar_col, alpha)
                else:
                    ob = CHIPS[k]
                    b = next(nd for nd in ob.data.materials[0].node_tree.nodes if nd.type == 'BSDF_PRINCIPLED')
                    b.inputs['Base Color'].default_value = lin((255, 255, 255) if ch['kind'] == 'white' else (250, 240, 214))
                    b.inputs['Alpha'].default_value = alpha
                    try:
                        ob.data.materials[0].surface_render_method = 'BLENDED'
                    except Exception:
                        pass
                ob.hide_render = alpha <= 0.01
                place(ob, m)
        pt = demo.pet(t)
        pet = PETS[i - 1]
        pet.hide_render = False
        kk = PET_FIT[i - 1] * pt['k']
        off = PET_OFF[i - 1]
        # Blender-space: pet faces +Y (= towards the camera)
        pet.matrix_world = (A @ RT(0, pt['y'], 0) @ AI) @ Matrix.Rotation(pt['spin'], 4, 'Z') @ Matrix.Scale(kk, 4) @ Matrix.Translation(-off)
        if tr.get('glow'):
            halo.hide_render = False
            set_neon(halo, rar_col, 0.28)
            hs = max(TL.HV['petSize'] * (1.25 + 0.08 * math.sin(t * 5)) * min(pt['k'], 1.2), 0.05)
            place(halo, RT(0, pt['y'] + TL.HV['petSize'] * 0.45, 2.5) @ SC(hs, hs, hs))


# ---------------------------------------------------------------- render all frames
f = 0
for i in range(1, 6):
    demo = TL.Demo(i)
    nf = int(round(demo.dur * TL.FPS))
    for j in range(nf):
        if (ONLY and ONLY != i) or f % EVERY:
            f += 1
            continue
        t = j / TL.FPS
        frame(demo, t)
        sc.render.filepath = str(OUT / f'f{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        f += 1
print('frames', f)
