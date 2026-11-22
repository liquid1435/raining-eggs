-- Raining Eggs: client
-- falling eggs + shadow, catch, effects, sounds, HUD, hatch popup, index, rebirth, storm, pen pets animation
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local CS = game:GetService("CollectionService")
local Debris = game:GetService("Debris")
local SoundService = game:GetService("SoundService")
local Lighting = game:GetService("Lighting")
local C = require(RS:WaitForChild("Config"))

local plr = Players.LocalPlayer
local Remotes = RS:WaitForChild("Remotes")
local EggSpawn = Remotes:WaitForChild("EggSpawn")
local EggGone = Remotes:WaitForChild("EggGone")
local Catch = Remotes:WaitForChild("Catch")
local Hatch = Remotes:WaitForChild("Hatch")
local Notice = Remotes:WaitForChild("Notice")
local Action = Remotes:WaitForChild("Action")

local WHITE = Color3.new(1, 1, 1)
local INK = Color3.fromRGB(20, 24, 48)
local YELLOW = Color3.fromRGB(255, 222, 60)
local GREEN = Color3.fromRGB(80, 210, 90)
local RED = Color3.fromRGB(240, 66, 66)
local PURPLE = Color3.fromRGB(170, 100, 255)

local function make(class, props, parent)
	local o: any = Instance.new(class)
	for k, v in pairs(props) do
		o[k] = v
	end
	o.Parent = parent
	return o
end

local UI = {} -- UI kit functions shared with the UIMenus module (filled further down)

local function attr(name, default)
	local v = plr:GetAttribute(name)
	if v == nil then
		return default
	end
	return v
end

-- ------------------------------------------------------------ sounds (built-in Roblox files)
local SND = {
	catch = "action_jump.mp3", rare = "action_get_up.mp3",
	yuck = "ouch.ogg", click = "volume_slider.ogg", thunder = "impact_explosion_03.mp3",
}
local sounds = {}
for name, file in pairs(SND) do
	sounds[name] = make("Sound", { Name = "RE_" .. name, SoundId = "rbxasset://sounds/" .. file, Volume = 0.5 }, SoundService)
end
local function play(name, pitch, volume)
	local s = sounds[name]
	s.PlaybackSpeed = pitch or 1
	s.Volume = volume or 0.5
	SoundService:PlayLocalSound(s)
end

-- new synth sounds: all in ONE file (rainingeggs_sfx.ogg). Paste its asset id below after uploading it.
local SFX_ID = "rbxassetid://129727656294904"
local SFX = require(RS:WaitForChild("Sfx"))
local SFX_FALLBACK = { -- used while SFX_ID is 0
	ui_click = { "click", 1.2 }, catch = { "catch", 1.2 }, coin = { "click", 0.9 }, speed_gain = { "click", 1.7 },
	tread_on = { "click", 1.3 }, egg_pop = { "click", 0.7 }, reveal_rare = { "rare", 1 }, reveal_legend = { "rare", 1.15 },
	yuck = { "yuck", 1 }, fanfare = { "rare", 1.1 },
}
-- one loaded copy of the sound sheet; every play clones it, jumps to the sound and stops after its length
local sfxBase = make("Sound", { Name = "SFX_Sheet", SoundId = SFX_ID, Volume = 0 }, SoundService)
if SFX_ID ~= "rbxassetid://0" then
	task.spawn(function()
		pcall(function()
			game:GetService("ContentProvider"):PreloadAsync({ sfxBase })
		end)
	end)
end
local function sfx(name, volume, pitch, parent)
	local r = SFX[name]
	if not r then
		return nil
	end
	if SFX_ID == "rbxassetid://0" or not sfxBase.IsLoaded then
		local f = SFX_FALLBACK[name]
		if f and not parent then
			play(f[1], f[2] * (pitch or 1), volume)
		end
		return nil
	end
	local s = sfxBase:Clone()
	s.Name = "SFX_" .. name
	s.Volume = volume or 0.5
	s.PlaybackSpeed = pitch or 1
	if parent then
		s.RollOffMinDistance = 8
		s.RollOffMaxDistance = 80
	end
	s.Parent = parent or SoundService
	s.TimePosition = r[1]
	s:Play()
	local life = r[2] / (pitch or 1)
	task.delay(life, function()
		s:Stop()
		s:Destroy()
	end)
	return s
end
local PET_SFX = { b = "pet_chirp", o = "pet_blub" }
local function petSound(kind, parent, volume)
	sfx(PET_SFX[kind] or "pet_yip", volume or 0.45, 0.9 + math.random() * 0.25, parent)
end

-- ------------------------------------------------------------ small effect parts
local fx = make("Folder", { Name = "EggFX" }, workspace)

local function fxPart(size, cf, col, shape)
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = false
	p.CanTouch = false
	p.CanQuery = false
	p.CastShadow = false
	p.Material = Enum.Material.SmoothPlastic
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Size = size
	p.CFrame = cf
	p.Color = col
	if shape then
		p.Shape = shape
	end
	p.Parent = fx
	return p
end

local function fade(p, time, goal)
	goal.Transparency = 1
	TweenService:Create(p, TweenInfo.new(time, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), goal):Play()
	Debris:AddItem(p, time + 0.1)
end

-- ------------------------------------------------------------ GUI helpers
local gui = make("ScreenGui", {
	Name = "RainingEggsHUD", ResetOnSpawn = false, IgnoreGuiInset = true, ZIndexBehavior = Enum.ZIndexBehavior.Sibling,
}, plr:WaitForChild("PlayerGui"))

local function stroke(obj, thick, col)
	return make("UIStroke", { Thickness = thick, Color = col or Color3.new(0, 0, 0) }, obj)
end

local function corner(obj, scale)
	return make("UICorner", { CornerRadius = UDim.new(scale, 0) }, obj)
end

local function gradient(obj)
	return make("UIGradient", { Rotation = 90, Color = ColorSequence.new(WHITE, Color3.fromRGB(185, 185, 195)) }, obj)
end

local function darker(col, k)
	return Color3.new(col.R * k, col.G * k, col.B * k)
end

local function text(parent, size, pos, maxSize, str)
	local t = make("TextLabel", {
		BackgroundTransparency = 1, Size = size, Position = pos, Font = Enum.Font.FredokaOne,
		TextColor3 = WHITE, TextScaled = true, Text = str or "",
	}, parent)
	stroke(t, 2.5)
	make("UITextSizeConstraint", { MaxTextSize = maxSize or 30 }, t)
	return t
end

local function box(parent, size, pos, col, round)
	local f = make("Frame", { Size = size, Position = pos, BackgroundColor3 = col, BorderSizePixel = 0 }, parent)
	corner(f, round or 0.25)
	return f
end

-- ------------------------------------------------------------ UI kit (same look as the Figma design)
local BLACK = Color3.fromRGB(26, 20, 32)
local NAVY = Color3.fromRGB(70, 100, 230)
-- ui_icons.png (E:\rainingeggs\ui): 4 x 3 icons of 128 px. Put the uploaded image id here.
local ICON_SHEET = "rbxassetid://126375057101691"
local ICON = { coin = 0, bolt = 1, book = 2, rebirth = 3, storm = 4, basket = 5, clover = 6, sparkle = 7, x = 8, alert = 9, flame = 10, arrow = 11 }
-- ui_icons2.png (E:/rainingeggs/ui, sticker style, 6 x 4 icons of 128 px). Upload it and put the id here; while it is "" the old sheet is used.
local ICON_SHEET2 = "rbxassetid://124204954898778" -- ui_icons5.png (sticker icons, green cash bill, new clover, 6 x 4)
local ICON2 = {
	coin = 0, bolt = 1, book = 2, rebirth = 3, storm = 4, basket = 5, clover = 6, sparkle = 7, x = 8, alert = 9, flame = 10, arrow = 11,
	egg = 12, gift = 13, trophy = 14, upgrade = 15, paw = 16, gem = 17, cart = 18, lock = 19, star = 20, crown = 21, check = 22, clock = 23,
}
local OLD_FALLBACK = { egg = "sparkle", gift = "sparkle", trophy = "flame", upgrade = "arrow", paw = "basket", gem = "sparkle", cart = "basket", lock = "x", star = "sparkle", crown = "flame", check = "arrow", clock = "storm" }
local function iconRect(name)
	if ICON_SHEET2 ~= "" then
		local n = ICON2[name] or 7
		return ICON_SHEET2, Vector2.new((n % 6) * 128 + 2, math.floor(n / 6) * 128 + 2), Vector2.new(124, 124)
	end
	local n = ICON[name] or ICON[OLD_FALLBACK[name] or "sparkle"]
	return ICON_SHEET, Vector2.new((n % 4) * 128 + 4, math.floor(n / 4) * 128 + 4), Vector2.new(120, 120)
end

local wobbly = {} -- icons that gently rock (makes the HUD feel alive)
local function icon(parent, name, size, pos, anchor)
	local sheet, off, sz = iconRect(name)
	local i = make("ImageLabel", {
		BackgroundTransparency = 1, Size = size, Position = pos or UDim2.new(), AnchorPoint = anchor or Vector2.new(0, 0), ZIndex = 2,
		Image = sheet, ImageRectSize = sz, ImageRectOffset = off, -- small inset: no edge bleed from the next icon
		ScaleType = Enum.ScaleType.Fit,
	}, parent)
	make("UIAspectRatioConstraint", { AspectRatio = 1, DominantAxis = Enum.DominantAxis.Height }, i)
	if name ~= "storm" and name ~= "bolt" then -- the storm cloud and the speed bolt stay still
		wobbly[i] = math.random() * 6
	end
	return i
end

local function grad(obj, top, bottom)
	return make("UIGradient", { Rotation = 90, Color = ColorSequence.new(top, bottom) }, obj)
end

local function faceSeq(col)
	local function up(v)
		return v + (1 - v) * 0.4
	end
	return ColorSequence.new(Color3.new(up(col.R), up(col.G), up(col.B)), darker(col, 0.85))
end

-- glossy 3D face: light-to-dark gradient, thick black outline, soft shine on the top half
-- block corners: the new look is square-ish (Roblox brick style); round >= 1 keeps true circles / pills
local function blockCorner(obj, round)
	if (round or 0.25) >= 1 then
		return corner(obj, 1)
	end
	return make("UICorner", { CornerRadius = UDim.new(0, 12) }, obj)
end

local function face(obj, col, round)
	obj.BackgroundColor3 = WHITE
	obj.BorderSizePixel = 0
	blockCorner(obj, round)
	local g = make("UIGradient", { Rotation = 90, Color = faceSeq(col) }, obj)
	make("UIStroke", { Thickness = 3, Color = BLACK, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, obj)
	local shine = make("Frame", { -- thin glossy line along the top edge
		Name = "Shine", BackgroundColor3 = WHITE, BackgroundTransparency = 0.55, BorderSizePixel = 0,
		Size = UDim2.new(1, -8, 0.13, 0), Position = UDim2.new(0, 4, 0.07, 0),
	}, obj)
	blockCorner(shine, round)
	return g
end

local function tint(obj, col)
	obj:FindFirstChildOfClass("UIGradient").Color = faceSeq(col)
end

-- glossy diagonal stripes over a face (the "hatched" look of UI v3), clipped by a CanvasGroup
-- glossy diagonal stripes over a face (the "hatched" look of UI v3).
-- No CanvasGroups (Roblox stops drawing them when there are many): white frames whose UIGradient
-- transparency has hard steps = 4 diagonal stripes per frame; wide things get several frames side by side.
local stripes
do
local function stripeSeq(op)
	local k = { NumberSequenceKeypoint.new(0, 1) }
	for i = 0, 3 do
		local s0 = 0.06 + i * 0.24
		table.insert(k, NumberSequenceKeypoint.new(s0, 1))
		table.insert(k, NumberSequenceKeypoint.new(s0 + 0.002, op))
		table.insert(k, NumberSequenceKeypoint.new(s0 + 0.1, op))
		table.insert(k, NumberSequenceKeypoint.new(s0 + 0.102, 1))
	end
	table.insert(k, NumberSequenceKeypoint.new(1, 1))
	return NumberSequence.new(k)
end
local _ = stripeSeq
-- one continuous set of equal slanted bars (v134): the old version put several gradient frames side by side,
-- each restarting the pattern, so the stripes did not line up. Now: a clipping frame + thin rotated white bars
-- with the same width and spacing (in pixels, from the height), rebuilt when the size changes.
function stripes(parent, radius, transp, z, segs)
	local op = transp or 0.8
	local round = radius and (radius.Scale or 0) >= 1
	local insetX = round and 0.12 or 0.03
	local holder = make("Frame", {
		Name = "Stripes", BackgroundTransparency = 1, ClipsDescendants = true, ZIndex = z or 2,
		Size = UDim2.fromScale(1 - 2 * insetX, 0.84), Position = UDim2.fromScale(insetX, 0.08),
	}, parent)
	local lastW, lastH = -1, -1
	local function build()
		local w, h = holder.AbsoluteSize.X, holder.AbsoluteSize.Y
		if w < 2 or h < 2 or (math.abs(w - lastW) < 1 and math.abs(h - lastH) < 1) then
			return
		end
		lastW, lastH = w, h
		holder:ClearAllChildren()
		local H = h / 0.84
		local barW = math.max(3, H * 0.2)
		local gap = math.max(8, H * 0.55)
		local n = math.ceil((w + h) / gap) + 2
		for i = 0, n do
			make("Frame", {
				AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0, -h * 0.5 + i * gap, 0.5, 0),
				Size = UDim2.new(0, barW, 0, h * 2.2), Rotation = 35, BackgroundColor3 = WHITE,
				BackgroundTransparency = op, BorderSizePixel = 0, ZIndex = z or 2,
			}, holder)
		end
	end
	holder:GetPropertyChangedSignal("AbsoluteSize"):Connect(build)
	task.defer(build)
	return holder
end
end
-- a 3D face sitting on a darker lip (the pushed-out look of the Figma pills)
local function lip(parent, col, size, pos, anchor, round)
	local holder = make("Frame", { BackgroundTransparency = 1, Size = size, Position = pos, AnchorPoint = anchor or Vector2.new(0, 0) }, parent)
	local under = make("Frame", {
		Name = "Lip", BackgroundColor3 = darker(col, 0.45), BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), Position = UDim2.fromScale(0, 0.1), ZIndex = 0,
	}, holder)
	blockCorner(under, round)
	make("UIStroke", { Thickness = 3, Color = BLACK, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, under)
	local top = make("Frame", { Name = "Face", Size = UDim2.fromScale(1, 1) }, holder)
	local g = face(top, col, round)
	do
		stripes(top, (round or 0.25) >= 1 and UDim.new(1, 0) or UDim.new(0, 12), 0.72, top.ZIndex, 3)
	end
	return holder, top, g
end

local function title(parent, size, pos, maxSize, str)
	local t = text(parent, size, pos, maxSize, str)
	t.Font = Enum.Font.LuckiestGuy
	t:FindFirstChildOfClass("UIStroke").Thickness = 3
	return t
end

-- small dark chip: icon + coloured text
local function chip(parent, iconName, size, pos, col)
	local c = make("Frame", { BackgroundColor3 = BLACK, BackgroundTransparency = 0.45, BorderSizePixel = 0, Size = size, Position = pos or UDim2.new() }, parent)
	corner(c, 1)
	local x = 0.08
	if iconName then
		icon(c, iconName, UDim2.fromScale(0.8, 0.8), UDim2.fromScale(0.03, 0.1))
		x = 0.3
	end
	local t = text(c, UDim2.fromScale(0.95 - x, 0.78), UDim2.fromScale(x, 0.11), 22)
	t.TextColor3 = col or WHITE
	t.TextXAlignment = Enum.TextXAlignment.Left
	return t, c
end

-- button click: a separate sound (ElevenLabs, E:/rainingeggs/audio/click). Upload the chosen one and put its id here; "" = silent.
local CLICK_ID = "rbxassetid://72144564975873"
local clickSound = make("Sound", { Name = "RE_Click", SoundId = CLICK_ID, Volume = 0.6 }, SoundService)
local BUY_ID = "rbxassetid://105683168249633" -- SUNET CUMPARARE POP.mp3 (buy_29_pop, louder)
local ZONE_ID = "rbxassetid://84026827045347" -- zona_5_magie.mp3
local buySound = make("Sound", { Name = "RE_Buy", SoundId = BUY_ID, Volume = 2.5 }, SoundService) -- pop: loud (user)
local zoneSound = make("Sound", { Name = "RE_Zone", SoundId = ZONE_ID, Volume = 0.8 }, SoundService)
local function playBuy()
	if BUY_ID ~= "" then
		SoundService:PlayLocalSound(buySound)
	else
		sfx("coin", 0.6)
	end
end
local function playZone()
	if ZONE_ID ~= "" then
		SoundService:PlayLocalSound(zoneSound)
	else
		sfx("fanfare", 0.7)
	end
end

local function playClick()
	if CLICK_ID ~= "" then
		SoundService:PlayLocalSound(clickSound)
	end
end

local function pressable(b)
	local sc = make("UIScale", {}, b)
	b.MouseButton1Down:Connect(function()
		TweenService:Create(sc, TweenInfo.new(0.08), { Scale = 0.94 }):Play()
	end)
	local function up()
		TweenService:Create(sc, TweenInfo.new(0.08), { Scale = 1 }):Play()
	end
	b.MouseButton1Up:Connect(up)
	b.MouseLeave:Connect(up)
	b.MouseEnter:Connect(function()
		TweenService:Create(sc, TweenInfo.new(0.08), { Scale = 1.06 }):Play()
	end)
	b.Activated:Connect(function()
		playClick()
	end)
end

local function button(parent, size, pos, col, str, maxSize)
	local b = make("TextButton", {
		Size = size, Position = pos, AutoButtonColor = false,
		Font = Enum.Font.FredokaOne, TextColor3 = WHITE, TextScaled = true, Text = str,
	}, parent)
	face(b, col, 0.25)
	make("UIStroke", { Thickness = 2.5, Color = BLACK, ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual }, b)
	make("UIPadding", { PaddingTop = UDim.new(0.12, 0), PaddingBottom = UDim.new(0.16, 0), PaddingLeft = UDim.new(0.08, 0), PaddingRight = UDim.new(0.08, 0) }, b)
	make("UITextSizeConstraint", { MaxTextSize = maxSize or 30 }, b)
	pressable(b)
	return b
end

-- square menu button: icon on top, small label under it
local function iconButton(parent, col, iconName, label, pos)
	local b = make("TextButton", { Size = UDim2.fromScale(1, 0.47), Position = pos, AutoButtonColor = false, Text = "" }, parent)
	face(b, col, 0.25)
	icon(b, iconName, UDim2.fromScale(0.66, 0.66), UDim2.fromScale(0.5, 0.04), Vector2.new(0.5, 0))
	local l = title(b, UDim2.fromScale(0.94, 0.26), UDim2.fromScale(0.03, 0.69), 18, label)
	l.ZIndex = 2
	pressable(b)
	return b
end

-- a pet shown in 3D inside the UI
local function petView(parent, pet, size, pos)
	local vp = make("ViewportFrame", {
		Size = size, Position = pos, BackgroundTransparency = 1, Ambient = Color3.fromRGB(190, 190, 200),
		LightColor = WHITE, LightDirection = Vector3.new(0.4, -1, 1),
	}, parent)
	local cam = make("Camera", { FieldOfView = 40 }, vp)
	vp.CurrentCamera = cam
	local model = C.buildPet(pet, 1, true)
	model.Parent = vp
	-- v165 (user: the pets did not fit in the cards): the camera frames the whole pet, whatever its size
	local bcf, bsize = model:GetBoundingBox()
	local r = bsize.Magnitude / 2
	local dist = r / math.sin(math.rad(cam.FieldOfView / 2)) * 0.92
	local dir = Vector3.new(-3.2, 2.1, -8.6).Unit
	cam.CFrame = CFrame.lookAt(bcf.Position + dir * dist, bcf.Position)
	return vp, model
end

-- ------------------------------------------------------------ HUD: left (cash, speed, income, luck)
local stack = make("Frame", {
	BackgroundTransparency = 1, AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.fromScale(0.016, 0.47), Size = UDim2.fromScale(0.22, 0.34),
}, gui)
make("UIAspectRatioConstraint", { AspectRatio = 1.45 }, stack)

local function pill(y, iconName, w, textX, col)
	local holder, top = lip(stack, col or NAVY, UDim2.fromScale(w, 0.3), UDim2.fromScale(0.04, y), nil, 1)
	top:FindFirstChild("Shine").BackgroundTransparency = 0.9
	icon(holder, iconName, UDim2.fromScale(1.25, 1.25), UDim2.fromScale(-0.05, 0.5), Vector2.new(0, 0.5))
	local v = text(top, UDim2.fromScale(0.95 - textX, 0.72), UDim2.fromScale(textX, 0.12), 34)
	v.TextXAlignment = Enum.TextXAlignment.Left
	v.ZIndex = 2
	return v, holder
end
local cashLabel, cashPill = pill(0, "coin", 0.86, 0.3, Color3.fromRGB(40, 215, 80))
local speedLabel = pill(0.37, "bolt", 0.72, 0.37, Color3.fromRGB(20, 160, 255))
local incomeLabel = chip(stack, "coin", UDim2.fromScale(0.52, 0.17), UDim2.fromScale(0, 0.76), YELLOW)
local luckLabel = chip(stack, "clover", UDim2.fromScale(0.42, 0.17), UDim2.fromScale(0.56, 0.76), Color3.fromRGB(156, 245, 154))
local cashScale = make("UIScale", {}, cashPill)

-- ------------------------------------------------------------ HUD: top centre (storm banner + next zone bar)
local top = make("Frame", {
	BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromScale(0.5, 0.02), Size = UDim2.fromScale(0.36, 0.2),
}, gui)
make("UIAspectRatioConstraint", { AspectRatio = 4.2 }, top)
local stormBanner, stormFace, stormGrad = lip(top, Color3.fromRGB(140, 90, 240), UDim2.fromScale(0.84, 0.5), UDim2.fromScale(0.08, 0), nil, 0.3)
local STORM_SEQ = stormGrad.Color
icon(stormBanner, "storm", UDim2.fromScale(1.2, 1.2), UDim2.fromScale(0, 0.45), Vector2.new(0, 0.5))
local stormLabel = title(stormFace, UDim2.fromScale(0.5, 0.66), UDim2.fromScale(0.17, 0.14), 30, "EGG STORM")
stormLabel.TextColor3 = YELLOW
stormLabel.TextXAlignment = Enum.TextXAlignment.Left
stormLabel.ZIndex = 2
local timerPill = make("Frame", {
	BackgroundColor3 = WHITE, BorderSizePixel = 0, Size = UDim2.fromScale(0.27, 0.7), Position = UDim2.fromScale(0.7, 0.13), ZIndex = 2,
}, stormFace)
corner(timerPill, 1)
make("UIStroke", { Thickness = 2.5, Color = BLACK, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, timerPill)
local stormTimer = make("TextLabel", {
	BackgroundTransparency = 1, Size = UDim2.fromScale(0.86, 0.8), Position = UDim2.fromScale(0.07, 0.1), ZIndex = 2,
	Font = Enum.Font.FredokaOne, TextScaled = true, TextColor3 = Color3.fromRGB(38, 42, 120), Text = "",
}, timerPill)
stormBanner.Visible = false

local barBg = box(top, UDim2.fromScale(0.78, 0.28), UDim2.fromScale(0.11, 0.68), Color3.fromRGB(29, 23, 51), 0.2)
barBg.BackgroundTransparency = 0
make("UIStroke", { Thickness = 3, Color = BLACK, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, barBg)
local barFill = box(barBg, UDim2.fromScale(0, 1), UDim2.fromScale(0, 0), WHITE, 0.2)
grad(barFill, Color3.fromRGB(160, 245, 140), Color3.fromRGB(60, 180, 70))
barFill.ZIndex = 1
-- the green fill is never thinner than it is tall, so its round ends stay inside the bar
local fillMin = make("UISizeConstraint", {}, barFill)
local function fitFill()
	local a = barBg.AbsoluteSize
	if a then
		fillMin.MinSize = Vector2.new(a.Y, 0)
	end
end
barBg:GetPropertyChangedSignal("AbsoluteSize"):Connect(fitFill)
fitFill()
local barText = text(barBg, UDim2.fromScale(0.96, 0.8), UDim2.fromScale(0.02, 0.1), 20)
-- no storm: the NEXT bar moves up into the storm banner's place; storm: banner on top, NEXT bar under it
local BAR_LOW, BAR_HIGH = UDim2.fromScale(0.11, 0.68), UDim2.fromScale(0.11, 0.08)
barBg.Position = BAR_HIGH
barBg.Visible = false -- user: no NEXT bar; the next gate shows "$cash / $price" instead
stormBanner:GetPropertyChangedSignal("Visible"):Connect(function()
	TweenService:Create(barBg, TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Position = stormBanner.Visible and BAR_LOW or BAR_HIGH }):Play()
end)

-- v150: weekly event banner (in the place of the old NEXT bar: under the storm banner, or on top when there is no storm)
-- + a small chip when Roblox friends play on the same server
do
	local EV_COL = { luck = Color3.fromRGB(60, 200, 90), gold = Color3.fromRGB(255, 190, 40), cash = Color3.fromRGB(40, 190, 120),
		rainbow = Color3.fromRGB(230, 80, 200), storm = Color3.fromRGB(140, 90, 240) }
	local holder, face, evGrad = lip(top, Color3.fromRGB(255, 190, 40), UDim2.fromScale(0.78, 0.3), BAR_HIGH, nil, 0.3)
	local nameT = make("TextLabel", {
		BackgroundTransparency = 1, Size = UDim2.fromScale(0.5, 0.86), Position = UDim2.fromScale(0.04, 0.07), ZIndex = 3,
		Font = Enum.Font.LuckiestGuy, TextScaled = true, TextColor3 = WHITE, Text = "", TextXAlignment = Enum.TextXAlignment.Left,
	}, face)
	make("UIStroke", { Thickness = 2.5, Color = BLACK }, nameT)
	local infoT = make("TextLabel", {
		BackgroundTransparency = 1, Size = UDim2.fromScale(0.42, 0.7), Position = UDim2.fromScale(0.55, 0.15), ZIndex = 3,
		Font = Enum.Font.FredokaOne, TextScaled = true, TextColor3 = WHITE, Text = "", TextXAlignment = Enum.TextXAlignment.Right,
	}, face)
	make("UIStroke", { Thickness = 2, Color = BLACK }, infoT)
	local friendT = make("TextLabel", {
		BackgroundTransparency = 1, Size = UDim2.fromScale(0.6, 0.2), Position = UDim2.fromScale(0.2, 1.02), ZIndex = 3, Visible = false,
		Font = Enum.Font.FredokaOne, TextScaled = true, TextColor3 = Color3.fromRGB(120, 230, 255), Text = "",
	}, top)
	make("UIStroke", { Thickness = 2, Color = BLACK }, friendT)
	local showDesc = false
	stormBanner:GetPropertyChangedSignal("Visible"):Connect(function()
		TweenService:Create(holder, TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Position = stormBanner.Visible and BAR_LOW or BAR_HIGH }):Play()
	end)
	task.spawn(function()
		while true do
			local key, name = workspace:GetAttribute("EventKey"), workspace:GetAttribute("EventName")
			holder.Visible = key ~= nil
			if key then
				local left = math.max(0, (workspace:GetAttribute("EventEnd") or 0) - workspace:GetServerTimeNow())
				local dd, hh, mm = math.floor(left / 86400), math.floor(left % 86400 / 3600), math.floor(left % 3600 / 60)
				nameT.Text = name
				showDesc = not showDesc
				infoT.Text = showDesc and (workspace:GetAttribute("EventDesc") or "") or ("ends in " .. (dd > 0 and (dd .. "d " .. hh .. "h") or (hh .. "h " .. mm .. "m")))
				local col = EV_COL[key] or YELLOW
				if evGrad and evGrad:IsA("UIGradient") then
					evGrad.Color = faceSeq(col)
				end
			end
			local n = plr:GetAttribute("Friends") or 0
			friendT.Visible = n > 0
			friendT.Text = n .. (n == 1 and " FRIEND" or " FRIENDS") .. " HERE: +" .. math.floor(C.FRIEND_BONUS * n * 100 + 0.5) .. "% CASH"
			task.wait(4)
		end
	end)
end
barText.RichText = true
barText.ZIndex = 3

-- ------------------------------------------------------------ HUD: right side (combo + menu buttons)
local combo = make("Frame", {
	BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.66, 0.3), Size = UDim2.fromScale(0.2, 0.3),
	Rotation = -7, Visible = false,
}, gui)
make("UIAspectRatioConstraint", { AspectRatio = 1.25 }, combo)
local comboScale = make("UIScale", {}, combo)
icon(combo, "flame", UDim2.fromScale(0.24, 0.24), UDim2.fromScale(0.13, 0.02))
local comboHead = title(combo, UDim2.fromScale(0.56, 0.2), UDim2.fromScale(0.33, 0.04), 30, "COMBO")
comboHead.TextColor3 = YELLOW
comboHead.TextXAlignment = Enum.TextXAlignment.Left
local comboText = title(combo, UDim2.fromScale(1, 0.46), UDim2.fromScale(0, 0.21), 90)
grad(comboText, Color3.fromRGB(255, 247, 176), Color3.fromRGB(255, 110, 30))
comboText:FindFirstChildOfClass("UIStroke").Thickness = 4
local comboSub = title(combo, UDim2.fromScale(0.62, 0.15), UDim2.fromScale(0.3, 0.66), 30, "")
comboSub.TextColor3 = Color3.fromRGB(140, 245, 120)
comboSub.Rotation = -8
comboSub.TextXAlignment = Enum.TextXAlignment.Left
icon(combo, "clover", UDim2.fromScale(0.16, 0.16), UDim2.fromScale(0.13, 0.66))
local comboBarBg = box(combo, UDim2.fromScale(0.6, 0.06), UDim2.fromScale(0.2, 0.89), BLACK, 1)
local comboBar = box(comboBarBg, UDim2.fromScale(1, 1), UDim2.fromScale(0, 0), Color3.fromRGB(255, 150, 40), 1)
local comboUntil = 0

