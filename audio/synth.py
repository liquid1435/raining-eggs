r"""Raining Eggs sound effects, synthesised from scratch (no samples, so they are ours to use).

  py synth.py   -> sfx\*.wav (one per sound, for listening), rainingeggs_sfx.wav + .ogg (all sounds in one file),
                   ..\game\Sfx.lua (start + length of every sound inside the sheet)

The game plays a piece of the sheet with Sound.PlaybackRegion, so only ONE audio upload is needed.
"""
import math, random, wave, struct, json, pathlib, subprocess

HERE = pathlib.Path(__file__).resolve().parent
SR = 44100
rnd = random.Random(5)
NOTE = lambda n: 440 * 2 ** ((n - 69) / 12)            # midi note -> Hz
C5, D5, E5, F5, G5, A5, B5 = 72, 74, 76, 77, 79, 81, 83


def silence(t):
    return [0.0] * int(SR * t)


def mix(*tracks):
    n = max(len(t) for t in tracks)
    out = [0.0] * n
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    return out


def at(t, track):
    return silence(t) + track


def tone(dur, f0, f1=None, shape='sine', att=0.005, dec=None, vib=0.0, vibf=6.0, curve=1.0, harm=None):
    """one note: frequency glides f0 -> f1, attack + exponential decay (dec = time to fall to ~5%)"""
    n = int(SR * dur)
    f1 = f0 if f1 is None else f1
    dec = dec or dur
    out, ph = [], 0.0
    for i in range(n):
        t = i / SR
        u = (t / dur) ** curve if dur else 0
        f = f0 + (f1 - f0) * u
        f *= 1 + vib * math.sin(2 * math.pi * vibf * t)
        ph += 2 * math.pi * f / SR
        if shape == 'sine':
            v = math.sin(ph)
        elif shape == 'soft':                            # rounded square, cute "chip" sound
            v = math.sin(ph) + 0.3 * math.sin(3 * ph) + 0.12 * math.sin(5 * ph)
        elif shape == 'saw':
            v = sum(math.sin(k * ph) / k for k in range(1, 7)) * 0.6
        elif shape == 'bell':                            # inharmonic partial = bell / chime
            v = math.sin(ph) + 0.45 * math.sin(2.76 * ph) * math.exp(-t * 9) + 0.2 * math.sin(5.4 * ph) * math.exp(-t * 16)
        else:
            v = math.sin(ph)
        if harm:
            v += harm * math.sin(2 * ph)
        a = min(1.0, t / att) if att > 0 else 1.0
        e = math.exp(-3.0 * t / dec)
        tail = min(1.0, (dur - t) / 0.01)               # no click at the end
        out.append(v * a * e * tail)
    return out


def noise(dur, dec=None, lp=1.0, hp=0.0, att=0.001):
    """filtered white noise; lp / hp = one-pole filter amounts 0..1"""
    n = int(SR * dur)
    dec = dec or dur
    out, y, prev, hy = [], 0.0, 0.0, 0.0
    for i in range(n):
        t = i / SR
        x = rnd.uniform(-1, 1)
        y += lp * (x - y)
        hy = y - prev if hp else y
        prev = y
        a = min(1.0, t / att)
        out.append(hy * a * math.exp(-3.0 * t / dec) * min(1.0, (dur - t) / 0.005))
    return out


def gain(track, g):
    return [v * g for v in track]


def norm(track, peak=0.9):
    m = max(abs(v) for v in track) or 1
    return [v * peak / m for v in track]


# ---------------------------------------------------------------- the sounds
S = {}
# bubbly "bloop" for buttons: quick upward pop + a bright little ping on top
S['ui_click'] = mix(tone(0.1, 380, 950, curve=0.5, dec=0.06, harm=0.25), at(0.04, gain(tone(0.12, 1320, 1480, shape='bell', dec=0.07), 0.45)))
S['ui_hover'] = gain(tone(0.05, 1250, 1600, shape='soft', dec=0.025), 0.6)
S['catch'] = mix(tone(0.09, 480, 980, 'sine', dec=0.09, curve=0.6), at(0.06, gain(tone(0.3, NOTE(96), shape='bell', dec=0.18), 0.5)),
                 at(0.09, gain(tone(0.25, NOTE(103), shape='bell', dec=0.14), 0.35)))
S['coin'] = mix(tone(0.07, NOTE(88), shape='soft', dec=0.08), at(0.065, tone(0.35, NOTE(93), shape='soft', dec=0.22)))
S['speed_gain'] = mix(tone(0.06, NOTE(84), shape='soft', dec=0.06), at(0.05, tone(0.06, NOTE(88), shape='soft', dec=0.06)),
                      at(0.1, tone(0.16, NOTE(91), shape='soft', dec=0.12)))
S['tread_on'] = mix(tone(0.3, 180, 820, 'soft', att=0.02, dec=0.5, curve=1.4), at(0.22, gain(tone(0.3, NOTE(96), shape='bell', dec=0.15), 0.5)))
S['tread_off'] = tone(0.35, 760, 140, 'soft', att=0.01, dec=0.4, curve=0.7)
S['tread_step'] = mix(tone(0.09, 120, 70, 'sine', dec=0.05), gain(noise(0.04, lp=0.25, dec=0.02), 0.5))
hum = []
for i in range(int(SR * 1.2)):                          # motor: low hum with a wobble, soft ends so it can be repeated
    t = i / SR
    v = (math.sin(2 * math.pi * 72 * t) + 0.5 * math.sin(2 * math.pi * 144 * t) + 0.25 * math.sin(2 * math.pi * 216 * t))
    v *= 0.75 + 0.25 * math.sin(2 * math.pi * 9 * t)
    v *= min(1.0, t / 0.04) * min(1.0, (1.2 - t) / 0.04)
    hum.append(v)
