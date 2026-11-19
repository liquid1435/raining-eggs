r"""Reads the MeshParts the user imported (File > Import 3D) out of a saved .rbxlx and adds name -> asset id + size
to ..\game\meshes.json, so to_rbxlx.py can put them in the place file and nobody has to import again.

  py harvest_meshes.py "C:\...\RAINING EGGS - JOC v9.rbxlx"
"""
import json, pathlib, re, sys

t = open(sys.argv[1], encoding='utf-8', errors='replace').read()
dst = pathlib.Path(__file__).resolve().parent.parent / 'game' / 'meshes.json'
out = json.loads(dst.read_text(encoding='utf-8')) if dst.exists() else {}
before = len(out)
old_ids = {k: v['id'] for k, v in out.items()}
PRE = ('Pet_', 'Egg_', 'Fence_', 'Tread_', 'TreadNeon_', 'Map_', 'Shop_', 'ShopNeon_', 'Basket_', 'BasketNeon_')
seen = {}
for m in re.finditer(r'<Item class="MeshPart"', t):
    chunk = t[m.start():m.start() + 7000]
    chunk = chunk[:chunk.find('</Properties>')]
    name = re.search(r'<string name="Name">([^<]*)</string>', chunk).group(1)
    uri = re.search(r'<Content name="MeshContent">\s*<uri>([^<]+)</uri>', chunk) or re.search(r'<Content name="MeshId">\s*<url>([^<]+)</url>', chunk)

    def v(prop):
        r = re.search(r'<Vector3 name="%s">\s*<X>([^<]+)</X>\s*<Y>([^<]+)</Y>\s*<Z>([^<]+)</Z>' % prop, chunk)
        return [float(x) for x in r.groups()] if r else None

    tex = re.search(r'<Content name="TextureContent">\s*<uri>(rbxassetid://[^<]+)</uri>', chunk) or re.search(r'<Content name="TextureID">\s*<url>(rbxassetid://[^<]+)</url>', chunk)
    if uri and name.startswith(PRE) and v('InitialSize'):
        if name in seen and 'tex' in seen[name] and not tex:
            continue  # a copy with a texture (new import) wins over an old copy without one
        if name in seen and name in old_ids and uri.group(1) == old_ids[name] and seen[name]['id'] != old_ids[name]:
            continue  # a re-imported (fixed) model wins over the old copy still sitting in ReplicatedStorage.Assets
        out[name] = {'id': uri.group(1), 'size': v('InitialSize')}
        if tex:
            out[name]['tex'] = tex.group(1)
        seen[name] = out[name]
dst.write_text(json.dumps(out, indent=1), encoding='utf-8')
print(f'{before} -> {len(out)} meshes in {dst}')
print('fence:', [n for n in out if n.startswith('Fence_')], ' treadmills:', sum(1 for n in out if n.startswith('Tread_')), '+ neon', sum(1 for n in out if n.startswith('TreadNeon_')))
