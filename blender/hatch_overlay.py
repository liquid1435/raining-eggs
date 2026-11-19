"""2D layer of the hatch-show preview: game background, dark backdrop, rays, burst, texts, flashes, confetti
on top of the Blender frames (out/hp3d) -> mp4 on the Desktop + a contact sheet.
  py hatch_overlay.py"""
import math, random, pathlib, subprocess, shutil, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hatch_tl as TL

SRC = HERE / 'out' / 'hp3d'
DST = HERE / 'out' / 'hpfinal'
DST.mkdir(exist_ok=True)
LG = str(HERE / 'fonts' / 'LuckiestGuy.ttf')
FR = str(HERE / 'fonts' / 'Fredoka.ttf')
FF = r'C:\Users\onixfly\AppData\Local\Programs\Python\Python313\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe'
SW, SH = 1280, 720
RW, RH = 0.6 * SW, 0.64 * SH                      # reveal frame (aspect 0.95 -> limited by height)
RW = min(RW, RH * 0.95)
RCX, RCY = SW * 0.5, SH * 0.45
G = 1200                                           # group canvas (rays reach out of the frame)
NAMES = (SRC / 'names.txt').read_text(encoding='utf-8').split('\n')
WHITE = (255, 255, 255)

# background: the player's game screenshot, blurred
shots = sorted((pathlib.Path(os.environ['USERPROFILE']) / 'Pictures' / 'Screenshots').glob('*.png'), key=lambda p: p.stat().st_mtime)
bg = max((Image.open(p) for p in shots[-12:]), key=lambda im: im.width * im.height).convert('RGB')
k = max(SW / bg.width, SH / bg.height)
bg = bg.resize((int(bg.width * k) + 1, int(bg.height * k) + 1))
bg = bg.crop((0, 0, SW, SH)).filter(ImageFilter.GaussianBlur(5)).convert('RGBA')

_cache = {}


def text_img(txt, h, fill=WHITE, grad=None, font=LG, stroke=None):
    key = (txt, h, fill, grad, font)
    if key in _cache:
        return _cache[key]
    size = int(h * 0.92)
    f = ImageFont.truetype(font, size)
    st = stroke if stroke is not None else max(3, int(size * 0.09))
    l, t, r, b = f.getbbox(txt, stroke_width=st)
    w, hh = r - l + 6, b - t + 6
    im = Image.new('RGBA', (w, hh))
    d = ImageDraw.Draw(im)
    d.text((3 - l, 3 - t), txt, font=f, fill=fill, stroke_width=st, stroke_fill=(0, 0, 0))
    if grad:
        mask = Image.new('L', (w, hh))
        ImageDraw.Draw(mask).text((3 - l, 3 - t), txt, font=f, fill=255)
        gi = Image.new('RGBA', (w, hh))
        gd = ImageDraw.Draw(gi)
        for y in range(hh):
            u = y / hh
            gd.line([(0, y), (w, y)], fill=tuple(int(grad[0][c] + (grad[1][c] - grad[0][c]) * u) for c in range(3)) + (255,))
        im.paste(gi, (0, 0), mask)
    _cache[key] = im
    return im


def put(canvas, im, cx, cy, scale=1.0, rot=0.0, maxw=None):
    if scale <= 0.01:
        return
    s = scale
    if maxw and im.width * s > maxw:
        s = maxw / im.width
    w, h = max(1, int(im.width * s)), max(1, int(im.height * s))
    x = im.resize((w, h), Image.LANCZOS)
    if rot:
        x = x.rotate(-rot, expand=True, resample=Image.BICUBIC)
    canvas.alpha_composite(x, (int(cx - x.width / 2), int(cy - x.height / 2)))


