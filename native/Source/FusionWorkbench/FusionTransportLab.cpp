// Original MIT. All geometry in this view is linked to the local transport input.
#include "FusionTransportLab.h"
#include "ProceduralMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/MemoryReader.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
namespace {
FString S(TSharedPtr<FJsonObject> O,const TCHAR* K){FString V;if(O)O->TryGetStringField(K,V);return V;}
double N(TSharedPtr<FJsonObject> O,const TCHAR* K){double V=0;if(O)O->TryGetNumberField(K,V);return V;}
TArray<double> A(TSharedPtr<FJsonObject> O,const TCHAR* K){TArray<double> V;const TArray<TSharedPtr<FJsonValue>>* X=nullptr;if(O&&O->TryGetArrayField(K,X))for(auto Q:*X)V.Add(Q->AsNumber());return V;}
struct FBuffer{TArray<FVector> V,Normal;TArray<int32> I;TArray<FVector2D> UV;TArray<FColor> C;
 void Tri(FVector A,FVector B,FVector D,FLinearColor Col){int32 K=V.Num();FVector Z=FVector::CrossProduct(B-A,D-A).GetSafeNormal();V.Append({A,B,D});I.Append({K,K+1,K+2});for(int J=0;J<3;J++){Normal.Add(Z);UV.Add(FVector2D::ZeroVector);C.Add(Col.ToFColor(true));}}
 void Quad(FVector A,FVector B,FVector Cc,FVector D,FLinearColor Col){Tri(A,B,Cc,Col);Tri(A,Cc,D,Col);}
 void Draw(UProceduralMeshComponent* P,bool Collision=false){P->ClearAllMeshSections();P->CreateMeshSection(0,V,I,Normal,UV,C,TArray<FProcMeshTangent>(),Collision);}
};
FLinearColor Ramp(double F){F=FMath::Clamp(F,0.,1.);return F<.5?FMath::Lerp(FLinearColor(.025,.07,.25),FLinearColor(.04,.82,.68),F*2):FMath::Lerp(FLinearColor(.04,.82,.68),FLinearColor(1,.38,.07),F*2-1);}
void Line(FBuffer& M,FVector P,FVector Q,float R,FLinearColor Col){FVector D=(Q-P).GetSafeNormal(),U=FVector::CrossProduct(D,FVector::UpVector).GetSafeNormal();if(U.IsNearlyZero())U=FVector::RightVector;FVector V=FVector::CrossProduct(D,U).GetSafeNormal();M.Quad(P+U*R,Q+U*R,Q-U*R,P-U*R,Col);M.Quad(P+V*R,Q+V*R,Q-V*R,P-V*R,Col);}
}
AFusionTransportLab::AFusionTransportLab(){RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("TransportLab"));}
FVector AFusionTransportLab::WorldPoint(FVector P)const{P-=Size*.5;P.Y=-P.Y;return P;}
UProceduralMeshComponent* AFusionTransportLab::MakePart(const TCHAR* Name,UMaterialInterface* M){auto P=NewObject<UProceduralMeshComponent>(this,Name);P->SetupAttachment(RootComponent);P->RegisterComponent();P->SetMaterial(0,M);P->SetCollisionEnabled(ECollisionEnabled::NoCollision);P->SetCastShadow(false);P->bUseComplexAsSimpleCollision=true;return P;}
void AFusionTransportLab::SetActive(bool Active){SetActorHiddenInGame(!Active);SetActorEnableCollision(Active);}
bool AFusionTransportLab::Load(){
 FString Raw;if(!FFileHelper::LoadFileToString(Raw,*(FPaths::ProjectContentDir()/TEXT("WorkbenchData/transport_lab.json")))||Raw.Len()>32000000){Error=TEXT("No checked transport dataset loaded.");return false;}
 if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw),Packet)||S(Packet,TEXT("schema"))!=TEXT("fusion.transport-lab.v1")){Error=TEXT("Invalid transport dataset schema.");return false;}
 auto Dim=A(Packet,TEXT("dimensions_cm"));if(Dim.Num()!=3||Dim[0]<=0||Dim[1]<=0||Dim[2]<=0)return false;Size=FVector(Dim[0],Dim[1],Dim[2]);HeatScale=N(Packet,TEXT("common_heating_scale"));
 const TArray<TSharedPtr<FJsonValue>>* Rows=nullptr;if(!Packet->TryGetArrayField(TEXT("cases"),Rows)||Rows->Num()==0||Rows->Num()>128)return false;for(auto V:*Rows)Cases.Add(V->AsObject());
 Metal=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Workbench/M_LabMetal.M_LabMetal"));DataMaterial=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Workbench/M_LabData.M_LabData"));Ghost=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Workbench/M_LabGhost.M_LabGhost"));if(!Metal||!DataMaterial||!Ghost)return false;
 Particles=MakePart(TEXT("RecordedParticles"),DataMaterial);Trails=MakePart(TEXT("RecordedPaths"),DataMaterial);Field=MakePart(TEXT("HeatingSlice"),DataMaterial);Field->SetCollisionResponseToAllChannels(ECR_Ignore);Field->SetCollisionResponseToChannel(ECC_Visibility,ECR_Block);
 if(!LoadSourceSites())return false;Ready=true;SelectCase(0);return Validate();
}
void AFusionTransportLab::SelectCase(int32 Index){
 if(!Cases.IsValidIndex(Index))return;if(bSourceContext)SetSourceContext(false);CaseIndex=Index;Case=Cases[Index];Tracks.Reset();const TArray<TSharedPtr<FJsonValue>>* P=nullptr;
 if(Case->TryGetArrayField(TEXT("paths"),P))for(auto Path:*P){auto O=Path->AsObject();FLabTrack T;T.Photon=S(O,TEXT("particle"))==TEXT("photon");T.Primary=int32(N(O,TEXT("primary")));const TArray<TSharedPtr<FJsonValue>>* Points=nullptr;
 if(!O||!O->TryGetArrayField(TEXT("states"),Points))continue;double Last=-1;
 for(auto X:*Points){auto Row=X->AsArray();if(Row.Num()!=5)continue;double Tim=Row[3]->AsNumber();FVector Pos(Row[0]->AsNumber(),Row[1]->AsNumber(),Row[2]->AsNumber());if(Pos.ContainsNaN()||!FMath::IsFinite(Tim)||Tim<Last)continue;Last=Tim;T.P.Add(WorldPoint(Pos));T.Time.Add(Tim);T.Energy.Add(Row[4]->AsNumber());}
 if(T.P.Num()>1)Tracks.Add(MoveTemp(T));}
 MaxTime=N(Case,TEXT("max_track_time_s"));if(MaxTime<=0)MaxTime=1e-6;Phase=.45f;FieldInspection=TEXT("Click a colored slice cell to inspect its computed value and uncertainty.");BuildHardware();BuildTrails();BuildField();Animate(0);
}
bool AFusionTransportLab::Validate()const{return Ready&&Cases.Num()>0&&Tracks.Num()>0&&A(Case,TEXT("heating_density")).Num()==24*16*16&&N(Case,TEXT("source_histories"))>0;}
void AFusionTransportLab::BuildHardware(){
 for(auto P:Hardware)P->DestroyComponent();Hardware.Reset();auto Box=[&](const TCHAR* Name,FVector Lo,FVector Hi,FLinearColor Col,UMaterialInterface* Mat){FBuffer M;FVector V[8];for(int I=0;I<8;I++)V[I]=WorldPoint(FVector(I&1?Hi.X:Lo.X,I&2?Hi.Y:Lo.Y,I&4?Hi.Z:Lo.Z));for(auto Face:TArray<FIntVector>{FIntVector(0,1,3),FIntVector(0,3,2),FIntVector(4,6,7),FIntVector(4,7,5),FIntVector(0,4,5),FIntVector(0,5,1),FIntVector(2,3,7),FIntVector(2,7,6),FIntVector(0,2,6),FIntVector(0,6,4),FIntVector(1,5,7),FIntVector(1,7,3)})M.Tri(V[Face.X],V[Face.Y],V[Face.Z],Col);auto P=MakePart(Name,Mat);M.Draw(P);Hardware.Add(P);};
 Box(TEXT("BreederEnvelope"),FVector::ZeroVector,Size,FLinearColor(.48,.38,.18),Ghost);
 double H=bCutHardware?Size.Z*.28:Size.Z;Box(TEXT("TungstenArmour"),FVector(-2.3,0,0),FVector(-1.8,Size.Y,H),FLinearColor(.24,.29,.34),Metal);Box(TEXT("FirstWall"),FVector(-1.8,0,0),FVector(0,Size.Y,H),FLinearColor(.55,.62,.69),Metal);
 FBuffer Wire;for(int Axis=0;Axis<3;Axis++)for(int J=0;J<4;J++){FVector Lo(0,0,0),Hi(0,0,0);int A1=(Axis+1)%3,A2=(Axis+2)%3;Lo[A1]=Hi[A1]=(J&1)?Size[A1]:0;Lo[A2]=Hi[A2]=(J&2)?Size[A2]:0;Hi[Axis]=Size[Axis];Line(Wire,WorldPoint(Lo),WorldPoint(Hi),.18,FLinearColor(.08,.48,.52));}auto Frame=MakePart(TEXT("ModelBoundaryNotHousing"),DataMaterial);Wire.Draw(Frame);Hardware.Add(Frame);
 double Ro=N(Packet,TEXT("header_outer_radius_cm")),Ri=N(Packet,TEXT("header_inner_radius_cm")),Cap=N(Packet,TEXT("header_cap_cm"));bool Front=S(Case,TEXT("layout"))==TEXT("headers_front");double X=Front?Ro:Size.X-Ro;
 for(int J=0;J<3;J++){double Y=Size.Y*(1.+2.*J)/6;FBuffer M,Fluid;auto P=[&](double R,double A,double Z){return WorldPoint(FVector(X+R*cos(A),Y+R*sin(A),Z));};
 for(int I=0;I<96;I++){double A0=2*PI*I/96,A1=2*PI*(I+1)/96;Fluid.Quad(P(Ri,A0,Cap),P(Ri,A1,Cap),P(Ri,A1,Size.Z-Cap),P(Ri,A0,Size.Z-Cap),FLinearColor(.03,.36,.72));
 if(bCutHardware&&I>=30&&I<66)continue;
 M.Quad(P(Ro,A0,0),P(Ro,A1,0),P(Ro,A1,Size.Z),P(Ro,A0,Size.Z),FLinearColor(.53,.61,.69));M.Quad(P(Ri,A1,Cap),P(Ri,A0,Cap),P(Ri,A0,Size.Z-Cap),P(Ri,A1,Size.Z-Cap),FLinearColor(.32,.4,.48));
 M.Quad(P(Ri,A0,Cap),P(Ri,A1,Cap),P(Ro,A1,Cap),P(Ro,A0,Cap),FLinearColor(.65,.69,.72));M.Quad(P(Ro,A0,Size.Z-Cap),P(Ro,A1,Size.Z-Cap),P(Ri,A1,Size.Z-Cap),P(Ri,A0,Size.Z-Cap),FLinearColor(.65,.69,.72));
 for(double Z:{0.,Size.Z})M.Tri(WorldPoint(FVector(X,Y,Z)),P(Ro,A0,Z),P(Ro,A1,Z),FLinearColor(.55,.62,.68));}
 auto MetalPart=MakePart(*FString::Printf(TEXT("Header%dSteel"),J),Metal);M.Draw(MetalPart);Hardware.Add(MetalPart);auto FluidPart=MakePart(*FString::Printf(TEXT("Header%dHelium"),J),Ghost);Fluid.Draw(FluidPart);Hardware.Add(FluidPart);
 }
}
void AFusionTransportLab::BuildTrails(){FBuffer M;for(const auto& T:Tracks){FLinearColor Col=T.Photon?FLinearColor(.72,.39,.045):FLinearColor(.025,.38,.48);for(int I=1;I<T.P.Num();I++)if((T.P[I]-T.P[I-1]).SizeSquared()>1e-10)Line(M,T.P[I-1],T.P[I],.08,Col);}M.Draw(Trails);Trails->SetVisibility(bShowTrails);}
void AFusionTransportLab::BuildField(){
 auto V=A(Case,TEXT("heating_density")),SE=A(Case,TEXT("heating_standard_error_density"));if(V.Num()!=6144||SE.Num()!=6144)return;FBuffer M;double Dx=Size.X/24,Dy=Size.Y/16,Z=(SliceIndex+.5)*Size.Z/16;
 for(int Y=0;Y<16;Y++)for(int X=0;X<24;X++){int Index=X+24*(Y+16*SliceIndex);bool Known=V[Index]>0&&SE[Index]/V[Index]<=.5;double Level=log(1+FMath::Max(V[Index],0.))/log(1+HeatScale);FLinearColor Col=Known?Ramp(Level):FLinearColor(.13,.13,.16);double Gap=.04;
 M.Quad(WorldPoint(FVector(X*Dx+Gap,Y*Dy+Gap,Z)),WorldPoint(FVector((X+1)*Dx-Gap,Y*Dy+Gap,Z)),WorldPoint(FVector((X+1)*Dx-Gap,(Y+1)*Dy-Gap,Z)),WorldPoint(FVector(X*Dx+Gap,(Y+1)*Dy-Gap,Z)),Col);}
 M.Draw(Field,true);Field->SetVisibility(bShowField);Field->SetCollisionEnabled(bShowField?ECollisionEnabled::QueryOnly:ECollisionEnabled::NoCollision);
}
void AFusionTransportLab::SetSlice(float V){if(bSourceContext)return;SliceIndex=FMath::Clamp(FMath::FloorToInt(V*16),0,15);BuildField();}
void AFusionTransportLab::InspectWorld(FVector Point){Point.Y=-Point.Y;Point+=Size*.5;int X=FMath::FloorToInt(Point.X/(Size.X/24)),Y=FMath::FloorToInt(Point.Y/(Size.Y/16));if(X<0||X>=24||Y<0||Y>=16)return;InspectField(2*(X+24*Y));}
void AFusionTransportLab::InspectField(int32 Face){if(Face<0)return;int I=Face/2;if(I<0||I>=384)return;int X=I%24,Y=I/24,K=X+24*(Y+16*SliceIndex);auto V=A(Case,TEXT("heating_density")),SE=A(Case,TEXT("heating_standard_error_density"));if(!V.IsValidIndex(K))return;
 FieldInspection=FString::Printf(TEXT("Voxel (%d,%d,%d), center (%.2f, %.2f, %.2f) cm\nHeating %.5g +/- %.3g eV / cm^3 / source neutron\nRelative statistical error %.1f%% | %s"),X,Y,SliceIndex,(X+.5)*Size.X/24,(Y+.5)*Size.Y/16,(SliceIndex+.5)*Size.Z/16,V[K],SE[K],V[K]>0?100*SE[K]/V[K]:0.,V[K]>0&&SE[K]/V[K]<=.5?TEXT("computed voxel mean"):TEXT("masked: insufficient statistics"));double SourceRate=N(Case,TEXT("incident_neutrons_s"));if(SourceRate>0)FieldInspection+=FString::Printf(TEXT("\nConditional DT-rate scaling: %.4f +/- %.4f MW/m^3 (MC error only; geometry/source not validated)"),V[K]*SourceRate*1.602176634e-19,SE[K]*SourceRate*1.602176634e-19);if(N(Case,TEXT("incident_neutrons_s"))>0)FieldInspection+=FString::Printf(TEXT("\nConditional DT-rate scaling: %.4g MW/m^3; source/geometry uncertainty NOT included."),V[K]*N(Case,TEXT("incident_neutrons_s"))*1.602176634e-19);}
