"""Pose adapter: raw MediaPipe world landmarks -> body frame, on the shared adapter fixtures.

The Swift port must pass an equivalent test (ios/SparEngine/Tests/SparEngineTests/AdapterTests.swift)
on the same files. Run:  python tests/test_adapter.py
"""
import glob, json, os, sys
from types import SimpleNamespace

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from spar_engine import mediapipe_to_body_frame  # noqa: E402
from test_fixtures import run, signature  # noqa: E402

FIXTURES = os.path.join(HERE, "..", "..", "fixtures")
ADAPTER_FIXTURES = sorted(glob.glob(os.path.join(FIXTURES, "adapter", "*.json")))
TOL = 1e-9


def landmarks(world):
    """{"index": [x, y, z, visibility]} -> list of 33 landmark objects."""
    lms = [SimpleNamespace(x=0.0, y=0.0, z=0.0, visibility=0.0) for _ in range(33)]
    for i, (x, y, z, v) in world.items():
        lms[int(i)] = SimpleNamespace(x=x, y=y, z=z, visibility=v)
    return lms


def adapt(fx, mirrored):
    frames, confs = [], []
    for f in fx["frames"]:
        joints, conf = mediapipe_to_body_frame(landmarks(f["world"]), mirrored)
        frames.append({"t": f["t"], "joints": joints}); confs.append(conf)
    return frames, confs


def first_punch(events):
    return next(e.data for e in events if e.kind == "punch")


def check(path):
    fx = json.load(open(path))
    src = json.load(open(os.path.join(FIXTURES, fx["source"])))
    frames, confs = adapt(fx, fx["mirrored"])
    errors = []
    assert len(frames) == len(src["frames"])
    for got, want in zip(frames, src["frames"]):
        for name, w in want["joints"].items():
            g = got["joints"][name]
            if max(abs(a - b) for a, b in zip(g, w)) > TOL:
                errors.append(f't={got["t"]} {name}: got {g}, want {w}')
    if any(abs(c - fx["expected_confidence"]) > 1e-6 for c in confs):
        errors.append(f"confidence {confs[0]} != {fx['expected_confidence']}")
    # Lead-jab sanity check through the real engine
    stream = {"stance": src["stance"], "frames": frames, "attacks": [], "combos": []}
    events, _ = run(stream)
    if signature(events) != signature(src["expected"]):
        errors.append(f"events {signature(events)} != {signature(src['expected'])}")
    p = first_punch(events)
    if (p["hand"], p["punch"]) != ("lead", "jab"):
        errors.append(f"lead-jab check failed: {p}")
    # With the wrong mirroring flag the same jab must come out as the rear hand,
    # which is exactly the mistake the on-device check is there to catch.
    wrong, _ = adapt(fx, not fx["mirrored"])
    events, _ = run({**stream, "frames": wrong})
    if first_punch(events)["hand"] != "rear":
        errors.append("wrong mirroring flag was not detected by the lead-jab check")
    return errors


def test_adapter_fixtures():
    assert ADAPTER_FIXTURES, "no adapter fixtures - run reference/tools/make_adapter_fixtures.py"
    for p in ADAPTER_FIXTURES:
        errors = check(p)
        assert not errors, f"{os.path.basename(p)}: " + "; ".join(errors[:5])


if __name__ == "__main__":
    bad = 0
    for p in ADAPTER_FIXTURES:
        errors = check(p)
        print(("PASS " if not errors else "FAIL ") + "adapter/" + os.path.basename(p))
        for e in errors[:5]:
            print("  " + e)
        bad += bool(errors)
    sys.exit(1 if bad else 0)
