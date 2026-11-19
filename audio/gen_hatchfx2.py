"""New hatch show sounds v2 (ElevenLabs sound generation) -> audio/hatchfx2/*.mp3, then one sheet rainingeggs_hatch2.ogg.
py gen_hatchfx2.py [names...]   (no names = all)"""
import json, os, re, subprocess, sys, urllib.request, pathlib
HERE = pathlib.Path(__file__).resolve().parent
KEY = open(r"C:\Users\onixfly\backtester\promo\elevenlabs.key", encoding="utf-8-sig").read().strip()
OUT = HERE / "hatchfx2"
OUT.mkdir(exist_ok=True)
FF = r'C:\Users\onixfly\AppData\Local\Programs\Python\Python313\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe'
N = ", high quality mobile game UI sound effect, polished, punchy, clean mix, no music, no voice"
S = [
    ("appear", 0.9, "Magical egg appearing with a soft airy whoosh and a bright twinkling sparkle pop" + N),
    ("step_1", 0.7, "Single soft glassy chime with gentle sparkle, rarity tier one reveal" + N),
    ("step_2", 0.8, "Bright two-note rising glass chime with sparkles, rarity tier two reveal" + N),
    ("step_3", 0.9, "Crisp rising crystal arpeggio with electric sparkle whoosh, rare tier reveal" + N),
    ("step_4", 1.1, "Powerful rising magical arpeggio with deep whoosh and shimmering crystal sparkles, epic tier reveal" + N),
    ("step_5", 1.4, "Huge golden rising fanfare swell with deep sub boom and heavenly glittering shimmer, legendary tier reveal" + N),
    ("zap", 0.6, "Short crackling magical electric arc, bright sizzling spark" + N),
    ("riser", 1.6, "Intense magical energy charge-up riser, swirling whoosh rising in pitch and volume, tension before explosion" + N),
    ("burst", 2.0, "Massive magical egg explosion, sharp crack and deep cinematic boom with glittering sparkle debris raining down" + N),
    ("reveal", 1.8, "Triumphant joyful reveal sting, bright bells and sparkles, a new pet appears, very satisfying reward sound" + N),
    ("legend", 3.0, "Epic heavenly choir aah with golden shimmer and soft orchestral swell, legendary reward" + N),
]


def gen(name, dur, text):
    req = urllib.request.Request("https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_128",
                                 data=json.dumps({"text": text, "duration_seconds": dur, "prompt_influence": 0.55}).encode(),
                                 headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        (OUT / f"{name}.mp3").write_bytes(r.read())
    print("ok", name)


def dur_of(p):
    out = subprocess.run([FF, '-i', str(p)], capture_output=True, text=True).stderr
    h, m, s = re.search(r'Duration: (\d+):(\d+):([\d.]+)', out).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


want = sys.argv[1:]
for name, d, text in S:
    if not want or name in want:
        gen(name, d, text)

# one sheet = one Roblox upload; prints the start/length table for the client (HFX)
GAP = 0.4
tab, t, inputs, filt = [], 0.0, [], []
for i, (n, _, _) in enumerate(S):
    p = OUT / f'{n}.mp3'
    d = dur_of(p)
    tab.append((n, round(t, 3), round(d, 3)))
    inputs += ['-i', str(p)]
    filt.append(f'[{i}:a]aresample=44100,aformat=channel_layouts=stereo,apad=pad_dur={GAP}[a{i}]')
    t += d + GAP
filt.append(''.join(f'[a{i}]' for i in range(len(S))) + f'concat=n={len(S)}:v=0:a=1[out]')
sheet = HERE / 'rainingeggs_hatch2.ogg'
subprocess.run([FF, '-loglevel', 'error', '-y'] + inputs + ['-filter_complex', ';'.join(filt), '-map', '[out]', '-c:a', 'libvorbis', '-q:a', '6', str(sheet)], check=True)
lua = 'local HFX = { -- start, length in the sheet (written by audio/gen_hatchfx2.py)\n\t' + ', '.join(f'{n} = {{ {a}, {d} }}' for n, a, d in tab) + ',\n}'
(HERE / 'hatchfx2_table.lua').write_text(lua, encoding='utf-8')
print(sheet, round(t, 2), 's')
print(lua)
