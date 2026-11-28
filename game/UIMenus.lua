-- Raining Eggs: the new menus (ModuleScript in ReplicatedStorage). Client.client.lua calls init(ctx) once.
-- Compact button grid on the right, and: Pets (inventory), Store (game passes), Daily rewards,
-- Upgrades, Top (leaderboard), toast notifications, coin fly-in, purchase / rare confetti.
local M = {}

function M.init(X)
	local C, make, gui, plr = X.C, X.make, X.gui, X.plr
	local UI, TweenService, RunService = X.UI, X.TweenService, X.RunService
	local WHITE, BLACK, YELLOW, GREEN, RED = X.WHITE, X.BLACK, X.YELLOW, X.GREEN, X.RED
	local DARK, SOFT, GREY, GOLD = UI.DARK, UI.SOFT, UI.GREY, UI.GOLD
	local attr, Action, sfx = X.attr, X.Action, X.sfx
	local face, lip, title, icon, pressable, corner = X.face, X.lip, X.title, X.icon, X.pressable, X.corner
	local panel, ink, bar, setBar, bigButton, outline = UI.panel, UI.ink, UI.bar, UI.setBar, UI.bigButton, UI.outline
	local MPS = game:GetService("MarketplaceService")

	local function tw(o, t, goal, style, dir)
		local x = TweenService:Create(o, TweenInfo.new(t, style or Enum.EasingStyle.Quad, dir or Enum.EasingDirection.Out), goal)
		x:Play()
		return x
	end
	local function hasPass(key)
		return table.find(string.split(attr("Passes", ""), ","), key) ~= nil
	end
	M.hasPass = hasPass

	-- ============================================================ toasts (stacked cards under the top bar)
	local TOAST = {
		info = { "arrow", Color3.fromRGB(150, 90, 255) }, good = { "check", Color3.fromRGB(50, 190, 80) },
		bad = { "alert", Color3.fromRGB(235, 60, 60) }, cash = { "coin", Color3.fromRGB(255, 170, 20) },
		buy = { "coin", Color3.fromRGB(255, 170, 20) }, legend = { "crown", Color3.fromRGB(255, 190, 20) },
		storm = { "storm", Color3.fromRGB(150, 90, 255) },
	}
	local stack = make("Frame", {
		BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromScale(0.5, 0.2), Size = UDim2.fromScale(0.36, 0.3), ZIndex = 20,
	}, gui)
	make("UIListLayout", { Padding = UDim.new(0.02, 0), HorizontalAlignment = Enum.HorizontalAlignment.Center, SortOrder = Enum.SortOrder.LayoutOrder }, stack)
	local order = 0
	local function toast(msg, kind)
		if UI.noteFn then -- messages are plain outlined text under the bottom hint now (Client showNote)
			return UI.noteFn(msg, kind)
		end
		local k = TOAST[kind] or TOAST.info
		order = order + 1
		local kids = {}
		for _, c in ipairs(stack:GetChildren()) do
			if c:IsA("Frame") then
				table.insert(kids, c)
			end
		end
		if #kids >= 3 then
			table.sort(kids, function(a, b) return a.LayoutOrder < b.LayoutOrder end)
			kids[1]:Destroy()
		end
		local holder = make("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 0.26), LayoutOrder = order, ZIndex = 20 }, stack)
		local card = make("Frame", { Size = UDim2.fromScale(1, 1), Position = UDim2.fromScale(0, -0.6), ZIndex = 20 }, holder)
		face(card, Color3.fromRGB(46, 38, 92), 0.35)
		local strip = make("Frame", { Size = UDim2.fromScale(0.16, 1), BackgroundColor3 = k[2], BorderSizePixel = 0, ZIndex = 21 }, card)
		corner(strip, 0.35)
		local ic = icon(card, k[1], UDim2.fromScale(0.9, 0.9), UDim2.fromScale(0.08, 0.5), Vector2.new(0.5, 0.5))
		ic.ZIndex = 22
		local t = title(card, UDim2.fromScale(0.78, 0.62), UDim2.fromScale(0.19, 0.19), 30, msg)
		t.Font = Enum.Font.FredokaOne
		t.TextXAlignment = Enum.TextXAlignment.Left
		t.ZIndex = 22
		local sc = make("UIScale", { Scale = 0.85 }, card)
		tw(card, 0.25, { Position = UDim2.fromScale(0, 0) }, Enum.EasingStyle.Back)
		tw(sc, 0.25, { Scale = 1 }, Enum.EasingStyle.Back)
		task.delay((kind == "legend" or kind == "storm") and 4.5 or 2.6, function()
			if holder.Parent then
				tw(sc, 0.2, { Scale = 0.7 })
				local x = tw(card, 0.2, { Position = UDim2.fromScale(0, -0.4) })
				x.Completed:Wait()
				holder:Destroy()
			end
		end)
	end
	M.toast = toast

	-- ============================================================ confetti + coin fly (purchases, rare pets, cash)
	local fxLayer = make("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 30 }, gui)
	local CONF = { Color3.fromRGB(255, 80, 120), Color3.fromRGB(255, 210, 40), Color3.fromRGB(80, 200, 255), Color3.fromRGB(110, 230, 110), Color3.fromRGB(190, 110, 255) }
	local function confetti(n, col)
		for i = 1, n or 40 do
			local s = math.random(8, 16)
			local p = make("Frame", {
				AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5 + (math.random() - 0.5) * 0.1, 0.45), Size = UDim2.fromOffset(s, s * 0.6),
				BackgroundColor3 = (col and i % 3 == 0) and col or CONF[math.random(#CONF)], BorderSizePixel = 0, Rotation = math.random(0, 360), ZIndex = 30,
			}, fxLayer)
			local a = math.random() * math.pi * 2
			local d = 0.15 + math.random() * 0.35
			local up = UDim2.fromScale(0.5 + math.cos(a) * d * 0.7, 0.45 + math.sin(a) * d - 0.15)
			tw(p, 0.5, { Position = up, Rotation = p.Rotation + math.random(-200, 200) }, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
			task.delay(0.5, function()
				tw(p, 0.9, { Position = up + UDim2.fromScale(0, 0.35), BackgroundTransparency = 1, Rotation = p.Rotation + 180 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
				task.delay(0.95, function()
					p:Destroy()
				end)
			end)
		end
	end
	M.confetti = confetti
	local function coinFly(n, target)
		for i = 1, n do
			local c = icon(fxLayer, "coin", UDim2.fromScale(0.045, 0.045), UDim2.fromScale(0.5 + (math.random() - 0.5) * 0.2, 0.5 + (math.random() - 0.5) * 0.15), Vector2.new(0.5, 0.5))
			c.ZIndex = 31
			X.wobbly[c] = nil
			task.delay(i * 0.04, function()
				local x = tw(c, 0.55, { Position = target }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
				x.Completed:Wait()
				c:Destroy()
			end)
		end
	end
	local lastCash = attr("Cash", 0)
	plr:GetAttributeChangedSignal("Cash"):Connect(function()
		local c = attr("Cash", 0)
		local gain = c - lastCash
		lastCash = c
		if gain > 0 and gain >= math.max(20, attr("Income", 0) * 5) then -- only for big gains (selling, rewards), not every income tick
			coinFly(math.clamp(math.floor(math.log10(gain + 1) * 2), 4, 12), UDim2.fromScale(0.05, 0.86))
		end
	end)

	-- ============================================================ HUD v4 (as in Desktop/RAINING EGGS NOU/UI v4/hud.png)
	-- left: PETS / STORE / DAILY, right: INDEX / UPGRADE / REBIRTH / TOP (wide colour buttons, big icon sticking out top-left),
	-- bottom-left: basket, speed + luck, income, and the big green cash. The old pills / square buttons stay hidden underneath.
	X.menu.Visible = false
	X.stack.Visible = false
	X.basketBox.Visible = false
	-- the mockup is 1920 x 1080: a button is 280 x 76 with 16 between them
	local BTN_W, BTN_H, GAP = 280, 76, 16
	local function column(n, anchorX, x)
		local h = n * BTN_H + (n - 1) * GAP
		local f = make("Frame", {
			BackgroundTransparency = 1, AnchorPoint = Vector2.new(anchorX, 0), Position = UDim2.fromScale(x, 300 / 1080),
			Size = UDim2.fromScale(BTN_W / 1920, h / 1080), ZIndex = 2,
		}, gui)
		make("UIAspectRatioConstraint", { AspectRatio = BTN_W / h }, f)
		return f, h
	end
	local left, leftH = column(4, 0, 40 / 1920)
	local right, rightH = column(3, 1, 1 - 40 / 1920) -- v240 (user): no UPGRADE button any more
	local COL = {
		orange = Color3.fromRGB(255, 138, 30), blue = Color3.fromRGB(46, 155, 255), red = Color3.fromRGB(242, 70, 78),
		purple = Color3.fromRGB(154, 92, 255), green = Color3.fromRGB(63, 207, 90), pink = Color3.fromRGB(255, 92, 173), gold = Color3.fromRGB(255, 194, 30),
	}
	local function wideBtn(side, colH, k, col, iconName, label)
		local b = make("TextButton", {
			BackgroundTransparency = 1, Text = "", AutoButtonColor = false,
			Size = UDim2.fromScale(1, BTN_H / colH), Position = UDim2.fromScale(0, k * (BTN_H + GAP) / colH), ZIndex = 2,
		}, side)
		local holder, f = lip(b, col, UDim2.fromScale(1, 0.92), UDim2.new(), nil, 0.3)
		f.ZIndex = 2
		local ic = icon(holder, iconName, UDim2.fromScale(1.26, 1.26), UDim2.fromScale(-18 / BTN_W, -0.18))
		ic.ZIndex = 4
		X.wobbly[ic] = nil
		local t = make("TextLabel", {
			BackgroundTransparency = 1, Size = UDim2.fromScale(0.64, 0.6), Position = UDim2.fromScale(90 / BTN_W, 0.16), Font = Enum.Font.FredokaOne,
			TextScaled = true, TextColor3 = WHITE, TextXAlignment = Enum.TextXAlignment.Left, Text = label, ZIndex = 4,
		}, f)
		make("UIStroke", { Thickness = 3, Color = BLACK }, t)
		pressable(b)
		local badge = make("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.98, 0.04), Size = UDim2.fromScale(0.6, 0.6), Visible = false, ZIndex = 6 }, b)
		make("UIAspectRatioConstraint", { AspectRatio = 1 }, badge)
		face(badge, RED, 1)
		local bt = title(badge, UDim2.fromScale(0.6, 0.7), UDim2.fromScale(0.2, 0.12), 26, "!")
		bt.Font = Enum.Font.FredokaOne
		bt.ZIndex = 7
		return b, badge, bt
	end
	local eggsBtn, eggsBadge, eggsBadgeT = wideBtn(left, leftH, 0, COL.gold, "egg", "EGGS")
	local petsBtn = wideBtn(left, leftH, 1, COL.orange, "paw", "PETS")
	local storeBtn = wideBtn(left, leftH, 2, COL.blue, "gem", "STORE")
	local dailyBtn, dailyBadge = wideBtn(left, leftH, 3, COL.red, "gift", "DAILY")
	local idxBtn, idxBadge = wideBtn(right, rightH, 0, COL.purple, "book", "INDEX")
	local upBtn = wideBtn(right, rightH, 1, COL.green, "upgrade", "UPGRADE")
	upBtn.Visible = false -- v240 (user): the UPGRADES menu is gone (training = fence board, luck = LUCK SHOP)
	local rbBtn = wideBtn(right, rightH, 1, COL.pink, "rebirth", "REBIRTH")
	local topBtn = wideBtn(right, rightH, 2, COL.gold, "trophy", "TOP")
	idxBtn.Activated:Connect(function()
		if X.UI.openIndex then
			X.UI.openIndex()
		end
	end)
	rbBtn.Activated:Connect(function()
		if X.UI.openRebirth then
			X.UI.openRebirth()
		end
	end)

	-- money block (bottom-left): 420 x 330 in the mockup
	local money = make("Frame", {
		BackgroundTransparency = 1, AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(36 / 1920, 1 - 40 / 1080), Size = UDim2.fromScale(420 / 1920, 330 / 1080), ZIndex = 2,
	}, gui)
	make("UIAspectRatioConstraint", { AspectRatio = 420 / 330 }, money)
	local function outlined(parent, size, pos, maxSize, col, top, bottom, thick, font)
		local t = make("TextLabel", {
			BackgroundTransparency = 1, Size = size, Position = pos, Font = font or Enum.Font.LuckiestGuy, TextScaled = true, Text = "",
			TextColor3 = col or WHITE, TextXAlignment = Enum.TextXAlignment.Left, ZIndex = 3,
		}, parent)
		make("UIStroke", { Thickness = thick or 3, Color = BLACK }, t)
		make("UITextSizeConstraint", { MaxTextSize = maxSize }, t)
		if top then
			make("UIGradient", { Rotation = 90, Color = ColorSequence.new(top, bottom) }, t)
		end
		return t
	end
	local function row(y, h, iconName, x, w, col)
		local ic = icon(money, iconName, UDim2.fromScale(1, h), UDim2.fromScale(x, y))
		ic.ZIndex = 3
		X.wobbly[ic] = nil
		return outlined(money, UDim2.fromScale(w, h * 0.8), UDim2.fromScale(x + h * 330 / 420 + 0.015, y + h * 0.1), 60, col, nil, nil, 3)
	end
	local basketT = row(0, 0.19, "basket", 0.02, 0.5, WHITE)
	local speedT = row(0.21, 0.19, "bolt", 0.02, 0.24, Color3.fromRGB(127, 208, 255))
	local luckT = row(0.21, 0.19, "clover", 0.42, 0.3, Color3.fromRGB(141, 255, 122))
	local incT = row(0.42, 0.19, "coin", 0.02, 0.6, Color3.fromRGB(255, 216, 74))
	local cashIcon = icon(money, "coin", UDim2.fromScale(1, 0.33), UDim2.fromScale(0.02, 0.65))
	cashIcon.ZIndex = 3
	X.wobbly[cashIcon] = nil
	local cashT = outlined(money, UDim2.fromScale(0.72, 0.33), UDim2.fromScale(0.28, 0.65), 110, WHITE, Color3.fromRGB(217, 255, 176), Color3.fromRGB(31, 168, 58), 4.5)
	local cashSc = make("UIScale", {}, cashT)
	local lastShownCash = nil
	local function refreshHud()
		local cash = attr("Cash", 0)
		cashT.Text = "$" .. C.fmt(cash)
		if lastShownCash and cash > lastShownCash then
			cashSc.Scale = 1.12
			tw(cashSc, 0.25, { Scale = 1 }, Enum.EasingStyle.Back)
		end
		lastShownCash = cash
		speedT.Text = C.fmt(attr("Speed", 0))
		incT.Text = "+$" .. C.fmt(attr("Income", 0)) .. "/s"
		luckT.Text = "x" .. C.luck(attr("LuckLv", 0))
		local carry, mx = attr("Carry", 0), attr("CarryMax", 3)
		basketT.Text = carry .. " / " .. mx
		basketT.TextColor3 = carry >= mx and Color3.fromRGB(255, 90, 90) or WHITE
		idxBadge.Visible = X.UI.indexHasNew and X.UI.indexHasNew() or false
	end
	plr.AttributeChanged:Connect(refreshHud)
	refreshHud()
	task.spawn(function()
		while true do
			task.wait(1)
			idxBadge.Visible = X.UI.indexHasNew and X.UI.indexHasNew() or false
		end
	end)

	-- ============================================================ shared bits
	local RAR_COL = {}
	for i, r in ipairs(C.RARITY) do
		RAR_COL[i] = r.color
	end
	local function card(parent, col, size, pos)
		local f = make("Frame", { Size = size, Position = pos or UDim2.new(), ZIndex = 2 }, parent)
		face(f, col, 0.12)
		return f
	end
	-- v200 (user: "make these cards better and more professional"): rarity gradient card with a dark outline, a soft
	-- light behind the pet, a floor shadow, a rarity ribbon at the bottom, a small GOLD / RAINBOW chip and a gloss
	local function shade(c, k)
		return Color3.new(c.R * k, c.G * k, c.B * k)
	end
	local function lighten(c, k)
		return c:Lerp(WHITE, k)
	end
	local RAINBOW_SEQ = ColorSequence.new({
		ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 80, 80)), ColorSequenceKeypoint.new(0.2, Color3.fromRGB(255, 180, 50)),
		ColorSequenceKeypoint.new(0.4, Color3.fromRGB(250, 240, 70)), ColorSequenceKeypoint.new(0.6, Color3.fromRGB(80, 220, 110)),
		ColorSequenceKeypoint.new(0.8, Color3.fromRGB(70, 160, 255)), ColorSequenceKeypoint.new(1, Color3.fromRGB(190, 90, 255)),
	})
	local function petCard(parent, pet, ribbonH)
		local rar = C.RARITY[pet.i]
		local col = rar.color
		ribbonH = ribbonH or 0.2
		local c = make("Frame", { BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 2, ClipsDescendants = true }, parent)
		make("UICorner", { CornerRadius = UDim.new(0.1, 0) }, c)
		make("UIStroke", { Thickness = 3, Color = Color3.fromRGB(22, 18, 44), ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, c)
		make("UIGradient", { Rotation = 90, Color = ColorSequence.new(lighten(col, 0.45), shade(col, 0.78)) }, c)
		-- soft light behind the pet
		local glow = make("Frame", {
			AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.42), Size = UDim2.fromScale(0.95, 0.95),
			BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 2,
		}, c)
		make("UIAspectRatioConstraint", { AspectRatio = 1 }, glow)
		make("UICorner", { CornerRadius = UDim.new(1, 0) }, glow)
		make("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.45), NumberSequenceKeypoint.new(1, 1) }) }, glow)
		-- floor shadow
		local sh = make("Frame", {
			AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.71), Size = UDim2.fromScale(0.62, 0.07),
			BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 0.72, BorderSizePixel = 0, ZIndex = 2,
		}, c)
		make("UICorner", { CornerRadius = UDim.new(1, 0) }, sh)
		-- gloss on the top
		local gl = make("Frame", { Size = UDim2.fromScale(1, 0.35), BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 4 }, c)
		make("UIGradient", { Rotation = 90, Transparency = NumberSequence.new(0.78, 1) }, gl)
		-- rarity ribbon
		local rb = make("Frame", {
			AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1), Size = UDim2.fromScale(1, ribbonH),
			BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 4,
		}, c)
		make("UIGradient", { Rotation = 90, Color = ColorSequence.new(shade(col, 0.7), shade(col, 0.5)) }, rb)
		make("Frame", { Size = UDim2.new(1, 0, 0, 2), BackgroundColor3 = Color3.fromRGB(22, 18, 44), BackgroundTransparency = 0.4, BorderSizePixel = 0, ZIndex = 5 }, rb)
		local rt = title(rb, UDim2.fromScale(0.9, 0.66), UDim2.fromScale(0.05, 0.18), 24, rar.name:upper())
		rt.ZIndex = 6
		-- GOLD / RAINBOW chip
		if (pet.t or 1) > 1 then
			local chip = make("Frame", {
				Position = UDim2.fromScale(0.06, 0.05), Size = UDim2.fromScale(0.44, 0.11), BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 6,
			}, c)
			make("UICorner", { CornerRadius = UDim.new(1, 0) }, chip)
			make("UIStroke", { Thickness = 2, Color = Color3.fromRGB(22, 18, 44), ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, chip)
			make("UIGradient", {
				Rotation = pet.t == 2 and 90 or 0,
				Color = pet.t == 2 and ColorSequence.new(Color3.fromRGB(255, 240, 150), Color3.fromRGB(230, 150, 20)) or RAINBOW_SEQ,
			}, chip)
			local ct = title(chip, UDim2.fromScale(0.86, 0.74), UDim2.fromScale(0.07, 0.13), 16, pet.t == 2 and "GOLD" or "RAINBOW")
			ct.ZIndex = 7
		end
		-- a little bounce when the mouse is over it / it is pressed
		local sc = make("UIScale", {}, c)
		c.MouseEnter:Connect(function()
			TweenService:Create(sc, TweenInfo.new(0.12), { Scale = 1.04 }):Play()
		end)
		c.MouseLeave:Connect(function()
			TweenService:Create(sc, TweenInfo.new(0.12), { Scale = 1 }):Play()
		end)
		return c
	end
	local function equippedMark(c)
		make("UIStroke", { Color = Color3.fromRGB(70, 235, 100), Thickness = 4, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, c)
		local tick = make("Frame", { AnchorPoint = Vector2.new(1, 0), Size = UDim2.fromScale(0.2, 0.2), Position = UDim2.fromScale(0.94, 0.05), BackgroundColor3 = Color3.fromRGB(60, 210, 90), ZIndex = 7 }, c)
		make("UIAspectRatioConstraint", { AspectRatio = 1 }, tick)
		make("UICorner", { CornerRadius = UDim.new(1, 0) }, tick)
		make("UIStroke", { Thickness = 2.5, Color = WHITE }, tick)
		make("UIGradient", { Rotation = 90, Color = ColorSequence.new(Color3.fromRGB(130, 255, 140), Color3.fromRGB(30, 170, 70)) }, tick)
		title(tick, UDim2.fromScale(0.76, 0.76), UDim2.fromScale(0.12, 0.1), 26, "✓").ZIndex = 8
		return tick
	end
	local function scroller(parent, size, pos, cols, aspect)
		local sf = make("ScrollingFrame", {
			BackgroundTransparency = 1, BorderSizePixel = 0, Size = size, Position = pos, ScrollBarThickness = 6, ScrollBarImageColor3 = SOFT,
			CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollingDirection = Enum.ScrollingDirection.Y, ZIndex = 2,
		}, parent)
		make("UIPadding", { PaddingTop = UDim.new(0, 6), PaddingLeft = UDim.new(0, 6), PaddingRight = UDim.new(0, 12), PaddingBottom = UDim.new(0, 6) }, sf)
		local g = make("UIGridLayout", { CellPadding = UDim2.fromOffset(10, 10), SortOrder = Enum.SortOrder.LayoutOrder }, sf)
		local function fit()
			local a = sf.AbsoluteSize
			local w = a and (a.X - 18) or 0
			if w > 0 then
				local cw = (w - (cols - 1) * 10) / cols
				g.CellSize = UDim2.fromOffset(cw, cw / aspect)
			end
		end
		sf:GetPropertyChangedSignal("AbsoluteSize"):Connect(fit)
		fit()
		return sf
	end
	local function clear(sf)
		for _, c in ipairs(sf:GetChildren()) do
			if c:IsA("GuiObject") then
				c:Destroy()
			end
		end
	end
	local function parsePets(s)
		local out = {}
		for _, k in ipairs(string.split(s or "", ",")) do
			local z, i, t, v = string.match(k, "^(%d+)_(%d+)_(%d+)_?(%d*)$")
			if z and C.ZONES[tonumber(z)] and C.RARITY[tonumber(i)] then
				table.insert(out, { z = tonumber(z), i = tonumber(i), t = tonumber(t), v = tonumber(v) })
			end
		end
		return out
	end
	local function tabs(parent, names, pos, size, onPick)
		local row = make("Frame", { BackgroundTransparency = 1, Position = pos, Size = size, ZIndex = 2 }, parent)
		make("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0.015, 0), SortOrder = Enum.SortOrder.LayoutOrder }, row)
		local btns = {}
		local function pick(i)
			for j, b in ipairs(btns) do
				b.color(j == i and GREEN or Color3.fromRGB(90, 96, 200))
			end
			onPick(i)
		end
		for i, n in ipairs(names) do
			local b = bigButton(row, Color3.fromRGB(90, 96, 200), UDim2.fromScale(1 / #names - 0.015, 1), UDim2.new())
			b.button.LayoutOrder = i
			b.label.Text = n
			b.button.Activated:Connect(function()
				pick(i)
			end)
			btns[i] = b
		end
		return pick
	end

	-- ============================================================ PETS v254 (user reference "Neon Equip Pets"): dark navy panel
	-- with a neon rim in the selected pet's rarity colour, "Equip Pets" tab top-left, red X; left = big detail card of the
	-- selected pet (rarity banner, 3D pet, name, green Equip / Unequip, purple delete); right = filter chips, 4-column grid of
	-- slots (empty slots show "+"), "Equipped: x / y" pill at the bottom (+ small EQUIP BEST).
	do
		local NAVY1, NAVY2, SLOT = Color3.fromRGB(38, 42, 84), Color3.fromRGB(20, 21, 44), Color3.fromRGB(46, 50, 96)
		local DEF_ACC = Color3.fromRGB(150, 100, 255)
		local petsPanel = panel("MY PETS", "paw", Color3.fromRGB(255, 140, 40), 0.66, 2.05)
		local pf = petsPanel.frame
		for _, ch in ipairs(pf:GetChildren()) do -- keep the panel's open / close, hide its old cartoon skin (the X is rebuilt)
			if ch:IsA("GuiObject") then
				ch.Visible = false
			end
		end
		local function rnd(o, s)
			make("UICorner", { CornerRadius = UDim.new(s or 0.08, 0) }, o)
		end
		local function txt(parent, size, pos, maxSize, s, col, xa, font)
			local t = make("TextLabel", {
				BackgroundTransparency = 1, Size = size, Position = pos, Font = font or Enum.Font.FredokaOne, TextScaled = true,
				Text = s or "", TextColor3 = col or WHITE, TextXAlignment = xa or Enum.TextXAlignment.Center, ZIndex = 12,
			}, parent)
			make("UIStroke", { Thickness = 2.5, Color = BLACK }, t)
			make("UITextSizeConstraint", { MaxTextSize = maxSize }, t)
			return t
		end
		local function grad(o, a, b, rot)
			return make("UIGradient", { Rotation = rot or 90, Color = ColorSequence.new(a, b) }, o)
		end
		local function shade(c, k)
			return Color3.new(c.R * k, c.G * k, c.B * k)
		end
		local root = make("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 10 }, pf)
		-- neon glow + body
		local glow = make("Frame", { Size = UDim2.new(1, 14, 0.9, 14), Position = UDim2.new(0, -7, 0.1, -7), BackgroundTransparency = 1, ZIndex = 10 }, root)
		rnd(glow, 0.07)
		local glowS = make("UIStroke", { Thickness = 9, Transparency = 0.55, Color = DEF_ACC }, glow)
		local body = make("Frame", { Size = UDim2.fromScale(1, 0.9), Position = UDim2.fromScale(0, 0.1), BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 10 }, root)
		rnd(body, 0.06)
		grad(body, NAVY1, NAVY2)
		local bodyS = make("UIStroke", { Thickness = 4, Color = DEF_ACC, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, body)
		-- title tab
		local tab = make("Frame", { Size = UDim2.fromScale(0.36, 0.17), Position = UDim2.fromScale(0.025, 0), BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 11 }, root)
		rnd(tab, 0.3)
		grad(tab, NAVY1, Color3.fromRGB(28, 30, 62))
		local tabS = make("UIStroke", { Thickness = 3, Color = DEF_ACC, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, tab)
		local tabIcon = icon(tab, "paw", UDim2.fromScale(0.2, 0.9), UDim2.fromScale(0.03, 0.5), Vector2.new(0, 0.5))
		make("UIAspectRatioConstraint", { AspectRatio = 1 }, tabIcon)
		tabIcon.ZIndex = 12
		X.wobbly[tabIcon] = nil
		txt(tab, UDim2.fromScale(0.72, 0.66), UDim2.fromScale(0.25, 0.17), 46, "Equip Pets", WHITE, Enum.TextXAlignment.Left)
		-- red X
		local xb = make("TextButton", { AutoButtonColor = false, Text = "", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.975, 0.115), Size = UDim2.fromScale(0.075, 0.15), ZIndex = 13 }, root)
		make("UIAspectRatioConstraint", { AspectRatio = 1.05 }, xb)
		xb.BackgroundColor3 = WHITE
		rnd(xb, 0.25)
		grad(xb, Color3.fromRGB(255, 90, 90), Color3.fromRGB(200, 20, 30))
		make("UIStroke", { Thickness = 3, Color = WHITE, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, xb)
		txt(xb, UDim2.fromScale(0.6, 0.6), UDim2.fromScale(0.2, 0.18), 40, "X").ZIndex = 14
		pressable(xb)
		xb.Activated:Connect(function()
			petsPanel.close()
		end)

		-- ---------------------------------------------------------------- left: detail card
		local det = make("Frame", { Size = UDim2.fromScale(0.3, 0.8), Position = UDim2.fromScale(0.025, 0.155), BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 11 }, root)
		rnd(det, 0.07)
		local detG = grad(det, NAVY1, NAVY2)
		local detS = make("UIStroke", { Thickness = 3, Color = DEF_ACC, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, det)
		local banner = make("Frame", { Size = UDim2.fromScale(0.78, 0.11), Position = UDim2.fromScale(0.11, 0.035), BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 12 }, det)
		rnd(banner, 1)
		local banG = grad(banner, Color3.fromRGB(70, 74, 110), Color3.fromRGB(30, 32, 58))
		local banS = make("UIStroke", { Thickness = 2.5, Color = WHITE, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, banner)
		local banT = txt(banner, UDim2.fromScale(0.86, 0.76), UDim2.fromScale(0.07, 0.12), 34, "")
		banT.ZIndex = 13
		local wings = {}
		for sx = -1, 1, 2 do -- little wings on the banner
			local w = txt(det, UDim2.fromScale(0.12, 0.11), UDim2.fromScale(sx < 0 and 0.01 or 0.87, 0.035), 34, sx < 0 and "»" or "«")
			table.insert(wings, w)
		end
		local halo = make("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.66), Size = UDim2.fromScale(0.78, 0.09), BackgroundTransparency = 0.35, BorderSizePixel = 0, ZIndex = 12 }, det)
		rnd(halo, 1)
		local haloS = make("UIStroke", { Thickness = 3, Color = WHITE, Transparency = 0.1 }, halo)
		local light = make("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.42), Size = UDim2.fromScale(0.95, 0.6), BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 11 }, det)
		rnd(light, 1)
		make("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.55), NumberSequenceKeypoint.new(1, 1) }) }, light)
		local sparks = {}
		for k, p in ipairs({ { 0.1, 0.3, 0.09 }, { 0.83, 0.26, 0.07 }, { 0.86, 0.55, 0.06 }, { 0.12, 0.6, 0.06 } }) do
			local s = txt(det, UDim2.fromScale(p[3] * 1.6, p[3]), UDim2.fromScale(p[1], p[2]), 40, "✦")
			s.TextColor3 = WHITE
			sparks[k] = s
		end
		local viewHolder = make("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(0.9, 0.55), Position = UDim2.fromScale(0.05, 0.15), ZIndex = 13 }, det)
		local nameT = txt(det, UDim2.fromScale(0.92, 0.09), UDim2.fromScale(0.04, 0.715), 36, "")
		local subT = txt(det, UDim2.fromScale(0.92, 0.055), UDim2.fromScale(0.04, 0.8), 22, "", Color3.fromRGB(255, 222, 90))
		local eqHolder = make("TextButton", { AutoButtonColor = false, Text = "", Size = UDim2.fromScale(0.66, 0.12), Position = UDim2.fromScale(0.05, 0.865), BackgroundColor3 = WHITE, ZIndex = 12 }, det)
		rnd(eqHolder, 0.3)
		local eqG = grad(eqHolder, Color3.fromRGB(120, 245, 90), Color3.fromRGB(40, 175, 50))
		make("UIStroke", { Thickness = 2.5, Color = Color3.fromRGB(20, 60, 20), ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, eqHolder)
		local eqT = txt(eqHolder, UDim2.fromScale(0.84, 0.7), UDim2.fromScale(0.08, 0.15), 40, "Equip")
		eqT.ZIndex = 13
		pressable(eqHolder)
		local del = make("TextButton", { AutoButtonColor = false, Text = "", Size = UDim2.fromScale(0.2, 0.12), Position = UDim2.fromScale(0.75, 0.865), BackgroundColor3 = WHITE, ZIndex = 12 }, det)
		rnd(del, 0.3)
		local delG = grad(del, Color3.fromRGB(170, 120, 255), Color3.fromRGB(100, 50, 210))
		make("UIStroke", { Thickness = 2.5, Color = Color3.fromRGB(40, 20, 90), ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, del)
		local delT = txt(del, UDim2.fromScale(0.8, 0.7), UDim2.fromScale(0.1, 0.15), 34, "🗑")
		delT.ZIndex = 13
		pressable(del)
		-- empty state
		local empty = make("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 12 }, det)
		local emptyIcon = icon(empty, "paw", UDim2.fromScale(0.4, 0.3), UDim2.fromScale(0.5, 0.36), Vector2.new(0.5, 0.5))
		make("UIAspectRatioConstraint", { AspectRatio = 1 }, emptyIcon)
		emptyIcon.ZIndex = 13
		emptyIcon.ImageTransparency = 0.25
		X.wobbly[emptyIcon] = nil
		txt(empty, UDim2.fromScale(0.9, 0.09), UDim2.fromScale(0.05, 0.56), 34, "Select a pet")
		txt(empty, UDim2.fromScale(0.9, 0.05), UDim2.fromScale(0.05, 0.66), 20, "to view details", Color3.fromRGB(170, 160, 230))
		local detailParts = { banner, halo, light, viewHolder, nameT, subT, eqHolder, del, table.unpack(wings) }
		for _, s in ipairs(sparks) do
			table.insert(detailParts, s)
		end

		-- ---------------------------------------------------------------- right: chips, grid, footer
		local FILTERS = {
			{ "All", Color3.fromRGB(80, 150, 255) }, { "Equipped", Color3.fromRGB(70, 220, 100) }, { "Legendary", C.RARITY[5].color },
			{ "Epic", C.RARITY[4].color }, { "Rare", C.RARITY[3].color }, { "Uncommon", C.RARITY[2].color }, { "Common", C.RARITY[1].color },
			{ "Basket", Color3.fromRGB(255, 150, 50) },
		}
		local chipRow = make("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(0.64, 0.075), Position = UDim2.fromScale(0.345, 0.155), ZIndex = 11 }, root)
		make("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0.008, 0), SortOrder = Enum.SortOrder.LayoutOrder, VerticalAlignment = Enum.VerticalAlignment.Center }, chipRow)
		local filter, chips = 1, {}
		local grid = make("ScrollingFrame", {
			BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(0.635, 0.6), Position = UDim2.fromScale(0.345, 0.25),
			ScrollBarThickness = 6, ScrollBarImageColor3 = Color3.fromRGB(120, 110, 220), CanvasSize = UDim2.new(),
			AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollingDirection = Enum.ScrollingDirection.Y, ZIndex = 11,
		}, root)
		make("UIPadding", { PaddingTop = UDim.new(0, 6), PaddingLeft = UDim.new(0, 4), PaddingRight = UDim.new(0, 12), PaddingBottom = UDim.new(0, 6) }, grid)
		local gl = make("UIGridLayout", { CellPadding = UDim2.fromOffset(10, 10), SortOrder = Enum.SortOrder.LayoutOrder }, grid)
		local function fit()
			local w = grid.AbsoluteSize.X - 16
			if w > 0 then
				local cw = (w - 3 * 10) / 4
				gl.CellSize = UDim2.fromOffset(cw, cw)
			end
		end
		grid:GetPropertyChangedSignal("AbsoluteSize"):Connect(fit)
		fit()
		local foot = make("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Size = UDim2.fromScale(0.27, 0.085), Position = UDim2.fromScale(0.6, 0.915), BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 11 }, root)
		rnd(foot, 1)
		grad(foot, Color3.fromRGB(44, 46, 86), Color3.fromRGB(26, 28, 56))
		make("UIStroke", { Thickness = 2, Color = Color3.fromRGB(90, 96, 160), ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, foot)
		local footIcon = icon(foot, "paw", UDim2.fromScale(0.16, 0.8), UDim2.fromScale(0.05, 0.5), Vector2.new(0, 0.5))
		make("UIAspectRatioConstraint", { AspectRatio = 1 }, footIcon)
		footIcon.ZIndex = 12
		X.wobbly[footIcon] = nil
		local footT = txt(foot, UDim2.fromScale(0.72, 0.62), UDim2.fromScale(0.23, 0.19), 30, "Equipped: 0/0", WHITE, Enum.TextXAlignment.Left)
		local best = make("TextButton", { AutoButtonColor = false, Text = "", AnchorPoint = Vector2.new(0.5, 0.5), Size = UDim2.fromScale(0.16, 0.085), Position = UDim2.fromScale(0.88, 0.915), BackgroundColor3 = WHITE, ZIndex = 11 }, root)
		rnd(best, 1)
		grad(best, Color3.fromRGB(120, 245, 90), Color3.fromRGB(40, 175, 50))
		make("UIStroke", { Thickness = 2, Color = Color3.fromRGB(20, 60, 20), ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, best)
		txt(best, UDim2.fromScale(0.86, 0.6), UDim2.fromScale(0.07, 0.2), 26, "Equip Best")
		pressable(best)
		local incT = txt(root, UDim2.fromScale(0.16, 0.06), UDim2.fromScale(0.345, 0.885), 26, "", Color3.fromRGB(255, 222, 74), Enum.TextXAlignment.Left)

		-- ---------------------------------------------------------------- state + drawing
		local sel = nil -- { key, eq, basket } of the selected pet
		local selPet = nil
		local delArmed = 0
		local function click()
			if sfx then
				pcall(sfx, "click", 0.4)
			end
		end
		local function keyOf(p)
			return p.z .. "_" .. p.i .. "_" .. p.t .. "_" .. (p.v or 1)
		end
		local function accent(col)
			for _, s in ipairs({ glowS, bodyS, tabS, detS }) do
				s.Color = col
			end
		end
		local function showDetail(pet)
			selPet = pet
			empty.Visible = pet == nil
			for _, o in ipairs(detailParts) do
				o.Visible = pet ~= nil
			end
			for _, v in ipairs(viewHolder:GetChildren()) do
				v:Destroy()
			end
			if not pet then
				detG.Color = ColorSequence.new(NAVY1, NAVY2)
				accent(DEF_ACC)
				return
			end
			local col = C.RARITY[pet.i].color
			accent(col)
			detG.Color = ColorSequence.new(col:Lerp(WHITE, 0.15), shade(col, 0.32))
			banG.Color = ColorSequence.new(shade(col, 0.8), shade(col, 0.35))
			banS.Color = col:Lerp(WHITE, 0.5)
			banT.Text = (pet.t == 2 and "GOLD " or pet.t == 3 and "RAINBOW " or "") .. C.RARITY[pet.i].name:upper()
			halo.BackgroundColor3 = col
			haloS.Color = col:Lerp(WHITE, 0.6)
			for _, w in ipairs(wings) do
				w.TextColor3 = col:Lerp(WHITE, 0.4)
			end
			local v = X.petView(viewHolder, pet, UDim2.fromScale(1, 1), UDim2.new())
			v.ZIndex = 13
			nameT.Text = C.petName(pet)
			subT.Text = pet.basket and "In your basket - bring it to your pen" or ("+$" .. C.fmt(C.petIncome(pet)) .. "/s  ·  " .. C.traitText(pet))
			if pet.basket then
				eqT.Text = "In basket"
				eqG.Color = ColorSequence.new(Color3.fromRGB(150, 150, 165), Color3.fromRGB(90, 90, 105))
			elseif pet.eq then
				eqT.Text = "Unequip"
				eqG.Color = ColorSequence.new(Color3.fromRGB(255, 150, 80), Color3.fromRGB(220, 80, 30))
			else
				eqT.Text = "🐾 Equip"
				eqG.Color = ColorSequence.new(Color3.fromRGB(120, 245, 90), Color3.fromRGB(40, 175, 50))
			end
			del.Visible = not pet.basket
			delArmed = 0
			delT.Text = "🗑"
		end
		local function slot(n)
			local s = make("TextButton", { AutoButtonColor = false, Text = "", BackgroundColor3 = WHITE, LayoutOrder = n, ZIndex = 12 }, grid)
			rnd(s, 0.14)
			local g = grad(s, SLOT, Color3.fromRGB(30, 32, 64))
			local st = make("UIStroke", { Thickness = 2, Color = Color3.fromRGB(70, 76, 130), ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, s)
			return s, st, g
		end
		function M.refreshPets()
			if not pf.Visible then
				return
			end
			for _, c in ipairs(grid:GetChildren()) do
				if c:IsA("GuiObject") then
					c:Destroy()
				end
			end
			local owned = parsePets(attr("PetList", ""))
			local eqN = attr("Equipped", math.min(#owned, attr("PenMax", C.PEN_MAX)))
			for k, pet in ipairs(owned) do
				pet.idx, pet.eq = k, k <= eqN
			end
			local list = owned
			local f = FILTERS[filter][1]
			if f == "Basket" then
				list = parsePets(attr("CarryList", ""))
				for _, pet in ipairs(list) do
					pet.basket = true
				end
			elseif f == "Equipped" then
				list = {}
				for _, pet in ipairs(owned) do
					if pet.eq then
						table.insert(list, pet)
					end
				end
			elseif f ~= "All" then
				list = {}
				for _, pet in ipairs(owned) do
					if C.RARITY[pet.i].name == f then
						table.insert(list, pet)
					end
				end
			end
			table.sort(list, function(a, b)
				if a.eq ~= b.eq then
					return a.eq == true
				end
				return C.petIncome(a) > C.petIncome(b)
			end)
			footT.Text = "Equipped: " .. eqN .. "/" .. attr("PenMax", C.PEN_MAX)
			incT.Text = "+$" .. C.fmt(attr("Income", 0)) .. "/s"
			best.Visible = f ~= "Basket"
			-- keep the selection on the same pet (indices change after equip / unequip)
			local found = nil
			if sel then
				for pass = 1, 2 do
					for _, pet in ipairs(list) do
						if keyOf(pet) == sel.key and (pet.basket or false) == sel.basket and (pass == 2 or pet.eq == sel.eq) then
							found = pet
							break
						end
					end
					if found then
						break
					end
				end
			end
			for n, pet in ipairs(list) do
				local s, st, sg = slot(n)
				local col = C.RARITY[pet.i].color
				local v = X.petView(s, pet, UDim2.fromScale(0.9, 0.74), UDim2.fromScale(0.05, 0.02))
				v.ZIndex = 13
				local rt = txt(s, UDim2.fromScale(0.9, 0.2), UDim2.fromScale(0.05, 0.76), 20, C.RARITY[pet.i].name:upper(), WHITE)
				rt.ZIndex = 14
				if (pet.t or 1) > 1 then
					local tt = txt(s, UDim2.fromScale(0.6, 0.15), UDim2.fromScale(0.05, 0.04), 16, pet.t == 2 and "GOLD" or "RAINBOW", pet.t == 2 and Color3.fromRGB(255, 214, 70) or Color3.fromRGB(255, 140, 230), Enum.TextXAlignment.Left)
					tt.ZIndex = 14
				end
				if pet.eq then
					local tick = make("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Size = UDim2.fromScale(0.26, 0.26), Position = UDim2.fromScale(0.9, 0.1), BackgroundColor3 = WHITE, ZIndex = 15 }, s)
					rnd(tick, 1)
					grad(tick, Color3.fromRGB(130, 255, 140), Color3.fromRGB(30, 170, 70))
					make("UIStroke", { Thickness = 2, Color = WHITE }, tick)
					txt(tick, UDim2.fromScale(0.7, 0.7), UDim2.fromScale(0.15, 0.12), 24, "✓").ZIndex = 16
				end
				if pet == found then
					st.Color, st.Thickness = col, 3.5
					sg.Color = ColorSequence.new(shade(col, 0.75), shade(col, 0.3))
				end
				s.Activated:Connect(function()
					click()
					sel = { key = keyOf(pet), eq = pet.eq, idx = pet.idx, basket = pet.basket or false }
					M.refreshPets()
				end)
			end
			local filled = #list
			local total = math.max(8, math.ceil(filled / 4) * 4 + (filled % 4 == 0 and 4 or 0))
			for n = filled + 1, total do
				local s = slot(n)
				local p = txt(s, UDim2.fromScale(0.4, 0.4), UDim2.fromScale(0.3, 0.3), 60, "+", Color3.fromRGB(150, 150, 210))
				p.ZIndex = 13
				make("UIStroke", { Thickness = 0, Transparency = 1 }, p)
				s.AutoButtonColor = false
			end
			if found then
				sel.idx, sel.eq = found.idx, found.eq
			end
			showDetail(found)
		end
		for i, fd in ipairs(FILTERS) do
			local b = make("TextButton", { AutoButtonColor = false, Text = "", Size = UDim2.fromScale(1 / #FILTERS - 0.008, 1), BackgroundColor3 = WHITE, LayoutOrder = i, ZIndex = 12 }, chipRow)
			rnd(b, 1)
			local g = grad(b, Color3.fromRGB(46, 50, 92), Color3.fromRGB(30, 32, 62))
			make("UIStroke", { Thickness = 2, Color = fd[2], ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, b)
			local t = txt(b, UDim2.fromScale(0.88, 0.62), UDim2.fromScale(0.06, 0.19), 20, fd[1])
			t.ZIndex = 13
			chips[i] = { g = g, col = fd[2] }
			b.Activated:Connect(function()
				click()
				filter = i
				for j, c in ipairs(chips) do
					c.g.Color = j == i and ColorSequence.new(c.col:Lerp(WHITE, 0.2), shade(c.col, 0.6)) or ColorSequence.new(Color3.fromRGB(46, 50, 92), Color3.fromRGB(30, 32, 62))
				end
				M.refreshPets()
			end)
		end
		chips[1].g.Color = ColorSequence.new(chips[1].col:Lerp(WHITE, 0.2), shade(chips[1].col, 0.6))
		eqHolder.Activated:Connect(function()
			if not selPet or selPet.basket then
				return
			end
			click()
			sel.eq = not selPet.eq
			Action:FireServer("equip", selPet.idx)
		end)
		del.Activated:Connect(function()
			if not selPet or selPet.basket then
				return
			end
			click()
			if os.clock() - delArmed > 2.5 then -- first tap asks, second tap deletes
				delArmed = os.clock()
				delT.Text = "Sure?"
				task.delay(2.5, function()
					if os.clock() - delArmed >= 2.4 then
						delT.Text = "🗑"
					end
				end)
				return
			end
			delArmed = 0
			Action:FireServer("deletepet", selPet.idx)
			sel = nil
		end)
		best.Activated:Connect(function()
			click()
			Action:FireServer("equipbest")
		end)
		petsBtn.Activated:Connect(function()
			petsPanel.toggle()
			M.refreshPets()
		end)
	end

	-- ============================================================ EGGS (caught eggs, not hatched yet)
	-- same eggs are grouped in one card (spinning 3D egg, name, best pet odds, "x4", own HATCH button); HATCH ALL at the bottom
	local eggsPanel = panel("MY EGGS", "egg", Color3.fromRGB(255, 180, 30), 0.74, 1.7)
	local ei = eggsPanel.inner
	local eggsInfo = ink(ei, UDim2.fromScale(0.5, 0.08), UDim2.fromScale(0.03, 0.03), 44, "", DARK, Enum.Font.LuckiestGuy)
	local capBg, capFill = bar(ei, UDim2.fromScale(0.4, 0.05), UDim2.fromScale(0.57, 0.045), Color3.fromRGB(255, 214, 80), Color3.fromRGB(255, 150, 20))
	local eggGrid = scroller(ei, UDim2.fromScale(0.95, 0.68), UDim2.fromScale(0.025, 0.12), 4, 0.72)
	local hatchAll = bigButton(ei, GREEN, UDim2.fromScale(0.4, 0.14), UDim2.fromScale(0.5, 0.985), Vector2.new(0.5, 1))
	local KIND = {
		golden = { "GOLDEN EGG", Color3.fromRGB(255, 196, 40), "80% GOLD 20% RAINBOW" }, -- v244: no extra luck
		storm = { "STORM EGG", Color3.fromRGB(140, 80, 255), "x" .. C.STORM_EGG_LUCK .. " LUCK" },
		royal = { "ROYAL EGG", Color3.fromRGB(200, 60, 150), "x" .. C.ROYAL_LUCK .. " LUCK  GOLD / RAINBOW" }, -- v256 Robux egg
	}
	local ZONE_CARD = Color3.fromRGB(96, 160, 255)
	local spinning = {} -- egg parts in the open cards, turned every frame
	local function eggView(parent, z, kind)
		local vp = make("ViewportFrame", {
			Size = UDim2.fromScale(0.9, 0.5), Position = UDim2.fromScale(0.05, 0.03), BackgroundTransparency = 1, Ambient = Color3.fromRGB(205, 205, 215),
			LightColor = WHITE, LightDirection = Vector3.new(0.5, -1, 0.8), ZIndex = 3,
		}, parent)
		local cam = make("Camera", { FieldOfView = 34 }, vp)
		vp.CurrentCamera = cam
		local name = (kind == "golden" and "Egg_Gold") or (kind == "storm" and "Egg_Storm") or (kind == "royal" and "Egg_Secret") or ("Egg_" .. z)
		local src = (kind == "golden" and C.meshOf("Egg_" .. z .. "_G")) or C.meshOf(name) -- v244: gold-coated zone egg
		local p, rot
		if src then
			p = src:Clone()
			p.Anchored = true
			rot = src.CFrame.Rotation
		else
			local c = C.ZONES[z].eggCol
			p = make("Part", { Anchored = true, Shape = Enum.PartType.Ball, Size = Vector3.new(2, 2.5, 2), Color = KIND[kind] and KIND[kind][2] or Color3.fromRGB(c[1], c[2], c[3]) })
			rot = CFrame.new()
		end
		p.CFrame = rot
		p.Parent = vp
		local h = math.max(p.Size.X, p.Size.Y, p.Size.Z)
		cam.CFrame = CFrame.lookAt(Vector3.new(0, h * 0.25, -h * 2.2), Vector3.new())
		table.insert(spinning, { p = p, rot = rot, t = math.random() * 6 })
	end
	RunService.RenderStepped:Connect(function(dt)
		if not eggsPanel.frame.Visible then
			return
		end
		for _, s in ipairs(spinning) do
			s.t = s.t + dt
			if s.p.Parent then
				s.p.CFrame = CFrame.new(0, math.sin(s.t * 2.2) * 0.12, 0) * CFrame.Angles(0, s.t * 0.9, math.sin(s.t * 1.7) * 0.08) * s.rot
			end
		end
	end)
	local function eggGroups()
		local groups, order = {}, {}
		for _, k in ipairs(string.split(attr("EggList", ""), ",")) do
			local z, kind = string.match(k, "^(%d+)_(%a+)$")
			if z and C.ZONES[tonumber(z)] then
				if not groups[k] then
					groups[k] = { key = k, z = tonumber(z), kind = kind, n = 0 }
					table.insert(order, groups[k])
				end
				groups[k].n = groups[k].n + 1
			end
		end
		table.sort(order, function(a, b)
			local ra = (a.kind == "royal" and 3 or a.kind == "storm" and 2 or a.kind == "golden" and 1 or 0) * 100 + a.z
			local rb = (b.kind == "royal" and 3 or b.kind == "storm" and 2 or b.kind == "golden" and 1 or 0) * 100 + b.z
			return ra > rb
		end)
		return order
	end
	local lastHatch = 0
	local function doHatch(key, one)
		if attr("Eggs", 0) == 0 or os.clock() - lastHatch < 0.5 then
			return
		end
		lastHatch = os.clock()
		eggsPanel.close()
		Action:FireServer(one and "hatch1" or "hatch", key)
	end
	function M.refreshEggs()
		local n = attr("Eggs", 0)
		eggsBadge.Visible = n > 0
		eggsBadgeT.Text = tostring(n)
		if not eggsPanel.frame.Visible then
			return
		end
		clear(eggGrid)
		spinning = {}
		local groups = eggGroups()
		eggsInfo.Text = n .. (n == 1 and " EGG" or " EGGS")
		local carry, mx = attr("Carry", 0), attr("CarryMax", 3)
		setBar(capFill, carry / math.max(mx, 1))
		hatchAll.label.Text = n > 0 and ("HATCH ALL (" .. n .. ")") or "HATCH ALL"
		hatchAll.color(n > 0 and GREEN or GREY)
		for k, g in ipairs(groups) do
			local info = KIND[g.kind]
			local c = card(eggGrid, info and info[2] or ZONE_CARD, UDim2.new(), UDim2.new())
			c.LayoutOrder = k
			eggView(c, g.z, g.kind)
			if g.n > 1 then
				local cnt = title(c, UDim2.fromScale(0.36, 0.12), UDim2.fromScale(0.6, 0.03), 34, "x" .. g.n)
				cnt.TextColor3 = YELLOW
				cnt.TextXAlignment = Enum.TextXAlignment.Right
				cnt.ZIndex = 4
			end
			local nm = title(c, UDim2.fromScale(0.92, 0.1), UDim2.fromScale(0.04, 0.53), 24, info and info[1] or C.ZONES[g.z].name:upper())
			nm.ZIndex = 3
			-- the best pet this egg can give, with its odds
			local best = C.ZONES[g.z].pets[#C.RARITY]
			local sub = title(c, UDim2.fromScale(0.92, 0.075), UDim2.fromScale(0.04, 0.635), 18,
				info and (info[3] .. "  -  " .. C.ZONES[g.z].name) or ("BEST: " .. best.name .. "  1/" .. C.comma(C.RARITY[#C.RARITY].odds)))
			sub.Font = Enum.Font.FredokaOne
			sub.TextColor3 = Color3.fromRGB(255, 235, 150)
			sub.ZIndex = 3
			local hb = bigButton(c, GREEN, UDim2.fromScale(0.8, 0.2), UDim2.fromScale(0.5, 0.97), Vector2.new(0.5, 1))
			if c.LayoutOrder <= 1 or not X.UI.tutFirstHatch or not X.UI.tutFirstHatch.Parent then
				X.UI.tutFirstHatch = hb.button
			end
			hb.label.Text = "HATCH" -- v103 (user): one egg at a time, the player picks which one; HATCH ALL is at the bottom
			hb.button.ZIndex = 4
			hb.button.Activated:Connect(function()
				doHatch(g.key, true)
			end)
		end
		if #groups == 0 then
			local e = ink(eggGrid, UDim2.new(), UDim2.new(), 36, "No eggs yet - catch falling eggs!", SOFT)
			e.TextXAlignment = Enum.TextXAlignment.Center
		end
	end
	hatchAll.button.Activated:Connect(function()
		doHatch(nil)
	end)
	eggsBtn.Activated:Connect(function()
		eggsPanel.toggle()
		M.refreshEggs()
	end)
	-- v182: the introduction (Client) points at these
	X.UI.tutEggsBtn = eggsBtn
	X.UI.tutEggsOpen = function()
		return eggsPanel.frame.Visible
	end
	X.UI.tutHatchBtn = function()
		return X.UI.tutFirstHatch or hatchAll.button
	end
	M.refreshEggs()

	-- ============================================================ SELL (v104, user: "select the pets, with their picture, professional")
	-- opens while standing on the SELL shop zone: tabs BASKET / PEN, cards like MY PETS (3D pet, name, rarity, price),
	-- tap cards to select (green frame + tick), SELECT ALL, SELL SELECTED ($total)
	local sellPanel = panel("SELL PETS", "coin", Color3.fromRGB(240, 170, 20), 0.76, 1.75)
	local sp = sellPanel.inner
	local sellInfo = ink(sp, UDim2.fromScale(0.6, 0.075), UDim2.fromScale(0.37, 0.045), 34, "", DARK, Enum.Font.LuckiestGuy, Enum.TextXAlignment.Right)
	local sellGrid = scroller(sp, UDim2.fromScale(0.95, 0.66), UDim2.fromScale(0.025, 0.15), 5, 0.78)
	local allBtn = bigButton(sp, Color3.fromRGB(90, 96, 200), UDim2.fromScale(0.3, 0.13), UDim2.fromScale(0.03, 0.84))
	allBtn.label.Text = "SELECT ALL"
	local sellBtn = bigButton(sp, GREEN, UDim2.fromScale(0.6, 0.13), UDim2.fromScale(0.37, 0.84))
	local sellTab, picked, lastSellKey = 1, {}, nil
	local function sellSource()
		return attr(sellTab == 1 and "CarryList" or "PetList", ""), sellTab == 1 and "c" or "p"
	end
	local function priceOf(pet)
		return math.floor(C.petIncome(pet) * C.SELL_MULT)
	end
	local cards = {}
	local function updateSellButtons()
		local str = sellSource()
		local list = parsePets(str)
		local n, sum = 0, 0
		for key, on in pairs(picked) do
			local i = tonumber(string.sub(key, 2))
			if on and list[i] then
				n, sum = n + 1, sum + priceOf(list[i])
			end
		end
		sellInfo.Text = n > 0 and ("SELECTED " .. n .. "  -  $" .. C.fmt(sum)) or (#list .. (sellTab == 1 and " IN YOUR BASKET" or " PETS YOU OWN"))
		sellBtn.label.Text = n > 0 and ("SELL " .. n .. " FOR $" .. C.fmt(sum)) or "SELECT PETS TO SELL"
		sellBtn.color(n > 0 and GREEN or GREY)
		allBtn.label.Text = (#list > 0 and n == #list) and "CLEAR" or "SELECT ALL"
		for key, c in pairs(cards) do
			local on = picked[key] == true
			c.stroke.Thickness = on and 5 or 0
			c.tick.Visible = on
			c.scale.Scale = on and 0.95 or 1
		end
	end
	local function refreshSell(force)
		if not sellPanel.frame.Visible then
			return
		end
		local str, where = sellSource()
		local key = sellTab .. "|" .. str
		if key == lastSellKey and not force then
			updateSellButtons()
			return
		end
		lastSellKey = key
		picked, cards = {}, {}
		clear(sellGrid)
		local list = parsePets(str)
		for i, pet in ipairs(list) do
			local rar = C.RARITY[pet.i]
			local id = where .. i
			local c = card(sellGrid, rar.color, UDim2.new(), UDim2.new())
			c.LayoutOrder = (6 - pet.i) * 1000 + i -- rarest first
			local v = X.petView(c, pet, UDim2.fromScale(1, 0.56), UDim2.fromScale(0, 0.04))
			v.ZIndex = 3
			local nm = title(c, UDim2.fromScale(0.92, 0.12), UDim2.fromScale(0.04, 0.6), 22, C.petName(pet))
			nm.ZIndex = 3
			local rr = title(c, UDim2.fromScale(0.92, 0.09), UDim2.fromScale(0.04, 0.72), 18, rar.name:upper())
			rr.Font = Enum.Font.FredokaOne
			rr.ZIndex = 3
			-- price tag
			local tag = make("Frame", { Size = UDim2.fromScale(0.84, 0.14), Position = UDim2.fromScale(0.08, 0.83), ZIndex = 3 }, c)
			face(tag, Color3.fromRGB(40, 200, 80), 1)
			local pt = title(tag, UDim2.fromScale(0.9, 0.78), UDim2.fromScale(0.05, 0.11), 22, "$" .. C.fmt(priceOf(pet)))
			pt.ZIndex = 4
			-- selection: green frame + round tick
			local stroke = make("UIStroke", { Color = Color3.fromRGB(60, 230, 90), Thickness = 0, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, c)
			local tick = make("Frame", { Visible = false, Size = UDim2.fromScale(0.26, 0.2), Position = UDim2.fromScale(0.7, 0.03), BackgroundColor3 = Color3.fromRGB(60, 210, 90), ZIndex = 6 }, c)
			make("UIAspectRatioConstraint", { AspectRatio = 1 }, tick)
			make("UICorner", { CornerRadius = UDim.new(1, 0) }, tick)
			make("UIStroke", { Thickness = 3, Color = WHITE }, tick)
			local tt = title(tick, UDim2.fromScale(0.8, 0.8), UDim2.fromScale(0.1, 0.08), 30, "✓")
			tt.ZIndex = 7
			local scale = make("UIScale", {}, c)
			local hit = make("TextButton", { BackgroundTransparency = 1, Text = "", Size = UDim2.fromScale(1, 1), ZIndex = 8 }, c)
			hit.Activated:Connect(function()
				picked[id] = not picked[id] or nil
				if sfx then
					pcall(sfx, "click", 0.4)
				end
				updateSellButtons()
			end)
			cards[id] = { stroke = stroke, tick = tick, scale = scale }
		end
		if #list == 0 then
			local e = ink(sellGrid, UDim2.new(), UDim2.new(), 36, sellTab == 1 and "Your basket is empty - catch eggs!" or "No pets yet - catch eggs!", SOFT)
			e.TextXAlignment = Enum.TextXAlignment.Center
		end
		updateSellButtons()
	end
	local pickSellTab = tabs(sp, { "BASKET", "PETS" }, UDim2.fromScale(0.03, 0.04), UDim2.fromScale(0.32, 0.08), function(i)
		sellTab = i
		refreshSell(true)
	end)
	allBtn.button.Activated:Connect(function()
		local list = parsePets((sellSource()))
		local _, where = sellSource()
		local n = 0
		for _, on in pairs(picked) do
			n = n + (on and 1 or 0)
		end
		picked = {}
		if n < #list then
			for i = 1, #list do
				picked[where .. i] = true
			end
		end
		updateSellButtons()
	end)
	local lastSell = 0
	sellBtn.button.Activated:Connect(function()
		local keys = {}
		for key, on in pairs(picked) do
			if on then
				table.insert(keys, key)
			end
		end
		if #keys == 0 or os.clock() - lastSell < 0.5 then
			return
		end
		lastSell = os.clock()
		Action:FireServer("sellpets", table.concat(keys, ","))
		picked = {}
	end)
	plr.AttributeChanged:Connect(function(name)
		if (name == "CarryList" or name == "PetList") and sellPanel.frame.Visible then
			refreshSell()
		end
	end)
	X.UI.openSell = function()
		if not sellPanel.frame.Visible then
			sellPanel.open()
			pickSellTab(attr("CarryList", "") ~= "" and 1 or 2)
		end
	end
	X.UI.closeSell = function()
		if sellPanel.frame.Visible then
			sellPanel.close()
		end
	end

	-- ============================================================ SHOP v256 (user video of Steal an Egg's shop): green "Shop" title
	-- bar + red X, dark body, ONE list you scroll: -- FEATURED -- (Royal Egg banner), -- PASSES -- (2 per row),
	-- -- SPEED -- (3 per row), -- MONEY -- (3 small + 2 wide). Category buttons on the right jump to each section.
	do
		local BG1, BG2 = Color3.fromRGB(44, 44, 52), Color3.fromRGB(28, 28, 34)
		local storePanel = panel("STORE", "gem", Color3.fromRGB(40, 170, 255), 0.6, 1.72)
		local sf = storePanel.frame
		for _, ch in ipairs(sf:GetChildren()) do
			if ch:IsA("GuiObject") then
				ch.Visible = false
			end
		end
		local function rnd(o, s)
			make("UICorner", { CornerRadius = UDim.new(s or 0.08, 0) }, o)
		end
		local function grad(o, a, b, rot)
			return make("UIGradient", { Rotation = rot or 90, Color = ColorSequence.new(a, b) }, o)
		end
		local function txt(parent, size, pos, maxSize, s, col, xa, font, z)
			local t = make("TextLabel", {
				BackgroundTransparency = 1, Size = size, Position = pos, Font = font or Enum.Font.FredokaOne, TextScaled = true,
				Text = s or "", TextColor3 = col or WHITE, TextXAlignment = xa or Enum.TextXAlignment.Center, ZIndex = z or 14,
			}, parent)
			make("UIStroke", { Thickness = 2.5, Color = BLACK }, t)
			make("UITextSizeConstraint", { MaxTextSize = maxSize }, t)
			return t
		end
		local function frame(parent, size, pos, a, b, stroke, z, corner)
			local f = make("Frame", { Size = size, Position = pos or UDim2.new(), BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = z or 12 }, parent)
			rnd(f, corner)
			grad(f, a, b)
			if stroke then
				make("UIStroke", { Thickness = 3, Color = stroke, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, f)
			end
			return f
		end
		local function shade(c, k)
			return Color3.new(c.R * k, c.G * k, c.B * k)
		end
		local function click()
			if sfx then
				pcall(sfx, "click", 0.4)
			end
		end
		local root = make("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 10 }, sf)
		-- body + green title bar + X
		local body = frame(root, UDim2.fromScale(1, 1), nil, BG1, BG2, BLACK, 10, 0.03)
		local bar = frame(root, UDim2.fromScale(1, 0.1), nil, Color3.fromRGB(130, 245, 70), Color3.fromRGB(60, 190, 40), BLACK, 11, 0.25)
		txt(bar, UDim2.fromScale(0.5, 0.72), UDim2.fromScale(0.025, 0.14), 48, "Shop", WHITE, Enum.TextXAlignment.Left, Enum.Font.LuckiestGuy)
		local xb = make("TextButton", { AutoButtonColor = false, Text = "", AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.fromScale(0.99, 0.05), Size = UDim2.fromScale(0.07, 0.085), BackgroundColor3 = WHITE, ZIndex = 13 }, root)
		make("UIAspectRatioConstraint", { AspectRatio = 1 }, xb)
		rnd(xb, 0.2)
		grad(xb, Color3.fromRGB(255, 80, 80), Color3.fromRGB(200, 20, 30))
		make("UIStroke", { Thickness = 2.5, Color = BLACK, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, xb)
		txt(xb, UDim2.fromScale(0.62, 0.62), UDim2.fromScale(0.19, 0.17), 40, "X", WHITE, nil, Enum.Font.LuckiestGuy, 14)
		pressable(xb)
		xb.Activated:Connect(function()
			storePanel.close()
		end)
		local list = make("ScrollingFrame", {
			BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(0.96, 0.87), Position = UDim2.fromScale(0.02, 0.115),
			ScrollBarThickness = 8, ScrollBarImageColor3 = Color3.fromRGB(150, 150, 160), CanvasSize = UDim2.new(),
			AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollingDirection = Enum.ScrollingDirection.Y, ZIndex = 11,
		}, root)
		make("UIListLayout", { Padding = UDim.new(0, 10), SortOrder = Enum.SortOrder.LayoutOrder, HorizontalAlignment = Enum.HorizontalAlignment.Center }, list)
		make("UIPadding", { PaddingTop = UDim.new(0, 6), PaddingRight = UDim.new(0, 14), PaddingBottom = UDim.new(0, 12) }, list)
		local order = 0
		local function nextOrder()
			order += 1
			return order
		end
		-- a block of the list: full width, height = width / aspect (in pixels, so the canvas can grow)
		local blocks = {}
		local function fitBlocks()
			local w = list.AbsoluteSize.X - 14
			for f, aspect in pairs(blocks) do
				f.Size = UDim2.new(1, 0, 0, math.floor(w / aspect))
			end
		end
		list:GetPropertyChangedSignal("AbsoluteSize"):Connect(fitBlocks)
		local function block(aspect)
			local f = make("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 40), LayoutOrder = nextOrder(), ZIndex = 11 }, list)
			blocks[f] = aspect
			fitBlocks()
			return f
		end
		local sections = {}
		local function header(name)
			local h = block(16)
			txt(h, UDim2.fromScale(1, 0.9), UDim2.fromScale(0, 0.05), 34, "-- " .. name .. " --", Color3.fromRGB(255, 226, 90), nil, Enum.Font.LuckiestGuy, 12)
			sections[name] = h
			return h
		end
		-- green Robux price button
		local function priceBtn(parent, size, pos, onBuy)
			local b = make("TextButton", { AutoButtonColor = false, Text = "", Size = size, Position = pos, BackgroundColor3 = WHITE, ZIndex = 14 }, parent)
			rnd(b, 0.3)
			local g = grad(b, Color3.fromRGB(120, 245, 90), Color3.fromRGB(40, 175, 50))
			make("UIStroke", { Thickness = 2.5, Color = Color3.fromRGB(15, 60, 20), ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, b)
			local t = txt(b, UDim2.fromScale(0.86, 0.7), UDim2.fromScale(0.07, 0.15), 40, "", WHITE, nil, nil, 15)
			pressable(b)
			b.Activated:Connect(function()
				click()
				onBuy()
			end)
			return { button = b, label = t, grad = g }
		end
		local function buyProduct(pk, name)
			if pk.id == 0 then
				toast(name .. " - coming soon!", "info")
			else
				MPS:PromptProductPurchase(plr, pk.id)
			end
		end
		-- a coloured card with rays of light
		local function card(parent, col, size, pos)
			local c = frame(parent, size, pos, col:Lerp(WHITE, 0.25), shade(col, 0.55), shade(col, 0.4), 12, 0.1)
			local rays = make("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.35), Size = UDim2.fromScale(0.9, 0.9), BackgroundColor3 = WHITE, BorderSizePixel = 0, ZIndex = 12 }, c)
			make("UIAspectRatioConstraint", { AspectRatio = 1 }, rays)
			rnd(rays, 1)
			make("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.7), NumberSequenceKeypoint.new(1, 1) }) }, rays)
			return c
		end
		local function bigIcon(parent, name, size, pos)
			local ic = icon(parent, name, size, pos, Vector2.new(0.5, 0.5))
			make("UIAspectRatioConstraint", { AspectRatio = 1 }, ic)
			ic.ZIndex = 13
			X.wobbly[ic] = nil
			return ic
		end

		-- ---------------------------------------------------------------- FEATURED: Royal Egg
		header("FEATURED")
		local feat = block(2.45)
		local fc = frame(feat, UDim2.fromScale(1, 1), nil, Color3.fromRGB(210, 40, 80), Color3.fromRGB(90, 10, 60), Color3.fromRGB(255, 200, 60), 12, 0.06)
		local newTag = frame(fc, UDim2.fromScale(0.09, 0.11), UDim2.fromScale(0.02, 0.04), Color3.fromRGB(255, 90, 90), Color3.fromRGB(190, 10, 30), WHITE, 15, 0.3)
		txt(newTag, UDim2.fromScale(0.84, 0.76), UDim2.fromScale(0.08, 0.12), 26, "New!", WHITE, nil, nil, 16)
		txt(fc, UDim2.fromScale(0.45, 0.17), UDim2.fromScale(0.13, 0.03), 54, "ROYAL EGG", Color3.fromRGB(255, 222, 70), Enum.TextXAlignment.Left, Enum.Font.LuckiestGuy)
		local fsub = txt(fc, UDim2.fromScale(0.6, 0.08), UDim2.fromScale(0.13, 0.19), 26, "", Color3.fromRGB(255, 220, 245), Enum.TextXAlignment.Left)
		-- the egg (violet SECRET egg mesh), turning
		local eggVp = make("ViewportFrame", { Size = UDim2.fromScale(0.22, 0.6), Position = UDim2.fromScale(0.0, 0.18), BackgroundTransparency = 1, Ambient = Color3.fromRGB(210, 200, 220), LightColor = WHITE, LightDirection = Vector3.new(0.5, -1, 0.8), ZIndex = 13 }, fc)
		local eggCam = make("Camera", { FieldOfView = 34 }, eggVp)
		eggVp.CurrentCamera = eggCam
		local eggSrc = C.meshOf("Egg_Secret") or C.meshOf("Egg_Gold")
		local eggPart, eggRot
		if eggSrc then
			eggPart = eggSrc:Clone()
			eggPart.Anchored = true
			eggRot = eggSrc.CFrame.Rotation
			eggPart.CFrame = eggRot
			eggPart.Parent = eggVp
			local h = math.max(eggPart.Size.X, eggPart.Size.Y, eggPart.Size.Z)
			eggCam.CFrame = CFrame.lookAt(Vector3.new(0, h * 0.2, -h * 2.3), Vector3.new())
		end
		RunService.RenderStepped:Connect(function()
			if eggPart and sf.Visible then
				local t = os.clock()
				eggPart.CFrame = CFrame.new(0, math.sin(t * 2) * 0.1, 0) * CFrame.Angles(0, t * 0.8, 0) * eggRot
			end
		end)
		-- the 5 pets it can give (your best zone) with their chances
		local petRow = make("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(0.75, 0.5), Position = UDim2.fromScale(0.235, 0.28), ZIndex = 12 }, fc)
		local petSlots = {}
		for i = 1, #C.ROYAL_PETS do -- v272: the 6 royal pets of the egg
			local s = frame(petRow, UDim2.fromScale(0.158, 1), UDim2.fromScale((i - 1) * 0.1685, 0), Color3.fromRGB(70, 20, 60), Color3.fromRGB(35, 8, 35), C.RARITY[C.ROYAL_PETS[i].i].color, 13, 0.1)
			local pct = txt(s, UDim2.fromScale(0.9, 0.2), UDim2.fromScale(0.05, 0.02), 28, "", WHITE, nil, nil, 16)
			local inc = txt(s, UDim2.fromScale(0.9, 0.16), UDim2.fromScale(0.05, 0.82), 22, "", Color3.fromRGB(255, 222, 70), nil, nil, 16)
			local holder = make("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 0.62), Position = UDim2.fromScale(0, 0.2), ZIndex = 14 }, s)
			petSlots[i] = { pct = pct, inc = inc, holder = holder, key = nil }
		end
		local royalBtns = {}
		for k, pk in ipairs(C.ROYAL_PACKS) do
			local x = 0.235 + (k - 1) * 0.19
			txt(fc, UDim2.fromScale(0.17, 0.07), UDim2.fromScale(x, 0.79), 24, pk.n .. (pk.n == 1 and " Egg" or " Eggs"), WHITE)
			local b = priceBtn(fc, UDim2.fromScale(0.17, 0.12), UDim2.fromScale(x, 0.865), function()
				buyProduct(pk, "Royal Egg")
			end)
			b.label.Text = "R$ " .. C.comma(pk.robux) .. (pk.old and ("  <font color='#ff6b6b'><s>" .. C.comma(pk.old) .. "</s></font>") or "")
			b.label.RichText = true
			royalBtns[k] = b
		end
		local function refreshFeatured()
			local z = math.clamp(attr("Unlocked", 1), 1, #C.ZONES)
			fsub.Text = "EXCLUSIVE pets  ·  x" .. C.ROYAL_MULT .. " income  ·  always GOLD or RAINBOW"
			for i, s in ipairs(petSlots) do
				local rp = C.ROYAL_PETS[i]
				local p = rp.odds * 100
				s.pct.Text = (p >= 10 and string.format("%.0f%%", p)) or string.format("%.1f%%", p)
				local pet = { z = z, i = rp.i, t = 2, v = 100 + i }
				s.inc.Text = "$" .. C.fmt(C.petIncome(pet)) .. "/s"
				local key = z .. "_" .. i
				if s.key ~= key then
					s.key = key
					for _, v in ipairs(s.holder:GetChildren()) do
						v:Destroy()
					end
					local ok, v = pcall(X.petView, s.holder, pet, UDim2.fromScale(1, 1), UDim2.new())
					if ok and v then
						v.ZIndex = 15
					end
				end
			end
		end

		-- ---------------------------------------------------------------- PASSES (2 per row)
		header("PASSES")
		local passCards = {}
		for n = 1, #C.PASSES, 2 do
			local row = block(4.6)
			for k = 0, 1 do
				local p = C.PASSES[n + k]
				if p then
					local c = card(row, p.col, UDim2.fromScale(0.49, 1), UDim2.fromScale(k * 0.51, 0))
					bigIcon(c, p.icon, UDim2.fromScale(0.34, 0.8), UDim2.fromScale(0.17, 0.5))
					txt(c, UDim2.fromScale(0.6, 0.26), UDim2.fromScale(0.36, 0.07), 40, p.name:upper(), WHITE, Enum.TextXAlignment.Left, Enum.Font.LuckiestGuy)
					local ds = txt(c, UDim2.fromScale(0.6, 0.26), UDim2.fromScale(0.36, 0.34), 24, p.desc .. "!", WHITE, Enum.TextXAlignment.Left)
					ds.TextWrapped = true
					local b = priceBtn(c, UDim2.fromScale(0.56, 0.28), UDim2.fromScale(0.38, 0.66), function()
						if hasPass(p.key) then
							toast("You already own " .. p.name, "info")
						elseif p.id == 0 then
							toast(p.name .. " - coming soon!", "info")
						else
							MPS:PromptGamePassPurchase(plr, p.id)
						end
					end)
					table.insert(passCards, { b = b, p = p })
				end
			end
		end

		-- ---------------------------------------------------------------- SPEED (3 per row)
		header("SPEED")
		local srow = block(3.3)
		for k, pk in ipairs(C.SPEED_PACKS) do
			local c = card(srow, Color3.fromRGB(60, 190, 255), UDim2.fromScale(0.32, 1), UDim2.fromScale((k - 1) * 0.34, 0))
			bigIcon(c, "bolt", UDim2.fromScale(0.5, 0.45), UDim2.fromScale(0.5, 0.3))
			txt(c, UDim2.fromScale(0.9, 0.18), UDim2.fromScale(0.05, 0.53), 36, "x" .. pk.mult .. " SPEED", WHITE, nil, Enum.Font.LuckiestGuy)
			local b = priceBtn(c, UDim2.fromScale(0.8, 0.2), UDim2.fromScale(0.1, 0.75), function()
				buyProduct(pk, "Speed pack")
			end)
			b.label.Text = "R$ " .. pk.robux
		end

		-- ---------------------------------------------------------------- MONEY (3 small + 2 wide)
		header("MONEY")
		local cashLabels = {}
		local function cashCard(parent, pk, size, pos)
			local c = card(parent, Color3.fromRGB(70, 200, 80), size, pos)
			bigIcon(c, "coin", UDim2.fromScale(0.45, 0.4), UDim2.fromScale(0.5, 0.26))
			local amt = txt(c, UDim2.fromScale(0.9, 0.17), UDim2.fromScale(0.05, 0.46), 40, "", Color3.fromRGB(255, 240, 120), nil, Enum.Font.LuckiestGuy)
			local secs = pk.secs >= 3600 and (pk.secs / 3600 .. (pk.secs == 3600 and " hour" or " hours")) or (pk.secs / 60 .. " min")
			txt(c, UDim2.fromScale(0.9, 0.09), UDim2.fromScale(0.05, 0.63), 20, pk.name .. "  ·  " .. secs .. " of income", WHITE)
			local b = priceBtn(c, UDim2.fromScale(0.8, 0.2), UDim2.fromScale(0.1, 0.76), function()
				buyProduct(pk, pk.name)
			end)
			b.label.Text = "R$ " .. pk.robux
			if pk.tag then
				local tg = frame(c, UDim2.fromScale(0.42, 0.11), UDim2.fromScale(0.56, 0.03), Color3.fromRGB(255, 90, 90), Color3.fromRGB(190, 10, 30), WHITE, 15, 0.3)
				txt(tg, UDim2.fromScale(0.9, 0.7), UDim2.fromScale(0.05, 0.15), 20, pk.tag, WHITE, nil, nil, 16)
			end
			table.insert(cashLabels, { t = amt, pk = pk })
		end
		local mrow1 = block(3.3)
		for k = 1, 3 do
			cashCard(mrow1, C.CASH_PACKS[k], UDim2.fromScale(0.32, 1), UDim2.fromScale((k - 1) * 0.34, 0))
		end
		local mrow2 = block(3.3)
		for k = 4, 5 do
			cashCard(mrow2, C.CASH_PACKS[k], UDim2.fromScale(0.49, 1), UDim2.fromScale((k - 4) * 0.51, 0))
		end

		-- ---------------------------------------------------------------- right side: jump to a section
		local side = make("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0, 0), Position = UDim2.new(1, 10, 0.12, 0), Size = UDim2.fromScale(0.13, 0.6), ZIndex = 12 }, root)
		make("UIListLayout", { Padding = UDim.new(0.03, 0), SortOrder = Enum.SortOrder.LayoutOrder }, side)
		for k, it in ipairs({ { "FEATURED", "Featured", "gem", Color3.fromRGB(255, 80, 120) }, { "PASSES", "Passes", "star", Color3.fromRGB(255, 190, 40) },
			{ "SPEED", "Speed", "bolt", Color3.fromRGB(60, 190, 255) }, { "MONEY", "Money", "coin", Color3.fromRGB(70, 200, 80) } }) do
			local b = make("TextButton", { AutoButtonColor = false, Text = "", Size = UDim2.fromScale(1, 0.22), BackgroundColor3 = WHITE, LayoutOrder = k, ZIndex = 13 }, side)
			rnd(b, 0.2)
			grad(b, it[4]:Lerp(WHITE, 0.2), shade(it[4], 0.6))
			make("UIStroke", { Thickness = 2.5, Color = BLACK, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, b)
			local ic = icon(b, it[3], UDim2.fromScale(0.6, 0.6), UDim2.fromScale(0.5, 0.38), Vector2.new(0.5, 0.5))
			make("UIAspectRatioConstraint", { AspectRatio = 1 }, ic)
			ic.ZIndex = 14
			X.wobbly[ic] = nil
			txt(b, UDim2.fromScale(0.9, 0.26), UDim2.fromScale(0.05, 0.7), 22, it[2], WHITE, nil, nil, 15)
			pressable(b)
			b.Activated:Connect(function()
				click()
				local h = sections[it[1]]
				if h then
					local y = h.AbsolutePosition.Y - list.AbsolutePosition.Y + list.CanvasPosition.Y
					TweenService:Create(list, TweenInfo.new(0.3, Enum.EasingStyle.Quad), { CanvasPosition = Vector2.new(0, math.max(0, y - 4)) }):Play()
				end
			end)
		end

		local function refreshStore()
			for _, pc in ipairs(passCards) do
				local own = hasPass(pc.p.key)
				pc.b.label.Text = own and "OWNED" or ("R$ " .. pc.p.robux)
				pc.b.grad.Color = own and ColorSequence.new(Color3.fromRGB(170, 170, 180), Color3.fromRGB(110, 110, 120)) or ColorSequence.new(Color3.fromRGB(120, 245, 90), Color3.fromRGB(40, 175, 50))
			end
			local income = attr("Income", 0)
			for _, cl in ipairs(cashLabels) do
				cl.t.Text = "+$" .. C.fmt(math.max(cl.pk.min, math.floor(income * cl.pk.secs)))
			end
			refreshFeatured()
		end
		plr.AttributeChanged:Connect(function(a)
			if sf.Visible and (a == "Income" or a == "Unlocked" or a == "LuckLv" or a == "Passes") then
				refreshStore()
			end
		end)
		storeBtn.Activated:Connect(function()
			refreshStore()
			list.CanvasPosition = Vector2.zero
			storePanel.toggle()
		end)
	end

	-- ============================================================ DAILY rewards (7-day streak)
	local dailyPanel = panel("DAILY REWARDS", "gift", Color3.fromRGB(240, 70, 90), 0.7, 1.75)
	local di = dailyPanel.inner
	ink(di, UDim2.fromScale(0.94, 0.08), UDim2.fromScale(0.03, 0.05), 34, "Come back every day - day 7 gives a free GOLDEN egg!", SOFT, nil, Enum.TextXAlignment.Center)
	local days = {}
	for n = 1, #C.DAILY do
		local big = n == #C.DAILY
		local c = card(di, Color3.fromRGB(90, 96, 200), UDim2.fromScale(big and 0.2 or 0.115, 0.5), UDim2.fromScale(0.03 + (n - 1) * 0.128, 0.18))
		local dl = title(c, UDim2.fromScale(0.9, 0.15), UDim2.fromScale(0.05, 0.05), 30, "DAY " .. n)
		dl.ZIndex = 3
		local ic = icon(c, big and "gift" or "coin", UDim2.fromScale(0.62, 0.4), UDim2.fromScale(0.5, 0.48), Vector2.new(0.5, 0.5))
		ic.ZIndex = 3
		local am = title(c, UDim2.fromScale(0.9, 0.14), UDim2.fromScale(0.05, 0.78), 24, "")
		am.TextColor3 = YELLOW
		am.ZIndex = 3
		local ck = icon(c, "check", UDim2.fromScale(0.5, 0.35), UDim2.fromScale(0.5, 0.48), Vector2.new(0.5, 0.5))
		ck.ZIndex = 4
		X.wobbly[ck] = nil
		days[n] = { card = c, amount = am, check = ck }
	end
	local claimBtn = bigButton(di, GREEN, UDim2.fromScale(0.4, 0.17), UDim2.fromScale(0.3, 0.76))
	local function dailyState()
		local last, day = attr("DailyLast", 0), attr("DailyDay", 0)
		local now = workspace:GetServerTimeNow()
		local ready = last == 0 or now - last >= C.DAILY_COOLDOWN
		local nextDay = (last == 0 or now - last > C.DAILY_RESET) and 1 or (day % #C.DAILY + 1)
		local doneUpTo = (last ~= 0 and now - last <= C.DAILY_RESET) and day or 0
		if ready and nextDay == 1 then
			doneUpTo = 0
		end
		return ready, nextDay, doneUpTo, math.max(0, last + C.DAILY_COOLDOWN - now)
	end
	local function refreshDaily()
		local ready, nextDay, doneUpTo, wait = dailyState()
		dailyBadge.Visible = ready
		if not dailyPanel.frame.Visible then
			return
		end
		for n, d in ipairs(days) do
			local r = C.DAILY[n]
			d.amount.Text = "$" .. C.fmt(math.max(r.min, math.floor(attr("Income", 0) * r.secs)))
			d.check.Visible = n <= doneUpTo
			local col = (n <= doneUpTo and Color3.fromRGB(60, 180, 90)) or ((n == nextDay and ready) and GOLD) or Color3.fromRGB(90, 96, 200)
			X.tint(d.card, col)
		end
		local h, m, sec = math.floor(wait / 3600), math.floor(wait % 3600 / 60), math.floor(wait % 60)
		claimBtn.label.Text = ready and "CLAIM!" or ("NEXT IN " .. (h > 0 and (h .. "h " .. m .. "m") or (m .. "m " .. sec .. "s")))
		claimBtn.color(ready and GREEN or GREY)
	end
	claimBtn.button.Activated:Connect(function()
		if dailyState() then
			Action:FireServer("daily")
		else
			toast("Your next reward is not ready yet", "info")
		end
	end)
	dailyBtn.Activated:Connect(function()
		dailyPanel.toggle()
		refreshDaily()
	end)
	task.spawn(function()
		while true do
			refreshDaily()
			task.wait(1)
		end
	end)

	-- ============================================================ UPGRADES (train / basket / luck from the menu)
	local upPanel = panel("UPGRADES", "upgrade", Color3.fromRGB(70, 200, 160), 0.62, 1.45)
	local ui_ = upPanel.inner
	local UPS = {
		-- v232 (user): TRAINING is bought on the fence board only; here = PEN SPACE, one more pet in your pen per level
		{ kind = "pen", name = "PEN SPACE", icon = "basket", attrName = "PenLv", fx = function(lv) return (C.PEN_MAX + lv) .. " pets" end },
		{ kind = "luck", name = "LUCK", icon = "clover", attrName = "LuckLv", fx = function(lv) return "x" .. C.luck(lv) .. " luck" end },
	}
	local upRows = {}
	for n, u in ipairs(UPS) do
		local r = card(ui_, Color3.fromRGB(236, 232, 250), UDim2.fromScale(0.94, 0.27), UDim2.fromScale(0.03, 0.05 + (n - 1) * 0.31))
		local ic = icon(r, u.icon, UDim2.fromScale(0.8, 0.8), UDim2.fromScale(0.02, 0.1))
		ic.ZIndex = 3
		local nm = ink(r, UDim2.fromScale(0.35, 0.34), UDim2.fromScale(0.16, 0.1), 40, u.name, DARK, Enum.Font.LuckiestGuy)
		nm.ZIndex = 3
		local fx = ink(r, UDim2.fromScale(0.4, 0.26), UDim2.fromScale(0.16, 0.46), 30, "", SOFT)
		fx.ZIndex = 3
		local bg, fill = bar(r, UDim2.fromScale(0.36, 0.12), UDim2.fromScale(0.16, 0.76), Color3.fromRGB(130, 240, 190), Color3.fromRGB(30, 170, 120))
		bg.ZIndex = 3
		fill.ZIndex = 3
		local b = bigButton(r, GREEN, UDim2.fromScale(0.36, 0.62), UDim2.fromScale(0.6, 0.18))
		b.button.Activated:Connect(function()
			local lv = attr(u.attrName, 0)
			if lv >= C.MAX_LV[u.kind] then
				toast(u.name .. " is MAX", "info")
			elseif attr("Cash", 0) < C.cost(u.kind, lv) then
				toast("You need $" .. C.fmt(C.cost(u.kind, lv)), "bad")
			else
				if X.UI.buyUpgrade then X.UI.buyUpgrade(u.kind) else Action:FireServer("upgrade", u.kind) end -- v190: instant
			end
		end)
		upRows[n] = { u = u, fx = fx, fill = fill, b = b, name = nm }
	end
	local function refreshUp()
		if not upPanel.frame.Visible then
			return
		end
		for _, r in ipairs(upRows) do
			local lv, mx = attr(r.u.attrName, 0), C.MAX_LV[r.u.kind]
			r.name.Text = r.u.name .. "  " .. lv .. "/" .. mx
			setBar(r.fill, lv / mx)
			if lv >= mx then
				r.fx.Text = r.u.fx(lv)
				r.b.label.Text = "MAX"
				r.b.color(GREY)
			else
				r.fx.Text = r.u.fx(lv) .. "  >  " .. r.u.fx(lv + 1)
				local cost = C.cost(r.u.kind, lv)
				r.b.label.Text = "$" .. C.fmt(cost)
				r.b.color(attr("Cash", 0) >= cost and GREEN or GREY)
			end
		end
	end
	upBtn.Activated:Connect(function()
		upPanel.toggle()
		refreshUp()
	end)

	-- ============================================================ TOP (leaderboard of the players on this server)
	local topPanel = panel("LEADERBOARD", "trophy", Color3.fromRGB(255, 190, 30), 0.56, 1.25)
	local ti = topPanel.inner
	local topList = make("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(0.94, 0.78), Position = UDim2.fromScale(0.03, 0.19), ZIndex = 2 }, ti)
	make("UIListLayout", { Padding = UDim.new(0.015, 0), SortOrder = Enum.SortOrder.LayoutOrder }, topList)
	local STATS = { { "Cash", "coin", "$" }, { "Speed", "bolt", "" }, { "Rebirth", "rebirth", "" }, { "Caught", "egg", "" } }
	local topStat = 1
	local thumbs = {}
	local function refreshTop()
		if not topPanel.frame.Visible then
			return
		end
		clear(topList)
		local st = STATS[topStat]
		local list = {}
		for _, p in ipairs(game:GetService("Players"):GetPlayers()) do
			table.insert(list, { p = p, v = p:GetAttribute(st[1]) or 0 })
		end
		table.sort(list, function(a, b) return a.v > b.v end)
		for n = 1, math.min(#list, 8) do
			local e = list[n]
			local col = (n == 1 and GOLD) or (n == 2 and Color3.fromRGB(200, 205, 220)) or (n == 3 and Color3.fromRGB(225, 140, 70)) or Color3.fromRGB(110, 116, 210)
			local row = card(topList, e.p == plr and Color3.fromRGB(200, 245, 200) or Color3.fromRGB(232, 232, 252), UDim2.fromScale(1, 0.11), UDim2.new())
			row.LayoutOrder = n
			local badge = make("Frame", { Size = UDim2.fromScale(0.09, 0.8), Position = UDim2.fromScale(0.015, 0.1), ZIndex = 3 }, row)
			make("UIAspectRatioConstraint", { AspectRatio = 1 }, badge)
			face(badge, col, 1)
			local bn = title(badge, UDim2.fromScale(0.7, 0.7), UDim2.fromScale(0.15, 0.13), 30, tostring(n))
			bn.ZIndex = 4
			local av = make("ImageLabel", { BackgroundTransparency = 1, Size = UDim2.fromScale(0.1, 0.9), Position = UDim2.fromScale(0.13, 0.05), ZIndex = 3 }, row)
			make("UIAspectRatioConstraint", { AspectRatio = 1 }, av)
			corner(av, 1)
			if thumbs[e.p.UserId] then
				av.Image = thumbs[e.p.UserId]
			else
				task.spawn(function()
					local ok, img = pcall(function()
						return game:GetService("Players"):GetUserThumbnailAsync(e.p.UserId, Enum.ThumbnailType.HeadShot, Enum.ThumbnailSize.Size100x100)
					end)
					if ok and img then
						thumbs[e.p.UserId] = img
						av.Image = img
					end
				end)
			end
			local nm = title(row, UDim2.fromScale(0.45, 0.6), UDim2.fromScale(0.26, 0.2), 30, e.p.DisplayName)
			nm.TextXAlignment = Enum.TextXAlignment.Left
			nm.ZIndex = 3
			local ic = icon(row, st[2], UDim2.fromScale(0.07, 0.75), UDim2.fromScale(0.68, 0.12))
			ic.ZIndex = 3
			X.wobbly[ic] = nil
			local vl = title(row, UDim2.fromScale(0.22, 0.6), UDim2.fromScale(0.76, 0.2), 30, st[3] .. C.fmt(e.v))
			vl.TextColor3 = YELLOW
			vl.TextXAlignment = Enum.TextXAlignment.Right
			vl.ZIndex = 3
		end
	end
	local pickTop = tabs(ti, { "CASH", "SPEED", "REBIRTHS", "EGGS" }, UDim2.fromScale(0.03, 0.05), UDim2.fromScale(0.94, 0.1), function(i)
		topStat = i
		refreshTop()
	end)
	topBtn.Activated:Connect(function()
		topPanel.toggle()
		pickTop(topStat)
	end)
	task.spawn(function()
		while true do
			task.wait(2)
			refreshTop()
		end
	end)

	-- live refresh of the open menus
	plr.AttributeChanged:Connect(function(a)
		if a == "PetList" or a == "CarryList" or a == "Income" or a == "Equipped" then
			M.refreshPets()
		end
		if a == "EggList" or a == "Eggs" or a == "CarryMax" then
			M.refreshEggs()
		end
		if a == "Cash" then
			refreshUp()
		end
		if a == "TrainLv" or a == "BasketLv" or a == "LuckLv" or a == "PenLv" or a == "Rebirth" then
			refreshUp()
		end
	end)

	return M
end

return M
