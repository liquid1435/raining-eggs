-- Client-side coats for the 50 V2 UV atlases. Import PetCoatMaps alongside this module.
local AssetService = game:GetService("AssetService")
local EncodingService = game:GetService("EncodingService")
local RunService = game:GetService("RunService")
local Coat = {}
local models, groups, palettes = {}, {}, {}
local heartbeat
local period = 1 / 12
local white = Color3.new(1, 1, 1)

local function channels(tier, phase)
	local h = phase / 256
	local value = 1
	local saturation = 1
	if tier == "Gold" then
		local d = math.abs(h - .5)
		value = .5 + .5*d + .9*(1 - 2*d)^18
		saturation = 1 - .2*d
		h = .115 + .03*d
	end
	local c = Color3.fromHSV(h, saturation, 1)
	return (c.R*value)^(1/2.2), (c.G*value)^(1/2.2), (c.B*value)^(1/2.2)
end

local function palette(tier)
	if palettes[tier] then return palettes[tier] end
	-- Repeat each phase row so a moving offset needs no modulus inside the pixel loop.
	local lut = buffer.create(256*512*4)
	for phase = 0, 255 do
		local r, g, b = channels(tier, phase)
		for lum = 0, 255 do
			local chroma = math.clamp((lum-24)/32, 0, 1)*math.clamp((255-lum)/12, 0, 1)
			local value = lum + 52*(1-lum/255)*chroma
			if tier == "Gold" then -- v138: brighter, warmer gold (the sheet looked olive)
				value = math.min(255, 46 + lum*0.95 + 40*(1-lum/255)*chroma)
				chroma = math.max(chroma, 0.85)
			end
			local function channel(c)
				return math.clamp(math.round(value*(1 + chroma*(c-1))), 0, 255)
			end
			local pixel = channel(r) + channel(g)*256 + channel(b)*65536 + 0xff000000
			local offset = (lum*512 + phase)*4
			buffer.writeu32(lut, offset, pixel)
			buffer.writeu32(lut, offset+1024, pixel)
		end
	end
	palettes[tier] = lut
	return lut
end

local function readMap(name)
	local folder = script.Parent:FindFirstChild("PetCoatMaps")
	local entry = folder and folder:FindFirstChild(name)
	if not entry then return {} end
	local dims, bones, start = entry.Value:match("^([%d,]+);([%d,]+);()")
	if not start then return {} end
	local w,h,y,rows = dims:match("^(%d+),(%d+),(%d+),(%d+)$")
	return {entry=entry, start=start, size=Vector2.new(tonumber(w),tonumber(h)),
		origin=Vector2.new(0,tonumber(y)), region=Vector2.new(tonumber(w),tonumber(rows)),
		bones=string.split(bones,",")}
end

local function makeImage(g)
	local map = g.map
	if not map.entry then return false end
	local image = AssetService:CreateEditableImage({Size=map.size})
	if not image then return false end
	g.image = image -- kept here so a partial initialization can be undone
	local encoded = buffer.fromstring(map.entry.Value:sub(map.start))
	local raw = EncodingService:DecompressBuffer(EncodingService:Base64Decode(encoded), Enum.CompressionAlgorithm.Zstd)
	local count = map.region.X * map.region.Y
	assert(buffer.len(raw) == 2*count)
	local indices = buffer.create(4*count)
	for i = 0, count-1 do
		local phase = buffer.readu8(raw,i*2)
		local lum = buffer.readu8(raw,i*2+1)
		buffer.writeu32(indices,i*4,(lum*512 + 256 + (phase*2)%256)*4)
	end
	g.indices, g.pixels, g.lut = indices, buffer.create(4*count), palette(g.tier)
	g.content = Content.fromObject(image)
	return true
end

local function paint(g, step)
	local pixels, indices, lut = g.pixels, g.indices, g.lut
	for i = 0, buffer.len(pixels)-4, 4 do
		buffer.writeu32(pixels,i,buffer.readu32(lut,buffer.readu32(indices,i)-step*4))
	end
	g.image:WritePixelsBuffer(g.map.origin,g.map.region,pixels)
end

local function restore(p)
	if p.bound then
		p.target[p.property] = p.original
		p.bound = false
	end
	p.tint.Color = p.color
end

local function release(g)
	for state in g.members do
		for _,p in state.parts do
			if p.bound then restore(p) end
			p.rejected = false
		end
	end
	if g.image then g.image:Destroy() end
	g.image, g.indices, g.pixels, g.content = nil, nil, nil, nil
end

local function addPart(state, mesh)
	if not mesh:IsA("MeshPart") or state.parts[mesh] then return end
	local surface = mesh:FindFirstChildOfClass("SurfaceAppearance")
	local target = surface or mesh
	local property = surface and "ColorMapContent" or "TextureContent"
	local ok, original = pcall(function() return target[property] end)
	local index = tonumber(mesh.Name:match("^Part(%d+)$"))
	local bones = state.group.map.bones
	local phase = index and bones and tonumber(bones[index])
	if not phase then
		local localPos = state.frame:PointToObjectSpace(mesh.Position)
		phase = math.clamp(.5+(-localPos.Z+.545*localPos.Y)/state.extent,0,1)*255
	end
	state.parts[mesh] = {target=target, tint=target, property=property, original=original,
		readable=ok, color=target.Color, phase=math.round(phase)*2}
