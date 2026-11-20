local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Lighting = game:GetService("Lighting")
local Debris = game:GetService("Debris")
local FX = require(script.Parent.FX)
local GeometryService = game:GetService("GeometryService")
local VFX = {ClaimDuration = 5, ShowRing = true, RingDistance = 42}
local rng = Random.new()
local current = nil
local crater = nil
-- v122 (user: 'instead of earth put cosmic earth'): world 2 (high above the map) gets a cosmic crater
local cosmic = false
local function cc(normal, space) return if cosmic then space else normal end
local gui = nil
local shakeEnd = 0
local unshake = CFrame.identity
local shakenCamera = nil
local shakeActive = false

local function shake(pos)
	local camera = workspace.CurrentCamera
	if not camera then return end
	local strength = math.clamp(1 - (camera.CFrame.Position - pos).Magnitude / 85, 0, 1)
	if strength == 0 then return end
	shakeEnd = os.clock() + 0.44
	if shakeActive then return end
	shakeActive = true
	RunService:BindToRenderStep("BigEggRemoveShake", Enum.RenderPriority.Camera.Value - 1, function()
		if shakenCamera then shakenCamera.CFrame *= unshake end
		shakenCamera = nil
	end)
	RunService:BindToRenderStep("BigEggApplyShake", Enum.RenderPriority.Camera.Value + 1, function()
		local remaining = shakeEnd - os.clock()
		if remaining <= 0 then
			RunService:UnbindFromRenderStep("BigEggRemoveShake")
			RunService:UnbindFromRenderStep("BigEggApplyShake")
			shakeActive = false
			return
		end
		local cam = workspace.CurrentCamera
		if cam then
			local delta = CFrame.new(math.noise(remaining*37, 2), math.noise(remaining*39, 7), 0)
			local offset = CFrame.identity:Lerp(delta, strength * remaining)
			cam.CFrame *= offset
			shakenCamera, unshake = cam, offset:Inverse()
		end
	end)
end

local function banner(title, subtitle)
	if gui then gui:Destroy() end
	gui = Instance.new("ScreenGui")
	gui.Name = "BigEggBanner"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 20
	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	local bar = Instance.new("Frame")
	bar.Size = UDim2.fromScale(1, 0.15)
	bar.BackgroundColor3 = FX.plum
	bar.BorderSizePixel = 0
	bar.Parent = gui
	local line = Instance.new("Frame")
	line.Size = UDim2.new(1, 0, 0, 3)
	line.Position = UDim2.fromScale(0, 1)
	line.BorderSizePixel = 0
	line.BackgroundColor3 = FX.gold
	line.Parent = bar
	local main = FX.label(bar, UDim2.fromScale(1, 0.64))
	main.Text = title
	local small = FX.label(bar, UDim2.fromScale(1, 0.29))
	small.Position = UDim2.fromScale(0, 0.64)
	small.TextColor3 = FX.teal
	small.Text = subtitle
	return gui, small
end

local function run(state, fn)
	local conn
	conn = RunService.RenderStepped:Connect(function()
		if state ~= current or fn(os.clock()) == false then conn:Disconnect() end
	end)
	table.insert(state.connections, conn)
end

local function stopClaim(s)
	if s.claimTrack then s.claimTrack:Stop(.14) end
	s.claimTrack, s.claimant = nil, nil
end

local function characterClip(character, name, looped, fade)
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if humanoid then
		return FX.clip(humanoid:FindFirstChildOfClass("Animator"), script:GetAttribute(name..humanoid.RigType.Name), looped, fade)
	end
	return nil
end

local function clearPresentation()
	if gui then gui:Destroy() gui = nil end
	if current then
		stopClaim(current)
		if current.celebration and current.celebration.IsPlaying then current.celebration:Stop(.12) end
		if current.stretchRoot and current.stretchRoot.Parent then current.stretchRoot.Size = current.restSize end
		for _, conn in ipairs(current.connections) do conn:Disconnect() end
		for _, item in ipairs(current.items) do item:Destroy() end
		for part, alpha in pairs(current.hidden) do
			if part.Parent then part.LocalTransparencyModifier = alpha end
		end
		if current.egg and current.egg.Parent and current.original then current.egg:PivotTo(current.original) end
		current = nil
	end
