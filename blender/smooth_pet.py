r"""Turn a voxel pet (from vox_*.py, with colour layers Col + Gl) into a SMOOTH low-poly model with the brick tile only as texture.
Run in live Blender after the voxel build:  exec(open(p).read(), {'__file__': p, 'SRC': 'Pet_Raptor', 'DST': 'Pet_RaptorSmooth'})
Steps: voxel remesh (fills the stairs) -> smooth -> decimate (big flat facets) -> transfer colours -> brick tile by box projection."""
import bpy, pathlib
HERE = pathlib.Path(__file__).resolve().parent
g = globals()
SRC, DST = g.get("SRC", "Pet_Raptor"), g.get("DST", "Pet_RaptorSmooth")
VOX = g.get("VOX", 0.045)          # remesh size (m); voxel of the source = 0.035
SMOOTH_IT = g.get("SMOOTH_IT", 6)
RATIO = g.get("RATIO", 0.07)       # decimate ratio
BRICK = g.get("BRICK", 0.55)       # brick tile size in metres (bigger = bigger bricks)

src = bpy.data.objects[SRC]
old = bpy.data.objects.get(DST)
if old:
    bpy.data.objects.remove(old, do_unlink=True)
me = src.data.copy()
me.name = DST
for m in list(me.color_attributes):
    pass
dst = bpy.data.objects.new(DST, me)
for c in src.users_collection:
    c.objects.link(dst)
dst.matrix_world = src.matrix_world.copy()
me.materials.clear()

vl = bpy.context.view_layer
for o in bpy.context.selected_objects:
    o.select_set(False)
vl.objects.active = dst
dst.select_set(True)

r = dst.modifiers.new("Remesh", "REMESH")
r.mode = "VOXEL"
r.voxel_size = VOX
r.use_smooth_shade = False
s = dst.modifiers.new("Smooth", "CORRECTIVE_SMOOTH")
s.iterations = SMOOTH_IT
s.smooth_type = "SIMPLE"
s.use_only_smooth = True
s.factor = 0.6
d = dst.modifiers.new("Decimate", "DECIMATE")
d.ratio = RATIO
for mo in list(dst.modifiers):
    bpy.ops.object.modifier_apply(modifier=mo.name)

# colours from the voxel model (nearest face), both Col and Gl
for name in ("Col", "Gl"):
    if name not in me.color_attributes:
        me.color_attributes.new(name, "BYTE_COLOR", "CORNER")
# ONE flat colour per face (no blending): nearest voxel face decides
from mathutils.bvhtree import BVHTree
sme = src.data
bvh = BVHTree.FromPolygons([v.co for v in sme.vertices], [p.vertices for p in sme.polygons])
scol = sme.color_attributes["Col"].data
sgl = sme.color_attributes["Gl"].data
dcol = me.color_attributes["Col"].data
dgl = me.color_attributes["Gl"].data
for p in me.polygons:
    loc, nrm, idx, dist = bvh.find_nearest(p.center)
    li = sme.polygons[idx].loop_start
    c, gl = tuple(scol[li].color), tuple(sgl[li].color)
    for l in p.loop_indices:
        dcol[l].color = c
        dgl[l].color = gl

