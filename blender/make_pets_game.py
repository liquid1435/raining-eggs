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
 10: ['Golden Pheasant', 'Golden Lynx', 'Royal Tiger', 'Golden Ram', 'Celestial Dragon'],
 11: ['Star Kitten', 'Moon Bunny', 'Comet Fox', 'Nebula Wolf', 'Galaxy Dragon'],
 12: ['Moon Mouse', 'Crater Pup', 'Rocket Rabbit', 'Astro Panda', 'Lunar Phoenix'],
 13: ['Nebula Jelly', 'Star Fish', 'Comet Seahorse', 'Void Shark', 'Galaxy Kraken'],
 14: ['Meteor Mole', 'Rock Golem Pup', 'Orbit Owl', 'Asteroid Armadillo', 'Meteor Rhino'],
 15: ['Ember Cat', 'Flare Fox', 'Magma Turtle', 'Solar Phoenix', 'Sun Lion'],
 16: ['Frost Penguin', 'Comet Seal', 'Ice Yeti Cub', 'Glacier Mammoth', 'Aurora Stag'],
 17: ['Glow Gecko', 'Alien Frog', 'Tentacle Pup', 'Three-Eyed Monkey', 'Xeno Raptor'],
 18: ['Void Cat', 'Shadow Bat', 'Eclipse Wolf', 'Gravity Bear', 'Singularity Serpent'],
 19: ['Robo Dog', 'Mecha Bunny', 'Laser Owl', 'Drone Fox', 'Titan Mech Lion'],
 20: ['Star Unicorn', 'Cosmic Pegasus', 'Celestial Tiger', 'Astral Griffin', 'Universe Dragon'],
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
# v153: variants 2 and 3 of every rarity (Codex models 101-200, manifest field "variant")
for n, e0 in new.items():
    if e0.get('variant', 1) > 1:
        e = dict(e0); used.add(n)
        e['folder'] = str(NEW / e['folder'])
        out.append(e)
assert used == set(new), set(new) - used
(OUT / 'manifest.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
# v139: world 2 only (zones 11-20) for a small FBX import
W2 = pathlib.Path(r'E:\rainingeggs\codex_pets_game_w2'); W2.mkdir(exist_ok=True)
(W2 / 'manifest.json').write_text(json.dumps([e for e in out if e['zone_number'] > 10], indent=1), encoding='utf-8')
# v153: variants only, split in two halves for the Studio import (big FBX files fail silently)
for tag, lo, hi in (('va', 1, 5), ('vb', 6, 10)):
    D = pathlib.Path(r'E:\rainingeggs\codex_pets_game_' + tag); D.mkdir(exist_ok=True)
    (D / 'manifest.json').write_text(json.dumps([e for e in out if e.get('variant', 1) > 1 and lo <= e['zone_number'] <= hi], indent=1), encoding='utf-8')
print(len(out), 'pets')
