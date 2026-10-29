# Spar — a boxing partner that lives in your room

A virtual coach that stands beside you on screen, holds the mitts, calls combos,
throws slow punches for you to slip, and **reacts to what you actually do**:
it sees your punches, your guard, and your head movement through the phone camera.

Built for someone learning to box who doesn't always have a partner.

## What's in this repo right now

| Path | What it is | Status |
|---|---|---|
| `docs/SPEC.md` | Product: modes, user flow, what the MVP is and isn't | ✅ |
| `docs/ARCHITECTURE.md` | App architecture and the key technical decisions | ✅ |
| `docs/MOVEMENT.md` | How punches, guard and defence are detected (rules + coordinate frame) | ✅ |
| `docs/DATASETS.md` | Public fitness/boxing datasets and how to use them | ✅ |
| `docs/ROADMAP.md` | Milestones with acceptance criteria | ✅ |
| `reference/spar_engine/` | **Reference movement engine (Python)**: the source of truth for detection logic | ✅ tested |
| `reference/tests/` | Fixture tests + noise-robustness test | ✅ passing |
| `reference/tools/make_fixtures.py` | Generates synthetic boxing sequences + expected events | ✅ |
| `reference/tools/analyze_video.py` | Runs a recorded video through MediaPipe → engine, for tuning | ✅ (needs the model file) |
| `fixtures/*.json` | Shared test data. The Swift engine must pass these too | ✅ |
| `ios/` | iOS app + Swift engine port | ⏳ to build (see ROADMAP) |

## Quick start (reference engine)

```bash
cd reference
python tools/make_fixtures.py        # regenerate fixtures (only if you change the generator)
python tests/test_fixtures.py        # 7 scenarios: punches, combos, defence, guard, coach attacks
python tests/test_robustness.py      # same move set under 1.5 cm pose jitter, 15 seeds
```

Analyse your own recording (see the docstring for the model download):

```bash
python tools/analyze_video.py my_session.mp4 --model pose_landmarker_full.task --mirrored
```

## For the building agent

Read `AGENTS.md` first.