void AFusionTransportLab::Animate(float Dt){
 if(!Ready)return;if(bSourceContext){AnimateSourceContext(Dt);return;}if(bPlayback)Phase=FMath::Fmod(Phase+Dt/16.f,1.f);PhysicalTime=(exp(log(1+MaxTime/1e-9)*Phase)-1)*1e-9;FBuffer M;VisibleParticles=0;
 const FVector Corners[6]={FVector(1,0,0),FVector(-1,0,0),FVector(0,1,0),FVector(0,-1,0),FVector(0,0,1),FVector(0,0,-1)};const int Faces[8][3]={{0,2,4},{2,1,4},{1,3,4},{3,0,4},{2,0,5},{1,2,5},{3,1,5},{0,3,5}};
 for(const auto& T:Tracks){if(PhysicalTime<T.Time[0]||PhysicalTime>T.Time.Last())continue;int Lo=0,Hi=T.Time.Num()-1;while(Hi-Lo>1){int Mid=(Lo+Hi)/2;if(T.Time[Mid]<=PhysicalTime)Lo=Mid;else Hi=Mid;}double Range=T.Time[Hi]-T.Time[Lo];FVector Pos=FMath::Lerp(T.P[Lo],T.P[Hi],Range>0?(PhysicalTime-T.Time[Lo])/Range:0.);FLinearColor Col=T.Photon?FLinearColor(1,.66,.08):FLinearColor(.07,.95,1);for(auto& F:Faces)M.Tri(Pos+Corners[F[0]]*.75,Pos+Corners[F[1]]*.75,Pos+Corners[F[2]]*.75,Col);VisibleParticles++;}
 M.Draw(Particles);Trails->SetVisibility(bShowTrails);Field->SetVisibility(bShowField);
}
FString AFusionTransportLab::TimeLabel()const{if(bSourceContext)return FString::Printf(TEXT("Source-map animation phase %.2f | %d displayed direct rays | not a physical source pulse or a time-resolved plasma"),Phase,VisibleParticles);return FString::Printf(TEXT("%.3g microseconds | logarithmic time slider | %d visible markers\nFirst 16 independent source histories aligned at emission; NOT source intensity."),PhysicalTime*1e6,VisibleParticles);}
FString AFusionTransportLab::Status()const{
 if(bSourceContext)return FString::Printf(TEXT("MODEL-DERIVED DIRECT SOURCE\n\nParameterized plasma geometry uses the r838 density/temperature profiles. Source rays run to an outboard midplane patch, then the coupled local calculation transports particles through the headers.\n\n%d of %d canonical source sites are drawn (display-only selection). All weights, directions and observations remain stored. They do not represent source intensity. Straight rays contain no collisions before the first wall.\n\nThe geometry proxy differs by %.3f%% in plasma volume from the systems model and is not a reconstructed equilibrium. Its source rate is explicitly normalized to the reproduced DT rate.\n\nNo surrounding-blanket return flux or whole-reactor TBR is established."),SourceDrawIndices.Num(),SourceSites.Num(),N(Packet->GetObjectField(TEXT("source_context")),TEXT("parameterized_volume_difference_percent")));
 if(!Ready)return Error;
 return FString::Printf(TEXT("%s\nSource: %s | %.0f histories in tally\nTritons per incident neutron: %.5f +/- %.5f\nHeating: %.3f +/- %.3f MeV/source\n\nSOLVER -> DATA -> VIEW\nOpenMC 0.15.2 -> statepoint + tracks -> checked JSON -> Unreal\n%d recorded neutron/photon paths\nMesh: 24 x 16 x 16 voxels\n\nHEATING COLORS\nCommon logarithmic scale: 0 to %.4g eV/cm^3/source\nGrey voxels: relative statistical error >50%% or no score.\nNot temperature; no coolant velocity field exists yet.\n\nGeometry: same r838-linked local module, cm-to-cm coordinates.\nCutaways and large glowing particle markers are display encodings.\nNo reactor-wide neutron field or extra electricity is inferred."),*S(Case,TEXT("title")),*S(Case,TEXT("source_law")),N(Case,TEXT("source_histories")),N(Case,TEXT("tritons_per_source")),N(Case,TEXT("tritons_standard_error")),N(Case,TEXT("heating_MeV_per_source")),N(Case,TEXT("heating_standard_error_MeV")),Tracks.Num(),HeatScale);
}

