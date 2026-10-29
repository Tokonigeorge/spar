import Observation
import QuartzCore
import SparEngine

/// Owns the camera -> pose pipeline and the state the debug screen shows.
/// UI state is only mutated on the main actor.
@Observable
final class DebugModel {
    let config: PipelineConfig
    let camera: CameraCapture

    private(set) var sample: PoseSample?
    private(set) var stats = FrameStats.Snapshot()
    private(set) var jabCheck = LeadJabCheck()
    private(set) var errorMessage: String?
    private(set) var cameraRunning = false
    var stance: Stance = .orthodox {
        didSet { jabCheck.reset() }
    }

    @ObservationIgnored private let frameStats: FrameStats
    @ObservationIgnored private var poseService: PoseService?
    @ObservationIgnored private var started = false

    init(config: PipelineConfig = .default) {
        self.config = config
        camera = CameraCapture(config: config)
        frameStats = FrameStats(config: config)
    }

    @MainActor
    func start() async {
        guard !started else { return }
        started = true
        do {
            let pose = try PoseService(config: config)
            let stats = frameStats
            pose.onSample = { [weak self] sample in
                stats.recordPose(inferenceMs: sample.inferenceMs)
                Task { @MainActor in self?.apply(sample) }
            }
            camera.onFrame = { buffer in
                stats.recordCameraFrame()
                pose.process(buffer)
            }
            poseService = pose
            try await camera.start()
            cameraRunning = true
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    @MainActor
    func resetJabCheck() {
        jabCheck.reset()
    }

    @MainActor
    private func apply(_ sample: PoseSample) {
        self.sample = sample
        stats = frameStats.snapshot()
        if let frame = sample.frame {
            jabCheck.update(frame, stance: stance, config: config)
        }
    }
}
