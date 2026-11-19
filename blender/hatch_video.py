"""Text overlay (rarity banner, pet name, odds) on the Blender hatch frames -> mp4 + preview sheet.
  py hatch_video.py   (needs out\\hatch0001.png ... from hatch_anim.py)"""
import pathlib, subprocess, math, os, shutil
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / 'out'
DST = HERE / 'out' / 'hatch_final'
DST.mkdir(exist_ok=True)
LG = str(HERE / 'fonts' / 'LuckiestGuy.ttf')
FR = str(HERE / 'fonts' / 'Fredoka.ttf')
POP = 96
ODDS = 2000
INK = (26, 20, 48)
GOLD_T, GOLD_B, GOLD_LIP = (255, 243, 168), (240, 164, 12), (168, 106, 8)
FF = r'C:\Users\onixfly\AppData\Local\Programs\Python\Python313\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe'


def back_out(t, s=2.4):
    t = min(max(t, 0), 1) - 1
    return t * t * ((s + 1) * t + s) + 1


def text_img(txt, font, size, fill, stroke=8, shadow=6, grad=None):
    f = ImageFont.truetype(font, size)
    l, t, r, b = f.getbbox(txt, stroke_width=stroke)
    w, h = r - l + 4, b - t + shadow + 4
    im = Image.new('RGBA', (w, h))
    d = ImageDraw.Draw(im)
    d.text((2 - l, 2 - t + shadow), txt, font=f, fill=(0, 0, 0, 90), stroke_width=stroke, stroke_fill=(0, 0, 0, 90))
    d.text((2 - l, 2 - t), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=INK)
    if grad:
        mask = Image.new('L', (w, h))
        ImageDraw.Draw(mask).text((2 - l, 2 - t), txt, font=f, fill=255)
        g = Image.new('RGBA', (w, h))
        gd = ImageDraw.Draw(g)
        for y in range(h):
            u = y / h
            gd.line([(0, y), (w, y)], fill=tuple(int(grad[0][k] + (grad[1][k] - grad[0][k]) * u) for k in range(3)) + (255,))
        im.paste(g, (0, 0), mask)
    return im


def pill(w, h, top, bot, lip, r=None):
    r = r or h // 2
    im = Image.new('RGBA', (w + 12, h + 22))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 14, w + 6, h + 14), r, fill=lip, outline=INK, width=6)
    face = Image.new('RGBA', (w, h))
    fd = ImageDraw.Draw(face)
    for y in range(h):
        u = y / h
        fd.line([(0, y), (w, y)], fill=tuple(int(top[k] + (bot[k] - top[k]) * u) for k in range(3)) + (255,))
    m = Image.new('L', (w, h))
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    im.paste(face, (6, 4), m)
    d.rounded_rectangle((6, 4, w + 6, h + 4), r, outline=INK, width=6)
    shine = Image.new('RGBA', (w - 40, int(h * 0.36)))
    ImageDraw.Draw(shine).rounded_rectangle((0, 0, w - 41, int(h * 0.36) - 1), int(h * 0.18), fill=(255, 255, 255, 95))
    im.alpha_composite(shine, (26, 12))
    return im


# pieces made once
title = text_img('LEGENDARY!', LG, 74, (255, 255, 255))
banner = pill(title.width + 120, 112, GOLD_T, GOLD_B, GOLD_LIP)
banner.alpha_composite(title, ((banner.width - title.width) // 2, 20))
name = text_img('Sun Lion', LG, 96, (255, 255, 255), stroke=10, grad=((255, 246, 170), (255, 176, 30)))
odds_t = text_img('1 in 2,000', LG, 44, (255, 255, 255), stroke=6, shadow=3)
odds = pill(odds_t.width + 60, 66, (70, 60, 120), (40, 32, 80), (20, 16, 44))
odds.alpha_composite(odds_t, ((odds.width - odds_t.width) // 2, 13))
inc_t = text_img('$1.2K/s', FR, 40, (255, 255, 255), stroke=6, shadow=3)
inc = pill(inc_t.width + 60, 66, (200, 255, 158), (40, 168, 60), (18, 110, 40))
inc.alpha_composite(inc_t, ((inc.width - inc_t.width) // 2, 13))
new_t = text_img('NEW!', FR, 40, (255, 255, 255), stroke=6, shadow=3)
new = pill(new_t.width + 60, 66, (255, 179, 220), (224, 47, 134), (156, 26, 92))
new.alpha_composite(new_t, ((new.width - new_t.width) // 2, 13))


def put(frame, im, cx, cy, s, rot=0, alpha=1.0):
    if s <= 0.01 or alpha <= 0:
        return
    w, h = max(1, int(im.width * s)), max(1, int(im.height * s))
    x = im.resize((w, h), Image.LANCZOS)
    if rot:
        x = x.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        a = x.getchannel('A').point(lambda v: int(v * alpha))
        x.putalpha(a)
    frame.alpha_composite(x, (int(cx - x.width / 2), int(cy - x.height / 2)))


frames = sorted(p for p in SRC.glob('hatch[0-9]*.png'))
for p in frames:
    f = int(p.stem[5:])
    im = Image.open(p).convert('RGBA')
    W, H = im.size
    k = f - (POP + 6)
    # no rarity banner (user: show only the odds)
    k = f - (POP + 20)
    if k >= 0:
        put(im, name, W / 2, 62, back_out(k / 9) * 0.85)
    # the odds count up while the egg shakes and cracks, and land on the real number when it pops
    C0, C1 = 28, POP + 2
    if f >= C0:
        u = min(1, (f - C0) / (C1 - C0))
        val = ODDS if u >= 1 else max(1, int(round(ODDS ** (u ** 1.6))))
        done = f >= C1
        txt = '1 in ' + format(val, ',')
        col_grad = ((255, 246, 170), (255, 176, 30)) if done else None
        t_im = text_img(txt, LG, 44, (255, 255, 255), stroke=6, shadow=3, grad=col_grad)
        if done:
            sc_ = 1.3 + 0.35 * max(0, 1 - (f - C1) / 8) * math.sin(min(1, (f - C1) / 8) * math.pi)
        else:
            sc_ = 1.0 + 0.25 * u + 0.05 * math.sin(f * 1.3)      # grows and buzzes while counting
        put(im, t_im, W / 2, H - 70, sc_ * min(1, (f - C0) / 5))
    im.convert('RGB').save(DST / f'{f:04d}.png')

mp4 = HERE / 'out' / 'hatch_preview.mp4'
subprocess.run([FF, '-y', '-loglevel', 'error', '-framerate', '30', '-i', str(DST / '%04d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                '-crf', '17', '-vf', 'tpad=stop_mode=clone:stop_duration=1', str(mp4)], check=True)
desk = pathlib.Path(os.environ['USERPROFILE']) / 'Desktop' / 'RAINING EGGS NOU' / 'UI v3'
shutil.copyfile(mp4, desk / 'hatch_animation.mp4')
# contact sheet of key moments
picks = [10, 18, 50, 70, 88, 98, 104, 116, 135, 160]
ims = [Image.open(DST / f'{f:04d}.png').resize((640, 360)) for f in picks]
sheet = Image.new('RGB', (640 * 2, 360 * 5))
for i, x in enumerate(ims):
    sheet.paste(x, ((i % 2) * 640, (i // 2) * 360))
sheet.save(desk / 'hatch_frames.png')
print('ok', mp4)
