-- PetBuilder: turns one PetData entry into a Roblox Model made of studded blocks.
--   local PB = require(ReplicatedStorage.PetBuilder)
--   local model = PB.build(PetData[i], { mutation = "Gold" | "Rainbow" | nil, size = "Big" | ..., income = 1234 })
--   PB.animate(model, t)     -- call every frame on the client (idle bob, wings, tail, head, floating parts, spinning halos)
-- The model: PrimaryPart "Root" (invisible, at the ground centre), every block anchored, no collision, all faces studded.
local PB = {}

PB.RARITY_COLOR = {
	Common = Color3.fromRGB(220, 224, 232), Uncommon = Color3.fromRGB(110, 235, 110), Rare = Color3.fromRGB(90, 180, 255),
	Epic = Color3.fromRGB(190, 110, 255), Legendary = Color3.fromRGB(255, 210, 50), Mythic = Color3.fromRGB(255, 70, 70),
	Secret = Color3.fromRGB(30, 30, 36), Divine = Color3.fromRGB(255, 250, 210),
}
PB.SIZES = { Normal = 1, Big = 1.3, Large = 1.65, Huge = 2.2, Titanic = 3.0 }

local STUDS = Enum.SurfaceType.Studs
local FACES = { "TopSurface", "BottomSurface", "LeftSurface", "RightSurface", "FrontSurface", "BackSurface" }
local GOLD = { Color3.fromRGB(200, 120, 0), Color3.fromRGB(255, 176, 0), Color3.fromRGB(255, 214, 40), Color3.fromRGB(255, 244, 150) }
local registry = setmetatable({}, { __mode = "k" }) -- model -> { root CFrame, parts = { {part, base, tag} } }

local function isFace(c)
	return (c.R > 0.95 and c.G > 0.95 and c.B > 0.95) or (c.R < 0.12 and c.G < 0.12 and c.B < 0.14)
end

-- ------------------------------------------------------------ effects
local function emitter(parent, props)
	local e = Instance.new("ParticleEmitter")
	e.LightEmission = 1
	e.LightInfluence = 0
	e.Rate = 6
	e.Lifetime = NumberRange.new(1, 1.6)
	e.Speed = NumberRange.new(0.5, 1.5)
	e.SpreadAngle = Vector2.new(180, 180)
	e.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.4), NumberSequenceKeypoint.new(1, 0) })
	e.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 1) })
	e.Texture = "rbxasset://textures/particles/sparkles_main.dds"
	for k, v in pairs(props) do
		e[k] = v
	end
	e.Parent = parent
	return e
end

local FX = {}
FX.sparkle = function(at, col, h)
	emitter(at, { Color = ColorSequence.new(Color3.new(1, 1, 0.85)), Rate = 4, Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(1, 0) }) })
end
FX.fire = function(at, col, h)
	emitter(at, { Texture = "rbxasset://textures/particles/fire_main.dds", Color = ColorSequence.new(Color3.fromRGB(255, 200, 60), Color3.fromRGB(255, 70, 20)),
		Rate = 18, Speed = NumberRange.new(2, 4), SpreadAngle = Vector2.new(15, 15), Acceleration = Vector3.new(0, 4, 0),
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.2), NumberSequenceKeypoint.new(1, 0.1) }) })
end
FX.ember = function(at) emitter(at, { Color = ColorSequence.new(Color3.fromRGB(255, 140, 40)), Rate = 5, Acceleration = Vector3.new(0, 3, 0) }) end
FX.electric = function(at)
	emitter(at, { Texture = "rbxasset://textures/particles/sparkles_main.dds", Color = ColorSequence.new(Color3.fromRGB(140, 230, 255), Color3.fromRGB(255, 255, 120)),
		Rate = 14, Lifetime = NumberRange.new(0.15, 0.3), Speed = NumberRange.new(6, 10), Size = NumberSequence.new(0.35) })