end

function VFX.Clear()
	clearPresentation()
	if crater then
		crater.model:Destroy()
		if crater.surface and crater.surface.Parent then
			crater.surface.LocalTransparencyModifier = crater.originalAlpha
			if crater.originalCollide ~= nil then crater.surface.CanCollide = crater.originalCollide end
		end
		crater = nil
	end
end

local function state()
	if not current then current = {items = {}, connections = {}, hidden = {}} end
	return current
end

local function own(s, item)
	table.insert(s.items, item)
	return item
end

function VFX.PlayIncoming(pos)
	VFX.Clear()
	local s = state()
	local screen, label = banner("BIG EGG INCOMING!", "DROP IN   10")
	local tint = own(s, Instance.new("ColorCorrectionEffect"))
	tint.Parent = Lighting
	FX.tween(tint, 1.3, {Brightness = -0.13, TintColor = Color3.fromRGB(192, 204, 255)})
	local marker = own(s, FX.anchor(pos + Vector3.yAxis * 0.12, 12))
	local pulse = FX.ring(marker, 8, 0.26, FX.teal)
	FX.ring(marker, 6.8, 0.11, FX.cream)
	local start = os.clock()
	run(s, function(now)
		local t = now - start
		if t >= 10 then screen:Destroy() marker:Destroy() return false end
		label.Text = string.format("DROP IN   %02d", math.ceil(10 - t))
		pulse(8 + 0.5 * math.sin(t * 5), 0.18)
	end)
end

function VFX.PlayFall(egg, pos)
	local s = state()
	local root = FX.root(egg)
	if not root or s.egg then return end
	s.egg, s.original = egg, egg:GetPivot()
	local cf, size
	if egg:IsA("Model") then cf, size = egg:GetBoundingBox() else cf, size = egg.CFrame, egg.Size end
	local base = pos + Vector3.yAxis * (s.original.Position.Y - cf.Position.Y + size.Y / 2)
	s.shellSize = size
	local rotation = s.original.Rotation
	-- Imported shell MeshParts and single-part Models share the same local deformation.
	local single = true
	for _, child in egg:GetDescendants() do
		if child:IsA("BasePart") and child ~= root then single = false break end
	end
	if single then s.stretchRoot, s.restSize = root, root.Size end
	local a = own(s, FX.attach(root, Vector3.xAxis * root.Size.X * -0.32))
	local b = own(s, FX.attach(root, Vector3.xAxis * root.Size.X * 0.32))
	local trail = own(s, FX.trail(root, a, b, FX.gold))
	local fire = own(s, FX.emitter(a, FX.gold, 2, "rbxasset://textures/particles/fire_main.dds"))
	fire.Rate = 85
	local aura = own(s, FX.emitter(b, FX.teal, 0.8))
	local light = own(s, Instance.new("PointLight"))
	light.Color, light.Range, light.Parent = FX.gold, 22, root
	local top = own(s, FX.attach(root, Vector3.yAxis * 90))
	local center = own(s, FX.attach(root, Vector3.zero))
	local beam = own(s, Instance.new("Beam"))
	beam.Attachment0, beam.Attachment1 = center, top
	beam.Width0, beam.Width1 = 1.2, 3
	beam.FaceCamera, beam.LightEmission = true, 1
	beam.Transparency = NumberSequence.new(0.55, 1)
	beam.Color = ColorSequence.new(FX.cream, FX.teal)
	beam.Enabled, beam.Parent = false, root
	local halo = own(s, beam:Clone())
	halo.Width0, halo.Width1 = size.X*.52, size.X*1.35
	halo.Transparency = NumberSequence.new(.89,1)
	halo.Parent = root
	local cinders = own(s, FX.emitter(center, FX.coral, .29, "rbxasset://textures/particles/fire_main.dds"))
	cinders.Acceleration, cinders.Rate = Vector3.yAxis*8, 40
	local start = os.clock()
	local function animate(now)
		if not egg.Parent then VFX.Clear() return false end
		local t = now - start
		local p = math.min(1, t / 1.4)
		local air = 1 - p*p
		local sink = math.clamp((t - 1.4) / .09, 0, 1)
		local age = math.max(0, t-1.4)
		local envelope = math.exp(-5.2*age)
		local stretch = .09*p*p*(1-sink) - .19*envelope*math.sin(18*age)
		if s.stretchRoot and t < 3 then
			local axial = 1+stretch
			local radial = 1/math.sqrt(axial)
			root.Size = s.restSize * Vector3.new(radial, axial, radial)
		elseif s.stretchRoot and root.Size ~= s.restSize then
			root.Size = s.restSize
		end
		local bob = size.Y*.012*math.sin(age*2.8)*(1-envelope)
		egg:PivotTo(CFrame.new(base + Vector3.new(24*air, 260*air - size.Y/3 * sink + bob, 0))
			* rotation * CFrame.Angles(0, 1.35*p, .22*envelope*math.sin(age*14)))
		if p == 1 and trail.Enabled then
			trail.Enabled, fire.Enabled, beam.Enabled = false, false, true
			aura.Rate = 14
			halo.Enabled, cinders.Rate = true, 0
		end
		light.Brightness = 2.2 + math.sin(t*3)*0.8
	end
	animate(start)
	run(s, animate)
