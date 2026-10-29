"""ComboJudge: checks the user's punches against a called combination, e.g. "1-2-3"."""
from .types import Event


class ComboJudge:
    def __init__(self, combo, t_called, max_first_s=1.5, max_gap_s=0.9):
        self.expected = [int(c) for c in combo.split("-")]
        self.t_called = t_called
        self.max_first_s = max_first_s
        self.max_gap_s = max_gap_s
        self.thrown = []          # (t, code)
        self.done = False

    def on_event(self, ev: Event):
        """Feed engine events; returns a combo_result Event when the combo resolves."""
        if self.done:
            return None
        if ev.kind == "punch" and ev.t >= self.t_called:
            last = self.thrown[-1][0] if self.thrown else self.t_called
            limit = self.max_gap_s if self.thrown else self.max_first_s
            if ev.t - last > limit:
                return self._finish(ev.t, "too_slow")
            self.thrown.append((ev.t, ev.data["code"]))
            i = len(self.thrown) - 1
            if self.thrown[i][1] != self.expected[i]:
                return self._finish(ev.t, "wrong_punch")
            if len(self.thrown) == len(self.expected):
                return self._finish(ev.t, "clean")
        return None

    def tick(self, t):
        """Call every frame so a combo that is never finished times out."""
        if self.done:
            return None
        last = self.thrown[-1][0] if self.thrown else self.t_called
        limit = self.max_gap_s if self.thrown else self.max_first_s
        if t - last > limit:
            return self._finish(t, "too_slow" if self.thrown else "no_response")
        return None

    def _finish(self, t, result):
        self.done = True
        return Event(t, "combo_result", {
            "expected": "-".join(map(str, self.expected)),
            "thrown": "-".join(str(c) for _, c in self.thrown),
            "result": result,
            "duration_s": round(t - self.t_called, 3),
        })
