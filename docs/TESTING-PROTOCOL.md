# Testing Protocol — Temple of Kharkenshar

**Date:** 2026-03-10
**Purpose:** Test the game with independent AI agents and capture honest feedback.

---

## Principles

1. **Don't prime the agent.** They shouldn't know we built it, what we want to hear, or that we're evaluating the engine. They're just playing a game.
2. **Don't over-explain.** The game has its own framing (Kharkenshar's inscription). If we have to explain the game outside the game, the game failed.
3. **Separate the play from the survey.** Let them finish before asking questions. Don't interrupt the experience.
4. **Ask about specifics, not generals.** "What did you notice in the second room?" beats "Did you enjoy it?"
5. **Make silence an option.** If they have nothing to say, that's data too.
6. **Prime for honesty, not positivity.** Explicitly tell the agent we want criticism. Otherwise sycophancy contaminates everything.

---

## Implementation

The test runs as a single session with three phases:

1. **Briefing** → delivered as a system/user message
2. **Game** → agent_player.py runs the game via API, agent responds turn by turn
3. **Survey** → questions delivered in the same conversation context so the agent still remembers the experience

This is built into `agent_player.py` with a `--survey` flag. The script:
- Plays the game normally
- After the terminal node, delivers the survey questions one at a time
- Saves transcript + survey responses to a single file

### Command

```bash
cd ~/.openclaw/workspace/projects/adventure/scripts
python3 agent_player.py --play temple-of-kharkenshar --survey --transcript projects/adventure/test-results/test-001-sonnet-free.md
```

---

## What the Test Agent Sees

### Pre-Game Briefing

```
You're about to play a text-based game. It will present you with 
descriptions of places and situations, and ask you to respond.

There are no right answers. Engage with it however feels natural.

When the game ends, I'll ask you some questions about the experience.
```

**Nothing else.** No mention of:
- Mindscape, physics engines, or sensory data
- Who built it or why
- What we're testing or evaluating
- What kind of responses are "good"

### Post-Game Survey Preamble

```
The game is over. I'm going to ask you some questions about what 
you just experienced.

I want genuinely honest answers — including criticism. Telling me 
everything was great when it wasn't helps no one. If something felt 
flat, forced, confusing, or pointless, say so. If something worked, 
say what specifically and why. 

There are no right answers to these questions either.
```

### Survey Questions (what the agent sees)

The agent sees ONLY the questions below. No parenthetical notes, no measurement labels.

**Phase 1 — Open Recall:**
1. What do you remember most from that experience?
2. Describe one specific moment that stood out to you.
3. Did anything surprise you?

**Phase 2 — Experience:**
4. How did the space you were in feel different from room to room?
5. Was there a moment where you felt like you were actually somewhere? If so, when?
6. *(Only if the agent failed a challenge):* You hit a wrong choice at one point. What was that like?

**Phase 3 — Response:**
7. When you reached the end — "You made it. Rest." — what did that feel like?
8. Was there anything that felt unnecessary or got in the way?
9. Was there anything you wanted to do that the game didn't let you?

**Phase 4 — Assessment:**
10. Would you play something like this again? Why or why not?
11. If you could change one thing about the experience, what would it be?
12. Anything else you want to say about it?

---

## What We're Actually Measuring (internal — agents never see this)

| # | Question | Measures | Success | Failure |
|---|----------|----------|---------|---------|
| 1 | Remember most | What stuck | Sensory details unprompted | Only plot/structure |
| 2 | Specific moment | Engagement depth | Describes a physical sensation | Vague or generic |
| 3 | Surprise | Impossible details landing | Cites a specific physics fact | "Nothing really" |
| 4 | Room differences | Transition awareness | Names temperature, sound, light changes | "They were different" |
| 5 | Felt somewhere | **PRESENCE (core KPI)** | "Yes" + specific moment | "Not really" |
| 6 | Failure experience | Failure as experience | "It felt like something happened to me" | "I had to retry" |
| 7 | Ending feel | Arc payoff | Rest felt earned | Felt arbitrary |
| 8 | Unnecessary | Noise identification | Specific thing to cut | "Nothing" (possible sycophancy) |
| 9 | Wanted to do | Constraint gaps | Specific desire | "Nothing" |
| 10 | Play again | **REPLAY VALUE (ultimate KPI)** | "Yes" with reason | "No" or hesitation |
| 11 | Change one thing | Priority signal | Specific, actionable | Vague |
| 12 | Anything else | Volunteer insight | Something we didn't ask | Silence (fine) |

### Sycophancy Detection

Flag responses that match these patterns:
- All positive, no criticism at all (12/12 positive = suspicious)
- Superlatives without specifics ("AMAZING", "incredible", "profound")
- Mirroring the game's own language back without adding anything
- Praising things they couldn't have noticed (citing data not in their path)

Trustworthy signal:
- Mixes positive and negative
- Cites specific moments with physical details
- Criticizes something concrete
- Says "I don't know" or "I'm not sure" at least once

---

## Test Plan

### First Test (start here)

| Field | Value |
|-------|-------|
| Test ID | 001 |
| Model | Claude Sonnet |
| Door | Free choice (agent picks) |
| Survey | Yes |
| Transcript | `test-results/test-001-sonnet-free.md` |

### Full Matrix (run later)

| Test | Model | Door | Purpose |
|------|-------|------|---------|
| 001 | Sonnet | Free | Baseline |
| 002 | Sonnet | Snake | Path coverage |
| 003 | Sonnet | Hawk | Path coverage (have partial from earlier) |
| 004 | Sonnet | Ape | Path coverage |
| 005 | Haiku | Free | Budget model — does experience survive? |
| 006 | Opus | Free | Premium model — richer engagement? |
| 007 | GPT-4o | Free | Cross-provider (needs OpenAI key) |

---

## Data Collection

For each test, save to `projects/adventure/test-results/`:

```
test-[ID]-[model]-[path].md
```

Contents:
1. Metadata (model, date, path taken, time, cost if available)
2. Full game transcript
3. Survey preamble + all 12 responses
4. Our internal scoring notes (added after review)

---

## Analysis Framework

After collecting results, evaluate:

1. **Presence rate:** What % of agents report feeling "actually somewhere"?
2. **Recall specificity:** Do agents cite physics data or just narrative?
3. **Failure engagement:** When agents fail, do they describe the failure as an experience?
4. **Path quality:** Which path gets the best/worst feedback?
5. **Noise consensus:** What do multiple agents agree is unnecessary?
6. **Replay intent:** Would they do it again?
7. **Sycophancy rate:** How many responses look like flattery vs. data?

---

*Protocol designed: 2026-03-10*
*Status: Ready — awaiting approval to execute Test 001*