end

local function display(state, step)
	local g = state.group
	for _,p in state.parts do
		if g.content and p.readable and not p.bound and not p.rejected then
			p.bound = pcall(function() p.target[p.property] = g.content end)
			p.rejected = not p.bound
			if p.bound then p.tint.Color = white end
		end
		if not p.bound then
			local r,gc,b = channels(g.tier,(p.phase-step)%256)
			p.tint.Color = Color3.new(math.min(1,r),math.min(1,gc),math.min(1,b))
		end
	end
end

local function visible(state, camera)
	if not state.model:IsDescendantOf(workspace) then return false end
	local pos = state.model:GetPivot().Position
	if (pos-camera.CFrame.Position).Magnitude > 100 + state.extent then return false end
	local point = camera.CFrame:PointToObjectSpace(pos)
	local depth, margin = -point.Z, state.extent
	local halfH = math.tan(math.rad(camera.FieldOfView)*.5)
	local size = camera.ViewportSize
	return depth > -margin and math.abs(point.Y) <= math.max(0,depth)*halfH+margin
		and math.abs(point.X) <= math.max(0,depth)*halfH*size.X/math.max(size.Y,1)+margin
end

local function tickCoats()
	local camera = workspace.CurrentCamera
	if not camera then return end
	local now = os.clock()
	local chosen
	for _,g in groups do
		if now >= g.nextUpdate then
			local near = false
			for state in g.members do
				state.visible = visible(state,camera)
				near = near or state.visible
			end
			if near then
				g.lastSeen = now
				if not chosen or g.nextUpdate < chosen.nextUpdate then chosen = g end
			else
				g.nextUpdate = now+period
				if g.image and now-g.lastSeen > 3 then release(g) end
			end
		end
	end
	-- Roblox presents one changing EditableImage per frame. Serve the oldest due group.
	if not chosen then return end
	local g = chosen
	g.nextUpdate = now + period - .001
	local step = math.floor(now*.55*256)%256
	if not g.image and now >= g.retry then
		local ok, made = pcall(makeImage,g)
		if not ok or not made then
			release(g)
			g.retry = now+10
		end
	end
	if g.image and not pcall(paint,g,step) then
		release(g)
		g.retry = now+10
	end
	for state in g.members do
		if state.visible then display(state,step) end
	end
end

function Coat.clear(model)
	local s = models[model]
	if not s then return end
	for _,c in s.connections do c:Disconnect() end
	for _,p in s.parts do restore(p) end
	local g = s.group
	models[model], g.members[s] = nil, nil
	if not next(g.members) then
		release(g)
		groups[g.key] = nil
	end
	if not next(models) then heartbeat:Disconnect(); heartbeat = nil end
end

function Coat.apply(model, petName, tier)
	local key = petName.."/"..tier
	local old = models[model]
	if old and old.group.key == key then return end
	Coat.clear(model)
	if tier ~= "Rainbow" and tier ~= "Gold" then return end
	local g = groups[key]
	if not g then
		g = {key=key,tier=tier,map=readMap(petName),members={},nextUpdate=0,retry=0}
		groups[key] = g
	end
	local size = model:IsA("Model") and model:GetExtentsSize() or model.Size
	local s = {model=model,group=g,parts={},connections={},extent=math.max(size.Magnitude,1),
		frame=model:GetPivot()*CFrame.Angles(0,model:GetAttribute("AnimYaw") or 0,0)}
	models[model], g.members[s] = s, true
	addPart(s,model)
	for _,obj in model:GetDescendants() do addPart(s,obj) end
	local function refreshSurface(surface)
		local mesh = surface.Parent
		if mesh and s.parts[mesh] then
			restore(s.parts[mesh])
			s.parts[mesh] = nil
			addPart(s,mesh)
		end
	end
	table.insert(s.connections,model.DescendantAdded:Connect(function(obj)
		if obj:IsA("SurfaceAppearance") then refreshSurface(obj) else addPart(s,obj) end
	end))
	table.insert(s.connections,model.DescendantRemoving:Connect(function(obj)
		if s.parts[obj] then restore(s.parts[obj]); s.parts[obj] = nil end
		if obj:IsA("SurfaceAppearance") and s.parts[obj.Parent] then
			local mesh = obj.Parent
			restore(s.parts[mesh])
			s.parts[mesh] = nil
			task.defer(function()
				if models[model] == s and (mesh == model or mesh:IsDescendantOf(model)) then addPart(s,mesh) end
			end)
		end
	end))
	table.insert(s.connections,model.Destroying:Connect(function() Coat.clear(model) end))
	table.insert(s.connections,model.AncestryChanged:Connect(function(_,parent)
		if parent == nil then Coat.clear(model) end
	end))
	if not heartbeat then heartbeat = RunService.Heartbeat:Connect(tickCoats) end
end

return Coat
