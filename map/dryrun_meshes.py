"""pretend every Blender mesh in props_meta.json is imported (fake ids), build the map, then restore meshes.json"""
import json, pathlib, shutil, subprocess, sys
G = pathlib.Path(__file__).resolve().parent.parent / 'game'
src, bak = G / 'meshes.json', G / 'meshes.json.dry'
shutil.copyfile(src, bak)
try:
    d = json.loads(src.read_text(encoding='utf-8'))
    pm = json.loads((G / 'props_meta.json').read_text(encoding='utf-8'))
    for k in pm:
        if k.startswith(('Map_', 'Shop')):
            d.setdefault(k, {'id': 'rbxassetid://1', 'size': pm[k]['size']})
    src.write_text(json.dumps(d), encoding='utf-8')
    out = subprocess.run([sys.executable, str(G.parent / 'map' / 'gen_map.py')], capture_output=True, text=True)
    print(out.stdout[-600:], out.stderr[-2000:])
finally:
    shutil.copyfile(bak, src)
    bak.unlink()
    subprocess.run([sys.executable, str(G.parent / 'map' / 'gen_map.py')], capture_output=True)
