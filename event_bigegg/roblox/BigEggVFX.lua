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

-- ---------------------------------------------------------------- v126 compact "BIG EGG INCOMING" card
-- (user, 20 Nov: "smaller but noticeable, must not cover any UI"). It looks for the first free spot near the
-- top centre of the screen: every visible piece of the game's own UI (buttons, banners, panels, text) is
-- measured and the card moves down until it overlaps none of them; checked again twice a second.
local UIS = game:GetService("UserInputService")

local function uiRects(skip)
	local rects = {}
	local pg = Players.LocalPlayer:FindFirstChildOfClass("PlayerGui")
	local cam = workspace.CurrentCamera
	if not pg or not cam then return rects end
	local vp = cam.ViewportSize
	local function walk(obj)
		for _, c in ipairs(obj:GetChildren()) do
			if c:IsA("GuiObject") then
				if c.Visible then
					local sz, p = c.AbsoluteSize, c.AbsolutePosition
					local big = sz.X * sz.Y > vp.X * vp.Y * 0.3      -- full-screen containers / dimmers
					local drawn = c.BackgroundTransparency < 0.9
						or ((c:IsA("TextLabel") or c:IsA("TextButton")) and c.Text ~= "" and c.TextTransparency < 0.9)
						or ((c:IsA("ImageLabel") or c:IsA("ImageButton")) and c.Image ~= "" and c.ImageTransparency < 0.9)
					if drawn and not big and sz.X > 2 and sz.Y > 2 then
						table.insert(rects, { p.X, p.Y, p.X + sz.X, p.Y + sz.Y })
					end
					walk(c)
				end
			elseif c:IsA("Folder") then
				walk(c)
			end
		end
	end
	for _, g in ipairs(pg:GetChildren()) do
		if g:IsA("ScreenGui") and g.Enabled and g ~= skip then
			walk(g)                                                   -- AbsolutePosition space (same for every ScreenGui)
		end
	end
	return rects
end