end
FX.toxic = function(at) emitter(at, { Color = ColorSequence.new(Color3.fromRGB(150, 255, 60)), Rate = 8, Acceleration = Vector3.new(0, 2, 0), Texture = "rbxasset://textures/particles/smoke_main.dds" }) end
FX.ghost = function(at) emitter(at, { Color = ColorSequence.new(Color3.fromRGB(180, 255, 240)), Rate = 5, Texture = "rbxasset://textures/particles/smoke_main.dds", Acceleration = Vector3.new(0, 1.5, 0) }) end
FX.shadow = function(at) emitter(at, { Color = ColorSequence.new(Color3.fromRGB(120, 40, 220)), LightEmission = 0.3, Rate = 10, Texture = "rbxasset://textures/particles/smoke_main.dds" }) end
FX.spores = function(at) emitter(at, { Color = ColorSequence.new(Color3.fromRGB(200, 140, 255)), Rate = 6, Speed = NumberRange.new(0.3, 0.8), Acceleration = Vector3.new(0, 0.8, 0) }) end
FX.bubbles = function(at) emitter(at, { Color = ColorSequence.new(Color3.fromRGB(170, 230, 255)), Rate = 5, Acceleration = Vector3.new(0, 2, 0), LightEmission = 0.4 }) end
FX.water = FX.bubbles
FX.wind = function(at) emitter(at, { Color = ColorSequence.new(Color3.new(1, 1, 1)), Rate = 4, Speed = NumberRange.new(3, 5), SpreadAngle = Vector2.new(10, 180), LightEmission = 0.2 }) end
FX.dust = function(at) emitter(at, { Color = ColorSequence.new(Color3.fromRGB(180, 160, 130)), Rate = 4, LightEmission = 0, Texture = "rbxasset://textures/particles/smoke_main.dds" }) end
FX.leaves = function(at) emitter(at, { Color = ColorSequence.new(Color3.fromRGB(130, 230, 90)), Rate = 4, Acceleration = Vector3.new(0, -1, 0), LightEmission = 0.2 }) end
FX.glow = function(at) end
FX.glitch = function(at) emitter(at, { Color = ColorSequence.new(Color3.fromRGB(0, 255, 140), Color3.fromRGB(255, 0, 200)), Rate = 12, Lifetime = NumberRange.new(0.1, 0.3), Speed = NumberRange.new(4, 6), Size = NumberSequence.new(0.6) }) end
FX.cosmic = function(at) emitter(at, { Color = ColorSequence.new(Color3.fromRGB(150, 110, 255), Color3.fromRGB(80, 220, 255)), Rate = 10, Speed = NumberRange.new(0.2, 0.6) }) end
FX.divine = function(at) emitter(at, { Color = ColorSequence.new(Color3.fromRGB(255, 250, 200)), Rate = 12, Speed = NumberRange.new(1, 2), Acceleration = Vector3.new(0, 2, 0), Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(1, 0) }) }) end
FX.rainbow = function(at) emitter(at, { Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 60, 60)), ColorSequenceKeypoint.new(0.33, Color3.fromRGB(255, 230, 60)), ColorSequenceKeypoint.new(0.66, Color3.fromRGB(60, 200, 255)), ColorSequenceKeypoint.new(1, Color3.fromRGB(220, 80, 255)) }), Rate = 10 }) end

