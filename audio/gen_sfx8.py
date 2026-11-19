import json, os, urllib.request, shutil
KEY = open(r"C:\Users\onixfly\backtester\promo\elevenlabs.key").read().strip()
OUT = r"E:\rainingeggs\audio\new8"
DESK = r"C:\Users\onixfly\Desktop\RAINING EGGS NOU\SUNETE NOI 8"
os.makedirs(OUT, exist_ok=True); os.makedirs(DESK, exist_ok=True)
S = [
 ("buy_20_bubble", 0.8, "Cute bubbly water bubble pop sequence rising in pitch, playful and short, game purchase, no coins, no money sounds, no voice"),
 ("buy_21_boing", 0.8, "Springy cartoon boing with a happy little upward wobble, funny cute game unlock, no coins, no money, no voice"),
 ("buy_22_harp", 1.2, "Quick bright harp glissando upward, short and magical, item unlocked in a cozy game, no coins, no money, no voice"),
 ("buy_23_synth", 0.8, "Modern soft synth success blip, two notes up, smooth and rounded like a phone app confirmation, no coins, no money, no voice"),
 ("buy_24_powerup", 1.0, "Classic cartoon power-up sound, fast rising sweep with a bright finish, energetic game upgrade, no coins, no money, no voice"),
 ("buy_25_fanfare", 1.2, "Tiny short trumpet ta-da fanfare, two brass notes, cheerful and quick, game item bought, no coins, no money, no voice"),
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
