"""Realistic EARTH sinks (user: 'a sound of earth, like it goes into the ground'): granular soil crunch + low rumble + pebbles."""
import numpy as np, subprocess, pathlib, wave, imageio_ffmpeg
SR = 44100; OUT = pathlib.Path(__file__).parent / 'golden_sfx'; FF = imageio_ffmpeg.get_ffmpeg_exe()
def t_(d): return np.arange(int(SR * d)) / SR
def env(n, a, r):
    e = np.ones(n); na, nr = int(SR * a), int(SR * r); e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
def lp(x, k): return np.convolve(x, np.ones(k) / k, 'same')
def save(name, x):
    x = x / (np.abs(x).max() + 1e-9) * 0.9; w = OUT / (name + '.wav')
    with wave.open(str(w), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes((x * 32767).astype(np.int16).tobytes())
    subprocess.run([FF, '-v', 'error', '-y', '-i', str(w), '-b:a', '192k', str(OUT / (name + '.mp3'))], check=True); w.unlink()

def soil(n, rng, density, dur_ms=(8, 45), dark=(3, 12), vol=(0.15, 0.6), shape=None):
    """many tiny crunch grains = dirt crumbling / compressing"""
    out = np.zeros(n)
    t = np.arange(n) / SR
    for _ in range(int(density)):
        tt = rng.uniform(0, n / SR * 0.95)
        if shape is not None and rng.random() > shape(tt): continue
        m = int(rng.uniform(*dur_ms) / 1000 * SR); p = int(tt * SR)
        if p + m >= n: continue
        g = lp(rng.uniform(-1, 1, m), int(rng.uniform(*dark))) * np.exp(-np.linspace(0, rng.uniform(3, 9), m))
        out[p:p + m] += g * rng.uniform(*vol)
    return out

def rumble(n, rng, k=700): return lp(rng.uniform(-1, 1, n), k) * 9

d = 3.0; t = t_(d); n = len(t)
# H: the ground cracks open and the egg pushes down: dense crunch first, then thinner, low rumble under, pebbles rolling in
rng = np.random.default_rng(21)
crunch = soil(n, rng, 2600, shape=lambda x: np.exp(-x * 0.9))
peb = soil(n, rng, 120, dur_ms=(3, 8), dark=(1, 2), vol=(0.1, 0.35), shape=lambda x: 0.3 + 0.7 * (x > 0.8))
save('sink_H_earth', (crunch * 1.3 + peb + rumble(n, rng) * np.exp(-t * 0.6)) * env(n, 0.02, 0.6))
# I: heavier: a deep thump as it hits the ground, then soil pressing and settling, dirt falling back on top at the end
rng = np.random.default_rng(33)
thump = np.sin(2 * np.pi * 48 * t) * np.exp(-t * 6) * 2.2
press = soil(n, rng, 2000, dur_ms=(15, 70), dark=(6, 18), vol=(0.2, 0.7), shape=lambda x: 0.4 + 0.6 * np.exp(-x))
fall = soil(n, rng, 500, dur_ms=(5, 20), dark=(2, 5), vol=(0.1, 0.4), shape=lambda x: 1.0 if x > 1.9 else 0.05)
save('sink_I_heavy_earth', (thump + press + fall * 0.9 + rumble(n, rng, 900) * np.exp(-t * 0.8)) * env(n, 0.005, 0.5))
# J: slow, deep sink: the earth slowly gives way (long low groan + continuous fine crumble), last soft crunch
rng = np.random.default_rng(45)
groan = lp(rng.uniform(-1, 1, n), 1200) * 12 * (0.7 + 0.3 * np.sin(2 * np.pi * 1.3 * t)) + 0.4 * np.sin(2 * np.pi * (38 - 8 * t / d) * t)
fine = soil(n, rng, 3200, dur_ms=(5, 25), dark=(2, 8), vol=(0.08, 0.3))
last = np.zeros(n); p = int(2.5 * SR); last[p:] = soil(n - p, rng, 200, dur_ms=(20, 60), dark=(4, 10), vol=(0.3, 0.8))
save('sink_J_slow_earth', (groan + fine + last) * env(n, 0.3, 0.4))
print('ok')
