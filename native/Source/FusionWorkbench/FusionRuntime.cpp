// Original application code: MIT. No engine source is redistributed here.
#include "FusionRuntime.h"
#include "FusionTransportLab.h"
#include "ProceduralMeshComponent.h"
#include "Camera/CameraComponent.h"
#include "Components/SceneComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/DirectionalLight.h"
#include "Components/DirectionalLightComponent.h"
#include "Engine/Scene.h"
#include "UnrealClient.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "HAL/PlatformFileManager.h"
#include "HAL/PlatformProcess.h"
#include "Serialization/MemoryReader.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SSlider.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SLeafWidget.h"
#include "Styling/CoreStyle.h"
#include "Rendering/DrawElements.h"
#include "InputCoreTypes.h"
namespace {
 FLinearColor Ink(0.025f,0.045f,0.06f,1),Panel(0.045f,0.075f,0.095f,1),Teal(0.15f,0.82f,0.73f,1),Muted(0.56f,0.68f,0.75f,1),Gold(0.95f,0.66f,0.28f,1);
 FString Str(TSharedPtr<FJsonObject> O,const FString& K){FString S;if(O)O->TryGetStringField(K,S);return S;}
 double Num(TSharedPtr<FJsonObject> O,const FString& K){double V=0;if(O)O->TryGetNumberField(K,V);return V;}
 TSharedPtr<FJsonObject> Obj(TSharedPtr<FJsonObject> O,const FString& K){const TSharedPtr<FJsonObject>* R=nullptr;return O&&O->TryGetObjectField(K,R)?*R:nullptr;}
 TArray<double> Numbers(TSharedPtr<FJsonObject> O,const FString& K){TArray<double> R;const TArray<TSharedPtr<FJsonValue>>* A=nullptr;if(O&&O->TryGetArrayField(K,A))for(auto& V:*A)R.Add(V->AsNumber());return R;}
 FText Txt(const FString& S){return FText::FromString(S);}
 TSharedRef<STextBlock> Text(const FString& S,int Size=14,FLinearColor C=FLinearColor::White){return SNew(STextBlock).Text(Txt(S)).Font(FCoreStyle::GetDefaultFontStyle("Regular",Size)).ColorAndOpacity(C).AutoWrapText(false);}
 bool ReadString(FArchive& A,FString& Out){uint32 N=0;A<<N;if(N>256||A.Tell()+N>A.TotalSize())return false;TArray<uint8> B;B.SetNumZeroed(N+1);A.Serialize(B.GetData(),N);Out=UTF8_TO_TCHAR(reinterpret_cast<const char*>(B.GetData()));return !A.IsError();}
 bool SaveJson(const FString& Path,TSharedPtr<FJsonObject> O){FString S;FJsonSerializer::Serialize(O.ToSharedRef(),TJsonWriterFactory<>::Create(&S));IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path),true);return FFileHelper::SaveStringToFile(S,*Path,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);}
}
AFusionGameMode::AFusionGameMode(){PlayerControllerClass=AFusionController::StaticClass();DefaultPawnClass=nullptr;}
AFusionRig::AFusionRig(){RootComponent=CreateDefaultSubobject<USceneComponent>("Root");Camera=CreateDefaultSubobject<UCameraComponent>("Camera");Camera->SetupAttachment(RootComponent);Camera->FieldOfView=48;Camera->PostProcessSettings.bOverride_AutoExposureBias=true;Camera->PostProcessSettings.AutoExposureBias=0;}
void AFusionRig::Orbit(float Y,float P,float D){FRotator R(-P,Y+180,0);FVector Eye=D*FVector(FMath::Cos(FMath::DegreesToRadians(P))*FMath::Cos(FMath::DegreesToRadians(Y)),FMath::Cos(FMath::DegreesToRadians(P))*FMath::Sin(FMath::DegreesToRadians(Y)),FMath::Sin(FMath::DegreesToRadians(P)));Camera->SetWorldLocation(Eye);Camera->SetWorldRotation((-Eye).Rotation());}
FString AFusionRig::GroupFor(UPrimitiveComponent* C)const{for(int32 I=0;I<Parts.Num();++I)if(Parts[I]==C)return Groups[I];return {};}
void AFusionRig::Refresh(const TMap<FString,bool>& L,bool Cut){for(int32 I=0;I<Parts.Num();++I){const bool* Enabled=L.Find(Groups[I]);bool Show=Enabled&&*Enabled&&!(Cut&&Cuts[I]);Parts[I]->SetVisibility(Show);Parts[I]->SetCollisionEnabled(Show?ECollisionEnabled::QueryOnly:ECollisionEnabled::NoCollision);}}
bool AFusionRig::LoadModel(const FString& Id){
 if(Id!=TEXT("r838")&&Id!=TEXT("r900"))return false;
 TArray<uint8> Bytes;if(!FFileHelper::LoadFileToArray(Bytes,*(FPaths::ProjectContentDir()/TEXT("WorkbenchData")/(Id+TEXT(".fwm"))))||Bytes.Num()>32000000)return false;
 FMemoryReader A(Bytes);uint32 Magic=0,Count=0;A<<Magic<<Count;if(Magic!=0x31425746||Count!=34)return false;
 for(auto P:Parts)P->DestroyComponent();Parts.Empty();Groups.Empty();Cuts.Empty();FBox Bounds(ForceInit);
 UMaterialInterface* Base=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Workbench/M_Surface.M_Surface"));if(!Base)return false;
 for(uint32 I=0;I<Count;++I){FString Name,Group;if(!ReadString(A,Name)||!ReadString(A,Group))return false;
  uint8 Cut=0;uint32 NV=0,NI=0;A<<Cut<<NV<<NI;if(NV>250000||NI>1500000||NI%3||A.Tell()+16+int64(NV)*24+int64(NI)*4>A.TotalSize())return false;
  float R,G,B,Alpha;A<<R<<G<<B<<Alpha;TArray<FVector> V,N;TArray<int32> Indices;TArray<FVector2D> UV;
  V.Reserve(NV);N.Reserve(NV);UV.Init(FVector2D::ZeroVector,NV);
  for(uint32 J=0;J<NV;++J){float X,Y,Z;A<<X<<Y<<Z;if(!FMath::IsFinite(X)||!FMath::IsFinite(Y)||!FMath::IsFinite(Z))return false;V.Add(FVector(X,Y,Z));Bounds+=V.Last();}
  for(uint32 J=0;J<NV;++J){float X,Y,Z;A<<X<<Y<<Z;N.Add(FVector(X,Y,Z));}
  for(uint32 J=0;J<NI;++J){uint32 K;A<<K;if(K>=NV)return false;Indices.Add(int32(K));}
  auto P=NewObject<UProceduralMeshComponent>(this,*Name);P->SetupAttachment(RootComponent);P->RegisterComponent();P->bUseAsyncCooking=true;P->bUseComplexAsSimpleCollision=true;
  P->CreateMeshSection(0,V,Indices,N,UV,TArray<FColor>(),TArray<FProcMeshTangent>(),true);
  auto M=UMaterialInstanceDynamic::Create(Base,this);M->SetVectorParameterValue(TEXT("Color"),FLinearColor(R,G,B,1));M->SetScalarParameterValue(TEXT("Glow"),Group==TEXT("plasma")?0.35f:0.18f);P->SetMaterial(0,M);
  P->SetCollisionResponseToAllChannels(ECR_Ignore);P->SetCollisionResponseToChannel(ECC_Visibility,ECR_Block);Parts.Add(P);Groups.Add(Group);Cuts.Add(Cut!=0);
 }
 ModelSize=Bounds.GetSize();return !A.IsError()&&A.Tell()==A.TotalSize()&&Parts.Num()==34;
}
FString AFusionController::Title()const{return Str(Config,TEXT("title"));}
double AFusionController::Metric(const FString& K)const{return Num(Obj(Config,TEXT("metrics")),K);}
TArray<double> AFusionController::Times()const{return Numbers(Obj(Config,TEXT("pulse")),TEXT("time_s"));}
TArray<double> AFusionController::Series(const FString& K)const{return Numbers(Obj(Obj(Config,TEXT("pulse")),TEXT("series")),K);}
double AFusionController::Sample(const FString& K,double T)const{auto X=Times(),Y=Series(K);if(X.Num()!=Y.Num()||X.Num()<2)return 0;for(int32 I=1;I<X.Num();++I)if(T<=X[I])return FMath::Lerp(Y[I-1],Y[I],FMath::Clamp((T-X[I-1])/(X[I]-X[I-1]),0.,1.));return Y.Last();}
void AFusionController::RefreshLayers(){if(Rig)Rig->Refresh(Layers,bCut);}
void AFusionController::ZoomIn(){if(bLab){LabDistance=FMath::Max(Lab&&Lab->bSourceContext?1800.f:250.f,LabDistance*.92f);return;}if(bResearch||bEvidence||bNeutron)return;Distance=FMath::Max(2100.f,Distance*0.92f);}
void AFusionController::ZoomOut(){if(bLab){LabDistance=FMath::Min(Lab&&Lab->bSourceContext?12000.f:1800.f,LabDistance*1.08f);return;}if(bResearch||bEvidence||bNeutron)return;Distance=FMath::Min(15000.f,Distance*1.08f);}
void AFusionController::SelectConfiguration(const FString& Id){
 if(bBusy)return;const TArray<TSharedPtr<FJsonValue>>* A=nullptr;if(!Catalog||!Catalog->TryGetArrayField(TEXT("configurations"),A))return;
 for(auto V:*A)if(Str(V->AsObject(),TEXT("id"))==Id){Config=V->AsObject();ConfigurationId=Id;break;}
 bModelOK=Rig&&Rig->LoadModel(ConfigurationId);RefreshLayers();Selected=TEXT("solenoid");
 if(!bModelOK)JobText=TEXT("Model failed its format/dimension check. No scientific result changed.");
}
void AFusionController::BeginPlay(){
 Super::BeginPlay();bShowMouseCursor=true;SetInputMode(FInputModeGameAndUI().SetHideCursorDuringCapture(false));
 FString S;FFileHelper::LoadFileToString(S,*(FPaths::ProjectContentDir()/TEXT("WorkbenchData/catalog.json")));FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(S),Catalog);
 for(auto K:{TEXT("plasma"),TEXT("solenoid"),TEXT("first_wall"),TEXT("blanket"),TEXT("shield"),TEXT("vessel"),TEXT("coils")})Layers.Add(K,true);
 Rig=GetWorld()->SpawnActor<AFusionRig>();SetViewTarget(Rig);SelectConfiguration(TEXT("r838"));
 auto Light=GetWorld()->SpawnActor<ADirectionalLight>(FVector(0,0,2000),FRotator(-40,-30,0));Light->GetLightComponent()->SetIntensity(5.f);
 LoadResearchLibrary();LoadNeutronics();Lab=GetWorld()->SpawnActor<AFusionTransportLab>();Lab->Load();Lab->SetActive(false);MakeUI();Poll();bSolverSmoke=FParse::Param(FCommandLine::Get(),TEXT("WorkbenchSolverSmokeTest"));bSelfTest=FParse::Param(FCommandLine::Get(),TEXT("WorkbenchSelfTest"));bScreenshot=FParse::Param(FCommandLine::Get(),TEXT("WorkbenchScreenshot"));
}
void AFusionController::SetupInputComponent(){Super::SetupInputComponent();InputComponent->BindKey(EKeys::MouseScrollUp,IE_Pressed,this,&AFusionController::ZoomIn);InputComponent->BindKey(EKeys::MouseScrollDown,IE_Pressed,this,&AFusionController::ZoomOut);}
void AFusionController::PlayerTick(float D){
 Super::PlayerTick(D);Elapsed+=D;
 if(bSolverSmoke&&!bSmokeStarted&&Elapsed>4&&bOnline&&bSolver){bSmokeStarted=true;StartSolver();}
 if(bSolverSmoke&&!bSmokeDone&&Elapsed>630){CancelSolver();FinishSmoke(nullptr);}
 if(bSmokeDone&&Elapsed>SmokeDoneAt+4){FPlatformMisc::RequestExit(false);}
PollTime+=D;if(PollTime>1.5f){PollTime=0;Poll();}
 if(!bLab&&!bResearch&&!bNeutron&&IsInputKeyDown(EKeys::RightMouseButton)){float X=0,Y=0;GetInputMouseDelta(X,Y);Yaw-=X*.3f;Pitch=FMath::Clamp(Pitch+Y*.3f,-5.f,75.f);}
 if(WasInputKeyJustPressed(EKeys::LeftMouseButton)&&!bLab&&!bEvidence&&!bResearch&&!bNeutron){float X,Y;int32 SX,SY;GetViewportSize(SX,SY);if(GetMousePosition(X,Y)&&Y>90&&Y<SY-220&&(bPresenting||(X>250&&X<SX-325))){FHitResult Hit;if(GetHitResultUnderCursor(ECC_Visibility,true,Hit)){auto G=Rig->GroupFor(Hit.GetComponent());if(!G.IsEmpty())Selected=G;}}}
 if(bLab&&Lab){
  if(IsInputKeyDown(EKeys::RightMouseButton)){float X=0,Y=0;GetInputMouseDelta(X,Y);LabYaw-=X*.3f;LabPitch=FMath::Clamp(LabPitch+Y*.3f,-65.f,80.f);}
  Lab->Animate(D);if(WasInputKeyJustPressed(EKeys::LeftMouseButton)){float X=0,Y=0;int32 SX,SY;GetViewportSize(SX,SY);if(GetMousePosition(X,Y)&&X>290&&X<SX-310&&Y>130&&Y<SY-185){FHitResult Hit;if(GetHitResultUnderCursor(ECC_Visibility,true,Hit)&&Hit.GetComponent()==Lab->Field)Lab->InspectWorld(Hit.ImpactPoint);}}
 }
 if(Rig){if(bLab)Rig->Orbit(LabYaw,LabPitch,LabDistance);else Rig->Orbit(Yaw,Pitch,Distance);}if(bPlaying)Playback=FMath::Fmod(Playback+D/50.f,1.f);
 if(bSelfTest&&!bSelfTestDone&&Elapsed>4){bSelfTestDone=true;RunSelfTest();}
 if(bScreenshot&&!bScreenshotDone&&Elapsed>8){bScreenshotDone=true;FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots/Workbench.png"),true,false);}
 if(bSelfTest&&Elapsed>12)FPlatformMisc::RequestExit(false);
}
FString AFusionController::PhaseText()const{auto X=Times();double T=X.Num()?Playback*X.Last():0;FString P=TEXT("Recorded profile");const TArray<TSharedPtr<FJsonValue>>* A=nullptr;auto O=Obj(Config,TEXT("pulse"));if(O&&O->TryGetArrayField(TEXT("phase_names"),A))for(int32 I=1;I<X.Num();++I)if(T<=X[I]){P=(*A)[I-1]->AsString();break;}return FString::Printf(TEXT("RECORDED SIMULATION  |  %s  |  %.0f s  |  Net %.1f MW"),*P,T,Sample(TEXT("net_MW"),T));}
FString AFusionController::Inspector()const{
 FString S;const TArray<TSharedPtr<FJsonValue>>* A=nullptr;if(Config&&Config->TryGetArrayField(TEXT("components"),A))for(auto V:*A){auto O=V->AsObject();if(Str(O,TEXT("id"))==Selected)S=Str(O,TEXT("title"))+TEXT("\n\n")+Str(O,TEXT("detail"));}
 auto G=Obj(Config,TEXT("geometry"));
 if(Selected==TEXT("solenoid"))S+=FString::Printf(TEXT("\n\nInner radius: %.3f m\nRadial width: %.3f m\nHeight: %.3f m\n\nModel hoop stress: %.2f MPa\nModel life: %.0f cycles\nRequired: %.0f cycles\nMaterial margin: NOT QUALIFIED"),Num(G,TEXT("solenoid_inner_radius_m")),Num(G,TEXT("solenoid_radial_width_m")),Num(G,TEXT("solenoid_height_m")),Metric(TEXT("solenoid_hoop_MPa")),Metric(TEXT("fatigue_cycles")),Metric(TEXT("required_fatigue_cycles")));
 else if(Selected==TEXT("plasma"))S+=FString::Printf(TEXT("\n\nMajor radius: %.3f m\nMinor radius: %.3f m\nElongation: %.2f\nTriangularity: %.2f\nInternal multiplier: %.3f\nNot automatically global H98."),Num(G,TEXT("major_radius_m")),Num(G,TEXT("minor_radius_m")),Num(G,TEXT("elongation")),Num(G,TEXT("triangularity")),Metric(TEXT("internal_confinement_multiplier")));
 else {FString Prefix=Selected==TEXT("first_wall")?TEXT("first_wall"):Selected;S+=FString::Printf(TEXT("\n\nInboard radial thickness: %.3f m\nOutboard radial thickness: %.3f m\nScalar inputs are NOT spatial simulation fields."),Num(G,Prefix+TEXT("_inboard_m")),Num(G,Prefix+TEXT("_outboard_m")));}
 S+=TEXT("\n\nSource artifact SHA-256:\n")+Str(Obj(Config,TEXT("provenance")),TEXT("artifact_sha256"));return S;
}
FString AFusionController::Progress()const{FString S=TEXT("CURRENT RESEARCH EVIDENCE\n\nNo claimed percentage of fusion solved. No operating fusion power plant validated.\n\n");const TArray<TSharedPtr<FJsonValue>>* A=nullptr;if(Catalog&&Catalog->TryGetArrayField(TEXT("tracks"),A))for(auto V:*A){auto O=V->AsObject();S+=Str(O,TEXT("title"))+TEXT("\n")+Str(O,TEXT("model_status"))+TEXT(" | ")+Str(O,TEXT("validation_status"))+TEXT("\n")+Str(O,TEXT("summary"))+TEXT("\n\n");}return S;}
class SPulseGraph : public SLeafWidget {
public:SLATE_BEGIN_ARGS(SPulseGraph){} SLATE_ARGUMENT(AFusionController*,Controller) SLATE_END_ARGS()
 TWeakObjectPtr<AFusionController> C;
 void Construct(const FArguments& A){C=A._Controller;}
 virtual FVector2D ComputeDesiredSize(float)const override{return FVector2D(600,90);}
 virtual int32 OnPaint(const FPaintArgs& Args,const FGeometry& G,const FSlateRect& Clip,FSlateWindowElementList& Out,int32 Layer,const FWidgetStyle& Style,bool Enabled)const override{
  if(!C.IsValid())return Layer;auto X=C->Times();if(X.Num()<2)return Layer;
  FVector2D Size=G.GetLocalSize();auto Point=[&](double T,double V){return FVector2D(8+(Size.X-16)*T/X.Last(),Size.Y-8-(V+180)/1550*(Size.Y-16));};
  TArray<FVector2D> Zero={Point(0,0),Point(X.Last(),0)};FSlateDrawElement::MakeLines(Out,Layer,G.ToPaintGeometry(),Zero,ESlateDrawEffect::None,Muted*.5f,true,1);
  int32 J=0;for(auto Key:{TEXT("gross_MW"),TEXT("net_MW")}){auto Y=C->Series(Key);if(Y.Num()!=X.Num())continue;TArray<FVector2D> P;for(int32 I=0;I<X.Num();++I)P.Add(Point(X[I],Y[I]));FSlateDrawElement::MakeLines(Out,Layer+1,G.ToPaintGeometry(),P,ESlateDrawEffect::None,J++?Teal:Gold,true,2);}
  float T=C->Playback*X.Last();TArray<FVector2D> Cursor={Point(T,-180),Point(T,1370)};FSlateDrawElement::MakeLines(Out,Layer+2,G.ToPaintGeometry(),Cursor,ESlateDrawEffect::None,FLinearColor::White,true,1);return Layer+2;
 }
};
void AFusionController::MakeUI(){
 auto Button=[](const FString& Name,TFunction<void()> Fn){return SNew(SButton).ButtonColorAndOpacity(Panel).ContentPadding(FMargin(10,8)).OnClicked_Lambda([Fn](){Fn();return FReply::Handled();})[Text(Name,13)];};
 auto Left=SNew(SVerticalBox);Left->AddSlot().AutoHeight().Padding(0,0,0,15)[Text(TEXT("CONFIGURATIONS"),11,Muted)];
 Left->AddSlot().AutoHeight().Padding(0,3)[Button(TEXT("Reference | 8.38 m"),[this](){SelectConfiguration(TEXT("r838"));})];
 Left->AddSlot().AutoHeight().Padding(0,3)[Button(TEXT("Comparator | 9.00 m"),[this](){SelectConfiguration(TEXT("r900"));})];
 Left->AddSlot().AutoHeight().Padding(0,15)[Text(TEXT("One geometry. Its evidence.\nNo mixed subsystem gains."),12,Muted)];
 Left->AddSlot().AutoHeight().Padding(0,10)[Text(TEXT("MODEL LAYERS"),11,Muted)];
 TArray<FString> Keys={TEXT("plasma"),TEXT("solenoid"),TEXT("first_wall"),TEXT("blanket"),TEXT("shield"),TEXT("vessel"),TEXT("coils")};
 TArray<FString> Names={TEXT("Plasma"),TEXT("Central solenoid"),TEXT("First wall"),TEXT("Breeding blanket"),TEXT("Shield"),TEXT("Vacuum vessel"),TEXT("Toroidal coils")};
 for(int32 I=0;I<Keys.Num();++I){FString K=Keys[I];Left->AddSlot().AutoHeight().Padding(0,4)[SNew(SCheckBox).IsChecked_Lambda([this,K](){return Layers.FindRef(K)?ECheckBoxState::Checked:ECheckBoxState::Unchecked;}).OnCheckStateChanged_Lambda([this,K](ECheckBoxState State){Layers[K]=State==ECheckBoxState::Checked;Selected=K;RefreshLayers();})[Text(Names[I],13)]];}
 Left->AddSlot().AutoHeight().Padding(0,16)[Button(TEXT("Toggle cutaway"),[this](){bCut=!bCut;RefreshLayers();})];
 Left->AddSlot().AutoHeight()[Button(TEXT("Reset camera"),[this](){Yaw=45;Pitch=24;Distance=7400;})];
 Left->AddSlot().AutoHeight().Padding(0,18)[Text(TEXT("DISPLAY ENVELOPES\nNot engineering CAD.\n\nRight-drag to orbit\nWheel to zoom\nClick a visible component"),12,Muted)];
 auto Right=SNew(SVerticalBox);Right->AddSlot().AutoHeight().Padding(0,0,0,12)[Text(TEXT("COMPONENT / EVIDENCE"),11,Muted)];
 Right->AddSlot().FillHeight(1)[SNew(SScrollBox)+SScrollBox::Slot()[SNew(STextBlock).Text_Lambda([this](){return Txt(Inspector());}).Font(FCoreStyle::GetDefaultFontStyle("Regular",13)).WrappingPolicy(ETextWrappingPolicy::AllowPerCharacterWrapping).AutoWrapText(true)]];
 Right->AddSlot().AutoHeight().Padding(0,10)[Text(TEXT("LOCAL EXPERIMENTS"),11,Teal)];
 Right->AddSlot().AutoHeight().Padding(0,3)[Button(TEXT("Verify recorded electricity"),[this](){VerifyRecorded();})];
 Right->AddSlot().AutoHeight().Padding(0,3)[SNew(SButton).IsEnabled_Lambda([this](){return bOnline&&bSolver&&!bBusy;}).ContentPadding(FMargin(10,8)).OnClicked_Lambda([this](){StartSolver();return FReply::Handled();})[Text(TEXT("Run full-system test"),13)]];
 Right->AddSlot().AutoHeight().Padding(0,3)[SNew(SButton).IsEnabled_Lambda([this](){return bOnline&&bBusy;}).OnClicked_Lambda([this](){CancelSolver();return FReply::Handled();})[Text(TEXT("Cancel my current run"),12)]];
 Right->AddSlot().AutoHeight().Padding(0,12)[SNew(STextBlock).Text_Lambda([this](){return Txt(JobText);}).Font(FCoreStyle::GetDefaultFontStyle("Regular",12)).ColorAndOpacity(Muted).AutoWrapText(true)];
 Right->AddSlot().AutoHeight()[Text(TEXT("Recorded replay is not live plasma.\nResults never auto-promote a design."),11,Gold)];
 auto Center=SNew(SVerticalBox);Center->AddSlot().AutoHeight().Padding(20,8)[SNew(STextBlock).Text_Lambda([this](){return Txt(Title());}).Font(FCoreStyle::GetDefaultFontStyle("Bold",23))];
 Center->AddSlot().AutoHeight().Padding(20,0)[Text(TEXT("CONCEPTUAL MODEL | PHYSICAL VALIDATION OPEN"),11,Gold)];
 Center->AddSlot().FillHeight(1)[SNew(SBox)];
 Center->AddSlot().AutoHeight().Padding(20,0)[Text(TEXT("Glow is illustrative. No spatial temperature, stress or neutron field is claimed."),11,Muted)];
 Center->AddSlot().AutoHeight().Padding(20,10)[SNew(STextBlock).Text_Lambda([this](){return Txt(FString::Printf(TEXT("%.2f m major radius     %.1f MW generating net     %.2f MW conditional average"),Num(Obj(Config,TEXT("geometry")),TEXT("major_radius_m")),Metric(TEXT("flat_top_net_MW")),Metric(TEXT("conditional_average_net_MW"))));}).Font(FCoreStyle::GetDefaultFontStyle("Bold",15)).ColorAndOpacity(Teal).AutoWrapText(true)];
 Center->AddSlot().AutoHeight().Padding(20,0)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Ink)[SNew(SBox).HeightOverride(95)[SNew(SPulseGraph).Controller(this)]]];
 Center->AddSlot().AutoHeight().Padding(20,8)[SNew(SHorizontalBox)+SHorizontalBox::Slot().AutoWidth()[Button(TEXT("Play / pause"),[this](){bPlaying=!bPlaying;})]+SHorizontalBox::Slot().FillWidth(1).Padding(12,0)[SNew(SSlider).Value_Lambda([this](){return Playback;}).OnValueChanged_Lambda([this](float V){Playback=V;})]];
 Center->AddSlot().AutoHeight().Padding(20,0,20,16)[SNew(STextBlock).Text_Lambda([this](){return Txt(PhaseText());}).Font(FCoreStyle::GetDefaultFontStyle("Regular",11)).ColorAndOpacity(Muted)];
 auto Header=SNew(SHorizontalBox);Header->AddSlot().FillWidth(1)[Text(TEXT("FUSION WORKBENCH\nOpen research for humanity"),18,Teal)];
 Header->AddSlot().AutoWidth().Padding(4,0)[Button(TEXT("Device"),[this](){bEvidence=false;bResearch=false;bNeutron=false;})];
 Header->AddSlot().AutoWidth().Padding(4,0)[Button(TEXT("Evidence & progress"),[this](){bNeutron=false;bResearch=false;bEvidence=!bEvidence;})];
 Header->AddSlot().AutoWidth().Padding(4,0)[Button(TEXT("Research library"),[this](){bNeutron=false;bResearch=!bResearch;UpdateResearchRows();})];
 Header->AddSlot().AutoWidth().Padding(4,0)[Button(TEXT("3D transport"),[this](){OpenTransportLab(true);})];
 Header->AddSlot().AutoWidth().Padding(4,0)[Button(TEXT("Neutron study"),[this](){bNeutron=!bNeutron;bResearch=false;bEvidence=false;})];
 Header->AddSlot().AutoWidth().Padding(4,0)[Button(TEXT("Export proposal"),[this](){ExportProposal();})];
 Header->AddSlot().AutoWidth().Padding(4,0)[Button(TEXT("Presentation"),[this](){bNeutron=false;bResearch=false;bPresenting=!bPresenting;})];
 Header->AddSlot().AutoWidth().Padding(4,0)[Button(TEXT("Quit"),[](){FPlatformMisc::RequestExit(false);})];
 auto CenterOverlay=SNew(SOverlay)+SOverlay::Slot()[Center]+SOverlay::Slot().Padding(16)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Ink).Visibility_Lambda([this](){return bEvidence?EVisibility::Visible:EVisibility::Collapsed;}).Padding(20)[SNew(SScrollBox)+SScrollBox::Slot()[SNew(STextBlock).Text_Lambda([this](){return Txt(Progress());}).Font(FCoreStyle::GetDefaultFontStyle("Regular",15)).AutoWrapText(true)]]];
 RootWidget=SNew(SVerticalBox)
 +SVerticalBox::Slot().AutoHeight()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Ink).Padding(FMargin(20,12))[Header]]
 +SVerticalBox::Slot().FillHeight(1)[SNew(SHorizontalBox)
  +SHorizontalBox::Slot().AutoWidth()[SNew(SBox).WidthOverride(240).Visibility_Lambda([this](){return bPresenting?EVisibility::Collapsed:EVisibility::Visible;})[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).Padding(18).BorderBackgroundColor(Ink)[Left]]]
  +SHorizontalBox::Slot().FillWidth(1)[CenterOverlay]
  +SHorizontalBox::Slot().AutoWidth()[SNew(SBox).WidthOverride(310).Visibility_Lambda([this](){return bPresenting?EVisibility::Collapsed:EVisibility::Visible;})[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).Padding(18).BorderBackgroundColor(Ink)[Right]]]]
 +SVerticalBox::Slot().AutoHeight()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Panel).Padding(FMargin(15,5))[SNew(STextBlock).Text_Lambda([this](){return Txt(TEXT("Fusion Workbench contributors  |  ")+Connection+TEXT("  |  Original work MIT; Unreal Engine separately licensed"));}).Font(FCoreStyle::GetDefaultFontStyle("Regular",10)).ColorAndOpacity(Muted)]];
 auto ResearchPane=MakeResearchUI();
 RootWidget=SNew(SOverlay)+SOverlay::Slot()[RootWidget.ToSharedRef()]+SOverlay::Slot().Padding(FMargin(12,82,12,26))[SNew(SBox).Visibility_Lambda([this](){return bResearch?EVisibility::Visible:EVisibility::Collapsed;})[ResearchPane]];
 auto NeutronPane=MakeNeutronicsUI();
 RootWidget=SNew(SOverlay)+SOverlay::Slot()[RootWidget.ToSharedRef()]+SOverlay::Slot().Padding(FMargin(12,82,12,26))[SNew(SBox).Visibility_Lambda([this](){return bNeutron?EVisibility::Visible:EVisibility::Collapsed;})[NeutronPane]];
 auto LabPane=MakeTransportLabUI();RootWidget=SNew(SOverlay)+SOverlay::Slot()[SNew(SBox).Visibility_Lambda([this](){return bLab?EVisibility::Collapsed:EVisibility::Visible;})[RootWidget.ToSharedRef()]]+SOverlay::Slot()[SNew(SBox).Visibility_Lambda([this](){return bLab?EVisibility::Visible:EVisibility::Collapsed;})[LabPane]];
 if(GEngine&&GEngine->GameViewport)GEngine->GameViewport->AddViewportWidgetContent(RootWidget.ToSharedRef(),10);
}
void AFusionController::Request(const FString& Route,const FString& Verb,const FString& Body,TFunction<void(TSharedPtr<FJsonObject>)> Done){
 auto R=FHttpModule::Get().CreateRequest();R->SetURL(TEXT("http://127.0.0.1:18765")+Route);R->SetVerb(Verb);R->SetTimeout(5);R->SetHeader(TEXT("Content-Type"),TEXT("application/json"));R->SetHeader(TEXT("Origin"),TEXT("http://127.0.0.1:18765"));R->SetHeader(TEXT("X-Workbench-Request"),TEXT("local-ui-v1"));if(!Body.IsEmpty())R->SetContentAsString(Body);
 TWeakObjectPtr<AFusionController> Weak(this);R->OnProcessRequestComplete().BindLambda([Weak,Done](FHttpRequestPtr Req,FHttpResponsePtr Response,bool Good){if(!Weak.IsValid())return;TSharedPtr<FJsonObject> O;if(Good&&Response.IsValid()&&Response->GetResponseCode()>=200&&Response->GetResponseCode()<300)FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Response->GetContentAsString()),O);Done(O);});R->ProcessRequest();
}
void AFusionController::Poll(){Request(TEXT("/api/status"),TEXT("GET"),TEXT(""),[this](TSharedPtr<FJsonObject> O){
 bOnline=O.IsValid()&&Str(O,TEXT("mode"))==TEXT("local")&&Str(O,TEXT("worker"))==TEXT("available");bSolver=false;if(O)O->TryGetBoolField(TEXT("full_solver_configured"),bSolver);
 Connection=bOnline?TEXT("Local worker connected; no public host"):TEXT("Offline viewer; local worker unavailable");
 if(bSubmitting)return;const TArray<TSharedPtr<FJsonValue>>* A=nullptr;if(O&&O->TryGetArrayField(TEXT("jobs"),A))for(auto V:*A){auto J=V->AsObject();if(Str(J,TEXT("id"))!=JobId)continue;FString State=Str(J,TEXT("state"));bBusy=State==TEXT("queued")||State==TEXT("running")||State==TEXT("cancelling");JobText=State.ToUpper()+TEXT(" | FULL SOLVER | ")+Str(J,TEXT("configuration_id"))+TEXT("\n")+Str(J,TEXT("message"));auto Result=Obj(J,TEXT("result"));if(bSolverSmoke&&bSmokeStarted&&!bSmokeDone&&!bBusy)FinishSmoke(Result);if(Result){auto M=Obj(Result,TEXT("metrics"));JobText+=M?FString::Printf(TEXT("\nFresh result: %.6f MW conditional average\nNo automatic reference update."),Num(M,TEXT("conditional_average_net_MW"))):TEXT("\nNo accepted numerical result.");}}
 });}
