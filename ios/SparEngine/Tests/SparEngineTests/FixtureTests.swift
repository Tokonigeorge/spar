import XCTest
@testable import SparEngine

// TODO(M3): load every ../../../../fixtures/*.json, run it through SparEngine + ComboJudge,
// and assert the same event signature as reference/tests/test_fixtures.py.
final class FixtureTests: XCTestCase {
    func testPlaceholder() {
        XCTAssertEqual(SparEngineInfo.version, "0.1.0")
    }
}
