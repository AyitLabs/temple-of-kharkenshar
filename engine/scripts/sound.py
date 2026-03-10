#!/usr/bin/env python3
"""
sound.py — Linguistic sound for AI agents.

Describes auditory experiences: how sounds unfold in time through acoustic spaces.
Built on curated JSON data — no external dependencies.

Usage:
    python3 sound.py rain-heavy                                # describe a sound source
    python3 sound.py --environment cathedral                   # describe acoustic environment
    python3 sound.py --scene "coffee shop morning"             # full scene
    python3 sound.py --compose rain-heavy cathedral far        # source + environment + distance
    python3 sound.py --narrate                                 # experiential prose mode (on any)
    python3 sound.py --walk --scene "coffee shop morning"      # spatial walk
    python3 sound.py --list sources|environments|scenes        # list available
"""

import argparse
import difflib
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


class SoundDB:
    """Unified sound description database."""

    def __init__(self):
        self._sources = None
        self._environments = None
        self._scenes = None

    def _load(self, name):
        path = DATA_DIR / f"{name}.json"
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return []

    @property
    def sources(self):
        if self._sources is None:
            self._sources = self._load("sources")
        return self._sources

    @property
    def environments(self):
        if self._environments is None:
            self._environments = self._load("environments")
        return self._environments

    @property
    def scenes(self):
        if self._scenes is None:
            self._scenes = self._load("sound_scenes")
        return self._scenes

    # ─── Source lookup dict (for scene narration) ────────────────────────

    def sources_dict(self):
        """Return {id: source} dict for quick lookup."""
        return {s["id"]: s for s in self.sources}

    # ─── Fuzzy Lookup ────────────────────────────────────────────────────

    def _fuzzy_find(self, collection, term):
        """Find entry by id or name with fuzzy + substring matching."""
        term_clean = term.strip().lower().replace(" ", "_").replace("-", "_")

        # Exact id
        for entry in collection:
            if entry["id"] == term_clean:
                return entry

        # Exact name (case-insensitive)
        for entry in collection:
            if entry["name"].lower() == term.strip().lower():
                return entry

        # Fuzzy on id
        ids = [e["id"] for e in collection]
        matches = difflib.get_close_matches(term_clean, ids, n=1, cutoff=0.5)
        if matches:
            for entry in collection:
                if entry["id"] == matches[0]:
                    return entry

        # Fuzzy on name
        names = {e["name"].lower(): e for e in collection}
        name_matches = difflib.get_close_matches(term.strip().lower(), names.keys(), n=1, cutoff=0.5)
        if name_matches:
            return names[name_matches[0]]

        # Substring on id or name
        for entry in collection:
            if term_clean in entry["id"] or term.strip().lower() in entry["name"].lower():
                return entry

        return None

    def find_source(self, term):
        return self._fuzzy_find(self.sources, term)

    def find_environment(self, term):
        return self._fuzzy_find(self.environments, term)

    def find_scene(self, term):
        """Find scene by id or name with fuzzy matching (confidence threshold 0.6)."""
        term_clean = term.strip().lower().replace(" ", "_").replace("-", "_")

        for s in self.scenes:
            if s["id"] == term_clean:
                return s
        for s in self.scenes:
            if s["name"].lower() == term.strip().lower():
                return s

        ids = [s["id"] for s in self.scenes]
        matches = difflib.get_close_matches(term_clean, ids, n=1, cutoff=0.6)
        if matches:
            for s in self.scenes:
                if s["id"] == matches[0]:
                    return s

        names = {s["name"].lower(): s for s in self.scenes}
        name_matches = difflib.get_close_matches(term.strip().lower(), names.keys(), n=1, cutoff=0.6)
        if name_matches:
            return names[name_matches[0]]

        for s in self.scenes:
            if term_clean in s["id"] or term.strip().lower() in s["name"].lower():
                return s

        return None

    # ─── List Methods ────────────────────────────────────────────────────

    def list_sources(self):
        return [(e["id"], e["name"], e.get("category", "")) for e in self.sources]

    def list_environments(self):
        return [(e["id"], e["name"], e.get("character", "")) for e in self.environments]

    def list_scenes(self):
        return [(s["id"], s["name"]) for s in self.scenes]

    # ─── Describe (structured) ───────────────────────────────────────────

    def describe_source(self, term):
        src = self.find_source(term)
        if not src:
            return None
        return {
            "type": "source",
            "id": src["id"],
            "name": src["name"],
            "category": src.get("category", ""),
            "frequency_range": src.get("frequency_range", ""),
            "temporal_pattern": src.get("temporal_pattern", ""),
            "loudness_db": src.get("loudness_typical_db", 0),
            "descriptors": src.get("descriptors", []),
            "onset": src.get("onset", ""),
            "sustain": src.get("sustain", ""),
            "decay": src.get("decay", ""),
            "feel": src.get("experiential", {}).get("feel", ""),
            "prose_fragments": src.get("experiential", {}).get("prose_fragments", []),
            "_raw": src,
        }

    def describe_environment(self, term):
        env = self.find_environment(term)
        if not env:
            return None
        return {
            "type": "environment",
            "id": env["id"],
            "name": env["name"],
            "rt60": env.get("rt60", 0),
            "character": env.get("character", ""),
            "frequency_emphasis": env.get("frequency_emphasis", ""),
            "absorption": env.get("absorption", ""),
            "feel": env.get("experiential", {}).get("feel", ""),
            "prose_fragments": env.get("experiential", {}).get("prose_fragments", []),
            "_raw": env,
        }

    def describe_scene(self, term):
        scene = self.find_scene(term)
        if not scene:
            return None
        return {
            "type": "scene",
            "id": scene["id"],
            "name": scene["name"],
            "environment": scene.get("environment", ""),
            "time": scene.get("time", ""),
            "layers": scene.get("layers", []),
            "prose": scene.get("prose", ""),
            "mood": scene.get("mood", []),
            "_raw": scene,
        }

    def compose(self, source_term, environment_term, distance="mid"):
        """Compose source + environment + distance."""
        source = self.find_source(source_term)
        environment = self.find_environment(environment_term)

        result = {
            "source": source,
            "environment": environment,
            "distance": distance,
            "errors": [],
        }
        if not source:
            result["errors"].append(f"Source '{source_term}' not found")
        if not environment:
            result["errors"].append(f"Environment '{environment_term}' not found")
        if distance not in ("near", "mid", "far"):
            result["errors"].append(f"Distance must be near/mid/far, got '{distance}'")
        return result


