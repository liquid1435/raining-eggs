r"""Runs Server.server.lua + Client.client.lua against a small fake Roblox (luau.exe) with a fake player:
catch eggs, deposit, treadmill, upgrade, gate, storm, rebirth, leave. Catches runtime errors without Studio.
  py test_game.py
"""
import pathlib
import subprocess
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
LUAU = r'C:\Users\onixfly\roblox\tools\luau\luau.exe'

MOCK = r'''
local NOW = 0
local queue = {}
local function resume(co, ...)
	local ok, t = coroutine.resume(co, ...)
	if not ok then error("ERROR in task: " .. tostring(t) .. "\n" .. debug.traceback(co), 0) end
	if coroutine.status(co) ~= "dead" then table.insert(queue, { co = co, at = NOW + (tonumber(t) or 0) }) end
end
local mtask = {}
function mtask.spawn(f, ...) resume(coroutine.create(f), ...) end
function mtask.defer(f, ...) mtask.spawn(f, ...) end
function mtask.wait(t) coroutine.yield(t or 0.03) return t end
function mtask.delay(t, f, ...)
	local args = { ... }
	table.insert(queue, { co = coroutine.create(function() f(table.unpack(args)) end), at = NOW + t })
end
local function advance(dt, each)
	local stop = NOW + dt
	while true do
		local best, bi = nil, nil
		for i, q in ipairs(queue) do
			if q.at <= stop and (not best or q.at < best.at) then best, bi = q, i end
		end
		if not best then break end
		table.remove(queue, bi)
		if best.at > NOW then NOW = best.at end
		resume(best.co)
		if each then each() end
	end
	NOW = stop
end
local mos = { clock = function() return NOW end, time = function() return math.floor(NOW) end }

local V3 = {}
V3.__index = function(t, k) if k == "Magnitude" then return math.sqrt(t.X * t.X + t.Y * t.Y + t.Z * t.Z) end return nil end
local function v3(x, y, z) return setmetatable({ X = x or 0, Y = y or 0, Z = z or 0 }, V3) end
V3.__add = function(a, b) return v3(a.X + b.X, a.Y + b.Y, a.Z + b.Z) end
V3.__sub = function(a, b) return v3(a.X - b.X, a.Y - b.Y, a.Z - b.Z) end
V3.__mul = function(a, b) if type(b) == "number" then return v3(a.X * b, a.Y * b, a.Z * b) end return v3(a.X * b.X, a.Y * b.Y, a.Z * b.Z) end
V3.__unm = function(a) return v3(-a.X, -a.Y, -a.Z) end
Vector3 = { new = v3, zero = v3(0, 0, 0) }
local CF = {}
local cf
CF.__index = function(t, k) if k == "Rotation" then return cf(Vector3.zero) end return CF[k] end
cf = function(p) return setmetatable({ Position = p }, CF) end
CF.__mul = function(a, b) if getmetatable(b) == V3 then return a.Position + b end return cf(a.Position + b.Position) end
CF.__add = function(a, b) return cf(a.Position + b) end
function CF.PointToObjectSpace(a, p) return p - a.Position end
function CF.VectorToWorldSpace(a, v) return v end
function CF.VectorToObjectSpace(a, v) return v end
CF.__sub = function(a, b) return cf(a.Position - b) end
CFrame = {
	new = function(x, y, z) if type(x) == "table" then return cf(x) end return cf(v3(x, y, z)) end,
	Angles = function() return cf(v3(0, 0, 0)) end,
	lookAt = function(p) return cf(p) end,
}
CF.RightVector = v3(1, 0, 0)
NumberRange = { new = function() return {} end }
NumberSequence = { new = function() return {} end }
NumberSequenceKeypoint = { new = function() return {} end }
local function col(r, g, b) return { R = r, G = g, B = b } end
Color3 = { new = col, fromRGB = function(r, g, b) return col(r / 255, g / 255, b / 255) end, fromHSV = function(h, s, v) return col(v, v, v) end }
local U2 = {}
U2.__add = function(a, b) return setmetatable({}, U2) end
U2.__sub = U2.__add
local function u2() return setmetatable({}, U2) end
UDim2 = { new = u2, fromScale = u2, fromOffset = u2 }
UDim = { new = function() return {} end }
Vector2 = { new = function() return {} end }
TweenInfo = { new = function() return {} end }
ColorSequence = { new = function() return {} end }
RaycastParams = { new = function() return {} end }
local function enumProxy(path)
	return setmetatable({}, { __index = function(_, k) return enumProxy(path .. "." .. k) end, __tostring = function() return path end })
end
Enum = enumProxy("Enum")

local SIGNALS = { PromptGamePassPurchaseFinished = true, OnServerEvent = 1, OnClientEvent = 1, Triggered = 1, CharacterAdded = 1, PlayerAdded = 1, PlayerRemoving = 1, AttributeChanged = 1,
	Touched = 1, DescendantAdded = 1, Activated = 1, MouseButton1Down = 1, MouseButton1Up = 1, MouseLeave = 1, MouseEnter = 1, JumpRequest = 1, RenderStepped = 1, Completed = 1, Heartbeat = 1 }
local function signal()
	local s = { fns = {} }
	function s:Connect(f) table.insert(self.fns, f) return { Disconnect = function() end } end
	function s:Wait() end
	function s:Fire(...) for _, f in ipairs(self.fns) do f(...) end end
	return s
end
local tags, tagAdded, tagRemoved = {}, {}, {}
local M = {}
local Inst = {}
local LOG = { notices = {}, eggs = 0, hatches = {} }
local THE_PLAYER
Inst.__index = function(t, k)
	local m = M[k]
	if m then return m end
	if k == "Parent" then return rawget(t, "_parent") end
	if SIGNALS[k] then
		local sigs = rawget(t, "_sig")
		if not sigs[k] then sigs[k] = signal() end
		return sigs[k]
	end
	if k == "Position" then local c = rawget(t, "CFrame") return c and c.Position or v3(0, 0, 0) end
	for _, c in ipairs(rawget(t, "_kids")) do if c.Name == k then return c end end
	return nil
end
Inst.__newindex = function(t, k, v)
	if k == "Parent" then
		local old = rawget(t, "_parent")
		if old then
			local kids = rawget(old, "_kids")
			for i, c in ipairs(kids) do if c == t then table.remove(kids, i) break end end
		end
		rawset(t, "_parent", v)
		if v then table.insert(rawget(v, "_kids"), t) end
	elseif k == "Position" then
		rawset(t, "CFrame", cf(v))
	else
		rawset(t, k, v)
	end
end
local function new(class, name, parent)
	local o = setmetatable({ ClassName = class, Name = name or class, _kids = {}, _attrs = {}, _sig = {} }, Inst)
	if class == "Humanoid" then rawset(o, "Health", 100) rawset(o, "WalkSpeed", 16) end
	if parent then o.Parent = parent end
	return o
end
Instance = { new = function(class) return new(class) end }
function M:GetChildren() local r = {} for i, c in ipairs(self._kids) do r[i] = c end return r end
function M:GetDescendants()
	local r = {}
	local function walk(o) for _, c in ipairs(o._kids) do table.insert(r, c) walk(c) end end
	walk(self)
	return r
end
function M:FindFirstChild(n, rec)
	for _, c in ipairs(self._kids) do if c.Name == n then return c end end
	if rec then for _, c in ipairs(self:GetDescendants()) do if c.Name == n then return c end end end
	return nil
end
function M:WaitForChild(n) local c = self:FindFirstChild(n) if not c then error("WaitForChild would hang: " .. n, 2) end return c end
function M:FindFirstChildOfClass(cn) for _, c in ipairs(self._kids) do if c.ClassName == cn then return c end end return nil end
function M:IsA(cn)
	if self.ClassName == cn then return true end
	if cn == "BasePart" then return self.ClassName == "Part" or self.ClassName == "SpawnLocation" end
	return false
end
function M:Destroy() self.Parent = nil end
function M:ClearAllChildren() for _, c in ipairs(self:GetChildren()) do c.Parent = nil end end
function M:GetFullName() local p = rawget(self, "_parent") return (p and p:GetFullName() .. "." or "") .. self.Name end
function M:SetAttribute(k, v)
	if self._attrs[k] == v then return end
	self._attrs[k] = v
	local s = rawget(self, "_sig").AttributeChanged
	if s then s:Fire(k) end
end
function M:GetAttribute(k) return self._attrs[k] end
function M:GetPlayerFromCharacter(c) if THE_PLAYER and rawget(THE_PLAYER, "Character") == c then return THE_PLAYER end return nil end
function M:ScaleTo(s) rawset(self, "_scale", s) end
function M:Emit() end
function M:GetPropertyChangedSignal() return signal() end
function M:GetAttributeChangedSignal() return signal() end
function M:PivotTo(c) rawset(self, "_pivot", c) end
function M:GetPivot() return rawget(self, "_pivot") or cf(v3(0, 0, 0)) end
function M:GetBoundingBox() return cf(v3(0, 1, 0)), v3(2, 2, 2) end
warn = function(...) print("WARN", ...) end
local services = {}
function M:GetService(n) if not services[n] then services[n] = new(n, n) end return services[n] end
function M:GetPlayers() return self:GetChildren() end
function M:BindToClose() end
function M:GetDataStore() error("datastore not available in the test") end
function M:GetServerTimeNow() return NOW end
function M:Raycast(o, d) return { Position = v3(o.X, 0, o.Z), Instance = self } end
function M:AddTag(o, tag)
	tags[tag] = tags[tag] or {}
	table.insert(tags[tag], o)
	if tagAdded[tag] then tagAdded[tag]:Fire(o) end
end
function M:GetTagged(tag) local r = {} for _, o in ipairs(tags[tag] or {}) do if o.Parent then table.insert(r, o) end end return r end
function M:GetInstanceAddedSignal(tag) tagAdded[tag] = tagAdded[tag] or signal() return tagAdded[tag] end
function M:GetInstanceRemovedSignal(tag) tagRemoved[tag] = tagRemoved[tag] or signal() return tagRemoved[tag] end
function M:Create() return { Play = function() end, Completed = signal() } end
function M:AddItem() end
function M:PlayLocalSound() end
function M:FireAllClients(...)
	if self.Name == "Notice" then table.insert(LOG.notices, "[all] " .. tostring((...))) end
	if self.Name == "EggSpawn" then LOG.eggs = LOG.eggs + 1 end
	self.OnClientEvent:Fire(...)
end
function M:FireClient(plr, ...)
	if self.Name == "Notice" then table.insert(LOG.notices, tostring((...))) end
	if self.Name == "Hatch" then local pet = ... table.insert(LOG.hatches, pet.z .. "_" .. pet.i) end
	self.OnClientEvent:Fire(...)
end
function M:FireServer(...) self.OnServerEvent:Fire(THE_PLAYER, ...) end

game = new("DataModel", "game")
workspace = new("Workspace", "Workspace")
services.Workspace = workspace
local RS, Players, Lighting = game:GetService("ReplicatedStorage"), game:GetService("Players"), game:GetService("Lighting")
new("ModuleScript", "Config", RS)
new("ModuleScript", "Sfx", RS)
new("ModuleScript", "UIMenus", RS)
new("ColorCorrectionEffect", "ColorCorrection", Lighting)
new("Camera", "Camera", workspace).CFrame = cf(v3(0, 10, -40))
rawset(workspace, "CurrentCamera", workspace.Camera)

-- fake map
local Map = new("Model", "Map", workspace)
local function part(name, parent, x, y, z, sx, sy, sz)
	local p = new("Part", name, parent)
	p.CFrame = cf(v3(x, y, z))
	p.Size = v3(sx, sy, sz)
	return p
end
for i = 1, 8 do
	local b = new("Model", "Base" .. i, Map)
	local px = -147 + (i - 1) * 42
	part("PenFloor", b, px, 0.1, -86, 34, 0.1, 52)
	part("Treadmill", b, px - 11.5, 0.4, -67, 5, 0.8, 8)
	local sign = part("OwnerSign", b, px + 9, 5.7, -58.4, 7, 3, 0.6)
	new("TextLabel", "Label", new("Frame", "Bg", new("SurfaceGui", "SignFront", sign))).Text = "EMPTY"
	part("DemoPet", b, px, 0.5, -80, 1, 1, 1)
end
local plaza = new("Folder", "Plaza", Map)
for _, x in ipairs({ -52, 52, -96, 96 }) do part("ShopPad", new("Model", "Shop", plaza), x, 0.1, -26.5, 11, 0.3, 4) end
for _, x in ipairs({ -140, 140 }) do new("SurfaceGui", "SignFront", part("Leaderboard", plaza, x, 11, -14, 20, 14, 1.4)) end
part("DemoEgg", new("Model", "Zone1_SunnyMeadow", Map), 0, 60, 50, 3, 3, 3)
part("DemoEgg", plaza, 0, 6, -22, 3, 3, 3)
'''

