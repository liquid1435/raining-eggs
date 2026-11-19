import json, os, urllib.request
KEY = open(r"C:\Users\onixfly\backtester\promo\elevenlabs.key").read().strip()
OUT = r"E:\rainingeggs\audio\hatchfx"
N = ", game sound effect, clean, no music, no voice"
S = [
 ("step_1", 0.8, "Soft magical shimmer swell, gentle sparkle rising, rarity level up" + N),
 ("step_2", 0.9, "Bright magical power up swell with sparkles, rising tone, rarity level up" + N),
 ("step_3", 1.0, "Strong magical power up whoosh with electric sparkles, rising, rare item level up" + N),
 ("step_4", 1.2, "Powerful mystical energy surge, deep whoosh rising into crystal shimmer, epic level up" + N),
 ("step_5", 1.5, "Massive golden divine energy surge, deep boom rising into bright heavenly shimmer, legendary level up" + N),
 ("zap", 0.5, "Short crackling electric lightning zap, sparky and bright" + N),
 ("shing", 0.7, "Crystal blades appearing, bright metallic shing with sparkle tail" + N),
 ("riser", 1.4, "Fast intense magical energy riser building tension, whoosh getting higher and louder before an explosion" + N),
 ("burst", 2.2, "Huge magical explosion burst, deep impact boom with bright sparkle debris and shimmering tail" + N),
 ("reveal", 1.6, "Triumphant bright magical reveal chime with sparkles, new creature appears, satisfying" + N),
]
for name, dur, text in S:
    req = urllib.request.Request("https://api.elevenlabs.io/v1/sound-generation",
        data=json.dumps({"text": text, "duration_seconds": dur, "prompt_influence": 0.6}).encode(),
        headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r, open(os.path.join(OUT, name + ".mp3"), "wb") as f:
        f.write(r.read())
    print("ok", name)
