-- v198 (user: "make the loading screen professional and nicer"), first version v192.
-- ReplicatedFirst.Loading: covers the screen while the map, the meshes and the textures load.
-- Look: night-sky gradient, slowly turning light rays, colourful eggs raining down, gold RAINING EGGS logo with a moving
-- shine, a spinning legendary pet (once its meshes are there), a dark-glass panel with gold rim, glossy striped progress
-- bar + percent, status line and rotating tips. Ends when: game loaded + map + character + download queue (almost) empty;
-- min 3 s, max 30 s. Then a soft white flash and fade.
local Players = game:GetService("Players")
local RF = game:GetService("ReplicatedFirst")
local RS = game:GetService("ReplicatedStorage")
local CP = game:GetService("ContentProvider")
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")

local plr = Players.LocalPlayer
pcall(function()
	RF:RemoveDefaultLoadingScreen()
end)

local INK = Color3.fromRGB(20, 16, 44)
local GOLD = Color3.fromRGB(255, 205, 60)
local WHITE = Color3.new(1, 1, 1)

local function new(cls, props, parent)
	local o = Instance.new(cls)
	for k, v in pairs(props) do
		o[k] = v
	end
	o.Parent = parent
	return o
end
local function stroke(o, th, col)
	return new("UIStroke", { Thickness = th, Color = col or INK, ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual }, o)
end
local function corner(o, r)
	return new("UICorner", { CornerRadius = r or UDim.new(1, 0) }, o)
end

local gui = new("ScreenGui", { Name = "LoadingScreen", IgnoreGuiInset = true, DisplayOrder = 1000, ResetOnSpawn = false }, nil)
local bg = new("Frame", { Size = UDim2.fromScale(1, 1), BorderSizePixel = 0, BackgroundColor3 = WHITE, ClipsDescendants = true }, gui)
new("UIGradient", {
	Rotation = 90,
	Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, Color3.fromRGB(34, 24, 92)),
		ColorSequenceKeypoint.new(0.55, Color3.fromRGB(78, 52, 170)),
		ColorSequenceKeypoint.new(1, Color3.fromRGB(150, 90, 220)),
	}),
}, bg)

-- light rays behind the logo (slowly turning)
local rays = new("Frame", {
	AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.36), Size = UDim2.fromScale(1.6, 1.6),
	BackgroundTransparency = 1, ZIndex = 1,
}, bg)
new("UIAspectRatioConstraint", { AspectRatio = 1 }, rays)
for k = 0, 11 do -- 12 bars through the centre = 24 rays (Roblox turns a frame around its own centre)
	local r = new("Frame", {
		AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(0.05, 1),
		BackgroundColor3 = Color3.fromRGB(255, 230, 160), BorderSizePixel = 0, Rotation = k * 15, ZIndex = 1,
	}, rays)
	new("UIGradient", {
		Rotation = 90,
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.82), NumberSequenceKeypoint.new(1, 1) }),
	}, r)
end
-- soft glow in the middle
local glow = new("Frame", {
	AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.36), Size = UDim2.fromScale(0.55, 0.55),
	BackgroundColor3 = Color3.fromRGB(255, 220, 150), BorderSizePixel = 0, ZIndex = 1,
}, bg)
new("UIAspectRatioConstraint", { AspectRatio = 1 }, glow)
corner(glow)
new("UIGradient", {
	Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.75), NumberSequenceKeypoint.new(1, 1) }),
}, glow)

