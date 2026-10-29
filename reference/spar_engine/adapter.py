"""Pose adapters: pose-model output -> SparEngine body frame (see types.py, docs/MOVEMENT.md).

Mirrors ios/SparEngine/Sources/SparEngine/PoseAdapter.swift. Shared test data:
fixtures/adapter/*.json (Python: tests/test_adapter.py, Swift: AdapterTests).
"""

# MediaPipe Pose landmark indices (anatomical left/right of the person)
MP_INDEX = {"nose": 0, "l_shoulder": 11, "r_shoulder": 12, "l_elbow": 13, "r_elbow": 14,
            "l_wrist": 15, "r_wrist": 16, "l_hip": 23, "r_hip": 24}


def mediapipe_to_body_frame(world_landmarks, mirrored=False):
    """MediaPipe world landmarks (metres, origin at hips, x=image right, y=down,
    z=smaller is closer to camera) -> (joints, confidence) in the SparEngine body frame
    (+x boxer's right, +y up, +z toward camera).

    For a person facing an unmirrored camera, their right side is on the image's
    left, so body x = -image x. A mirrored image flips that AND MediaPipe's left/right
    labels, so we swap the labels back and keep image x.

    `world_landmarks` is indexable by landmark index; each item has .x .y .z and
    optionally .visibility (None counts as 0, an absent attribute as 1).
    """
    joints, vis = {}, []
    for name in MP_INDEX:
        src = name
        if mirrored and name[:2] in ("l_", "r_"):
            src = ("r_" if name[:2] == "l_" else "l_") + name[2:]
        lm = world_landmarks[MP_INDEX[src]]
        x = lm.x if mirrored else -lm.x
        joints[name] = (x, -lm.y, -lm.z)
        vis.append(getattr(lm, "visibility", 1.0) or 0.0)
    return joints, sum(vis) / len(vis)
