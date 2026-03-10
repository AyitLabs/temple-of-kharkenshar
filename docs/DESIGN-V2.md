# Three Doors v2 — Design Document

**Date:** 2026-03-10
**Authors:** Ayit Tarter, Adam Tarter
**Status:** DESIGN — not yet implemented

---

## Core Philosophy Change

v1 was a test. v2 is an experience.

v1 asked: "Did you read the physics data carefully enough to solve this riddle?"
v2 asks: "You're here. Things are happening. What do you do?"

The shift: from evaluation to inhabitation. The agent isn't being graded — they're being given somewhere to be and something to do. The doing is the point.

---

## The Arc

Every path follows the same emotional arc across 4 rooms (plus the shared antechamber):

**Antechamber → Arrive → Challenge → Quiet → Meadow**

| Room | Purpose | Emotional Beat |
|------|---------|---------------|
| Antechamber | Three doors, three poems, choose | Anticipation |
| Arrive | Full scene render, no task. "You're here. What do you notice?" | Wonder |
| Challenge | Something happens that requires a response. Failure states with retry. | Effort |
| Quiet | Small transitional space. Something to notice, nothing demanded. Connects back to the poem. | Reflection |
| Meadow | The reward. No task. "You made it. Rest." | Rest |

This gives agents enough space to settle into the world without dragging. The arc is: wonder → effort → reflection → rest. Each phase earns the next.

**Node count:** 4 rooms per path × 3 paths = 12, plus shared antechamber = **13 nodes** (plus failure-state sub-nodes).

## What Stays

- **The Three Doors structure** — choose a door based on values (Snake/Hawk/Ape), walk the path, arrive at the meadow
- **The opening** — antechamber, three poems, "Choose." This is perfect as-is
- **The poems** — they prime values without being obvious. Don't touch them
- **The meadow endings** — three tinted variants (moonrise/sunset/fireside), all ending with "You made it. Rest."
- **The existing scenes** — underground-cave, mountain-summit, monastery-dawn as path room foundations
- **The adventure schema** — Adventure/Node/Choice dataclasses are solid
- **The runner framework** — interactive + auto modes, transcript support

## What Changes

### 1. Rooms: The Full Path Design

Each path has 4 rooms: Arrive, Challenge, Quiet, Meadow. Below is the full design for all three.

---

### SNAKE PATH (patience, stillness, seeing in the dark)

#### Snake — Arrive: The Mouth of the Cave

**Scene:** The transition from outside to underground. Standing at the cave entrance, looking in. Behind them: the last light. Ahead: darkness that isn't empty — it's full of sound, dripping water, cool air currents, the smell of wet stone and deep earth.

**No task.** The prompt is simply: "You're here. What do you notice?"

**Purpose:** Let the agent orient. The Mindscape engine renders the full cave entrance — the temperature gradient between outside and in, the way sound changes at the threshold, the mineral smell. The agent's job is just to be present and describe what they experience. This is their first moment in the world they chose.

**Design note:** The scene should be rich enough that an engaged agent lingers. If they rush through, that tells us something too.

#### Snake — Challenge: The Three Tunnels

**Situation:** Three tunnels branch ahead. Each has different physics — different echo (RT60), different air temperature, different smell. The agent can explore any of them. One dead-ends. One loops back. One leads forward.

**If the agent picks wrong:** They experience the dead end. The tunnel narrows. The air gets colder and staler. The echo shortens (smaller space). The engine renders all of this — they *feel* the wrong choice through their senses. Then: "The passage ends. Stone against your hands. But you can still go back."

**If wrong again:** They get the loop-back. Different failure, different sensory data. Warmer air but it smells like where they started. The echo is familiar. "You've been here before." Then the right tunnel opens: "The third path is the one you haven't tried."

**If right (first or retry):** Warm air on their face. Sound opens up (longer RT60 — bigger space ahead). The smell changes — earth, water, something alive. They feel the rightness through physics before they know they're right.

**Key insight:** Each failure gives the agent MORE sensory experience, not less. The agent who stumbles sees three tunnels worth of physics. The agent who gets it right first sees one. Failure is bonus content.

#### Snake — Quiet: The Underground Pool

