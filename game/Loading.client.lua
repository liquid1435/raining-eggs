-- v192 (user: the game lags at the start): loading screen (ReplicatedFirst.Loading)
-- covers the screen while the map, the meshes and the textures load, so the player only sees the game once it is ready.
-- Ends when: game loaded + map there + character there + the download queue is (almost) empty; min 3 s, max 30 s.
local Players = game:GetService("Players")
local RF = game:GetService("ReplicatedFirst")
local CP = game:GetService("ContentProvider")
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")

local plr = Players.LocalPlayer
pcall(function()
	RF:RemoveDefaultLoadingScreen()
end)

local gui = Instance.new("ScreenGui")
gui.Name = "LoadingScreen"
gui.IgnoreGuiInset = true
gui.DisplayOrder = 1000
gui.ResetOnSpawn = false

local bg = Instance.new("Frame")
bg.Size = UDim2.fromScale(1, 1)
bg.BorderSizePixel = 0
bg.BackgroundColor3 = Color3.new(1, 1, 1)
bg.Parent = gui
local grad = Instance.new("UIGradient")
grad.Rotation = 90
grad.Color = ColorSequence.new(Color3.fromRGB(110, 190, 255), Color3.fromRGB(70, 110, 235))
grad.Parent = bg

local function label(text, size, pos, col, font)
	local t = Instance.new("TextLabel")
	t.BackgroundTransparency = 1
	t.AnchorPoint = Vector2.new(0.5, 0.5)
	t.Size, t.Position = size, pos
	t.Font = font or Enum.Font.LuckiestGuy
	t.TextScaled = true
	t.Text = text
	t.TextColor3 = col
	local s = Instance.new("UIStroke")
	s.Thickness = 4
	s.Color = Color3.fromRGB(20, 24, 60)
	s.Parent = t
	t.Parent = bg
	return t
end

-- bouncing egg (white with spots)
local egg = Instance.new("Frame")
egg.AnchorPoint = Vector2.new(0.5, 0.5)
egg.Position = UDim2.fromScale(0.5, 0.36)
egg.Size = UDim2.fromScale(0.09, 0.16)
egg.BackgroundColor3 = Color3.fromRGB(255, 250, 236)
egg.BorderSizePixel = 0
egg.Parent = bg
Instance.new("UIAspectRatioConstraint", egg).AspectRatio = 0.78
local ec = Instance.new("UICorner")
ec.CornerRadius = UDim.new(0.5, 0)
ec.Parent = egg
local es = Instance.new("UIStroke")
es.Thickness = 4
es.Color = Color3.fromRGB(20, 24, 60)
es.Parent = egg
for _, d in ipairs({ { 0.3, 0.3, 0.22 }, { 0.62, 0.5, 0.18 }, { 0.38, 0.68, 0.14 } }) do
	local spot = Instance.new("Frame")
	spot.AnchorPoint = Vector2.new(0.5, 0.5)
	spot.Position = UDim2.fromScale(d[1], d[2])
	spot.Size = UDim2.fromScale(d[3], d[3] * 0.78)
	spot.BackgroundColor3 = Color3.fromRGB(150, 200, 120)
	spot.BorderSizePixel = 0
	Instance.new("UICorner", spot).CornerRadius = UDim.new(0.5, 0)
	spot.Parent = egg
end

label("RAINING EGGS", UDim2.fromScale(0.7, 0.13), UDim2.fromScale(0.5, 0.58), Color3.fromRGB(255, 226, 70))
local status = label("Loading...", UDim2.fromScale(0.5, 0.05), UDim2.fromScale(0.5, 0.79), Color3.new(1, 1, 1), Enum.Font.FredokaOne)

local barBg = Instance.new("Frame")
barBg.AnchorPoint = Vector2.new(0.5, 0.5)
barBg.Position = UDim2.fromScale(0.5, 0.71)
barBg.Size = UDim2.fromScale(0.42, 0.04)
barBg.BackgroundColor3 = Color3.fromRGB(30, 40, 90)
barBg.BorderSizePixel = 0
barBg.Parent = bg
Instance.new("UICorner", barBg).CornerRadius = UDim.new(1, 0)
local bs = Instance.new("UIStroke")
bs.Thickness = 3
bs.Color = Color3.fromRGB(20, 24, 60)
bs.Parent = barBg
local fill = Instance.new("Frame")
fill.Size = UDim2.fromScale(0.03, 1)
fill.BackgroundColor3 = Color3.fromRGB(120, 230, 90)
fill.BorderSizePixel = 0
fill.Parent = barBg
Instance.new("UICorner", fill).CornerRadius = UDim.new(1, 0)

gui.Parent = plr:WaitForChild("PlayerGui")

local t0 = os.clock()
local bounce = RunService.RenderStepped:Connect(function()
	local t = os.clock() - t0
	egg.Position = UDim2.fromScale(0.5, 0.36 - math.abs(math.sin(t * 4)) * 0.05)
	egg.Rotation = math.sin(t * 4) * 8
end)

local shown = 0.03
local function setProgress(p, text)
	shown = math.max(shown, math.clamp(p, 0.03, 1))
	TweenService:Create(fill, TweenInfo.new(0.25), { Size = UDim2.fromScale(shown, 1) }):Play()
	if text then
		status.Text = text
	end
end

-- 1) the place itself
if not game:IsLoaded() then
	setProgress(0.1, "Loading the world...")
	game.Loaded:Wait()
end
setProgress(0.35, "Loading the map...")
workspace:WaitForChild("Map", 20)
-- 2) your character
setProgress(0.5, "Getting you ready...")
if not plr.Character then
	plr.CharacterAdded:Wait()
end
-- 3) meshes and textures: wait until the download queue is (almost) empty
local startQ = math.max(CP.RequestQueueSize, 1)
while os.clock() - t0 < 30 do
	local q = CP.RequestQueueSize
	setProgress(0.5 + 0.48 * (1 - math.min(q, startQ) / startQ), "Loading pets and eggs...")
	if q <= 5 and os.clock() - t0 > 3 then
		break
	end
	task.wait(0.2)
end
setProgress(1, "Ready!")
task.wait(0.6) -- one more moment so the first frames are rendered under the screen

-- fade out
for _, d in ipairs(bg:GetDescendants()) do
	if d:IsA("TextLabel") then
		TweenService:Create(d, TweenInfo.new(0.5), { TextTransparency = 1 }):Play()
	elseif d:IsA("UIStroke") then
		TweenService:Create(d, TweenInfo.new(0.5), { Transparency = 1 }):Play()
	elseif d:IsA("Frame") then
		TweenService:Create(d, TweenInfo.new(0.5), { BackgroundTransparency = 1 }):Play()
	end
end
TweenService:Create(bg, TweenInfo.new(0.6), { BackgroundTransparency = 1 }):Play()
task.wait(0.65)
bounce:Disconnect()
gui:Destroy()