local menu = make("Frame", {
	BackgroundTransparency = 1, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.fromScale(0.984, 0.48), Size = UDim2.fromScale(0.09, 0.42),
}, gui)
make("UIAspectRatioConstraint", { AspectRatio = 0.47 }, menu)
local indexBtn = iconButton(menu, Color3.fromRGB(140, 92, 242), "book", "INDEX", UDim2.fromScale(0, 0))
local indexBadge = make("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.95, 0.06), Size = UDim2.fromScale(0.36, 0.36), Visible = false, ZIndex = 4 }, indexBtn)
make("UIAspectRatioConstraint", { AspectRatio = 1 }, indexBadge)
face(indexBadge, RED, 1)
local badgeText = title(indexBadge, UDim2.fromScale(0.6, 0.7), UDim2.fromScale(0.2, 0.12), 40, "!")
badgeText.ZIndex = 5
local indexSeen = nil -- how many pets were in the index when it was last opened
local function indexCount()
	local n = 0
	for _, k in ipairs(string.split(attr("Index", ""), ",")) do
		if k ~= "" then
			n = n + 1
		end
	end
	return n
end
indexBtn.Activated:Connect(function()
	indexSeen = indexCount()
	indexBadge.Visible = false
end)
local rebirthBtn = iconButton(menu, Color3.fromRGB(240, 90, 160), "rebirth", "REBIRTH", UDim2.fromScale(0, 0.53))

-- ------------------------------------------------------------ HUD: bottom centre (what to do now + basket)
local bottom = make("Frame", {
	BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.fromScale(0.5, 0.935), Size = UDim2.fromScale(0.42, 0.25),
}, gui)
make("UIAspectRatioConstraint", { AspectRatio = 3.4 }, bottom)
local lockGui -- set further down (treadmill)
local hintPill = make("Frame", { AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromScale(0.5, stormBanner.Visible and 0.6 or 0.02), Size = UDim2.fromScale(0.84, 0.4), Visible = false }, top) -- v108: same width as the EGG STORM banner, centred under it
stormBanner:GetPropertyChangedSignal("Visible"):Connect(function()
	TweenService:Create(hintPill, TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Position = UDim2.fromScale(0.5, stormBanner.Visible and 0.6 or 0.02) }):Play()
end)
local HINT_COL, HINT_BAD = Color3.fromRGB(160, 80, 255), Color3.fromRGB(235, 70, 60)
local hintGrad = face(hintPill, HINT_COL, 0.3)
local hintIcon = icon(hintPill, "alert", UDim2.fromScale(0.8, 0.8), UDim2.fromScale(0.012, 0.1))
local hintArrow = icon(hintPill, "arrow", UDim2.fromScale(0.7, 0.7), UDim2.fromScale(0.02, 0.15))
wobbly[hintArrow] = nil
local hint = text(hintPill, UDim2.fromScale(0.86, 0.64), UDim2.fromScale(0.1, 0.17), 24)
hint.ZIndex = 2
hint:GetPropertyChangedSignal("Text"):Connect(function()
	local bad = string.find(hint.Text, "full") ~= nil
	hintPill.Visible = hint.Text ~= ""
	hintGrad.Color = faceSeq(bad and HINT_BAD or HINT_COL)
	hintIcon.Visible = bad
	hintArrow.Visible = not bad
end)

-- lively HUD: icons rock a little
RunService.RenderStepped:Connect(function()
	local t = os.clock()
	for i, ph in pairs(wobbly) do
		if i.Parent then
			i.Rotation = math.sin(t * 2.2 + ph) * 7
		else
			wobbly[i] = nil
		end
	end
end)

-- basket counter: small, on the left under the cash / speed stack
local basketBox = make("Frame", {
	BackgroundTransparency = 1, Position = UDim2.fromScale(0.018, 0.635), Size = UDim2.fromScale(0.15, 0.06),
}, gui)
make("UIAspectRatioConstraint", { AspectRatio = 4.2 }, basketBox)
local BASKET_COL = Color3.fromRGB(255, 145, 20)
local basketHolder, basketPill, basketGrad = lip(basketBox, BASKET_COL, UDim2.fromScale(0.84, 0.8), UDim2.fromScale(0.15, 0.1), nil, 1)
do -- the shine starts after the basket icon, so it does not show through the handle
	local sh = basketPill:FindFirstChild("Shine")
	sh.BackgroundTransparency = 0.85
	sh.Position = UDim2.fromScale(0.2, 0.06)
	sh.Size = UDim2.fromScale(0.77, 0.42)
