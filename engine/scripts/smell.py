#!/usr/bin/env python3
"""
smell_compact.py — Compact SmellDB loading from pre-processed JSON.

Same API as SmellDB in smell.py, but loads from smell_compounds.json
instead of pyrfume-data CSVs. No pyrfume/pandas dependency.

Usage:
    python3 smell_compact.py "vanillin" "benzaldehyde"
    python3 smell_compact.py --json "ethanol"
    python3 smell_compact.py --scene coffee-shop
    python3 smell_compact.py --mix "vanillin" "limonene" "eugenol"
"""

import argparse
import difflib
import json
import os
import sys
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
COMPOUNDS_PATH = DATA_DIR / "smell_compounds.json"
SCENES_PATH = DATA_DIR / "smell_scenes.json"

# Common name → compound name(s) in the database.
SYNONYMS = {
    "cinnamon": ["cinnamaldehyde", "cinnamic acid", "cinnamyl"],
    "coffee": ["furfuryl mercaptan", "furfural", "2-furfurylthiol", "coffee"],
    "vanilla": ["vanillin", "ethyl vanillin"],
    "almond": ["benzaldehyde"],
    "banana": ["isoamyl acetate", "amyl acetate"],
    "clove": ["eugenol"],
    "mint": ["menthol", "menthone", "peppermint"],
    "peppermint": ["menthol", "menthone"],
    "lemon": ["citral", "limonene", "citronellal"],
    "orange": ["limonene", "octanal", "decanal", "orange"],
    "rose": ["geraniol", "citronellol", "rose oxide", "phenylethyl alcohol"],
    "jasmine": ["jasmine", "indole", "benzyl acetate", "jasmone"],
    "lavender": ["linalool", "linalyl acetate", "lavender"],
    "garlic": ["allicin", "diallyl disulfide", "garlic"],
    "onion": ["propanethiol", "onion"],
    "butter": ["diacetyl", "butter", "butanoic acid"],
    "caramel": ["diacetyl", "maltol", "furaneol", "caramel"],
    "chocolate": ["chocolate", "theobromine", "vanillin"],
    "coconut": ["gamma-nonalactone", "coconut"],
    "peach": ["gamma-decalactone", "peach"],
    "strawberry": ["ethyl methylphenylglycidate", "furaneol", "strawberry"],
    "apple": ["ethyl 2-methylbutyrate", "hexanal", "apple"],
    "grape": ["methyl anthranilate", "grape"],
    "pineapple": ["ethyl butyrate", "allyl hexanoate", "pineapple"],
    "honey": ["phenylacetic acid", "phenylacetaldehyde", "honey"],
    "maple": ["sotolon", "maple"],
    "smoke": ["guaiacol", "syringol", "smoke"],
    "wood": ["cedrene", "cedarwood", "sandalwood", "guaiacol"],
    "cedar": ["cedrene", "cedarwood", "cedar"],
    "pine": ["pinene", "pine"],
    "eucalyptus": ["eucalyptol", "cineole", "eucalyptus"],
    "camphor": ["camphor"],
    "musk": ["muscone", "musk"],
    "anise": ["anethole", "anise", "anisaldehyde"],
    "licorice": ["anethole", "anise"],
    "ginger": ["gingerol", "zingiberene", "ginger"],
    "pepper": ["piperine", "pepper", "rotundone"],
    "nutmeg": ["myristicin", "nutmeg"],
    "cardamom": ["cineole", "cardamom"],
    "coriander": ["linalool", "coriander"],
    "cumin": ["cuminaldehyde", "cumin"],
    "thyme": ["thymol", "thyme"],
    "basil": ["estragole", "linalool", "basil"],
    "sage": ["thujone", "sage"],
    "tea": ["linalool", "geraniol", "tea"],
    "gasoline": ["benzene", "toluene", "octane"],
    "plastic": ["styrene", "vinyl"],
    "rubber": ["isoprene", "rubber"],
    "soap": ["linalool", "limonene", "soap"],
}