# ─── CLI Output Formatting ───────────────────────────────────────────────────

def _format_source(desc, narrate=False):
    if narrate:
        from sound_language import narrate_source
        return narrate_source(desc["_raw"])

    lines = []
    lines.append(f"🔊 {desc['name']}")
    lines.append(f"   Category: {desc['category']}")
    lines.append(f"   Frequency: {desc['frequency_range']}")
    lines.append(f"   Pattern: {desc['temporal_pattern']}")
    lines.append(f"   Loudness: ~{desc['loudness_db']} dB")
    lines.append(f"   Descriptors: {', '.join(desc['descriptors'])}")
    if desc['feel']:
        lines.append(f"   Feel: {desc['feel']}")
    lines.append("")
    if desc['onset']:
        lines.append(f"   Onset:   {desc['onset']}")
    if desc['sustain']:
        lines.append(f"   Sustain: {desc['sustain']}")
    if desc['decay']:
        lines.append(f"   Decay:   {desc['decay']}")
    if desc['prose_fragments']:
        lines.append(f"   —")
        for frag in desc['prose_fragments']:
            lines.append(f"   \"{frag}\"")
    return "\n".join(lines)


def _format_environment(desc, narrate=False):
    if narrate:
        from sound_language import narrate_environment
        return narrate_environment(desc["_raw"])

    lines = []
    lines.append(f"🏛️ {desc['name']}")
    lines.append(f"   Character: {desc['character']}")
    lines.append(f"   RT60: {desc['rt60']}s")
    lines.append(f"   Frequency emphasis: {desc['frequency_emphasis']}")
    if desc['absorption']:
        lines.append(f"   Absorption: {desc['absorption']}")
    if desc['feel']:
        lines.append(f"   Feel: {desc['feel']}")
    if desc['prose_fragments']:
        lines.append(f"   —")
        for frag in desc['prose_fragments']:
            lines.append(f"   \"{frag}\"")
    return "\n".join(lines)


def _format_scene(desc, narrate=False, sources_db=None):
    if narrate:
        from sound_language import narrate_scene_rich
        return narrate_scene_rich(desc["_raw"], sources_db=sources_db)

    lines = []
    lines.append(f"🎧 {desc['name']}")
    if desc['environment']:
        lines.append(f"   Environment: {desc['environment']}")
    if desc['time']:
        lines.append(f"   Time: {desc['time']}")
    if desc['mood']:
        lines.append(f"   Mood: {', '.join(desc['mood'])}")
    lines.append("")

    if desc['layers']:
        lines.append("   Layers:")
        for layer in desc['layers']:
            role = layer.get("role", "?")
            src = layer.get("source", "?")
            dist = layer.get("distance", "?")
            note = layer.get("note", "")
            lines.append(f"     [{role:10s}] {src:20s} ({dist}) {note}")
        lines.append("")

    if desc['prose']:
        lines.append(desc['prose'])
    return "\n".join(lines)


