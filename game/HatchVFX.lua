-- Raining Eggs: HATCH SHOW v2 (world-space VFX: particles, trails, beams, shockwaves, light)
-- The egg appears in front of the camera, the world behind goes dark and blurred, the egg climbs through the rarity
-- colours (every step: colour burst, ring, jolt, sound, the name on top), charges up (comet trails spiral in, it shakes
-- and turns white-hot), POPS (flash, two shockwaves, sparks, shell shards, light) and the pet comes out with rays,
-- confetti (Epic+) and a golden rain (Legendary). Tap = 3x faster. Everything is client-side and cleaned up at the end.
local RunService = game:GetService("RunService")
local Lighting = game:GetService("Lighting")
local UIS = game:GetService("UserInputService")
local Players = game:GetService("Players")

local M = {}
M.VOLUME = 0.25 -- master volume of every hatch sound (user 19 Nov: still too loud at 0.5)

local RCOL = { Color3.fromRGB(235, 240, 255), Color3.fromRGB(80, 255, 120), Color3.fromRGB(40, 190, 255), Color3.fromRGB(200, 70, 255), Color3.fromRGB(255, 190, 30), Color3.fromRGB(255, 60, 90) }
local RNAME = { "COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY", "???" }
local STEP_T = { 0.7, 0.75, 0.85, 1.0, 1.2, 2.4 }
local HOLD = { 1.5, 1.7, 2.1, 2.6, 3.4, 3.8 }
local TEX = {
	spark = "rbxasset://textures/particles/sparkles_main.dds",
	fsp = "rbxasset://textures/particles/fire_sparks_main.dds",
	smoke = "rbxasset://textures/particles/smoke_main.dds",
	fire = "rbxasset://textures/particles/fire_main.dds",
}
local WHITE = Color3.new(1, 1, 1)
local GOLD = Color3.fromRGB(255, 200, 60)

local function clamp(x, a, b)
	return math.max(a or 0, math.min(b or 1, x))
end
local function eo(u)
	u = clamp(u)
	return 1 - (1 - u) ^ 3
end
local function backOut(u)
	u = clamp(u) - 1
	return u * u * (2.7 * u + 1.7) + 1
end
local function new(class, props, parent)
	local o = Instance.new(class)
	for k, v in pairs(props) do
		o[k] = v
	end
	o.Parent = parent
	return o
end
local function part(parent, size, col, mat)
	return new("Part", { Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, CastShadow = false, Size = size, Color = col or WHITE,
		Material = mat or Enum.Material.Neon, Transparency = 1, CFrame = CFrame.new(0, -500, 0) }, parent)
end
local function emitter(parent, props)
	local e = new("ParticleEmitter", {
		Texture = TEX.spark, LightEmission = 1, LightInfluence = 0, Rate = 0, Lifetime = NumberRange.new(0.5, 1.1), Speed = NumberRange.new(6, 18),
		SpreadAngle = Vector2.new(180, 180), Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(1, 0) }),
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 1) }), Drag = 2, ZOffset = 1,
	}, parent)
	for k, v in pairs(props or {}) do
		e[k] = v
	end
	return e
end
local function setCol(e, a, b)
	e.Color = ColorSequence.new(a, b or a)
end
-- a ring made of 4 curved beams (no texture needed)
local function ring(anchor, col, width)
	local att, beams = {}, {}
	for i = 1, 4 do
		att[i] = new("Attachment", {}, anchor)
	end
	for i = 1, 4 do
		beams[i] = new("Beam", { Attachment0 = att[i], Attachment1 = att[i % 4 + 1], Width0 = width, Width1 = width, LightEmission = 1, LightInfluence = 0,
			FaceCamera = true, Segments = 20, Color = ColorSequence.new(col), Transparency = NumberSequence.new(1) }, anchor)
	end
	local function set(cf, r, alpha, c, w)
		for i = 1, 4 do
			local a = (i - 1) * math.pi / 2
			-- the attachment's X axis points along the circle (tangent), like Codex's FX.ring
			att[i].WorldCFrame = cf * CFrame.new(math.cos(a) * r, math.sin(a) * r, 0) * CFrame.Angles(0, 0, a + math.pi / 2)
			local b = beams[i]
			b.CurveSize0, b.CurveSize1 = r * 0.552, r * 0.552
			b.Transparency = NumberSequence.new(1 - clamp(alpha))
			if c then
				b.Color = ColorSequence.new(c)
			end
			if w then
				b.Width0, b.Width1 = w, w
			end
		end
	end
	return set
