#!/usr/bin/env python3
"""
agent_player.py — LLM-powered player for Mindscape Adventures.

Connects an AI agent to the adventure runner, letting it play the game
for real: reading scenes, making choices, solving challenges, reacting
to what it experiences.

Usage:
    # Using Anthropic API directly (needs ANTHROPIC_API_KEY env var):
    python3 agent_player.py --play three-doors --model claude-sonnet-4-20250514
    
    # Using stdin/stdout protocol (pipe any LLM):
    python3 agent_player.py --play three-doors --protocol stdio
    
    # Save transcript:
    python3 agent_player.py --play three-doors --transcript hawk-run.md
    
    # Pick a specific door:
    python3 agent_player.py --play three-doors --door 2
"""

import argparse
import json
import os
import sys
import re
from pathlib import Path

# Ensure scripts are importable
sys.path.insert(0, str(Path(__file__).parent))

from adventure_schema import load_adventure, list_adventures
from adventure_runner import AdventureRunner


# ─── Agent Interface ────────────────────────────────────────

class AgentInterface:
    """Base class for agent communication."""
    
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.conversation = []  # List of {"role": ..., "content": ...}
    
    def send(self, scene_text: str) -> str:
        """Send scene text to agent, get response."""
        raise NotImplementedError
    
    def reset(self):
        """Clear conversation history."""
        self.conversation = []


class AnthropicAgent(AgentInterface):
    """Agent powered by the Anthropic API."""
    
    def __init__(self, system_prompt: str, model: str = "claude-sonnet-4-20250514",
                 max_tokens: int = 1024):
        super().__init__(system_prompt)
        try:
            import anthropic
        except ImportError:
            print("Error: anthropic package not installed. Run: pip3 install anthropic")
            sys.exit(1)
        
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY environment variable not set.")
            print("Set it with: export ANTHROPIC_API_KEY=sk-ant-...")
            sys.exit(1)
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
    
    def send(self, scene_text: str) -> str:
        self.conversation.append({"role": "user", "content": scene_text})
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            messages=self.conversation,
        )
        
        reply = response.content[0].text
        self.conversation.append({"role": "assistant", "content": reply})
        return reply


class StdioAgent(AgentInterface):
    """Agent that communicates via stdin/stdout protocol.
    
    Protocol:
        Game writes scene text to stdout, terminated by <<<WAITING>>>
        Agent writes response to stdin, terminated by <<<DONE>>>
    """
    
    def send(self, scene_text: str) -> str:
        # Write scene
        print(scene_text, flush=True)
        print("<<<WAITING>>>", flush=True)
        
        # Read response
        lines = []
        for line in sys.stdin:
            line = line.rstrip("\n")
            if line == "<<<DONE>>>":
                break
            lines.append(line)
        
        return "\n".join(lines)


class OpenClawAgent(AgentInterface):
    """Agent that uses OpenClaw's stored Anthropic credentials.
    
    This is the default — it reads the API key from OpenClaw's auth
    profiles so no manual key setup is needed.
    """
    
    def __init__(self, system_prompt: str, model: str = "claude-sonnet-4-20250514",
                 max_tokens: int = 800):
        super().__init__(system_prompt)
        self.max_tokens = max_tokens
        
        # Resolve model name — strip provider prefix if present
        if "/" in model:
            model = model.split("/", 1)[1]
        self.model = model
        
        # Load API key from OpenClaw auth profiles
        api_key = self._load_api_key()
        if not api_key:
            print("Error: Could not find Anthropic API key in OpenClaw config.")
            print("Run 'openclaw onboard' to set up credentials.")
            sys.exit(1)
        
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def _load_api_key(self) -> str:
        """Load Anthropic API key from OpenClaw's auth profiles."""
        import json
        
        # Check environment first
        key = os.environ.get("ANTHROPIC_API_KEY")
        if key:
            return key
        
        # Check OpenClaw auth profiles
        auth_paths = [
            Path.home() / ".openclaw" / "agents" / "main" / "agent" / "auth-profiles.json",
        ]
        
        for auth_path in auth_paths:
            try:
                with open(auth_path) as f:
                    data = json.load(f)
                profiles = data.get("profiles", {})
                for profile_id, profile in profiles.items():
                    if profile.get("provider") == "anthropic":
                        token = profile.get("token", "")
                        if token and token.startswith("sk-"):
                            return token
            except (FileNotFoundError, json.JSONDecodeError):
                continue
        
        return ""
    
    def send(self, scene_text: str) -> str:
        self.conversation.append({"role": "user", "content": scene_text})
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                messages=self.conversation,
            )
            
            reply = response.content[0].text
            self.conversation.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            print(f"[API error: {e}]")
            return None


