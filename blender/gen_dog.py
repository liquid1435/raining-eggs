"""Zone 1 pet: DOG (Common). Smooth organic body (metaballs) + brick pattern only as texture, flat clean colour zones.
Reuses the helpers of wyvern_rig.py. Run in Blender:  exec(open(p).read(), {'__file__': p, '__name__': '__main__'})
Faces -Y. ~1.6 m tall."""
import bpy, sys, math, pathlib, importlib
from mathutils import Vector, Euler
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wyvern_rig as W
importlib.reload(W)
from wyvern_rig import brick_material, flat_material, ellipsoid, tube, link

# linear colours
TAN = (0.62, 0.30, 0.09)
WHITE = (0.86, 0.84, 0.80)
DARK = (0.22, 0.09, 0.03)
PINK = (0.85, 0.25, 0.32)
RED = (0.75, 0.03, 0.03)
GOLD = (1.0, 0.62, 0.08)


def build():
    W.clear_scene()
    M = {
        "tan": brick_material("Dog_Tan", TAN, mortar_mul=0.62),
        "white": brick_material("Dog_White", WHITE, mortar_mul=0.75),
        "dark": brick_material("Dog_Dark", DARK, mortar_mul=0.6),
        "black": flat_material("Dog_Black", (0.01, 0.01, 0.012), rough=0.15),
        "shine": flat_material("Dog_Shine", (1, 1, 1), rough=0.2, emit_strength=1.0),
        "pink": flat_material("Dog_Tongue", PINK, rough=0.35),
        "red": flat_material("Dog_Collar", RED, rough=0.4),
        "gold": flat_material("Dog_Tag", GOLD, rough=0.25),
    }
    M["gold"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.9

    mb = bpy.data.metaballs.new("DogMB")
    mb.resolution = mb.render_resolution = 0.025
    mb.threshold = 0.6
    ob = link(bpy.data.objects.new("Dog", mb))

    def ball(co, r):
        e = mb.elements.new(type='BALL'); e.co, e.radius, e.stiffness = co, r, 2.0

    def ell(co, size, rot=(0, 0, 0)):
        e = mb.elements.new(type='ELLIPSOID'); e.co, e.radius, e.stiffness = co, 1.0, 2.0
        e.size_x, e.size_y, e.size_z = size
        e.rotation = Euler(rot).to_quaternion()

    def cap(a, b, r):
        a, b = Vector(a), Vector(b); d = b - a
        e = mb.elements.new(type='CAPSULE'); e.co = (a + b) / 2
        e.radius, e.stiffness, e.size_x = r, 2.0, d.length / 2
        e.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized())

    ell((0, 0.1, 0.72), (0.42, 0.58, 0.42))           # chunky body
    ball((0, -0.3, 0.82), 0.62)                       # chest
    cap((0, -0.34, 0.95), (0, -0.46, 1.2), 0.38)      # neck
    ball((0, -0.5, 1.42), 0.78)                       # big round head
    ell((0, -0.88, 1.3), (0.24, 0.26, 0.18))          # muzzle
    ell((0, -0.42, 1.66), (0.27, 0.26, 0.16))         # forehead dome
    for s in (-1, 1):
        cap((s * 0.2, -0.32, 0.6), (s * 0.21, -0.36, 0.13), 0.22)    # front legs (short)
        ell((s * 0.21, -0.42, 0.09), (0.15, 0.19, 0.1))             # front paws
        ell((s * 0.23, 0.36, 0.62), (0.2, 0.27, 0.3))               # thighs
        cap((s * 0.23, 0.42, 0.5), (s * 0.22, 0.38, 0.13), 0.2)     # back legs
        ell((s * 0.22, 0.3, 0.09), (0.15, 0.19, 0.1))               # back paws
        ell((s * 0.27, -0.66, 1.4), (0.13, 0.13, 0.13))             # cheeks
    cap((0, 0.6, 0.85), (0, 0.76, 1.0), 0.15)         # tail, curving up
    cap((0, 0.76, 1.0), (0, 0.8, 1.2), 0.12)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target='MESH')
    dog = bpy.context.view_layer.objects.active
    me = dog.data
    me.materials.clear()
    for k in ("tan", "white", "dark"):
        me.materials.append(M[k])
    for p in me.polygons:
        c, n = p.center, p.normal
        white = (c.y < -0.74 and c.z < 1.42) \
            or (n.y < -0.25 and abs(c.x) < 0.2 and 0.45 < c.z < 1.12 and c.y < -0.2) \
            or (n.z < -0.35 and abs(c.x) < 0.24 and -0.3 < c.y < 0.45 and c.z > 0.35) \
            or c.z < 0.17 \
            or (c.y > 0.6 and c.z > 1.08) \
            or (abs(c.x) < 0.06 and c.y < -0.55 and c.z > 1.5 and n.y < -0.2)     # white stripe on the forehead
        dark = (not white) and c.z > 1.0 and 0.05 < c.y < 0.45 and n.z > 0.55 and abs(c.x) < 0.22   # saddle patch
        p.material_index = 1 if white else (2 if dark else 0)
        p.use_smooth = True

    # ears (floppy, dark), nose, eyes, mouth, tongue, collar
    for s in (-1, 1):
        tube("Ear", [(s * 0.34, -0.4, 1.78), (s * 0.47, -0.42, 1.7), (s * 0.52, -0.44, 1.5), (s * 0.5, -0.46, 1.3),
                     (s * 0.46, -0.47, 1.2)], [0.1, 0.15, 0.15, 0.12, 0.05], M["dark"], seg=12)
        ellipsoid("Eye", (s * 0.2, -0.95, 1.5), (0.075, 0.05, 0.095), M["black"], rot=(0, 0, s * math.radians(-18)))
        ellipsoid("Shine", (s * 0.18, -1.0, 1.55), (0.025, 0.012, 0.028), M["shine"])
        ellipsoid("Shine2", (s * 0.225, -0.99, 1.47), (0.012, 0.008, 0.014), M["shine"])
        ellipsoid("Brow", (s * 0.2, -0.95, 1.63), (0.07, 0.03, 0.02), M["dark"], rot=(0, s * math.radians(-12), 0))
    ellipsoid("Nose", (0, -1.05, 1.36), (0.075, 0.05, 0.05), M["black"])
    ellipsoid("NoseShine", (0.025, -1.09, 1.385), (0.02, 0.008, 0.012), M["shine"])
    tube("MouthL", [(0, -1.06, 1.3), (0.05, -1.05, 1.24), (0.11, -1.0, 1.25)], [0.012, 0.012, 0.0], M["black"], seg=6)
    tube("MouthR", [(0, -1.06, 1.3), (-0.05, -1.05, 1.24), (-0.11, -1.0, 1.25)], [0.012, 0.012, 0.0], M["black"], seg=6)
    ellipsoid("Tongue", (0.02, -1.04, 1.17), (0.05, 0.03, 0.08), M["pink"], rot=(math.radians(15), 0, 0))
    # collar = ring of the neck + gold tag
    pts = [(math.cos(a) * 0.4, -0.44 + math.sin(a) * 0.37, 1.1 - 0.07 * math.sin(a)) for a in
           [2 * math.pi * k / 24 for k in range(25)]]
    tube("Collar", pts, [0.055] * 25, M["red"], seg=8)
    ellipsoid("Tag", (0, -0.86, 1.0), (0.07, 0.025, 0.08), M["gold"])

    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            o.select_set(True)
    bpy.context.view_layer.objects.active = dog
    bpy.ops.object.join()
    dog = bpy.context.view_layer.objects.active
    dog.name = dog.data.name = "Pet_Dog"
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    except (AttributeError, RuntimeError):
        bpy.ops.object.shade_smooth()
    d = dog.dimensions
    for k in ("tan", "white", "dark"):
        M[k].node_tree.nodes["BrickMapping"].inputs["Scale"].default_value = (d.x / 0.12, d.y / 0.12, d.z / 0.12)
    print("dog faces", len(dog.data.polygons), "dims", tuple(round(x, 2) for x in d))
    return dog


if __name__ == "__main__":
    build()
