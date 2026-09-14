// Original MIT. Interactive, data-backed transport laboratory.
#include "FusionRuntime.h"
#include "FusionTransportLab.h"
#include "ProceduralMeshComponent.h"
#include "Engine/World.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SSlider.h"
#include "Widgets/Text/STextBlock.h"
#include "Styling/CoreStyle.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Serialization/JsonSerializer.h"
namespace{FText TT(const FString& S){return FText::FromString(S);}const FLinearColor BG(.024,.042,.055,1),FG(.1,.82,.78,1),Muted(.62,.71,.77,1);}
void AFusionController::OpenTransportLab(bool Active){
 if(Active&&!Lab){Lab=GetWorld()->SpawnActor<AFusionTransportLab>();Lab->Load();}
 bLab=Active;bEvidence=false;bResearch=false;bNeutron=false;
 if(Lab)Lab->SetActive(Active);if(Rig){Rig->SetActorEnableCollision(!Active);for(auto P:Rig->Parts)P->SetHiddenInGame(Active);if(!Active)RefreshLayers();}
}
TSharedRef<SWidget> AFusionController::MakeTransportLabUI(){
 auto Btn=[](const FString& Name,TFunction<void()> Do){return SNew(SButton).ContentPadding(FMargin(12,9)).OnClicked_Lambda([Do](){Do();return FReply::Handled();})[SNew(STextBlock).Text(TT(Name))];};
 auto Left=SNew(SVerticalBox);Left->AddSlot().AutoHeight().Padding(0,0,0,10)[SNew(STextBlock).Text(TT(TEXT("RECORDED BOUNDARY TESTS"))).ColorAndOpacity(FG)];
 TArray<FString> Names;if(Lab)for(auto Row:Lab->Cases)Names.Add(Row->GetStringField(TEXT("title")));
 for(int I=0;I<Names.Num();I++)Left->AddSlot().AutoHeight().Padding(0,4)[Btn(Names[I],[this,I](){if(Lab){Lab->SelectCase(I);LabDistance=620;}})];
 Left->AddSlot().AutoHeight().Padding(0,12)[Btn(TEXT("Source context / module"),[this](){if(Lab){Lab->SetSourceContext(!Lab->bSourceContext);LabDistance=Lab->bSourceContext?5200:620;LabYaw=-145;LabPitch=25;}})];
 Left->AddSlot().AutoHeight().Padding(0,16)[SNew(SCheckBox).IsEnabled_Lambda([this](){return Lab&&!Lab->bSourceContext;}).IsChecked_Lambda([this](){return Lab&&Lab->bCutHardware?ECheckBoxState::Checked:ECheckBoxState::Unchecked;}).OnCheckStateChanged_Lambda([this](ECheckBoxState V){if(Lab){Lab->bCutHardware=V==ECheckBoxState::Checked;Lab->BuildHardware();}})[SNew(STextBlock).Text(TT(TEXT("Cutaway metal / armour")))]];
 Left->AddSlot().AutoHeight().Padding(0,6)[SNew(SCheckBox).IsEnabled_Lambda([this](){return Lab&&!Lab->bSourceContext;}).IsChecked_Lambda([this](){return Lab&&Lab->bShowTrails?ECheckBoxState::Checked:ECheckBoxState::Unchecked;}).OnCheckStateChanged_Lambda([this](ECheckBoxState V){if(Lab)Lab->bShowTrails=V==ECheckBoxState::Checked;})[SNew(STextBlock).Text(TT(TEXT("Recorded path trails")))]];
 Left->AddSlot().AutoHeight().Padding(0,6)[SNew(SCheckBox).IsEnabled_Lambda([this](){return Lab&&!Lab->bSourceContext;}).IsChecked_Lambda([this](){return Lab&&Lab->bShowField?ECheckBoxState::Checked:ECheckBoxState::Unchecked;}).OnCheckStateChanged_Lambda([this](ECheckBoxState V){if(Lab){Lab->bShowField=V==ECheckBoxState::Checked;Lab->BuildField();}})[SNew(STextBlock).Text(TT(TEXT("Computed heating slice")))]];
 Left->AddSlot().AutoHeight().Padding(0,16)[SNew(STextBlock).Text(TT(TEXT("SLICE HEIGHT (physical z)"))).ColorAndOpacity(FG)];
 Left->AddSlot().AutoHeight()[SNew(SSlider).IsEnabled_Lambda([this](){return Lab&&!Lab->bSourceContext;}).Value_Lambda([this](){return Lab?Lab->SliceIndex/15.f:.5f;}).OnValueChanged_Lambda([this](float V){if(Lab)Lab->SetSlice(V);})];
 Left->AddSlot().AutoHeight().Padding(0,20)[Btn(TEXT("Reset 3D camera"),[this](){LabYaw=-145;LabPitch=22;LabDistance=Lab&&Lab->bSourceContext?5200:620;})];
 Left->AddSlot().AutoHeight().Padding(0,8)[SNew(STextBlock).Text(TT(TEXT("Right-drag: orbit\nMouse wheel: zoom\nClick slice: inspect voxel\n\nSteel and helium domains follow model dimensions. The translucent block is homogenized breeder, not resolved pebbles."))).AutoWrapText(true).ColorAndOpacity(Muted)];
 auto Center=SNew(SVerticalBox);Center->AddSlot().AutoHeight().Padding(20,4)[SNew(STextBlock).Text(TT(TEXT("3D TRANSPORT LAB | SOURCE / RECORDED PHYSICS"))).Font(FCoreStyle::GetDefaultFontStyle("Bold",18)).ColorAndOpacity(FG).AutoWrapText(true)];
 Center->AddSlot().AutoHeight().Padding(20,5)[SNew(STextBlock).Text(TT(TEXT("Local r838 module; NOT full-reactor geometry. Cyan = neutron, gold = photon.\nModule: recorded log-time playback; source context: geometric-ray animation only. No invented coolant flow."))).AutoWrapText(true).ColorAndOpacity(Muted)];
 Center->AddSlot().FillHeight(1)[SNew(SBox)];
 Center->AddSlot().AutoHeight().Padding(20,8)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(BG).Padding(10)[SNew(STextBlock).Text_Lambda([this](){return TT(Lab?Lab->FieldInspection:TEXT("Dataset unavailable"));}).AutoWrapText(true).ColorAndOpacity(FG)]];
 Center->AddSlot().AutoHeight().Padding(20,4)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(BG).Padding(10)[SNew(SVerticalBox)
 +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text_Lambda([this](){return TT(Lab?Lab->TimeLabel():TEXT("No track data"));}).AutoWrapText(true)]
 +SVerticalBox::Slot().AutoHeight().Padding(0,10)[SNew(SHorizontalBox)+SHorizontalBox::Slot().AutoWidth()[Btn(TEXT("Play / pause"),[this](){if(Lab)Lab->bPlayback=!Lab->bPlayback;})]+SHorizontalBox::Slot().FillWidth(1).Padding(10,0)[SNew(SSlider).Value_Lambda([this](){return Lab?Lab->Phase:0.f;}).OnValueChanged_Lambda([this](float V){if(Lab){Lab->Phase=V;Lab->bPlayback=false;Lab->Animate(0);}})]]]];
 auto Right=SNew(SScrollBox)+SScrollBox::Slot()[SNew(STextBlock).Text_Lambda([this](){return TT(Lab?Lab->Status():TEXT("Open the data-backed module"));}).Font(FCoreStyle::GetDefaultFontStyle("Regular",13)).AutoWrapText(true)];
 auto Header=SNew(SHorizontalBox)+SHorizontalBox::Slot().FillWidth(1)[SNew(STextBlock).Text(TT(TEXT("FUSION WORKBENCH | PHYSICS IN VIEW"))).Font(FCoreStyle::GetDefaultFontStyle("Bold",19)).ColorAndOpacity(FG)]
 +SHorizontalBox::Slot().AutoWidth()[Btn(TEXT("Read study and limits"),[this](){OpenTransportLab(false);bResearch=true;ResearchQuery=TEXT("source coupling");UpdateResearchRows();})]
 +SHorizontalBox::Slot().AutoWidth().Padding(15,0)[Btn(TEXT("Return to reactor"),[this](){OpenTransportLab(false);})];
 return SNew(SVerticalBox)+SVerticalBox::Slot().AutoHeight()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(BG).Padding(18)[Header]]
 +SVerticalBox::Slot().FillHeight(1).Padding(12,12)[SNew(SHorizontalBox)+SHorizontalBox::Slot().AutoWidth()[SNew(SBox).WidthOverride(275)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(BG).Padding(14)[Left]]]+SHorizontalBox::Slot().FillWidth(1)[Center]+SHorizontalBox::Slot().AutoWidth()[SNew(SBox).WidthOverride(295)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(BG).Padding(14)[Right]]]]
 +SVerticalBox::Slot().AutoHeight()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(BG).Padding(12)[SNew(STextBlock).Text(TT(TEXT("Recorded Monte Carlo histories are not a live plasma. Source hypotheses are not experimental bounds. No global TBR or new net-power claim."))).AutoWrapText(true).ColorAndOpacity(Muted)]];
}
void AFusionController::TestTransportLab(){
 FString Before=ConfigurationId;OpenTransportLab(true);bool OK=Lab&&Lab->Validate()&&Rig&&!Rig->GetActorEnableCollision();int Count=0;
 if(Lab&&Lab->Ready)for(int I=0;I<Lab->Cases.Num();I++){Lab->SelectCase(I);OK&=Lab->Validate();Count+=Lab->Tracks.Num();Lab->bPlayback=false;Lab->Phase=.45f;Lab->Animate(0);OK&=FMath::IsFinite(Lab->PhysicalTime);}
 if(Lab&&Lab->Ready){Lab->SelectCase(4);Lab->bPlayback=false;Lab->Phase=.4f;Lab->Animate(0);Lab->InspectWorld(Lab->WorldPoint(FVector(2.5*Lab->Size.X/24,2.5*Lab->Size.Y/16,(Lab->SliceIndex+.5)*Lab->Size.Z/16)));OK&=Lab->FieldInspection.Contains(TEXT("Voxel (2,2,"));}
 if(FParse::Param(FCommandLine::Get(),TEXT("WorkbenchSourceContextTest"))&&Lab&&Lab->Ready){Lab->SetSourceContext(true);LabDistance=5200;LabYaw=-145;LabPitch=25;Lab->bPlayback=false;Lab->Phase=.45f;Lab->Animate(0);OK&=Lab->SourceWire&&Lab->SourceBody&&Lab->VisibleParticles==Lab->SourceDrawIndices.Num();}
 OK&=Before==ConfigurationId;auto O=MakeShared<FJsonObject>();O->SetBoolField(TEXT("passed"),OK);O->SetNumberField(TEXT("case_count"),Lab?Lab->Cases.Num():0);O->SetNumberField(TEXT("total_recorded_paths"),Count);O->SetNumberField(TEXT("canonical_source_sites"),Lab?Lab->SourceSites.Num():0);O->SetNumberField(TEXT("rendered_source_sites"),Lab?Lab->SourceDrawIndices.Num():0);O->SetBoolField(TEXT("configuration_unchanged"),Before==ConfigurationId);O->SetBoolField(TEXT("physical_validation"),false);
 FString Out;FJsonSerializer::Serialize(O,TJsonWriterFactory<>::Create(&Out));auto Dest=FPaths::ProjectSavedDir()/TEXT("Automation/transport-lab-test.json");IFileManager::Get().MakeDirectory(*FPaths::GetPath(Dest),true);FFileHelper::SaveStringToFile(Out,*Dest);
}
