"""Joins audio/hatchfx/*.mp3 into ONE sound file (rainingeggs_hatch.ogg) with gaps, so Roblox needs a single upload;
writes the start/length table into game/Client.client.lua (HFX = {...})."""
import subprocess, re, pathlib
FF = r'C:\Users\onixfly\AppData\Local\Programs\Python\Python313\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe'
HERE = pathlib.Path(__file__).resolve().parent
names = ['step_1', 'step_2', 'step_3', 'step_4', 'step_5', 'shing', 'riser', 'burst', 'reveal']
GAP = 0.4
def dur(p):
    out = subprocess.run([FF, '-i', str(p)], capture_output=True, text=True).stderr
    h, m, s = re.search(r'Duration: (\d+):(\d+):([\d.]+)', out).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)
tab, t, inputs, filt = [], 0.0, [], []
for i, n in enumerate(names):
    p = HERE / 'hatchfx' / f'{n}.mp3'
    d = dur(p)
    tab.append((n, round(t, 3), round(d, 3)))
    inputs += ['-i', str(p)]
    filt.append(f'[{i}:a]aresample=44100,aformat=channel_layouts=stereo,apad=pad_dur={GAP}[a{i}]')
    t += d + GAP
filt.append(''.join(f'[a{i}]' for i in range(len(names))) + f'concat=n={len(names)}:v=0:a=1[out]')
out = HERE / 'rainingeggs_hatch.ogg'
subprocess.run([FF, '-loglevel', 'error', '-y'] + inputs + ['-filter_complex', ';'.join(filt), '-map', '[out]', '-c:a', 'libvorbis', '-q:a', '6', str(out)], check=True)
lua = 'local HFX = { -- start, length in the sheet (written by audio/make_hatch_sheet.py)\n\t' + ', '.join(f'{n} = {{ {a}, {d} }}' for n, a, d in tab) + ',\n}'
c = HERE.parent / 'game' / 'Client.client.lua'
s = c.read_text(encoding='utf-8')
s2 = re.sub(r'local HFX = \{ -- start, length in the sheet.*?\n\}', lambda m: lua, s, count=1, flags=re.S)
assert s2 != s or lua in s
c.write_bytes(s2.encode('utf-8'))
print(out, round(t, 2), 's')
for r in tab:
    print(r)
