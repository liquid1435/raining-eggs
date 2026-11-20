r"""map.json -> Roblox place file with the whole map as real (anchored) parts in Workspace.

  py to_rbxlx.py   -> GROW A ROBOT - MAP.rbxlx here + copy on the Desktop
Includes Lighting (Future, atmosphere, bloom, colour correction, sun rays) and one server Script (MapAnimations)
that moves the demo robots along the conveyor and spins the gears / turbines.
"""
import json
import os
import pathlib
from xml.sax.saxutils import escape

HERE = pathlib.Path(__file__).resolve().parent
data = json.loads((HERE / 'map.json').read_text(encoding='utf-8'))

MAT = {'Plastic': 256, 'SmoothPlastic': 272, 'Neon': 288, 'Wood': 512, 'WoodPlanks': 528, 'Marble': 784, 'Concrete': 816,
       'Pavement': 836, 'Rock': 896, 'DiamondPlate': 1056, 'Foil': 1072, 'Metal': 1088, 'Grass': 1280, 'Fabric': 1312,
       'Glass': 1568, 'Sand': 1296, 'Slate': 800}
SHAPE = {'Ball': 0, 'Block': 1, 'Cylinder': 2}
_mj = HERE.parent / 'game' / 'meshes.json'
MESH_IDS = json.loads(_mj.read_text(encoding='utf-8')) if _mj.exists() else {}      # Blender meshes the user imported: name -> id, size
FACE = {'Right': 0, 'Top': 1, 'Back': 2, 'Left': 3, 'Bottom': 4, 'Front': 5}
_ref = [0]


PRECISE = ('LolliTop', 'LolliStick', 'Cake', 'CandyCane', 'IceCream', 'Gumdrop')

def ref():
    _ref[0] += 1
    return f'RBX{_ref[0]}'


def f(v):
    return f'{v:.4f}'.rstrip('0').rstrip('.') if isinstance(v, float) else str(v)


def c3(c):
    return f'<R>{c[0] / 255:.4f}</R><G>{c[1] / 255:.4f}</G><B>{c[2] / 255:.4f}</B>'


def cframe(p, r, name='CFrame'):
    keys = ['R00', 'R01', 'R02', 'R10', 'R11', 'R12', 'R20', 'R21', 'R22']
    return (f'<CoordinateFrame name="{name}"><X>{f(p[0])}</X><Y>{f(p[1])}</Y><Z>{f(p[2])}</Z>' +
            ''.join(f'<{k}>{f(v)}</{k}>' for k, v in zip(keys, r)) + '</CoordinateFrame>')


def udim2(name, xs, xo, ys, yo):
    return f'<UDim2 name="{name}"><XS>{xs}</XS><XO>{xo}</XO><YS>{ys}</YS><YO>{yo}</YO></UDim2>'


def font(name, family='FredokaOne', weight=400):
    return f'<Font name="{name}"><Family><url>rbxasset://fonts/families/{family}.json</url></Family><Weight>{weight}</Weight><Style>Normal</Style></Font>'


def item(cls, props, children=''):
    return f'<Item class="{cls}" referent="{ref()}"><Properties>{props}</Properties>{children}</Item>'


def label(text, pos_y, h, color, stroke, fam='FredokaOne', weight=400, pad=0.04):
    st = item('UIStroke', f'<string name="Name">UIStroke</string><Color3 name="Color">{c3(stroke)}</Color3><float name="Thickness">4</float>')
    return item('TextLabel', '<string name="Name">Label</string><float name="BackgroundTransparency">1</float>' +
                udim2('Size', 1 - 2 * pad, 0, h, 0) + udim2('Position', pad, 0, pos_y, 0) + font('FontFace', fam, weight) +
                f'<string name="Text">{escape(text)}</string><Color3 name="TextColor3">{c3(color)}</Color3>'
                '<bool name="TextScaled">true</bool><bool name="TextWrapped">true</bool>', st)