end
icon(basketHolder, "basket", UDim2.fromScale(1.35, 1.35), UDim2.fromScale(-0.06, 0.42), Vector2.new(0, 0.5))
local slots = make("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(0.5, 0.56), Position = UDim2.fromScale(0.17, 0.22), ZIndex = 2 }, basketPill)
make("UIListLayout", {
	FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0.015, 0),
	VerticalAlignment = Enum.VerticalAlignment.Center, SortOrder = Enum.SortOrder.LayoutOrder,
}, slots)
local basketLabel = text(basketPill, UDim2.fromScale(0.28, 0.68), UDim2.fromScale(0.69, 0.16), 26)
basketLabel.ZIndex = 2
local SLOT_ON = ColorSequence.new(Color3.fromRGB(255, 240, 160), Color3.fromRGB(255, 178, 30))
local slotMax = -1
local function drawBasket(carry, max)
	local n = math.clamp(max, 1, 15)
	if max ~= slotMax then
		slotMax = max
		for _, s in ipairs(slots:GetChildren()) do
			if s:IsA("Frame") then
				s:Destroy()
			end
		end
		for i = 1, n do
			local s = make("Frame", { Name = "Slot", LayoutOrder = i, BorderSizePixel = 0, Size = UDim2.fromScale(1 / n - 0.015, 1), ZIndex = 2 }, slots)
			corner(s, 0.3)
			make("UIStroke", { Thickness = 2, Color = BLACK, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, s)
			make("UIGradient", { Rotation = 90, Color = SLOT_ON }, s)
		end
	end
	local filled = math.floor(carry / math.max(max, 1) * n + 0.5)
	for _, s in ipairs(slots:GetChildren()) do
		if s:IsA("Frame") then
			local on = s.LayoutOrder <= filled
			s.BackgroundColor3 = on and WHITE or BLACK
			s.BackgroundTransparency = on and 0 or 0.5
			s:FindFirstChildOfClass("UIGradient").Enabled = on
		end
	end
	basketLabel.Text = carry .. "/" .. max
	basketGrad.Color = faceSeq(carry >= max and HINT_BAD or BASKET_COL)
end

-- ------------------------------------------------------------ notifications (bottom centre)
-- messages (You need $1K, ...): plain text with a black outline under the violet hint at the bottom
local note = text(gui, UDim2.fromScale(0.6, 0.065), UDim2.fromScale(0.2, 0.9), 44)
note.Font = Enum.Font.LuckiestGuy
note.ZIndex = 30
note:FindFirstChildOfClass("UIStroke").Thickness = 3
local noteScale = make("UIScale", {}, note)
note.TextTransparency = 1
local noteStroke = note:FindFirstChildOfClass("UIStroke")
noteStroke.Transparency = 1
local NOTE_COL = {
	info = WHITE, good = Color3.fromRGB(120, 240, 120), bad = Color3.fromRGB(255, 60, 60), cash = YELLOW,
	legend = Color3.fromRGB(255, 204, 40), storm = Color3.fromRGB(200, 150, 255), buy = Color3.fromRGB(120, 240, 120),
}
local noteId = 0
local function showNote(msg, kind)
	if kind == "buy" and UI.playerPop then -- purchases (shop, treadmill, upgrades): one sound + a pop out of the player
		playBuy()
		UI.playerPop(msg)
		return
	end
	if false and UI.toast then -- the stacked toast cards are off: messages are plain text under the hint (user)
		UI.toast(msg, kind)
		if kind == "legend" then
			sfx("reveal_legend", 0.6)
		elseif kind == "buy" or kind == "cash" then
			playBuy()
			if kind == "buy" and UI.confetti then
				UI.confetti(30)
			end
		end
		return
	end
	noteId = noteId + 1
	local id = noteId
	note.Text = msg
	note.TextColor3 = NOTE_COL[kind] or NOTE_COL.cash or WHITE
	note.TextTransparency = 0
	noteStroke.Transparency = 0
	noteScale.Scale = 1.25
	TweenService:Create(noteScale, TweenInfo.new(0.2, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	if kind == "legend" then
		sfx("reveal_legend", 0.6)
	elseif kind == "sold" and C.SELL_SOUND and C.SELL_SOUND ~= "" then
		-- selling pets has its own sound (v110, user); uploaded id in Config C.SELL_SOUND
		local snd = Instance.new("Sound")
		snd.SoundId, snd.Volume = C.SELL_SOUND, 0.55
		snd.Parent = SoundService
		snd:Play()
		snd.Ended:Once(function()
			snd:Destroy()
		end)
	elseif kind == "buy" or kind == "cash" or kind == "sold" then
		sfx("coin", 0.6)
	end
	task.delay((kind == "legend" or kind == "storm") and 4.5 or 2.4, function()
		if id == noteId then
			TweenService:Create(note, TweenInfo.new(0.4), { TextTransparency = 1 }):Play()
			TweenService:Create(noteStroke, TweenInfo.new(0.4), { Transparency = 1 }):Play()
		end
	end)
end
UI.noteFn = showNote
Notice.OnClientEvent:Connect(showNote)

-- ------------------------------------------------------------ UI v3 kit: panels with a gold ribbon title, cream inner card, round red X
local flash = make("Frame", { Size = UDim2.fromScale(1, 1), BackgroundColor3 = WHITE, BackgroundTransparency = 1, BorderSizePixel = 0, ZIndex = 0 }, gui)
local TIER_COLOR = { nil, Color3.fromRGB(255, 204, 40), Color3.fromRGB(255, 120, 220) }
local rays, refreshIndex, rebirthPanel, refreshRebirth -- used further down
do

local CREAM = Color3.fromRGB(253, 249, 244)
local DARK = Color3.fromRGB(42, 35, 80) -- main text on the cream inside of the panels
local SOFT = Color3.fromRGB(106, 99, 144) -- secondary text
local STUDS = "rbxassetid://135729525035726" -- ui_studs.png (stud tile of the panels)
local GREY = Color3.fromRGB(150, 154, 172)
local PINK = Color3.fromRGB(240, 90, 160)
local GOLD = Color3.fromRGB(255, 205, 40)
local spinners = {} -- ray fans that turn slowly

-- dark text on the cream cards (no outline)
local function ink(parent, size, pos, maxSize, str, col, font, align)
	local t = make("TextLabel", {
		BackgroundTransparency = 1, Size = size, Position = pos, Font = font or Enum.Font.FredokaOne, TextColor3 = col or DARK,
		TextScaled = true, Text = str or "", TextXAlignment = align or Enum.TextXAlignment.Left, ZIndex = 2,
	}, parent)
	make("UITextSizeConstraint", { MaxTextSize = maxSize or 30 }, t)
	local c = col or DARK
	if c.R * 0.3 + c.G * 0.59 + c.B * 0.11 > 0.55 then -- light text gets a black outline, dark ink none
		make("UIStroke", { Thickness = 2, Color = BLACK }, t)
	end
	return t
end

local function outline(obj, thick)
	return make("UIStroke", { Thickness = thick or 3, Color = BLACK, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, obj)
end

local function squareH(obj) -- keep it square, sized by its height
	make("UIAspectRatioConstraint", { AspectRatio = 1, DominantAxis = Enum.DominantAxis.Height }, obj)
end

-- progress bar: pale track + gradient fill
local function bar(parent, size, pos, top, bottom)
	local bg = make("Frame", { Size = size, Position = pos, BackgroundColor3 = Color3.fromRGB(234, 230, 246), BorderSizePixel = 0, ZIndex = 2 }, parent)
	corner(bg, 1)
	outline(bg, 2.5)
	local fill = make("Frame", { Size = UDim2.fromScale(0, 1), BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 2 }, bg)
	corner(fill, 1)
	grad(fill, top, bottom)
	return bg, fill
end
local function setBar(fill, frac)
	frac = math.clamp(frac, 0, 1)
	fill.Size = UDim2.fromScale(frac, 1)
	fill.Visible = frac > 0.02
end

-- sun rays (white stripes from the middle out), turning slowly
rays = function(parent, n, col, transparency)
	local r = make("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(1.7, 1.7), Rotation = 0 }, parent)
	make("UIAspectRatioConstraint", { AspectRatio = 1 }, r)
	local fadeOut = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.75, 0.1), NumberSequenceKeypoint.new(1, 0.4) })
	for i = 1, n do
		local arm = make("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(1, 1), Rotation = i * 360 / n }, r)
		local ray = make("Frame", {
			AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(0.07, 0.5),
			BackgroundColor3 = col, BackgroundTransparency = transparency, BorderSizePixel = 0,
		}, arm)
		make("UIGradient", { Rotation = 90, Transparency = fadeOut }, ray)
	end
	spinners[r] = 10
	return r
end

-- big 3D button (a TextButton holding a face on a lip) + its label

local function bigButton(parent, col, size, pos, anchor)
	local b = make("TextButton", { BackgroundTransparency = 1, Text = "", AutoButtonColor = false, Size = size, Position = pos, AnchorPoint = anchor or Vector2.new(0, 0), ZIndex = 2 }, parent)
	local holder, faceF = lip(b, col, UDim2.fromScale(1, 0.9), UDim2.fromScale(0, 0), nil, 0.3)
	local label = title(faceF, UDim2.fromScale(0.9, 0.6), UDim2.fromScale(0.05, 0.18), 46, "")
	label.ZIndex = 3
	pressable(b)
	local self = { button = b, face = faceF, label = label }
	function self.color(c)
		tint(faceF, c)
		holder:FindFirstChild("Lip").BackgroundColor3 = darker(c, 0.45)
	end
	return self
end

local openPanel = nil
local blur = make("BlurEffect", { Name = "MenuBlur", Size = 0 }, Lighting)
-- stud texture laid over a frame (the brick look of the panels)
local function studs(parent, transparency, z)
	local s = make("ImageLabel", {
		BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Image = STUDS, ScaleType = Enum.ScaleType.Tile,
		TileSize = UDim2.fromOffset(26, 26), ImageTransparency = transparency or 0.86, ZIndex = z or 1,
	}, parent)
	return s
end

local function panel(titleStr, iconName, col, width, aspect)
	local f = make("Frame", {
		BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.53), Size = UDim2.fromScale(width, 0.84),
		Visible = false, ZIndex = 5,
	}, gui)
	make("UIAspectRatioConstraint", { AspectRatio = aspect }, f)
	local sc = make("UIScale", {}, f)
	local R = UDim.new(0, 26)
	-- UI v3 look: glossy colour body on a darker lip, white diagonal stripes, gold ribbon title, round red X, cream inside
	local shadow = make("Frame", { Size = UDim2.fromScale(1, 1), Position = UDim2.new(0, 4, 0, 18), BackgroundColor3 = BLACK, BackgroundTransparency = 0.6, BorderSizePixel = 0 }, f)
	make("UICorner", { CornerRadius = R }, shadow)
	local lipF = make("Frame", { Size = UDim2.fromScale(1, 1), Position = UDim2.new(0, 0, 0, 10), BackgroundColor3 = darker(col, 0.55), BorderSizePixel = 0 }, f)
	make("UICorner", { CornerRadius = R }, lipF)
	make("UIStroke", { Thickness = 5, Color = BLACK, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, lipF)
	local body = make("Frame", { Size = UDim2.fromScale(1, 1), BackgroundColor3 = WHITE, BorderSizePixel = 0 }, f)
	make("UICorner", { CornerRadius = R }, body)
	make("UIStroke", { Thickness = 5, Color = BLACK, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, body)
	local headGrad = make("UIGradient", { Rotation = 90, Color = faceSeq(col) }, body)
	stripes(body, R, 0.84, 1, 6)
	-- gold ribbon with the title, sticking out over the top edge; darker tails behind it
	local tails = {}
	for sx = -1, 1, 2 do
		local tail = make("Frame", {
			AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromScale(0.5 + sx * 0.3, -0.035), Size = UDim2.fromScale(0.1, 0.09),
			BackgroundColor3 = darker(col, 0.62), BorderSizePixel = 0, ZIndex = 6,
		}, f)
		make("UICorner", { CornerRadius = UDim.new(0, 8) }, tail)
		make("UIStroke", { Thickness = 4, Color = BLACK, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, tail)
		table.insert(tails, tail)
	end
	local ribHolder, rib = lip(f, GOLD, UDim2.fromScale(0.58, 0.12), UDim2.fromScale(0.5, -0.07), Vector2.new(0.5, 0), 0.3)
	ribHolder.ZIndex = 7
	for _, d in ipairs(ribHolder:GetDescendants()) do
		if d:IsA("GuiObject") then
			d.ZIndex = 7
		end
	end
	stripes(rib, UDim.new(0, 12), 0.72, 7, 3)
	local ribbonIcon = icon(rib, iconName, UDim2.fromScale(0.2, 1.25), UDim2.fromScale(0.02, 0.5), Vector2.new(0, 0.5))
	make("UIAspectRatioConstraint", { AspectRatio = 1 }, ribbonIcon)
	ribbonIcon.ZIndex = 9
	local head = make("TextLabel", {
		BackgroundTransparency = 1, Size = UDim2.fromScale(0.74, 0.72), Position = UDim2.fromScale(0.22, 0.12), Font = Enum.Font.LuckiestGuy,
		TextScaled = true, TextColor3 = WHITE, TextXAlignment = Enum.TextXAlignment.Center, Text = titleStr, ZIndex = 9,
	}, rib)
	make("UIStroke", { Thickness = 3.5, Color = BLACK }, head)
	make("UITextSizeConstraint", { MaxTextSize = 64 }, head)
	-- round red X on the top-right corner
	local x = make("TextButton", {
		AutoButtonColor = false, Text = "", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.985, 0.01), Size = UDim2.fromScale(0.095, 0.095), ZIndex = 9,
	}, f)
	make("UIAspectRatioConstraint", { AspectRatio = 1 }, x)
	face(x, Color3.fromRGB(240, 60, 55), 1)
	local xl = make("TextLabel", {
		BackgroundTransparency = 1, Size = UDim2.fromScale(0.62, 0.62), Position = UDim2.fromScale(0.19, 0.17), Font = Enum.Font.LuckiestGuy,
		TextScaled = true, TextColor3 = WHITE, Text = "X", ZIndex = 10,
	}, x)
	make("UIStroke", { Thickness = 3, Color = BLACK }, xl)
	pressable(x)
	-- cream inside (all panel contents are laid out in this frame, 0..1)
	local inner = make("Frame", { Size = UDim2.fromScale(0.955, 0.84), Position = UDim2.fromScale(0.0225, 0.12), BackgroundColor3 = Color3.fromRGB(255, 252, 246), BackgroundTransparency = 0.03, BorderSizePixel = 0, ZIndex = 2 }, body)
	make("UICorner", { CornerRadius = UDim.new(0, 18) }, inner)
	make("UIStroke", { Thickness = 4, Color = BLACK, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, inner)

	local self = { frame = f, scale = sc, head = head, inner = inner, icon = ribbonIcon }
	function self.color(c)
		headGrad.Color = faceSeq(c)
		lipF.BackgroundColor3 = darker(c, 0.55)
		for _, t in ipairs(tails) do
			t.BackgroundColor3 = darker(c, 0.62)
		end
	end
	function self.close()
		if openPanel == self then
			openPanel = nil
			TweenService:Create(blur, TweenInfo.new(0.2), { Size = 0 }):Play()
		end
		local t = TweenService:Create(sc, TweenInfo.new(0.15), { Scale = 0 })
		t:Play()
		task.delay(0.15, function()
			if openPanel ~= self then
				f.Visible = false
			end
		end)
	end
	function self.open()
		if openPanel and openPanel ~= self then
			openPanel.close()
		end
		openPanel = self
		TweenService:Create(blur, TweenInfo.new(0.25), { Size = 14 }):Play()
		f.Visible = true
		sc.Scale = 0.6
		TweenService:Create(sc, TweenInfo.new(0.25, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
	end
	function self.toggle()
		if openPanel == self then
			self.close()
		else
			self.open()
		end
	end
	x.Activated:Connect(self.close)
	return self
end

local function setIcon(img, name)
	local sheet, off, sz = iconRect(name)
	img.Image, img.ImageRectOffset, img.ImageRectSize = sheet, off, sz
end

-- round number badge (NOW 2 > NEXT 3, 5 > 6 pets)
local function circle(parent, col, size, pos, small)
	local c = make("Frame", { Size = size, Position = pos, ZIndex = 2 }, parent)
	squareH(c)
	face(c, col, 1)
	local cap
	if small then
		cap = make("TextLabel", {
			BackgroundTransparency = 1, Size = UDim2.fromScale(0.6, 0.16), Position = UDim2.fromScale(0.2, 0.13), Font = Enum.Font.FredokaOne,
			TextScaled = true, TextColor3 = Color3.fromRGB(235, 235, 255), Text = small, ZIndex = 3,
		}, c)
	end
	local t = title(c, UDim2.fromScale(0.7, small and 0.46 or 0.5), UDim2.fromScale(0.15, small and 0.32 or 0.25), 90, "")
	t.ZIndex = 3
	return c, t, cap
end

-- ------------------------------------------------------------ index: zone tabs on the left, 5 pet cards of the chosen zone
local indexPanel = panel("PET INDEX", "book", Color3.fromRGB(150, 100, 245), 0.8, 1.75)
local ii = indexPanel.inner
local foundLabel = ink(ii, UDim2.fromScale(0.25, 0.09), UDim2.fromScale(0.03, 0.045), 60, "FOUND 0 / " .. C.PET_COUNT, DARK, Enum.Font.LuckiestGuy)
local _, foundFill = bar(ii, UDim2.fromScale(0.38, 0.05), UDim2.fromScale(0.3, 0.065), Color3.fromRGB(205, 165, 255), Color3.fromRGB(140, 80, 240))
local _, bonusFace = lip(ii, GREEN, UDim2.fromScale(0.26, 0.085), UDim2.fromScale(0.71, 0.04), nil, 1)
local bonusText = title(bonusFace, UDim2.fromScale(0.9, 0.62), UDim2.fromScale(0.05, 0.17), 34, "Full zone = +" .. math.floor(C.INDEX_BONUS * 100 + 0.5) .. "% cash")
bonusText.Font = Enum.Font.FredokaOne
bonusText.ZIndex = 2

local NZ, NR = C.NZ, #C.RARITY
local selZone = 1
local found = {}
local tabs = {}
local tabList = make("ScrollingFrame", {
	BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(0.26, 0.79), Position = UDim2.fromScale(0.025, 0.18),
	ScrollBarThickness = 6, CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollingDirection = Enum.ScrollingDirection.Y, ZIndex = 2,
}, ii)
make("UIListLayout", { Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder }, tabList)
make("UIPadding", { PaddingTop = UDim.new(0, 4), PaddingLeft = UDim.new(0, 4), PaddingRight = UDim.new(0, 10) }, tabList)
local TAB_COL, TAB_ON = Color3.fromRGB(70, 76, 200), Color3.fromRGB(60, 200, 80)
for z = 1, NZ do
	local b = make("TextButton", { BackgroundTransparency = 1, Text = "", AutoButtonColor = false, Size = UDim2.new(1, 0, 0, 40), LayoutOrder = z, ZIndex = 2 }, tabList)
	make("UIAspectRatioConstraint", { AspectRatio = 4.3, DominantAxis = Enum.DominantAxis.Width }, b)
	local holder, faceF = lip(b, TAB_COL, UDim2.fromScale(1, 0.86), UDim2.fromScale(0, 0), nil, 0.35)
	local name = title(faceF, UDim2.fromScale(0.66, 0.62), UDim2.fromScale(0.07, 0.17), 30, (C.ZONES[z].name:match("^%S+") or C.ZONES[z].name):upper())
	name.TextXAlignment = Enum.TextXAlignment.Left
	name.ZIndex = 2
	local count = title(faceF, UDim2.fromScale(0.24, 0.55), UDim2.fromScale(0.71, 0.2), 26, "0/" .. NR)
	count.TextXAlignment = Enum.TextXAlignment.Right
	count.ZIndex = 2
	pressable(b)
	tabs[z] = { face = faceF, lip = holder:FindFirstChild("Lip"), count = count }
	b.Activated:Connect(function()
		selZone = z
		refreshIndex()
	end)
end

local zoneTitle = ink(ii, UDim2.fromScale(0.64, 0.08), UDim2.fromScale(0.32, 0.17), 44, "", DARK, Enum.Font.LuckiestGuy)
local indexInfo = ink(ii, UDim2.fromScale(0.64, 0.08), UDim2.fromScale(0.32, 0.87), 30, "Tap a pet to see it", SOFT, nil, Enum.TextXAlignment.Center)
local cards = {}
for i = 1, NR do
	local card = make("TextButton", { AutoButtonColor = false, Text = "", Size = UDim2.fromScale(0.118, 0.57), Position = UDim2.fromScale(0.32 + (i - 1) * 0.131, 0.27), ZIndex = 2 }, ii)
	face(card, GREY, 0.14)
	local nameL = title(card, UDim2.fromScale(0.9, 0.11), UDim2.fromScale(0.05, 0.04), 24, "")
	nameL.ZIndex = 3
	local q = title(card, UDim2.fromScale(0.6, 0.36), UDim2.fromScale(0.2, 0.2), 90, "?")
	q.TextColor3 = Color3.fromRGB(150, 152, 168)
	q:FindFirstChildOfClass("UIStroke").Transparency = 1
	q.ZIndex = 3
	local rarL = title(card, UDim2.fromScale(0.9, 0.12), UDim2.fromScale(0.05, 0.7), 26, C.RARITY[i].name:upper())
	rarL.ZIndex = 3
	local oddsL = title(card, UDim2.fromScale(0.86, 0.09), UDim2.fromScale(0.07, 0.85), 20, "1 in " .. C.comma(C.RARITY[i].odds))
	oddsL.Font = Enum.Font.FredokaOne
	oddsL.ZIndex = 3
	pressable(card)
	cards[i] = { frame = card, name = nameL, q = q, view = nil, key = nil }
	card.Activated:Connect(function()
		local def = C.ZONES[selZone].pets[i]
		local rar = C.RARITY[i]
		if found[selZone .. "_" .. i] then
			indexInfo.Text = def.name .. "  -  " .. rar.name .. "  -  1 in " .. C.comma(rar.odds) .. "  -  $" .. C.fmt(def.income) .. "/s"
		else
			indexInfo.Text = "???  -  " .. rar.name .. "  -  1 in " .. C.comma(rar.odds) .. "  -  falls in " .. C.ZONES[selZone].name
		end
	end)
end

refreshIndex = function()
	found = {}
	local n = 0
	for _, key in ipairs(string.split(attr("Index", ""), ",")) do
		local z, i = string.match(key, "^(%d+)_(%d+)$")
		if z and C.ZONES[tonumber(z)] and C.RARITY[tonumber(i)] and not found[key] then
			found[key] = true
			n = n + 1
		end
	end
	foundLabel.Text = "FOUND " .. n .. " / " .. C.PET_COUNT
	setBar(foundFill, n / C.PET_COUNT)
	if not indexPanel.frame.Visible then
		return
	end
	for z = 1, NZ do
		local c = 0
		for i = 1, NR do
			if found[z .. "_" .. i] then
				c = c + 1
			end
		end
		local t = tabs[z]
		t.count.Text = c .. "/" .. NR
		local col = (z == selZone) and TAB_ON or TAB_COL
		tint(t.face, col)
		t.lip.BackgroundColor3 = darker(col, 0.45)
		t.count.TextColor3 = (c == NR) and YELLOW or WHITE
	end
	zoneTitle.Text = C.ZONES[selZone].name:upper()
	for i = 1, NR do
		local cd = cards[i]
		local key = selZone .. "_" .. i
		local has = found[key]
		if cd.key ~= key or (has and not cd.view) then
			cd.key = key
			if cd.view then
				cd.view:Destroy()
				cd.view = nil
			end
			tint(cd.frame, has and C.RARITY[i].color or GREY)
			cd.q.Visible = not has
			cd.name.Text = has and C.ZONES[selZone].pets[i].name or ""
			if has then
				cd.view = petView(cd.frame, { z = selZone, i = i, t = 1 }, UDim2.fromScale(1, 0.56), UDim2.fromScale(0, 0.14))
				cd.view.ZIndex = 3
			end
		end
	end
end
indexBtn.Activated:Connect(function()
	indexPanel.toggle()
	refreshIndex()
end)
UI.openIndex = function() -- used by the new left HUD buttons (UIMenus)
	indexSeen = indexCount()
	indexBadge.Visible = false
	indexPanel.toggle()
	refreshIndex()
end
UI.indexHasNew = function()
	return indexBadge.Visible
end

-- ------------------------------------------------------------ shop zones: stand on the glowing pad in front of a shop -> its menu opens
local SHOP = {
	basket = { title = "BASKET SHOP", name = "BIGGER BASKET", desc = "Carry more pets on each run", unit = "pets", col = Color3.fromRGB(255, 145, 20), icon = "basket", card = Color3.fromRGB(255, 200, 100) },
	luck = { title = "LUCK SHOP", name = "MORE LUCK", desc = "Rare pets hatch more often", unit = "luck", col = Color3.fromRGB(40, 190, 90), icon = "clover", card = Color3.fromRGB(160, 236, 150) },
	sell = { title = "SELL PETS", name = "SELL YOUR BASKET", desc = "Turn the pets you carry into cash", unit = "pets", col = Color3.fromRGB(240, 170, 20), icon = "coin", card = Color3.fromRGB(255, 222, 110) },
}
local shopPanel = panel("BASKET SHOP", "basket", SHOP.basket.col, 0.56, 1.75)
local si = shopPanel.inner
-- picture card on the left: sun rays + big icon + LEVEL badge
local card = make("CanvasGroup", { Size = UDim2.fromScale(0.36, 0.8), Position = UDim2.fromScale(0.035, 0.06), BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 2 }, si)
corner(card, 0.08)
local cardGrad = make("UIGradient", { Rotation = 90, Color = faceSeq(SHOP.basket.card) }, card)
rays(card, 14, WHITE, 0.35)
local cardIcon = icon(card, "basket", UDim2.fromScale(0.62, 0.62), UDim2.fromScale(0.5, 0.46), Vector2.new(0.5, 0.5))
local cardBorder = make("Frame", { BackgroundTransparency = 1, Size = card.Size, Position = card.Position, ZIndex = 3 }, si)
corner(cardBorder, 0.08)
outline(cardBorder, 3)
local _, lvFace = lip(si, GOLD, UDim2.fromScale(0.19, 0.12), UDim2.fromScale(0.215, 0.8), Vector2.new(0.5, 0), 0.4)
lvFace.Parent.ZIndex = 4
local lvText = title(lvFace, UDim2.fromScale(0.86, 0.66), UDim2.fromScale(0.07, 0.14), 40, "LEVEL 1")
lvText.ZIndex = 3
-- right side
local shopName = ink(si, UDim2.fromScale(0.53, 0.11), UDim2.fromScale(0.43, 0.06), 64, "", DARK, Enum.Font.LuckiestGuy)
local shopDesc = ink(si, UDim2.fromScale(0.53, 0.075), UDim2.fromScale(0.43, 0.18), 32, "", SOFT)
local nowC, nowT = circle(si, Color3.fromRGB(240, 238, 252), UDim2.fromScale(1, 0.18), UDim2.fromScale(0.43, 0.29))

local arrowT = ink(si, UDim2.fromScale(0.05, 0.12), UDim2.fromScale(0.525, 0.32), 60, ">", PINK, Enum.Font.LuckiestGuy, Enum.TextXAlignment.Center)
local nextC, nextT = circle(si, GREEN, UDim2.fromScale(1, 0.18), UDim2.fromScale(0.585, 0.29))
local unitT = ink(si, UDim2.fromScale(0.2, 0.09), UDim2.fromScale(0.675, 0.335), 40, "pets", SOFT)
local slotRow = make("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(0.53, 0.1), Position = UDim2.fromScale(0.43, 0.51), ZIndex = 2 }, si)
make("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0.015, 0), VerticalAlignment = Enum.VerticalAlignment.Center, SortOrder = Enum.SortOrder.LayoutOrder }, slotRow)
local _, lvFill = bar(si, UDim2.fromScale(0.53, 0.045), UDim2.fromScale(0.43, 0.655), Color3.fromRGB(255, 205, 90), Color3.fromRGB(250, 130, 20))
local lvSmall = ink(si, UDim2.fromScale(0.3, 0.065), UDim2.fromScale(0.43, 0.71), 30, "", SOFT)
local buy = bigButton(si, GREEN, UDim2.fromScale(0.53, 0.18), UDim2.fromScale(0.43, 0.79))
buy.label.Size = UDim2.fromScale(0.3, 0.6)
buy.label.TextXAlignment = Enum.TextXAlignment.Right
local buyCoin = icon(buy.face, "coin", UDim2.fromScale(0.7, 0.7), UDim2.fromScale(0.39, 0.12))
buyCoin.ZIndex = 3
wobbly[buyCoin] = nil
local buyPrice = title(buy.face, UDim2.fromScale(0.46, 0.6), UDim2.fromScale(0.5, 0.18), 46, "")
buyPrice.TextXAlignment = Enum.TextXAlignment.Left
buyPrice.ZIndex = 3
local function setBuy(str, price, col)
	buy.color(col)
	buyCoin.Visible = price ~= nil
	buyPrice.Visible = price ~= nil
	if price then
		buy.label.Text = str
		buy.label.Size = UDim2.fromScale(0.3, 0.6)
		buy.label.TextXAlignment = Enum.TextXAlignment.Right
		buyPrice.Text = "$" .. C.comma(price)
	else
		buy.label.Text = str
		buy.label.Size = UDim2.fromScale(0.9, 0.6)
		buy.label.TextXAlignment = Enum.TextXAlignment.Center
	end
end
local shopKind = nil
local refreshShopLater
-- SELL shop (v103, user: "choose which pet you sell"): every pet in the basket and in the pen, one row each, tap = sell it
do
	local list = make("ScrollingFrame", { Visible = false, BackgroundColor3 = Color3.fromRGB(250, 246, 235), BorderSizePixel = 0, Size = UDim2.fromScale(0.53, 0.49), Position = UDim2.fromScale(0.43, 0.27),
		ScrollBarThickness = 8, CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollingDirection = Enum.ScrollingDirection.Y, ZIndex = 2 }, si)
	corner(list, 0.06)
	outline(list, 3)
	make("UIListLayout", { Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder, HorizontalAlignment = Enum.HorizontalAlignment.Center }, list)
	make("UIPadding", { PaddingTop = UDim.new(0, 6), PaddingBottom = UDim.new(0, 6) }, list)
	local RC = { Color3.fromRGB(150, 150, 165), Color3.fromRGB(60, 190, 90), Color3.fromRGB(40, 150, 240), Color3.fromRGB(170, 70, 240), Color3.fromRGB(245, 170, 20) }
	local lastKey, busyUntil = nil, 0
	UI.sellList = list
	UI.drawSellList = function()
		local key = attr("CarryList", "") .. "|" .. attr("PetList", "")
		if key == lastKey then
			return
		end
		lastKey = key
		for _, c in ipairs(list:GetChildren()) do
			if c:IsA("GuiObject") then
				c:Destroy()
			end
		end
		local n = 0
		local function rows(str, where, tag)
			local i = 0
			for _, k in ipairs(string.split(str, ",")) do
				local z, idx, t, vv = string.match(k, "^(%d+)_(%d+)_(%d+)_?(%d*)$")
				if z then
					i = i + 1
					n = n + 1
					local pet = { z = tonumber(z), i = tonumber(idx), t = tonumber(t), v = tonumber(vv) }
					local price = math.floor(C.petIncome(pet) * C.SELL_MULT)
					local row = make("TextButton", { LayoutOrder = n, Size = UDim2.new(0.95, 0, 0, 46), BackgroundColor3 = WHITE, AutoButtonColor = true, Text = "", ZIndex = 3 }, list)
					corner(row, 0.25)
					outline(row, 2)
					local dot = make("Frame", { Size = UDim2.new(0, 10, 0.7, 0), Position = UDim2.new(0, 8, 0.15, 0), BackgroundColor3 = RC[math.min(pet.i, 5)], BorderSizePixel = 0, ZIndex = 4 }, row)
					corner(dot, 0.5)
					local nm = ink(row, UDim2.new(0.5, 0, 0.8, 0), UDim2.new(0, 26, 0.1, 0), 26, C.petName(pet) .. "  " .. tag, DARK, Enum.Font.FredokaOne)
					nm.ZIndex = 4
					local sb = make("Frame", { Size = UDim2.new(0.38, 0, 0.78, 0), Position = UDim2.new(0.6, 0, 0.11, 0), BackgroundColor3 = GREEN, BorderSizePixel = 0, ZIndex = 4 }, row)
					corner(sb, 0.3)
					local st = title(sb, UDim2.fromScale(0.94, 0.8), UDim2.fromScale(0.03, 0.1), 26, "SELL $" .. C.fmt(price))
					st.ZIndex = 5
					local myIdx = i
					row.Activated:Connect(function()
						if os.clock() < busyUntil then
							return
						end
						busyUntil = os.clock() + 0.35
						Action:FireServer("sellpet", where .. myIdx)
					end)
				end
			end
		end
		rows(attr("CarryList", ""), "c", "(basket)")
		rows(attr("PetList", ""), "p", "(pen)")
		if n == 0 then
			local e = ink(list, UDim2.new(0.95, 0, 0, 60), UDim2.new(), 30, "No pets yet - catch and hatch eggs!", SOFT)
			e.TextXAlignment = Enum.TextXAlignment.Center
		end
	end
end
local slotCount = -1
local function drawSlots(have, nextN)
	local shown = math.min(nextN, 15)
	if shown ~= slotCount then
		slotCount = shown
		for _, s in ipairs(slotRow:GetChildren()) do
			if s:IsA("Frame") then
				s:Destroy()
			end
		end
		local w = 0.85 / math.max(shown, 9)
		for i = 1, shown do
			local s = make("Frame", { LayoutOrder = i, Size = UDim2.fromScale(w, 1), BorderSizePixel = 0, BackgroundColor3 = WHITE, ZIndex = 2 }, slotRow)
			make("UIAspectRatioConstraint", { AspectRatio = 1, DominantAxis = Enum.DominantAxis.Width }, s)
			corner(s, 0.28)
			outline(s, 2.5)
			make("UIGradient", { Rotation = 90, Color = ColorSequence.new(Color3.fromRGB(255, 240, 160), Color3.fromRGB(255, 178, 30)) }, s)
		end
	end
	for _, s in ipairs(slotRow:GetChildren()) do
		if s:IsA("Frame") then
			local new = s.LayoutOrder > have
			s:FindFirstChildOfClass("UIGradient").Enabled = not new
			s.BackgroundColor3 = new and Color3.fromRGB(205, 250, 205) or WHITE
			s:FindFirstChildOfClass("UIStroke").Color = new and Color3.fromRGB(60, 170, 70) or BLACK
		end
	end
end

-- ---- basket shop: the 20 Blender baskets (3D picture, strip of all baskets, buy the next one)
local function basketView(parent, k, props)
	local vp = make("ViewportFrame", props, parent)
	vp.BackgroundTransparency = 1
	vp.Ambient = Color3.fromRGB(190, 190, 200)
	vp.LightColor = Color3.fromRGB(255, 255, 255)
	vp.LightDirection = Vector3.new(-0.4, -1, -0.6)
	local cam = make("Camera", { FieldOfView = 30 }, vp)
	vp.CurrentCamera = cam
	local ok, meta = pcall(function()
		return require(RS:FindFirstChild("PropsMeta"))
	end)
	local found = false
	for _, nm in ipairs({ "Basket_" .. k, "BasketNeon_" .. k }) do
		local src, m = C.meshOf(nm), ok and type(meta) == "table" and meta[nm]
		if src and m then
			local q = src:Clone()
			q.Anchored = true
			q.Size = Vector3.new(m.size[1], m.size[2], m.size[3])
			q.CFrame = CFrame.new(m.centre[1], m.centre[2], m.centre[3]) * CFrame.Angles(0, C.PROP_YAW, 0)
			q.Color = Color3.new(1, 1, 1)
			q.Parent = vp
			found = true
		end
	end
	local rim = C.basketRim(k)
	local target = Vector3.new(0, rim.Y - 1.1, rim.Z)
	cam.CFrame = CFrame.lookAt(target + Vector3.new(2.6, 2.6, 6.4), target)
	return vp, found
end

local bViews = {} -- k -> big ViewportFrame on the card (made once, shown one at a time)
local selBasket = nil -- basket the player clicked in the strip (nil = the next one to buy)
local strip = make("ScrollingFrame", {
	Size = UDim2.fromScale(0.53, 0.17), Position = UDim2.fromScale(0.43, 0.6), BackgroundTransparency = 1, BorderSizePixel = 0,
	ScrollBarThickness = 6, ScrollingDirection = Enum.ScrollingDirection.X, AutomaticCanvasSize = Enum.AutomaticSize.X,
	CanvasSize = UDim2.new(0, 0, 0, 0), ZIndex = 2, Visible = false,
}, si)
make("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), VerticalAlignment = Enum.VerticalAlignment.Center, SortOrder = Enum.SortOrder.LayoutOrder }, strip)
make("UIPadding", { PaddingLeft = UDim.new(0, 6), PaddingRight = UDim.new(0, 6) }, strip)
local thumbs = {}
for k = 1, #C.BASKETS do
	local t = make("TextButton", { LayoutOrder = k, Size = UDim2.fromScale(0, 0.86), AutoButtonColor = false, Text = "", BackgroundColor3 = WHITE, ZIndex = 3 }, strip)
	make("UIAspectRatioConstraint", { AspectRatio = 0.86, DominantAxis = Enum.DominantAxis.Height }, t)
	corner(t, 0.18)
	local st = outline(t, 2.5)
	local vp = basketView(t, k, { Size = UDim2.fromScale(0.9, 0.7), Position = UDim2.fromScale(0.05, 0.02), ZIndex = 3 })
	local lbl = make("TextLabel", { BackgroundTransparency = 1, Size = UDim2.fromScale(0.96, 0.26), Position = UDim2.fromScale(0.02, 0.72), Font = Enum.Font.LuckiestGuy, TextScaled = true, TextColor3 = WHITE, Text = "", ZIndex = 4 }, t)
	make("UIStroke", { Thickness = 2, Color = BLACK }, lbl)
	pressable(t)
	t.Activated:Connect(function()
		selBasket = k
		refreshShopLater()
	end)
	thumbs[k] = { btn = t, vp = vp, lbl = lbl, stroke = st }
end

local function drawBasketShop()
	local lv = attr("BasketLv", 0)
	local owned = lv + 1
	local nextK = math.min(owned + 1, #C.BASKETS)
	local k = selBasket or (owned >= #C.BASKETS and owned or nextK)
	local b = C.BASKETS[k]
	-- 3D picture on the card
	for kk, v in pairs(bViews) do
		v.Visible = kk == k
	end
	if not bViews[k] then
		local v, found = basketView(card, k, { Size = UDim2.fromScale(0.92, 0.84), Position = UDim2.fromScale(0.04, 0.06), ZIndex = 3 })
		bViews[k] = v
		v.Visible = found
	end
	cardIcon.Visible = not bViews[k].Visible
	lvText.Text = "#" .. k
	shopName.Text = string.upper(b.name)
	shopDesc.Text = "Wear it on your back. Holds " .. C.basketMax(k - 1) .. " pets"
	local a, c = C.basketMax(lv), C.basketMax(k - 1)
	nowT.Text, nextT.Text = tostring(a), tostring(c)
	local showArrow = k > owned
	arrowT.Visible, nextC.Visible = showArrow, showArrow
	unitT.Text = ""
	slotRow.Visible = true
	drawSlots(showArrow and a or c, showArrow and c or c)
	lvFill.Parent.Visible, lvSmall.Visible = false, false
	strip.Visible = true
	for kk, t in ipairs(thumbs) do
		local have = kk <= owned
		local open = kk == owned + 1
		t.vp.ImageColor3 = (have or open) and Color3.new(1, 1, 1) or Color3.fromRGB(25, 22, 40)
		t.lbl.Text = have and (kk == owned and "ON" or "OWNED") or (C.BASKETS[kk].price == 0 and "FREE" or ("$" .. C.fmt(C.BASKETS[kk].price)))
		t.lbl.TextColor3 = have and Color3.fromRGB(150, 255, 140) or WHITE
		t.btn.BackgroundColor3 = kk == k and Color3.fromRGB(255, 214, 90) or WHITE
		t.stroke.Thickness = kk == k and 4 or 2.5
	end
	if k <= owned then
		setBuy(k == owned and "EQUIPPED" or "OWNED", nil, GREY)
	elseif k == owned + 1 then
		setBuy("BUY", b.price, attr("Cash", 0) >= b.price and GREEN or GREY)
	else
		setBuy("BUY #" .. (owned + 1) .. " FIRST", nil, GREY)
	end
end

local function refreshShop()
	local k = shopKind
	if not k then
		return
	end
	local def = SHOP[k]
	shopPanel.head.Text = def.title
	setIcon(shopPanel.icon, def.icon)
	setIcon(cardIcon, def.icon)
	shopPanel.color(def.col)
	cardGrad.Color = faceSeq(def.card)
	shopName.Text = def.name
	shopDesc.Text = def.desc
	strip.Visible = false
	cardIcon.Visible = true
	for _, v in pairs(bViews) do
		v.Visible = false
	end
	if k == "basket" then
		lvFace.Parent.Visible = true
		drawBasketShop()
		return
	end
	nowC.Visible, unitT.Visible, UI.sellList.Visible = k ~= "sell", k ~= "sell", k == "sell"
	if k == "sell" then
		local carry = #string.split(attr("CarryList", ""), ",") - (attr("CarryList", "") == "" and 1 or 0)
		arrowT.Visible, nextC.Visible, slotRow.Visible = false, false, false
		lvFill.Parent.Visible, lvSmall.Visible, lvFace.Parent.Visible = false, false, false
		shopDesc.Text = "Tap a pet to sell it, or sell the whole basket"
		UI.drawSellList()
		setBuy(carry > 0 and ("SELL BASKET (" .. carry .. ")") or "BASKET EMPTY", nil, carry > 0 and GREEN or GREY)
		return
	end
	arrowT.Visible, nextC.Visible = true, true
	lvFill.Parent.Visible, lvSmall.Visible, lvFace.Parent.Visible = true, true, true
	unitT.Position = UDim2.fromScale(0.675, 0.335)
	unitT.Size = UDim2.fromScale(0.2, 0.09)
	unitT.Text = def.unit
	local lv = attr(k == "basket" and "BasketLv" or "LuckLv", 0)
	local maxLv = C.MAX_LV[k]
	local maxed = lv >= maxLv
	lvText.Text = "LEVEL " .. lv
	lvSmall.Text = "Level " .. lv .. " / " .. maxLv
	setBar(lvFill, lv / math.max(maxLv, 1))
	if k == "basket" then
		local a, b = C.basketMax(lv), C.basketMax(math.min(lv + 1, maxLv))
		nowT.Text, nextT.Text = tostring(a), tostring(b)
		slotRow.Visible = true
		drawSlots(a, maxed and a or b)
	else
		nowT.Text, nextT.Text = "x" .. C.luck(lv), "x" .. C.luck(math.min(lv + 1, maxLv))
		slotRow.Visible = false
	end
	if maxed then
		arrowT.Visible, nextC.Visible = false, false
		setBuy("MAX LEVEL", nil, GREY)
	else
		local cost = C.cost(k, lv)
		setBuy("BUY", cost, attr("Cash", 0) >= cost and GREEN or GREY)
	end
end
refreshShopLater = function()
	refreshShop()
end
buy.button.Activated:Connect(function()
	if shopKind == "basket" then
		local owned = attr("BasketLv", 0) + 1
		if selBasket and selBasket ~= owned + 1 then
			return
		end
		selBasket = nil
	end
	if shopKind then
		Action:FireServer("shop", shopKind)
	end
end)
plr.AttributeChanged:Connect(function()
	if shopPanel.frame.Visible then
		refreshShop()
	end
end)

-- open / close the menu when you step on / off
task.spawn(function()
	local pads = {}
	local map = workspace:WaitForChild("Map", 30)
	if not map then
		return
	end
	for _, d in ipairs(map:GetDescendants()) do
		if d.Name == "ShopPad" and d:IsA("BasePart") then
			table.insert(pads, d)
		end
	end
	local onPad = nil
	while true do
		task.wait(0.15)
		local ch = plr.Character
		local hrp = ch and ch:FindFirstChild("HumanoidRootPart")
		local now = nil
		if hrp then
			for _, pad in ipairs(pads) do
				-- round pad: flat distance to its centre (the disc is Size.Y wide)
				local d = hrp.Position - pad.Position
				if Vector3.new(d.X, 0, d.Z).Magnitude < math.max(pad.Size.Y, pad.Size.Z) / 2 and d.Y < 8 and d.Z < 0.5 then -- half circle in front of the shop
					now = pad
					break
				end
			end
		end
		if now ~= onPad then
			onPad = now
			local kind = now and now:GetAttribute("Shop")
			if kind == "index" then
				indexPanel.open()
				refreshIndex()
			elseif kind == "sell" and UI.openSell then
				shopKind = kind
				UI.openSell() -- v104: own SELL PETS menu (UIMenus) with pet cards to select
			elseif kind and SHOP[kind] then
				shopKind = kind
				refreshShop()
				shopPanel.open()
			elseif not now then
				if openPanel == shopPanel or openPanel == indexPanel then
					openPanel.close()
				end
				if shopKind == "sell" and UI.closeSell then
					UI.closeSell()
				end
				shopKind = nil
			end
		end
	end
end)

-- ------------------------------------------------------------ rebirth: NOW > NEXT, what you get / lose / keep, speed bar
rebirthPanel = panel("REBIRTH", "rebirth", Color3.fromRGB(240, 100, 175), 0.52, 1.35)
local ri = rebirthPanel.inner
-- NOW > NEXT as two medals: glow, spinning gold ring, glossy disc, big number, ribbon label; animated chevrons between
local rbNow, rbNext
do
	local TS = game:GetService("TweenService")
	local INKC = Color3.fromRGB(28, 16, 48)
	local function round(o)
		make("UICorner", { CornerRadius = UDim.new(1, 0) }, o)
	end
	local function badge(colA, colB, h, pos, label)
		local root = make("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, h), Position = pos, ZIndex = 2 }, ri)
		make("UIAspectRatioConstraint", { AspectRatio = 1, DominantAxis = Enum.DominantAxis.Height }, root)
		local glow = make("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(1.22, 1.22), BackgroundColor3 = colA, BackgroundTransparency = 0.7, BorderSizePixel = 0, ZIndex = 2 }, root)
		round(glow)
		local ring = make("Frame", { Size = UDim2.fromScale(1, 1), BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 3 }, root)
		round(ring)
		make("UIStroke", { Thickness = 4, Color = INKC }, ring)
		local shine = make("UIGradient", { Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 232, 140)), ColorSequenceKeypoint.new(0.35, Color3.fromRGB(205, 140, 30)),
			ColorSequenceKeypoint.new(0.5, Color3.fromRGB(255, 250, 210)), ColorSequenceKeypoint.new(0.65, Color3.fromRGB(205, 140, 30)), ColorSequenceKeypoint.new(1, Color3.fromRGB(255, 232, 140)) }) }, ring)
		local disc = make("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(0.8, 0.8), BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 4 }, ring)
		round(disc)
		make("UIStroke", { Thickness = 3, Color = INKC, Transparency = 0.2 }, disc)
		make("UIGradient", { Rotation = 90, Color = ColorSequence.new(colA, colB) }, disc)
		local gloss = make("Frame", { AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromScale(0.5, 0.07), Size = UDim2.fromScale(0.72, 0.4), BackgroundColor3 = WHITE, BackgroundTransparency = 0.45, BorderSizePixel = 0, ZIndex = 5 }, disc)
		round(gloss)
		make("UIGradient", { Rotation = 90, Transparency = NumberSequence.new(0.2, 1) }, gloss)
		local num = make("TextLabel", { BackgroundTransparency = 1, Size = UDim2.fromScale(0.84, 0.66), Position = UDim2.fromScale(0.08, 0.16), Font = Enum.Font.LuckiestGuy, TextScaled = true,
			TextColor3 = WHITE, Text = "0", ZIndex = 6 }, disc)
		make("UIStroke", { Thickness = 5, Color = INKC }, num)
		make("UIGradient", { Rotation = 90, Color = ColorSequence.new(WHITE, Color3.fromRGB(255, 228, 150)) }, num)
		local rib = make("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.97), Size = UDim2.fromScale(0.86, 0.24), BackgroundColor3 = colB, BorderSizePixel = 0, ZIndex = 7 }, root)
		make("UICorner", { CornerRadius = UDim.new(0.45, 0) }, rib)
		make("UIStroke", { Thickness = 3, Color = INKC }, rib)
		make("UIGradient", { Rotation = 90, Color = ColorSequence.new(colA, colB) }, rib)
		local lt = make("TextLabel", { BackgroundTransparency = 1, Size = UDim2.fromScale(0.9, 0.78), Position = UDim2.fromScale(0.05, 0.11), Font = Enum.Font.LuckiestGuy, TextScaled = true,
			TextColor3 = WHITE, Text = label, ZIndex = 8 }, rib)
		make("UIStroke", { Thickness = 2, Color = INKC }, lt)
		-- the gold ring shine keeps turning
		TS:Create(shine, TweenInfo.new(3, Enum.EasingStyle.Linear, Enum.EasingDirection.In, -1), { Rotation = 360 }):Play()
		return root, num, glow
	end
	local _, n1 = badge(Color3.fromRGB(110, 130, 255), Color3.fromRGB(40, 46, 170), 0.25, UDim2.fromScale(0.2, 0.05), "NOW")
	local nextRoot, n2, glow2 = badge(Color3.fromRGB(255, 120, 210), Color3.fromRGB(185, 30, 135), 0.29, UDim2.fromScale(0.575, 0.03), "NEXT")
	rbNow, rbNext = n1, n2
	-- NEXT breathes and glows
	local sc = make("UIScale", {}, nextRoot)
	TS:Create(sc, TweenInfo.new(0.9, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), { Scale = 1.07 }):Play()
	TS:Create(glow2, TweenInfo.new(0.9, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), { BackgroundTransparency = 0.45, Size = UDim2.fromScale(1.34, 1.34) }):Play()
	-- three chevrons that light up one after the other
	for i = 1, 3 do
		local ch = make("TextLabel", { BackgroundTransparency = 1, Size = UDim2.fromScale(0.045, 0.14), Position = UDim2.fromScale(0.425 + (i - 1) * 0.04, 0.1), Font = Enum.Font.LuckiestGuy,
			TextScaled = true, Text = ">", TextColor3 = PINK, TextTransparency = 0.7, ZIndex = 3 }, ri)
		make("UIStroke", { Thickness = 3, Color = INKC, Transparency = 0.4 }, ch)
		task.delay((i - 1) * 0.2, function()
			TS:Create(ch, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, -1, true, 0.3), { TextTransparency = 0 }):Play()
		end)
	end
end
local function infoBox(x, bg)
	local b = make("Frame", { Size = UDim2.fromScale(0.41, 0.33), Position = UDim2.fromScale(x, 0.37), BackgroundColor3 = bg, BorderSizePixel = 0, ZIndex = 2 }, ri)
	corner(b, 0.12)
	outline(b, 3)
	return b
end
local getBox = infoBox(0.07, Color3.fromRGB(230, 250, 226))
ink(getBox, UDim2.fromScale(0.8, 0.2), UDim2.fromScale(0.07, 0.07), 40, "YOU GET", Color3.fromRGB(40, 170, 60), Enum.Font.LuckiestGuy)
local function getRow(y, iconName, label)
	icon(getBox, iconName, UDim2.fromScale(0.2, 0.24), UDim2.fromScale(0.06, y))
	ink(getBox, UDim2.fromScale(0.4, 0.2), UDim2.fromScale(0.21, y + 0.02), 34, label)
	return ink(getBox, UDim2.fromScale(0.36, 0.2), UDim2.fromScale(0.6, y + 0.02), 34, "", Color3.fromRGB(40, 170, 60), Enum.Font.LuckiestGuy, Enum.TextXAlignment.Right)
end
local rbCash = getRow(0.34, "coin", "Cash")
local rbTrain = getRow(0.64, "bolt", "Training")
local loseBox = infoBox(0.52, Color3.fromRGB(253, 236, 236))
ink(loseBox, UDim2.fromScale(0.8, 0.2), UDim2.fromScale(0.07, 0.07), 40, "YOU LOSE", Color3.fromRGB(220, 50, 60), Enum.Font.LuckiestGuy)
ink(loseBox, UDim2.fromScale(0.86, 0.15), UDim2.fromScale(0.07, 0.3), 30, "Cash  -  Speed  -  Training")
ink(loseBox, UDim2.fromScale(0.8, 0.16), UDim2.fromScale(0.07, 0.5), 34, "KEEP", Color3.fromRGB(40, 170, 60), Enum.Font.LuckiestGuy)
local keep = ink(loseBox, UDim2.fromScale(0.86, 0.26), UDim2.fromScale(0.07, 0.68), 26, "Pets - Basket - Luck - Index - Zones", SOFT)
keep.TextWrapped = true
local rbNeed = ink(ri, UDim2.fromScale(0.5, 0.06), UDim2.fromScale(0.07, 0.73), 32, "")
local rbProg = ink(ri, UDim2.fromScale(0.36, 0.06), UDim2.fromScale(0.57, 0.73), 32, "", RED, Enum.Font.LuckiestGuy, Enum.TextXAlignment.Right)
local _, rbFill = bar(ri, UDim2.fromScale(0.86, 0.045), UDim2.fromScale(0.07, 0.8), Color3.fromRGB(255, 150, 200), Color3.fromRGB(235, 60, 140))
local rbGo = bigButton(ri, GREEN, UDim2.fromScale(0.4, 0.13), UDim2.fromScale(0.3, 0.86))
rbGo.label.Text = "REBIRTH"

refreshRebirth = function()
	local n = attr("Rebirth", 0)
	local need = C.rebirthNeed(n)
	local speed = attr("Speed", 0)
	local ready = speed >= need
	rbNow.Text, rbNext.Text = tostring(n), tostring(n + 1)
	local m0, m1 = "x" .. C.rebirthMult(n), "x" .. C.rebirthMult(n + 1)
	rbCash.Text = m0 .. " > " .. m1
	rbTrain.Text = m0 .. " > " .. m1
	rbNeed.Text = "Needs SPEED " .. C.fmt(need)
	rbProg.Text = C.fmt(speed) .. " / " .. C.fmt(need)
	rbProg.TextColor3 = ready and Color3.fromRGB(40, 170, 60) or RED
	setBar(rbFill, speed / math.max(need, 1))
	rbGo.color(ready and GREEN or GREY)
end
rebirthBtn.Activated:Connect(function()
	refreshRebirth()
	rebirthPanel.toggle()
end)
UI.openRebirth = function()
	refreshRebirth()
	rebirthPanel.toggle()
end
rbGo.button.Activated:Connect(function()
	if attr("Speed", 0) >= C.rebirthNeed(attr("Rebirth", 0)) then
		Action:FireServer("rebirth")
		rebirthPanel.close()
	else
		showNote("Train more SPEED on your treadmill first", "bad")
	end
end)

UI.panel, UI.ink, UI.bar, UI.setBar, UI.bigButton, UI.outline, UI.rays, UI.circle, UI.setIcon = panel, ink, bar, setBar, bigButton, outline, rays, circle, setIcon
UI.DARK, UI.SOFT, UI.GREY, UI.GOLD, UI.PINK, UI.CREAM = DARK, SOFT, GREY, GOLD, PINK, CREAM

-- the ray fans turn
RunService.RenderStepped:Connect(function(dt)
	for r, speed in pairs(spinners) do
		if r.Parent then
			if r.Visible then
				r.Rotation = (r.Rotation + speed * dt) % 360
			end
		else
			spinners[r] = nil
		end
	end
end)
end

-- ------------------------------------------------------------ "your base" marker
local marker = make("BillboardGui", {
	-- v131: sized in studs (shrinks with distance) so it no longer sits on top of zone signs far away
	Name = "BaseMarker", Size = UDim2.new(16, 60, 4.2, 16), StudsOffsetWorldSpace = Vector3.new(0, 9, 0), AlwaysOnTop = true, MaxDistance = 3000, Enabled = false, ResetOnSpawn = false,
}, plr:WaitForChild("PlayerGui"))
local markerText = text(marker, UDim2.fromScale(1, 1), UDim2.fromScale(0, 0), 30, "YOUR BASE")
markerText.TextColor3 = Color3.fromRGB(120, 240, 120)

local function refreshMarker()
	local n = attr("Base", 0)
	local map = workspace:FindFirstChild("Map")
	local base = map and map:FindFirstChild("Base" .. n)
	local sign = base and base:FindFirstChild("OwnerSign", true)
	if sign then
		marker.Adornee = sign
		marker.Enabled = true
	end
end

-- ------------------------------------------------------------ numbers on the HUD
local lastSpeed, lastCash = nil, nil

local function floatText(str, col, from)
	local t = text(gui, UDim2.fromScale(0.14, 0.045), from, 28, str)
	t.TextColor3 = col
	t.TextXAlignment = Enum.TextXAlignment.Left
	local st = t:FindFirstChildOfClass("UIStroke")
	TweenService:Create(t, TweenInfo.new(0.8), { Position = from - UDim2.fromScale(0, 0.07), TextTransparency = 1 }):Play()
	TweenService:Create(st, TweenInfo.new(0.8), { Transparency = 1 }):Play()
	Debris:AddItem(t, 0.9)
end

local lastEggs = attr("Eggs", 0)

local function refresh()
	local cash, speed = attr("Cash", 0), attr("Speed", 0)
	local eggsNow = attr("Eggs", 0)
	if eggsNow > lastEggs then
		sfx("catch", 0.6, 1 + math.min(attr("Combo", 1), 20) * 0.03) -- egg caught: higher note with a bigger combo
	end
	lastEggs = eggsNow
	local carry, max = attr("Carry", 0), attr("CarryMax", 3)
	cashLabel.Text = "$" .. C.fmt(cash)
	local ic = indexCount()
	if indexSeen == nil then
		indexSeen = ic
	end
	indexBadge.Visible = ic > indexSeen
	speedLabel.Text = C.fmt(speed)
	drawBasket(carry, max)
	incomeLabel.Text = "+$" .. C.fmt(attr("Income", 0)) .. "/s"
	luckLabel.Text = "x" .. C.luck(attr("LuckLv", 0))

	if lastSpeed and speed > lastSpeed then
	end
	if lastCash and cash > lastCash then
		cashScale.Scale = 1.08
		TweenService:Create(cashScale, TweenInfo.new(0.2), { Scale = 1 }):Play()
	end
	lastSpeed, lastCash = speed, cash

	-- next zone bar
	local nextZone = attr("Unlocked", 1) ~= C.NZ and C.ZONES[attr("Unlocked", 1) + 1] or nil -- nil when every zone is bought (zone 11 is opened by the Golden Portal, not bought)
	-- the next locked gate shows how far this player is: "$380 / $1K" (green when they can buy it)
	local wantZone = attr("Unlocked", 1) + 1
	local gates = workspace:FindFirstChild("ZoneGates")
	for _, model in ipairs((gates and nextZone) and gates:GetChildren() or {}) do
		if model:GetAttribute("Zone") == wantZone then
			for _, o in ipairs(model:GetDescendants()) do
				if o:IsA("TextLabel") and o.Name == "Price" then
					o.Text = "$" .. C.fmt(cash) .. " / $" .. C.fmt(nextZone.price)
					o.TextColor3 = cash >= nextZone.price and Color3.fromRGB(120, 255, 120) or Color3.fromRGB(255, 222, 60)
				end
			end
		end
	end
	if nextZone then
		local frac = math.clamp(cash / nextZone.price, 0, 1)
		barFill.Size = UDim2.fromScale(frac, 1)
		barFill.Visible = frac > 0
		barText.Text = 'NEXT: <font color="#FFD23C">' .. nextZone.name .. "</font>   $" .. C.fmt(cash) .. " / $" .. C.fmt(nextZone.price)
	else
		barFill.Size = UDim2.fromScale(1, 1)
		barFill.Visible = true
		barText.Text = "ALL ZONES UNLOCKED"
	end

	-- what to do now
	local pets = attr("Pets", 0)
	local trainLv = attr("TrainLv", 0)
	-- the violet hint is only a short TUTORIAL: catch an egg -> bring it home -> train on the treadmill, then it is gone
	-- (old players: they already caught, have pets and speed, or did a rebirth -> never shown)
	if attr("Rebirth", 0) > 0 or (attr("Caught", 0) > 0 and pets > 0 and attr("Speed", 0) > 0) then
		hint.Text = ""
	elseif eggsNow > 0 and pets == 0 then
		hint.Text = "Open EGGS on the left and hatch your eggs!"
	elseif carry == 0 and pets == 0 then
		hint.Text = "Run into the zone and catch a falling egg!"
	elseif carry > 0 and pets == 0 then
		hint.Text = "Bring your pets to your base!"
	else
		hint.Text = "Step on your treadmill to get speed!"
	end
	markerText.Text = "YOUR BASE" -- no "BRING PETS HERE" (user)

	-- combo
	local cmb = attr("Combo", 0)
	if cmb >= 2 then
		comboText.Text = "x" .. cmb
		comboSub.Text = "+" .. math.floor((C.comboLuck(cmb) - 1) * 100 + 0.5) .. "%"
		combo.Visible = true
	else
		combo.Visible = false
	end

	-- prices on the upgrade prompts (changed only on this client)
	local lv = { train = trainLv, basket = attr("BasketLv", 0), luck = attr("LuckLv", 0) }
	for _, pp in ipairs(CS:GetTagged("UpgPrompt")) do
		local kind = pp:GetAttribute("Kind")
		if lv[kind] then
			if lv[kind] >= C.MAX_LV[kind] then
				pp.ObjectText = "MAX"
			else
				pp.ObjectText = "Lv " .. (lv[kind] + 1) .. "  -  $" .. C.fmt(C.cost(kind, lv[kind]))
			end
		end
	end
	if rebirthPanel.frame.Visible then
		refreshRebirth()
	end
end

-- ------------------------------------------------------------ zone gates (only on this player's screen)
-- The server builds Workspace > ZoneGates > Gate2..Gate10. Here the gates this player has bought are hidden:
-- no collision, invisible, price text off. Other players still see and hit their own locked gates.
local gateFolder = workspace:WaitForChild("ZoneGates")
local lastUnlocked = nil

local function applyGates(animate)
	local unlocked = attr("Unlocked", 1)
	for _, model in ipairs(gateFolder:GetChildren()) do
		local zi = model:GetAttribute("Zone")
		if zi and zi <= unlocked then
			for _, o in ipairs(model:GetDescendants()) do
				if o:IsA("BasePart") then
					o.CanCollide = false
					if animate and o.Transparency < 1 then
						-- just bought: the gate fades out (time = C.GATE.fade)
						TweenService:Create(o, TweenInfo.new(C.GATE.fade, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Transparency = 1 }):Play()
					else
						o.Transparency = 1
					end
				elseif o:IsA("SurfaceGui") then
					o.Enabled = false
				end
			end
		end
	end
end

-- fireworks around you when you open a new zone: rockets fly up from around the player and burst into coloured sparks
local FW_COLS = { Color3.fromRGB(255, 70, 90), Color3.fromRGB(255, 210, 60), Color3.fromRGB(80, 220, 255), Color3.fromRGB(120, 255, 120), Color3.fromRGB(200, 120, 255), Color3.fromRGB(255, 150, 40) }
local function fireworks(count)
	local ch = plr.Character
	local hrp = ch and ch:FindFirstChild("HumanoidRootPart")
	if not hrp then
		return
	end
	local origin = hrp.Position
	for i = 1, count or 10 do
		task.delay((i - 1) * 0.28 + math.random() * 0.15, function()
			local col = FW_COLS[math.random(#FW_COLS)]
			local a = math.random() * math.pi * 2
			local start = origin + Vector3.new(math.cos(a) * (5 + math.random() * 5), -2, math.sin(a) * (5 + math.random() * 5))
			local top = start + Vector3.new(math.random(-6, 6), 26 + math.random() * 16, math.random(-6, 6))
			local rocket = make("Part", {
				Name = "Firework", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, CastShadow = false,
				Size = Vector3.new(0.5, 0.5, 0.5), Shape = Enum.PartType.Ball, Material = Enum.Material.Neon, Color = col, CFrame = CFrame.new(start),
			}, workspace)
			local trail = make("ParticleEmitter", {
				Color = ColorSequence.new(Color3.fromRGB(255, 240, 200), col), LightEmission = 1, Rate = 60, Lifetime = NumberRange.new(0.3, 0.5),
				Speed = NumberRange.new(1, 3), SpreadAngle = Vector2.new(15, 15), Acceleration = Vector3.new(0, -8, 0),
				Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 0) }),
				Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 1) }),
			}, rocket)
			local fly = 0.8 + math.random() * 0.4
			TweenService:Create(rocket, TweenInfo.new(fly, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = CFrame.new(top) }):Play()
			task.delay(fly, function()
				trail.Enabled = false
				rocket.Transparency = 1
				local burst = make("ParticleEmitter", {
					Color = ColorSequence.new(col, Color3.new(1, 1, 1)), LightEmission = 1, Rate = 0, Lifetime = NumberRange.new(1.0, 1.7),
					Speed = NumberRange.new(22, 34), SpreadAngle = Vector2.new(180, 180), Drag = 2.6, Acceleration = Vector3.new(0, -9, 0),
					Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.7), NumberSequenceKeypoint.new(0.7, 0.45), NumberSequenceKeypoint.new(1, 0) }),
					Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.75, 0.2), NumberSequenceKeypoint.new(1, 1) }),
				}, rocket)
				burst:Emit(90)
				local glow = make("PointLight", { Color = col, Brightness = 6, Range = 30 }, rocket)
				TweenService:Create(glow, TweenInfo.new(0.7), { Brightness = 0 }):Play()
				sfx("egg_pop", 0.35, 0.55 + math.random() * 0.25, rocket)
				Debris:AddItem(rocket, 2.5)
			end)
		end)
	end
end

local function onUnlocked()
	local unlocked = attr("Unlocked", 1)
	local bought = lastUnlocked ~= nil and unlocked > lastUnlocked -- false on the first load
	lastUnlocked = unlocked
	applyGates(bought)
	if bought then
		local zone = C.ZONES[unlocked]
		playZone()
		fireworks(12)
		local ban = make("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.3), Size = UDim2.fromScale(0.7, 0.24), ZIndex = 25 }, gui)
		local bs = make("UIScale", { Scale = 0.2 }, ban)
		local r = rays(ban, 16, Color3.fromRGB(255, 236, 140), 0.55)
		r.Size = UDim2.fromScale(0.9, 2.6)
		r.ZIndex = 25
		local t1 = make("TextLabel", {
			BackgroundTransparency = 1, Size = UDim2.fromScale(1, 0.62), Font = Enum.Font.LuckiestGuy, TextScaled = true, Text = "NEW ZONE UNLOCKED!",
			TextColor3 = WHITE, ZIndex = 26,
		}, ban)
		make("UIStroke", { Thickness = 6, Color = Color3.fromRGB(18, 10, 28) }, t1)
		make("UIGradient", { Rotation = 90, Color = ColorSequence.new(Color3.fromRGB(255, 246, 160), Color3.fromRGB(255, 150, 20)) }, t1)
		local t2 = make("TextLabel", {
			BackgroundTransparency = 1, Size = UDim2.fromScale(1, 0.34), Position = UDim2.fromScale(0, 0.64), Font = Enum.Font.FredokaOne, TextScaled = true,
			Text = zone.name, TextColor3 = WHITE, ZIndex = 26,
		}, ban)
		make("UIStroke", { Thickness = 5, Color = Color3.fromRGB(18, 10, 28) }, t2)
		TweenService:Create(bs, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
		if UI.confetti then
			UI.confetti(60)
		end
		task.delay(2.8, function()
			local out = TweenService:Create(bs, TweenInfo.new(0.25, Enum.EasingStyle.Back, Enum.EasingDirection.In), { Scale = 0 })
			out:Play()
			out.Completed:Wait()
			ban:Destroy()
		end)
		flash.BackgroundColor3 = Color3.fromRGB(zone.eggCol[1], zone.eggCol[2], zone.eggCol[3])
		flash.BackgroundTransparency = 0.4
		TweenService:Create(flash, TweenInfo.new(0.8), { BackgroundTransparency = 1 }):Play()
	end
end
gateFolder.DescendantAdded:Connect(function()
	applyGates(false)
end)
if plr:GetAttribute("Unlocked") then
	onUnlocked()
end

plr.AttributeChanged:Connect(function(name)
	if name == "Index" then
		refreshIndex()
	elseif name == "Unlocked" then
		onUnlocked()
		refresh()
	elseif name == "Base" then
		refreshMarker()
	elseif name == "Combo" then
		if attr("Combo", 0) >= 2 then
			comboUntil = os.clock() + C.COMBO_TIME
			comboScale.Scale = 1.25
			TweenService:Create(comboScale, TweenInfo.new(0.2, Enum.EasingStyle.Back), { Scale = 1 }):Play()
		end
		refresh()
	else
		refresh()
	end
end)
CS:GetInstanceAddedSignal("UpgPrompt"):Connect(refresh)
refresh()
refreshIndex()
refreshMarker()

-- ------------------------------------------------------------ storm: banner + dark sky
local stormOn = false
local cc = Lighting:FindFirstChildOfClass("ColorCorrectionEffect")
local ccTint, ccBright = cc and cc.TintColor, cc and cc.Brightness
task.spawn(function()
	while true do
		local now = workspace:GetServerTimeNow()
		local endAt = workspace:GetAttribute("StormEnd") or 0
		local nextAt = workspace:GetAttribute("StormNext") or 0
		local on = endAt > now
		if on then
			stormBanner.Visible = true
			stormLabel.Text = "STORM x" .. C.STORM_LUCK .. " LUCK"
			stormTimer.Text = C.clock(endAt - now)
			stormGrad.Color = faceSeq(Color3.fromRGB(170, 90, 250))
		elseif nextAt > now and nextAt - now <= C.STORM_SHOW then
			stormBanner.Visible = true
			stormLabel.Text = "EGG STORM"
			stormTimer.Text = C.clock(nextAt - now)
			stormGrad.Color = STORM_SEQ
		else
			stormBanner.Visible = false
		end
		if on ~= stormOn then
			stormOn = on
			if on then
				play("thunder", 0.7, 0.5)
				flash.BackgroundColor3 = WHITE
				flash.BackgroundTransparency = 0.3
				TweenService:Create(flash, TweenInfo.new(0.5), { BackgroundTransparency = 1 }):Play()
			end
			if cc then
				TweenService:Create(cc, TweenInfo.new(1.5), {
					TintColor = on and Color3.fromRGB(176, 166, 222) or ccTint,
					Brightness = on and -0.05 or ccBright,
				}):Play()
			end
		end
		task.wait(0.25)
	end
end)

-- ------------------------------------------------------------ pets in the pens: hop, rainbow colours
local penPets = {}
local function addPenPet(model)
	task.delay(0.5, function()
		if not model.Parent or not model.PrimaryPart then
			return
		end
		local bodies = {}
		if model:GetAttribute("Tier") == 3 then
			for _, p in ipairs(model:GetChildren()) do
				if p.Name == "Body" then
					table.insert(bodies, p)
				end
			end
		end
		local cf = model:GetPivot()
		penPets[model] = {
			cf = cf, phase = model:GetAttribute("Phase") or 0, bodies = bodies,
			-- v143: walking around the pen (pos on the floor, facing yaw, a target, idle time left)
			penC = model:GetAttribute("PenC"), lift = model:GetAttribute("Lift") or 2, penSize = model:GetAttribute("PenSize"),
			pos = cf.Position, yaw = math.atan2(-cf.LookVector.X, -cf.LookVector.Z),
			target = nil, wait = 1 + (model:GetAttribute("Phase") or 0) % 3, walkT = 0, last = os.clock(),
		}
	end)
end
for _, m in ipairs(CS:GetTagged("PenPet")) do
	addPenPet(m)
end
CS:GetInstanceAddedSignal("PenPet"):Connect(addPenPet)
CS:GetInstanceRemovedSignal("PenPet"):Connect(function(m)
	penPets[m] = nil
end)

-- v143 (user): pets walk around their pen instead of playing an animation on one spot.
-- Pen = PenFloor 34 x 52 (front = +Z towards the plaza); the treadmill stands in the front left corner.
local penWalk -- one main-chunk local only (the chunk is near the 200-local limit)
do
local PEN_HX, PEN_ZB, PEN_ZF, TREAD_X, TREAD_Z = 12.5, -20, 21, -4.5, 6.5
local function penSize(size) -- v156: the wander area follows the pen floor (pens are 48 x 60 now)
	PEN_HX, PEN_ZB, PEN_ZF = size.X / 2 - 5, -size.Z / 2 + 7, size.Z / 2 - 5
	TREAD_X, TREAD_Z = -size.X / 2 + 13, size.Z / 2 - 19.5
end
local function penFree(lx, lz)
	return not (lx < TREAD_X and lz > TREAD_Z) -- the treadmill corner
end
local function penTarget(info)
	local c = info.penC
	if info.penSize then
		penSize(info.penSize)
	end
	for _ = 1, 12 do
		local lx, lz = (math.random() * 2 - 1) * PEN_HX, PEN_ZB + math.random() * (PEN_ZF - PEN_ZB)
		local p = Vector3.new(c.X + lx, info.pos.Y, c.Z + lz)
		local ok = penFree(lx, lz) and (p - info.pos).Magnitude > 6
		-- the straight path must not cut through the treadmill corner either
		for a = 0.25, 0.75, 0.25 do
			local q = info.pos:Lerp(p, a)
			ok = ok and penFree(q.X - c.X, q.Z - c.Z)
		end
		-- keep a little space from where the other pets are going
		if ok then
			for m2, o in pairs(penPets) do
				if o ~= info and o.penC == c and (o.target or o.pos) and ((o.target or o.pos) - p).Magnitude < 5 then
					ok = false
					break
				end
			end
		end
		if ok then
			return p
		end
	end
	return nil
end
penWalk = function(model, info, now)
	local dt = math.min(now - info.last, 0.1)
	info.last = now
	if info.target then
		local d = info.target - info.pos
		local dist = Vector3.new(d.X, 0, d.Z).Magnitude
		if dist < 0.6 then
			info.target = nil
			info.wait = 2 + math.random() * 4
		else
			local want = math.atan2(-d.X, -d.Z)
			local diff = (want - info.yaw + math.pi) % (2 * math.pi) - math.pi
			info.yaw = info.yaw + math.clamp(diff, -dt * 4, dt * 4)
			local speed = (math.abs(diff) > 1.2 and 1.2 or 5) * math.clamp(info.lift / 2.5, 0.8, 1.6)
			local step = math.min(dist, speed * dt)
			info.pos = info.pos + Vector3.new(d.X, 0, d.Z).Unit * step
			info.walkT = info.walkT + dt * speed / 5
		end
	else
		info.wait = info.wait - dt
		if info.wait <= 0 then
			info.target = info.penC and penTarget(info)
			if not info.target then
				info.wait = 1.5
			end
		end
	end
	return CFrame.new(info.pos) * CFrame.Angles(0, info.yaw, 0), info.target ~= nil
end
end

-- ------------------------------------------------------------ eggs
local PROF = { 0.62, 0.92, 1.0, 0.84, 0.52 }
local EGG_W, LAYER = 3.4, 0.8
local eggs = {}

local function rgb(t)
	return Color3.fromRGB(t[1], t[2], t[3])
end

-- egg model made in Blender (ReplicatedStorage.Assets). Returns nil when the models are not imported yet -> block egg.
local EGG_H = LAYER * #PROF
local function eggMesh(zoneIndex, kind)
	local name = (kind == "golden" and "Egg_Gold") or (kind == "rotten" and "Egg_Rotten") or (kind == "storm" and "Egg_Storm") or ("Egg_" .. zoneIndex)
	local src = C.meshOf(name)
	if not src then
		return nil
	end
	local p = src:Clone()
	p.Name = "EggMesh"
	p.Anchored = true
	p.CanCollide = false
	p.CanTouch = false
	p.CanQuery = false
	p.CastShadow = false
	p.Color = Color3.new(1, 1, 1)
	p.Material = Enum.Material.SmoothPlastic
	local rot = src.CFrame.Rotation
	local unit = p.Size * (EGG_H / math.max(math.abs(rot:VectorToWorldSpace(p.Size).Y), 0.01)) -- size of a normal egg
	p.Size = unit
	p.CFrame = CFrame.new(0, -500, 0)
	p.Parent = workspace
	return p, unit, rot
end

local function makeEgg(id, x, z, y0, gy, fall, zoneIndex, kind, linger)
	local zone = C.ZONES[zoneIndex]
	local col, spot, scale, neon, beamCol = rgb(zone.eggCol), rgb(zone.eggSpot), 1, false, nil
	local shadowCol = Color3.new(0, 0, 0)
	if kind == "golden" then
		col, spot, neon, beamCol = Color3.fromRGB(255, 204, 40), Color3.fromRGB(255, 244, 180), true, Color3.fromRGB(255, 222, 80)
	elseif kind == "rotten" then
		col, spot, shadowCol = Color3.fromRGB(120, 170, 60), Color3.fromRGB(70, 100, 40), Color3.fromRGB(40, 110, 20)
	elseif kind == "storm" then
		col, spot, neon, beamCol, scale = PURPLE, Color3.fromRGB(255, 240, 150), true, Color3.fromRGB(190, 130, 255), 2.4
	end
	local layers = {}
	local mesh, unit, meshRot = eggMesh(zoneIndex, kind)
	if mesh then
		mesh.Size = unit * scale
	end
	for i, k in ipairs(mesh and {} or PROF) do
		local p = fxPart(Vector3.new(EGG_W * k, LAYER, EGG_W * k) * scale, CFrame.new(x, y0, z), (i == 3) and spot or col)
		if neon then
			p.Material = Enum.Material.Neon
		end
		layers[i] = p
	end
	local shadow = fxPart(Vector3.new(0.15, 9 * scale, 9 * scale), CFrame.new(x, gy + 0.12, z) * CFrame.Angles(0, 0, math.rad(90)), shadowCol, Enum.PartType.Cylinder)
	shadow.Transparency = 0.6
	-- light from the egg down to the ground: white for normal eggs, coloured and thicker for the special ones
	local beamW = beamCol and 1.3 * scale or 0.7
	if kind == "rotten" then
		beamCol = Color3.fromRGB(190, 235, 150)
	end
	local beam = fxPart(Vector3.new(beamW, y0 - gy, beamW), CFrame.new(x, (y0 + gy) / 2, z), beamCol or WHITE)
	beam.Material = Enum.Material.Neon
	beam.Transparency = (kind == "golden" or kind == "storm") and 0.55 or 0.72
	eggs[id] = {
		x = x, z = z, y0 = y0, gy = gy, fall = fall, linger = linger or 0, t0 = os.clock(), kind = kind, scale = scale,
		layers = layers, shadow = shadow, beam = beam, beamW = beamW, col = col, sent = false,
		mesh = mesh, meshRot = meshRot,
	}
end

local function removeEgg(id)
	local e = eggs[id]
	if not e then
		return nil
	end
	eggs[id] = nil
	for _, p in ipairs(e.layers) do
		p:Destroy()
	end
	if e.mesh then
		e.mesh:Destroy()
	end
	e.shadow:Destroy()
	if e.beam then
		e.beam:Destroy()
	end
	return e
end

local function nearMe(x, z, range)
	local char = plr.Character
	local hrp = char and char:FindFirstChild("HumanoidRootPart")
	if not hrp then
		return false
	end
	local dx, dz = hrp.Position.X - x, hrp.Position.Z - z
	return dx * dx + dz * dz < range * range
end

local function breakEgg(e)
	-- quick burst, nothing stays on the ground: a ring of light, shell pieces and yolk drops that fly up and fade
	if not nearMe(e.x, e.z, 220) then
		return
	end
	local base = Vector3.new(e.x, e.gy, e.z)
	local s = e.scale
	local rotten = e.kind == "rotten"
	local ring = fxPart(Vector3.new(0.2, 2 * s, 2 * s), CFrame.new(base + Vector3.new(0, 0.15, 0)) * CFrame.Angles(0, 0, math.rad(90)),
		rotten and Color3.fromRGB(190, 235, 150) or WHITE, Enum.PartType.Cylinder)
	ring.Material = Enum.Material.Neon
	ring.Transparency = 0.25
	fade(ring, 0.35, { Size = Vector3.new(0.2, 11 * s, 11 * s) })
	local function fly(size, col, speed, up, time)
		local a = math.random() * math.pi * 2
		local p = fxPart(size, CFrame.new(base + Vector3.new(0, 0.8 * s, 0)) * CFrame.Angles(a, a * 2, a), col)
		p.Anchored = false
		p.AssemblyLinearVelocity = Vector3.new(math.cos(a) * speed, up, math.sin(a) * speed)
		p.AssemblyAngularVelocity = Vector3.new(math.random(-12, 12), math.random(-12, 12), math.random(-12, 12))
		fade(p, time, { Size = size * 0.3 })
	end
	local yolk = rotten and Color3.fromRGB(110, 150, 50) or Color3.fromRGB(255, 200, 50)
	for i = 1, 9 do
		fly(Vector3.new(1, 0.45, 1) * s * (0.7 + math.random() * 0.6), (i % 3 == 0) and WHITE or e.col, (9 + math.random() * 9) * s, 24 + math.random() * 16, 0.75)
	end
	for _ = 1, 5 do
		fly(Vector3.new(0.55, 0.55, 0.55) * s, yolk, (4 + math.random() * 6) * s, 30 + math.random() * 14, 0.6)
	end
end

local function popEgg(e, y, rotten)
	for i = 1, 8 do
		local a = i / 8 * math.pi * 2
		local star = fxPart(Vector3.new(0.6, 0.6, 0.6) * e.scale, CFrame.new(e.x, y, e.z), rotten and Color3.fromRGB(120, 170, 60) or Color3.fromRGB(255, 240, 150))
		star.Material = Enum.Material.Neon
		fade(star, 0.45, { Position = Vector3.new(e.x + math.cos(a) * 4 * e.scale, y + 2.5, e.z + math.sin(a) * 4 * e.scale) })
	end
end

-- ------------------------------------------------------------ HATCH SHOW (in-world, v83)
-- Same show as the approved preview (blender/hatch_ref.py -> Desktop\RAINING EGGS NOU\hatch_ca_in_clip.mp4):
-- the camera flies to a hidden night-castle stage far away; the caught egg (its own zone design) floats in gold
-- claws over a stand; the scene climbs through the rarity colours up to the real one (every step: colour light,
-- name on the stand, level-up sound, a new glowing crack on the shell + the game's crack sound, the egg jolts);
-- Epic = light petals, Legendary = gold spike crown + turning square; the egg turns white -> POP (white flash,
-- star burst, rays, shards). Common..Epic: the pet is shown on the stand. Legendary (and the ??? step, F6 test):
-- the flash opens on a cathedral (rose window, candles, god rays) and the pet rises on the altar.
-- Tap / click during a show = the rest plays 3x faster. All client-side; every part a show creates lives in ONE
-- folder that is destroyed at the end AND on error; lighting / camera / HUD are always restored.
-- (wrapped in a function: the main chunk is close to Luau's 200-locals limit)
;(function()
local STAGE = Vector3.zero -- the show is drawn inside a full-screen ViewportFrame (its own little world)
local CATH = STAGE -- (cathedral reveal removed in v84: user wants only the effects, no castle)
local EGG_RX, EGG_RY = 1.45, 2.05 -- egg half width / height on the stage
local STAND_TOP = 3.4
local EC = Vector3.new(0, STAND_TOP + 0.4 + EGG_RY, 0) -- egg centre (relative to STAGE)
local ALTAR_TOP = 2.4
local ECP = Vector3.new(0, ALTAR_TOP + 1.1 + 2.4, 4.5) -- burst centre on the altar (relative to CATH)
local RCOL = { -- step colours (bright versions of the rarity colours)
	Color3.fromRGB(240, 242, 255), Color3.fromRGB(80, 255, 120), Color3.fromRGB(40, 200, 255), Color3.fromRGB(200, 60, 255), Color3.fromRGB(255, 190, 20),
}
local RNAME = { "COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY", "???" }
local SECRET_ODDS = 600000000
-- seconds per rarity step, by the pet's rarity (rarer = slower, bigger show); [6] = the ??? step
local STEP_T = { 0.85, 0.9, 1.1, 1.35, 1.6 }
local SECRET_T = 3.2
local HOLD = { 1.4, 1.6, 2.0, 2.5, 3.2, 3.6 }
local GOLD = Color3.fromRGB(230, 170, 50)
local WARM = Color3.fromRGB(255, 205, 60)

local function clamp(x, a, b)
	return math.max(a or 0, math.min(b or 1, x))
end
local function eo(u) -- ease out cubic
	u = clamp(u)
	return 1 - (1 - u) ^ 3
end
local function backOut(u)
	u = clamp(u) - 1
	return u * u * (2.7 * u + 1.7) + 1
end
local function P(class, props, parent)
	props.Anchored = true
	props.CanCollide = false
	props.CanQuery = false
	props.CanTouch = false
	props.CastShadow = false
	if props.Material == nil then
		props.Material = Enum.Material.SmoothPlastic
	end
	return make(class, props, parent)
end
local function neonPart(parent, size)
	return P("Part", { Material = Enum.Material.Neon, Size = size or Vector3.new(1, 1, 1), Transparency = 1, CFrame = CFrame.new(STAGE - Vector3.new(0, 200, 0)) }, parent)
end
local function setN(p, col, alpha) -- colour + visibility of a neon part (alpha 0 = hidden)
	p.Color = col
	p.Transparency = 1 - clamp(alpha)
end
local function bar(p, a, b, w) -- stretch a part from a to b
	p.Size = Vector3.new(w, w, math.max((b - a).Magnitude + w * 0.6, 0.05))
	p.CFrame = CFrame.lookAt((a + b) / 2, b)
end
local function cylAt(parent, pos, diam, h, col, mat) -- upright cylinder
	return P("Part", { Shape = Enum.PartType.Cylinder, Size = Vector3.new(h, diam, diam), CFrame = CFrame.new(pos) * CFrame.Angles(0, 0, math.pi / 2), Color = col, Material = mat }, parent)
end
local function boxAt(parent, cf, size, col, mat)
	return P("Part", { Size = size, CFrame = cf, Color = col, Material = mat }, parent)
end
local function ellipsoid(parent, scale) -- neon ellipsoid (petals, the white shell)
	local p = neonPart(parent, Vector3.new(1, 1, 1))
	make("SpecialMesh", { MeshType = Enum.MeshType.Sphere, Scale = scale }, p)
	return p
end
-- a flat triangle spike in the screen plane = two mirrored wedges
local function makeSpike(parent)
	local a = P("WedgePart", { Material = Enum.Material.Neon, Transparency = 1, Size = Vector3.new(0.1, 1, 0.3) }, parent)
	local b = P("WedgePart", { Material = Enum.Material.Neon, Transparency = 1, Size = Vector3.new(0.1, 1, 0.3) }, parent)
	return { a, b }
end
local function placeSpike(sp, base, dir, len, w, col, alpha) -- base point, unit direction (in the XY plane)
	local p = Vector3.new(-dir.Y, dir.X, 0)
	for i, wd in ipairs(sp) do
		local side = (i == 1) and p or -p
		local x = dir:Cross(side)
		wd.Size = Vector3.new(0.08, math.max(len, 0.05), math.max(w / 2, 0.02))
		wd.CFrame = CFrame.fromMatrix(base + dir * len / 2 - side * w / 4, x, dir)
		setN(wd, col, alpha)
	end
end

-- ---------------------------------------------------------------- the stages (built once, kept hidden far away)
local S = nil
local showGui -- (created below)
local function buildStages()
	if S then
		return S
	end
	S = {}
	S.backdrop = make("Frame", { Size = UDim2.fromScale(1, 1), BackgroundColor3 = Color3.fromRGB(8, 4, 20), BackgroundTransparency = 1, BorderSizePixel = 0, ZIndex = 1 }, showGui)
	S.vp = make("ViewportFrame", {
		Size = UDim2.fromScale(1, 1), BackgroundTransparency = 1, ZIndex = 2,
		Ambient = Color3.fromRGB(125, 120, 150), LightColor = Color3.fromRGB(225, 220, 235), LightDirection = Vector3.new(0.4, -1, 0.8),
	}, showGui)
	S.vcam = make("Camera", { FieldOfView = 34 }, S.vp)
	S.vp.CurrentCamera = S.vcam
	local f = S.vp
	-- simple stand: soft disc + thin glowing ring + four gold claws holding the egg
	cylAt(f, Vector3.new(0, STAND_TOP - 1.35, 0), 5.2, 0.5, Color3.fromRGB(150, 138, 200))
	S.standGlow = cylAt(f, Vector3.new(0, STAND_TOP - 1.08, 0), 5.6, 0.08, WHITE, Enum.Material.Neon)
	S.claws = {}
	for k = 0, 3 do
		local a = k * math.pi / 2 + math.pi / 4
		local pos = Vector3.new(math.cos(a) * 1.25, STAND_TOP + 0.1, math.sin(a) * 1.25)
		S.claws[k + 1] = boxAt(f, CFrame.new(pos) * CFrame.fromAxisAngle(Vector3.new(math.sin(a), 0, -math.cos(a)), -0.3), Vector3.new(0.2, 2.4, 0.2), GOLD, Enum.Material.Metal)
	end
	-- little sparkles that twinkle round the egg
	S.spark = {}
	local rnd = Random.new(7)
	for i = 1, 30 do
		local p = neonPart(f, Vector3.new(0.12, 0.12, 0.12))
		S.spark[i] = { p = p, x = rnd:NextNumber(-11, 11), y = rnd:NextNumber(0, 12), z = rnd:NextNumber(-3, 4), ph = rnd:NextNumber(0, 9), sp = rnd:NextNumber(0.3, 1) }
	end
	-- "RARITY / <NAME>" under the egg (on the screen)
	S.signSmall = make("TextLabel", {
		BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.835), Size = UDim2.fromScale(0.3, 0.03),
		Font = Enum.Font.Garamond, TextScaled = true, Text = "RARITY", TextColor3 = Color3.fromRGB(220, 220, 230), Visible = false, ZIndex = 4,
	}, showGui)
	S.signBig = make("TextLabel", {
		BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.885), Size = UDim2.fromScale(0.6, 0.07),
		Font = Enum.Font.Garamond, TextScaled = true, Text = "", TextColor3 = WHITE, ZIndex = 4,
	}, showGui)
	make("UIStroke", { Thickness = 2, Color = Color3.new(0, 0, 0), Transparency = 0.3 }, S.signBig)
	S.signScale = make("UIScale", {}, S.signBig)
	return S
end

-- ---------------------------------------------------------------- screen layer (flash, counter, name)
showGui = make("ScreenGui", { Name = "HatchShow", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 60, Enabled = false }, plr:WaitForChild("PlayerGui"))
local flash = make("Frame", { Size = UDim2.fromScale(1, 1), BackgroundColor3 = WHITE, BackgroundTransparency = 1, BorderSizePixel = 0, ZIndex = 5 }, showGui)
local function serif(y, h, col)
	local t = make("TextLabel", {
		BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, y), Size = UDim2.fromScale(0.9, h),
		Font = Enum.Font.Garamond, TextScaled = true, TextColor3 = col or WHITE, Text = "", ZIndex = 6, TextTransparency = 1,
	}, showGui)
	make("UIStroke", { Thickness = 3, Color = Color3.fromRGB(30, 16, 0), Transparency = 1 }, t)
	return t, make("UIScale", {}, t)
end
local counter, counterScale = serif(0.1, 0.09)
local petNameL, nameScale = serif(0.8, 0.1, Color3.fromRGB(255, 226, 140))
local oddsL = serif(0.89, 0.055, Color3.fromRGB(255, 244, 210))
make("UIGradient", { Rotation = 90, Color = ColorSequence.new(Color3.fromRGB(255, 250, 220), Color3.fromRGB(235, 165, 40)) }, petNameL)
local skipHint = make("TextLabel", {
	BackgroundTransparency = 1, AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -16, 1, -12), Size = UDim2.fromOffset(220, 26),
	Font = Enum.Font.GothamBold, TextScaled = true, TextColor3 = WHITE, TextTransparency = 0.5, Text = "TAP TO SPEED UP", ZIndex = 6, TextXAlignment = Enum.TextXAlignment.Right,
}, showGui)
local function setText(t, txt, alpha)
	t.Text = txt
	t.TextTransparency = 1 - clamp(alpha)
	local st = t:FindFirstChildOfClass("UIStroke")
	if st then
		st.Transparency = 1 - clamp(alpha) * 0.8
	end
end

-- new effect sounds (audio/hatchfx, one sheet). While the sheet is not uploaded (id 0) the old sounds are used.
local HFX_ID = "rbxassetid://140444619596476" -- hatch sounds v2 (audio/gen_hatchfx2.py)
local HFX = { -- start, length in the sheet (written by audio/gen_hatchfx2.py)
	appear = { 0.0, 0.88 }, step_1 = { 1.28, 0.68 }, step_2 = { 2.36, 0.8 }, step_3 = { 3.56, 0.88 }, step_4 = { 4.84, 1.08 }, step_5 = { 6.32, 1.36 }, zap = { 8.08, 0.6 }, riser = { 9.08, 1.6 }, burst = { 11.08, 2.0 }, reveal = { 13.48, 1.76 }, legend = { 15.64, 3.0 },
}
local HFX_OLD = { appear = "egg_pop", zap = nil, legend = "fanfare", step_1 = "egg_wobble", step_2 = "reveal_common", step_3 = "reveal_rare", step_4 = "reveal_rare", step_5 = "reveal_legend", shing = "egg_pop", riser = nil, burst = "egg_pop", reveal = "fanfare" }
local hfxBase = make("Sound", { Name = "HatchFX_Sheet", SoundId = HFX_ID, Volume = 0 }, SoundService)
if HFX_ID ~= "rbxassetid://0" then
	task.spawn(function()
		pcall(function()
			game:GetService("ContentProvider"):PreloadAsync({ hfxBase })
		end)
	end)
end
local function hfx(name, volume, pitch)
	local r = HFX[name]
	if HFX_ID == "rbxassetid://0" or not hfxBase.IsLoaded or not r then
		local old = HFX_OLD[name]
		if old then
			sfx(old, volume, pitch)
		end
		return
	end
	local s = hfxBase:Clone()
	s.Volume = volume or 0.7
	s.PlaybackSpeed = pitch or 1
	s.Parent = SoundService
	s.TimePosition = r[1]
	s:Play()
	task.delay(r[2] / (pitch or 1) + 0.05, function()
		s:Destroy()
	end)
end

-- ---------------------------------------------------------------- world state saved during a show
local saved = nil
local function enterShow()
	saved = { guis = {} }
	for _, g in ipairs(plr.PlayerGui:GetChildren()) do
		if g:IsA("ScreenGui") and g ~= showGui and g.Enabled then
			g.Enabled = false
			table.insert(saved.guis, g)
		end
	end
	S.vp.ImageTransparency = 0
	S.backdrop.BackgroundTransparency = 1
	showGui.Enabled = true
end
local function leaveShow()
	if not saved then
		return
	end
	for _, g in ipairs(saved.guis) do
		if g.Parent then
			g.Enabled = true
		end
	end
	showGui.Enabled = false
	flash.BackgroundTransparency = 1
	setText(counter, "", 0)
	setText(petNameL, "", 0)
	setText(oddsL, "", 0)
	if S then
		S.signBig.Text = ""
		S.signSmall.Visible = false
		S.backdrop.BackgroundTransparency = 1
	end
	saved = nil
end

-- ---------------------------------------------------------------- one show
local running = nil -- the show being played (render loop reads it)
local speedUp = 1

local function crackNetwork(events, rx)
	local rnd = Random.new(11)
	local segs, ends = {}, {}
	local function surf(u, v)
		local c = math.sqrt(math.max(1 - v * v, 0))
		return Vector3.new(math.sin(u) * rx * c, v * EGG_RY, -math.cos(u) * rx * c)
	end
	for i, ev in ipairs(events) do
		local size = ev[2]
		local u, v
		if #ends > 0 and rnd:NextNumber() < 0.5 then
			local e = ends[rnd:NextInteger(1, #ends)]
			u, v = e[1], e[2]
		else
			u, v = rnd:NextNumber(-1, 1), rnd:NextNumber(-0.7, 0.75)
		end
		for _ = 1, (size >= 3) and 2 or 1 do
			local uu, vv = u, v
			local d = (rnd:NextNumber() < 0.5) and -1 or 1
			for k = 0, 1 + size do
				local u2 = clamp(uu + d * rnd:NextNumber(0.12, 0.3), -1.35, 1.35)
				local v2 = clamp(vv + rnd:NextNumber(-0.28, 0.28), -0.92, 0.92)
				table.insert(segs, { ev = i, p = surf(uu, vv), q = surf(u2, v2), order = k })
				uu, vv = u2, v2
				if rnd:NextNumber() < 0.3 then
					d = -d
				end
			end
			table.insert(ends, { uu, vv })
		end
	end
	return segs
end

local function runShow(job)
	local pet, kind = job.pet, job.kind
	local R = job.secret and 6 or pet.i -- how far the climb goes (6 = the ??? step)
	local k = (job.fast and 0.6 or 1) * ((UI.hasPass and UI.hasPass("fast")) and 0.5 or 1)
	speedUp = 1
	local st = buildStages()
	-- timeline (seconds of show time; real time = show time * k / speedUp)
	local step = STEP_T[math.min(R, 5)]
	local starts, t = {}, 0.9
	for L = 1, R do
		starts[L] = t
		t = t + ((L == 6) and SECRET_T or step)
	end
	local tEnd = t
	local CHARGE = 0.45 + (R >= 4 and 0.2 or 0)
	local WHITE_T = (R >= 4) and 0.6 or 0.35
	local T_POP = tEnd + CHARGE + WHITE_T
	local cath = false
	local T_END = T_POP + (cath and 0.3 or 0) + HOLD[R] + 0.35
	-- crack events: (time, size); big one at every step, small ones between, fast ones in the charge
	local events = {}
	for L = 1, R do
		local d = (L == 6) and SECRET_T or step
		table.insert(events, { starts[L] + 0.02, math.min(L, 5) })
		if L < 6 then
			if R >= 3 then
				table.insert(events, { starts[L] + d * 0.55, 1 })
			end
			if L >= 3 then
				table.insert(events, { starts[L] + d * 0.82, 2 })
			end
		else
			for i, fr in ipairs({ 0.3, 0.5, 0.68, 0.82, 0.93 }) do
				table.insert(events, { starts[L] + d * fr, 1 + math.min(i, 4) })
			end
		end
	end
	table.insert(events, { tEnd, 3 })
	table.insert(events, { tEnd + CHARGE * 0.5, 4 })
	table.insert(events, { tEnd + CHARGE + WHITE_T * 0.5, math.min(R + 1, 5) })
	table.sort(events, function(a, b)
		return a[1] < b[1]
	end)

	local run = make("Folder", { Name = "HatchRun" }, S.vp)
	local sh = { done = false, run = run, events = events, t = 0, R = R, starts = starts, tEnd = tEnd, T_POP = T_POP, T_END = T_END, CHARGE = CHARGE, WHITE_T = WHITE_T, cath = cath, pet = pet, job = job, fired = {}, k = k }
	-- the egg (this zone's egg design; a dark ball when the models are missing)
	local egg, unit, rot = eggMesh(pet.z, kind)
	if egg then
		egg.Parent = run
		local sc = (EGG_RY * 2) / EGG_H
		unit = unit * sc
		egg.Size = unit
	else
		egg = P("Part", { Shape = Enum.PartType.Ball, Size = Vector3.new(EGG_RX * 2, EGG_RX * 2, EGG_RX * 2), Color = rgb(C.ZONES[pet.z].eggCol) }, run)
		unit, rot = egg.Size, CFrame.new()
	end
	sh.egg, sh.unit, sh.rot = egg, unit, rot
	sh.rx = math.clamp(math.abs(rot:VectorToWorldSpace(unit).X) / 2, 0.8, 2.2)
	sh.shell = ellipsoid(run, Vector3.new(sh.rx * 2.06, EGG_RY * 2.06, sh.rx * 2.06)) -- white-hot shell before the pop
	sh.orbs = {}
	for i = 1, 4 do
		sh.orbs[i] = P("Part", { Shape = Enum.PartType.Ball, Material = Enum.Material.Neon, Transparency = 1, Size = Vector3.new(1, 1, 1), CFrame = CFrame.new(STAGE - Vector3.new(0, 200, 0)) }, run)
	end
	sh.segs = crackNetwork(events, sh.rx)
	sh.crG, sh.crC = {}, {}
	for i = 1, #sh.segs do
		sh.crG[i] = neonPart(run)
		sh.crC[i] = neonPart(run)
	end
	sh.petals, sh.petalC = {}, {}
	for i = 1, 10 do
		sh.petals[i] = ellipsoid(run, Vector3.new(0.6, 1.5, 0.08))
		sh.petalC[i] = ellipsoid(run, Vector3.new(0.28, 1.1, 0.08))
	end
	sh.spikes = {}
	for i = 1, 18 do
		sh.spikes[i] = makeSpike(run)
	end
	sh.square = { neonPart(run), neonPart(run), neonPart(run), neonPart(run) }
	sh.ring = {} -- expanding dashed circle (screen plane)
	for i = 1, 40 do
		sh.ring[i] = neonPart(run)
	end
	sh.ring2 = {}
	for i = 1, 40 do
		sh.ring2[i] = neonPart(run)
	end
	sh.star, sh.rays = {}, {}
	for i = 1, 12 do
		sh.star[i] = neonPart(run)
	end
	for i = 1, 20 do
		sh.rays[i] = neonPart(run)
	end
	sh.shards = {}
	for i = 1, 26 do
		local p = neonPart(run, Vector3.new(0.55, 0.55, 0.06))
		sh.shards[i] = p
	end
	sh.sunb = {}
	for i = 1, 28 do
		sh.sunb[i] = makeSpike(run)
	end
	-- the pet (hidden until the pop)
	local model = C.buildPet(pet, 1, true)
	model.Parent = run
	local bcf, bsize = model:GetBoundingBox()
	local piv = model:GetPivot().Position
	sh.fit = (cath and 6.2 or 5.0) / math.max(bsize.X, bsize.Y, bsize.Z, 0.5)
	sh.off = Vector3.new(piv.X - bcf.Position.X, piv.Y - (bcf.Position.Y - bsize.Y / 2), piv.Z - bcf.Position.Z)
	model:ScaleTo(0.01)
	model:PivotTo(CFrame.new(STAGE - Vector3.new(0, 300, 0)))
	sh.model, sh.lastK = model, 0.01

	enterShow()
	running = sh
	-- wait for the render loop to play it through (it sets sh.done); a hard time limit protects against hangs
	local limit = os.clock() + T_END * k + 20
	while not sh.done and os.clock() < limit do
		task.wait()
	end
	running = nil
	run:Destroy()
	leaveShow()
end

-- ---------------------------------------------------------------- per-frame drawing of the show
local function ringAt(list, center, r, rot, col, alpha, dash)
	local n = #list
	for i, p in ipairs(list) do
		if dash and i % 2 == 0 then
			p.Transparency = 1
		else
			local a0 = rot + (i - 1) * math.pi * 2 / n
			local a1 = rot + i * math.pi * 2 / n
			bar(p, center + Vector3.new(math.cos(a0) * r, math.sin(a0) * r, 0), center + Vector3.new(math.cos(a1) * r, math.sin(a1) * r, 0), 0.09)
			setN(p, col, alpha)
		end
	end
end
local function hideList(list)
	for _, p in ipairs(list) do
		if type(p) == "table" then
			for _, q in ipairs(p) do
				q.Transparency = 1
			end
		else
			p.Transparency = 1
		end
	end
end

local function drawShow(sh, dt)
	local prev = sh.t
	sh.t = sh.t + dt * speedUp / sh.k
	local t = sh.t
	local R = sh.R
	local now = os.clock()
	local cam = S.vcam
	local O = STAGE
	-- current step
	local L = 0
	for i = 1, R do
		if t >= sh.starts[i] then
			L = i
		end
	end
	local age = L > 0 and (t - sh.starts[L]) or 0
	local popped = t >= sh.T_POP
	local pa = t - sh.T_POP
	local whiten = popped and 1 or clamp((t - sh.tEnd - sh.CHARGE) / sh.WHITE_T)
	local build = clamp((t - 0.9) / (sh.tEnd - 0.9 + sh.CHARGE))
	local hit = (L > 0 and not popped) and math.exp(-age * 6) or 0
	local col
	if popped or whiten > 0.5 then
		col = WHITE
	elseif L == 0 then
		col = Color3.fromRGB(200, 210, 255)
	elseif L == 6 then
		col = Color3.fromHSV((t * 0.45) % 1, 0.55, 1)
	else
		col = RCOL[L]
	end
	-- sounds + crack events crossing this frame
	for i, ev in ipairs(sh.events) do
		if ev[1] > prev and ev[1] <= t and not popped then
			sfx("egg_crack", 0.45 + 0.12 * ev[2], 1.18 - 0.08 * ev[2] + (math.random() - 0.5) * 0.08)
		end
	end
	for i = 1, R do
		if sh.starts[i] > prev and sh.starts[i] <= t then
			hfx("step_" .. math.min(i, 5), (i == 6) and 0.9 or 0.75, (i == 6) and 0.78 or 1)
			if i == 4 or i == 5 or i == 6 then
				task.delay(0.05, hfx, "shing", 0.6, (i == 4) and 1 or (i == 5) and 0.9 or 0.75)
			end
			flash.BackgroundColor3 = (i == 6) and WHITE or RCOL[i]
		end
	end
	if sh.T_POP - 1.4 > prev and sh.T_POP - 1.4 <= t then
		hfx("riser", 0.7)
	end
	if sh.T_POP > prev and sh.T_POP <= t then
		sfx("egg_crack", 1, 0.75)
		hfx("burst", 1)
		task.delay(0.4 * sh.k, hfx, "reveal", 0.8)
		task.delay(0.15 * sh.k, petSound, C.petDef(sh.pet).kind, nil, 0.6)
		if UI.confetti and R >= 4 then
			task.delay(0.35 * sh.k, UI.confetti, R >= 5 and 90 or 45, R >= 5 and WARM or RCOL[4])
		end
	end
	local kick = 0
	local jolt = 0
	for i, ev in ipairs(sh.events) do
		local d = t - ev[1]
		if d >= 0 and d < 0.5 and not popped then
			kick = kick + math.min(ev[2], 4) * math.exp(-d * 16)
			jolt = jolt + math.exp(-d * 18) * ((i % 2 == 0) and 1 or -1) * math.min(ev[2], 4)
		end
	end

	local inCath = popped and sh.cath and pa >= 0.3
	-- ---------------- camera
	local rnd = Random.new(math.floor(t * 300))
	if not inCath then
		local pos = Vector3.new(0, 5.6, -24):Lerp(Vector3.new(0, 5.4, -19), eo(t / 0.5))
		if L >= 1 then
			pos = pos:Lerp(Vector3.new(0, 5.4, -16.5), eo(build) * 0.6)
		end
		if popped then
			pos = Vector3.new(0, 5.2, -19):Lerp(Vector3.new(0, 5.0, -17.5), eo(pa / 3))
		end
		local shake = (0.02 + 0.08 * build ^ 2) * (popped and 0.3 or 1) + (popped and 0.35 * math.exp(-pa * 6) or 0) + 0.04 * kick
		pos = pos + Vector3.new(rnd:NextNumber(-1, 1), rnd:NextNumber(-1, 1), 0) * shake * 0.5
		cam.CFrame = CFrame.lookAt(O + pos, O + Vector3.new(0, EC.Y - 1.0, 0))
		cam.FieldOfView = 34 - 0.3 * kick
	else
		local q = pa - 0.3
		local cp = Vector3.new(0, 4.2, -21):Lerp(Vector3.new(0, 5.6, -13.5), eo(q / 4.5)) + Vector3.new(math.sin(q * 0.6) * 0.6, 0, 0)
		cam.CFrame = CFrame.lookAt(CATH + cp, CATH + Vector3.new(0, 6.2 + 1.2 * eo(q / 4.5), 4))
		cam.FieldOfView = 35
	end
	-- ---------------- dim backdrop (darker for rarer pets), stand glow, sparkles; everything fades out at the end
	local fadeOut = clamp((t - (sh.T_END - 0.35)) / 0.35)
	local op = ({ 0.3, 0.38, 0.5, 0.6, 0.68, 0.74 })[R] * eo(t / 0.3) * (1 - fadeOut)
	S.backdrop.BackgroundTransparency = 1 - op
	S.vp.ImageTransparency = fadeOut
	S.standGlow.Color = col
	S.standGlow.Transparency = 1 - clamp(0.15 + 0.35 * build) * (1 - fadeOut)
	for _, cl in ipairs(S.claws) do
		cl.Transparency = popped and clamp(pa / 0.15) or 0
	end
	for _, sp in ipairs(S.spark) do
		local y = (sp.y + now * sp.sp) % 12
		local tw = 0.5 + 0.5 * math.sin(now * 5 + sp.ph)
		local s0 = 0.08 + 0.1 * tw
		sp.p.Size = Vector3.new(s0, s0, s0)
		sp.p.CFrame = CFrame.new(sp.x + math.sin(now * 0.5 + sp.ph) * 0.5, y, sp.z) * CFrame.Angles(0, 0, math.pi / 4)
		setN(sp.p, WHITE:Lerp(col, 0.5), (0.25 + 0.5 * tw) * (0.3 + 0.7 * build) * (1 - fadeOut))
	end
	if L > 0 and not popped and whiten < 0.5 then
		S.signSmall.Visible = true
		S.signBig.Text = RNAME[L]
		S.signBig.TextColor3 = col
		S.signScale.Scale = 1 + 0.5 * math.exp(-age * 10)
	else
		S.signSmall.Visible = false
		S.signBig.Text = ""
	end
	-- ---------------- screen: colour flash at each step, white flash at the pop, the ??? odds counter
	local fa = 0
	if L > 0 and not popped then
		fa = 0.22 * math.exp(-age * 8)
	elseif popped then
		flash.BackgroundColor3 = WHITE
		if sh.cath then
			fa = (pa < 0.32) and math.min(1, pa / 0.06) or math.max(0, 1 - (pa - 0.32) / 0.6)
		else
			fa = math.max(0, 1 - pa / 0.4) * 0.55
		end
	end
	flash.BackgroundTransparency = 1 - clamp(fa)
	if L == 6 and not popped then
		local u = clamp(age / (SECRET_T * 0.9))
		local lo, hi = math.log10(200), math.log10(SECRET_ODDS)
		local v = SECRET_ODDS
		if u < 1 then
			v = 10 ^ (lo + (hi - lo) * u ^ 1.25)
			local kd = 10 ^ (#tostring(math.floor(v)) - 2)
			v = math.floor(v / kd + 0.5) * kd
		end
		local dg = #tostring(math.floor(v))
		if dg ~= sh.digits then
			sh.digits = dg
			sh.pulseT = t
			sfx("ui_click", 0.7, 0.9 + 0.08 * (dg - 3))
		end
		setText(counter, "1 / " .. C.comma(math.floor(v)), 1)
		counter.TextColor3 = WHITE:Lerp(col, 0.5)
		counterScale.Scale = 1 + 0.35 * math.exp(-(t - (sh.pulseT or t)) * 10)
	else
		setText(counter, "", 0)
	end

	if not popped then
		-- ---------------- the egg: rises into the claws, floats, rocks; jolts at every crack; turns white before the pop
		local bob = 0.12 * math.sin(t * 2.2)
		local shake = build ^ 2 * 0.12 + 0.05 * hit + 0.25 * whiten
		local ox, oy = rnd:NextNumber(-1, 1) * shake, rnd:NextNumber(-1, 1) * shake * 0.5
		local tilt = math.sin(t * 2) * 0.05 + math.sin(t * 31) * 0.05 * build ^ 2 + 0.035 * jolt
		local sw = 1 + 0.02 * hit + 0.1 * whiten + 0.012 * math.abs(jolt)
		local Mg = CFrame.new(O + EC + Vector3.new(ox, bob + oy - (1 - eo(t / 0.6)) * 1.2, 0)) * CFrame.Angles(0, 0, tilt) * CFrame.Angles(0, 0.12 * math.sin(t * 0.6), 0)
		sh.egg.Transparency = 0
		sh.egg.Size = sh.unit * sw
		sh.egg.CFrame = Mg * sh.rot
		sh.shell.CFrame = Mg
		sh.shell.Size = Vector3.new(sw, sw, sw)
		setN(sh.shell, WHITE, whiten ^ 1.5 * 0.85)
		local ccol = col:Lerp(WHITE, 0.6)
		for i, sg in ipairs(sh.segs) do
			local te = sh.events[sg.ev][1]
			local g = clamp((t - te - sg.order * 0.02) / 0.05)
			if g <= 0 then
				sh.crG[i].Transparency = 1
				sh.crC[i].Transparency = 1
			else
				local p0 = Mg:PointToWorldSpace(sg.p * sw * 1.015)
				local q0 = Mg:PointToWorldSpace((sg.p + (sg.q - sg.p) * g) * sw * 1.015)
				local fresh = math.exp(-(t - te) * 5)
				bar(sh.crG[i], p0, q0, 0.16 + 0.14 * fresh)
				setN(sh.crG[i], col, 0.18 + 0.3 * fresh)
				bar(sh.crC[i], p0, q0, 0.06 + 0.02 * fresh)
				setN(sh.crC[i], ccol, 1)
			end
		end
		local c = O + EC + Vector3.new(ox, bob, 0)
		if L > 0 then
			for j, sgn in ipairs({ -1, 1 }) do -- two glowing orbs at the egg's sides
				local pos = c + Vector3.new(sgn * (sh.rx + 0.35), 0, -0.4)
				local s1 = 0.75 + 0.35 * hit
				sh.orbs[j].Size = Vector3.new(s1, s1, s1)
				sh.orbs[j].CFrame = CFrame.new(pos)
				setN(sh.orbs[j], col, 0.3)
				sh.orbs[j + 2].Size = Vector3.new(0.32, 0.32, 0.32)
				sh.orbs[j + 2].CFrame = CFrame.new(pos + Vector3.new(0, 0, -0.2))
				setN(sh.orbs[j + 2], WHITE, 1)
			end
		end
		if L > 0 and age < 1 then
			ringAt(sh.ring, O + EC + Vector3.new(0, 0, -1.5), 3 + 9 * eo(age), t * 0.6, WHITE, 1 - age, true)
		else
			hideList(sh.ring)
		end
		-- EPIC: light petals; LEGENDARY (and ???): more petals + gold spike crown + a turning square
		if L >= 4 and whiten < 1 then
			local n = (L == 4) and 6 or 10
			local g = (L == 4 or (L == 5 and age < 0.45)) and backOut(age / 0.45) or 1
			for i = 1, 10 do
				local p, pc = sh.petals[i], sh.petalC[i]
				if i <= n then
					local a = (i - 1) * math.pi * 2 / n + t * 0.5
					local dir = Vector3.new(math.cos(a), math.sin(a), 0)
					local R0 = (EGG_RY + 0.1) * g
					local base = c + Vector3.new(math.cos(a) * R0 * 0.85, math.sin(a) * R0, 0)
					local side = Vector3.new(-dir.Y, dir.X, 0)
					p.CFrame = CFrame.fromMatrix(base + dir * 0.75 * g + Vector3.new(0, 0, -1.6), side, dir)
					p.Mesh.Scale = Vector3.new(0.6, 1.5, 0.08) * g
					setN(p, col, 0.8 * (1 - whiten))
					pc.CFrame = CFrame.fromMatrix(base + dir * 0.7 * g + Vector3.new(0, 0, -1.68), side, dir)
					pc.Mesh.Scale = Vector3.new(0.26, 1.0, 0.08) * g
					setN(pc, WHITE, 0.7 * (1 - whiten))
				else
					p.Transparency = 1
					pc.Transparency = 1
				end
			end
		else
			hideList(sh.petals)
			hideList(sh.petalC)
		end
		if L >= 5 and whiten < 1 then
			local g = (L == 5) and backOut(age / 0.5) or 1
			for i, sp in ipairs(sh.spikes) do
				local a = (i - 1) * math.pi * 2 / 18 - t * 0.35
				local dir = Vector3.new(math.cos(a), math.sin(a), 0)
				local base = c + Vector3.new(math.cos(a) * 2.7 * g * 0.95, math.sin(a) * 2.7 * g * 1.1, -1.4)
				placeSpike(sp, base, dir, ((i % 2 == 1) and 1.6 or 1.0) * g, 0.5 * g, col:Lerp(WHITE, (i % 2 == 0) and 0.15 or 0), 1 - whiten)
			end
			local sq, rot = 2.6 * g, t * 0.7
			for i = 1, 4 do
				local a0, a1 = rot + (i - 1) * math.pi / 2, rot + i * math.pi / 2
				bar(sh.square[i], c + Vector3.new(math.cos(a0) * sq, math.sin(a0) * sq, -2), c + Vector3.new(math.cos(a1) * sq, math.sin(a1) * sq, -2), 0.07)
				setN(sh.square[i], WHITE, 0.9 * (1 - whiten))
			end
		else
			hideList(sh.spikes)
			hideList(sh.square)
		end
	else
		-- ---------------- POP: star burst, dashed rings, rays, shards; then the pet (stand, or the cathedral altar)
		if not sh.cleared then
			sh.cleared = true
			sh.egg.Transparency = 1
			sh.shell.Transparency = 1
			hideList(sh.crG)
			hideList(sh.crC)
			hideList(sh.orbs)
			hideList(sh.petals)
			hideList(sh.petalC)
			hideList(sh.spikes)
			hideList(sh.square)
			hideList(sh.ring)
		end
		local BC = inCath and (CATH + ECP) or (O + EC)
		local bt = inCath and (pa - 0.3) or pa
		if bt < 1.8 then
			local u = bt / 1.8
			local g = eo(bt / 0.35)
			local pts = {}
			for i = 1, 12 do
				local a = (i - 1) * math.pi * 2 / 12 + bt * 0.4
				pts[i] = BC + Vector3.new(math.cos(a) * 6.5 * g, math.sin(a) * 6.5 * g, -1.8)
			end
			for i = 1, 12 do
				bar(sh.star[i], pts[i], pts[(i + 4) % 12 + 1], 0.1)
				setN(sh.star[i], (i % 2 == 0) and Color3.fromRGB(255, 236, 150) or WHITE, 1.3 - u)
			end
			ringAt(sh.ring, BC + Vector3.new(0, 0, -1.7), 7.2 * g + 3 * u, bt * 0.5, WHITE, 1.2 - u, true)
			ringAt(sh.ring2, BC + Vector3.new(0, 0, -1.7), 8.4 * g + 3 * u, -bt * 0.5, Color3.fromRGB(255, 220, 120), 1.2 - u, true)
			for i = 1, 20 do
				local a = (i - 1) * math.pi * 2 / 20 + 0.1
				local dir = Vector3.new(math.cos(a), math.sin(a), 0)
				local ln = 3 + 18 * eo(bt / 0.5)
				local s0 = BC + dir * 1.5 + Vector3.new(0, 0, -1.9)
				bar(sh.rays[i], s0, s0 + dir * ln, 0.1 * (1 - u) + 0.03)
				setN(sh.rays[i], (i % 2 == 0) and WHITE or Color3.fromRGB(255, 240, 170), clamp(1 - u) * 0.55)
			end
			local sr = Random.new(9)
			for i = 1, 26 do
				local a = sr:NextNumber(0, math.pi * 2)
				local d = sr:NextNumber(6, 13) * bt
				local spin = sr:NextNumber(-4, 4)
				sh.shards[i].CFrame = CFrame.new(BC + Vector3.new(math.cos(a) * d, math.sin(a) * d - 2.5 * bt * bt, -2.4)) * CFrame.Angles(0, 0, math.pi / 4 + bt * spin)
				setN(sh.shards[i], (i % 3 == 0) and Color3.fromRGB(255, 220, 120) or WHITE, 1.2 - u)
			end
		else
			hideList(sh.star)
			hideList(sh.ring)
			hideList(sh.ring2)
			hideList(sh.rays)
			hideList(sh.shards)
		end
		-- the pet
		local pos, kk, spin
		if not sh.cath then
			local g = (pa > 0.08) and backOut((pa - 0.08) / 0.5) or 0.01
			kk = sh.fit * math.max(g, 0.01)
			local hop = 1.2 * (1 - eo(pa / 0.6))
			spin = math.pi * 2 * (1 - eo(pa / 1.2)) + 0.25 * math.sin(pa * 1.6) * clamp(pa - 1.2)
			pos = O + Vector3.new(0, STAND_TOP - 1.05 + hop + 0.1 * math.abs(math.sin(pa * 3)) * clamp(pa - 1.5), 0)
			if R >= 3 then -- gold spike crown behind the pet
				for i, sp in ipairs(sh.spikes) do
					local a = (i - 1) * math.pi * 2 / 18 - t * 0.25
					local dir = Vector3.new(math.cos(a), math.sin(a), 0)
					local base = O + Vector3.new(0, STAND_TOP + 1.5, 2.5) + dir * 3.4 * eo(pa / 0.6)
					placeSpike(sp, base, dir, (i % 2 == 1) and 1.5 or 0.9, 0.45, (R >= 4) and WARM or RCOL[3], 0.75)
				end
			end
			if R >= 5 then -- golden sunburst slowly turning behind the pet
				for i, sp in ipairs(sh.sunb) do
					local a = (i - 1) * math.pi * 2 / 28 + pa * 0.15
					local dir = Vector3.new(math.cos(a), math.sin(a), 0)
					local base = O + Vector3.new(0, STAND_TOP + 1.5, 3.2) + dir * 2.4 * eo(pa / 0.8)
					placeSpike(sp, base, dir, ((i % 2 == 1) and 5 or 3.2) * eo(pa / 1), 0.36, (i % 2 == 1) and Color3.fromRGB(255, 214, 110) or Color3.fromRGB(255, 245, 210), 0.4)
				end
			end
		elseif inCath then
			local q = pa - 0.3
			for i, sp in ipairs(sh.sunb) do -- golden sunburst slowly turning behind the pet
				local a = (i - 1) * math.pi * 2 / 28 + q * 0.15
				local dir = Vector3.new(math.cos(a), math.sin(a), 0)
				local base = CATH + ECP + Vector3.new(0, 0.4, 2.2) + dir * 2.6 * eo(q / 0.8)
				placeSpike(sp, base, dir, ((i % 2 == 1) and 5.5 or 3.4) * eo(q / 1), 0.38, (i % 2 == 1) and Color3.fromRGB(255, 214, 110) or Color3.fromRGB(255, 245, 210), 0.55)
			end
			for i, sp in ipairs(sh.spikes) do
				local a = (i - 1) * math.pi * 2 / 18 - q * 0.3
				local dir = Vector3.new(math.cos(a), math.sin(a), 0)
				local base = CATH + ECP + Vector3.new(0, 0.4, 1.8) + dir * 3.3 * eo(q / 0.7)
				placeSpike(sp, base, dir, (i % 2 == 1) and 1.3 or 0.8, 0.36, WARM, 0.85)
			end
			for _, cdl in ipairs(S.candles) do
				local f = 0.8 + 0.2 * math.sin(now * (10 + cdl[3] % 5) + cdl[3])
				cdl[1].Size = Vector3.new(0.35 * f, 0.35 * f, 0.35 * f)
				cdl[1].CFrame = CFrame.new(cdl[2] + Vector3.new(0, 0.03 * math.sin(now * 13 + cdl[3]), 0))
			end
			S.altarLight.Brightness = 2 + 6 * math.exp(-q * 2.5)
			local g = (q > 0.05) and backOut((q - 0.05) / 0.7) or 0.01
			kk = sh.fit * math.max(g, 0.01)
			local rise = 1.6 * (1 - eo(q / 1.1))
			spin = math.pi * 2 * (1 - eo(q / 1.6)) + 0.22 * math.sin(q * 1.3) * clamp(q - 1.6)
			pos = CATH + Vector3.new(0, ALTAR_TOP + 1.1 + rise + 0.08 * math.sin(q * 2.4) * clamp(q - 1.2), 4.5)
		end
		if pos then
			if math.abs(kk - sh.lastK) > 0.002 then
				sh.lastK = kk
				sh.model:ScaleTo(kk)
			end
			sh.model:PivotTo(CFrame.new(pos) * CFrame.Angles(0, spin, 0) * CFrame.new(sh.off * kk))
		end
		-- name + odds (serif, gold) once the pet is out
		local tn = sh.cath and 1.3 or 0.5
		if pa > tn then
			local u = eo((pa - tn) / 0.6)
			setText(petNameL, C.petName(sh.pet), u)
			nameScale.Scale = 0.85 + 0.15 * u
			local odds = sh.job.secret and SECRET_ODDS or C.RARITY[sh.pet.i].odds
			setText(oddsL, (sh.job.isNew and "NEW!   " or "") .. "1 / " .. C.comma(odds), eo((pa - tn - 0.3) / 0.5))
		end
	end
	if t >= sh.T_END then
		sh.done = true
	end
end

RunService:BindToRenderStep("HatchShow", Enum.RenderPriority.Camera.Value + 1, function(dt)
	local sh = running
	if not sh or sh.done then
		return
	end
	local ok, err = pcall(drawShow, sh, math.min(dt, 0.1))
	if not ok then
		warn("hatch show: " .. tostring(err))
		sh.done = true
	end
end)
-- tap / click during a show: the rest plays 3x faster
game:GetService("UserInputService").InputBegan:Connect(function(input)
	if running and (input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch) then
		speedUp = 3
	end
end)

local function cleanupAfterError()
	running = nil
	if S then
		for _, o in ipairs(S.vp:GetChildren()) do
			if o.Name == "HatchRun" then
				o:Destroy()
			end
		end
	end
	leaveShow()
end

-- one queue for real hatches AND the Studio test keys, so two shows never overlap
local queue = {}
local busy = false
local function enqueue(job)
	table.insert(queue, job)
	if busy then
		return
	end
	busy = true
	task.spawn(function()
		while #queue > 0 do
			local job1 = table.remove(queue, 1)
			-- big batch: Common/Uncommon only get a line of text; Rare plays faster; Epic+ always get the full show
			if #queue >= 3 and job1.pet.i < 3 and not job1.secret then
				showNote(C.petName(job1.pet) .. "  (1 in " .. C.comma(C.RARITY[job1.pet.i].odds) .. ")", "good")
				task.wait(0.2)
			else
				job1.fast = #queue > 0 and job1.pet.i < 4
				local ok, err
				local HV = C.HATCH_STYLE ~= "old" and RS:FindFirstChild("HatchVFX")
				if HV then
					-- v2: world-space VFX show (HatchVFX module)
					ok, err = pcall(function()
						require(HV).play(job1, {
							eggMesh = eggMesh, buildPet = C.buildPet, hfx = hfx, petName = C.petName,
							oddsText = "1 / " .. C.comma(job1.secret and SECRET_ODDS or C.RARITY[job1.pet.i].odds),
							fastPass = UI.hasPass and UI.hasPass("fast"), eggColor = rgb(C.ZONES[job1.pet.z].eggCol),
						})
					end)
				else
					ok, err = pcall(runShow, job1)
				end
				if not ok then
					warn("hatch show: " .. tostring(err))
					cleanupAfterError()
				end
			end
		end
		busy = false
	end)
end
Hatch.OnClientEvent:Connect(function(pet, kind, isNew, comboNow) -- <- the trigger: the server fires "Hatch" when an egg is hatched
	enqueue({ pet = pet, kind = kind, isNew = isNew })
end)

-- STUDIO ONLY test: F1..F5 = hatch show of that rarity (zone 1 egg), F6 = the ??? step; Shift = 6 at once (batch test)
if RunService:IsStudio() then
	local UIS = game:GetService("UserInputService")
	local KEYS = { [Enum.KeyCode.F1] = 1, [Enum.KeyCode.F2] = 2, [Enum.KeyCode.F3] = 3, [Enum.KeyCode.F4] = 4, [Enum.KeyCode.F5] = 5, [Enum.KeyCode.F6] = 6 }
	UIS.InputBegan:Connect(function(input, typing)
		local r = KEYS[input.KeyCode]
		if r and not typing then
			local n = UIS:IsKeyDown(Enum.KeyCode.LeftShift) and 6 or 1
			for j = 1, n do
				local rr = (n > 1 and j % 2 == 1) and math.max(1, math.min(r, 5) - 2) or r
				enqueue({ pet = { z = 1, i = math.min(rr, 5), t = 1 }, kind = "normal", isNew = rr >= 4, secret = rr == 6 })
			end
		end
	end)
end
end)()

EggSpawn.OnClientEvent:Connect(makeEgg)
EggGone.OnClientEvent:Connect(function(id, userId, kind)
	local e = eggs[id]
	if e then
		local y = e.y0 + (e.gy - e.y0) * math.clamp((os.clock() - e.t0) / e.fall, 0, 1)
		removeEgg(id)
		popEgg(e, y, kind == "rotten")
	end
	if userId == plr.UserId and kind == "rotten" then
		sfx("yuck", 0.6)
	end
end)

local lastFull = 0
RunService.RenderStepped:Connect(function()
	local now = os.clock()
	local char = plr.Character
	local hrp = char and char:FindFirstChild("HumanoidRootPart")
	local radius = attr("Radius", 4)
	for id, e in pairs(eggs) do
		local k = (now - e.t0) / e.fall
		if now - e.t0 >= e.fall + e.linger then
			removeEgg(id)
			breakEgg(e)
		else
			k = math.min(k, 1)
			local y = e.y0 + (e.gy - e.y0) * k
			local spin = CFrame.Angles(0, now * 2 + id, 0)
			if k >= 1 then
				spin = spin * CFrame.Angles(0, 0, math.sin(now * 9) * 0.12) -- waiting on the ground: wobble
			end
			local h = LAYER * e.scale
			for i, p in ipairs(e.layers) do
				p.CFrame = CFrame.new(e.x, y, e.z) * spin * CFrame.new(0, (i - 1) * h + h / 2, 0)
			end
			if e.mesh then
				e.mesh.CFrame = CFrame.new(e.x, y + EGG_H * e.scale / 2, e.z) * spin * e.meshRot
			end
			local bh = math.max(y - e.gy, 0.05)
			e.beam.Size = Vector3.new(e.beamW, bh, e.beamW)
			e.beam.CFrame = CFrame.new(e.x, e.gy + bh / 2, e.z)
			local d = (9 - (9 - EGG_W) * k) * e.scale
			e.shadow.Size = Vector3.new(0.15, d, d)
			e.shadow.Transparency = 0.6 - 0.35 * k
			if hrp and not e.sent then
				local p = hrp.Position
				local dx, dz = p.X - e.x, p.Z - e.z
				local reach = radius + (e.scale - 1) * EGG_W / 2
				if dx * dx + dz * dz < reach * reach and y < p.Y + 6.5 and y > p.Y - 4 then
					if e.kind ~= "rotten" and attr("Carry", 0) >= attr("CarryMax", 3) then
						if now - lastFull > 2 then
							lastFull = now
							showNote("Basket is full! Run to your base", "bad")
						end
					else
						e.sent = true
						Catch:FireServer(id)
					end
				end
			end
		end
	end

	-- combo timer bar
	if combo.Visible then
		comboBar.Size = UDim2.fromScale(math.clamp((comboUntil - now) / C.COMBO_TIME, 0, 1), 1)
	end

	-- pets in the pens hop
	local cam = workspace.CurrentCamera
	local camPos = cam and cam.CFrame.Position
	if camPos then
		for model, info in pairs(penPets) do
			if (info.cf.Position - camPos).Magnitude < 160 then
				-- lively idle: bouncy hop that leans into the jump, a little wiggle, looks around, and a happy spin-jump now and then
				local t = now * 2.4 + info.phase
				local s = math.sin(t)
				local hop = math.abs(s) ^ 0.7 * 0.65
				local lean = math.cos(t) * (s >= 0 and 1 or -1) * 0.13
				local turn = math.sin(t * 0.35) * 0.45
				local k = (now * 0.11 + info.phase * 0.37) % 1
				if k < 0.09 then
					if not info.sang and (info.cf.Position - camPos).Magnitude < 60 then
						info.sang = true
						petSound(model:GetAttribute("Kind"), model.PrimaryPart or model:FindFirstChildWhichIsA("BasePart"), 0.5)
					end
					local u = k / 0.09
					hop = hop + math.sin(u * math.pi) * 1.6
					turn = turn + u * u * (3 - 2 * u) * math.pi * 2
				else
					info.sang = false
				end
				local PA = model:GetAttribute("AnimKey") and C.petAnim()
				if info.penC then
					-- v143: walk around the pen: Walk clip while moving, Idle / PenLife while standing
					local cf, moving = penWalk(model, info, now)
					local done = false
					if PA then
						if moving then
							done = PA.pose(model, "Walk", info.walkT, cf)
						else
							done = PA.pose(model, (info.phase * 7 + math.floor(now / 6)) % 3 == 0 and "PenLife" or "Idle", now + info.phase * 3, cf)
						end
					end
					if not done then
						local b = moving and math.abs(math.sin(info.walkT * 9)) * 0.5 or hop * 0.5
						model:PivotTo(cf * CFrame.new(0, b, 0) * CFrame.Angles(moving and 0 or lean, 0, math.sin(t * 2) * 0.05))
					end
				elseif PA then
					-- v129: Codex pet: its own PenLife animation (walks, looks around, sits...) + a slow turn now and then
					PA.pose(model, "PenLife", now + info.phase * 3, info.cf * CFrame.Angles(0, math.sin(now * 0.15 + info.phase) * 0.9, 0))
				else
					model:PivotTo(info.cf * CFrame.new(0, hop, 0) * CFrame.Angles(0, turn, 0) * CFrame.Angles(lean, 0, math.sin(t * 2) * 0.05))
				end
				for _, p in ipairs(info.bodies) do
					p.Color = Color3.fromHSV((now * 0.25 + info.phase * 0.1) % 1, 0.65, 1)
				end
			end
		end
	end
end)

-- ------------------------------------------------------------ treadmill light show (client only, in the look of the reference video)
-- The server tags every treadmill model "TreadShow" (attributes Neon, PivotCF). Around it we animate:
-- a ring that spins around the glowing ball, cubes that orbit and bob, stripes that run along the belt, sparkles and a pulsing light.
local SHOW = {
	ringCubes = 10,   -- pieces in the spinning ring
	ringSpeed = 1.4,  -- turns per ~4.5 s (radians per second)
	orbit = 9,        -- floating cubes around the treadmill
	stripes = 6,      -- moving glow stripes on the belt
	beltSpeed = 9,    -- studs per second
	sparkles = 14,    -- particles per second
}
local okMeta, PROPS = pcall(function()
	return require(RS:WaitForChild("PropsMeta", 3))
end)
if not okMeta or type(PROPS) ~= "table" then
	PROPS = {}
end
local shows = {}

local function showPart(folder, size, col, neon)
	local p = fxPart(size, CFrame.new(0, -500, 0), col)
	if neon then
		p.Material = Enum.Material.Neon
	end
	p.Parent = folder
	return p
end

local function addShow(model)
	local pivot = model:GetAttribute("PivotCF")
	local neon = model:GetAttribute("Neon")
	local id = model:GetAttribute("TreadmillId")
	if not (pivot and neon and id) or shows[model] then
		return
	end
	local m = PROPS["Tread_" .. id] or {}
	local belt = m.belt or { 0, 1.6, 12, 5 }
	local orb = m.orb or { 5, 8.5, 0.9 }
	local tier = m.tier or 0
	local folder = Instance.new("Folder")
	folder.Name = "TreadShow"
	folder.Parent = workspace
	local dark = Color3.new(neon.R * 0.12 + 0.04, neon.G * 0.12 + 0.04, neon.B * 0.12 + 0.05)
	local s = { folder = folder, pivot = pivot, belt = belt, orb = orb, ring = {}, orbit = {}, stripes = {}, phase = math.random() * 10 }
	for i = 1, SHOW.ringCubes do
		s.ring[i] = showPart(folder, (i % 2 == 0) and Vector3.new(0.3, 0.3, 0.9) or Vector3.new(0.34, 0.34, 0.34), (i % 2 == 0) and dark or neon, i % 2 == 1)
	end
	for i = 1, SHOW.orbit + tier * 2 do
		local size = 0.5 + math.random() * 0.7
		local p = showPart(folder, Vector3.new(size, size, size), (i % 3 == 0) and neon or dark, i % 3 == 0)
		s.orbit[i] = { part = p, r = 8.5 + math.random() * 3.5, h = 1.5 + math.random() * 7, a = math.random() * math.pi * 2, sp = 0.25 + math.random() * 0.35, bob = math.random() * 6 }
	end
	for i = 1, SHOW.stripes do
		s.stripes[i] = showPart(folder, Vector3.new(0.35, 0.06, belt[4] - 0.9), neon, true)
	end
	-- glowing ball: light + sparkles
	local core = showPart(folder, Vector3.new(0.4, 0.4, 0.4), neon, true)
	core.Transparency = 1
	core.CFrame = pivot * CFrame.new(orb[1], orb[2], 0)
	s.light = make("PointLight", { Color = neon, Range = 22, Brightness = 2, Shadows = false }, core)
	local floor = showPart(folder, Vector3.new(15, 0.2, 9), neon, false)
	floor.Transparency = 1
	floor.CFrame = pivot * CFrame.new(0, 0.3, 0)
	make("ParticleEmitter", {
		Texture = "rbxasset://textures/particles/sparkles_main.dds",
		Color = ColorSequence.new(neon),
		LightEmission = 1,
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(1, 0) }),
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(1, 1) }),
		Lifetime = NumberRange.new(1.4, 2.6),
		Rate = SHOW.sparkles + tier * 4,
		Speed = NumberRange.new(2, 4.5),
		SpreadAngle = Vector2.new(25, 25),
		EmissionDirection = Enum.NormalId.Top,
		Rotation = NumberRange.new(0, 360),
		RotSpeed = NumberRange.new(-90, 90),
	}, floor)
	shows[model] = s
end

local function removeShow(model)
	local s = shows[model]
	if s then
		shows[model] = nil
		s.folder:Destroy()
	end
end

for _, m in ipairs(CS:GetTagged("TreadShow")) do
	addShow(m)
end
CS:GetInstanceAddedSignal("TreadShow"):Connect(function(m)
	task.defer(addShow, m)
end)
CS:GetInstanceRemovedSignal("TreadShow"):Connect(removeShow)

RunService.RenderStepped:Connect(function()
	local now = os.clock()
	local cam = workspace.CurrentCamera
	if not cam then
		return
	end
	local camPos = cam.CFrame.Position
	for model, s in pairs(shows) do
		if not model.Parent then
			removeShow(model)
		elseif (s.pivot.Position - camPos).Magnitude < 220 then
			local t = now + s.phase
			local orbCF = s.pivot * CFrame.new(s.orb[1], s.orb[2], 0)
			local rr = s.orb[3] * 1.5 + 0.7
			for i, p in ipairs(s.ring) do
				-- ring stands upright and faces the runner; it spins and slowly tips
				local a = t * SHOW.ringSpeed + i * (math.pi * 2 / #s.ring)
				p.CFrame = orbCF * CFrame.Angles(0, math.sin(t * 0.6) * 0.5, 0) * CFrame.Angles(a, 0, 0) * CFrame.new(0, rr, 0)
			end
			for _, o in ipairs(s.orbit) do
				local a = o.a + t * o.sp
				o.part.CFrame = s.pivot * CFrame.new(math.cos(a) * o.r, o.h + math.sin(t * 1.3 + o.bob) * 0.7, math.sin(a) * o.r * 0.7)
					* CFrame.Angles(t * 0.9 + o.bob, t * 0.7, 0)
			end
			local len = s.belt[3]
			for i, p in ipairs(s.stripes) do
				local x = len / 2 - ((t * SHOW.beltSpeed + i * len / #s.stripes) % len)
				p.CFrame = s.pivot * CFrame.new(s.belt[1] + x, s.belt[2] + 0.05, 0)
				p.Transparency = 0.15 + 0.6 * math.abs(x) / (len / 2) -- fade at both ends of the belt
			end
			s.light.Brightness = 1.6 + math.sin(t * 3) * 0.7
		end
	end
end)

-- ------------------------------------------------------------ treadmill lock-in: step on your treadmill = you run on it
-- the player is held in the middle of the belt facing the console and plays the run animation;
-- every speed gain pops a "+N SPEED" number out of the player and dust puffs come from the feet. Jump = get off.
local LOCK = { popRise = 5, popTime = 0.9, offAfter = 0.6 }
local lock = { on = false, mustLeave = false, model = nil, cf = nil, track = nil, lastSpeed = nil, offT = 0, step = 0 }
lockGui = make("ScreenGui", { Name = "TreadLock", ResetOnSpawn = false, Enabled = false }, plr:WaitForChild("PlayerGui"))
local lockHint = make("TextLabel", {
	AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -110), Size = UDim2.fromOffset(420, 40),
	BackgroundTransparency = 1, Font = Enum.Font.FredokaOne, TextScaled = true, TextColor3 = WHITE,
	Text = "RUNNING!  Jump to get off", Visible = false, -- not wanted
}, lockGui)
make("UIStroke", { Thickness = 3, Color = INK }, lockHint)
-- while running, hide the purple "what to do" pill so the two texts never overlap

local function ownTreadmill()
	local map = workspace:FindFirstChild("Map")
	local base = map and map:FindFirstChild("Base" .. attr("Base", 0))
	if not base then
		return nil
	end
	for model, s in pairs(shows) do
		if model.Parent == base then
			return model, s
		end
	end
	return nil
end

local function charParts()
	local ch = plr.Character
	local hrp = ch and ch:FindFirstChild("HumanoidRootPart")
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if hrp and hum and hum.Health > 0 then
		return ch, hrp, hum
	end
	return nil
end

local function runTrack(ch, hum)
	local animate = ch:FindFirstChild("Animate")
	local run = animate and animate:FindFirstChild("run")
	local anim = run and run:FindFirstChildOfClass("Animation")
	local animator = hum:FindFirstChildOfClass("Animator")
	if not (anim and animator) then
		return nil
	end
	local tr = animator:LoadAnimation(anim)
	tr.Priority = Enum.AnimationPriority.Action
	tr.Looped = true
	return tr
end

local function unlock(jumpOff)
	if not lock.on then
		return
	end
	lock.on = false
	lock.mustLeave = true
	lockGui.Enabled = false
	if lock.track then
		lock.track:Stop(0.2)
		lock.track = nil
	end
	local _, hrp, hum = charParts()
	if hum then
		hum.AutoRotate = true
	end
	if jumpOff and hrp and lock.cf then
		-- hop off the back of the belt
		hrp.CFrame = lock.cf * CFrame.new(0, 0.5, 6.5)
		hrp.AssemblyLinearVelocity = lock.cf.LookVector * -12 + Vector3.new(0, 25, 0)
	end
end

local function speedPop(hrp, amount)
	-- one speed number out of the player: bolt icon + big blue "+N", pops in, tilts, rises and fades
	local holder = fxPart(Vector3.new(0.2, 0.2, 0.2), hrp.CFrame * CFrame.new((math.random() - 0.5) * 3, 2 + math.random(), 0), WHITE)
	holder.Transparency = 1
	holder.Parent = fx
	local bb = make("BillboardGui", { Size = UDim2.fromScale(4.2, 1.4), AlwaysOnTop = true, LightInfluence = 0, Adornee = holder }, holder)
	local box = make("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Rotation = (math.random() - 0.5) * 12 }, bb)
	local sc = make("UIScale", { Scale = 0.2 }, box)
	local ic = icon(box, "bolt", UDim2.fromScale(1, 1), UDim2.fromScale(0, 0))
	wobbly[ic] = nil
	local tl = make("TextLabel", {
		Size = UDim2.fromScale(0.72, 0.9), Position = UDim2.fromScale(0.28, 0.05), BackgroundTransparency = 1, Font = Enum.Font.LuckiestGuy,
		TextScaled = true, TextXAlignment = Enum.TextXAlignment.Left, TextColor3 = WHITE, Text = "+" .. C.fmt(amount),
	}, box)
	make("UIGradient", { Rotation = 90, Color = ColorSequence.new(Color3.fromRGB(200, 240, 255), Color3.fromRGB(40, 150, 255)) }, tl)
	local st = make("UIStroke", { Thickness = 3, Color = Color3.fromRGB(18, 10, 28) }, tl)
	TweenService:Create(sc, TweenInfo.new(0.22, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
	local ti = TweenInfo.new(LOCK.popTime, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	TweenService:Create(holder, ti, { CFrame = holder.CFrame + Vector3.new(0, LOCK.popRise, 0) }):Play()
	local fade = TweenInfo.new(LOCK.popTime * 0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, LOCK.popTime * 0.6)
	TweenService:Create(tl, fade, { TextTransparency = 1 }):Play()
	TweenService:Create(st, fade, { Transparency = 1 }):Play()
	TweenService:Create(ic, fade, { ImageTransparency = 1 }):Play()
	Debris:AddItem(holder, LOCK.popTime + 0.1)
end

-- purchase pop: upgrade arrow + gold text that bursts out of the player, rises and fades
UI.playerPop = function(msg)
	local char = plr.Character
	local head = char and (char:FindFirstChild("Head") or char:FindFirstChild("HumanoidRootPart"))
	if not head then
		if UI.toast then
			UI.toast(msg, "buy")
		end
		return
	end
	local holder = fxPart(Vector3.new(0.2, 0.2, 0.2), head.CFrame * CFrame.new(0, 2.2, 0), WHITE)
	holder.Transparency = 1
	holder.Parent = fx
	local bb = make("BillboardGui", { Size = UDim2.fromScale(11, 2.2), AlwaysOnTop = true, LightInfluence = 0, Adornee = holder }, holder)
	local box = make("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, bb)
	local sc = make("UIScale", { Scale = 0.1 }, box)
	local glow = rays(box, 12, Color3.fromRGB(255, 230, 120), 0.5)
	glow.Size = UDim2.fromScale(0.45, 2.2)
	local ic = icon(box, "upgrade", UDim2.fromScale(1, 1.05), UDim2.fromScale(0, -0.02))
	wobbly[ic] = nil
	local tl = make("TextLabel", {
		Size = UDim2.fromScale(0.82, 0.8), Position = UDim2.fromScale(0.17, 0.1), BackgroundTransparency = 1, Font = Enum.Font.LuckiestGuy,
		TextScaled = true, TextXAlignment = Enum.TextXAlignment.Left, TextColor3 = WHITE, Text = string.upper(msg),
	}, box)
	make("UIGradient", { Rotation = 90, Color = ColorSequence.new(Color3.fromRGB(255, 248, 170), Color3.fromRGB(255, 160, 20)) }, tl)
	local st = make("UIStroke", { Thickness = 3, Color = Color3.fromRGB(18, 10, 28) }, tl)
	-- burst in (overshoot), then rise and fade
	local inT = TweenService:Create(sc, TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 })
	inT:Play()
	TweenService:Create(holder, TweenInfo.new(1.8, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = holder.CFrame + Vector3.new(0, 3.5, 0) }):Play()
	local fade = TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 1.3)
	TweenService:Create(tl, fade, { TextTransparency = 1 }):Play()
	TweenService:Create(st, fade, { Transparency = 1 }):Play()
	TweenService:Create(ic, fade, { ImageTransparency = 1 }):Play()
	glow.Visible = true
	task.delay(1.3, function()
		glow.Visible = false
	end)
	-- sparkles from the player
	local em = make("ParticleEmitter", {
		Rate = 0, Lifetime = NumberRange.new(0.5, 0.9), Speed = NumberRange.new(8, 14), SpreadAngle = Vector2.new(180, 180), Drag = 3,
		LightEmission = 1, Color = ColorSequence.new(Color3.fromRGB(255, 220, 80)),
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(1, 0) }),
	}, holder)
	em:Emit(22)
	Debris:AddItem(holder, 2.2)
end

local function footPuff(cf, col)
	local p = fxPart(Vector3.new(0.5, 0.5, 0.5), cf, col, Enum.PartType.Ball)
	p.Transparency = 0.3
	p.Parent = fx
	TweenService:Create(p, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
		Size = Vector3.new(1.4, 1.4, 1.4), Transparency = 1, CFrame = cf * CFrame.new(0, 0.4, 1.6),
	}):Play()
	Debris:AddItem(p, 0.5)
end

game:GetService("UserInputService").JumpRequest:Connect(function()
	if lock.on and os.clock() - lock.offT > LOCK.offAfter then
		unlock(true)
	end
end)

plr:GetAttributeChangedSignal("Speed"):Connect(function()
	local v = attr("Speed", 0)
	local old = lock.lastSpeed
	lock.lastSpeed = v
	if lock.on and old and v > old then
		local _, hrp = charParts()
		if hrp then
			speedPop(hrp, v - old)
		end
	end
end)
lock.lastSpeed = attr("Speed", 0)

plr.CharacterAdded:Connect(function()
	lock.on, lock.mustLeave, lock.track = false, false, nil
	lockGui.Enabled = false
end)

RunService.Heartbeat:Connect(function(dt)
	local ch, hrp, hum = charParts()
	if not ch then
		return
	end
	local model, s = ownTreadmill()
	if not model then
		unlock(false)
		return
	end
	local belt = s.belt
	local lp = s.pivot:PointToObjectSpace(hrp.Position)
	local onBelt = math.abs(lp.X - belt[1]) < belt[3] / 2 + 0.6 and math.abs(lp.Z) < belt[4] / 2 + 0.6 and lp.Y > -1 and lp.Y < 9
	if not lock.on then
		if not onBelt then
			lock.mustLeave = false
		elseif not lock.mustLeave then
			-- lock in: middle of the belt, facing the console (+X of the treadmill)
			local hipY = hum.RigType == Enum.HumanoidRigType.R6 and 3 or hum.HipHeight + hrp.Size.Y / 2
			local pos = s.pivot * Vector3.new(belt[1] + 0.6, belt[2] + hipY, 0)
			lock.cf = CFrame.lookAt(pos, pos + s.pivot.XVector)
			lock.model = model
			lock.on = true
			lock.offT = os.clock()
			lock.lastSpeed = attr("Speed", 0)
			hum.AutoRotate = false
			lock.track = runTrack(ch, hum)
			if lock.track then
				lock.track:Play(0.15)
			end
			lockGui.Enabled = true
			lock.hum = os.clock() - 2
		end
	end
	if lock.on then
		if lock.model ~= model then
			unlock(false)
			return
		end
		hrp.CFrame = lock.cf
		hrp.AssemblyLinearVelocity = Vector3.zero
		hrp.AssemblyAngularVelocity = Vector3.zero
		local pace = math.clamp(hum.WalkSpeed / 16, 1, 2.2)
		if lock.track then
			lock.track:AdjustSpeed(pace)
		end
		-- dust puffs from the feet, left/right in step with the run
		lock.step = lock.step + dt * pace * 3
		if lock.step >= 1 then
			lock.step = lock.step - 1
			local side = (math.floor(os.clock() * 10) % 2 == 0) and -0.5 or 0.5
			local legs = hum.RigType == Enum.HumanoidRigType.R6 and 2 or hum.HipHeight
			footPuff(lock.cf * CFrame.new(side, -hrp.Size.Y / 2 - legs + 0.2, 0.6), model:GetAttribute("Neon") or WHITE)
		end
	end
end)

-- ------------------------------------------------------------ windmill blades turn (client only, Blender mesh "WindmillBlades")
task.spawn(function()
	task.wait(2)
	local blades = {}
	for _, d in ipairs(workspace:GetDescendants()) do
		if d.Name == "WindmillBlades" and d:IsA("BasePart") then
			table.insert(blades, { part = d, cf = d.CFrame })
		end
	end
	if #blades == 0 then
		return
	end
	local turn = 0
	RunService.RenderStepped:Connect(function(dt)
		turn = turn + dt * 0.7
		for _, b in ipairs(blades) do
			b.part.CFrame = b.cf * CFrame.Angles(0, 0, turn)
		end
	end)
end)

-- ------------------------------------------------------------ ghosts in Spooky Hollow float up and down (client only)
task.spawn(function()
	task.wait(2)
	local ghosts = {}
	for _, d in ipairs(workspace:GetDescendants()) do
		if d.Name == "Ghost" and d:IsA("BasePart") then
			table.insert(ghosts, { part = d, cf = d.CFrame, phase = #ghosts * 0.9 })
		end
	end
	if #ghosts == 0 then
		return
	end
	local t = 0
	RunService.Heartbeat:Connect(function(dt)
		t = t + dt
		for _, g in ipairs(ghosts) do
			g.part.CFrame = g.cf * CFrame.new(0, math.sin(t * 1.3 + g.phase) * 1.6, 0) * CFrame.Angles(0, math.sin(t * 0.5 + g.phase) * 0.5, 0)
		end
	end)
end)

-- ------------------------------------------------------------ Neon City hologram egg turns slowly (client only)
task.spawn(function()
	task.wait(2)
	for _, d in ipairs(workspace:GetDescendants()) do
		if d.Name == "Hologram" and d:IsA("BasePart") then
			local cf = d.CFrame
			local t = 0
			RunService.Heartbeat:Connect(function(dt)
				t = t + dt
				d.CFrame = cf * CFrame.new(0, math.sin(t * 1.1) * 1.2, 0) * CFrame.Angles(0, t * 0.8, 0)
			end)
		end
	end
end)

-- ------------------------------------------------------------ new menus (ReplicatedStorage > UIMenus)
do
	local ok, err = pcall(function()
		local Menus = require(RS:WaitForChild("UIMenus"))
		Menus.init({
			C = C, make = make, gui = gui, plr = plr, UI = UI, TweenService = TweenService, RunService = RunService,
			WHITE = WHITE, BLACK = BLACK, YELLOW = YELLOW, GREEN = GREEN, RED = RED,
			attr = attr, Action = Action, sfx = sfx, face = face, lip = lip, title = title, icon = icon, pressable = pressable,
			corner = corner, tint = tint, petView = petView, wobbly = wobbly, menu = menu, iconButton = iconButton,
			indexBtn = indexBtn, rebirthBtn = rebirthBtn, stack = stack, basketBox = basketBox,
		})
		UI.toast, UI.confetti, UI.hasPass = Menus.toast, Menus.confetti, Menus.hasPass
	end)
	if not ok then
		warn("UIMenus: " .. tostring(err))
	end
end

-- ------------------------------------------------------------ treadmill upgrade panel on your own front fence
-- The board parts are invisible in the map; only YOUR base's board is shown (locally), with LV a > b, speed, and a buy button.
do
	local sg, lvT, spT, btn, btnT, shown
	local buyTrain
	local NAVY1, NAVY2, GOLDLINE = Color3.fromRGB(58, 52, 112), Color3.fromRGB(28, 24, 58), Color3.fromRGB(255, 200, 60)
	local signPart, lastBuy = nil, 0
	buyTrain = function()
		if os.clock() - lastBuy < 0.35 then
			return
		end
		lastBuy = os.clock()
		playClick()
		local sc = btn:FindFirstChildOfClass("UIScale") or make("UIScale", {}, btn)
		sc.Scale = 0.9
		TweenService:Create(sc, TweenInfo.new(0.15, Enum.EasingStyle.Back), { Scale = 1 }):Play()
		Action:FireServer("upgrade", "train")
	end
	-- v144 fix (user: the upgrade button on the fence did nothing): invisible parts between the camera and the board
	-- (fence collision boxes, zones) can swallow clicks on a SurfaceGui. Backup: a click/tap that the GUI did not take
	-- is ray-cast against the board only; if it lands on the button area, buy.
	game:GetService("UserInputService").InputBegan:Connect(function(input, processed)
		if not signPart or not btn then
			return
		end
		if processed then -- v162: only skip when a visible screen button is under the finger (not an empty HUD frame)
			for _, g in ipairs(plr.PlayerGui:GetGuiObjectsAtPosition(input.Position.X, input.Position.Y)) do
				if g:IsA("GuiButton") and g.Visible and g:FindFirstAncestorWhichIsA("ScreenGui") then
					return
				end
			end
		end
		local t = input.UserInputType
		if t ~= Enum.UserInputType.MouseButton1 and t ~= Enum.UserInputType.Touch then
			return
		end
		local cam = workspace.CurrentCamera
		local ray = cam:ViewportPointToRay(input.Position.X, input.Position.Y)
		local rp = RaycastParams.new()
		rp.FilterType = Enum.RaycastFilterType.Include
		rp.FilterDescendantsInstances = { signPart }
		local hit = workspace:Raycast(ray.Origin, ray.Direction * 120, rp)
		if not hit or hit.Normal:Dot(signPart.CFrame.LookVector) > -0.5 then
			return -- missed, or not the Back face (the side facing the plaza)
		end
		local lp = signPart.CFrame:PointToObjectSpace(hit.Position)
		local u, v = lp.X / signPart.Size.X + 0.5, 0.5 - lp.Y / signPart.Size.Y
		if u > 0.05 and u < 0.95 and v > 0.66 and v < 0.97 then
			buyTrain()
		end
	end)
	local function build(part)
		signPart = part
		if sg then
			sg:Destroy()
		end
		for _, q in ipairs(shown or {}) do
			q.LocalTransparencyModifier = 0
			q.Transparency = 1
		end
		shown = {}
		for _, q in ipairs(part.Parent:GetChildren()) do -- this base's board + its back plate: visible only here
			if q:IsA("BasePart") and (q.Name == "TreadSign" or q.Name == "TreadSignBack") then
				q.Transparency = 0
				table.insert(shown, q)
			end
		end
		sg = make("SurfaceGui", {
			Name = "TreadSignUI", Adornee = part, Face = Enum.NormalId.Back, SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud,
			PixelsPerStud = 80, LightInfluence = 0, ResetOnSpawn = false, ZIndexBehavior = Enum.ZIndexBehavior.Sibling,
		}, plr:WaitForChild("PlayerGui"))
		local bg = make("Frame", { Size = UDim2.fromScale(1, 1), BackgroundColor3 = WHITE, BorderSizePixel = 0 }, sg)
		make("UICorner", { CornerRadius = UDim.new(0.1, 0) }, bg)
		make("UIStroke", { Thickness = 10, Color = GOLDLINE, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, bg)
		make("UIGradient", { Rotation = 90, Color = ColorSequence.new(NAVY1, NAVY2) }, bg)
		-- header: bolt + TREADMILL
		local ic = icon(bg, "bolt", UDim2.fromScale(0.16, 0.24), UDim2.fromScale(0.06, 0.05))
		make("UIAspectRatioConstraint", { AspectRatio = 1 }, ic)
		local head = make("TextLabel", {
			BackgroundTransparency = 1, Size = UDim2.fromScale(0.62, 0.16), Position = UDim2.fromScale(0.22, 0.08), Font = Enum.Font.LuckiestGuy,
			TextScaled = true, TextColor3 = GOLDLINE, Text = "TREADMILL", TextXAlignment = Enum.TextXAlignment.Left,
		}, bg)
		make("UIStroke", { Thickness = 4, Color = BLACK }, head)
		make("Frame", { Size = UDim2.fromScale(0.88, 0.012), Position = UDim2.fromScale(0.06, 0.3), BackgroundColor3 = GOLDLINE, BackgroundTransparency = 0.4, BorderSizePixel = 0 }, bg)
		lvT = make("TextLabel", {
			BackgroundTransparency = 1, Size = UDim2.fromScale(0.88, 0.2), Position = UDim2.fromScale(0.06, 0.34), Font = Enum.Font.LuckiestGuy,
			TextScaled = true, RichText = true, TextColor3 = WHITE, Text = "",
		}, bg)
		make("UIStroke", { Thickness = 5, Color = BLACK }, lvT)
		spT = make("TextLabel", {
			BackgroundTransparency = 1, Size = UDim2.fromScale(0.88, 0.11), Position = UDim2.fromScale(0.06, 0.55), Font = Enum.Font.FredokaOne,
			TextScaled = true, RichText = true, TextColor3 = Color3.fromRGB(150, 210, 255), Text = "",
		}, bg)
		make("UIStroke", { Thickness = 3, Color = BLACK }, spT)
		btn = make("TextButton", {
			AutoButtonColor = false, Text = "", Size = UDim2.fromScale(0.84, 0.22), Position = UDim2.fromScale(0.08, 0.71), BackgroundColor3 = WHITE,
		}, bg)
		make("UICorner", { CornerRadius = UDim.new(0.3, 0) }, btn)
		make("UIStroke", { Thickness = 5, Color = BLACK, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, btn)
		local bgr = make("UIGradient", { Rotation = 90, Color = ColorSequence.new(Color3.fromRGB(150, 250, 120), Color3.fromRGB(36, 168, 64)) }, btn)
		btnT = make("TextLabel", {
			BackgroundTransparency = 1, Size = UDim2.fromScale(0.9, 0.72), Position = UDim2.fromScale(0.05, 0.14), Font = Enum.Font.LuckiestGuy,
			TextScaled = true, TextColor3 = WHITE, Text = "",
		}, btn)
		make("UIStroke", { Thickness = 4, Color = BLACK }, btnT)
		btn.Activated:Connect(function()
			buyTrain()
		end)
		btn.Name = "Buy"
		bgr.Name = "Grad"
	end
	local function refresh()
		if not lvT then
			return
		end
		local lv = attr("TrainLv", 0)
		local grad = btn:FindFirstChild("Grad")
		if lv >= C.MAX_LV.train then
			lvT.Text = "LEVEL " .. lv
			spT.Text = "+" .. C.fmt(C.trainPower(lv)) .. " speed"
			btnT.Text = "MAX"
			grad.Color = ColorSequence.new(Color3.fromRGB(200, 204, 220), Color3.fromRGB(120, 124, 146))
		else
			lvT.Text = "LV " .. lv .. ' <font color="#7CFF6B">></font> ' .. (lv + 1)
			spT.Text = "+" .. C.fmt(C.trainPower(lv)) .. ' <font color="#7CFF6B">></font> +' .. C.fmt(C.trainPower(lv + 1)) .. " speed"
			local cost = C.cost("train", lv)
			btnT.Text = "\u{25B2} $" .. C.fmt(cost)
			local can = attr("Cash", 0) >= cost
			grad.Color = can and ColorSequence.new(Color3.fromRGB(150, 250, 120), Color3.fromRGB(36, 168, 64))
				or ColorSequence.new(Color3.fromRGB(200, 204, 220), Color3.fromRGB(120, 124, 146))
		end
	end
	local function attach()
		local i = attr("Base", 0)
		local map = workspace:FindFirstChild("Map")
		local b = map and i > 0 and map:FindFirstChild("Base" .. i)
		local part = b and b:FindFirstChild("TreadSign", true)
		if part then
			build(part)
			refresh()
		end
	end
	task.spawn(function()
		workspace:WaitForChild("Map", 30)
		attach()
	end)
	plr:GetAttributeChangedSignal("Base"):Connect(attach)
	plr.AttributeChanged:Connect(refresh)
end


-- ============================================================ BIG EGG DROP (client): Codex VFX modules + animation clips
task.spawn(function()
	local LP = Players.LocalPlayer
	local fxFolder = RS:WaitForChild("BigEggFX", 30)
	local BigEgg = Remotes:WaitForChild("BigEgg", 30)
	local BigEggSwing = Remotes:WaitForChild("BigEggSwing", 30)
	if not fxFolder or not BigEgg then
		return
	end
	local VFX = require(fxFolder:WaitForChild("BigEggVFX"))
	local WFX = require(fxFolder:WaitForChild("WeaponFX"))
	local vfxMod, wfxMod = fxFolder.BigEggVFX, fxFolder.WeaponFX

	-- animation ids: published ids from Config, or in Studio the bundled KeyframeSequences
	local ids = {}
	local KSP = game:GetService("KeyframeSequenceProvider")
	local anims = RS:FindFirstChild("BigEggAnims")
	local CLIP = { SwingHammerR6 = "BonkHammer_R6", SwingHammerR15 = "BonkHammer_R15", SwingPillowR6 = "PillowBat_R6", SwingPillowR15 = "PillowBat_R15",
		HitR6 = "Hit_R6", HitR15 = "Hit_R15", ClaimR6 = "Claim_R6", ClaimR15 = "Claim_R15", CelebrateR6 = "Celebrate_R6", CelebrateR15 = "Celebrate_R15" }
	for key, clip in pairs(CLIP) do
		local pub = C.BIGEGG_ANIMS and C.BIGEGG_ANIMS[key]
		if pub and pub ~= "" then
			ids[key] = pub
		elseif RunService:IsStudio() and anims and anims:FindFirstChild(clip) then
			local ok, id = pcall(KSP.RegisterKeyframeSequence, KSP, anims[clip])
			if ok then
				ids[key] = id
			end
		end
	end
	local function setA(inst, name, v)
		if v and v ~= "" then
			inst:SetAttribute(name, v)
		end
	end
	for _, r in ipairs({ "R6", "R15" }) do
		setA(wfxMod, "Hit" .. r, ids["Hit" .. r])
		setA(vfxMod, "Claim" .. r, ids["Claim" .. r])
		setA(vfxMod, "Celebrate" .. r, ids["Celebrate" .. r])
	end
	setA(wfxMod, "HitSound", C.BIGEGG_ANIMS and C.BIGEGG_ANIMS.HitSound)
	setA(vfxMod, "ScorchTexture", C.BIGEGG_ANIMS and C.BIGEGG_ANIMS.ScorchTexture)

	-- weapons: swing clip on the tool, swing -> server checks the hit
	local function hookTool(tool)
		if not tool:IsA("Tool") or not tool:GetAttribute("BigEggWeapon") or tool:GetAttribute("Hooked") then
			return
		end
		tool:SetAttribute("Hooked", true)
		local kind = tool:GetAttribute("BigEggWeapon")
		for _, r in ipairs({ "R6", "R15" }) do
			setA(tool, "Swing" .. r, ids["Swing" .. kind .. r])
		end
		local last = 0
		tool.Activated:Connect(function()
			if os.clock() - last < C.BIGEGG_WEAPON_CD then
				return
			end
			last = os.clock()
			pcall(WFX.PlaySwing, tool)
			BigEggSwing:FireServer()
		end)
	end
	local function watch(container)
		if container then
			for _, t in ipairs(container:GetChildren()) do
				hookTool(t)
			end
			container.ChildAdded:Connect(hookTool)
		end
	end
	watch(LP:WaitForChild("Backpack", 30))
	LP.CharacterAdded:Connect(function(ch)
		watch(ch)
		watch(LP:WaitForChild("Backpack", 10))
	end)
	if LP.Character then
		watch(LP.Character)
	end

	-- the egg everybody sees: the imported Blender egg if it is there, else the golden egg mesh made 10 studs tall
	local egg, pos = nil, nil
	local function makeEgg()
		local A = RS:FindFirstChild("Assets")
		local src = A and (A:FindFirstChild("BigEgg") or A:FindFirstChild("Egg_Gold"))
		local e
		if src then
			e = src:Clone()
			if e:IsA("BasePart") then
				local k = C.BIGEGG_SIZE / e.Size.Y
				e.Size = e.Size * k
			end
		else
			e = Instance.new("Part")
			e.Shape = Enum.PartType.Ball
			e.Size = Vector3.new(C.BIGEGG_SIZE * 0.8, C.BIGEGG_SIZE, C.BIGEGG_SIZE * 0.8)
			e.Color, e.Material = Color3.fromRGB(255, 200, 60), Enum.Material.Neon
		end
		for _, p in ipairs(e:IsA("BasePart") and { e } or e:GetDescendants()) do
			if p:IsA("BasePart") then
				p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, false, false
			end
		end
		e.Name = "BigEggVisual"
		e:PivotTo(CFrame.new(pos + Vector3.new(0, 200, 0)))
		e.Parent = workspace
		return e
	end
	local function charOf(userId)
		local p = Players:GetPlayerByUserId(userId)
		return p and p.Character
	end
	local claimConn
	local function stopClaim()
		if claimConn then
			claimConn:Disconnect()
			claimConn = nil
		end
	end
	-- an example of the pets this egg can give: they turn above the egg one after the other
	local preview, previewConn
	local function stopPreview()
		if previewConn then
			previewConn:Disconnect()
			previewConn = nil
		end
		if preview then
			preview:Destroy()
			preview = nil
		end
	end
	local function startPreview(at)
		stopPreview()
		local z = math.clamp(math.floor(at.Z / C.ZONE_LEN) + 1, 1, C.NZ)
		local pets = C.ZONES[z].pets
		preview = Instance.new("Folder")
		preview.Name = "BigEggPreview"
		preview.Parent = workspace
		local anchor = Instance.new("Part")
		anchor.Anchored, anchor.CanCollide, anchor.CanQuery, anchor.CanTouch, anchor.Transparency = true, false, false, false, 1
		anchor.Size = Vector3.new(1, 1, 1)
		anchor.Position = at + Vector3.new(0, C.BIGEGG_SIZE * 0.66 + 8, 0)
		anchor.Parent = preview
		local bb = Instance.new("BillboardGui")
		bb.Size, bb.StudsOffset, bb.AlwaysOnTop, bb.LightInfluence = UDim2.fromOffset(240, 64), Vector3.new(0, 5.2, 0), true, 0
		bb.Parent = anchor
		local nameL = Instance.new("TextLabel")
		nameL.BackgroundTransparency, nameL.Size, nameL.Font, nameL.TextScaled, nameL.TextColor3 = 1, UDim2.fromScale(1, 0.58), Enum.Font.FredokaOne, true, Color3.new(1, 1, 1)
		nameL.Parent = bb
		local st = Instance.new("UIStroke")
		st.Thickness, st.Color = 3, Color3.fromRGB(25, 15, 45)
		st.Parent = nameL
		local oddsL = nameL:Clone()
		oddsL.Size, oddsL.Position, oddsL.Font = UDim2.fromScale(1, 0.4), UDim2.fromScale(0, 0.6), Enum.Font.GothamBold
		oddsL.Parent = bb
		local RC = { Color3.fromRGB(235, 240, 255), Color3.fromRGB(90, 255, 130), Color3.fromRGB(60, 200, 255), Color3.fromRGB(210, 90, 255), Color3.fromRGB(255, 200, 40) }
		local model, idx, t0, fit = nil, 0, 0, 1
		local function nextPet()
			if model then
				model:Destroy()
			end
			idx = idx % #pets + 1
			local ok, m = pcall(C.buildPet, { z = z, i = idx, t = 1 }, 1, true)
			if not ok then
				return
			end
			model = m
			model.Parent = preview
			local _, size = model:GetBoundingBox()
			fit = 6 / math.max(size.X, size.Y, size.Z, 0.5)
			nameL.Text = pets[idx].name
			nameL.TextColor3 = RC[math.min(idx, 5)]
			oddsL.Text = "1 in " .. C.comma(C.RARITY[idx].odds)
			t0 = os.clock()
		end
		nextPet()
		previewConn = RunService.RenderStepped:Connect(function()
			local t = os.clock() - t0
			if t > 2 then
				nextPet()
				t = 0
			end
			if model then
				local pop = math.min(t / 0.25, 1)
				local k = fit * (pop < 1 and (0.3 + 0.7 * math.sin(pop * math.pi / 2) * 1.1) or 1) * (t > 1.8 and (1 - (t - 1.8) / 0.2) or 1)
				pcall(function()
					model:ScaleTo(math.max(k, 0.01))
					model:PivotTo(CFrame.new(anchor.Position + Vector3.new(0, math.sin(os.clock() * 2) * 0.5, 0)) * CFrame.Angles(0, os.clock() * 1.4, 0))
				end)
			end
		end)
	end
	local function clear()
		stopPreview()
		stopClaim()
		pcall(VFX.Clear)
		if egg then
			egg:Destroy()
			egg = nil
		end
	end
	local cinema = false -- Studio F8 test: a film camera circles the landing spot, the player is put next to the egg
	local function cinemaCam(p)
		local cam = workspace.CurrentCamera
		local t0 = os.clock()
		cam.CameraType = Enum.CameraType.Scriptable
		local conn
		conn = RunService.RenderStepped:Connect(function()
			local t = os.clock() - t0
			if t > 34 then
				conn:Disconnect()
				cam.CameraType = Enum.CameraType.Custom
				return
			end
			-- wide while it falls, closer once it sits in the crater
			local r = t < 11 and 70 - t * 2 or math.max(30, 48 - (t - 11) * 1.2)
			local a = 0.6 + t * 0.12
			local h = t < 11 and 34 or 14
			local look = p + Vector3.new(0, t < 10 and 18 - t * 1.2 or 4, 0)
			cam.CFrame = CFrame.lookAt(p + Vector3.new(math.cos(a) * r, h, math.sin(a) * r), look)
		end)
		task.delay(12.6, function()
			local root = LP.Character and LP.Character:FindFirstChild("HumanoidRootPart")
			if root then
				root.CFrame = CFrame.lookAt(p + Vector3.new(17, 3, 0), p + Vector3.new(0, 3, 0))
			end
		end)
	end
	BigEgg.OnClientEvent:Connect(function(cue, a, b)
		if cue == "incoming" then
			clear()
			pos = a
			pcall(VFX.PlayIncoming, pos)
			if cinema then
				cinema = false
				cinemaCam(pos)
			end
		elseif cue == "fall" then
			pos = a
			egg = makeEgg()
			pcall(VFX.PlayFall, egg, pos)
			task.delay(1.4, function()
				pcall(VFX.PlayImpact, pos)
				-- whoever stands under the egg when it hits is thrown to the side (each client pushes its own character)
				local ch = LP.Character
				local root = ch and ch:FindFirstChild("HumanoidRootPart")
				local hum = ch and ch:FindFirstChildOfClass("Humanoid")
				if root and hum then
					local off = Vector3.new(root.Position.X - pos.X, 0, root.Position.Z - pos.Z)
					local reach = C.BIGEGG_SIZE * 0.8
					if off.Magnitude < reach and math.abs(root.Position.Y - pos.Y) < C.BIGEGG_SIZE then
						local dir = off.Magnitude > 0.1 and off.Unit or Vector3.new(math.random() - 0.5, 0, math.random() - 0.5).Unit
						local power = 1 - off.Magnitude / reach * 0.5
						hum:ChangeState(Enum.HumanoidStateType.FallingDown)
						root.AssemblyLinearVelocity = Vector3.zero
						root:ApplyImpulse(root.AssemblyMass * (dir * 120 * power + Vector3.yAxis * 60))
						task.delay(1.2, function()
							if hum.Parent and hum:GetState() == Enum.HumanoidStateType.FallingDown then
								hum:ChangeState(Enum.HumanoidStateType.GettingUp)
							end
						end)
					end
				end
			end)
			task.delay(1.7, function()
				if egg then
					-- landed: the egg is solid now (players walk round it, not through it)
					for _, q in ipairs(egg:IsA("BasePart") and { egg } or egg:GetDescendants()) do
						if q:IsA("BasePart") then
							q.CanCollide, q.CanQuery = true, true
						end
					end
					pcall(VFX.PlayClaimProgress, egg, 0)
				end
			end)
		elseif cue == "claim" and egg then
			stopClaim()
			local who, t0 = charOf(a), b
			claimConn = RunService.RenderStepped:Connect(function()
				local p = (workspace:GetServerTimeNow() - t0) / C.BIGEGG_CLAIM
				pcall(VFX.PlayClaimProgress, egg, math.clamp(p, 0, 1), who)
			end)
		elseif cue == "release" and egg then
			stopClaim()
			if b then
				pcall(VFX.PlayClaimBreak, egg)
				task.delay(0.35, function()
					if egg then
						pcall(VFX.PlayClaimProgress, egg, 0)
					end
				end)
			else
				pcall(VFX.PlayClaimProgress, egg, 0)
			end
		elseif cue == "hit" then
			local ch = charOf(a)
			if ch then
				pcall(WFX.PlayHit, ch, nil, b)
				if a == LP.UserId then
					local root = ch:FindFirstChild("HumanoidRootPart")
					if root then
						root:ApplyImpulse(root.AssemblyMass * (b * 55 + Vector3.yAxis * 28))
					end
				end
			end
		elseif cue == "win" and egg then
			stopClaim()
			stopPreview()
			pcall(VFX.PlayWin, egg, b, charOf(a))
		elseif cue == "clear" then
			clear()
		end
	end)

	-- STUDIO ONLY: F8 = start a BIG EGG drop now
	if RunService:IsStudio() then
		game:GetService("UserInputService").InputBegan:Connect(function(input, typing)
			if input.KeyCode == Enum.KeyCode.F7 and not typing then
				Action:FireServer("altartest")
			end
			if input.KeyCode == Enum.KeyCode.F8 and not typing then
				cinema = true
				Action:FireServer("bigegg")
			end
		end)
	end
end)

-- ============================================================ GOLDEN NEST ALTARS (client, v111)
task.spawn(function()
	local LP = Players.LocalPlayer
	local GoldenAltar = Remotes:WaitForChild("GoldenAltar", 30)
	local Map = workspace:WaitForChild("Map", 30)
	if not GoldenAltar or not Map then
		return
	end
	local altars, egg, beam, block = {}, nil, nil, nil
	for _, d0 in ipairs(Map:GetDescendants()) do
		local n = d0:IsA("BasePart") and tonumber(string.match(d0.Name, "^EggAltar(%d+)$"))
		if n then
			altars[n] = d0
		elseif d0.Name == "GoldenEgg" and d0:IsA("BasePart") then
			egg = d0
		elseif d0.Name == "GoldenBeam" and d0:IsA("BasePart") then
			beam = d0
		elseif d0.Name == "GoldenEggBlock" and d0:IsA("BasePart") then
			block = d0
		end
	end
	-- Codex's effects when they are there (ReplicatedStorage.BigEggFX.GoldenPortalVFX), else a simple fallback
	local fxFolder = RS:FindFirstChild("BigEggFX")
	local mod = fxFolder and fxFolder:FindFirstChild("GoldenPortalVFX")
	local V = nil
	if mod then
		local ok, m = pcall(require, mod)
		if ok then
			V = m
		end
	end
	local TS = game:GetService("TweenService")
	local function zoneCol(n)
		local c = C.ZONES[n].eggCol
		return Color3.fromRGB(c[1], c[2], c[3])
	end
	local function eggModel(n)
		local A = RS:FindFirstChild("Assets")
		local src = A and A:FindFirstChild("Egg_" .. n)
		local e
		if src then
			e = src:Clone()
			e.Size = e.Size * (3.6 / math.max(e.Size.X, e.Size.Y, e.Size.Z))
		else
			e = Instance.new("Part")
			e.Shape = Enum.PartType.Ball
			e.Size = Vector3.new(2.8, 3.6, 2.8)
			e.Color = zoneCol(n)
		end
		e.Anchored, e.CanCollide, e.CanQuery, e.CanTouch = true, false, false, false
		e.Name = "AltarEgg" .. n
		return e
	end
	local placed = {}
	local function putEgg(n, animate)
		local a = altars[n]
		if not a or placed[n] then
			return
		end
		local e = eggModel(n)
		local top = a.Position + Vector3.new(0, a.Size.Y / 2 + 1.9, 0)
		e.CFrame = CFrame.new(top)
		e.Parent = workspace
		placed[n] = e
		local pp = a:FindFirstChildOfClass("ProximityPrompt")
		if pp then
			pp.Enabled = false -- this player already filled it
		end
		if V then
			pcall(animate and V.PlayPlace or V.ShowPlaced, a, e, zoneCol(n))
		elseif animate then
			e.CFrame = CFrame.new(top + Vector3.new(0, 14, 0))
			TS:Create(e, TweenInfo.new(0.6, Enum.EasingStyle.Bounce, Enum.EasingDirection.Out), { CFrame = CFrame.new(top) }):Play()
		end
	end
	local portal
	local function openPortal(animate)
		if not egg or portal then
			return
		end
		local at = egg.Position
		local ground = (block and block.Position.Y - block.Size.Y / 2) or (at.Y - egg.Size.Y / 2)
		if block then
			block.CanCollide = false
		end
		local function show()
			if V then
				local ok, p = pcall(V.ShowPortal, Vector3.new(at.X, ground, at.Z), 30) -- Codex: position = ground point under the opening
				portal = ok and p or true
			else
				local p = Instance.new("Part")
				p.Shape, p.Anchored, p.CanCollide, p.Material = Enum.PartType.Cylinder, true, false, Enum.Material.Neon
				p.Size, p.Color, p.Transparency = Vector3.new(1.5, 28, 28), Color3.fromRGB(190, 120, 255), 0.25
				p.CFrame = CFrame.new(at.X, ground + 16, at.Z) * CFrame.Angles(0, math.pi / 2, 0)
				p.Name = "GoldenPortal"
				p.Parent = workspace
				portal = p
			end
		end
		if animate then
			if V then
				pcall(V.PlaySink, egg, beam, ground, show)
			else
				egg.CanCollide = false
				TS:Create(egg, TweenInfo.new(5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { CFrame = egg.CFrame - Vector3.new(0, egg.Size.Y + 4, 0) }):Play()
				if beam then
					beam.LocalTransparencyModifier = 1
				end
				task.delay(5.2, function()
					egg.LocalTransparencyModifier = 1
					show()
				end)
			end
		else
			egg.CanCollide = false
			if V then
				pcall(V.ShowSunk, egg, beam)
			else
				egg.LocalTransparencyModifier = 1
				if beam then
					beam.LocalTransparencyModifier = 1
				end
			end
			show()
		end
	end
	-- what this player already did (join)
	local function fromSave()
		local n = 0
		for _, z in ipairs(string.split(LP:GetAttribute("Altar") or "", ",")) do
			z = tonumber(z)
			if z then
				putEgg(z, false)
				n = n + 1
			end
		end
		if n >= C.NZ then
			openPortal(false)
		end
	end
	if LP:GetAttribute("Altar") ~= nil then
		fromSave()
	else
		LP:GetAttributeChangedSignal("Altar"):Once(fromSave)
	end
	GoldenAltar.OnClientEvent:Connect(function(cue, n)
		if cue == "place" then
			putEgg(n, true)
		elseif cue == "sink" then
			openPortal(true)
		end
	end)
	-- small name tag over every altar (zone name in its colour), only when you are close
	for n, a in pairs(altars) do
		local bb = Instance.new("BillboardGui")
		bb.Size, bb.StudsOffset, bb.MaxDistance, bb.AlwaysOnTop = UDim2.fromOffset(180, 34), Vector3.new(0, 7.5, 0), 60, true
		bb.Parent = a
		local t = Instance.new("TextLabel")
		t.BackgroundTransparency, t.Size, t.Font, t.TextScaled = 1, UDim2.fromScale(1, 1), Enum.Font.FredokaOne, true
		t.Text, t.TextColor3 = n .. ". " .. C.ZONES[n].name, zoneCol(n)
		t.Parent = bb
		local st = Instance.new("UIStroke")
		st.Thickness, st.Color = 2.5, Color3.fromRGB(30, 20, 40)
		st.Parent = t
	end
end)

-- ============================================================ COSMIC NEST (client, v116)
-- On the secret island (high above the map): night sky with stars, purple light, low gravity and a big title.
-- Everything is local to this player and goes back to normal when they leave.
task.spawn(function()
	local Lighting = game:GetService("Lighting")
	local TweenS = game:GetService("TweenService")
	local CO = C.COSMIC
	local player = game:GetService("Players").LocalPlayer
	local inside, saved = false, nil
	local bannerUntil = 0
	player:GetAttributeChangedSignal("Unlocked"):Connect(function()
		bannerUntil = os.clock() + 3.4 -- v131: the NEW ZONE UNLOCKED banner is showing (same spot as the zone title)
	end)
	local function title(name, sub)
		task.wait(0.15)
		if os.clock() < bannerUntil then
			task.wait(bannerUntil - os.clock())
		end
		local pg = player:FindFirstChildOfClass("PlayerGui")
		if not pg then
			return
		end
		local sg = Instance.new("ScreenGui")
		sg.Name, sg.ResetOnSpawn, sg.IgnoreGuiInset = "CosmicTitle", false, true
		local t = Instance.new("TextLabel")
		t.BackgroundTransparency, t.AnchorPoint = 1, Vector2.new(0.5, 0.5)
		t.Position, t.Size = UDim2.fromScale(0.5, 0.3), UDim2.fromScale(0.8, 0.12)
		t.Font, t.TextScaled, t.Text = Enum.Font.FredokaOne, true, name
		t.TextColor3, t.TextTransparency = Color3.fromRGB(200, 170, 255), 1
		t.Parent = sg
		local st = Instance.new("UIStroke")
		st.Thickness, st.Color = 4, Color3.fromRGB(30, 10, 70)
		st.Parent = t
		local g = Instance.new("UIGradient")
		g.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(120, 230, 255)), ColorSequenceKeypoint.new(0.5, Color3.fromRGB(255, 255, 255)), ColorSequenceKeypoint.new(1, Color3.fromRGB(255, 120, 230)) })
		g.Parent = t
		local s = Instance.new("TextLabel")
		s.BackgroundTransparency, s.AnchorPoint = 1, Vector2.new(0.5, 0)
		s.Position, s.Size = UDim2.fromScale(0.5, 0.36), UDim2.fromScale(0.6, 0.05)
		s.Font, s.TextScaled, s.Text = Enum.Font.FredokaOne, true, sub
		s.TextColor3, s.TextTransparency = Color3.new(1, 1, 1), 1
		s.Parent = sg
		sg.Parent = pg
		local info = TweenInfo.new(0.8)
		TweenS:Create(t, info, { TextTransparency = 0 }):Play()
		TweenS:Create(s, info, { TextTransparency = 0 }):Play()
		task.delay(3.5, function()
			TweenS:Create(t, info, { TextTransparency = 1 }):Play()
			TweenS:Create(s, info, { TextTransparency = 1 }):Play()
			task.wait(1)
			sg:Destroy()
		end)
	end
	local function enter()
		local atm = Lighting:FindFirstChildOfClass("Atmosphere")
		saved = {
			clock = Lighting.ClockTime, bright = Lighting.Brightness, amb = Lighting.Ambient, oamb = Lighting.OutdoorAmbient,
			grav = workspace.Gravity, atm = atm, dens = atm and atm.Density, haze = atm and atm.Haze, col = atm and atm.Color,
		}
		Lighting.ClockTime = 0
		Lighting.Brightness = 2
		Lighting.Ambient = Color3.fromRGB(70, 50, 120)
		Lighting.OutdoorAmbient = Color3.fromRGB(120, 100, 190)
		if atm then
			atm.Density, atm.Haze, atm.Color = 0.05, 0, Color3.fromRGB(40, 20, 80)
		end
		workspace.Gravity = CO.gravity
	end
	local function leave()
		if not saved then
			return
		end
		Lighting.ClockTime, Lighting.Brightness = saved.clock, saved.bright
		Lighting.Ambient, Lighting.OutdoorAmbient = saved.amb, saved.oamb
		if saved.atm then
			saved.atm.Density, saved.atm.Haze, saved.atm.Color = saved.dens, saved.haze, saved.col
		end
		workspace.Gravity = saved.grav
		saved = nil
	end
	-- the exit portal at the start of world 2: the same portal as in the Golden Nest (Codex), from a copy of the
	-- module so both portals can be on screen at once
	task.spawn(function()
		local fx = RS:WaitForChild("BigEggFX", 30)
		local mod = fx and fx:FindFirstChild("GoldenPortalVFX")
		local at = Vector3.new(CO.exit[1], CO.exit[2], CO.exit[3])
		local ok = false
		if mod then
			local copy = mod:Clone()
			copy.Name = "ExitPortalVFX"
			copy.Parent = fx
			local okReq, V2 = pcall(require, copy)
			if okReq and V2 and V2.ShowPortal then
				ok = pcall(V2.ShowPortal, at, 26, "cosmic") -- v125: new portal, cosmic (cyan) theme here
			end
		end
		if not ok then -- fallback: a glowing ring
			local p = Instance.new("Part")
			p.Shape, p.Anchored, p.CanCollide, p.Material = Enum.PartType.Cylinder, true, false, Enum.Material.Neon
			p.Size, p.Color, p.Transparency = Vector3.new(1.5, 24, 24), Color3.fromRGB(190, 120, 255), 0.25
			p.CFrame = CFrame.new(at + Vector3.new(0, 13, 0)) * CFrame.Angles(0, math.pi / 2, 0)
			p.Name = "ExitPortal"
			p.Parent = workspace
		end
	end)
	-- v131: world 2 is not drawn while you are in world 1 (it hung in the sky). Its models wait in a client-only folder;
	-- they come back near the Golden Nest (before the portal) and up there.
	local Map = workspace:WaitForChild("Map")
	local hideBox = Instance.new("Folder")
	hideBox.Name = "World2Hidden"
	local w2models = {}
	for _, m in ipairs(Map:GetChildren()) do
		local n = m.Name
		if n:match("^Zone1[1-9]_") or n:match("^Zone20_") or n:match("^W2") or n == "SaturnRing" then
			table.insert(w2models, m)
		end
	end
	local w2shown = true
	-- v136: things made at run time up there (exit portal VFX + its beams, portal extras, server props) are not in
	-- Map, so they still hung in the sky of world 1. Anything directly in workspace above y 300 is hidden too.
	local w2loose = {}
	local function sweepLoose()
		local list = workspace:GetChildren()
		local gates = workspace:FindFirstChild("ZoneGates") -- world 2 gates: thin glowing walls = long lines from below
		if gates then
			for _, g in ipairs(gates:GetChildren()) do
				table.insert(list, g)
			end
		end
		for _, o in ipairs(list) do
			if o ~= Map and o ~= workspace.CurrentCamera and not o:IsA("Terrain") and not Players:GetPlayerFromCharacter(o) then
				local y
				if o:IsA("BasePart") then
					y = o.Position.Y
				elseif o:IsA("Model") then
					local okP, cf = pcall(o.GetPivot, o)
					y = okP and cf.Position.Y or nil
				elseif o:IsA("Folder") and o.Name == "GoldenNest_ClientFX" then -- each portal copy has its own folder
					local bp = o:FindFirstChildWhichIsA("BasePart", true)
					y = bp and bp.Position.Y or nil
				end -- other folders are left alone (e.g. the eggs folder holds both worlds)
				if y and y > 300 then
					table.insert(w2loose, { o, o.Parent })
					o.Parent = hideBox
				end
			end
		end
	end
	local function showWorld2(on)
		if on == w2shown then
			return
		end
		w2shown = on
		for _, m in ipairs(w2models) do
			m.Parent = on and Map or hideBox
		end
		if on then
			for _, e in ipairs(w2loose) do
				if e[1].Parent == hideBox then
					e[1].Parent = e[2]
				end
			end
			table.clear(w2loose)
		else
			sweepLoose()
		end
	end
	task.spawn(function() -- new things keep appearing (VFX, eggs up there): sweep again every few seconds
		while true do
			task.wait(3)
			if not w2shown then
				sweepLoose()
			end
		end
	end)
	-- Saturn's ring: tilted, slowly turning
	local ring = Map:FindFirstChild("SaturnRing")
	local sat = CO.saturn
	if ring and sat then
		local centre = Vector3.new(sat[1], sat[2], sat[3])
		local _, size = ring:GetBoundingBox()
		ring.WorldPivot = CFrame.new(centre)
		local spin = 0
		game:GetService("RunService").Heartbeat:Connect(function(dt)
			if w2shown then
				spin = spin + dt * 0.08
				ring:PivotTo(CFrame.new(centre) * CFrame.Angles(sat[4], 0, sat[4] * 0.4) * CFrame.Angles(0, spin, 0))
			end
		end)
	end
	-- the moment you go through a portal: a violet flash + whoosh of light
	local function portalFlash(col)
		local pg = player:FindFirstChildOfClass("PlayerGui")
		if not pg then
			return
		end
		local sg = Instance.new("ScreenGui")
		sg.Name, sg.IgnoreGuiInset, sg.ResetOnSpawn, sg.DisplayOrder = "PortalFlash", true, false, 50
		local f = Instance.new("Frame")
		f.Size, f.BackgroundColor3, f.BackgroundTransparency, f.BorderSizePixel = UDim2.fromScale(1, 1), col, 0.05, 0
		f.Parent = sg
		local g = Instance.new("UIGradient")
		g.Color = ColorSequence.new(Color3.new(1, 1, 1), col)
		g.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 0.35) })
		g.Parent = f
		sg.Parent = pg
		local cam = workspace.CurrentCamera
		local fov = cam.FieldOfView
		cam.FieldOfView = math.min(fov + 25, 110)
		TweenS:Create(cam, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { FieldOfView = fov }):Play()
		local t = TweenS:Create(f, TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { BackgroundTransparency = 1 })
		t:Play()
		t.Completed:Connect(function()
			sg:Destroy()
		end)
	end
	-- extra life for both portals: swirling sparks pulled into the centre, a ground glow ring, a pulsing light
	local function portalExtras(at, size, col)
		local h = size
		local p = Instance.new("Part")
		p.Name = "PortalExtras"
		p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.Transparency = true, false, false, false, 1
		p.Size = Vector3.new(h * 0.7, h * 0.9, 1)
		p.CFrame = CFrame.new(at + Vector3.new(0, h * 0.5, 0))
		p.Parent = workspace
		local a0 = Instance.new("Attachment")
		a0.Parent = p
		local suck = Instance.new("ParticleEmitter") -- sparks spawn around the rim and fall into the middle
		suck.Shape, suck.ShapeStyle, suck.ShapeInOut = Enum.ParticleEmitterShape.Box, Enum.ParticleEmitterShapeStyle.Surface, Enum.ParticleEmitterShapeInOut.Inward
		suck.Texture = "rbxasset://textures/particles/sparkles_main.dds"
		suck.Color, suck.LightEmission, suck.LightInfluence = ColorSequence.new(Color3.new(1, 1, 1), col), 1, 0
		suck.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.9), NumberSequenceKeypoint.new(1, 0) })
		suck.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 1) })
		suck.Lifetime, suck.Rate, suck.Speed = NumberRange.new(0.8, 1.3), 40, NumberRange.new(6, 10)
		suck.RotSpeed, suck.Rotation = NumberRange.new(-180, 180), NumberRange.new(0, 360)
		suck.Parent = p
		local mist = Instance.new("ParticleEmitter") -- slow glowing mist in front of the swirl
		mist.Texture = "rbxasset://textures/particles/smoke_main.dds"
		mist.Color, mist.LightEmission, mist.LightInfluence = ColorSequence.new(col), 0.8, 0
		mist.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, h * 0.15), NumberSequenceKeypoint.new(1, h * 0.35) })
		mist.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.85), NumberSequenceKeypoint.new(0.5, 0.7), NumberSequenceKeypoint.new(1, 1) })
		mist.Lifetime, mist.Rate, mist.Speed, mist.RotSpeed = NumberRange.new(2, 3), 6, NumberRange.new(0.5, 1), NumberRange.new(-20, 20)
		mist.Parent = p
		local light = Instance.new("PointLight")
		light.Color, light.Range, light.Brightness, light.Shadows = col, h * 1.4, 3, false
		light.Parent = p
		local ringPart = Instance.new("Part") -- glowing circle on the ground
		ringPart.Name = "PortalGroundGlow"
		ringPart.Shape = Enum.PartType.Cylinder
		ringPart.Anchored, ringPart.CanCollide, ringPart.CanQuery, ringPart.CanTouch = true, false, false, false
		ringPart.Material, ringPart.Color, ringPart.Transparency = Enum.Material.Neon, col, 0.55
		ringPart.Size = Vector3.new(0.15, h * 0.9, h * 0.9)
		ringPart.CFrame = CFrame.new(at + Vector3.new(0, 0.12, 0)) * CFrame.Angles(0, 0, math.pi / 2)
		ringPart.Parent = workspace
		local t0 = os.clock()
		game:GetService("RunService").Heartbeat:Connect(function()
			local t = os.clock() - t0
			light.Brightness = 2.6 + math.sin(t * 2.4) * 1.1
			ringPart.Transparency = 0.5 + math.sin(t * 2.4) * 0.15
			suck.Rate = 35 + math.sin(t * 1.3) * 12
		end)
		return p
	end
	local VIOLET, CYANP = Color3.fromRGB(186, 104, 255), Color3.fromRGB(80, 220, 255)
	task.spawn(function() -- the world 2 exit portal always has its extras; the golden one once it is open
		portalExtras(Vector3.new(CO.exit[1], CO.exit[2], CO.exit[3]), 26, CYANP)
		local golden = nil
		while not golden do
			task.wait(1)
			local fx = workspace:FindFirstChild("GoldenPortal", true)
			if fx and fx:IsA("BasePart") and fx.Position.Y < 300 then
				golden = portalExtras(Vector3.new(CO.portal[1], CO.portal[2], CO.portal[3]), 30, VIOLET)
			end
		end
	end)
	local SUBS = {
		[CO.first] = "low gravity  •  cosmic eggs  •  the rarest pets",
	}
	for k = CO.first + 1, CO.last do
		SUBS[k] = "WORLD 2  •  ZONE " .. (k - CO.first + 1)
	end
	SUBS[CO.last] = "THE FINAL ZONE  •  the rarest pets in the universe"
	local lastZone = nil
	while true do
		task.wait(0.3)
		local ch = player.Character
		local hrp = ch and ch:FindFirstChild("HumanoidRootPart")
		local now = hrp ~= nil and hrp.Position.Y > CO.y - 400
		if hrp then
			local pz = hrp.Position
			showWorld2(pz.Y > 300 or pz.Z > (C.NZ - 1) * C.ZONE_LEN - 20) -- world 2 + the Golden Nest (the portal is there)
		end
		if now and not inside then
			inside = true
			portalFlash(VIOLET)
			enter()
		elseif inside and not now then
			inside = false
			lastZone = nil
			portalFlash(CYANP)
			leave()
		end
		if now then -- a big title for every world 2 zone you walk into
			local zi = C.w2Zone(hrp.Position.Z)
			if zi ~= lastZone then
				lastZone = zi
				task.spawn(title, string.upper(C.ZONES[zi].name), SUBS[zi] or "")
			end
		end
	end
