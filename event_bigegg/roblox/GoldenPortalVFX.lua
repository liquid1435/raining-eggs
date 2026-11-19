-- Client presentation for Golden Nest. All coordinates use world Y as up.
local RunService = game:GetService("RunService")
local FX = require(script.Parent.FX)

local VFX = {}
local Y = Vector3.yAxis
local TAU = 2 * math.pi
local gold, cream = FX.gold, FX.cream
local purple = Color3.fromRGB(164, 78, 255)
local orchid = Color3.fromRGB(235, 169, 255)
local smokeTexture = "rbxasset://textures/particles/smoke_main.dds"
local random = Random.new()
local altars, placements, originals = {}, {}, {}
local scene, ritual, portal
local shakeCamera, shakePose, shakeDelta
local shakeKey = "GoldenNestShake_" .. game:GetService("HttpService"):GenerateGUID(false)

local function root()
	if not scene then
		scene = Instance.new("Folder")
		scene.Name = "GoldenNest_ClientFX"
		scene.Parent = workspace
	end
	return scene
end

local function anchor(parent, name, at)
	local p = FX.part(parent, name, Vector3.one * 0.1, at, gold)
	p.Transparency = 1
	return p
end

local function light(parent, color, range, brightness)
	local l = Instance.new("PointLight")
	l.Color, l.Range, l.Brightness = color, math.min(60, range), brightness
	l.Parent = parent
	return l
end

local function beam(parent, a, b, color, w0, w1, fade)
	local line = Instance.new("Beam")
	line.Attachment0, line.Attachment1 = a, b
	line.Width0, line.Width1 = w0, w1
	line.Color = ColorSequence.new(color)
	line.Transparency = NumberSequence.new(fade)
	line.LightEmission, line.FaceCamera = 1, true
	line.Segments = 10
	line.Parent = parent
	return line
end

local function animate(state, step)
	local start = os.clock()
	state.connection = RunService.RenderStepped:Connect(function()
		if step(os.clock() - start) == false and state.connection then
			state.connection:Disconnect()
			state.connection = nil
		end
	end)
end

local function stop(state)
	if state.connection then state.connection:Disconnect() end
	state.root:Destroy()
end

local function ease(x)
	x = math.clamp(x, 0, 1)
	return x * x * (3 - 2 * x)
end

local function removePlacement(s)
	stop(s)
	if s.egg.Parent then
		for _, item in s.parts do
			if item.part.Parent then item.part.Size = item.size end
		end
		s.egg:PivotTo(s.original)
		for _, item in s.parts do
			if item.part.Parent then item.part.CFrame = item.original end
		end
	end
	altars[s.altar], placements[s.egg] = nil, nil
end

