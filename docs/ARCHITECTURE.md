# Architecture

## Pipeline

```
Front camera (AVFoundation, 30–60 fps)
   └─► Pose (MediaPipe Pose Landmarker, world landmarks, on-device)
         └─► Adapter → body frame (docs/MOVEMENT.md)
               └─► SparEngine (Swift port of reference/spar_engine)
                     ├─► events: punch / retract / guard_drop / guard_up / slip / duck / attack_result
                     └─► ComboJudge (mitt work)
                           └─► Session Director (state machine: rounds, drills, difficulty)
                                 ├─► Coach Controller → RealityKit character (animations, gaze)
                                 ├─► Audio (pre-recorded cues, mitt pops, crowd)
                                 └─► HUD (round timer, combo call, stats)
Between rounds only: LLM (summary, chat, plan changes)
```

## Key decisions (and why)

### 1. iPhone first, Swift + SwiftUI
LiDAR is not needed for the MVP, but iPhone is where the target users are, and the
rendering, audio and camera stack is the most predictable there.

### 2. Pose model: MediaPipe Pose Landmarker (full), not Apple Vision
- Gives **3D world landmarks in metres** in real time. Straight punches travel toward the
  camera, so 2D keypoints alone can't see them well. Depth is essential.
- The **same model runs in the Python tuning tool** (`reference/tools/analyze_video.py`),
  so thresholds tuned on a laptop transfer directly to the phone.
- Cross-platform later (Android).
- Alternative to evaluate in M2: Apple Vision `VNDetectHumanBodyPose3DRequest`. Only
  switch if it's clearly better on device, and if so, re-tune on real recordings.

### 3. Front camera + composited coach ("pseudo-AR"), not ARKit world tracking
ARKit world tracking doesn't run on the front camera, and the user must see the screen
while being filmed. So:
- Show the (mirrored) camera feed full-screen.
- Render the coach with RealityKit in a non-AR view layered on top, placed beside the
  user. Position and scale come from the user's detected body (hip midpoint and
  shoulder width in image space), so the coach stands "on the same floor" at a plausible size.
- The coach faces/looks at the user's head position every frame. This gaze is a big
  part of the "it's watching me" feeling.
- Later option: rear camera + ARKit + the user watches a TV via AirPlay, for true AR with
  occlusion and environment lighting.

### 4. Deterministic engine, LLM only off the critical path
Detection and coach reactions are rules + state machines → predictable, testable,
instant. The LLM adds personality between rounds where 1–3 s of latency is fine.

### 5. Rules first, learned model later
Hand-written rules on joint angles and velocities ship fast and are explainable.
Once we have a few hours of labelled real sessions (recorder mode), train a small
temporal classifier on pose sequences (e.g. 1D-CNN/GRU over 0.5 s windows, Core ML)
for punch typing. Keep rules for guard/head-movement unless proven worse.

## Latency budget (punch end → coach starts reacting)

| Stage | Budget |
|---|---|
| Camera frame delivery | ≤ 33 ms |
| Pose inference | ≤ 40 ms |
| Engine + director | ≤ 5 ms |
| Animation blend start + audio | ≤ 50 ms |
| Engine detection delay (needs a few frames after the punch peaks) | ~70–100 ms |
| **Total target** | **< 200 ms** |

Measure it in M4 with an on-screen timestamp test (film the screen with a second phone).

## Modules (Swift)

| Module | Responsibility |
|---|---|
| `SparEngine` (Swift package) | Pure logic port. No UIKit/AVFoundation imports. Fixture-tested. |
| `PoseService` | Camera capture + MediaPipe + adapter → `PoseFrame` stream |
| `SessionDirector` | Modes, rounds, combo calling, attack scheduling, difficulty |
| `CoachController` | Maps events/director intents → animations, gaze, voice |
| `CoachView` | RealityKit scene + compositing over the camera feed |
| `AudioCues` | Pre-recorded voice lines + SFX, low-latency playback |
| `Recorder` | Saves pose streams + user labels as fixture-format JSON |
| `CoachChat` | LLM between rounds (summary, chat, plan changes) |

## Assets
- Character: start with a free rigged humanoid + Mixamo animations (boxing idles, jab,
  hook, block, dodge, mitt-holding poses, celebrate). Replace with a custom character later.
- Voice: pre-generate ~150 cue lines with one TTS voice; store as audio files.
