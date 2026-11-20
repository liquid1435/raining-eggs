"""Decode the finished movie in Blender. Use -- samples to save review stills."""
import bpy
import struct
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
renders = root / "renders"
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 20
strip = scene.sequence_editor_create().sequences.new_movie(
    "Starlight review", str(renders / "preview.mp4"), 1, 1)
assert strip.frame_duration == 400, strip.frame_duration
element = strip.elements[0]
assert (element.orig_width, element.orig_height) == (1920, 1080)
assert abs(strip.fps - 20) < .001
with (renders / "hero.png").open("rb") as f:
    header = f.read(24)
assert header[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", header[16:24]) == (1920, 1080)
print(f"Verified {strip.frame_duration} frames at {strip.fps} fps, 1920 x 1080, plus full-size hero.")
if "samples" in sys.argv:
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 50
    scene.view_settings.view_transform = "Standard"
    for frame in (45, 192, 301, 400):
        scene.frame_set(frame)
        scene.render.filepath = str(renders / f"review_{frame}.png")
        bpy.ops.render.render(write_still=True)
