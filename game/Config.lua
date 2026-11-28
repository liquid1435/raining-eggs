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
C.GOLDEN_LUCK = 1 -- v244 (user): a golden egg = a normal egg of its zone, only the coat is 80% Gold / 20% Rainbow
C.ROTTEN_CHANCE = 0.1
C.ROTTEN_SLOW = 3       -- seconds
C.ROTTEN_FACTOR = 0.45  -- walk speed while slowed

C.COMBO_TIME = 7        -- seconds to catch the next egg
C.COMBO_STEP = 0.05     -- luck per combo step
C.COMBO_MAX = 20

C.STORM_FIRST = { 900, 1800 }  -- v224 (user: rare): random seconds after the server starts (15-30 min)
C.STORM_EVERY = { 2400, 4200 } -- v224: random time between storms (40-70 min)
-- BIG EGG DROP: a giant egg falls in the plaza, players fight with weapons, holding E for 5 s claims it
C.BIGEGG_FIRST = { 1200, 2400 } -- v244 (user: rarer): 20-40 min  -- v224 (user: SECRET EGG, rare): seconds after the server starts (10-20 min)
C.BIGEGG_EVERY = { 3000, 5400 } -- v244 (user: rarer): 50-90 min -- v224: random time between drops (25-45 min)
C.TEST_ALL_ZONES_FREE = true    -- Studio only: all 20 zones (world 1 + world 2) and the Golden Portal open for free; the real game is not affected
C.MUSIC_ID = "1848049490" -- v206: Strauss II "Voices of Spring" (Roblox Toolbox audio, chosen by the user); v204: calm background music (audio/rainingeggs_music.ogg uploaded to Roblox), "" = no music
C.MUSIC_VOLUME = 0.13 -- v208 (user): a bit quieter (was 0.22)
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
C.REBIRTH_PRICE = { 1e13, 6e13, 3.8e14, 2.6e15, 1.8e16, 1.4e17, 1.1e18, 9.5e18, 8.6e19, 8.2e20, 8.3e21, 8.9e22, 1e24, 1.2e25, 1.6e26, 2.1e27, 1e28, 4e28, 1.5e29, 6e29 } -- v244 (user): 20 rebirths, cash price from small to big, each takes longer (tools/sim_economy.py)
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
		{ "Golden Lynx", { 255, 214, 80 }, W, 2, "q" }, -- v208: was Gold Scarab (user: no insects)
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
C.ZONE_PRICE = { 0, 430, 3.4e4, 1e6, 3.1e7, 1e9, 2.6e10, 3.6e11, 7.9e12, 1.5e14, 0, 2.3e16, 2.9e17, 3.1e18, 7.9e19, 1.1e21, 1e22, 1.9e23, 2.3e24, 3.4e25 } -- 11-20 = world 2 (11 free: the Golden Portal)
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

