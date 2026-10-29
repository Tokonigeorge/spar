# Instructions for coding agents

You are building **Spar**, an iPhone boxing-partner app. Read these before writing code:
`docs/SPEC.md` → `docs/ARCHITECTURE.md` → `docs/MOVEMENT.md` → `docs/ROADMAP.md`.

## Ground rules

1. **Work milestone by milestone** (`docs/ROADMAP.md`). Don't start a milestone until the
   previous one meets its acceptance criteria. Update the checklist in ROADMAP.md as you go.
2. **The reference engine is the source of truth for detection logic.**
   `reference/spar_engine/` (Python) defines behaviour; the Swift `SparEngine` is a port.
   - Any change to detection logic or thresholds is made in BOTH, in the same commit.
   - Both must pass every file in `fixtures/` (Python: `reference/tests/`, Swift: XCTest).
   - Never edit a fixture's `expected` list just to make a test pass. If a fixture is
     wrong, explain why in the commit message.
3. **Latency-critical path stays on-device and network-free.** Camera → pose → engine →
   coach reaction must never wait on a network call or an LLM. Live voice cues are
   pre-recorded/pre-generated audio. The LLM is only used between rounds.
4. **Privacy:** never upload camera video. Recorder mode saves pose streams (joint
   coordinates) locally by default; video recording is opt-in and local.
5. **Coordinate frame** is defined in `docs/MOVEMENT.md` and `reference/spar_engine/types.py`.
   Pose adapters must convert into it. Verify with the "lead jab" sanity check.
6. Keep thresholds in one `Config` struct; no magic numbers scattered in code.
7. Prefer boring, well-supported Apple frameworks (SwiftUI, AVFoundation, RealityKit).
   Ask before adding a third-party dependency other than MediaPipe Tasks.

## Commands

```bash
# Reference engine
cd reference && python tests/test_fixtures.py && python tests/test_robustness.py

# Swift engine (once created)
cd ios/SparEngine && swift test
```

## Definition of done for any task
- Tests pass (Python + Swift where relevant)
- ROADMAP.md checklist updated
- Anything the human needs to do on a real device (permissions, test recordings,
  on-device checks) is written down at the end of your summary
