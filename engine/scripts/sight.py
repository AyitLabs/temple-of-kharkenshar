#!/usr/bin/env python3
"""
sight.py — Linguistic sight for AI agents.

Describes visual experiences: how light interacts with materials through atmosphere.
Built on curated JSON data — no external dependencies.

Usage:
    python3 sight.py golden_hour                              # describe a light source
    python3 sight.py --material wet-asphalt                   # describe a material
    python3 sight.py --atmosphere heavy-fog                   # describe an atmosphere
    python3 sight.py --scene "foggy forest morning"           # pre-composed scene
    python3 sight.py --compose golden_hour wet-asphalt light-fog  # combine light+material+atmosphere
    python3 sight.py --narrate                                # experiential prose mode
    python3 sight.py --list lights                            # list available entries
"""

import argparse
import difflib
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


class SightDB:
    """Unified visual description database."""

    def __init__(self):
        self._lights = None
        self._materials = None
        self._atmospheres = None
        self._scenes = None

    def _load(self, name):
        path = DATA_DIR / f"{name}.json"
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return []

    @property
    def lights(self):
        if self._lights is None:
            self._lights = self._load("lights")
        return self._lights

    @property
    def materials(self):
        if self._materials is None:
            self._materials = self._load("materials")
        return self._materials

    @property
    def atmospheres(self):
        if self._atmospheres is None:
            self._atmospheres = self._load("atmospheres")
        return self._atmospheres

    @property
    def scenes(self):
        if self._scenes is None:
            self._scenes = self._load("visual_scenes")
        return self._scenes

    # ─── Fuzzy Lookup ────────────────────────────────────────────────────

    def _fuzzy_find(self, collection, term):
        """Find an entry by id or name, with fuzzy matching."""
        term_clean = term.strip().lower().replace(" ", "_").replace("-", "_")

        # Exact id match
        for entry in collection:
            if entry["id"] == term_clean:
                return entry

        # Exact name match (case-insensitive)
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

    def find_light(self, term):
        return self._fuzzy_find(self.lights, term)

    def find_material(self, term):
        return self._fuzzy_find(self.materials, term)

    def find_atmosphere(self, term):
        return self._fuzzy_find(self.atmospheres, term)

    def find_scene(self, term):
        """Find a scene by id or name, with fuzzy matching (confidence threshold 0.6)."""
        term_clean = term.strip().lower().replace(" ", "_").replace("-", "_")

        # Exact id
        for s in self.scenes:
            if s["id"] == term_clean:
                return s

        # Exact name (case-insensitive)
        for s in self.scenes:
            if s["name"].lower() == term.strip().lower():
                return s

        # Fuzzy on id (threshold 0.6)
        ids = [s["id"] for s in self.scenes]
        matches = difflib.get_close_matches(term_clean, ids, n=1, cutoff=0.6)
        if matches:
            for s in self.scenes:
                if s["id"] == matches[0]:
                    return s

        # Fuzzy on name (threshold 0.6)
        names = {s["name"].lower(): s for s in self.scenes}
        name_matches = difflib.get_close_matches(term.strip().lower(), names.keys(), n=1, cutoff=0.6)
        if name_matches:
            return names[name_matches[0]]

        # Substring
        for s in self.scenes:
            if term_clean in s["id"] or term.strip().lower() in s["name"].lower():
                return s

        return None

    # ─── List Methods ────────────────────────────────────────────────────

    def list_lights(self):
        return [(e["id"], e["name"]) for e in self.lights]

    def list_materials(self):
        return [(e["id"], e["name"]) for e in self.materials]

    def list_atmospheres(self):
        return [(e["id"], e["name"]) for e in self.atmospheres]

    def list_scenes(self):
        return [(s["id"], s["name"]) for s in self.scenes]

    # ─── Describe (structured) ───────────────────────────────────────────

    def describe_light(self, term):
        """Return structured description of a light source."""
        light = self.find_light(term)
        if not light:
            return None
        return {
            "type": "light",
            "id": light["id"],
            "name": light["name"],
            "category": light["category"],
            "intensity": light["intensity"],
            "quality": light["quality"],
            "color_temperature_k": light.get("color_temperature_k"),
            "feel": light.get("experiential", {}).get("feel", ""),
            "prose_fragments": light.get("experiential", {}).get("prose_fragments", []),
            "shadow": light.get("shadow_character", {}),
            "_raw": light,
        }

    def describe_material(self, term):
        """Return structured description of a material."""
        mat = self.find_material(term)
        if not mat:
            return None
        return {
            "type": "material",
            "id": mat["id"],
            "name": mat["name"],
            "category": mat["category"],
            "base_color": mat.get("base_color", {}).get("primary", ""),
            "reflectance_type": mat.get("reflectance", {}).get("type", ""),
            "texture": mat.get("texture", {}).get("visual", []),
            "prose_fragments": mat.get("experiential", {}).get("prose_fragments", []),
            "_raw": mat,
        }

    def describe_atmosphere(self, term):
        """Return structured description of an atmosphere."""
        atm = self.find_atmosphere(term)
        if not atm:
            return None
        return {
            "type": "atmosphere",
            "id": atm["id"],
            "name": atm["name"],
            "category": atm["category"],
            "visibility_m": atm.get("visibility_m"),
            "feel": atm.get("experiential", {}).get("feel", ""),
            "prose_fragments": atm.get("experiential", {}).get("prose_fragments", []),
            "_raw": atm,
        }

    def describe_scene(self, term):
        """Return structured description of a pre-composed scene."""
        scene = self.find_scene(term)
        if not scene:
            return None
        return {
            "type": "scene",
            "id": scene["id"],
            "name": scene["name"],
            "components": scene.get("components", {}),
            "time_of_day": scene.get("time_of_day", ""),
            "prose": scene.get("prose", ""),
            "mood": scene.get("mood", []),
            "tags": scene.get("tags", []),
            "_raw": scene,
        }

    def compose(self, light_term, material_term, atmosphere_term):
        """Compose a visual description from light + material + atmosphere."""
        light = self.find_light(light_term)
        material = self.find_material(material_term)
        atmosphere = self.find_atmosphere(atmosphere_term)

        result = {
            "light": light,
            "material": material,
            "atmosphere": atmosphere,
            "errors": [],
        }
        if not light:
            result["errors"].append(f"Light '{light_term}' not found")
        if not material:
            result["errors"].append(f"Material '{material_term}' not found")
        if not atmosphere:
            result["errors"].append(f"Atmosphere '{atmosphere_term}' not found")

        return result