local function place(altar, egg, color, fly)
	if altars[altar] then removePlacement(altars[altar]) end
	if placements[egg] then removePlacement(placements[egg]) end
	local original = egg:GetPivot()
	local list = if egg:IsA("BasePart") then {egg} else egg:GetDescendants()
	local low, high = math.huge, -math.huge
	local minX, minZ, maxX, maxZ = low, low, high, high
	local parts = {}
	-- Project each oriented box onto world axes. This also handles imported,
	-- off-center pivots and eggs built from several anchored MeshParts.
	for _, p in list do
		if not p:IsA("BasePart") then continue end
		local cf, h = p.CFrame, p.Size * .5
		local ext = cf.RightVector:Abs() * h.X + cf.UpVector:Abs() * h.Y + cf.LookVector:Abs() * h.Z
		local lo, hi = cf.Position - ext, cf.Position + ext
		low, high = math.min(low, lo.Y), math.max(high, hi.Y)
		minX, maxX = math.min(minX, lo.X), math.max(maxX, hi.X)
		minZ, maxZ = math.min(minZ, lo.Z), math.max(maxZ, hi.Z)
		table.insert(parts, {part = p, size = p.Size, original = cf})
	end
	if #parts == 0 then return end
	local foot = altar.CFrame:PointToWorldSpace(Y * altar.Size.Y * .5)
	local height = high - low
	local shift = foot - Vector3.new((minX + maxX) / 2, low, (minZ + maxZ) / 2)
	local final = original + shift
	local r = math.clamp(math.min(altar.Size.X, altar.Size.Z) * .38, .45, 8)
	local base = anchor(root(), "OfferingAura", CFrame.new(foot + Y * .06))
	local s = {root = base, egg = egg, altar = altar, original = original, parts = parts}
	altars[altar], placements[egg] = s, s
	local floor = FX.attach(base, Vector3.zero)
	local crown = FX.attach(base, Y * (height + r * 3.8))
	s.halo = beam(base, floor, crown, color, r * .92, r * .24, .84)
	s.thread = beam(base, floor, crown, color:Lerp(cream, .45), r * .14, .04, .52)
	s.light = light(base, color, r * 4 + 3, 1.1)
	local function ignite(on)
		s.halo.Enabled, s.thread.Enabled, s.light.Enabled = on, on, on
	end
	if not fly then
		egg:PivotTo(final)
		return
	end
	ignite(false)
	local transient = anchor(base, "LandingFlare", base.CFrame)
	local sparks = FX.emitter(transient, color, math.max(.22, r * .30))
	local resize = FX.ring(transient, r * .38, r * .09, color)
	resize(r * .38, 1)
	local drop = math.max(height * 1.7, r * 3)
	egg:PivotTo(final + Y * drop)
	local hit, settled = false, false
	animate(s, function(t)
		if not egg.Parent or not altar.Parent then
			removePlacement(s)
			return false
		end
		if t < .42 then
			local u = t / .42
			egg:PivotTo((final + Y * (drop * (1 - u * u))) * CFrame.Angles(0, .28 * (1-u) * u * 4, 0))
		else
			if not hit then
				hit = true
				egg:PivotTo(final)
				ignite(true)
				sparks:Emit(24)
			end
			if not settled then
				local u = math.clamp((t - .42) / .18, 0, 1)
				local squash = .15 * math.sin(math.pi * u)
				for _, item in parts do
					local cf = item.original + shift
					local p = item.part
					-- Scale each local axis by its alignment with world vertical.
					local stretch = Vector3.new(1+squash*.5, 1-squash, 1+squash*.5)
					local function extent(axis) return (axis * stretch).Magnitude end
					p.Size = item.size * Vector3.new(extent(cf.RightVector), extent(cf.UpVector), extent(cf.LookVector))
					p.CFrame = cf.Rotation + (foot + (cf.Position - foot) * stretch)
				end
				settled = u == 1
				if settled then egg:PivotTo(final) end
			end
			local u = math.clamp((t - .42) / .48, 0, 1)
			resize(r * (.38 + 1.15 * ease(u)), u)
		end
		if t >= 1.42 then
			transient:Destroy()
			return false
		end
		return true
	end)
end

function VFX.PlayPlace(altarPart, eggModel, zoneColor: Color3)
	place(altarPart, eggModel, zoneColor, true)
end

function VFX.ShowPlaced(altarPart, eggModel, zoneColor)
	place(altarPart, eggModel, zoneColor, false)
end

local function remember(p)
	if p and not originals[p] then
		originals[p] = {cf = p.CFrame, size = p.Size, alpha = p.LocalTransparencyModifier, collide = p.CanCollide}
	end
	return originals[p]
end

local function restore(p, old)
	if p and p.Parent then
		p.Size, p.CFrame = old.size, old.cf
		p.LocalTransparencyModifier, p.CanCollide = old.alpha, old.collide
	end
end

local function undoShake()
	if shakeCamera and shakeCamera.CFrame == shakePose then shakeCamera.CFrame *= shakeDelta:Inverse() end
	shakeCamera = nil
end

local function endRitual()
	if not ritual then return end
	RunService:UnbindFromRenderStep(shakeKey .. "Before")
	RunService:UnbindFromRenderStep(shakeKey .. "After")
	undoShake()
	stop(ritual)
	for _, s in altars do s.light.Brightness, s.halo.Width0 = 1.1, s.width or s.halo.Width0 end
	ritual = nil
end

local function cancelRitual()
	if not ritual then return end
	local egg, shaft = ritual.egg, ritual.shaft
	endRitual()
	restore(egg, originals[egg])
	restore(shaft, originals[shaft])
