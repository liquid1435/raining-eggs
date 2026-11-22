r"""v204: calm background music loop for Raining Eggs (user: "something calm that plays while the players play").

Warm pad + soft music-box melody + gentle bass, C major, 72 BPM, 16 bars (~53 s), seamless loop (the reverb tail is
folded back into the start). Writes audio\rainingeggs_music.ogg (and .wav).

  py audio\gen_music.py
"""
import pathlib
import subprocess
import wave

import imageio_ffmpeg
import numpy as np

SR = 44100
BPM = 72
BEAT = 60 / BPM
BARS = 16
LEN = int(SR * BEAT * 4 * BARS)
OUT = pathlib.Path(__file__).resolve().parent
rng = np.random.default_rng(7)


def hz(n):  # MIDI note -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)


L = np.zeros(LEN)
R = np.zeros(LEN)


def add(sig, start, pan=0.0):
    i = int(start * SR) % LEN
    n = len(sig)
    gl, gr = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    end = i + n
    if end <= LEN:
        L[i:end] += sig * gl
        R[i:end] += sig * gr
    else:  # wrap around: seamless loop
        k = LEN - i
        L[i:] += sig[:k] * gl
        R[i:] += sig[:k] * gr
        L[:n - k] += sig[k:] * gl
        R[:n - k] += sig[k:] * gr


def pad(note, dur):
    t = np.arange(int(SR * (dur + 1.5))) / SR
    f = hz(note)
    s = sum(np.sin(2 * np.pi * f * m * t * (1 + d)) / m ** 1.6 for m, d in ((1, 0), (2, 0.0007), (3, -0.0005), (1, 0.003)))
    att = np.clip(t / 0.9, 0, 1)
    rel = np.clip((dur + 1.5 - t) / 1.5, 0, 1)
    trem = 1 + 0.06 * np.sin(2 * np.pi * 0.25 * t)
    return s * att * rel * trem * 0.05


def bell(note, vel=1.0):  # music box / soft piano pluck
    t = np.arange(int(SR * 2.6)) / SR
    f = hz(note)
    s = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 3)
         + 0.12 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t * 6))
    env = np.exp(-t * 1.9) * np.clip(t / 0.004, 0, 1)
    return s * env * 0.11 * vel


def bass(note, dur):
    t = np.arange(int(SR * dur)) / SR
    f = hz(note)
    s = np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * 2 * f * t)
    env = np.clip(t / 0.05, 0, 1) * np.exp(-t * 0.8) * np.clip((dur - t) / 0.3, 0, 1)
    return s * env * 0.09


# C - Am - F - G, then C - Em - F - G (each one bar), x2
CHORDS = [(48, [60, 64, 67]), (45, [57, 60, 64]), (41, [57, 60, 65]), (43, [55, 59, 62]),
          (48, [60, 64, 67]), (40, [55, 59, 64]), (41, [57, 60, 65]), (43, [55, 59, 62])] * 2
SCALE = [72, 74, 76, 79, 81, 84]  # C major pentatonic, high (music box)
bar = BEAT * 4
for b, (root, notes) in enumerate(CHORDS):
    t0 = b * bar
    for k, n in enumerate(notes):
        add(pad(n, bar), t0, pan=(k - 1) * 0.5)
    add(bass(root, bar * 0.95), t0)
    # melody: 4-6 soft notes per bar, chord tones preferred
    tones = [n + 12 for n in notes] + SCALE
    steps = sorted(rng.choice(8, size=rng.integers(3, 6), replace=False))
    for st in steps:
        note = int(rng.choice(tones))
        add(bell(note, 0.7 + 0.3 * rng.random()), t0 + st * BEAT / 2, pan=rng.uniform(-0.4, 0.4))
    if b % 4 == 3:  # little sparkle at the end of each phrase
        for j, n in enumerate((84, 88, 91)):
            add(bell(n, 0.35), t0 + bar - BEAT + j * 0.12, pan=0.3)

# simple stereo reverb (feedback delays), wraps around the loop
def verb(x, delays, fb):
    y = x.copy()
    for d in delays:
        n = int(d * SR)
        buf = np.zeros(LEN)
        for _ in range(6):
            buf = np.roll(x if not buf.any() else buf, n) * fb
            y += buf * 0.35
    return y


L2 = verb(L, (0.137, 0.211), 0.45)
R2 = verb(R, (0.153, 0.197), 0.45)
mix = np.stack([L2, R2], axis=1)
mix /= np.max(np.abs(mix)) * 1.12
pcm = (mix * 32767).astype(np.int16)
wav = OUT / 'rainingeggs_music.wav'
with wave.open(str(wav), 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
ogg = OUT / 'rainingeggs_music.ogg'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-loglevel', 'error', '-i', str(wav), '-c:a', 'libvorbis', '-q:a', '5', str(ogg)], check=True)
print('music', LEN / SR, 's ->', ogg)
