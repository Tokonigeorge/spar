import AVFoundation
import SwiftUI

/// Full-screen camera feed, mirrored like a selfie view, aspect-filled.
/// `ImageMapping` must use the same gravity and mirroring to line the skeleton up.
struct CameraPreviewView: UIViewRepresentable {
    let session: AVCaptureSession
    let config: PipelineConfig
    /// Flips to true once the session has its input; the preview connection exists from then on.
    let running: Bool

    final class PreviewView: UIView {
        override class var layerClass: AnyClass { AVCaptureVideoPreviewLayer.self }
        var previewLayer: AVCaptureVideoPreviewLayer { layer as! AVCaptureVideoPreviewLayer }
    }

    func makeUIView(context: Context) -> PreviewView {
        let view = PreviewView()
        view.backgroundColor = .black
        view.previewLayer.session = session
        view.previewLayer.videoGravity = .resizeAspectFill
        return view
    }

    func updateUIView(_ view: PreviewView, context: Context) {
        // The connection only exists once the session has an input (see `running`).
        guard running, let connection = view.previewLayer.connection else { return }
        if connection.isVideoRotationAngleSupported(config.portraitRotationAngle) {
            connection.videoRotationAngle = config.portraitRotationAngle
        }
        if connection.isVideoMirroringSupported {
            connection.automaticallyAdjustsVideoMirroring = false
            connection.isVideoMirrored = true
        }
    }
}

/// Maps normalized camera-buffer points onto the mirrored, aspect-filled preview.
struct ImageMapping {
    let imageSize: CGSize
    let viewSize: CGSize
    /// The preview is mirrored; buffers are not (PipelineConfig.mirroredBuffers).
    let flipX: Bool

    func point(_ p: CGPoint) -> CGPoint {
        guard imageSize.width > 0, imageSize.height > 0 else { return .zero }
        let scale = max(viewSize.width / imageSize.width, viewSize.height / imageSize.height)
        let w = imageSize.width * scale, h = imageSize.height * scale
        let ox = (viewSize.width - w) / 2, oy = (viewSize.height - h) / 2
        let x = flipX ? 1 - p.x : p.x
        return CGPoint(x: ox + x * w, y: oy + p.y * h)
    }
}
