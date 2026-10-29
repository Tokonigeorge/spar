# iOS

To be built by the coding agent (see `docs/ROADMAP.md`, M2 onward).

- `SparEngine/`: Swift package, pure-logic port of `reference/spar_engine`. Its tests must
  load `../../fixtures/*.json` and pass the same checks as `reference/tests/`.
- `Spar/`: the app (Xcode project, SwiftUI, iOS 17+). Not created yet.

Note: this scaffold was written without a Swift toolchain, so only the minimal package
manifest exists. Run `swift build` first thing.
