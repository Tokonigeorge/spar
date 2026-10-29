import SparEngine

enum Stance: String, CaseIterable, Identifiable {
    case orthodox, southpaw
    var id: String { rawValue }
    /// The lead hand's wrist and shoulder (orthodox leads with the left).
    var leadSide: (wrist: Joint, shoulder: Joint) {
        self == .orthodox ? (.lWrist, .lShoulder) : (.rWrist, .rShoulder)
    }
    var rearSide: (wrist: Joint, shoulder: Joint) {
        self == .orthodox ? (.rWrist, .rShoulder) : (.lWrist, .lShoulder)
    }
}

/// The adapter sanity check from docs/MOVEMENT.md, without the engine (that's M3):
/// throw a jab with the lead hand; the hand that reaches forward (+z) must be the lead.
/// If it reports the rear hand, the mirroring is wrong; if neither hand ever reaches,
/// the z axis is probably flipped.
struct LeadJabCheck {
    enum Hand: String { case lead, rear }

    /// How far each wrist is in front of its shoulder, in shoulder-widths.
    private(set) var leadReach = 0.0
    private(set) var rearReach = 0.0
    /// The last hand that reached out, and how many times each hand has.
    private(set) var lastPunch: Hand?
    private(set) var counts: [Hand: Int] = [.lead: 0, .rear: 0]

    private var armed: [Hand: Bool] = [.lead: true, .rear: true]

    mutating func update(_ frame: PoseFrame, stance: Stance, config: PipelineConfig) {
        guard let ls = frame.joints[.lShoulder], let rs = frame.joints[.rShoulder] else { return }
        let shoulderWidth = ((ls - rs) * (ls - rs)).sum().squareRoot()
        guard shoulderWidth > 1e-6 else { return }

        func reach(_ side: (wrist: Joint, shoulder: Joint)) -> Double {
            guard let w = frame.joints[side.wrist], let s = frame.joints[side.shoulder] else { return 0 }
            return (w.z - s.z) / shoulderWidth
        }
        leadReach = reach(stance.leadSide)
        rearReach = reach(stance.rearSide)

        for (hand, r) in [(Hand.lead, leadReach), (Hand.rear, rearReach)] {
            if armed[hand]!, r >= config.jabReachSW {
                armed[hand] = false
                lastPunch = hand
                counts[hand, default: 0] += 1
            } else if r <= config.jabRearmSW {
                armed[hand] = true
            }
        }
    }

    mutating func reset() {
        self = LeadJabCheck()
    }
}
