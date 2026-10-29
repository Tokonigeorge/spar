import AVFoundation
import MediaPipeTasksVision
import QuartzCore
import SparEngine

/// One pose result: body-frame joints for the engine plus image-space points for drawing.
struct PoseSample {
    var t: Double                        // seconds (camera presentation time)
    var inferenceMs: Double?             // detectAsync call -> result callback
    var frame: PoseFrame?                // body frame (nil when nobody is detected)
    var imagePoints: [CGPoint] = []      // normalized (0...1) in the camera buffer, MediaPipe index order
    var imageVisibility: [Double] = []
    var imageSize: CGSize = .zero        // camera buffer size in pixels
}

/// Camera frames -> MediaPipe Pose Landmarker (live stream) -> adapter -> PoseSample.
final class PoseService: NSObject, PoseLandmarkerLiveStreamDelegate {
    enum PoseError: LocalizedError {
        case modelMissing(String)

        var errorDescription: String? {
            switch self {
            case .modelMissing(let name):
                return "\(name).task is not in the app bundle. Run ios/Spar/scripts/fetch_model.sh and rebuild."
            }
        }
    }

    /// Called on MediaPipe's callback queue.
    var onSample: ((PoseSample) -> Void)?

    private let config: PipelineConfig
    private var landmarker: PoseLandmarker?
    private let lock = NSLock()
    private var sentAt: [Int: CFTimeInterval] = [:]   // timestamp ms -> host time it was sent
    private var lastTimestampMs = -1
    private var imageSize: CGSize = .zero

    init(config: PipelineConfig) throws {
        self.config = config
        super.init()
        guard let path = Bundle.main.path(forResource: config.modelName, ofType: "task") else {
            throw PoseError.modelMissing(config.modelName)
        }
        let options = PoseLandmarkerOptions()
        options.baseOptions.modelAssetPath = path
        options.baseOptions.delegate = config.delegate
        options.runningMode = .liveStream
        options.numPoses = 1
        options.poseLandmarkerLiveStreamDelegate = self
        landmarker = try PoseLandmarker(options: options)
    }

    /// Call from the camera queue for every frame.
    func process(_ sampleBuffer: CMSampleBuffer) {
        guard let landmarker else { return }
        let pts = CMSampleBufferGetPresentationTimeStamp(sampleBuffer)
        let timestampMs = Int(CMTimeGetSeconds(pts) * 1000)
        // MediaPipe requires strictly increasing timestamps in live-stream mode.
        guard timestampMs > lastTimestampMs else { return }
        lastTimestampMs = timestampMs

        guard let image = try? MPImage(sampleBuffer: sampleBuffer, orientation: .up) else { return }
        lock.withLock {
            sentAt[timestampMs] = CACurrentMediaTime()
            imageSize = CGSize(width: image.width, height: image.height)
        }
        do {
            try landmarker.detectAsync(image: image, timestampInMilliseconds: timestampMs)
        } catch {
            lock.withLock { _ = sentAt.removeValue(forKey: timestampMs) }
        }
    }

    func poseLandmarker(_ poseLandmarker: PoseLandmarker,
                        didFinishDetection result: PoseLandmarkerResult?,
                        timestampInMilliseconds: Int,
                        error: Error?) {
        let now = CACurrentMediaTime()
        let (sent, size) = lock.withLock { () -> (CFTimeInterval?, CGSize) in
            let sent = sentAt[timestampInMilliseconds]
            // Frames MediaPipe dropped never call back; forget them too.
            sentAt = sentAt.filter { $0.key > timestampInMilliseconds }
            return (sent, imageSize)
        }

        let t = Double(timestampInMilliseconds) / 1000
        var sample = PoseSample(t: t, inferenceMs: sent.map { (now - $0) * 1000 }, imageSize: size)
        if let world = result?.worldLandmarks.first {
            let raw = world.map {
                RawLandmark(x: Double($0.x), y: Double($0.y), z: Double($0.z), visibility: $0.visibility?.doubleValue)
            }
            if let body = MediaPipeAdapter.bodyFrame(world: raw, mirrored: config.mirroredBuffers) {
                sample.frame = PoseFrame(t: t, joints: body.joints, confidence: body.confidence)
            }
        }
        if let image = result?.landmarks.first {
            sample.imagePoints = image.map { CGPoint(x: CGFloat($0.x), y: CGFloat($0.y)) }
            sample.imageVisibility = image.map { $0.visibility?.doubleValue ?? 0 }
        }
        onSample?(sample)
    }
}