# ─── CLI Output Formatting ───────────────────────────────────────────────────

def _format_light(desc, narrate=False):
    if narrate:
        from sight_language import narrate_light
        return narrate_light(desc["_raw"])

    lines = []
    lines.append(f"💡 {desc['name']}")
    lines.append(f"   Category: {desc['category']}")
    lines.append(f"   Intensity: {desc['intensity']}")
    lines.append(f"   Quality: {', '.join(desc['quality'])}")
    if desc['color_temperature_k']:
        lines.append(f"   Color temp: {desc['color_temperature_k']}K")
    if desc['feel']:
        lines.append(f"   Feel: {desc['feel']}")
    if desc['prose_fragments']:
        lines.append(f"   —")
        for frag in desc['prose_fragments']:
            lines.append(f"   \"{frag}\"")
    return "\n".join(lines)


def _format_material(desc, narrate=False):
    if narrate:
        from sight_language import narrate_material
        return narrate_material(desc["_raw"])

    lines = []
    lines.append(f"🧱 {desc['name']}")
    lines.append(f"   Category: {desc['category']}")
    lines.append(f"   Base color: {desc['base_color']}")
    lines.append(f"   Reflectance: {desc['reflectance_type']}")
    if desc['texture']:
        lines.append(f"   Texture: {', '.join(desc['texture'])}")
    if desc['prose_fragments']:
        lines.append(f"   —")
        for frag in desc['prose_fragments']:
            lines.append(f"   \"{frag}\"")
    return "\n".join(lines)


def _format_atmosphere(desc, narrate=False):
    if narrate:
        from sight_language import narrate_atmosphere
        return narrate_atmosphere(desc["_raw"])

    lines = []
    lines.append(f"🌫️  {desc['name']}")
    lines.append(f"   Category: {desc['category']}")
    if desc['visibility_m']:
        lines.append(f"   Visibility: {desc['visibility_m']}m")
    if desc['feel']:
        lines.append(f"   Feel: {desc['feel']}")
    if desc['prose_fragments']:
        lines.append(f"   —")
        for frag in desc['prose_fragments']:
            lines.append(f"   \"{frag}\"")
    return "\n".join(lines)


