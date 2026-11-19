"""Sell sound options (ElevenLabs sound generation) -> audio/sell/sell_1..3.mp3 (+ .ogg for the Roblox upload)."""
import json, pathlib, subprocess, urllib.request
HERE = pathlib.Path(__file__).resolve().parent
KEY = open(r"C:\Users\onixfly\backtester\promo\elevenlabs.key", encoding="utf-8-sig").read().strip()
FF = r'C:\Users\onixfly\AppData\Local\Programs\Python\Python313\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe'
OUT = HERE / "sell"
OUT.mkdir(exist_ok=True)
N = ", mobile game UI sound effect, polished, satisfying, clean, no music, no voice"
S = [
    ("sell_4", 0.8, "Short crisp magical coin pickup, two bright rising notes with a sparkle, like collecting gems in a mobile game" + N),
    ("sell_5", 1.0, "Cartoon pop then a soft bouncy coin jingle and a cute success ding, kid friendly" + N),
    ("sell_6", 1.2, "Arcade style money gain: fast rising coin counter ticks ending in a bright bell, retro and punchy" + N),
]
for name, dur, text in S:
    req = urllib.request.Request("https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_128",
                                 data=json.dumps({"text": text, "duration_seconds": dur, "prompt_influence": 0.6}).encode(),
                                 headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        (OUT / f"{name}.mp3").write_bytes(r.read())
    subprocess.run([FF, '-loglevel', 'error', '-y', '-i', str(OUT / f"{name}.mp3"), '-c:a', 'libvorbis', '-q:a', '6', str(OUT / f"{name}.ogg")], check=True)
    print("ok", name)
