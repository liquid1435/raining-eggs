"""2D layer for hatch_ref.py frames: colour flash at each rarity step, white flash at the pop, serif pet name + odds
(like the clip), vignette -> Desktop/RAINING EGGS NOU/hatch_ca_in_clip.mp4 (+ sounds from the game's sfx file)"""
import json, math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / 'out' / 'hr3d'
DST = HERE / 'out' / 'hrfinal'
DST.mkdir(exist_ok=True)
SERIF = r'C:\Windows\Fonts\georgiab.ttf'
FF = r'C:\Users\onixfly\AppData\Local\Programs\Python\Python313\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe'
OUTV = pathlib.Path.home() / 'Desktop' / 'RAINING EGGS NOU' / 'hatch_ca_in_clip.mp4'
W, H = 1280, 720


def text_img(txt, size, top, bot, spacing=0):
    f = ImageFont.truetype(SERIF, size)
    st = max(2, size // 16)
    l, t, r, b = f.getbbox(txt, stroke_width=st)
    w, h = r - l + 8 + spacing * len(txt), b - t + 8
    im = Image.new('RGBA', (w, h))
    mask = Image.new('L', (w, h))
    d, dm = ImageDraw.Draw(im), ImageDraw.Draw(mask)
    x = 4 - l
    for ch in txt:
        d.text((x, 4 - t), ch, font=f, fill=(0, 0, 0, 255), stroke_width=st, stroke_fill=(20, 10, 0))
        dm.text((x, 4 - t), ch, font=f, fill=255)
        x += f.getlength(ch) + spacing
    gi = Image.new('RGBA', (w, h))
    gd = ImageDraw.Draw(gi)
    for y in range(h):
        u = y / h
        gd.line([(0, y), (w, y)], fill=tuple(int(top[c] + (bot[c] - top[c]) * u) for c in range(3)) + (255,))
    im.paste(gi, (0, 0), mask)
    glow = im.getchannel('A').filter(ImageFilter.GaussianBlur(size // 6))
    gl = Image.new('RGBA', (w, h), top + (0,))
    gl.putalpha(glow.point(lambda v: int(v * 0.6)))
    out = Image.new('RGBA', (w, h))
    out.alpha_composite(gl)
    out.alpha_composite(im)
    return out


def put(cv, im, cx, cy, scale=1.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    im2 = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if alpha < 1:
        im2.putalpha(im2.getchannel('A').point(lambda v: int(v * alpha)))
    cv.alpha_composite(im2, (int(cx - im2.width / 2), int(cy - im2.height / 2)))


def eo(u):
    u = max(0.0, min(1.0, u))
    return 1 - (1 - u) ** 3


metas = json.loads((SRC / 'meta.json').read_text(encoding='utf-8'))
name = metas[0]['name'].upper()
NAME = text_img(name, 70, (255, 248, 210), (235, 165, 40), spacing=4)
ODDS = text_img('1 / 600,000,000', 38, (255, 255, 255), (255, 214, 120), spacing=3)
_cnt_cache = {}


def nice(n):  # 2 significant digits while it climbs: 200, 3,000, 45,000 ... 600,000,000
    if n < 100:
        return int(n)
    k = 10 ** (len(str(int(n))) - 2)
    return int(round(n / k) * k)


def counter_img(v, colr):
    key = (v, colr)
    if key not in _cnt_cache:
        if len(_cnt_cache) > 60:
            _cnt_cache.clear()
        _cnt_cache[key] = text_img(f'1 / {v:,}', 64, (255, 255, 255), colr, spacing=3)
    return _cnt_cache[key]


ticks = []  # (time, digits) every time the counter gains a digit
last_digits = 0
pulse_t = 0.0
vig = Image.new('L', (W, H), 0)
d = ImageDraw.Draw(vig)
for k in range(40):
    e = k * 9
    d.rectangle([e, e * 0.56, W - e, H - e * 0.56], outline=int(170 * (1 - k / 40)), width=10)
vig = vig.filter(ImageFilter.GaussianBlur(40))
sounds = []  # (time, name, volume)
lastL = 0
for m in metas:
    im = Image.open(SRC / f"f{m['f']:04d}.png").convert('RGBA')
    col = tuple(int(c) for c in m['col'])
    dark = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    dark.putalpha(vig)
    im.alpha_composite(dark)
    fa = 0.0
    if m['L'] and not m['popped']:
        fa = 0.5 * math.exp(-m['age'] * 8)
        if m['L'] != lastL:
            lastL = m['L']
    if m['popped']:
        pa_ = m['pa']
        fa = min(1.0, pa_ / 0.06) if pa_ < 0.32 else max(0.0, 1 - (pa_ - 0.32) / 0.6)
        col = (255, 255, 255)
    if fa > 0.01:
        im.alpha_composite(Image.new('RGBA', (W, H), col + (int(255 * min(fa, 1)),)))
    # ??? step: the odds counter climbs 1/200 -> 1/3,000 -> ... -> 1/600,000,000 at the top of the screen
    if m['L'] == 6 and not m['popped']:
        u = max(0.0, min(1.0, m['age'] / (m['sd'] * 0.9)))
        lo, hi = math.log10(200), math.log10(600000000)
        v = 600000000 if u >= 1 else nice(10 ** (lo + (hi - lo) * u ** 1.25))
        dg = len(str(v))
        if dg != last_digits:
            ticks.append((m['t'], dg))
            last_digits = dg
            pulse_t = m['t']
        k = 1 + 0.35 * math.exp(-(m['t'] - pulse_t) * 10)
        jit = (math.sin(m['t'] * 90) * 3 * u, math.cos(m['t'] * 77) * 2 * u)
        put(im, counter_img(v, col), W / 2 + jit[0], 78 + jit[1], k * (1 if m['age'] > 0.15 else eo(m['age'] / 0.15)))
    if m['popped'] and m['pa'] > 1.3:
        u = (m['pa'] - 1.3) / 0.7
        put(im, NAME, W / 2, H - 120, 0.85 + 0.15 * eo(u), eo(u))
        put(im, ODDS, W / 2, H - 62, 1, eo((m['pa'] - 1.6) / 0.5))
    left = m['end'] - m['t']
    if left < 0.4:
        im.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * (1 - left / 0.4)))))
    im.convert('RGB').save(DST / f"f{m['f']:04d}.png")