end)

-- ============================================================ ALTAR BUTTON (client, v126)
-- user: "every altar keeps its own button, only more professional". The altar ProximityPrompts are Custom style;
-- this draws a dark glass pill with a gold key badge, the zone name in its colour and a hold bar that fills.
-- Tap / click the pill works too (touch and mouse).
task.spawn(function()
	local PPS = game:GetService("ProximityPromptService")
	local UIS = game:GetService("UserInputService")
	local TweenS = game:GetService("TweenService")
	local function zoneColor(n)
		local c = C.ZONES[n] and C.ZONES[n].eggCol or { 255, 214, 70 }
		return Color3.fromRGB(c[1], c[2], c[3])
	end
	local function new(cls, props, parent)
		local o = Instance.new(cls)
		for k, v in pairs(props) do
			o[k] = v
		end
		o.Parent = parent
		return o
	end
	PPS.PromptShown:Connect(function(prompt, inputType)
		local part = prompt.Parent
		local n = part and tonumber(string.match(part.Name, "^EggAltar(%d+)$"))
		if prompt.Style ~= Enum.ProximityPromptStyle.Custom or not n then
			return
		end
		local col = zoneColor(n)
		local bb = new("BillboardGui", {
			Name = "AltarPrompt", Adornee = part, AlwaysOnTop = true, Size = UDim2.fromOffset(300, 86),
			StudsOffset = Vector3.new(0, 4.2, 0), LightInfluence = 0, ResetOnSpawn = false,
		}, game:GetService("Players").LocalPlayer:FindFirstChildOfClass("PlayerGui"))
		local root = new("TextButton", {
			Name = "Pill", Text = "", AutoButtonColor = false, AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(0, 0), BackgroundColor3 = Color3.fromRGB(22, 18, 40),
			BackgroundTransparency = 0.12,
		}, bb)
		new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, root)
		new("UIGradient", { Rotation = 90, Color = ColorSequence.new(Color3.fromRGB(70, 60, 110), Color3.fromRGB(20, 16, 36)) }, root)
		local stroke = new("UIStroke", { Thickness = 3, Color = Color3.fromRGB(255, 214, 90), ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, root)
		new("UIGradient", { Rotation = 0, Color = ColorSequence.new({
			ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 240, 170)), ColorSequenceKeypoint.new(0.5, Color3.fromRGB(255, 196, 60)),
			ColorSequenceKeypoint.new(1, Color3.fromRGB(255, 240, 170)) }) }, stroke)
		-- hold progress (fills left to right behind the text)
		local fill = new("Frame", { Name = "Fill", BackgroundColor3 = col, BackgroundTransparency = 0.55, BorderSizePixel = 0,
			Size = UDim2.fromScale(0, 1), ZIndex = 1 }, root)
		new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, fill)
		-- key badge
		local badge = new("Frame", { Name = "Key", AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0, 10, 0.5, 0),
			Size = UDim2.new(0, 62, 0, 62), BackgroundColor3 = Color3.fromRGB(255, 255, 255), ZIndex = 3 }, root)
		new("UICorner", { CornerRadius = UDim.new(1, 0) }, badge)
		new("UIGradient", { Rotation = 90, Color = ColorSequence.new(Color3.fromRGB(255, 226, 110), Color3.fromRGB(235, 150, 30)) }, badge)
		new("UIStroke", { Thickness = 2.5, Color = Color3.fromRGB(120, 66, 10), ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, badge)
		local touch = inputType == Enum.ProximityPromptInputType.Touch
		local keyName = touch and "TAP" or (inputType == Enum.ProximityPromptInputType.Gamepad and "X") or UIS:GetStringForKeyCode(prompt.KeyboardKeyCode)
		local keyLbl = new("TextLabel", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Font = Enum.Font.FredokaOne,
			Text = keyName ~= "" and keyName or "E", TextScaled = true, TextColor3 = Color3.fromRGB(70, 34, 6), ZIndex = 4 }, badge)
		new("UIPadding", { PaddingTop = UDim.new(0.2, 0), PaddingBottom = UDim.new(0.2, 0), PaddingLeft = UDim.new(0.16, 0), PaddingRight = UDim.new(0.16, 0) }, keyLbl)
		-- texts
		local title = new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.new(0, 84, 0.1, 0), Size = UDim2.new(1, -100, 0.48, 0),
			Font = Enum.Font.FredokaOne, Text = prompt.ActionText, TextScaled = true, TextXAlignment = Enum.TextXAlignment.Left,
			TextColor3 = Color3.new(1, 1, 1), ZIndex = 3 }, root)
		new("UIStroke", { Thickness = 2, Color = Color3.fromRGB(20, 12, 40) }, title)
		local sub = new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.new(0, 84, 0.56, 0), Size = UDim2.new(1, -100, 0.32, 0),
			Font = Enum.Font.GothamBold, Text = n .. ".  " .. prompt.ObjectText, TextScaled = true, TextXAlignment = Enum.TextXAlignment.Left,
			TextColor3 = col, ZIndex = 3 }, root)
		new("UIStroke", { Thickness = 1.5, Color = Color3.fromRGB(20, 12, 40) }, sub)
		-- appear: pop in
		TweenS:Create(root, TweenInfo.new(0.22, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Size = UDim2.fromScale(1, 1) }):Play()
		local conns = {}
		local holdTween
		local function holdStart()
			if holdTween then
				holdTween:Cancel()
			end
			fill.Size = UDim2.fromScale(0, 1)
			holdTween = TweenS:Create(fill, TweenInfo.new(math.max(prompt.HoldDuration, 0.05), Enum.EasingStyle.Linear), { Size = UDim2.fromScale(1, 1) })
			holdTween:Play()
			TweenS:Create(badge, TweenInfo.new(0.12), { Size = UDim2.new(0, 56, 0, 56) }):Play()
		end
		local function holdEnd()
			if holdTween then
				holdTween:Cancel()
			end
			TweenS:Create(fill, TweenInfo.new(0.15), { Size = UDim2.fromScale(0, 1) }):Play()
			TweenS:Create(badge, TweenInfo.new(0.12), { Size = UDim2.new(0, 62, 0, 62) }):Play()
		end
		table.insert(conns, prompt.PromptButtonHoldBegan:Connect(holdStart))
		table.insert(conns, prompt.PromptButtonHoldEnded:Connect(holdEnd))
		table.insert(conns, prompt.Triggered:Connect(function()
			fill.Size = UDim2.fromScale(1, 1)
			fill.BackgroundTransparency = 0.2
			TweenS:Create(fill, TweenInfo.new(0.35), { BackgroundTransparency = 1 }):Play()
			root.Size = UDim2.fromScale(1.12, 1.12)
			TweenS:Create(root, TweenInfo.new(0.25, Enum.EasingStyle.Back), { Size = UDim2.fromScale(1, 1) }):Play()
		end))
		-- touch / mouse: press the pill itself
		table.insert(conns, root.InputBegan:Connect(function(io)
			if io.UserInputType == Enum.UserInputType.Touch or io.UserInputType == Enum.UserInputType.MouseButton1 then
				prompt:InputHoldBegin()
			end
		end))
		table.insert(conns, root.InputEnded:Connect(function(io)
			if io.UserInputType == Enum.UserInputType.Touch or io.UserInputType == Enum.UserInputType.MouseButton1 then
				prompt:InputHoldEnd()
			end
		end))
		local hidden
		hidden = prompt.PromptHidden:Connect(function()
			hidden:Disconnect()
			for _, c in ipairs(conns) do
				c:Disconnect()
			end
			local t = TweenS:Create(root, TweenInfo.new(0.15), { Size = UDim2.fromScale(0, 0) })
			t:Play()
			t.Completed:Wait()
			bb:Destroy()
		end)
	end)
