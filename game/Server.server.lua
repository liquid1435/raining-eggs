-- Raining Eggs: server
-- egg rain, catch check, hatch RNG, combo, rotten/golden/storm eggs, basket, pen + fusion, income,
-- treadmill, gates, upgrades, index, rebirth, storm event, leaderboards, save
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local CS = game:GetService("CollectionService")
local DSS = game:GetService("DataStoreService")
local C = require(RS:WaitForChild("Config"))

local Map = workspace:WaitForChild("Map")

local Remotes = Instance.new("Folder")
Remotes.Name = "Remotes"
local function remote(name)
	local r = Instance.new("RemoteEvent")
	r.Name = name
	r.Parent = Remotes
	return r
end
local EggSpawn = remote("EggSpawn") -- server -> all: id, x, z, y0, groundY, fall, zone, kind, linger
local EggGone = remote("EggGone") -- server -> all: id, userId of the catcher, kind
local Catch = remote("Catch") -- client -> server: id
local Hatch = remote("Hatch") -- server -> catcher: pet, egg kind, new in index, combo
local Notice = remote("Notice") -- server -> client: text, kind
local Bought = remote("Bought") -- v280 server -> buyer: what was bought (CONGRATULATIONS + fireworks + confetti)
local Action = remote("Action") -- client -> server: "rebirth"
Remotes.Parent = RS

-- ------------------------------------------------------------ Blender models
-- File > Import 3D puts "RainingEggsAssets" in Workspace; the game keeps it in ReplicatedStorage.Assets (see Config.meshOf)
if not RS:FindFirstChild("Assets") then
	for _, m in ipairs(workspace:GetChildren()) do
		if m.Name:find("RainingEggsAssets") or (m:IsA("Model") and m:FindFirstChild("Pet_1_1", true)) then
			m.Name = "Assets"
			m.Parent = RS
			break
		end
	end
end

-- ------------------------------------------------------------ map clean-up
for _, d in ipairs(Map:GetDescendants()) do
	if d.Name == "DemoPet" then
		d:Destroy()
	elseif d.Name == "DemoEgg" and d:GetFullName():find("Zone") then
		d:Destroy()
	end
end

-- ------------------------------------------------------------ bases
local bases = {}
for i = 1, 8 do
	local m = Map:FindFirstChild("Base" .. i)
	if m then
		local folder = Instance.new("Folder")
		folder.Name = "Pets"
		folder.Parent = m
		bases[i] = {
			pen = m:FindFirstChild("PenFloor", true),
			tread = m:FindFirstChild("Treadmill", true),
			sign = m:FindFirstChild("OwnerSign", true),
			treadSign = m:FindFirstChild("TreadSign", true),
			folder = folder,
			model = m,
			owner = nil,
		}
	end
end

local buyTrain -- v162: defined next to buy()
-- v232: pen space upgrade (UPGRADES menu): every level = one more pet in your pen
local function penMax(d)
	return C.PEN_MAX + (d and d.pen or 0) + ((d and d.passes and d.passes.slots3) and C.SLOTS_PASS or 0) -- v262: +3 Pet Slots pass
end

