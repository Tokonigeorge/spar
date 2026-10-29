"""Generate synthetic pose sequences + the events we EXPECT the engine to emit.

These fixtures are the contract between the Python reference engine and the Swift
port: both must produce the expected events for every file in fixtures/.
Synthetic data proves the logic; real recorded sessions (docs/DATASETS.md) tune it.

Usage:  python reference/tools/make_fixtures.py   (writes ../../fixtures/*.json)
"""
import json, math, os, random, sys

FPS = 30
L_UP, L_FORE = 0.30, 0.27          # upper arm, forearm (m)
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures")

# Orthodox guard, body frame (+x boxer's right, +y up, +z toward camera)
BASE = {
    "nose": (0.0, 1.62, 0.05),
    "l_shoulder": (-0.20, 1.45, 0.0), "r_shoulder": (0.20, 1.45, 0.0),
    "l_hip": (-0.15, 1.00, 0.0), "r_hip": (0.15, 1.00, 0.0),
}
GUARD = {"l": (-0.10, 1.55, 0.22), "r": (0.10, 1.55, 0.18)}
POLE_DOWN = {"l": (-0.5, -1.0, 0.0), "r": (0.5, -1.0, 0.0)}
POLE_HOOK = {"l": (-1.0, 0.4, -0.2), "r": (1.0, 0.4, -0.2)}


def v_add(a, b): return tuple(x + y for x, y in zip(a, b))
def v_sub(a, b): return tuple(x - y for x, y in zip(a, b))
def v_mul(a, k): return tuple(x * k for x in a)
def v_dot(a, b): return sum(x * y for x, y in zip(a, b))
def v_norm(a): return math.sqrt(v_dot(a, a))
def v_lerp(a, b, t): return v_add(a, v_mul(v_sub(b, a), t))
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def elbow_ik(S, W, pole):
    d_vec = v_sub(W, S); d = min(v_norm(d_vec), L_UP + L_FORE - 1e-4)
    u = v_mul(d_vec, 1 / max(v_norm(d_vec), 1e-9))
    a = (L_UP ** 2 - L_FORE ** 2 + d ** 2) / (2 * d)
    h = math.sqrt(max(0.0, L_UP ** 2 - a ** 2))
    p = v_sub(pole, v_mul(u, v_dot(pole, u))); p = v_mul(p, 1 / max(v_norm(p), 1e-9))
    return v_add(v_add(S, v_mul(u, a)), v_mul(p, h))


class Script:
    """Keyframe-ish script: each segment animates wrist targets / body offset."""

    def __init__(self):
        self.t = 0.0
        self.segments = []   # (t0, t1, fn(progress)->state-patch)
        self.wrist = dict(GUARD)
        self.pole = dict(POLE_DOWN)
        self.body = (0.0, 0.0, 0.0)
        self.expected = []
        self.attacks = []
        self.combos = []

    def hold(self, dur):
        w, p, b = dict(self.wrist), dict(self.pole), self.body
        self.segments.append((self.t, self.t + dur, lambda k, w=w, p=p, b=b: (w, p, b)))
        self.t += dur

    def move(self, dur, wrist=None, pole=None, body=None):
        w0, b0 = dict(self.wrist), self.body
        w1 = dict(w0); w1.update(wrist or {})
        p1 = dict(self.pole); p1.update(pole or {})
        b1 = body if body is not None else b0
        def fn(k, w0=w0, w1=w1, p1=p1, b0=b0, b1=b1):
            s = smooth(k)
            return ({h: v_lerp(w0[h], w1[h], s) for h in "lr"}, p1, v_lerp(b0, b1, s))
        self.segments.append((self.t, self.t + dur, fn))
        self.t += dur
        self.wrist, self.pole, self.body = w1, p1, b1

    def expect(self, kind, **data):
        self.expected.append({"kind": kind, **data})

    # ---- boxing moves -------------------------------------------------
    def punch(self, side, target, pole, name, out=0.12, back=0.18):
        self.move(out, wrist={side: target}, pole={side: pole})
        self.hold(0.05)
        self.expect("punch", punch=name)
        self.move(back, wrist={side: GUARD[side]}, pole={side: POLE_DOWN[side]})

    def jab(self):
        self.punch("l", v_add(BASE["l_shoulder"], (0.12, 0.08, 0.55)), POLE_DOWN["l"], "jab")

    def cross(self):
        self.punch("r", v_add(BASE["r_shoulder"], (-0.18, 0.08, 0.53)), POLE_DOWN["r"], "cross")

    def lead_hook(self):
        self.punch("l", (0.12, 1.47, 0.32), POLE_HOOK["l"], "lead_hook", out=0.14)

    def rear_hook(self):
        self.punch("r", (-0.12, 1.47, 0.30), POLE_HOOK["r"], "rear_hook", out=0.14)

    def rear_uppercut(self):
        self.move(0.2, wrist={"r": (0.12, 1.36, 0.20)})          # load (slow)
        self.punch("r", (-0.02, 1.60, 0.30), (0.0, -1.0, 0.0), "rear_uppercut", out=0.12)

    def guard_drop(self, side="l"):
        self.move(0.4, wrist={side: (-0.18 if side == "l" else 0.18, 1.15, 0.10)})
        self.expect("guard_drop", hand="lead" if side == "l" else "rear")
        self.hold(0.6)
        self.move(0.4, wrist={side: GUARD[side]})
        self.expect("guard_up", hand="lead" if side == "l" else "rear")

    def slip(self, direction="right", dur=0.2, hold=0.3):
        dx = 0.18 if direction == "right" else -0.18
        self.move(dur, body=(dx, 0.0, 0.0)); self.expect("slip", direction=direction)
        self.hold(hold); self.move(0.25, body=(0.0, 0.0, 0.0))

    def duck(self):
        self.move(0.2, body=(0.0, -0.17, 0.0)); self.expect("duck")
        self.hold(0.3); self.move(0.25, body=(0.0, 0.0, 0.0))

    # ---- render -------------------------------------------------------
    def frames(self, noise=0.0, seed=0):
        rnd = random.Random(seed)
        out, n = [], int(self.t * FPS) + 1
        for i in range(n):
            t = i / FPS
            seg = next((s for s in self.segments if s[0] <= t < s[1]), self.segments[-1])
            k = (t - seg[0]) / max(1e-9, seg[1] - seg[0])
            wrist, pole, body = seg[2](min(1.0, k))
            # Head and shoulders move with the body; hips stay planted.
            j = {}
            for name in ("nose", "l_shoulder", "r_shoulder"):
                j[name] = v_add(BASE[name], body)
            for name in ("l_hip", "r_hip"):
                j[name] = BASE[name]
            for h in "lr":
                W = v_add(wrist[h], body)
                j[f"{h}_wrist"] = W
                j[f"{h}_elbow"] = elbow_ik(j[f"{h}_shoulder"], W, pole[h])
            if noise:
                j = {k2: tuple(c + rnd.gauss(0, noise) for c in v) for k2, v in j.items()}
            out.append({"t": round(t, 4), "joints": {k2: [round(c, 5) for c in v] for k2, v in j.items()}})
        return out