pop_t = next(m['t'] for m in metas if m['popped'])
# sounds: cracks = the game's own egg_crack (user likes it), effects = new ElevenLabs set in audio/hatchfx
import re, random as _r
table = dict((k, (float(a), float(b))) for k, a, b in re.findall(r'(\w+) = \{ ([\d.]+), ([\d.]+) \}', (HERE.parent / 'game' / 'Sfx.lua').read_text()))
sfx_file = HERE.parent / 'audio' / 'rainingeggs_sfx.ogg'
FX = HERE.parent / 'audio' / 'hatchfx'
ev = json.loads((SRC / 'crack_events.json').read_text(encoding='utf-8'))
rr = _r.Random(4)
ca, cl = table['egg_crack']
clips = []  # (time, file, trim start, trim end, volume, pitch)
for te, sz in ev:
    if te < pop_t:
        clips.append((te, sfx_file, ca, ca + cl, 0.5 + 0.12 * sz, 1.18 - 0.08 * sz + rr.uniform(-0.04, 0.04)))
clips.append((pop_t - 0.02, sfx_file, ca, ca + cl, 1.0, 0.75))
step_t, lastL = {}, 0
for m in metas:
    if m['L'] and m['L'] != lastL and not m['popped']:
        step_t[m['L']] = m['t']
        lastL = m['L']
for L, tt in step_t.items():
    clips.append((tt, FX / f'step_{min(L, 5)}.mp3', 0, None, 0.75 if L < 6 else 0.9, 1 if L < 6 else 0.78))
if 6 in step_t:
    clips.append((step_t[6] + 0.05, FX / 'shing.mp3', 0, None, 0.7, 0.75))
ua, ul = table['ui_click']
for tt, dg in ticks:  # a tick for every new digit of the counter, pitch climbing
    clips.append((tt, sfx_file, ua, ua + ul, 0.7, 0.9 + 0.08 * (dg - 3)))
for L in (4, 5):
    if L in step_t:
        clips.append((step_t[L] + 0.05, FX / 'shing.mp3', 0, None, 0.6, 1 if L == 4 else 0.9))
clips.append((max(0, pop_t - 1.4), FX / 'riser.mp3', 0, None, 0.7, 1))
clips.append((pop_t, FX / 'burst.mp3', 0, None, 1.0, 1))
clips.append((pop_t + 0.4, FX / 'reveal.mp3', 0, None, 0.8, 1))
cmd = [FF, '-loglevel', 'error', '-y', '-framerate', '30', '-start_number', '0', '-i', str(DST / 'f%04d.png')]
filt = []
for n, (tt, path, a0, a1, vol, pitch) in enumerate(clips, 1):
    cmd += ['-i', str(path)]
    trim = f'atrim={a0}:{a1},' if a1 else ''
    pt = f'asetrate={int(44100 * pitch)},aresample=44100,' if abs(pitch - 1) > 0.001 else ''
    filt.append(f'[{n}:a]{trim}asetpts=PTS-STARTPTS,aresample=44100,{pt}aformat=channel_layouts=stereo,volume={vol:.2f},adelay={int(tt * 1000)}|{int(tt * 1000)}[s{n}]')
n = len(clips)
filt.append(''.join(f'[s{k}]' for k in range(1, n + 1)) + f'amix=inputs={n}:normalize=0,alimiter=limit=0.85,apad,asetpts=N/SR/TB[aout]')
cmd += ['-filter_complex', ';'.join(filt), '-map', '0:v', '-map', '[aout]', '-c:a', 'aac', '-b:a', '160k', '-t', f'{len(metas) / 30:.2f}']
cmd += ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', str(OUTV)]
subprocess.run(cmd, check=True)
print('video', OUTV)
