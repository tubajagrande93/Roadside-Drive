using UnrealBuildTool;

public class RoadsideDriveTarget : TargetRules
{
    public RoadsideDriveTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V6;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("RoadsideDrive");
    }
}
