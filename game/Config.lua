-- Raining Eggs: shared numbers + pet builder (ReplicatedStorage.Config)
local C = {}

C.ZONE_LEN = 140        -- zone i covers z = (i-1)*140 .. i*140
C.EGG_X = 150           -- eggs land between x = -150 .. 150
C.EGG_Y = 105           -- height the eggs start from
C.PEN_MAX = 10          -- equipped pets: they stand in your pen and earn cash (v119, was 12)
C.STORAGE_MAX = 50      -- your other pets wait in storage (PETS menu: tap to equip, EQUIP BEST); a full storage sells its weakest
C.SELL_MULT = 30        -- sell price = income per second * this
C.FUSE = 3              -- same pets needed for the next tier

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
C.REBIRTH_SPEED_SCALE = 1e6 -- v119 balance: rebirth speed = zone speed numbers x this (first rebirth after ~3 h of play, was ~5 min)

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
		{ "Chick", { 255, 222, 70 }, { 255, 150, 40 }, 0, "b" },
		{ "Bunny", W, { 255, 170, 200 }, 2, "q" },
		{ "Piglet", { 255, 170, 190 }, { 240, 120, 150 }, 1, "q" },
		{ "Fox", { 255, 140, 50 }, W, 1, "q" },
		{ "Sun Lion", { 255, 190, 60 }, { 255, 240, 120 }, 1, "q" },
	}),
	zone("Mushroom Grove", 500, 8, { 190, 130, 255 }, W, {
		{ "Snail", { 200, 170, 120 }, { 150, 100, 70 }, 0, "o" },
		{ "Frog", { 100, 200, 90 }, { 220, 250, 160 }, 0, "o" },
		{ "Shroom Mouse", { 232, 60, 70 }, W, 1, "q" },
		{ "Glow Moth", { 150, 110, 230 }, { 90, 240, 230 }, 2, "b" },
		{ "Spore Dragon", { 110, 80, 200 }, { 120, 255, 200 }, 1, "q" },
	}),
	zone("Candy Canyon", 5e3, 60, { 255, 150, 180 }, W, {
		{ "Gummy Bear", { 255, 90, 120 }, { 255, 170, 190 }, 1, "q" },
		{ "Mint Cat", { 150, 240, 210 }, W, 1, "q" },
		{ "Cookie Pup", { 200, 150, 90 }, { 110, 70, 40 }, 1, "q" },
		{ "Lolli Bunny", { 255, 130, 200 }, { 120, 200, 255 }, 2, "q" },
		{ "Candy Unicorn", W, { 255, 110, 210 }, 1, "q" },
	}),
	zone("Toy Town", 4e4, 450, { 240, 70, 70 }, W, {
		{ "Wind-up Mouse", { 150, 156, 170 }, { 240, 70, 70 }, 1, "q" },
		{ "Teddy", { 190, 130, 80 }, { 240, 210, 170 }, 1, "q" },
		{ "Rubber Duck", { 255, 214, 50 }, { 255, 140, 40 }, 0, "b" },
		{ "Robo Dog", { 70, 130, 250 }, { 255, 204, 40 }, 1, "q" },
		{ "Toy King", { 190, 100, 250 }, { 255, 204, 40 }, 2, "q" },
	}),
	zone("Crystal Coast", 2.5e5, 3500, { 80, 230, 255 }, W, {
		{ "Crab", { 240, 90, 70 }, { 255, 170, 150 }, 0, "o" },
		{ "Seal", { 170, 190, 210 }, W, 0, "o" },
		{ "Gem Turtle", { 80, 200, 150 }, { 80, 230, 255 }, 0, "o" },
		{ "Crystal Fox", { 190, 120, 255 }, { 80, 230, 255 }, 1, "q" },
		{ "Diamond Whale", { 90, 170, 255 }, { 220, 250, 255 }, 0, "o" },
	}),
	zone("Spooky Hollow", 2e6, 25000, { 255, 132, 30 }, { 24, 28, 52 }, {
		{ "Bat", { 70, 60, 90 }, { 150, 100, 220 }, 2, "b" },
		{ "Black Cat", { 40, 40, 52 }, { 140, 255, 150 }, 1, "q" },
		{ "Pumpkin Pup", { 255, 132, 30 }, { 60, 120, 50 }, 1, "q" },
		{ "Ghost Bunny", { 235, 240, 250 }, { 150, 100, 220 }, 2, "o" },
		{ "Reaper Wolf", { 50, 46, 70 }, { 140, 255, 150 }, 1, "q" },
	}),
	zone("Thunder Peaks", 1.5e7, 200000, { 255, 226, 60 }, { 24, 28, 52 }, {
		{ "Goat", { 220, 220, 225 }, { 120, 110, 100 }, 1, "q" },
		{ "Storm Owl", { 110, 120, 150 }, { 255, 226, 60 }, 1, "b" },
		{ "Spark Lynx", { 255, 226, 60 }, { 24, 28, 52 }, 1, "q" },
		{ "Thunder Ram", { 110, 150, 255 }, { 255, 236, 80 }, 1, "q" },
		{ "Lightning Dragon", { 70, 76, 100 }, { 255, 236, 80 }, 1, "q" },
	}),
	zone("Neon City", 1e8, 1.5e6, { 255, 60, 200 }, W, {
		{ "Pixel Cat", { 60, 230, 255 }, { 255, 60, 200 }, 1, "q" },
		{ "Laser Pup", { 255, 60, 200 }, { 60, 230, 255 }, 1, "q" },
		{ "Glitch Bunny", { 140, 255, 90 }, { 60, 56, 96 }, 2, "q" },
		{ "Cyber Fox", { 60, 56, 96 }, { 255, 230, 60 }, 1, "q" },
		{ "Hologram Tiger", { 255, 140, 40 }, { 60, 230, 255 }, 1, "q" },
	}),
	zone("Cloud Kingdom", 1e9, 1.2e7, W, { 255, 150, 200 }, {
		{ "Cloud Sheep", W, { 255, 200, 220 }, 1, "q" },
		{ "Sky Bird", { 150, 200, 255 }, { 255, 240, 130 }, 0, "b" },
		{ "Rainbow Cat", { 255, 150, 200 }, { 150, 200, 255 }, 1, "q" },
		{ "Star Bunny", { 255, 240, 130 }, W, 2, "q" },
		{ "Angel Pegasus", W, { 255, 222, 50 }, 1, "q" },
	}),
	zone("Golden Nest", 2.5e10, 1e8, { 255, 204, 40 }, W, {
		{ "Gold Chick", { 255, 204, 40 }, { 255, 240, 150 }, 0, "b" },
		{ "Gold Bunny", { 255, 214, 80 }, W, 2, "q" },
		{ "Royal Fox", { 255, 180, 40 }, { 160, 100, 250 }, 1, "q" },
		{ "Crown Lion", { 255, 204, 40 }, { 240, 66, 66 }, 1, "q" },
		{ "Egg God", { 255, 240, 150 }, { 160, 100, 250 }, 2, "o" },
	}),
}
-- v116: the 10 normal zones (gates, unlocks, index, altars). Zone 11 below is the secret one.
C.NZ = #C.ZONES

