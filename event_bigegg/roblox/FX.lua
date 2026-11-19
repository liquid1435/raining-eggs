-- Local presentation primitives shared by the two public modules.
local TweenService = game:GetService("TweenService")
local Debris = game:GetService("Debris")
local FX = {}
FX.gold = Color3.fromRGB(255, 185, 55)
FX.cream = Color3.fromRGB(255, 246, 190)
FX.teal = Color3.fromRGB(65, 222, 213)
FX.plum = Color3.fromRGB(49, 34, 79)
FX.coral = Color3.fromRGB(255, 97, 116)

function FX.clip(animator, assetId, looped, fade)
	if not animator or not assetId or assetId == "" then return nil end
	local anim = Instance.new("Animation")
	anim.AnimationId = assetId
	local ok, track = pcall(function() return animator:LoadAnimation(anim) end)
	anim:Destroy()
	if not ok then return nil end
	track.Priority = Enum.AnimationPriority.Action2
	track.Looped = looped == true
	track:Play(fade or .035)
	track.Ended:Once(function() track:Destroy() end)
	return track
end

function FX.tween(object, duration, properties, style)
	local tween = TweenService:Create(object, TweenInfo.new(duration, style or Enum.EasingStyle.Quad, Enum.EasingDirection.Out), properties)
	tween:Play()
	return tween
end

function FX.part(parent, name, size, at, color)
	local part = Instance.new("Part")
	part.Name = name
	part.Anchored = true
	part.CanCollide = false
	part.CanTouch = false
	part.CanQuery = false
	part.CastShadow = false
	part.Material = Enum.Material.Neon
	part.Size = size
	part.CFrame = at
	part.Color = color
	part.Parent = parent
	return part
end

function FX.anchor(pos, life)
	local part = FX.part(workspace, "BigEggFX", Vector3.one * 0.1, CFrame.new(pos), FX.gold)
	part.Transparency = 1
	Debris:AddItem(part, life)
	return part
end

function FX.attach(part, offset)
	local attachment = Instance.new("Attachment")
	attachment.Position = offset
	attachment.Parent = part
	return attachment
end

function FX.trail(part, a, b, color)
	local trail = Instance.new("Trail")
	trail.Attachment0 = a
	trail.Attachment1 = b
	trail.Color = ColorSequence.new(FX.cream, color)
	trail.Lifetime = 0.22
	trail.FaceCamera = true
	trail.LightEmission = 1
	trail.Transparency = NumberSequence.new(0.08, 1)
	trail.WidthScale = NumberSequence.new(1, 0)
	trail.Parent = part
	return trail
end

function FX.emitter(parent, color, size, texture)
	local emitter = Instance.new("ParticleEmitter")
	emitter.Texture = texture or "rbxasset://textures/particles/sparkles_main.dds"
	emitter.Color = ColorSequence.new(FX.cream, color)
	emitter.LightEmission = 0.65
	emitter.Size = NumberSequence.new(size, 0)
	emitter.Transparency = NumberSequence.new(0.1, 1)
	emitter.Lifetime = NumberRange.new(0.45, 0.95)
	emitter.Speed = NumberRange.new(6, 16)
	emitter.SpreadAngle = Vector2.new(180, 180)
	emitter.Rate = 0
	emitter.Parent = parent
	return emitter
end

-- Four cubic beam arcs form a hollow ring without an uploaded texture.
function FX.ring(part, radius, width, color)
	local arcs = {}
	for i = 1, 4 do
		local a = (i - 1) * math.pi / 2
		local attachment = FX.attach(part, Vector3.new(math.cos(a), 0, math.sin(a)) * radius)
		attachment.Axis = Vector3.new(-math.sin(a), 0, math.cos(a))
		arcs[i] = attachment
	end
	local beams = {}
	for i, a in ipairs(arcs) do
		local beam = Instance.new("Beam")
		beam.Attachment0 = a
		beam.Attachment1 = arcs[i % 4 + 1]
		beam.Width0 = width
		beam.Width1 = width
		beam.Color = ColorSequence.new(color)
		beam.Transparency = NumberSequence.new(0.05)
		beam.LightEmission = 1
		beam.FaceCamera = true
		beam.Segments = 16
		beam.Parent = part
		beams[i] = beam
	end
	local function resize(r, fade)
		for i, beam in ipairs(beams) do
			local a = (i - 1) * math.pi / 2
			arcs[i].Position = Vector3.new(math.cos(a), 0, math.sin(a)) * r
			beam.CurveSize0 = r * 0.552285
			beam.CurveSize1 = beam.CurveSize0
			beam.Transparency = NumberSequence.new(fade)
		end
	end
	resize(radius, 0.05)
	return resize
end

function FX.root(object)
	return if object:IsA("BasePart") then object else object.PrimaryPart or object:FindFirstChildWhichIsA("BasePart", true)
end

function FX.label(parent, size)
	local label = Instance.new("TextLabel")
	label.Size = size
	label.BackgroundTransparency = 1
	label.TextScaled = true
	label.Font = Enum.Font.FredokaOne
	label.TextColor3 = FX.cream
	label.TextStrokeColor3 = FX.plum
	label.TextStrokeTransparency = 0.3
	label.Parent = parent
	return label
end
return FX