class SmellDB:
    """Unified scent descriptor database — compact JSON backend."""

    def __init__(self):
        self._cas = {}       # CAS/key → {"n": name, "d": [descriptors], "s": source}
        self._cid = {}       # CID → {"n": name, "d": [descriptors]}
        self._names = {}     # lowercase name → {"t": "cas"|"cid", "k": key}
        self._loaded = False
        self._scenes = None

    def _ensure_loaded(self):
        if self._loaded:
            return
        if not COMPOUNDS_PATH.exists():
            raise FileNotFoundError(f"Compound data not found: {COMPOUNDS_PATH}")
        with open(COMPOUNDS_PATH) as f:
            data = json.load(f)
        self._cas = data.get("cas", {})
        self._cid = data.get("cid", {})
        self._names = data.get("names", {})
        self._loaded = True

    def _fuzzy_match_name(self, term_lower, cutoff=0.6):
        all_names = list(self._names.keys())
        return difflib.get_close_matches(term_lower, all_names, n=3, cutoff=cutoff)

    def _resolve_synonyms(self, term_lower):
        if term_lower in SYNONYMS:
            return SYNONYMS[term_lower]
        for key, compounds in SYNONYMS.items():
            if term_lower in key or key in term_lower:
                return compounds
        return []

    def query(self, term):
        self._ensure_loaded()
        term_clean = term.strip()
        term_lower = term_clean.lower()

        if not term_clean:
            return {"query": term_clean, "name": None, "cas": None, "descriptors": [], "source": None}

        # 1. Try as CAS key
        if term_clean in self._cas:
            entry = self._cas[term_clean]
            return {
                "query": term_clean,
                "name": entry["n"],
                "cas": term_clean,
                "descriptors": entry["d"],
                "source": entry.get("s", "compact"),
            }

        # 2. Exact name match
        ref = self._names.get(term_lower)
        if ref:
            if ref["t"] == "cas" and ref["k"] in self._cas:
                entry = self._cas[ref["k"]]
                return {
                    "query": term_clean,
                    "name": entry["n"],
                    "cas": ref["k"],
                    "descriptors": entry["d"],
                    "source": entry.get("s", "compact"),
                }
            elif ref["t"] == "cid" and ref["k"] in self._cid:
                entry = self._cid[ref["k"]]
                return {
                    "query": term_clean,
                    "name": entry["n"],
                    "cas": None,
                    "descriptors": entry["d"],
                    "source": "flavornet",
                }

        # 3. Synonym resolution
        synonyms = self._resolve_synonyms(term_lower)
        for syn in synonyms:
            result = self._query_direct(syn.lower())
            if result and result["descriptors"]:
                result["query"] = term_clean
                result["source"] = (result.get("source") or "") + " (via synonym)"
                return result

        # 4. Fuzzy match
        fuzzy_matches = self._fuzzy_match_name(term_lower)
        for match in fuzzy_matches:
            result = self._query_direct(match)
            if result and result["descriptors"]:
                result["query"] = term_clean
                result["source"] = (result.get("source") or "") + " (fuzzy)"
                return result

        # 5. Substring match
        for name, ref in self._names.items():
            if term_lower in name:
                if ref["t"] == "cas" and ref["k"] in self._cas:
                    entry = self._cas[ref["k"]]
                    return {
                        "query": term_clean,
                        "name": entry["n"],
                        "cas": ref["k"],
                        "descriptors": entry["d"],
                        "source": entry.get("s", "compact") + " (substring)",
                    }

        return {"query": term_clean, "name": None, "cas": None, "descriptors": [], "source": None}

    def _query_direct(self, name_lower):
        ref = self._names.get(name_lower)
        if ref:
            if ref["t"] == "cas" and ref["k"] in self._cas:
                entry = self._cas[ref["k"]]
                return {
                    "query": name_lower,
                    "name": entry["n"],
                    "cas": ref["k"],
                    "descriptors": entry["d"],
                    "source": entry.get("s", "compact"),
                }
            elif ref["t"] == "cid" and ref["k"] in self._cid:
                entry = self._cid[ref["k"]]
                return {
                    "query": name_lower,
                    "name": entry["n"],
                    "cas": None,
                    "descriptors": entry["d"],
                    "source": "flavornet",
                }
        # Substring fallback
        for name, r in self._names.items():
            if name_lower in name:
                if r["t"] == "cas" and r["k"] in self._cas:
                    entry = self._cas[r["k"]]
                    return {
                        "query": name_lower,
                        "name": entry["n"],
                        "cas": r["k"],
                        "descriptors": entry["d"],
                        "source": entry.get("s", "compact"),
                    }
        return None

    def query_multi(self, term):
        self._ensure_loaded()
        term_lower = term.strip().lower()
        results = []
        seen_cas = set()

        single = self.query(term)
        if single["descriptors"]:
            results.append(single)
            if single["cas"]:
                seen_cas.add(single["cas"])

        synonyms = self._resolve_synonyms(term_lower)
        for syn in synonyms:
            r = self._query_direct(syn.lower())
            if r and r["descriptors"] and r.get("cas") not in seen_cas:
                r["query"] = term
                results.append(r)
                if r.get("cas"):
                    seen_cas.add(r["cas"])

        return results if results else [single]

    def describe(self, term):
        result = self.query(term)
        if not result["descriptors"]:
            return f"❌ {term}: no scent data found"
        name = result["name"] or result["query"]
        cas_str = f" (CAS {result['cas']})" if result["cas"] else ""
        descs = ", ".join(result["descriptors"])
        return f"🫧 {name}{cas_str}: {descs}"

    def mix(self, terms):
        self._ensure_loaded()
        all_descriptors = []
        compounds_found = []

        for term in terms:
            result = self.query(term)
            if result["descriptors"]:
                compounds_found.append({
                    "name": result["name"] or result["query"],
                    "cas": result["cas"],
                    "descriptors": result["descriptors"],
                })
                all_descriptors.extend(result["descriptors"])

        counter = Counter(d.lower() for d in all_descriptors)
        dominant = [d for d, c in counter.most_common() if c >= 2]
        subtle = [d for d, c in counter.most_common() if c == 1]

        return {
            "compounds": compounds_found,
            "total_compounds": len(compounds_found),
            "dominant_notes": dominant,
            "subtle_notes": subtle,
            "all_notes_ranked": [d for d, _ in counter.most_common()],
        }

    def describe_mix(self, terms):
        result = self.mix(terms)
        if not result["compounds"]:
            return "❌ No scent data found for any of the given compounds."
        lines = []
        lines.append(f"🧪 Scent Mix ({result['total_compounds']} compounds)")
        lines.append("")
        for c in result["compounds"]:
            cas_str = f" (CAS {c['cas']})" if c["cas"] else ""
            lines.append(f"  🫧 {c['name']}{cas_str}: {', '.join(c['descriptors'])}")
        lines.append("")
        if result["dominant_notes"]:
            lines.append(f"  🔴 Dominant: {', '.join(result['dominant_notes'])}")
        if result["subtle_notes"]:
            lines.append(f"  🔵 Subtle: {', '.join(result['subtle_notes'])}")
        return "\n".join(lines)

    def load_scenes(self):
        if self._scenes is None:
            if SCENES_PATH.exists():
                with open(SCENES_PATH) as f:
                    self._scenes = json.load(f)
            else:
                self._scenes = {}
        return self._scenes

    def list_scenes(self):
        return sorted(self.load_scenes().keys())

    def scene(self, scene_name):
        scenes = self.load_scenes()
        scene_key = scene_name.strip().lower()
        if scene_key not in scenes:
            matches = difflib.get_close_matches(scene_key, scenes.keys(), n=1, cutoff=0.6)
            if matches:
                scene_key = matches[0]
            else:
                return None
        s = scenes[scene_key]
        mix_result = self.mix(s["compounds"])
        mix_result["scene_name"] = s["name"]
        mix_result["scene_description"] = s["description"]
        return mix_result

    def describe_scene(self, scene_name):
        result = self.scene(scene_name)
        if result is None:
            available = ", ".join(self.list_scenes())
            return f"❌ Scene '{scene_name}' not found. Available: {available}"
        lines = []
        lines.append(f"🏠 {result['scene_name']}")
        lines.append(f"   {result['scene_description']}")
        lines.append("")
        for c in result["compounds"]:
            cas_str = f" (CAS {c['cas']})" if c["cas"] else ""
            lines.append(f"  🫧 {c['name']}{cas_str}: {', '.join(c['descriptors'])}")
        lines.append("")
        if result["dominant_notes"]:
            lines.append(f"  🔴 Dominant: {', '.join(result['dominant_notes'])}")
        if result["subtle_notes"]:
            lines.append(f"  🔵 Subtle: {', '.join(result['subtle_notes'])}")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Look up scent descriptors for chemical compounds")
    parser.add_argument("compounds", nargs="*", help="Compound names or CAS numbers")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--scene", type=str, help="Look up a scene profile")
    parser.add_argument("--list-scenes", action="store_true", help="List available scenes")
    parser.add_argument("--mix", action="store_true", help="Mix compounds")
    parser.add_argument("--narrate", action="store_true", help="Experiential prose")
    parser.add_argument("--walk", action="store_true", help="Walk through a scene")
    parser.add_argument("--intensity", type=str, default="moderate",
                        choices=["trace", "faint", "moderate", "strong", "overwhelming"])
    args = parser.parse_args()

    db = SmellDB()

    if args.list_scenes:
        print("Available scenes:")
        for s in db.list_scenes():
            scenes = db.load_scenes()
            print(f"  {s}: {scenes[s]['name']}")
        return

    if args.scene and args.walk:
        from smell_language import walk_scene
        print(walk_scene(db, args.scene))
        return

    if args.scene:
        if args.json:
            result = db.scene(args.scene)
            print(json.dumps(result, indent=2))
        elif args.narrate:
            from smell_language import narrate_scene
            result = db.scene(args.scene)
            if result is None:
                available = ", ".join(db.list_scenes())
                print(f"❌ Scene '{args.scene}' not found. Available: {available}")
            else:
                print(narrate_scene(result, args.intensity))
        else:
            print(db.describe_scene(args.scene))
        return

    if not args.compounds:
        parser.print_help()
        return

    if args.mix:
        if args.json:
            print(json.dumps(db.mix(args.compounds), indent=2))
        elif args.narrate:
            from smell_language import narrate_mix
            result = db.mix(args.compounds)
            print(narrate_mix(result, args.intensity))
        else:
            print(db.describe_mix(args.compounds))
        return

    if args.json:
        results = [db.query(c) for c in args.compounds]
        print(json.dumps(results, indent=2))
    elif args.narrate:
        from smell_language import narrate_compound
        for compound in args.compounds:
            result = db.query(compound)
            print(narrate_compound(result, args.intensity))
    else:
        for compound in args.compounds:
            print(db.describe(compound))


if __name__ == "__main__":
    main()
