"""Build the textured, skinned dragon and its FBX takes in Blender 4.2."""
import bmesh
import bpy
import math
import struct
import zlib
import numpy as np
from mathutils import Vector
from pathlib import Path
from math import sin, cos, pi
ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / 'models'
MODELS.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 24
# Each atlas cell is a reusable painted UV island with gutters. The eye is
# projected on its own cell so the pupil and catchlights follow the blink.
pal = [
    ('9872ce', 'e3bdf8'), ('56bfae', 'c5ffdd'), ('cb8142', 'ffe29a'),
    ('915792', 'ffbcdb'), ('9765b0', 'd5a3ec'), ('54446d', '54446d'),
    ('69529a', 'a680dc'), ('fff1b1', 'fff9de'), ('7589d5', 'aaf5ee'),
    ('cca3bc', 'fff0de'), ('a168b5', 'd7afea'), ('9e78ce', 'e9ccfd'),
    ('e19857', 'fff6c8'), ('7445a0', 'ac79c9'), ('9670be', 'dabaee'), ('6dcaba', 'c0ffdf')]


def rgb(h): return np.array(list(bytes.fromhex(h)), dtype=float)


def png(path, data):
    def chunk(k, d): return struct.pack('>I', len(d))+k+d+struct.pack('>I', zlib.crc32(k+d) & 0xffffffff)
    raw = b''.join(b'\0'+line.tobytes() for line in data[::-1])
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB', 1024, 1024, 8,
                     2 if data.ndim == 3 else 0, 0, 0, 0))+chunk(b'IDAT', zlib.compress(raw, 9))+chunk(b'IEND', b''))


