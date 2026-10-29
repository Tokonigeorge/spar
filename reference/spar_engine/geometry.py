"""Tiny vector helpers. Pure Python so the logic ports 1:1 to Swift (SIMD3<Float>)."""
import math

Vec = tuple  # (x, y, z)


def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def norm(a): return math.sqrt(dot(a, a))
def dist(a, b): return norm(sub(a, b))
def lerp(a, b, t): return add(a, mul(sub(b, a), t))
def mid(a, b): return lerp(a, b, 0.5)


def angle_deg(a, vertex, c):
    """Angle at `vertex` formed by a-vertex-c, in degrees (e.g. elbow angle)."""
    u, v = sub(a, vertex), sub(c, vertex)
    nu, nv = norm(u), norm(v)
    if nu < 1e-9 or nv < 1e-9:
        return 0.0
    cosv = max(-1.0, min(1.0, dot(u, v) / (nu * nv)))
    return math.degrees(math.acos(cosv))


class EMA:
    """Exponential smoothing for a 3D point. alpha=1 means no smoothing.
    Upgrade path: One Euro filter (see docs/MOVEMENT.md)."""

    def __init__(self, alpha):
        self.alpha = alpha
        self.value = None

    def update(self, p):
        if self.value is None:
            self.value = p
        else:
            self.value = lerp(self.value, p, self.alpha)
        return self.value
