#pragma once

#include "CoreMinimal.h"
#include "Engine/StaticMeshActor.h"
#include "RoadsideWorldFeatureActor.generated.h"

UCLASS()
class ROADSIDEDRIVE_API ARoadsideWorldFeatureActor : public AStaticMeshActor
{
    GENERATED_BODY()

public:
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Roadside Inspection")
    FString StableId;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Roadside Inspection")
    FString FeatureType;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Roadside Inspection")
    FVector DimensionsM = FVector::ZeroVector;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Roadside Inspection")
    FVector LocalCenterM = FVector::ZeroVector;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Roadside Inspection")
    FVector SourceCenterM = FVector::ZeroVector;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Roadside Inspection")
    FString CoordinateReference;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Roadside Inspection")
    FString SourceType;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Roadside Inspection")
    FString Confidence;

    UFUNCTION(BlueprintCallable, Category = "Roadside Inspection")
    void InitializeCatalog(const FString& Id, const FString& Kind, const FVector& LocalMinM,
                           const FVector& LocalMaxM, const FVector& OriginM, const FString& Reference,
                           const FString& DatasetKind, const FString& Classification)
    {
        StableId = Id;
        FeatureType = Kind;
        DimensionsM = LocalMaxM - LocalMinM;
        LocalCenterM = (LocalMinM + LocalMaxM) / 2.0;
        SourceCenterM = OriginM + LocalCenterM;
        CoordinateReference = Reference;
        SourceType = DatasetKind;
        Confidence = Classification;
    }

    bool IsSpectatorFloor() const { return FeatureType == TEXT("road") || FeatureType == TEXT("ground"); }
};
