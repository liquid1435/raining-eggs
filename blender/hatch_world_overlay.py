"""2D screen layer for the in-world hatch preview (hatch_world.py frames + meta.json):
flashes, vignette, '1 in N' counter, pet name, final odds, NEW! -> Desktop/RAINING EGGS NOU/hatch_nou_in_lume.mp4
  py hatch_world_overlay.py"""
import json, math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / 'out' / 'hw3d'
DST = HERE / 'out' / 'hwfinal'
DST.mkdir(exist_ok=True)
LG = str(HERE / 'fonts' / 'LuckiestGuy.ttf')
FF = r'C:\Users\onixfly\AppData\Local\Programs\Python\Python313\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe'
OUTV = pathlib.Path.home() / 'Desktop' / 'RAINING EGGS NOU' / 'hatch_nou_in_lume.mp4'
ODDS = [2, 4, 20, 150, 2000]
_cache = {}


def text_img(txt, size, fill=(255, 255, 255), grad=None):
    key = (txt, size, fill, grad)
    if key in _cache:
        return _cache[key]
    f = ImageFont.truetype(LG, size)
    st = max(3, int(size * 0.09))
    l, t, r, b = f.getbbox(txt, stroke_width=st)
    w, h = r - l + 6, b - t + 6
    im = Image.new('RGBA', (w, h))
    ImageDraw.Draw(im).text((3 - l, 3 - t), txt, font=f, fill=fill, stroke_width=st, stroke_fill=(0, 0, 0))
    if grad:
        mask = Image.new('L', (w, h))
        ImageDraw.Draw(mask).text((3 - l, 3 - t), txt, font=f, fill=255)
        gi = Image.new('RGBA', (w, h))
        gd = ImageDraw.Draw(gi)
        for y in range(h):
            u = y / h
            gd.line([(0, y), (w, y)], fill=tuple(int(grad[0][c] + (grad[1][c] - grad[0][c]) * u) for c in range(3)) + (255,))
        im.paste(gi, (0, 0), mask)
    _cache[key] = im
    return im


def put(cv, im, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    im2 = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if rot:
        im2 = im2.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1:
        a = im2.getchannel('A').point(lambda v: int(v * alpha))
        im2.putalpha(a)
    cv.alpha_composite(im2, (int(cx - im2.width / 2), int(cy - im2.height / 2)))


def back_out(u, s=1.7):
    u = max(0.0, min(1.0, u)) - 1
    return u * u * ((s + 1) * u + s) + 1


def comma(n):
    return f'{n:,}'


metas = json.loads((SRC / 'meta.json').read_text(encoding='utf-8'))
W, H = 1280, 720
vig = Image.new('L', (W, H), 0)
d = ImageDraw.Draw(vig)
for k in range(40):
    e = k * 9
    d.rectangle([e, e * 0.56, W - e, H - e * 0.56], outline=int(150 * (1 - k / 40)), width=10)
vig = vig.filter(ImageFilter.GaussianBlur(40))
for m in metas:
    im = Image.open(SRC / f"f{m['f']:04d}.png").convert('RGBA')
    col = tuple(int(c) for c in m['col'])
    r = m['r']
    # vignette darkens as the tension grows
    dark = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    dark.putalpha(vig.point(lambda v, k=(0.4 + 0.6 * m['cu']): int(v * k)))
    im.alpha_composite(dark)
    # colour flash at every new rarity step, big white flash at the pop
    fa = 0.0
    fc = col
    if m['level'] and not m['popped']:
        fa = 0.45 * math.exp(-m['age'] * 9) * (1.4 if m['level'] >= 4 else 1)
    if m['popped']:
        fa = max(0.0, 1 - m['pa'] / (0.55 if r >= 4 else 0.35)) * (1.0 if r >= 3 else 0.7)
        fc = (255, 255, 255)
    if fa > 0.01:
        fl = Image.new('RGBA', (W, H), fc + (int(255 * min(fa, 1)),))
        im.alpha_composite(fl)
    if not m['popped']:
        # odds counter climbs while the egg charges
        u = m['cu']
        v = max(1, int(round(ODDS[r - 1] ** (u ** 1.6))))
        if m['level']:
            put(im, text_img('1 in ' + comma(v), 54, (255, 255, 255)), W / 2, H - 52, 1 + 0.25 * math.exp(-m['age'] * 10))
    else:
        pa = m['pa']
        name = m['name'].upper()
        put(im, text_img(name, 76, grad=((255, 255, 255), col)), W / 2, 70, back_out((pa - 0.25) / 0.35) if pa > 0.25 else 0)
        put(im, text_img('1 in ' + comma(ODDS[r - 1]), 64, grad=((255, 246, 170), (255, 165, 25))), W / 2, H - 56, 1.6 - 0.6 * back_out(pa / 0.35))
        if r >= 4 and pa > 0.5:
            put(im, text_img('NEW!', 40, (120, 255, 120)), W / 2 + 300, 120, back_out((pa - 0.5) / 0.3), rot=-12)
    # fade out at the end of each demo
    left = m['end'] - m['t']
    if left < 0.3:
        im.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * (1 - left / 0.3)))))
    im.convert('RGB').save(DST / f"f{m['f']:04d}.png")
subprocess.run([FF, '-loglevel', 'error', '-y', '-framerate', '30', '-start_number', '0', '-i', str(DST / 'f%04d.png'),
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', str(OUTV)], check=True)
print('video', OUTV)