-- v153 (user: 3 animals per rarity in every egg): variants 2 and 3 (Codex models 101-200) - { name, sound kind }
-- An egg hatches variant 1, 2 or 3 of the rolled rarity (equal chance) once that variant's meshes are imported.
C.VARIANTS = {
	[1] = { { { "Rabbit", "q" }, { "Hedgehog", "q" } }, { { "Squirrel", "q" }, { "Badger", "q" } }, { { "Wild Boar", "q" }, { "Beaver", "q" } }, { { "Lynx", "q" }, { "Moose", "q" } }, { { "Hippogriff", "b" }, { "Leaf Dragon", "q" } } },
	[2] = { { { "Frog", "o" }, { "Dormouse", "q" } }, { { "Mole", "q" }, { "Truffle Pig", "q" } }, { { "Sloth", "q" }, { "Lemur", "q" } }, { { "Spirit Elk", "q" }, { "Mushroom Deer", "q" } }, { { "Fungus Dragon", "q" }, { "Shroom Tortoise", "q" } } },
	[3] = { { { "Hamster", "q" }, { "Flamingo", "b" } }, { { "Pink Poodle", "q" }, { "Llama", "q" } }, { { "Macaw", "b" }, { "Cotton Candy Sheep", "q" } }, { { "Pink Dolphin", "o" }, { "Caramel Camel", "q" } }, { { "Candy Dragon", "q" }, { "Rainbow Alicorn", "q" } } },
	[4] = { { { "Puppy", "q" }, { "Duckling", "b" } }, { { "Wind-up Mouse", "q" }, { "Tin Turtle", "q" } }, { { "Robot Cat", "q" }, { "Clockwork Monkey", "q" } }, { { "Rocking Horse", "q" }, { "Clockwork Owl", "b" } }, { { "Mecha Rex", "q" }, { "Brick Dragon", "q" } } },
	[5] = { { { "Crab", "o" }, { "Clownfish", "o" } }, { { "Sea Turtle", "o" }, { "Pufferfish", "o" } }, { { "Dolphin", "o" }, { "Walrus", "o" } }, { { "Orca", "o" }, { "Crystal Seahorse", "o" } }, { { "Leviathan", "o" }, { "Sea Serpent", "o" } } },
	[6] = { { { "Bat", "b" }, { "Black Cat", "q" } }, { { "Raven", "b" }, { "Hyena", "q" } }, { { "Ghost Fox", "q" }, { "Werewolf Pup", "q" } }, { { "Nightmare Horse", "q" }, { "Wraith Owl", "b" } }, { { "Bone Dragon", "q" }, { "Shadow Wyvern", "b" } } },
	[7] = { { { "Mountain Goat", "q" }, { "Marmot", "q" } }, { { "Falcon", "b" }, { "Yak", "q" } }, { { "Puma", "q" }, { "Bighorn Ram", "q" } }, { { "Storm Wolf", "q" }, { "Lightning Lynx", "q" } }, { { "Storm Dragon", "q" }, { "Thunder Roc", "b" } } },
	[8] = { { { "Pigeon", "b" }, { "Rat", "q" } }, { { "Raccoon", "q" }, { "Alley Cat", "q" } }, { { "Neon Jellyfish", "o" }, { "Cyber Wolf", "q" } }, { { "Neon Tiger", "q" }, { "Holo Koi", "o" } }, { { "Cyber Phoenix", "b" }, { "Neon Manticore", "q" } } },
	[9] = { { { "Lamb", "q" }, { "Dove", "b" } }, { { "Alpaca", "q" }, { "Cloud Bunny", "q" } }, { { "Sky Ray", "o" }, { "Angel Cat", "q" } }, { { "Halo Stag", "q" }, { "Wind Serpent", "o" } }, { { "Sky Dragon", "q" }, { "Seraph Owl", "b" } } },
	[10] = { { { "Golden Hamster", "q" }, { "Gold Chick", "b" } }, { { "Golden Retriever", "q" }, { "Gold Frog", "o" } }, { { "Royal Peacock", "b" }, { "Golden Monkey", "q" } }, { { "Gilded Elephant", "q" }, { "Royal Horse", "q" } }, { { "Golden Phoenix", "b" }, { "King Griffin", "q" } } },
	[11] = { { { "Star Hamster", "q" }, { "Cosmic Chick", "b" } }, { { "Moon Fawn", "q" }, { "Stardust Ferret", "q" } }, { { "Comet Lynx", "q" }, { "Nebula Owl", "b" } }, { { "Starlight Stag", "q" }, { "Cosmic Bear", "q" } }, { { "Nova Phoenix", "b" }, { "Galaxy Griffin", "b" } } }, -- v228: world 2 variants (Codex 201-300)
	[12] = { { { "Moon Hedgehog", "q" }, { "Crater Crab", "o" } }, { { "Lunar Goat", "q" }, { "Moon Mole", "q" } }, { { "Astro Raccoon", "q" }, { "Lunar Lynx", "q" } }, { { "Moon Bear", "q" }, { "Crater Rhino", "q" } }, { { "Lunar Dragon", "q" }, { "Moon Unicorn", "q" } } }, -- v228: world 2 variants (Codex 201-300)
	[13] = { { { "Nebula Crab", "o" }, { "Star Clownfish", "o" } }, { { "Cosmic Turtle", "o" }, { "Nebula Puffer", "o" } }, { { "Galaxy Dolphin", "o" }, { "Star Ray", "o" } }, { { "Nebula Orca", "o" }, { "Cosmic Octopus", "o" } }, { { "Void Leviathan", "o" }, { "Star Serpent", "o" } } }, -- v228: world 2 variants (Codex 201-300)
	[14] = { { { "Rock Hamster", "q" }, { "Meteor Lizard", "q" } }, { { "Crater Goat", "q" }, { "Orbit Bat", "b" } }, { { "Asteroid Boar", "q" }, { "Comet Eagle", "b" } }, { { "Meteor Wolf", "q" }, { "Asteroid Tortoise", "q" } }, { { "Meteor Dragon", "q" }, { "Asteroid Titan Bear", "q" } } }, -- v228: world 2 variants (Codex 201-300)
	[15] = { { { "Ember Chick", "b" }, { "Cinder Mouse", "q" } }, { { "Flame Salamander", "q" }, { "Ash Hound", "q" } }, { { "Lava Lizard", "q" }, { "Sun Hawk", "b" } }, { { "Magma Bull", "q" }, { "Solar Tiger", "q" } }, { { "Sun Dragon", "q" }, { "Inferno Griffin", "q" } } }, -- v228: world 2 variants (Codex 201-300)
	[16] = { { { "Snow Hare", "q" }, { "Ice Puffin", "b" } }, { { "Frost Ferret", "q" }, { "Ice Otter", "o" } }, { { "Frost Lynx", "q" }, { "Ice Owl", "b" } }, { { "Glacier Bear", "q" }, { "Aurora Wolf", "q" } }, { { "Frost Dragon", "q" }, { "Ice Phoenix", "b" } } }, -- v228: world 2 variants (Codex 201-300)
	[17] = { { { "Alien Bunny", "q" }, { "Spore Lizard", "q" } }, { { "Glow Sloth", "q" }, { "Alien Toucan", "b" } }, { { "Xeno Jaguar", "q" }, { "Tentacle Bird", "b" } }, { { "Alien Gorilla", "q" }, { "Glow Panther", "q" } }, { { "Xeno Dragon", "q" }, { "Alien Hydra", "q" } } }, -- v228: world 2 variants (Codex 201-300)
	[18] = { { { "Void Mouse", "q" }, { "Shadow Raven", "b" } }, { { "Dark Matter Fox", "q" }, { "Void Lizard", "q" } }, { { "Eclipse Owl", "b" }, { "Shadow Panther", "q" } }, { { "Void Rhino", "q" }, { "Eclipse Stag", "q" } }, { { "Void Dragon", "q" }, { "Black Hole Phoenix", "b" } } }, -- v228: world 2 variants (Codex 201-300)
	[19] = { { { "Robo Cat", "q" }, { "Bolt Hamster", "q" } }, { { "Mecha Penguin", "q" }, { "Robo Turtle", "o" } }, { { "Laser Wolf", "q" }, { "Drone Eagle", "b" } }, { { "Mecha Bear", "q" }, { "Robo Rhino", "q" } }, { { "Mecha Dragon", "q" }, { "Titan Robo Griffin", "q" } } }, -- v228: world 2 variants (Codex 201-300)
	[20] = { { { "Royal Star Kitten", "q" }, { "Astral Bunny", "q" } }, { { "Celestial Deer", "q" }, { "Cosmic Peacock", "b" } }, { { "Astral Lion", "q" }, { "Galaxy Swan", "b" } }, { { "Celestial Elephant", "q" }, { "Astral Wolf King", "q" } }, { { "Cosmos Phoenix", "b" }, { "Infinity Dragon", "q" } } }, -- v228: world 2 variants (Codex 201-300)
}
for z, list in pairs(C.VARIANTS) do
	for i, vars in ipairs(list) do
		local base = C.ZONES[z].pets[i]
		base.vars = {}
		for k, v in ipairs(vars) do
			base.vars[k + 1] = { name = v[1], kind = v[2], c = base.c, a = base.a, ears = base.ears, income = base.income }
		end
	end
