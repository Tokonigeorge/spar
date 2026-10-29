import SwiftUI

/// M2 debug screen: camera feed, skeleton, FPS / inference time, body-frame axes,
/// and the lead-jab sanity check.
struct DebugScreen: View {
    @State private var model = DebugModel()

    var body: some View {
        ZStack {
            CameraPreviewView(session: model.camera.session, config: model.config, running: model.cameraRunning)
                .ignoresSafeArea()
            SkeletonOverlay(sample: model.sample, stance: model.stance, config: model.config)
                .ignoresSafeArea()
            VStack(alignment: .leading, spacing: 8) {
                statsHUD
                Spacer()
                if let error = model.errorMessage {
                    Text(error).font(.callout).padding(8)
                        .background(.red.opacity(0.8), in: RoundedRectangle(cornerRadius: 8))
                }
                HStack(alignment: .bottom) {
                    BodyFramePanel(frame: model.sample?.frame, stance: model.stance)
                    Spacer()
                    jabCheckPanel
                }
                .padding(8)
                .background(.black.opacity(0.5), in: RoundedRectangle(cornerRadius: 12))
            }
            .foregroundStyle(.white)
            .padding()
        }
        .task {
            UIApplication.shared.isIdleTimerDisabled = true
            await model.start()
        }
    }

    private var statsHUD: some View {
        let s = model.stats
        let poseOK = s.poseFPS >= model.config.minSustainedFPS
        return VStack(alignment: .leading, spacing: 2) {
            Text(String(format: "Pose %.0f fps", s.poseFPS)).foregroundStyle(poseOK ? Color.green : Color.red)
            Text(s.sustainedPoseFPS.map { String(format: "Worst 1 s (last %.0f s): %.0f fps", model.config.sustainedWindowS, $0) }
                 ?? String(format: "Worst 1 s: measuring (%.0f s)…", model.config.sustainedWindowS))
            Text(String(format: "Camera %.0f fps", s.cameraFPS))
            Text(s.inferenceMs.map { String(format: "Inference %.1f ms", $0) } ?? "Inference –")
            Text(model.sample?.frame.map { String(format: "Confidence %.2f", $0.confidence) } ?? "No person")
        }
        .font(.system(.caption, design: .monospaced))
        .padding(8)
        .background(.black.opacity(0.5), in: RoundedRectangle(cornerRadius: 8))
    }

    private var jabCheckPanel: some View {
        let check = model.jabCheck
        return VStack(alignment: .trailing, spacing: 6) {
            Picker("Stance", selection: $model.stance) {
                ForEach(Stance.allCases) { Text($0.rawValue.capitalized).tag($0) }
            }
            .pickerStyle(.segmented)
            .frame(width: 190)
            Text("Lead-jab check").font(.caption.bold())
            Text("Throw a jab with your lead hand").font(.caption2).foregroundStyle(.secondary)
            reachBar("lead", check.leadReach, color: .orange)
            reachBar("rear", check.rearReach, color: .cyan)
            switch check.lastPunch {
            case .lead?: Label("Lead hand ✓", systemImage: "checkmark.circle.fill").foregroundStyle(.green)
            case .rear?: Label("Rear hand: mirroring wrong?", systemImage: "xmark.octagon.fill").foregroundStyle(.red)
            case nil: Text("waiting…").font(.caption)
            }
            Text("lead \(check.counts[.lead] ?? 0) · rear \(check.counts[.rear] ?? 0)")
                .font(.caption2.monospacedDigit())
            Button("Reset") { model.resetJabCheck() }.font(.caption)
        }
        .font(.caption)
    }

    private func reachBar(_ label: String, _ reach: Double, color: Color) -> some View {
        let maxReach = CGFloat(model.config.reachBarMaxSW)
        let threshold = CGFloat(model.config.jabReachSW)
        let filled = min(max(CGFloat(reach), 0), maxReach)
        return HStack(spacing: 4) {
            Text(label).frame(width: 30, alignment: .leading)
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Rectangle().fill(.white.opacity(0.2))
                    Rectangle().fill(color)
                        .frame(width: geo.size.width * filled / maxReach)
                    Rectangle().fill(.white)
                        .frame(width: 2)
                        .offset(x: geo.size.width * threshold / maxReach)
                }
            }
            .frame(width: 100, height: 8)
            Text(String(format: "%.1f", reach)).frame(width: 30, alignment: .trailing)
        }
        .font(.caption2.monospacedDigit())
    }
}
