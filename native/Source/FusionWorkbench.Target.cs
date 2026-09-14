using UnrealBuildTool;
public class FusionWorkbenchTarget : TargetRules {
 public FusionWorkbenchTarget(TargetInfo Target) : base(Target) {
  Type=TargetType.Game; DefaultBuildSettings=BuildSettingsVersion.V6;
  IncludeOrderVersion=EngineIncludeOrderVersion.Unreal5_7;
  ExtraModuleNames.Add("FusionWorkbench");
 }
}