end

local function hide(p)
	if p and p.Parent then
		remember(p)
		p.LocalTransparencyModifier, p.CanCollide = 1, false
	end
end

function VFX.ShowSunk(goldenEgg, beamPart)
	cancelRitual()
	hide(goldenEgg)
	hide(beamPart)
end

-- Each fissure grows out along a broken radial path, with a shorter side branch.
local function fissures(base, radius)
	local edges = {}
	for i = 1, 11 do
		local a = TAU * (i + random:NextNumber(-.24,.24)) / 11
		local function point(r, angle)
			return Vector3.new(math.cos(angle)*r, .12 + i*.002, math.sin(angle)*r)
		end
		local prev = FX.attach(base, point(radius*.75, a))
		for j = 1, 4 do
			local r = radius * (.75 + j*.24)
			local bend = a + random:NextNumber(-.11,.11)
			local tip = FX.attach(base, point(r, bend))
			local function segment(from, to, width, delay)
				local drawn = FX.attach(base, from.Position)
				local b = beam(base, from, drawn, gold:Lerp(cream, .34), width, width*.48, .06)
				table.insert(edges, {b = b, tip = drawn, a = from.Position, z = to.Position, start = delay})
			end
			local delay = .52 + (i%4)*.13 + j*.18
			segment(prev, tip, radius*.021*(1.2-j*.12), delay)
			if j == 2 then
				segment(tip, FX.attach(base, point(r+radius*.33,bend+.17)), radius*.011, delay+.19)
			end
			prev = tip
		end
	end
	return edges
end

