# Raining Eggs (Roblox) - guide for Claude

Two people work on this game, each with their own Claude, through this Git repository. Always `git pull` before you start, commit small steps with clear messages, and `git push` when a step works. Tell the user which files you changed.

## The game
Bright, blocky Roblox simulator. Eggs fall from the sky in 10 zones (one long strip along +Z, 140 studs each); you catch them by touching them (basket on your back), hatch them in the EGGS menu (each card's HATCH opens ONE egg, HATCH ALL opens all), pets ride in the basket and earn cash every second once you walk them into your own pen (8 bases behind the plaza). Upgrades: basket, luck (plaza shops), training (treadmill speed, bought in the UPGRADE menu; no prompt on the treadmill). Rebirth, Index (cash bonus per completed zone), daily rewards, game passes, leaderboards, DataStore save. SELL shop: its own "SELL PETS" menu (tabs BASKET / PEN, pet cards with 3D picture, tap to select, SELL n FOR $x).

Events: EGG STORM (random), BIG EGG DROP every 5 minutes (a 26-stud egg falls fast onto the white road of a random occupied zone, throws away players under it, digs a solid crater and stays in it; everyone gets a Bonk Hammer / Pillow Bat; hits knock back and cancel claims; hold E 5 s on the round E button in the middle of the egg to win a pet with x25 luck).

Hatch show: world-space VFX module `HatchVFX` (Config `C.HATCH_STYLE = "vfx"`). Sounds = one uploaded sheet `rbxassetid://140444619596476` (table `HFX` in the client), master volume `HatchVFX M.VOLUME = 0.5`.

## Repository layout
- `game/` - Roblox scripts: `Server.server.lua` (ServerScriptService.GameServer), `Client.client.lua` (StarterPlayerScripts.GameClient), `Config.lua`, `UIMenus.lua`, `HatchVFX.lua`, `Sfx.lua`, `PetBuilder.lua`, `PetData.lua`, `PropsMeta.lua`, `treadmills/` (ReplicatedStorage.Shared), `meshes.json` (ids of the Blender meshes already uploaded to Roblox), `props_meta.json`.
- `map/gen_map.py` - generates the whole map (`map/map.json`); `map/to_rbxlx.py "JOC v105"` builds the full place file (map + lighting + all scripts + BIG EGG modules/animations + Assets) to `Desktop/youtube/roblox/RAINING EGGS - JOC v105.rbxlx`.
- `event_bigegg/` - BIG EGG DROP visuals made with Codex: `roblox/FX.lua`, `BigEggVFX.lua`, `WeaponFX.lua` (ReplicatedStorage.BigEggFX), `animations/*.rbxmx` (ReplicatedStorage.BigEggAnims), models/audio.
- `blender/`, `audio/`, `pets/` - scripts that made the meshes, sounds and pets (outputs are not in the repo).

## Build and test
1. `py map/gen_map.py` (only after map changes), then `py map/to_rbxlx.py "JOC v<next number>"`. Use a NEW version number every time (Studio keeps open files and saves over them).
2. Syntax check: `luau-compile --null game/*.lua event_bigegg/roblox/*.lua` (Luau compiler from the Luau GitHub releases).
3. Open the .rbxlx in Roblox Studio, Play. Test keys (Studio only): F1..F5 hatch show of that rarity, F6 secret step, Shift = batch, F8 = BIG EGG drop now.
4. Publishing to the shared Team Create game overwrites it: agree with your teammate before you publish.

## Rules
- Do NOT change RemoteEvent names/arguments (Remotes: EggSpawn, EggGone, Catch, Hatch, Notice, Action, BigEgg, BigEggSwing), DataStore keys or the save format. Action verbs: hatch, hatch1, upgrade, shop, sellpet, sellpets, rebirth, daily, bigegg (Studio only).
- Do NOT change prices or odds in Config unless asked.
- `Client.client.lua`'s main chunk is near Luau's 200-local limit: new code goes in do-blocks, functions or new ModuleScripts.
- Collision: map MeshParts loaded from rbxlx collide as ONE big box, so irregular meshes (trees, lollipops, crystals, towers, ...) are `CanCollide=false` with a fitted invisible helper block (e.g. the tree trunk); box-shaped meshes (fences, houses, toy blocks) are solid; small or flat decor (< 3 studs, < 0.4 thick, flowers, lights, water, arches) is soft so players never get stuck. See `soft_mesh()` and `solidify()` in `gen_map.py`.
- The owner dislikes big UI redesigns: keep the current HUD/menu style and improve things in place. Pets and egg meshes are uploaded assets (ids in `meshes.json`).
- Test in Studio when you can and say exactly what you tested and what you could not.

## Latest
v104 (19 Nov 2026): SELL PETS menu with selectable pet cards, single-egg HATCH, pen entrance in fence wood colours, fitted hitboxes, solid crater + big egg, faster big egg fall with knockback, new street lamps, Rebirth NOW>NEXT medals, BIG EGG every 5 minutes, quieter hatch sounds.
