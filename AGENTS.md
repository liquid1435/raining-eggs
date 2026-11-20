# Notes for Codex (from the owner's Claude) - read before every task

The owner is Romanian, a beginner, and works with Claude (Claude Code) + you together.
Roles: Claude = game systems code; Codex = Blender models, VFX, animations, renders, automation. Do not change
Claude's game systems unless the task says so. Claude usually writes your task in a TASK_CODEX*.md file in the
folder you work in: follow it exactly and work only in that folder.

## Always
- SAVE CREDITS: one shared script instead of many, render once, look at the result, fix only what is wrong.
  No extra videos or long explanations unless asked.
- Keep your scripts in scripts\ (do NOT delete them at the end; Claude reuses them).
- Blender: E:\tools\blender-4.2.3-windows-x64\blender.exe in background mode with python scripts.
- Luau check: C:\Users\onixfly\roblox\tools\luau\luau-compile.exe --null <file>.
- Check your renders by looking at them before you finish.

## Projects
### Raining Eggs (Roblox) - E:\rainingeggs (Git: github.com/liquid1435/raining-eggs, private)
Read E:\rainingeggs\CLAUDE.md for the game, layout, build and rules. State on 20 Nov 2026 = v133:
- 10 zones (world 1) + WORLD 2 in space (y 900): Cosmic Nest, Moon Craters, Nebula Reef, then COMING SOON.
  The Golden Portal (Golden Nest, after 10 altar eggs) leads there.
- Portal VFX: event_bigegg\roblox\GoldenPortalVFX.lua (your design from codex_portal2, recoloured violet;
  ShowPortal(pos, size, theme) theme "cosmic" for the world 2 exit).
- Pets: your 50 voxel pets (E:\rainingeggs\codex_pets_all, style = Roblox "Steal an Egg") are in the game, cut into
  parts per bone (blender\anim_codex_pets.py) and animated by game\PetAnim.lua with your 4 clips
  (Idle, Walk, HappyHatch, PenLife). Gold/Rainbow = your _Gold/_Rainbow textures.
- Earlier work of yours: event_bigegg (BIG EGG DROP visuals, animations), codex_pet / codex_pet2 (Starlight Dragon,
  rejected: owner wants blocky voxel pets, not smooth chibi), codex_pet3 (Tabby Cat, approved style).
- Owner's taste: blocky voxel animals like "Steal an Egg", realistic proportions (not toys), violet portal,
  professional effects, nothing laggy on phones.

### Voxel creature art - E:\ytdesign\elephant (Claude) and E:\ytdesign\codex_animals (you)
Blender voxel creatures on a dark cosmic stage (cog coins, stars, glowing orange floor rings). The owner liked the
first earth/grass cat (ref\cat.png) and the polished ginger cat. Your 5 animals (wolf, owl, stag, bear, fox) were
liked; V2 = real natural colours, real eyes, smooth not pixelated (TASK_CODEX_V2.md).

### YouTube videos - E:\ytdesign
Story videos (heists, mysteries). Approved designs so far: documentary case-file, cinematic photoreal stills made
with your image tool (E:\ytdesign\ai, Dresden). Next story: Antwerp Diamond Heist (2003), new style being chosen
(samples in E:\ytdesign\antwerp\styles).