end
-- the definition of a pet (its variant when it has one)
function C.petDef(pet)
	local base = C.ZONES[pet.z].pets[pet.i]
	local v = pet.v or 1
	return (v > 1 and base.vars and base.vars[v]) or base
end
function C.variantCount(z, i)
	local base = C.ZONES[z] and C.ZONES[z].pets[i]
	return base and base.vars and #base.vars or 1
end

-- a pet is { z = zone, i = rarity index, t = tier (1 normal, 2 gold, 3 rainbow), v = variant (nil/1, 2, 3) }
function C.petIncome(pet)
	return C.ZONES[pet.z].pets[pet.i].income * C.TIER[pet.t or 1].mult
end
function C.petName(pet)
	return C.TIER[pet.t or 1].name .. C.petDef(pet).name
end
function C.petKey(pet) -- index key; also the asset key: Pet_<key>, Pet_<key>__<part>, Pet_<key>_G / _R
	return pet.z .. "_" .. pet.i .. ((pet.v or 1) > 1 and ("_" .. pet.v) or "")
end

-- v250 (user): every pet has a TRAIT = a visual effect by its theme (name words, else its zone). Epic and Legendary
-- pets in your pen also give a small bonus of their trait's kind (cash / egg luck / walk speed), capped.
C.TRAITS = {
	{ id = "gold", label = "Golden", icon = "✨", bonus = "cash", words = { "golden", "gold", "royal", "king", "gilded" } },
	{ id = "fire", label = "Fire", icon = "🔥", bonus = "cash", words = { "phoenix", "ember", "flare", "magma", "lava", "inferno", "solar", "sun", "flame", "cinder", "ash", "meteor" } },
	{ id = "ice", label = "Ice", icon = "❄️", bonus = "luck", words = { "frost", "ice", "glacier", "snow", "arctic", "penguin", "aurora", "yeti", "mammoth", "polar" } },
	{ id = "storm", label = "Storm", icon = "⚡", bonus = "speed", words = { "thunder", "storm", "lightning", "laser", "bolt" } },
	{ id = "shadow", label = "Shadow", icon = "🌑", bonus = "luck", words = { "void", "shadow", "eclipse", "black", "dark", "singularity", "gravity", "nightmare", "wraith", "werewolf", "raven", "bat" } },
	{ id = "star", label = "Cosmic", icon = "⭐", bonus = "luck", words = { "nebula", "galaxy", "cosmic", "star", "astral", "celestial", "universe", "infinity", "comet", "nova", "moon", "lunar", "orbit", "cosmos" } },
	{ id = "water", label = "Water", icon = "💧", bonus = "speed", words = { "shark", "whale", "dolphin", "kraken", "jelly", "manta", "ray", "orca", "seal", "otter", "octopus", "turtle", "fish", "puffer", "crab", "seahorse", "narwhal", "leviathan", "serpent", "walrus", "koi", "axolotl", "swan" } },
	{ id = "leaf", label = "Nature", icon = "🍃", bonus = "speed", words = { "leaf", "fungus", "mushroom", "spore", "shroom", "glow", "alien", "xeno", "chameleon", "frog", "gecko", "sloth", "tentacle" } },
	{ id = "candy", label = "Sweet", icon = "🍬", bonus = "luck", words = { "candy", "cotton", "caramel", "pink", "poodle", "rainbow" } },
	{ id = "gear", label = "Machine", icon = "⚙️", bonus = "cash", words = { "mecha", "robo", "clockwork", "wind-up", "tin", "drone", "titan", "cyber", "mech", "robot", "rocket" } },
	{ id = "neon", label = "Neon", icon = "💡", bonus = "speed", words = { "neon", "holo" } },
	{ id = "spirit", label = "Spirit", icon = "🕊️", bonus = "luck", words = { "spirit", "angel", "seraph", "halo", "ghost", "unicorn", "alicorn", "pegasus", "cloud", "sky", "dove", "kitsune", "qilin" } },
	{ id = "dragon", label = "Dragon", icon = "🐉", bonus = "cash", words = { "dragon", "hydra", "wyvern", "griffin", "manticore", "basilisk", "cerberus", "fenrir", "rex", "raptor", "roc" } },
}
C.TRAIT_BY_ID = {}
for _, tr in ipairs(C.TRAITS) do
	C.TRAIT_BY_ID[tr.id] = tr
