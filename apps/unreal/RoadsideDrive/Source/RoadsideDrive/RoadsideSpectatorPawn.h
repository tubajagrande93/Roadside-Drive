#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/Pawn.h"
#include "RoadsideSpectatorPawn.generated.h"

class UCameraComponent;
class UPrimitiveComponent;

UCLASS()
class ROADSIDEDRIVE_API ARoadsideSpectatorPawn : public APawn
{
    GENERATED_BODY()

public:
    ARoadsideSpectatorPawn();
    virtual void Tick(float DeltaSeconds) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spectator", meta = (ClampMin = "1"))
    float ClearanceCm = 120.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spectator")
    float FallbackFloorCm = 0.0f;

    UFUNCTION(BlueprintCallable, Category = "Spectator")
    void ApplyFlightInput(FVector LocalAxes, float DeltaSeconds, bool bBoost);

protected:
    virtual void BeginPlay() override;

private:
    void Look(float MouseX, float MouseY);
    double SampleFloor(const FVector& Proposed);

    UPROPERTY(VisibleAnywhere, Category = "Spectator")
    TObjectPtr<UCameraComponent> Camera;

    TArray<TWeakObjectPtr<UPrimitiveComponent>> Floors;
    TOptional<double> LastFloorCm;
    double SpeedCmPerSecond = 1000.0;
};

UCLASS()
class ROADSIDEDRIVE_API ARoadsideSpectatorGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    ARoadsideSpectatorGameMode();
};