def scenario(name, build, noise=0.0, seed=1, note=""):
    s = Script()
    s.expect("calibrated")
    s.hold(1.2)
    build(s)
    s.hold(0.6)
    data = {"name": name, "note": note, "fps": FPS, "stance": "orthodox",
            "frames": s.frames(noise, seed), "attacks": s.attacks, "combos": s.combos,
            "expected": s.expected}
    with open(os.path.join(OUT_DIR, f"{name}.json"), "w") as f:
        json.dump(data, f, separators=(",", ":"))
    return name


def gap(s, d=0.5): s.hold(d)


def all_punches(s):
    for fn in (s.jab, s.cross, s.lead_hook, s.rear_hook, s.rear_uppercut):
        fn(); gap(s)


def combo_12(s):
    s.combos.append({"combo": "1-2", "t_called": round(s.t, 3), "expected_result": "clean"})
    gap(s, 0.3); s.jab(); gap(s, 0.08); s.cross(); gap(s)


def combo_wrong(s):
    s.combos.append({"combo": "1-2-3", "t_called": round(s.t, 3), "expected_result": "wrong_punch"})
    gap(s, 0.3); s.jab(); gap(s, 0.08); s.lead_hook(); gap(s)


def defence(s):
    s.slip("right"); gap(s); s.slip("left"); gap(s); s.duck(); gap(s)


def guard(s):
    s.guard_drop("l"); gap(s)


def attacks(s):
    # 1) coach jabs, user slips in time -> evaded
    t = s.t; s.attacks.append({"id": "a1", "punch": "jab", "t_launch": round(t + 0.1, 3), "t_impact": round(t + 0.5, 3)})
    s.hold(0.15); s.slip("left", dur=0.2, hold=0.4); s.expect("attack_result", id="a1", result="evaded"); gap(s)
    # 2) coach throws a hook, user keeps guard up and does nothing -> blocked
    t = s.t; s.attacks.append({"id": "a2", "punch": "lead_hook", "t_launch": round(t + 0.1, 3), "t_impact": round(t + 0.5, 3)})
    s.hold(0.9); s.expect("attack_result", id="a2", result="blocked")
    # 3) user drops guard, coach jabs -> hit
    s.move(0.4, wrist={"l": (-0.18, 1.15, 0.10)}); s.expect("guard_drop", hand="lead")
    t = s.t; s.attacks.append({"id": "a3", "punch": "jab", "t_launch": round(t + 0.1, 3), "t_impact": round(t + 0.4, 3)})
    s.hold(0.8); s.expect("attack_result", id="a3", result="hit")
    s.move(0.4, wrist={"l": GUARD["l"]}); s.expect("guard_up", hand="lead")


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    made = [
        scenario("punches_clean", all_punches, note="jab, cross, both hooks, rear uppercut; no noise"),
        scenario("punches_noisy", all_punches, noise=0.006, seed=7, note="same as punches_clean with 6 mm joint noise"),
        scenario("combo_1_2", combo_12, note="called 1-2, thrown clean"),
        scenario("combo_wrong", combo_wrong, note="called 1-2-3, user throws 1 then 3 -> wrong_punch"),
        scenario("defence", defence, note="slip right, slip left, duck"),
        scenario("guard_drop", guard, note="lead hand drops for 0.6s then returns"),
        scenario("attacks", attacks, note="coach attacks: evaded / blocked / hit"),
    ]
    print("wrote", ", ".join(made))
