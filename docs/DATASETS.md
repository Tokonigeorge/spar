# Datasets

**Bottom line:** public data is for *evaluating and tuning*. The most valuable dataset
will be our own: recorder-mode sessions of real users (and a real coach) shadowboxing
in front of a phone, labelled with what they actually threw.

Always check each dataset's licence. Most are research / non-commercial. Don't ship a
model trained on them commercially without permission.

## Boxing

| Dataset | What it has | How we'd use it |
|---|---|---|
| **BoxingVI** (2025), [arXiv 2511.16524](https://arxiv.org/abs/2511.16524) | Multi-modal benchmark for boxing action recognition and temporal localisation of punches | Best fit: run clips through `analyze_video.py` and measure punch detection/typing. Check the camera angles vs. our front-facing setup |
| **BoxMAC** (2024), [arXiv 2412.18204](https://arxiv.org/abs/2412.18204) | Boxing videos with multi-label action annotations | Extra evaluation clips; label vocabulary for future moves (feints, blocks) |
| Roboflow punch detection guide | Tutorial-level punch detection approach | Sanity reference only |

## Fitness / exercise coaching (for the wider fitness-coach version later)

| Dataset | What it has | Use |
|---|---|---|
| **QEVD** (Qualcomm, 2024), [project page](https://www.qualcomm.com/developer/software/qevd-dataset), [paper](https://arxiv.org/abs/2407.08101) | Large exercise video set incl. a live-coaching subset with timed feedback ("lower your hips") | Closest public match to "coach that reacts". Useful for the cue vocabulary and when to say it |
| **Fitness-AQA** ([arXiv 2202.14019](https://arxiv.org/abs/2202.14019)) | Real gym videos labelled with form errors (squat, overhead press, barbell row) | Form-error rules for a future gym mode |
| **FLEX** ([arXiv 2506.03198](https://arxiv.org/abs/2506.03198)) | Multi-modal, multi-action fitness quality assessment | Same, more exercises |

## Our own data (the plan)
1. **M1:** record 10–20 min of yourself (and ideally your boxing coach) from the real
   phone position. Mix of all six punches, slips, ducks, guard drops.
2. Run `analyze_video.py --export`, write the `expected` list by hand → new fixtures.
3. In-app **recorder mode** (later milestone): users opt in to save pose streams + quick
   labels. Pose only, no video, so it's light and private.
4. Once there are a few hours of labelled sessions, train the learned punch classifier
   (see ARCHITECTURE.md decision 5).
