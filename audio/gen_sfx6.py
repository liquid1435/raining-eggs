import json, os, urllib.request, shutil
KEY = open(r"C:\Users\onixfly\backtester\promo\elevenlabs.key").read().strip()
OUT = r"E:\rainingeggs\audio\new6"
DESK = r"C:\Users\onixfly\Desktop\RAINING EGGS NOU\SUNETE NOI 6"
os.makedirs(OUT, exist_ok=True); os.makedirs(DESK, exist_ok=True)
S = [
 ("buy_petsim_1", 0.9, "Roblox pet simulator style purchase sound: short glossy bright bling with a quick sparkly glitter shimmer, polished mobile game UI, no voice"),
 ("buy_petsim_2", 0.8, "Shiny cartoon purchase success sound like in Pet Simulator: soft pop then a high glittering twinkle, very clean and satisfying, no voice"),
 ("buy_petsim_3", 1.0, "Bubbly glossy game shop buy sound: quick upward bloop into a crystal sparkle sparkle, cute simulator game, no voice"),
 ("buy_petsim_4", 0.9, "Satisfying shiny reward ding with a little magical glitter sweep, premium polished Roblox simulator purchase, short, no voice"),
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
