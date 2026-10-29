import Foundation
import XCTest
@testable import SparEngine

// Mirrors reference/tests/test_adapter.py: raw MediaPipe world landmarks in
// fixtures/adapter/*.json must map back onto the body-frame joints of the source fixture.
// (The engine-level lead-jab half of the Python test is added in M3 with the engine port.)
final class AdapterTests: XCTestCase {
    struct AdapterFixture: Decodable {
        struct Frame: Decodable {
            let t: Double
            let world: [String: [Double]]   // landmark index -> [x, y, z, visibility]
        }
        let name: String
        let source: String
        let mirrored: Bool
        let expected_confidence: Double
        let frames: [Frame]
    }

    struct SourceFixture: Decodable {
        struct Frame: Decodable {
            let t: Double
            let joints: [String: [Double]]
        }
        let frames: [Frame]
    }

    static let fixturesDir = URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent()   // SparEngineTests
        .deletingLastPathComponent()   // Tests
        .deletingLastPathComponent()   // SparEngine
        .deletingLastPathComponent()   // ios
        .deletingLastPathComponent()   // repo root
        .appendingPathComponent("fixtures")

    static func landmarks(_ world: [String: [Double]]) -> [RawLandmark] {
        var lms = Array(repeating: RawLandmark(x: 0, y: 0, z: 0, visibility: 0), count: 33)
        for (i, v) in world {
            lms[Int(i)!] = RawLandmark(x: v[0], y: v[1], z: v[2], visibility: v[3])
        }
        return lms
    }

    func testAdapterFixtures() throws {
        let dir = Self.fixturesDir.appendingPathComponent("adapter")
        let files = try FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil)
            .filter { $0.pathExtension == "json" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
        XCTAssertFalse(files.isEmpty, "no adapter fixtures - run reference/tools/make_adapter_fixtures.py")

        for file in files {
            let fx = try JSONDecoder().decode(AdapterFixture.self, from: Data(contentsOf: file))
            let src = try JSONDecoder().decode(
                SourceFixture.self,
                from: Data(contentsOf: Self.fixturesDir.appendingPathComponent(fx.source)))
            XCTAssertEqual(fx.frames.count, src.frames.count, fx.name)

            for (raw, want) in zip(fx.frames, src.frames) {
                let out = try XCTUnwrap(MediaPipeAdapter.bodyFrame(world: Self.landmarks(raw.world), mirrored: fx.mirrored))
                XCTAssertEqual(out.confidence, fx.expected_confidence, accuracy: 1e-6, fx.name)
                for (name, w) in want.joints {
                    let joint = try XCTUnwrap(Joint(rawValue: name), "unknown joint \(name)")
                    let g = try XCTUnwrap(out.joints[joint])
                    for axis in 0..<3 {
                        XCTAssertEqual(g[axis], w[axis], accuracy: 1e-9, "\(fx.name) t=\(raw.t) \(name)[\(axis)]")
                    }
                }
            }
        }
    }

    func testWrongMirroringSwapsHands() throws {
        // A left wrist reported by MediaPipe (index 15) in an unmirrored image is the
        // person's left; decoded as mirrored it would be read as the right wrist.
        var world = Array(repeating: RawLandmark(x: 0, y: 0, z: 0, visibility: 1), count: 33)
        world[15] = RawLandmark(x: 0.3, y: -0.4, z: -0.5, visibility: 1)
        let unmirrored = try XCTUnwrap(MediaPipeAdapter.bodyFrame(world: world, mirrored: false))
        XCTAssertEqual(unmirrored.joints[.lWrist], Vec3(-0.3, 0.4, 0.5))
        let mirrored = try XCTUnwrap(MediaPipeAdapter.bodyFrame(world: world, mirrored: true))
        XCTAssertEqual(mirrored.joints[.rWrist], Vec3(0.3, 0.4, 0.5))
    }

    func testTooFewLandmarks() {
        XCTAssertNil(MediaPipeAdapter.bodyFrame(world: [], mirrored: false))
    }
}
