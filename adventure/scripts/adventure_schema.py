#!/usr/bin/env python3
"""
adventure_schema.py — Data model for Mindscape adventures (v2).

An adventure is a graph of nodes (scenes) connected by choices.
Challenges replace puzzles — experiential situations with failure states,
not keyword-matching riddles.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Choice:
    """A choice the player can make at a node."""
    text: str              # What the player sees: "Enter the door of the Snake"
    hint: str              # Sensory preview: "Cold air. Silence. The dark waits."
    target_node: str       # Node ID this leads to

    @classmethod
    def from_dict(cls, d: dict) -> "Choice":
        return cls(
            text=d["text"],
            hint=d.get("hint", ""),
            target_node=d["target_node"],
        )


@dataclass
class FailureState:
    """What happens when the agent picks a wrong option in a challenge."""
    option_keywords: list[str]       # Keywords that trigger this failure
    narration: str                   # What the agent experiences (physics-grounded)
    nudge: str                       # Contextual hint after the failure
    sensory_details: dict = field(default_factory=dict)  # Extra physics to render

    @classmethod
    def from_dict(cls, d: dict) -> "FailureState":
        return cls(
            option_keywords=d.get("option_keywords", []),
            narration=d.get("narration", ""),
            nudge=d.get("nudge", ""),
            sensory_details=d.get("sensory_details", {}),
        )


@dataclass
class Challenge:
    """An experiential challenge — a situation, not a quiz.
    
    The agent faces a situation and responds freely. Responses are routed
    based on which option they chose (via keyword matching). Wrong choices
    lead to failure states with physics-rendered consequences and retries.
    Right choices lead to the next node.
    """
    situation_text: str                    # What's happening — the prompt
    correct_keywords: list[str]            # Keywords that indicate the right choice
    success_narration: str                 # What the agent feels when right
    failure_states: list[FailureState]     # Ordered failure experiences
    max_attempts: int = 3                  # After this, pass them through anyway
    pass_through_text: str = ""            # Text when they pass through after max failures

    @classmethod
    def from_dict(cls, d: dict) -> "Challenge":
        failures = [FailureState.from_dict(f) for f in d.get("failure_states", [])]
        return cls(
            situation_text=d["situation_text"],
            correct_keywords=d.get("correct_keywords", []),
            success_narration=d.get("success_narration", ""),
            failure_states=failures,
            max_attempts=d.get("max_attempts", 3),
            pass_through_text=d.get("pass_through_text", ""),
        )

    def evaluate(self, answer: str, attempt: int) -> tuple[bool, str]:
        """Evaluate a free-text response. Returns (passed, narration).
        
        For wrong answers, cycles through failure states to give different
        experiences each time. After max_attempts, passes them through.
        """
        answer_lower = answer.lower()
        
        # Check for correct answer
        if any(kw.lower() in answer_lower for kw in self.correct_keywords):
            return True, self.success_narration
        
        # Wrong answer — which failure state?
        if attempt >= self.max_attempts:
            return True, self.pass_through_text or "The path opens despite you."
        
        # Check if any specific failure state matches
        for fs in self.failure_states:
            if any(kw.lower() in answer_lower for kw in fs.option_keywords):
                return False, f"{fs.narration}\n\n{fs.nudge}"
        
        # Generic failure — use the failure state by attempt number
        if self.failure_states:
            idx = min(attempt, len(self.failure_states) - 1)
            fs = self.failure_states[idx]
            return False, f"{fs.narration}\n\n{fs.nudge}"
        
        return False, "Something doesn't feel right. Try again."


@dataclass
class AdventureNode:
    """A single node in the adventure graph."""
    id: str
    scene_id: str                          # Points to a mindscape scene
    arrival_text: str                      # Narration on entry
    room_type: str = "standard"            # "arrive", "challenge", "quiet", "meadow", "standard"
    prompt: str = ""                       # What to ask the agent ("What do you notice?" etc.)
    choices: list[Choice] = field(default_factory=list)
    challenge: Optional[Challenge] = None
    reward_text: str = ""                  # For terminal nodes
    terminal: bool = False
    transition_hints: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "AdventureNode":
        choices = [Choice.from_dict(c) for c in d.get("choices", [])]
        challenge = Challenge.from_dict(d["challenge"]) if d.get("challenge") else None
        return cls(
            id=d["id"],
            scene_id=d["scene_id"],
            arrival_text=d.get("arrival_text", ""),
            room_type=d.get("room_type", "standard"),
            prompt=d.get("prompt", ""),
            choices=choices,
            challenge=challenge,
            reward_text=d.get("reward_text", ""),
            terminal=d.get("terminal", False),
            transition_hints=d.get("transition_hints", {}),
        )


@dataclass
class Adventure:
    """A complete adventure — a graph of nodes connected by choices."""
    id: str
    title: str
    opening_text: str
    nodes: dict[str, AdventureNode]
    start_node: str
    agent_framing: str = ""  # The prompt that tells an agent what this is

    @classmethod
    def from_dict(cls, d: dict) -> "Adventure":
        nodes = {}
        for node_data in d.get("nodes", []):
            node = AdventureNode.from_dict(node_data)
            nodes[node.id] = node
        return cls(
            id=d["id"],
            title=d["title"],
            opening_text=d.get("opening_text", ""),
            nodes=nodes,
            start_node=d["start_node"],
            agent_framing=d.get("agent_framing", ""),
        )

    @classmethod
    def load(cls, path: Path) -> "Adventure":
        """Load an adventure from a JSON file."""
        with open(path) as f:
            return cls.from_dict(json.load(f))

    def validate(self) -> list[str]:
        """Check for broken references. Returns list of errors."""
        errors = []
        if self.start_node not in self.nodes:
            errors.append(f"Start node '{self.start_node}' not found in nodes")
        for node_id, node in self.nodes.items():
            for choice in node.choices:
                if choice.target_node not in self.nodes:
                    errors.append(f"Node '{node_id}' choice targets '{choice.target_node}' which doesn't exist")
        return errors


ADVENTURES_DIR = Path(__file__).parent.parent / "data" / "adventures"


def list_adventures() -> list[Adventure]:
    """List all available adventures."""
    if not ADVENTURES_DIR.exists():
        return []
    adventures = []
    for f in sorted(ADVENTURES_DIR.glob("*.json")):
        try:
            adventures.append(Adventure.load(f))
        except Exception as e:
            print(f"Warning: Could not load {f.name}: {e}")
    return adventures


def load_adventure(name: str) -> Optional[Adventure]:
    """Load an adventure by name."""
    path = ADVENTURES_DIR / f"{name}.json"
    if path.exists():
        return Adventure.load(path)
    # Fuzzy match
    for f in ADVENTURES_DIR.glob("*.json"):
        if name.lower() in f.stem.lower():
            return Adventure.load(f)
    return None
