import json, os, urllib.request, shutil
KEY = open(r"C:\Users\onixfly\backtester\promo\elevenlabs.key").read().strip()
OUT = r"E:\rainingeggs\audio\new4"
DESK = r"C:\Users\onixfly\Desktop\RAINING EGGS NOU\SUNETE NOI 4"
os.makedirs(OUT, exist_ok=True); os.makedirs(DESK, exist_ok=True)
S = [
 ("cumparare_10_gem", 1.2, "Bright crystal gem collect sound, glassy sparkle ding with a soft shimmer tail, premium mobile game reward, no voice"),
 ("cumparare_11_arcade", 1.0, "Retro 8-bit arcade purchase sound, quick happy rising bleeps, chiptune coin get, no voice"),
 ("cumparare_12_bag", 1.3, "Heavy bag of coins dropped on a wooden table with a satisfying jingle, cartoon game shop, no voice"),
 ("cumparare_13_magic", 1.5, "Soft magical fairy chime sweep upward with twinkling bells, cozy cute game item unlocked, no voice"),
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