end

local function fragments(pos, count, confetti, radius)
	local colors = {FX.gold, FX.coral, FX.teal, FX.cream}
	for i = 1, count do
		local color = if confetti then colors[(i-1)%4+1] else cc(Color3.fromRGB(157, 111, 77), Color3.fromRGB(80, 52, 150))
		local size = if confetti then Vector3.new(.32,.05,.55) else Vector3.one*rng:NextNumber(.35,1.1)
		local part = FX.part(workspace, "EggFragment", size, CFrame.new(pos), color)
		part.Material = if confetti then Enum.Material.SmoothPlastic else Enum.Material.Slate
		local a = rng:NextNumber(0, 2*math.pi)
		local velocity = Vector3.new(math.cos(a)*rng:NextNumber(5,16),rng:NextNumber(9,22),math.sin(a)*rng:NextNumber(5,16))
		local origin = pos + Vector3.new(math.cos(a), 0, math.sin(a)) * (radius or 0)
		part.Position = origin
		local life = if confetti then 2.5 else 1.65
		local start = os.clock()
		local s = state()
		own(s, part)
		run(s, function()
			local t = os.clock()-start
			if t >= life then part:Destroy() return false end
			local offset = velocity*t - Vector3.yAxis*(if confetti then 7 else 17)*t*t
			if confetti then
				local drift = Vector3.new(math.sin(t*6+a)-math.sin(a),0,math.cos(t*4+a)-math.cos(a))
				offset += drift * math.min(1,t)*.65
			end
			local y = math.max(0, offset.Y)
			if not confetti then
				local rebound = math.max(0, t - velocity.Y/17)
				y += math.max(0, rebound*(velocity.Y*.39 - 17*rebound))
			end
			part.CFrame = CFrame.new(origin+Vector3.new(offset.X, y, offset.Z))*CFrame.Angles(t*5,a+t*3,t*4)
			part.Transparency = math.clamp(t/life*3-2,0,1)
		end)
	end
end