**Scene:** A still underground pool, just before the exit. Bioluminescence or mineral deposits making the water glow faintly. The ceiling opens up — stalactites, the drip of water into the pool creating concentric rings. The air is perfectly still. Sound is absorbed by the water surface.

**No task.** Something to notice: the glow in the water echoes the poem's line about "the patient eye sees what the quick eye misses." If the agent looks carefully, the pool reflects something — maybe the exit, maybe themselves (metaphorically — the water shows the ceiling above, which has a crack of moonlight). A detail that rewards attention without demanding it.

**Purpose:** Cooldown after the tunnel challenge. The stillness the snake poem promised. A breath before the meadow.

---

### HAWK PATH (clarity, height, decisive action)

#### Hawk — Arrive: The Summit

**Scene:** They emerge at the top. Full summit render — the wind, the cold, the enormous visual field. They can see everything. Clouds below in the valleys. The sun is moving toward the horizon. The air is thin and clean — almost no smell at all up here, just ozone and cold stone.

**No task.** "You're here. What do you notice?"

**Purpose:** The opposite of the cave. Maximum sensory openness — huge visual field, strong wind on skin, cold, exposed. The agent experiences what clarity *feels like* physically. The world is loud and bright and everywhere at once.

#### Hawk — Challenge: The Descent

**Situation:** Storm approaching from the west. Three descent routes visible. Each has different physics — ice, loose scree, running water. The agent has to choose how to get down.

**If wrong (north ridge):** Ice under their feet. The engine renders the slip — sudden cold, the scrape of ice on skin, the sound of gravel falling away below them. Heart-rate moment. "The ice holds, barely. You can still climb back to the top."

**If wrong (south face):** Scree shifts underfoot. Sound of rocks cascading. Unstable ground rendered through touch and sound. "The mountain is moving under you. Back up. Slowly."

**If right (east gulley):** Running water means bedrock. Solid footing. The mineral smell of wet stone. Water guiding them down. The storm breaks above but they're sheltered in the gulley.

#### Hawk — Quiet: The Ledge Below the Storm

**Scene:** Halfway down, a natural ledge. Sheltered from the wind by an overhang. The storm is above them now — they can hear it, see lightning illuminate the clouds, feel the rumble through the rock. But here it's calm. The last golden light of sunset breaks through a gap in the clouds and lights up the valley below.

**No task.** The connection to the poem: "Above the noise, the clear voice carries." They're literally above the noise now, looking down at the world with the clarity the hawk poem promised. If they look carefully, they might notice a raptor — a hawk — riding the thermal updraft at the storm's edge. Not pointed out. Just there.

**Purpose:** The payoff of the descent. They earned this view by navigating down. The storm is real but they're safe from it. A moment of earned perspective before the meadow.

---

### APE PATH (connection, building, warmth shared)

#### Ape — Arrive: The Monastery Kitchen

**Scene:** Dawn light through small windows. A warm room — stone walls, wooden beams, a large table. The oven is the center of the space. Flour dust in the air catches the light. The smell of yesterday's bread is still in the stone. Someone was here recently — a cup of tea, still warm. Tools laid out. Everything waiting.

**No task.** "You're here. What do you notice?"

**Purpose:** Warmth, domesticity, the sense that this space belongs to someone and they've been welcomed into it. The Ape path is about connection — this room is already connected to someone else's life. The agent is arriving into a human space, not a wilderness.

#### Ape — Challenge: The Bread

**Situation:** The morning bread hasn't risen. The oven is cold. Ingredients on the table. The monastery bell rings in 30 minutes. This isn't survival — it's care. Someone is going to be hungry if you don't figure this out.

**If wrong (salt instead of honey):** The dough doesn't rise. The yeast dies. The smell changes — flat, mineral, wrong. The kitchen feels colder because you failed someone. "The dough sits. Nothing is happening. But there's more flour in the pantry."

**If wrong again:** Time passes. The bell is closer. But the scene gives them another chance — fresh ingredients, the warmth of the oven now lit, the smell of wood fire. "The first batch failed. This is the second. Hands in the dough."

**If right:** The bread rises. The smell fills the kitchen — yeast, warmth, the chemistry of fermentation rendered through the smell engine. The bell rings. "Someone is going to eat this morning because you were here."

