r"""Voxel pets v3: real proportions (long legs, jaws, muscles) + a stud texture on every face (the "pixel" look).
  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P gen_voxel_pets3.py -- preview
"""
import bpy, bmesh, math, sys, pathlib, hashlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gen_voxel_pets2 as V2
from gen_voxel_pets2 import Vox, eyes, INK, WHITE, sh, recolor, DIRS

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'out'
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
S = V2.S
STUD = 2          # voxels per stud tile


def saber_tiger():
    v = Vox()
    G, Gd, L, St = (246, 150, 52), (200, 110, 36), (255, 238, 214), (52, 36, 40)
    v.ell(0, 1, 13, 5.2, 11, 5.0, G)                                          # torso
    v.ell(0, -6, 13.5, 6.0, 5.5, 6.0, G)                                       # big chest
    v.ell(0, 9, 13.5, 5.4, 5, 5.4, G)                                          # hips
    v.paint(lambda X, Y, Z, o: Z < 10.2, L)                                    # light belly
    for sx in (-1, 1):
        v.ell(sx * 3.9, -6.5, 10, 2.3, 2.8, 3.6, G)                             # shoulders
        v.line((sx * 3.9, -7, 9), (sx * 3.9, -8, 1.6), lambda t: 1.9 - 0.4 * t, G)
        v.box(sx * 3.9 - 1.8, -10.4, 0, sx * 3.9 + 1.8, -6.6, 1.6, L)           # front paws
        v.ell(sx * 3.7, 9.5, 11, 2.4, 3.8, 4.2, G)                              # thighs
        v.line((sx * 3.8, 11, 8), (sx * 3.8, 9.5, 1.6), lambda t: 1.6 - 0.3 * t, G)
        v.box(sx * 3.8 - 1.6, 7.0, 0, sx * 3.8 + 1.6, 10.6, 1.6, L)
    v.line((0, -9, 15), (0, -12.5, 17), 3.6, G)                                # neck
    v.ell(0, -14, 17.5, 4.8, 5.0, 4.4, G)                                      # head
    v.box(-3.0, -21, 14.6, 3.0, -16, 18.0, G)                                  # muzzle
    v.box(-2.9, -21.2, 16.6, 2.9, -18, 18.2, L)                                # light upper lip
    v.box(-1.2, -21.6, 17.2, 1.2, -20.8, 18.4, INK)                            # nose
    v.box(-2.5, -20, 12.4, 2.5, -15.5, 14.2, Gd)                               # lower jaw
    v.box(-2.6, -20.4, 14.2, 2.6, -15.5, 14.6, (150, 40, 60))                  # mouth line
    for sx in (-1, 1):
        v.line((sx * 1.9, -19.6, 14.4), (sx * 2.1, -20.4, 9.6), lambda t: 0.7 - 0.45 * t, WHITE)   # sabers
        v.box(sx * 3.4 - 1.3, -15.5, 20.5, sx * 3.4 + 1.3, -13.8, 23.0, Gd)                     # ears
        v.box(sx * 3.4 - 0.6, -15.9, 21.0, sx * 3.4 + 0.6, -15.4, 22.4, (230, 150, 170))
    # dark stripes over the back
    v.paint(lambda X, Y, Z, o: o == G and Z > 14 and int((Y + 40) / 2.2) % 2 == 0 and abs(X) < 4.2, St)
    v.paint(lambda X, Y, Z, o: o == G and Y < -14 and Z > 20 and int(abs(X) * 2) % 3 == 1, St)
    v.line((0, 14, 15), (0, 19, 18), 1.2, G)                                   # tail
    v.line((0, 19, 18), (0, 23, 15.5), lambda t: 1.2 - 0.4 * t, St)
    eyes(v, 2.4, 18.4, w=2.2, h=1.8, angry=True)
    v.sym()
    return v


