// Port of reference/spar_engine/types.py (Python is the source of truth).
// M2 ports only what the pose pipeline needs (joints, PoseFrame); M3 adds Config, Event, Attack.

/// Canonical "body frame", metres: +x = the boxer's own right, +y = up,
/// +z = toward the camera / coach. See docs/MOVEMENT.md.
public typealias Vec3 = SIMD3<Double>

/// Joints used by the engine. Raw values match the Python names (`JOINTS`).
/// Left/right are the person's anatomical sides.
public enum Joint: String, CaseIterable, Codable, Sendable {
    case nose
    case lShoulder = "l_shoulder", rShoulder = "r_shoulder"
    case lElbow = "l_elbow", rElbow = "r_elbow"
    case lWrist = "l_wrist", rWrist = "r_wrist"
    case lHip = "l_hip", rHip = "r_hip"
}

public struct PoseFrame: Sendable {
    public var t: Double                 // seconds, monotonic
    public var joints: [Joint: Vec3]     // body frame, metres
    public var confidence: Double        // overall pose confidence 0..1

    public init(t: Double, joints: [Joint: Vec3], confidence: Double = 1.0) {
        self.t = t
        self.joints = joints
        self.confidence = confidence
    }
}