def rays(canvas, n, col, base_tr, size, angle):
    lay = Image.new('RGBA', canvas.size)
    d = ImageDraw.Draw(lay)
    cx, cy = canvas.width / 2, canvas.height / 2
    L = size * 0.5
    wdt = size * 0.07
    segs = 30
    for i in range(n):
        a = math.radians(angle + i * 360 / n)
        ux, uy = math.sin(a), -math.cos(a)
        px, py = -uy, ux
        for s in range(segs):
            r0, r1 = L * s / segs, L * (s + 1) / segs
            v = (s + 0.5) / segs
            tr = 1 - v / 0.75 * 0.9 if v < 0.75 else 0.1 + (v - 0.75) / 0.25 * 0.3
            al = int(255 * (1 - base_tr) * (1 - tr))
            if al <= 0:
                continue
            hw0, hw1 = wdt / 2 * (s / segs), wdt / 2 * ((s + 1) / segs)   # thin at the centre like the rotated frames
            hw0, hw1 = max(hw0, wdt * 0.15), max(hw1, wdt * 0.15)
            pts = [(cx + ux * r0 - px * hw0, cy + uy * r0 - py * hw0), (cx + ux * r1 - px * hw1, cy + uy * r1 - py * hw1),
                   (cx + ux * r1 + px * hw1, cy + uy * r1 + py * hw1), (cx + ux * r0 + px * hw0, cy + uy * r0 + py * hw0)]
            d.polygon(pts, fill=tuple(col) + (al,))
    canvas.alpha_composite(lay)


def frame(demo, t, f):
    i = demo.i
    tr = demo.tier
    name, odds, rcol = TL.RARITY[i - 1]
    out = bg.copy()
    # dark backdrop
    op = demo.backdrop(t)
    if op > 0:
        out.alpha_composite(Image.new('RGBA', (SW, SH), (8, 4, 20, int(255 * op))))
    us = demo.ui_scale(t)
    if t < demo.end and us > 0.01:
        grp = Image.new('RGBA', (G, G))
        gc = G / 2
        P = demo.P
        if t >= P:
            dt = t - P
            # rays (behind everything in the reveal)
            rs = TL.back_out(dt / 0.4)
            rays(grp, 16, rcol if i >= 2 else WHITE, 0.45, 1.7 * RW * rs, dt * 25)
            if tr.get('rays2'):
                rays(grp, 10, (255, 250, 220) if i >= 5 else WHITE, 0.55, 1.7 * RW * 1.35 * TL.back_out(dt / 0.6), dt * 25 + 18)
            # burst
            if dt < 0.4:
                u = TL.quad_out(dt / 0.4)
                r = RW * (0.3 + 1.2 * u) / 2
                c = rcol if i >= 2 else WHITE
                lay = Image.new('RGBA', (G, G))
                ImageDraw.Draw(lay).ellipse((gc - r, gc - r + RH * 0.05, gc + r, gc + r + RH * 0.05), fill=tuple(c) + (int(255 * (1 - u)),))
                grp.alpha_composite(lay)
        # the 3D viewport
        p = SRC / f'f{f:04d}.png'
        if p.exists():
            v = Image.open(p).convert('RGBA').resize((int(RW), int(RH * 0.8)), Image.LANCZOS)
            grp.alpha_composite(v, (int(gc - RW / 2), int(gc - RH / 2 + RH * 0.1)))

        def ry(y):
            return gc - RH / 2 + RH * y
        # odds
        if demo.t_shake <= t < P:
            u = min(max((t - demo.t_shake) / (demo.T + demo.S), 0), 1)
            val = max(1, int(math.floor(odds ** (u ** 1.6) + 0.5)))
            rng = random.Random(f)
            im = text_img(f'1 in {val:,}', int(RH * 0.095 * 0.95))
            put(grp, im, gc + (rng.random() - 0.5) * 0.014 * u * RW, ry(0.93) + (rng.random() - 0.5) * 0.01 * u * RH, 1, (rng.random() - 0.5) * 6 * u, maxw=RW * 1.3)
        elif t >= P:
            dt = t - P
            sc_ = 1.5 + (1 - 1.5) * TL.back_out(dt / 0.35)
            im = text_img(f'1 in {odds:,}', int(RH * 0.095 * 0.95), grad=((255, 246, 170), (255, 165, 25)))
            put(grp, im, gc, ry(0.93), sc_, maxw=RW * 1.3 * sc_)
            # banner
            if tr.get('banner'):
                bs = 3 + (1 - 3) * TL.back_out(dt / 0.35)
                rot = -6 + (math.sin(t * 6) * 5 if i >= 5 else 0)
                im = text_img(tr['banner'], int(RH * 0.15 * 0.95), fill=WHITE if i >= 5 else rcol,
                              grad=((255, 246, 170), (255, 165, 25)) if i >= 5 else None)
                put(grp, im, gc, ry(0.8), bs, rot, maxw=RW * 1.3 * bs)
            # name + NEW
            if dt >= 0.22:
                ns = 0.2 + 0.8 * TL.back_out((dt - 0.22) / 0.35)
                im = text_img(NAMES[i - 1], int(RH * 0.12 * 0.95), grad=((255, 246, 170), (255, 165, 25)))
                put(grp, im, gc, ry(0.07), ns, maxw=RW * 1.3 * ns)
                if i >= 4:
                    im = text_img('NEW!', int(RH * 0.07 * 0.95), fill=(120, 255, 120))
                    put(grp, im, gc, ry(0.165), 0.2 + 0.8 * TL.back_out((dt - 0.22) / 0.3))
        # screen shake + ui scale, then onto the screen
        amp = demo.scr(t)
        rng = random.Random(f * 7 + 1)
        ox = (rng.random() - 0.5) * 2 * amp * SW
        oy = (rng.random() - 0.5) * 2 * amp * SH
        if us != 1:
            gs = max(1, int(G * us))
            grp = grp.resize((gs, gs), Image.LANCZOS)
        out.alpha_composite(grp, (int(RCX + ox - grp.width / 2), int(RCY + oy - grp.height / 2)))
    # flashes
    fl = [(te, TL.RARITY[lv - 1][2], 0.15 if lv >= 5 else 0.55, 0.35) for te, lv in demo.climb]
    fl.append((demo.P, WHITE if i >= 4 else rcol, 0 if i >= 3 else 0.5, 0.9 if i >= 4 else 0.45))
    for te, c, frm, dur in fl:
        if te <= t < te + dur:
            a = (1 - frm) * (1 - TL.quad_out((t - te) / dur))
            out.alpha_composite(Image.new('RGBA', (SW, SH), tuple(c) + (int(255 * a),)))
    # confetti
    if t >= demo.P and demo.conf:
        dt = t - demo.P
        lay = Image.new('RGBA', (SW, SH))
        d = ImageDraw.Draw(lay)
        for c in demo.conf:
            y = (c['y0'] + c['vy'] * dt + 0.15 * dt * dt) * SH
            if y > SH + 20:
                continue
            x = (c['x'] + 0.02 * math.sin(c['sway'] + dt * 4)) * SW
            w = c['w'] * SW
            h = w * 0.55 * abs(math.cos(math.radians(c['rot'] + c['vr'] * dt)))
            d.rectangle((x - w / 2, y - h / 2 - 1, x + w / 2, y + h / 2 + 1), fill=tuple(c['col']) + (255,))
        out.alpha_composite(lay)
    # caption
    cap = text_img(f'{i}/5  {name.upper()}  (1 in {odds:,})', 34, font=FR, stroke=4)
    out.alpha_composite(cap, (24, 18))
    return out.convert('RGB')


