import json, os, urllib.request
KEY = open(r"C:\Users\onixfly\backtester\promo\elevenlabs.key").read().strip()
OUT = r"E:\rainingeggs\audio\crack"
S = [
 ("crack_1", 0.5, "Single tiny eggshell crack, close-up, dry thin shell snapping a little, crisp and clean, no music, no voice, no reverb"),
 ("crack_2", 0.6, "Small eggshell crack, a short crisp crackle of a hard egg shell splitting, close mic, no music, no voice"),
 ("crack_3", 0.8, "Medium eggshell cracking, a sharp crack followed by fine crackling as the shell splits further, close mic, no music, no voice"),
 ("crack_4", 1.0, "Big thick eggshell cracking open, loud sharp crack with crunchy splintering shell, dramatic, close mic, no music, no voice"),
 ("crack_5", 1.2, "Very heavy magical egg shell cracking, deep loud crack with long crunchy splintering, epic and powerful, no music, no voice"),
 ("shatter", 1.6, "Large egg shell bursting apart, explosive crunchy shell shatter with small shell pieces scattering on stone, powerful impact, no music, no voice"),
]
for name, dur, text in S:
    req = urllib.request.Request("https://api.elevenlabs.io/v1/sound-generation",
        data=json.dumps({"text": text, "duration_seconds": dur, "prompt_influence": 0.7}).encode(),
        headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r, open(os.path.join(OUT, name + ".mp3"), "wb") as f:
        f.write(r.read())
    print("ok", name)