-- ------------------------------------------------------------ build
function PB.build(def, opts)
	opts = opts or {}
	local model = Instance.new("Model")
	model.Name = def.name
	local root = Instance.new("Part")
	root.Name = "Root"
	root.Anchored, root.CanCollide, root.CanQuery, root.CanTouch = true, false, false, false
	root.Transparency = 1
	root.Size = Vector3.new(1, 1, 1)
	root.CFrame = CFrame.new()
	root.Parent = model
	model.PrimaryPart = root
	local info = { parts = {} }
	registry[model] = info
	local top = 0
	for i, q in ipairs(def.parts) do
		local p = Instance.new("Part")
		p.Name = (q[14] ~= "" and q[14]) or "Block"
		p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, false, false
		p.CastShadow = q[13] ~= "Neon"
		p.Size = Vector3.new(q[1], q[2], q[3])
		local col = Color3.fromRGB(q[10], q[11], q[12])
		local mat = Enum.Material[q[13]] or Enum.Material.Plastic
		if opts.mutation == "Gold" and q[13] ~= "Neon" and not isFace(col) then
			local l = 0.3 * col.R + 0.59 * col.G + 0.11 * col.B
			col = GOLD[math.clamp(math.floor(l * 4.2) + 1, 1, 4)]
			mat = Enum.Material.Foil
		end
		p.Color = col
		p.Material = mat
		p.Transparency = q[15]
		for _, f in ipairs(FACES) do
			p[f] = STUDS
		end
		local base = CFrame.new(q[4], q[5], q[6]) * CFrame.Angles(math.rad(q[7]), math.rad(q[8]), math.rad(q[9]))
		p.CFrame = base
		p.Parent = model
		top = math.max(top, q[5] + q[2] / 2)
		local rb = opts.mutation == "Rainbow" and q[13] ~= "Neon" and not isFace(col)
		table.insert(info.parts, { part = p, base = base, tag = q[14], rainbow = rb, phase = q[4] * 0.05 + q[5] * 0.08 })
	end
	info.top = top
	-- effects: one attachment above the back, plus a light for Epic and up
	local col = PB.RARITY_COLOR[def.rarity] or Color3.new(1, 1, 1)
	local at = Instance.new("Attachment")
	at.Name = "FX"
	at.Position = Vector3.new(0, top * 0.6, 0)
	at.Parent = root
	for _, f in ipairs(def.fx) do
		if FX[f] then
			FX[f](at, col, top)
		end
	end
	local tierIndex = table.find({ "Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic", "Secret", "Divine" }, def.rarity) or 1
	if table.find(def.fx, "light") or tierIndex >= 4 then
		local l = Instance.new("PointLight")
		l.Color = def.rarity == "Secret" and Color3.fromRGB(255, 0, 160) or col
		l.Range = 8 + tierIndex * 2
		l.Brightness = 1 + tierIndex * 0.2
		l.Parent = at
	end
	if table.find(def.fx, "aura") or tierIndex >= 5 then
		local ring = Instance.new("Attachment")
		ring.Name = "Aura"
		ring.Position = Vector3.new(0, 0.3, 0)
		ring.Parent = root
		emitter(ring, { Color = ColorSequence.new(def.rarity == "Secret" and Color3.fromRGB(255, 0, 160) or col), Rate = 10 + tierIndex * 3,
			Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
			Speed = NumberRange.new(0.5, 1), Acceleration = Vector3.new(0, 3, 0), SpreadAngle = Vector2.new(0, 0),
			EmissionDirection = Enum.NormalId.Top, Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(1, 0) }) })
	end
	if table.find(def.fx, "rays") then
		local r = Instance.new("Attachment")
		r.Name = "Rays"
		r.Position = Vector3.new(0, top * 0.55, 0)
		r.Parent = root
		emitter(r, { Texture = "rbxasset://textures/particles/sparkles_main.dds", Color = ColorSequence.new(col), Rate = 3, Lifetime = NumberRange.new(1.5),
			Speed = NumberRange.new(0), Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.5, top * 0.9), NumberSequenceKeypoint.new(1, 0) }),
			Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.75), NumberSequenceKeypoint.new(1, 1) }),
			RotSpeed = NumberRange.new(20, 40), Rotation = NumberRange.new(0, 360) })
	end
	local k = PB.SIZES[opts.size or "Normal"] or 1
	if k ~= 1 then
		model:ScaleTo(k)
		info.scale = k
		for _, e in ipairs(info.parts) do
			e.base = e.base - e.base.Position + e.base.Position * k
		end
		info.top = top * k
	end
	model:SetAttribute("Rarity", def.rarity)
	model:SetAttribute("PetId", def.id)
	if opts.income then
		PB.billboard(model, def, opts)
	end
	return model
end

-- ------------------------------------------------------------ floating name + income
local function fmt(n)
	local s = { "", "K", "M", "B", "T", "Qa", "Qi" }
	local i = 1
	while n >= 1000 and i < #s do
		n = n / 1000
		i = i + 1
	end
	return (n >= 100 and string.format("%d", n) or string.format("%.1f", n):gsub("%.0$", "")) .. s[i]
end
PB.fmt = fmt