-- origin = AbsolutePosition of offset (0, 0) in our own ScreenGui; returns AbsolutePosition-space x, y
local function freeSpot(w, h, skip, origin)
	local cam = workspace.CurrentCamera
	local vp = cam and cam.ViewportSize or Vector2.new(1280, 720)
	local top = origin.Y + 6                                       -- the top of our own screen area (below Roblox's top bar)
	local rects = uiRects(skip)
	local pad = 6
	local function free(x, y)
		for _, r in ipairs(rects) do
			if x - pad < r[3] and x + w + pad > r[1] and y - pad < r[4] and y + h + pad > r[2] then
				return false
			end
		end
		return true
	end
	local cx = origin.X + (vp.X - w) / 2
	local xs = { cx, cx - w * 0.6, cx + w * 0.6 }                  -- centre first, then a bit left / right
	for y = top, origin.Y + vp.Y * 0.62, 4 do
		for _, x in ipairs(xs) do
			if x >= origin.X + 4 and x + w <= origin.X + vp.X - 4 and free(x, y) then
				return x, y
			end
		end
	end
	return cx, top                                                 -- nothing free (tiny screen): top centre
end

local function incomingCard(pos)
	if gui then gui:Destroy() end
	gui = Instance.new("ScreenGui")
	gui.Name = "BigEggBanner"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.DisplayOrder = 20
	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	-- v139 (user: "a nicer, more professional UI"): gold rim + dark glass panel, an egg medallion that pops out on
	-- the left with turning light rays, LuckiestGuy title with a gold gradient, a pill on the right (arrow + distance)
	-- and a glossy countdown bar. Same api (update / close) as before.
	local vp = workspace.CurrentCamera.ViewportSize
	local w = math.clamp(vp.X * 0.28, 250, 370)
	local h = math.floor(w * 0.28)
	local DARK = Color3.fromRGB(22, 12, 40)
	local function corner(o, r) Instance.new("UICorner", o).CornerRadius = r or UDim.new(0, math.floor(h * 0.3)) end
	local function grad(o, c1, c2, rot)
		local g = Instance.new("UIGradient")
		g.Rotation = rot or 90
		g.Color = ColorSequence.new(c1, c2)
		g.Parent = o
		return g
	end
	local function outline(o, th, col)
		local st = Instance.new("UIStroke")
		st.Thickness, st.Color = th, col or DARK
		st.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
		st.Parent = o
		return st
	end
	local function text(parent, size, pos, font, col, strokeTh)
		local t = Instance.new("TextLabel")
		t.BackgroundTransparency = 1
		t.Size, t.Position = size, pos
		t.Font, t.TextColor3, t.TextScaled = font, col, true
		t.TextXAlignment = Enum.TextXAlignment.Left
		t.Parent = parent
		local st = Instance.new("UIStroke")
		st.Thickness, st.Color = strokeTh or 2, DARK
		st.Parent = t
		return t
	end
	-- the card = gold rim (gradient) with a dark outline
	local card = Instance.new("Frame")
	card.Name = "Card"
	card.Size = UDim2.fromOffset(w, h)
	card.BackgroundColor3 = Color3.new(1, 1, 1)
	card.BackgroundTransparency = 0
	card.Parent = gui
	corner(card)
	grad(card, Color3.fromRGB(255, 232, 120), Color3.fromRGB(230, 130, 20))
	local stroke = outline(card, 3, DARK)
	local scale = Instance.new("UIScale", card)
	-- dark glass panel inside the rim
	local inner = Instance.new("Frame")
	inner.Name = "Inner"
	inner.AnchorPoint = Vector2.new(0.5, 0.5)
	inner.Position = UDim2.fromScale(0.5, 0.5)
	inner.Size = UDim2.new(1, -6, 1, -6)
	inner.BackgroundColor3 = Color3.new(1, 1, 1)
	inner.ClipsDescendants = true
	inner.Parent = card
	corner(inner, UDim.new(0, math.floor(h * 0.27)))
	grad(inner, Color3.fromRGB(74, 44, 130), Color3.fromRGB(28, 16, 54))
	local shine = Instance.new("Frame")                           -- glossy top half
	shine.Size = UDim2.new(1, 0, 0.46, 0)
	shine.BackgroundColor3 = Color3.new(1, 1, 1)
	shine.BackgroundTransparency = 0.9
	shine.BorderSizePixel = 0
	shine.Parent = inner
	for k = 0, 5 do                                               -- faint diagonal stripes (like the rest of the HUD)
		local st = Instance.new("Frame")
		st.AnchorPoint = Vector2.new(0.5, 0.5)
		st.Position = UDim2.new(0, h * 1.2 + k * h * 0.55, 0.5, 0)
		st.Size = UDim2.new(0, h * 0.16, 2, 0)
		st.Rotation = 28
		st.BackgroundColor3 = Color3.new(1, 1, 1)
		st.BackgroundTransparency = 0.95
		st.BorderSizePixel = 0
		st.Parent = inner
	end
	-- egg medallion popping out on the left: turning rays, gold disc, egg with spots and a shine
	local mh = h * 1.22
	local medal = Instance.new("Frame")
	medal.Name = "Medal"
	medal.AnchorPoint = Vector2.new(0.5, 0.5)
	medal.Position = UDim2.new(0, h * 0.42, 0.5, 0)
	medal.Size = UDim2.fromOffset(mh, mh)
	medal.BackgroundTransparency = 1
	medal.ZIndex = 3
	medal.Parent = card
	local rays = Instance.new("Frame")
	rays.AnchorPoint = Vector2.new(0.5, 0.5)
	rays.Position = UDim2.fromScale(0.5, 0.5)
	rays.Size = UDim2.fromScale(1.3, 1.3)
	rays.BackgroundTransparency = 1
	rays.ZIndex = 3
	rays.Parent = medal
	for k = 0, 5 do
		local r = Instance.new("Frame")
		r.AnchorPoint = Vector2.new(0.5, 0.5)
		r.Position = UDim2.fromScale(0.5, 0.5)
		r.Size = UDim2.fromScale(0.16, 1)
		r.Rotation = k * 30
		r.BackgroundColor3 = Color3.fromRGB(255, 236, 140)
		r.BackgroundTransparency = 0.55
		r.BorderSizePixel = 0
		r.ZIndex = 3
		r.Parent = rays
		local fade = Instance.new("UIGradient")
		fade.Rotation = 90
		fade.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0), NumberSequenceKeypoint.new(1, 1) })
		fade.Parent = r
	end
	local disc = Instance.new("Frame")
	disc.AnchorPoint = Vector2.new(0.5, 0.5)
	disc.Position = UDim2.fromScale(0.5, 0.5)
	disc.Size = UDim2.fromScale(0.86, 0.86)
	disc.BackgroundColor3 = Color3.new(1, 1, 1)
	disc.ZIndex = 4
	disc.Parent = medal
	corner(disc, UDim.new(1, 0))
	grad(disc, Color3.fromRGB(255, 214, 90), Color3.fromRGB(225, 110, 20))
	outline(disc, 3, DARK)
	local ring = Instance.new("Frame")                            -- inner ring
	ring.AnchorPoint = Vector2.new(0.5, 0.5)
	ring.Position = UDim2.fromScale(0.5, 0.5)
	ring.Size = UDim2.fromScale(0.78, 0.78)
	ring.BackgroundColor3 = Color3.fromRGB(110, 50, 170)
	ring.ZIndex = 4
	ring.Parent = disc
	corner(ring, UDim.new(1, 0))
	grad(ring, Color3.fromRGB(140, 80, 220), Color3.fromRGB(60, 24, 110))
	outline(ring, 2, Color3.fromRGB(255, 240, 170))
	local eggIcon = Instance.new("Frame")
	eggIcon.AnchorPoint = Vector2.new(0.5, 0.55)
	eggIcon.Position = UDim2.fromScale(0.5, 0.55)
	eggIcon.Size = UDim2.fromScale(0.52, 0.68)
	eggIcon.BackgroundColor3 = Color3.new(1, 1, 1)
	eggIcon.ZIndex = 5
	eggIcon.Parent = ring
	corner(eggIcon, UDim.new(0.5, 0))
	grad(eggIcon, Color3.fromRGB(255, 250, 225), Color3.fromRGB(255, 196, 70))
	outline(eggIcon, 2, Color3.fromRGB(120, 60, 10))
	for _, sp in ipairs({ { 0.3, 0.55, 0.22 }, { 0.66, 0.38, 0.16 }, { 0.62, 0.74, 0.14 } }) do
		local dot = Instance.new("Frame")
		dot.AnchorPoint = Vector2.new(0.5, 0.5)
		dot.Position = UDim2.fromScale(sp[1], sp[2])
		dot.Size = UDim2.fromScale(sp[3], sp[3] * 0.76)
		dot.BackgroundColor3 = Color3.fromRGB(240, 130, 30)
		dot.ZIndex = 6
		dot.Parent = eggIcon
		corner(dot, UDim.new(1, 0))
	end
	local gloss = Instance.new("Frame")
	gloss.Position = UDim2.fromScale(0.22, 0.14)
	gloss.Size = UDim2.fromScale(0.18, 0.26)
	gloss.BackgroundColor3 = Color3.new(1, 1, 1)
	gloss.BackgroundTransparency = 0.15
	gloss.ZIndex = 6
	gloss.Parent = eggIcon
	corner(gloss, UDim.new(1, 0))
	-- texts
	local textX = h * 1.08
	local pillW = h * 0.92
	local title = text(inner, UDim2.new(1, -textX - pillW - h * 0.12, 0.42, 0), UDim2.new(0, textX, 0.1, 0), Enum.Font.LuckiestGuy,
		Color3.new(1, 1, 1), 2.5)
	title.Text = "BIG EGG INCOMING!"
	title.ZIndex = 2
	local tg = grad(title, Color3.fromRGB(255, 250, 200), Color3.fromRGB(255, 186, 40))
	local sub = text(inner, UDim2.new(1, -textX - pillW - h * 0.12, 0.28, 0), UDim2.new(0, textX, 0.54, 0), Enum.Font.FredokaOne,
		Color3.new(1, 1, 1), 2)
	sub.Text = "LANDS IN 10s"
	sub.ZIndex = 2
	-- pill on the right: arrow to the landing spot + distance
	local pill = Instance.new("Frame")
	pill.AnchorPoint = Vector2.new(1, 0.5)
	pill.Position = UDim2.new(1, -h * 0.12, 0.44, 0)
	pill.Size = UDim2.fromOffset(pillW, h * 0.6)
	pill.BackgroundColor3 = Color3.new(1, 1, 1)
	pill.ZIndex = 2
	pill.Parent = inner
	corner(pill, UDim.new(0, math.floor(h * 0.18)))
	local pillGrad = grad(pill, Color3.fromRGB(70, 230, 220), Color3.fromRGB(20, 140, 170))
	outline(pill, 2, DARK)
	local arrow = text(pill, UDim2.fromScale(0.42, 0.52), UDim2.fromScale(0.5, 0.3), Enum.Font.GothamBlack, Color3.new(1, 1, 1), 1.5)
	arrow.AnchorPoint = Vector2.new(0.5, 0.5)
	arrow.TextXAlignment = Enum.TextXAlignment.Center
	arrow.Text = "▲"
	arrow.ZIndex = 3
	local dist = text(pill, UDim2.fromScale(0.9, 0.34), UDim2.fromScale(0.05, 0.6), Enum.Font.FredokaOne, Color3.new(1, 1, 1), 1.5)
	dist.TextXAlignment = Enum.TextXAlignment.Center
	dist.ZIndex = 3
	-- glossy countdown bar along the bottom
	local track = Instance.new("Frame")
	track.AnchorPoint = Vector2.new(0, 1)
	track.Position = UDim2.new(0, textX, 1, -h * 0.1)
	track.Size = UDim2.new(1, -textX - h * 0.12, 0, math.max(5, h * 0.1))
	track.BackgroundColor3 = Color3.fromRGB(14, 8, 28)
	track.BorderSizePixel = 0
	track.ZIndex = 2
	track.Parent = inner
	corner(track, UDim.new(1, 0))
	outline(track, 1.5, Color3.fromRGB(10, 4, 20))
	local fill = Instance.new("Frame")
	fill.Size = UDim2.fromScale(1, 1)
	fill.BackgroundColor3 = Color3.new(1, 1, 1)
	fill.BorderSizePixel = 0
	fill.ZIndex = 3
	fill.Parent = track
	corner(fill, UDim.new(1, 0))
	local fillGrad = grad(fill, Color3.fromRGB(120, 255, 230), Color3.fromRGB(30, 170, 200))
	local fillShine = Instance.new("Frame")
	fillShine.Position = UDim2.fromScale(0.02, 0.12)
	fillShine.Size = UDim2.fromScale(0.96, 0.3)
	fillShine.BackgroundColor3 = Color3.new(1, 1, 1)
	fillShine.BackgroundTransparency = 0.45
	fillShine.BorderSizePixel = 0
	fillShine.ZIndex = 4
	fillShine.Parent = fill
	corner(fillShine, UDim.new(1, 0))
	local TEAL1, TEAL2 = ColorSequence.new(Color3.fromRGB(120, 255, 230), Color3.fromRGB(30, 170, 200)),
		ColorSequence.new(Color3.fromRGB(70, 230, 220), Color3.fromRGB(20, 140, 170))
	local RED1, RED2 = ColorSequence.new(Color3.fromRGB(255, 150, 120), Color3.fromRGB(230, 50, 60)),
		ColorSequence.new(Color3.fromRGB(255, 120, 110), Color3.fromRGB(200, 40, 60))
	local t0 = os.clock()
	local animConn = game:GetService("RunService").RenderStepped:Connect(function()  -- rays turn, the egg wobbles
		if not rays.Parent then return end
		local t = os.clock() - t0
		rays.Rotation = t * 40
		eggIcon.Rotation = math.sin(t * 7) * 8
		tg.Offset = Vector2.new(0, math.sin(t * 3) * 0.12)
	end)
	gui.Destroying:Connect(function() animConn:Disconnect() end)
	local function setUrgent(on)
		fillGrad.Color = on and RED1 or TEAL1
		pillGrad.Color = on and RED2 or TEAL2
	end
	local probe = Instance.new("Frame")                  -- where offset (0, 0) of our ScreenGui is on screen
	probe.BackgroundTransparency, probe.Size = 1, UDim2.fromOffset(1, 1)
	probe.Parent = gui
	local function spot()
		local o = probe.AbsolutePosition
		local ax, ay = freeSpot(w, h, gui, o)
		return ax - o.X, ay - o.Y
	end
	local x, y = spot()
	card.Position = UDim2.fromOffset(x, y - h * 0.6)
	scale.Scale = 0.6
	FX.tween(card, 0.35, { Position = UDim2.fromOffset(x, y) }, Enum.EasingStyle.Back)
	FX.tween(scale, 0.3, { Scale = 1 }, Enum.EasingStyle.Back)
	local api = {}
	local nextCheck, lastSec = 0, nil
	function api.update(t)
		local left = math.max(0, 10 - t)
		local sec = math.ceil(left)
		sub.Text = "LANDS IN " .. sec .. "s"
		fill.Size = UDim2.fromScale(left / 10, 1)
		local urgent = left <= 3
		setUrgent(urgent)
		stroke.Color = urgent and Color3.fromRGB(120, 10, 20) or Color3.fromRGB(22, 12, 40)
		if sec ~= lastSec then
			lastSec = sec
			scale.Scale = urgent and 1.06 or 1.03                  -- small "tick" every second
			FX.tween(scale, 0.25, { Scale = 1 })
		end
		local cam = workspace.CurrentCamera
		if cam then
			local rel = cam.CFrame:PointToObjectSpace(pos)
			arrow.Rotation = math.deg(math.atan2(rel.X, -rel.Z))
			local char = Players.LocalPlayer.Character
			local root = char and char:FindFirstChild("HumanoidRootPart")
			local d = root and (root.Position - pos).Magnitude
			if root and math.abs(root.Position.Y - pos.Y) > 300 then -- v131: the egg is in the other world (space is 900 up)
				dist.Text = pos.Y > 500 and "IN WORLD 2" or "IN WORLD 1"
			else
				dist.Text = d and (d < 30 and "HERE!" or (math.floor(d / 10 + 0.5) * 10 .. " studs")) or ""
			end
		end
		if t >= nextCheck then                                    -- the HUD may change (EGG STORM banner, menus...)
			nextCheck = t + 0.5
			local nx, ny = spot()
			if math.abs(nx - x) + math.abs(ny - y) > 2 then
				x, y = nx, ny
				FX.tween(card, 0.25, { Position = UDim2.fromOffset(x, y) })
			end
		end
	end
	function api.close()
		local g = gui
		FX.tween(card, 0.25, { Position = UDim2.fromOffset(x, y - h * 0.6), BackgroundTransparency = 1 })
		for _, o in ipairs(card:GetDescendants()) do
			if o:IsA("TextLabel") then FX.tween(o, 0.2, { TextTransparency = 1, TextStrokeTransparency = 1 })
			elseif o:IsA("Frame") then FX.tween(o, 0.2, { BackgroundTransparency = 1 })
			elseif o:IsA("UIStroke") then FX.tween(o, 0.2, { Transparency = 1 }) end
		end
		Debris:AddItem(g, 0.3)
	end
	return api