def surface_gui(s):
    bg = item('UIGradient', '<string name="Name">UIGradient</string>'
              f'<ColorSequence name="Color">0 {s["bg1"][0] / 255:.4f} {s["bg1"][1] / 255:.4f} {s["bg1"][2] / 255:.4f} 0 '
              f'1 {s["bg2"][0] / 255:.4f} {s["bg2"][1] / 255:.4f} {s["bg2"][2] / 255:.4f} 0 </ColorSequence><float name="Rotation">90</float>')
    corner = item('UICorner', '<string name="Name">UICorner</string><UDim name="CornerRadius"><S>0</S><O>18</O></UDim>')
    stroke = item('UIStroke', f'<string name="Name">UIStroke</string><Color3 name="Color">{c3(s["stroke"])}</Color3><float name="Thickness">8</float>'
                  '<token name="ApplyStrokeMode">1</token>')
    if s.get('sub'):
        labels = label(s['title'], 0.06, 0.58, s['fg'], s['stroke'], pad=s.get('pad', 0.04)) + label(s['sub'], 0.64, 0.28, (235, 240, 255), s['stroke'], 'BuilderSans', 700)
    else:
        labels = label(s['title'], 0.14, 0.72, s['fg'], s['stroke'], pad=s.get('pad', 0.04))
    frame = item('Frame', '<string name="Name">Bg</string><Color3 name="BackgroundColor3"><R>1</R><G>1</G><B>1</B></Color3>'
                 '<int name="BorderSizePixel">0</int>' + udim2('Size', 1, 0, 1, 0), bg + corner + stroke + labels)
    return item('SurfaceGui', f'<string name="Name">Sign{s["face"]}</string><token name="Face">{FACE[s["face"]]}</token>'
                f'<token name="SizingMode">1</token><float name="PixelsPerStud">{s.get("pps", 20)}</float>'
                '<float name="LightInfluence">0</float><float name="Brightness">1.3</float>', frame)


def light_item(l):
    kind = l['kind']
    props = (f'<string name="Name">{kind}</string><Color3 name="Color">{c3(l["c"])}</Color3><float name="Brightness">{l["br"]}</float>'
             f'<float name="Range">{l["range"]}</float><bool name="Shadows">false</bool>')
    if kind in ('SpotLight', 'SurfaceLight'):
        props += f'<token name="Face">{FACE[l.get("face", "Bottom")]}</token><float name="Angle">{l.get("angle", 90)}</float>'
    return item(kind, props)


def part_xml(p):
    cls = 'SpawnLocation' if p.get('spawn') else p['cls']
    mesh = MESH_IDS.get(p.get('mesh'))
    if mesh:
        cls = 'MeshPart'
    col = 0xFF000000 | (p['c'][0] << 16) | (p['c'][1] << 8) | p['c'][2]
    name = p.get('name') or ('Spawn' if p.get('spawn') else 'Part')
    props = (f'<string name="Name">{name}</string><bool name="Anchored">true</bool>' + cframe(p['p'], p['r']) +
             f'<Color3uint8 name="Color3uint8">{col}</Color3uint8><token name="Material">{MAT.get(p["m"], 272)}</token>'
             f'<Vector3 name="size"><X>{f(p["size"][0])}</X><Y>{f(p["size"][1])}</Y><Z>{f(p["size"][2])}</Z></Vector3>'
             '<token name="TopSurface">0</token><token name="BottomSurface">0</token>')
    if cls in ('Part', 'SpawnLocation'):
        props += f'<token name="shape">{SHAPE[p["shape"]]}</token>'
    if mesh:
        s = mesh['size']
        props += (f'<Content name="MeshContent"><uri>{mesh["id"]}</uri></Content>'
                  f'<Vector3 name="InitialSize"><X>{s[0]}</X><Y>{s[1]}</Y><Z>{s[2]}</Z></Vector3>' +
                  ('<bool name="CanQuery">false</bool>' if p.get('cancollide') is False else '<token name="CollisionFidelity">3</token>'))
        # v124 (user: the candy designs / the cake "deform" while walking): Roblox swaps in simpler LOD meshes with
        # distance (RenderFidelity Automatic). Detailed candy meshes keep full detail: Precise (token 1).
        if any(k in p['mesh'] for k in PRECISE):
            props += '<token name="RenderFidelity">1</token>'
    if p.get('transparency'):
        props += f'<float name="Transparency">{p["transparency"]}</float>'
    if p.get('reflectance'):
        props += f'<float name="Reflectance">{p["reflectance"]}</float>'
    if p.get('cancollide') is False:
        props += '<bool name="CanCollide">false</bool>'
    if p['m'] == 'Neon' or p.get('transparency', 0) > 0.5 or p.get('noshadow'):
        props += '<bool name="CastShadow">false</bool>'
    if cls == 'SpawnLocation':
        props += '<bool name="Neutral">true</bool><int name="Duration">0</int>'
    kids = ''.join(light_item(l) for l in p.get('lights', [])) + ''.join(surface_gui(s) for s in p.get('signs', []))
    # v125 precise hitboxes: the server reads these (see PRECISE HITBOXES in Server.server.lua)
    for key, nm in (('precise', 'PreciseId'), ('hitboxof', 'HitboxOf')):
        if p.get(key):
            kids += item('IntValue', f'<string name="Name">{nm}</string><int64 name="Value">{p[key]}</int64>')
    if p.get('solidafter'):
        kids += item('BoolValue', '<string name="Name">SolidAfter</string><bool name="Value">true</bool>')
    if p.get('headmesh'):                                   # classic Roblox head
        kids += item('SpecialMesh', '<string name="Name">Mesh</string><token name="MeshType">0</token>'
                     '<Vector3 name="Scale"><X>1.25</X><Y>1.25</Y><Z>1.25</Z></Vector3>')
    if p.get('face'):
        kids += item('Decal', '<string name="Name">face</string><Content name="Texture"><url>rbxasset://textures/face.png</url></Content>'
                     f'<token name="Face">{FACE["Front"]}</token>')
    return item(cls, props, kids)


