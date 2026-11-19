# Golden Portal VFX

Place `GoldenPortalVFX.lua` in a ModuleScript named `GoldenPortalVFX` under `ReplicatedStorage.BigEggFX`, alongside the existing `FX` ModuleScript. Require it from a LocalScript. Use anchored display eggs and an anchored altar. Distances below are in studs, and Y is world up.

## API

| Call | Timing and behavior |
| --- | --- |
| `PlayPlace(altarPart, eggModel, zoneColor)` | Drops a BasePart or Model onto the center of the altar's top face. At 0.42 s the egg touches down, a colored ring expands, sparkles scatter, and the altar beam lights. The squash settles at 0.60 s. The last sparkles expire by 1.42 s. Returns nothing. |
| `ShowPlaced(altarPart, eggModel, zoneColor)` | Immediately seats the egg in its resting pose and lights its altar. Use this when restoring a saved offering. Reusing an altar or egg replaces its previous placement effect. |
| `PlaySink(goldenEgg, beamPart, groundY, done)` | Starts a six-second cinematic and returns immediately. The altar lights pulse, the shell trembles, and branching gold fissures spread at the supplied floor height. The shaft contracts from 1.15 to 3.50 s. From 1.65 to 5.70 s the egg descends by its original height plus 2 studs amid dust, stone chips, and sparks. Camera shake falls off with viewer distance. At 6 s the temporary effects clear, the egg and optional shaft are locally hidden with collision disabled, and the optional callback runs once. |
| `ShowPortal(position, size)` | Treats `position` as the **ground point beneath the opening**. Creates a two-sided upright portal in the world XY plane, facing along Z. The default height is about 30 studs. Gold and violet filaments wind around the rim, three spiral arms turn on each face, and sparks rise through the opening. Returns the stationary, anchored root Part immediately. It supports touches, queries, and a ProximityPrompt. A subsequent call replaces it. |
| `ShowSunk(goldenEgg, beamPart)` | Instantly hides the egg and optional shaft locally and disables their collision at their current positions. Use with `ShowPortal` when loading a completed nest. |
| `Clear()` | Cancels active animation and pending completion, removes portal and altar effects, releases camera shake, and restores the original egg poses, part sizes, local visibility, and collision settings modified by the module. Safe to call repeatedly. |

Capture the portal's ground point before the descent. Use the top of the visible nest floor for `groundY` so the fissures and portal sit on the surface.

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local vfx = require(ReplicatedStorage.BigEggFX.GoldenPortalVFX)

local groundPoint = Vector3.new(goldenEgg.Position.X, groundY, goldenEgg.Position.Z)
vfx.PlaySink(goldenEgg, beamPart, groundY, function()
    local portalRoot = vfx.ShowPortal(groundPoint, 30)
    -- Attach the client interaction prompt to portalRoot here.
end)
```

Calling `PlaySink`, `ShowSunk`, or `Clear` during a sink cancels that run's callback. The module owns one active cinematic and one portal per client. The caller supplies the altar colors, completion state, and interaction handling.

[Watch the 15-second Blender concept preview](preview/portal_preview.mp4).