end

function VFX.PlayIncoming(pos)
	VFX.Clear()
	local s = state()
	local card = incomingCard(pos)
	local tint = own(s, Instance.new("ColorCorrectionEffect"))
	tint.Parent = Lighting
	FX.tween(tint, 1.3, {Brightness = -0.13, TintColor = Color3.fromRGB(192, 204, 255)})
	local marker = own(s, FX.anchor(pos + Vector3.yAxis * 0.12, 12))
	local pulse = FX.ring(marker, 8, 0.26, FX.teal)
	FX.ring(marker, 6.8, 0.11, FX.cream)
	local start = os.clock()
	run(s, function(now)
		local t = now - start
		if t >= 10 then card.close() marker:Destroy() return false end
		card.update(t)
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

-- ---------------------------------------------------------------- v126 claim badge (user, 20 Nov: "more professional,
-- higher quality"): a round badge in the middle of the egg - dark disc, smooth progress ring (gold -> cream),
-- keycap with the key to hold (E / the gamepad button / TAP on phones), a "HOLD TO CLAIM" pill under it.
-- The badge lives in PlayerGui (Adornee = the egg), so phones can tap and hold it: the prompt is Style Custom,
-- which draws no button of its own (before v126 touch players could not claim at all).
local function claimPrompt()
	local t = workspace:FindFirstChild("BigEggTarget")
	return t and t:FindFirstChildOfClass("ProximityPrompt")
end

local function keyText()
	local last = UIS:GetLastInputType()
	if last == Enum.UserInputType.Touch then
		return "TAP", "TAP & HOLD TO CLAIM"
	end
	if last.Name:find("Gamepad") then
		local pp = claimPrompt()
		local k = pp and pp.GamepadKeyCode.Name:gsub("^Button", "") or "X"
		return k, "HOLD " .. k .. " TO CLAIM"
	end
	local pp = claimPrompt()
	local k = pp and pp.KeyboardKeyCode.Name or "E"
	return k, "HOLD " .. k .. " TO CLAIM"
end

-- one half of the progress ring: a full disc clipped to its half; a sharp UIGradient decides how much shows
local function ringHalf(parent, right)
	local clip = Instance.new("Frame")
	clip.BackgroundTransparency = 1
	clip.ClipsDescendants = true
	clip.Size = UDim2.fromScale(0.5, 1)
	clip.Position = UDim2.fromScale(right and 0.5 or 0, 0)
	clip.ZIndex = 2
	clip.Parent = parent
	local disc = Instance.new("Frame")
	disc.Size = UDim2.fromScale(2, 1)
	disc.Position = UDim2.fromScale(right and -1 or 0, 0)
	disc.BackgroundColor3 = Color3.new(1, 1, 1)
	disc.BorderSizePixel = 0
	disc.ZIndex = 2
	disc.Parent = clip
	Instance.new("UICorner", disc).CornerRadius = UDim.new(1, 0)
	local g = Instance.new("UIGradient")
	g.Color = ColorSequence.new(FX.gold, FX.cream)
	g.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.5, 0),
		NumberSequenceKeypoint.new(0.501, 1), NumberSequenceKeypoint.new(1, 1) })
	g.Parent = disc
	return g, disc