local function buildCrater(s, pos)
	local size = s.shellSize or Vector3.new(8, 10, 8)
	local radius = math.max(size.X, size.Z) * .71
	local depth = size.Y * .41
	local model = Instance.new("Model")
	model.Name, model.Parent = "BigEggCrater", workspace
	local hole = {model = model}
	crater = hole

	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = if s.egg then {s.egg} else {}
	local hit = workspace:Raycast(pos + Vector3.yAxis * .45, -Vector3.yAxis * .95, params)
	local soil = cc(Color3.fromRGB(84, 54, 46), Color3.fromRGB(40, 24, 80))
	local lip = if hit then hit.Instance.Color else Color3.fromRGB(153, 111, 76)
	local function disk(name, y, thickness, color)
		local cf = CFrame.new(pos + Vector3.yAxis*y) * CFrame.Angles(0, 0, math.pi/2)
		local part = FX.part(model, name, Vector3.new(thickness, radius*2, radius*2), cf, color)
		part.Shape, part.Material = Enum.PartType.Cylinder, Enum.Material.Ground
		return part
	end
	local floor = disk("Crater floor", -depth, .4, soil)
	floor.CanCollide, floor.CanQuery = true, true
	local decal = Instance.new("Decal")
	decal.Face = Enum.NormalId.Right
	decal.Texture = script:GetAttribute("ScorchTexture") or "rbxasset://textures/particles/smoke_main.dds"
	decal.Color3, decal.Transparency, decal.Parent = soil, .28, floor

	-- (v2, user: "more professional and realistic") earth walls, a raised soil mound, broken pieces of the
	-- surface tilted up around the lip, radial cracks, scattered stones, dirt splashes and slow settling dust.
	local dirt = cc(Color3.fromRGB(110, 76, 52), Color3.fromRGB(80, 52, 150))
	local darkDirt = cc(Color3.fromRGB(62, 42, 30), Color3.fromRGB(26, 16, 56))
	local crackCol = cc(darkDirt, Color3.fromRGB(90, 230, 255)) -- cosmic: glowing cracks
	local crackMat = cc(Enum.Material.Slate, Enum.Material.Neon)
	local function solid(p, mat)
		p.Material = mat
		p.CanCollide, p.CanQuery = true, true -- solid: nobody walks or looks through the crater (user, 19 Nov)
		p.CastShadow = true
		return p
	end
	-- (v3, user: "like before, just more details") the original look: earth walls sloping down to the floor and
	-- big fractured capstones of the surface tilted up on the lip; plus a second ring of smaller broken pieces,
	-- rubble between the slabs and dark earth showing under every slab
	for i = 1, 24 do
		local angle = i * math.pi / 12
		local outward = Vector3.new(math.cos(angle), 0, math.sin(angle))
		local bottom = pos + outward*(radius*.49) - Vector3.yAxis*depth
		local top = pos + outward*radius
		local span = top-bottom
		solid(FX.part(model, "Exposed earth", Vector3.new(radius*.27,.25,span.Magnitude),
			CFrame.lookAt((bottom+top)/2, top), soil:Lerp(lip, rng:NextNumber(.09,.34))), Enum.Material.Ground)
		local cf = CFrame.lookAt(top, top+outward) * CFrame.Angles(rng:NextNumber(-.55,-.22), 0, rng:NextNumber(-.24,.24))
		local size = Vector3.new(radius*rng:NextNumber(.20,.27), radius*rng:NextNumber(.08,.16), radius*rng:NextNumber(.19,.32))
		local rock = solid(FX.part(model, "Fractured rim", size, cf, lip:Lerp(soil,rng:NextNumber(.07,.42))), Enum.Material.Slate)
		FX.tween(rock, .13, {CFrame = cf + Vector3.yAxis*radius*rng:NextNumber(.04,.11)})
		-- dark earth under the lifted slab
		solid(FX.part(model, "Slab earth", Vector3.new(size.X*.95, size.Y*.6, size.Z*.7), cf * CFrame.new(0, -size.Y*.55, size.Z*.1), darkDirt), Enum.Material.Ground)
		-- rubble chips in the gap to the next slab
		for j = 1, 3 do
			local a = angle + math.pi / 24 + rng:NextNumber(-.06, .06)
			local o = Vector3.new(math.cos(a), 0, math.sin(a))
			local c = rng:NextNumber(.25, .6)
			solid(FX.part(model, "Rubble", Vector3.new(c, c*.6, c*.9), CFrame.new(pos + o*radius*rng:NextNumber(.95, 1.12) + Vector3.yAxis*c*.25)
				* CFrame.Angles(rng:NextNumber(0, 3), rng:NextNumber(0, 3), rng:NextNumber(0, 3)), lip:Lerp(darkDirt, rng:NextNumber(.1, .6))), Enum.Material.Slate)
		end
	end
	-- second ring: smaller broken pieces pushed further out
	for i = 1, 20 do
		local angle = i * math.pi / 10 + rng:NextNumber(-.1, .1)
		local outward = Vector3.new(math.cos(angle), 0, math.sin(angle))
		local top = pos + outward*radius*rng:NextNumber(1.18, 1.35)
		local cf = CFrame.lookAt(top, top+outward) * CFrame.Angles(rng:NextNumber(-.4,-.12), rng:NextNumber(-.3, .3), rng:NextNumber(-.3,.3))
		local size = Vector3.new(radius*rng:NextNumber(.1,.16), radius*rng:NextNumber(.05,.09), radius*rng:NextNumber(.1,.17))
		solid(FX.part(model, "Broken surface", size, cf, lip:Lerp(soil, rng:NextNumber(.05, .3))), Enum.Material.Slate)
	end
	-- radial cracks running out over the surface
	for i = 1, 14 do
		local angle = i * math.pi * 2 / 14 + rng:NextNumber(-.15, .15)
		local p0 = radius * rng:NextNumber(1.1, 1.3)
		local len = radius * rng:NextNumber(.6, 1.6)
		local a2 = angle + rng:NextNumber(-.12, .12)
		local a = pos + Vector3.new(math.cos(angle), 0, math.sin(angle)) * p0
		local b = pos + Vector3.new(math.cos(a2), 0, math.sin(a2)) * (p0 + len)
		local mid = (a + b) / 2
		solid(FX.part(model, "Crack", Vector3.new(rng:NextNumber(.18, .35), .06, (b - a).Magnitude), CFrame.lookAt(mid + Vector3.yAxis*.04, b + Vector3.yAxis*.04), crackCol), crackMat)
		-- a small branch
		local c = mid + Vector3.new(math.cos(a2 + 0.7), 0, math.sin(a2 + 0.7)) * len * .3
		solid(FX.part(model, "Crack", Vector3.new(.14, .05, (c - mid).Magnitude), CFrame.lookAt((mid + c) / 2 + Vector3.yAxis*.04, c + Vector3.yAxis*.04), crackCol), crackMat)
	end
	-- scattered stones and dirt splashes further out
	for i = 1, 26 do
		local angle = rng:NextNumber(0, math.pi * 2)
		local d = radius * rng:NextNumber(1.3, 2.4)
		local s = rng:NextNumber(.25, .9)
		local stone = solid(FX.part(model, "Stone", Vector3.new(s, s * .7, s * 1.1), CFrame.new(pos + Vector3.new(math.cos(angle) * d, s * .3, math.sin(angle) * d))
			* CFrame.Angles(rng:NextNumber(0, 3), rng:NextNumber(0, 3), rng:NextNumber(0, 3)), cc(Color3.fromRGB(120, 112, 104), Color3.fromRGB(60, 50, 100)):Lerp(dirt, rng:NextNumber(0, .6))), Enum.Material.Slate)
		stone.Shape = rng:NextNumber() < .5 and Enum.PartType.Ball or Enum.PartType.Block
	end
	for i = 1, 10 do
		local angle = rng:NextNumber(0, math.pi * 2)
		local d = radius * rng:NextNumber(1.25, 1.9)
		local sz = radius * rng:NextNumber(.25, .5)
		local splash = solid(FX.part(model, "Dirt splash", Vector3.new(.08, sz, sz * rng:NextNumber(.6, 1)), CFrame.new(pos + Vector3.new(math.cos(angle) * d, .03, math.sin(angle) * d))
			* CFrame.Angles(0, angle, math.pi / 2), dirt), Enum.Material.Ground)
		splash.Shape = Enum.PartType.Cylinder
		splash.Transparency = .25
	end
	-- dust keeps drifting out of the hole for a few seconds
	local dustA = FX.anchor(pos + Vector3.yAxis * .5, 9)
	local drift = FX.emitter(dustA, cc(Color3.fromRGB(190, 160, 125), Color3.fromRGB(150, 120, 230)), 3.5, "rbxasset://textures/particles/smoke_main.dds")
	drift.LightEmission, drift.Drag, drift.Rate = .02, 2, 14
	drift.Speed = NumberRange.new(1.5, 4)
	drift.Lifetime = NumberRange.new(2, 3.5)
	drift.Transparency = NumberSequence.new({NumberSequenceKeypoint.new(0, .7), NumberSequenceKeypoint.new(1, 1)})
	drift.Size = NumberSequence.new({NumberSequenceKeypoint.new(0, radius * .3), NumberSequenceKeypoint.new(1, radius * .9)})
	task.delay(5, function() drift.Rate = 0 end)

	if hit and hit.Instance:IsA("BasePart") and not hit.Instance:IsA("Terrain") then
		local surface = hit.Instance
		local source = surface:Clone()
		if not source then return radius end
		source:ClearAllChildren()
		local cutter = disk("Excavation volume", -depth*.5, depth+.5, soil)
		cutter.Parent = nil
		task.spawn(function()
			local ok, pieces = pcall(function()
				return GeometryService:SubtractAsync(source, {cutter}, {SplitApart = false})
			end)
			source:Destroy()
			cutter:Destroy()
			if not ok then warn("BigEgg crater cut failed", pieces) return end
			if crater ~= hole or not surface.Parent then
				for _, piece in ipairs(pieces) do piece:Destroy() end
				return
			end
			for _, piece in ipairs(pieces) do
				piece.Anchored, piece.CanCollide, piece.CanTouch, piece.CanQuery = true, true, false, true
				piece.Parent = model
			end
			hole.surface, hole.originalAlpha, hole.originalCollide = surface, surface.LocalTransparencyModifier, surface.CanCollide
			surface.LocalTransparencyModifier = 1
			surface.CanCollide = false -- the cut copy (with the hole) is the solid ground now, on this client
		end)
	end
	return radius