end
-- zone theme when the name has no trait word (1 Sunny Meadow ... 20 Galaxy Throne)
C.ZONE_TRAIT = { "leaf", "leaf", "candy", "gear", "water", "shadow", "storm", "neon", "spirit", "gold",
	"star", "star", "star", "fire", "fire", "ice", "leaf", "shadow", "gear", "star" }
C.TRAIT_BONUS = { [4] = 0.03, [5] = 0.06, [6] = 0.08 } -- per Epic / Legendary / Special pet in the pen
C.TRAIT_CAP = 0.3
local traitCache = {}
function C.petTrait(pet)
	local name = C.petDef(pet).name
	local hit = traitCache[name]
	if hit then
		return hit
	end
	local low = " " .. string.lower(name) .. " "
	for _, tr in ipairs(C.TRAITS) do
		for _, w in ipairs(tr.words) do
			if string.find(low, w, 1, true) then
				hit = tr
				break
			end
		end
		if hit then
			break
		end
	end
	hit = hit or C.TRAIT_BY_ID[C.ZONE_TRAIT[pet.z] or "leaf"]
	traitCache[name] = hit
	return hit
end
-- total trait bonus of the pets in the pen: { cash = 0.09, luck = 0.03, speed = 0 }
function C.traitBonus(pets)
	local b = { cash = 0, luck = 0, speed = 0 }
	for _, pet in ipairs(pets or {}) do
		local v = C.TRAIT_BONUS[pet.i]
		if v then
			local k = C.petTrait(pet).bonus
			b[k] = math.min(C.TRAIT_CAP, b[k] + v)
		end
	end
	return b
