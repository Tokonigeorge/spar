#!/bin/sh
# Downloads the MediaPipe Pose Landmarker (full) model into ios/Spar/Models/ (git-ignored)
# and, when run from the Xcode build phase, copies it into the app bundle.
# Same model as reference/tools/analyze_video.py, so thresholds tuned there transfer.
set -eu

NAME="pose_landmarker_full.task"
URL="https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/$NAME"
SHA256="5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1"

DIR="$(cd "$(dirname "$0")/.." && pwd)/Models"
MODEL="$DIR/$NAME"

if [ ! -f "$MODEL" ]; then
    mkdir -p "$DIR"
    echo "Downloading $NAME"
    curl -fsSL -o "$MODEL.part" "$URL"
    mv "$MODEL.part" "$MODEL"
fi

ACTUAL="$(shasum -a 256 "$MODEL" | cut -d' ' -f1)"
if [ "$ACTUAL" != "$SHA256" ]; then
    echo "error: $MODEL has sha256 $ACTUAL, expected $SHA256. Delete it and rerun." >&2
    exit 1
fi

# Xcode build phase: copy into the .app
if [ -n "${TARGET_BUILD_DIR:-}" ] && [ -n "${UNLOCALIZED_RESOURCES_FOLDER_PATH:-}" ]; then
    DEST="$TARGET_BUILD_DIR/$UNLOCALIZED_RESOURCES_FOLDER_PATH"
    mkdir -p "$DEST"
    cp "$MODEL" "$DEST/$NAME"
fi