cols = np.zeros((1024, 1024, 3), np.uint8)
mask = np.zeros_like(cols)
v, u = np.mgrid[0:256, 0:256]/255
for i, (a, b) in enumerate(pal):
    f = np.clip(.13+.83*v+.09*np.sin(pi*u)*np.sin(pi*v), 0, 1)[:, :, None]
    tile = rgb(a)*(1-f)+rgb(b)*f
    glow = np.zeros_like(u)
    if i == 6:
        x = (u-.5)/.47
        y = (v-.5)/.47
        radius = np.sqrt(x*x+y*y)
        tile[:] = rgb('322740')

        def paint(k, color):
            global tile
            k = np.clip(k, 0, 1)[:, :, None]
            tile = tile*(1-k)+np.array(color)*k
        iris = rgb('48356f')+(rgb('69dcdf')-rgb('48356f'))*np.clip(.48-.65*y, 0, 1)[:, :, None]
        iris += np.maximum(0, -y)[:, :, None]*np.cos(32*np.arctan2(y, x))[:, :, None]*8
        paint((.89-radius)*80, iris)
        paint((.57-np.sqrt((x+.035)**2+(y-.095)**2))*90, rgb('28213e'))
        star = (np.abs((x+.29)/.22)**.70+np.abs((y-.39)/.26)**.70)
        glow = np.maximum(np.clip((1-star)*15, 0, 1), np.clip((.105-np.hypot(x-.26, y-.49))*100, 0, 1))
        paint(glow, rgb('fff8ec'))
        paint((.065-np.hypot(x-.42, y+.37))*100, rgb('fff3c7'))
    if i in (7, 12):
        glow[:] = 1 if i == 7 else .6
    sl = np.s_[(i//4)*256:(i//4+1)*256, (i % 4)*256:(i % 4+1)*256]
    cols[sl] = np.clip(tile, 0, 255)
    mask[sl] = (255*glow[:, :, None]).astype('uint8')
png(MODELS/'StarlightDragon_Color.png', cols)
png(MODELS/'StarlightDragon_Emission.png', mask[:, :, 0])
verts = []
faces = []
maps = []
groups = {}


def piece(points, polys, uv, cell, bone):
    offset = len(verts)
    verts.extend(points)
    groups.setdefault(bone, []).extend(range(offset, offset+len(points)))
    for face in polys:
        faces.append(tuple(offset+j for j in face))
        maps.append([((cell % 4+.015+.97*uv[j][0])/4, (cell//4+.015+.97*uv[j][1])/4) for j in face])


def oval(c, s, cell, bone, n=16, m=10, yaw=0, eye=False, tilt=0):
    pts = []
    uv = []
    fs = []
    for k in range(m+1):
        t = pi*k/m-pi/2
        for j in range(n+1):
            a = 2*pi*j/n
            x = cos(t)*sin(a)
            y = -cos(t)*cos(a)
            z = sin(t)
            X = x*s[0]
            Y = y*s[1]
            Z = z*s[2]
            X, Z = X*cos(tilt)+Z*sin(tilt), Z*cos(tilt)-X*sin(tilt)
            pts.append((c[0]+X*cos(yaw)-Y*sin(yaw), c[1]+X*sin(yaw)+Y*cos(yaw), c[2]+Z))
            uv.append((.5+.47*x, .5+.47*z) if eye else (j/n, k/m))
            if k and j:
                h = k*(n+1)+j
                q = (h-n-2, h-n-1, h, h-1)
                fs.append(q[1:] if k == 1 else (q[0], q[1], q[3]) if k == m else q)
    piece(pts, fs, uv, cell, bone)


def tube(path, radii, cell, bone, n=8):
    path = list(map(Vector, path))
    pts = []
    uv = []
    fs = []
    for k, p in enumerate(path):
        d = (path[min(k+1, len(path)-1)]-path[max(0, k-1)]).normalized()
        ref = Vector((0, 1, 0)) if abs(d.y) < .85 else Vector((1, 0, 0))
        a = d.cross(ref).normalized()
        b = d.cross(a)
        for j in range(n):
            ang = 2*pi*j/n
            pts.append(p+radii[k]*(a*cos(ang)+b*sin(ang)))
            uv.append((.5+.40*cos(ang), k/(len(path)-1)))
            if k:
                fs.append(((k-1)*n+j, (k-1)*n+(j+1) % n, k*n+(j+1) % n, k*n+j))
    fs.extend([tuple(reversed(range(n))), tuple(range(len(pts)-n, len(pts)))])
    piece(pts, fs, uv, cell, bone)


def badge(c, rx, rz, cell, bone, yaw=0, points=4):
    pts = [(c[0]+.085*sin(yaw), c[1]-.085*cos(yaw), c[2])]
    uv = [(.5, .65)]
    for i in range(points*2):
        a = i*pi/points
        r = .38 if i % 2 else 1
        x = r*rx*sin(a)
        z = r*rz*cos(a)
        pts.append((c[0]+cos(yaw)*x, c[1]+sin(yaw)*x, c[2]+z))
        uv.append((.5+.46*r*sin(a), .5+.46*r*cos(a)))
    fs = [(0, (i+1) % (2*points)+1, i+1) for i in range(points*2)]
    fs.append(tuple(range(1, 2*points+1)))
    piece(pts, fs, uv, cell, bone)


bones = {}
def bone(name, pt, parent=None): bones[name] = (pt, parent); return name


root = bone('Root', (0, 0, 0))
body = bone('Body', (0, 0, .7), root)
head = bone('Head', (0, -.26, 1.94), body)
oval((0, .18, 1.23), (.91, .94, 1.04), 0, body, 24, 14)
oval((0, -.55, 1.27), (.64, .28, .74), 1, body, 18, 10)
oval((0, -.39, 2.68), (1.23, .98, 1.02), 0, head, 32, 20)
oval((0, -1.19, 2.34), (.68, .44, .41), 9, head, 22, 12)
for sign in [-1, 1]:
    def S(x): return sign*x
    tag = 'R' if sign > 0 else 'L'
    foot = bone('Foot_'+tag, (S(.52), -.30, .65), body)
    oval((S(.56), -.32, .34), (.37, .51, .34), 0, foot, 14, 9)
    oval((S(.57), .64, .37), (.45, .50, .37), 4, body, 14, 9)
    for j in [-1, 1]:
        oval((S(.56)+j*.095, -.775, .26), (.07, .075, .065), 9, foot, 8, 5)
    arm = bone('Paw_'+tag, (S(.69), -.29, 1.55), body)
    oval((S(.77), -.42, 1.19), (.245, .30, .42), 11, arm, 14, 9, tilt=S(-.24))
    e = (S(.635), -1.175, 2.79)
    eyeBone = bone('Eye_'+tag, e, head)
    oval(e, (.316, .155, .363), 6, eyeBone, 22, 14, yaw=S(.47), eye=True)
    oval((S(.945), -1.018, 2.42), (.18, .065, .094), 3, head, 12, 7, yaw=S(.74))
    oval((S(.248), -1.561, 2.48), (.061, .035, .043), 5, head, 10, 6, yaw=S(.25))
    # Swept horns and jewelry-like collar bands at their roots.
    horn = [(S(.66), -.13, 3.40), (S(.73), -.10, 3.58),
            (S(.83), -.03, 3.79), (S(.90), .10, 3.96), (S(.91), .23, 4.08)]
    tube(horn, [.235, .20, .148, .080, .009], 2, head, 14)
    tube([horn[0], (S(.70), -.115, 3.53), horn[1]], [.244, .235, .199], 12, head, 14)
    # Leaf-shaped ear fins, folded around a mint inset.

    def fin(inset):
        base = Vector((S(.94), -.17, 3.04))
        tip = Vector((S(1.57), .04, 3.52))
        axis = tip-base
        pts = []
        fs = []
        uv = []
        for k in range(9):
            f = k/8
            width = (sin(pi*f)**.75)*(.125 if inset else .215)+.008
            p = base+axis*(.13+.71*f if inset else f)
            p.y -= .102 if inset else 0
            for j in range(8):
                a = 2*pi*j/8
                pts.append((p.x-S(.55)*width*cos(a), p.y+width*.55*sin(a), p.z+width*cos(a)))
                uv.append((j/8, f))
                if k:
                    fs.append(((k-1)*8+j, (k-1)*8+(j+1) % 8, k*8+(j+1) % 8, k*8+j))
        fs.extend([tuple(reversed(range(8))), tuple(range(64, 72))])
        piece(pts, fs, uv, 1 if inset else 4, head)
    fin(False)
    fin(True)
    wing = bone('Wing_'+tag, (S(.60), .61, 1.64), body)
    # A cambered bat wing with three concave scallops, a rolled leading edge and ribs.
    outline = [(.59, 1.56), (.73, 1.96), (1.05, 2.33), (1.50, 2.59), (1.86, 2.64), (2.12, 2.58), (1.94, 2.42), (1.83, 2.22),
               (1.83, 2.06), (1.63, 2.13), (1.46, 2.08), (1.30, 1.92), (1.28, 1.75), (1.12, 1.86), (.96, 1.83), (.81, 1.68), (.75, 1.52)]

    def wp(x, z): return (S(x), .68+.26*(x-.6), z)
    pts = [wp(x, z) for x, z in outline]
    h = len(pts)
    hub = Vector(wp(1.28, 2.22))
    pts.extend([hub+Vector((0, -.15, 0)), hub+Vector((0, .16, 0))])
    fs = []
    for j in range(h):
        fs.extend([(h, j, (j+1) % h), (h+1, (j+1) % h, j)])
    piece(pts, fs, [((abs(p[0])-.50)/1.7, (p[2]-1.45)/1.25) for p in pts], 1, wing)
    tube([wp(*p) for p in outline[:6]], [.12, .115, .105, .085, .048, .012], 4, wing)
    for end in [(1.83, 2.06), (1.28, 1.75)]:
        p = Vector(wp(1.50, 2.57))
        q = Vector(wp(*end))
        mid = (p+q)/2
        mid.y -= .12
        tube([p, mid, q], [.055, .035, .009], 15, wing, 7)
    for x, z, r in [(1.55, 2.38, .075), (1.68, 2.44, .033)]:
        p = Vector(wp(x, z))
        p.y -= .135
        badge(p, r, r*1.3, 7, wing)
# Delicate curved smile beneath the muzzle.
tube([(-.20, -1.582, 2.242), (-.12, -1.604, 2.203), (0, -1.611, 2.19),
     (.12, -1.604, 2.203), (.20, -1.582, 2.242)], [.007, .016, .018, .016, .007], 5, head)
badge((0, -1.254, 3.10), .145, .202, 2, head)
badge((0, -1.277, 3.11), .089, .132, 7, head)
for j in range(3):
    y = .05+j*.38
    z = 3.66-j*.13
    tube([(0, y, z-.19), (0, y+.025, z), (0, y+.17, z+.15)], [.15, .12, .013], 1, head, 10)
for x, y, z, r in [(0, -.828, 1.42, .13), (-.29, -.756, 1.58, .06), (.24, -.776, 1.23, .055)]:
    badge((x, y, z), r, r*1.22, 7, body)
tailpath = [(0, .75, 1.09), (.18, 1.15, .98), (.49, 1.48, .88), (.88, 1.64, .85),
            (1.22, 1.68, .94), (1.50, 1.61, 1.13), (1.65, 1.48, 1.37), (1.67, 1.31, 1.59)]
tail = bone('Tail', tailpath[0], body)
tip = bone('TailTip', tailpath[3], tail)
tube(tailpath, [.39, .34, .28, .22, .18, .137, .107, .08], 0, tail, 14)
# Blend the last rings between the two tail bones.
tailids = groups[tail][:]
groups[tip] = tailids[4*14:]
groups[tail] = tailids[:4*14]
badge(tailpath[-1], .23, .29, 12, tip, .18, 5)
bone('GlowSocket', tailpath[-1], tip)
mesh = bpy.data.meshes.new('StarlightDragon_Geometry')
mesh.from_pydata(verts, [], faces)
mesh.update()
obj = bpy.data.objects.new('StarlightDragon', mesh)
scene.collection.objects.link(obj)
layer = mesh.uv_layers.new(name='PaintedAtlas')
for face, coords in zip(mesh.polygons, maps):
    face.use_smooth = True
    for i, uv in zip(face.loop_indices, coords):
        layer.data[i].uv = uv
mat = bpy.data.materials.new('Starlight Enamel')
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
bs = nodes.get('Principled BSDF')
for label, filename in [('Color', 'Color'), ('Glow', 'Emission')]:
    node = nodes.new('ShaderNodeTexImage')
    node.image = bpy.data.images.load(str(MODELS/f'StarlightDragon_{filename}.png'))
    if label == 'Color':
        links.new(node.outputs['Color'], bs.inputs['Base Color'])
        links.new(node.outputs['Color'], bs.inputs['Emission Color'])
    else:
        node.image.colorspace_settings.name = 'Non-Color'
        strength = nodes.new('ShaderNodeMath')
        strength.operation = 'MULTIPLY'
        strength.inputs[1].default_value = 2.6
        links.new(node.outputs['Color'], strength.inputs[0])
        links.new(strength.outputs[0], bs.inputs['Emission Strength'])
bs.inputs['Roughness'].default_value = .34
mesh.materials.append(mat)
arm = bpy.data.armatures.new('Dragon skeleton')
rig = bpy.data.objects.new('StarlightRig', arm)
scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name, (p, parent) in bones.items():
    b = arm.edit_bones.new(name)
    b.head = p
    b.tail = Vector(p)+Vector((0, 0, .22))
    if parent:
        b.parent = arm.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
for name, indices in groups.items():
    obj.vertex_groups.new(name=name).add(indices, 1, 'REPLACE')
for j in (3, 4):
    ids = tailids[14*j:14*(j+1)]
    for name, w in [(tail, .72 if j == 3 else .28), (tip, .28 if j == 3 else .72)]:
        obj.vertex_groups[name].add(ids, w, 'REPLACE')
# Weld coincident seam vertices, retain loop UVs and unify shell normals.
bm = bmesh.new()
bm.from_mesh(mesh)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=.00001)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.to_mesh(mesh)
bm.free()
mesh.update()
obj.parent = rig
mod = obj.modifiers.new('Starlight skin', 'ARMATURE')
mod.object = rig
rig.animation_data_create()
actions = {}
for name, end in [('Idle', 49), ('Hop', 25), ('Hatch', 49)]:
    act = bpy.data.actions.new(name)
    actions[name] = act
    act.use_fake_user = True
    rig.animation_data.action = act
    frames = sorted(set(range(1, end+1, 3)) | {end} | ({32, 34, 36, 38} if name == 'Idle' else set()))
    for fr in frames:
        t = (fr-1)/(end-1)
        a = 2*pi*t
        phase = sin(a)
        rise = (1-cos(a))/2
        for p in rig.pose.bones:
            p.rotation_mode = 'XYZ'
            p.location = (0, 0, 0)
            p.rotation_euler = (0, 0, 0)
            p.scale = (1, 1, 1)
        pb = rig.pose.bones
        def rot(b, xyz): pb[b].rotation_euler = xyz
        # Vertical edit bones use local Y for height and local Z for forward.
        if name == 'Idle':
            pb[body].location.y = .027*rise
            pb[body].scale = (1+.012*rise, 1+.036*rise, 1+.018*rise)
            rot(head, (.026*phase, .055*phase, .035*phase))
            height = 0
            flap = .105*phase
            blink = max(.055, min(1, abs(fr-35)/3))
            if fr in (34, 36):
                blink = .07
        elif name == 'Hop':
            height = .52*sin(pi*t)**1.6
            flap = .31*phase
            rot(body, (.14*phase, 0, 0))
            rot(head, (-.09*phase, 0, .045*phase))
            blink = 1
            for side in ['L', 'R']:
                rot('Foot_'+side, (.47*phase, 0, 0))
                rot('Paw_'+side, (-.45*phase, 0, 0))
        else:
            jump = max(0, sin(pi*min(1, max(0, (t-.13)/.67))))
            height = 1.04*jump
            flap = .68*jump-.15*sin(2*a)
            spin = min(1, max(0, (t-.14)/.64))
            spin = spin*spin*(3-2*spin)
            rot(root, (0, 2*pi*spin, 0))
            rot(head, (-.12*jump, 0, .10*phase))
            blink = 1
            squash = .10*math.exp(-((t-.12)/.065)**2)+.13*math.exp(-((t-.82)/.06)**2)
            pb[body].scale = (1+squash, 1-squash, 1+squash)
        pb[root].location.y = height
        rot(tail, (.08*phase, .22*phase, 0))
        rot(tip, (.13*phase, .24*phase, 0))
        for tag, sign in [('L', -1), ('R', 1)]:
            rot('Wing_'+tag, (.06*phase, sign*.12*phase, sign*flap))
            pb['Eye_'+tag].scale.y = blink
            pb['Eye_'+tag].location.z = -.16*(1-blink)
        for p in pb:
            for prop in ['location', 'rotation_euler', 'scale']:
                p.keyframe_insert(data_path=prop, frame=fr, group=p.name)
rig.animation_data.action = actions['Idle']
scene.frame_set(1)
if __name__ == '__main__':
    obj.select_set(True)
    rig.select_set(True)
    export_settings = dict(
        use_selection=True, object_types={'ARMATURE', 'MESH'},
        axis_forward='-Z', axis_up='Y', global_scale=1.17,
        apply_scale_options='FBX_SCALE_UNITS', add_leaf_bones=False,
        bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0,
        path_mode='STRIP', use_triangles=True,
    )
    bpy.ops.export_scene.fbx(filepath=str(MODELS/'StarlightDragon.fbx'),
                             bake_anim_use_all_actions=True, **export_settings)
    # Studio's animation editor can consume one take per file directly.
    clip_dir = MODELS/'animations'
    clip_dir.mkdir(exist_ok=True)
    for name, action in actions.items():
        single = action.copy()
        for curve in single.fcurves:
            for key in curve.keyframe_points:
                key.co_ui.x -= 1
        rig.animation_data.action = single
        scene.name = name
        scene.frame_start, scene.frame_end = map(int, single.frame_range)
        scene.frame_set(scene.frame_start)
        bpy.ops.export_scene.fbx(filepath=str(clip_dir/f'{name}.fbx'),
                                 bake_anim_use_all_actions=False, **export_settings)
        rig.animation_data.action = None
        bpy.data.actions.remove(single)
    scene.name = 'Starlight Dragon'
    scene.frame_start = 1
    rig.animation_data.action = actions['Idle']
    scene.frame_set(1)
    mesh.calc_loop_triangles()
    print('ASSET TRIANGLES', len(mesh.loop_triangles), flush=True)
