import SparEngine
import SwiftUI

/// MediaPipe landmarks drawn over the camera preview. Lead arm orange, rear arm blue.
struct SkeletonOverlay: View {
    let sample: PoseSample?
    let stance: Stance
    let config: PipelineConfig

    // MediaPipe Pose indices: torso, arms, legs (knees up are what the setup guarantees).
    static let bones: [(Int, Int)] = [
        (11, 12), (11, 23), (12, 24), (23, 24),
        (11, 13), (13, 15), (12, 14), (14, 16),
        (23, 25), (24, 26), (25, 27), (26, 28),
    ]

    /// Image landmark index of a body-frame joint, honouring the adapter's label swap.
    func imageIndex(_ joint: Joint) -> Int {
        MediaPipeAdapter.index[config.mirroredBuffers ? joint.swappedSide : joint]!
    }

    var body: some View {
        Canvas { context, size in
            guard let sample, !sample.imagePoints.isEmpty else { return }
            let mapping = ImageMapping(imageSize: sample.imageSize, viewSize: size, flipX: !config.mirroredBuffers)
            let pts = sample.imagePoints.map(mapping.point)
            func visible(_ i: Int) -> Bool { i < pts.count }

            let leadArm = Set([stance.leadSide.shoulder, stance.leadSide.wrist,
                               stance == .orthodox ? Joint.lElbow : .rElbow].map(imageIndex))
            let rearArm = Set([stance.rearSide.shoulder, stance.rearSide.wrist,
                               stance == .orthodox ? Joint.rElbow : .lElbow].map(imageIndex))

            for (a, b) in Self.bones where visible(a) && visible(b) {
                var path = Path()
                path.move(to: pts[a]); path.addLine(to: pts[b])
                let color: Color = leadArm.contains(a) && leadArm.contains(b) ? .orange
                    : rearArm.contains(a) && rearArm.contains(b) ? .cyan : .white
                context.stroke(path, with: .color(color.opacity(0.9)), lineWidth: 4)
            }
            for joint in Joint.allCases {
                let i = imageIndex(joint)
                guard visible(i) else { continue }
                let r: CGFloat = 6
                let dot = Path(ellipseIn: CGRect(x: pts[i].x - r, y: pts[i].y - r, width: 2 * r, height: 2 * r))
                context.fill(dot, with: .color(.yellow))
            }
            // Label wrists L/R (the person's anatomical side) so mirroring mistakes are visible.
            for (joint, label) in [(Joint.lWrist, "L"), (.rWrist, "R")] {
                let i = imageIndex(joint)
                guard visible(i) else { continue }
                context.draw(Text(label).font(.headline.bold()).foregroundColor(.yellow),
                             at: CGPoint(x: pts[i].x, y: pts[i].y - 18))
            }
        }
        .allowsHitTesting(false)
    }
}