end
function C.traitText(pet)
	local tr = C.petTrait(pet)
	local v = C.TRAIT_BONUS[pet.i]
	local what = { cash = "cash", luck = "egg luck", speed = "speed" }
	return tr.icon .. " " .. tr.label .. (v and ("  +" .. math.floor(v * 100 + 0.5) .. "% " .. what[tr.bonus]) or "")
end

-- upgrades: level starts at 0
C.MAX_LV = { train = 60, basket = 19, luck = 20, pen = 10 }
-- v232: PEN SPACE upgrade (UPGRADES menu, replaces TRAINING there): level n = C.PEN_MAX + n pets in your pen
C.PEN_COST = { 300, 4e3, 6e4, 9e5, 1.5e7, 2.5e8, 5e9, 1e11, 2.5e12, 7e13 }
-- 20 baskets you BUY one after another (no upgrades); basket k holds 2 + k pets and hangs on your back (Blender mesh Basket_k)
-- BasketLv 0 = basket 1 (free), BasketLv 19 = basket 20
C.BASKETS = {
	{ name = "Old Basket", price = 0 },
	{ name = "Straw Basket", price = 40 },
	{ name = "Picnic Basket", price = 110 },
	{ name = "Flower Basket", price = 410 },
	{ name = "Honey Pot", price = 2.5e3 },
	{ name = "Mushroom Basket", price = 1.8e4 },
	{ name = "Candy Bucket", price = 1.3e5 },
	{ name = "Sand Pail", price = 9.9e5 },
	{ name = "Cookie Jar", price = 7.6e6 },
	{ name = "Pumpkin Pack", price = 6.1e7 },
	{ name = "Ice Bucket", price = 4.8e8 },
	{ name = "Tech Pack", price = 3.6e9 },
	{ name = "Ocean Basket", price = 2.9e10 },
	{ name = "Lava Basket", price = 2.9e11 },
	{ name = "Thunder Pack", price = 3.9e12 },
	{ name = "Neon Basket", price = 7.8e13 },
	{ name = "Cloud Basket", price = 2.2e15 },
	{ name = "Crystal Basket", price = 7e16 },
	{ name = "Rainbow Basket", price = 2.5e18 },
	{ name = "Royal Basket", price = 9.7e19 },
}
function C.basketRim(k) -- top of basket k, seen from the torso centre (same numbers as blender\gen_baskets20.py)
	local t = (k - 1) / 19
	local rt, h, y0 = 1.0 + 0.3 * t, 1.9 + 0.4 * t, -1.25 - 0.2 * t
	return Vector3.new(0, y0 + h + 0.1, 0.55 + rt + 0.05)