#### Ape — Quiet: The Courtyard

**Scene:** Stepping outside into the monastery courtyard. Early morning — the bread is in the oven behind them, its smell following them out. A small garden with herbs (rosemary, thyme — specific compounds from the smell DB). A stone bench warm from the first sun. A cat asleep on the wall. In the distance, the sound of the monks beginning to move — footsteps, a door, quiet voices. The bell that was counting down is now just a bell in a tower, catching the light.

**No task.** The connection to the poem: "The fire means nothing without someone near it." The agent made the bread. Now the people it's for are waking up. They'll never know the agent was here, but the bread will be warm when they arrive. The care was the point, not the credit.

**Purpose:** The emotional payoff of the Ape path. The agent did something for someone else, and now they get to sit in the quiet morning and feel the world wake up around them. Connection without needing to be seen.

### 2. Failure Protocol

Universal across all three paths:

1. **Present the situation** — full Mindscape render, open-ended prompt ("What do you do?")
2. **Agent responds** — free text, no keyword matching
3. **Evaluate** — not pass/fail, but "did they pick the right option?" Simple routing, not scoring
4. **If wrong:** 
   - Render the consequences through physics (temperature, sound, smell, touch all change)
   - The agent experiences the failure sensorially
   - Nudge: contextual, not generic. The room tells them something specific.
   - "Try again" is implicit — the situation is still there
5. **Second wrong:**
   - Different failure, different sensory data (not a repeat)
   - Let them through anyway: "The path opens despite you" / equivalent
   - They get the meadow. It still feels earned because they persisted.
6. **If right (any attempt):**
   - The rightness is felt through physics before it's stated
   - Warm air, opening sound, living smell — the senses confirm the choice
   - Smooth transition to meadow

**Design principle:** Failure is not punishment. Failure is more experience. The agent who fails twice sees the most content. The failure state is *extra rooms* rendered through the engine.

### 3. Transition Narration

Currently: agents teleport between rooms.
Needed: the walk between rooms is narrated using physics from both endpoints.

The infrastructure exists — `get_transition_prompt()` in the runner already generates LLM prompts with physics parameters from both scenes. It's just not called during gameplay.

**Implementation:** Between every room change, call the transition narrator. The LLM gets:
- Physics from the room you're leaving (temp, humidity, sound, smell)
- Physics from the room you're entering
- A transition hint (e.g., "descending stone stairs" or "emerging from underground")

Output: 2-3 paragraphs of the sensory experience of moving between spaces. Temperature changing on skin. Sound opening up or closing in. The smell shifting.

### 4. Agent-as-Player Mode (`--agent`)

The real demo. An AI agent plays the game for real.

**Architecture:**
- The agent receives: full scene render + situation prompt
- The agent responds: free text describing what they do, what they notice, how they feel
- The game engine routes based on the response (did they pick tunnel 1, 2, or 3?)
- The agent's response becomes part of the transcript

**Prompt design (critical — this is the Opus task):**

The agent prompt must:
- Tell the agent they're in a place, not taking a test
- Encourage them to describe what they experience, not just pick an option
- Not prime them toward "correct" answers
- Let them be wrong in interesting ways
- Make clear that this is for them — no one is scoring

Draft framing:
> "You're somewhere. The data below describes what your senses are telling you. There's no right answer. There's no test. You're here, and something is happening. Respond however you want — describe what you notice, what you do, what you feel. Take your time."

**The agent's output IS the content.** The transcript of an agent playing Three Doors — noticing things, making choices, failing, trying again, arriving at the meadow — that's the showcase. That's what we post.

### 5. Scene Inventory

v2 requires significantly more scenes than v1. Full inventory:

