r"""Sun Lion made of small cubes (voxels), Steal-an-Egg look: every outside face gets the LEGO brick tile.
  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P vox_lion.py   -> out/vox_lion_a.png, out/vox_lion_b.png
Design units: x = right, y = back (looks towards -y), z = up."""
import bpy, bmesh, math, sys, pathlib, hashlib, random
from mathutils import Vector
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gen_voxel_pets2 as V2
from gen_voxel_pets2 import Vox, eyes, INK, WHITE, DIRS

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "out"
TILE = 8  # voxels per brick tile (tile = 4 studs across -> 1 stud every 2 voxels)
random.seed(3)

G, Gd, L = (242, 172, 40), (214, 134, 22), (252, 228, 160)
M0, M1, M2, M3 = (255, 238, 90), (255, 206, 30), (255, 160, 16), (232, 108, 10)
NOSE = (70, 36, 30)


def lion():
    v = Vox()
    v.ell(0, 2, 12.5, 4.8, 10.5, 4.6, G)                    # torso
    v.ell(0, -6, 13, 5.6, 5.5, 5.6, G)                      # deep chest
    v.ell(0, 9.5, 12.5, 4.9, 5, 5, G)                       # hips
    v.paint(lambda X, Y, Z, o: Z < 9.6 and o == G, L)       # light belly
    for sx in (-1, 1):
        v.ell(sx * 3.7, -6.5, 10, 2.3, 2.8, 3.6, G)                          # shoulders
        v.line((sx * 3.8, -7, 9), (sx * 3.8, -7.8, 1.8), lambda t: 1.95 - 0.25 * t, G)
        v.box(sx * 3.8 - 1.9, -10.6, 0, sx * 3.8 + 1.9, -6.4, 1.8, Gd)      # front paws
        v.ell(sx * 3.6, 9.5, 11, 2.5, 3.9, 4.3, G)                           # thighs
        v.line((sx * 3.7, 11, 8), (sx * 3.8, 9.8, 1.8), lambda t: 1.75 - 0.2 * t, G)
        v.box(sx * 3.8 - 1.7, 7.4, 0, sx * 3.8 + 1.7, 11.2, 1.8, Gd)        # back paws
        for tx in (-1, 0, 1):                                                # toe lines
            v.box(sx * 3.8 + tx * 1.1 - 0.15, -10.8, 0.3, sx * 3.8 + tx * 1.1 + 0.15, -10.4, 1.3, NOSE)
    v.line((0, -9, 15), (0, -12, 17.5), 3.6, G)                             # neck

    # ---- sun mane: a big round fluffy mass around head and neck + cube rays in every direction (not forward)
    MC = (0, -11.5, 17.2)
    v.ell(MC[0], MC[1], MC[2], 6.6, 5.2, 6.6, M1)
    def shade(X, Y, Z, o):
        r = math.sqrt((X - MC[0]) ** 2 + ((Y - MC[1]) * 1.25) ** 2 + (Z - MC[2]) ** 2)
        return M0 if r < 5.0 else (M1 if r < 6.0 else M2)
    v.paint(lambda X, Y, Z, o: o == M1, shade)
    golden = math.pi * (3 - math.sqrt(5))
    N = 46
    for k in range(N):
        yk = 1 - 2 * (k + 0.5) / N
        rr = math.sqrt(1 - yk * yk)
        th = golden * k
        d = Vector((math.cos(th) * rr, yk, math.sin(th) * rr))
        if d.y < -0.35:
            continue  # nothing sticks out towards the face
        d.y *= 0.7
        d.normalize()
        ln = random.uniform(9.0, 10.8) * (0.8 if d.z < -0.6 else 1)
        p0 = Vector(MC) + d * 5.0
        p1 = Vector(MC) + d * (5.0 + (ln - 5.0) * 0.55)
        p2 = Vector(MC) + d * ln
        v.line(tuple(p0), tuple(p1), lambda t: 1.7 - 0.5 * t, M2)
        v.line(tuple(p1), tuple(p2), lambda t: 1.1 - 0.75 * t, M3)
    v.ell(0, -12.8, 17.4, 6.2, 1.6, 6.2, M0, only_empty=False)               # bright ring right behind the face

    # ---- head
    v.ell(0, -14.2, 18, 4.5, 4.4, 4.3, G)
    v.box(-3.6, -18.9, 17.6, 3.6, -15, 21.6, G)                             # flat face for the eyes
    v.box(-2.7, -20.2, 14.8, 2.7, -16, 18.4, G)                             # muzzle
    v.box(-2.6, -20.4, 14.6, 2.6, -16.5, 16.4, L)                           # light jaw
    v.box(-1.3, -20.8, 17.4, 1.3, -19.8, 18.8, NOSE)                        # nose
    v.box(-0.25, -20.7, 15.8, 0.25, -20.2, 17.4, NOSE)                      # mouth
    v.box(-1.8, -20.7, 15.6, 1.8, -20.2, 16.1, NOSE)
    for sx in (-1, 1):
        v.box(sx * 3.2 - 1.2, -15, 21.4, sx * 3.2 + 1.2, -13.2, 23.6, G)     # ears
        v.box(sx * 3.2 - 0.6, -15.3, 21.9, sx * 3.2 + 0.6, -14.8, 23.1, (200, 110, 40))

    # ---- tail with a crystal tuft
    v.line((0, 14, 14), (0, 19, 9), 0.95, G)
    v.line((0, 19, 9), (0, 22, 10.5), 0.9, G)
    v.ell(0, 23.2, 11.3, 1.9, 1.9, 1.9, M3)
    for a in range(6):
        t = a * math.pi / 3
        v.line((0, 23.2, 11.3), (math.cos(t) * 2.6, 24.6, 11.3 + math.sin(t) * 2.6), lambda u: 0.8 - 0.5 * u, M2)
    v.sym()
    flat_eyes(v, 2.0, 19.0, w=2.6, h=2.2)
    return v