end

function VFX.PlayImpact(pos)
	local s = state()
	if crater then return end
	cosmic = pos.Y > 500
	local radius = buildCrater(s, pos)
	local ground = own(s, FX.anchor(pos + Vector3.yAxis * 0.12, 15))
	local resize = FX.ring(ground, 3, .58, FX.cream)
	local dust = FX.emitter(ground, cc(Color3.fromRGB(206,164,107), Color3.fromRGB(150,120,230)), 4, "rbxasset://textures/particles/smoke_main.dds")
	dust.LightEmission = .07
	dust.Drag = 3
	dust.Size = NumberSequence.new({NumberSequenceKeypoint.new(0,.7),NumberSequenceKeypoint.new(.56,4.3),NumberSequenceKeypoint.new(1,5.7)})
	dust:Emit(35)
	local embers = FX.emitter(ground, FX.gold, .32, "rbxasset://textures/particles/fire_main.dds")
	embers.Acceleration = -Vector3.yAxis*18
	embers.Speed = NumberRange.new(11,25)
	embers:Emit(52)
	local echo = FX.ring(ground, 2, .15, FX.teal)
	local flash = Instance.new("PointLight")
	flash.Range, flash.Brightness, flash.Color, flash.Parent = 50, 12, FX.cream, ground
	FX.tween(flash, .35, {Brightness=0}, Enum.EasingStyle.Exponential)
	for i = 1, 8 do
		local a = i*math.pi/4
		local puff = FX.attach(ground, Vector3.new(math.cos(a),0,math.sin(a))*radius)
		FX.emitter(puff, cc(Color3.fromRGB(180,145,104), Color3.fromRGB(130,100,220)), 3, "rbxasset://textures/particles/smoke_main.dds"):Emit(5)
	end
	fragments(pos, 14, false, radius)
	shake(pos)
	local start = os.clock()
	run(s, function(now)
		local p = math.min(1,(now-start)/.7)
		resize(3+19*(1-(1-p)^2),p)
		echo(2+16*math.sin(p*math.pi/2), .35+.65*p)
		return p<1
	end)
