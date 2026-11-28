"""Sound options for the GOLDEN EGG sinking into the ground and the GOLDEN PORTAL appearing (user, 28 Nov).
py gen_golden_sfx.py -> E:/rainingeggs/audio/golden_sfx/*.mp3"""
import numpy as np, subprocess, pathlib, wave
import imageio_ffmpeg
SR = 44100
OUT = pathlib.Path(__file__).parent / 'golden_sfx'
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(7)
FF = imageio_ffmpeg.get_ffmpeg_exe()


def t_(d):
    return np.arange(int(SR * d)) / SR


def env(n, a, r):
    e = np.ones(n)
    na, nr = int(SR * a), int(SR * r)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, 'same')


def noise(n):
    return rng.uniform(-1, 1, n)


def save(name, x):
    x = x / (np.abs(x).max() + 1e-9) * 0.9
    w = OUT / (name + '.wav')
    with wave.open(str(w), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((x * 32767).astype(np.int16).tobytes())
    subprocess.run([FF, '-v', 'error', '-y', '-i', str(w), '-b:a', '192k', str(OUT / (name + '.mp3'))], check=True)
    w.unlink()


# ---------------- SINK (egg goes into the ground), ~3 s
d = 3.0; t = t_(d); n = len(t)
# A: deep earth rumble + gravel crunches, slowing down
rum = lowpass(noise(n), 400) * 6 * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t))
grav = np.zeros(n)
for k in range(38):
    p = int(rng.uniform(0, d * 0.85) * SR); m = int(0.03 * SR)
    if p + m < n: grav[p:p + m] += lowpass(noise(m), 3) * np.exp(-np.linspace(0, 6, m)) * rng.uniform(0.2, 0.6)
save('sink_A_rumble', (rum + grav * 1.2 + 0.5 * np.sin(2 * np.pi * (45 - 12 * t / d) * t)) * env(n, 0.15, 0.9))
# B: magic sink: falling golden chime + soft rumble
f = 880 * 2 ** (-2 * t / d)
chime = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
save('sink_B_magic', (chime * 0.5 * np.exp(-t * 0.6) + lowpass(noise(n), 300) * 3) * env(n, 0.05, 0.8))
# C: heavy thud at the start + grinding stone that fades
thud = np.sin(2 * np.pi * 55 * t) * np.exp(-t * 7) * 2
grind = lowpass(noise(n), 25) * (0.5 + 0.5 * np.sin(2 * np.pi * 13 * t)) * np.exp(-t * 0.7)
save('sink_C_heavy', (thud + grind * 1.5 + lowpass(noise(n), 500) * 4 * np.exp(-t * 1.2)) * env(n, 0.005, 0.7))

# ---------------- PORTAL appears, ~3.5 s
d = 3.5; t = t_(d); n = len(t)
# A: big whoosh + rising shimmering chord
sweep = lowpass(noise(n), 6) * np.exp(-((t - 0.9) / 0.6) ** 2)
chord = sum(np.sin(2 * np.pi * f0 * 2 ** (t / d * 0.5) * t) for f0 in (262, 330, 392, 523))
trem = 0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)
save('portal_A_whoosh', (sweep * 1.5 + chord * 0.25 * trem * np.clip(t / 1.2, 0, 1)) * env(n, 0.05, 1.0))
# B: deep energy hum that swirls (wobble) + sparkles
hum = np.sin(2 * np.pi * 70 * t + 3 * np.sin(2 * np.pi * 2.2 * t)) + 0.5 * np.sin(2 * np.pi * 140 * t)
sp = np.zeros(n)
for k in range(60):
    p = int(rng.uniform(0.3, d - 0.3) * SR); m = int(0.12 * SR); ff = rng.uniform(2000, 5000)
    if p + m < n: sp[p:p + m] += np.sin(2 * np.pi * ff * t_(0.12)[:m]) * np.exp(-np.linspace(0, 8, m)) * 0.3
save('portal_B_energy', (hum * 0.6 * np.clip(t / 0.8, 0, 1) + sp) * env(n, 0.1, 1.0))
# C: magic burst: bright sparkle hit, then a soft angelic pad
hit = noise(n) * np.exp(-t * 9) * 0.8 + np.sin(2 * np.pi * 1046 * t) * np.exp(-t * 3) * 0.6
pad = sum(np.sin(2 * np.pi * f0 * t + 0.3 * np.sin(2 * np.pi * 5 * t)) for f0 in (523, 659, 784, 1046)) * 0.15
save('portal_C_magic', (hit + pad * np.clip((t - 0.2) / 0.8, 0, 1)) * env(n, 0.005, 1.2))
print('done', sorted(p.name for p in OUT.glob('*.mp3')))
