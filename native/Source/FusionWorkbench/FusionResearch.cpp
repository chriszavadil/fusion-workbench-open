// Original research-library UI. MIT. Plain text only: no executable HTML or scripts.
#include "FusionRuntime.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Input/SSearchBox.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SMultiLineEditableTextBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Styling/CoreStyle.h"
namespace {
FString Field(TSharedPtr<FJsonObject> O,const TCHAR* Key){FString S;if(O)O->TryGetStringField(Key,S);return S;}
FText T(const FString& S){return FText::FromString(S);}
const FLinearColor Back(.025f,.045f,.06f,1),Accent(.15f,.82f,.73f,1),Warn(.95f,.66f,.28f,1);
}
void AFusionController::LoadResearchLibrary(){
 FString Raw;TSharedPtr<FJsonObject> O;ResearchRecords.Reset();
 if(!FFileHelper::LoadFileToString(Raw,*(FPaths::ProjectContentDir()/TEXT("WorkbenchData/research_library.json")))||Raw.Len()>20000000)return;
 if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw),O)||Field(O,TEXT("schema"))!=TEXT("fusion.research-library.v1"))return;
 const TArray<TSharedPtr<FJsonValue>>* A=nullptr;if(!O->TryGetArrayField(TEXT("records"),A)||A->Num()>1000)return;
 for(const auto& V:*A){auto E=V->AsObject();if(!E||Field(E,TEXT("id")).IsEmpty()||Field(E,TEXT("title")).IsEmpty()||Field(E,TEXT("body")).Len()>2000000){ResearchRecords.Reset();return;}ResearchRecords.Add(E);}
 ResearchUpdated=Field(O,TEXT("updated_date"));if(ResearchRecords.Num())SelectedResearch=ResearchRecords[0];
}
bool AFusionController::ResearchMatches(TSharedPtr<FJsonObject> E)const{
 if(bResearchCurrentOnly&&!Field(E,TEXT("configuration_scope")).Contains(ConfigurationId))return false;
 if(ResearchQuery.IsEmpty())return true;
 FString Hay=Field(E,TEXT("title"))+TEXT(" ")+Field(E,TEXT("body"))+TEXT(" ")+Field(E,TEXT("track"))+TEXT(" ")+Field(E,TEXT("date"))+TEXT(" ")+Field(E,TEXT("status"));
 TArray<FString> Terms;ResearchQuery.ParseIntoArrayWS(Terms);for(const FString& Term:Terms)if(!Hay.Contains(Term,ESearchCase::IgnoreCase))return false;return true;
}
void AFusionController::UpdateResearchRows(){
 if(!ResearchList.IsValid())return;ResearchList->ClearChildren();ResearchMatchesCount=0;
 for(auto E:ResearchRecords){if(!ResearchMatches(E))continue;++ResearchMatchesCount;
 ResearchList->AddSlot().Padding(0,0,8,9)[SNew(SButton).ContentPadding(10).OnClicked_Lambda([this,E](){SelectedResearch=E;if(ResearchReader.IsValid())ResearchReader->SetText(T(Field(E,TEXT("body"))));return FReply::Handled();})[
 SNew(SVerticalBox)+SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(T(Field(E,TEXT("title")))).Font(FCoreStyle::GetDefaultFontStyle("Bold",13)).AutoWrapText(true)]
 +SVerticalBox::Slot().AutoHeight().Padding(0,6)[SNew(STextBlock).Text(T(Field(E,TEXT("date"))+TEXT(" | ")+Field(E,TEXT("track"))+TEXT(" | ")+Field(E,TEXT("status")))).ColorAndOpacity(Accent).AutoWrapText(true)]]];
 }
 if(ResearchMatchesCount==0)ResearchList->AddSlot()[SNew(STextBlock).Text(T(TEXT("No matching records. Change the search or configuration filter."))).AutoWrapText(true)];
}
FString AFusionController::ResearchHeader()const{
 if(!SelectedResearch)return TEXT("No research file loaded. Existing model results are unchanged.");
 return Field(SelectedResearch,TEXT("title"))+TEXT("\n")+Field(SelectedResearch,TEXT("date"))+TEXT(" | ")+Field(SelectedResearch,TEXT("track"))+TEXT(" | ")+Field(SelectedResearch,TEXT("status"))+TEXT("\nScope: ")+Field(SelectedResearch,TEXT("configuration_scope"))+TEXT("\n")+Field(SelectedResearch,TEXT("scope_notice"));
}
TSharedRef<SWidget> AFusionController::MakeResearchUI(){
 SAssignNew(ResearchList,SScrollBox);SAssignNew(ResearchReader,SMultiLineEditableTextBox).IsReadOnly(true).AutoWrapText(true).AllowContextMenu(true).Font(FCoreStyle::GetDefaultFontStyle("Regular",14)).Text(T(Field(SelectedResearch,TEXT("body"))));
 auto Body=SNew(SHorizontalBox)+SHorizontalBox::Slot().FillWidth(.31f)[ResearchList.ToSharedRef()]
 +SHorizontalBox::Slot().FillWidth(.69f).Padding(15,0)[SNew(SVerticalBox)
 +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,12)[SNew(STextBlock).Text_Lambda([this](){return T(ResearchHeader());}).AutoWrapText(true).Font(FCoreStyle::GetDefaultFontStyle("Bold",14)).ColorAndOpacity(Warn)]
 +SVerticalBox::Slot().FillHeight(1)[ResearchReader.ToSharedRef()]
 +SVerticalBox::Slot().AutoHeight().Padding(0,8)[SNew(STextBlock).Text_Lambda([this](){return T(TEXT("Record SHA-256: ")+Field(SelectedResearch,TEXT("content_sha256"))+TEXT("\n")+Field(SelectedResearch,TEXT("source_path")));}).Font(FCoreStyle::GetDefaultFontStyle("Regular",10)).AutoWrapText(true)]];
 auto Panel=SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Back).Padding(20)[SNew(SVerticalBox)
 +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(T(TEXT("RESEARCH LIBRARY | Read the evidence, including failed and superseded work"))).Font(FCoreStyle::GetDefaultFontStyle("Bold",19)).ColorAndOpacity(Accent).AutoWrapText(true)]
 +SVerticalBox::Slot().AutoHeight().Padding(0,8)[SNew(STextBlock).Text_Lambda([this](){return T(FString::Printf(TEXT("%d of %d records | Updated %s | Full cleared text, not all historical raw data. External papers and private correspondence are not included."),ResearchMatchesCount,ResearchRecords.Num(),*ResearchUpdated));}).AutoWrapText(true)]
 +SVerticalBox::Slot().AutoHeight().Padding(0,8,0,15)[SNew(SHorizontalBox)
 +SHorizontalBox::Slot().FillWidth(1)[SNew(SSearchBox).HintText(T(TEXT("Search titles, full text, dates or topics..."))).OnTextChanged_Lambda([this](const FText& Q){ResearchQuery=Q.ToString().Left(256);UpdateResearchRows();})]
 +SHorizontalBox::Slot().AutoWidth().Padding(18,0)[SNew(SCheckBox).IsChecked_Lambda([this](){return bResearchCurrentOnly?ECheckBoxState::Checked:ECheckBoxState::Unchecked;}).OnCheckStateChanged_Lambda([this](ECheckBoxState State){bResearchCurrentOnly=State==ECheckBoxState::Checked;UpdateResearchRows();})[SNew(STextBlock).Text(T(TEXT("Selected configuration only")))]]
 +SHorizontalBox::Slot().AutoWidth().Padding(18,0)[SNew(SButton).OnClicked_Lambda([this](){bResearch=false;return FReply::Handled();})[SNew(STextBlock).Text(T(TEXT("Return to device")))]]]
 +SVerticalBox::Slot().FillHeight(1)[Body]
 +SVerticalBox::Slot().AutoHeight().Padding(0,8)[SNew(STextBlock).Text(T(TEXT("READING DOES NOT RUN CODE OR CHANGE THE DESIGN. A simulation result is not experimental validation. Publication remains on hold."))).ColorAndOpacity(Accent).AutoWrapText(true)]];
 UpdateResearchRows();return Panel;
}
void AFusionController::TestResearchLibrary(){
 auto Result=MakeShared<FJsonObject>();bool Pass=ResearchRecords.Num()>=39;FString Before=ConfigurationId;
 bool Old=false,New=false;for(auto E:ResearchRecords){Old|=Field(E,TEXT("status"))==TEXT("superseded");New|=Field(E,TEXT("title")).Contains(TEXT("Confinement comparison"));}
 ResearchQuery=TEXT("confinement");UpdateResearchRows();int32 Found=ResearchMatchesCount;Pass&=Found>0&&Old&&New;
 ResearchQuery=TEXT("not-a-real-research-record-987654321");UpdateResearchRows();Pass&=ResearchMatchesCount==0;
 ResearchQuery=TEXT("");bResearchCurrentOnly=true;UpdateResearchRows();Pass&=ResearchMatchesCount>0;bResearchCurrentOnly=false;UpdateResearchRows();
 Pass&=ConfigurationId==Before;Result->SetBoolField(TEXT("passed"),Pass);Result->SetNumberField(TEXT("readable_records"),ResearchRecords.Num());Result->SetNumberField(TEXT("confinement_search_results"),Found);Result->SetBoolField(TEXT("superseded_and_new_records_present"),Old&&New);Result->SetBoolField(TEXT("configuration_unchanged"),Before==ConfigurationId);Result->SetBoolField(TEXT("physical_validation"),false);
 FString Out;FJsonSerializer::Serialize(Result,TJsonWriterFactory<>::Create(&Out));FString Dest=FPaths::ProjectSavedDir()/TEXT("Automation/research-library-test.json");IFileManager::Get().MakeDirectory(*FPaths::GetPath(Dest),true);FFileHelper::SaveStringToFile(Out,*Dest);bResearch=true;
}
