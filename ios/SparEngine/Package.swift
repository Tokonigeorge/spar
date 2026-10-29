// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "SparEngine",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [.library(name: "SparEngine", targets: ["SparEngine"])],
    targets: [
        .target(name: "SparEngine"),
        .testTarget(name: "SparEngineTests", dependencies: ["SparEngine"]),
    ]
)
