import AVFoundation

/// Front camera -> upright, unmirrored BGRA sample buffers on a background queue.
final class CameraCapture: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    enum CaptureError: LocalizedError {
        case permissionDenied, noFrontCamera, configurationFailed(String)

        var errorDescription: String? {
            switch self {
            case .permissionDenied: return "Camera access denied. Enable it in Settings > Spar."
            case .noFrontCamera: return "No front camera found."
            case .configurationFailed(let why): return "Camera setup failed: \(why)"
            }
        }
    }

    let session = AVCaptureSession()
    /// Called on `frameQueue` for every delivered frame.
    var onFrame: ((CMSampleBuffer) -> Void)?

    private let config: PipelineConfig
    private let sessionQueue = DispatchQueue(label: "spar.camera.session")
    private let frameQueue = DispatchQueue(label: "spar.camera.frames", qos: .userInteractive)

    init(config: PipelineConfig) {
        self.config = config
        super.init()
    }

    func start() async throws {
        guard await AVCaptureDevice.requestAccess(for: .video) else { throw CaptureError.permissionDenied }
        try await withCheckedThrowingContinuation { (cont: CheckedContinuation<Void, Error>) in
            sessionQueue.async {
                do {
                    try self.configure()
                    self.session.startRunning()
                    cont.resume()
                } catch {
                    cont.resume(throwing: error)
                }
            }
        }
    }

    func stop() {
        sessionQueue.async { self.session.stopRunning() }
    }

    private func configure() throws {
        session.beginConfiguration()
        defer { session.commitConfiguration() }

        if session.canSetSessionPreset(config.sessionPreset) {
            session.sessionPreset = config.sessionPreset
        }
        guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front) else {
            throw CaptureError.noFrontCamera
        }
        let input = try AVCaptureDeviceInput(device: device)
        guard session.canAddInput(input) else { throw CaptureError.configurationFailed("cannot add input") }
        session.addInput(input)

        let output = AVCaptureVideoDataOutput()
        // MediaPipe's MPImage accepts 32BGRA buffers.
        output.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA]
        output.alwaysDiscardsLateVideoFrames = true
        output.setSampleBufferDelegate(self, queue: frameQueue)
        guard session.canAddOutput(output) else { throw CaptureError.configurationFailed("cannot add output") }
        session.addOutput(output)

        if let connection = output.connection(with: .video) {
            if connection.isVideoRotationAngleSupported(config.portraitRotationAngle) {
                connection.videoRotationAngle = config.portraitRotationAngle
            }
            if connection.isVideoMirroringSupported {
                connection.automaticallyAdjustsVideoMirroring = false
                connection.isVideoMirrored = config.mirroredBuffers
            }
        }

        try lockFrameRate(device)
    }

    private func lockFrameRate(_ device: AVCaptureDevice) throws {
        let fps = Double(config.targetFPS)
        let supported = device.activeFormat.videoSupportedFrameRateRanges.contains {
            $0.minFrameRate <= fps && fps <= $0.maxFrameRate
        }
        guard supported else { return }
        try device.lockForConfiguration()
        let duration = CMTime(value: 1, timescale: config.targetFPS)
        device.activeVideoMinFrameDuration = duration
        device.activeVideoMaxFrameDuration = duration
        device.unlockForConfiguration()
    }

    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        onFrame?(sampleBuffer)
    }
}