-- treadmills from TreadmillPack (ReplicatedStorage.Shared): 20 models, a better one every 3 training levels
local Shared = RS:FindFirstChild("Shared")
local TBuilder = Shared and Shared:FindFirstChild("TreadmillBuilder") and require(Shared.TreadmillBuilder)
local TList = TBuilder and TBuilder.list()
local function treadTier(lv)
	return math.clamp(math.floor(lv / 3) + 1, 1, TList and #TList or 20)
end
-- the sign on the fence next to the treadmill: TREADMILL / LEVEL n / next upgrade price (lv = nil: empty base)
local function setTreadSign(base, lv)
	local part = base.treadSign
	if true or not part then -- the board is private now: each player's client shows only its own (Client: treadmill upgrade panel)
		return
	end
	local g = base.treadGui
	if not g then
		g = Instance.new("SurfaceGui")
		g.Face = Enum.NormalId.Back
		g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		g.PixelsPerStud = 50
		g.LightInfluence = 0
		g.Parent = part
		local bg = Instance.new("Frame")
		bg.Size = UDim2.fromScale(1, 1)
		bg.BackgroundColor3 = Color3.fromRGB(255, 196, 60)
		bg.BorderSizePixel = 0
		bg.Parent = g
		local gr = Instance.new("UIGradient")
		gr.Rotation = 90
		gr.Color = ColorSequence.new(Color3.fromRGB(255, 226, 120), Color3.fromRGB(240, 150, 30))
		gr.Parent = bg
		local st = Instance.new("UIStroke")
		st.Thickness = 10
		st.Color = Color3.fromRGB(40, 26, 20)
		st.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
		st.Parent = bg
		local function line(name, y, h, col)
			local t = Instance.new("TextLabel")
			t.Name = name
			t.BackgroundTransparency = 1
			t.Position = UDim2.fromScale(0.05, y)
			t.Size = UDim2.fromScale(0.9, h)
			t.Font = Enum.Font.LuckiestGuy
			t.TextScaled = true
			t.TextColor3 = col
			t.Text = ""
			t.Parent = bg
			local s2 = Instance.new("UIStroke")
			s2.Thickness = 5
			s2.Color = Color3.fromRGB(30, 20, 40)
			s2.Parent = t
			return t
		end
		line("Title", 0.06, 0.26, Color3.fromRGB(255, 255, 255))
		line("Level", 0.36, 0.28, Color3.fromRGB(130, 220, 255))
		line("Price", 0.68, 0.26, Color3.fromRGB(140, 255, 120))
		base.treadGui = g
	end
	local bg = g:FindFirstChildOfClass("Frame")
	bg.Title.Text = "TREADMILL"
	if lv == nil then
		bg.Level.Text = ""
		bg.Price.Text = ""
	elseif lv >= C.MAX_LV.train then
		bg.Level.Text = "LEVEL " .. lv
		bg.Price.Text = "MAX"
	else
		bg.Level.Text = "LEVEL " .. lv
		bg.Price.Text = "UPGRADE $" .. C.fmt(C.cost("train", lv))
	end
end

local function setTreadmill(base, lv)
	if not (TList and base.tread) then
		return
	end
	local tier = treadTier(lv)
	if base.treadTier == tier then
		return
	end
	base.treadTier = tier
	if base.treadModel then
		base.treadModel:Destroy()
	end
	local model = TBuilder.build(TList[tier])
	local prim = model.PrimaryPart
	model.PrimaryPart = nil -- pivot on the ground under the model, not in the middle of its base plate
	model.WorldPivot = CFrame.new()
	local c = base.tread.Position
	local pivot = CFrame.new(c.X, c.Y - base.tread.Size.Y / 2, c.Z) * CFrame.Angles(0, math.pi / 2, 0)
	model:PivotTo(pivot)
	model.PrimaryPart = prim
	-- the client animates a light show around it (spinning ring, orbiting cubes, moving belt stripes, sparkles)
	model:SetAttribute("Neon", Color3.fromHex(TList[tier].Neon or "#FFFFFF"))
	model:SetAttribute("PivotCF", pivot)
	CS:AddTag(model, "TreadShow")
	-- Blender version of the same treadmill (when imported): show the meshes, keep the block parts only for collisions
	local id = TList[tier].Id
	local meta = RS:FindFirstChild("PropsMeta") and require(RS.PropsMeta)
	local function addMesh(name, neon)
		local src, m = C.meshOf(name), meta and meta[name]
		if not (src and m) then
			return false
		end
		local p = src:Clone()
		p.Name = neon and "NeonMesh" or "BodyMesh"
		p.Size = Vector3.new(m.size[1], m.size[2], m.size[3])
		p.CFrame = pivot * CFrame.new(m.centre[1], m.centre[2], m.centre[3]) * CFrame.Angles(0, C.PROP_YAW, 0)
		p.Color = Color3.new(1, 1, 1)
		p.Material = neon and Enum.Material.Neon or Enum.Material.SmoothPlastic
		p.Anchored = true
		p.CanCollide = false
		p.CanTouch = false
		p.CanQuery = false
		p.CastShadow = not neon
		p.Parent = model
		return true
	end
	if addMesh("Tread_" .. id, false) then
		addMesh("TreadNeon_" .. id, true)
		for _, p in ipairs(model:GetChildren()) do
			if p:IsA("Part") then
				p.Transparency = 1
				p.CastShadow = false
			end
		end
	end
	model.Parent = base.model
	base.treadModel = model
end
for _, base in pairs(bases) do
	setTreadmill(base, 0)
end

-- the owner's name floats in the air above the pen ("EMPTY" when nobody owns it)
local function setSign(base, text, sub)
	if not base.sign then
		return
	end
	local bb = base.sign:FindFirstChild("OwnerTag")
	if not bb then
		bb = Instance.new("BillboardGui")
		bb.Name = "OwnerTag"
		bb.Size = UDim2.fromScale(30, 9)
		bb.MaxDistance = 400
		bb.AlwaysOnTop = false
		bb.LightInfluence = 0
		local function line(name, y, h, col)
			local t = Instance.new("TextLabel")
			t.Name = name
			t.BackgroundTransparency = 1
			t.Size = UDim2.fromScale(1, h)
			t.Position = UDim2.fromScale(0, y)
			t.Font = Enum.Font.FredokaOne
			t.Text = ""
			t.TextColor3 = col
			t.TextScaled = true
			local st = Instance.new("UIStroke")
			st.Thickness = 4
			st.Color = Color3.fromRGB(14, 20, 48)
			st.Parent = t
			t.Parent = bb
		end
		line("NameLabel", 0, 0.62, Color3.new(1, 1, 1))
		line("SubLabel", 0.62, 0.38, Color3.fromRGB(255, 222, 60))
		bb.Parent = base.sign
	end
	bb.NameLabel.Text = text
	bb.NameLabel.TextColor3 = base.owner and Color3.new(1, 1, 1) or Color3.fromRGB(200, 206, 224)
	bb.SubLabel.Text = sub or ""
end
for _, base in pairs(bases) do
	setSign(base, "EMPTY")
end

-- ------------------------------------------------------------ player data
local data = {}
local store
pcall(function()
	store = DSS:GetDataStore("RainingEggs_v1")
end)

local function zonesDone(d)
	local n = 0
	for z = 1, C.NZ do
		local all = true
		for i = 1, #C.RARITY do
			local got = d.index[z .. "_" .. i]
			for v = 2, C.variantCount(z, i) do
				got = got or d.index[z .. "_" .. i .. "_" .. v]
			end
			if not got then
				all = false
				break
			end
		end
		if all then
			n = n + 1
		end
	end
	return n
end

-- v153: which of the 3 animals of a rarity hatches (equal chance); a variant only once its meshes are imported
-- v164 (user: 3 eggs gave the same beetle 3 times): animals of that rarity you do not have yet come first, so 3 eggs
-- of one rarity give its 3 different animals; once you have all 3, it is random again
local function rollVariant(pet, d)
	local PA = C.petAnim()
	local ok = { 1 }
	for v = 2, C.variantCount(pet.z, pet.i) do
		if PA and PA.has({ z = pet.z, i = pet.i, v = v }) then
			table.insert(ok, v)
		end
	end
	local new = {}
	for _, v in ipairs(ok) do
		local key = pet.z .. "_" .. pet.i .. (v > 1 and ("_" .. v) or "")
		if not (d and d.index[key]) then
			table.insert(new, v)
		end
	end
	local list = #new > 0 and new or ok
	local v = list[math.random(1, #list)]
	return v > 1 and v or nil
end
task.defer(function() -- Output check: how many variant animals the game can hatch
	local PA, n = C.petAnim(), 0
	for z = 1, C.TOTAL do
		for i = 1, #C.RARITY do
			for v = 2, C.variantCount(z, i) do
				if PA and PA.has({ z = z, i = i, v = v }) then
					n = n + 1
				end
			end
		end
	end
	print("Pet variants live: " .. n .. " (should be 100)")
end)
local function eventKey()
	return (C.eventAt(os.time())).key
end
local function cashMult(d)
	return C.rebirthMult(d.rebirth) * (1 + C.INDEX_BONUS * d.zonesDone) * (d.passes.cash2 and 2 or 1)
		* (eventKey() == "cash" and 2 or 1) * (1 + C.FRIEND_BONUS * (d.friends or 0)) -- v150: weekly event + friends
		* (1 + C.traitBonus(d.pets).cash) -- v250: Fire / Gold / Machine / Dragon traits
end

-- basket size: upgrades + the VIP Basket game pass
local function carryMax(d)
	return C.basketMax(d.basket) + (d.passes.vip and C.VIP_BASKET or 0)
end

local function petList(list)
	local t = {}
	for _, pet in ipairs(list) do
		table.insert(t, pet.z .. "_" .. pet.i .. "_" .. (pet.t or 1) .. ((pet.v or 1) > 1 and ("_" .. pet.v) or "")) -- v153: _v
	end
	return table.concat(t, ",")
end

-- v119 equip: d.pets = the EQUIPPED pets (stand in the pen, earn cash, max C.PEN_MAX), d.stored = the other pets you own
-- (max C.STORAGE_MAX). The client sees one list (PetList = equipped first, then stored) + "Equipped" = how many are equipped,
-- so "p<i>" (SELL shop) and the PETS menu use one index i into that list.
local function ownedAt(d, i)
	if i >= 1 and i <= #d.pets then
		return d.pets, i
	end
	local j = i - #d.pets
	if j >= 1 and j <= #d.stored then
		return d.stored, j
	end
	return nil
end

local function byIncome(list)
	table.sort(list, function(a, b)
		return C.petIncome(a) > C.petIncome(b)
	end)
end

local function income(d)
	local sum = 0
	for _, pet in ipairs(d.pets) do
		sum = sum + C.petIncome(pet)
	end
	return sum * cashMult(d)
end

local function sync(plr)
	local d = data[plr]
	if not d then
		return
	end
	plr:SetAttribute("Cash", d.cash)
	plr:SetAttribute("Speed", d.speed)
	plr:SetAttribute("Carry", #d.carry + #d.bag)
	plr:SetAttribute("Eggs", #d.bag) -- unhatched eggs (EGGS menu on the left)
	local el = {}
	for _, egg in ipairs(d.bag) do
		table.insert(el, egg.z .. "_" .. egg.kind)
	end
	plr:SetAttribute("EggList", table.concat(el, ","))
	plr:SetAttribute("CarryMax", carryMax(d))
	plr:SetAttribute("Radius", C.basketRadius(d.basket))
	plr:SetAttribute("TrainLv", d.train)
	plr:SetAttribute("Tut", d.tut or 99)
	if bases[d.base] then
		setTreadmill(bases[d.base], d.train)
		setTreadSign(bases[d.base], d.train)
	end
	plr:SetAttribute("BasketLv", d.basket)
	plr:SetAttribute("LuckLv", d.luck)
	plr:SetAttribute("PenLv", d.pen or 0)
	plr:SetAttribute("PenMax", penMax(d))
	plr:SetAttribute("Rebirth", d.rebirth)
	plr:SetAttribute("Income", income(d))
	plr:SetAttribute("Pets", #d.pets)
	plr:SetAttribute("Combo", d.combo)
	plr:SetAttribute("ZonesDone", d.zonesDone)
	plr:SetAttribute("Unlocked", d.unlocked) -- highest zone this player has bought (the client hides those gates)
	local owned = petList(d.pets)
	if #d.stored > 0 then
		owned = owned .. (owned ~= "" and "," or "") .. petList(d.stored)
	end
	plr:SetAttribute("PetList", owned) -- all your pets for the PETS / SELL menus: the equipped ones first
	plr:SetAttribute("Equipped", #d.pets)
	plr:SetAttribute("CarryList", petList(d.carry))
	plr:SetAttribute("Caught", d.caught)
	local al = {}
	for z in pairs(d.altar or {}) do
		table.insert(al, z)
	end
	table.sort(al)
	plr:SetAttribute("Altar", table.concat(al, ",")) -- Golden Nest altars this player has filled
	plr:SetAttribute("BestOdds", d.bestOdds)
	local owned = {}
	for k in pairs(d.passes) do
		table.insert(owned, k)
	end
	plr:SetAttribute("Passes", table.concat(owned, ","))
	plr:SetAttribute("DailyDay", d.dailyDay)
	plr:SetAttribute("DailyLast", d.dailyLast)
	local base = bases[d.base]
	local inc = math.floor(income(d))
	if base and base.shownInc ~= inc then
		base.shownInc = inc
		setSign(base, plr.DisplayName, "$" .. C.fmt(inc) .. " / s")
	end
	local ls = plr:FindFirstChild("leaderstats")
	if ls then
		ls.Cash.Value = math.floor(d.cash)
		ls.Speed.Value = math.floor(d.speed)
		ls.Rebirths.Value = d.rebirth
	end
end

local function syncIndex(plr)
	local d = data[plr]
	local keys = {}
	for key in pairs(d.index) do
		table.insert(keys, key)
	end
	plr:SetAttribute("Index", table.concat(keys, ","))
end

local function say(plr, text, kind)
	Notice:FireClient(plr, text, kind or "info")
end

-- ------------------------------------------------------------ pets in the pen / on the head
local TIER_COLOR = { nil, Color3.fromRGB(255, 204, 40), Color3.fromRGB(255, 120, 220) }
local function label(model, pet, mult)
	local bb = Instance.new("BillboardGui")
	bb.Name = "Tag"
	bb.Size = UDim2.fromOffset(170, 64) -- v250: + trait line; v214 (user: a giant "$600M/s" up close): same size on screen at any distance
	-- v144 fix (user: some pets showed no $/s): the tag sat a fixed 5 studs up, inside the big pets' bodies
	-- (AlwaysOnTop off hides it there), and pets without a PrimaryPart got no tag at all -> put it above the real top
	local root = model.PrimaryPart or model:FindFirstChildWhichIsA("BasePart", true)
	if not root then
		return
	end
	local bcf, bsize = model:GetBoundingBox()
	local top = bcf.Position.Y + bsize.Y / 2 - root.Position.Y
	bb.StudsOffsetWorldSpace = Vector3.new(0, math.max(top, 2) + 2.2, 0)
	bb.MaxDistance = 90
	bb.AlwaysOnTop = false
	bb.Adornee = root
	local function line(text, y, h, col)
		local t = Instance.new("TextLabel")
		t.BackgroundTransparency = 1
		t.Size = UDim2.fromScale(1, h)
		t.Position = UDim2.fromScale(0, y)
		t.Font = Enum.Font.FredokaOne
		t.Text = text
		t.TextColor3 = col
		t.TextScaled = true
		local st = Instance.new("UIStroke")
		st.Thickness = 2.5
		st.Color = Color3.new(0, 0, 0)
		st.Parent = t
		t.Parent = bb
	end
	line(C.petName(pet), 0, 0.42, TIER_COLOR[pet.t] or C.RARITY[pet.i].color)
	line("$" .. C.fmt(C.petIncome(pet) * mult) .. "/s", 0.42, 0.33, Color3.fromRGB(255, 222, 60))
	line(C.traitText(pet), 0.75, 0.25, Color3.fromRGB(200, 235, 255)) -- v250: the pet's trait (+ bonus for Epic / Legendary)
	bb.Parent = root
end

local SLOT_X = { -14, 0, 14 } -- v156: bigger pens (48 x 60) and bigger pets
local SLOT_Z = { 8, -4, -16, -24 } -- front row first (the pen opens towards the plaza, +Z); behind the treadmill
local function renderPen(plr)
	local d = data[plr]
	local base = d and bases[d.base]
	if not base or not base.pen then
		return
	end
	-- v184 (user: placing / taking one pet reset all the others): keep the models of pets that stay in the pen (they keep
	-- walking where they are on the clients); only removed pets lose their model, only new pets get one
	if base.modelsOf ~= d then
		base.folder:ClearAllChildren()
		base.models, base.modelsOf = {}, d
	end
	table.sort(d.pets, function(a, b)
		return C.petIncome(a) > C.petIncome(b)
	end)
	local c = base.pen.Position
	local mult = cashMult(d)
	local keep = {}
	for _, pet in ipairs(d.pets) do
		keep[pet] = true
	end
	for pet, m in pairs(base.models) do
		if not keep[pet] or not m.Parent then
			m:Destroy()
			base.models[pet] = nil
		end
	end
	for k, pet in ipairs(d.pets) do
		local old = base.models[pet]
		if old then
			old:SetAttribute("PenIdx", k)
			local root = old.PrimaryPart or old:FindFirstChildWhichIsA("BasePart", true)
			local tag = root and root:FindFirstChild("Tag")
			if tag then
				tag:Destroy()
			end
			label(old, pet, mult) -- the $/s can change (friends, rebirth...)
			continue
		end
		local col = (k - 1) % 3 + 1
		local row = math.floor((k - 1) / 3) + 1
		local s = (1.3 + 0.1 * pet.i + 0.15 * (pet.t - 1)) * C.zoneScale(pet.z) -- v160: bigger every zone
		local m = C.buildPet(pet, s, true)
		local px, pz = SLOT_X[col] or 0, SLOT_Z[row] or 0
		local placed = pet.px and math.abs(pet.px) <= base.pen.Size.X / 2 and math.abs(pet.pz) <= base.pen.Size.Z / 2
		if placed then -- v171: the spot the player chose
			px, pz = pet.px, pet.pz
		end
		m:PivotTo(CFrame.new(c.X + px, c.Y + 0.05 + 1.75 * s, c.Z + pz) * CFrame.Angles(0, math.pi, 0))
		m:SetAttribute("PenIdx", k)
		if placed then
			m:SetAttribute("Home", Vector3.new(c.X + px, c.Y, c.Z + pz))
		end
		label(m, pet, mult)
		m:SetAttribute("Phase", k * 0.7)
		m:SetAttribute("Kind", C.petDef(pet).kind)
		-- v143: the client lets the pet walk around the pen (centre of the pen floor + how high the pivot sits)
		m:SetAttribute("PenC", Vector3.new(c.X, c.Y + 0.05, c.Z))
		m:SetAttribute("Lift", 1.75 * s)
		m:SetAttribute("PenSize", base.pen.Size)
		m.Parent = base.folder
		CS:AddTag(m, "PenPet")
		base.models[pet] = m
	end
end

local function torsoOf(char)
	return char and (char:FindFirstChild("UpperTorso") or char:FindFirstChild("Torso"))
end

local function renderCarry(plr)
	local d = data[plr]
	local char = plr.Character
	local head = char and char:FindFirstChild("Head")
	if not d or not head then
		return
	end
	local old = char:FindFirstChild("CarryPets")
	if old then
		old:Destroy()
	end
	if true then
		return -- user: nothing on the back any more (pets and eggs live in the PETS / EGGS menus)
	end
	local folder = Instance.new("Folder")
	folder.Name = "CarryPets"
	-- pets pile up out of the basket on your back (or on your head with the old block basket)
	local torso = torsoOf(char)
	local back = char:FindFirstChild("BackBasket")
	local anchor, base = head, head.CFrame * CFrame.new(0, 2.9, 0)
	if back and torso then
		anchor, base = torso, torso.CFrame * CFrame.new(C.basketRim(d.basket + 1)) * CFrame.new(0, 0.8, 0)
	end
	for k, pet in ipairs(d.carry) do
		local m = C.buildPet(pet, 0.45, false)
		m:PivotTo(base * CFrame.new(0, (k - 1) * 1.25, 0))
		local w = Instance.new("WeldConstraint")
		w.Part0 = anchor
		w.Part1 = m.PrimaryPart
		w.Parent = m.PrimaryPart
		m.Parent = folder
	end
	folder.Parent = char
end

-- the basket you own hangs on your back: Blender mesh Basket_k (+ BasketNeon_k), welded to the torso
local function addBasket(plr, char)
	-- wait until the avatar has loaded: Roblox swaps the body parts then, and anything welded to the old ones disappears
	for _ = 1, 60 do
		local ok, loaded = pcall(function()
			return plr:HasAppearanceLoaded()
		end)
		if not ok or loaded or plr.Character ~= char then
			break
		end
		task.wait(0.1)
	end
	if plr.Character ~= char then
		return
	end
	task.wait(0.2)
	local head = char:WaitForChild("Head", 10)
	if not head then
		return
	end
	local torso = torsoOf(char)
	for _, p in ipairs(char:GetChildren()) do
		if p.Name == "Basket" or p.Name == "BackBasket" then
			p:Destroy()
		end
	end
	local d = data[plr]
	local k = d and (d.basket + 1) or 1
	local meta = RS:FindFirstChild("PropsMeta") and require(RS.PropsMeta)
	local function mesh(name, neon)
		local src, m = C.meshOf(name), meta and meta[name]
		if not (src and m and torso) then
			return nil
		end
		local p = src:Clone()
		p.Name = neon and "Neon" or "Body"
		p.Size = Vector3.new(m.size[1], m.size[2], m.size[3])
		p.CFrame = torso.CFrame * CFrame.new(m.centre[1], m.centre[2], m.centre[3]) * CFrame.Angles(0, C.PROP_YAW, 0)
		p.Color = Color3.new(1, 1, 1)
		p.Material = neon and Enum.Material.Neon or Enum.Material.SmoothPlastic
		p.Anchored = false
		p.CanCollide = false
		p.CanTouch = false
		p.CanQuery = false
		p.Massless = true
		p.CastShadow = not neon
		local w = Instance.new("WeldConstraint")
		w.Part0 = torso
		w.Part1 = p
		w.Parent = p
		return p
	end
	local body = mesh("Basket_" .. k, false)
	if not body then
		warn("[RainingEggs] back basket: no mesh Basket_" .. k, C.meshOf("Basket_" .. k) ~= nil, meta ~= nil and meta["Basket_" .. k] ~= nil, torso)
	end
	if body then
		local model = Instance.new("Model")
		model.Name = "BackBasket"
		body.Parent = model
		local neon = mesh("BasketNeon_" .. k, true)
		if neon then
			neon.Parent = model
		end
		model.Parent = char
		renderCarry(plr)
		return
	end
	-- the Blender baskets are not imported yet: the old block basket on the head
	local function piece(sx, sy, sz, y, col)
		local p = Instance.new("Part")
		p.Name = "Basket"
		p.Size = Vector3.new(sx, sy, sz)
		p.Color = col
		p.Material = Enum.Material.SmoothPlastic
		p.TopSurface = Enum.SurfaceType.Smooth
		p.BottomSurface = Enum.SurfaceType.Smooth
		p.CanCollide = false
		p.CanTouch = false
		p.CanQuery = false
		p.Massless = true
		p.CFrame = head.CFrame * CFrame.new(0, y, 0)
		local w = Instance.new("WeldConstraint")
		w.Part0 = head
		w.Part1 = p
		w.Parent = p
		p.Parent = char
	end
	piece(2.6, 0.9, 2.6, 1.35, Color3.fromRGB(190, 126, 60))
	piece(3.2, 0.35, 3.2, 1.95, Color3.fromRGB(222, 150, 66))
	piece(3.2, 0.2, 0.5, 2.2, Color3.fromRGB(240, 66, 66))
	renderCarry(plr)
end

-- 3 same pets of one tier become 1 pet of the next tier (equipped and stored pets together;
-- the new pet is equipped when one of the three was)
local function fuse(d)
	local all = {}
	for _, pet in ipairs(d.pets) do
		table.insert(all, { pet = pet, eq = true })
	end
	for _, pet in ipairs(d.stored) do
		table.insert(all, { pet = pet, eq = false })
	end
	local made = {}
	local again = true
	while again do
		again = false
		local groups = {}
		for k, e in ipairs(all) do
			local pet = e.pet
			if pet.t < #C.TIER then
				local key = pet.z .. "_" .. pet.i .. "_" .. pet.t .. "_" .. (pet.v or 1)
				groups[key] = groups[key] or {}
				table.insert(groups[key], k)
				if #groups[key] == C.FUSE then
					local idxs = groups[key]
					table.sort(idxs, function(a, b)
						return a > b
					end)
					local eq = false
					for _, k2 in ipairs(idxs) do
						eq = eq or all[k2].eq
						table.remove(all, k2)
					end
					local new = { z = pet.z, i = pet.i, t = pet.t + 1, v = pet.v }
					table.insert(all, { pet = new, eq = eq })
					table.insert(made, new)
					again = true
					break
				end
			end
		end
	end
	d.pets, d.stored = {}, {}
	for _, e in ipairs(all) do
		table.insert((e.eq and #d.pets < penMax(d)) and d.pets or d.stored, e.pet)
	end
	return made
end

-- carried pets come home: same pets fuse, empty pen places are filled with your best stored pets,
-- the rest wait in storage (PETS menu: tap to equip, EQUIP BEST); a full storage sells its weakest pets
local function deposit(plr)
	local d = data[plr]
	local n = #d.carry
	for _, pet in ipairs(d.carry) do
		table.insert(d.stored, pet)
	end
	d.carry = {}
	local made = C.AUTO_FUSE and fuse(d) or {} -- v143 (user): no automatic fusing into Gold any more
	byIncome(d.stored)
	-- v171 (user): new pets are NOT put into the pen automatically: they wait in the hotbar, the player places them
	local sold = 0
	while #d.stored > C.STORAGE_MAX do
		local pet = table.remove(d.stored) -- the weakest (sorted)
		sold = sold + C.petIncome(pet) * C.SELL_MULT
	end
	d.cash = d.cash + sold
	renderPen(plr)
	renderCarry(plr)
	sync(plr)
	if #made > 0 then
		say(plr, C.FUSE .. " pets fused into " .. C.petName(made[#made]) .. "!", "legend")
	elseif sold > 0 then
		say(plr, "Storage is full! Weakest pets sold for $" .. C.fmt(sold), "cash")
	elseif n > 0 and #d.pets >= penMax(d) then
		say(plr, "Pen is full! New pets wait in the bar below", "info")
	elseif n > 0 then
		say(plr, "New pet! Pick it in the bar below and place it in your pen", "info")
	end
end

-- PETS menu: tap a pet = equip / unequip it; EQUIP BEST = your C.PEN_MAX best pets go into the pen
local function equipPet(plr, i)
	local d = data[plr]
	local list, j = ownedAt(d, i)
	if not list then
		return
	end
	if list == d.pets then
		table.insert(d.stored, table.remove(d.pets, j))
		byIncome(d.stored)
	elseif #d.pets >= penMax(d) then
		say(plr, "Your pen is full (" .. penMax(d) .. ")! Unequip a pet first", "bad")
		return
	else
		table.insert(d.pets, table.remove(d.stored, j))
	end
	renderPen(plr)
	sync(plr)
end

local function equipBest(plr)
	local d = data[plr]
	local all = {}
	for _, pet in ipairs(d.pets) do
		table.insert(all, pet)
	end
	for _, pet in ipairs(d.stored) do
		table.insert(all, pet)
	end
	byIncome(all)
	d.pets, d.stored = {}, {}
	for k, pet in ipairs(all) do
		table.insert(k <= penMax(d) and d.pets or d.stored, pet)
	end
	renderPen(plr)
	sync(plr)
	say(plr, "Equipped your " .. #d.pets .. " best pets!", "good")
end

local function sellCarry(plr)
	local d = data[plr]
	if #d.carry == 0 then
		say(plr, "Catch eggs first, then sell the pets here", "info")
		return
	end
	local sum = 0
	for _, pet in ipairs(d.carry) do
		sum = sum + C.petIncome(pet) * C.SELL_MULT
	end
	d.carry = {}
	d.cash = d.cash + sum
	renderCarry(plr)
	sync(plr)
	say(plr, "Sold for $" .. C.fmt(sum), "sold")
end

-- ------------------------------------------------------------ upgrades (ProximityPrompts; the client writes the price on them)
local UP_NAME = { train = "Training", basket = "Basket", luck = "Luck", pen = "Pen" }
local function buy(plr, kind, part)
	local d = data[plr]
	if not d then
		return
	end
	if kind == "sell" then
		sellCarry(plr)
		return
	elseif kind == "index" then
		say(plr, "Open the INDEX button on the right side", "info")
		return
	end
	if kind == "train" and (not bases[d.base] or bases[d.base].tread ~= part) then
		say(plr, "This is not your base", "bad")
		sync(plr)
		return
	end
	local lv = d[kind]
	if lv >= C.MAX_LV[kind] then
		say(plr, UP_NAME[kind] .. " is MAX", "info")
		sync(plr) -- v190: undo the client's instant preview
		return
	end
	local cost = C.cost(kind, lv)
	if d.cash < cost then
		say(plr, "You need $" .. C.fmt(cost), "bad")
		sync(plr)
		return
	end
	d.cash = d.cash - cost
	d[kind] = lv + 1
	sync(plr)
	if kind == "basket" then
		if plr.Character then
			task.spawn(addBasket, plr, plr.Character)
		end
		say(plr, C.BASKETS[lv + 2].name .. "! Holds " .. C.basketMax(lv + 1) .. " pets", "buy")
		return
	end
	if kind == "pen" then
		say(plr, "Bigger pen! It holds " .. penMax(d) .. " pets now", "buy")
		return
	end
	if kind == "train" and TList and treadTier(lv + 1) ~= treadTier(lv) then
		say(plr, "Training level " .. (lv + 1) .. " - new treadmill: " .. TList[treadTier(lv + 1)].Id .. "!", "buy")
		return
	end
	say(plr, UP_NAME[kind] .. " level " .. (lv + 1) .. "!", "buy")
end

-- v162 (user: the upgrade button on the fence does nothing): the treadmill board also gets a ClickDetector (click and
-- phone tap, works even when an invisible part or a screen GUI swallows the SurfaceGui button). The SurfaceGui button,
-- the client ray fallback and this detector can all fire on one press -> one buy per 0.4 s.
local lastTrain = {}
buyTrain = function(plr)
	local d = data[plr]
	if not d or os.clock() - (lastTrain[plr] or 0) < 0.12 then -- v190: only collapses the 2-3 paths of one press
		return
	end
	lastTrain[plr] = os.clock()
	print("[treadmill] upgrade press from " .. plr.Name .. " (level " .. tostring(d.train) .. ", cash " .. math.floor(d.cash) .. ")")
	buy(plr, "train", bases[d.base] and bases[d.base].tread)
end
Players.PlayerRemoving:Connect(function(plr)
	lastTrain[plr] = nil
end)
for _, b in pairs(bases) do
	local sign = b.treadSign
	if sign then
		sign.CanQuery = true
		local cd = Instance.new("ClickDetector")
		cd.MaxActivationDistance = 45
		cd.Parent = sign
		cd.MouseClick:Connect(function(plr)
			local d = data[plr]
			print("[treadmill] board click from " .. plr.Name .. (d and bases[d.base] == b and "" or " (not his base)"))
			if d and bases[d.base] == b then
				buyTrain(plr)
			end
		end)
		-- v190 (user): no "E Upgrade" prompt - the button on the board is the way to upgrade
	end
end

local function prompt(part, kind, action)
	local pp = Instance.new("ProximityPrompt")
	pp.Name = "Upg"
	pp.ActionText = action
	pp.ObjectText = ""
	pp.HoldDuration = 0.25
	pp.MaxActivationDistance = 22
	pp.RequiresLineOfSight = false
	pp:SetAttribute("Kind", kind)
	pp.Parent = part
	CS:AddTag(pp, "UpgPrompt")
	pp.Triggered:Connect(function(plr)
		buy(plr, kind, part)
	end)
end

-- (no E prompt on the treadmill any more: the user removed it 19 Nov; training is upgraded from the UPGRADE menu)
local boards = {}
local shopPads = {} -- kind -> ShopPad part
for _, d in ipairs(Map:GetDescendants()) do
	if d.Name == "ShopPad" and d:IsA("BasePart") then
		-- shop zone: the client opens the shop menu while you stand on it (no prompt)
		local x = d.Position.X
		local kind = (x < -74 and "sell") or (x < 0 and "basket") or (x < 74 and "luck") or "index"
		d:SetAttribute("Shop", kind)
		shopPads[kind] = d
	elseif d.Name == "Leaderboard" and d:IsA("BasePart") then
		table.insert(boards, d)
	end
end

-- ------------------------------------------------------------ ZONE GATES
-- Every zone after the first has a see-through gate at its entrance with the price on it.
-- Walk into the gate with enough cash -> the cash is taken, the zone is yours forever (saved).
-- The gate parts are made here, so nothing has to be placed by hand in Studio:
--   Workspace > ZoneGates > Gate2 .. Gate10 > Gate (with PriceGui on both sides), WallLeft, WallRight, Blocker
-- Prices and looks: Config > C.ZONE_PRICE and C.GATE.
-- The gate is the same part for everybody; each player's own client hides the gates that player owns
-- (see "zone gates" in the client). The server still checks every step in the main loop below,
-- so a cheater who deletes the gate on their screen is sent back.
local G = C.GATE
local GateFolder = Instance.new("Folder")
GateFolder.Name = "ZoneGates"

local function gatePart(name, size, pos, col, transparency, parent)
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.CanCollide = true
	p.CanQuery = false -- the camera and the egg raycasts ignore it
	p.CastShadow = false
	p.Material = Enum.Material.SmoothPlastic
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Size = size
	p.CFrame = CFrame.new(pos)
	p.Color = col
	p.Transparency = transparency
	p.Parent = parent
	return p
end

-- the price text on one side of the gate
local function gateSign(part, face, zoneIndex)
	local zone = C.ZONES[zoneIndex]
	local sg = Instance.new("SurfaceGui")
	sg.Name = "PriceGui"
	sg.Face = face
	sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	sg.PixelsPerStud = 20
	sg.LightInfluence = 0
	-- one text line: name, top edge (0..1), height (0..1), text, colour
	local function line(name, y, h, str, col)
		local t = Instance.new("TextLabel")
		t.Name = name
		t.BackgroundTransparency = 1
		t.Size = UDim2.fromScale(0.9, h)
		t.Position = UDim2.fromScale(0.05, y)
		t.Font = Enum.Font.FredokaOne
		t.Text = str
		t.TextColor3 = col
		t.TextScaled = true
		local st = Instance.new("UIStroke")
		st.Thickness = 5
		st.Color = Color3.fromRGB(14, 20, 48)
		st.Parent = t
		t.Parent = sg
	end
	line("Top", 0.07, 0.15, G.textTop, Color3.fromRGB(255, 120, 120))
	line("ZoneName", 0.24, 0.2, zone.name, Color3.new(1, 1, 1))
	line("Price", 0.45, 0.32, "$" .. C.fmt(zone.price), Color3.fromRGB(255, 222, 60))
	line("Hint", 0.8, 0.12, G.textHint, Color3.fromRGB(225, 230, 250))
	sg.Parent = part
end

-- buy the zone behind a gate (called when a player touches the gate)
local function tryUnlock(plr, zoneIndex)
	local d = data[plr]
	if not d or zoneIndex <= d.unlocked then
		return -- already owned
	end
	local now = os.clock()
	if now - d.lastTouch < G.touchCooldown then
		return -- touching fires many times a second; answer only now and then
	end
	d.lastTouch = now
	if zoneIndex > d.unlocked + 1 then
		return -- an earlier zone must be bought first (no message)
	end
	local zone = C.ZONES[zoneIndex]
	if d.cash < zone.price then
		return -- not enough cash yet (no message; the gate itself shows cash / price)
	end
	d.cash = d.cash - zone.price -- take the money
	d.unlocked = zoneIndex -- open forever (saved with the rest of the data)
	sync(plr) -- the "Unlocked" attribute tells the client to fade the gate away
end

for zoneIndex = 2, C.TOTAL do
	if zoneIndex == C.NZ + 1 then
		continue -- the Cosmic Nest has no gate (the Golden Portal opens it)
	end
	local w2 = zoneIndex > C.NZ -- v119: world 2 gates stand up in space
	local z = w2 and C.w2Z0(zoneIndex) or (zoneIndex - 1) * C.ZONE_LEN -- the arch of zone n stands at z = (n - 1) * 140
	local gy = w2 and C.COSMIC.y or 0
	local col = Color3.fromRGB(C.ZONES[zoneIndex].eggCol[1], C.ZONES[zoneIndex].eggCol[2], C.ZONES[zoneIndex].eggCol[3])
	local model = Instance.new("Model")
	model.Name = "Gate" .. zoneIndex
	model:SetAttribute("Zone", zoneIndex)

	-- the glowing gate in the arch, with the price on both sides
	local gate = gatePart("Gate", Vector3.new(G.width, G.height, G.thick), Vector3.new(0, gy + G.height / 2, z), col, G.transparency, model)
	gate.Material = Enum.Material.Neon
	gateSign(gate, Enum.NormalId.Front, zoneIndex)
	gateSign(gate, Enum.NormalId.Back, zoneIndex)
	gate.Touched:Connect(function(hit)
		local plr = Players:GetPlayerFromCharacter(hit.Parent)
		if plr then
			tryUnlock(plr, zoneIndex)
		end
	end)

	-- glass walls left and right of the arch, and an invisible wall above everything
	local side = (G.wallWidth - G.width) / 2
	for _, sx in ipairs({ -1, 1 }) do
		local wall = gatePart(sx < 0 and "WallLeft" or "WallRight", Vector3.new(side, G.height, G.thick),
			Vector3.new(sx * (G.width / 2 + side / 2), gy + G.height / 2, z), col, G.wallTransparency, model)
		wall.CanTouch = false
		wall.Material = Enum.Material.Neon -- glows like the gate, so you see where the locked zone starts
	end
	gatePart("Blocker", Vector3.new(G.wallWidth, G.blockHeight, G.thick), Vector3.new(0, gy + G.height + G.blockHeight / 2, z), col, 1, model).CanTouch = false
	model.Parent = GateFolder
end
GateFolder.Parent = workspace

-- the big arch signs of the map still say "SPEED 500+": write the cash price there instead
do
	local newText = {}
	for i = 2, C.NZ do
		newText["SPEED " .. C.fmt(C.ZONES[i].req) .. "+"] = "COSTS $" .. C.fmt(C.ZONES[i].price)
	end
	for _, o in ipairs(Map:GetDescendants()) do
		if o:IsA("TextLabel") and newText[o.Text] then
			o.Text = newText[o.Text]
		end
	end
end

-- ============================================================ v171: HOTBAR - the player places pets in the pen himself
-- "place", i, x, z = put stored pet i (the hotbar shows the first 10 stored pets) at world x, z inside your pen
-- "pickup", k = take pen pet k (attribute PenIdx) back into the hotbar
local function placeOk(base, lx, lz)
	local hx, hz = base.pen.Size.X / 2 - 3, base.pen.Size.Z / 2 - 3
	if math.abs(lx) > hx or math.abs(lz) > hz then
		return false
	end
	return not (lx < -base.pen.Size.X / 2 + 12 and lz > base.pen.Size.Z / 2 - 18) -- the treadmill corner
end
local function num(v)
	return typeof(v) == "number" and v == v and math.abs(v) < 1e6
end
Action.OnServerEvent:Connect(function(plr, what, a)
	-- v182: the introduction tells the server which step the player reached (saved, so it never repeats)
	if what ~= "tut" then
		return
	end
	local d = data[plr]
	if d and typeof(a) == "number" and a == a and a >= (d.tut or 0) and a <= 99 then
		local before = d.tut or 0
		d.tut = math.floor(a)
		plr:SetAttribute("Tut", d.tut)
		if before < 99 and d.tut == 99 then -- v284 (user): finishing the introduction gives $5,000 (only once: Tut is saved)
			d.cash = d.cash + C.TUT_REWARD
			plr:SetAttribute("Cash", d.cash)
			Bought:FireClient(plr, "$" .. C.comma(C.TUT_REWARD), "TUTORIAL COMPLETE!")
		end
	end
end)
Action.OnServerEvent:Connect(function(plr, what, a, x, z)
	if what ~= "place" and what ~= "pickup" then
		return
	end
	local d = data[plr]
	local base = d and bases[d.base]
	if not base or not base.pen then
		return
	end
	local now = os.clock()
	if now - (d.placeT or 0) < 0.2 then
		return
	end
	d.placeT = now
	if what == "place" then
		if not (num(a) and num(x) and num(z)) or a % 1 ~= 0 then
			return
		end
		local pet = d.stored[a]
		if not pet then
			return
		end
		if #d.pets >= penMax(d) then
			say(plr, "Your pen is full (" .. penMax(d) .. ")! Pick a pet up first", "bad")
			return
		end
		local c = base.pen.Position
		local lx, lz = x - c.X, z - c.Z
		if not placeOk(base, lx, lz) then
			say(plr, "Place it inside your pen", "bad")
			return
		end
		table.remove(d.stored, a)
		pet.px, pet.pz = math.floor(lx * 10 + 0.5) / 10, math.floor(lz * 10 + 0.5) / 10
		table.insert(d.pets, pet)
	else
		if not num(a) or a % 1 ~= 0 or not d.pets[a] then
			return
		end
		local pet = table.remove(d.pets, a)
		pet.px, pet.pz = nil, nil
		table.insert(d.stored, 1, pet)
		byIncome(d.stored)
	end
	renderPen(plr)
	sync(plr)
end)

Action.OnServerEvent:Connect(function(plr, what, kind)
	local d = data[plr]
	if not d then
		return
	end
	if what == "equip" or what == "equipbest" then
		-- PETS menu (v119): "equip", i = equip / unequip pet i of PetList; "equipbest" = the best pets into the pen. Anywhere.
		local now = os.clock()
		if now - (d.equipT or 0) < 0.2 then
			return -- the pen models are rebuilt each time: no spamming
		end
		d.equipT = now
		if what == "equipbest" then
			equipBest(plr)
		elseif typeof(kind) == "number" and kind == kind and kind % 1 == 0 then
			equipPet(plr, kind)
		end
		return
	end
	if what == "deletepet" then
		-- v254 PETS menu delete button (asks twice on the client): pet i of PetList is removed, no money
		if typeof(kind) ~= "number" or kind ~= kind or kind % 1 ~= 0 then
			return
		end
		local list, j = ownedAt(d, kind)
		if not list or not list[j] then
			return
		end
		local pet = table.remove(list, j)
		renderPen(plr)
		sync(plr)
		say(plr, "Deleted " .. C.petName(pet), "sold")
		return
	end
	if what == "sellpets" then
		-- the SELL PETS menu: "c3,c1,p2" = pets 3 and 1 of the basket and pet 2 of the pen; only near the SELL shop
		local pad = shopPads.sell
		local hrp = plr.Character and plr.Character:FindFirstChild("HumanoidRootPart")
		if not pad or not hrp or typeof(kind) ~= "string" or #kind > 2000 then
			return
		end
		local off = hrp.Position - pad.Position
		if Vector3.new(off.X, 0, off.Z).Magnitude > math.max(pad.Size.Y, pad.Size.Z) / 2 + 10 then
			return
		end
		local pick = { c = {}, p = {} }
		for _, k in ipairs(string.split(kind, ",")) do
			local where, i = string.match(k, "^([cp])(%d+)$")
			if where then
				pick[where][tonumber(i)] = true
			end
		end
		local sum, n, last = 0, 0, nil
		for where, set in pairs(pick) do
			local idx = {}
			for i in pairs(set) do
				table.insert(idx, i)
			end
			table.sort(idx, function(a, b)
				return a > b -- highest first: stored pets go before equipped ones, so the other indices stay valid
			end)
			for _, i in ipairs(idx) do
				local list, j = d.carry, i
				if where == "p" then
					list, j = ownedAt(d, i)
				end
				if list and list[j] then
					local pet = table.remove(list, j)
					sum = sum + C.petIncome(pet) * C.SELL_MULT
					n, last = n + 1, pet
				end
			end
		end
		if n == 0 then
			return
		end
		d.cash = d.cash + sum
		renderPen(plr)
		renderCarry(plr)
		sync(plr)
		say(plr, (n == 1 and ("Sold " .. C.petName(last)) or ("Sold " .. n .. " pets")) .. " for $" .. C.fmt(sum), "sold")
		return
	end
	if what == "sellpet" then
		-- the SELL shop list: "c<i>" = pet i in the basket, "p<i>" = pet i in the pen; only near the SELL shop
		local pad = shopPads.sell
		local hrp = plr.Character and plr.Character:FindFirstChild("HumanoidRootPart")
		if not pad or not hrp or typeof(kind) ~= "string" then
			return
		end
		local off = hrp.Position - pad.Position
		if Vector3.new(off.X, 0, off.Z).Magnitude > math.max(pad.Size.Y, pad.Size.Z) / 2 + 8 then
			return
		end
		local where, i = string.match(kind, "^([cp])(%d+)$")
		i = tonumber(i)
		local list, j = nil, i
		if where == "c" then
			list = d.carry
		elseif where == "p" and i then
			list, j = ownedAt(d, i)
		end
		local pet = list and list[j]
		if not pet then
			return
		end
		table.remove(list, j)
		local price = C.petIncome(pet) * C.SELL_MULT
		d.cash = d.cash + price
		if where == "p" then
			renderPen(plr)
		else
			renderCarry(plr)
		end
		sync(plr)
		say(plr, "Sold " .. C.petName(pet) .. " for $" .. C.fmt(price), "sold")
		return
	end
	if what == "shop" then
		-- buy from the shop menu: only while standing near that shop's zone
		local pad = typeof(kind) == "string" and shopPads[kind]
		local hrp = plr.Character and plr.Character:FindFirstChild("HumanoidRootPart")
		if pad and hrp and (kind == "basket" or kind == "luck" or kind == "sell") then
			local d = hrp.Position - pad.Position
			if Vector3.new(d.X, 0, d.Z).Magnitude < math.max(pad.Size.Y, pad.Size.Z) / 2 + 8 then
				buy(plr, kind, pad)
			end
		end
		return
	end
	if what ~= "rebirth" then
		return
	end
	local need = C.rebirthNeed(d.rebirth)
	if need == math.huge then
		say(plr, "You reached the MAX rebirth!", "info")
		return
	elseif d.cash < need then -- v244 (user): every rebirth has its own cash price (small to big)
		say(plr, "Rebirth costs $" .. C.fmt(need), "bad")
		return
	end
	d.rebirth = d.rebirth + 1
	d.cash, d.speed, d.train = 0, 0, 0
	sync(plr)
	renderPen(plr)
	Notice:FireAllClients(plr.DisplayName .. " reached REBIRTH " .. d.rebirth .. "!", "legend")
end)

-- ------------------------------------------------------------ leaderboards on the plaza (players on this server)
local boardRows = {}
local function buildBoard(part, title, col)
	for _, ch in ipairs(part:GetChildren()) do
		if ch:IsA("SurfaceGui") then
			ch:Destroy()
		end
	end
	local sg = Instance.new("SurfaceGui")
	sg.Name = "Board"
	sg.Face = Enum.NormalId.Front
	sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	sg.PixelsPerStud = 20
	sg.LightInfluence = 0
	local bg = Instance.new("Frame")
	bg.Size = UDim2.fromScale(1, 1)
	bg.BackgroundColor3 = col
	bg.BorderSizePixel = 0
	local g = Instance.new("UIGradient")
	g.Rotation = 90
	g.Color = ColorSequence.new(Color3.new(1, 1, 1), Color3.fromRGB(120, 120, 140))
	g.Parent = bg
	bg.Parent = sg
	local rows = {}
	local function line(y, h, text, color)
		local t = Instance.new("TextLabel")
		t.BackgroundTransparency = 1
		t.Size = UDim2.fromScale(0.92, h)
		t.Position = UDim2.fromScale(0.04, y)
		t.Font = Enum.Font.FredokaOne
		t.Text = text
		t.TextColor3 = color
		t.TextScaled = true
		t.TextXAlignment = Enum.TextXAlignment.Left
		local st = Instance.new("UIStroke")
		st.Thickness = 3
		st.Color = Color3.fromRGB(14, 20, 48)
		st.Parent = t
		t.Parent = bg
		return t
	end
	local head = line(0.03, 0.2, title, Color3.new(1, 1, 1))
	head.TextXAlignment = Enum.TextXAlignment.Center
	for i = 1, 5 do
		rows[i] = line(0.25 + (i - 1) * 0.145, 0.125, "", i == 1 and Color3.fromRGB(255, 222, 60) or Color3.new(1, 1, 1))
	end
	sg.Parent = part
	return rows
end
for _, b in ipairs(boards) do
	if b.Position.X < 0 then
		boardRows.luck = buildBoard(b, "TOP LUCK", Color3.fromRGB(160, 100, 250))
	else
		boardRows.catch = buildBoard(b, "TOP CATCHERS", Color3.fromRGB(60, 190, 230))
	end
end

task.spawn(function()
	while true do
		task.wait(5)
		local list = {}
		for plr, d in pairs(data) do
			table.insert(list, { name = plr.DisplayName, caught = d.caught, odds = d.bestOdds, pet = d.bestName })
		end
		if boardRows.catch then
			table.sort(list, function(a, b)
				return a.caught > b.caught
			end)
			for i = 1, 5 do
				local r = list[i]
				boardRows.catch[i].Text = r and (i .. ". " .. r.name .. "  -  " .. C.fmt(r.caught) .. " eggs") or ""
			end
		end
		if boardRows.luck then
			table.sort(list, function(a, b)
				return a.odds > b.odds
			end)
			for i = 1, 5 do
				local r = list[i]
				boardRows.luck[i].Text = (r and r.odds > 0) and (i .. ". " .. r.name .. "  -  " .. r.pet .. " (1 in " .. C.comma(r.odds) .. ")") or ""
			end
		end
	end
end)

-- ------------------------------------------------------------ join / leave / save
local function load(plr)
	local saved
	if store then
		pcall(function()
			saved = store:GetAsync("u" .. plr.UserId)
		end)
	end
	saved = type(saved) == "table" and saved or {}
	-- equipped pets (saved.pets) and stored pets (saved.stored, v119); an old pen bigger than C.PEN_MAX keeps
	-- its extra pets in storage instead of losing them
	local pets, stored = {}, {}
	local penLv = math.clamp(math.floor(tonumber(saved.pen) or 0), 0, C.MAX_LV.pen)
	local function readPets(list, into)
		for _, pet in ipairs(type(list) == "table" and list or {}) do
			local t = type(pet) == "table" and (tonumber(pet.t) or 1)
			if t and C.ZONES[pet.z] and C.ZONES[pet.z].pets[pet.i] and C.TIER[t] then
				local v = math.clamp(math.floor(tonumber(pet.v) or 1), 1, C.variantCount(pet.z, pet.i))
				table.insert((into == pets and #pets < C.PEN_MAX + penLv) and pets or stored, { z = pet.z, i = pet.i, t = t, v = v > 1 and v or nil, px = tonumber(pet.px), pz = tonumber(pet.pz) })
			end
		end
	end
	readPets(saved.pets, pets)
	readPets(saved.stored, stored)
	byIncome(stored)
	local index = {}
	for _, key in ipairs(type(saved.index) == "table" and saved.index or {}) do
		index[tostring(key)] = true
	end
	for _, list in ipairs({ pets, stored }) do
		for _, pet in ipairs(list) do
			index[C.petKey(pet)] = true
		end
	end
	local bag = {}
	for _, egg in ipairs(type(saved.eggs) == "table" and saved.eggs or {}) do
		if type(egg) == "table" and C.ZONES[tonumber(egg.z) or 0] then
			table.insert(bag, { z = tonumber(egg.z), kind = tostring(egg.kind or "normal"), luck = tonumber(egg.luck) or 1, tier = tonumber(egg.tier), force = tonumber(egg.force) })
		end
	end
	local d = {
		cash = tonumber(saved.cash) or 0,
		speed = tonumber(saved.speed) or 0,
		train = tonumber(saved.train) or 0,
		basket = tonumber(saved.basket) or 0,
		luck = tonumber(saved.luck) or 0,
		pen = penLv, -- v232: pen space level (optional save key)
		rebirth = tonumber(saved.rebirth) or 0,
		caught = tonumber(saved.caught) or 0,
		bestOdds = tonumber(saved.bestOdds) or 0,
		bestName = tostring(saved.bestName or ""),
		pets = pets,
		stored = stored,
		index = index,
		carry = {},
		bag = bag, -- caught eggs not hatched yet: { z, kind, luck } (luck = rolled with the luck of the moment it was caught)
		combo = 0,
		comboT = 0,
		slowUntil = 0,
		zone = 0,
		lastGate = 0,
		lastTouch = 0,
		zonesDone = 0,
		unlocked = 1,
		passes = {},
		dailyDay = tonumber(saved.dailyDay) or 0, -- last claimed day of the streak (1..7)
		dailyLast = tonumber(saved.dailyLast) or 0, -- os.time() of the last claim
		gift = saved.gift == true or (tonumber(saved.caught) or 0) > 0, -- v150: welcome egg already given (old players: yes)
		friends = 0,
		tut = tonumber(saved.tut) or ((tonumber(saved.caught) or 0) > 0 and 99 or 0), -- v182: introduction step (99 = done)
		altar = {}, -- zones whose egg is on its altar in the Golden Nest (all 10 = the golden egg sinks, the portal opens)
	}
	for _, z in ipairs(type(saved.altar) == "table" and saved.altar or {}) do
		if C.ZONES[tonumber(z) or 0] then
			d.altar[tonumber(z)] = true
		end
	end
	-- zones bought with cash. Old saves (from when gates needed speed) keep the zones their speed had opened.
	local unlocked = tonumber(saved.unlocked)
	if not unlocked then
		unlocked = 1
		for i = 2, C.NZ do
			if d.speed >= C.ZONES[i].req then
				unlocked = i
			else
				break
			end
		end
	end
	d.unlocked = math.clamp(math.floor(unlocked), 1, C.TOTAL)
	if C.TEST_TUTORIAL and game:GetService("RunService"):IsStudio() then
		d.gift, d.tut = false, 0 -- v182: Studio test of the introduction
	end
	if C.TEST_ALL_ZONES_FREE and game:GetService("RunService"):IsStudio() then
		-- Studio test: every zone open for free (Config C.TEST_ALL_ZONES_FREE); v226 (user): world 2 too - all 20 zones and
		-- the Golden Portal open (all 10 altars filled)
		d.unlocked = C.TOTAL
		for z = 1, C.NZ do
			d.altar[z] = true
		end
	end
	d.zonesDone = zonesDone(d)
	return d
end

local function altarList(d)
	local t = {}
	for z in pairs(d.altar or {}) do
		table.insert(t, z)
	end
	table.sort(t)
	return t
end

local function save(plr)
	local d = data[plr]
	if not d or not store then
		return
	end
	local keys = {}
	for key in pairs(d.index) do
		table.insert(keys, key)
	end
	pcall(function()
		store:SetAsync("u" .. plr.UserId, {
			cash = d.cash, speed = d.speed, train = d.train, basket = d.basket, luck = d.luck, pen = d.pen, rebirth = d.rebirth,
			caught = d.caught, bestOdds = d.bestOdds, bestName = d.bestName, pets = d.pets, stored = d.stored, index = keys,
			unlocked = d.unlocked, dailyDay = d.dailyDay, dailyLast = d.dailyLast, eggs = d.bag, altar = altarList(d), gift = d.gift, tut = d.tut,
		})
	end)
end

local function onPlayer(plr)
	local ls = Instance.new("Folder")
	ls.Name = "leaderstats"
	for _, n in ipairs({ "Cash", "Speed", "Rebirths" }) do
		local v = Instance.new("NumberValue")
		v.Name = n
		v.Parent = ls
	end
	ls.Parent = plr

	local d = load(plr)
	if not plr.Parent then
		return
	end
	for i = 1, 8 do
		if bases[i] and not bases[i].owner then
			bases[i].owner = plr
			bases[i].shownInc = nil
			d.base = i
			break
		end
	end
	data[plr] = d
	plr:SetAttribute("Base", d.base or 0)
	sync(plr)
	syncIndex(plr)
	renderPen(plr)

	plr.CharacterAdded:Connect(function(char)
		task.spawn(addBasket, plr, char)
	end)
	pcall(function()
		plr.CharacterAppearanceLoaded:Connect(function(char)
			task.spawn(addBasket, plr, char) -- again once the avatar is in (body parts were replaced)
		end)
	end)
	if plr.Character then
		task.spawn(addBasket, plr, plr.Character)
	end
end

Players.PlayerAdded:Connect(onPlayer)
for _, plr in ipairs(Players:GetPlayers()) do
	task.spawn(onPlayer, plr)
end

Players.PlayerRemoving:Connect(function(plr)
	save(plr)
	local d = data[plr]
	if d and bases[d.base] then
		bases[d.base].owner = nil
		setTreadmill(bases[d.base], 0)
		setTreadSign(bases[d.base], nil)
		bases[d.base].folder:ClearAllChildren()
		bases[d.base].models, bases[d.base].modelsOf = {}, nil
		setSign(bases[d.base], "EMPTY")
	end
	data[plr] = nil
end)

game:BindToClose(function()
	for _, plr in ipairs(Players:GetPlayers()) do
		save(plr)
	end
end)

task.spawn(function()
	while true do
		task.wait(90)
		for plr in pairs(data) do
			save(plr)
		end
	end
end)

-- ------------------------------------------------------------ eggs
local eggs = {}
local nextId = 0
local storm = false
local rayParams = RaycastParams.new()
rayParams.RespectCanCollide = true

local function spawnEgg(zoneIndex, near, forced)
	local z0 = (zoneIndex - 1) * C.ZONE_LEN
	local CO = C.COSMIC
	if zoneIndex > C.NZ then -- v119 world 2: eggs fall slowly onto the floating zone
		local w0 = C.w2Z0(zoneIndex)
		for _ = 1, 6 do
			local x, z = (math.random() * 2 - 1) * CO.eggX, w0 + 10 + math.random() * (C.ZONE_LEN - 20)
			if near and math.random() < 0.6 then
				local a, r = math.random() * math.pi * 2, 10 + math.random() * 35
				x, z = near.X + math.cos(a) * r, near.Z + math.sin(a) * r
			end
			x = math.clamp(x, -CO.eggX, CO.eggX)
			z = math.clamp(z, w0 + 10, w0 + C.ZONE_LEN - 10)
			local y0 = CO.y + CO.eggHeight
			local hit = workspace:Raycast(Vector3.new(x, y0, z), Vector3.new(0, -CO.eggHeight - 40, 0), rayParams)
			if hit and hit.Position.Y > CO.y - 25 then
				nextId = nextId + 1
				local id = nextId
				local kind, fall, linger = forced or "normal", CO.fall, 0
				if kind == "storm" then
					fall, linger = fall * 1.4, C.STORM_EGG_LINGER
				elseif math.random() < C.GOLDEN_CHANCE * (eventKey() == "gold" and C.EVENT_GOLD_CHANCE or 1) then
					kind, fall = "golden", fall * 1.2
				end
				eggs[id] = { x = x, z = z, y0 = y0, gy = hit.Position.Y, fall = fall, linger = linger, t0 = os.clock(), zone = zoneIndex, kind = kind }
				EggSpawn:FireAllClients(id, x, z, y0, hit.Position.Y, fall, zoneIndex, kind, linger)
				task.delay(fall + linger + 0.8, function()
					eggs[id] = nil
				end)
				return true
			end
		end
		return false
	end
	for _ = 1, 5 do
		local x, z
		if near and (forced or math.random() < 0.65) then
			local a, r = math.random() * math.pi * 2, 12 + math.random() * 45
			x, z = near.X + math.cos(a) * r, near.Z + math.sin(a) * r
		else
			x, z = (math.random() * 2 - 1) * C.EGG_X, z0 + 10 + math.random() * (C.ZONE_LEN - 20)
		end
		x = math.clamp(x, -C.EGG_X, C.EGG_X)
		z = math.clamp(z, z0 + 10, z0 + C.ZONE_LEN - 10)
		local hit = workspace:Raycast(Vector3.new(x, C.EGG_Y, z), Vector3.new(0, -C.EGG_Y - 30, 0), rayParams)
		if hit and hit.Position.Y < 8 then
			nextId = nextId + 1
			local id = nextId
			local kind, fall, linger = forced or "normal", C.fallTime(zoneIndex), 0
			if kind == "storm" then
				fall, linger = fall * 1.7, C.STORM_EGG_LINGER
			else
				local r = math.random()
				local gc = C.GOLDEN_CHANCE * (eventKey() == "gold" and C.EVENT_GOLD_CHANCE or 1)
				if r < gc then
					kind, fall = "golden", fall * 1.35
				elseif r < gc + C.ROTTEN_CHANCE then
					kind = "rotten"
				end
			end
			eggs[id] = { x = x, z = z, y0 = C.EGG_Y, gy = hit.Position.Y, fall = fall, linger = linger, t0 = os.clock(), zone = zoneIndex, kind = kind }
			EggSpawn:FireAllClients(id, x, z, C.EGG_Y, hit.Position.Y, fall, zoneIndex, kind, linger)
			task.delay(fall + linger + 0.8, function()
				eggs[id] = nil
			end)
			return true
		end
	end
	return false
end

local function roll(luck)
	for i = #C.RARITY, 2, -1 do
		if math.random() < math.min(luck / C.RARITY[i].odds, 0.9) then
			return i
		end
	end
	return 1
end

Catch.OnServerEvent:Connect(function(plr, id)
	local e = type(id) == "number" and eggs[id]
	local d = data[plr]
	local char = plr.Character
	local hrp = char and char:FindFirstChild("HumanoidRootPart")
	if not e or e.done or not d or not hrp then
		return
	end
	local now = os.clock()
	local t = now - e.t0
	local p = hrp.Position
	local dx, dz = p.X - e.x, p.Z - e.z
	local reach = C.basketRadius(d.basket) + 8
	local eggY = e.y0 + (e.gy - e.y0) * math.clamp(t / e.fall, 0, 1)
	if t > e.fall + e.linger + 0.6 or dx * dx + dz * dz > reach * reach or eggY > p.Y + 16 then
		return
	end

	if e.kind == "rotten" then
		e.done = true
		d.slowUntil = now + C.ROTTEN_SLOW
		d.combo = 0
		EggGone:FireAllClients(id, plr.UserId, e.kind)
		sync(plr)
		say(plr, "Yuck, a rotten egg! You are slow for " .. C.ROTTEN_SLOW .. " seconds", "bad")
		return
	end
	if #d.carry + #d.bag >= carryMax(d) then
		say(plr, "Basket is full! Hatch your eggs or run to your base", "bad")
		return
	end
	e.done = true
	if now - d.comboT > C.COMBO_TIME then
		d.combo = 0
	end
	d.combo = d.combo + 1
	d.comboT = now

	-- the luck is saved with the egg now (combo, storm, golden...), the pet is rolled when the player presses HATCH EGGS
	local ev = eventKey()
	local luck = C.luck(d.luck) * C.comboLuck(d.combo) * (storm and C.STORM_LUCK or 1) * (d.passes.luck2 and 2 or 1) * (ev == "luck" and 2 or 1) * (1 + C.traitBonus(d.pets).luck)
	local tier = nil
	if e.kind == "golden" then
		luck = luck * C.GOLDEN_LUCK
	elseif e.kind == "storm" then
		luck = luck * C.STORM_EGG_LUCK
	end
	table.insert(d.bag, { z = e.zone, kind = e.kind, luck = luck, tier = tier })
	EggGone:FireAllClients(id, plr.UserId, e.kind)
	-- v190 (user): no more violet "X caught the STORM EGG!" message
	renderCarry(plr)
	sync(plr)
end)

-- HATCH EGGS button: every egg in the basket hatches; the pets stay in the basket until the player walks home
local function hatchBag(plr, only, limit)
	local d = data[plr]
	if not d or #d.bag == 0 then
		return
	end
	local bag, keep = {}, {}
	for _, egg in ipairs(d.bag) do
		if (type(only) ~= "string" or egg.z .. "_" .. egg.kind == only) and (not limit or #bag < limit) then
			table.insert(bag, egg)
		else
			table.insert(keep, egg)
		end
	end
	d.bag = keep
	for _, egg in ipairs(bag) do
		local royal = egg.kind == "royal" and C.rollRoyal() or nil -- v262: the Royal Egg gives one of the 6 royal pets
		local idx = royal and C.ROYAL_PETS[royal].i or egg.force or roll(egg.luck) -- v182: the welcome egg has its rarity fixed
		-- v152: the coat (normal / Gold / Rainbow) is rolled at hatch: C.TIER_ODDS by egg kind
		local pet = { z = egg.z, i = idx, t = math.clamp(math.floor(egg.tier or C.rollTier(egg.kind, eventKey() == "rainbow")), 1, #C.TIER) }
		pet.v = royal and (100 + royal) or rollVariant(pet, d)
		if royal and C.ROYAL_PETS[royal].secret then
			Notice:FireAllClients(plr.DisplayName .. " hatched the SECRET King Lion from a Royal Egg!", "legend")
		end
		local def = C.petDef(pet)
		local odds = C.RARITY[idx].odds
		table.insert(d.carry, pet)
		d.caught = d.caught + 1
		if odds > d.bestOdds then
			d.bestOdds, d.bestName = odds, def.name
		end
		local key = C.petKey(pet)
		local isNew = not d.index[key]
		if isNew then
			d.index[key] = true
			local before = d.zonesDone
			d.zonesDone = zonesDone(d)
			syncIndex(plr)
			if d.zonesDone > before then
				say(plr, C.ZONES[egg.z].name .. " index complete! +" .. math.floor(C.INDEX_BONUS * 100) .. "% cash forever", "legend")
				renderPen(plr)
			end
		end
		Hatch:FireClient(plr, pet, egg.kind, isNew, 1)
		if idx == #C.RARITY then
			Notice:FireAllClients(plr.DisplayName .. " hatched a LEGENDARY " .. def.name .. "! (1 in " .. C.comma(odds) .. ")", "legend")
		end
	end
	-- v188 (user: the pet showed up in the bar only back at the pen): hatched pets go straight into your pets / hotbar
	deposit(plr)
end

local function occupied()
	local inZone = {}
	for plr, d in pairs(data) do
		local hrp = plr.Character and plr.Character:FindFirstChild("HumanoidRootPart")
		if hrp and d.zone >= 1 then
			inZone[d.zone] = inZone[d.zone] or {}
			table.insert(inZone[d.zone], hrp.Position)
		end
	end
	return inZone
end

-- egg rain: only in zones where somebody is
task.spawn(function()
	local acc = {}
	while true do
		task.wait(0.5)
		for zoneIndex, list in pairs(occupied()) do
			acc[zoneIndex] = (acc[zoneIndex] or 0) + 0.5 * (1.2 + 0.7 * #list) * (storm and C.STORM_RATE or 1)
			while acc[zoneIndex] >= 1 do
				acc[zoneIndex] = acc[zoneIndex] - 1
				spawnEgg(zoneIndex, list[math.random(#list)])
			end
		end
	end
end)

-- storm event: the clients read StormNext / StormEnd (server time) from workspace
task.spawn(function()
	local nextAt = workspace:GetServerTimeNow() + math.random(C.STORM_FIRST[1], C.STORM_FIRST[2]) -- random: nobody knows when
	local endAt, warned = 0, false
	local bigEggs = {}
	workspace:SetAttribute("StormNext", nextAt)
	workspace:SetAttribute("StormEnd", 0)
	while true do
		task.wait(1)
		local now = workspace:GetServerTimeNow()
		if not storm then
			-- v208 (user): never an EGG STORM while a BIG EGG is out - the storm waits until the big egg is gone
			-- v244 (user: never both at once): a big egg out -> the storm stays at least 4 minutes away (no warning yet)
			if workspace:GetAttribute("BigEggActive") and now >= nextAt - 240 then
				nextAt = now + 240
				warned = false
				workspace:SetAttribute("StormNext", nextAt)
			end
			if not warned and now >= nextAt - 10 then
				warned = true
				Notice:FireAllClients("EGG STORM in 10 seconds! Run to a zone!", "storm")
			end
			if now >= nextAt then
				storm = true
				endAt = now + C.STORM_LEN
				bigEggs = { now + 6, now + 24 }
				workspace:SetAttribute("StormEnd", endAt)
				Notice:FireAllClients("EGG STORM! More eggs and x" .. C.STORM_LUCK .. " luck", "storm")
			end
		else
			if bigEggs[1] and now >= bigEggs[1] then
				table.remove(bigEggs, 1)
				for zoneIndex, list in pairs(occupied()) do
					if spawnEgg(zoneIndex, list[math.random(#list)], "storm") then
						Notice:FireAllClients("A giant STORM EGG is falling in " .. C.ZONES[zoneIndex].name .. "!", "storm")
					end
				end
			end
			if now >= endAt then
				storm = false
				warned = false
				nextAt = now + math.random(C.STORM_EVERY[1], C.STORM_EVERY[2]) / (eventKey() == "storm" and 2 or 1)
				workspace:SetAttribute("StormNext", nextAt)
				workspace:SetAttribute("StormEnd", 0)
			end
		end
	end
end)

-- ------------------------------------------------------------ main loop: gates, pen, treadmill, walk speed
task.spawn(function()
	while true do
		task.wait(0.25)
		local now = os.clock()
		for plr, d in pairs(data) do
			local char = plr.Character
			local hrp = char and char:FindFirstChild("HumanoidRootPart")
			local hum = char and char:FindFirstChildOfClass("Humanoid")
			if hrp and hum and hum.Health > 0 then
				local p = hrp.Position
				local zi = p.Z >= 0 and math.min(math.floor(p.Z / C.ZONE_LEN) + 1, C.NZ) or 0
				-- v119 world 2: everything high above the map (only through the Golden Portal)
				local CO = C.COSMIC
				local opened = #altarList(d) >= C.NZ
				if p.Y > CO.y - 400 then
					zi = C.w2Zone(p.Z)
					local function put(x, y, z)
						hrp.CFrame = CFrame.new(x, y, z)
						hrp.AssemblyLinearVelocity = Vector3.zero
					end
					if not opened then -- no way in without the portal
						put(CO.back[1], CO.back[2], CO.back[3])
						zi = C.NZ
					else
						if d.unlocked < CO.first then
							d.unlocked = CO.first -- the Cosmic Nest is free once the portal is open
							sync(plr)
						end
						-- v131: only when you walk THROUGH the exit portal (cross its plane inside the frame), not next to it
						local side = p.Z < CO.exit[3] and -1 or 1
						local crossed = d.exitSide ~= nil and side ~= d.exitSide
						d.exitSide = side
						if crossed and math.abs(p.X - CO.exit[1]) < CO.exit[4] and p.Y < CO.exit[2] + 20 then
							put(CO.back[1], CO.back[2], CO.back[3]) -- exit portal: back to the Golden Nest
							zi = C.NZ
						elseif zi > d.unlocked then -- a world 2 zone this player did not buy
							put(p.X, CO.y + 4, C.w2Z0(d.unlocked) + C.ZONE_LEN - 8)
							zi = d.unlocked
						elseif p.Y < CO.y - 40 then -- fell off: back to the start of this zone
							put(0, CO.y + 6, math.max(C.w2Z0(zi) + 12, CO.spawn[3]))
						end
					end
				elseif zi == C.NZ and opened and p.Y < CO.portal[2] + 26 and math.abs(p.X - CO.portal[1]) < CO.portal[4]
					and math.abs(p.Z - CO.portal[3]) < 4 then -- v131: inside the portal (its plane), not just next to it
					hrp.CFrame = CFrame.new(CO.spawn[1], CO.spawn[2], CO.spawn[3]) -- into the Golden Portal
					hrp.AssemblyLinearVelocity = Vector3.zero
					zi = CO.first
					if not d.cosmicSeen then
						d.cosmicSeen = true
						-- v222 (user): no "entered the COSMIC NEST" message / sound
					end
				end
				if zi > 1 and zi <= C.NZ then
					-- safety net behind the gates: a player standing in a zone they did not buy is put back
					local allowed = d.unlocked
					if zi > allowed then
						hrp.CFrame = hrp.CFrame - p + Vector3.new(p.X, p.Y + 1, allowed * C.ZONE_LEN - 8)
						hrp.AssemblyLinearVelocity = Vector3.zero
						zi = allowed
					end
				end
				d.zone = zi

				if d.combo > 0 and now - d.comboT > C.COMBO_TIME then
					d.combo = 0
					sync(plr)
				end

				local base = bases[d.base]
				if base then
					if base.pen and #d.carry > 0 then
						local c = base.pen.Position
						if math.abs(p.X - c.X) < base.pen.Size.X / 2 and math.abs(p.Z - c.Z) < base.pen.Size.Z / 2 then
							deposit(plr)
						end
					end
					if base.tread then
						local c = base.tread.Position
						if math.abs(p.X - c.X) < 3.5 and math.abs(p.Z - c.Z) < 7 and p.Y < c.Y + 9 then
							d.speed = d.speed + math.floor(C.trainPower(d.train) * C.rebirthMult(d.rebirth))
							sync(plr)
						end
					end
				end
				hum.WalkSpeed = C.walkSpeed(d.speed) * (1 + C.traitBonus(d.pets).speed) * (now < d.slowUntil and C.ROTTEN_FACTOR or 1) * (now < (d.stunUntil or 0) and 0.15 or 1)
			end
		end
	end
end)

-- pets earn cash every second
task.spawn(function()
	while true do
		task.wait(1)
		for plr, d in pairs(data) do
			local inc = income(d)
			if inc > 0 then
				d.cash = d.cash + inc
				sync(plr)
			end
		end
	end
end)


-- ============================================================ NEW MENUS: upgrades from the menu, daily rewards, game passes
local MPS = game:GetService("MarketplaceService")

-- a pet straight into the pen (daily reward egg): same path as walking home with it, the basket is left alone
local function hatchToPen(plr, d, z, kind, boost, force)
	local luck = C.luck(d.luck) * (d.passes.luck2 and 2 or 1) * (boost or 1) * (eventKey() == "luck" and 2 or 1)
	local idx = force or roll(luck)
	local pet = { z = z, i = idx, t = C.rollTier(kind, eventKey() == "rainbow") } -- v152
	pet.v = rollVariant(pet, d)
	local def = C.petDef(pet)
	d.caught = d.caught + 1
	if C.RARITY[idx].odds > d.bestOdds then
		d.bestOdds, d.bestName = C.RARITY[idx].odds, def.name
	end
	local key = C.petKey(pet)
	local isNew = not d.index[key]
	if isNew then
		d.index[key] = true
		d.zonesDone = zonesDone(d)
		syncIndex(plr)
	end
	Hatch:FireClient(plr, pet, kind, isNew, 1)
	local keep = d.carry
	d.carry = { pet }
	deposit(plr)
	d.carry = keep
	renderCarry(plr)
	sync(plr)
	if idx == #C.RARITY then
		Notice:FireAllClients(plr.DisplayName .. " hatched a LEGENDARY " .. def.name .. "! (1 in " .. C.comma(C.RARITY[idx].odds) .. ")", "legend")
	end
end

-- ============================================================ v150: WELCOME GIFT, FRIENDS, WEEKLY EVENT
-- welcome gift: a new player gets a golden egg 10 s after joining -> a Rare (sometimes Epic) pet straight into the pen
local function giveGift(plr)
	task.wait(C.GIFT_DELAY)
	local d = data[plr]
	if not d or d.gift or not plr.Parent then
		return
	end
	d.gift = true
	-- v182 (user): the gift egg goes into EGGS (it does not open on its own) and the introduction starts
	table.insert(d.bag, { z = 1, kind = "golden", luck = 1, force = math.random() < C.GIFT_EPIC and 4 or 3 })
	d.tut = 1
	plr:SetAttribute("Tut", d.tut)
	say(plr, "WELCOME GIFT! A free golden egg - open EGGS!", "gift") -- v212: silent (a "cash" note plays a coin)
	sync(plr)
end
-- friends on the same server: +10% cash each (max 4); recount for everybody when someone joins or leaves
local function countFriends()
	for plr, d in pairs(data) do
		local n = 0
		for other in pairs(data) do
			if other ~= plr then
				local ok, yes = pcall(plr.IsFriendsWith, plr, other.UserId)
				if ok and yes then
					n = n + 1
				end
			end
		end
		n = math.min(n, C.FRIEND_MAX)
		if n ~= (d.friends or 0) then
			local more = n > (d.friends or 0)
			d.friends = n
			plr:SetAttribute("Friends", n)
			renderPen(plr) -- the $/s tags show the new bonus
			sync(plr)
			if more then
				say(plr, "Playing with friends! +" .. math.floor(C.FRIEND_BONUS * n * 100 + 0.5) .. "% cash", "cash")
			end
		end
	end
end
local function onJoin(plr)
	for _ = 1, 100 do
		if data[plr] or not plr.Parent then
			break
		end
		task.wait(0.2)
	end
	if data[plr] then
		task.spawn(giveGift, plr)
		countFriends()
	end
end
Players.PlayerAdded:Connect(onJoin)
for _, plr in ipairs(Players:GetPlayers()) do
	task.spawn(onJoin, plr)
end
Players.PlayerRemoving:Connect(function()
	task.defer(countFriends)
end)
-- weekly event: the clients read these attributes for the banner
task.spawn(function()
	while true do
		local ev, ends = C.eventAt(os.time())
		workspace:SetAttribute("EventKey", ev.key)
		workspace:SetAttribute("EventName", ev.name)
		workspace:SetAttribute("EventDesc", ev.desc)
		workspace:SetAttribute("EventEnd", ends)
		task.wait(30)
	end
end)

Action.OnServerEvent:Connect(function(plr, what, kind)
	local d = data[plr]
	if not d then
		return
	end
	if what == "hatch" then
		hatchBag(plr, kind)
	elseif what == "hatch1" then
		hatchBag(plr, kind, 1) -- the EGGS menu: the player picks which egg to open, one at a time
	elseif what == "upgrade" then
		if kind == "basket" or kind == "luck" or kind == "pen" then
			buy(plr, kind, nil)
		elseif kind == "train" then
			buyTrain(plr)
		end
	elseif what == "daily" then
		local now = os.time()
		if d.dailyLast > 0 and now - d.dailyLast < C.DAILY_COOLDOWN then
			say(plr, "Come back later for your next reward", "info")
			return
		end
		local day = (d.dailyLast == 0 or now - d.dailyLast > C.DAILY_RESET) and 1 or (d.dailyDay % #C.DAILY + 1)
		local r = C.DAILY[day]
		local cash = math.max(r.min, math.floor(income(d) * r.secs))
		d.dailyDay, d.dailyLast = day, now
		d.cash = d.cash + cash
		sync(plr)
		say(plr, "Day " .. day .. " reward: +$" .. C.fmt(cash), "buy")
		if r.egg then
			hatchToPen(plr, d, d.unlocked, "golden")
		end
		save(plr)
	end
end)

-- game passes: check what the player owns when they join, and when they buy one
local function givePass(plr, key)
	local d = data[plr]
	if d and not d.passes[key] then
		d.passes[key] = true
		sync(plr)
	end
end
Players.PlayerAdded:Connect(function(plr)
	for _, p in ipairs(C.PASSES) do
		if p.id ~= 0 then
			task.spawn(function()
				local ok, has = pcall(MPS.UserOwnsGamePassAsync, MPS, plr.UserId, p.id)
				if ok and has then
					for _ = 1, 50 do -- wait for the save to load
						if data[plr] then
							break
						end
						task.wait(0.2)
					end
					givePass(plr, p.key)
				end
			end)
		end
	end
end)
-- v256: Robux products (SHOP: Royal Egg, speed, money). Granted once per receipt.
local granted = {}
local grantProduct -- v284: defined right below (also used by the Studio test buy)
MPS.ProcessReceipt = function(info)
	local plr = Players:GetPlayerByUserId(info.PlayerId)
	local d = plr and data[plr]
	if not d then
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end
	if granted[info.PurchaseId] then
		return Enum.ProductPurchaseDecision.PurchaseGranted
	end
	local pk
	for _, p in pairs(C.PRODUCTS) do
		if p.id ~= 0 and p.id == info.ProductId then
			pk = p
		end
	end
	if not pk then
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end
	grantProduct(plr, d, pk)
	granted[info.PurchaseId] = true
	return Enum.ProductPurchaseDecision.PurchaseGranted
end
grantProduct = function(plr, d, pk)
	if pk.kind == "royal" then
		for _ = 1, pk.n do
			table.insert(d.bag, { z = math.max(1, d.unlocked or 1), kind = "royal", luck = C.luck(d.luck) * C.ROYAL_LUCK })
		end
		renderCarry(plr)
		say(plr, pk.n .. (pk.n == 1 and " ROYAL EGG" or " ROYAL EGGS") .. " added to your EGGS! Thank you!", "legend")
		Bought:FireClient(plr, pk.n .. (pk.n == 1 and " Royal Egg" or " Royal Eggs"))
	elseif pk.kind == "speed" then
		d.speed = math.max(d.speed, 100) * pk.mult
		say(plr, "Speed x" .. pk.mult .. "! Thank you!", "legend")
		Bought:FireClient(plr, "Speed x" .. pk.mult)
	elseif pk.kind == "cash" then
		local income = tonumber(plr:GetAttribute("Income")) or 0
		local gain = math.max(pk.min, math.floor(income * pk.secs))
		d.cash = d.cash + gain
		say(plr, "+$" .. C.fmt(gain) .. "! Thank you!", "legend")
		Bought:FireClient(plr, "+$" .. C.fmt(gain))
	end
	sync(plr)
end
-- v284 (user: try the Robux things without paying): in Studio ONLY, the shop buttons of products / passes without an id
-- give the thing for free (Action "testbuy", key). On the real game servers this does nothing.
Action.OnServerEvent:Connect(function(plr, what, key)
	if what ~= "testbuy" or not game:GetService("RunService"):IsStudio() or typeof(key) ~= "string" then
		return
	end
	local d = data[plr]
	if not d then
		return
	end
	local pk = C.PRODUCTS[key]
	if pk then
		grantProduct(plr, d, pk)
		return
	end
	for _, p in ipairs(C.PASSES) do
		if p.key == key then
			givePass(plr, p.key)
			say(plr, p.name .. " unlocked! (Studio test)", "legend")
			Bought:FireClient(plr, p.name)
		end
	end
end)
-- v262 AUTO HATCH pass: every 4 s one egg from the EGGS menu hatches on its own (same as pressing HATCH)
task.spawn(function()
	while true do
		task.wait(4)
		for plr, d in pairs(data) do
			if d.passes and d.passes.autohatch and #d.bag > 0 and plr.Parent then
				pcall(hatchBag, plr, nil, 1)
			end
		end
	end
end)
MPS.PromptGamePassPurchaseFinished:Connect(function(plr, id, bought)
	if not bought then
		return
	end
	for _, p in ipairs(C.PASSES) do
		if p.id == id then
			givePass(plr, p.key)
			say(plr, p.name .. " unlocked! Thank you!", "legend")
			Bought:FireClient(plr, p.name)
		end
	end
end)


-- ============================================================ BIG EGG DROP (VFX + animations by Codex: ReplicatedStorage.BigEggFX)
-- A giant egg falls into the plaza, digs a crater and stays in it. Everybody gets a weapon; a hit knocks you back,
-- slows you for a second and stops your claim. Holding E for 5 seconds wins the egg = a pet hatched with big luck.
local RunService = game:GetService("RunService")
local BigEgg = remote("BigEgg") -- server -> all: "incoming", pos | "fall", pos | "claim", userId, serverTime | "release", userId | "hit", victimUserId, dir | "win", userId, name | "clear"
local BigEggSwing = remote("BigEggSwing") -- client -> server: a swing
local bigEv = nil

local function weaponTool(kind)
	local t = Instance.new("Tool")
	t.Name = kind == "Hammer" and "Bonk Hammer" or "Pillow Bat"
	t.CanBeDropped = false
	t.ToolTip = "Hit players to stop them taking the SECRET EGG"
	t:SetAttribute("BigEggWeapon", kind)
	local h = Instance.new("Part")
	h.Name = "Handle"
	h.CanCollide, h.Massless = false, true
	local function add(size, off, col, mat)
		local p = Instance.new("Part")
		p.Size, p.Color, p.Material = size, col, mat or Enum.Material.SmoothPlastic
		p.CanCollide, p.Massless, p.CanTouch, p.CanQuery = false, true, false, false
		p.CFrame = h.CFrame * off
		local w = Instance.new("WeldConstraint")
		w.Part0, w.Part1, w.Parent = h, p, p
		p.Parent = t
	end
	local mesh = RS:FindFirstChild("Assets") and RS.Assets:FindFirstChild(kind == "Hammer" and "BonkHammer" or "PillowBat")
	if mesh then
		h:Destroy()
		h = mesh:Clone()
		h.Name, h.Anchored, h.CanCollide, h.Massless = "Handle", false, false, true
	elseif kind == "Hammer" then
		h.Size, h.Color, h.Material = Vector3.new(0.4, 3, 0.4), Color3.fromRGB(120, 78, 44), Enum.Material.Wood
		add(Vector3.new(1.4, 1.1, 2.2), CFrame.new(0, 1.6, 0), Color3.fromRGB(255, 70, 90))
		add(Vector3.new(1.5, 0.3, 2.3), CFrame.new(0, 1.6, 0), Color3.fromRGB(255, 220, 90))
	else
		h.Size, h.Color = Vector3.new(0.35, 1.2, 0.35), Color3.fromRGB(240, 240, 255)
		add(Vector3.new(1.6, 2.4, 0.8), CFrame.new(0, 1.7, 0), Color3.fromRGB(160, 200, 255), Enum.Material.Fabric)
	end
	h.Parent = t
	t.Grip = CFrame.new(0, -1, 0)
	return t
end

-- v210 (user): a wooden baseball bat instead of the hammer / pillow
local function batTool()
	local t = Instance.new("Tool")
	t.Name = "Bat"
	t.CanBeDropped = false
	t.ToolTip = "Hit players to stop them taking the SECRET EGG"
	t:SetAttribute("BigEggWeapon", "Bat")
	local WOOD, DARKW, TAPE = Color3.fromRGB(214, 160, 96), Color3.fromRGB(150, 98, 52), Color3.fromRGB(40, 36, 52)
	-- the handle runs along Y (like the old weapons: Grip (0, -1, 0)); round looks come from cylinders turned upright
	local h = Instance.new("Part")
	h.Name = "Handle"
	h.Size = Vector3.new(0.3, 1.5, 0.3)
	h.Transparency = 1
	h.CanCollide, h.Massless = false, true
	h.Parent = t
	local UPRIGHT = CFrame.Angles(0, 0, math.rad(90)) -- a cylinder's axis is X: turn it onto Y
	local function seg(len, d, y, col, mat)
		local p = Instance.new("Part")
		p.Shape = Enum.PartType.Cylinder
		p.Size = Vector3.new(len, d, d)
		p.Color, p.Material = col, mat or Enum.Material.Wood
		p.CanCollide, p.Massless, p.CanTouch, p.CanQuery = false, true, false, false
		p.CFrame = h.CFrame * CFrame.new(0, y, 0) * UPRIGHT
		local w = Instance.new("WeldConstraint")
		w.Part0, w.Part1, w.Parent = h, p, p
		p.Parent = t
	end
	seg(1.5, 0.32, 0, TAPE, Enum.Material.Fabric)  -- grip tape
	seg(0.18, 0.5, -0.84, DARKW)                  -- knob
	seg(0.9, 0.36, 1.15, WOOD)                    -- taper
	seg(0.8, 0.46, 1.95, WOOD)
	seg(0.9, 0.56, 2.8, WOOD)                     -- barrel
	seg(0.12, 0.58, 3.3, DARKW)                   -- end cap
	t.Grip = CFrame.new(0, -0.3, 0)
	return t
end

local function giveWeapons()
	for _, plr in ipairs(Players:GetPlayers()) do
		local bp = plr:FindFirstChildOfClass("Backpack")
		local has = (bp and bp:FindFirstChild("Bat")) or (plr.Character and plr.Character:FindFirstChild("Bat"))
		if bp and not has then
			batTool().Parent = bp
		end
	end
end

local function takeWeapons()
	for _, plr in ipairs(Players:GetPlayers()) do
		for _, holder in ipairs({ plr:FindFirstChildOfClass("Backpack"), plr.Character }) do
			if holder then
				for _, t in ipairs(holder:GetChildren()) do
					if t:IsA("Tool") and t:GetAttribute("BigEggWeapon") then
						t:Destroy()
					end
				end
			end
		end
	end
end

local function endBigEgg()
	if not bigEv then
		return
	end
	if bigEv.target then
		bigEv.target:Destroy()
	end
	bigEv = nil
	takeWeapons()
	workspace:SetAttribute("BigEggActive", false)
end

local function startBigEgg()
	if bigEv then
		return
	end
	-- a random zone: one where players are now, else any zone somebody has unlocked; the egg lands on the white road in its middle
	local zones, maxUnlocked = {}, 1
	for zi in pairs(occupied()) do
		table.insert(zones, zi) -- v122: world 2 zones too (it lands on the space ground, cosmic crater)
	end
	for _, d in pairs(data) do
		maxUnlocked = math.max(maxUnlocked, d.unlocked or 1)
	end
	-- v176 (user: "a big egg is falling" but nothing falls): with nobody in a zone it went to a random far zone ->
	-- zone 1, right next to the plaza and the bases
	-- v224 (user): a random zone (RNG) of the zones the players have opened - never the last zone of a world
	local pool = {}
	for z = 1, math.min(maxUnlocked, C.TOTAL) do
		if z ~= C.NZ and z ~= C.TOTAL then
			table.insert(pool, z)
		end
	end
	local zi = #pool > 0 and pool[math.random(#pool)] or 1
	local w2 = zi > C.NZ
	-- v224 (user): in the Golden Nest the middle is the fenced giant golden egg -> the big egg lands near the zone start
	local frac = (zi == C.NZ) and (0.14 + math.random() * 0.08) or (0.4 + math.random() * 0.2)
	local spot = { 0, (w2 and C.w2Z0(zi) or (zi - 1) * C.ZONE_LEN) + C.ZONE_LEN * frac }
	local top = w2 and C.COSMIC.y or 0
	local params = RaycastParams.new()
	local chars = {}
	for _, p in ipairs(Players:GetPlayers()) do
		if p.Character then
			table.insert(chars, p.Character)
		end
	end
	params.FilterDescendantsInstances = chars
	local hit = workspace:Raycast(Vector3.new(spot[1], top + 300, spot[2]), Vector3.new(0, -400, 0), params)
	local pos = hit and hit.Position or Vector3.new(spot[1], top + 0.5, spot[2])
	bigEv = { pos = pos, holds = {} }
	local ev = bigEv
	workspace:SetAttribute("BigEggActive", true)
	BigEgg:FireAllClients("incoming", pos)
	Notice:FireAllClients("A SECRET EGG is falling in " .. C.ZONES[zi].name .. "! Grab a bat!", "storm")
	giveWeapons()
	task.wait(10)
	if bigEv ~= ev then
		return
	end
	BigEgg:FireAllClients("fall", pos)
	task.wait(1.7)
	if bigEv ~= ev then
		return
	end
	-- the claim point does not move with the falling / bobbing visual on the clients
	local target = Instance.new("Part")
	target.Name = "BigEggTarget"
	target.Anchored, target.CanCollide, target.CanQuery, target.Transparency = true, false, false, 1
	target.Size = Vector3.new(20, 16, 20)
	target.Position = pos + Vector3.new(0, 8, 0)
	target.Parent = workspace
	ev.target = target
	local pp = Instance.new("ProximityPrompt")
	pp.ActionText, pp.ObjectText = "CLAIM", "SECRET EGG"
	pp.HoldDuration = C.BIGEGG_CLAIM
	pp.MaxActivationDistance = 22
	pp.RequiresLineOfSight = false
	pp.KeyboardKeyCode = Enum.KeyCode.E
	pp.Style = Enum.ProximityPromptStyle.Default
	-- no default prompt box: the clients draw the round E button in the middle of the egg (user, 19 Nov); E still works
	pp.Style = Enum.ProximityPromptStyle.Custom
	pp.MaxActivationDistance = 24
	pp.Parent = target
	ev.prompt = pp
	pp.PromptButtonHoldBegan:Connect(function(plr)
		ev.holds[plr] = os.clock()
		BigEgg:FireAllClients("claim", plr.UserId, workspace:GetServerTimeNow())
	end)
	pp.PromptButtonHoldEnded:Connect(function(plr)
		if ev.holds[plr] then
			ev.holds[plr] = nil
			BigEgg:FireAllClients("release", plr.UserId)
		end
	end)
	pp.Triggered:Connect(function(plr)
		local d = data[plr]
		if bigEv ~= ev or not d or ev.won then
			return
		end
		ev.won = true
		pp.Enabled = false
		BigEgg:FireAllClients("win", plr.UserId, plr.DisplayName)
		-- v174 (user): no "claimed the BIG EGG" message
		task.delay(1.2, function()
			hatchToPen(plr, d, d.unlocked, "secret", C.BIGEGG_LUCK) -- v244 (user): the hatch shows the violet SECRET EGG, not a golden one
			save(plr)
		end)
		task.delay(6, function()
			if bigEv == ev then
				BigEgg:FireAllClients("clear")
				endBigEgg()
			end
		end)
	end)
	task.delay(C.BIGEGG_LIFE, function()
		if bigEv == ev and not ev.won then
			Notice:FireAllClients("Nobody claimed the SECRET EGG... it sank into the ground", "info")
			BigEgg:FireAllClients("clear")
			endBigEgg()
		end
	end)
end

-- swings: the server checks who is in reach; the victim's own client pushes its character (it owns its physics)
BigEggSwing.OnServerEvent:Connect(function(plr)
	local d = data[plr]
	local char = plr.Character
	local root = char and char:FindFirstChild("HumanoidRootPart")
	local tool = char and char:FindFirstChildOfClass("Tool")
	if not bigEv or not d or not root or not tool or not tool:GetAttribute("BigEggWeapon") then
		return
	end
	local now = os.clock()
	if now - (d.swingT or 0) < C.BIGEGG_WEAPON_CD then
		return
	end
	d.swingT = now
	BigEgg:FireAllClients("swing", plr.UserId) -- v210: every client swings that player's arm
	local best, bestDist = nil, C.BIGEGG_REACH
	for _, other in ipairs(Players:GetPlayers()) do
		local oc = other ~= plr and other.Character
		local orr = oc and oc:FindFirstChild("HumanoidRootPart")
		local oh = oc and oc:FindFirstChildOfClass("Humanoid")
		if orr and oh and oh.Health > 0 then
			local off = orr.Position - root.Position
			local flat = Vector3.new(off.X, 0, off.Z)
			local dist = flat.Magnitude
			if dist < bestDist and (dist < 2.5 or root.CFrame.LookVector:Dot(flat.Unit) > 0.25) then
				best, bestDist = other, dist
			end
		end
	end
	if not best then
		return
	end
	task.delay(0.18, function() -- the hit lands when the arm comes down
		local orr = best.Character and best.Character:FindFirstChild("HumanoidRootPart")
		if not orr or not bigEv then
			return
		end
		local flat = Vector3.new(orr.Position.X - root.Position.X, 0, orr.Position.Z - root.Position.Z)
		local dir = flat.Magnitude > 0.01 and flat.Unit or root.CFrame.LookVector
		local od = data[best]
		if od then
			od.stunUntil = os.clock() + C.BIGEGG_STUN
		end
		BigEgg:FireAllClients("hit", best.UserId, dir)
		if bigEv.holds[best] and bigEv.prompt then
			-- a hit breaks the hold: switching the prompt off and on cancels the E hold
			bigEv.holds[best] = nil
			BigEgg:FireAllClients("release", best.UserId, true)
			bigEv.prompt.Enabled = false
			task.delay(0.15, function()
				if bigEv and bigEv.prompt and not bigEv.won then
					bigEv.prompt.Enabled = true
				end
			end)
		end
	end)
end)

-- late joiners and respawns during the event still get a weapon
Players.PlayerAdded:Connect(function(plr)
	plr.CharacterAdded:Connect(function()
		task.wait(1)
		if bigEv then
			giveWeapons()
		end
	end)
end)
for _, plr in ipairs(Players:GetPlayers()) do
	plr.CharacterAdded:Connect(function()
		task.wait(1)
		if bigEv then
			giveWeapons()
		end
	end)
end

-- Studio test: F8 on the client starts a drop now
Action.OnServerEvent:Connect(function(plr, what)
	if what == "bigegg" and RunService:IsStudio() then
		task.spawn(startBigEgg)
	end
end)

task.spawn(function()
	task.wait(math.random(C.BIGEGG_FIRST[1], C.BIGEGG_FIRST[2]))
	while true do
		-- every 5 minutes (C.BIGEGG_EVERY); during an egg storm it waits until the storm is over
		-- v244 (user): never together with an EGG STORM - also not when a storm starts in the next 4 minutes
		while #Players:GetPlayers() == 0 or storm or bigEv
			or (workspace:GetAttribute("StormNext") or 0) - workspace:GetServerTimeNow() < 240 do
			task.wait(5)
		end
		task.spawn(startBigEgg)
		task.wait(math.random(C.BIGEGG_EVERY[1], C.BIGEGG_EVERY[2]))
	end
end)


-- ============================================================ GOLDEN NEST ALTARS (v111)
-- 10 altars in the last zone, one per zone. Hold E at altar n with an unhatched egg of zone n in your EGGS:
-- the egg goes on the altar (saved). All 10 filled = for that player the giant golden egg sinks into the ground and
-- a portal opens (client: GoldenPortalVFX by Codex). Progress is per player.
local GoldenAltar = remote("GoldenAltar") -- server -> one client: "place", zone | "sink"
local altars = {}
-- put the player's egg of zone n on altar n. Returns "placed", "has" (already there) or "noegg". quiet = no per-altar message
local function placeAltar(plr, n, quiet)
	local d = data[plr]
	if not d then
		return "noegg"
	end
	if d.altar[n] then
		if not quiet then
			say(plr, "This altar already has your " .. C.ZONES[n].name .. " egg", "info")
		end
		return "has"
	end
	local pick
	for k, egg in ipairs(d.bag) do
		if egg.z == n and egg.kind ~= "royal" and (not pick or egg.kind == "normal") then
			pick = k
		end
	end
	if not pick then
		if not quiet then
			say(plr, "Bring an egg from " .. C.ZONES[n].name .. " (catch one, do not hatch it)", "bad")
		end
		return "noegg"
	end
	table.remove(d.bag, pick)
	d.altar[n] = true
	renderCarry(plr)
	sync(plr)
	GoldenAltar:FireClient(plr, "place", n)
	local count = #altarList(d)
	if count >= C.NZ then
		task.delay(0.8, function()
			GoldenAltar:FireClient(plr, "sink")
		end)
		-- v222 (user): no "opened the GOLDEN PORTAL" message / sound
	elseif not quiet then
		say(plr, C.ZONES[n].name .. " egg placed! " .. count .. " / " .. C.NZ .. " altars", "good")
	end
	save(plr)
	return "placed"
end
for _, d0 in ipairs(Map:GetDescendants()) do
	local n = d0:IsA("BasePart") and tonumber(string.match(d0.Name, "^EggAltar(%d+)$"))
	if n and C.ZONES[n] then
		altars[n] = d0
		local pp = Instance.new("ProximityPrompt")
		pp.ActionText = "PLACE EGG"
		pp.ObjectText = C.ZONES[n].name:upper() .. " EGG"
		pp.HoldDuration = 0.6
		pp.MaxActivationDistance = 12
		pp.RequiresLineOfSight = false
		pp.Style = Enum.ProximityPromptStyle.Custom -- v126: the client draws its own altar button (AltarPrompt)
		pp.Parent = d0
		pp.Triggered:Connect(function(plr)
			placeAltar(plr, n, false)
		end)
	end
end

-- v125: the PLACE ALL EGGS button (client, only in the Golden Nest): every egg the player has for an empty altar goes on it
Action.OnServerEvent:Connect(function(plr, what)
	local d = data[plr]
	if what ~= "altarall" or not d then
		return
	end
	if d.zone ~= C.NZ then
		say(plr, "Go to the Golden Nest to use the altars", "info")
		return
	end
	local now = os.clock()
	if now - (d.altarAllT or 0) < 1 then
		return
	end
	d.altarAllT = now
	local placed, missing = 0, {}
	for n = 1, C.NZ do
		if altars[n] and not d.altar[n] then
			local r = placeAltar(plr, n, true)
			if r == "placed" then
				placed = placed + 1
			elseif r == "noegg" then
				table.insert(missing, C.ZONES[n].name)
			end
		end
	end
	local count = #altarList(d)
	if placed == 0 and count < C.NZ then
		say(plr, "No eggs to place. Still missing: " .. table.concat(missing, ", "), "bad")
	elseif count < C.NZ then
		say(plr, placed .. " eggs placed! " .. count .. " / " .. C.NZ .. " altars. Missing: " .. table.concat(missing, ", "), "good")
	end
end)

-- Studio test (F7): altars 1-9 filled + one zone-10 egg in your EGGS, so the 10th altar opens the portal
Action.OnServerEvent:Connect(function(plr, what)
	local d = data[plr]
	if what == "altartest" and d and RunService:IsStudio() then
		for z = 1, C.NZ - 1 do
			if not d.altar[z] then
				d.altar[z] = true
				GoldenAltar:FireClient(plr, "place", z)
			end
		end
		table.insert(d.bag, { z = C.NZ, kind = "normal", luck = 1 })
		sync(plr)
		say(plr, "Studio test: altars 1-9 filled, a Golden Nest egg is in your EGGS", "info")
	end
end)


-- ============================================================ PRECISE HITBOXES (v125)
-- user: "hitboxes exactly at the edge of every object". Meshes loaded from the place file collide as one big box, so
-- the map used invisible helper boxes. Here every map mesh with a PreciseId gets its real shape as collision
-- (AssetService:CreateMeshPartAsync with PreciseConvexDecomposition + ApplyMesh). Where that works the mesh becomes
-- solid and its linked helper boxes (HitboxOf = same id) stop colliding; where it fails nothing changes.
task.spawn(function()
	local AssetService = game:GetService("AssetService")
	local byId, groups, helpers = {}, {}, {}
	for _, o in ipairs(Map:GetDescendants()) do
		if o:IsA("IntValue") and o.Name == "PreciseId" and o.Parent:IsA("MeshPart") then
			local mp = o.Parent
			local key = mp.MeshId ~= "" and mp.MeshId or (mp.MeshContent and mp.MeshContent.Uri) or ""
			if key ~= "" then
				groups[key] = groups[key] or {}
				table.insert(groups[key], mp)
				byId[o.Value] = mp
			end
		elseif o:IsA("IntValue") and o.Name == "HitboxOf" and o.Parent:IsA("BasePart") then
			helpers[o.Value] = helpers[o.Value] or {}
			table.insert(helpers[o.Value], o.Parent)
		end
	end
	local done, failed, running = 0, 0, 0
	local okUid = {}
	for key, list in pairs(groups) do
		while running >= 6 do
			task.wait()
		end
		running = running + 1
		task.spawn(function()
			local opts = {
				CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
				RenderFidelity = list[1].RenderFidelity,
			}
			local ok, src = pcall(function()
				return AssetService:CreateMeshPartAsync(key, opts) -- older API: the id string
			end)
			if not ok then
				ok, src = pcall(function()
					return AssetService:CreateMeshPartAsync(Content.fromUri(key), opts) -- newer API: a Content
				end)
			end
			if ok and src then
				for _, mp in ipairs(list) do
					local size, cf = mp.Size, mp.CFrame
					local applied = pcall(function()
						mp:ApplyMesh(src)
					end)
					if applied then
						mp.Size, mp.CFrame = size, cf
						if mp:FindFirstChild("SolidAfter") then
							mp.CanCollide, mp.CanQuery = true, true
						end
						okUid[mp.PreciseId.Value] = true
						done = done + 1
					else
						failed = failed + 1
					end
				end
				src:Destroy()
			else
				failed = failed + #list
				warn("Precise hitbox failed for", key, src)
			end
			running = running - 1
		end)
	end
	while running > 0 do
		task.wait()
	end
	local off = 0
	for uid in pairs(okUid) do
		for _, h in ipairs(helpers[uid] or {}) do
			h.CanCollide, h.CanQuery = false, false
			off = off + 1
		end
	end
	print(("Precise hitboxes: %d meshes exact, %d failed, %d helper boxes off"):format(done, failed, off))
end)