# ---------------------------------------------------------------- hierarchy of Models
class Node:
    def __init__(self, name):
        self.name = name
        self.kids = {}
        self.order = []
        self.parts = []


root = Node('Map')
for p in data['parts']:
    path = p['g'].split('/')[1:]
    n = root
    for seg in path:
        if seg not in n.kids:
            n.kids[seg] = Node(seg.split('#')[0])
            n.order.append(seg)
        n = n.kids[seg]
    n.parts.append(p)


def node_xml(n, cls='Model'):
    body = ''.join(part_xml(p) for p in n.parts) + ''.join(node_xml(n.kids[k], 'Folder' if n is root and n.kids[k].name in
                                                                                ('Ground', 'Gates', 'Water', 'Plaza') else 'Model') for k in n.order)
    if any(p.get('rig') for p in n.parts):                  # R6 character: anchored statue with a Humanoid
        body += item('Humanoid', '<string name="Name">Humanoid</string><token name="RigType">0</token>'
                     '<token name="DisplayDistanceType">2</token><token name="HealthDisplayType">2</token>'
                     '<bool name="RequiresNeck">false</bool><bool name="BreakJointsOnDeath">false</bool>')
    return item(cls, f'<string name="Name">{escape(n.name)}</string>', body)


lighting = item('Lighting', '<string name="Name">Lighting</string><token name="Technology">4</token>'
                '<float name="ClockTime">14.3</float><float name="Brightness">1.7</float>'
                '<Color3 name="Ambient"><R>0.32</R><G>0.33</G><B>0.38</B></Color3>'
                '<Color3 name="OutdoorAmbient"><R>0.55</R><G>0.56</G><B>0.6</B></Color3>'
                '<float name="EnvironmentDiffuseScale">1</float><float name="EnvironmentSpecularScale">1</float>'
                '<bool name="GlobalShadows">true</bool><float name="GeographicLatitude">35</float><float name="ShadowSoftness">0.25</float>',
                item('Atmosphere', '<string name="Name">Atmosphere</string><float name="Density">0.28</float><float name="Offset">0.2</float>'
                     '<Color3 name="Color"><R>0.78</R><G>0.84</G><B>0.95</B></Color3><Color3 name="Decay"><R>0.42</R><G>0.5</G><B>0.66</B></Color3>'
                     '<float name="Glare">0.25</float><float name="Haze">1.2</float>') +
                item('BloomEffect', '<string name="Name">Bloom</string><float name="Intensity">0.25</float><float name="Size">24</float><float name="Threshold">2</float>') +
                item('ColorCorrectionEffect', '<string name="Name">ColorCorrection</string><float name="Saturation">0.18</float><float name="Contrast">0.08</float><float name="Brightness">-0.03</float>'
                     '<Color3 name="TintColor"><R>1</R><G>0.99</G><B>0.97</B></Color3>') +
                item('SunRaysEffect', '<string name="Name">SunRays</string><float name="Intensity">0.05</float><float name="Spread">0.6</float>'))

import sys  # noqa: E402

# py to_rbxlx.py "JOC v1"  -> also puts the game scripts in and writes Desktop\...\RAINING EGGS - JOC v1.rbxlx
TAG = sys.argv[1] if len(sys.argv) > 1 else None
SRC = HERE.parent / 'game'


def scr(cls, name, path):
    s = path.read_text(encoding='utf-8').replace(']]>', ']]]]><![CDATA[>')
    return item(cls, f'<string name="Name">{name}</string><ProtectedString name="Source"><![CDATA[{s}]]></ProtectedString>')