def flat_eyes(v, ex, ez, w=2.8, h=2.2):
    """eyes painted INTO the face (no cubes sticking out): the two front-most voxels of every column become the eye"""
    S = V2.S
    for sx in (-1, 1):
        cx = sx * ex
        for xi in range(math.floor((cx - w / 2) * S), math.ceil((cx + w / 2) * S)):
            for zi in range(math.floor(ez * S), math.ceil((ez + h) * S)):
                X, Z = (xi + 0.5) / S, (zi + 0.5) / S
                t = (X - cx) / w * sx + 0.5          # 0 = inner edge, 1 = outer edge
                if Z > ez + h - 0.7 * (1 - t):       # top edge slopes down towards the nose
                    continue
                ys = sorted(k[1] for k in v.g if k[0] == xi and k[2] == zi)
                if not ys:
                    continue
                pupil = t < 0.55 and Z < ez + h * 0.78 and Z > ez + 0.25
                shine = pupil and 0.3 < t < 0.45 and Z > ez + h * 0.55
                col = WHITE if (shine or not pupil) else INK
                if ys[0] / S > -18.4:
                    continue  # only the flat face, never the nose or the sides
                for y in ys[:1]:
                    v.g[(xi, y, zi)] = col


def build(name, v, unit=0.07):
    bm = bmesh.new()
    cl = bm.loops.layers.color.new("Col")
    uvl = bm.loops.layers.uv.new("UV")
    xs = [k[0] for k in v.g]
    ys = [k[1] for k in v.g]
    zs = [k[2] for k in v.g]
    ox, oy, oz = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2, min(zs)
    vc = {}

    def vert(p):
        if p not in vc:
            vc[p] = bm.verts.new(((p[0] - ox) * unit, -(p[1] - oy) * unit, (p[2] - oz) * unit))  # -y: head to +y in Blender
        return vc[p]

    for key, col in v.g.items():
        hsh = int(hashlib.md5(str(key).encode()).hexdigest()[:4], 16) / 65535
        j = 0.95 + 0.08 * hsh
        for (dx, dy, dz), quad in DIRS:
            if (key[0] + dx, key[1] + dy, key[2] + dz) in v.g:
                continue
            pts = [(key[0] + a, key[1] + b, key[2] + c) for a, b, c in quad]
            f = bm.faces.new([vert(p) for p in pts])
            light = 1.1 if dz == 1 else (0.96 if dz == 0 else 0.75)
            cc = tuple(min(1.0, (x / 255) * j * light) for x in col) + (1.0,)
            for lp, p in zip(f.loops, pts):
                lp[cl] = cc
                u, w = (p[1], p[2]) if dx else ((p[0], p[2]) if dy else (p[0], p[1]))
                lp[uvl].uv = (u / TILE, w / TILE)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)  # the -y flip mirrors the mesh: turn the faces back out
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    m = bpy.data.materials.new(name + "M")
    m.use_nodes = True
    nt = m.node_tree
    a = nt.nodes.new("ShaderNodeVertexColor")
    a.layer_name = "Col"
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(str(HERE / "tex" / "brick.png"))
    t.image.colorspace_settings.name = "Non-Color"
    k = nt.nodes.new("ShaderNodeMath")
    k.operation = "MULTIPLY"
    k.inputs[1].default_value = 1.18
    nt.links.new(t.outputs["Color"], k.inputs[0])
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    nt.links.new(a.outputs["Color"], mul.inputs["A"])
    nt.links.new(k.outputs[0], mul.inputs["B"])
    b = nt.nodes["Principled BSDF"]
    nt.links.new(mul.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.6
    me.materials.append(m)
    return o


def lin(c):
    return tuple((x / 255) ** 2.2 for x in c) + (1,)


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
ob = build("Pet_1_5", lion())  # zone 1, Legendary slot = Sun Lion
print("faces", len(ob.data.polygons))


def bake_for_roblox(ob, size=1024):
    """Roblox reads one texture: bake vertex colour x brick tile into an image on a second, non-overlapping UV map"""
    me = ob.data
    tile_uv = me.uv_layers["UV"]
    bake_uv = me.uv_layers.new(name="Bake")
    me.uv_layers.active = bake_uv
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(5), island_margin=0.002)
    bpy.ops.object.mode_set(mode="OBJECT")
    m = me.materials[0]
    nt = m.node_tree
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "UV"
    for nd in nt.nodes:
        if nd.type == "TEX_IMAGE":
            nt.links.new(uvn.outputs["UV"], nd.inputs["Vector"])
    img = bpy.data.images.new(ob.name + "_tex", size, size)
    tgt = nt.nodes.new("ShaderNodeTexImage")
    tgt.image = img
    nt.nodes.active = tgt
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 4
    sc.render.bake.use_pass_direct = False
    sc.render.bake.use_pass_indirect = False
    sc.render.bake.margin = 2
    bpy.ops.object.bake(type="DIFFUSE")
    img.filepath_raw = str(OUT / (ob.name + "_tex.png"))
    img.file_format = "PNG"
    img.save()
    me.uv_layers.remove(me.uv_layers["UV"])
    me.uv_layers["Bake"].active_render = True
    nm = bpy.data.materials.new(ob.name + "_baked")
    nm.use_nodes = True
    t = nm.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = img
    nm.node_tree.links.new(t.outputs["Color"], nm.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    me.materials.clear()
    me.materials.append(nm)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(OUT / "SunLion_voxel.fbx"), use_selection=True, object_types={"MESH"},
                             apply_scale_options="FBX_SCALE_UNITS", mesh_smooth_type="FACE", add_leaf_bones=False,
                             bake_anim=False, path_mode="COPY", embed_textures=True)
    print("baked + exported")


