-- PetAnim (v129): the Codex voxel pets as moving parts, playing their Codex animations (Idle, Walk, HappyHatch,
-- PenLife) without any uploaded Animation. Data: ReplicatedStorage.PetAnimData (made by blender/anim_codex_pets.py),
-- meshes: ReplicatedStorage.Assets.Pet_<z>_<i>__<k> (one per bone, the pet's texture goes on them).
--   PA.build(pet, s, anchored, tier) -> Model or nil (nil = no part meshes yet: the caller uses the one-piece pet)
--   PA.pose(model, clip, t, pivot)   -> moves the parts of a built model to clip time t (seconds, loops) at pivot
local RS = game:GetService("ReplicatedStorage")
local PA = {}
-- if the parts come out mirrored front/back (Roblox turned the import half a turn), set this to true
PA.FLIP = false
local Y180 = CFrame.Angles(0, math.pi, 0)
-- v139 (user screenshot: you saw the back of the fox's head, paws turned backwards): Studio's importer turns every
-- part mesh half a turn on its own axis. Each part is turned back here; write false if heads ever look backwards.
PA.PART_TURN = true
local function turn()
	return PA.PART_TURN and Y180 or CFrame.identity
end

local okData, DATA = pcall(require, RS:WaitForChild("PetAnimData", 10))
if not okData then
	DATA = {}
end

local function asset(name)
	local a = RS:FindFirstChild("Assets")
	local m = a and a:FindFirstChild(name, true)
	if m and not m:IsA("MeshPart") then
		m = m:FindFirstChildWhichIsA("MeshPart", true)
	end
	return m
end

-- ------------------------------------------------------------ base64 -> buffer (decoded once per pet and clip)
local B64 = {}
do
	local abc = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
	for i = 1, 64 do
		B64[string.byte(abc, i)] = i - 1
	end
end
local function decode(s)
	local n = #s
	local pad = (string.sub(s, -2) == "==" and 2) or (string.sub(s, -1) == "=" and 1) or 0
	local out = buffer.create(n // 4 * 3 - pad)
	local o = 0
	for i = 1, n, 4 do
		local a, b, c, d = string.byte(s, i, i + 3)
		local v = B64[a] * 262144 + B64[b] * 4096 + (B64[c] or 0) * 64 + (B64[d] or 0)
		buffer.writeu8(out, o, v // 65536)
		if o + 1 < buffer.len(out) then
			buffer.writeu8(out, o + 1, (v // 256) % 256)
		end
		if o + 2 < buffer.len(out) then
			buffer.writeu8(out, o + 2, v % 256)
		end
		o = o + 3
	end
	return out
end

-- clip frames: frames[f][j] = CFrame (unscaled translation) of part j at frame f
local cache = {}
local function frames(key, clip)
	local ck = key .. "/" .. clip
	if cache[ck] then
		return cache[ck]
	end
	local d = DATA[key]
	local c = d and d.clips[clip]
	if not c then
		return nil
	end
	local buf = decode(c.d)
	local list, o = {}, 0
	for f = 1, c.n do
		local row = {}
		for j = 1, d.parts do
			local qx, qy, qz, qw = buffer.readi8(buf, o) / 127, buffer.readi8(buf, o + 1) / 127, buffer.readi8(buf, o + 2) / 127, buffer.readi8(buf, o + 3) / 127
			local tx, ty, tz = buffer.readi16(buf, o + 4) / 1000, buffer.readi16(buf, o + 6) / 1000, buffer.readi16(buf, o + 8) / 1000
			o = o + 10
			local m = math.sqrt(qx * qx + qy * qy + qz * qz + qw * qw)
			if m < 1e-4 then
				qx, qy, qz, qw, m = 0, 0, 0, 1, 1
			end
			row[j] = { tx, ty, tz, CFrame.new(0, 0, 0, qx / m, qy / m, qz / m, qw / m) }
		end
		list[f] = row
	end
	-- v143: pets now walk around the pen themselves, so a Walk clip that moves forward on its own (root motion)
	-- would slide them and snap back each loop: take out a steady horizontal drift, keep the steps and the sway
	if clip == "Walk" and c.n > 1 then
		local function mid(row)
			local x, z = 0, 0
			for j = 1, #row do
				x, z = x + row[j][1], z + row[j][3]
			end
			return x / #row, z / #row
		end
		local x0, z0 = mid(list[1])
		local x1, z1 = mid(list[c.n])
		if (x1 - x0) ^ 2 + (z1 - z0) ^ 2 > 0.04 then
			for f = 1, c.n do
				local a = (f - 1) / (c.n - 1)
				for _, e in ipairs(list[f]) do
					e[1], e[3] = e[1] - (x1 - x0) * a, e[3] - (z1 - z0) * a
				end
			end
		end
	end
	local entry = { n = c.n, len = c.len, list = list }
	cache[ck] = entry
	return entry
end

local function keyOf(pet) -- v153: variants 2/3 = <z>_<i>_<v>
	return pet.z .. "_" .. pet.i .. ((pet.v or 1) > 1 and ("_" .. pet.v) or "")
end

function PA.has(pet)
	local key = keyOf(pet)
	return DATA[key] ~= nil and asset("Pet_" .. key .. "__1") ~= nil
end

-- the pet's texture for its tier (the one-piece meshes Pet_z_i / _G / _R carry the uploaded textures)
local function textureOf(key, tier)
	local m = (tier == 2 and asset("Pet_" .. key .. "_G")) or (tier == 3 and asset("Pet_" .. key .. "_R")) or asset("Pet_" .. key)
	return m and m.TextureID or ""
end

function PA.build(pet, s, anchored, meshYaw, meshSize)
	local key = keyOf(pet)
	local d = DATA[key]
	if not d or not asset("Pet_" .. key .. "__1") then
		return nil
	end
	local tier = pet.t or 1
	local k = meshSize * s / d.longest
	local m = Instance.new("Model")
	local root = Instance.new("Part")
	root.Name = "Root"
	root.Size = Vector3.new(0.2, 0.2, 0.2)
	root.Transparency = 1
	root.CanCollide, root.CanTouch, root.CanQuery, root.Massless, root.Anchored = false, false, false, true, anchored
	root.CFrame = CFrame.new()
	root.Parent = m
	m.PrimaryPart = root
	local base = CFrame.new(0, -1.75 * s, 0) * CFrame.Angles(0, meshYaw, 0)
	local tex = textureOf(key, tier)
	local parts = {}
	for j = 1, d.parts do
		local src = asset("Pet_" .. key .. "__" .. j)
		if src then
			local p = src:Clone()
			p.Name = "Part" .. j
			p.Size = src.Size * k
			p.TextureID = tex
			p.Color = Color3.new(1, 1, 1)
			p.Material = Enum.Material.SmoothPlastic
			p.Reflectance = tier == 2 and 0.12 or 0
			p.CanCollide, p.CanTouch, p.CanQuery, p.Massless, p.CastShadow = false, false, false, true, false
			p.Anchored = anchored
			local r = d.rest[j]
			local fx = PA.FLIP and -1 or 1
			p.CFrame = base * CFrame.new(fx * r[1] * k, r[2] * k, fx * r[3] * k) * turn()
			p.Parent = m
			if not anchored then
				local w = Instance.new("WeldConstraint")
				w.Part0, w.Part1 = root, p
				w.Parent = p
			end
			parts[j] = p
		end
	end
	m:SetAttribute("AnimKey", key)
	m:SetAttribute("AnimK", k)
	m:SetAttribute("AnimS", s)
	m:SetAttribute("AnimYaw", meshYaw)
	return m
end

-- per model: parts in order + rest CFrames (scaled), cached
local rigs = setmetatable({}, { __mode = "k" })
local function rig(model)
	local r = rigs[model]
	if r then
		return r
	end
	local key = model:GetAttribute("AnimKey")
	local d = key and DATA[key]
	if not d then
		return nil
	end
	local k, s = model:GetAttribute("AnimK"), model:GetAttribute("AnimS")
	r = { key = key, k = k, base = CFrame.new(0, -1.75 * s, 0) * CFrame.Angles(0, model:GetAttribute("AnimYaw") or math.pi, 0), parts = {}, rest = {}, idx = {} }
	for j = 1, d.parts do
		local p = model:FindFirstChild("Part" .. j)
		if p then
			table.insert(r.parts, p)
			table.insert(r.idx, j)
			local q = d.rest[j]
			local fx = PA.FLIP and -1 or 1
			table.insert(r.rest, CFrame.new(fx * q[1] * k, q[2] * k, fx * q[3] * k) * turn())
		end
	end
	r.root = model.PrimaryPart
	rigs[model] = r
	return r
end

local cfs = {}
function PA.pose(model, clip, t, pivot)
	local r = rig(model)
	local fr = r and frames(r.key, clip)
	if not fr then
		return false
	end
	local x = (t % fr.len) / fr.len * (fr.n - 1)
	local f0 = math.floor(x)
	local a = x - f0
	local row0, row1 = fr.list[f0 + 1], fr.list[math.min(f0 + 2, fr.n)]
	local k = r.k
	local top = pivot * r.base
	table.clear(cfs)
	for n, j in ipairs(r.idx) do
		local p0, p1 = row0[j], row1[j]
		local rot = p0[4]:Lerp(p1[4], a)
		local tx, ty, tz = p0[1] + (p1[1] - p0[1]) * a, p0[2] + (p1[2] - p0[2]) * a, p0[3] + (p1[3] - p0[3]) * a
		local D = CFrame.new(tx * k, ty * k, tz * k) * rot
		if PA.FLIP then
			D = Y180 * D * Y180
		end
		cfs[n] = top * D * r.rest[n]
	end
	workspace:BulkMoveTo(r.parts, cfs, Enum.BulkMoveMode.FireCFrameChanged)
	if r.root then
		r.root.CFrame = pivot
	end
	return true
end

return PA
