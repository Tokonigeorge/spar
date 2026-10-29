// Port of reference/spar_engine/adapter.py (Python is the source of truth).
// Shared test data: fixtures/adapter/*.json.

/// One landmark as the pose model reports it. Kept free of MediaPipe types so the
/// engine package has no dependencies; the app copies MediaPipe's `Landmark` into this.
public struct RawLandmark: Sendable {
    public var x: Double
    public var y: Double
    public var z: Double
    public var visibility: Double?   // nil counts as 0

    public init(x: Double, y: Double, z: Double, visibility: Double? = nil) {
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility
    }
}

public enum MediaPipeAdapter {
    /// MediaPipe Pose landmark indices (anatomical left/right of the person).
    public static let index: [Joint: Int] = [
        .nose: 0, .lShoulder: 11, .rShoulder: 12, .lElbow: 13, .rElbow: 14,
        .lWrist: 15, .rWrist: 16, .lHip: 23, .rHip: 24,
    ]

    /// MediaPipe world landmarks (metres, origin at hips, x = image right, y = down,
    /// z = smaller is closer to camera) -> body frame (+x boxer's right, +y up, +z toward camera).
    ///
    /// For a person facing an unmirrored camera, their right side is on the image's
    /// left, so body x = -image x. A mirrored image flips that AND MediaPipe's left/right
    /// labels, so we swap the labels back and keep image x.
    ///
    /// Returns nil if `world` is too short to contain every joint (MediaPipe gives 33).
    public static func bodyFrame(world: [RawLandmark], mirrored: Bool) -> (joints: [Joint: Vec3], confidence: Double)? {
        guard world.count > index.values.max()! else { return nil }
        var joints: [Joint: Vec3] = [:]
        var visibilitySum = 0.0
        for joint in Joint.allCases {
            let source = mirrored ? joint.swappedSide : joint
            let lm = world[index[source]!]
            let x = mirrored ? lm.x : -lm.x
            joints[joint] = Vec3(x, -lm.y, -lm.z)
            visibilitySum += lm.visibility ?? 0
        }
        return (joints, visibilitySum / Double(Joint.allCases.count))
    }
}

extension Joint {
    /// The same joint on the other side of the body (nose maps to itself).
    public var swappedSide: Joint {
        switch self {
        case .nose: return .nose
        case .lShoulder: return .rShoulder
        case .rShoulder: return .lShoulder
        case .lElbow: return .rElbow
        case .rElbow: return .lElbow
        case .lWrist: return .rWrist
        case .rWrist: return .lWrist
        case .lHip: return .rHip
        case .rHip: return .lHip
        }
    }
}