# material: vertex colour x brick tile (box projected, so it sits nicely on every flat facet) + glow
m = bpy.data.materials.get(DST + "M") or bpy.data.materials.new(DST + "M")
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
outn = nt.nodes.new("ShaderNodeOutputMaterial")
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
nt.links.new(bsdf.outputs[0], outn.inputs[0])
col = nt.nodes.new("ShaderNodeVertexColor"); col.layer_name = "Col"
glw = nt.nodes.new("ShaderNodeVertexColor"); glw.layer_name = "Gl"
tc = nt.nodes.new("ShaderNodeTexCoord")
mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (1 / BRICK,) * 3
nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(str(HERE / "tex" / "brick.png"), check_existing=True)
tex.image.colorspace_settings.name = "Non-Color"
tex.projection = "BOX"
tex.projection_blend = 0.15
nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
k = nt.nodes.new("ShaderNodeMath"); k.operation = "MULTIPLY"; k.inputs[1].default_value = 1.18
nt.links.new(tex.outputs["Color"], k.inputs[0])
mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
mul.inputs["Factor"].default_value = 1.0
nt.links.new(col.outputs["Color"], mul.inputs["A"])
nt.links.new(k.outputs[0], mul.inputs["B"])
nt.links.new(mul.outputs["Result"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.55
em = nt.nodes.new("ShaderNodeMath"); em.operation = "MULTIPLY"; em.inputs[1].default_value = 1.1
nt.links.new(glw.outputs["Color"], em.inputs[0])
nt.links.new(mul.outputs["Result"], bsdf.inputs["Emission Color"])
nt.links.new(em.outputs[0], bsdf.inputs["Emission Strength"])
me.materials.append(m)
bpy.ops.object.shade_smooth_by_angle(angle=0.75)     # soft surfaces, crisp edges


def add_eyes(eye_pts):
    """real eyes: low-poly glowing yellow ellipsoid + black slit pupil, sunk into the head (eye_pts = world centres, outward x)"""
    import bmesh
    from mathutils import Matrix, Vector
    em = bpy.data.materials.get(DST + "Eye") or bpy.data.materials.new(DST + "Eye")
    em.use_nodes = True
    b = next(n for n in em.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (1.0, 0.78, 0.05, 1)
    b.inputs["Emission Color"].default_value = (1.0, 0.75, 0.05, 1)
    b.inputs["Emission Strength"].default_value = 4.0
    pm = bpy.data.materials.get(DST + "Pupil") or bpy.data.materials.new(DST + "Pupil")
    pm.use_nodes = True
    pb = next(n for n in pm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    pb.inputs["Base Color"].default_value = (0.01, 0.01, 0.015, 1)
    pb.inputs["Roughness"].default_value = 0.3
    for mat in (em, pm):
        if mat.name not in me.materials:
            me.materials.append(mat)
    ie, ip = me.materials.find(em.name), me.materials.find(pm.name)
    bm = bmesh.new()
    bm.from_mesh(me)
    inv = dst.matrix_world.inverted()
    for c, (ry, rz, depth) in eye_pts:
        c = inv @ Vector(c)
        sx = 1 if c.x > 0 else -1
        r = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=1.0)
        vs = r["verts"]
        bmesh.ops.scale(bm, vec=(depth, ry, rz), verts=vs)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(0.25 * sx, 3, "X"), verts=vs)   # angry tilt
        bmesh.ops.translate(bm, vec=c, verts=vs)
        for f in {f for v in vs for f in v.link_faces}:
            f.material_index = ie
            f.smooth = True
        r = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=1.0)    # dark rim around the eye
        vs = r["verts"]
        bmesh.ops.scale(bm, vec=(depth * 0.9, ry * 1.25, rz * 1.35), verts=vs)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(0.25 * sx, 3, "X"), verts=vs)
        bmesh.ops.translate(bm, vec=c - Vector((sx * depth * 0.25, 0, 0)), verts=vs)
        for f in {f for v in vs for f in v.link_faces}:
            f.material_index = ip
            f.smooth = True
        r = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=1.0)
        vs = r["verts"]
        bmesh.ops.scale(bm, vec=(depth * 0.6, ry * 0.22, rz * 0.85), verts=vs)
        bmesh.ops.translate(bm, vec=c + Vector((sx * depth * 0.55, 0, 0)), verts=vs)
        for f in {f for v in vs for f in v.link_faces}:
            f.material_index = ip
            f.smooth = True
    bm.to_mesh(me)
    bm.free()


def add_teeth(teeth, r=0.05):
    """sharp white cone teeth: teeth = [(world base point, +1 up / -1 down, length m)]"""
    import bmesh
    from mathutils import Vector
    tm = bpy.data.materials.get(DST + "Tooth") or bpy.data.materials.new(DST + "Tooth")
    tm.use_nodes = True
    tb = next(n for n in tm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    tb.inputs["Base Color"].default_value = (0.95, 0.95, 0.93, 1)
    tb.inputs["Roughness"].default_value = 0.35
    if tm.name not in me.materials:
        me.materials.append(tm)
    it = me.materials.find(tm.name)
    bm = bmesh.new()
    bm.from_mesh(me)
    inv = dst.matrix_world.inverted()
    for base, sgn, ln in teeth:
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=r, radius2=0.0, depth=ln)
        vs = res["verts"]
        if sgn < 0:                                   # flip so the tip points down
            bmesh.ops.scale(bm, vec=(1, 1, -1), verts=vs)
            bmesh.ops.reverse_faces(bm, faces=list({f for v in vs for f in v.link_faces}))
        bmesh.ops.translate(bm, vec=inv @ Vector(base) + Vector((0, 0, sgn * ln / 2)), verts=vs)
        for f in {f for v in vs for f in v.link_faces}:
            f.material_index = it
    bm.to_mesh(me)
    bm.free()


EYES = g.get("EYES")
if EYES:
    add_eyes(EYES)
TEETH_W = g.get("TEETH_W")
if TEETH_W:
    add_teeth(TEETH_W)
src.hide_set(True)
src.hide_render = True
print(DST, "faces", len(me.polygons))