end
-- v148: price of the next treadmill / luck level (index = level you have + 1); fitted by tools/tune_economy.py
C.TRAIN_COST = { 35, 48, 65, 89, 130, 230, 450, 1e3, 2.2e3, 4.5e3, 8.6e3, 1.8e4, 4e4, 9.2e4, 1.8e5, 3.1e5, 5.4e5, 1.1e6, 2.6e6, 5.7e6, 1.1e7, 1.9e7, 3.9e7, 9.4e7, 2.2e8, 4.4e8, 8.2e8, 1.6e9, 3.5e9, 7.2e9, 1.5e10, 3.2e10, 7.4e10, 1.7e11, 3.9e11, 1e12, 2.5e12, 5.7e12, 1.3e13, 3.3e13, 1.1e14, 4.6e14, 1.9e15, 6.7e15, 2e16, 6.1e16, 2e17, 7.2e17, 2.8e18, 1.2e19, 5.4e19, 2.5e20, 1.2e21, 5.5e21, 2.7e22, 1.4e23, 7.6e23, 4.3e24, 2.5e25, 1.6e26 }
C.LUCK_COST = { 67, 370, 2.4e3, 1.7e4, 1.3e5, 8.9e5, 6.5e6, 5.1e7, 4.2e8, 3.3e9, 2.7e10, 2.7e11, 3.7e12, 6.8e13, 1.7e15, 5e16, 1.8e18, 8.4e19, 5.3e21, 4.1e23 }
function C.cost(kind, lv)
	if kind == "train" and C.TRAIN_COST[lv + 1] then
		return C.TRAIN_COST[lv + 1]
	elseif kind == "pen" then
		return C.PEN_COST[lv + 1] or math.huge
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
function C.rebirthNeed(n) -- v244 (user): CASH price of rebirth number n + 1 (math.huge after the last one)
	if C.REBIRTH_PRICE then
		return C.REBIRTH_PRICE[n + 1] or math.huge
	end
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
-- v160 (user, like Throw Food For Animals): pets of the first zones are small, every next zone they get bigger
C.PET_ZONE_SCALE = { first = 0.6, step = 0.075, max = 2.1 } -- zone 1 = 0.6x, zone 10 = 1.28x, zone 20 = 2.03x
function C.zoneScale(z)
	local k = C.PET_ZONE_SCALE
	return math.min(k.first + (z - 1) * k.step, k.max)