function PB.billboard(model, def, opts)
	local info = registry[model]
	local bb = Instance.new("BillboardGui")
	bb.Name = "PetTag"
	bb.Size = UDim2.fromOffset(220, 74)
	bb.StudsOffsetWorldSpace = Vector3.new(0, (info and info.top or 6) + 1.6, 0)
	bb.AlwaysOnTop = true
	bb.MaxDistance = 90
	bb.LightInfluence = 0
	local function line(name, y, h, text, col, font)
		local t = Instance.new("TextLabel")
		t.Name = name
		t.BackgroundTransparency = 1
		t.Size = UDim2.fromScale(1, h)
		t.Position = UDim2.fromScale(0, y)
		t.Font = font or Enum.Font.FredokaOne
		t.TextScaled = true
		t.Text = text
		t.TextColor3 = col
		local st = Instance.new("UIStroke")
		st.Thickness = 2.5
		st.Color = Color3.fromRGB(20, 16, 34)
		st.Parent = t
		t.Parent = bb
		return t
	end
	local rc = PB.RARITY_COLOR[def.rarity]
	local tags = {}
	if opts.size and opts.size ~= "Normal" then
		table.insert(tags, opts.size)
	end
	if opts.mutation then
		table.insert(tags, opts.mutation)
	end
	local rar = line("Rarity", 0, 0.28, (#tags > 0 and (table.concat(tags, " ") .. " ") or "") .. def.rarity, rc)
	local nm = line("PetName", 0.26, 0.4, def.name, Color3.new(1, 1, 1))
	line("Income", 0.66, 0.34, "$" .. fmt(opts.income) .. "/s", Color3.fromRGB(110, 255, 110))
	if def.rarity == "Secret" then
		rar.TextColor3 = Color3.new(1, 1, 1)
		rar:FindFirstChildOfClass("UIStroke").Color = Color3.fromRGB(255, 0, 160)
	end
	local tier = table.find({ "Legendary", "Mythic", "Secret", "Divine" }, def.rarity)
	if tier or opts.mutation == "Rainbow" then
		local g = Instance.new("UIGradient")
		g.Name = "Shine"
		g.Color = opts.mutation == "Rainbow" and ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 80, 80)), ColorSequenceKeypoint.new(0.25, Color3.fromRGB(255, 220, 60)),
			ColorSequenceKeypoint.new(0.5, Color3.fromRGB(80, 255, 120)), ColorSequenceKeypoint.new(0.75, Color3.fromRGB(80, 180, 255)), ColorSequenceKeypoint.new(1, Color3.fromRGB(220, 90, 255)) })
			or ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.new(1, 1, 1)), ColorSequenceKeypoint.new(0.5, rc), ColorSequenceKeypoint.new(1, Color3.new(1, 1, 1)) })
		g.Parent = nm
	end
	bb.Parent = model.PrimaryPart
	return bb
end

-- ------------------------------------------------------------ idle animation (client)
function PB.animate(model, t)
	local info = registry[model]
	if not info then
		return
	end
	local root = model.PrimaryPart.CFrame
	local bob = math.abs(math.sin(t * 2.4)) * 0.25 * (info.scale or 1)
	local breathe = 1 + math.sin(t * 2.4) * 0.015
	for _, e in ipairs(info.parts) do
		local b = e.base
		local tag = e.tag
		local cf
		if tag == "WingL" or tag == "WingR" then
			local s = tag == "WingL" and -1 or 1
			local a = math.sin(t * 7) * 0.35
			local pivot = CFrame.new(0, b.Position.Y, b.Position.Z)
			cf = pivot * CFrame.Angles(0, 0, a * s) * pivot:Inverse() * b
		elseif tag == "Tail" then
			cf = CFrame.Angles(0, math.sin(t * 4) * 0.12, 0) * b
		elseif tag == "Head" then
			cf = CFrame.new(0, math.sin(t * 2.4 + 0.6) * 0.08, 0) * b
		elseif tag == "Float" then
			cf = CFrame.new(0, math.sin(t * 1.8) * 0.4, 0) * b
		elseif tag == "Spin" then
			cf = CFrame.Angles(0, t * 1.5, 0) * b
		elseif tag == "ArmL" or tag == "ArmR" then
			cf = CFrame.new(0, math.sin(t * 2.4 + (tag == "ArmL" and 0 or math.pi)) * 0.1, 0) * b
		elseif tag == "Glow" then
			cf = b * CFrame.new(0, math.sin(t * 9 + e.phase * 10) * 0.08, 0)
		else
			cf = b
		end
		e.part.CFrame = root * CFrame.new(0, bob, 0) * cf
		if e.rainbow then
			e.part.Color = Color3.fromHSV((t * 0.25 + e.phase) % 1, 0.7, 1)
		end
	end
	local tag = model.PrimaryPart:FindFirstChild("PetTag")
	local g = tag and tag:FindFirstChild("PetName") and tag.PetName:FindFirstChild("Shine")
	if g then
		g.Offset = Vector2.new(math.sin(t * 1.5) * 0.6, 0)
	end
end

return PB
