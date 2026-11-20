# Task for Codex: ONE premium animated pet for Raining Eggs (Roblox)

User wants NEW animal models for the game. First ONE model, shown to the user before more are made.
It must look PROFESSIONAL: top-tier Roblox pet quality (Pet Simulator 99 / Adopt Me level), WITH EFFECTS AND ANIMATIONS.

Game: Raining Eggs, a bright Roblox simulator (catch falling eggs, hatch pets, pets stand in your pen and earn cash).
Current pets (see ref/) are cute, smooth, chunky toys. The new pet must fit that world but look clearly more premium.

The pet: LEGENDARY "Starlight Dragon" baby dragon: big head, big shiny eyes, tiny horns, small wings, round belly,
short legs, curled tail with a glowing tip, pastel palette (lavender + mint with gold details), a few glowing star spots.
Cute, friendly, readable from far away.

Tools: Blender at E:\tools\blender-4.2.3-windows-x64\blender.exe (run it in background mode with python scripts).
Work ONLY in this folder (E:\rainingeggs\codex_pet2). Keep scripts in scripts\, so everything can be re-run.

Requirements:
1. Model: clean smooth game-ready mesh, max ~8,000 triangles, UV-unwrapped, one 1024x1024 baked colour texture
   (soft shading/AO painted in) + emission mask for glowing parts (star spots, tail tip, eyes highlight).
   Standing pose, facing +Z (Roblox front), origin at the bottom centre between the feet, about 5 units on the longest side.
2. Rig + animations (simple, reliable armature, skinned): 
   - Idle (loop ~2 s): breathing, tail sway, slow wing flutter, blink.
   - Walk/hop (loop ~1 s): bouncy pet-follow hop.
   - Happy/Hatch reveal (~2 s): pops up, spins, wings spread, lands.
3. Effects (in the preview render, and described for Roblox): sparkle particles around the body, glowing tail tip trail,
   soft glow/bloom on emissive parts, a rarity aura ring on the ground (gold/legendary). If possible also write
   roblox\StarlightDragonVFX.lua (ParticleEmitters/Attachments/Trail/PointLight setup a server script can attach to the model).
4. Export: models\StarlightDragon.fbx with armature + the 3 animations (re-import once to check), textures in models\.
5. Preview for the user (MOST IMPORTANT, the user decides from this):
   renders\preview.mp4 1920x1080 ~20 s, Eevee with bloom, nice pastel background + soft ground:
   turnaround (idle), then walk/hop, then the hatch reveal with all effects. Also renders\hero.png beauty shot.
   Use ffmpeg if present, otherwise Blender's own FFMPEG output.
6. README.md: files, triangle count, animation names/frame ranges, how to import in Roblox Studio.

Take the time needed for the highest quality. Check your renders by looking at frames before finishing.
