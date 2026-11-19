"""Timeline of the in-game hatch show (same numbers as Client.client.lua TIERS / runReveal), shared by
hatch_preview.py (Blender 3D layer) and hatch_overlay.py (2D layer + mp4). Pure python, no bpy."""
import math, random

FPS = 30
HV = dict(appear=0.3, swell=0.14, petGrow=0.45, leave=0.22, petSize=4.6)
EGG_H = 4.0
GAP = 0.5  # pause between the five demos
RARITY = [('Common', 2, (205, 208, 215)), ('Uncommon', 4, (96, 214, 96)), ('Rare', 20, (80, 160, 255)),
          ('Epic', 150, (180, 100, 255)), ('Legendary', 2000, (255, 204, 40))]
TIERS = [
    dict(shake=0.9, steps=5, dark=1, chips=10, hold=0.9, fov=0, float=0, beams=0, orbs=0, rings=1, scr=0, conf=0),
    dict(shake=1.2, steps=6, dark=0.8, chips=14, hold=1.1, fov=2, float=0, beams=0, orbs=0, rings=1, scr=0, conf=0, banner='UNCOMMON'),
    dict(shake=1.8, steps=9, dark=0.55, chips=20, hold=1.6, fov=5, float=0.4, beams=4, orbs=8, rings=2, scr=0.004, conf=25, banner='RARE!'),
    dict(shake=2.5, steps=12, dark=0.35, chips=28, hold=2.3, fov=8, float=1.1, beams=6, orbs=20, rings=3, scr=0.009, conf=55, banner='EPIC!', rays2=True, glow=True),
    dict(shake=3.5, steps=16, dark=0.12, chips=42, hold=3.2, fov=11, float=1.7, beams=8, orbs=40, rings=4, scr=0.016, conf=130, banner='LEGENDARY!!', rays2=True, glow=True, orbit=True),
]


def back_out(t, s=1.70158):
    t = min(max(t, 0.0), 1.0) - 1
    return t * t * ((s + 1) * t + s) + 1


def back_in(t, s=1.70158):
    t = min(max(t, 0.0), 1.0)
    return t * t * ((s + 1) * t - s)


def quad_in(t):
    t = min(max(t, 0.0), 1.0)
    return t * t


def quad_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 2


def quint_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 5


def sine_io(t):
    t = min(max(t, 0.0), 1.0)
    return -(math.cos(math.pi * t) - 1) / 2


def bounce_out(t):
    t = min(max(t, 0.0), 1.0)
    n, d = 7.5625, 2.75
    if t < 1 / d:
        return n * t * t
    if t < 2 / d:
        t -= 1.5 / d
        return n * t * t + 0.75
    if t < 2.5 / d:
        t -= 2.25 / d
        return n * t * t + 0.9375
    t -= 2.625 / d
    return n * t * t + 0.984375