end

local function buildBadge(s, root)
	local bb = Instance.new("BillboardGui")
	bb.Name = "BigEggClaim"
	bb.Size = UDim2.fromOffset(150, 186)
	bb.StudsOffsetWorldSpace = Vector3.zero -- in the middle of the egg (user, 19 Nov)
	bb.AlwaysOnTop = true
	bb.Active = true
	bb.Adornee = root
	bb.Enabled = VFX.ShowRing
	bb.MaxDistance = VFX.RingDistance -- only seen when you are close to the egg (user, 19 Nov)
	bb.ResetOnSpawn = false
	bb.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	local box = Instance.new("Frame")
	box.BackgroundTransparency = 1
	box.Size = UDim2.fromScale(1, 1)
	box.Parent = bb
	local sc = Instance.new("UIScale", box)
	local ring = Instance.new("Frame")                    -- 132 px badge at the top of the billboard
	ring.Name = "Ring"
	ring.AnchorPoint = Vector2.new(0.5, 0)
	ring.Position = UDim2.fromScale(0.5, 0)
	ring.Size = UDim2.fromOffset(132, 132)
	ring.BackgroundTransparency = 1
	ring.Parent = box
	local glow = Instance.new("Frame")                    -- soft breathing glow behind everything
	glow.AnchorPoint = Vector2.one * 0.5
	glow.Position = UDim2.fromScale(0.5, 0.5)
	glow.Size = UDim2.fromScale(1.12, 1.12)
	glow.BackgroundColor3 = FX.gold
	glow.BackgroundTransparency = 0.7
	glow.ZIndex = 0
	glow.Parent = ring
	Instance.new("UICorner", glow).CornerRadius = UDim.new(1, 0)
	local track = Instance.new("Frame")                   -- ring track (dark)
	track.Size = UDim2.fromScale(1, 1)
	track.BackgroundColor3 = Color3.fromRGB(58, 40, 98)
	track.BackgroundTransparency = 0
	track.ZIndex = 1
	track.Parent = ring
	Instance.new("UICorner", track).CornerRadius = UDim.new(1, 0)
	local ts = Instance.new("UIStroke", track)
	ts.Thickness, ts.Color, ts.Transparency = 2, FX.cream, 0.55
	local gR, dR = ringHalf(ring, true)
	local gL, dL = ringHalf(ring, false)
	local inner = Instance.new("Frame")                   -- covers the middle: what is left of the discs is the ring
	inner.AnchorPoint = Vector2.one * 0.5
	inner.Position = UDim2.fromScale(0.5, 0.5)
	inner.Size = UDim2.fromScale(0.76, 0.76)
	inner.BackgroundColor3 = Color3.new(1, 1, 1)               -- white: a UIGradient multiplies the background colour
	inner.ZIndex = 3
	inner.Parent = ring
	Instance.new("UICorner", inner).CornerRadius = UDim.new(1, 0)
	local ig = Instance.new("UIGradient", inner)
	ig.Rotation = 90
	ig.Color = ColorSequence.new(Color3.fromRGB(124, 92, 190), Color3.fromRGB(66, 44, 116))
	local is_ = Instance.new("UIStroke", inner)
	is_.Thickness, is_.Color, is_.Transparency = 1.5, Color3.new(0, 0, 0), 0.4
	local cap = Instance.new("Frame")                     -- the keycap
	cap.AnchorPoint = Vector2.one * 0.5
	cap.Position = UDim2.fromScale(0.5, 0.47)
	cap.Size = UDim2.fromScale(0.44, 0.44)
	cap.BackgroundColor3 = Color3.fromRGB(250, 248, 240)
	cap.ZIndex = 5
	cap.Parent = ring
	Instance.new("UICorner", cap).CornerRadius = UDim.new(0.22, 0)
	local cg = Instance.new("UIGradient", cap)
	cg.Rotation = 90
	cg.Color = ColorSequence.new(Color3.new(1, 1, 1), Color3.fromRGB(214, 206, 226))
	local cs = Instance.new("UIStroke", cap)
	cs.Thickness, cs.Color = 2.5, Color3.fromRGB(30, 20, 50)
	local capShadow = cap:Clone()                         -- the key's lower edge (gives it depth)
	capShadow:ClearAllChildren()
	Instance.new("UICorner", capShadow).CornerRadius = UDim.new(0.22, 0)
	capShadow.BackgroundColor3 = Color3.fromRGB(30, 20, 50)
	capShadow.Position = UDim2.fromScale(0.5, 0.51)
	capShadow.ZIndex = 4
	capShadow.Parent = ring
	local key = FX.label(cap, UDim2.fromScale(0.8, 0.8))
	key.Position = UDim2.fromScale(0.1, 0.1)
	key.Font = Enum.Font.GothamBlack
	key.TextColor3 = Color3.fromRGB(36, 24, 60)
	key.TextStrokeTransparency = 1
	key.ZIndex = 6
	key.Text = (keyText())
	local pct = FX.label(ring, UDim2.fromScale(0.5, 0.14))  -- "64%" under the key while someone holds
	pct.AnchorPoint = Vector2.new(0.5, 0)
	pct.Position = UDim2.fromScale(0.5, 0.71)
	pct.Font = Enum.Font.GothamBlack
	pct.TextColor3 = FX.gold
	pct.ZIndex = 6
	local pill = Instance.new("Frame")                    -- "HOLD E TO CLAIM" pill under the badge
	pill.AnchorPoint = Vector2.new(0.5, 0)
	pill.Position = UDim2.new(0.5, 0, 0, 140)
	pill.Size = UDim2.fromOffset(150, 40)
	pill.BackgroundColor3 = FX.plum
	pill.BackgroundTransparency = 0.08
	pill.Parent = box
	Instance.new("UICorner", pill).CornerRadius = UDim.new(1, 0)
	local ps = Instance.new("UIStroke", pill)
	ps.Thickness, ps.Color = 2, FX.gold
	local line1 = FX.label(pill, UDim2.new(1, -16, 0.56, 0))
	line1.Position = UDim2.new(0, 8, 0.06, 0)
	line1.Font = Enum.Font.GothamBlack
	line1.TextColor3 = FX.cream
	line1.TextStrokeTransparency = 1
	local line2 = FX.label(pill, UDim2.new(1, -16, 0.3, 0))
	line2.Position = UDim2.new(0, 8, 0.6, 0)
	line2.Font = Enum.Font.GothamBold
	line2.TextColor3 = FX.gold
	line2.TextStrokeTransparency = 1
	line2.Text = "BIG EGG  ·  x25 LUCK"
	-- touch / click: hold the badge = hold the prompt (keyboard E and gamepad still work as before)
	local hit = Instance.new("TextButton")
	hit.BackgroundTransparency = 1
	hit.Text = ""
	hit.Size = UDim2.fromScale(1, 1)
	hit.ZIndex = 10
	hit.Parent = box
	local holding = false
	hit.InputBegan:Connect(function(io)
		if io.UserInputType == Enum.UserInputType.Touch or io.UserInputType == Enum.UserInputType.MouseButton1 then
			local pp = claimPrompt()
			if pp and pp.Enabled then
				holding = true
				pcall(pp.InputHoldBegin, pp)
			end
		end
	end)
	-- release anywhere ends the hold (a finger / mouse let go outside the badge must not leave the prompt held)
	local function release(io)
		if holding and (io.UserInputType == Enum.UserInputType.Touch or io.UserInputType == Enum.UserInputType.MouseButton1) then
			holding = false
			local pp = claimPrompt()
			if pp then pcall(pp.InputHoldEnd, pp) end
		end
	end
	hit.InputEnded:Connect(release)
	table.insert(s.connections, UIS.InputEnded:Connect(release))
	bb.Destroying:Connect(function()
		if holding then
			holding = false
			local pp = claimPrompt()
			if pp then pcall(pp.InputHoldEnd, pp) end
		end
	end)
	local t0 = os.clock()
	local b = { gui = bb, scale = sc, gR = gR, gL = gL, dR = dR, dL = dL, glow = glow, key = key, cap = cap, pct = pct,
		line1 = line1, line2 = line2, pill = pill, pillStroke = ps, ring = ring }
	run(s, function(now)                                  -- idle "breathing" glow + live key label
		if not bb.Parent then return false end
		local t = now - t0
		glow.Size = UDim2.fromScale(1.1 + 0.05 * math.sin(t * 3), 1.1 + 0.05 * math.sin(t * 3))
		glow.BackgroundTransparency = (b.p or 0) > 0 and 0.5 or (0.68 + 0.08 * math.sin(t * 3))
		local k, l = keyText()
		key.Text = k                                       -- the key follows the last device used (E / TAP / gamepad)
		if (b.p or 0) == 0 and not b.busy then
			line1.Text = l
		end
	end)
	return b
