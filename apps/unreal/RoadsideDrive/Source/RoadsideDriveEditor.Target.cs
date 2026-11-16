using UnrealBuildTool;

public class RoadsideDriveEditorTarget : TargetRules
{
    public RoadsideDriveEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V6;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("RoadsideDrive");
    }
}
