# Big Egg Drop

Watch [the 25-second Blender preview](preview/big_egg_event.mp4) with sound. At 14.15 seconds, Nova interrupts a claim with the Bonk Hammer, holds E for five uninterrupted seconds, then wins the drop. The camera follows the drop into the crater, moves alongside the hammer strike, then closes on Nova during the celebration. [Previous preview (v3)](preview/big_egg_event_v3.mp4)

## Studio import

1. Use the 3D Importer on the three FBXs in `models`. Keep the adjacent PNGs beside them. Each contains one UV-mapped mesh. Suggested heights are 10 studs for BigEgg and 3 studs for each weapon. Scale uniformly.
2. On the egg MeshPart, use a SurfaceAppearance with `Sunburst_Color.png` as the ColorMap and `Sunburst_Emission.png` as the EmissiveMaskContent. Set EmissiveTint to warm ivory and start EmissiveStrength at 2. The white lines in the mask are the shell fissures. [SurfaceAppearance properties](https://create.roblox.com/docs/reference/engine/classes/SurfaceAppearance)
3. Put each weapon mesh directly under a Tool as `Handle`. Use `BonkHammer_Color.png` for the hammer and `PillowBat_Color.png` for the bat. Make the Handle unanchored, massless and noncolliding. Adjust Tool.Grip until the right hand closes on the wrapped grip. Optional Attachments named `TrailBase` and `TrailTip` on Handle override the default swing endpoints.
4. Create a folder in ReplicatedStorage with three sibling ModuleScripts named `FX`, `BigEggVFX` and `WeaponFX`. Paste in the corresponding files from `roblox`. Require BigEggVFX and WeaponFX from a LocalScript. FX supplies their emitters, trails, rings and labels.
5. Insert the ten files from `animations` using **Insert from File**. Each imports as a KeyframeSequence. Publish each sequence as an animation under the experience owner or group. To inspect a clip before publishing, load it on the matching rig. [Importing saved sequences](https://create.roblox.com/docs/education/build-it-play-it-island-of-move/sharing-animations) · [Animation Editor](https://create.roblox.com/docs/animation/editor)
6. Upload `audio/Bonk.wav` and `models/Scorch.png`. Enter the resulting IDs and the ten animation IDs below as **string attributes** using the form `rbxassetid://123456789`. The mesh and color texture IDs belong on the imported model assets.

| Instance | Attribute | Source file |
| --- | --- | --- |
| Bonk Hammer Tool | SwingR6 / SwingR15 | BonkHammer_R6.rbxmx / BonkHammer_R15.rbxmx |
| Pillow Bat Tool | SwingR6 / SwingR15 | PillowBat_R6.rbxmx / PillowBat_R15.rbxmx |
| WeaponFX ModuleScript | HitR6 / HitR15 | Hit_R6.rbxmx / Hit_R15.rbxmx |
| BigEggVFX ModuleScript | ClaimR6 / ClaimR15 | Claim_R6.rbxmx / Claim_R15.rbxmx |
| BigEggVFX ModuleScript | CelebrateR6 / CelebrateR15 | Celebrate_R6.rbxmx / Celebrate_R15.rbxmx |
| WeaponFX ModuleScript | HitSound | Bonk.wav |
| BigEggVFX ModuleScript | ScorchTexture | Scorch.png |

## Client cue sheet

Use an anchored presentation copy of the egg on each client. Use a horizontal, anchored, archivable ground Part with a queryable top surface. Supply its top-center landing point in world coordinates and leave room for the crater within that Part. On layered or Terrain maps, provide a landing pad with clearance beneath it for the bowl (at least half the shell height). Keep the authoritative claim target separate so the visual fall and settling motion do not move the interaction point.

| Cue | Call | Presentation |
| --- | --- | --- |
| Announcement | `BigEggVFX.PlayIncoming(pos)` | Starts the ten-second countdown, darkens the scene and pulses the landing marker. |
| Countdown ends | `BigEggVFX.PlayFall(egg, pos)` | Moves the visual from the sky over 1.4 seconds, then drives the lower third of the shell below grade. The shell compresses at contact, wobbles into place and bobs slightly within the crater under a pulsing light and layered beacon. Use the imported single shell for squash and stretch. Multipart presentation models retain their authored proportions. |
| Touchdown, 1.4 s after fall starts | `BigEggVFX.PlayImpact(pos)` | Cuts a client-side opening, raises a fractured rim and throws dust and rocks outward. A dark floor and sloped earth line the hole. Camera shake attenuates to zero at 85 studs. |
| Claim available | `BigEggVFX.PlayClaimProgress(egg, 0)` | Shows the E prompt above the shell. |
| Holding E | `BigEggVFX.PlayClaimProgress(egg, elapsed / BigEggVFX.ClaimDuration, claimantCharacter)` | Fills the radial meter over five seconds and blends into a looping kneel on the supplied character. Update from the current hold. Reset to zero on release. |
| Claim interrupted | `BigEggVFX.PlayClaimBreak(egg)` | Splits the meter into coral segments. Show a fresh prompt when another attempt is available. |
| Swing begins | `local track = WeaponFX.PlaySwing(tool)` | Selects the wielder's rig clip and activates the edge trail during the swing. |
| Confirmed hit | `WeaponFX.PlayHit(targetCharacter, track, direction)` | Pauses the attacker's swing for 55 ms, tips the target into a short directional stumble and plays a small contact burst and bonk. Only the victim feels the brief camera shake. The last two arguments are optional. Direction is a world-space knockback vector. |
| Winner confirmed | `BigEggVFX.PlayWin(egg, playerName, winnerCharacter)` | Captures the resting position, hides the local shell and launches golden pieces and confetti. The supplied winner raises both arms. The winner banner lasts four seconds. |
| Event teardown or abort | `BigEggVFX.Clear()` | Removes the crater, restores the landing surface, releases the banner, tint and continuing effects and restores the supplied visual. On victory, retire the egg copy before cleanup to avoid showing it again. |

Call the fall and impact cues separately. Fan out the winner cue to every client. The hammer's authored contact pose is at 0.310 s and the pillow's is at 0.295 s. The one-second hit clips shift weight into a catch step, overshoot and recover. The optional character arguments on the progress and win cues select the appropriate R6 or R15 clip. Pass the same claimant on every positive progress update. Release, interruption, victory and teardown fade the hold out.

The integration owns input, hit validation, physical knockback, the one-second stun, claim cancellation and the award. On a confirmed hit, apply the shove once through the authoritative physics path. For example, for an unanchored target root and a horizontal unit vector pointing away from the attacker, use `root:ApplyImpulse(root.AssemblyMass * (away * 16 + Vector3.yAxis * 8))`. Pass the same direction to PlayHit on observing clients, including the victim. Set the authoritative hold duration to five seconds and reset elapsed time on release or interruption. Where character animation playback already replicates, play each character's track once through the owning animation path. Client-only presentation rigs can play all cues locally.

## Verification

The Blender 4.2.3 preview is 1920 x 1080 at 30 fps with an original synthesized soundtrack. Eevee renders the 9,216-face shell under a sun and two area lights with screen-space ambient occlusion, motion blur, depth of field and a fog-glow pass. The captions are composited after the camera effects. All three modules passed `luau-compile --null`. The three exported FBXs were reimported with their UVs and color textures. All ten animation files were checked for rig hierarchy, ordered keyframes and valid rotation matrices. Published-ID playback and multiplayer verification remain part of Studio integration.
