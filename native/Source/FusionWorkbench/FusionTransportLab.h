// Original MIT. Visualization of bounded recorded OpenMC results, not a new solver.
#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Dom/JsonObject.h"
#include "FusionTransportLab.generated.h"
class UProceduralMeshComponent;class UMaterialInterface;
struct FLabTrack{TArray<FVector> P;TArray<double> Time,Energy;bool Photon=false;int32 Primary=0;};
struct FLabSourceSite{uint64 Id=0;uint32 Bank=0,Index=0;double Weight=0,Probability=0;FVector Birth,Target,Local,Direction;};
UCLASS() class AFusionTransportLab:public AActor{
 GENERATED_BODY()
public:
 AFusionTransportLab();
 UPROPERTY() TArray<UProceduralMeshComponent*> Hardware;
 UPROPERTY() UProceduralMeshComponent* Particles=nullptr;
 UPROPERTY() UProceduralMeshComponent* Trails=nullptr;
 UPROPERTY() UProceduralMeshComponent* Field=nullptr;
 UPROPERTY() UMaterialInterface* Metal=nullptr;
 UPROPERTY() UMaterialInterface* DataMaterial=nullptr;
 UPROPERTY() UMaterialInterface* Ghost=nullptr;
 TSharedPtr<FJsonObject> Packet,Case;TArray<TSharedPtr<FJsonObject>> Cases;TArray<FLabTrack> Tracks;
 FVector Size=FVector(100,133,196);double MaxTime=1e-6,PhysicalTime=0,HeatScale=1;
 int32 CaseIndex=0,VisibleParticles=0,SliceIndex=8;bool bPlayback=true,bShowTrails=true,bShowField=true,bCutHardware=true;
 float Phase=.5f;bool Ready=false;FString Error,FieldInspection;
 UPROPERTY() UProceduralMeshComponent* SourceWire=nullptr;
 UPROPERTY() UProceduralMeshComponent* SourceBody=nullptr;
 bool bSourceContext=false;
 void BuildSourceContext();void SetSourceContext(bool Active);void AnimateSourceContext(float Dt);
 TArray<FLabSourceSite> SourceSites;TArray<int32> SourceDrawIndices;
 bool LoadSourceSites();
 bool Load();void SelectCase(int32 Index);void BuildHardware();void BuildTrails();void BuildField();void Animate(float Dt);
 FVector WorldPoint(FVector P)const;void SetActive(bool Active);void SetSlice(float Value);void InspectField(int32 Face);void InspectWorld(FVector Point);
 FString Status()const;FString TimeLabel()const;bool Validate()const;
 UProceduralMeshComponent* MakePart(const TCHAR* Name,UMaterialInterface* Material);
};
