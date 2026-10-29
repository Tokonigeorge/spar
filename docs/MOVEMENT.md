# Movement detection

Implementation: `reference/spar_engine/engine.py` (source of truth). All thresholds live
in `Config` (`reference/spar_engine/types.py`).

## Coordinate frame ("body frame")

| Axis | Direction |
|---|---|
| +x | the boxer's own right |
| +y | up |
| +z | toward the camera / coach (the direction punches travel) |

Units are metres in, but **every threshold is in shoulder-widths (SW)**, measured at
calibration, so the rules work for any body size or distance from the camera.

Joints used: `nose, l/r_shoulder, l/r_elbow, l/r_wrist, l/r_hip` (left/right =
the person's anatomical side).

**Adapter sanity check:** throw one jab with your lead hand. The engine must report
`hand: lead, punch: jab`. If it says rear, the mirroring is wrong.

The MediaPipe adapter is `reference/spar_engine/adapter.py` (Swift: `SparEngine/PoseAdapter.swift`).
`fixtures/adapter/*.json` hold a known sequence as raw MediaPipe world landmarks from an unmirrored
and a mirrored image; both ports must map them back exactly (`tests/test_adapter.py`, `AdapterTests`).
The Python test also runs the result through the engine and checks the jab comes out as the lead hand,
and that the wrong mirroring flag turns it into the rear hand. On the phone, the debug screen has
the same check (without the engine until M3).

## Calibration
The first `calibration_s` (1 s) of frames, standing in guard:
- shoulder width (the unit SW)
- baseline head (nose) position, used for slips and ducks

## Punches (per hand state machine)

```
idle ──(speed ≥ start for 2 frames, moving outward, not recovering)──► out
out  ──(hand slows OR starts coming back)──► classify → emit `punch`
out  ──(hand back in guard zone)──► emit `retract` (with return time) → idle
```

- **Velocity** is measured over a ~67 ms window, not frame-to-frame (jitter).
- **Outward** = forward (+z), across the body toward the midline, or up. A hand
  returning to guard has none, so returns never start a punch.
- **Valid punch:** peak speed ≥ 4 SW/s, travel ≥ 0.5 SW, and ≥ 60% of the peak velocity outward.
- **Classification** by the direction of the velocity at peak speed + max elbow angle:

| Shape | Rule | Lead | Rear |
|---|---|---|---|
| straight | forward-dominant, elbow ≥ 145° | 1 jab | 2 cross |
| hook | across-dominant, elbow ≤ ~160° | 3 lead hook | 4 rear hook |
| uppercut | upward-dominant | 5 lead uppercut | 6 rear uppercut |

Using velocity at peak (not start→end displacement) handles the uppercut's dip/load
before it rises.

## Guard
A hand is "in guard" if it's no more than 0.45 SW below the nose and within 1.0 SW of
it horizontally. `guard_drop` fires after 0.3 s out of guard (punching hands excluded).
`guard_up` fires when it returns. A hand coming back up from a drop is marked
*recovering*, so the lift isn't read as an uppercut.
Each punch event includes `other_hand_guard`, which catches "dropping the rear hand
while jabbing".

## Defence (head movement)
Relative to the calibrated nose position:
- `slip` (left/right): lateral shift ≥ 0.4 SW
- `duck`: drop ≥ 0.35 SW
- Resets when the head is back within 0.2 SW.

## Coach attacks
`Attack{id, punch, t_launch, t_impact}` is scheduled by the Session Director.
At `t_impact`:
- **evaded:** a slip or duck happened between `t_launch − 0.1 s` and impact.
  Hooks need a duck/roll; a slip doesn't count against a hook.
- **blocked:** no evasion, but both hands were in guard
- **hit:** otherwise

## Combos
`ComboJudge("1-2-3", t_called)`: punches must match in order. First punch within
1.5 s of the call, then ≤ 0.9 s between punches. Result: `clean | wrong_punch | too_slow | no_response`.

## Test status
- 7 synthetic fixtures pass (`reference/tests/test_fixtures.py`)
- MediaPipe adapter round-trips both camera setups and passes the lead-jab check (`test_adapter.py`)
- Full move set detected exactly under 1.5 cm joint jitter, 15/15 seeds
  (`test_robustness.py`). At 2 cm, ~90%.
- **Not yet validated on real recordings.** That is milestone M1. Expect to retune:
  real hooks arc, real crosses rotate the head (may need slip suppression during
  rear-hand punches), and the camera angle affects depth estimates.

## Known gaps / next improvements
- Rotate into a torso-aligned frame if users stand very bladed to the camera
- One Euro filter instead of EMA (less lag at the same jitter)
- Footwork, body shots, feints
- Southpaw needs a real-recording fixture (the logic is mirrored via lead/rear roles)
