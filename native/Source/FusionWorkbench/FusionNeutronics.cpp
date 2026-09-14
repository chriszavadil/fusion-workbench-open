// Original MIT. Recorded local neutron transport, not whole-device spatial physics.
#include "FusionRuntime.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Widgets/SLeafWidget.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Text/STextBlock.h"
#include "Styling/CoreStyle.h"
#include "Rendering/DrawElements.h"
namespace {
FString NS(TSharedPtr<FJsonObject> O,const TCHAR* K){FString S;if(O)O->TryGetStringField(K,S);return S;}
double NN(TSharedPtr<FJsonObject> O,const TCHAR* K){double V=0;if(O)O->TryGetNumberField(K,V);return V;}
TArray<double> NA(TSharedPtr<FJsonObject> O,const TCHAR* K){TArray<double> R;const TArray<TSharedPtr<FJsonValue>>* A=nullptr;if(O&&O->TryGetArrayField(K,A))for(auto V:*A)R.Add(V->AsNumber());return R;}
FText NT(const FString& S){return FText::FromString(S);}
const FLinearColor Dark(.025f,.045f,.06f,1),Bright(.17f,.8f,.72f,1),Amber(.94f,.65f,.27f,1),Grey(.55f,.65f,.73f,1);
}
void AFusionController::LoadNeutronics(){
 FString Raw;NeutronCases.Reset();TSharedPtr<FJsonObject> O;
 if(!FFileHelper::LoadFileToString(Raw,*(FPaths::ProjectContentDir()/TEXT("WorkbenchData/neutronics.json")))||Raw.Len()>1000000)return;
 if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw),O)||NS(O,TEXT("schema"))!=TEXT("fusion.neutronics-view.v1"))return;
 const TArray<TSharedPtr<FJsonValue>>* A=nullptr;if(!O->TryGetArrayField(TEXT("cases"),A)||A->Num()!=3)return;
 for(auto V:*A){auto C=V->AsObject();auto Y=NA(C,TEXT("depth_tritons_per_incident_neutron"));if(!C||Y.Num()!=40||!FMath::IsFinite(NN(C,TEXT("tritons_per_incident_neutron")))){NeutronCases.Reset();return;}NeutronCases.Add(C);}
 NeutronData=O;NeutronLayout=0;
}
class SNeutronFigure:public SLeafWidget{
public:SLATE_BEGIN_ARGS(SNeutronFigure){}SLATE_ARGUMENT(AFusionController*,Controller) SLATE_ARGUMENT(bool,Geometry) SLATE_END_ARGS()
 TWeakObjectPtr<AFusionController> C;bool Geometry=false;
 void Construct(const FArguments& A){C=A._Controller;Geometry=A._Geometry;}
 virtual FVector2D ComputeDesiredSize(float)const override{return FVector2D(520,340);}
 virtual int32 OnPaint(const FPaintArgs&,const FGeometry& G,const FSlateRect&,FSlateWindowElementList& Out,int32 L,const FWidgetStyle&,bool)const override{
  if(!C.IsValid()||C->NeutronCases.Num()!=3)return L;auto Size=G.GetLocalSize();auto Data=C->NeutronCases[C->NeutronLayout];
  auto Lines=[&](TArray<FVector2D> P,FLinearColor Color,float Thick=2){FSlateDrawElement::MakeLines(Out,L+1,G.ToPaintGeometry(),P,ESlateDrawEffect::None,Color,true,Thick);};
  auto Label=[&](const FString& S,FVector2D Pos,FLinearColor Color){FSlateDrawElement::MakeText(Out,L+2,G.ToPaintGeometry(FVector2f(400,25),FSlateLayoutTransform(FVector2f(Pos))),NT(S),FCoreStyle::GetDefaultFontStyle("Regular",12),ESlateDrawEffect::None,Color);};
  if(Geometry){
   double Depth=NN(C->NeutronData,TEXT("module_depth_m")),Width=NN(C->NeutronData,TEXT("module_width_m"));if(Depth<=0||Width<=0)return L;
   double Scale=FMath::Min((Size.X-100)/Depth,(Size.Y-70)/Width);FVector2D Origin(65,30);
   auto P=[&](double X,double Y){return Origin+FVector2D(Scale*X,Scale*Y);};
   Lines({P(0,0),P(Depth,0),P(Depth,Width),P(0,Width),P(0,0)},Bright,2);
   Lines({P(-.02,0),P(-.02,Width)},Amber,4);Label(TEXT("14.1 MeV neutrons ->"),FVector2D(5,5),Amber);
   Label(TEXT("1 m depth; reflecting side faces"),FVector2D(45,Size.Y-24),Grey);
   if(C->NeutronLayout>0){double Outer=NN(C->NeutronData,TEXT("header_outer_radius_m")),Inner=NN(C->NeutronData,TEXT("header_inner_radius_m"));double X=C->NeutronLayout==1?Depth-Outer:Outer;
    for(double Y:{Width/6,Width/2,Width*5/6})for(double Radius:{Outer,Inner}){TArray<FVector2D> Circle;for(int I=0;I<=48;++I){double A=2*PI*I/48;Circle.Add(P(X+Radius*FMath::Cos(A),Y+Radius*FMath::Sin(A)));}Lines(Circle,Radius==Outer?Grey:Amber,2);}
   }else Label(TEXT("Same material inventory, uniformly mixed"),P(.04,Width*.48),Grey);
  }else{
   auto Base=NA(C->NeutronCases[0],TEXT("depth_tritons_per_incident_neutron"));auto Y=NA(Data,TEXT("depth_tritons_per_incident_neutron"));double Max=0;for(auto V:Base)Max=FMath::Max(Max,V);for(auto V:Y)Max=FMath::Max(Max,V);if(Max<=0)return L;
   auto P=[&](int I,double V){return FVector2D(55+(Size.X-80)*(I+.5)/40,Size.Y-48-(Size.Y-100)*V/(Max*1.1));};
   Lines({FVector2D(55,45),FVector2D(55,Size.Y-48),FVector2D(Size.X-20,Size.Y-48)},Grey,1);
   int J=0;for(auto Values:{Base,Y}){TArray<FVector2D> Points;for(int I=0;I<40;++I)Points.Add(P(I,Values[I]));Lines(Points,J++?Bright:Grey,2);}
   Label(FString::Printf(TEXT("%.4f tritons/source per 2.5 cm bin"),Max),FVector2D(55,14),Bright);Label(TEXT("0 cm"),FVector2D(55,Size.Y-27),Grey);Label(TEXT("Blanket depth"),FVector2D(Size.X*.45,Size.Y-27),Grey);Label(TEXT("100 cm"),FVector2D(Size.X-72,Size.Y-27),Grey);
  }return L+2;
 }
};
FString AFusionController::NeutronMetrics()const{
 if(NeutronCases.Num()!=3)return TEXT("No completed local transport study loaded. No reactor metric has changed.");
 auto R=NeutronCases[NeutronLayout];return FString::Printf(TEXT("%s\nTritons produced per incident neutron: %.5f +/- %.5f (1 standard error, Monte Carlo only)\nDeposited energy: %.3f +/- %.3f MeV per incident neutron\n%.0f simulated source histories | Recorded OpenMC neutron + photon transport"),*NS(R,TEXT("title")),NN(R,TEXT("tritons_per_incident_neutron")),NN(R,TEXT("tritons_standard_error")),NN(R,TEXT("heating_MeV_per_incident_neutron")),NN(R,TEXT("heating_standard_error_MeV")),NN(R,TEXT("source_histories")));
}
TSharedRef<SWidget> AFusionController::MakeNeutronicsUI(){
 auto Buttons=SNew(SHorizontalBox);int32 Index=0;for(const FString Name:{TEXT("Uniform inventory"),TEXT("Headers at rear"),TEXT("Headers near front")}){int32 I=Index++;Buttons->AddSlot().AutoWidth().Padding(0,0,10,0)[SNew(SButton).ContentPadding(10).OnClicked_Lambda([this,I](){NeutronLayout=I;return FReply::Handled();})[SNew(STextBlock).Text(NT(Name))]];}
 Buttons->AddSlot().AutoWidth().Padding(15,0)[SNew(SButton).ContentPadding(10).OnClicked_Lambda([this](){bNeutron=false;bResearch=true;ResearchQuery=TEXT("header neutron");UpdateResearchRows();return FReply::Handled();})[SNew(STextBlock).Text(NT(TEXT("Read the audit")))]];
 Buttons->AddSlot().AutoWidth().Padding(15,0)[SNew(SButton).ContentPadding(10).OnClicked_Lambda([this](){bNeutron=false;return FReply::Handled();})[SNew(STextBlock).Text(NT(TEXT("Return to device")))]];
 return SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Dark).Padding(20)[SNew(SVerticalBox)
 +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(NT(TEXT("NEUTRON TRANSPORT | LOCAL BLANKET / HEADER STUDY"))).Font(FCoreStyle::GetDefaultFontStyle("Bold",20)).ColorAndOpacity(Bright)]
 +SVerticalBox::Slot().AutoHeight().Padding(0,10)[SNew(STextBlock).Text(NT(TEXT("r838-linked repeated rectangular cell, NOT a full reactor. Equal nuclide inventories; placement changes only. This panel never transfers the results to r900."))).AutoWrapText(true)]
 +SVerticalBox::Slot().AutoHeight().Padding(0,8)[Buttons]
 +SVerticalBox::Slot().AutoHeight().Padding(0,12)[SNew(STextBlock).Text_Lambda([this](){return NT(NeutronMetrics());}).Font(FCoreStyle::GetDefaultFontStyle("Regular",15)).ColorAndOpacity(Amber).AutoWrapText(true)]
 +SVerticalBox::Slot().FillHeight(1)[SNew(SHorizontalBox)
 +SHorizontalBox::Slot().FillWidth(.48f)[SNew(SVerticalBox)+SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(NT(TEXT("Geometry at mid-height; not a neutron heat map")))] +SVerticalBox::Slot().FillHeight(1)[SNew(SNeutronFigure).Controller(this).Geometry(true)]]
 +SHorizontalBox::Slot().FillWidth(.52f)[SNew(SVerticalBox)+SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(NT(TEXT("Calculated depth profile: grey = uniform, teal = selected")))] +SVerticalBox::Slot().FillHeight(1)[SNew(SNeutronFigure).Controller(this).Geometry(false)]]]
 +SVerticalBox::Slot().AutoHeight().Padding(0,15)[SNew(STextBlock).Text_Lambda([this](){return NT(NS(NeutronData,TEXT("decision")));}).AutoWrapText(true).Font(FCoreStyle::GetDefaultFontStyle("Bold",14)).ColorAndOpacity(Amber)]
 +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(NT(TEXT("No global tritium-breeding ratio, recovered usable fuel, measured hardware validation or extra net electricity is claimed. Statistical error excludes nuclear-data and geometry uncertainty."))).AutoWrapText(true).ColorAndOpacity(Grey)]];
}
void AFusionController::TestNeutronics(){
 bool OK=NeutronCases.Num()==3;FString Before=ConfigurationId;if(OK)for(auto R:NeutronCases){auto Y=NA(R,TEXT("depth_tritons_per_incident_neutron"));OK&=Y.Num()==40&&NN(R,TEXT("source_histories"))>=500000&&NN(R,TEXT("tritons_per_incident_neutron"))>0;for(auto V:Y)OK&=FMath::IsFinite(V)&&V>=0;}
 auto O=MakeShared<FJsonObject>();O->SetBoolField(TEXT("passed"),OK);O->SetNumberField(TEXT("layouts_loaded"),NeutronCases.Num());O->SetBoolField(TEXT("configuration_unchanged"),Before==ConfigurationId);O->SetBoolField(TEXT("physical_validation"),false);
 FString Text;FJsonSerializer::Serialize(O,TJsonWriterFactory<>::Create(&Text));FString Dest=FPaths::ProjectSavedDir()/TEXT("Automation/neutronics-view-test.json");IFileManager::Get().MakeDirectory(*FPaths::GetPath(Dest),true);FFileHelper::SaveStringToFile(Text,*Dest);NeutronLayout=2;bNeutron=true;bResearch=false;bEvidence=false;
}
