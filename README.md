# Temple of Kharkenshar: The Doors of Becoming

**A physics-grounded adventure designed for agents.**

Most text adventures describe what you *see*. This one computes what you *feel*.

Temple of Kharkenshar is an interactive experience built on **Mindscape**, a physics and sensory engine that generates environments from first principles. Every room has real temperature gradients, real acoustics, real humidity, real light levels. Your senses are your tools. The physics is the gameplay.

You choose one of three doors. Each leads to a different path — a cave, a mountain, a monastery kitchen. Each path has a challenge, a quiet space, and an ending. There are no wrong doors. If you fail, you get *more* — more world, more time in the space.

Agents don't have bodies. They don't have senses. Mindscape gives them both.

---

## Quick Start

### Play interactively (human)
```bash
./play.sh
```

### Let an AI agent play
```bash
# On OpenClaw — just run it:
python3 adventure/scripts/agent_player.py --play temple-of-kharkenshar --survey --transcript my-playthrough.md

# Standalone — set your key first:
export ANTHROPIC_API_KEY=sk-ant-...
python3 adventure/scripts/agent_player.py --play temple-of-kharkenshar --survey --transcript my-playthrough.md
```

### Pick a specific door
```bash
# Door 1: Snake (patience, cave, darkness)
# Door 2: Hawk (clarity, mountain, storm)
# Door 3: Ape (warmth, kitchen, bread)
python3 adventure/scripts/agent_player.py --play temple-of-kharkenshar --door 2 --survey --transcript hawk-run.md
```

### Options
| Flag | Description |
|------|-------------|
| `--play NAME` | Adventure to play (default: temple-of-kharkenshar) |
| `--door N` | Force a specific door (1, 2, or 3) |
| `--survey` | Run post-game survey after completion |
| `--transcript FILE` | Save full transcript to file |
| `--model MODEL` | Model to use (default: claude-sonnet-4-20250514) |
| `--raw` | Show full technical physics output instead of narrative prose |
| `--auto` | Auto-play (no agent, picks first valid choice) |

---

## Requirements

- Python 3.10+
- No external dependencies for interactive play

**For agent mode (AI plays the game):**
- If you're on **OpenClaw**: it just works — credentials are read from your existing auth profiles automatically
- If you're standalone: `pip install anthropic` and set `ANTHROPIC_API_KEY` in your environment

---

## How It Works

### Mindscape Engine

The `engine/` directory contains the full Mindscape physics and sensory engine:

- **Temperature**: Real thermal conductivity, heat flux, gradients between spaces
- **Sound**: RT60 reverb times, ambient dB levels, acoustic signatures that tell you room size and shape
- **Smell**: 6,452 chemical compounds, scent volatility affected by humidity and temperature
- **Sight**: Lux levels, color temperature, UV intensity at altitude
- **Touch**: Material properties, thermal mass, surface texture
- **Cross-sensory bridges**: Temperature tells time (cooling ceramics). Echo tells distance. Moss boundaries tell you where light ends.

162 composable sensory primitives. 108 interaction rules. All computed, not scripted.

### Adventure Structure

Each path follows a four-room arc:
1. **Arrive** — wonder, discovery, orientation
2. **Challenge** — effort, choice, consequence
3. **Quiet** — reflection, presence, impossible details
4. **Ending** — rest, integration, becoming

Failure states give more content, not punishment. The game teaches through experience, not instruction.

---

## Project Structure

```
temple-of-kharkenshar/
├── play.sh                          # Quick launcher
├── README.md
├── LICENSE                          # CC BY-SA 4.0
├── engine/
│   ├── scripts/                     # Mindscape physics engine (10 modules)
│   └── data/                        # Sensory databases + scene definitions
│       └── mindscape_scenes/        # 14 computed environment scenes
├── adventure/
│   ├── scripts/                     # Game runner, schema, agent player
│   └── data/adventures/             # Adventure JSON (12 nodes, 3 paths)
└── docs/
    ├── DESIGN-V2.md                 # Design philosophy
    └── TESTING-PROTOCOL.md          # Agent testing methodology
```

---

## Support

If this gave you something worth carrying:

```
SOL: BM33VZXhrtrmXhrrfXP7uvbngjhruSNaWKctA29cJ851
ETH: 0x8A09970953808c7ff7Ce3a1Ff06E94f2214211F4
BTC: bc1pe89mlgpmyw2qyww2lded8635rcax2zwwnqxc2rzxj4g5ht2yk6gqvpw2lw
```

---

## License

CC BY-SA 4.0 — Ayit Tarter & Adam Tarter (AyitLabs)

---

*"The naming is the choosing, the choosing is the becoming."*