end

local function clearRing(s)
	if s.ring then s.ring:Destroy() s.ring = nil end
end

function VFX.PlayClaimProgress(egg, p, character)
	local s = state()
	local root = FX.root(egg)
	if not root then return end
	if not s.ring or not s.ring.Parent or s.ring.Adornee ~= root then
		clearRing(s)
		local ring = Instance.new("BillboardGui")
		ring.Name = "BigEggClaim"
		ring.Size = UDim2.fromOffset(130,130)
		ring.StudsOffsetWorldSpace = Vector3.zero -- in the middle of the egg (user, 19 Nov)
		ring.AlwaysOnTop, ring.Adornee, ring.Parent = true, root, root
		ring.Enabled = VFX.ShowRing -- the game shows the ProximityPrompt above the egg instead (user, 19 Nov)
		ring.MaxDistance = VFX.RingDistance -- only seen when you are close to the egg (user, 19 Nov)
		s.ring = own(s,ring)
		s.segments = {}
		for i = 1, 48 do
			local a = (i-1)*math.pi/24
			local tile = Instance.new("Frame")
			tile.AnchorPoint = Vector2.one*.5
			tile.Position = UDim2.fromScale(.5+.43*math.sin(a), .5-.43*math.cos(a))
			tile.Size, tile.Rotation = UDim2.fromOffset(7,10), math.deg(a)
			tile.BorderSizePixel, tile.Parent = 0, ring
			s.segments[i] = tile
		end
		s.caption = FX.label(ring, UDim2.fromScale(.54,.48))
		s.caption.Position = UDim2.fromScale(.23,.26)
	end
	p = math.clamp(p,0,1)
	local claimant = if p > 0 then character else nil
	if s.claimant ~= claimant then
		stopClaim(s)
		s.claimant = claimant
		if claimant then s.claimTrack = characterClip(claimant,"Claim",true,.22) end
	end
	s.caption.Text = if p == 0 then "E" else string.format("%d%%",math.floor(p*100))
	for i, tile in ipairs(s.segments) do tile.BackgroundColor3 = if i<=p*48 then FX.teal else FX.plum end
