# Roadmap

Each milestone has acceptance criteria. Don't move on until they're met.

## M0 — Reference engine ✅
- [x] Rule-based engine: punches (6 types), retract, guard, slips/ducks, coach attacks, combos
- [x] Synthetic fixtures + expected events (7 scenarios)
- [x] Noise robustness test (1.5 cm jitter)
- [x] Video analysis tool (MediaPipe → engine)

## M1 — Tune on real recordings (human + agent)
- [ ] Human: record ≥ 10 min of shadowboxing from the real phone position (front camera,
      2.5–3 m, chest height). Say each punch out loud, or keep a written list of what was thrown.
- [ ] Run `analyze_video.py` and check the lead-jab sanity test
- [ ] Turn ≥ 3 recordings into fixtures with hand-written `expected` lists
- [ ] Retune `Config` until: punch detection ≥ 90%, type ≥ 85%, guard drops ≥ 90%,
      false punches < 1 per minute
- [ ] Evaluate on BoxingVI clips (where the camera angle is comparable); record the results here

## M2 — iOS skeleton
- [ ] Xcode project `ios/Spar` (SwiftUI, iOS 17+), Swift package `ios/SparEngine`
- [ ] Front camera capture + MediaPipe Pose Landmarker (world landmarks) + adapter
- [ ] Debug overlay: skeleton, FPS, inference ms, body-frame axes
- [ ] ≥ 25 fps sustained on iPhone 12 or newer; adapter passes the lead-jab check on device

## M3 — Swift engine port
- [ ] Port `reference/spar_engine` 1:1 (same Config defaults)
- [ ] XCTest loads every `fixtures/*.json` and asserts the same event signature as the Python tests
- [ ] Robustness test ported (seeded noise)

## M4 — Shadowboxing with feedback (no character yet)
- [ ] Live engine on device → HUD (punch counter by type, guard status)
- [ ] Pre-recorded voice cues for guard drop, slow retraction, no head movement, nice combo
- [ ] Round timer (3 × 2 min, 45 s rest), end-of-round stats
- [ ] Latency measured end to end; < 200 ms target

## M5 — The coach appears + mitt work
- [ ] Rigged character in RealityKit composited beside the user, scaled and placed from body detection
- [ ] Gaze: the coach looks at the user's head every frame
- [ ] Animations: idle bounce, mitts up, mitt recoil per punch type, demo combo, celebrate, disappointed
- [ ] Mitt-work mode with combo calling + ComboJudge + mitt-pop audio
- [ ] Hallway test: 3 people say it feels like the coach is watching them

## M6 — Defence drill
- [ ] Coach attack animations (telegraph + jab/cross/hook) synced to `Attack` scheduling
- [ ] Evaded / blocked / hit reactions; difficulty ramps attack speed
- [ ] Engine tweak if needed: suppress `slip` during the user's own rear-hand punches

## M7 — Personality + test
- [ ] Session director: levels, warm-up, mixed rounds
- [ ] LLM between rounds: summary, one focus point, chat ("make it harder")
- [ ] Recorder mode (pose + labels, local, opt-in)
- [ ] TestFlight with 5–10 boxers; measure against the SPEC success metrics
