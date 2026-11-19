import json, os, urllib.request, shutil
KEY = open(r"C:\Users\onixfly\backtester\promo\elevenlabs.key").read().strip()
OUT = r"E:\rainingeggs\audio\new9"
DESK = r"C:\Users\onixfly\Desktop\RAINING EGGS NOU\SUNETE NOI 9"
os.makedirs(OUT, exist_ok=True); os.makedirs(DESK, exist_ok=True)
S = [
 ("buy_26_bloop", 0.7, "Soft rounded bloop that bends upward, cute and bouncy, toy-like game purchase, no coins, no money, no trumpets, no brass, no voice"),
 ("buy_27_chime", 1.0, "Three fast ascending glockenspiel notes, light and playful, item bought in a kids game, no coins, no money, no trumpets, no brass, no voice"),
 ("buy_28_sparkle", 0.9, "Quick airy whoosh up into soft twinkling sparkles, magical and light, game unlock, no coins, no money, no trumpets, no brass, no voice"),
 ("buy_29_pop", 0.6, "Single fat juicy cartoon pop with a tiny squeak, very satisfying button press, game purchase, no coins, no money, no trumpets, no brass, no voice"),
 ("buy_30_kalimba", 1.0, "Warm kalimba two-note melody going up, friendly and calm, cozy game purchase, no coins, no money, no trumpets, no brass, no voice"),
 ("buy_31_zap", 0.7, "Short bright electric zap-sparkle, energetic arcade unlock blip, clean, no coins, no money, no trumpets, no brass, no voice"),
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