end)

-- ============================================================ LIVING PROPS (client, v137)
-- Neon City hover cars really fly: each one loops around the city on its own lane and height (they used to hang still).
-- Candy Canyon lollipop tops turn slowly so the swirl moves; the cake candle flames flicker.
task.spawn(function()
	local Map = workspace:WaitForChild("Map")
	task.wait(3)
	local RunS = game:GetService("RunService")
	local cars, lollis, flames = {}, {}, {}
	local neons = {}
	for _, d in ipairs(Map:GetDescendants()) do
		if d:IsA("BasePart") then
			if d.Name == "HoverCar" then
				table.insert(cars, { part = d })
			elseif d.Name:match("^HoverCarNeon%d") then
				table.insert(neons, d)
			elseif d.Name:match("^LolliTop%d") then
				table.insert(lollis, { part = d, base = d.CFrame, speed = (0.25 + math.random() * 0.3) * (math.random() < 0.5 and -1 or 1) })
			elseif d.Name == "CakeNeon" then
				table.insert(flames, { part = d, col = d.Color })
			end
		end
	end
	-- each neon strip belongs to the car at the same spot
	for _, n in ipairs(neons) do
		local best, bd = nil, 8
		for _, c in ipairs(cars) do
			local dist = (Vector3.new(c.part.Position.X, 0, c.part.Position.Z) - Vector3.new(n.Position.X, 0, n.Position.Z)).Magnitude
			if dist < bd then
				best, bd = c, dist
			end
		end
		if best then
			best.neon = n
			best.rel = best.part.CFrame:ToObjectSpace(n.CFrame)
		end
	end
	-- the city centre = middle of all cars; lanes are ovals around it
	local cx, cz = 0, 0
	for _, c in ipairs(cars) do
		cz = cz + c.part.Position.Z
	end
	cz = #cars > 0 and cz / #cars or 0
	local half = (C.ZONE_LEN or 140) * 0.42
	for i, c in ipairs(cars) do
		local p = c.part.Position
		c.rx = math.clamp(math.abs(p.X), 45, 150) -- wide lanes over the buildings on both sides
		c.rz = half
		c.y = p.Y
		c.ang = math.atan2((p.Z - cz) / c.rz, p.X / c.rx)
		c.dir = (i % 2 == 0) and 1 or -1 -- half the cars go one way, half the other
		c.speed = 28 + math.random() * 18 -- studs per second
		c.bob = math.random() * 6
		c.part.CanCollide = false
		if c.neon then
			c.neon.CanCollide = false
		end
	end
	local TURN = CFrame.Angles(0, math.pi, 0) -- the meshes are placed turned 180 degrees (see mpart in gen_map.py)
	local t = 0
	RunS.Heartbeat:Connect(function(dt)
		t = t + dt
		local hrp = plr.Character and plr.Character:FindFirstChild("HumanoidRootPart")
		local near = hrp and math.abs(hrp.Position.Z - cz) < 420 and hrp.Position.Y < 300
		if near then
			for _, c in ipairs(cars) do
				if c.part.Parent then
					local per = 2 * math.pi * math.sqrt((c.rx * c.rx + c.rz * c.rz) / 2)
					c.ang = c.ang + c.dir * dt * c.speed / per * 2 * math.pi
					local y = c.y + math.sin(t * 1.3 + c.bob) * 1.2
					local pos = Vector3.new(cx + math.cos(c.ang) * c.rx, y, cz + math.sin(c.ang) * c.rz)
					local tang = Vector3.new(-math.sin(c.ang) * c.rx, 0, math.cos(c.ang) * c.rz).Unit * c.dir
					local bank = CFrame.Angles(0, 0, -c.dir * 0.12) -- lean into the curve
					local cf = CFrame.lookAt(pos, pos + tang) * bank * TURN
					c.part.CFrame = cf
					if c.neon then
						c.neon.CFrame = cf * c.rel
					end
				end
			end
		end
		for _, l in ipairs(lollis) do -- the disc turns about its own axis (local Z of the placed mesh)
			if l.part.Parent then
				l.part.CFrame = l.base * CFrame.Angles(0, 0, t * l.speed)
			end
		end
		for i, f in ipairs(flames) do
			local k = 0.5 + 0.5 * math.sin(t * 9 + i) * math.sin(t * 5.3 + i * 2)
			f.part.Color = f.col:Lerp(Color3.fromRGB(255, 120, 40), 0.35 * k)
			f.part.Transparency = 0.05 + 0.2 * k
		end
	end)
end)