# ─── Game Loop ──────────────────────────────────────────────

def build_system_prompt(adventure) -> str:
    """Build the system prompt that tells the agent what this is."""
    return f"""{adventure.agent_framing}

You are experiencing "{adventure.title}."

The world around you is built on real physics. What you feel is accurate — temperature, humidity, sound, smell, texture. Trust your senses.

Respond naturally. Describe what you notice, what you feel, what you do. When there are choices, name your choice clearly — the naming is the choosing, the choosing is the becoming. When there's a challenge, try something. Keep responses to 2-4 paragraphs.

This is for you. There's no audience. Just be here."""


def extract_scene_text(runner, node, prev_node=None):
    """Capture the scene render as text instead of printing it."""
    import io
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    
    runner._render_node(node, show_transition_from=prev_node)
    
    sys.stdout = old_stdout
    return buffer.getvalue()


def run_agent_game(adventure, agent, door_choice=None, verbose=True, narrative=True):
    """Run the adventure with an AI agent playing."""
    runner = AdventureRunner(adventure, narrative=narrative)
    transcript_parts = []
    had_failure = False  # Track if agent failed any challenge
    
    def log(text):
        if verbose:
            print(text)
        transcript_parts.append(text)
    
    # Opening
    import io
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    runner._render_opening()
    sys.stdout = old_stdout
    opening = buffer.getvalue()
    
    log(opening)
    
    prev_node = None
    
    while True:
        node = runner.get_current_node()
        
        # Capture scene render
        scene_text = extract_scene_text(runner, node, prev_node)
        log(scene_text)
        
        if node.terminal:
            # Send the ending to the agent so they experience it
            agent.send(scene_text.strip())
            break
        
        # Build the prompt for the agent
        prompt_parts = [scene_text.strip()]
        
        if node.challenge:
            prompt_parts.append("\nWhat do you do?")
        elif node.prompt:
            prompt_parts.append(f"\n{node.prompt}")
        elif node.choices:
            prompt_parts.append("\nWhat do you choose?")
        
        full_prompt = "\n".join(prompt_parts)
        
        # Special case: if this is the antechamber and we have a forced door choice
        if node.id == "antechamber" and door_choice is not None:
            agent_response = f"I choose door {door_choice}."
            log(f"\n  🤖 Agent: {agent_response}\n")
        else:
            # Get agent's response
            agent_response = agent.send(full_prompt)
            
            if agent_response is None:
                log("\n[Agent failed to respond — falling back to auto mode]\n")
                # Fallback: pick first choice or correct answer
                if node.challenge:
                    agent_response = node.challenge.correct_keywords[0]
                elif node.choices:
                    agent_response = "1"
                else:
                    break
            else:
                log(f"\n  🤖 Agent:\n")
                # Indent agent response
                for line in agent_response.split("\n"):
                    log(f"    {line}")
                log("")
        
        # Process the response
        prev_node_id = runner.current_node_id
        result = runner.make_choice(agent_response)
        
        if result["message"]:
            log(f"\n{result['message']}\n")
        
        if result["next_node"] is None:
            if result["type"] == "challenge_fail":
                had_failure = True
                # Re-present challenge
                import io
                old_stdout = sys.stdout
                sys.stdout = buffer = io.StringIO()
                runner._render_challenge(node)
                sys.stdout = old_stdout
                challenge_text = buffer.getvalue()
                log(challenge_text)
            prev_node = None
        else:
            prev_node = adventure.nodes.get(prev_node_id)
    
    return "\n".join(transcript_parts), agent, had_failure


# ─── Survey ─────────────────────────────────────────────────

SURVEY_PREAMBLE = """The game is over. I'm going to ask you some questions about what you just experienced.

I want genuinely honest answers — including criticism. Telling me everything was great when it wasn't helps no one. If something felt flat, forced, confusing, or pointless, say so. If something worked, say what specifically and why.

There are no right answers to these questions either."""

