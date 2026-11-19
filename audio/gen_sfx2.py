import json, os, sys, urllib.request, shutil
KEY = open(r"C:\Users\onixfly\backtester\promo\elevenlabs.key").read().strip()
OUT = r"E:\rainingeggs\audio\new2"
DESK = r"C:\Users\onixfly\Desktop\RAINING EGGS NOU\SUNETE NOI 2"
os.makedirs(OUT, exist_ok=True); os.makedirs(DESK, exist_ok=True)
S = [
 ("cumparare_4_bling", 1.5, "Bright cheerful video game purchase sound: quick sparkling coin bling followed by a happy rising chime, cartoon mobile game, clean, no voice"),
 ("cumparare_5_powerup", 1.8, "Satisfying cartoon game power-up purchase sound: bubbly pop then rising magical sparkle arpeggio, kid friendly Roblox style, clean, no voice"),
 ("cumparare_6_jackpot", 2.0, "Short happy game reward sound: coins pouring into a pile with a bright bell ding at the end, cheerful arcade, clean, no voice"),
 ("zona_4_epic", 5.0, "Epic triumphant video game new area unlocked jingle: big orchestral brass fanfare with drums and shimmering sparkles, rising and celebratory, ends with a long magical ringing chord, kid friendly adventure game, no voice"),
 ("zona_5_magie", 5.0, "Magical new world discovered sound for a cartoon game: twinkling harp glissando, choir ahh swell, sparkling chimes, warm uplifting chord that rings out slowly, no voice"),
 ("zona_6_victorie", 5.5, "Celebratory game level unlock music sting: happy upbeat brass and bells melody with a drum roll, confetti sparkles, big final chord that holds and fades, Roblox simulator style, no voice"),
]
for name, dur, text in S:
    req = urllib.request.Request("https://api.elevenlabs.io/v1/sound-generation",
        data=json.dumps({"text": text, "duration_seconds": dur, "prompt_influence": 0.6}).encode(),
        headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    p = os.path.join(OUT, name + ".mp3")
    with urllib.request.urlopen(req, timeout=120) as r, open(p, "wb") as f:
        f.write(r.read())
    shutil.copy(p, DESK)
    print("ok", name, os.path.getsize(p))
