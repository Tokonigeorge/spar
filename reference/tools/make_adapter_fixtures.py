"""Generate fixtures/adapter/*.json: raw MediaPipe world landmarks for a known body-frame
sequence, so the pose adapter (Python and Swift) can be checked against ground truth.

Each file inverts the adapter for one camera setup: it takes the body-frame frames of
`source` (a regular fixture) and writes what MediaPipe would report for them. Running
the adapter must give back the source joints exactly, and the engine must then emit the
source's `expected` events (the lead jab must come out as hand=lead).

Usage:  python reference/tools/make_adapter_fixtures.py
"""
import json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from spar_engine import MP_INDEX  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures")
SOURCE = "punches_clean.json"
# Per-joint visibility (deterministic, not all equal) so confidence averaging is tested too
VISIBILITY = {"nose": 0.99, "l_shoulder": 0.98, "r_shoulder": 0.97, "l_elbow": 0.9, "r_elbow": 0.8,
              "l_wrist": 0.7, "r_wrist": 0.6, "l_hip": 0.5, "r_hip": 0.4}


def swap_side(name):
    if name[:2] in ("l_", "r_"):
        return ("r_" if name[:2] == "l_" else "l_") + name[2:]
    return name


def to_mediapipe(joints, mirrored):
    """Inverse of spar_engine.adapter.mediapipe_to_body_frame."""
    world = {}
    for name, (x, y, z) in joints.items():
        label = swap_side(name) if mirrored else name
        world[str(MP_INDEX[label])] = [x if mirrored else -x, -y, -z, VISIBILITY[name]]
    return world


def main():
    src = json.load(open(os.path.join(FIXTURES, SOURCE)))
    out_dir = os.path.join(FIXTURES, "adapter")
    os.makedirs(out_dir, exist_ok=True)
    conf = sum(VISIBILITY.values()) / len(VISIBILITY)
    for mirrored in (False, True):
        name = "mediapipe_" + ("mirrored" if mirrored else "unmirrored")
        fx = {"name": name,
              "note": f"{SOURCE} as MediaPipe world landmarks from a {'mirrored' if mirrored else 'unmirrored'} image",
              "source": SOURCE, "mirrored": mirrored, "expected_confidence": round(conf, 6),
              "frames": [{"t": f["t"], "world": to_mediapipe(f["joints"], mirrored)} for f in src["frames"]]}
        path = os.path.join(out_dir, name + ".json")
        json.dump(fx, open(path, "w"), separators=(",", ":"))
        print("wrote", os.path.relpath(path))


if __name__ == "__main__":
    main()
