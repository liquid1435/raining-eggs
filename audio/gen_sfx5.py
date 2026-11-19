import json, os, urllib.request, shutil
KEY = open(r"C:\Users\onixfly\backtester\promo\elevenlabs.key").read().strip()
OUT = r"E:\rainingeggs\audio\new5"
DESK = r"C:\Users\onixfly\Desktop\RAINING EGGS NOU\SUNETE NOI 5"
os.makedirs(OUT, exist_ok=True); os.makedirs(DESK, exist_ok=True)
S = [
 ("cumparare_14_pling", 0.6, "Very short clean UI confirm pling, single soft bell note, modern mobile game button purchase, no voice"),
 ("cumparare_15_bills", 1.2, "Fast paper money counting, banknotes flicking, short and crisp, cash spent sound, no voice"),
 ("cumparare_16_piano", 1.2, "Short bright major piano chord stab with a little sparkle, positive purchase confirmation, no voice"),
 ("cumparare_17_whoosh", 1.0, "Quick whoosh into a coin clink, item flies into your inventory, snappy cartoon game sound, no voice"),
 ("cumparare_18_yay", 1.2, "Small crowd of cartoon kids cheering yay very briefly, happy purchase celebration, game sound effect"),
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
