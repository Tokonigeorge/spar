"""Run every fixture through the engine and compare against its expected events.

The Swift port must pass an equivalent test (ios/SparEngine/Tests) on the same files.
Run:  cd reference && python -m pytest -q   (or: python tests/test_fixtures.py)
"""
import glob, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from spar_engine import SparEngine, ComboJudge, Config, PoseFrame, Attack  # noqa: E402

FIXTURES = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "..", "fixtures", "*.json")))
KEYS = {"punch": "punch", "guard_drop": "hand", "guard_up": "hand", "slip": "direction", "attack_result": "result"}


def run(fx):
    eng = SparEngine(Config(stance=fx["stance"]))
    for a in fx["attacks"]:
        eng.schedule_attack(Attack(**a))
    judges = [(c, ComboJudge(c["combo"], c["t_called"])) for c in fx["combos"]]
    events, combo_results = [], []
    for f in fx["frames"]:
        evs = eng.update(PoseFrame(f["t"], {k: tuple(v) for k, v in f["joints"].items()}))
        events += evs
        for c, j in judges:
            for e in evs:
                r = j.on_event(e)
                if r: combo_results.append((c, r))
            r = j.tick(f["t"])
            if r: combo_results.append((c, r))
    return events, combo_results


def signature(evs):
    out = []
    for e in evs:
        d = e if isinstance(e, dict) else {"kind": e.kind, **e.data}
        if d["kind"] == "retract":
            continue
        k = KEYS.get(d["kind"])
        out.append(f'{d["kind"]}:{d[k]}' if k else d["kind"])
    return out


def check(path):
    fx = json.load(open(path))
    events, combos = run(fx)
    got, want = signature(events), signature(fx["expected"])
    ok = got == want
    for c, r in combos:
        ok = ok and r.data["result"] == c["expected_result"]
    if len(combos) != len(fx["combos"]):
        ok = False
    return ok, got, want, combos


def test_all_fixtures():
    assert FIXTURES, "no fixtures - run reference/tools/make_fixtures.py"
    for p in FIXTURES:
        ok, got, want, combos = check(p)
        assert ok, f"{os.path.basename(p)}\n got: {got}\nwant: {want}\ncombos: {[(c['combo'], r.data) for c, r in combos]}"


if __name__ == "__main__":
    bad = 0
    for p in FIXTURES:
        ok, got, want, combos = check(p)
        print(("PASS " if ok else "FAIL ") + os.path.basename(p))
        if not ok:
            bad += 1
            print("  got: ", got); print("  want:", want)
            for c, r in combos: print("  combo", c["combo"], r.data)
    sys.exit(1 if bad else 0)
