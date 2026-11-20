-- ModuleScript. Call attach(model) after the rig has been placed upright.
local StarlightDragonVFX = {}
local active = setmetatable({}, { __mode = "k" })
local gold = Color3.fromRGB(255, 205, 109)
local pearl = Color3.fromRGB(255, 250, 216)
local mint = Color3.fromRGB(167, 255, 222)
local shimmer = ColorSequence.new(pearl, gold)

function StarlightDragonVFX.attach(model)
    if active[model] then
        return active[model]
    end
    local function bone(name)
        local result = model:FindFirstChild(name, true)
        assert(result and result:IsA("Bone"), "Missing Starlight Dragon bone " .. name)
        return result
    end
    local root, body, tip = bone("Root"), bone("Body"), bone("GlowSocket")
    local mesh = root:FindFirstAncestorWhichIsA("BasePart")
    assert(mesh, "Place the imported bone hierarchy inside its skinned MeshPart")
    local scale = mesh.Size.Magnitude / 8.02
    local owned = {}
    local function create(class, name, parent)
        local item = Instance.new(class)
        item.Name = name
        item.Parent = parent
        table.insert(owned, item)
        return item
    end
    local function attachment(parent, name, offset)
        local socket = create("Attachment", name, parent)
        socket.Position = offset
        return socket
    end
    local top = attachment(tip, "CometTop", Vector3.new(0, .085 * scale, 0))
    local bottom = attachment(tip, "CometBottom", Vector3.new(0, -.085 * scale, 0))
    local trail = create("Trail", "CometRibbon", mesh)
    trail.Attachment0, trail.Attachment1 = top, bottom
    trail.FaceCamera = true
    trail.Lifetime = .34
    trail.MinLength = .015 * scale
    trail.LightEmission = 1
    trail.Color = ColorSequence.new(pearl, mint)
    trail.WidthScale = NumberSequence.new(1, 0)
    trail.Transparency = NumberSequence.new(.1, 1)
    local light = create("PointLight", "CometLight", tip)
    light.Color, light.Range, light.Brightness = gold, 4.2 * scale, .65

    local function glitter(parent, name, rate)
        local emitter = create("ParticleEmitter", name, parent)
        emitter.Texture = "rbxasset://textures/particles/sparkles_main.dds"
        emitter.Rate = rate
        emitter.Color = shimmer
        emitter.LightEmission = 1
        emitter.Lifetime = NumberRange.new(.65, 1.2)
        emitter.Speed = NumberRange.new(.16 * scale, .52 * scale)
        emitter.SpreadAngle = Vector2.new(180, 180)
        emitter.Size = NumberSequence.new({
            NumberSequenceKeypoint.new(0, 0),
            NumberSequenceKeypoint.new(.24, .24 * scale),
            NumberSequenceKeypoint.new(1, 0),
        })
        emitter.Rotation = NumberRange.new(-45, 45)
        emitter.RotSpeed = NumberRange.new(-25, 25)
        return emitter
    end
    for _, name in ipairs({"Wing_L", "Wing_R"}) do
        local side = name == "Wing_L" and -1 or 1
        glitter(attachment(bone(name), "WingGlints", Vector3.new(side * .78, .50, 0) * scale), "StarDust", 3)
    end
    glitter(tip, "TailDust", 5)
    local burst = glitter(body, "HatchBurst", 0)
    burst.Speed = NumberRange.new(2.0 * scale, 4.1 * scale)
    burst.Lifetime = NumberRange.new(.45, .90)
    burst.Drag = 1.4

    -- Four cubic quarter circles track the pet's base, independently of the hop.
    local radius = 2.57 * scale
    local center = root.WorldPosition + Vector3.new(0, .025 * scale, 0)
    local anchors = {}
    for index = 1, 4 do
        local angle = (index - 1) * math.pi / 2
        local radial = Vector3.new(math.cos(angle), 0, math.sin(angle))
        local tangent = Vector3.new(-math.sin(angle), 0, math.cos(angle))
        local a = attachment(mesh, "OrbitAnchor" .. index, Vector3.zero)
        a.CFrame = mesh.CFrame:ToObjectSpace(CFrame.fromMatrix(center + radial * radius, tangent, Vector3.yAxis))
        anchors[index] = a
    end
    for index = 1, 4 do
        local arc = create("Beam", "LegendaryOrbit", mesh)
        arc.Attachment0, arc.Attachment1 = anchors[index], anchors[index % 4 + 1]
        arc.CurveSize0, arc.CurveSize1 = .552285 * radius, .552285 * radius
        arc.Width0, arc.Width1 = .035 * scale, .035 * scale
        arc.Segments = 14
        arc.FaceCamera, arc.LightEmission = true, 1
        arc.Color = shimmer
        arc.Transparency = NumberSequence.new(.16)
    end
    local handle = {}
    function handle.hatch()
        burst:Emit(28)
    end
    local connection
    function handle.destroy()
        if active[model] ~= handle then return end
        active[model] = nil
        connection:Disconnect()
        for i = #owned, 1, -1 do owned[i]:Destroy() end
    end
    active[model] = handle
    connection = model.Destroying:Connect(handle.destroy)
    return handle
end

return StarlightDragonVFX
