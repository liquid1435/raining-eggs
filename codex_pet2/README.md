# Starlight Dragon

A legendary hatchling for **Raining Eggs**, with lavender skin, mint wing membranes and enamel-like gold horns. The star-shaped catchlights, forehead jewel and comet tip share an emissive texture mask.

[Watch the 20-second preview](renders/preview.mp4) · [Open the 1920 × 1080 hero image](renders/hero.png)

## Asset files

| File | Use |
| --- | --- |
| [StarlightDragon.fbx](models/StarlightDragon.fbx) | One skinned mesh, one armature and all three baked animation takes |
| [Color atlas](models/StarlightDragon_Color.png) | 1024 × 1024 sRGB texture with painted underside shading, eye gradients and catchlights |
| [Emission mask](models/StarlightDragon_Emission.png) | 1024 × 1024 grayscale mask for stars, luminous gold and eye glints |
| [Animation FBXs](models/animations/) | One file per take for Studio’s Animation Editor |
| [StarlightDragonVFX.lua](roblox/StarlightDragonVFX.lua) | Server-side ModuleScript for wing sparkles, tail ribbon, point light, hatch burst and gold ground ring |

**Geometry.** The FBX contains 7,884 triangles, 4,044 vertices and 14 bones. The bind-pose dimensions are approximately 4.99 wide × 4.77 high × 4.09 deep. The pivot sits on the ground between the feet. In the exported Y-up coordinate system, the muzzle points along +Z. The UV layout reuses painted atlas cells across matching shells. The plinth and surrounding effects belong to the presentation scene.

## Animation

The takes are baked at 24 fps. Frame ranges include both endpoints.

| Take | Frames | Duration | Playback |
| --- | --- | --- | --- |
| Idle | 1–49 | 2 s | Loop. The chest rises, the head tilts, the eyes blink, and the wings and tail sway. |
| Hop | 1–25 | 1 s | Loop. The body lifts and lands while the feet and forepaws swing. Apply horizontal travel with the pet-follow system. |
| Hatch | 1–49 | 2 s | Play once. The dragon gathers itself, springs up, turns through 360°, spreads its wings and settles. |

The 20-second showcase runs at 20 fps. The first eight seconds show the idle turnaround. The next six show the follow hop. The hatch begins at 14 seconds and returns to idle at 16 seconds.

## Import in Roblox Studio

1. Keep the two PNGs beside the main FBX. Open **File → Import**, select the main FBX and choose **Custom** for the rig type. Enable **Keep Zero Influence Bones** for the ground root and tail effect socket, and **Set Pivot to Scene Origin** for pen placement. Select **Studs** and check for a width close to 5 in the import preview. [Studio Importer settings](https://create.roblox.com/docs/studio/importer)
2. Select the skinned MeshPart. Add or select its **SurfaceAppearance** and assign the color PNG to **ColorMap** and the emission PNG to **EmissiveMaskContent**. Upload the PNGs through Studio if asset IDs are needed. Start with white **EmissiveTint** and **EmissiveStrength** of 2.6. Adjust strength in the pen’s lighting. A BloomEffect in Lighting gives bright stars and the trail a soft halo. [Roblox PBR texture guide](https://create.roblox.com/docs/art/modeling/surface-appearance)
3. Give the model an **AnimationController** with an **Animator** child. Open **Animation Editor**, select the dragon, and import each FBX from the animations folder through the editor’s FBX animation import. Save each clip with its take name and publish it under the experience owner for runtime playback. Load the resulting animation IDs through the Animator. Set the Idle and Hop tracks to loop and Hatch to play once. [Roblox custom character animation workflow](https://create.roblox.com/docs/resources/beyond-the-dark/custom-characters)
4. Place the pet using its ground pivot. For follow systems that aim Roblox’s local −Z axis along a path, apply a 180° yaw to the target CFrame so the dragon’s +Z muzzle leads.
5. Create a **ModuleScript** named **StarlightDragonVFX** in **ServerScriptService** and paste in the supplied Lua. After sizing and placing the upright pet, attach the effects from its server-side spawn code.

~~~lua
local module = require(game.ServerScriptService.StarlightDragonVFX)
local effects = module.attach(dragonModel)

-- When the reveal starts, play the one-shot track and release the burst.
hatchTrack.Looped = false
hatchTrack:Play()
effects.hatch()
~~~

The ring follows the pet’s base while the animated body jumps. The tail ribbon follows the GlowSocket bone. Repeated attach calls return the existing effect handle. Call effects.destroy() when returning the pet to a pool. Destroying the model also removes its effects.

## Rebuild and verify

Run these commands in PowerShell from this folder with Blender 4.2.3. The render script builds its scene directly from the model generator. It uses Eevee, compositor fog glow, Blender’s H.264 encoder, and the Georgia and Calibri Bold fonts included with Windows.

~~~powershell
$blender = 'E:\tools\blender-4.2.3-windows-x64\blender.exe'
& $blender -b --python-exit-code 1 -P scripts\dragon.py
& $blender -b --python-exit-code 1 -P scripts\verify.py
& $blender -b --python-exit-code 1 -P scripts\preview.py -- hero
& $blender -b --python-exit-code 1 -P scripts\preview.py -- movie
& $blender -b --python-exit-code 1 -P scripts\verify_preview.py
~~~

The FBX verifier checks the imported skin weights, triangle count, UV layer, take lengths and sampled vertex movement. It reopens each single-take file to check its duration. The preview verifier opens the encoded movie and checks its dimensions, frame count and frame rate. Adding **-- samples** writes decoded stills for visual inspection.

Verification covers the Blender FBX round trip and the local preview. Studio playback and the Lua effects still need an in-experience playtest.
