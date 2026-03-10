#!/usr/bin/env python3
"""
adventure_runner.py — Runtime for Mindscape adventures (v2).

Renders scenes, presents choices, handles experiential challenges,
generates transitions between rooms. Supports interactive, auto, and
agent-driven play modes.
"""

import sys
import json
from pathlib import Path

# Add mindscape scripts to path for scene rendering
# Mindscape engine path — relative to repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MINDSCAPE_SCRIPTS = REPO_ROOT / "engine" / "scripts"
sys.path.insert(0, str(MINDSCAPE_SCRIPTS))

from adventure_schema import Adventure, AdventureNode, load_adventure, list_adventures
from mindscape import MindscapeEngine
from mindscape_deep import deep_generate, deep_generate_narrative


class AdventureRunner:
    """Runs a Mindscape adventure."""

    def __init__(self, adventure: Adventure, compact: bool = False, narrative: bool = False):
        self.adventure = adventure
        self.engine = MindscapeEngine()
        self.current_node_id = adventure.start_node
        self.history = []       # List of (node_id, action_text) tuples
        self.transcript = []    # Full text output
        self.attempt_count = 0  # Current challenge attempt number
        self.compact = compact  # If True, use first-pass only (less tokens)
        self.narrative = narrative  # If True, use narrative mode (no data dumps)

    def _emit(self, text: str):
        """Output text and add to transcript."""
        print(text)
        self.transcript.append(text)

    def _render_scene(self, node: AdventureNode) -> str:
        """Render a node's scene using the mindscape engine."""
        scene = self.engine.find_scene(node.scene_id)
        if not scene:
            return f"[Scene '{node.scene_id}' not found — the physics data for this room is missing]"
        if self.narrative:
            return deep_generate_narrative(self.engine, scene)
        return deep_generate(self.engine, scene)

    def _render_transition(self, from_node: AdventureNode, to_node: AdventureNode) -> str:
        """Generate a transition description between two rooms using physics."""
        hints = to_node.transition_hints
        if not hints:
            return ""

        parts = []
        parts.append("─── transition ───")
        parts.append("")

        if "path" in hints:
            parts.append(hints["path"])
        if "temperature_shift" in hints:
            parts.append(f"Temperature: {hints['temperature_shift']}")
        if "surface_shift" in hints:
            parts.append(f"Underfoot: {hints['surface_shift']}")

        parts.append("")
        parts.append("──────────────────")
        return "\n".join(parts)

    def _render_opening(self):
        """Render the adventure opening."""
        self._emit("")
        self._emit("═" * 64)
        self._emit(f"  {self.adventure.title}")
        self._emit("═" * 64)
        self._emit("")
        if self.adventure.agent_framing:
            self._emit(f"[{self.adventure.agent_framing}]")
            self._emit("")
        self._emit(self.adventure.opening_text)
        self._emit("")

    def _render_node(self, node: AdventureNode, show_transition_from: AdventureNode = None):
        """Render a node: transition + arrival + scene + prompt/challenge/choices."""
        self._emit("")
        self._emit("─" * 64)
        self._emit("")

        # Transition from previous room
        if show_transition_from:
            transition = self._render_transition(show_transition_from, node)
            if transition:
                self._emit(transition)
                self._emit("")

        # Arrival narration
        if node.arrival_text:
            self._emit(node.arrival_text)
            self._emit("")

        # Scene render (skip for terminal nodes to let the reward breathe)
        if not node.terminal:
            scene_output = self._render_scene(node)
            self._emit(scene_output)
            self._emit("")

        # Terminal node — reward
        if node.terminal:
            if node.reward_text:
                self._emit("")
                self._emit(node.reward_text)
            return

        # Challenge
        if node.challenge:
            self._render_challenge(node)
            return

        # Prompt (for arrive/quiet rooms)
        if node.prompt:
            self._emit("")
            self._emit(f"  {node.prompt}")
            self._emit("")

        # Choices
        if node.choices:
            self._render_choices(node)

    def _render_challenge(self, node: AdventureNode):
        """Present a challenge situation."""
        challenge = node.challenge
        self._emit("─" * 40)
        self._emit(challenge.situation_text)
        self._emit("─" * 40)
        self._emit("")

    def _render_choices(self, node: AdventureNode):
        """Display choices."""
        self._emit("─" * 40)
        for i, choice in enumerate(node.choices, 1):
            self._emit(f"  [{i}] {choice.text}")
            if choice.hint:
                self._emit(f"      {choice.hint}")
        self._emit("─" * 40)
        self._emit("")

    def get_current_node(self) -> AdventureNode:
        return self.adventure.nodes[self.current_node_id]

    def make_choice(self, choice_input: str) -> dict:
        """
        Process a choice or challenge response.
        Returns: {
            "type": "choice" | "challenge_pass" | "challenge_fail" | "terminal",
            "message": str,
            "next_node": str | None,
            "transition_text": str
        }
        """
        node = self.get_current_node()

        # Handle challenge
        if node.challenge:
            passed, narration = node.challenge.evaluate(choice_input, self.attempt_count)
            if passed:
                # Challenge complete — move forward
                next_id = node.choices[0].target_node if node.choices else None
                if next_id:
                    self.history.append((self.current_node_id, f"challenge: {choice_input}"))
                    self.current_node_id = next_id
                    self.attempt_count = 0
                return {
                    "type": "challenge_pass",
                    "message": narration,
                    "next_node": next_id,
                    "transition_text": node.choices[0].hint if node.choices else "",
                }
            else:
                self.attempt_count += 1
                return {
                    "type": "challenge_fail",
                    "message": narration,
                    "next_node": None,
                    "transition_text": "",
                }

        # Helper to commit a choice
        def _commit_choice(choice):
            self.history.append((self.current_node_id, choice.text))
            self.current_node_id = choice.target_node
            self.attempt_count = 0
            next_node = self.adventure.nodes.get(choice.target_node)
            return {
                "type": "terminal" if (next_node and next_node.terminal) else "choice",
                "message": "",
                "next_node": choice.target_node,
                "transition_text": choice.hint,
            }

        # 1. Handle choice by number — extract digits from input
        import re
        numbers = re.findall(r'\b(\d+)\b', choice_input.strip())
        for num_str in numbers:
            idx = int(num_str) - 1
            if 0 <= idx < len(node.choices):
                return _commit_choice(node.choices[idx])

        # 2. Handle choice by keyword matching
        # Use last paragraph/sentence for matching to avoid pollution from
        # agents describing all options before stating their choice
        skip_words = {"the", "a", "an", "of", "to", "i", "my", "is", "it", "in",
                      "and", "or", "but", "for", "with", "this", "that", "choose",
                      "pick", "go", "take", "want", "door", "—", "-", "choice"}

        # Extract the decision line: last paragraph, or line with "I choose/pick/take"
        paragraphs = [p.strip() for p in choice_input.strip().split('\n\n') if p.strip()]
        decision_text = paragraphs[-1] if paragraphs else choice_input
        # Check if any paragraph has an explicit choice declaration
        for p in paragraphs:
            p_lower = p.lower()
            if any(marker in p_lower for marker in ['i choose', 'i pick', 'i select', 'i take the', 'my choice']):
                decision_text = p
                break

        # Strip markdown and punctuation before word matching
        import string
        decision_clean = decision_text.lower()
        decision_clean = decision_clean.replace('*', '').replace('_', '').replace('`', '')
        decision_clean = decision_clean.translate(str.maketrans('', '', string.punctuation.replace('-', '')))
        input_words = set(decision_clean.split()) - skip_words

        best_match = None
        best_score = 0
        for choice in node.choices:
            choice_clean = choice.text.lower().translate(str.maketrans('', '', string.punctuation.replace('-', '')))
            choice_words = set(choice_clean.split()) - skip_words
            overlap = choice_words & input_words
            if len(overlap) > best_score:
                best_score = len(overlap)
                best_match = choice

        if best_match and best_score > 0:
            return _commit_choice(best_match)

        # 3. Single choice — just proceed
        if len(node.choices) == 1:
            return _commit_choice(node.choices[0])

        return {
            "type": "choice",
            "message": "I didn't understand that choice. Try a number or keyword.",
            "next_node": None,
            "transition_text": "",
        }

    def run_interactive(self):
        """Run the adventure interactively with stdin input."""
        self._render_opening()
        prev_node = None

        while True:
            node = self.get_current_node()
            self._render_node(node, show_transition_from=prev_node)

            if node.terminal:
                break

            # Get input
            try:
                choice_input = input("\n> ").strip()
                if not choice_input:
                    # Single choice nodes — just pressing enter proceeds
                    if len(node.choices) == 1 and not node.challenge:
                        choice_input = "1"
                    else:
                        continue
                if choice_input.lower() in ("quit", "exit", "q"):
                    self._emit("\nAdventure ended.")
                    break
            except (EOFError, KeyboardInterrupt):
                self._emit("\nAdventure ended.")
                break

            prev_node_id = self.current_node_id
            result = self.make_choice(choice_input)

            if result["message"]:
                self._emit(f"\n{result['message']}")

            if result["next_node"] is None:
                prev_node = None  # Stay in same room, no transition
                if result["type"] == "challenge_fail":
                    # Re-present the challenge
                    self._emit("")
                    self._render_challenge(node)
            else:
                prev_node = self.adventure.nodes.get(prev_node_id)

    def run_auto(self, chooser=None):
        """
        Run the adventure with an automatic chooser.
        chooser: function(node, choices) -> int (0-indexed choice)
        Default: always picks the first option.
        """
        if chooser is None:
            chooser = lambda node, choices: 0

        self._render_opening()
        prev_node = None

        while True:
            node = self.get_current_node()
            self._render_node(node, show_transition_from=prev_node)

            if node.terminal:
                break

            prev_node_id = self.current_node_id

            if node.challenge:
                # Auto-mode picks the correct answer using keywords
                correct = node.challenge.correct_keywords
                if correct:
                    self._emit(f"\n  → {correct[0]}")
                    result = self.make_choice(correct[0])
                    if result["message"]:
                        self._emit(f"\n{result['message']}")
                else:
                    # Skip
                    if node.choices:
                        self.current_node_id = node.choices[0].target_node
                        self.history.append((node.id, "auto-challenge-skip"))
            elif not node.choices:
                break
            else:
                choice_idx = chooser(node, node.choices)
                choice = node.choices[min(choice_idx, len(node.choices) - 1)]
                self._emit(f"\n  → {choice.text}")
                self.history.append((node.id, choice.text))
                self.current_node_id = choice.target_node

            prev_node = self.adventure.nodes.get(prev_node_id)

    def get_transcript(self) -> str:
        """Return the full transcript as a string."""
        return "\n".join(self.transcript)

    def get_transition_prompt(self, from_node_id: str, to_node_id: str) -> str:
        """
        Generate a prompt for an LLM to narrate the transition between two nodes.
        """
        from_node = self.adventure.nodes.get(from_node_id)
        to_node = self.adventure.nodes.get(to_node_id)
        if not from_node or not to_node:
            return ""

        from_scene = self.engine.find_scene(from_node.scene_id)
        to_scene = self.engine.find_scene(to_node.scene_id)

        parts = []
        parts.append("Write a 2-3 paragraph sensory transition between these two spaces.")
        parts.append("Focus on what changes: temperature, sound, smell, light, surface underfoot.")
        parts.append("Show the change happening gradually, not all at once.")
        parts.append("")

        if from_scene:
            env = from_scene.environment
            parts.append(f"LEAVING: {from_scene.name}")
            parts.append(f"  Temp: {env.temperature_c}°C | Humidity: {env.humidity_pct}% | Wind: {env.wind_speed_kmh} km/h")
            parts.append(f"  Indoor: {env.indoor}")

        if to_scene:
            env = to_scene.environment
            parts.append(f"ENTERING: {to_scene.name}")
            parts.append(f"  Temp: {env.temperature_c}°C | Humidity: {env.humidity_pct}% | Wind: {env.wind_speed_kmh} km/h")
            parts.append(f"  Indoor: {env.indoor}")

        hints = to_node.transition_hints
        if hints:
            parts.append(f"PATH: {json.dumps(hints)}")

        return "\n".join(parts)