end

function M.play(job, d)
	local cam = workspace.CurrentCamera
	-- all hatch sounds at half volume (user: too loud, 19 Nov)
	local function snd(name, v, pitch)
		d.hfx(name, (v or 0.7) * M.VOLUME, pitch)
	end
	local plr = Players.LocalPlayer
	local pet = job.pet
	local R = job.secret and 6 or pet.i
	local k = (job.fast and 0.6 or 1) * (d.fastPass and 0.5 or 1)
	local speed = 1
	local tapConn = UIS.InputBegan:Connect(function(input)
		if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then
			speed = 3
		end
	end)

	-- timeline (show seconds)
	local starts, t = {}, 0.75
	for L = 1, R do
		starts[L] = t
		t = t + STEP_T[L == 6 and 6 or math.min(R, 5)]
	end
	local T_CHARGE = t
	local CHARGE = 0.7 + (R >= 4 and 0.35 or 0)
	local T_POP = T_CHARGE + CHARGE
	local T_OUT = T_POP + HOLD[R]
	local T_END = T_OUT + 0.45

	-- ---------- scene
	local saved = { type = cam.CameraType, cf = cam.CFrame, guis = {} }
	for _, g in ipairs(plr.PlayerGui:GetChildren()) do
		if g:IsA("ScreenGui") and g.Enabled and g.Name ~= "HatchVFX" then
			g.Enabled = false
			table.insert(saved.guis, g)
		end
	end
	cam.CameraType = Enum.CameraType.Scriptable
	-- hide my own character (it would stand between the camera and the egg)
	local hidden = {}
	if plr.Character then
		for _, o in ipairs(plr.Character:GetDescendants()) do
			if o:IsA("BasePart") or o:IsA("Decal") then
				hidden[o] = o.LocalTransparencyModifier
				o.LocalTransparencyModifier = 1
			end
		end
	end
	-- the show floats in front of the camera; if the ground is too close under it (low camera), lift camera + show
	local base = CFrame.lookAt(cam.CFrame.Position, cam.CFrame.Position + Vector3.new(cam.CFrame.LookVector.X, 0, cam.CFrame.LookVector.Z).Unit)
	local center = base * CFrame.new(0, -0.4, -11)
	do
		local rp = RaycastParams.new()
		rp.FilterType = Enum.RaycastFilterType.Exclude
		rp.FilterDescendantsInstances = { plr.Character }
		local hit = workspace:Raycast(center.Position + Vector3.new(0, 40, 0), Vector3.new(0, -120, 0), rp)
		local need = 8.5 -- egg half height + the stand ring under the pet + some air
		if hit and center.Position.Y - hit.Position.Y < need then
			local lift = Vector3.new(0, need - (center.Position.Y - hit.Position.Y), 0)
			base, center = base + lift, center + lift
		end
	end
	local folder = new("Folder", { Name = "HatchVFX" }, workspace)
	local cc = new("ColorCorrectionEffect", { Name = "HatchVFX_CC" }, Lighting)
	local dof = new("DepthOfFieldEffect", { Name = "HatchVFX_DOF", FarIntensity = 0, FocusDistance = 11, InFocusRadius = 6, NearIntensity = 0 }, Lighting)
	local blur = new("BlurEffect", { Name = "HatchVFX_Blur", Size = 0 }, Lighting)

	-- backdrop disc behind the egg (dark glow) so busy worlds do not fight the effects
	local back = part(folder, Vector3.new(0.2, 90, 90), Color3.fromRGB(10, 6, 24), Enum.Material.SmoothPlastic)
	back.Shape = Enum.PartType.Cylinder
	local backGlow = part(folder, Vector3.new(0.2, 12, 12), RCOL[1])
	backGlow.Shape = Enum.PartType.Cylinder

	local anchor = part(folder, Vector3.new(0.2, 0.2, 0.2))
	local att = new("Attachment", {}, anchor)
	local aura = emitter(att, { Rate = 0, Speed = NumberRange.new(1, 3), Lifetime = NumberRange.new(0.6, 1.2), Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.45), NumberSequenceKeypoint.new(1, 0) }), Acceleration = Vector3.new(0, 3, 0) })
	local burst = emitter(att, { Speed = NumberRange.new(10, 26), Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.9), NumberSequenceKeypoint.new(1, 0) }) })
	local sparks = emitter(att, { Texture = TEX.fsp, Speed = NumberRange.new(14, 34), Lifetime = NumberRange.new(0.4, 0.9), Acceleration = Vector3.new(0, -24, 0), Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 0) }) })
	local smoke = emitter(att, { Texture = TEX.smoke, LightEmission = 0.3, Speed = NumberRange.new(4, 9), Lifetime = NumberRange.new(0.8, 1.4), Drag = 4,
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.5), NumberSequenceKeypoint.new(1, 5) }), Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(1, 1) }) })
	local confetti = emitter(att, { Texture = "", Speed = NumberRange.new(12, 24), Lifetime = NumberRange.new(1.6, 2.6), Acceleration = Vector3.new(0, -14, 0), Drag = 1.5, LightEmission = 0.2,
		Size = NumberSequence.new(0.22), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-400, 400),
		Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 80, 120)), ColorSequenceKeypoint.new(0.33, Color3.fromRGB(255, 220, 60)), ColorSequenceKeypoint.new(0.66, Color3.fromRGB(80, 220, 255)), ColorSequenceKeypoint.new(1, Color3.fromRGB(150, 255, 120)) }) })
	local rainAtt = new("Attachment", {}, anchor)
	local goldRain = emitter(rainAtt, { Rate = 0, EmissionDirection = Enum.NormalId.Bottom, SpreadAngle = Vector2.new(60, 60), Speed = NumberRange.new(2, 5), Lifetime = NumberRange.new(1.5, 2.5), Acceleration = Vector3.new(0, -6, 0) })
	setCol(goldRain, GOLD, Color3.fromRGB(255, 240, 180))
	local light = new("PointLight", { Range = 22, Brightness = 0, Color = RCOL[1], Shadows = false }, anchor)

	-- comet trails that spiral into the egg during the charge
	local comets = {}
	for i = 1, 6 do
		local p = part(folder, Vector3.new(0.35, 0.35, 0.35), RCOL[1])
		local a0 = new("Attachment", { Position = Vector3.new(0, 0.18, 0) }, p)
		local a1 = new("Attachment", { Position = Vector3.new(0, -0.18, 0) }, p)
		local tr = new("Trail", { Attachment0 = a0, Attachment1 = a1, Lifetime = 0.35, LightEmission = 1, LightInfluence = 0, FaceCamera = true,
			WidthScale = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0) }),
			Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 1) }), Enabled = false }, p)
		comets[i] = { p = p, tr = tr, ph = i * math.pi / 3 }
	end
	-- ---------- extra layers (v2.1: more spectacular)
	local bloom = new("BloomEffect", { Name = "HatchVFX_Bloom", Intensity = 0, Size = 36, Threshold = 0.9 }, Lighting)
	local fov0 = cam.FieldOfView
	-- speed lines: sparks stretched along their velocity
	local streaks = emitter(att, { Texture = TEX.spark, Speed = NumberRange.new(30, 60), Lifetime = NumberRange.new(0.18, 0.35), Drag = 3,
		Orientation = Enum.ParticleOrientation.VelocityParallel, Squash = NumberSequence.new({ NumberSequenceKeypoint.new(0, -2.5), NumberSequenceKeypoint.new(1, -1.2) }),
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.9), NumberSequenceKeypoint.new(1, 0.2) }) })
	-- one big soft flare in the middle (steps + pop)
	local flare = emitter(att, { Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.35, 0.45), SpreadAngle = Vector2.new(0, 0), RotSpeed = NumberRange.new(-90, 90), Rotation = NumberRange.new(0, 360),
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 9), NumberSequenceKeypoint.new(0.25, 7), NumberSequenceKeypoint.new(1, 0) }),
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(1, 1) }), ZOffset = 2 })
	-- implosion: energy pulled in from all around during the charge
	local suck = {}
	for i = 1, 10 do
		local a = new("Attachment", {}, anchor)
		local e = emitter(a, { EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(8, 8), Speed = NumberRange.new(9, 12), Lifetime = NumberRange.new(0.5, 0.6), Drag = 0,
			Orientation = Enum.ParticleOrientation.VelocityParallel, Squash = NumberSequence.new(-1.6), Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(0.7, 0.5), NumberSequenceKeypoint.new(1, 0) }) })
		suck[i] = { a = a, e = e, dir = Vector3.new(math.cos(i * 2.4), math.sin(i * 1.7), math.sin(i * 2.4) * 0.4).Unit }
	end
	-- three tilted rings that spin round the egg like an atom
	local atom = { ring(anchor, WHITE, 0.18), ring(anchor, WHITE, 0.18), ring(anchor, WHITE, 0.18) }
	-- lightning (Epic+): 4 bolts of 5 segments, re-shaped every few frames
	local bolts = {}
	for b = 1, 4 do
		local pts, segs = {}, {}
		for j = 1, 6 do
			pts[j] = new("Attachment", {}, anchor)
		end
		for j = 1, 5 do
			segs[j] = new("Beam", { Attachment0 = pts[j], Attachment1 = pts[j + 1], Width0 = 0.16, Width1 = 0.16, LightEmission = 1, LightInfluence = 0, FaceCamera = true, Segments = 1, Enabled = false }, anchor)
		end
		bolts[b] = { pts = pts, segs = segs }
	end
	local boltT = 0
	-- spotlight from above on the pet + a ring it stands on
	local spotTop, spotBot = new("Attachment", {}, anchor), new("Attachment", {}, anchor)
	local spot = new("Beam", { Attachment0 = spotTop, Attachment1 = spotBot, Width0 = 2, Width1 = 7, LightEmission = 1, LightInfluence = 0, FaceCamera = true, Segments = 2, Enabled = false,
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.95), NumberSequenceKeypoint.new(0.5, 0.75), NumberSequenceKeypoint.new(1, 0.9) }) }, anchor)
	local podium = ring(anchor, WHITE, 0.3)
	local podium2 = ring(anchor, WHITE, 0.12)
	local freezeUntil = nil

	-- rays behind the pet (beams from the centre outwards)
	local rays = {}
	local rayRoot = new("Attachment", {}, anchor)
	for i = 1, 12 do
		local tip = new("Attachment", {}, anchor)
		local b = new("Beam", { Attachment0 = rayRoot, Attachment1 = tip, Width0 = 0.2, Width1 = 3.2, LightEmission = 1, LightInfluence = 0, FaceCamera = true, Segments = 2,
			Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 1) }), Color = ColorSequence.new(WHITE), Enabled = false }, anchor)
		rays[i] = { b = b, tip = tip }
	end
	local ringA, ringB, ringC = ring(anchor, WHITE, 0.5), ring(anchor, WHITE, 0.25), ring(anchor, WHITE, 0.35)

	-- the egg
	local egg, unit, rot = d.eggMesh(pet.z, job.kind)
	if egg then
		local h = math.abs((rot or CFrame.new()):VectorToWorldSpace(unit).Y)
		egg.Size = unit * (5.4 / math.max(h, 0.1))
		egg.Anchored, egg.CanCollide, egg.CanQuery, egg.CanTouch = true, false, false, false
		egg.Parent = folder
	else
		egg = part(folder, Vector3.new(3.2, 4.2, 3.2), d.eggColor or WHITE, Enum.Material.SmoothPlastic)
		egg.Shape = Enum.PartType.Ball
		egg.Transparency = 0
		rot = CFrame.new()
	end
	rot = rot or CFrame.new()
	local eggSize = egg.Size
	local hot = part(folder, Vector3.new(1, 1, 1), WHITE) -- white-hot shell
	new("SpecialMesh", { MeshType = Enum.MeshType.Sphere, Scale = Vector3.new(4.5, 5.9, 4.5) }, hot)
	-- shell shards for the pop
	local shards = {}
	local rnd = Random.new(pet.i * 31 + pet.z)
	for i = 1, 14 do
		local w = new("WedgePart", { Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, CastShadow = false, Material = Enum.Material.SmoothPlastic,
			Size = Vector3.new(0.2, rnd:NextNumber(0.6, 1.3), rnd:NextNumber(0.5, 1.1)), Color = egg.Color, Transparency = 1, CFrame = CFrame.new(0, -500, 0) }, folder)
		local a = rnd:NextNumber(0, math.pi * 2)
		shards[i] = { p = w, v = Vector3.new(math.cos(a) * rnd:NextNumber(6, 13), rnd:NextNumber(4, 12), math.sin(a) * rnd:NextNumber(2, 6)), spin = Vector3.new(rnd:NextNumber(-9, 9), rnd:NextNumber(-9, 9), rnd:NextNumber(-9, 9)) }
	end
	-- the pet
	local model = d.buildPet(pet, 1, true)
	model.Parent = folder
	local bcf, bsize = model:GetBoundingBox()
	local piv = model:GetPivot().Position
	local fit = 5.6 / math.max(bsize.X, bsize.Y, bsize.Z, 0.5)
	local off = Vector3.new(piv.X - bcf.Position.X, piv.Y - bcf.Position.Y, piv.Z - bcf.Position.Z)
	model:ScaleTo(0.01)
	model:PivotTo(CFrame.new(0, -600, 0))
	local lastK = 0.01

	-- screen text
	local gui = new("ScreenGui", { Name = "HatchVFX", IgnoreGuiInset = true, ResetOnSpawn = false, DisplayOrder = 70 }, plr.PlayerGui)
	local flash = new("Frame", { Size = UDim2.fromScale(1, 1), BackgroundColor3 = WHITE, BackgroundTransparency = 1, BorderSizePixel = 0, ZIndex = 5 }, gui)
	local function label(y, h, font)
		local l = new("TextLabel", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, y), Size = UDim2.fromScale(0.8, h),
			Font = font or Enum.Font.FredokaOne, TextScaled = true, TextColor3 = WHITE, Text = "", TextTransparency = 1, ZIndex = 6 }, gui)
		local st = new("UIStroke", { Thickness = 4, Color = Color3.fromRGB(20, 10, 40), Transparency = 1 }, l)
		return l, st, new("UIScale", {}, l)
	end
	local top, topSt, topSc = label(0.16, 0.11)
	local nameL, nameSt, nameSc = label(0.78, 0.1)
	local oddsL, oddsSt = label(0.87, 0.05, Enum.Font.GothamBold)
	local hint = new("TextLabel", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -16, 1, -12), Size = UDim2.fromOffset(220, 26),
		Font = Enum.Font.GothamBold, TextScaled = true, TextColor3 = WHITE, TextTransparency = 0.5, Text = "TAP TO SPEED UP", ZIndex = 6, TextXAlignment = Enum.TextXAlignment.Right }, gui)
	local function txt(l, st, s, a)
		l.Text = s
		l.TextTransparency = 1 - clamp(a)
		st.Transparency = 1 - clamp(a) * 0.9
	end

	-- ---------- per frame
	local tS, fired, stepNow = 0, {}, 0
	local function once(key, fn)
		if not fired[key] then
			fired[key] = true
			fn()
		end
	end
	local done = false
	local conn = RunService.RenderStepped:Connect(function(dt)
		local ok, err = pcall(function()
			-- hit-stop: time almost stops for a moment right at the pop
			local adv = math.min(dt, 0.1) * speed / k
			if freezeUntil and os.clock() < freezeUntil then
				adv = adv * 0.04
			end
			tS = tS + adv
			if not fired.freeze and tS >= T_POP then
				fired.freeze = true
				freezeUntil = os.clock() + 0.13 / speed
			end
			local t = tS
			once("appear", function()
				snd("appear", 0.7, 1)
			end)
			-- camera: slow push-in, zoom in while it charges, kick out on the pop, shake + roll
			local shake = (t > T_POP and t < T_POP + 0.6) and (1 - (t - T_POP) / 0.6) ^ 2 or 0
			local chargeU = clamp((t - T_CHARGE) / CHARGE) * (t < T_POP and 1 or 0)
			shake = math.max(shake, chargeU * 0.3)
			local kick = t > T_POP and math.exp(-(t - T_POP) * 5) or 0
			cam.FieldOfView = fov0 * (1 - 0.14 * chargeU * chargeU + 0.12 * kick - 0.05 * clamp((t - T_POP - 0.6) / 2) * (t < T_OUT and 1 or 0))
			cam.CFrame = base * CFrame.new(math.sin(t * 61) * 0.22 * shake, math.cos(t * 53) * 0.17 * shake, -math.min(t, T_OUT) * 0.12) * CFrame.Angles(0, 0, math.sin(t * 47) * 0.02 * shake)
			bloom.Intensity = (0.35 + 0.9 * chargeU + 1.6 * kick) * eo(t / 0.4) * (1 - clamp((t - T_OUT) / 0.4))
			bloom.Threshold = 0.95 - 0.2 * chargeU - 0.25 * kick
			-- world fades back
			local dark = eo(t / 0.5) * (1 - clamp((t - T_OUT) / 0.4))
			cc.Brightness, cc.Saturation, cc.Contrast = -0.28 * dark, -0.45 * dark, 0.1 * dark
			dof.FarIntensity = 0.9 * dark
			blur.Size = 6 * dark
			local cf = center
			back.CFrame = cf * CFrame.new(0, 0, -4) * CFrame.Angles(0, math.pi / 2, 0)
			back.Transparency = 1 - 0.55 * dark
			anchor.CFrame = cf
			rainAtt.WorldPosition = cf.Position + Vector3.new(0, 9, 0)

			-- rarity step now
			local L = 0
			for i = 1, R do
				if t >= starts[i] then
					L = i
				end
			end
			local col = L > 0 and RCOL[L] or WHITE
			if L ~= stepNow and L > 0 then
				stepNow = L
				setCol(burst, WHITE, col)
				burst:Emit(18 + L * 6)
				setCol(aura, WHITE, col)
				light.Color = col
				snd("step_" .. math.min(L, 5), 0.7, 1)
				topSc.Scale = 1.35
				top.TextColor3 = col
				setCol(flare, WHITE, col)
				flare.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 4 + L), NumberSequenceKeypoint.new(1, 0) })
				flare:Emit(1)
				setCol(streaks, WHITE, col)
				streaks:Emit(10 + L * 4)
			end
			-- atom rings: tilted, spinning, faster and brighter as it charges (from Rare up, and always in the charge)
			for i, set in ipairs(atom) do
				local on = (L >= 3 or chargeU > 0) and t < T_POP
				if on then
					local sp = 1.2 + chargeU * 6
					local tilt = CFrame.Angles(0.9 + i * 0.7, t * sp * (i % 2 == 0 and -1 or 1), i * 1.1)
					set(cf * tilt, 3.4 - chargeU * 0.9 + i * 0.25, 0.55 + 0.4 * chargeU, col:Lerp(WHITE, 0.3), 0.12 + 0.12 * chargeU)
				else
					set(cf, 0.1, 0)
				end
			end
			-- implosion: streaks pulled into the egg while it charges
			for _, s in ipairs(suck) do
				local p = cf.Position + s.dir * 6.5
				s.a.WorldCFrame = CFrame.lookAt(p, cf.Position) * CFrame.Angles(-math.pi / 2, 0, 0)
				s.e.Rate = chargeU > 0 and (8 + 40 * chargeU) or 0
				setCol(s.e, WHITE, col)
			end
			-- lightning round the egg (Epic+) in the charge
			boltT = boltT + dt
			for _, b in ipairs(bolts) do
				local on = R >= 4 and chargeU > 0.15
				for _, s in ipairs(b.segs) do
					s.Enabled = on and math.random() > 0.15
					s.Color = ColorSequence.new(WHITE, col)
				end
				if on and boltT > 0.06 then
					if b == bolts[1] and (not fired.zapT or os.clock() - fired.zapT > 0.28) then
						fired.zapT = os.clock()
						snd("zap", 0.35, 0.9 + math.random() * 0.3)
					end
					local a = math.random() * math.pi * 2
					local p0 = cf.Position + (cf.RightVector * math.cos(a) + cf.UpVector * math.sin(a)) * 1.6
					local p1 = cf.Position + (cf.RightVector * math.cos(a + 0.6) + cf.UpVector * math.sin(a + 0.6)) * (5 + math.random() * 2)
					for j, pt in ipairs(b.pts) do
						local f = (j - 1) / 5
						local jit = (j > 1 and j < 6) and (cf.RightVector * (math.random() - 0.5) + cf.UpVector * (math.random() - 0.5)) * 1.1 or Vector3.zero
						pt.WorldPosition = p0:Lerp(p1, f) + jit
					end
				end
			end
			if boltT > 0.06 then
				boltT = 0
			end
			-- egg: in, wobble, jolt each step, shake + white during the charge
			local inU = backOut(t / 0.45)
			local jolt = L > 0 and math.exp(-(t - starts[L]) * 7) or 0
			local wob = math.sin(t * 9) * 0.06 + jolt * 0.35 * math.sin((t - (starts[L] or 0)) * 40)
			local sh = chargeU * 0.22
			local eggCF = cf * CFrame.new(math.sin(t * 70) * sh, math.sin(t * 2.4) * 0.15 + math.cos(t * 83) * sh * 0.6, 0) * CFrame.Angles(0, t * 0.8, wob) * rot
			if t < T_POP then
				egg.CFrame = eggCF
				egg.Size = eggSize * math.max(inU, 0.01) * (1 + jolt * 0.08 + chargeU * 0.06 * math.sin(t * 40))
				egg.Transparency = 0
				hot.CFrame = eggCF
				hot.Transparency = 1 - clamp((chargeU - 0.35) / 0.65)
				hot.Color = WHITE:Lerp(col, 0.25)
			else
				egg.Transparency = 1
				hot.Transparency = 1
			end
			backGlow.CFrame = cf * CFrame.new(0, 0, -3.8) * CFrame.Angles(0, math.pi / 2, 0)
			backGlow.Color = col
			backGlow.Size = Vector3.new(0.2, 9 + jolt * 3 + chargeU * 5, 9 + jolt * 3 + chargeU * 5)
			backGlow.Transparency = t < T_POP and (0.55 - jolt * 0.3 - chargeU * 0.3) or 1
			light.Brightness = (t < T_POP) and (1 + jolt * 4 + chargeU * 6) or math.max(0, 9 * math.exp(-(t - T_POP) * 3))
			aura.Rate = (t < T_POP and t > 0.3) and (12 + L * 6 + chargeU * 90) or 0
			-- step ring
			if L > 0 then
				local u = clamp((t - starts[L]) / 0.55)
				ringA(cf, 2.4 + 6 * eo(u), (1 - u) * 0.9, col, 0.5 * (1 - u) + 0.1)
			end
			-- rarity name on top
			if L > 0 and t < T_POP then
				txt(top, topSt, RNAME[L], 1)
				topSc.Scale = topSc.Scale + (1 - topSc.Scale) * math.min(1, dt * 12)
			end
			-- comets spiral in
			for i, c in ipairs(comets) do
				local on = t > T_CHARGE - 0.2 and t < T_POP
				c.tr.Enabled = on
				if on then
					local u = clamp((t - T_CHARGE + 0.2) / (CHARGE + 0.2))
					local r = 7 * (1 - u) + 0.6
					local a = c.ph + u * 9
					c.p.CFrame = cf * CFrame.new(math.cos(a) * r, math.sin(a) * r * 0.75, math.sin(a + 1) * 1.5)
					c.p.Color = col
					c.p.Transparency = 0.1
					c.tr.Color = ColorSequence.new(WHITE, col)
				else
					c.p.Transparency = 1
				end
			end
			once("riser", function()
				if t >= T_CHARGE then
					snd("riser", 0.6, 1)
				end
			end)
			if t < T_CHARGE then
				fired.riser = nil
			end

			-- POP
			if t >= T_POP then
				once("pop", function()
					snd("burst", 0.6, 1)
					setCol(burst, WHITE, col)
					burst:Emit(90 + R * 25)
					setCol(sparks, WHITE, col)
					sparks:Emit(50 + R * 15)
					setCol(smoke, col:Lerp(WHITE, 0.5))
					smoke:Emit(14)
					setCol(flare, WHITE, col)
					flare.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 16), NumberSequenceKeypoint.new(0.3, 11), NumberSequenceKeypoint.new(1, 0) })
					flare:Emit(2)
					setCol(streaks, WHITE, col)
					streaks:Emit(60 + R * 20)
					for _, b in ipairs(bolts) do
						for _, s in ipairs(b.segs) do
							s.Enabled = false
						end
					end
					if R >= 4 then
						confetti:Emit(80 + R * 20)
					end
					for _, s in ipairs(shards) do
						s.p.Color = egg.Color
						s.p.Transparency = 0
					end
				end)
				local u = t - T_POP
				flash.BackgroundTransparency = clamp(u / 0.35) * 1
				ringB(cf, 1 + 16 * eo(u / 0.6), 1 - clamp(u / 0.6), col, 1.2 * (1 - clamp(u / 0.6)) + 0.1)
				ringC(cf, 0.5 + 10 * eo(u / 0.9), 0.8 * (1 - clamp(u / 0.9)), WHITE, 0.4)
				for _, s in ipairs(shards) do
					local q = u * 0.8
					s.p.CFrame = cf * CFrame.new(s.v * q + Vector3.new(0, -9 * q * q, 0)) * CFrame.Angles(s.spin.X * q, s.spin.Y * q, s.spin.Z * q)
					s.p.Transparency = clamp((u - 0.7) / 0.6)
				end
				-- rays + golden rain for the rare ones
				for i, r in ipairs(rays) do
					local on = R >= 3 and t < T_OUT
					r.b.Enabled = on
					if on then
						local a = i * math.pi * 2 / #rays + t * 0.6
						local len = (6 + (i % 2) * 3) * eo(u / 0.5) * (R >= 5 and 1.4 or 1)
						r.tip.WorldPosition = cf.Position + (cf.RightVector * math.cos(a) + cf.UpVector * math.sin(a)) * len - cf.LookVector * 1.5
						r.b.Color = ColorSequence.new(WHITE, R >= 5 and GOLD or col)
						r.b.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3 + 0.4 * clamp((t - T_OUT + 0.4) / 0.4)), NumberSequenceKeypoint.new(1, 1) })
					end
				end
				goldRain.Rate = (R >= 5 and t < T_OUT) and 60 or 0
				aura.Rate = t < T_OUT and 18 or 0
				setCol(aura, WHITE, col)
				-- the pet
				local g = (u > 0.05) and backOut((u - 0.05) / 0.6) or 0.01
				local out = clamp((t - T_OUT) / 0.4)
				local kk = fit * math.max(g * (1 - out), 0.01)
				if math.abs(kk - lastK) > 0.002 then
					lastK = kk
					model:ScaleTo(kk)
				end
				local spin = math.pi * 2 * (1 - eo(u / 1.2)) + 0.25 * math.sin(u * 1.6)
				local pcf = cf * CFrame.new(0, -1.6 + 0.2 * math.sin(u * 2.2) - out * 6, 0) * CFrame.Angles(0, math.pi + spin, 0)
				model:PivotTo(pcf * CFrame.new(-off * kk))
				-- spotlight from above + a glowing ring under the pet
				local sa = eo((u - 0.1) / 0.5) * (1 - out)
				spot.Enabled = sa > 0.01
				spotTop.WorldPosition = cf.Position + Vector3.new(0, 11, -1)
				spotBot.WorldPosition = cf.Position + Vector3.new(0, -4.2, 0)
				spot.Color = ColorSequence.new(WHITE, col)
				spot.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1 - 0.1 * sa), NumberSequenceKeypoint.new(0.6, 1 - 0.3 * sa), NumberSequenceKeypoint.new(1, 1 - 0.15 * sa) })
				local floor = cf * CFrame.new(0, -4.3, 0) * CFrame.Angles(math.pi / 2, 0, t * 0.7)
				podium(floor, 3.2 * sa + 0.1, 0.85 * sa, col, 0.3)
				podium2(floor * CFrame.Angles(0, 0, -t * 1.6), (4.1 + 0.25 * math.sin(t * 3)) * sa + 0.1, 0.6 * sa, WHITE, 0.12)
				-- texts
				txt(top, topSt, RNAME[R], 1 - out)
				local nu = eo((u - 0.45) / 0.5) * (1 - out)
				txt(nameL, nameSt, d.petName(pet), nu)
				nameL.TextColor3 = col
				nameSc.Scale = 0.85 + 0.15 * nu
				txt(oddsL, oddsSt, (job.isNew and "NEW!   " or "") .. d.oddsText, eo((u - 0.75) / 0.5) * (1 - out))
				once("reveal", function()
					snd("reveal", 0.4, 1)
					if R >= 5 then
						snd("legend", 0.3, 1)
					end
				end)
			end
			hint.TextTransparency = speed > 1 and 1 or 0.5
			if t >= T_END then
				done = true
			end
		end)
		if not ok then
			warn("hatch vfx: " .. tostring(err))
			done = true
		end
	end)

	local limit = os.clock() + T_END * k + 15
	while not done and os.clock() < limit do
		task.wait()
	end
	conn:Disconnect()
	tapConn:Disconnect()
	-- restore everything
	folder:Destroy()
	gui:Destroy()
	cc:Destroy()
	dof:Destroy()
	blur:Destroy()
	bloom:Destroy()
	cam.FieldOfView = fov0
	for o, v in pairs(hidden) do
		if o.Parent then
			o.LocalTransparencyModifier = v
		end
	end
	cam.CameraType = saved.type
	if saved.type ~= Enum.CameraType.Scriptable then
		cam.CFrame = saved.cf
	end
	for _, g in ipairs(saved.guis) do
		if g.Parent then
			g.Enabled = true
		end
	end
end

return M