void AFusionController::StartSolver(){if(!bOnline||!bSolver||bBusy)return;bBusy=true;bSubmitting=true;JobId.Empty();JobText=TEXT("Submitting approved local calculation...");Request(TEXT("/api/jobs"),TEXT("POST"),TEXT("{\"kind\":\"rerun_process\",\"configuration_id\":\"")+ConfigurationId+TEXT("\"}"),[this](TSharedPtr<FJsonObject> O){bSubmitting=false;if(O){JobId=Str(O,TEXT("id"));JobText=TEXT("QUEUED | ")+ConfigurationId;Poll();}else{bBusy=false;JobText=TEXT("Submission rejected or worker unavailable. No input was changed.");}});}
void AFusionController::CancelSolver(){if(!bBusy||JobId.IsEmpty())return;Request(TEXT("/api/jobs/")+JobId+TEXT("/cancel"),TEXT("POST"),TEXT("{}"),[this](TSharedPtr<FJsonObject>){Poll();});}
void AFusionController::VerifyRecorded(){if(bBusy)return;auto X=Times(),Y=Series(TEXT("net_MW"));double Energy=0,Error=0;bool OK=X.Num()==7&&Y.Num()==7;
 for(int32 I=1;OK&&I<X.Num();++I){OK=X[I]>X[I-1]&&FMath::IsFinite(Y[I]);Energy+=.5*(Y[I]+Y[I-1])*(X[I]-X[I-1])/3.6;}
 if(OK)for(int32 I=0;I<7;++I){double Balance=0;const TSharedPtr<FJsonObject> O=Obj(Obj(Config,TEXT("pulse")),TEXT("series"));for(auto& KV:O->Values)if(KV.Key!=TEXT("net_MW")){auto Z=Series(KV.Key);if(Z.Num()==7)Balance+=Z[I];else OK=false;}Error=FMath::Max(Error,FMath::Abs(Balance-Y[I]));}
 const double Diff=FMath::Abs(Energy-Metric(TEXT("pulse_energy_kWh")));OK=OK&&Diff<.00001&&Error<.0000001;
 JobText=FString::Printf(TEXT("%s | RECORDED OUTPUT CHECK | %s\nPulse energy difference %.8g kWh\nElectrical balance difference %.8g MW\nNumerical verification only. Physical validation unchanged."),OK?TEXT("PASSED"):TEXT("FAILED"),*ConfigurationId,Diff,Error);
}
void AFusionController::ExportProposal(){auto O=MakeShared<FJsonObject>();O->SetStringField(TEXT("schema"),TEXT("fusion.contribution-brief.v1"));O->SetStringField(TEXT("configuration_id"),ConfigurationId);O->SetStringField(TEXT("source_artifact_sha256"),Str(Obj(Config,TEXT("provenance")),TEXT("artifact_sha256")));O->SetStringField(TEXT("question"),TEXT("Describe the unresolved question and closest published result."));O->SetStringField(TEXT("proposed_change"),TEXT("State input changes, units, model assumptions and licensing."));O->SetStringField(TEXT("falsification_test"),TEXT("What result would reject the proposal?"));O->SetBoolField(TEXT("automatically_executed"),false);FString Path=FPaths::ProjectSavedDir()/TEXT("Contributions/proposal.json");JobText=SaveJson(Path,O)?TEXT("Proposal template saved under Saved/Contributions. No private identifiers exported. Submit through the public repository once configured."):TEXT("Could not save proposal template.");}
void AFusionController::RunSelfTest(){
 auto O=MakeShared<FJsonObject>();bool Passed=true;TArray<TSharedPtr<FJsonValue>> Cases;
 for(auto Id:{TEXT("r838"),TEXT("r900")}){SelectConfiguration(Id);auto C=MakeShared<FJsonObject>();VerifyRecorded();bool OK=bModelOK&&JobText.StartsWith(TEXT("PASSED"));
  auto G=Obj(Config,TEXT("geometry"));const double Height=Num(G,TEXT("solenoid_height_m"))*100;OK=OK&&FMath::Abs(Rig->ModelSize.Z-Height)<.02;
  auto T=Times();double Before=Sample(TEXT("net_MW"),T[0]);double During=Sample(TEXT("net_MW"),.5*(T[3]+T[4]));OK=OK&&Before<0&&FMath::Abs(During-400)<.01;
  Layers[TEXT("plasma")]=false;RefreshLayers();for(int32 I=0;I<Rig->Parts.Num();++I)if(Rig->Groups[I]==TEXT("plasma")&&Rig->Parts[I]->IsVisible())OK=false;Layers[TEXT("plasma")]=true;RefreshLayers();
  C->SetStringField(TEXT("configuration_id"),Id);C->SetBoolField(TEXT("passed"),OK);C->SetNumberField(TEXT("mesh_components"),Rig->Parts.Num());C->SetNumberField(TEXT("height_error_cm"),FMath::Abs(Rig->ModelSize.Z-Height));Cases.Add(MakeShared<FJsonValueObject>(C));Passed&=OK;
 }
 SelectConfiguration(TEXT("r838"));VerifyRecorded();O->SetStringField(TEXT("schema"),TEXT("fusion.native-runtime-test.v1"));O->SetArrayField(TEXT("configurations"),Cases);O->SetBoolField(TEXT("passed"),Passed);O->SetBoolField(TEXT("physical_validation"),false);O->SetBoolField(TEXT("native_unreal_runtime"),true);O->SetBoolField(TEXT("public_host_configured"),false);
 SaveJson(FPaths::ProjectSavedDir()/TEXT("Automation/native-selftest.json"),O);
 if(FParse::Param(FCommandLine::Get(),TEXT("WorkbenchLibraryTest")))TestResearchLibrary();
 if(FParse::Param(FCommandLine::Get(),TEXT("WorkbenchNeutronicsTest")))TestNeutronics();
 if(FParse::Param(FCommandLine::Get(),TEXT("WorkbenchTransportLabTest")))TestTransportLab();
}

void AFusionController::FinishSmoke(TSharedPtr<FJsonObject> Result){
 bSmokeDone=true;SmokeDoneAt=Elapsed;auto O=MakeShared<FJsonObject>();bool Passed=false;if(Result)Result->TryGetBoolField(TEXT("passed"),Passed);
 O->SetStringField(TEXT("schema"),TEXT("fusion.native-solver-smoke.v1"));O->SetBoolField(TEXT("passed"),Passed);O->SetBoolField(TEXT("actual_local_solver_requested"),bSmokeStarted);O->SetBoolField(TEXT("physical_validation"),false);O->SetBoolField(TEXT("reference_auto_updated"),false);if(Result)O->SetObjectField(TEXT("safe_solver_result"),Result);
 SaveJson(FPaths::ProjectSavedDir()/TEXT("Automation/native-solver-smoke.json"),O);FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots/WorkbenchSolver.png"),true,false);
}
