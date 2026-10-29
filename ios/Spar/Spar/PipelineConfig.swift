import AVFoundation
import MediaPipeTasksVision

/// Every tunable of the camera -> pose pipeline and the debug screen, in one place.
/// Detection thresholds live in the engine's Config (reference/spar_engine/types.py), not here.
struct PipelineConfig {
    // Camera
    var sessionPreset: AVCaptureSession.Preset = .hd1280x720
    var targetFPS: Int32 = 30
    /// Rotation applied to camera buffers so they arrive upright in portrait.
    var portraitRotationAngle: CGFloat = 90
    /// We ask AVFoundation for unmirrored buffers, so the adapter must not un-mirror.
    /// The on-screen preview is mirrored separately (selfie view).
    var mirroredBuffers = false

    // Pose model (bundled by scripts/fetch_model.sh)
    var modelName = "pose_landmarker_full"
    var delegate: Delegate = .GPU

    // Lead-jab sanity check (docs/MOVEMENT.md), in shoulder-widths
    /// Wrist this far in front of its shoulder (+z) counts as an extended punch.
    var jabReachSW = 1.0
    /// Wrist must come back behind this before the same hand can trigger again.
    var jabRearmSW = 0.7
    /// Full scale of the reach bars on screen.
    var reachBarMaxSW = 2.0

    // Stats
    /// M2 acceptance: pose results per second, sustained (docs/ROADMAP.md).
    var minSustainedFPS = 25.0
    /// Window over which the worst one-second FPS is reported (the "sustained" number).
    var sustainedWindowS = 30.0
    /// Smoothing for the displayed inference time.
    var inferenceEMAAlpha = 0.1

    static let `default` = PipelineConfig()
}