-- raining eggs: the real egg models of the game (ReplicatedStorage.Assets Egg_1..Egg_10, Egg_Gold) falling in 3D
-- (v202, user). They appear as soon as the meshes are downloaded; until then the sky and the rays show.
local eggVp = new("ViewportFrame", {
	Size = UDim2.fromScale(1, 1), BackgroundTransparency = 1, ZIndex = 2,
	Ambient = Color3.fromRGB(190, 180, 220), LightColor = WHITE, LightDirection = Vector3.new(-0.5, -1, -0.7),
}, bg)
local eggCam = new("Camera", { FieldOfView = 50, CFrame = CFrame.lookAt(Vector3.new(0, 0, 60), Vector3.zero) }, eggVp)
eggVp.CurrentCamera = eggCam
local eggs = {}
local rng = Random.new()
local function spawnEggs()
	task.spawn(function()
		local assets = RS:WaitForChild("Assets", 30)
		if not assets then
			return
		end
		local names = { "Egg_1", "Egg_2", "Egg_3", "Egg_4", "Egg_5", "Egg_6", "Egg_7", "Egg_8", "Egg_9", "Egg_10", "Egg_Gold" }
		for k = 1, 20 do
			local src = assets:FindFirstChild(names[(k - 1) % #names + 1], true)
			if src and src:IsA("BasePart") then
				local e = src:Clone()
				local sz = rng:NextNumber(4, 7.5)
				e.Size = src.Size * (sz / math.max(src.Size.X, src.Size.Y, src.Size.Z))
				e.Anchored = true
				e.Parent = eggVp
				eggs[#eggs + 1] = { p = e, x = rng:NextNumber(-48, 48), y = rng:NextNumber(-40, 45), z = rng:NextNumber(-25, 8),
					v = rng:NextNumber(7, 15), spin = rng:NextNumber(-1.5, 1.5), tilt = rng:NextNumber(-0.5, 0.5), a0 = rng:NextNumber(0, 6.28) }
			end
		end
	end)
end

-- logo
local logo = new("TextLabel", {
	AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.2), Size = UDim2.fromScale(0.72, 0.17),
	BackgroundTransparency = 1, Font = Enum.Font.LuckiestGuy, TextScaled = true, Text = "RAINING EGGS", TextColor3 = WHITE, ZIndex = 6,
}, bg)
stroke(logo, 7)
local logoGrad = new("UIGradient", {
	Rotation = 90,
	Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 248, 170)),
		ColorSequenceKeypoint.new(0.5, Color3.fromRGB(255, 205, 60)),
		ColorSequenceKeypoint.new(1, Color3.fromRGB(255, 128, 30)),
	}),
}, logo)
-- shine that sweeps over the logo
local shine = new("TextLabel", {
	AnchorPoint = Vector2.new(0.5, 0.5), Position = logo.Position, Size = logo.Size, BackgroundTransparency = 1,
	Font = Enum.Font.LuckiestGuy, TextScaled = true, Text = "RAINING EGGS", TextColor3 = WHITE, ZIndex = 7,
}, bg)
local shineGrad = new("UIGradient", {
	Rotation = 20,
	Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.42, 1), NumberSequenceKeypoint.new(0.5, 0.25),
		NumberSequenceKeypoint.new(0.58, 1), NumberSequenceKeypoint.new(1, 1),
	}),
	Offset = Vector2.new(-1, 0),
}, shine)
local sub = new("TextLabel", {
	AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.305), Size = UDim2.fromScale(0.4, 0.045),
	BackgroundTransparency = 1, Font = Enum.Font.FredokaOne, TextScaled = true, Text = "catch them all - hatch them all",
	TextColor3 = Color3.fromRGB(230, 220, 255), ZIndex = 6,
}, bg)
stroke(sub, 3)