DRIVER = r'''
-- ---------------------------------------------------------------- run
local CONFIG = __config()
local SFXT = __sfx()
local MENUS = __menus(nil, mos, mtask)
local function fakeRequire(m) if m and m.Name == "Sfx" then return SFXT end if m and m.Name == "UIMenus" then return MENUS end return CONFIG end
__server(fakeRequire, mos, mtask)
assert(not Map.Base1:FindFirstChild("DemoPet"), "DemoPet stays")
assert(Map.Plaza:FindFirstChild("DemoEgg"), "statue egg removed")
assert(not Map.Zone1_SunnyMeadow:FindFirstChild("DemoEgg"), "zone DemoEgg stays")

local plr = new("Player", "Tester")
rawset(plr, "UserId", 42)
rawset(plr, "DisplayName", "Tester")
new("PlayerGui", "PlayerGui", plr)
local char = new("Model", "Tester")
local head = new("Part", "Head", char)
head.CFrame = cf(v3(0, 4.5, -44))
local hrp = new("Part", "HumanoidRootPart", char)
hrp.CFrame = cf(v3(0, 3, -44))
local hum = new("Humanoid", "Humanoid", char)
rawset(plr, "Character", char)
plr.Parent = Players
rawset(Players, "LocalPlayer", plr)
THE_PLAYER = plr
Players.PlayerAdded:Fire(plr)
__client(fakeRequire, mos, mtask)

local RunService = game:GetService("RunService")
local frames = 0
local function frame() frames = frames + 1 RunService.RenderStepped:Fire(0.016) end
local function run(t) for _ = 1, math.floor(t / 0.05) do advance(0.05) frame() end end
local function A(k) return plr:GetAttribute(k) end
local function go(x, y, z) hrp.CFrame = cf(v3(x, y, z)) end

run(1)
print("base", A("Base"), "sign:", Map.Base1.OwnerSign.OwnerTag.NameLabel.Text, "walk", hum.WalkSpeed)
assert(A("Base") == 1)

-- catch eggs: follow every egg the server announces
local Remotes = RS.Remotes
local target
Remotes.EggSpawn.OnClientEvent:Connect(function(id, x, z, y0, gy, fall, zone, kind)
	if (not target or NOW > target.till) and (kind ~= "rotten" or math.random() < 0.3) then target = { x = x, z = z, till = NOW + fall + 0.3 } end
end)
go(0, 3, 50)
local t0 = NOW
while A("Carry") < A("CarryMax") and NOW - t0 < 60 do
	run(0.25)
	if target then go(target.x, 3, target.z) end
end
print("after catching: carry", A("Carry"), "/", A("CarryMax"), "combo", A("Combo"), "eggs spawned", LOG.eggs, "hatches", table.concat(LOG.hatches, " "), "t", NOW - t0)
assert(A("Carry") == A("CarryMax"), "basket did not fill")
assert(char:FindFirstChild("CarryPets") and #char.CarryPets:GetChildren() == A("Carry"), "carry models")
target = nil
run(1) -- basket full: extra eggs must be refused

-- deposit in the pen
go(-147, 3, -86)
run(0.6)
print("after deposit: carry", A("Carry"), "pets", A("Pets"), "income", A("Income"), "pen models", #Map.Base1.Pets:GetChildren())
assert(A("Carry") == 0 and A("Pets") >= 1)
assert(#Map.Base1.Pets:GetChildren() == A("Pets"))
run(1)

-- treadmill
go(-158.5, 3, -67)
run(5)
print("after treadmill: speed", A("Speed"), "walk", hum.WalkSpeed, "cash", A("Cash"))
assert(A("Speed") > 0)

-- upgrades through the prompts
local function trigger(partName, x)
	for _, pp in ipairs(game:GetService("CollectionService"):GetTagged("UpgPrompt")) do
		local p = pp.Parent
		if p.Name == partName and (not x or math.abs(p.Position.X - x) < 1) then pp.Triggered:Fire(plr) return pp end
	end
	error("no prompt on " .. partName)
end
run(60)
local pp = trigger("Treadmill", -158.5)
print("train prompt text:", pp.ObjectText, "| TrainLv", A("TrainLv"), "cash", A("Cash"))
-- shop zones: stand on the pad, buy from the menu (Action "shop")
go(-52, 3, -26.5) run(1) Remotes.Action:FireServer("shop", "basket")
go(52, 3, -26.5) run(1) Remotes.Action:FireServer("shop", "luck")
go(-96, 3, -26.5) run(1) Remotes.Action:FireServer("shop", "sell")
go(52, 3, -26.5) Remotes.Action:FireServer("shop", "basket") -- too far from the basket shop: ignored
print("BasketLv", A("BasketLv"), "LuckLv", A("LuckLv"))

-- gate: zone 2 without speed -> pushed back (speed is small)
do
	go(0, 3, 160)
	run(0.5)
	print("gate: z after", hrp.Position.Z)
	assert(hrp.Position.Z < 140, "gate did not stop the player")
end

-- rebirth without enough speed, then stay in zone 1 through a whole storm
Remotes.Action:FireServer("rebirth")
go(0, 3, 60)
local storms = 0
Remotes.EggSpawn.OnClientEvent:Connect(function(id, x, z, y0, gy, fall, zone, kind) if kind == "storm" then storms = storms + 1 target = { x = x, z = z, till = NOW + fall + 3 } end end)
local tEnd = workspace:GetAttribute("StormNext") + CONFIG.STORM_LEN + 20 -- through the first storm
while NOW < tEnd do
	run(0.25)
	if target then go(target.x, 3, target.z) end
	if A("Carry") >= A("CarryMax") then go(-147, 3, -86) run(0.6) go(0, 3, 60) target = nil end
end
print("after storm: storm eggs", storms, "StormNext-now", workspace:GetAttribute("StormNext") - NOW, "pets", A("Pets"), "cash", A("Cash"), "index", A("Index"))
assert(storms >= 1, "no storm egg")

-- long run with a lot of speed: train, then rebirth
go(-158.5, 3, -67)
for _ = 1, 40 do run(20) trigger("Treadmill", -158.5) end
print("long train: speed", A("Speed"), "TrainLv", A("TrainLv"), "cash", A("Cash"), "income", A("Income"))
local before = A("Rebirth")
Remotes.Action:FireServer("rebirth")
run(1)
print("rebirth", before, "->", A("Rebirth"), "speed", A("Speed"), "cash", A("Cash"))

go(0, 3, 160)
run(0.5)
print("gate after rebirth: z", hrp.Position.Z)
assert(hrp.Position.Z < 140, "gate did not stop the player")

-- buy zone 2 at the gate: too poor first (cash is 0 after the rebirth), then with enough cash
local gate2 = workspace.ZoneGates.Gate2.Gate
assert(#workspace.ZoneGates:GetChildren() == 9, "9 gates")
print("gate text:", gate2.PriceGui.ZoneName.Text, gate2.PriceGui.Price.Text, "| unlocked", A("Unlocked"))
go(0, 3, 100)
local poorCash = A("Cash")
gate2.Touched:Fire(hrp)
assert(poorCash >= 1000 or A("Unlocked") == 1, "bought without cash") -- income after rebirth can already pass $1K (random pets)
local tw = NOW
while A("Cash") < 1000 and NOW - tw < 900 do run(5) end
local cashBefore = A("Cash")
gate2.Touched:Fire(hrp)
run(0.5)
print("gate buy: cash", cashBefore, "->", A("Cash"), "unlocked", A("Unlocked"), "collide", gate2.CanCollide, "gui", gate2.PriceGui.Enabled)
assert(A("Unlocked") == 2 and (poorCash >= 1000 or A("Cash") < cashBefore) and gate2.CanCollide == false and gate2.PriceGui.Enabled == false, "gate buy failed")
assert(workspace.ZoneGates.Gate3.Gate.CanCollide == true, "gate 3 must stay closed")
go(0, 3, 160)
run(0.5)
assert(hrp.Position.Z == 160, "owner pushed back from an unlocked zone")
go(0, 3, 300)
run(0.5)
assert(hrp.Position.Z < 280, "zone 3 is open without paying")
workspace.ZoneGates.Gate4.Gate.Touched:Fire(hrp)
run(2)

-- leaderboard text
run(6)
for _, b in ipairs(Map.Plaza:GetChildren()) do
	if b.Name == "Leaderboard" then
		local out = {}
		for _, l in ipairs(b:GetDescendants()) do if l.ClassName == "TextLabel" and l.Text ~= "" then table.insert(out, l.Text) end end
		print("board:", table.concat(out, " | "))
	end
end

-- new menus: upgrades from the menu, daily reward
local bl = A("BasketLv")
while A("Cash") < math.floor(100 * 4 ^ bl) do run(5) end
Remotes.Action:FireServer("upgrade", "basket")
run(0.3)
print("menu upgrade basket", bl, "->", A("BasketLv"))
assert(A("BasketLv") == bl + 1, "menu upgrade failed")
local c0 = A("Cash")
Remotes.Action:FireServer("daily")
run(0.3)
print("daily: day", A("DailyDay"), "cash", c0, "->", A("Cash"))
assert(A("DailyDay") == 1 and A("Cash") > c0, "daily reward failed")
local c1 = A("Cash")
Remotes.Action:FireServer("daily") -- too soon
run(0.3)
assert(A("DailyDay") == 1, "daily claimed twice")

-- click every button of the HUD and the menus (each must run without an error)
local hud = plr:FindFirstChild("PlayerGui"):FindFirstChild("RainingEggsHUD")
local clicked, labels = 0, {}
local function textOf(b)
	for _, d in ipairs(b:GetDescendants()) do
		if d.ClassName == "TextLabel" and d.Text ~= "" then return d.Text end
	end
	return b.Text or ""
end
for round = 1, 2 do
	for _, b in ipairs(hud:GetDescendants()) do
		if b.ClassName == "TextButton" then
			b.Activated:Fire()
			clicked = clicked + 1
			labels[textOf(b)] = true
			run(0.05)
		end
	end
end
local names = {}
for k in pairs(labels) do table.insert(names, k) end
table.sort(names)
print("clicked", clicked, "buttons:", table.concat(names, " | "))
for _, need in ipairs({ "PETS", "STORE", "DAILY", "UPGRADE", "TOP", "INDEX", "REBIRTH" }) do
	assert(labels[need], "button missing: " .. need)
end

-- leave
Players.PlayerRemoving:Fire(plr)
run(2)
print("after leave: sign", Map.Base1.OwnerSign.OwnerTag.NameLabel.Text, "pen models", #Map.Base1.Pets:GetChildren())
local seen, uniq = {}, {}
for _, n in ipairs(LOG.notices) do if not seen[n] then seen[n] = true table.insert(uniq, n) end end
print("NOTICES (" .. #LOG.notices .. "):")
for i = 1, math.min(#uniq, 40) do print("  " .. uniq[i]) end
print("frames", frames, "OK")
'''


def wrap(name, src):
    return f'local function {name}(require, os, task)\n{src}\nend\n'


cfg = (HERE / 'Config.lua').read_text(encoding='utf-8')
full = (MOCK + f'local function __config()\n{cfg}\nend\n' + 'local function __sfx()' + chr(10) + (HERE / 'Sfx.lua').read_text(encoding='utf-8') + chr(10) + 'end' + chr(10) + wrap('__menus', (HERE / 'UIMenus.lua').read_text(encoding='utf-8')) + wrap('__server', (HERE / 'Server.server.lua').read_text(encoding='utf-8')) +
        wrap('__client', (HERE / 'Client.client.lua').read_text(encoding='utf-8')) + DRIVER)
tmp = pathlib.Path(tempfile.gettempdir()) / 're_test_game.luau'
tmp.write_text(full, encoding='utf-8')
r = subprocess.run([LUAU, str(tmp)], capture_output=True, text=True)
print(r.stdout[-6000:])
print(r.stderr[-3000:])
print('exit', r.returncode)
