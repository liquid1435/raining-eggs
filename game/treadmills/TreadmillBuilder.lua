--!strict
-- Construiește un treadmill din TreadmillData (Part-uri simple, ancorate).
-- Folosire:
--   local Builder = require(ReplicatedStorage.Shared.TreadmillBuilder)
--   local model = Builder.buildById("Dragon", CFrame.new(0, 0, 0))
--   model.Parent = workspace
--   Builder.setBeltSpeed(model, 14)

local TreadmillData = require(script.Parent.TreadmillData)

local Builder = {}

local byId: { [string]: any } = {}
for _, def in ipairs(TreadmillData) do
	byId[def.Id] = def
end

local function partCFrame(p): CFrame
	local cf = CFrame.new(p.pos[1], p.pos[2], p.pos[3])
	for _, r in ipairs(p.rot) do
		local a = math.rad(r[2])
		if r[1] == "X" then
			cf *= CFrame.Angles(a, 0, 0)
		elseif r[1] == "Y" then
			cf *= CFrame.Angles(0, a, 0)
		else
			cf *= CFrame.Angles(0, 0, a)
		end
	end
	return cf
end

-- Returnează lista tuturor modelelor (în ordinea 1..20).
function Builder.list()
	return TreadmillData
end

function Builder.get(id: string)
	return byId[id]
end

-- pivot = unde ajunge centrul bazei (pe sol). Consola privește spre +X-ul pivotului.
function Builder.build(def, pivot: CFrame?): Model
	local model = Instance.new("Model")
	model.Name = "Treadmill_" .. def.Id
	model:SetAttribute("TreadmillId", def.Id)
	model:SetAttribute("DisplayName", def.Name)
	model:SetAttribute("Rarity", def.Rarity)
	model:SetAttribute("Index", def.Index)

	local bodyMaterial = (Enum.Material :: any)[def.Material] or Enum.Material.SmoothPlastic
	local decorCount = 0

	for _, p in ipairs(def.Parts) do
		local part = Instance.new("Part")
		if p.role == "Part" then
			decorCount += 1
			part.Name = "Decor" .. decorCount
		else
			part.Name = p.role
		end
		part.Anchored = true
		part.Size = Vector3.new(p.size[1], p.size[2], p.size[3])
		part.CFrame = partCFrame(p)
		part.Color = Color3.fromHex(p.color)
		part.Material = if p.neon then Enum.Material.Neon else bodyMaterial
		part.TopSurface = Enum.SurfaceType.Smooth
		part.BottomSurface = Enum.SurfaceType.Smooth
		-- Doar baza, corpul și banda au coliziune; decorul nu încurcă jucătorul.
		part.CanCollide = p.role ~= "Part"
		part.CanQuery = p.role ~= "Part"
		part.CastShadow = not p.neon
		part.Parent = model
	end

	local base = model:FindFirstChild("Base") :: BasePart
	model.PrimaryPart = base
	model.WorldPivot = CFrame.new(0, 0, 0)
	if pivot then
		model:PivotTo(pivot)
	end
	return model
end

function Builder.buildById(id: string, pivot: CFrame?): Model
	local def = byId[id]
	assert(def, "Treadmill necunoscut: " .. tostring(id))
	return Builder.build(def, pivot)
end

-- Face banda să „curgă” spre spatele treadmill-ului (efect de bandă rulantă).
-- speed în studs/secundă; 0 oprește banda.
function Builder.setBeltSpeed(model: Model, speed: number)
	local belt = model:FindFirstChild("Belt") :: BasePart?
	if not belt then
		return
	end
	belt.AssemblyLinearVelocity = -belt.CFrame.RightVector * speed
	model:SetAttribute("BeltSpeed", speed)
end

return Builder