def lava_bull():
    v = Vox()
    K, Kd, M, L, Y, Hn = (52, 44, 54), (36, 30, 38), (92, 84, 92), (255, 92, 20), (255, 206, 40), (240, 232, 214)
    v.ell(0, 3, 12.5, 6.4, 11, 6.2, K)                                         # body
    v.ell(0, -4, 16, 6.2, 5.5, 5.2, K)                                         # shoulder hump
    v.ell(0, -8, 12, 6.0, 4, 6, K)                                             # chest
    for sx in (-1, 1):
        for ly in (-6.5, 10):
            v.box(sx * 4.2 - 1.9, ly - 1.9, 0, sx * 4.2 + 1.9, ly + 1.9, 8.5, K)
            v.box(sx * 4.2 - 2.0, ly - 2.0, 0, sx * 4.2 + 2.0, ly + 2.0, 1.2, Kd)   # hooves
    v.ell(0, -13, 11.5, 4.4, 4.6, 4.8, K)                                      # head, low and forward
    v.box(-3.2, -18.6, 7.6, 3.2, -15.2, 11.6, M)                               # big muzzle
    v.box(-2.2, -19, 9.4, -0.9, -18.4, 10.8, L)                                # glowing nostrils
    v.box(0.9, -19, 9.4, 2.2, -18.4, 10.8, L)
    v.box(-0.6, -19.2, 7.6, 0.6, -18.4, 9.0, Y)                                # nose ring
    for sx in (-1, 1):                                                          # wide horns
        v.line((sx * 3.6, -13, 15), (sx * 8.4, -13.2, 15.6), lambda t: 1.4 - 0.3 * t, Hn)
        v.line((sx * 8.4, -13.2, 15.6), (sx * 9.8, -15.4, 19.6), lambda t: 1.1 - 0.75 * t, Hn)
        v.line((sx * 4.3, -11, 11), (sx * 5.2, -10.5, 13), 0.9, K)             # ears
    # lava cracks on the flanks and back
    def crack(X, Y_, Z, o):                                                  # zigzag lava lines painted into the skin
        if o != K:
            return False
        ph = (Y_ + 12) / 3.8
        zz = abs(((Z * 0.9 + ph * 2.0) % 3.0) - 1.5)
        return abs(ph - round(ph) + (zz - 0.75) * 0.35) < 0.07 and Z > 5
    v.paint(crack, lambda X, Y_, Z, o: Y if int(Z) % 3 == 0 else L)
    # flames on the hump
    for k, (x, y, hgt) in enumerate(((0, -5, 6), (-2.4, -3, 4.5), (2.4, -3, 4.5), (-1.2, 0, 5), (1.2, 0, 5), (0, 3, 4))):
        v.line((x, y, 20), (x * 0.7, y + 0.6, 20 + hgt), lambda t: 1.4 - 1.1 * t, L)
        v.line((x, y, 20.5 + hgt * 0.4), (x * 0.7, y + 0.6, 20 + hgt * 0.95), lambda t: 0.8 - 0.6 * t, Y)
    v.line((0, 14, 13), (0, 16.5, 7), 0.6, K)                                   # tail + fire tip
    v.ell(0, 16.6, 6.2, 1.1, 1.1, 1.5, L)
    eyes(v, 2.6, 12.6, w=1.9, h=1.6, angry=True)
    v.paint(lambda X, Y, Z, o: o == WHITE and Y < -15 and Z > 12, Y)            # burning yellow eyes
    v.sym()
    return v


PETS = [('Saber Tiger', saber_tiger), ('Lava Bull', lava_bull)]


def build_mesh(name, v, kind='normal', unit=0.07):
    """outside faces, vertex colours, and UVs so the stud tile repeats every STUD voxels"""
    bm = bmesh.new()
    cl = bm.loops.layers.color.new('Col')
    uvl = bm.loops.layers.uv.new('UV')
    xs = [k[0] for k in v.g]
    ys = [k[1] for k in v.g]
    zs = [k[2] for k in v.g]
    ox, oy, oz = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2, min(zs)
    vc = {}

    def vert(p):
        if p not in vc:
            vc[p] = bm.verts.new(((p[0] - ox) * unit, (p[1] - oy) * unit, (p[2] - oz) * unit))
        return vc[p]

    for key, col in v.g.items():
        c = recolor(col, key, kind)
        hsh = int(hashlib.md5(str(key).encode()).hexdigest()[:4], 16) / 65535
        j = 0.96 + 0.06 * hsh
        for (dx, dy, dz), quad in DIRS:
            if (key[0] + dx, key[1] + dy, key[2] + dz) in v.g:
                continue
            pts = [(key[0] + a, key[1] + b, key[2] + cc) for a, b, cc in quad]
            f = bm.faces.new([vert(p) for p in pts])
            light = 1.12 if dz == 1 else (0.95 if dz == 0 else 0.72)
            cc_ = tuple(min(1.0, (x / 255) * j * light) for x in c) + (1.0,)
            for lp, p in zip(f.loops, pts):
                lp[cl] = cc_
                if dx:
                    u, w = p[1], p[2]
                elif dy:
                    u, w = p[0], p[2]
                else:
                    u, w = p[0], p[1]
                lp[uvl].uv = (u / STUD, w / STUD)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    m = bpy.data.materials.new(name + 'M')
    m.use_nodes = True
    nt = m.node_tree
    a = nt.nodes.new('ShaderNodeVertexColor')
    a.layer_name = 'Col'
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(str(HERE / 'tex' / 'stud.png'), check_existing=True)
    t.interpolation = 'Closest' if False else 'Linear'
    mul = nt.nodes.new('ShaderNodeMix')
    mul.data_type = 'RGBA'
    mul.blend_type = 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1.0
    nt.links.new(a.outputs['Color'], mul.inputs['A'])
    nt.links.new(t.outputs['Color'], mul.inputs['B'])
    b = nt.nodes['Principled BSDF']
    br = nt.nodes.new('ShaderNodeBrightContrast')
    br.inputs['Bright'].default_value = 0.0
    br.inputs['Contrast'].default_value = 0.12
    nt.links.new(mul.outputs['Result'], br.inputs['Color'])
    nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.55
    me.materials.append(m)
    return o


if __name__ == '__main__' and 'preview' in args:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc, cam = V2.stage()
    V2.YAW = -38
    V2.RIGHT = (math.cos(math.radians(V2.YAW)), math.sin(math.radians(V2.YAW)))
    x = 0
    for name, fn in PETS:
        o = build_mesh(name, fn())
        o.location = V2.along(x)
        x += 5.2
    V2.render(OUT / 'vox3_pets.png', cam, 2.6, 13, 1800, 900, tz=1.0, pitch=72)
    print('done')
