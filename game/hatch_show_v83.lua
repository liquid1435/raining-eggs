-- ------------------------------------------------------------ HATCH SHOW (in-world, v83)
-- Same show as the approved preview (blender/hatch_ref.py -> Desktop\RAINING EGGS NOU\hatch_ca_in_clip.mp4):
-- the camera flies to a hidden night-castle stage far away; the caught egg (its own zone design) floats in gold
-- claws over a stand; the scene climbs through the rarity colours up to the real one (every step: colour light,
-- name on the stand, level-up sound, a new glowing crack on the shell + the game's crack sound, the egg jolts);
-- Epic = light petals, Legendary = gold spike crown + turning square; the egg turns white -> POP (white flash,
-- star burst, rays, shards). Common..Epic: the pet is shown on the stand. Legendary (and the ??? step, F6 test):
-- the flash opens on a cathedral (rose window, candles, god rays) and the pet rises on the altar.
-- Tap / click during a show = the rest plays 3x faster. All client-side; every part a show creates lives in ONE
-- folder that is destroyed at the end AND on error; lighting / camera / HUD are always restored.
do
local STAGE = Vector3.new(0, 1200, 6000) -- castle stage (far from the map, nothing else is near)
local CATH = STAGE + Vector3.new(600, 0, 0) -- cathedral room
local EGG_RX, EGG_RY = 1.45, 2.05 -- egg half width / height on the stage
local STAND_TOP = 3.4
local EC = Vector3.new(0, STAND_TOP + 0.4 + EGG_RY, 0) -- egg centre (relative to STAGE)
local ALTAR_TOP = 2.4
local ECP = Vector3.new(0, ALTAR_TOP + 1.1 + 2.4, 4.5) -- burst centre on the altar (relative to CATH)
local RCOL = { -- step colours (bright versions of the rarity colours)
	Color3.fromRGB(240, 242, 255), Color3.fromRGB(80, 255, 120), Color3.fromRGB(40, 200, 255), Color3.fromRGB(200, 60, 255), Color3.fromRGB(255, 190, 20),
}
local RNAME = { "COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY", "???" }
local SECRET_ODDS = 600000000
-- seconds per rarity step, by the pet's rarity (rarer = slower, bigger show); [6] = the ??? step
local STEP_T = { 0.85, 0.9, 1.1, 1.35, 1.6 }
local SECRET_T = 3.2
local HOLD = { 1.5, 1.7, 2.1, 2.7, 4.2, 5.0 }
local GOLD = Color3.fromRGB(230, 170, 50)
local WARM = Color3.fromRGB(255, 205, 60)

local function clamp(x, a, b)
	return math.max(a or 0, math.min(b or 1, x))
end
local function eo(u) -- ease out cubic
	u = clamp(u)
	return 1 - (1 - u) ^ 3
end
local function backOut(u)
	u = clamp(u) - 1
	return u * u * (2.7 * u + 1.7) + 1
end
local function P(class, props, parent)
	props.Anchored = true
	props.CanCollide = false
	props.CanQuery = false
	props.CanTouch = false
	props.CastShadow = false
	if props.Material == nil then
		props.Material = Enum.Material.SmoothPlastic
	end
	return make(class, props, parent)
end
local function neonPart(parent, size)
	return P("Part", { Material = Enum.Material.Neon, Size = size or Vector3.new(1, 1, 1), Transparency = 1, CFrame = CFrame.new(STAGE - Vector3.new(0, 200, 0)) }, parent)
end
local function setN(p, col, alpha) -- colour + visibility of a neon part (alpha 0 = hidden)
	p.Color = col
	p.Transparency = 1 - clamp(alpha)
end
local function bar(p, a, b, w) -- stretch a part from a to b
	p.Size = Vector3.new(w, w, math.max((b - a).Magnitude + w * 0.6, 0.05))
	p.CFrame = CFrame.lookAt((a + b) / 2, b)
end
local function cylAt(parent, pos, diam, h, col, mat) -- upright cylinder
	return P("Part", { Shape = Enum.PartType.Cylinder, Size = Vector3.new(h, diam, diam), CFrame = CFrame.new(pos) * CFrame.Angles(0, 0, math.pi / 2), Color = col, Material = mat }, parent)
end
local function boxAt(parent, cf, size, col, mat)
	return P("Part", { Size = size, CFrame = cf, Color = col, Material = mat }, parent)
end
local function ellipsoid(parent, scale) -- neon ellipsoid (petals, the white shell)
	local p = neonPart(parent, Vector3.new(1, 1, 1))
	make("SpecialMesh", { MeshType = Enum.MeshType.Sphere, Scale = scale }, p)
	return p
end
-- a flat triangle spike in the screen plane = two mirrored wedges
local function makeSpike(parent)
	local a = P("WedgePart", { Material = Enum.Material.Neon, Transparency = 1, Size = Vector3.new(0.1, 1, 0.3) }, parent)
	local b = P("WedgePart", { Material = Enum.Material.Neon, Transparency = 1, Size = Vector3.new(0.1, 1, 0.3) }, parent)
	return { a, b }
end
local function placeSpike(sp, base, dir, len, w, col, alpha) -- base point, unit direction (in the XY plane)
	local p = Vector3.new(-dir.Y, dir.X, 0)
	for i, wd in ipairs(sp) do
		local side = (i == 1) and p or -p
		local x = dir:Cross(side)
		wd.Size = Vector3.new(0.08, math.max(len, 0.05), math.max(w / 2, 0.02))
		wd.CFrame = CFrame.fromMatrix(base + dir * len / 2 - side * w / 4, x, dir)
		setN(wd, col, alpha)
	end
end

-- ---------------------------------------------------------------- the stages (built once, kept hidden far away)
local S = nil
local function buildStages()
	if S then
		return S
	end
	S = {}
	local f = make("Folder", { Name = "HatchStages" }, workspace)
	S.folder = f
	local O = STAGE
	local stone, stoneD, floorC, clay = Color3.fromRGB(46, 50, 78), Color3.fromRGB(30, 32, 52), Color3.fromRGB(70, 74, 100), Color3.fromRGB(150, 82, 52)
	-- castle at night: back wall with crenels, towers, side walls, big moon behind a tower
	local rnd = Random.new(3)
	for k = -6, 6 do
		local h = 10 + rnd:NextNumber(-1, 2.5)
		boxAt(f, CFrame.new(O + Vector3.new(k * 5, h / 2, 34 + rnd:NextNumber(-1, 1))), Vector3.new(5.05, h, 3), (k % 2 == 0) and stoneD or stone)
		if k % 2 == 0 then
			boxAt(f, CFrame.new(O + Vector3.new(k * 5, h + 1, 34)), Vector3.new(2.5, 2, 3), stone)
		end
	end
	for _, x in ipairs({ -26, 26 }) do
		boxAt(f, CFrame.new(O + Vector3.new(x, 14, 26)), Vector3.new(9, 28, 9), stoneD)
		for _, c in ipairs({ -3, 0, 3 }) do
			boxAt(f, CFrame.new(O + Vector3.new(x + c, 29, 26)), Vector3.new(2, 2.4, 9), stoneD)
		end
		for k = -3, 3 do
			boxAt(f, CFrame.new(O + Vector3.new(x * 24 / 26, 9, k * 6 + 6)), Vector3.new(3, 18, 6.05), stoneD)
		end
	end
	P("Part", { Shape = Enum.PartType.Cylinder, Size = Vector3.new(0.5, 13, 13), CFrame = CFrame.new(O + Vector3.new(-17, 21, 62)) * CFrame.Angles(0, math.pi / 2, 0), Color = Color3.fromRGB(235, 235, 250), Material = Enum.Material.Neon }, f)
	boxAt(f, CFrame.new(O + Vector3.new(-19.5, 8.5, 55)), Vector3.new(4, 25, 4), stoneD)
	for _, c in ipairs({ -1.3, 1.3 }) do
		boxAt(f, CFrame.new(O + Vector3.new(-19.5 + c, 22, 55)), Vector3.new(1.1, 2, 4), stoneD)
	end
	boxAt(f, CFrame.new(O + Vector3.new(-7, 15, 32.4)), Vector3.new(0.7, 1.6, 0.2), Color3.fromRGB(150, 110, 255), Enum.Material.Neon)
	-- round stone floor, tiles, glowing rim
	cylAt(f, O + Vector3.new(0, -0.25, 0), 32, 0.5, floorC)
	for k = 0, 23 do
		local a = k * math.pi * 2 / 24
		boxAt(f, CFrame.new(O + Vector3.new(math.cos(a) * 13.5, 0.03, math.sin(a) * 13.5)) * CFrame.Angles(0, -a, 0), Vector3.new(3.3, 0.06, 4.5), (k % 2 == 0) and floorC or stone)
	end
	S.rim = {}
	for k = 0, 63 do
		local a0, a1 = k * math.pi * 2 / 64, (k + 1) * math.pi * 2 / 64
		local p = neonPart(f)
		bar(p, O + Vector3.new(math.cos(a0) * 15.8, 0.08, math.sin(a0) * 15.8), O + Vector3.new(math.cos(a1) * 15.8, 0.08, math.sin(a1) * 15.8), 0.25)
		table.insert(S.rim, p)
	end
	-- goblet braziers with flames
	S.flames = {}
	for k = 0, 9 do
		local a = math.rad(-90 + 18 + k * 36)
		local x, z = math.cos(a) * 9.5, math.sin(a) * 9.5 + 1
		local c = O + Vector3.new(x, 0, z)
		cylAt(f, c + Vector3.new(0, 3, 0), 2, 1.2, clay)
		cylAt(f, c + Vector3.new(0, 2.3, 0), 1.2, 0.4, clay)
		cylAt(f, c + Vector3.new(0, 3.62, 0), 2.24, 0.12, clay)
		for l = 0, 2 do
			local b = l * math.pi * 2 / 3 + a
			boxAt(f, CFrame.new(c + Vector3.new(math.cos(b) * 0.6, 1.3, math.sin(b) * 0.6)) * CFrame.Angles(math.sin(b) * 0.25, 0, -math.cos(b) * 0.25), Vector3.new(0.18, 2.7, 0.18), clay)
		end
		local fl = P("Part", { Shape = Enum.PartType.Ball, Material = Enum.Material.Neon, Color = Color3.fromRGB(255, 130, 40), Size = Vector3.new(1, 1, 1), CFrame = CFrame.new(c + Vector3.new(0, 4, 0)) }, f)
		local fl2 = P("Part", { Shape = Enum.PartType.Ball, Material = Enum.Material.Neon, Color = Color3.fromRGB(255, 210, 110), Size = Vector3.new(0.55, 0.55, 0.55), CFrame = CFrame.new(c + Vector3.new(0, 4.45, 0)) }, f)
		make("PointLight", { Range = 11, Brightness = 1.4, Color = Color3.fromRGB(255, 150, 70), Shadows = false }, fl)
		table.insert(S.flames, { fl, fl2, c, k })
	end
	-- central stand: base, white disc, glowing ring, gold claws
	cylAt(f, O + Vector3.new(0, 0.5, 0), 4.8, 1, floorC)
	cylAt(f, O + Vector3.new(0, 1.3, 0), 3.4, 0.6, Color3.fromRGB(225, 225, 235))
	S.standGlow = cylAt(f, O + Vector3.new(0, 1.66, 0), 3.5, 0.12, WHITE, Enum.Material.Neon)
	for k = 0, 3 do
		local a = k * math.pi / 2 + math.pi / 4
		local pos = O + Vector3.new(math.cos(a) * 1.25, STAND_TOP + 0.1, math.sin(a) * 1.25)
		boxAt(f, CFrame.new(pos) * CFrame.fromAxisAngle(Vector3.new(math.sin(a), 0, -math.cos(a)), -0.3), Vector3.new(0.2, 2.4, 0.2), GOLD, Enum.Material.Metal)
	end
	-- "RARITY / <NAME>" sign on the front of the stand
	local sign = P("Part", { Transparency = 1, Size = Vector3.new(6, 1.6, 0.05), CFrame = CFrame.new(O + Vector3.new(0, 1.4, -2.65)) }, f)
	local sg = make("SurfaceGui", { Face = Enum.NormalId.Front, PixelsPerStud = 60, LightInfluence = 0, Brightness = 2, SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud }, sign)
	S.signSmall = make("TextLabel", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 0.3), Font = Enum.Font.Garamond, TextScaled = true, Text = "RARITY", TextColor3 = Color3.fromRGB(220, 220, 230), Visible = false }, sg)
	S.signBig = make("TextLabel", { BackgroundTransparency = 1, Position = UDim2.fromScale(0, 0.32), Size = UDim2.fromScale(1, 0.68), Font = Enum.Font.Garamond, TextScaled = true, Text = "", TextColor3 = WHITE }, sg)
	make("UIStroke", { Thickness = 2, Color = Color3.new(0, 0, 0), Transparency = 0.3 }, S.signBig)
	S.signScale = make("UIScale", {}, S.signBig)
	-- lights: one at the egg, one that floods the wall behind with the rarity colour
	S.eggLight = make("PointLight", { Range = 18, Brightness = 0, Shadows = false }, P("Part", { Transparency = 1, Size = Vector3.new(0.2, 0.2, 0.2), CFrame = CFrame.new(O + EC + Vector3.new(0, 0, -2.5)) }, f))
	S.backLight = make("PointLight", { Range = 45, Brightness = 0, Shadows = false }, P("Part", { Transparency = 1, Size = Vector3.new(0.2, 0.2, 0.2), CFrame = CFrame.new(O + Vector3.new(0, 9, 22)) }, f))
	-- floating sparkles (built-in particle texture)
	local dustPart = P("Part", { Transparency = 1, Size = Vector3.new(34, 1, 18), CFrame = CFrame.new(O + Vector3.new(0, 1, 2)) }, f)
	S.dust = make("ParticleEmitter", {
		Texture = "rbxasset://textures/particles/sparkles_main.dds", Rate = 0, Lifetime = NumberRange.new(3, 5), Speed = NumberRange.new(1, 3),
		SpreadAngle = Vector2.new(25, 25), EmissionDirection = Enum.NormalId.Top, LightEmission = 1, LightInfluence = 0,
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.2, 0.35), NumberSequenceKeypoint.new(1, 0) }),
		Transparency = NumberSequence.new(0.1), Color = ColorSequence.new(WHITE),
	}, dustPart)

	-- ============ cathedral (the Legendary reveal room)
	local Q = CATH
	local cstone, cstone2, cdark = Color3.fromRGB(168, 150, 126), Color3.fromRGB(128, 112, 94), Color3.fromRGB(70, 58, 48)
	boxAt(f, CFrame.new(Q + Vector3.new(0, -0.5, -4)), Vector3.new(46, 1, 60), cstone2)
	for i = -5, 5 do
		for j = -8, 4 do
			if (i + j) % 2 == 0 then
				boxAt(f, CFrame.new(Q + Vector3.new(i * 4, 0.02, j * 4)), Vector3.new(4, 0.04, 4), cstone)
			end
		end
	end
	boxAt(f, CFrame.new(Q + Vector3.new(0, 0.06, -12)), Vector3.new(5, 0.06, 36), Color3.fromRGB(160, 22, 28), Enum.Material.Fabric)
	for _, x in ipairs({ -2.6, 2.6 }) do
		boxAt(f, CFrame.new(Q + Vector3.new(x, 0.07, -12)), Vector3.new(0.25, 0.06, 36), GOLD, Enum.Material.Metal)
	end
	for k, s in ipairs({ { 14, 4 }, { 11, 4.5 }, { 8, 5 } }) do
		boxAt(f, CFrame.new(Q + Vector3.new(0, 0.4 + (k - 1) * 0.8, s[2])), Vector3.new(s[1], 0.8, 7 - k), cstone)
	end
	cylAt(f, Q + Vector3.new(0, ALTAR_TOP + 0.5, 4.5), 4.4, 1, Color3.fromRGB(240, 232, 210))
	cylAt(f, Q + Vector3.new(0, ALTAR_TOP + 1.02, 4.5), 4.6, 0.12, GOLD, Enum.Material.Metal)
	boxAt(f, CFrame.new(Q + Vector3.new(0, 15, 17)), Vector3.new(46, 32, 2), cstone2)
	for _, x in ipairs({ -9.5, 9.5 }) do
		for _, z in ipairs({ -20, -12, -4, 4 }) do
			cylAt(f, Q + Vector3.new(x, 9, z), 2.2, 18, cstone)
			boxAt(f, CFrame.new(Q + Vector3.new(x, 18.4, z)), Vector3.new(3, 0.8, 3), cstone2)
			boxAt(f, CFrame.new(Q + Vector3.new(x, 0.4, z)), Vector3.new(2.8, 0.8, 2.8), cstone2)
		end
	end
	for _, x in ipairs({ -15, 15 }) do
		boxAt(f, CFrame.new(Q + Vector3.new(x, 13, -6)), Vector3.new(2, 26, 50), cdark)
	end
	for _, x in ipairs({ -9.1, 9.1 }) do -- red banners with gold trim
		boxAt(f, CFrame.new(Q + Vector3.new(x, 9, 15.9)), Vector3.new(3, 9, 0.2), Color3.fromRGB(140, 18, 26), Enum.Material.Fabric)
		boxAt(f, CFrame.new(Q + Vector3.new(x, 13.6, 15.8)), Vector3.new(3.3, 0.3, 0.25), GOLD, Enum.Material.Metal)
		boxAt(f, CFrame.new(Q + Vector3.new(x, 9, 15.75)), Vector3.new(0.4, 7.6, 0.22), GOLD, Enum.Material.Metal)
	end
	-- rose window: three rings of coloured glass pieces + core + stone frame
	local RC = Q + Vector3.new(0, 17.2, 15.85)
	local GLASS = { Color3.fromRGB(220, 40, 40), Color3.fromRGB(40, 90, 230), Color3.fromRGB(250, 200, 40), Color3.fromRGB(40, 170, 90), Color3.fromRGB(150, 60, 210) }
	P("Part", { Shape = Enum.PartType.Cylinder, Size = Vector3.new(0.1, 2.4, 2.4), CFrame = CFrame.new(RC - Vector3.new(0, 0, 0.05)) * CFrame.Angles(0, math.pi / 2, 0), Color = Color3.fromRGB(255, 230, 150), Material = Enum.Material.Neon }, f)
	for _, ring in ipairs({ { 1.35, 3.2, 10, { 1, 2 } }, { 3.35, 5.0, 20, { 3, 1, 2, 3, 5 } }, { 5.15, 6.0, 30, { 2, 3, 1 } } }) do
		local r0, r1, n, pal = ring[1], ring[2], ring[3], ring[4]
		for k = 0, n - 1 do
			local a = (k + 0.5) * math.pi * 2 / n
			local rm = (r0 + r1) / 2
			local w = 2 * rm * math.sin(math.pi / n) * 0.9
			boxAt(f, CFrame.new(RC + Vector3.new(math.cos(a) * rm, math.sin(a) * rm, -0.05)) * CFrame.Angles(0, 0, a), Vector3.new(r1 - r0, w, 0.1), GLASS[pal[k % #pal + 1]], Enum.Material.Neon)
		end
	end
	P("Part", { Shape = Enum.PartType.Cylinder, Size = Vector3.new(0.1, 13.4, 13.4), CFrame = CFrame.new(RC + Vector3.new(0, 0, 0.02)) * CFrame.Angles(0, math.pi / 2, 0), Color = cdark }, f)
	-- god rays from the window down to the altar
	S.godrays = {}
	for k = 0, 6 do
		local top = RC + Vector3.new((k - 3) * 1.2, 0, -0.3)
		local bottom = Q + Vector3.new((k - 3) * 0.5, 2, -6)
		local p = P("Part", { Material = Enum.Material.Neon, Color = Color3.fromRGB(255, 225, 160), Transparency = 0.9 }, f)
		bar(p, top, bottom, 1.2 + 0.3 * (k % 2))
		table.insert(S.godrays, p)
	end
	-- candles (stands along the carpet + on the altar)
	S.candles = {}
	local cpos = {}
	for _, z in ipairs({ -22, -16, -10, -4 }) do
		table.insert(cpos, { -5.5, z })
		table.insert(cpos, { 5.5, z })
	end
	for _, c in ipairs({ { -4.5, 2.5 }, { 4.5, 2.5 }, { -6, 6 }, { 6, 6 }, { -3.4, 7 }, { 3.4, 7 } }) do
		table.insert(cpos, c)
	end
	for k, c in ipairs(cpos) do
		local x, z = c[1], c[2]
		local y0 = 2.0
		if z <= 0 then
			cylAt(f, Q + Vector3.new(x, 1.2, z), 0.24, 2.4, GOLD, Enum.Material.Metal)
			cylAt(f, Q + Vector3.new(x, 2.4, z), 1, 0.1, GOLD, Enum.Material.Metal)
			y0 = 2.45
		end
		local h = 0.9 + (k % 3) * 0.35
		cylAt(f, Q + Vector3.new(x, y0 + h / 2, z), 0.44, h, Color3.fromRGB(240, 232, 210))
		local fl = P("Part", { Shape = Enum.PartType.Ball, Material = Enum.Material.Neon, Color = Color3.fromRGB(255, 170, 70), Size = Vector3.new(0.35, 0.35, 0.35), CFrame = CFrame.new(Q + Vector3.new(x, y0 + h + 0.25, z)) }, f)
		table.insert(S.candles, { fl, Q + Vector3.new(x, y0 + h + 0.25, z), k })
		if k % 4 == 0 then
			make("PointLight", { Range = 12, Brightness = 1.2, Color = Color3.fromRGB(255, 170, 90), Shadows = false }, fl)
		end
	end
	S.altarLight = make("PointLight", { Range = 22, Brightness = 2, Color = Color3.fromRGB(255, 205, 150), Shadows = false }, P("Part", { Transparency = 1, Size = Vector3.new(0.2, 0.2, 0.2), CFrame = CFrame.new(Q + Vector3.new(0, 9, 1)) }, f))
	make("PointLight", { Range = 30, Brightness = 2.2, Color = Color3.fromRGB(255, 220, 170), Shadows = false }, P("Part", { Transparency = 1, Size = Vector3.new(0.2, 0.2, 0.2), CFrame = CFrame.new(Q + Vector3.new(0, 16, 12)) }, f))
	local dust2 = P("Part", { Transparency = 1, Size = Vector3.new(24, 1, 26), CFrame = CFrame.new(Q + Vector3.new(0, 1, -6)) }, f)
	S.dust2 = S.dust:Clone()
	S.dust2.Color = ColorSequence.new(Color3.fromRGB(255, 214, 140))
	S.dust2.Parent = dust2
	return S
end

-- ---------------------------------------------------------------- screen layer (flash, counter, name)
local showGui = make("ScreenGui", { Name = "HatchShow", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 60, Enabled = false }, plr:WaitForChild("PlayerGui"))
local flash = make("Frame", { Size = UDim2.fromScale(1, 1), BackgroundColor3 = WHITE, BackgroundTransparency = 1, BorderSizePixel = 0, ZIndex = 5 }, showGui)
local function serif(y, h, col)
	local t = make("TextLabel", {
		BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, y), Size = UDim2.fromScale(0.9, h),
		Font = Enum.Font.Garamond, TextScaled = true, TextColor3 = col or WHITE, Text = "", ZIndex = 6, TextTransparency = 1,
	}, showGui)
	make("UIStroke", { Thickness = 3, Color = Color3.fromRGB(30, 16, 0), Transparency = 1 }, t)
	return t, make("UIScale", {}, t)
end
local counter, counterScale = serif(0.1, 0.09)
local petNameL, nameScale = serif(0.8, 0.1, Color3.fromRGB(255, 226, 140))
local oddsL = serif(0.89, 0.055, Color3.fromRGB(255, 244, 210))
make("UIGradient", { Rotation = 90, Color = ColorSequence.new(Color3.fromRGB(255, 250, 220), Color3.fromRGB(235, 165, 40)) }, petNameL)
local skipHint = make("TextLabel", {
	BackgroundTransparency = 1, AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -16, 1, -12), Size = UDim2.fromOffset(220, 26),
	Font = Enum.Font.GothamBold, TextScaled = true, TextColor3 = WHITE, TextTransparency = 0.5, Text = "TAP TO SPEED UP", ZIndex = 6, TextXAlignment = Enum.TextXAlignment.Right,
}, showGui)
local function setText(t, txt, alpha)
	t.Text = txt
	t.TextTransparency = 1 - clamp(alpha)
	local st = t:FindFirstChildOfClass("UIStroke")
	if st then
		st.Transparency = 1 - clamp(alpha) * 0.8
	end
end

-- new effect sounds (audio/hatchfx, one sheet). While the sheet is not uploaded (id 0) the old sounds are used.
local HFX_ID = "rbxassetid://0"
local HFX = { -- start, length in the sheet (written by audio/make_hatch_sheet.py)
	step_1 = { 0, 0.8 }, step_2 = { 1.1, 0.9 }, step_3 = { 2.3, 1.0 }, step_4 = { 3.6, 1.2 }, step_5 = { 5.1, 1.5 },
	shing = { 6.9, 0.7 }, riser = { 7.9, 1.4 }, burst = { 9.6, 2.2 }, reveal = { 12.1, 1.6 },
}
local HFX_OLD = { step_1 = "egg_wobble", step_2 = "reveal_common", step_3 = "reveal_rare", step_4 = "reveal_rare", step_5 = "reveal_legend", shing = "egg_pop", riser = nil, burst = "egg_pop", reveal = "fanfare" }
local hfxBase = make("Sound", { Name = "HatchFX_Sheet", SoundId = HFX_ID, Volume = 0 }, SoundService)
if HFX_ID ~= "rbxassetid://0" then
	task.spawn(function()
		pcall(function()
			game:GetService("ContentProvider"):PreloadAsync({ hfxBase })
		end)
	end)
end
local function hfx(name, volume, pitch)
	local r = HFX[name]
	if HFX_ID == "rbxassetid://0" or not hfxBase.IsLoaded or not r then
		local old = HFX_OLD[name]
		if old then
			sfx(old, volume, pitch)
		end
		return
	end
	local s = hfxBase:Clone()
	s.Volume = volume or 0.7
	s.PlaybackSpeed = pitch or 1
	s.Parent = SoundService
	s.TimePosition = r[1]
	s:Play()
	task.delay(r[2] / (pitch or 1) + 0.05, function()
		s:Destroy()
	end)
end

-- ---------------------------------------------------------------- world state saved during a show
local saved = nil
local hatchBloom = make("BloomEffect", { Name = "HatchBloom", Enabled = false, Intensity = 0.9, Size = 30, Threshold = 0.95 }, Lighting)
local function enterShow()
	local cam = workspace.CurrentCamera
	saved = {
		camType = cam.CameraType, camCF = cam.CFrame, fov = cam.FieldOfView,
		light = { ClockTime = Lighting.ClockTime, Brightness = Lighting.Brightness, Ambient = Lighting.Ambient, OutdoorAmbient = Lighting.OutdoorAmbient,
			FogColor = Lighting.FogColor, FogStart = Lighting.FogStart, FogEnd = Lighting.FogEnd, ExposureCompensation = Lighting.ExposureCompensation },
		guis = {},
	}
	local atm = Lighting:FindFirstChildOfClass("Atmosphere")
	if atm then
		saved.atm, saved.atmDensity = atm, atm.Density
		atm.Density = 0
	end
	for _, g in ipairs(plr.PlayerGui:GetChildren()) do
		if g:IsA("ScreenGui") and g ~= showGui and g.Enabled then
			g.Enabled = false
			table.insert(saved.guis, g)
		end
	end
	cam.CameraType = Enum.CameraType.Scriptable
	Lighting.ClockTime = 0
	Lighting.Brightness = 0.6
	Lighting.Ambient = Color3.fromRGB(30, 30, 46)
	Lighting.OutdoorAmbient = Color3.fromRGB(26, 26, 40)
	Lighting.FogColor = Color3.fromRGB(4, 5, 14)
	Lighting.FogStart = 140
	Lighting.FogEnd = 400
	Lighting.ExposureCompensation = 0
	hatchBloom.Enabled = true
	showGui.Enabled = true
end
local function leaveShow()
	if not saved then
		return
	end
	local cam = workspace.CurrentCamera
	cam.CameraType = saved.camType == Enum.CameraType.Scriptable and Enum.CameraType.Custom or saved.camType
	cam.FieldOfView = saved.fov
	for k, v in pairs(saved.light) do
		Lighting[k] = v
	end
	if saved.atm then
		saved.atm.Density = saved.atmDensity
	end
	for _, g in ipairs(saved.guis) do
		if g.Parent then
			g.Enabled = true
		end
	end
	hatchBloom.Enabled = false
	showGui.Enabled = false
	flash.BackgroundTransparency = 1
	setText(counter, "", 0)
	setText(petNameL, "", 0)
	setText(oddsL, "", 0)
	if S then
		S.dust.Rate = 0
		S.dust2.Rate = 0
		S.dust:Clear()
		S.dust2:Clear()
		S.signBig.Text = ""
		S.signSmall.Visible = false
	end
	saved = nil
end

-- ---------------------------------------------------------------- one show
local running = nil -- the show being played (render loop reads it)
local speedUp = 1

local function crackNetwork(events, rx)
	local rnd = Random.new(11)
	local segs, ends = {}, {}
	local function surf(u, v)
		local c = math.sqrt(math.max(1 - v * v, 0))
		return Vector3.new(math.sin(u) * rx * c, v * EGG_RY, -math.cos(u) * rx * c)
	end
	for i, ev in ipairs(events) do
		local size = ev[2]
		local u, v
		if #ends > 0 and rnd:NextNumber() < 0.5 then
			local e = ends[rnd:NextInteger(1, #ends)]
			u, v = e[1], e[2]
		else
			u, v = rnd:NextNumber(-1, 1), rnd:NextNumber(-0.7, 0.75)
		end
		for _ = 1, (size >= 3) and 2 or 1 do
			local uu, vv = u, v
			local d = (rnd:NextNumber() < 0.5) and -1 or 1
			for k = 0, 1 + size do
				local u2 = clamp(uu + d * rnd:NextNumber(0.12, 0.3), -1.35, 1.35)
				local v2 = clamp(vv + rnd:NextNumber(-0.28, 0.28), -0.92, 0.92)
				table.insert(segs, { ev = i, p = surf(uu, vv), q = surf(u2, v2), order = k })
				uu, vv = u2, v2
				if rnd:NextNumber() < 0.3 then
					d = -d
				end
			end
			table.insert(ends, { uu, vv })
		end
	end
	return segs
end

local function runShow(job)
	local pet, kind = job.pet, job.kind
	local R = job.secret and 6 or pet.i -- how far the climb goes (6 = the ??? step)
	local k = (job.fast and 0.6 or 1) * ((UI.hasPass and UI.hasPass("fast")) and 0.5 or 1)
	speedUp = 1
	local st = buildStages()
	-- timeline (seconds of show time; real time = show time * k / speedUp)
	local step = STEP_T[math.min(R, 5)]
	local starts, t = {}, 0.9
	for L = 1, R do
		starts[L] = t
		t = t + ((L == 6) and SECRET_T or step)
	end
	local tEnd = t
	local CHARGE = 0.45 + (R >= 4 and 0.2 or 0)
	local WHITE_T = (R >= 4) and 0.6 or 0.35
	local T_POP = tEnd + CHARGE + WHITE_T
	local cath = R >= 5
	local T_END = T_POP + (cath and 0.3 or 0) + HOLD[R] + 0.35
	-- crack events: (time, size); big one at every step, small ones between, fast ones in the charge
	local events = {}
	for L = 1, R do
		local d = (L == 6) and SECRET_T or step
		table.insert(events, { starts[L] + 0.02, math.min(L, 5) })
		if L < 6 then
			if R >= 3 then
				table.insert(events, { starts[L] + d * 0.55, 1 })
			end
			if L >= 3 then
				table.insert(events, { starts[L] + d * 0.82, 2 })
			end
		else
			for i, fr in ipairs({ 0.3, 0.5, 0.68, 0.82, 0.93 }) do
				table.insert(events, { starts[L] + d * fr, 1 + math.min(i, 4) })
			end
		end
	end
	table.insert(events, { tEnd, 3 })
	table.insert(events, { tEnd + CHARGE * 0.5, 4 })
	table.insert(events, { tEnd + CHARGE + WHITE_T * 0.5, math.min(R + 1, 5) })
	table.sort(events, function(a, b)
		return a[1] < b[1]
	end)

	local run = make("Folder", { Name = "HatchRun" }, workspace)
	local sh = { run = run, events = events, t = 0, R = R, starts = starts, tEnd = tEnd, T_POP = T_POP, T_END = T_END, CHARGE = CHARGE, WHITE_T = WHITE_T, cath = cath, pet = pet, job = job, fired = {}, k = k }
	-- the egg (this zone's egg design; a dark ball when the models are missing)
	local egg, unit, rot = eggMesh(pet.z, kind)
	if egg then
		egg.Parent = run
		local sc = (EGG_RY * 2) / EGG_H
		unit = unit * sc
		egg.Size = unit
	else
		egg = P("Part", { Shape = Enum.PartType.Ball, Size = Vector3.new(EGG_RX * 2, EGG_RX * 2, EGG_RX * 2), Color = rgb(C.ZONES[pet.z].eggCol) }, run)
		unit, rot = egg.Size, CFrame.new()
	end
	sh.egg, sh.unit, sh.rot = egg, unit, rot
	sh.rx = math.clamp(math.abs(rot:VectorToWorldSpace(unit).X) / 2, 0.8, 2.2)
	sh.shell = ellipsoid(run, Vector3.new(sh.rx * 2.06, EGG_RY * 2.06, sh.rx * 2.06)) -- white-hot shell before the pop
	sh.orbs = {}
	for i = 1, 4 do
		sh.orbs[i] = P("Part", { Shape = Enum.PartType.Ball, Material = Enum.Material.Neon, Transparency = 1, Size = Vector3.new(1, 1, 1), CFrame = CFrame.new(STAGE - Vector3.new(0, 200, 0)) }, run)
	end
	sh.segs = crackNetwork(events, sh.rx)
	sh.crG, sh.crC = {}, {}
	for i = 1, #sh.segs do
		sh.crG[i] = neonPart(run)
		sh.crC[i] = neonPart(run)
	end
	sh.petals, sh.petalC = {}, {}
	for i = 1, 10 do
		sh.petals[i] = ellipsoid(run, Vector3.new(0.6, 1.5, 0.08))
		sh.petalC[i] = ellipsoid(run, Vector3.new(0.28, 1.1, 0.08))
	end
	sh.spikes = {}
	for i = 1, 18 do
		sh.spikes[i] = makeSpike(run)
	end
	sh.square = { neonPart(run), neonPart(run), neonPart(run), neonPart(run) }
	sh.ring = {} -- expanding dashed circle (screen plane)
	for i = 1, 40 do
		sh.ring[i] = neonPart(run)
	end
	sh.ring2 = {}
	for i = 1, 40 do
		sh.ring2[i] = neonPart(run)
	end
	sh.star, sh.rays = {}, {}
	for i = 1, 12 do
		sh.star[i] = neonPart(run)
	end
	for i = 1, 20 do
		sh.rays[i] = neonPart(run)
	end
	sh.shards = {}
	for i = 1, 26 do
		local p = neonPart(run, Vector3.new(0.55, 0.55, 0.06))
		sh.shards[i] = p
	end
	sh.sunb = {}
	for i = 1, 28 do
		sh.sunb[i] = makeSpike(run)
	end
	-- the pet (hidden until the pop)
	local model = C.buildPet(pet, 1, true)
	model.Parent = run
	local bcf, bsize = model:GetBoundingBox()
	local piv = model:GetPivot().Position
	sh.fit = (cath and 6.2 or 5.0) / math.max(bsize.X, bsize.Y, bsize.Z, 0.5)
	sh.off = Vector3.new(piv.X - bcf.Position.X, piv.Y - (bcf.Position.Y - bsize.Y / 2), piv.Z - bcf.Position.Z)
	model:ScaleTo(0.01)
	model:PivotTo(CFrame.new(STAGE - Vector3.new(0, 300, 0)))
	sh.model, sh.lastK = model, 0.01

	enterShow()
	running = sh
	-- wait for the render loop to play it through (it sets sh.done); a hard time limit protects against hangs
	local limit = os.clock() + T_END * k + 20
	while not sh.done and os.clock() < limit do
		task.wait()
	end
	running = nil
	run:Destroy()
	leaveShow()
end

-- ---------------------------------------------------------------- per-frame drawing of the show
local function ringAt(list, center, r, rot, col, alpha, dash)
	local n = #list
	for i, p in ipairs(list) do
		if dash and i % 2 == 0 then
			p.Transparency = 1
		else
			local a0 = rot + (i - 1) * math.pi * 2 / n
			local a1 = rot + i * math.pi * 2 / n
			bar(p, center + Vector3.new(math.cos(a0) * r, math.sin(a0) * r, 0), center + Vector3.new(math.cos(a1) * r, math.sin(a1) * r, 0), 0.09)
			setN(p, col, alpha)
		end
	end
end
local function hideList(list)
	for _, p in ipairs(list) do
		if type(p) == "table" then
			for _, q in ipairs(p) do
				q.Transparency = 1
			end
		else
			p.Transparency = 1
		end
	end
end

local function drawShow(sh, dt)
	local prev = sh.t
	sh.t = sh.t + dt * speedUp / sh.k
	local t = sh.t
	local R = sh.R
	local now = os.clock()
	local cam = workspace.CurrentCamera
	local O = STAGE
	-- current step
	local L = 0
	for i = 1, R do
		if t >= sh.starts[i] then
			L = i
		end
	end
	local age = L > 0 and (t - sh.starts[L]) or 0
	local popped = t >= sh.T_POP
	local pa = t - sh.T_POP
	local whiten = popped and 1 or clamp((t - sh.tEnd - sh.CHARGE) / sh.WHITE_T)
	local build = clamp((t - 0.9) / (sh.tEnd - 0.9 + sh.CHARGE))
	local hit = (L > 0 and not popped) and math.exp(-age * 6) or 0
	local col
	if popped or whiten > 0.5 then
		col = WHITE
	elseif L == 0 then
		col = Color3.fromRGB(200, 210, 255)
	elseif L == 6 then
		col = Color3.fromHSV((t * 0.45) % 1, 0.55, 1)
	else
		col = RCOL[L]
	end
	-- sounds + crack events crossing this frame
	for i, ev in ipairs(sh.events) do
		if ev[1] > prev and ev[1] <= t and not popped then
			sfx("egg_crack", 0.45 + 0.12 * ev[2], 1.18 - 0.08 * ev[2] + (math.random() - 0.5) * 0.08)
		end
	end
	for i = 1, R do
		if sh.starts[i] > prev and sh.starts[i] <= t then
			hfx("step_" .. math.min(i, 5), (i == 6) and 0.9 or 0.75, (i == 6) and 0.78 or 1)
			if i == 4 or i == 5 or i == 6 then
				task.delay(0.05, hfx, "shing", 0.6, (i == 4) and 1 or (i == 5) and 0.9 or 0.75)
			end
			flash.BackgroundColor3 = (i == 6) and WHITE or RCOL[i]
		end
	end
	if sh.T_POP - 1.4 > prev and sh.T_POP - 1.4 <= t then
		hfx("riser", 0.7)
	end
	if sh.T_POP > prev and sh.T_POP <= t then
		sfx("egg_crack", 1, 0.75)
		hfx("burst", 1)
		task.delay(0.4 * sh.k, hfx, "reveal", 0.8)
		task.delay(0.15 * sh.k, petSound, C.ZONES[sh.pet.z].pets[sh.pet.i].kind, nil, 0.6)
		if UI.confetti and R >= 4 then
			task.delay(0.35 * sh.k, UI.confetti, R >= 5 and 90 or 45, R >= 5 and WARM or RCOL[4])
		end
	end
	local kick = 0
	local jolt = 0
	for i, ev in ipairs(sh.events) do
		local d = t - ev[1]
		if d >= 0 and d < 0.5 and not popped then
			kick = kick + math.min(ev[2], 4) * math.exp(-d * 16)
			jolt = jolt + math.exp(-d * 18) * ((i % 2 == 0) and 1 or -1) * math.min(ev[2], 4)
		end
	end

	local inCath = popped and sh.cath and pa >= 0.3
	-- ---------------- camera
	local rnd = Random.new(math.floor(t * 300))
	if not inCath then
		local pos = Vector3.new(0, 7, -32):Lerp(Vector3.new(0, 6.2, -21), eo(t / 1.6))
		if L >= 1 then
			pos = pos:Lerp(Vector3.new(0, 6.0, -15.5), eo(build) * 0.8)
		end
		if popped then
			pos = Vector3.new(0, 6.0, -18):Lerp(Vector3.new(0, 5.6, -15.5), eo(pa / 4))
		end
		local shake = (0.03 + 0.12 * build ^ 2) * (popped and 0.3 or 1) + (popped and 0.6 * math.exp(-pa * 6) or 0) + 0.06 * kick
		pos = pos + Vector3.new(rnd:NextNumber(-1, 1), rnd:NextNumber(-1, 1), 0) * shake * 0.5
		cam.CFrame = CFrame.lookAt(O + pos, O + Vector3.new(0, EC.Y - 1.1, 0))
		cam.FieldOfView = 34 - 0.3 * kick
	else
		local q = pa - 0.3
		local cp = Vector3.new(0, 4.2, -21):Lerp(Vector3.new(0, 5.6, -13.5), eo(q / 4.5)) + Vector3.new(math.sin(q * 0.6) * 0.6, 0, 0)
		cam.CFrame = CFrame.lookAt(CATH + cp, CATH + Vector3.new(0, 6.2 + 1.2 * eo(q / 4.5), 4))
		cam.FieldOfView = 35
	end
	-- ---------------- castle lights, rim, stand glow, flames, sparkles, the sign on the stand
	S.eggLight.Color = col
	S.eggLight.Brightness = popped and (2 * math.exp(-pa * 2) + 0.4) or (0.3 + 1.6 * build + 2.5 * hit)
	S.backLight.Color = col
	S.backLight.Brightness = (L == 0) and 0 or (popped and (4 * math.exp(-pa * 1.5) + 0.6) or (5 * (0.2 + 0.8 * hit) * ((L >= 4) and 0.6 or 1)))
	S.standGlow.Color = col
	S.standGlow.Transparency = 1 - clamp(0.2 + 0.5 * build)
	local rimA = 1 - clamp(0.3 + 0.6 * build + 0.3 * hit)
	for _, p in ipairs(S.rim) do
		p.Color = col
		p.Transparency = rimA
	end
	for _, fl in ipairs(S.flames) do
		local f = 0.75 + 0.25 * math.sin(now * (11 + fl[4]) + 1) + 0.1 * math.sin(now * 23 + fl[4])
		local s = 0.9 * f * (1 + 0.2 * build)
		local y = 0.08 * math.sin(now * 9 + fl[4])
		fl[1].Size = Vector3.new(s, s, s)
		fl[1].Color = Color3.fromRGB(255, 120, 30):Lerp(col, 0.4 * build)
		fl[1].CFrame = CFrame.new(fl[3] + Vector3.new(0, 3.95 + y, 0))
		fl[2].Size = Vector3.new(s * 0.55, s * 0.55, s * 0.55)
		fl[2].CFrame = CFrame.new(fl[3] + Vector3.new(0, 4.4 + y, 0))
	end
	S.dust.Rate = inCath and 0 or (8 + 40 * build)
	S.dust.Color = ColorSequence.new(WHITE:Lerp(col, 0.4))
	S.dust2.Rate = inCath and 30 or 0
	if L > 0 and not popped and whiten < 0.5 then
		S.signSmall.Visible = true
		S.signBig.Text = RNAME[L]
		S.signBig.TextColor3 = col
		S.signScale.Scale = 1 + 0.5 * math.exp(-age * 10)
	else
		S.signSmall.Visible = false
		S.signBig.Text = ""
	end
	-- ---------------- screen: colour flash at each step, white flash at the pop, the ??? odds counter
	local fa = 0
	if L > 0 and not popped then
		fa = 0.5 * math.exp(-age * 8)
	elseif popped then
		flash.BackgroundColor3 = WHITE
		if sh.cath then
			fa = (pa < 0.32) and math.min(1, pa / 0.06) or math.max(0, 1 - (pa - 0.32) / 0.6)
		else
			fa = math.max(0, 1 - pa / 0.45) * 0.9
		end
	end
	if t > sh.T_END - 0.35 then -- fade to black at the end
		flash.BackgroundColor3 = Color3.new(0, 0, 0)
		fa = clamp((t - (sh.T_END - 0.35)) / 0.35)
	end
	flash.BackgroundTransparency = 1 - clamp(fa)
	if L == 6 and not popped then
		local u = clamp(age / (SECRET_T * 0.9))
		local lo, hi = math.log10(200), math.log10(SECRET_ODDS)
		local v = SECRET_ODDS
		if u < 1 then
			v = 10 ^ (lo + (hi - lo) * u ^ 1.25)
			local kd = 10 ^ (#tostring(math.floor(v)) - 2)
			v = math.floor(v / kd + 0.5) * kd
		end
		local dg = #tostring(math.floor(v))
		if dg ~= sh.digits then
			sh.digits = dg
			sh.pulseT = t
			sfx("ui_click", 0.7, 0.9 + 0.08 * (dg - 3))
		end
		setText(counter, "1 / " .. C.comma(math.floor(v)), 1)
		counter.TextColor3 = WHITE:Lerp(col, 0.5)
		counterScale.Scale = 1 + 0.35 * math.exp(-(t - (sh.pulseT or t)) * 10)
	else
		setText(counter, "", 0)
	end

	if not popped then
		-- ---------------- the egg: rises into the claws, floats, rocks; jolts at every crack; turns white before the pop
		local bob = 0.12 * math.sin(t * 2.2)
		local shake = build ^ 2 * 0.12 + 0.05 * hit + 0.25 * whiten
		local ox, oy = rnd:NextNumber(-1, 1) * shake, rnd:NextNumber(-1, 1) * shake * 0.5
		local tilt = math.sin(t * 2) * 0.05 + math.sin(t * 31) * 0.05 * build ^ 2 + 0.035 * jolt
		local sw = 1 + 0.02 * hit + 0.1 * whiten + 0.012 * math.abs(jolt)
		local Mg = CFrame.new(O + EC + Vector3.new(ox, bob + oy - (1 - eo(t / 0.6)) * 1.2, 0)) * CFrame.Angles(0, 0, tilt) * CFrame.Angles(0, 0.12 * math.sin(t * 0.6), 0)
		sh.egg.Transparency = 0
		sh.egg.Size = sh.unit * sw
		sh.egg.CFrame = Mg * sh.rot
		sh.shell.CFrame = Mg
		sh.shell.Size = Vector3.new(sw, sw, sw)
		setN(sh.shell, WHITE, whiten ^ 1.5 * 0.97)
		local ccol = col:Lerp(WHITE, 0.6)
		for i, sg in ipairs(sh.segs) do
			local te = sh.events[sg.ev][1]
			local g = clamp((t - te - sg.order * 0.02) / 0.05)
			if g <= 0 then
				sh.crG[i].Transparency = 1
				sh.crC[i].Transparency = 1
			else
				local p0 = Mg:PointToWorldSpace(sg.p * sw * 1.015)
				local q0 = Mg:PointToWorldSpace((sg.p + (sg.q - sg.p) * g) * sw * 1.015)
				local fresh = math.exp(-(t - te) * 5)
				bar(sh.crG[i], p0, q0, 0.16 + 0.14 * fresh)
				setN(sh.crG[i], col, 0.3 + 0.4 * fresh)
				bar(sh.crC[i], p0, q0, 0.06 + 0.02 * fresh)
				setN(sh.crC[i], ccol, 1)
			end
		end
		local c = O + EC + Vector3.new(ox, bob, 0)
		if L > 0 then
			for j, sgn in ipairs({ -1, 1 }) do -- two glowing orbs at the egg's sides
				local pos = c + Vector3.new(sgn * (sh.rx + 0.35), 0, -0.4)
				local s1 = 0.75 + 0.35 * hit
				sh.orbs[j].Size = Vector3.new(s1, s1, s1)
				sh.orbs[j].CFrame = CFrame.new(pos)
				setN(sh.orbs[j], col, 0.45)
				sh.orbs[j + 2].Size = Vector3.new(0.32, 0.32, 0.32)
				sh.orbs[j + 2].CFrame = CFrame.new(pos + Vector3.new(0, 0, -0.2))
				setN(sh.orbs[j + 2], WHITE, 1)
			end
		end
		if L > 0 and age < 1 then
			ringAt(sh.ring, O + EC + Vector3.new(0, 0, -1.5), 3 + 9 * eo(age), t * 0.6, WHITE, 1 - age, true)
		else
			hideList(sh.ring)
		end
		-- EPIC: light petals; LEGENDARY (and ???): more petals + gold spike crown + a turning square
		if L >= 4 and whiten < 1 then
			local n = (L == 4) and 6 or 10
			local g = (L == 4 or (L == 5 and age < 0.45)) and backOut(age / 0.45) or 1
			for i = 1, 10 do
				local p, pc = sh.petals[i], sh.petalC[i]
				if i <= n then
					local a = (i - 1) * math.pi * 2 / n + t * 0.5
					local dir = Vector3.new(math.cos(a), math.sin(a), 0)
					local R0 = (EGG_RY + 0.1) * g
					local base = c + Vector3.new(math.cos(a) * R0 * 0.85, math.sin(a) * R0, 0)
					local side = Vector3.new(-dir.Y, dir.X, 0)
					p.CFrame = CFrame.fromMatrix(base + dir * 0.75 * g + Vector3.new(0, 0, -1.6), side, dir)
					p.Mesh.Scale = Vector3.new(0.6, 1.5, 0.08) * g
					setN(p, col, 1 - whiten)
					pc.CFrame = CFrame.fromMatrix(base + dir * 0.7 * g + Vector3.new(0, 0, -1.68), side, dir)
					pc.Mesh.Scale = Vector3.new(0.26, 1.0, 0.08) * g
					setN(pc, WHITE, 1 - whiten)
				else
					p.Transparency = 1
					pc.Transparency = 1
				end
			end
		else
			hideList(sh.petals)
			hideList(sh.petalC)
		end
		if L >= 5 and whiten < 1 then
			local g = (L == 5) and backOut(age / 0.5) or 1
			for i, sp in ipairs(sh.spikes) do
				local a = (i - 1) * math.pi * 2 / 18 - t * 0.35
				local dir = Vector3.new(math.cos(a), math.sin(a), 0)
				local base = c + Vector3.new(math.cos(a) * 2.7 * g * 0.95, math.sin(a) * 2.7 * g * 1.1, -1.4)
				placeSpike(sp, base, dir, ((i % 2 == 1) and 1.6 or 1.0) * g, 0.5 * g, col:Lerp(WHITE, (i % 2 == 0) and 0.15 or 0), 1 - whiten)
			end
			local sq, rot = 2.6 * g, t * 0.7
			for i = 1, 4 do
				local a0, a1 = rot + (i - 1) * math.pi / 2, rot + i * math.pi / 2
				bar(sh.square[i], c + Vector3.new(math.cos(a0) * sq, math.sin(a0) * sq, -2), c + Vector3.new(math.cos(a1) * sq, math.sin(a1) * sq, -2), 0.07)
				setN(sh.square[i], WHITE, 0.9 * (1 - whiten))
			end
		else
			hideList(sh.spikes)
			hideList(sh.square)
		end
	else
		-- ---------------- POP: star burst, dashed rings, rays, shards; then the pet (stand, or the cathedral altar)
		if not sh.cleared then
			sh.cleared = true
			sh.egg.Transparency = 1
			sh.shell.Transparency = 1
			hideList(sh.crG)
			hideList(sh.crC)
			hideList(sh.orbs)
			hideList(sh.petals)
			hideList(sh.petalC)
			hideList(sh.spikes)
			hideList(sh.square)
			hideList(sh.ring)
		end
		local BC = inCath and (CATH + ECP) or (O + EC)
		local bt = inCath and (pa - 0.3) or pa
		if bt < 1.8 then
			local u = bt / 1.8
			local g = eo(bt / 0.35)
			local pts = {}
			for i = 1, 12 do
				local a = (i - 1) * math.pi * 2 / 12 + bt * 0.4
				pts[i] = BC + Vector3.new(math.cos(a) * 6.5 * g, math.sin(a) * 6.5 * g, -1.8)
			end
			for i = 1, 12 do
				bar(sh.star[i], pts[i], pts[(i + 4) % 12 + 1], 0.1)
				setN(sh.star[i], (i % 2 == 0) and Color3.fromRGB(255, 236, 150) or WHITE, 1.3 - u)
			end
			ringAt(sh.ring, BC + Vector3.new(0, 0, -1.7), 7.2 * g + 3 * u, bt * 0.5, WHITE, 1.2 - u, true)
			ringAt(sh.ring2, BC + Vector3.new(0, 0, -1.7), 8.4 * g + 3 * u, -bt * 0.5, Color3.fromRGB(255, 220, 120), 1.2 - u, true)
			for i = 1, 20 do
				local a = (i - 1) * math.pi * 2 / 20 + 0.1
				local dir = Vector3.new(math.cos(a), math.sin(a), 0)
				local ln = 3 + 18 * eo(bt / 0.5)
				local s0 = BC + dir * 1.5 + Vector3.new(0, 0, -1.9)
				bar(sh.rays[i], s0, s0 + dir * ln, 0.1 * (1 - u) + 0.03)
				setN(sh.rays[i], (i % 2 == 0) and WHITE or Color3.fromRGB(255, 240, 170), clamp(1 - u) * 0.8)
			end
			local sr = Random.new(9)
			for i = 1, 26 do
				local a = sr:NextNumber(0, math.pi * 2)
				local d = sr:NextNumber(6, 13) * bt
				local spin = sr:NextNumber(-4, 4)
				sh.shards[i].CFrame = CFrame.new(BC + Vector3.new(math.cos(a) * d, math.sin(a) * d - 2.5 * bt * bt, -2.4)) * CFrame.Angles(0, 0, math.pi / 4 + bt * spin)
				setN(sh.shards[i], (i % 3 == 0) and Color3.fromRGB(255, 220, 120) or WHITE, 1.2 - u)
			end
		else
			hideList(sh.star)
			hideList(sh.ring)
			hideList(sh.ring2)
			hideList(sh.rays)
			hideList(sh.shards)
		end
		-- the pet
		local pos, kk, spin
		if not sh.cath then
			local g = (pa > 0.08) and backOut((pa - 0.08) / 0.5) or 0.01
			kk = sh.fit * math.max(g, 0.01)
			local hop = 1.2 * (1 - eo(pa / 0.6))
			spin = math.pi * 2 * (1 - eo(pa / 1.2)) + 0.25 * math.sin(pa * 1.6) * clamp(pa - 1.2)
			pos = O + Vector3.new(0, STAND_TOP - 0.2 + hop + 0.1 * math.abs(math.sin(pa * 3)) * clamp(pa - 1.5), 0)
			if R >= 3 then -- gold spike crown behind the pet
				for i, sp in ipairs(sh.spikes) do
					local a = (i - 1) * math.pi * 2 / 18 - t * 0.25
					local dir = Vector3.new(math.cos(a), math.sin(a), 0)
					local base = O + Vector3.new(0, STAND_TOP + 2.6, 2.5) + dir * 3.6 * eo(pa / 0.6)
					placeSpike(sp, base, dir, (i % 2 == 1) and 1.5 or 0.9, 0.45, (R >= 4) and WARM or RCOL[3], 0.85)
				end
			end
		elseif inCath then
			local q = pa - 0.3
			for i, sp in ipairs(sh.sunb) do -- golden sunburst slowly turning behind the pet
				local a = (i - 1) * math.pi * 2 / 28 + q * 0.15
				local dir = Vector3.new(math.cos(a), math.sin(a), 0)
				local base = CATH + ECP + Vector3.new(0, 0.4, 2.2) + dir * 2.6 * eo(q / 0.8)
				placeSpike(sp, base, dir, ((i % 2 == 1) and 5.5 or 3.4) * eo(q / 1), 0.38, (i % 2 == 1) and Color3.fromRGB(255, 214, 110) or Color3.fromRGB(255, 245, 210), 0.55)
			end
			for i, sp in ipairs(sh.spikes) do
				local a = (i - 1) * math.pi * 2 / 18 - q * 0.3
				local dir = Vector3.new(math.cos(a), math.sin(a), 0)
				local base = CATH + ECP + Vector3.new(0, 0.4, 1.8) + dir * 3.3 * eo(q / 0.7)
				placeSpike(sp, base, dir, (i % 2 == 1) and 1.3 or 0.8, 0.36, WARM, 0.85)
			end
			for _, cdl in ipairs(S.candles) do
				local f = 0.8 + 0.2 * math.sin(now * (10 + cdl[3] % 5) + cdl[3])
				cdl[1].Size = Vector3.new(0.35 * f, 0.35 * f, 0.35 * f)
				cdl[1].CFrame = CFrame.new(cdl[2] + Vector3.new(0, 0.03 * math.sin(now * 13 + cdl[3]), 0))
			end
			S.altarLight.Brightness = 2 + 6 * math.exp(-q * 2.5)
			local g = (q > 0.05) and backOut((q - 0.05) / 0.7) or 0.01
			kk = sh.fit * math.max(g, 0.01)
			local rise = 1.6 * (1 - eo(q / 1.1))
			spin = math.pi * 2 * (1 - eo(q / 1.6)) + 0.22 * math.sin(q * 1.3) * clamp(q - 1.6)
			pos = CATH + Vector3.new(0, ALTAR_TOP + 1.1 + rise + 0.08 * math.sin(q * 2.4) * clamp(q - 1.2), 4.5)
		end
		if pos then
			if math.abs(kk - sh.lastK) > 0.002 then
				sh.lastK = kk
				sh.model:ScaleTo(kk)
			end
			sh.model:PivotTo(CFrame.new(pos) * CFrame.Angles(0, spin, 0) * CFrame.new(sh.off * kk))
		end
		-- name + odds (serif, gold) once the pet is out
		local tn = sh.cath and 1.3 or 0.5
		if pa > tn then
			local u = eo((pa - tn) / 0.6)
			setText(petNameL, C.petName(sh.pet), u)
			nameScale.Scale = 0.85 + 0.15 * u
			local odds = sh.job.secret and SECRET_ODDS or C.RARITY[sh.pet.i].odds
			setText(oddsL, (sh.job.isNew and "NEW!   " or "") .. "1 / " .. C.comma(odds), eo((pa - tn - 0.3) / 0.5))
		end
	end
	if t >= sh.T_END then
		sh.done = true
	end
end

RunService:BindToRenderStep("HatchShow", Enum.RenderPriority.Camera.Value + 1, function(dt)
	local sh = running
	if not sh or sh.done then
		return
	end
	local ok, err = pcall(drawShow, sh, math.min(dt, 0.1))
	if not ok then
		warn("hatch show: " .. tostring(err))
		sh.done = true
	end
end)
-- tap / click during a show: the rest plays 3x faster
game:GetService("UserInputService").InputBegan:Connect(function(input)
	if running and (input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch) then
		speedUp = 3
	end
end)

local function cleanupAfterError()
	running = nil
	for _, o in ipairs(workspace:GetChildren()) do
		if o.Name == "HatchRun" then
			o:Destroy()
		end
	end
	leaveShow()
end

-- one queue for real hatches AND the Studio test keys, so two shows never overlap
local queue = {}
local busy = false
local function enqueue(job)
	table.insert(queue, job)
	if busy then
		return
	end
	busy = true
	task.spawn(function()
		while #queue > 0 do
			local job1 = table.remove(queue, 1)
			-- big batch: Common/Uncommon only get a line of text; Rare plays faster; Epic+ always get the full show
			if #queue >= 3 and job1.pet.i < 3 and not job1.secret then
				showNote(C.petName(job1.pet) .. "  (1 in " .. C.comma(C.RARITY[job1.pet.i].odds) .. ")", "good")
				task.wait(0.2)
			else
				job1.fast = #queue > 0 and job1.pet.i < 4
				local ok, err = pcall(runShow, job1)
				if not ok then
					warn("hatch show: " .. tostring(err))
					cleanupAfterError()
				end
			end
		end
		busy = false
	end)
end
Hatch.OnClientEvent:Connect(function(pet, kind, isNew, comboNow) -- <- the trigger: the server fires "Hatch" when an egg is hatched
	enqueue({ pet = pet, kind = kind, isNew = isNew })
end)

-- STUDIO ONLY test: F1..F5 = hatch show of that rarity (zone 1 egg), F6 = the ??? step; Shift = 6 at once (batch test)
if RunService:IsStudio() then
	local UIS = game:GetService("UserInputService")
	local KEYS = { [Enum.KeyCode.F1] = 1, [Enum.KeyCode.F2] = 2, [Enum.KeyCode.F3] = 3, [Enum.KeyCode.F4] = 4, [Enum.KeyCode.F5] = 5, [Enum.KeyCode.F6] = 6 }
	UIS.InputBegan:Connect(function(input, typing)
		local r = KEYS[input.KeyCode]
		if r and not typing then
			local n = UIS:IsKeyDown(Enum.KeyCode.LeftShift) and 6 or 1
			for j = 1, n do
				local rr = (n > 1 and j % 2 == 1) and math.max(1, math.min(r, 5) - 2) or r
				enqueue({ pet = { z = 1, i = math.min(rr, 5), t = 1 }, kind = "normal", isNew = rr >= 4, secret = rr == 6 })
			end
		end
	end)
end
end
