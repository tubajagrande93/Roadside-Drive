"""A single daytime sun, captured atmosphere, and sparse native cloud cards."""

import math

import unreal
from g04a_materials import LIB, MATERIALS, PROPS, bind, connect, create, node, save

# A compact optical-density mask from smooth noise and overlapping cloud lobes.
DENSITY = """
struct Noise {
  float value(float2 p) {
    float2 i=floor(p), f=frac(p);
    f=f*f*(3-2*f);
    float4 h=frac(sin(dot(i,float2(127.1,311.7))+float4(0,127.1,311.7,438.8))*43758.5453);
    return lerp(lerp(h.x,h.y,f.x),lerp(h.z,h.w,f.x),f.y);
  }
  float lobe(float2 p, float2 c, float2 radius) {
    return 1-dot((p-c)/radius,(p-c)/radius);
  }
};
Noise n;
float2 p=UV;
float density=max(max(n.lobe(p,float2(.30,.55),float2(.22,.20)),
                       n.lobe(p,float2(.51,.48),float2(.25,.30))),
                  n.lobe(p,float2(.73,.55),float2(.19,.17)));
float detail=.47*n.value(p*13)+.25*n.value(p*27)+.12*n.value(p*58)+.05*n.value(p*114);
return smoothstep(.03,.44,density+(detail-.45)*1.5)*.96;
"""


def ensure_actor(actors, existing, cls):
    matches = [actor for actor in existing if isinstance(actor, cls)]
    if len(matches) > 1:
        raise RuntimeError(f"Duplicate G04A lighting actors: {cls.__name__}")
    return (
        matches[0] if matches else actors.spawn_actor_from_class(cls, unreal.Vector())
    )


def atmosphere(actors, point, yaw):
    existing = actors.get_all_level_actors()
    sun = ensure_actor(actors, existing, unreal.DirectionalLight)
    sun.set_actor_rotation(unreal.Rotator(pitch=-58, yaw=-20), False)
    direct = sun.get_component_by_class(unreal.DirectionalLightComponent)
    direct.set_mobility(unreal.ComponentMobility.MOVABLE)
    direct.set_editor_property("atmosphere_sun_light", True)
    direct.set_intensity(4.5)
    sky = ensure_actor(actors, existing, unreal.SkyAtmosphere)
    sky.set_actor_label("RD G04A summer atmosphere")
    ambient = ensure_actor(actors, existing, unreal.SkyLight)
    fill = ambient.get_component_by_class(unreal.SkyLightComponent)
    fill.set_mobility(unreal.ComponentMobility.MOVABLE)
    fill.set_real_time_capture(False)
    fill.set_intensity(0.9)
    fill.set_lower_hemisphere_color(unreal.LinearColor(0.09, 0.10, 0.12, 1))
    fill.recapture_sky()
    add_clouds(actors, point, yaw)


def add_clouds(actors, point, yaw):
    material = create(
        "M_G04A_Cloud", MATERIALS, unreal.Material, unreal.MaterialFactoryNew
    )
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("two_sided", True)
    uv = node(material, "MaterialExpressionTextureCoordinate", -650, 0)
    coordinate_input = unreal.CustomInput()
    coordinate_input.set_editor_property("input_name", "UV")
    density = node(
        material,
        "MaterialExpressionCustom",
        -400,
        0,
        code=DENSITY,
        output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT1,
        inputs=[coordinate_input],
    )
    connect(uv, density, 0)
    white = node(
        material,
        "MaterialExpressionConstant3Vector",
        -400,
        160,
        constant=unreal.LinearColor(1.25, 1.27, 1.30, 1.0),
    )
    bind(density, PROPS.MP_OPACITY)
    bind(white, PROPS.MP_EMISSIVE_COLOR)
    LIB.recompile_material(material)
    save(material)
    plane = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
    angle = math.radians(yaw)
    fx, fy = math.cos(angle), math.sin(angle)
    for index, (forward, lateral, height, width, depth, rotation) in enumerate(
        (
            (430, -140, 245, 170, 98, 27),
            (640, 170, 320, 280, 125, -20),
            (520, -320, 340, 220, 105, 53),
            (720, 430, 290, 180, 90, 12),
        ),
        1,
    ):
        location = unreal.Vector(
            point.x + (fx * forward - fy * lateral) * 100,
            point.y + (fy * forward + fx * lateral) * 100,
            height * 100,
        )
        actor = actors.spawn_actor_from_class(
            unreal.StaticMeshActor,
            location,
            unreal.Rotator(yaw=yaw + rotation),
        )
        actor.set_actor_label(f"RD G04A cloud {index}")
        actor.set_actor_scale3d(unreal.Vector(width, depth, 1))
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        comp.set_static_mesh(plane)
        comp.set_material(0, material)
        comp.set_cast_shadow(False)
        comp.set_collision_profile_name("NoCollision")
        comp.set_editor_property("generate_overlap_events", False)