-- bottom panel: dark glass with gold rim
local panel = new("Frame", {
	AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.fromScale(0.5, 0.94), Size = UDim2.fromScale(0.5, 0.2),
	BackgroundColor3 = Color3.fromRGB(26, 18, 56), BackgroundTransparency = 0.12, BorderSizePixel = 0, ZIndex = 8,
}, bg)
new("UISizeConstraint", { MaxSize = Vector2.new(760, 200) }, panel)
corner(panel, UDim.new(0.22, 0))
local rim = new("UIStroke", { Thickness = 4, Color = GOLD, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, panel)
new("UIGradient", { Rotation = 0, Color = ColorSequence.new(Color3.fromRGB(255, 240, 170), Color3.fromRGB(230, 150, 30)) }, rim)
local status = new("TextLabel", {
	Position = UDim2.fromScale(0.06, 0.1), Size = UDim2.fromScale(0.7, 0.24), BackgroundTransparency = 1,
	Font = Enum.Font.LuckiestGuy, TextScaled = true, Text = "Loading...", TextColor3 = WHITE, TextXAlignment = Enum.TextXAlignment.Left, ZIndex = 9,
}, panel)
stroke(status, 2.5)
local pct = new("TextLabel", {
	Position = UDim2.fromScale(0.74, 0.1), Size = UDim2.fromScale(0.2, 0.24), BackgroundTransparency = 1,
	Font = Enum.Font.LuckiestGuy, TextScaled = true, Text = "0%", TextColor3 = GOLD, TextXAlignment = Enum.TextXAlignment.Right, ZIndex = 9,
}, panel)
stroke(pct, 2.5)
local barBg = new("Frame", {
	Position = UDim2.fromScale(0.06, 0.42), Size = UDim2.fromScale(0.88, 0.2), BackgroundColor3 = Color3.fromRGB(12, 8, 30),
	BorderSizePixel = 0, ZIndex = 9, ClipsDescendants = true,
}, panel)
corner(barBg)
stroke(barBg, 2.5, Color3.fromRGB(0, 0, 0))
local fill = new("Frame", { Size = UDim2.fromScale(0.03, 1), BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 10, ClipsDescendants = true }, barBg)
corner(fill)
new("UIGradient", { Rotation = 90, Color = ColorSequence.new(Color3.fromRGB(170, 255, 120), Color3.fromRGB(40, 175, 70)) }, fill)
-- moving diagonal stripes inside the fill
local stripes = new("Frame", { Size = UDim2.new(2, 0, 1, 0), BackgroundTransparency = 1, ZIndex = 11 }, fill)
for k = 0, 39 do
	new("Frame", {
		Position = UDim2.fromScale(k / 40, -0.5), Size = UDim2.new(0, 10, 2, 0), Rotation = 30, BorderSizePixel = 0,
		BackgroundColor3 = WHITE, BackgroundTransparency = 0.8, ZIndex = 11,
	}, stripes)
end
new("Frame", { -- gloss on the top half
	Position = UDim2.fromScale(0, 0.08), Size = UDim2.fromScale(1, 0.38), BackgroundColor3 = WHITE, BackgroundTransparency = 0.6,
	BorderSizePixel = 0, ZIndex = 12,
}, fill)
local tip = new("TextLabel", {
	Position = UDim2.fromScale(0.06, 0.7), Size = UDim2.fromScale(0.88, 0.2), BackgroundTransparency = 1,
	Font = Enum.Font.FredokaOne, TextScaled = true, Text = "", TextColor3 = Color3.fromRGB(210, 200, 255), ZIndex = 9,
}, panel)
local TIPS = {
	"TIP: Golden eggs always give a GOLD or RAINBOW pet!",
	"TIP: Run on your treadmill to reach the far zones faster",
	"TIP: Every egg has 3 different animals for each rarity",
	"TIP: Play with friends for up to +40% cash",
	"TIP: A rare SECRET EGG can fall in any zone - grab a bat!",
	"TIP: Put your best pets in your pen - they earn while you play",
}
local tipK = rng:NextInteger(1, #TIPS)
tip.Text = TIPS[tipK]

gui.Parent = plr:WaitForChild("PlayerGui")

-- animation
local t0 = os.clock()
local lastTip = t0
local anim = RunService.RenderStepped:Connect(function(dt)
	local t = os.clock() - t0
	rays.Rotation = t * 6
	glow.Size = UDim2.fromScale(0.55 + math.sin(t * 2) * 0.03, 0.55 + math.sin(t * 2) * 0.03)
	for _, e in ipairs(eggs) do
		e.y = e.y - e.v * dt
		if e.y < -45 then
			e.y, e.x = 45, rng:NextNumber(-48, 48)
		end
		e.p.CFrame = CFrame.new(e.x, e.y, e.z) * CFrame.Angles(e.tilt, e.a0 + t * e.spin, e.tilt * 0.5)
	end
	local bob = math.sin(t * 2.2) * 0.008
	logo.Position = UDim2.fromScale(0.5, 0.2 + bob)
	logo.Rotation = math.sin(t * 1.6) * 1.5
	shine.Position, shine.Rotation = logo.Position, logo.Rotation
	local k = (t % 2.6) / 2.6
	shineGrad.Offset = Vector2.new(-1 + k * 2, 0)
	stripes.Position = UDim2.new(-((t * 0.35) % 0.05) * 2, 0, 0, 0)
	if os.clock() - lastTip > 3.2 then
		lastTip = os.clock()
		tipK = tipK % #TIPS + 1
		tip.Text = TIPS[tipK]
	end
end)

local shown = 0.03
local function setProgress(p, text)
	shown = math.max(shown, math.clamp(p, 0.03, 1))
	TweenService:Create(fill, TweenInfo.new(0.25, Enum.EasingStyle.Quad), { Size = UDim2.fromScale(shown, 1) }):Play()
	pct.Text = math.floor(shown * 100 + 0.5) .. "%"
	if text then
		status.Text = text
	end
end

-- 1) the place itself
if not game:IsLoaded() then
	setProgress(0.1, "Loading the world...")
	game.Loaded:Wait()
end
setProgress(0.3, "Loading the map...")
spawnEggs()
workspace:WaitForChild("Map", 20)
-- 2) your character
setProgress(0.45, "Getting you ready...")
if not plr.Character then
	plr.CharacterAdded:Wait()
end
-- 3) meshes and textures: wait until the download queue is (almost) empty
local startQ = math.max(CP.RequestQueueSize, 1)
while os.clock() - t0 < 30 do
	local q = CP.RequestQueueSize
	setProgress(0.45 + 0.53 * (1 - math.min(q, startQ) / startQ), "Loading pets and eggs...")
	if q <= 5 and os.clock() - t0 > 3 then
		break
	end
	task.wait(0.2)
end
setProgress(1, "Ready!")
task.wait(0.7) -- one more moment so the first frames are rendered under the screen

-- soft white flash, then everything fades
local flash = new("Frame", { Size = UDim2.fromScale(1, 1), BackgroundColor3 = WHITE, BackgroundTransparency = 1, BorderSizePixel = 0, ZIndex = 50 }, gui)
TweenService:Create(flash, TweenInfo.new(0.18), { BackgroundTransparency = 0.35 }):Play()
task.wait(0.18)
bg.Visible = false
TweenService:Create(flash, TweenInfo.new(0.6), { BackgroundTransparency = 1 }):Play()
task.wait(0.62)
anim:Disconnect()
gui:Destroy()