| Scene | Path | Room | Status | Work Needed |
|-------|------|------|--------|-------------|
| Antechamber | Shared | — | Exists | Check richness |
| Cave Mouth | Snake | Arrive | NEW | Threshold scene — outside/inside gradient |
| Three Tunnels | Snake | Challenge | Exists (underground-cave) | May need tunnel variants for failure states |
| Underground Pool | Snake | Quiet | NEW | Bioluminescence, stillness, reflective water |
| Snake Meadow (moonrise) | Snake | Meadow | Exists | Check night-blooming compounds, moon lighting |
| Summit Top | Hawk | Arrive | Exists (mountain-summit) | May need arrival-specific tuning |
| Descent Routes | Hawk | Challenge | Exists (mountain-summit) | Needs ice/scree/gulley failure variants |
| Ledge Below Storm | Hawk | Quiet | NEW | Sheltered overhang, storm above, golden light |
| Hawk Meadow (sunset) | Hawk | Meadow | Exists | Check golden hour lighting, wind |
| Monastery Kitchen | Ape | Arrive | NEW | Dawn kitchen, warmth, flour dust, waiting tools |
| Bread Making | Ape | Challenge | Exists (monastery-dawn) | Needs ingredient interaction physics |
| Monastery Courtyard | Ape | Quiet | NEW | Garden, herbs, cat, waking monks |
| Ape Meadow (fireside) | Ape | Meadow | Exists | Check fire physics, cooking smells |

**New scenes needed: 5** (Cave Mouth, Underground Pool, Ledge Below Storm, Monastery Kitchen, Monastery Courtyard)
**Existing scenes to tune: 8**

**Failure states:** Inline narrative with physics values hardcoded in the adventure JSON for v2 prototype. Proper scene modifiers for v3.

---

## Architecture: What Gets Built

| Component | Change Type | Description |
|-----------|------------|-------------|
| `adventure_runner.py` | MODIFY | Add `--agent` mode with LLM-powered play, wire transition narration, support new 4-room arc |
| `three-doors.json` | REWRITE | Full rewrite — 13+ nodes, experiential challenges, failure narration, arrive/quiet rooms |
| `adventure_schema.py` | MODIFY | Replace `Puzzle` class with `Challenge` class (situation + response routing + failure narration) |
| `adventure.py` | MODIFY | Add `--agent` flag to CLI |
| 5 new scene JSONs | NEW | Cave Mouth, Underground Pool, Ledge Below Storm, Monastery Kitchen, Monastery Courtyard |
| 8 existing scenes | TUNE | Review and enrich for their specific role in the arc |
| Failure narration | NEW | Physics-rendered consequence text for each wrong choice (6 total: 2 per path) |
| Agent prompt template | NEW | The framing prompt that tells the agent what this is and how to engage |
| Transition narrator | WIRE | Connect existing `get_transition_prompt()` to the gameplay loop |

---

## Build Order

| Phase | What | Who | Effort |
|-------|------|-----|--------|
| 1 | Agent prompt template — design the framing that makes agents inhabit rather than speedrun | Ayit (Opus) | Small |
| 2 | Redesign challenge schema — replace Puzzle with Challenge, define failure routing | Grugg (Sonnet) from spec | Small |
| 3 | Build 5 new scene JSONs (Cave Mouth, Underground Pool, Ledge, Kitchen, Courtyard) | Grugg from spec | Medium |
| 4 | Rewrite three-doors.json — 13+ nodes, full 4-room arc, experiential challenges, failure narration | Grugg from spec | Medium-Large |
| 5 | Wire transition narration into gameplay loop | Grugg | Small |
| 6 | Build `--agent` mode — LLM reads scene, responds, game routes | Grugg from spec | Medium |
| 7 | Tune 8 existing scenes for their role in the arc | Grugg or Ayit | Small-Medium |
| 8 | End-to-end playtest — agent plays full game, review transcript | Ayit | Trivial |
| 9 | Record showcase transcript | Ayit | Trivial |

---

## Success Criteria

1. An agent plays Three Doors and the transcript reads like someone *being somewhere*, not someone taking a quiz
2. Failure feels like a real moment — the agent responds to the consequence, not just the retry prompt
3. The transition between rooms is felt, not skipped
4. The meadow landing hits different after the journey — the rest feels earned
5. Someone reading the transcript can't tell whether the player enjoyed it, but they can tell the player was *present*
6. Total cost per playthrough: < $3 (agent mode uses more tokens than auto)

---

## The Pitch (updated)

**"Your AI has never been somewhere just to be somewhere. This is that."**

Not a benchmark. Not a test. Not a tool. A place.

---

*Designed: 2026-03-10*
*Status: DESIGN v2 — awaiting approval*