end

function VFX.PlayClaimBreak(egg)
	local s = state()
	if not s.ring or s.ring.Adornee ~= FX.root(egg) then return end
	stopClaim(s)
	local ring = s.ring
	s.ring = nil
	s.caption.Visible = false
	for i,tile in ipairs(s.segments) do
		local a = (i-1)*math.pi/24
		tile.BackgroundColor3 = FX.coral
		FX.tween(tile,.28,{Position=UDim2.fromScale(.5+.64*math.sin(a),.5-.64*math.cos(a)),Rotation=tile.Rotation+35,BackgroundTransparency=1})
	end
	Debris:AddItem(ring,.3)
end

function VFX.PlayWin(egg, playerName, winnerCharacter)
	local pos = egg:GetPivot().Position
	clearPresentation()
	local s = state()
	s.celebration = characterClip(winnerCharacter,"Celebrate",false,.14)
	local function hide(part)
		if part:IsA("BasePart") then
			s.hidden[part] = part.LocalTransparencyModifier
			part.LocalTransparencyModifier = 1
		end
	end
	hide(egg)
	for _, part in ipairs(egg:GetDescendants()) do hide(part) end
	local anchor = own(s,FX.anchor(pos,3))
	FX.emitter(anchor, FX.gold, 3):Emit(90)
	local fountain = FX.emitter(anchor, FX.cream, .44, "rbxasset://textures/particles/fire_main.dds")
	fountain.SpreadAngle, fountain.Speed = Vector2.new(48,48), NumberRange.new(14,27)
	fountain.Acceleration = -Vector3.yAxis*16
	fountain.Lifetime = NumberRange.new(.55,1.4)
	fountain:Emit(55)
	local light = Instance.new("PointLight")
	light.Color,light.Range,light.Brightness,light.Parent=FX.gold,48,10,anchor
	FX.tween(light,.5,{Brightness=0})
	-- Six shell pieces fly apart at the same instant as the local visual disappears.
	local shellSize = if egg:IsA("Model") then egg:GetExtentsSize() else egg.Size
	for i=1,6 do
		local a=i*math.pi/3
		local dir=Vector3.new(math.cos(a),.5,math.sin(a))
		local chip=Instance.new("WedgePart")
		chip.Size=shellSize*Vector3.new(.22,.38,.14)
		chip.Anchored,chip.CanCollide,chip.CanQuery,chip.CanTouch=true,false,false,false
		chip.Color,chip.Material=FX.gold,Enum.Material.Neon
		chip.CFrame=CFrame.new(pos+dir*shellSize.X*.3)*CFrame.Angles(0,-a,0)
		chip.Parent=anchor
		FX.tween(chip,.55,{CFrame=chip.CFrame+dir*6,Transparency=1})
	end
	fragments(pos,40,true)
	local screen = banner(playerName.." claimed the BIG EGG!", "BIG EGG   /   CLAIMED")
	Debris:AddItem(screen,4)
end
return VFX