-- ============================================================ WORLD 2 (v119): COSMIC NEST + 2 zones, then COMING SOON
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
C.TOTAL = #C.ZONES -- 13: the last zone a player can open
C.COSMIC = {
	first = C.NZ + 1, last = C.TOTAL,
	y = 900,                       -- height of the world 2 ground (top)
	half = 176,                    -- half width of the zones (v120: as wide as world 1, same walls)
	eggX = 150,                    -- eggs land between x = -150 .. 150 (like world 1)
	eggHeight = 90,                -- eggs start this high above the ground
	fall = 3.6,                    -- seconds an egg falls (slow, low gravity)
	gravity = 70,                  -- workspace gravity in world 2 (normal 196.2), client side
	portal = { 0, 0, 1352, 15 },   -- Golden Portal in the Golden Nest: x, ground y, z, radius
	spawn = { 0, 906, 22 },        -- where the Golden Portal puts you (start of the Cosmic Nest)
	exit = { 0, 900, -28, 9 },     -- exit portal at the start of world 2: x, ground y, z, radius
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
-- v119 balance (tools/sim_economy.py, target between medium and slow): a normal player opens zone 2 after ~4 min,
-- zone 3 ~14 min, zone 4 ~40 min, zone 5 ~2 h, zone 6 ~3.5 h, zone 7 ~5.5 h, zone 8 ~8 h, zone 9 ~11 h, zone 10 ~15 h of play.
-- (v118 prices { 0, 1e3, 1e4, 7.5e4, 5e5, 4e6, 3e7, 2.5e8, 2e9, 1.5e10 } let players open all 10 zones in ~15 minutes.)
C.ZONE_PRICE = { 0, 8e3, 5.5e5, 3.5e7, 3e9, 3e10, 5e11, 6.5e12, 6.5e13, 6.5e14, 0, 7e16, 9e17 } -- 11-13 = world 2 (11 free: the Golden Portal)
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
	{ name = "Straw Basket", price = 100 },
	{ name = "Picnic Basket", price = 220 },
	{ name = "Flower Basket", price = 480 },
	{ name = "Honey Pot", price = 1100 },
	{ name = "Mushroom Basket", price = 2300 },
	{ name = "Candy Bucket", price = 5200 },
	{ name = "Sand Pail", price = 11000 },
	{ name = "Cookie Jar", price = 25000 },
	{ name = "Pumpkin Pack", price = 55000 },
	{ name = "Ice Bucket", price = 120000 },
	{ name = "Tech Pack", price = 270000 },
	{ name = "Ocean Basket", price = 580000 },
	{ name = "Lava Basket", price = 1300000 },
	{ name = "Thunder Pack", price = 2800000 },
	{ name = "Neon Basket", price = 6200000 },
	{ name = "Cloud Basket", price = 14000000 },
	{ name = "Crystal Basket", price = 30000000 },
	{ name = "Rainbow Basket", price = 66000000 },
	{ name = "Royal Basket", price = 150000000 },
}
function C.basketRim(k) -- top of basket k, seen from the torso centre (same numbers as blender\gen_baskets20.py)
	local t = (k - 1) / 19
	local rt, h, y0 = 1.0 + 0.3 * t, 1.9 + 0.4 * t, -1.25 - 0.2 * t
	return Vector3.new(0, y0 + h + 0.1, 0.55 + rt + 0.05)
end
function C.cost(kind, lv)
	if kind == "train" then
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

local SUF = { "", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp" }
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

function C.buildPet(pet, s, anchored)
	local def = C.ZONES[pet.z].pets[pet.i]
	local tier = pet.t or 1
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
