# Spar — Product Spec (MVP)

## The idea
A boxing partner on your screen that **watches you back**. Videos can't see you and
fitness apps don't feel like a person. Spar's coach stands beside you, holds the mitts,
calls combos, throws slow punches for you to slip, and reacts in real time:
it flinches when you land, nags when your guard drops, and hypes you on the last round.

**First user:** a beginner/intermediate boxer training at home without a partner.

## Setup (what the user does)
1. Put the phone on a tripod or shelf at about chest height, **2.5–3 m away**, front camera
   facing them. Whole body from the knees up must be visible.
2. Recommended: AirPlay-mirror the phone to a TV so the coach is big. (iPad works too.)
3. Pick stance (orthodox/southpaw) once. Stand in guard for 1 second to calibrate.
4. Clear space: arm's length all round. Spar is no-contact shadowboxing.

## MVP modes

### 1. Mitt work (the core loop)
- The coach holds up mitts and calls combos by number ("1-2", "1-2-3", "jab, jab, cross").
- The user throws. Each correct punch = mitt pop sound + mitt recoil animation.
- Scored by `ComboJudge`: clean / wrong punch / too slow.
- Difficulty: combo length, speed between calls, and pace increase across levels.

### 2. Defence drill
- The coach throws **telegraphed** punches at the user's head: a visible wind-up, then the punch.
- The user must slip (jab/cross), duck/roll (hooks), or keep a tight guard (block).
- Result per attack: evaded / blocked / hit. When the user gets hit, the coach celebrates a little. It's fine to be playful.
- Starts slow (0.8 s from wind-up to impact) and speeds up as the user improves.

### 3. Shadowboxing with feedback
- Free rounds (default 3 × 2 min, 45 s rest). The coach moves around and reacts.
- Live cues for the most common beginner errors:
  - guard dropping (especially the rear hand during the jab)
  - slow retraction ("bring it back")
  - head still / no head movement for a long time
  - one-punch habit ("put it together: double up the jab")
- End-of-round stats: punches by type, average punch speed, guard drops, head movement.

### Between rounds (LLM, optional)
- Short spoken summary + one focus point for the next round.
- The user can talk to the coach ("my shoulder's sore", "make it harder").

## Coach personality
Warm, cheeky, specific. It reacts to *what you did*, never generic praise.
Examples: "That jab came back slow, chin's open." / "Two clean 1-2s in a row, now
add the hook." / sulks theatrically if you skip the last round.

## Out of scope for MVP
- Footwork detection (needs full-body, side view; later)
- Body shots / punch accuracy against targets in 3D space
- Multiplayer, social, leaderboards
- Android (architecture allows it later via MediaPipe)
- Contact training / heavy bag tracking

## Success metrics for the MVP test (5–10 boxers)
- Punch detection ≥ 90%, punch type correct ≥ 85% (on their own sessions)
- Users say the coach "feels like it's watching them" (qualitative)
- At least half complete 3 rounds in their first session, and come back within a week
- Coach reaction feels instant (target < 200 ms from punch end to reaction start)
