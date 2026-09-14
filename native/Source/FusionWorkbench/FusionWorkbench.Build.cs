using UnrealBuildTool;
public class FusionWorkbench : ModuleRules {
 public FusionWorkbench(ReadOnlyTargetRules Target) : base(Target) {
  PCHUsage=PCHUsageMode.UseExplicitOrSharedPCHs;
  PublicDependencyModuleNames.AddRange(new[]{"Core","CoreUObject","Engine","InputCore","Slate","SlateCore","Json","JsonUtilities","HTTP","ProceduralMeshComponent"});
 }
}