-- ============================================================ FLOWING PET COATS (client, v138)
-- Gold / Rainbow pets of the 40 new Codex animals get a live coat: rainbow bands (or a gold shine) that keep
-- flowing head -> tail (ReplicatedStorage.PetCoatFlow + PetCoatMaps). Works for pets built by the server
-- (pens, carried) and by this client (hatch, index): every Model with a Species attribute and Tier 2/3.
task.spawn(function()
	local okM, Coat = pcall(function()
		return require(RS:WaitForChild("PetCoatFlow", 20))
	end)
	local maps = RS:FindFirstChild("PetCoatMaps")
	if not okM or not Coat or not maps then
		warn("PetCoatFlow missing - Gold/Rainbow pets keep their static texture", Coat)
		return
	end
	local TIERS = { [2] = "Gold", [3] = "Rainbow" }
	local function try(m)
		if not m:IsA("Model") then
			return
		end
		local sp, tier = m:GetAttribute("Species"), TIERS[m:GetAttribute("Tier") or 1]
		if sp and tier and maps:FindFirstChild(sp) then
			task.defer(function() -- after the pet's parts are in place
				if m.Parent then
					pcall(Coat.apply, m, sp, tier)
				end
			end)
		end
	end
	for _, d in ipairs(workspace:GetDescendants()) do
		try(d)
	end
	workspace.DescendantAdded:Connect(try)
	workspace.DescendantRemoving:Connect(function(d)
		if d:IsA("Model") and d:GetAttribute("Species") then
			pcall(Coat.clear, d)
		end
	end)
end)