void AFusionTransportLab::BuildSourceContext(){
 const TSharedPtr<FJsonObject>* C=nullptr;if(!Packet||!Packet->TryGetObjectField(TEXT("source_context"),C))return;auto O=*C;const TSharedPtr<FJsonObject>* GP=nullptr;if(!O->TryGetObjectField(TEXT("geometry"),GP))return;auto G=*GP;
 double R=N(G,TEXT("rmajor"))*100,a=N(G,TEXT("rminor"))*100,k=N(G,TEXT("kappa")),d=N(G,TEXT("triang"));
 auto P=[&](double Theta,double Phi){double Rad=R+a*cos(Theta+d*sin(Theta));return FVector(Rad*cos(Phi),-Rad*sin(Phi),k*a*sin(Theta));};
 FBuffer Wire,Body;
 for(int I=0;I<72;I++)for(int J=0;J<40;J++){double p0=2*PI*I/72,p1=2*PI*(I+1)/72,t0=2*PI*J/40,t1=2*PI*(J+1)/40;Body.Quad(P(t0,p0),P(t0,p1),P(t1,p1),P(t1,p0),FLinearColor(.025,.4,.47));if(I%6==0)Line(Wire,P(t0,p0),P(t1,p0),1.,FLinearColor(.04,.5,.58));if(J%5==0)Line(Wire,P(t0,p0),P(t0,p1),1.,FLinearColor(.04,.35,.4));}
 for(int32 I:SourceDrawIndices){const auto& Site=SourceSites[I];auto X=Site.Birth,Y=Site.Target;Line(Wire,FVector(X.X,-X.Y,X.Z),FVector(Y.X,-Y.Y,Y.Z),1.,FLinearColor(.68,.45,.08));}
 auto LocalSize=A(O,TEXT("local_size_cm"));double Gap=N(O,TEXT("gap_m"))*100;
 if(LocalSize.Num()==3){double HalfY=LocalSize[1]/2,HalfZ=LocalSize[2]/2,WallA=a+Gap,WallR=R+WallA;
 auto PatchPoint=[&](double Y,double Z){double Th=asin(FMath::Clamp(Z/(k*WallA),-1.,1.));double Rad=R+WallA*cos(Th+d*sin(Th));double Phi=Y/WallR;return FVector(Rad*cos(Phi),-Rad*sin(Phi),Z);};
 for(int I=0;I<20;I++){double T0=I/20.,T1=(I+1)/20.;for(double Side:{-1.,1.}){Line(Wire,PatchPoint(-HalfY+2*HalfY*T0,Side*HalfZ),PatchPoint(-HalfY+2*HalfY*T1,Side*HalfZ),2.,FLinearColor(1,.3,.03));Line(Wire,PatchPoint(Side*HalfY,-HalfZ+2*HalfZ*T0),PatchPoint(Side*HalfY,-HalfZ+2*HalfZ*T1),2.,FLinearColor(1,.3,.03));}}
 }
 if(!SourceWire)SourceWire=MakePart(TEXT("DirectViewSourceRays"),DataMaterial);if(!SourceBody)SourceBody=MakePart(TEXT("ParameterizedSourceEnvelope"),Ghost);Wire.Draw(SourceWire);Body.Draw(SourceBody);
}
void AFusionTransportLab::SetSourceContext(bool Active){
 bSourceContext=Active;if(Active)BuildSourceContext();
 for(auto P:Hardware)P->SetVisibility(!Active);if(SourceWire)SourceWire->SetVisibility(Active);if(SourceBody)SourceBody->SetVisibility(Active);Trails->SetVisibility(!Active&&bShowTrails);Field->SetVisibility(!Active&&bShowField);Field->SetCollisionEnabled(!Active&&bShowField?ECollisionEnabled::QueryOnly:ECollisionEnabled::NoCollision);
 FieldInspection=Active?TEXT("Actual model profiles -> parameterized toroidal source -> visibility-weighted incident bank -> OpenMC local module. Golden lines are uncollided source-to-wall rays, not a whole-reactor transport solution."):TEXT("Click a computed slice voxel to inspect its mean and uncertainty.");Animate(0);
}
void AFusionTransportLab::AnimateSourceContext(float Dt){
 if(bPlayback)Phase=FMath::Fmod(Phase+Dt/16.f,1.f);FBuffer M;VisibleParticles=0;
 for(int32 I:SourceDrawIndices){const auto& Site=SourceSites[I];auto X=Site.Birth,Y=Site.Target;FVector Pos=FMath::Lerp(FVector(X.X,-X.Y,X.Z),FVector(Y.X,-Y.Y,Y.Z),Phase);FVector Dx(5,0,0),Dy(0,5,0),Dz(0,0,5);auto Col=FLinearColor(.1,.9,1);M.Quad(Pos+Dx+Dy,Pos-Dx+Dy,Pos-Dx-Dy,Pos+Dx-Dy,Col);M.Quad(Pos+Dx+Dz,Pos-Dx+Dz,Pos-Dx-Dz,Pos+Dx-Dz,Col);VisibleParticles++;}
 M.Draw(Particles);Trails->SetVisibility(false);Field->SetVisibility(false);
}

