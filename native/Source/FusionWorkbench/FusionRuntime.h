// Original application code: MIT. Unreal Engine remains separately licensed.
#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/GameModeBase.h"
#include "Dom/JsonObject.h"
#include "FusionRuntime.generated.h"
class UProceduralMeshComponent;
class UCameraComponent;
class SWidget;
UCLASS() class AFusionRig : public AActor {
 GENERATED_BODY()
public:
 AFusionRig();
 UPROPERTY() UCameraComponent* Camera;
 UPROPERTY() TArray<UProceduralMeshComponent*> Parts;
 TArray<FString> Groups; TArray<bool> Cuts;
 bool LoadModel(const FString& Id); void Refresh(const TMap<FString,bool>& Layers,bool Cut);
 void Orbit(float Yaw,float Pitch,float Distance); FString GroupFor(UPrimitiveComponent* Component) const;
 FVector ModelSize=FVector::ZeroVector;
};
UCLASS() class AFusionController : public APlayerController {
 GENERATED_BODY()
public:
 virtual void BeginPlay() override; virtual void PlayerTick(float Delta) override;
 virtual void SetupInputComponent() override;
 UPROPERTY() AFusionRig* Rig=nullptr;
 TSharedPtr<FJsonObject> Catalog,Config;
 TSharedPtr<SWidget> RootWidget;
 TMap<FString,bool> Layers;
 FString ConfigurationId=TEXT("r838"),Selected=TEXT("solenoid"),Connection=TEXT("Checking local worker"),JobText=TEXT("No active experiment"),JobId;
 bool bCut=true,bPlaying=false,bPresenting=false,bEvidence=false,bOnline=false,bSolver=false,bBusy=false;
 float Playback=0.77f,Yaw=45,Pitch=24,Distance=7400,PollTime=0,Elapsed=0;
 bool bSelfTest=false,bSelfTestDone=false,bScreenshot=false,bScreenshotDone=false;
 bool bModelOK=false,bSubmitting=false,bSolverSmoke=false,bSmokeStarted=false,bSmokeDone=false; float SmokeDoneAt=0;
 bool bResearch=false,bResearchCurrentOnly=false;
 FString ResearchQuery,ResearchUpdated;
 int32 ResearchMatchesCount=0;
 TArray<TSharedPtr<FJsonObject>> ResearchRecords;
 TSharedPtr<FJsonObject> SelectedResearch;
 TSharedPtr<class SScrollBox> ResearchList;
 TSharedPtr<class SMultiLineEditableTextBox> ResearchReader;
 bool bNeutron=false; int32 NeutronLayout=0; TSharedPtr<FJsonObject> NeutronData; TArray<TSharedPtr<FJsonObject>> NeutronCases;
 void LoadNeutronics(); FString NeutronMetrics()const; TSharedRef<SWidget> MakeNeutronicsUI(); void TestNeutronics();
 void LoadResearchLibrary(); void UpdateResearchRows(); void TestResearchLibrary();
 bool ResearchMatches(TSharedPtr<FJsonObject> E)const;
 FString ResearchHeader()const;
 TSharedRef<SWidget> MakeResearchUI();
 UPROPERTY() class AFusionTransportLab* Lab=nullptr;
 bool bLab=false;float LabYaw=-145,LabPitch=22,LabDistance=620;
 void OpenTransportLab(bool Active);TSharedRef<SWidget> MakeTransportLabUI();void TestTransportLab();
 void FinishSmoke(TSharedPtr<FJsonObject> Result);
 void SelectConfiguration(const FString& Id); void MakeUI(); void RefreshLayers();
 void ZoomIn(); void ZoomOut(); void Poll(); void StartSolver(); void CancelSolver();
 void VerifyRecorded(); void ExportProposal(); void RunSelfTest();
 FString Inspector() const; FString Progress() const; FString PhaseText() const;
 FString Title() const; double Metric(const FString& Key) const;
 TArray<double> Times() const; TArray<double> Series(const FString& Key) const;
 double Sample(const FString& Key,double T) const;
 void Request(const FString& Route,const FString& Verb,const FString& Body,TFunction<void(TSharedPtr<FJsonObject>)> Done);
};
UCLASS() class AFusionGameMode : public AGameModeBase {
 GENERATED_BODY()
public: AFusionGameMode();
};
