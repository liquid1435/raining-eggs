-- quick check of Config.lua outside Roblox (luau.exe): numbers, formatting, pet builder with a tiny mock
Color3 = { fromRGB = function(r, g, b) return { R = r / 255, G = g / 255, B = b / 255 } end, new = function(r, g, b) return { R = r, G = g, B = b } end }
Vector3 = { new = function(x, y, z) return setmetatable({ X = x, Y = y, Z = z }, { __mul = function(a, s) return a end }) end }
CFrame = { new = function() return {} end }
Enum = setmetatable({}, { __index = function() return setmetatable({}, { __index = function() return 1 end }) end })
local count = 0
Instance = { new = function(c) count = count + 1 return { ClassName = c } end }
local C = require("./Config")
assert(#C.ZONES == 10)
for i, z in ipairs(C.ZONES) do
	assert(#z.pets == 5, z.name)
	C.buildPet(i, 5, 1, false)
	C.buildPet(i, 1, 1, true)
end
print("parts+welds made", count)
print(C.fmt(999), C.fmt(1000), C.fmt(1250), C.fmt(2.5e10), C.fmt(1e8), C.comma(2000), C.comma(150))
print("train", C.cost("train", 0), C.trainPower(0), C.trainPower(5), "basket", C.cost("basket", 1), "luck", C.cost("luck", 1))
print("walk", C.walkSpeed(0), C.walkSpeed(500), C.walkSpeed(2.5e10), "fall", C.fallTime(1), C.fallTime(10))
for i, z in ipairs(C.ZONES) do
	print(i, z.name, z.req, z.pets[1].income, z.pets[5].income)
end
