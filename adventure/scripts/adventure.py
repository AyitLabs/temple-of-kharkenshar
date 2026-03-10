#!/usr/bin/env python3
"""
adventure.py — CLI for Mindscape Adventures.

Usage:
    python3 adventure.py --list                          # List adventures
    python3 adventure.py --play three-doors              # Play interactively
    python3 adventure.py --play three-doors --auto       # AI plays itself (picks first)
    python3 adventure.py --play three-doors --agent      # AI agent plays for real
    python3 adventure.py --play three-doors --transcript # Save transcript
"""

import argparse
import os
import sys
from pathlib import Path

# Ensure adventure scripts are importable
sys.path.insert(0, str(Path(__file__).parent))

from adventure_schema import load_adventure, list_adventures
from adventure_runner import AdventureRunner


def main():
    parser = argparse.ArgumentParser(description="Mindscape Adventure Engine")
    parser.add_argument("--list", "-l", action="store_true", help="List available adventures")
    parser.add_argument("--play", "-p", type=str, help="Play an adventure by name")
    parser.add_argument("--auto", action="store_true", help="AI plays automatically (picks first choice)")
    parser.add_argument("--agent", action="store_true", help="AI agent plays for real (needs ANTHROPIC_API_KEY)")
    parser.add_argument("--model", type=str, default="claude-sonnet-4-20250514", help="Model for --agent mode")
    parser.add_argument("--door", type=int, choices=[1, 2, 3], default=None,
                       help="Force a specific door (1=Snake, 2=Hawk, 3=Ape)")
    parser.add_argument("--transcript", "-t", type=str, help="Save transcript to file")
    parser.add_argument("--validate", action="store_true", help="Validate adventure structure")
    parser.add_argument("--choice", type=int, default=None, help="For --auto: always pick this choice (1-indexed)")

    args = parser.parse_args()

    if args.list:
        adventures = list_adventures()
        if not adventures:
            print("No adventures found.")
            print(f"Place adventure JSON files in: {Path(__file__).parent.parent / 'data' / 'adventures'}")
            return
        print("Available adventures:")
        for adv in adventures:
            node_count = len(adv.nodes)
            print(f"  {adv.id:<30} {adv.title} ({node_count} nodes)")
        return

    if not args.play:
        parser.print_help()
        return

    # Load adventure
    adventure = load_adventure(args.play)
    if not adventure:
        print(f"Adventure '{args.play}' not found. Use --list to see available.")
        return

    # Validate
    errors = adventure.validate()
    if errors:
        print("Adventure validation errors:")
        for e in errors:
            print(f"  ❌ {e}")
        if not args.validate:
            print("\nAttempting to play anyway...\n")

    if args.validate:
        if not errors:
            print(f"✅ Adventure '{adventure.id}' is valid. {len(adventure.nodes)} nodes, all references resolve.")
        return

    # Agent mode
    if args.agent:
        from agent_player import OpenClawAgent, AnthropicAgent, build_system_prompt, run_agent_game
        system_prompt = build_system_prompt(adventure)
        # Try gateway first (works without API key), fall back to direct API
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            agent = AnthropicAgent(system_prompt, model=args.model)
        else:
            agent = OpenClawAgent(system_prompt, model=args.model)
        transcript = run_agent_game(adventure, agent, door_choice=args.door)
        if args.transcript:
            with open(args.transcript, "w") as f:
                f.write(transcript)
            print(f"\nTranscript saved to: {args.transcript}")
        return

    # Create runner
    runner = AdventureRunner(adventure)

    if args.auto:
        # Auto-play mode
        if args.choice is not None:
            chooser = lambda node, choices: args.choice - 1
        else:
            chooser = None  # Default: first choice
        runner.run_auto(chooser=chooser)
    else:
        # Interactive mode
        runner.run_interactive()

    # Save transcript
    if args.transcript:
        transcript = runner.get_transcript()
        with open(args.transcript, "w") as f:
            f.write(transcript)
        print(f"\nTranscript saved to: {args.transcript}")


if __name__ == "__main__":
    main()
