local Debris = game:GetService("Debris")
local RunService = game:GetService("RunService")
local FX = require(script.Parent.FX)
local Players = game:GetService("Players")
local WeaponFX = {}
local swings = setmetatable({}, {__mode = "k"})
local activeHits = setmetatable({}, {__mode = "k"})

local function rig(character)
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if not humanoid then return nil end
	return humanoid:FindFirstChildOfClass("Animator"), humanoid.RigType.Name
end

function WeaponFX.PlaySwing(tool)
	local handle = tool:FindFirstChild("Handle")
	if not handle or not handle:IsA("BasePart") then return end
	local previous = swings[tool]
	if previous then previous() end
	local animator, rigName = rig(tool.Parent)
	local track = if rigName then FX.clip(animator,tool:GetAttribute("Swing"..rigName)) else nil
	local a = handle:FindFirstChild("TrailBase") or FX.attach(handle,Vector3.yAxis*handle.Size.Y*.1)
	local b = handle:FindFirstChild("TrailTip") or FX.attach(handle,Vector3.yAxis*handle.Size.Y*.48)
	local trail = FX.trail(handle,a,b,FX.teal)
	trail.Enabled = false
	local glints = FX.emitter(b, FX.cream, .18)
	glints.Speed = NumberRange.new(.6, 2.5)
	glints.Lifetime = NumberRange.new(.08, .22)
	local active = true
	local function finish()
		if not active then return end
		active = false
		if track and track.IsPlaying then track:Stop(.04) end
		trail.Enabled = false
		glints.Enabled = false
		Debris:AddItem(glints,.25)
		Debris:AddItem(trail,.25)
		if a.Name == "Attachment" then Debris:AddItem(a,.25) end
		if b.Name == "Attachment" then Debris:AddItem(b,.25) end
		swings[tool] = nil
	end
	swings[tool] = finish
	task.delay(.14,function() if active and trail.Parent then trail.Enabled = true glints.Rate = 65 end end)
	task.delay(.37,function() if active and trail.Parent then trail.Enabled = false glints.Rate = 0 end end)
	task.delay(.82,finish)
	return track
end

local function stumble(character, root, direction)
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	local torso = character:FindFirstChild("LowerTorso") or character:FindFirstChild("Torso")
	local joint
	for _, motor in character:GetDescendants() do
		if motor:IsA("Motor6D") and motor.Part0 == root and motor.Part1 == torso then
			joint = motor
			break
		end
	end
	local planar = Vector3.new(direction.X, 0, direction.Z)
	if planar.Magnitude < .001 then planar = Vector3.xAxis end
	planar = planar.Unit
	local start = os.clock()
	local offset = Vector3.zero
	local localPose, appliedPose
	local before, after
	local function restore()
		if joint and joint.Parent and appliedPose and joint.Transform == appliedPose then
			joint.Transform = localPose
		end
		appliedPose = nil
		if humanoid and humanoid.Parent then humanoid.CameraOffset -= offset end
		offset = Vector3.zero
	end
	local function finish()
		before:Disconnect()
		after:Disconnect()
		restore()
		activeHits[character] = nil
	end
	before = RunService.PreAnimation:Connect(restore)
	after = RunService.PreSimulation:Connect(function()
		local t = os.clock() - start
		if t >= .82 or not root:IsDescendantOf(workspace) then
			finish()
			return
		end
		if joint and joint.Parent then
			local arc = math.sin(t * 12) * math.exp(-4.6 * t) * math.min(1, (.82-t)/.12)
			local basis = root.CFrame * joint.C0
			local axis = basis:VectorToObjectSpace(Vector3.yAxis:Cross(planar))
			local lift = basis:VectorToObjectSpace((planar * .35 + Vector3.yAxis * .22) * arc)
			localPose = joint.Transform
			joint.Transform = CFrame.new(lift) * CFrame.fromAxisAngle(axis, arc * .36) * localPose
			appliedPose = joint.Transform
		end
		if humanoid and Players.LocalPlayer.Character == character and t < .16 then
			offset = Vector3.new(math.sin(90*t), math.cos(72*t), 0) * (.12 * (1-t/.16))
			humanoid.CameraOffset += offset
		end
	end)
	activeHits[character] = finish
end

function WeaponFX.PlayHit(character, swingTrack, direction)
	local head = character:FindFirstChild("Head")
	if not head or not head:IsA("BasePart") then return end
	if swingTrack and swingTrack.IsPlaying then
		local speed = swingTrack.Speed
		if speed ~= 0 then
			swingTrack:AdjustSpeed(0)
			task.delay(.055,function()
				if swingTrack.IsPlaying and swingTrack.Speed == 0 then swingTrack:AdjustSpeed(speed) end
			end)
		end
	end
	local animator, rigName = rig(character)
	if rigName then FX.clip(animator,script:GetAttribute("Hit"..rigName)) end
	local previous = activeHits[character]
	if previous then previous() end
	local root = character:FindFirstChild("HumanoidRootPart")
	local recoil = if typeof(direction) == "Vector3" and direction.Magnitude > .001
		then direction.Unit else -head.CFrame.LookVector
	if root and root:IsA("BasePart") then stumble(character, root, recoil) end
	local fx = FX.anchor(head.Position - Vector3.yAxis * .65 - recoil * .5, 1.15)
	local sound = Instance.new("Sound")
	sound.SoundId = script:GetAttribute("HitSound") or "rbxasset://sounds/collide.wav"
	sound.Volume, sound.RollOffMaxDistance, sound.Parent = .65, 65, fx
	sound:Play()
	local pop = FX.emitter(fx, FX.gold, .48, "rbxasset://textures/particles/smoke_main.dds")
	pop.Lifetime = NumberRange.new(.10, .21)
	pop.Speed = NumberRange.new(4, 9)
	pop:Emit(10)
	local streak = FX.emitter(fx, FX.cream, .17, "rbxasset://textures/particles/fire_main.dds")
	streak.Lifetime = NumberRange.new(.08,.15)
	streak.Speed = NumberRange.new(12,20)
	streak:Emit(7)
end
return WeaponFX