class Demo:
    """one hatch of rarity index i (1..5); t = seconds since this demo started"""

    def __init__(self, i, seed=0):
        self.i = i
        self.tier = TIERS[i - 1]
        tr = self.tier
        self.T = tr['shake']
        self.S = HV['swell'] * (2.2 if i >= 4 else 1)
        self.t_shake = HV['appear']
        self.P = self.t_shake + self.T + self.S                 # pop
        self.t_leave = self.P + HV['petGrow'] + tr['hold']
        self.end = self.t_leave + HV['leave']
        self.dur = self.end + GAP
        steps = tr['steps']
        self.stepT = self.T / steps
        # climb events (time, level)
        self.climb = []
        level = 1
        for s in range(1, steps + 1):
            want = min(i, 1 + int(math.floor(s / steps * i + 0.0001)))
            if want > level:
                level = want
                self.climb.append((self.t_shake + (s - 1) * self.stepT, level))
        rng = random.Random(100 + i + seed)
        self.orbs = []
        n = tr['orbs']
        for j in range(n):
            d = [rng.random() - 0.5, rng.random() * 0.8 - 0.2, rng.random() - 0.5]
            m = math.sqrt(sum(v * v for v in d)) or 1
            r = 7 + rng.random() * 3
            self.orbs.append(dict(t0=self.t_shake + self.T * (j + 0.5) / n, dur=0.55 + rng.random() * 0.3, d=[v / m * r for v in d]))
        self.chips = []
        for j in range(tr['chips']):
            a = rng.random() * math.tau
            s = 0.3 + rng.random() * 0.4
            sp = 1 + i * 0.12
            self.chips.append(dict(a=a, s=s, v=(math.cos(a) * (6 + rng.random() * 5) * sp, (7 + rng.random() * 7) * sp, math.sin(a) * 4 - 2),
                                   r=[(rng.random() - 0.5) * 14 for _ in range(3)], kind=('star' if i >= 4 and (j + 1) % 3 == 0 else 'white' if (j + 1) % 3 == 0 else 'egg')))
        self.conf = []
        for j in range(tr['conf']):
            self.conf.append(dict(x=rng.random(), y0=-0.05 - rng.random() * 0.4, vy=0.35 + rng.random() * 0.35, sway=rng.random() * 6.28,
                                  w=0.006 + rng.random() * 0.006, rot=rng.random() * 360, vr=(rng.random() - 0.5) * 600,
                                  col=[RARITY[i - 1][2], (255, 90, 120), (90, 200, 255), (255, 230, 80), (140, 240, 120), (255, 255, 255)][j % 6]))

    def level(self, t):
        lv = 1
        for te, l in self.climb:
            if t >= te:
                lv = l
        return lv

    def u(self, t):  # shake progress 0..1
        return min(max((t - self.t_shake) / self.T, 0.0), 1.0)

    def egg(self, t):
        """scale, tilt, hop, lift, yaw, aura, crack, or None after the pop"""
        if t >= self.P:
            return None
        tr = self.tier
        if t < self.t_shake:
            return dict(scale=max(back_out(t / HV['appear']), 0.01), tilt=0, hop=0, lift=0, yaw=0, aura=0, crack=0)
        u = self.u(t)
        scale = 1.0
        for te, _ in self.climb:
            if te <= t < te + 0.16:
                scale += 0.12 * (1 - abs((t - te) - 0.08) / 0.08)
        tilt = 0.0
        hop = 0.0
        steps = tr['steps']
        if t < self.t_shake + self.T:
            s = int((t - self.t_shake) / self.stepT) + 1
            s = min(s, steps)
            v = (t - self.t_shake - (s - 1) * self.stepT) / self.stepT

            def target(k):
                return 0.0 if k == 0 else (1 if k % 2 == 0 else -1) * (0.1 + 0.25 * k / steps)
            tilt = target(s - 1) + (target(s) - target(s - 1)) * sine_io(v)
            if s % 2 == 0 and v < 0.5:
                h = 0.25 + 0.35 * s / steps
                tilt_h = math.sin(math.pi * v * 2)
                hop = h * tilt_h
        else:  # swell
            w = (t - self.t_shake - self.T) / self.S
            last = (1 if steps % 2 == 0 else -1) * 0.35
            tilt = last * (1 - quad_out(w))
            scale = 1 + ((1.3 if self.i >= 4 else 1.18) - 1) * quad_in(w)
        return dict(scale=scale, tilt=tilt, hop=hop, lift=tr['float'] * sine_io(u), yaw=3 * self.T * u ** 3 if tr['float'] > 0 else 0,
                    aura=quad_in(u), crack=u)

    def fov(self, t):
        tr = self.tier
        if t < self.P:
            return 34 - tr['fov'] * quad_in(self.u(t))
        w = (t - self.P) / 0.35
        f0 = 34 - tr['fov']
        return f0 + (34 - f0) * back_out(w)

    def scr(self, t):
        tr = self.tier
        if t < self.P:
            return tr['scr'] * quad_in(self.u(t))
        return tr['scr'] * 2.2 * (1 - quad_out((t - self.P) / 0.6))

    def pet(self, t):
        if t < self.P:
            return None
        tr = self.tier
        d = t - self.P
        k = back_out(d / HV['petGrow'])
        spin_d = HV['petGrow'] + 0.3 + (0.5 if self.i >= 4 else 0)
        spin = math.pi * 1.5 * (1 - quint_out(d / spin_d)) + math.sin(t * 2.2) * 0.35
        h0 = 2.2 + tr['float']
        hop = h0 * (1 - bounce_out(d / (HV['petGrow'] + 0.15)))
        y = hop + abs(math.sin(t * 3)) * 0.15
        return dict(k=max(k, 0.01), spin=spin, y=y)

    def ui_scale(self, t):
        if t < HV['appear']:
            return 0.6 + 0.4 * back_out(t / 0.25)
        if t >= self.t_leave:
            return max(0.0, 1 - back_in((t - self.t_leave) / HV['leave']))
        return 1.0

    def backdrop(self, t):  # opacity 0..1
        tr = self.tier
        top = 1 - tr['dark']
        if t < self.t_shake:
            return 0.0
        if t < self.t_leave:
            return top * quad_in(self.u(t))
        return top * (1 - min((t - self.t_leave) / HV['leave'], 1))
