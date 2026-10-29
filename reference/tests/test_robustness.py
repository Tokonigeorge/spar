"""Noise robustness: the full move set must be detected exactly under realistic jitter.
Phone pose estimators jitter roughly 0.5-2 cm; we require a clean result at 1.5 cm."""
import importlib.util, os, sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from test_fixtures import run, signature  # noqa: E402

spec = importlib.util.spec_from_file_location("mf", os.path.join(HERE, "..", "tools", "make_fixtures.py"))
mf = importlib.util.module_from_spec(spec); spec.loader.exec_module(mf)


def full_session():
    s = mf.Script(); s.expect("calibrated"); s.hold(1.2)
    mf.all_punches(s); mf.defence(s); mf.guard(s); s.hold(0.6)
    return s


def test_noise_15mm():
    s = full_session()
    for seed in range(15):
        fx = {"stance": "orthodox", "frames": s.frames(0.015, seed), "attacks": [], "combos": []}
        events, _ = run(fx)
        assert signature(events) == signature(s.expected), f"seed {seed}: {signature(events)}"


if __name__ == "__main__":
    test_noise_15mm(); print("PASS noise 15mm x15 seeds")