def assets_folder():
    """Blender meshes the user imported once (asset ids harvested by blender\\harvest_meshes.py) -> ReplicatedStorage.Assets"""
    src = SRC / 'meshes.json'
    if not src.exists():
        return ''
    v3 = lambda name, s: f'<Vector3 name="{name}"><X>{s[0]}</X><Y>{s[1]}</Y><Z>{s[2]}</Z></Vector3>'
    kids = ''
    for k, (name, m) in enumerate(json.loads(src.read_text(encoding='utf-8')).items()):
        kids += item('MeshPart', f'<string name="Name">{name}</string><bool name="Anchored">true</bool>'
                     f'<Content name="MeshContent"><uri>{m["id"]}</uri></Content>' + (f'<Content name="TextureContent"><uri>{m["tex"]}</uri></Content>' if m.get('tex') else '') + v3('InitialSize', m['size']) + v3('size', m['size']) +
                     cframe([k % 8 * 7, 3, k // 8 * 7], [1, 0, 0, 0, 1, 0, 0, 0, 1]) +
                     '<Color3uint8 name="Color3uint8">4294967295</Color3uint8><token name="Material">272</token>'
                     '<bool name="CanCollide">false</bool><bool name="CanTouch">false</bool><bool name="CanQuery">false</bool>')
    return item('Folder', '<string name="Name">Assets</string>', kids) + props_meta()


def props_meta():
    """game\\props_meta.json (written by blender\\gen_props.py) -> ModuleScript ReplicatedStorage.PropsMeta"""
    src = SRC / 'props_meta.json'
    if not src.exists():
        return ''
    lua = lambda v: '{ ' + ', '.join(map(str, v)) + ' }' if isinstance(v, list) else str(v)
    rows = ''.join(f'\t["{n}"] = {{ ' + ', '.join(f'{k} = {lua(v)}' for k, v in m.items()) + ' },\n'
                   for n, m in json.loads(src.read_text(encoding='utf-8')).items())
    (SRC / 'PropsMeta.lua').write_text('-- generated from props_meta.json: where each Blender mesh sits from its model origin\nreturn {\n' + rows + '}\n', encoding='utf-8')
    return scr('ModuleScript', 'PropsMeta', SRC / 'PropsMeta.lua')


def bigegg():
    """BIG EGG DROP (Codex, E:\\rainingeggs\\event_bigegg): VFX modules -> ReplicatedStorage.BigEggFX, animation clips -> ReplicatedStorage.BigEggAnims"""
    ev = HERE.parent / 'event_bigegg'
    if not ev.exists():
        return ''
    mods = ''.join(scr('ModuleScript', f.stem, f) for f in sorted((ev / 'roblox').glob('*.lua')))   # FX, BigEggVFX, WeaponFX, GoldenPortalVFX...
    clips = ''
    for f in sorted((ev / 'animations').glob('*.rbxmx')):
        s = f.read_text(encoding='utf-8')
        clips += s[s.index('<Item'):s.rindex('</roblox>')]
    return item('Folder', '<string name="Name">BigEggFX</string>', mods) + item('Folder', '<string name="Name">BigEggAnims</string>', clips)


GAME = ''
if TAG:
    GAME = (item('ReplicatedStorage', '<string name="Name">ReplicatedStorage</string>', scr('ModuleScript', 'Config', SRC / 'Config.lua') + scr('ModuleScript', 'Sfx', SRC / 'Sfx.lua') + scr('ModuleScript', 'UIMenus', SRC / 'UIMenus.lua') + scr('ModuleScript', 'HatchVFX', SRC / 'HatchVFX.lua') + scr('ModuleScript', 'PetAnim', SRC / 'PetAnim.lua') + scr('ModuleScript', 'PetAnimData', SRC / 'PetAnimData.lua') + assets_folder() + bigegg() +
                 item('Folder', '<string name="Name">Shared</string>', ''.join(
                     scr('ModuleScript', n, SRC / 'treadmills' / f'{n}.lua') for n in ('TreadmillData', 'TreadmillBuilder', 'TreadmillConfig')))) +
            item('ServerScriptService', '<string name="Name">ServerScriptService</string>', scr('Script', 'GameServer', SRC / 'Server.server.lua')) +
            item('StarterPlayer', '<string name="Name">StarterPlayer</string>',
                 item('StarterPlayerScripts', '<string name="Name">StarterPlayerScripts</string>', scr('LocalScript', 'GameClient', SRC / 'Client.client.lua'))))

xml = ('<?xml version="1.0" encoding="utf-8"?>\n<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
       'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">' +
       item('Workspace', '<string name="Name">Workspace</string>', node_xml(root)) + lighting + GAME +
       '</roblox>')
out = HERE / 'RAINING EGGS - MAP.rbxlx'
out.write_text(xml, encoding='utf-8')
import xml.dom.minidom  # noqa: E402  (well-formed check)
xml.dom.minidom.parseString(out.read_bytes())
home = pathlib.Path(os.environ.get('USERPROFILE') or os.environ['HOME'])   # USERPROFILE on Windows, HOME on a Mac
desk = home / 'Desktop' / 'youtube' / 'roblox' / (f'RAINING EGGS - {TAG}.rbxlx' if TAG else 'RAINING EGGS - HARTA.rbxlx')
desk.parent.mkdir(parents=True, exist_ok=True)   # (a teammate's PC may not have this folder yet)
desk.write_bytes(out.read_bytes())
print(f'wrote {out.name} ({out.stat().st_size // 1024} KB), {len(data["parts"])} parts -> {desk}')
