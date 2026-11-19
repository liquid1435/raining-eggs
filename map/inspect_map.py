import json, pathlib, collections
d = json.loads((pathlib.Path(__file__).parent / 'map.json').read_text(encoding='utf-8'))
P = d['parts']
print('keys', [k for k in d if k != 'parts'], 'sample', P[0])
names = collections.Counter(p.get('name') or 'Part' for p in P)
print('NAMES', dict(names))
grp = collections.defaultdict(lambda: [1e9, -1e9, 1e9, -1e9, 1e9, -1e9, 0])
for p in P:
    g = '/'.join(p['g'].split('/')[:3])
    b = grp[g]
    x, y, z = p['p']
    b[0] = min(b[0], x); b[1] = max(b[1], x); b[2] = min(b[2], y); b[3] = max(b[3], y); b[4] = min(b[4], z); b[5] = max(b[5], z); b[6] += 1
for g, b in grp.items():
    print(g, [round(v) for v in b])
for nm in ['PenFloor', 'Treadmill', 'OwnerSign', 'DemoEgg', 'Wall', 'ShopPad', 'HeroEgg', 'Decor', 'Bounce', 'DemoPet']:
    ps = [p for p in P if p.get('name') == nm][:4]
    for p in ps:
        print(nm, p['g'], [round(v, 1) for v in p['p']], [round(v, 1) for v in p['size']], p['shape'], p.get('cancollide'), p.get('transparency'))
sub = collections.Counter('/'.join(p['g'].split('/')[:4]) for p in P if 'Zone1_' in p['g'] or 'Base1' in p['g'] or 'Gates' in p['g'])
print(dict(sub))
for p in P:
    if 'Gates' in p['g'] and p.get('signs'):
        print('GATE', p['g'], p.get('name'), [round(v, 1) for v in p['p']], [round(v, 1) for v in p['size']], p['signs'][0]['title'], p['signs'][0].get('sub'))
