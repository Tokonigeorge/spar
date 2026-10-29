import Foundation
import QuartzCore

/// Thread-safe FPS / latency counters for the debug overlay.
final class FrameStats {
    struct Snapshot {
        var cameraFPS = 0.0
        var poseFPS = 0.0
        /// Worst one-second pose FPS over the sustained window; nil until the window has filled.
        var sustainedPoseFPS: Double?
        var inferenceMs: Double?
    }

    private let config: PipelineConfig
    private let lock = NSLock()
    private var cameraTimes: [CFTimeInterval] = []
    private var poseTimes: [CFTimeInterval] = []
    private var perSecondPoseFPS: [(t: CFTimeInterval, fps: Double)] = []
    private var startedAt: CFTimeInterval?
    private var lastSecond: CFTimeInterval = 0
    private var inferenceEMA: Double?

    init(config: PipelineConfig) {
        self.config = config
    }

    func recordCameraFrame(now: CFTimeInterval = CACurrentMediaTime()) {
        lock.withLock {
            cameraTimes.append(now)
            Self.trim(&cameraTimes, now: now)
        }
    }

    func recordPose(inferenceMs: Double?, now: CFTimeInterval = CACurrentMediaTime()) {
        lock.withLock {
            if startedAt == nil { startedAt = now }
            poseTimes.append(now)
            Self.trim(&poseTimes, now: now)
            if now - lastSecond >= 1 {
                lastSecond = now
                perSecondPoseFPS.append((now, Double(poseTimes.count)))
                perSecondPoseFPS.removeAll { now - $0.t > config.sustainedWindowS }
            }
            if let ms = inferenceMs {
                let a = config.inferenceEMAAlpha
                inferenceEMA = inferenceEMA.map { $0 + a * (ms - $0) } ?? ms
            }
        }
    }

    func snapshot(now: CFTimeInterval = CACurrentMediaTime()) -> Snapshot {
        lock.withLock {
            Self.trim(&cameraTimes, now: now)
            Self.trim(&poseTimes, now: now)
            var s = Snapshot(cameraFPS: Double(cameraTimes.count), poseFPS: Double(poseTimes.count),
                             inferenceMs: inferenceEMA)
            if let startedAt, now - startedAt >= config.sustainedWindowS {
                s.sustainedPoseFPS = perSecondPoseFPS.map { $0.fps }.min()
            }
            return s
        }
    }

    /// Keep the last second of timestamps, so the count is the FPS.
    private static func trim(_ times: inout [CFTimeInterval], now: CFTimeInterval) {
        times.removeAll { now - $0 > 1 }
    }
}
