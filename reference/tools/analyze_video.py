"""Run a recorded video through MediaPipe Pose -> SparEngine and print the events.

This is the tuning loop: record yourself (or a coach) shadowboxing, run this, and
compare the events with what actually happened. Adjust Config thresholds, repeat.
It also exports the pose stream as a fixture-style JSON so a session can become a
regression test once you've written its `expected` list by hand.

Setup:
  pip install mediapipe opencv-python
  curl -L -o pose_landmarker_full.task \
    https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task

Usage:
  python reference/tools/analyze_video.py session.mp4 --model pose_landmarker_full.task \
      [--stance orthodox|southpaw] [--mirrored] [--export fixtures/my_session.json]

--mirrored: pass this for selfie-style (front camera) recordings that are mirrored.
SANITY CHECK the first time: throw one jab with your lead hand; the output must say
hand=lead. If it says rear, the mirroring flag is wrong.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from spar_engine import SparEngine, Config, PoseFrame, mediapipe_to_body_frame  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--model", required=True)
    ap.add_argument("--stance", default="orthodox"); ap.add_argument("--mirrored", action="store_true")
    ap.add_argument("--export", help="write a fixture-style JSON of the pose stream")
    a = ap.parse_args()

    import cv2
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions
    from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode

    opts = PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=a.model),
                                 running_mode=RunningMode.VIDEO, num_poses=1)
    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    eng = SparEngine(Config(stance=a.stance))
    frames, i = [], 0
    with PoseLandmarker.create_from_options(opts) as lmk:
        while True:
            ok, img = cap.read()
            if not ok:
                break
            t = i / fps; i += 1
            rgb = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            res = lmk.detect_for_video(rgb, int(t * 1000))
            if not res.pose_world_landmarks:
                continue
            joints, conf = mediapipe_to_body_frame(res.pose_world_landmarks[0], a.mirrored)
            frames.append({"t": round(t, 4), "joints": {k: [round(c, 5) for c in v] for k, v in joints.items()}})
            for ev in eng.update(PoseFrame(t, joints, conf)):
                print(json.dumps(ev.to_dict()))
    if a.export:
        json.dump({"name": os.path.splitext(os.path.basename(a.video))[0], "note": "recorded session",
                   "fps": fps, "stance": a.stance, "frames": frames, "attacks": [], "combos": [],
                   "expected": [{"kind": "calibrated"}]}, open(a.export, "w"), separators=(",", ":"))
        print(f"exported {len(frames)} frames -> {a.export} (fill in `expected` by hand)", file=sys.stderr)


if __name__ == "__main__":
    main()
