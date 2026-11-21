import json, pathlib
NEW = pathlib.Path(r'E:\rainingeggs\codex_pets_v2'); OLD = pathlib.Path(r'E:\rainingeggs\codex_pets_all')
OUT = pathlib.Path(r'E:\rainingeggs\codex_pets_game'); OUT.mkdir(exist_ok=True)
R = ['Common', 'Uncommon', 'Rare', 'Epic', 'Legendary']
ZONES = {
 1: ['Fox', 'Owl', 'Stag', 'Lion', 'Pegasus'],
 2: ['Chameleon', 'Red Panda', 'Axolotl', 'Jackalope', 'Kitsune'],
 3: ['Fennec Fox', 'Cockatoo', 'Toucan', 'Peacock', 'Unicorn'],
 4: ['Penguin', 'Pangolin', 'Komodo Dragon', 'Mandrill', 'Qilin'],
 5: ['Manta Ray', 'Shark', 'Narwhal', 'Humpback Whale', 'Kraken'],
 6: ['Wolf', 'Crocodile', 'Basilisk', 'Cerberus', 'Fenrir'],
 7: ['Eagle', 'Bear', 'Snow Leopard', 'Griffin', 'Thunderbird'],
 8: ['Octopus', 'Sphinx', 'Hydra', 'Phoenix', 'Eastern Dragon'],
 9: ['Snowy Owl', 'Swan', 'Arctic Fox', 'Sky Whale', 'Seraph Lion'],
 10: ['Golden Pheasant', 'Gold Scarab', 'Royal Tiger', 'Golden Ram', 'Celestial Dragon'],
}
new = {e['name']: e for e in json.loads((NEW / 'manifest.json').read_text(encoding='utf-8'))}
old = json.loads((OLD / 'manifest.json').read_text(encoding='utf-8'))
out = []
used = set()
for z, names in ZONES.items():
    for i, n in enumerate(names):
        e = dict(new[n]); used.add(n)
        e['zone_number'], e['rarity'], e['folder'] = z, R[i], str(NEW / e['folder'])
        out.append(e)
assert used == set(new), set(new) - used
(OUT / 'manifest.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
print(len(out), 'pets')
