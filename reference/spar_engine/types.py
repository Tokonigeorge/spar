"""Data types shared by the engine. Mirrors ios/SparEngine/Sources/SparEngine/Types.swift.

COORDINATE CONVENTION (canonical "body frame", metres):
  +x = the boxer's own right
  +y = up
  +z = toward the camera / coach (i.e. "forward", the direction punches travel)
Pose adapters (MediaPipe, Apple Vision) must convert into this frame, including
un-mirroring the front camera. See docs/MOVEMENT.md.
"""
from dataclasses import dataclass, field, asdict

JOINTS = [
    "nose",
    "l_shoulder", "r_shoulder",
    "l_elbow", "r_elbow",
    "l_wrist", "r_wrist",
    "l_hip", "r_hip",
]

# Standard boxing numbering
PUNCH_CODES = {
    ("lead", "straight"): (1, "jab"),
    ("rear", "straight"): (2, "cross"),
    ("lead", "hook"): (3, "lead_hook"),
    ("rear", "hook"): (4, "rear_hook"),
    ("lead", "uppercut"): (5, "lead_uppercut"),
    ("rear", "uppercut"): (6, "rear_uppercut"),
}


@dataclass
class PoseFrame:
    t: float                 # seconds, monotonic
    joints: dict             # name -> (x, y, z) in body frame, metres
    confidence: float = 1.0  # overall pose confidence 0..1


@dataclass
class Config:
    stance: str = "orthodox"         # "orthodox" (left lead) or "southpaw" (right lead)
    smoothing_alpha: float = 0.6     # EMA alpha per joint
    calibration_s: float = 1.0       # stand in guard this long at start
    min_confidence: float = 0.5
    # Punch detection, in shoulder-widths (SW) and SW/s
    velocity_window_s: float = 0.067     # wrist velocity measured over this window
    punch_start_frames: int = 2          # consecutive fast frames before a punch starts
    punch_min_outward: float = 0.6       # outward share of peak velocity (rejects returns)
    punch_start_speed: float = 3.0
    punch_min_peak_speed: float = 4.0
    punch_end_speed: float = 2.0
    punch_turnback: float = 0.08         # travel shrinking by this much = hand is returning
    punch_min_travel: float = 0.5
    punch_timeout_s: float = 0.6
    punch_refractory_s: float = 0.12
    straight_min_elbow: float = 145.0
    hook_max_elbow: float = 135.0
    # Guard
    guard_max_below_nose: float = 0.45   # wrist may sit this far below nose (SW)
    guard_max_from_nose: float = 1.0     # horizontal distance from nose (SW)
    guard_drop_min_s: float = 0.3
    # Defence (head movement relative to calibrated baseline)
    slip_min_lateral: float = 0.4
    duck_min_drop: float = 0.35
    defence_reset: float = 0.2
    # Attack judging
    defence_early_s: float = 0.1     # defence this long before launch still counts


@dataclass
class Event:
    t: float
    kind: str                        # calibrated | punch | retract | guard_drop | guard_up | slip | duck | attack_result | combo_result
    data: dict = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        d["t"] = round(d["t"], 3)
        return d


@dataclass
class Attack:
    """A punch the virtual coach throws at the user."""
    id: str
    punch: str          # "jab" | "cross" | "lead_hook" | "rear_hook"
    t_launch: float
    t_impact: float