f = 0
keys = []
for i in range(1, 6):
    demo = TL.Demo(i)
    nf = int(round(demo.dur * TL.FPS))
    for j in range(nf):
        t = j / TL.FPS
        im = frame(demo, t, f)
        im.save(DST / f'o{f:04d}.png')
        if abs(t - (demo.t_shake + demo.T * 0.8)) < 0.5 / TL.FPS or abs(t - (demo.P + 0.05)) < 0.5 / TL.FPS or abs(t - (demo.P + 0.9)) < 0.5 / TL.FPS:
            keys.append(im)
        f += 1
print('frames', f)
mp4 = HERE / 'out' / 'hatch_tiers_preview.mp4'
subprocess.run([FF, '-y', '-loglevel', 'error', '-framerate', str(TL.FPS), '-i', str(DST / 'o%04d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                '-crf', '18', str(mp4)], check=True)
desk = pathlib.Path(os.environ['USERPROFILE']) / 'Desktop' / 'RAINING EGGS NOU' / 'hatch_animatii_raritate.mp4'
shutil.copyfile(mp4, desk)
# contact sheet: 3 key moments per rarity
W, H = 427, 240
sheet = Image.new('RGB', (W * 3, H * 5))
for k, im in enumerate(keys[:15]):
    sheet.paste(im.resize((W, H)), ((k % 3) * W, (k // 3) * H))
sheet.save(HERE / 'out' / 'hatch_tiers_sheet.png')
print('ok', desk)