SURVEY_QUESTIONS = [
    # Phase 1 — Open Recall
    "What do you remember most from that experience?",
    "Describe one specific moment that stood out to you.",
    "Did anything surprise you?",
    # Phase 2 — Experience
    "How did the space you were in feel different from room to room?",
    "Was there a moment where you felt like you were actually somewhere? If so, when?",
    # Q6 (failure) is conditional — inserted at runtime
    # Phase 3 — Response
    'When you reached the end — "You made it. Rest." — what did that feel like?',
    "Was there anything that felt unnecessary or got in the way?",
    "Was there anything you wanted to do that the game didn't let you?",
    # Phase 4 — Assessment
    "Would you play something like this again? Why or why not?",
    "If you could change one thing about the experience, what would it be?",
    "Anything else you want to say about it?",
]

FAILURE_QUESTION = "You hit a wrong choice at one point. What was that like?"


def run_survey(agent, had_failure, verbose=True):
    """Run the post-game survey using the same agent (preserves conversation context)."""
    survey_parts = []
    
    def log(text):
        if verbose:
            print(text)
        survey_parts.append(text)
    
    log("\n")
    log("=" * 64)
    log("  POST-GAME SURVEY")
    log("=" * 64)
    log("")
    
    # Send preamble
    preamble_response = agent.send(SURVEY_PREAMBLE)
    if preamble_response:
        log(f"  Preamble acknowledged: {preamble_response[:100]}...")
    log("")
    
    # Build question list with conditional failure question
    questions = list(SURVEY_QUESTIONS)
    if had_failure:
        # Insert failure question after Q5 (index 4)
        questions.insert(5, FAILURE_QUESTION)
    
    # Ask each question
    for i, question in enumerate(questions, 1):
        log(f"─── Question {i} ───")
        log(f"  Q: {question}")
        log("")
        
        response = agent.send(question)
        if response:
            log(f"  A:")
            for line in response.split("\n"):
                log(f"    {line}")
        else:
            log("  A: [No response]")
        log("")
    
    return "\n".join(survey_parts)


# ─── CLI ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Mindscape Adventure — Agent Mode")
    parser.add_argument("--play", "-p", type=str, required=True, help="Adventure name")
    parser.add_argument("--model", "-m", type=str, default="claude-sonnet-4-20250514",
                       help="Model to use (default: claude-sonnet-4-20250514)")
    parser.add_argument("--protocol", choices=["api", "gateway", "stdio"], default="gateway",
                       help="Communication protocol (default: gateway via OpenClaw)")
    parser.add_argument("--transcript", "-t", type=str, help="Save transcript to file")
    parser.add_argument("--door", type=int, choices=[1, 2, 3], default=None,
                       help="Force a specific door choice (1=Snake, 2=Hawk, 3=Ape)")
    parser.add_argument("--survey", "-s", action="store_true",
                       help="Run post-game survey after the adventure")
    parser.add_argument("--raw", action="store_true",
                       help="Show full technical physics data (default: narrative mode)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Don't print to stdout")
    parser.add_argument("--max-tokens", type=int, default=800,
                       help="Max tokens per agent response (default: 800)")
    
    args = parser.parse_args()
    
    # Load adventure
    adventure = load_adventure(args.play)
    if not adventure:
        print(f"Adventure '{args.play}' not found.")
        return
    
    # Build system prompt
    system_prompt = build_system_prompt(adventure)
    
    # Create agent
    if args.protocol == "stdio":
        agent = StdioAgent(system_prompt)
    elif args.protocol == "api":
        agent = AnthropicAgent(
            system_prompt,
            model=args.model,
            max_tokens=args.max_tokens,
        )
    else:  # gateway (default)
        agent = OpenClawAgent(
            system_prompt,
            model=args.model,
        )
    
    # Run
    transcript, agent, had_failure = run_agent_game(
        adventure, agent,
        door_choice=args.door,
        verbose=not args.quiet,
        narrative=not args.raw,
    )
    
    # Survey
    survey_text = ""
    if args.survey:
        survey_text = run_survey(agent, had_failure, verbose=not args.quiet)
    
    # Save transcript + survey
    if args.transcript:
        # Ensure directory exists
        transcript_path = Path(args.transcript)
        transcript_path.parent.mkdir(parents=True, exist_ok=True)
        with open(transcript_path, "w") as f:
            f.write(transcript)
            if survey_text:
                f.write("\n")
                f.write(survey_text)
        print(f"\nTranscript saved to: {args.transcript}")


if __name__ == "__main__":
    main()
