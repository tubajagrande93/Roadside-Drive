"""Original PBR assets and one UV-independent road surface material."""

import unreal

ROOT = "/Game/RoadsideDrive/Generated/G04A"
MATERIALS = ROOT + "/Materials"
LIB = unreal.MaterialEditingLibrary
PROPS = unreal.MaterialProperty
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
SURFACES = {"asphalt": 4, "paving": 2, "concrete": 1}


def create(name, folder, asset_class, factory):
    asset = TOOLS.create_asset(name, folder, asset_class, factory())
    if not asset:
        raise RuntimeError(f"Could not create {folder}/{name}")
    return asset


def node(material, classname, x, y, **properties):
    expression = LIB.create_material_expression(
        material, getattr(unreal, classname), x, y
    )
    for key, value in properties.items():
        expression.set_editor_property(key, value)
    return expression


def connect(source, dest, pin, output=""):
    pins = list(LIB.get_material_expression_input_names(dest))
    if not LIB.connect_material_expressions(
        source, output, dest, pins[pin] if isinstance(pin, int) else pin
    ):
        raise RuntimeError(
            f"Cannot connect {source.get_name()} to {dest.get_name()}:{pin} in {pins}"
        )


def bind(expression, prop, output=""):
    if not LIB.connect_material_property(expression, output, prop):
        raise RuntimeError(f"Cannot drive material property {prop}")


def save(asset):
    if not asset.get_path_name().startswith(ROOT + "/"):
        raise RuntimeError(
            f"Refusing to save outside the G04A namespace: {asset.get_path_name()}"
        )
    if not unreal.EditorAssetLibrary.save_loaded_asset(asset, False):
        raise RuntimeError(f"Asset save failed: {asset.get_path_name()}")


def import_asset(path, folder, asset_type):
    task = unreal.AssetImportTask()
    for key, value in {
        "filename": str(path),
        "destination_path": folder,
        "automated": True,
        "replace_existing": False,
        "save": False,
    }.items():
        task.set_editor_property(key, value)
    TOOLS.import_asset_tasks([task])
    imported = task.get_objects()
    assets = [item for item in imported if isinstance(item, asset_type)]
    if len(assets) != 1 or not assets[0].get_path_name().startswith(folder + "/"):
        raise RuntimeError(f"Expected one owned {asset_type.__name__} for {path.name}")
    if asset_type == unreal.StaticMesh:
        for asset in imported:
            save(asset)
    return assets[0]


def create_pbr(texture_dir, manifest):
    textures = {}
    for name, spec in sorted(manifest["assets"].items()):
        image = import_asset(texture_dir / name, ROOT + "/Textures", unreal.Texture2D)
        channel = spec["channel"]
        compression = {
            "albedo": unreal.TextureCompressionSettings.TC_DEFAULT,
            "normal": unreal.TextureCompressionSettings.TC_NORMALMAP,
            "roughness": unreal.TextureCompressionSettings.TC_MASKS,
        }[channel]
        image.set_editor_property("compression_settings", compression)
        image.set_editor_property("srgb", channel == "albedo")
        save(image)
        textures[spec["texture_kind"], channel] = image

    master = create(
        "M_G04A_WorldXY", MATERIALS, unreal.Material, unreal.MaterialFactoryNew
    )
    position = node(master, "MaterialExpressionWorldPosition", -750, 0)
    xy = node(master, "MaterialExpressionComponentMask", -545, 0, r=True, g=True)
    scale = node(
        master,
        "MaterialExpressionScalarParameter",
        -550,
        125,
        parameter_name="WorldUVScale",
        default_value=0.0025,
    )
    uv = node(master, "MaterialExpressionMultiply", -355, 0)
    connect(position, xy, 0)
    connect(xy, uv, "A")
    connect(scale, uv, "B")
    for index, (channel, prop, sampler, output) in enumerate(
        (
            (
                "albedo",
                PROPS.MP_BASE_COLOR,
                unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
                "",
            ),
            (
                "normal",
                PROPS.MP_NORMAL,
                unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
                "",
            ),
            (
                "roughness",
                PROPS.MP_ROUGHNESS,
                unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
                "R",
            ),
        )
    ):
        sample = node(
            master,
            "MaterialExpressionTextureSampleParameter2D",
            -100,
            220 * index,
            parameter_name=channel,
            texture=textures["asphalt", channel],
            sampler_type=sampler,
        )
        connect(uv, sample, 0)
        if channel == "albedo":
            gain = node(
                master,
                "MaterialExpressionScalarParameter",
                -100,
                -130,
                parameter_name="BaseColorGain",
                default_value=1.0,
            )
            tint = node(master, "MaterialExpressionMultiply", 160, 0)
            connect(sample, tint, "A")
            connect(gain, tint, "B")
            bind(tint, prop)
        else:
            bind(sample, prop, output)
    metal = node(master, "MaterialExpressionConstant", -80, 690, r=0.0)
    bind(metal, PROPS.MP_METALLIC)
    LIB.recompile_material(master)
    save(master)

    instances = {}
    for surface, tile in SURFACES.items():
        instance = create(
            "MI_G04A_" + surface,
            MATERIALS,
            unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew,
        )
        LIB.set_material_instance_parent(instance, master)
        uv_scale = 1 / (tile * 100)
        gain = 0.62 if surface == "asphalt" else 1.0
        LIB.set_material_instance_scalar_parameter_value(
            instance, "BaseColorGain", gain
        )
        LIB.set_material_instance_scalar_parameter_value(
            instance, "WorldUVScale", uv_scale
        )
        for channel in ("albedo", "normal", "roughness"):
            LIB.set_material_instance_texture_parameter_value(
                instance, channel, textures[surface, channel]
            )
        LIB.update_material_instance(instance)
        observed = LIB.get_material_instance_scalar_parameter_value(
            instance, "WorldUVScale"
        )
        if abs(observed - uv_scale) > 1e-8:
            raise RuntimeError(
                f"Wrong world UV scale for {surface}: {observed} versus {uv_scale}"
            )
        observed_gain = LIB.get_material_instance_scalar_parameter_value(
            instance, "BaseColorGain"
        )
        if abs(observed_gain - gain) > 1e-6:
            raise RuntimeError(f"Wrong base color gain for {surface}: {observed_gain}")
        for channel in ("albedo", "normal", "roughness"):
            actual = LIB.get_material_instance_texture_parameter_value(
                instance, channel
            )
            if actual != textures[surface, channel]:
                raise RuntimeError(
                    f"Missing material channel {channel} for {surface}: {actual}"
                )
        save(instance)
        instances[surface] = instance
    return instances
