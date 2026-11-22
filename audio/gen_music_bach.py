r"""v206 (user: "something classical, like Mozart"): J. S. Bach, Prelude in C major BWV 846 (public domain), played
slowly on a soft synthesized piano with pedal and light reverb; bars 1-19 (ends on C, loops seamlessly).
Writes audio\rainingeggs_music.ogg (and .wav).

  py audio\gen_music_bach.py
"""
import pathlib
import subprocess
import wave

import imageio_ffmpeg
import numpy as np

SR = 44100
QUARTER = 60 / 58          # slow and calm
SIX = QUARTER / 4          # sixteenth note
BAR = QUARTER * 4
OUT = pathlib.Path(__file__).resolve().parent
NAMES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def midi(n):
    acc = n.count('#') - n.count('b')
    name, octave = n[0], int(n.rstrip('#b')[-1] if n[-1] not in '#b' else n[-2])
    return 12 * (octave + 1) + NAMES[name] + acc


def m(s):
    return [midi(x) for x in s.split()]


BARS = [m(x) for x in (
    'C4 E4 G4 C5 E5', 'C4 D4 A4 D5 F5', 'B3 D4 G4 D5 F5', 'C4 E4 G4 C5 E5',
    'C4 E4 A4 E5 A5', 'C4 D4 F#4 A4 D5', 'B3 D4 G4 D5 G5', 'B3 C4 E4 G4 C5',
    'A3 C4 E4 G4 C5', 'D3 A3 D4 F#4 C5', 'G3 B3 D4 G4 B4', 'G3 Bb3 E4 G4 C#5',
    'F3 A3 D4 A4 D5', 'F3 Ab3 D4 F4 B4', 'E3 G3 C4 G4 C5', 'E3 F3 A3 C4 F4',
    'D3 F3 A3 C4 F4', 'G2 D3 G3 B3 F4', 'C3 E3 G3 C4 E4',
)]
LEN = int(SR * BAR * len(BARS))
L = np.zeros(LEN)
R = np.zeros(LEN)


def hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def piano(n, dur, vel):
    """soft piano: a few slightly stretched partials, faster decay for the high ones, felt-like attack"""
    t = np.arange(int(SR * (dur + 1.2))) / SR
    f = hz(n)
    s = np.zeros_like(t)
    for k, a in ((1, 1.0), (2, 0.42), (3, 0.2), (4, 0.1), (5, 0.05), (6, 0.03)):
        fk = f * k * (1 + 0.0004 * k * k)
        s += a * np.sin(2 * np.pi * fk * t) * np.exp(-t * (0.9 + 0.55 * k) * (f / 260) ** 0.35)
    att = np.clip(t / 0.006, 0, 1)
    rel = np.clip((dur + 1.2 - t) / 1.2, 0, 1)   # pedal up at the end of the bar
    return s * att * rel * vel * 0.085


def add(sig, start, pan):
    i = int(start * SR) % LEN
    n = len(sig)
    gl, gr = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    k = min(n, LEN - i)
    L[i:i + k] += sig[:k] * gl
    R[i:i + k] += sig[:k] * gr
    if n > k:  # wrap: seamless loop
        L[:n - k] += sig[k:] * gl
        R[:n - k] += sig[k:] * gr


rng = np.random.default_rng(3)
for b, notes in enumerate(BARS):
    t0 = b * BAR
    # the prelude's figure, twice per bar: 1 2 3 4 5 3 4 5 (sixteenths); the pedal holds the bar
    order = [0, 1, 2, 3, 4, 2, 3, 4] * 2
    for j, idx in enumerate(order):
        start = t0 + j * SIX + rng.uniform(-0.006, 0.006)        # a human touch
        vel = (0.95 if j % 8 == 0 else 0.7) * (0.9 + 0.1 * rng.random())
        dur = BAR - j * SIX
        pan = (notes[idx] - 60) / 30
        add(piano(notes[idx], dur, vel), start, max(-0.6, min(0.6, pan)))

# light stereo reverb (comb filters on the loop)
def comb(x, d, fb):
    n = int(d * SR)
    y = np.zeros(LEN)
    tap = x.copy()
    for _ in range(8):
        tap = np.roll(tap, n) * fb
        y += tap
    return y


wetL = comb(L, 0.0297, 0.62) + comb(L, 0.0371, 0.6) + comb(L, 0.0411, 0.58)
wetR = comb(R, 0.0313, 0.62) + comb(R, 0.0353, 0.6) + comb(R, 0.0437, 0.58)
mix = np.stack([L + 0.16 * wetL, R + 0.16 * wetR], axis=1)
mix /= np.max(np.abs(mix)) * 1.15
pcm = (mix * 32767).astype(np.int16)
wav = OUT / 'rainingeggs_music.wav'
with wave.open(str(wav), 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
ogg = OUT / 'rainingeggs_music.ogg'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-loglevel', 'error', '-i', str(wav), '-c:a', 'libvorbis', '-q:a', '5', str(ogg)], check=True)
print('music', round(LEN / SR, 1), 's ->', ogg)
