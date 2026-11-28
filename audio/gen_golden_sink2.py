"""More SINK options (user liked none of A-C): D cartoon gulp, E sand sink, F stone platform, G magic swallow."""
import numpy as np, subprocess, pathlib, wave, imageio_ffmpeg
SR = 44100; OUT = pathlib.Path(__file__).parent / 'golden_sfx'; rng = np.random.default_rng(11); FF = imageio_ffmpeg.get_ffmpeg_exe()
def t_(d): return np.arange(int(SR * d)) / SR
def env(n, a, r):
    e = np.ones(n); na, nr = int(SR * a), int(SR * r); e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
def lp(x, k): return np.convolve(x, np.ones(k) / k, 'same')
def nz(n): return rng.uniform(-1, 1, n)
def save(name, x):
    x = x / (np.abs(x).max() + 1e-9) * 0.9; w = OUT / (name + '.wav')
    with wave.open(str(w), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes((x * 32767).astype(np.int16).tobytes())
    subprocess.run([FF, '-v', 'error', '-y', '-i', str(w), '-b:a', '192k', str(OUT / (name + '.mp3'))], check=True); w.unlink()
d = 2.8; t = t_(d); n = len(t)
# D: cartoon "gulp" - the ground swallows the egg: wobbly descending bloop + bubble pops + soft thump
f = 420 * 2 ** (-2.2 * t / d) * (1 + 0.08 * np.sin(2 * np.pi * 11 * t))
gulp = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 0.5)
pops = np.zeros(n)
for k in range(9):
    p = int((0.3 + k * 0.22) * SR); m = int(0.08 * SR); ff = 600 + 150 * rng.random()
    if p + m < n: pops[p:p + m] += np.sin(2 * np.pi * np.cumsum(np.linspace(ff, ff * 1.8, m)) / SR) * np.exp(-np.linspace(0, 7, m)) * 0.4
thump = np.zeros(n); p = int(2.35 * SR); m = n - p; thump[p:] = np.sin(2 * np.pi * 60 * t_(m / SR)[:m]) * np.exp(-t_(m / SR)[:m] * 12) * 1.2
save('sink_D_gulp', (gulp + pops + thump) * env(n, 0.02, 0.3))
# E: sand sink - hissing sand flowing down + muffled low rumble, slowing
hiss = (nz(n) - lp(nz(n), 3)) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)) * np.exp(-t * 0.5)
save('sink_E_sand', (lp(hiss, 2) * 0.8 + lp(nz(n), 600) * 5 * np.exp(-t * 0.3)) * env(n, 0.2, 0.8))
# F: stone platform lowering - grinding stone loop + clank stop at the end
grind = lp(nz(n), 18) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 16 * t)))
clank = np.zeros(n); p = int(2.4 * SR); m = n - p; tt = t_(m / SR)[:m]
clank[p:] = (np.sin(2 * np.pi * 180 * tt) + 0.6 * np.sin(2 * np.pi * 412 * tt)) * np.exp(-tt * 10) * 1.5
save('sink_F_stone', (grind * np.clip((2.4 - t) / 0.2, 0, 1) + clank + lp(nz(n), 500) * 3) * env(n, 0.05, 0.25))
# G: magic swallow - golden shimmer pulled down into a deep whoomp
f2 = 1600 * 2 ** (-4 * t / d)
sh = sum(np.sin(2 * np.pi * np.cumsum(f2 * r) / SR) for r in (1, 1.25, 1.5)) * 0.3 * (0.6 + 0.4 * np.sin(2 * np.pi * 14 * t))
whoomp = np.zeros(n); p = int(2.1 * SR); m = n - p; tt = t_(m / SR)[:m]
whoomp[p:] = np.sin(2 * np.pi * np.cumsum(np.linspace(120, 40, m)) / SR) * np.exp(-tt * 5) * 1.6
save('sink_G_swallow', (sh * np.clip((2.2 - t) / 0.3, 0, 1) + whoomp) * env(n, 0.05, 0.3))
print('ok')
