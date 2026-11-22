-- Raining Eggs: shared numbers + pet builder (ReplicatedStorage.Config)
local C = {}

C.ZONE_LEN = 140        -- zone i covers z = (i-1)*140 .. i*140
C.EGG_X = 150           -- eggs land between x = -150 .. 150
C.EGG_Y = 105           -- height the eggs start from
C.PEN_MAX = 10          -- equipped pets: they stand in your pen and earn cash (v119, was 12)
C.STORAGE_MAX = 50      -- your other pets wait in storage (PETS menu: tap to equip, EQUIP BEST); a full storage sells its weakest
C.SELL_MULT = 30        -- sell price = income per second * this
C.FUSE = 3              -- same pets needed for the next tier
C.AUTO_FUSE = false     -- v143 (user): 3 same pets no longer fuse into Gold on their own

C.GOLDEN_CHANCE = 1 / 30
C.GOLDEN_LUCK = 8
C.ROTTEN_CHANCE = 0.1
C.ROTTEN_SLOW = 3       -- seconds
C.ROTTEN_FACTOR = 0.45  -- walk speed while slowed

C.COMBO_TIME = 7        -- seconds to catch the next egg
C.COMBO_STEP = 0.05     -- luck per combo step
C.COMBO_MAX = 20

C.STORM_FIRST = { 360, 900 }   -- random seconds after the server starts (6-15 min)
C.STORM_EVERY = { 900, 2400 }  -- random time between storms (15-40 min)
-- BIG EGG DROP: a giant egg falls in the plaza, players fight with weapons, holding E for 5 s claims it
C.BIGEGG_FIRST = { 300, 300 }   -- seconds after the server starts (user: every 5 minutes)
C.BIGEGG_EVERY = { 300, 300 }   -- between drops: every 5 minutes
C.TEST_ALL_ZONES_FREE = true    -- Studio only: all 10 zones open for free (to test the Golden Nest portal); the real game is not affected
C.SELL_SOUND = ""              -- sound when you sell pets (rbxassetid://...), empty = the coin sound
C.HATCH_STYLE = "vfx"         -- "vfx" = new world-space hatch show (HatchVFX), "old" = the v85 show
C.BIGEGG_SIZE = 26              -- studs tall; it lands on the white road in the middle of a random zone
C.BIGEGG_CLAIM = 5              -- seconds to hold E
C.BIGEGG_LIFE = 120             -- the egg disappears if nobody claims it
C.BIGEGG_LUCK = 25              -- luck multiplier of the pet the winner hatches
C.BIGEGG_STUN = 1               -- seconds a hit player is slowed
C.BIGEGG_WEAPON_CD = 0.7        -- seconds between swings
C.BIGEGG_REACH = 9              -- studs a swing reaches
-- published animation ids (Studio: Animation Editor > Publish). Empty = in Studio the bundled clips are used
C.BIGEGG_ANIMS = { SwingHammerR6 = "", SwingHammerR15 = "", SwingPillowR6 = "", SwingPillowR15 = "", HitR6 = "", HitR15 = "",
	ClaimR6 = "", ClaimR15 = "", CelebrateR6 = "", CelebrateR15 = "", HitSound = "", ScorchTexture = "" }
C.STORM_SHOW = 300      -- the countdown banner shows only in the last 5 minutes
C.STORM_LEN = 45
C.STORM_RATE = 3        -- eggs fall this many times more often
C.STORM_LUCK = 2
C.STORM_EGG_LUCK = 40
C.STORM_EGG_LINGER = 5  -- seconds the storm egg waits on the ground

C.INDEX_BONUS = 0.1     -- cash per completed zone
C.REBIRTH_BONUS = 0.5   -- cash and training per rebirth
C.REBIRTH_SPEED_SCALE = 1e13 -- v148 balance: first rebirth after ~3 h of play (the faster early treadmill needed a bigger scale; was 1e6)

C.RARITY = {
	{ name = "Common", odds = 2, mult = 1, color = Color3.fromRGB(205, 208, 215) },
	{ name = "Uncommon", odds = 4, mult = 3, color = Color3.fromRGB(96, 214, 96) },
	{ name = "Rare", odds = 20, mult = 10, color = Color3.fromRGB(80, 160, 255) },
	{ name = "Epic", odds = 150, mult = 40, color = Color3.fromRGB(180, 100, 255) },
	{ name = "Legendary", odds = 2000, mult = 250, color = Color3.fromRGB(255, 204, 40) },
}
C.TIER = {
	{ name = "", mult = 1 },
	{ name = "Gold ", mult = 3 },
	{ name = "Rainbow ", mult = 10 },
}

-- pet = { name, body colour, accent colour, ears (0 none, 1 short, 2 tall), kind ("q" four legs, "b" bird, "o" blob) }
local function zone(name, req, income, eggCol, eggSpot, pets)
	local list = {}
	for i, p in ipairs(pets) do
		list[i] = { name = p[1], c = p[2], a = p[3], ears = p[4], kind = p[5], income = income * C.RARITY[i].mult }
	end
	return { name = name, req = req, eggCol = eggCol, eggSpot = eggSpot, pets = list }
end

local W = { 245, 247, 252 }
C.ZONES = {
	zone("Sunny Meadow", 0, 1, { 250, 240, 214 }, { 150, 200, 120 }, {
		{ "Fox", { 232, 120, 50 }, W, 1, "q" },
		{ "Owl", { 150, 110, 70 }, { 240, 220, 180 }, 1, "b" },
		{ "Stag", { 176, 100, 60 }, { 240, 230, 200 }, 1, "q" },
		{ "Lion", { 220, 170, 80 }, { 150, 80, 40 }, 1, "q" },
		{ "Pegasus", W, { 190, 150, 255 }, 1, "q" },
	}),
	zone("Mushroom Grove", 500, 8, { 190, 130, 255 }, W, {
		{ "Chameleon", { 90, 190, 120 }, { 200, 240, 120 }, 0, "q" },
		{ "Red Panda", { 200, 80, 40 }, W, 1, "q" },
		{ "Axolotl", { 255, 170, 200 }, { 240, 90, 140 }, 0, "o" },
		{ "Jackalope", { 140, 95, 60 }, { 240, 220, 160 }, 2, "q" },
		{ "Kitsune", W, { 255, 120, 60 }, 2, "q" },
	}),
	zone("Candy Canyon", 5e3, 60, { 255, 150, 180 }, W, {
		{ "Fennec Fox", { 240, 200, 140 }, W, 2, "q" },
		{ "Cockatoo", W, { 255, 220, 60 }, 0, "b" },
		{ "Toucan", { 30, 30, 36 }, { 255, 150, 30 }, 0, "b" },
		{ "Peacock", { 40, 90, 200 }, { 40, 200, 140 }, 0, "b" },
		{ "Unicorn", W, { 255, 110, 210 }, 1, "q" },
	}),
	zone("Toy Town", 4e4, 450, { 240, 70, 70 }, W, {
		{ "Penguin", { 30, 30, 40 }, W, 0, "b" },
		{ "Pangolin", { 170, 120, 80 }, { 220, 180, 130 }, 0, "q" },
		{ "Komodo Dragon", { 110, 100, 70 }, { 170, 150, 110 }, 0, "q" },
		{ "Mandrill", { 90, 80, 60 }, { 240, 60, 60 }, 1, "q" },
		{ "Qilin", { 40, 170, 160 }, { 255, 204, 40 }, 1, "q" },
	}),
	zone("Crystal Coast", 2.5e5, 3500, { 80, 230, 255 }, W, {
		{ "Manta Ray", { 40, 50, 80 }, W, 0, "o" },
		{ "Shark", { 120, 135, 150 }, W, 0, "o" },
		{ "Narwhal", { 150, 165, 185 }, W, 0, "o" },
		{ "Humpback Whale", { 40, 60, 90 }, { 210, 220, 230 }, 0, "o" },
		{ "Kraken", { 60, 70, 110 }, { 170, 110, 255 }, 0, "o" },
	}),
	zone("Spooky Hollow", 2e6, 25000, { 255, 132, 30 }, { 24, 28, 52 }, {
		{ "Wolf", { 150, 155, 165 }, W, 1, "q" },
		{ "Crocodile", { 80, 110, 60 }, { 170, 180, 110 }, 0, "q" },
		{ "Basilisk", { 70, 140, 70 }, { 240, 210, 90 }, 0, "q" },
		{ "Cerberus", { 60, 30, 34 }, { 255, 90, 40 }, 1, "q" },
		{ "Fenrir", { 40, 50, 66 }, { 150, 220, 255 }, 1, "q" },
	}),
	zone("Thunder Peaks", 1.5e7, 200000, { 255, 226, 60 }, { 24, 28, 52 }, {
		{ "Eagle", { 110, 70, 40 }, W, 0, "b" },
		{ "Bear", { 110, 70, 45 }, { 170, 120, 80 }, 1, "q" },
		{ "Snow Leopard", { 220, 220, 215 }, { 60, 60, 70 }, 1, "q" },
		{ "Griffin", { 210, 170, 100 }, W, 1, "q" },
		{ "Thunderbird", { 50, 60, 110 }, { 120, 230, 255 }, 0, "b" },
	}),
	zone("Neon City", 1e8, 1.5e6, { 255, 60, 200 }, W, {
		{ "Octopus", { 220, 90, 70 }, { 255, 170, 150 }, 0, "o" },
		{ "Sphinx", { 220, 190, 130 }, { 40, 60, 160 }, 1, "q" },
		{ "Hydra", { 60, 90, 50 }, { 170, 120, 255 }, 0, "q" },
		{ "Phoenix", { 230, 70, 30 }, { 255, 210, 60 }, 0, "b" },
		{ "Eastern Dragon", { 30, 160, 150 }, { 255, 204, 40 }, 1, "q" },
	}),
	zone("Cloud Kingdom", 1e9, 1.2e7, W, { 255, 150, 200 }, {
		{ "Snowy Owl", W, { 255, 200, 220 }, 1, "q" },
		{ "Swan", { 150, 200, 255 }, { 255, 240, 130 }, 0, "b" },
		{ "Arctic Fox", { 255, 150, 200 }, { 150, 200, 255 }, 1, "q" },
		{ "Sky Whale", { 255, 240, 130 }, W, 2, "q" },
		{ "Seraph Lion", W, { 255, 222, 50 }, 1, "q" },
	}),
	zone("Golden Nest", 2.5e10, 1e8, { 255, 204, 40 }, W, {
		{ "Golden Pheasant", { 255, 204, 40 }, { 255, 240, 150 }, 0, "b" },
		{ "Gold Scarab", { 255, 214, 80 }, W, 2, "q" },
		{ "Royal Tiger", { 255, 180, 40 }, { 160, 100, 250 }, 1, "q" },
		{ "Golden Ram", { 255, 204, 40 }, { 240, 66, 66 }, 1, "q" },
		{ "Celestial Dragon", { 255, 240, 150 }, { 160, 100, 250 }, 2, "o" },
	}),
}
-- v116: the 10 normal zones (gates, unlocks, index, altars). Zone 11 below is the secret one.
C.NZ = #C.ZONES

-- ============================================================ WORLD 2 (v119, v139: 10 zones): COSMIC NEST .. GALAXY THRONE, then the end wall
-- A strip of floating zones in space high above the map (same layout as world 1: zone k of world 2 covers
-- z = (k-1)*140 .. k*140, at height C.COSMIC.y). The only way in: the Golden Portal (all 10 altars) -> Cosmic Nest is
-- free, the next zones are bought at their gates like in world 1. Low gravity + night sky (client).
-- The exit portal at the start of world 2 takes you back to the Golden Nest. Keep in sync with map/gen_map.py WORLD2.
local HUGE = math.huge -- world 2 zones are never opened by the old "speed" rule
C.ZONES[C.NZ + 1] = zone("Cosmic Nest", HUGE, 1e9, { 120, 70, 230 }, { 90, 230, 255 }, {
	{ "Star Kitten", { 70, 60, 150 }, { 255, 240, 140 }, 1, "q" },
	{ "Moon Bunny", { 220, 225, 245 }, { 120, 140, 255 }, 2, "q" },
	{ "Comet Fox", { 60, 120, 255 }, { 120, 240, 255 }, 1, "q" },
	{ "Nebula Wolf", { 110, 50, 180 }, { 255, 110, 220 }, 1, "q" },
	{ "Galaxy Dragon", { 30, 24, 70 }, { 160, 255, 250 }, 1, "q" },
})
C.ZONES[C.NZ + 2] = zone("Moon Craters", HUGE, 1e10, { 200, 205, 220 }, { 120, 130, 160 }, {
	{ "Moon Mouse", { 200, 200, 210 }, { 255, 170, 190 }, 1, "q" },
	{ "Crater Pup", { 150, 150, 165 }, { 90, 90, 110 }, 1, "q" },
	{ "Rocket Rabbit", W, { 240, 70, 70 }, 2, "q" },
	{ "Astro Panda", W, { 40, 40, 52 }, 1, "q" },
	{ "Lunar Phoenix", { 220, 230, 255 }, { 120, 200, 255 }, 0, "b" },
})
C.ZONES[C.NZ + 3] = zone("Nebula Reef", HUGE, 1e11, { 255, 110, 220 }, { 90, 240, 230 }, {
	{ "Nebula Jelly", { 255, 140, 230 }, { 120, 240, 255 }, 0, "o" },
	{ "Star Fish", { 255, 200, 90 }, { 255, 120, 80 }, 0, "o" },
	{ "Comet Seahorse", { 90, 230, 210 }, { 255, 240, 150 }, 0, "b" },
	{ "Void Shark", { 40, 34, 80 }, { 160, 110, 255 }, 0, "o" },
	{ "Galaxy Kraken", { 120, 40, 160 }, { 90, 240, 230 }, 0, "o" },
})
C.ZONES[C.NZ + 4] = zone("Asteroid Belt", HUGE, 1e12, { 150, 120, 100 }, { 255, 150, 60 }, {
	{ "Meteor Mole", { 120, 100, 90 }, { 255, 150, 60 }, 1, "q" },
	{ "Rock Golem Pup", { 140, 130, 125 }, { 255, 190, 90 }, 1, "q" },
	{ "Orbit Owl", { 110, 96, 88 }, { 255, 210, 120 }, 1, "b" },
	{ "Asteroid Armadillo", { 160, 140, 120 }, { 255, 120, 40 }, 1, "q" },
	{ "Meteor Rhino", { 90, 80, 76 }, { 255, 100, 30 }, 1, "q" },
})
C.ZONES[C.NZ + 5] = zone("Solar Forge", HUGE, 1e13, { 255, 120, 40 }, { 255, 230, 90 }, {
	{ "Ember Cat", { 230, 90, 40 }, { 255, 220, 90 }, 1, "q" },
	{ "Flare Fox", { 255, 120, 30 }, W, 2, "q" },
	{ "Magma Turtle", { 70, 40, 36 }, { 255, 110, 30 }, 0, "o" },
	{ "Solar Phoenix", { 255, 150, 40 }, { 255, 240, 140 }, 0, "b" },
	{ "Sun Lion", { 255, 190, 60 }, { 255, 90, 30 }, 1, "q" },
})
C.ZONES[C.NZ + 6] = zone("Comet Glacier", HUGE, 1e14, { 200, 235, 255 }, { 90, 170, 255 }, {
	{ "Frost Penguin", { 40, 50, 70 }, W, 0, "b" },
	{ "Comet Seal", { 220, 235, 245 }, { 120, 190, 255 }, 0, "o" },
	{ "Ice Yeti Cub", W, { 120, 200, 255 }, 1, "q" },
	{ "Glacier Mammoth", { 160, 190, 220 }, W, 1, "q" },
	{ "Aurora Stag", { 210, 240, 255 }, { 120, 255, 200 }, 1, "q" },
})
C.ZONES[C.NZ + 7] = zone("Alien Jungle", HUGE, 1e15, { 130, 255, 120 }, { 190, 90, 255 }, {
	{ "Glow Gecko", { 110, 230, 120 }, { 255, 120, 220 }, 0, "q" },
	{ "Alien Frog", { 150, 255, 90 }, { 160, 80, 255 }, 0, "o" },
	{ "Tentacle Pup", { 170, 110, 255 }, { 120, 255, 160 }, 1, "q" },
	{ "Three-Eyed Monkey", { 90, 200, 160 }, { 255, 240, 120 }, 1, "q" },
	{ "Xeno Raptor", { 40, 90, 60 }, { 190, 255, 90 }, 0, "q" },
})
C.ZONES[C.NZ + 8] = zone("Black Hole", HUGE, 1e16, { 40, 30, 60 }, { 200, 120, 255 }, {
	{ "Void Cat", { 30, 26, 44 }, { 200, 120, 255 }, 1, "q" },
	{ "Shadow Bat", { 44, 36, 64 }, { 255, 90, 160 }, 2, "b" },
	{ "Eclipse Wolf", { 24, 22, 34 }, { 255, 200, 90 }, 1, "q" },
	{ "Gravity Bear", { 50, 40, 80 }, { 140, 110, 255 }, 1, "q" },
	{ "Singularity Serpent", { 16, 12, 28 }, { 255, 140, 255 }, 0, "o" },
})
C.ZONES[C.NZ + 9] = zone("Star Station", HUGE, 1e17, { 200, 210, 225 }, { 80, 220, 255 }, {
	{ "Robo Dog", { 190, 196, 210 }, { 80, 220, 255 }, 1, "q" },
	{ "Mecha Bunny", W, { 255, 90, 120 }, 2, "q" },
	{ "Laser Owl", { 120, 130, 150 }, { 255, 70, 70 }, 1, "b" },
	{ "Drone Fox", { 230, 140, 60 }, { 80, 220, 255 }, 1, "q" },
	{ "Titan Mech Lion", { 90, 96, 110 }, { 255, 210, 60 }, 1, "q" },
})
C.ZONES[C.NZ + 10] = zone("Galaxy Throne", HUGE, 1e18, { 255, 214, 80 }, { 170, 110, 255 }, {
	{ "Star Unicorn", W, { 255, 140, 230 }, 1, "q" },
	{ "Cosmic Pegasus", { 120, 90, 255 }, { 255, 230, 140 }, 1, "q" },
	{ "Celestial Tiger", { 255, 200, 90 }, { 60, 30, 120 }, 1, "q" },
	{ "Astral Griffin", { 255, 220, 120 }, { 140, 100, 255 }, 1, "b" },
	{ "Universe Dragon", { 20, 14, 50 }, { 255, 220, 100 }, 1, "q" },
})
C.TOTAL = #C.ZONES -- 20: the last zone a player can open (v139: world 2 has 10 zones like world 1)
C.COSMIC = {
	first = C.NZ + 1, last = C.TOTAL,
	y = 900,                       -- height of the world 2 ground (top)
	half = 176,                    -- half width of the zones (v120: as wide as world 1, same walls)
	eggX = 150,                    -- eggs land between x = -150 .. 150 (like world 1)
	eggHeight = 90,                -- eggs start this high above the ground
	fall = 3.6,                    -- seconds an egg falls (slow, low gravity)
	gravity = 70,                  -- workspace gravity in world 2 (normal 196.2), client side
	portal = { 0, 0, 1352, 10 },   -- Golden Portal in the Golden Nest: x, ground y, z (its plane), half width of the opening
	spawn = { 0, 906, 22 },        -- where the Golden Portal puts you (start of the Cosmic Nest)
	exit = { 0, 900, -28, 9 },     -- exit portal at the start of world 2: x, ground y, z (its plane), half width of the opening
	saturn = { 380, 1040, 120, 0.35 }, -- ringed planet centre + ring tilt (radians); the client spins Map.SaturnRing
	back = { 0, 4, 1318 },         -- where the exit portal puts you (in front of the Golden Portal)
}
-- zone index of a point in world 2 (call only when the point is up there)
function C.w2Zone(z)
	return C.NZ + math.clamp(math.floor(z / C.ZONE_LEN) + 1, 1, C.TOTAL - C.NZ)
end
-- start z of a world 2 zone
function C.w2Z0(zoneIndex)
	return (zoneIndex - C.NZ - 1) * C.ZONE_LEN
end

C.PET_COUNT = C.NZ * #C.RARITY

-- ============================================================ ZONE GATES (tweak here)
-- Cash price to open each zone, in order. Zone 1 is free. Change a number = change the price.
-- A player must buy them in order (zone 3 can not be bought before zone 2).
-- v148 balance (user: fast start as a hook, then each step harder; tools/tune_economy.py fits every price to a curve):
-- zone 2 ~1 min, 3 ~3 min, 4 ~7 min, 5 ~15 min, 6 ~30 min, 7 ~55 min, 8 ~1.5 h, 9 ~2.5 h, 10 ~4 h; world 2 zone 12 ~6.5 h .. zone 20 ~50 h.
-- Baskets, treadmill and luck follow the same kind of curve (C.BASKETS, C.TRAIN_COST, C.LUCK_COST).
-- (old) v119 balance (tools/sim_economy.py, target between medium and slow): a normal player opens zone 2 after ~4 min,
-- zone 3 ~14 min, zone 4 ~40 min, zone 5 ~2 h, zone 6 ~3.5 h, zone 7 ~5.5 h, zone 8 ~8 h, zone 9 ~11 h, zone 10 ~15 h of play.
-- (v118 prices { 0, 1e3, 1e4, 7.5e4, 5e5, 4e6, 3e7, 2.5e8, 2e9, 1.5e10 } let players open all 10 zones in ~15 minutes.)
C.ZONE_PRICE = { 0, 190, 1.2e4, 4.5e5, 1.3e7, 2.7e8, 9.1e9, 1.2e11, 2.4e12, 5.6e13, 0, 9.2e15, 1.2e17, 1.4e18, 1.8e19, 3e20, 4.2e21, 4.6e22, 6.7e23, 8e24 } -- 11-20 = world 2 (11 free: the Golden Portal)
for i, z in ipairs(C.ZONES) do
	z.price = C.ZONE_PRICE[i] or 0
end

C.GATE = {
	width = 18,              -- studs: the glowing gate between the two arch pillars (= the road: the pillars stand on its edges)
	height = 15,             -- studs: up to the sign of the arch
	thick = 1.5,             -- studs
	transparency = 0.45,     -- 0 = solid colour, 1 = invisible
	wallTransparency = 0.45, -- the walls left and right of the arch: same glow as the gate (1 = invisible)
	wallWidth = 400,         -- how far the walls reach to the sides (covers the whole island)
	blockHeight = 220,       -- invisible wall above, so nobody jumps or bounces over
	fade = 0.6,              -- seconds the gate takes to vanish after you buy it
	touchCooldown = 1.5,     -- seconds between two "you need $..." messages
	textTop = "LOCKED",                    -- small line on the gate
	textHint = "Walk into the gate to buy", -- bottom line on the gate
}

-- ============================================================ HATCH ANIMATION (tweak here)
-- Order: egg pops in -> shakes and grows -> jumps -> flash + sparkles -> pet grows in while it spins -> pet leaves
C.HATCH = {
	side = 5.5,          -- studs next to the player (left/right take turns)
	height = 3.5,        -- studs above the middle of the player
	appear = 0.12,       -- seconds: egg pops in
	shakes = 4,          -- how many times the egg rocks left-right
	shakeStep = 0.07,    -- seconds for half a rock (smaller = faster shaking)
	shakeAngle = 0.35,   -- how far it tilts (radians, 0.35 is about 20 degrees)
	eggGrow = 1.3,       -- egg size at the end of the shaking (1 = normal)
	jumpTime = 0.2,      -- seconds: the jump before it pops
	jumpHeight = 3,      -- studs
	flashTime = 0.35,    -- seconds: white flash ball
	flashSize = 11,      -- studs: how big the flash gets
	sparkles = 14,       -- particles for a Common pet
	sparklesPerRarity = 8, -- extra particles for every rarity step
	shellPieces = 7,     -- egg shell bits that fly away
	petSize = 1.2,       -- final size of the pet (1 = same as in the pen)
	petGrow = 0.45,      -- seconds: pet grows from 0 to full size
	petSpin = math.pi,   -- how much it spins while growing (math.pi = half a turn)
	hold = 0.9,          -- seconds the pet stays (Common .. Rare)
	holdRare = 2.2,      -- seconds the pet stays (Epic, Legendary)
	leave = 0.2,         -- seconds: pet shrinks away
}

-- a pet is { z = zone, i = rarity index, t = tier (1 normal, 2 gold, 3 rainbow) }
function C.petIncome(pet)
	return C.ZONES[pet.z].pets[pet.i].income * C.TIER[pet.t or 1].mult
end
function C.petName(pet)
	return C.TIER[pet.t or 1].name .. C.ZONES[pet.z].pets[pet.i].name
end
function C.petKey(pet)
	return pet.z .. "_" .. pet.i
end

-- upgrades: level starts at 0
C.MAX_LV = { train = 60, basket = 19, luck = 20 }
-- 20 baskets you BUY one after another (no upgrades); basket k holds 2 + k pets and hangs on your back (Blender mesh Basket_k)
-- BasketLv 0 = basket 1 (free), BasketLv 19 = basket 20
C.BASKETS = {
	{ name = "Old Basket", price = 0 },
	{ name = "Straw Basket", price = 26 },
	{ name = "Picnic Basket", price = 60 },
	{ name = "Flower Basket", price = 200 },
	{ name = "Honey Pot", price = 990 },
	{ name = "Mushroom Basket", price = 6.5e3 },
	{ name = "Candy Bucket", price = 4.7e4 },
	{ name = "Sand Pail", price = 3.4e5 },
	{ name = "Cookie Jar", price = 2.4e6 },
	{ name = "Pumpkin Pack", price = 1.8e7 },
	{ name = "Ice Bucket", price = 1.4e8 },
	{ name = "Tech Pack", price = 1.1e9 },
	{ name = "Ocean Basket", price = 9.4e9 },
	{ name = "Lava Basket", price = 8.8e10 },
	{ name = "Thunder Pack", price = 1e12 },
	{ name = "Neon Basket", price = 1.8e13 },
	{ name = "Cloud Basket", price = 4.6e14 },
	{ name = "Crystal Basket", price = 1.4e16 },
	{ name = "Rainbow Basket", price = 4.3e17 },
	{ name = "Royal Basket", price = 1.3e19 },
}
function C.basketRim(k) -- top of basket k, seen from the torso centre (same numbers as blender\gen_baskets20.py)
	local t = (k - 1) / 19
	local rt, h, y0 = 1.0 + 0.3 * t, 1.9 + 0.4 * t, -1.25 - 0.2 * t
	return Vector3.new(0, y0 + h + 0.1, 0.55 + rt + 0.05)
end
-- v148: price of the next treadmill / luck level (index = level you have + 1); fitted by tools/tune_economy.py
C.TRAIN_COST = { 28, 36, 47, 61, 81, 120, 240, 550, 1.1e3, 1.9e3, 3.2e3, 6.6e3, 1.7e4, 4e4, 7.9e4, 1.3e5, 2.3e5, 4.8e5, 1.1e6, 2.3e6, 4.2e6, 7.3e6, 1.4e7, 3.1e7, 6.5e7, 1.3e8, 2.7e8, 6.1e8, 1.4e9, 3e9, 6.6e9, 1.5e10, 3.4e10, 7.2e10, 1.5e11, 3.5e11, 8.4e11, 2.2e12, 6.6e12, 2.5e13, 1.1e14, 4.4e14, 1.6e15, 4.9e15, 1.5e16, 5e16, 1.8e17, 6.6e17, 2.6e18, 1.1e19, 4.9e19, 2.4e20, 1.2e21, 5.6e21, 2.6e22, 1.1e23, 5e23, 2.2e24, 9.7e24, 4.3e25 }
C.LUCK_COST = { 60, 210, 1e3, 6.4e3, 4.5e4, 3.2e5, 2.3e6, 1.6e7, 1.2e8, 1e9, 8.3e9, 7.8e10, 9e11, 1.4e13, 3.1e14, 9.2e15, 3.1e17, 1.2e19, 5.6e20, 3.1e22 }
function C.cost(kind, lv)
	if kind == "train" and C.TRAIN_COST[lv + 1] then
		return C.TRAIN_COST[lv + 1]
	elseif kind == "luck" then
		return C.LUCK_COST[lv + 1] or math.huge
	elseif kind == "train" then
		return math.floor(40 * 3 ^ lv)
	elseif kind == "basket" then
		local b = C.BASKETS[lv + 2]
		return b and b.price or math.huge
	end
	return math.floor(250 * 5 ^ lv)
end
function C.trainPower(lv) -- speed gained every 0.25 s on the treadmill (before the rebirth bonus)
	return math.floor(2 * 2.2 ^ lv + 0.5)
end
function C.basketMax(lv)
	return 3 + lv
end
function C.basketRadius(lv)
	return 4 + 0.32 * lv
end
function C.luck(lv)
	return 1 + 0.25 * lv
end
function C.comboLuck(combo)
	return 1 + math.clamp(combo - 1, 0, C.COMBO_MAX) * C.COMBO_STEP
end
function C.walkSpeed(speed)
	return math.min(16 + 7 * math.log10(1 + speed), 100)
end
function C.fallTime(zoneIndex)
	return 4.2 - 0.2 * zoneIndex
end
function C.rebirthMult(n)
	return 1 + C.REBIRTH_BONUS * n
end
function C.rebirthNeed(n) -- speed needed for rebirth number n + 1
	local zi = math.min(3 + n, C.NZ) -- the 10 normal zones (world 2 zones have no speed number)
	return C.ZONES[zi].req * 10 ^ math.max(0, 3 + n - C.NZ) * C.REBIRTH_SPEED_SCALE
end

local SUF = { "", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc" }
function C.fmt(n)
	n = math.floor(n)
	if n < 1000 then
		return tostring(n)
	end
	local i = 1
	while n >= 1000 and i < #SUF do
		n = n / 1000
		i = i + 1
	end
	local s = string.format("%.1f", math.floor(n * 10) / 10):gsub("%.0$", "")
	return s .. SUF[i]
end
function C.comma(n)
	local s = tostring(math.floor(n))
	local out = s:reverse():gsub("(%d%d%d)", "%1,"):reverse()
	return (out:gsub("^,", ""))
end
function C.clock(sec)
	sec = math.max(0, math.floor(sec))
	return string.format("%d:%02d", math.floor(sec / 60), sec % 60)
end

-- blocky pet from parts. Front looks to -Z, feet are 1.75 * s under the pivot.
local GOLD = Color3.fromRGB(255, 204, 40)
local BLACK = Color3.fromRGB(24, 28, 52)
local WHITE = Color3.fromRGB(255, 255, 255)
local BLUSH = Color3.fromRGB(255, 140, 165)

-- ============================================================ BLENDER MODELS (tweak here)
-- The pets and eggs made in Blender live in ReplicatedStorage.Assets (the server moves the imported model there).
-- Until they are imported the game uses the old block pets and eggs.
C.MESH_YAW = math.pi -- half a turn: the imported pets look to +Z, the game wants -Z (write 0 if they look backwards)
C.MESH_SIZE = 7.0  -- studs: the longest side of a pet at normal size (v128: bigger, user wanted the new pets larger)
C.PROP_YAW = math.pi -- same half turn for the Blender treadmills (write 0 if the console ends up at the wrong end)
function C.meshOf(name)
	local assets = game:GetService("ReplicatedStorage"):FindFirstChild("Assets")
	local src = assets and assets:FindFirstChild(name, true)
	if src and not src:IsA("MeshPart") then
		src = src:FindFirstChildWhichIsA("MeshPart", true)
	end
	return src
end

local petAnimMod = nil
function C.petAnim() -- v129: ReplicatedStorage.PetAnim (Codex pets made of moving parts), nil when it is not there
	if petAnimMod == nil then
		local mod = game:GetService("ReplicatedStorage"):FindFirstChild("PetAnim")
		local ok, m = false, nil
		if mod then
			ok, m = pcall(require, mod)
		end
		petAnimMod = ok and m or false
	end
	return petAnimMod or nil
end

function C.buildPet(pet, s, anchored)
	local def = C.ZONES[pet.z].pets[pet.i]
	local tier = pet.t or 1
	local PA = C.petAnim()
	if PA then -- v129: the animated Codex pet (parts) when its part meshes are imported
		local ok, am = pcall(PA.build, pet, s, anchored, C.MESH_YAW, C.MESH_SIZE)
		if ok and am then
			am.Name = C.petName(pet)
			am:SetAttribute("Tier", tier)
			am:SetAttribute("Species", def.name) -- v138: the client's flowing Gold/Rainbow coat (PetCoatFlow) looks this up
			return am
		end
	end
	local src = C.meshOf("Pet_" .. pet.z .. "_" .. pet.i)
	-- v127: the Codex pets have their own Gold / Rainbow textures (Pet_z_i_G / Pet_z_i_R); old pets only get a tint
	local variant = (tier == 2 and C.meshOf("Pet_" .. pet.z .. "_" .. pet.i .. "_G")) or (tier == 3 and C.meshOf("Pet_" .. pet.z .. "_" .. pet.i .. "_R")) or nil
	if variant then
		src = variant
	end
	if src then
		local m = Instance.new("Model")
		m.Name = C.petName(pet)
		m:SetAttribute("Tier", tier)
		m:SetAttribute("Species", def.name)
		local part = src:Clone()
		part.Name = "Body"
		local rot = src.CFrame.Rotation
		part.Size = part.Size * (C.MESH_SIZE * s / math.max(part.Size.X, part.Size.Y, part.Size.Z))
		local h = math.abs(rot:VectorToWorldSpace(part.Size).Y)
		part.CFrame = CFrame.new(0, -1.75 * s + h / 2, 0) * CFrame.Angles(0, C.MESH_YAW, 0) * rot
		part.PivotOffset = part.CFrame:Inverse() -- the model pivot stays where the block pet had it (feet 1.75 * s below)
		-- the mesh has its colours painted in; Color only tints it (white = as painted)
		part.Color = (variant and Color3.new(1, 1, 1)) or (tier == 2 and Color3.fromRGB(255, 208, 70)) or (tier == 3 and Color3.fromRGB(255, 150, 235)) or Color3.new(1, 1, 1)
		part.Material = Enum.Material.SmoothPlastic
		part.Reflectance = (tier == 2 and not variant) and 0.25 or (tier == 2 and 0.12 or 0)
		part.CanCollide = false
		part.CanTouch = false
		part.CanQuery = false
		part.Massless = true
		part.CastShadow = false
		part.Anchored = anchored
		part.Parent = m
		m.PrimaryPart = part
		return m
	end
	local idx = pet.i
	local body = Color3.fromRGB(def.c[1], def.c[2], def.c[3])
	local accent = Color3.fromRGB(def.a[1], def.a[2], def.a[3])
	if tier == 2 then
		body, accent = GOLD, Color3.fromRGB(255, 244, 170)
	elseif tier == 3 then
		body, accent = Color3.fromRGB(255, 110, 210), Color3.fromRGB(90, 230, 255)
	end
	local dark = Color3.new(body.R * 0.72, body.G * 0.72, body.B * 0.72)
	local m = Instance.new("Model")
	m.Name = C.petName(pet)
	m:SetAttribute("Tier", tier)
	local root
	local function p(sx, sy, sz, x, y, z, col, neon, name)
		local part = Instance.new("Part")
		part.Name = name or "PetPart"
		part.Size = Vector3.new(sx, sy, sz) * s
		part.CFrame = CFrame.new(x * s, y * s, z * s)
		part.Color = col
		part.Material = neon and Enum.Material.Neon or Enum.Material.SmoothPlastic
		if tier == 2 and not neon then
			part.Reflectance = 0.25
		end
		part.TopSurface = Enum.SurfaceType.Smooth
		part.BottomSurface = Enum.SurfaceType.Smooth
		part.CanCollide = false
		part.CanTouch = false
		part.CanQuery = false
		part.Massless = true
		part.CastShadow = false
		part.Anchored = anchored
		part.Parent = m
		if not root then
			root = part
			m.PrimaryPart = part
		elseif not anchored then
			local w = Instance.new("WeldConstraint")
			w.Part0 = root
			w.Part1 = part
			w.Parent = part
		end
	end
	local glow = tier == 3
	local topY, headZ, faceZ, eyeY, halfW -- where ears, horn, eyes and wings go
	if def.kind == "b" then
		p(2.2, 2, 2.2, 0, 0, 0, body, glow, "Body")
		p(2, 1.9, 1.9, 0, 1.5, -0.9, body, glow, "Body")
		p(0.6, 0.4, 0.6, 0, 1.3, -2.1, accent)
		p(0.9, 0.4, 0.9, 0, 0.3, 1.4, accent)
		for _, sx in ipairs({ -1, 1 }) do
			p(0.3, 1, 1.4, sx * 1.25, 0.1, 0.1, accent)
			p(0.4, 0.8, 0.4, sx * 0.5, -1.3, 0, accent)
			p(0.75, 0.15, 0.95, sx * 0.5, -1.675, -0.2, accent)
		end
		topY, headZ, faceZ, eyeY, halfW = 2.45, -0.9, -1.86, 1.7, 1.1
	elseif def.kind == "o" then
		p(2.8, 2, 3, 0, -0.75, 0, body, glow, "Body")
		p(1.7, 0.8, 1.8, 0, 0.6, 0.4, accent)
		p(0.7, 0.14, 0.06, 0, -1.05, -1.52, BLACK)
		for _, sx in ipairs({ -1, 1 }) do
			p(0.9, 0.45, 1, sx * 1.6, -1.52, 0.2, dark)
		end
		topY, headZ, faceZ, eyeY, halfW = 0.25, -0.9, -1.51, -0.3, 1.4
	else
		p(2.4, 1.7, 2.8, 0, 0, 0, body, glow, "Body")
		p(2.4, 2.2, 2.2, 0, 1.15, -1.7, body, glow, "Body")
		p(0.7, 0.45, 0.3, 0, 0.8, -2.9, accent)
		p(0.5, 0.5, 0.9, 0, 0.5, 1.75, accent)
		for _, sx in ipairs({ -1, 1 }) do
			p(0.7, 0.9, 0.7, sx * 0.75, -1.3, -0.9, dark)
			p(0.7, 0.9, 0.7, sx * 0.75, -1.3, 0.9, dark)
		end
		topY, headZ, faceZ, eyeY, halfW = 2.25, -1.7, -2.81, 1.3, 1.2
	end
	for _, sx in ipairs({ -1, 1 }) do
		p(0.45, 0.6, 0.08, sx * 0.6, eyeY, faceZ, BLACK)
		p(0.18, 0.18, 0.06, sx * 0.5, eyeY + 0.18, faceZ - 0.05, WHITE)
		p(0.4, 0.2, 0.06, sx * 0.98, eyeY - 0.45, faceZ, BLUSH)
		if def.ears == 1 then
			p(0.55, 0.6, 0.4, sx * 0.7, topY + 0.3, headZ, accent)
		elseif def.ears == 2 then
			p(0.5, 1.6, 0.4, sx * 0.6, topY + 0.8, headZ, accent)
		end
		if idx == 5 then
			p(0.3, 1.6, 2.2, sx * (halfW + 0.3), 0.7, 0.3, accent, true)
		end
	end
	if idx >= 4 then
		p(0.4, 1, 0.4, 0, topY + 0.5, headZ - 0.4, GOLD, true)
	end
	return m
end

-- ============================================================ NEW MENUS (game passes, daily rewards)
-- Game passes. Make them on create.roblox.com (your game > Monetization > Passes) and paste each id here.
-- While an id is 0 the store shows the pass but says "Coming soon" when you press BUY.
C.PASSES = {
	{ key = "cash2", id = 0, name = "2x Cash", desc = "All your pets earn double cash", robux = 199, icon = "coin", col = Color3.fromRGB(60, 200, 90) },
	{ key = "luck2", id = 0, name = "2x Luck", desc = "Rare pets hatch twice as often", robux = 249, icon = "clover", col = Color3.fromRGB(40, 170, 255) },
	{ key = "vip", id = 0, name = "VIP Basket", desc = "+5 basket space for every run", robux = 149, icon = "basket", col = Color3.fromRGB(255, 150, 30) },
	{ key = "fast", id = 0, name = "Fast Hatch", desc = "Egg opening plays 2x faster", robux = 79, icon = "egg", col = Color3.fromRGB(190, 90, 255) },
}
C.VIP_BASKET = 5

-- Daily rewards: claim once every 20 hours; miss 48 hours and the streak starts again at day 1.
C.DAILY_COOLDOWN = 20 * 3600
C.DAILY_RESET = 48 * 3600
C.DAILY = { -- cash = this many seconds of your income (at least min); day 7 also gives a free egg of your best zone
	{ secs = 60, min = 100 }, { secs = 120, min = 200 }, { secs = 180, min = 350 }, { secs = 300, min = 500 },
	{ secs = 420, min = 800 }, { secs = 600, min = 1200 }, { secs = 900, min = 2000, egg = true },
}

return C