function VFX.PlaySink(goldenEgg: BasePart, beamPart: BasePart?, groundY: number, done: (() -> ())?)
	cancelRitual()
	local shell = remember(goldenEgg)
	local shaft = remember(beamPart)
	restore(goldenEgg, shell)
	restore(beamPart, shaft)
	local pos = Vector3.new(shell.cf.X, groundY, shell.cf.Z)
	local radius = math.max(shell.size.X, shell.size.Z)*.58
	local base = anchor(root(), "NestRupture", CFrame.new(pos))
	local s = {root = base, egg = goldenEgg, shaft = beamPart, strength = 0}
	ritual = s
	local cracks = fissures(base, radius)
	local ember = light(base, gold, radius*2.7, 0)
	local glowRing = FX.ring(base, radius*.85, radius*.06, gold)
	glowRing(radius*.85, 1)
	local vents, rocks = {}, {}
	for i = 1, 10 do
		local a = i*TAU/10
		local vent = FX.attach(base, Vector3.new(math.cos(a)*radius, .35, math.sin(a)*radius))
		local dust = FX.emitter(vent, Color3.fromRGB(188,143,88), radius*.32, smokeTexture)
		dust.LightEmission = .10
		dust.Speed = NumberRange.new(2,5)
		dust.SpreadAngle = Vector2.new(55,55)
		dust.Acceleration = Y*2
		dust.Transparency = NumberSequence.new(.48,1)
		local sparks = FX.emitter(vent, gold, radius*.057)
		sparks.Acceleration = -Y*10
		sparks.SpreadAngle = Vector2.new(52,52)
		table.insert(vents, {dust = dust, sparks = sparks})
		for j = 1, 2 do
			local size = radius * random:NextNumber(.035,.085)
			local p = FX.part(base, "NestChip", Vector3.new(size,size*.7,size*.82), base.CFrame, FX.gold:Lerp(Color3.fromRGB(139,100,65),random:NextNumber()))
			p.Material, p.Transparency = Enum.Material.Slate, 1
			table.insert(rocks, {p=p, origin=pos+vent.Position, velocity=vent.Position.Unit*radius*.28+Y*radius*.82,
				start=1.6+random:NextNumber()*3.2, spin=random:NextNumber(-5,5)})
		end
	end
	RunService:BindToRenderStep(shakeKey.."Before", Enum.RenderPriority.Camera.Value-1, undoShake)
	RunService:BindToRenderStep(shakeKey.."After", Enum.RenderPriority.Camera.Value+1, function()
		local cam = workspace.CurrentCamera
		if not cam then return end
		local k = s.strength * math.clamp(1-(cam.CFrame.Position-pos).Magnitude/(radius*9+35),0,1)
		local n = os.clock()*19
		shakeDelta = CFrame.new(math.noise(n,1)*k*.6, math.noise(n,7)*k*.46, 0) * CFrame.Angles(0,0,math.noise(n,12)*k*.012)
		cam.CFrame *= shakeDelta
		shakeCamera, shakePose = cam, cam.CFrame
	end)
	animate(s, function(t)
		if not goldenEgg.Parent then
			cancelRitual()
			return false
		end
		local descent = ease((t-1.65)/4.05)
		local energy = ease(t/1.2)*(1-ease((t-4.95)/1.05))
		s.strength = energy*(.42+.35*descent)
		for _, aura in altars do
			aura.width = aura.width or aura.halo.Width0
			local pulse = (.5+.5*math.cos(t*6))*energy
			aura.light.Brightness = 1.1+3*pulse
			aura.halo.Width0 = aura.width*(1+.65*pulse)
		end
		local tremor = Vector3.new(math.noise(t*16,3),0,math.noise(t*18,8))*radius*.039*energy
		goldenEgg.CFrame = (shell.cf + tremor - Y*(shell.size.Y+2)*descent) * CFrame.Angles(0,0,math.noise(t*15,4)*energy*.016)
		if descent > 0 then goldenEgg.CanCollide = false end
		if beamPart and beamPart.Parent then
			local u = ease((t-1.15)/2.35)
			local ratio = math.max(.001,1-u)
			beamPart.Size = shaft.size*Vector3.new(ratio,ratio,ratio)
			beamPart.CFrame = shaft.cf - Y*(shaft.size.Y-beamPart.Size.Y)*.5
			beamPart.LocalTransparencyModifier = shaft.alpha + (1-shaft.alpha)*u
		end
		for _, edge in cracks do
			local u = math.clamp((t-edge.start)/.24,0,1)
			if edge.last ~= u then
				edge.tip.Position = edge.a:Lerp(edge.z,u)
				edge.last = u
			end
			if t > 5 then edge.b.Transparency = NumberSequence.new(.06+.94*ease(t-5)) end
		end
		ember.Brightness = energy*(2.1+.45*math.sin(t*9))
		glowRing(radius*(.79+.16*descent), 1-energy*.77)
		for _, vent in vents do
			vent.dust.Rate = 8*energy*ease((t-1.2)/.6)
			vent.sparks.Rate = 7*energy
		end
		for _, rock in rocks do
			local u = t-rock.start
			if u >= 0 and u < 1 then
				rock.p.Transparency = ease((u-.7)/.3)
				rock.p.CFrame = CFrame.new(rock.origin+rock.velocity*u-Y*radius*.89*u*u)*CFrame.Angles(u*rock.spin,u*3,u)
			elseif u >= 1 then rock.p.Transparency = 1 end
		end
		if t >= 6 then
			goldenEgg.CFrame = shell.cf - Y*(shell.size.Y+2)
			hide(goldenEgg)
			hide(beamPart)
			endRitual()
			if done then done() end
			return false
		end
		return true
	end)
end

-- Cubic Hermite arcs follow a parametric ellipse. The changing radius and
-- depth make the rim filaments visibly cross and the inner arms spiral.
local function ribbon(parent, segments, color, width, fade, sample)
	local knots, beams = {}, {}
	for i = 0, segments do
		knots[i+1] = FX.attach(parent, Vector3.zero)
		if i > 0 then
			beams[i] = beam(parent, knots[i], knots[i+1], color, width, width, fade)
		end
	end
	return function(phase)
		for i = 0, segments do
			local u = i/segments
			local point = sample(u,phase)
			local tangent = (sample(u+.001,phase)-sample(u-.001,phase))/.002
			local a = knots[i+1]
			a.Position, a.Axis = point, tangent.Unit
			local handle = tangent.Magnitude/(3*segments)
			if i > 0 then beams[i].CurveSize1 = handle end
			if i < segments then beams[i+1].CurveSize0 = handle end
		end
	end