bake_for_roblox(ob)

# Roblox-like stage: green baseplate, blue sky only for the camera, neutral light
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.eevee.use_gtao = True
sc.render.resolution_x = sc.render.resolution_y = 1200
sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
wn = w.node_tree
bgl = wn.nodes["Background"]
bgl.inputs[0].default_value = lin((235, 238, 245))
bgl.inputs[1].default_value = 0.8
bgs = wn.nodes.new("ShaderNodeBackground")
bgs.inputs[0].default_value = lin((140, 195, 245))
lp = wn.nodes.new("ShaderNodeLightPath")
mx = wn.nodes.new("ShaderNodeMixShader")
wn.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0])
wn.links.new(bgl.outputs[0], mx.inputs[1])
wn.links.new(bgs.outputs[0], mx.inputs[2])
wn.links.new(mx.outputs[0], wn.nodes["World Output"].inputs[0])
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(45), math.radians(15), math.radians(-40)))
bpy.context.object.data.energy = 3.0
bpy.context.object.data.angle = math.radians(10)
bpy.ops.mesh.primitive_plane_add(size=60)
gm = bpy.data.materials.new("Baseplate")
gm.use_nodes = True
chk = gm.node_tree.nodes.new("ShaderNodeTexChecker")
chk.inputs["Scale"].default_value = 15
chk.inputs["Color1"].default_value = lin((92, 160, 70))
chk.inputs["Color2"].default_value = lin((86, 150, 64))
gm.node_tree.links.new(chk.outputs["Color"], gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
bpy.context.object.data.materials.append(gm)

bpy.ops.object.camera_add()
cam = bpy.context.object
sc.camera = cam
cam.data.lens = 88
target = Vector((0, 0.2, 1.9))
for tag, pos in (("a", (11.5, 10.0, 4.8)), ("b", (13.0, -3.5, 4.2))):
    cam.location = pos
    cam.rotation_euler = (target - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = str(OUT / f"vox_lion_{tag}.png")
    bpy.ops.render.render(write_still=True)
print("done")
