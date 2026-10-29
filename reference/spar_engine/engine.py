"""SparEngine: turns a stream of 3D pose frames into boxing events.

Pipeline per frame:
  smoothing -> scale (shoulder width) -> calibration -> per-hand punch state machine
  -> guard monitor -> head-movement (defence) monitor -> attack judging.

Everything is rule-based and deterministic so it can be tuned against recorded
sessions and ported to Swift with identical results on fixtures/*.json.
"""
from .geometry import EMA, sub, dist, norm, mid, angle_deg, mul
from .types import Config, Event, PoseFrame, Attack, PUNCH_CODES, JOINTS


class _Hand:
    def __init__(self, side, role):
        self.side = side          # "l" | "r"
        self.role = role          # "lead" | "rear"
        self.state = "idle"       # idle | out
        self.prev_wrist = None
        self.prev_t = None
        self.start_pos = None
        self.start_t = None
        self.peak_speed = 0.0
        self.peak_vel = (0.0, 0.0, 0.0)
        self.max_travel = 0.0
        self.max_elbow = 0.0
        self.emitted = False
        self.last_event_t = -1e9
        self.down_since = None
        self.guard_down = False
        self.history = []         # recent (t, wrist) for windowed velocity
        self.fast_frames = 0
        self.retract_t = -1e9
        self.recovering = False   # hand is still travelling back up after a guard drop


