# iOS

| Path | What it is |
|---|---|
| `SparEngine/` | Swift package, pure-logic port of `reference/spar_engine`. So far: types + the MediaPipe adapter (M2). The engine itself is M3. Its tests load `../../fixtures/` |
| `Spar/` | The app (Xcode project, SwiftUI, iOS 17+). M2 = a debug screen: camera, skeleton, FPS, inference time, body-frame axes, lead-jab check |
| `MediaPipeTasks/` | MediaPipe's official Swift package manifest (release 1.1.1), vendored so SwiftPM downloads only the prebuilt binaries instead of cloning the whole MediaPipe repo. Binaries are pinned by checksum |

This code was written without a Mac or Swift toolchain, so the first build may need small fixes.

## First run (Mac with Xcode 15+)

1. `cd ios/SparEngine && swift test` (the adapter tests run on the shared fixtures).
2. Open `ios/Spar/Spar.xcodeproj`. Xcode resolves the two local packages. The first time,
   it downloads the MediaPipe binaries from dl.google.com (a few hundred MB).
3. Target **Spar** → Signing & Capabilities: pick your team. If the bundle ID
   `app.spar.Spar` is taken, change it.
4. Build to an iPhone (not the simulator: there's no front camera there). The **Bundle pose model**
   build phase runs `scripts/fetch_model.sh`. That downloads `pose_landmarker_full.task` once into
   `Spar/Models/` (git-ignored), checks its SHA-256 and copies it into the app. It's the same model
   file that `reference/tools/analyze_video.py` uses.

## Pipeline

```
CameraCapture (front camera, 1280×720 @ 30 fps, BGRA, rotated upright, NOT mirrored)
  └─► PoseService (MediaPipe Pose Landmarker full, live stream, GPU)
        └─► MediaPipeAdapter (SparEngine, mirrored: false) → PoseFrame in the body frame
              └─► DebugModel → DebugScreen
```

The preview on screen is mirrored like a selfie view. The buffers MediaPipe sees are not.
Both settings are explicit, in `PipelineConfig` and `CameraPreviewView`. All tunables are in
`Spar/PipelineConfig.swift`. If the GPU delegate misbehaves, set `delegate = .CPU` there.

## On-device checks for M2 (human)

Setup as in `docs/SPEC.md`: phone at chest height, 2.5–3 m away, portrait, knees up in frame.

1. **Skeleton lines up** with your body on the mirrored preview. The yellow **L** label sits on
   your *left* wrist. Raise your left hand to check: it's on the left of the screen, like a mirror.
2. **Body-frame panel** (bottom left):
   - *front* view: your right shoulder is toward the red +x arrow, your head is up.
   - *top* view: punch toward the phone and the wrist moves along the green +z arrow (down the panel).
3. **Lead-jab check** (bottom right): pick your stance and throw a few jabs with your lead hand.
   It must say **Lead hand ✓**, and the lead counter must go up.
   - "Rear hand" means the mirroring is wrong (`PipelineConfig.mirroredBuffers`).
   - If neither bar moves when you punch, z is flipped.
   - If the bars move but never cross the white line, note the peak reach value
     and adjust `jabReachSW`.
4. **FPS**: leave it running ≥ 30 s while you shadowbox. "Worst 1 s" must be ≥ 25 fps on an
   iPhone 12 or newer. Note the phone model, the worst-1 s FPS and the inference ms in
   `docs/ROADMAP.md`.