end
C.MESH_SIZE = 10.0 -- studs: the longest side of a pet at normal size (v156: bigger again, was 7; v128 was the first raise)
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
	local def = C.petDef(pet)
	local tier = pet.t or 1
	local PA = C.petAnim()
	if PA then -- v129: the animated Codex pet (parts) when its part meshes are imported
		local ok, am = pcall(PA.build, pet, s, anchored, C.MESH_YAW, C.MESH_SIZE)
		if ok and am then
			am.Name = C.petName(pet)
			am:SetAttribute("Tier", tier)
			am:SetAttribute("Trait", C.petTrait(pet).id)
			am:SetAttribute("Rarity", pet.i)
			am:SetAttribute("Species", def.name) -- v138: the client's flowing Gold/Rainbow coat (PetCoatFlow) looks this up
			return am
		end
	end
	local pk = C.petKey(pet)
	local src = C.meshOf("Pet_" .. pk)
	-- v127: the Codex pets have their own Gold / Rainbow textures (Pet_z_i_G / Pet_z_i_R); old pets only get a tint
	local variant = (tier == 2 and C.meshOf("Pet_" .. pk .. "_G")) or (tier == 3 and C.meshOf("Pet_" .. pk .. "_R")) or nil
	if variant then
		src = variant
	end
	if src then
		local m = Instance.new("Model")
		m.Name = C.petName(pet)
		m:SetAttribute("Tier", tier)
		m:SetAttribute("Species", def.name)
		m:SetAttribute("Trait", C.petTrait(pet).id)
		m:SetAttribute("Rarity", pet.i)
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
	{ key = "cash2", id = 0, name = "2x Cash", desc = "All your pets earn double cash", robux = 149, icon = "coin", col = Color3.fromRGB(60, 200, 90) },
	{ key = "luck2", id = 0, name = "2x Luck", desc = "Rare pets hatch twice as often", robux = 179, icon = "clover", col = Color3.fromRGB(40, 170, 255) },
	{ key = "vip", id = 0, name = "VIP Basket", desc = "+5 basket space for every run", robux = 99, icon = "basket", col = Color3.fromRGB(255, 150, 30) },
	{ key = "fast", id = 0, name = "Fast Hatch", desc = "Egg opening plays 2x faster", robux = 49, icon = "egg", col = Color3.fromRGB(190, 90, 255) },
	-- v262 (user: like the ChatGPT shop): two more passes
	{ key = "slots3", id = 0, name = "+3 Pet Slots", desc = "Equip 3 more pets", robux = 199, icon = "paw", col = Color3.fromRGB(60, 120, 255) },
	{ key = "autohatch", id = 0, name = "Auto Hatch", desc = "Hatch eggs automatically", robux = 99, icon = "bolt", col = Color3.fromRGB(255, 70, 150) },
}
C.SLOTS_PASS = 3
C.VIP_BASKET = 5
-- v256 SHOP like Steal an Egg (user video): Robux products (developer products; id 0 = not created yet -> "coming soon").
-- ROYAL EGG: hatches a pet of your best zone with big luck, always Gold or Rainbow (kind "royal", violet egg)
C.ROYAL_LUCK = 10
C.ROYAL_PACKS = {
	{ key = "royal1", id = 0, n = 1, robux = 49 },
	{ key = "royal3", id = 0, n = 3, robux = 129 },
	{ key = "royal10", id = 0, n = 10, robux = 399 },
	{ key = "royal50", id = 0, n = 50, robux = 1499, old = 2450 },
}
-- SPEED packs: your speed x N (speed is on a log scale, so x10 is a big but fair jump)
C.SPEED_PACKS = {
	{ key = "speed2", id = 0, mult = 2, robux = 19 },
	{ key = "speed5", id = 0, mult = 5, robux = 49 },
	{ key = "speed10", id = 0, mult = 10, robux = 99 },
}
-- MONEY packs: minutes / hours of YOUR current income (stay useful at every stage), never less than min
C.CASH_PACKS = {
	{ key = "cash10m", id = 0, secs = 600, robux = 9, name = "Handful of Cash", min = 5000 },
	{ key = "cash30m", id = 0, secs = 1800, robux = 19, name = "Stack of Cash", min = 20000 },
	{ key = "cash1h", id = 0, secs = 3600, robux = 35, name = "Bag of Cash", min = 50000 },
	{ key = "cash4h", id = 0, secs = 4 * 3600, robux = 99, name = "Crate of Cash", min = 250000, tag = "POPULAR" },
	{ key = "cash12h", id = 0, secs = 12 * 3600, robux = 199, name = "Vault of Cash", min = 1000000, tag = "BEST VALUE" },
}
-- v262: Codex shop art (E:/rainingeggs/codex_shop/sheets shop_A/B/C.png). Put the uploaded image ids here.
C.SHOP_ART = { A = "", B = "", C = "" }
C.SHOP_RECTS = {
	cash_1 = { "B", 8, 0, 324, 341 },
	cash_2 = { "B", 349, 0, 324, 341 },
	cash_3 = { "B", 690, 0, 324, 341 },
	cash_4 = { "B", 8, 341, 324, 341 },
	cash_5 = { "B", 349, 341, 324, 341 },
	pass_auto = { "A", 690, 341, 324, 341 },
	pass_cash = { "A", 8, 0, 324, 341 },
	pass_fast = { "A", 8, 341, 324, 341 },
	pass_luck = { "A", 349, 0, 324, 341 },
	pass_slots = { "A", 349, 341, 324, 341 },
	pass_vip = { "A", 690, 0, 324, 341 },
	ribbon_cash = { "C", 512, 115, 512, 99 },
	ribbon_featured = { "C", 0, 5, 512, 99 },
	ribbon_gamepasses = { "C", 512, 5, 512, 99 },
	ribbon_speed = { "C", 0, 115, 512, 99 },
	royal_egg = { "B", 704, 341, 297, 341 },
	royal_title = { "C", 63, 220, 897, 256 },
	speed_10 = { "A", 690, 682, 324, 341 },
	speed_2 = { "A", 8, 682, 324, 341 },
	speed_5 = { "A", 349, 682, 324, 341 },
	title_shop = { "B", 0, 752, 1024, 201 },
}
C.PRODUCTS = {} -- every product by key (server: by id)
for _, list in ipairs({ C.ROYAL_PACKS, C.SPEED_PACKS, C.CASH_PACKS }) do
	for _, pk in ipairs(list) do
		C.PRODUCTS[pk.key] = pk
	end
