#include "RoadsideSpectatorPawn.h"

#include "Camera/CameraComponent.h"
#include "CollisionQueryParams.h"
#include "Components/StaticMeshComponent.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "RoadsideWorldFeatureActor.h"

ARoadsideSpectatorPawn::ARoadsideSpectatorPawn()
{
    PrimaryActorTick.bCanEverTick = true;
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("SpectatorCamera"));
    SetRootComponent(Camera);
    Camera->bUsePawnControlRotation = true;
}

void ARoadsideSpectatorPawn::BeginPlay()
{
    Super::BeginPlay();
    for (TActorIterator<ARoadsideWorldFeatureActor> It(GetWorld()); It; ++It)
    {
        if (It->IsSpectatorFloor())
        {
            Floors.Add(It->GetStaticMeshComponent());
        }
    }
}

void ARoadsideSpectatorPawn::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    APlayerController* Player = Cast<APlayerController>(GetController());
    if (!Player || !Player->IsLocalController())
    {
        return;
    }

    float MouseX = 0.0f;
    float MouseY = 0.0f;
    Player->GetInputMouseDelta(MouseX, MouseY);
    Look(MouseX, MouseY);

    if (Player->WasInputKeyJustPressed(EKeys::MouseScrollUp))
    {
        SpeedCmPerSecond = FMath::Min(SpeedCmPerSecond * 1.25, 12000.0);
    }
    if (Player->WasInputKeyJustPressed(EKeys::MouseScrollDown))
    {
        SpeedCmPerSecond = FMath::Max(SpeedCmPerSecond / 1.25, 150.0);
    }

    const auto Down = [Player](const FKey& Key) { return Player->IsInputKeyDown(Key) ? 1.0 : 0.0; };
    const double Descend = FMath::Max(Down(EKeys::LeftControl), Down(EKeys::RightControl));
    const bool bBoost = Down(EKeys::LeftShift) > 0 || Down(EKeys::RightShift) > 0;
    ApplyFlightInput(
        FVector(Down(EKeys::W) - Down(EKeys::S), Down(EKeys::D) - Down(EKeys::A),
                Down(EKeys::SpaceBar) - Descend),
        DeltaSeconds, bBoost);
}

void ARoadsideSpectatorPawn::Look(float MouseX, float MouseY)
{
    if (MouseX == 0 && MouseY == 0)
    {
        return;
    }
    FRotator View = Controller->GetControlRotation();
    View.Yaw = FRotator::NormalizeAxis(View.Yaw + MouseX * 0.16);
    View.Pitch = FMath::Clamp(FRotator::NormalizeAxis(View.Pitch - MouseY * 0.16), -89.0, 89.0);
    View.Roll = 0.0;
    Controller->SetControlRotation(View);
}

void ARoadsideSpectatorPawn::ApplyFlightInput(FVector LocalAxes, float DeltaSeconds, bool bBoost)
{
    if (LocalAxes.ContainsNaN() || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0)
    {
        return;
    }

    const double Yaw = Controller ? Controller->GetControlRotation().Yaw : GetActorRotation().Yaw;
    const FRotator Heading(0, Yaw, 0);
    const FVector Direction = Heading.RotateVector(LocalAxes.GetClampedToMaxSize(1.0));
    const double Distance = SpeedCmPerSecond * (bBoost ? 3.0 : 1.0) * DeltaSeconds;
    FVector Proposed = GetActorLocation() + Direction * Distance;
    Proposed.Z = FMath::Max(Proposed.Z, SampleFloor(Proposed) + FMath::Max(1.0f, ClearanceCm));
    SetActorLocation(Proposed, false);
}

double ARoadsideSpectatorPawn::SampleFloor(const FVector& Proposed)
{
    TOptional<double> Top;
    const FVector Start(Proposed.X, Proposed.Y, 2000000);
    const FVector End(Proposed.X, Proposed.Y, -2000000);
    const FCollisionQueryParams Params(SCENE_QUERY_STAT(RoadsideSpectatorFloor), true);
    for (const TWeakObjectPtr<UPrimitiveComponent>& Floor : Floors)
    {
        if (UPrimitiveComponent* Component = Floor.Get())
        {
            FHitResult Hit;
            if (Component->LineTraceComponent(Hit, Start, End, Params)
                && (!Top.IsSet() || Hit.ImpactPoint.Z > Top.GetValue()))
            {
                Top = Hit.ImpactPoint.Z;
            }
        }
    }
    if (Top.IsSet())
    {
        LastFloorCm = Top;
    }
    return LastFloorCm.Get(FallbackFloorCm);
}

ARoadsideSpectatorGameMode::ARoadsideSpectatorGameMode()
{
    DefaultPawnClass = ARoadsideSpectatorPawn::StaticClass();
}