end

function VFX.ShowPortal(position: Vector3, size: number?)
	if portal then stop(portal) end
	local h = math.max(1, size or 30)
	local rx, ry = h*.35, h*.455
	local frame = CFrame.new(position + Y*h*.5)
	local p = anchor(root(), "GoldenPortal", frame)
	p.Size = Vector3.new(rx*1.95,ry*2,h*.09)
	p.CanTouch, p.CanQuery = true, true
	local s = {root = p}
	portal = s
	local veil = FX.part(p, "AmethystDepth", Vector3.new(rx*1.98,ry*1.99,h*.045), frame, Color3.fromRGB(54,21,91))
	veil.Shape, veil.Transparency = Enum.PartType.Ball, .16
	local ribbons = {}
	for strand = 1, 3 do
		local phaseOffset = TAU*(strand-1)/3
		table.insert(ribbons, ribbon(p, 12, ({gold,purple,cream})[strand], h*({.021,.016,.008})[strand], .045, function(u,phase)
			local a = TAU*u
			local wave = 3*a+phase+phaseOffset
			local r = 1+.038*math.cos(wave)
			return Vector3.new(rx*r*math.cos(a),ry*r*math.sin(a),h*.023*math.sin(wave))
		end))
	end
	-- Render spiral arms on both faces so the aperture reads from either side.
	for _, side in {-1,1} do
		for j = 1, 3 do
			table.insert(ribbons, ribbon(p, 7, if j==2 then orchid else purple, h*.009, .21, function(u,phase)
				local r = .095+.79*u
				local a = TAU*j/3+side*(2.8*u+phase*.49)
				return Vector3.new(rx*r*math.cos(a),ry*r*math.sin(a),side*h*(.026+.007*(1-u)))
			end))
		end
	end
	for j = 1, 12 do
		local a = TAU*j/12
		local big = j%3==0
		local gem = FX.part(p, "DialMarker", Vector3.new(h*.012,h*(if big then .064 else .031),h*.014),
			frame*CFrame.new(rx*1.105*math.cos(a),ry*1.046*math.sin(a),0)*CFrame.Angles(0,0,a-math.pi/2), if big then cream else gold)
		gem.Material = Enum.Material.Neon
	end
	local motes = {}
	for j = 1, 6 do
		local a = FX.attach(p, Vector3.zero)
		local emitter = FX.emitter(a, if j%2==0 then orchid else cream, h*.019)
		emitter.Speed = NumberRange.new(h*.012,h*.038)
		emitter.SpreadAngle = Vector2.new(25,25)
		emitter.Rate = 5
		emitter.Lifetime = NumberRange.new(.48,1.05)
		table.insert(motes,a)
	end
	local foot = FX.attach(p,-Y*ry*.92)
	local stars = FX.emitter(foot, gold, h*.018)
	stars.Speed = NumberRange.new(h*.16,h*.32)
	stars.SpreadAngle = Vector2.new(32,32)
	stars.Lifetime, stars.Rate = NumberRange.new(1.3,2.4), 12
	local lantern = light(p, gold, h*1.24, 1.7)
	local last = -1
	local function flow(t)
		if not p.Parent then
			stop(s)
			portal = nil
			return false
		end
		if t-last < 1/30 then return true end
		last = t
		for _, draw in ribbons do draw(t*.93) end
		for i, a in motes do
			local angle = TAU*i/6+t*(.58+i*.035)
			local r = .66+.16*math.sin(t*.68+i)
			a.Position = Vector3.new(rx*r*math.cos(angle),ry*r*math.sin(angle),h*.034*(if i%2==0 then 1 else -1))
		end
		lantern.Brightness = 1.7+.48*math.sin(t*1.9)
		return true
	end
	flow(0)
	animate(s,flow)
	return p
end

function VFX.Clear()
	endRitual()
	if portal then
		stop(portal)
		portal = nil
	end
	for _, s in altars do removePlacement(s) end
	for p, old in originals do restore(p,old) end
	table.clear(originals)
	if scene then
		scene:Destroy()
		scene = nil
	end
end

return VFX
