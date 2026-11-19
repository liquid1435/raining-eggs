import json, os, urllib.request, shutil
KEY = open(r"C:\Users\onixfly\backtester\promo\elevenlabs.key").read().strip()
OUT = r"E:\rainingeggs\audio\new7"
DESK = r"C:\Users\onixfly\Desktop\RAINING EGGS NOU\SUNETE NOI 7"
os.makedirs(OUT, exist_ok=True); os.makedirs(DESK, exist_ok=True)
S = [
 ("buy_petsim_5", 0.7, "Very short snappy game purchase click with a bright metallic coin ting on top, Roblox simulator shop, crisp, no voice"),
 ("buy_petsim_6", 1.0, "Two quick rising bell tones, ding-ding, bright and happy, mobile game purchase confirmed, no voice"),
 ("buy_petsim_7", 0.9, "Soft rounded marimba blip followed by a tiny sparkle, friendly cozy game buy sound, no voice"),
 ("buy_petsim_8", 1.1, "Coins sliding into a wallet with a bright shimmer at the end, short and clean, simulator game purchase, no voice"),
 ("buy_petsim_9", 0.8, "Low warm thump plus bright sparkle burst on top, punchy satisfying unlock purchase sound for kids game, no voice"),
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