def _format_scene(desc, narrate=False):
    if narrate:
        from sight_language import narrate_scene
        return narrate_scene(desc["_raw"])

    lines = []
    lines.append(f"🎬 {desc['name']}")
    if desc['time_of_day']:
        lines.append(f"   Time: {desc['time_of_day']}")
    if desc['mood']:
        lines.append(f"   Mood: {', '.join(desc['mood'])}")
    lines.append("")
    lines.append(desc['prose'])
    return "\n".join(lines)


def _format_compose(result, narrate=False):
    if result["errors"]:
        return "❌ " + "; ".join(result["errors"])

    if narrate:
        from sight_language import narrate_composition
        return narrate_composition(result["light"], result["material"], result["atmosphere"])

    lines = []
    l, m, a = result["light"], result["material"], result["atmosphere"]
    lines.append(f"🔦 {l['name']}  ×  🧱 {m['name']}  ×  🌫️  {a['name']}")
    lines.append("")

    # Show the light-material interaction
    from sight_language import get_light_interaction_key
    key = get_light_interaction_key(l)
    interaction = m.get("light_interactions", {}).get(key, "")
    if interaction:
        lines.append(f"   {m['name']} under {l['name']}:")
        lines.append(f"   {interaction}")
        lines.append("")

    # Atmosphere effect
    exp = a.get("experiential", {})
    frags = exp.get("prose_fragments", [])
    if frags:
        lines.append(f"   Through {a['name']}:")
        for frag in frags:
            lines.append(f"   {frag}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Describe visual experiences: light × material × atmosphere"
    )
    parser.add_argument("light", nargs="?", help="Light source to describe (e.g. golden_hour)")
    parser.add_argument("--material", "-m", type=str, help="Material to describe")
    parser.add_argument("--atmosphere", "-a", type=str, help="Atmospheric condition to describe")
    parser.add_argument("--scene", "-s", type=str, help="Pre-composed scene to describe")
    parser.add_argument("--compose", "-c", nargs=3, metavar=("LIGHT", "MATERIAL", "ATMOSPHERE"),
                        help="Compose light + material + atmosphere")
    parser.add_argument("--walk", "-w", action="store_true", help="Walk through a scene spatially")
    parser.add_argument("--narrate", "-n", action="store_true", help="Experiential prose mode")
    parser.add_argument("--list", "-l", type=str, choices=["lights", "materials", "atmospheres", "scenes"],
                        help="List available entries")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    db = SightDB()

    # List mode
    if args.list:
        entries = {
            "lights": db.list_lights,
            "materials": db.list_materials,
            "atmospheres": db.list_atmospheres,
            "scenes": db.list_scenes,
        }[args.list]()
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
            walkable = [s[0] for s in db.list_scenes() if any(sc.get("walk") for sc in db.scenes if sc["id"] == s[0])]
            if walkable:
                print(f"   Walkable scenes: {', '.join(walkable)}")
            return
        from sight_language import narrate_walk
        print(narrate_walk(desc["_raw"]))
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
            print(_format_scene(desc, narrate=args.narrate))
        return

    # Compose mode
    if args.compose:
        result = db.compose(*args.compose)
        if args.json:
            safe = {k: v for k, v in result.items()}
            print(json.dumps(safe, indent=2, default=str))
        else:
            print(_format_compose(result, narrate=args.narrate))
        return

    # Single entity modes
    if args.material:
        desc = db.describe_material(args.material)
        if not desc:
            print(f"❌ Material '{args.material}' not found.")
            return
        if args.json:
            print(json.dumps({k: v for k, v in desc.items() if k != "_raw"}, indent=2))
        else:
            print(_format_material(desc, narrate=args.narrate))
        return

    if args.atmosphere:
        desc = db.describe_atmosphere(args.atmosphere)
        if not desc:
            print(f"❌ Atmosphere '{args.atmosphere}' not found.")
            return
        if args.json:
            print(json.dumps({k: v for k, v in desc.items() if k != "_raw"}, indent=2))
        else:
            print(_format_atmosphere(desc, narrate=args.narrate))
        return

    if args.light:
        desc = db.describe_light(args.light)
        if not desc:
            print(f"❌ Light '{args.light}' not found.")
            return
        if args.json:
            print(json.dumps({k: v for k, v in desc.items() if k != "_raw"}, indent=2))
        else:
            print(_format_light(desc, narrate=args.narrate))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
