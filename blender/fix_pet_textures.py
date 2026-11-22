r"""v165: crisp, coloured pet textures for Roblox.

1. Codex's _Gold / _Rainbow atlases are GREY (they were made as the base for the live flowing coat, PetCoatFlow),
   so anywhere the live coat does not run (PETS menu viewports, a failed EditableImage) Gold / Rainbow pets were grey.
   Here they are coloured with the same formula as game/PetCoatFlow.lua at time 0 (Flow map = phase, Lum map = light).
2. The atlases are 256 px with one tiny cell per voxel face; Roblox filters textures smoothly, so neighbour cells bled
   into each other (blurry colours, wrong-coloured streaks). Every atlas is scaled up x4 with NEAREST (1024 px).

  py blender\fix_pet_textures.py   -> E:\rainingeggs\pet_tex\<model folder>\<stem>.png / _Gold.png / _Rainbow.png
(pack_codex_pets.py uses these when they exist)
"""
import colorsys, json, math, pathlib
from PIL import Image

SRC = pathlib.Path(r'E:\rainingeggs\codex_pets_v2')
OUT = pathlib.Path(r'E:\rainingeggs\pet_tex')
UP = 4


def channels(tier, phase):
    h = phase / 256
    value, sat = 1.0, 1.0
    if tier == 'Gold':
        d = abs(h - .5)
        value = .5 + .5 * d + .9 * (1 - 2 * d) ** 18
        sat = 1 - .2 * d
        h = .115 + .03 * d
    r, g, b = colorsys.hsv_to_rgb(h % 1, sat, 1)
    return [(c * value) ** (1 / 2.2) for c in (r, g, b)]


def lut(tier):
    t = {}
    for phase in range(256):
        rgb = channels(tier, phase)
        for lum in range(256):
            chroma = min(max((lum - 24) / 32, 0), 1) * min(max((255 - lum) / 12, 0), 1)
            value = lum + 52 * (1 - lum / 255) * chroma
            if tier == 'Gold':
                value = min(255, 46 + lum * 0.95 + 40 * (1 - lum / 255) * chroma)
                chroma = max(chroma, 0.85)
            t[phase, lum] = tuple(min(max(round(value * (1 + chroma * (c - 1))), 0), 255) for c in rgb)
    return t


LUT = {'Gold': lut('Gold'), 'Rainbow': lut('Rainbow')}
# v165: the PetCoatFlow gold came out olive in a still image -> a bright gold ramp by light (+ a little shine by phase)
GOLD = [(0.0, (96, 58, 8)), (0.35, (196, 128, 20)), (0.65, (255, 196, 46)), (0.85, (255, 226, 110)), (1.0, (255, 246, 196))]


def gold(phase, lum):
    t = min(1.0, (lum / 255) ** 0.75 * 1.08 + 0.12 * max(0.0, math.cos((phase / 256) * 2 * math.pi)) ** 8)
    for (a, ca), (b, cb) in zip(GOLD, GOLD[1:]):
        if t <= b:
            k = (t - a) / (b - a)
            return tuple(round(x + (y - x) * k) for x, y in zip(ca, cb))
    return GOLD[-1][1]


LUT['Gold'] = {(ph, lm): gold(ph, lm) for ph in range(256) for lm in range(256)}
man = json.loads((SRC / 'manifest.json').read_text(encoding='utf-8'))
import os
if os.environ.get('FIX_MIN'):  # v228: only models numbered >= FIX_MIN (e.g. 201 = world 2 variants)
    man = [e for e in man if int(pathlib.Path(e['folder']).name.split('_')[0]) >= int(os.environ['FIX_MIN'])]
if os.environ.get('FIX_ONLY'):  # v208: only folders containing this text (e.g. models_fix)
    man = [e for e in man if os.environ['FIX_ONLY'] in e['folder']]
for e in man:
    folder = SRC / e['folder']
    stem = pathlib.Path(e['files'][0]).stem
    out = OUT / pathlib.Path(e['folder']).name
    out.mkdir(parents=True, exist_ok=True)
    base = Image.open(folder / f'{stem}.png').convert('RGB')
    w, h = base.size
    base.resize((w * UP, h * UP), Image.NEAREST).save(out / f'{stem}.png')
    flow = Image.open(folder / f'{stem}_Flow.png').convert('L')
    lum = Image.open(folder / f'{stem}_Lum.png').convert('L')
    fp, lp = flow.load(), lum.load()
    for tier in ('Gold', 'Rainbow'):
        im = Image.new('RGB', (w, h))
        px = im.load()
        L = LUT[tier]
        for y in range(h):
            for x in range(w):
                px[x, y] = L[(2 * fp[x, y]) % 256, lp[x, y]]
        im.resize((w * UP, h * UP), Image.NEAREST).save(out / f'{stem}_{tier}.png')
    print(e['name'])
print('DONE', len(man))
