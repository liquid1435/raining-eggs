import json, os, urllib.request, shutil
KEY = open(r"C:\Users\onixfly\backtester\promo\elevenlabs.key").read().strip()
OUT = r"E:\rainingeggs\audio\new3"
DESK = r"C:\Users\onixfly\Desktop\RAINING EGGS NOU\SUNETE NOI 3"
os.makedirs(OUT, exist_ok=True); os.makedirs(DESK, exist_ok=True)
S = [
 ("cumparare_7_kaching", 1.2, "Short punchy cartoon cash register ka-ching purchase sound for a kids mobile game, bright bell, clean, no voice"),
 ("cumparare_8_pop", 1.0, "Satisfying bubbly pop with a quick sparkly upward chime, cute Roblox simulator buy button sound, clean, no voice"),
 ("cumparare_9_level", 1.5, "Happy short success jingle: three quick rising xylophone notes and a shimmer, video game item purchased, no voice"),
]
for name, dur, text in S:
    req = urllib.request.Request("https://api.elevenlabs.io/v1/sound-generation",
        data=json.dumps({"text": text, "duration_seconds": dur, "prompt_influence": 0.6}).encode(),
        headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    p = os.path.join(OUT, name + ".mp3")
    with urllib.request.urlopen(req, timeout=120) as r, open(p, "wb") as f:
        f.write(r.read())
    shutil.copy(p, DESK)
    print("ok", name)