end

local function setRing(b, p, color)
	local a = p * 360
	b.gR.Rotation = math.clamp(a, 0, 180)                  -- right half fills 12 -> 6 o'clock
	b.gL.Rotation = 180 + math.clamp(a - 180, 0, 180)      -- left half fills 6 -> 12 o'clock
	local c = color and ColorSequence.new(color) or ColorSequence.new(FX.gold, FX.cream)
	b.gR.Color, b.gL.Color = c, c
	local hidden = p <= 0
	b.dR.Visible, b.dL.Visible = not hidden, not hidden
end

function VFX.PlayClaimProgress(egg, p, character)
	local s = state()
	local root = FX.root(egg)
	if not root then return end
	if not s.badge or not s.badge.gui.Parent or s.badge.gui.Adornee ~= root then
		if s.badge then s.badge.gui:Destroy() end
		s.badge = buildBadge(s, root)
		own(s, s.badge.gui)
		s.ring = s.badge.gui
	end
	local b = s.badge
	p = math.clamp(p, 0, 1)
	local claimant = if p > 0 then character else nil
	if s.claimant ~= claimant then
		stopClaim(s)
		s.claimant = claimant
		if claimant then s.claimTrack = characterClip(claimant,"Claim",true,.22) end
	end
	local was = b.p or 0
	b.p = p
	setRing(b, p)
	if p > 0 then
		local me = character and character == Players.LocalPlayer.Character
		local who = character and Players:GetPlayerFromCharacter(character)
		b.pct.Text = math.floor(p * 100) .. "%"
		b.line1.Text = me and "CLAIMING..." or ((who and who.DisplayName:upper() or "SOMEONE") .. " IS CLAIMING!")
		b.line1.TextColor3 = me and FX.cream or FX.coral
		b.pillStroke.Color = me and FX.teal or FX.coral
		if was == 0 then                                     -- press: the key goes down a little
			FX.tween(b.cap, 0.08, { Position = UDim2.fromScale(0.5, 0.5) })
			b.scale.Scale = 1.05
			FX.tween(b.scale, 0.2, { Scale = 1 })
		end
		if p >= 1 then
			b.pct.Text = "100%"
		end
	else
		b.pct.Text = ""
		b.line1.TextColor3 = FX.cream
		b.pillStroke.Color = FX.gold
		if was > 0 then
			FX.tween(b.cap, 0.12, { Position = UDim2.fromScale(0.5, 0.47) })
		end
	end
end

function VFX.PlayClaimBreak(egg)
	local s = state()
	local b = s.badge
	if not b or b.gui.Adornee ~= FX.root(egg) then return end
	stopClaim(s)
	b.p = 0
	setRing(b, 1, FX.coral)                                  -- flash the whole ring red, shake, then reset
	b.pct.Text = ""
	b.line1.Text = "INTERRUPTED!"
	b.busy = true
	b.line1.TextColor3 = FX.coral
	b.pillStroke.Color = FX.coral
	FX.tween(b.cap, 0.12, { Position = UDim2.fromScale(0.5, 0.47) })
	local ring = b.ring
	task.spawn(function()
		for i = 1, 6 do
			ring.Position = UDim2.new(0.5, (i % 2 == 0 and 5 or -5) * (1 - i / 7), 0, 0)
			task.wait(0.04)
		end
		ring.Position = UDim2.fromScale(0.5, 0)
		task.wait(0.4)
		b.busy = false
		if b.gui.Parent and (b.p or 0) == 0 then
			setRing(b, 0)
			b.pillStroke.Color = FX.gold
			b.line1.TextColor3 = FX.cream
		end
	end)
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