bool AFusionTransportLab::LoadSourceSites(){
 const TSharedPtr<FJsonObject>* Ref=nullptr;if(!Packet->TryGetObjectField(TEXT("source_context"),Ref))return false;auto O=*Ref;
 if(S(O,TEXT("source_bank_file"))!=TEXT("source_context.bin"))return false;
 TArray<uint8> Bytes;if(!FFileHelper::LoadFileToArray(Bytes,*(FPaths::ProjectContentDir()/TEXT("WorkbenchData/source_context.bin"))))return false;
 FMemoryReader Reader(Bytes);uint32 Magic=0,Version=0;uint64 Count=0;Reader<<Magic<<Version<<Count;
 if(Magic!=0x53574331||Version!=1||Count==0||Count>2000000||uint64(Bytes.Num())!=16+128*Count||N(O,TEXT("source_particle_count"))!=double(Count))return false;
 SourceSites.Reset();SourceSites.Reserve(int32(Count));TSet<uint64> Ids;double ProbabilitySum=0;
 auto ReadVector=[&](){double X=0,Y=0,Z=0;Reader<<X<<Y<<Z;return FVector(X,Y,Z);};
 for(uint64 I=0;I<Count;I++){FLabSourceSite Site;Reader<<Site.Id<<Site.Bank<<Site.Index<<Site.Weight<<Site.Probability;Site.Birth=ReadVector();Site.Target=ReadVector();Site.Local=ReadVector();Site.Direction=ReadVector();
 if(Ids.Contains(Site.Id)||Site.Id!=((uint64(Site.Bank)<<32)|Site.Index)||Site.Birth.ContainsNaN()||Site.Target.ContainsNaN()||Site.Local.ContainsNaN()||Site.Direction.ContainsNaN()||!FMath::IsFinite(Site.Weight)||!FMath::IsFinite(Site.Probability)||Site.Weight<=0||Site.Probability<=0||FMath::Abs(Site.Direction.SizeSquared()-1)>1e-8)return false;
 Ids.Add(Site.Id);ProbabilitySum+=Site.Probability;SourceSites.Add(Site);}
 if(Reader.IsError()||Reader.Tell()!=Reader.TotalSize()||FMath::Abs(ProbabilitySum-1)>1e-8)return false;
 const TSharedPtr<FJsonObject>* Visual=nullptr;if(!O->TryGetObjectField(TEXT("visualization"),Visual))return false;
 int32 Budget=int32(N(*Visual,TEXT("default_source_site_budget"))),MaxBudget=int32(N(*Visual,TEXT("max_source_site_budget")));
 FParse::Value(FCommandLine::Get(),TEXT("SourceRenderBudget="),Budget);if(MaxBudget<1)return false;
 Budget=FMath::Clamp(Budget,1,FMath::Min(MaxBudget,SourceSites.Num()));SourceDrawIndices.Reset();
 for(int32 I=0;I<Budget;I++)SourceDrawIndices.Add(int32(int64(I)*SourceSites.Num()/Budget));
 return true;
}