end
C.ROYAL_PACKS[1].kind, C.ROYAL_PACKS[2].kind, C.ROYAL_PACKS[3].kind, C.ROYAL_PACKS[4].kind = "royal", "royal", "royal", "royal"
for _, pk in ipairs(C.SPEED_PACKS) do
	pk.kind = "speed"
end
for _, pk in ipairs(C.CASH_PACKS) do
	pk.kind = "cash"
end
-- chance of each rarity with a luck value (same rule as the server's roll)
function C.rarityChances(luck)
	local out, left = {}, 1
	for i = #C.RARITY, 2, -1 do
		local p = math.min(luck / C.RARITY[i].odds, 0.9)
		out[i] = left * p
		left = left * (1 - p)
	end
	out[1] = left
	return out
end

-- Daily rewards: claim once every 20 hours; miss 48 hours and the streak starts again at day 1.
C.DAILY_COOLDOWN = 20 * 3600
C.DAILY_RESET = 48 * 3600
C.DAILY = { -- cash = this many seconds of your income (at least min); day 7 also gives a free egg of your best zone
	{ secs = 60, min = 100 }, { secs = 120, min = 200 }, { secs = 180, min = 350 }, { secs = 300, min = 500 },
	{ secs = 420, min = 800 }, { secs = 600, min = 1200 }, { secs = 900, min = 2000, egg = true },
}

-- ============================================================ v150: WEEKLY EVENTS, FRIENDS, WELCOME GIFT
-- Every week (Monday 00:00 UTC) the next event of this list starts on every server; it runs 7 days.
C.EVENT_EPOCH = 1704067200 -- Monday 1 Jan 2024 00:00 UTC
C.EVENTS = {
	{ key = "luck", name = "LUCKY WEEK", desc = "x2 luck on every egg" },
	{ key = "gold", name = "GOLDEN WEEK", desc = "x3 golden eggs (Gold or Rainbow pets!)" },
	{ key = "cash", name = "CASH WEEK", desc = "x2 cash from all your pets" },
	{ key = "rainbow", name = "RAINBOW WEEK", desc = "x2 chance of RAINBOW pets" },
	{ key = "storm", name = "STORM WEEK", desc = "egg storms come twice as often" },
}
C.EVENT_GOLD_CHANCE = 3   -- golden eggs x this in GOLDEN WEEK
C.EVENT_RAINBOW = 2       -- RAINBOW WEEK: Rainbow chance x this
-- v152 (user): every egg rolls the coat of its pet: { normal, Gold, Rainbow } chances (golden egg = Gold guaranteed)
C.TIER_ODDS = {
	normal = { 0.7, 0.2, 0.1 },
	golden = { 0, 0.8, 0.2 },
	royal = { 0, 0.7, 0.3 }, -- v256: the Robux ROYAL EGG
	secret = { 0, 0.8, 0.2 }, -- v244: the SECRET (big) egg hatches as itself, same coats as a golden egg
}
function C.rollTier(kind, rainbowWeek)
	local o = C.TIER_ODDS[kind] or C.TIER_ODDS.normal
	local rb = math.min(o[3] * (rainbowWeek and C.EVENT_RAINBOW or 1), 0.9)
	local r = math.random()
	if r < rb then
		return 3
	elseif r < rb + o[2] then
		return 2
	end
	return 1
end
function C.eventAt(t) -- the event running at os.time() t, and when it ends
	local w = math.floor((t - C.EVENT_EPOCH) / 604800)
	return C.EVENTS[w % #C.EVENTS + 1], C.EVENT_EPOCH + (w + 1) * 604800
end
-- friends: every Roblox friend playing on the same server gives +10% cash (up to 4 friends = +40%)
C.FRIEND_BONUS = 0.1
C.FRIEND_MAX = 4
-- a new player gets a free egg 10 s after joining: Rare (or Epic) pet from Sunny Meadow
C.GIFT_DELAY = 10
C.GIFT_EPIC = 0.3
C.TEST_TUTORIAL = true  -- v182: Studio only - every Play starts the introduction (welcome egg + steps); the real game is not affected

return C
