# Task for Codex: "BIG EGG DROP" special event (Raining Eggs, Roblox)

Game: Raining Eggs (Roblox, blocky bright style; map in E:\rainingeggs\map, game scripts in E:\rainingeggs\game, Blender pipeline in E:\rainingeggs\blender).
Your role: animations, VFX, models, presentation. Do NOT edit files in E:\rainingeggs\game or E:\rainingeggs\map. Work only inside E:\rainingeggs\event_bigegg. Claude will wire your work into the server/client systems after the user approves.

## The event (user's idea)
From time to time a GIANT special egg falls into the middle of the map with a beautiful, cinematic animation. All players rush there and fight with weapons; the first one to claim the egg gets it. Professional animations + VFX.

## What to make
1. **Announcement**: screen-wide banner "BIG EGG INCOMING!" + countdown 10 s, sky darkens, a glowing marker/target circle appears on the ground where it will land.
2. **Fall animation**: egg comes from the sky trailing fire/light (Trail + ParticleEmitters), slight spin, camera shake for nearby players, impact = shockwave ring, dust burst, debris chunks, crater/scorch decal, flash. Egg then floats slightly and pulses with a glow aura + light beam to the sky.
3. **Weapons (kid-friendly, no blood/kill)**: 2-3 tools, e.g. Bonk Hammer, Pillow Bat, Egg Blaster. Hit = knockback + stun 1 s + stars VFX + hit sound. Professional swing animations (R15 + R6 KeyframeSequences or Animation data), hit-stop, trail on swing.
4. **Claim mechanic visuals**: player holds E near egg for 3 s to claim; radial progress ring over the egg; getting hit cancels it (break VFX on the ring). Winner: egg cracks with golden explosion, confetti, "PLAYER claimed the BIG EGG!" banner for everyone.
5. **Big egg model**: in the same style as the eggs from E:\rainingeggs\blender (gen_eggs2.py), bigger, golden/rainbow with glowing cracks. FBX export for Roblox + texture.

## Deliverables (in E:\rainingeggs\event_bigegg)
- `models\` big egg FBX + textures, weapon models FBX.
- `roblox\` Luau ModuleScripts with only the VFX/animation functions (e.g. `BigEggVFX.lua` with PlayIncoming(pos), PlayFall(egg,pos), PlayImpact(pos), PlayClaimProgress(egg,p), PlayClaimBreak(egg), PlayWin(egg,playerName); `WeaponFX.lua` with PlaySwing(tool), PlayHit(character)). Pure client-side effects, no game logic, no DataStore.
- `animations\` swing/hit animations (KeyframeSequence .rbxmx).
- `preview\big_egg_event.mp4` Blender preview video (~20 s) of the whole sequence so the user can approve the look.
- `README.md`: what each file is, how to import into Studio, which asset IDs need uploading.

Check Luau syntax with: C:\Users\onixfly\roblox\tools\luau\luau-compile.exe --null <file>
Blender: E:\tools\blender-4.2.3-windows-x64\blender.exe
