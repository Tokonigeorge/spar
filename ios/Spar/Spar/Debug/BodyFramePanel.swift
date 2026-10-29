import SparEngine
import SwiftUI

/// The engine's view of the body: joints in the body frame (docs/MOVEMENT.md),
/// drawn front-on (x, y) and from above (x, z). If the adapter is right:
/// the boxer's right shoulder is on +x, the head is +y, and punches go toward +z.
struct BodyFramePanel: View {
    let frame: PoseFrame?
    let stance: Stance

    static let bones: [(Joint, Joint)] = [
        (.lShoulder, .rShoulder), (.lShoulder, .lHip), (.rShoulder, .rHip), (.lHip, .rHip),
        (.lShoulder, .lElbow), (.lElbow, .lWrist), (.rShoulder, .rElbow), (.rElbow, .rWrist),
    ]
    /// Points per metre in the mini plots.
    static let scale: CGFloat = 70

    var body: some View {
        HStack(spacing: 8) {
            plot(title: "front", vertical: "+y up", project: { CGPoint(x: $0.x, y: -$0.y) })
            plot(title: "top", vertical: "+z cam", project: { CGPoint(x: $0.x, y: $0.z) })
        }
    }

    private func plot(title: String, vertical: String, project: @escaping (Vec3) -> CGPoint) -> some View {
        VStack(spacing: 2) {
            Canvas { context, size in
                let c = CGPoint(x: size.width / 2, y: size.height / 2)
                // Axes: +x to the right, the second axis downward on screen for "top" (+z toward you)
                // and upward for "front" (+y).
                let axisLen: CGFloat = size.width * 0.42
                let yDir: CGFloat = title == "front" ? -1 : 1
                arrow(&context, from: c, to: CGPoint(x: c.x + axisLen, y: c.y), color: .red)
                arrow(&context, from: c, to: CGPoint(x: c.x, y: c.y + yDir * axisLen), color: .green)
                context.draw(Text("+x R").font(.caption2).foregroundColor(.red),
                             at: CGPoint(x: c.x + axisLen - 10, y: c.y - 8))
                context.draw(Text(vertical).font(.caption2).foregroundColor(.green),
                             at: CGPoint(x: c.x + 22, y: c.y + yDir * (axisLen - 4)))

                guard let frame, let lh = frame.joints[.lHip], let rh = frame.joints[.rHip] else { return }
                let origin = (lh + rh) / 2 + (title == "front" ? Vec3(0, 0.3, 0) : .zero)
                func p(_ j: Joint) -> CGPoint? {
                    guard let v = frame.joints[j] else { return nil }
                    let q = project(v - origin)
                    return CGPoint(x: c.x + q.x * Self.scale, y: c.y + q.y * Self.scale)
                }
                for (a, b) in Self.bones {
                    guard let pa = p(a), let pb = p(b) else { continue }
                    var path = Path()
                    path.move(to: pa); path.addLine(to: pb)
                    let lead = [stance.leadSide.wrist, stance.leadSide.shoulder,
                                stance == .orthodox ? Joint.lElbow : .rElbow]
                    let color: Color = lead.contains(a) && lead.contains(b) ? .orange : .white
                    context.stroke(path, with: .color(color), lineWidth: 2)
                }
                if let nose = p(.nose) {
                    context.fill(Path(ellipseIn: CGRect(x: nose.x - 4, y: nose.y - 4, width: 8, height: 8)),
                                 with: .color(.yellow))
                }
            }
            .frame(width: 130, height: 130)
            Text(title).font(.caption2).foregroundStyle(.secondary)
        }
    }

    private func arrow(_ context: inout GraphicsContext, from a: CGPoint, to b: CGPoint, color: Color) {
        var path = Path()
        path.move(to: a); path.addLine(to: b)
        let angle = atan2(b.y - a.y, b.x - a.x)
        for side: CGFloat in [-1, 1] {
            let wing = angle + .pi + side * .pi / 7
            path.move(to: b)
            path.addLine(to: CGPoint(x: b.x + 7 * cos(wing), y: b.y + 7 * sin(wing)))
        }
        context.stroke(path, with: .color(color.opacity(0.8)), lineWidth: 1.5)
    }
}