class SparEngine:
    def __init__(self, config=None):
        self.cfg = config or Config()
        self.filters = {j: EMA(self.cfg.smoothing_alpha) for j in JOINTS}
        lead = "l" if self.cfg.stance == "orthodox" else "r"
        rear = "r" if lead == "l" else "l"
        self.hands = {lead: _Hand(lead, "lead"), rear: _Hand(rear, "rear")}
        self.sw = None                 # shoulder width (m), the unit for all thresholds
        self._calib = []
        self.calibrated = False
        self.base_nose = None
        self.head_state = "neutral"    # neutral | slip | duck
        self.defence_log = []          # (t, kind, direction)
        self.attacks = []              # pending Attack objects
        self.t0 = None

    # ------------------------------------------------------------------ API
    def schedule_attack(self, attack: Attack):
        self.attacks.append(attack)

    def update(self, frame: PoseFrame):
        """Feed one frame; returns a list of Events produced by it."""
        if frame.confidence < self.cfg.min_confidence:
            return []
        j = {k: self.filters[k].update(tuple(frame.joints[k])) for k in JOINTS}
        t = frame.t
        if self.t0 is None:
            self.t0 = t
        events = []

        if not self.calibrated:
            self._calib.append(j)
            if t - self.t0 >= self.cfg.calibration_s:
                n = len(self._calib)
                self.sw = sum(dist(f["l_shoulder"], f["r_shoulder"]) for f in self._calib) / n
                xs = [f["nose"] for f in self._calib]
                self.base_nose = tuple(sum(p[i] for p in xs) / n for i in range(3))
                self.calibrated = True
                events.append(Event(t, "calibrated", {"shoulder_width_m": round(self.sw, 3)}))
            for h in self.hands.values():
                h.prev_wrist, h.prev_t = j[f"{h.side}_wrist"], t
            return events

        for h in self.hands.values():
            events += self._update_hand(h, j, t)
        events += self._update_guard(j, t)
        events += self._update_head(j, t)
        events += self._judge_attacks(j, t)
        return events

    # ------------------------------------------------------------ punches
    def _update_hand(self, h, j, t):
        cfg, sw = self.cfg, self.sw
        wrist = j[f"{h.side}_wrist"]
        elbow = j[f"{h.side}_elbow"]
        shoulder = j[f"{h.side}_shoulder"]
        # Windowed velocity: compare with the sample ~velocity_window_s ago.
        # Frame-to-frame differences amplify pose jitter; a ~0.1 s window does not.
        h.history.append((t, wrist))
        while len(h.history) > 2 and t - h.history[1][0] >= cfg.velocity_window_s:
            h.history.pop(0)
        t_old, w_old = h.history[0]
        dt = max(1e-6, t - t_old)
        vel = mul(sub(wrist, w_old), 1.0 / (dt * sw))           # SW/s
        speed = norm(vel)
        h.prev_wrist, h.prev_t = wrist, t
        out = []

        if h.recovering and speed <= cfg.punch_end_speed:
            h.recovering = False
        if h.state == "idle":
            h.fast_frames = h.fast_frames + 1 if speed >= cfg.punch_start_speed else 0
            ready = (t - h.last_event_t >= cfg.punch_refractory_s
                     and t - h.retract_t >= cfg.punch_refractory_s)
            # A hand that has been sitting low (guard dropped) and comes back up is
            # a guard recovery, not an uppercut.
            if h.fast_frames >= cfg.punch_start_frames and ready and not h.guard_down and not h.recovering and self._outward(h, vel) > 0:
                h.state = "out"
                h.start_pos, h.start_t = w_old, t_old
                h.peak_speed, h.peak_vel = speed, vel
                h.max_travel, h.max_elbow, h.emitted = 0.0, 0.0, False
            return out

        # state == "out"
        travel = dist(wrist, h.start_pos) / sw
        h.max_travel = max(h.max_travel, travel)
        h.max_elbow = max(h.max_elbow, angle_deg(shoulder, elbow, wrist))
        if speed > h.peak_speed:
            h.peak_speed, h.peak_vel = speed, vel

        # Extension ends when the hand slows down OR starts coming back (travel shrinking).
        ended = speed <= cfg.punch_end_speed or travel < h.max_travel - cfg.punch_turnback
        if not h.emitted and ended and h.peak_speed >= cfg.punch_min_peak_speed:
            # The extension has ended: classify and emit.
            outward_ok = self._outward(h, h.peak_vel) >= cfg.punch_min_outward * h.peak_speed
            if h.max_travel >= cfg.punch_min_travel and outward_ok:
                out.append(self._classify(h, t))
                h.emitted = True
                h.last_event_t = t
            else:
                h.state = "idle"          # too small: a twitch, not a punch
                return out
        elif not h.emitted and ended:
            h.state = "idle"              # slow movement, never fast enough
            return out

        if h.emitted:
            # Wait for the hand to come back to guard
            if self._hand_in_guard(j, h.side):
                out.append(Event(t, "retract", {"hand": h.role, "return_s": round(t - h.last_event_t, 3)}))
                h.state = "idle"
                h.retract_t = t
            elif t - h.last_event_t > cfg.punch_timeout_s:
                h.state = "idle"
        elif t - h.start_t > cfg.punch_timeout_s:
            h.state = "idle"
        return out

    @staticmethod
    def _outward(h, vel):
        """Largest 'away from the body' velocity component (forward, across, or up).
        A hand coming back to guard has none of these, so it can't start a punch."""
        across = vel[0] if h.side == "l" else -vel[0]
        return max(vel[2], across, vel[1])

    def _classify(self, h, t):
        cfg = self.cfg
        vx, vy, vz = h.peak_vel
        across = vx if h.side == "l" else -vx      # toward the body's midline
        fwd, up = vz, vy
        if up > 0 and up >= max(fwd, across):
            shape = "uppercut"
        elif across >= fwd and h.max_elbow <= cfg.hook_max_elbow + 25:
            shape = "hook"
        elif fwd > 0 and h.max_elbow >= cfg.straight_min_elbow:
            shape = "straight"
        elif across >= fwd:
            shape = "hook"
        else:
            shape = "unknown"
        code, name = PUNCH_CODES.get((h.role, shape), (0, "unknown"))
        other = "r" if h.side == "l" else "l"
        return Event(t, "punch", {
            "hand": h.role, "punch": name, "code": code, "shape": shape,
            "t_start": round(h.start_t, 3),
            "peak_speed_sw": round(h.peak_speed, 2),
            "travel_sw": round(h.max_travel, 2),
            "max_elbow_deg": round(h.max_elbow, 1),
            "other_hand_guard": not self.hands[other].guard_down,
        })

    # -------------------------------------------------------------- guard
    def _hand_in_guard(self, j, side):
        nose, wrist = j["nose"], j[f"{side}_wrist"]
        below = (nose[1] - wrist[1]) / self.sw
        horiz = norm((wrist[0] - nose[0], 0.0, wrist[2] - nose[2])) / self.sw
        return below <= self.cfg.guard_max_below_nose and horiz <= self.cfg.guard_max_from_nose

    def _update_guard(self, j, t):
        out = []
        for h in self.hands.values():
            if h.state == "out":          # punching hands are not "dropped"
                h.down_since = None
                continue
            if self._hand_in_guard(j, h.side):
                h.down_since = None
                if h.guard_down:
                    h.guard_down = False
                    h.recovering = True
                    out.append(Event(t, "guard_up", {"hand": h.role}))
            else:
                if h.down_since is None:
                    h.down_since = t
                if not h.guard_down and t - h.down_since >= self.cfg.guard_drop_min_s:
                    h.guard_down = True
                    out.append(Event(t, "guard_drop", {"hand": h.role}))
        return out

    # ------------------------------------------------------------ defence
    def _update_head(self, j, t):
        cfg, sw = self.cfg, self.sw
        dx = (j["nose"][0] - self.base_nose[0]) / sw
        dy = (self.base_nose[1] - j["nose"][1]) / sw      # positive = lower
        out = []
        if self.head_state == "neutral":
            if dy >= cfg.duck_min_drop:
                self.head_state = "duck"
                out.append(Event(t, "duck", {"drop_sw": round(dy, 2)}))
                self.defence_log.append((t, "duck", None))
            elif abs(dx) >= cfg.slip_min_lateral:
                self.head_state = "slip"
                d = "right" if dx > 0 else "left"
                out.append(Event(t, "slip", {"direction": d, "lateral_sw": round(abs(dx), 2)}))
                self.defence_log.append((t, "slip", d))
        else:
            if abs(dx) < cfg.defence_reset and dy < cfg.defence_reset:
                self.head_state = "neutral"
        return out

    def _judge_attacks(self, j, t):
        out, keep = [], []
        for a in self.attacks:
            if t < a.t_impact:
                keep.append(a)
                continue
            lo, hi = a.t_launch - self.cfg.defence_early_s, a.t_impact
            moves = [d for d in self.defence_log if lo <= d[0] <= hi]
            hooks = a.punch in ("lead_hook", "rear_hook")
            if any(m[1] == "duck" for m in moves) or (moves and not hooks):
                result = "evaded"
            elif all(not h.guard_down for h in self.hands.values()):
                result = "blocked"
            else:
                result = "hit"
            out.append(Event(t, "attack_result", {"id": a.id, "punch": a.punch, "result": result,
                                                   "defence": [m[1] for m in moves]}))
        self.attacks = keep
        return out