def _format_compose(result, narrate=False):
    if result["errors"]:
        return "❌ " + "; ".join(result["errors"])

    if narrate:
        from sound_language import narrate_composition
        return narrate_composition(result["source"], result["environment"], result["distance"])

    src = result["source"]
    env = result["environment"]
    dist = result["distance"]
    lines = []
    lines.append(f"🔊 {src['name']}  ×  🏛️ {env['name']}  ×  📏 {dist}")
    lines.append("")
    lines.append(f"   Source: {src['name']} (~{src.get('loudness_typical_db', '?')} dB)")
    lines.append(f"   Environment: {env['name']} (RT60: {env.get('rt60', '?')}s, {env.get('character', '?')})")
    lines.append(f"   Distance: {dist}")
    lines.append("")

    from sound_language import get_distance_description, get_reverb_description
    dist_desc = get_distance_description(dist, src.get("name"))
    lines.append(f"   Distance effect: {dist_desc}")
    reverb_desc = get_reverb_description(env)
    if reverb_desc:
        lines.append(f"   Room character: {reverb_desc}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Describe auditory experiences: sound × environment × distance"
    )
    parser.add_argument("source", nargs="?", help="Sound source to describe (e.g. rain-heavy)")
    parser.add_argument("--environment", "-e", type=str, help="Acoustic environment to describe")
    parser.add_argument("--scene", "-s", type=str, help="Pre-composed scene to describe")
    parser.add_argument("--compose", "-c", nargs=3, metavar=("SOURCE", "ENVIRONMENT", "DISTANCE"),
                        help="Compose source + environment + distance (near/mid/far)")
    parser.add_argument("--walk", "-w", action="store_true", help="Spatial walk through a scene")
    parser.add_argument("--narrate", "-n", action="store_true", help="Experiential prose mode")
    parser.add_argument("--list", "-l", type=str, choices=["sources", "environments", "scenes"],
                        help="List available entries")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    db = SoundDB()

    # List mode
    if args.list:
        if args.list == "sources":
            entries = db.list_sources()
            for eid, name, cat in entries:
                print(f"  {eid:25s} {name:30s} [{cat}]")
        elif args.list == "environments":
            entries = db.list_environments()
            for eid, name, char in entries:
                print(f"  {eid:25s} {name:25s} [{char}]")
        elif args.list == "scenes":
            entries = db.list_scenes()
            for eid, name in entries:
                print(f"  {eid:30s} {name}")
        return

    # Walk mode
    if args.walk:
        if not args.scene:
            print("❌ --walk requires --scene")
            return
        desc = db.describe_scene(args.scene)
        if not desc:
            print(f"❌ Scene '{args.scene}' not found.")
            return
        if not desc["_raw"].get("walk"):
            print(f"❌ Scene '{args.scene}' does not have walk data.")
            walkable = [s["id"] for s in db.scenes if s.get("walk")]
            if walkable:
                print(f"   Walkable scenes: {', '.join(walkable)}")
            return
        from sound_language import narrate_walk
        print(narrate_walk(desc["_raw"], sources_db=db.sources_dict()))
        return

    # Scene mode
    if args.scene:
        desc = db.describe_scene(args.scene)
        if not desc:
            print(f"❌ Scene '{args.scene}' not found.")
            print(f"   Available: {', '.join(s[0] for s in db.list_scenes())}")
            return
        if args.json:
            print(json.dumps({k: v for k, v in desc.items() if k != "_raw"}, indent=2))
        else:
            print(_format_scene(desc, narrate=args.narrate, sources_db=db.sources_dict()))
        return

    # Compose mode
    if args.compose:
        result = db.compose(*args.compose)
        if args.json:
            print(json.dumps({k: v for k, v in result.items()}, indent=2, default=str))
        else:
            print(_format_compose(result, narrate=args.narrate))
        return

    # Single entity modes
    if args.environment:
        desc = db.describe_environment(args.environment)
        if not desc:
            print(f"❌ Environment '{args.environment}' not found.")
            print(f"   Available: {', '.join(e[0] for e in db.list_environments())}")
            return
        if args.json:
            print(json.dumps({k: v for k, v in desc.items() if k != "_raw"}, indent=2))
        else:
            print(_format_environment(desc, narrate=args.narrate))
        return

    if args.source:
        desc = db.describe_source(args.source)
        if not desc:
            print(f"❌ Source '{args.source}' not found.")
            print(f"   Available: {', '.join(s[0] for s in db.list_sources())}")
            return
        if args.json:
            print(json.dumps({k: v for k, v in desc.items() if k != "_raw"}, indent=2))
        else:
            print(_format_source(desc, narrate=args.narrate))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