S['tread_hum'] = mix(hum, gain(noise(1.2, lp=0.05, dec=10), 0.6))


def chirp(dur, f, depth, rate, up):
    return tone(dur, f, f * up, 'sine', att=0.004, dec=dur, vib=depth, vibf=rate)


S['pet_chirp'] = mix(chirp(0.08, 2600, 0.12, 38, 1.35), at(0.12, chirp(0.1, 2900, 0.1, 42, 1.45)))
S['pet_yip'] = mix(tone(0.16, 950, 1500, 'sine', att=0.01, dec=0.2, vib=0.03, vibf=18, harm=0.25),
                   at(0.17, tone(0.12, 1250, 1050, 'sine', att=0.01, dec=0.12, harm=0.2)))


def blub(dur, f0, f1):
    out = tone(dur, f0, f1, 'sine', att=0.01, dec=dur * 1.2)
    return [v * (0.6 + 0.4 * math.sin(2 * math.pi * 28 * i / SR)) for i, v in enumerate(out)]


S['pet_blub'] = mix(blub(0.14, 260, 560), at(0.15, blub(0.16, 320, 700)))
S['egg_wobble'] = mix(tone(0.06, 760, 700, dec=0.03, harm=0.4), gain(noise(0.02, lp=0.5), 0.25))
crack = []
for k in range(7):
    crack = mix(crack, at(rnd.uniform(0, 0.24), gain(noise(0.03, lp=0.9, hp=1, dec=0.012), rnd.uniform(0.5, 1))))
S['egg_crack'] = crack
S['egg_pop'] = mix(tone(0.05, 220, 950, dec=0.05), gain(noise(0.05, lp=0.8, dec=0.02), 0.6), at(0.02, gain(noise(0.35, lp=0.06, dec=0.2), 1.4)))
S['reveal_common'] = mix(tone(0.4, NOTE(G5), shape='bell', dec=0.3), at(0.12, tone(0.6, NOTE(C5 + 12), shape='bell', dec=0.45)))
rare = []
for k, n in enumerate((C5 + 12, E5 + 12, G5 + 12, C5 + 24)):
    rare = mix(rare, at(k * 0.07, gain(tone(0.5, NOTE(n), shape='bell', dec=0.35), 0.8)))
for k in range(10):                                      # shimmer
    rare = mix(rare, at(0.3 + k * 0.04, gain(tone(0.15, NOTE(rnd.choice((96, 100, 103, 108))), shape='sine', dec=0.08), 0.25)))
S['reveal_rare'] = rare
leg = []
for k, n in enumerate((C5 - 12, E5 - 12, G5 - 12)):
    leg = mix(leg, at(k * 0.11, tone(0.14, NOTE(n), shape='saw', att=0.01, dec=0.3)))
for n in (C5, E5, G5, C5 + 12):
    leg = mix(leg, at(0.33, gain(tone(0.9, NOTE(n), shape='saw', att=0.02, dec=1.2, vib=0.006, vibf=5.5), 0.7)))
for k in range(14):
    leg = mix(leg, at(0.4 + k * 0.045, gain(tone(0.16, NOTE(rnd.choice((96, 100, 103, 108, 112))), shape='bell', dec=0.1), 0.3)))
S['reveal_legend'] = leg
S['yuck'] = mix(tone(0.42, 420, 150, 'soft', att=0.01, dec=0.6, vib=0.05, vibf=7), at(0.05, gain(noise(0.2, lp=0.1, dec=0.15), 0.4)))
fan = []
for k, n in enumerate((G5 - 12, C5, E5, G5)):
    fan = mix(fan, at(k * 0.09, tone(0.12, NOTE(n), shape='soft', dec=0.2)))
for n in (C5 + 12, E5 + 12, G5 + 12):
    fan = mix(fan, at(0.38, gain(tone(0.7, NOTE(n), shape='soft', att=0.01, dec=0.8, vib=0.006), 0.6)))
S['fanfare'] = fan

# ---------------------------------------------------------------- write
(HERE / 'sfx').mkdir(exist_ok=True)


def write(path, track):
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b''.join(struct.pack('<h', int(max(-1, min(1, v)) * 32000)) for v in track))


sheet, table, gap = [], {}, 0.3
for name, tr in S.items():
    tr = norm(tr, 0.9 if name != 'tread_hum' else 0.7)
    write(HERE / 'sfx' / f'{name}.wav', tr)
    start = len(sheet) / SR
    table[name] = [round(start, 4), round(len(tr) / SR, 4)]
    sheet += tr + silence(gap)
write(HERE / 'rainingeggs_sfx.wav', sheet)
ff = r'C:\Users\onixfly\AppData\Local\Programs\Python\Python313\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe'
subprocess.run([ff, '-y', '-loglevel', 'error', '-i', str(HERE / 'rainingeggs_sfx.wav'), '-c:a', 'libvorbis', '-q:a', '6', str(HERE / 'rainingeggs_sfx.ogg')], check=True)
rows = ''.join(f'\t{k} = {{ {v[0]}, {v[1]} }},\n' for k, v in table.items())
(HERE.parent / 'game' / 'Sfx.lua').write_text('-- generated by audio\\synth.py: start and length (seconds) of every sound inside rainingeggs_sfx.ogg\nreturn {\n' + rows + '}\n', encoding='utf-8')
print(len(S), 'sounds,', round(len(sheet) / SR, 1), 's sheet')
print(json.dumps(table))
