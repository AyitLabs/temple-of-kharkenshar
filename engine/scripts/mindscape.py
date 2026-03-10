#!/usr/bin/env python3
"""
mindscape.py — The Mindscape Engine for Project Senses.

Stacks smell + sight + sound + touch into one coherent, walkable multi-sensory experience.

Usage:
    python3 mindscape.py --list
    python3 mindscape.py --scene "night market"
    python3 mindscape.py --walk --scene "night market"
    python3 mindscape.py --narrate --scene "old bookshop"
    python3 mindscape.py --scene "old bookshop" --time night
    python3 mindscape.py --custom --describe "rainy tokyo street"
"""

import argparse
import json
import sys
from pathlib import Path

# All modules live in the same scripts/ directory — no sys.path manipulation needed
SCENES_DIR = Path(__file__).parent.parent / "data" / "mindscape_scenes"

from smell import SmellDB
from sight import SightDB
from sound import SoundDB
from mindscape_schema import MindscapeScene, load_all_scenes, EnvironmentalConditions, TimeState
from mindscape_deep import deep_generate, deep_generate_custom, deep_generate_walk
from mindscape_language import (
    narrate_scene, narrate_walk, narrate_position, narrate_touch,
    get_env_description, get_temporal_description, find_bridge, pick,
    TEMPORAL_INTROS, BRIDGES, TIME_EFFECTS, TEMPORAL_TRANSITIONS,
    HUMIDITY_EFFECTS, TEMPERATURE_EFFECTS, RAIN_EFFECTS, WIND_EFFECTS,
)


# ─── Physics Primitives ────────────────────────────────────────────────────
# Reusable environmental building blocks for composition.

# ═══════════════════════════════════════════════════════════════
# PHYSICS PRIMITIVES — organized by category
# Each primitive carries real physics values across 4 senses
# ═══════════════════════════════════════════════════════════════

PHYSICS_PRIMITIVES = {
    # ─── SPATIAL TYPES (where you are) ────────────────────────
    "underground-tunnel": {
        "category": "spatial",
        "materials": ["concrete", "steel-metal", "tile-ceramic", "rust-corroded"],
        "sound": {"sources": ["drip-echo", "distant-rumble", "footstep-amplified", "ventilation-draft"], "absorption_mod": 0.05, "rt60_s": 2.5},
        "smell": {"compounds": ["mineral-damp", "iron-oxide", "stale-air", "concrete-dust", "mildew"], "volatility_mod": 0.7},
        "sight": {"clarity_mod": 0.3, "light_filter": "no-natural-light", "reflections": True, "color_temp_K": 0},
        "touch": {"surfaces": "concrete-rough, steel-rail-cold, tile-cracked", "air": "still, damp, cool — no wind ever reaches here",
                  "thermal_conductivity_dominant": 1.7,
                  "vibration": {"frequency_hz": 3, "amplitude": "subtle", "source": "distant train passage transmitted through rails and concrete"}},
        "taste": {"compounds": ["calcium-hydroxide", "ite-powder", "mineral"], "profile": {"bitter": 0.3, "chalky": 0.7, "metallic": 0.1}, "intensity": 0.2, "note": "alkaline chalk — pH ~12 when fresh, the tongue reads it as bitter-dry, saliva thickens on contact"},
        "taste": {"compounds": ["iron-ion-Fe2+", "chromium-trace", "carbon-steel-residue"], "profile": {"metallic": 0.9, "bitter": 0.2, "salt": 0.1}, "intensity": 0.6, "note": "metallic tang — Fe²⁺ ions react with lipids on the tongue to produce 1-octen-3-one, the 'metal' taste is actually a smell triggered by touch"},
        "taste": {"compounds": ["glaze-silica", "clay-mineral", "grout-calcium"], "profile": {"chalky": 0.3, "bitter": 0.2}, "intensity": 0.15, "note": "glazed surfaces are near-tasteless, but grout lines are alkaline chalk — the tongue maps the tile by taste-contrast"},
        "taste": {"compounds": ["iron-oxide-Fe2O3", "iron-hydroxide", "flake-particle"], "profile": {"metallic": 0.8, "bitter": 0.3, "astringent": 0.2}, "intensity": 0.5, "note": "concentrated iron — rust flakes dissolve in saliva releasing Fe3+ ions, stronger metallic hit than clean steel because more surface area"},
        "taste": {"compounds": ["sodium-chloride", "potassium-chloride", "magnesium-trace"], "profile": {"salt": 1.0, "bitter": 0.1}, "intensity": 1.0, "note": "pure signal — NaCl is detected via direct ion channel (ENaC), no enzymatic conversion needed, salt taste is the fastest taste: receptor to nerve in milliseconds", "mouthfeel": "gritty-chalky"},
        "environment": {"indoor": True, "temperature_c": 14, "humidity_pct": 78, "wind_speed_kmh": 0},
    },
    "enclosed-small": {
        "category": "spatial",
        "materials": ["plaster-drywall", "wood-old", "fabric-textile"],
        "sound": {"sources": ["breathing-loud", "fabric-rustle", "surface-contact"], "absorption_mod": 0.35, "rt60_s": 0.5},
        "smell": {"compounds": ["concentrated-ambient", "body-heat", "dust-close"], "volatility_mod": 1.3},
        "sight": {"clarity_mod": 0.9, "light_filter": "single-source-dominant", "reflections": False, "color_temp_K": 4200},
        "touch": {"surfaces": "walls-within-reach, ceiling-close", "air": "warm from body heat in small volume, still",
                  "thermal_conductivity_dominant": None},
        "taste": {"compounds": ["vanillin-from-lignin", "tannin", "cellulose-neutral"], "profile": {"bitter": 0.4, "astringent": 0.5, "sweet": 0.1}, "intensity": 0.3, "note": "tannin-astringent — proteins in saliva bind to wood tannins and precipitate, the mouth goes dry and rough, same mechanism as red wine"},
        "taste": {"compounds": ["dye-residue", "sizing-chemical", "dust-absorbed"], "profile": {"bitter": 0.2, "chalky": 0.1}, "intensity": 0.1, "note": "mostly texture, not taste — the tongue registers thread count and weave more than flavor"},
        "taste": {"compounds": ["calcium-sulfate-gypsum", "calcium-carbonate"], "profile": {"chalky": 0.8, "bitter": 0.2}, "intensity": 0.3, "note": "pure chalk — gypsum is the defining taste, plaster pulls water from the tongue on contact, the taste is desiccation itself", "mouthfeel": "dry-stale"},
        "environment": {"indoor": True, "wind_speed_kmh": 0},
    },
    "enclosed-large": {
        "category": "spatial",
        "materials": ["stone-limestone", "concrete", "wood-old", "glass"],
        "sound": {"sources": ["echo-long", "footstep-event", "ambient-hum", "distant-sounds-amplified"], "absorption_mod": 0.02, "rt60_s": 4.0},
        "smell": {"compounds": ["diffused-ambient", "dust-aged", "material-dominant"], "volatility_mod": 0.9},
        "sight": {"clarity_mod": 0.6, "light_filter": "high-windows-or-artificial", "reflections": False, "color_temp_K": 4200},
        "touch": {"surfaces": "floor-dominant, walls-distant", "air": "thermal mass keeps air cool, still, stratified",
                  "thermal_conductivity_dominant": None},
        "taste": {"compounds": ["silica-neutral", "sodium-trace"], "profile": {"metallic": 0.2}, "intensity": 0.05, "note": "nearly tasteless — glass is chemically inert, but the tongue detects its temperature and smoothness more than flavor"},
        "taste": {"compounds": ["calcium-carbonate", "calcium-bicarbonate", "mineral-brine"], "profile": {"chalky": 0.6, "bitter": 0.2, "salt": 0.2}, "intensity": 0.3, "note": "calcium carbonate is antacid — same compound in Tums, licking limestone briefly neutralizes tongue acidity", "mouthfeel": "dry"},
        "environment": {"indoor": True, "wind_speed_kmh": 0},
    },
    "open-field": {
        "category": "spatial",
        "materials": ["earth-soil"],
        "sound": {"sources": ["wind-in-grass", "insects-ground", "distant-sounds-flat", "birdsong-open"], "absorption_mod": 0.0, "rt60_s": 0.0},
        "smell": {"compounds": ["grass", "earth", "pollen", "open-air"], "volatility_mod": 1.0},
        "sight": {"clarity_mod": 1.0, "light_filter": "full-sky-exposure", "reflections": False, "color_temp_K": 6000},
        "touch": {"surfaces": "grass-soft, earth-uneven, exposed", "air": "wind-exposed, no shelter, sun or cold direct on skin"},
        "taste": {"compounds": ["geosmin", "mineral-mix", "humic-acid", "clay-particle"], "profile": {"umami": 0.3, "bitter": 0.3, "salt": 0.2, "sour": 0.1}, "intensity": 0.5, "note": "petrichor on the tongue — geosmin has a taste: earthy-beetroot, detectable at 10 parts per trillion", "mouthfeel": "clean-crisp"},
        "environment": {"indoor": False, "wind_speed_kmh": 10},
    },
    "corridor-narrow": {
        "category": "spatial",
        "materials": ["plaster-drywall", "vinyl-linoleum", "paint-chemical"],
        "sound": {"sources": ["footstep-sharp", "flutter-echo", "forced-airflow-whistle", "door-sounds-distant"], "absorption_mod": 0.1, "rt60_s": 1.5},
        "smell": {"compounds": ["paint-old", "floor-cleaner", "trapped-air", "dust-linear"], "volatility_mod": 1.1},
        "sight": {"clarity_mod": 0.8, "light_filter": "overhead-fluorescent-repeating", "reflections": True, "color_temp_K": 4200},
        "touch": {"surfaces": "walls-both-sides-close, floor-hard-uniform", "air": "channeled draft, directional",
                  "thermal_conductivity_dominant": None},
        "taste": {"compounds": ["solvent-VOC", "pigment-metal-oxide", "binder-acrylic-or-oil"], "profile": {"bitter": 0.6, "chemical-burn": 0.4}, "intensity": 0.5, "note": "solvent-bitter with chemical burn — fresh paint VOCs register as toxic on the tongue, old pre-1978 paint: lead-sweet (lead acetate is genuinely sweet)"},
        "taste": {"compounds": ["plasticizer-phthalate", "PVC-residue", "linseed-oil-if-linoleum"], "profile": {"bitter": 0.4, "chemical-burn": 0.2, "fat": 0.1}, "intensity": 0.2, "note": "true linoleum (linseed oil + cork) has a faint nutty-oily taste, vinyl is petrochemical-bitter, the tongue can tell which you're standing on", "mouthfeel": "dry-dusty"},
        "environment": {"indoor": True, "wind_speed_kmh": 2},
    },
    "rooftop": {
        "category": "spatial",
        "materials": ["asphalt", "concrete", "steel-metal"],
        "sound": {"sources": ["wind-unobstructed", "city-below-muffled", "mechanical-units-hum", "birds-overhead"], "absorption_mod": 0.0, "rt60_s": 0.0},
        "smell": {"compounds": ["tar", "exhaust-rising", "rain-residue", "hot-gravel"], "volatility_mod": 1.1},
        "sight": {"clarity_mod": 1.0, "light_filter": "full-sky-urban-horizon", "reflections": False, "color_temp_K": 6000},
        "touch": {"surfaces": "tar-paper-gritty, metal-railing-cold, gravel-loose", "air": "wind-dominant, exposed, temperature extremes"},
        "taste": {"compounds": ["bitumen-PAH", "petroleum-aromatic", "tar-volatile"], "profile": {"bitter": 0.6, "chemical-burn": 0.3}, "intensity": 0.3, "note": "PAH-bitter — hot asphalt volatilizes more, cold is nearly taste-inert, temperature gates the chemistry", "mouthfeel": "dry-windswept"},
        "environment": {"indoor": False, "wind_speed_kmh": 20},
    },
    "cave": {
        "category": "spatial",
        "materials": ["stone-limestone", "earth-soil", "moss-lichen", "clay-ceramic-raw"],
        "sound": {"sources": ["drip-precise", "water-trickle", "silence-absolute", "echo-crystalline"], "absorption_mod": 0.03, "rt60_s": 3.0},
        "smell": {"compounds": ["mineral-wet", "calcium-carbonate", "bat-guano", "clay", "iron-water"], "volatility_mod": 0.6},
        "sight": {"clarity_mod": 0.0, "light_filter": "total-darkness-unless-carried", "reflections": True, "color_temp_K": 0},
        "touch": {"surfaces": "rock-wet-irregular, stalactite-smooth, mud-clay", "air": "perfectly still, 100% humidity feels, constant temp year-round",
                  "thermal_conductivity_dominant": 2.3},
        "taste": {"compounds": ["calcium-carbonate-drip", "mineral-water", "guano-ammonia"], "profile": {"chalky": 0.4, "salt": 0.2, "bitter": 0.2}, "intensity": 0.3, "note": "cave water is liquid geology — dissolved limestone makes it hard and chalky, the tongue reads centuries of mineral filtration"},
        "taste": {"compounds": ["usnic-acid", "chlorophyll-breakdown", "moisture"], "profile": {"bitter": 0.6, "sour": 0.2, "umami": 0.1}, "intensity": 0.3, "note": "bitter and vegetal — usnic acid in lichen is genuinely bitter (evolutionary defense), moss tastes like concentrated green"},
        "taste": {"compounds": ["aluminum-silicate", "iron-oxide", "moisture-mineral"], "profile": {"chalky": 0.5, "umami": 0.2, "metallic": 0.1}, "intensity": 0.3, "note": "geophagy — eating clay is practiced worldwide, kaolin is genuinely palatable: mineral-smooth, slightly umami, the body craves it during mineral deficiency", "mouthfeel": "mineral-chalky"},
"environment": {"indoor": True, "temperature_c": 12, "humidity_pct": 95, "wind_speed_kmh": 0},
    },
    "vehicle-interior": {
        "category": "spatial",
        "materials": ["leather", "rubber-plastic", "glass", "steel-metal"],
        "sound": {"sources": ["engine-vibration", "road-noise", "ventilation-fan", "indicator-click", "seatbelt-creak"], "absorption_mod": 0.4, "rt60_s": 0.1},
        "smell": {"compounds": ["leather-or-fabric", "plastic-off-gas", "fuel-trace", "air-freshener", "body-heat"], "volatility_mod": 1.2},
        "sight": {"clarity_mod": 0.9, "light_filter": "windshield-filtered", "reflections": True, "color_temp_K": 4500},
        "touch": {"surfaces": "seat-fabric-or-leather, steering-wheel-grip, glass-cold, plastic-smooth", "air": "conditioned, sealed from outside",
                  "vibration": {"frequency_hz": 35, "amplitude": "moderate", "source": "engine through chassis"}},
        "taste": {"compounds": ["plasticizer-phthalate", "styrene-trace", "petroleum-derivative"], "profile": {"bitter": 0.5, "chemical-burn": 0.2}, "intensity": 0.3, "note": "petrochemical bitter — plasticizers leach from the surface, the tongue detects them as vaguely toxic"},
        "taste": {"compounds": ["tannin-heavy", "animal-fat-residue", "chromium-salt-if-chrome-tanned"], "profile": {"bitter": 0.5, "astringent": 0.6, "umami": 0.1}, "intensity": 0.4, "note": "concentrated tannin — vegetable-tanned leather tastes like very strong tea, chrome-tanned adds a metallic chemical edge", "mouthfeel": "dry-synthetic"},
        "environment": {"indoor": True, "wind_speed_kmh": 0, "temperature_c": 22},
    },
    "elevated-open": {
        "category": "spatial",
        "materials": ["steel-metal", "concrete", "granite"],
        "sound": {"sources": ["wind-stronger", "sounds-from-below", "exposure-quiet", "cable-hum"], "absorption_mod": 0.0, "rt60_s": 0.0},
        "smell": {"compounds": ["clean-altitude", "reduced-pollution", "cold-thin-air"], "volatility_mod": 0.7},
        "sight": {"clarity_mod": 1.0, "light_filter": "unobstructed-panoramic", "reflections": False, "color_temp_K": 6000},
        "touch": {"surfaces": "metal-grating, railing-wind-cold", "air": "wind chill significant, exposed skin loses heat fast"},
        "taste": {"compounds": ["feldspar-mineral", "quartz-inert", "mica-flake"], "profile": {"chalky": 0.3, "metallic": 0.1}, "intensity": 0.15, "note": "mineral-cold and nearly inert — granite's taste is really its temperature: high thermal mass means the tongue reads cold-stone more than chemistry", "mouthfeel": "crisp-thin"},
        "environment": {"indoor": False, "wind_speed_kmh": 25, "temperature_c": 10},
    },
    "waterside": {
        "category": "spatial",
        "materials": ["wood-old", "rope-fiber", "water-surface"],
        "sound": {"sources": ["lapping", "water-slap-on-structure", "gull-cry", "rope-creak", "wave-rhythm"], "absorption_mod": 0.05, "rt60_s": 0.2},
        "smell": {"compounds": ["salt-or-freshwater", "algae", "wet-wood", "fish-faint", "mineral"], "volatility_mod": 1.2},
        "sight": {"clarity_mod": 0.9, "light_filter": "water-reflected-shimmer", "reflections": True, "color_temp_K": 6000},
        "touch": {"surfaces": "wet-wood-dock, rope-coarse, spray-on-skin", "air": "humid, salt or mineral mist, breeze off water"},
        "taste": {"compounds": ["dissolved-mineral", "algae-trace", "dissolved-oxygen"], "profile": {"salt": 0.3, "umami": 0.1, "sweet": 0.1}, "intensity": 0.7, "note": "water has a taste — mineral content creates a fingerprint, distilled water tastes flat, spring water tastes alive"},
        "taste": {"compounds": ["hemp-terpene", "salt-if-marine", "tar-if-treated"], "profile": {"bitter": 0.4, "salt": 0.2, "astringent": 0.3}, "intensity": 0.3, "note": "hemp-bitter and salt-encrusted if nautical — old rope absorbs its environment, a ship's rope tastes like the sea", "mouthfeel": "mineral-smooth"},
        "environment": {"indoor": False, "humidity_pct": 75, "wind_speed_kmh": 8},
    },
    "metal-enclosed": {
        "category": "spatial",
        "materials": ["steel-metal", "rubber-plastic", "oil-grease", "aluminum", "copper-brass"],
        "sound": {"sources": ["hull-creak", "rivet-tick", "resonance-metallic", "ventilation-hum", "drip-on-metal-ping"],
                  "absorption_mod": 0.02, "rt60_s": 1.8},
        "smell": {"compounds": ["machine-oil", "diesel-residue", "rust-iron", "rubber-gasket", "stale-recycled-air", "ozone-electrical"],
                  "volatility_mod": 0.9},
        "sight": {"clarity_mod": 0.5, "light_filter": "artificial-harsh-shadows-hard", "reflections": True, "color_temp_K": 4200},
        "touch": {"surfaces": "steel-riveted-cold, hatch-wheel, cable-bundles, condensation-on-hull",
                  "air": "recycled, metallic taste, pressurized or stale",
                  "thermal_conductivity_dominant": 50.0,
                  "vibration": {"frequency_hz": 12, "amplitude": "subtle", "source": "machinery vibration through hull"}},
        "taste": {"compounds": ["copper-ion-Cu2+", "zinc-trace", "patina-carbonate"], "profile": {"metallic": 0.9, "bitter": 0.4, "sour": 0.2}, "intensity": 0.7, "note": "pennies — Cu2+ triggers immediate salivation response, the body trying to dilute a potential toxin"},
        "taste": {"compounds": ["aluminum-ion-Al3+", "oxide-layer"], "profile": {"metallic": 0.5, "astringent": 0.3}, "intensity": 0.3, "note": "astringent-metallic — biting aluminum foil with a metal filling creates a galvanic cell, the shock is literally electricity on your tongue"},
        "taste": {"compounds": ["hydrocarbon-chain", "oxidized-aldehyde", "mineral-oil-or-organic"], "profile": {"fat": 0.7, "bitter": 0.3, "chemical-burn": 0.1}, "intensity": 0.5, "note": "oleogustus — the tongue has dedicated fat receptors (discovered 2015), fresh oil is purely fatty, rancid adds bitter aldehydes, the tongue distinguishes them because rancid means danger", "mouthfeel": "metallic-dry"},
        "environment": {"indoor": True, "temperature_c": 16, "humidity_pct": 70, "wind_speed_kmh": 0},
    },
    "stairwell": {
        "category": "spatial",
        "materials": ["concrete", "steel-metal", "paint-chemical"],
        "sound": {"sources": ["footstep-multiplied-vertical", "echo-spiral", "door-slam-floors-away", "handrail-squeak"],
                  "absorption_mod": 0.05, "rt60_s": 2.0},
        "smell": {"compounds": ["concrete-dust", "cleaning-residue", "stale-trapped-air", "paint-old"], "volatility_mod": 0.9},
        "sight": {"clarity_mod": 0.7, "light_filter": "overhead-repeating-vertical", "reflections": False, "color_temp_K": 4200},
        "touch": {"surfaces": "metal-handrail-cold-worn-smooth, concrete-steps-gritty, paint-layers-thick",
                  "air": "chimney-effect draft, cooler at bottom, warmer at top"},
        "environment": {"indoor": True, "wind_speed_kmh": 2},
    },
    "basement-cellar": {
        "category": "spatial",
        "materials": ["concrete", "concrete-wet", "steel-metal", "wood-old"],
        "sound": {"sources": ["pipe-clank", "boiler-hum", "drip-slow", "muffled-above-footsteps"], "absorption_mod": 0.1, "rt60_s": 1.2},
        "smell": {"compounds": ["damp-concrete", "mildew", "old-paint", "dust-settled", "stored-chemicals"], "volatility_mod": 0.8},
        "sight": {"clarity_mod": 0.4, "light_filter": "single-bulb-harsh-shadows", "reflections": False, "color_temp_K": 4200},
        "touch": {"surfaces": "concrete-floor-cold-damp, pipe-metal-warm-or-cold, cobweb-face",
                  "air": "cool, damp, still, the house above presses down",
                  "thermal_conductivity_dominant": 1.7},
        "taste": {"compounds": ["calcium-hydroxide-dissolved", "mineral-slurry", "alkali"], "profile": {"bitter": 0.5, "chalky": 0.5, "chemical-burn": 0.3}, "intensity": 0.4, "note": "wet concrete is more alkaline than dry — water activates Ca(OH)2 to pH 12+, the water activates the chemistry the dry dust only hints at", "mouthfeel": "musty-damp"},
        "environment": {"indoor": True, "temperature_c": 15, "humidity_pct": 70, "wind_speed_kmh": 0},
    },
    "desert-open": {
        "category": "spatial",
        "materials": ["sand", "granite"],
        "sound": {"sources": ["wind-sand-hiss", "silence-vast", "heat-shimmer-hum", "own-footsteps-in-sand"],
                  "absorption_mod": 0.0, "rt60_s": 0.0},
        "smell": {"compounds": ["dust-mineral", "hot-rock", "nothing-clean-dry", "sage-creosote-bush"], "volatility_mod": 0.6},
        "sight": {"clarity_mod": 1.0, "light_filter": "harsh-white-no-shade-infinite-horizon", "reflections": True, "color_temp_K": 6000},
        "touch": {"surfaces": "sand-hot-shifting, rock-scorching, no-shade",
                  "air": "dry heat pressing on skin, wind abrasive with sand particles"},
        "taste": {"compounds": ["silica-inert", "shell-fragment-calcium", "salt-if-coastal"], "profile": {"salt": 0.3, "chalky": 0.2}, "intensity": 0.2, "note": "mostly texture — the tongue maps particle size, not chemistry, but coastal sand carries salt and shell calcium", "mouthfeel": "parched-gritty"},
        "environment": {"indoor": False, "temperature_c": 40, "humidity_pct": 10, "wind_speed_kmh": 12},
    },
    "mountain-exposed": {
        "category": "spatial",
        "materials": ["granite", "ice-frost", "earth-soil"],
        "sound": {"sources": ["wind-unobstructed", "rock-fall-distant", "nothing-vast", "own-breathing-altitude"],
                  "absorption_mod": 0.0, "rt60_s": 0.0},
        "smell": {"compounds": ["thin-cold-air", "rock-mineral", "alpine-plant", "snow-ozone"], "volatility_mod": 0.5},
        "sight": {"clarity_mod": 1.0, "light_filter": "uv-intense-blue-deep-shadows-sharp", "reflections": False, "color_temp_K": 7500},
        "touch": {"surfaces": "rock-cold-rough, gravel-shifting, ice-patches",
                  "air": "thin, cold, wind-chill severe, lungs work harder, UV burn on skin"},
        "taste": {"compounds": ["pure-water", "dissolved-mineral-concentrated-at-boundary"], "profile": {"sweet": 0.1, "salt": 0.1}, "intensity": 0.4, "note": "cold suppresses taste — below 15C receptor sensitivity drops sharply, but freezing concentrates minerals at crystal boundaries, so the first melt is saltier than the source", "mouthfeel": "crisp-cold-thin"},
        "environment": {"indoor": False, "temperature_c": 5, "humidity_pct": 30, "wind_speed_kmh": 30},
    },

    "organic-interior": {
        "category": "spatial",
        "materials": ["water-surface", "rubber-plastic"],
        "sound": {"sources": ["heartbeat-deep", "digestive-gurgle", "fluid-movement", "muscle-contraction", "breathing-walls"],
                  "absorption_mod": 0.6, "rt60_s": 0.3},
        "smell": {"compounds": ["stomach-acid", "bile", "mucus-membrane", "blood-iron", "saline", "ammonia-trace"],
                  "volatility_mod": 1.5},
        "sight": {"clarity_mod": 0.2, "light_filter": "bioluminescent-red-diffuse", "reflections": True, "color_temp_K": 2200},
        "touch": {"surfaces": "tissue-warm-wet, membrane-elastic, ridged-muscular-wall, mucus-slick",
                  "air": "humid, body-temperature, thick, every surface yields under pressure then pushes back",
                  "thermal_conductivity_dominant": 0.5},
        "taste": {"compounds": ["hydrochloric-acid", "bile-salt", "mucus-glycoprotein", "blood-plasma-NaCl"], "profile": {"sour": 0.8, "salt": 0.6, "bitter": 0.4, "umami": 0.2}, "intensity": 0.9, "note": "the air itself is tasteable — HCl vapor registers as sour-burn, bile salts as bitter, humidity carries NaCl at 0.9% isotonic with your own blood, so salt tastes like self", "mouthfeel": "slimy-mucilaginous"},
"environment": {"indoor": True, "temperature_c": 37, "humidity_pct": 99, "wind_speed_kmh": 0},
    },

    # ─── MATERIALS (what surfaces are made of) ────────────────
    "concrete": {
        "category": "material",
        "sound": {"sources": ["footstep-flat-hard"], "absorption_mod": -0.05},
        "smell": {"compounds": ["calcium-hydroxide", "ite-ite-dust", "mineral-cold"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "grey-neutral-flat", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "gritty-hard-cold, porous under fingers",
                  "thermal_conductivity": 1.7, "thermal_note": "conducts heat moderately — feels cold but not aggressive, warms slowly under sustained contact"},
        "taste": {"compounds": ["calcium-hydroxide", "ite-powder", "mineral"], "profile": {"bitter": 0.3, "chalky": 0.7, "metallic": 0.1}, "intensity": 0.2, "note": "alkaline chalk — pH ~12 when fresh, the tongue reads it as bitter-dry, saliva thickens on contact", "mouthfeel": "chalky-gritty"},
"environment": {},
    },
    "steel-metal": {
        "category": "material",
        "sound": {"sources": ["metallic-ring", "resonance-when-struck"], "absorption_mod": -0.1},
        "smell": {"compounds": ["iron-oxide-when-wet", "machine-oil-residue", "metallic-blood-note"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "reflective-hard-glint", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-cold-hard, sharp-edges-possible, greasy-if-industrial",
                  "thermal_conductivity": 50.0, "thermal_note": "conducts heat 30x faster than concrete — feels AGGRESSIVELY cold, drains hand heat in seconds, painful below 5°C"},
        "taste": {"compounds": ["iron-ion-Fe2+", "chromium-trace", "carbon-steel-residue"], "profile": {"metallic": 0.9, "bitter": 0.2, "salt": 0.1}, "intensity": 0.6, "note": "metallic tang — Fe²⁺ ions react with lipids on the tongue to produce 1-octen-3-one, the 'metal' taste is actually a smell triggered by touch", "mouthfeel": "metallic-tingling"},
"environment": {},
    },
    "wood-old": {
        "category": "material",
        "sound": {"sources": ["creak-groan", "hollow-knock", "footstep-warm-resonant"], "absorption_mod": 0.1},
        "smell": {"compounds": ["terpenes", "varnish-aged", "lignin-decay", "dust-wood"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "warm-brown-grain", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-where-worn, rough-where-not, splinter-risk, warm-feeling",
                  "thermal_conductivity": 0.12, "thermal_note": "insulator — feels warm even when cold, barely conducts body heat, comfortable to touch"},
        "taste": {"compounds": ["vanillin-from-lignin", "tannin", "cellulose-neutral"], "profile": {"bitter": 0.4, "astringent": 0.5, "sweet": 0.1}, "intensity": 0.3, "note": "tannin-astringent — proteins in saliva bind to wood tannins and precipitate, the mouth goes dry and rough, same mechanism as red wine", "mouthfeel": "dry-tannic"},
"environment": {},
    },
    "brick": {
        "category": "material",
        "sound": {"sources": ["footstep-hard-muted"], "absorption_mod": 0.02},
        "smell": {"compounds": ["clay-fired", "mortar-calcium", "damp-brick-earthy"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "warm-red-orange-textured", "reflections": False, "color_temp_K": 2400},
        "touch": {"surfaces": "rough-regular-pattern, mortar-joints-recessed, gritty",
                  "thermal_conductivity": 0.7, "thermal_note": "moderate conductor — noticeable cold but not aggressive, texture dominates the touch experience"},
        "taste": {"compounds": ["ite-powder", "calcium", "iron-oxide-trace"], "profile": {"chalky": 0.6, "bitter": 0.3, "metallic": 0.1}, "intensity": 0.2, "note": "calcium powder and fired clay — dry, mineral, pulls moisture from the tongue on contact", "mouthfeel": "gritty-chalky"},
"environment": {},
    },
    "glass": {
        "category": "material",
        "sound": {"sources": ["tap-ring-high", "rain-patter-sharp"], "absorption_mod": -0.08},
        "smell": {"compounds": ["nothing-clean", "condensation-mineral-trace"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "transparent-or-reflective-dual", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "perfectly-smooth-cold, condensation-beads",
                  "thermal_conductivity": 1.0, "thermal_note": "good conductor — feels cold and smooth, fingerprints leave thermal shadows visible in condensation"},
        "taste": {"compounds": ["silica-neutral", "sodium-trace"], "profile": {"metallic": 0.2}, "intensity": 0.05, "note": "nearly tasteless — glass is chemically inert, but the tongue detects its temperature and smoothness more than flavor", "mouthfeel": "smooth-neutral"},
"environment": {},
    },
    "tile-ceramic": {
        "category": "material",
        "sound": {"sources": ["footstep-click-sharp", "echo-hard"], "absorption_mod": -0.05},
        "smell": {"compounds": ["grout-damp", "cleaner-chlorine-trace", "mineral"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "reflective-if-glazed", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-hard-cold, grout-lines-textured",
                  "thermal_conductivity": 1.3, "thermal_note": "feels cold and clinical, smooth glazed surface offers no grip when wet"},
        "taste": {"compounds": ["glaze-silica", "clay-mineral", "grout-calcium"], "profile": {"chalky": 0.3, "bitter": 0.2}, "intensity": 0.15, "note": "glazed surfaces are near-tasteless, but grout lines are alkaline chalk — the tongue maps the tile by taste-contrast", "mouthfeel": "smooth-cool"},
"environment": {},
    },
    "earth-soil": {
        "category": "material",
        "sound": {"sources": ["footstep-muffled-soft", "squelch-if-wet"], "absorption_mod": 0.2},
        "smell": {"compounds": ["geosmin", "petrichor", "humus", "fungal-mycelium", "worm-castings"], "volatility_mod": 0.1},
        "sight": {"clarity_mod": 0.0, "light_filter": "dark-brown-irregular", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "soft-yielding-uneven, cool-damp, granular-or-clay",
                  "thermal_conductivity": 0.5, "thermal_note": "poor conductor but damp soil feels colder than it is — evaporative cooling adds to conductive loss"},
        "taste": {"compounds": ["geosmin", "mineral-mix", "humic-acid", "clay-particle"], "profile": {"umami": 0.3, "bitter": 0.3, "salt": 0.2, "sour": 0.1}, "intensity": 0.5, "note": "petrichor on the tongue — geosmin has a taste: earthy-beetroot, detectable at 10 parts per trillion", "mouthfeel": "gritty-mineral"},
"environment": {},
    },
    "stone-limestone": {
        "category": "material",
        "sound": {"sources": ["footstep-sharp-reverberant"], "absorption_mod": -0.08},
        "smell": {"compounds": ["calcium-carbonate-offgas", "mineral-cold", "damp-must-if-old"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "grey-cream-neutral", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "cool-smooth-where-worn, rough-where-cut, massive",
                  "thermal_conductivity": 2.3, "thermal_note": "high thermal mass — feels cold and STAYS cold, hand loses all warmth before stone temperature changes measurably"},
        "taste": {"compounds": ["calcium-carbonate", "calcium-bicarbonate", "mineral-brine"], "profile": {"chalky": 0.6, "bitter": 0.2, "salt": 0.2}, "intensity": 0.3, "note": "calcium carbonate is antacid — same compound in Tums, licking limestone briefly neutralizes tongue acidity", "mouthfeel": "chalky-mineral"},
"environment": {},
    },
    "rust-corroded": {
        "category": "material",
        "sound": {"sources": ["scrape-gritty", "flake-crumble"], "absorption_mod": 0.05},
        "smell": {"compounds": ["iron-oxide", "metallic-blood", "decay-mineral"], "volatility_mod": 0.1},
        "sight": {"clarity_mod": 0.0, "light_filter": "orange-brown-decay-texture", "reflections": False, "color_temp_K": 2400},
        "touch": {"surfaces": "rough-flaky-sharp, stains-skin-orange, tetanus-warning",
                  "thermal_conductivity": 40.0, "thermal_note": "still metal underneath — cold and aggressive, but roughened surface increases contact area"},
        "taste": {"compounds": ["iron-oxide-Fe2O3", "iron-hydroxide", "flake-particle"], "profile": {"metallic": 0.8, "bitter": 0.3, "astringent": 0.2}, "intensity": 0.5, "note": "concentrated iron — rust flakes dissolve in saliva releasing Fe3+ ions, stronger metallic hit than clean steel because more surface area", "mouthfeel": "metallic-gritty"},
"environment": {},
    },
    "moss-lichen": {
        "category": "material",
        "sound": {"sources": ["silence-absorption", "squelch-micro"], "absorption_mod": 0.15},
        "smell": {"compounds": ["chlorophyll-wet", "earth-biology", "fungal-damp"], "volatility_mod": 0.1},
        "sight": {"clarity_mod": 0.0, "light_filter": "green-organic-on-substrate", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "damp-soft-spongy, cool, alive-feeling",
                  "thermal_conductivity": 0.1, "thermal_note": "insulating biological layer — feels cool from moisture, soft from structure, alive from subtle give"},
        "taste": {"compounds": ["usnic-acid", "chlorophyll-breakdown", "moisture"], "profile": {"bitter": 0.6, "sour": 0.2, "umami": 0.1}, "intensity": 0.3, "note": "bitter and vegetal — usnic acid in lichen is genuinely bitter (evolutionary defense), moss tastes like concentrated green", "mouthfeel": "fibrous-damp"},
"environment": {},
    },
    "fabric-textile": {
        "category": "material",
        "sound": {"sources": ["rustle-soft", "muffled-absorption"], "absorption_mod": 0.3},
        "smell": {"compounds": ["detergent-or-must", "dye-chemical", "body-oils-absorbed", "dust-fiber"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "color-from-dye-matte", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "soft-varied-weave, warm-insulating",
                  "thermal_conductivity": 0.04, "thermal_note": "excellent insulator — feels warm immediately, traps air, body heat stays"},
        "taste": {"compounds": ["dye-residue", "sizing-chemical", "dust-absorbed"], "profile": {"bitter": 0.2, "chalky": 0.1}, "intensity": 0.1, "note": "mostly texture, not taste — the tongue registers thread count and weave more than flavor", "mouthfeel": "fibrous-dry"},
"environment": {},
    },
    "rubber-plastic": {
        "category": "material",
        "sound": {"sources": ["squeak-on-contact", "dull-thud"], "absorption_mod": 0.1},
        "smell": {"compounds": ["off-gas-chemical", "petroleum-base", "vinyl-sharp"], "volatility_mod": 0.2},
        "sight": {"clarity_mod": 0.0, "light_filter": "artificial-color-uniform", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-grippy-artificial, slightly-sticky-warm",
                  "thermal_conductivity": 0.2, "thermal_note": "insulator — feels neither warm nor cold, neutral, artificial"},
        "taste": {"compounds": ["plasticizer-phthalate", "styrene-trace", "petroleum-derivative"], "profile": {"bitter": 0.5, "chemical-burn": 0.2}, "intensity": 0.3, "note": "petrochemical bitter — plasticizers leach from the surface, the tongue detects them as vaguely toxic", "mouthfeel": "smooth-synthetic"},
"environment": {},
    },
    "water-surface": {
        "category": "material",
        "sound": {"sources": ["drip", "ripple", "splash-on-contact"], "absorption_mod": 0.0},
        "smell": {"compounds": ["mineral-dissolved", "chlorine-if-treated", "algae-if-standing", "fresh-if-moving"], "volatility_mod": 0.2},
        "sight": {"clarity_mod": 0.0, "light_filter": "reflective-distorted-moving", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "liquid-cold-enveloping, instant-thermal-shock",
                  "thermal_conductivity": 0.6, "thermal_note": "water conducts heat 25x faster than air — immersion feels shockingly cold even at moderate temps, evaporation amplifies cooling"},
        "taste": {"compounds": ["dissolved-mineral", "algae-trace", "dissolved-oxygen"], "profile": {"salt": 0.3, "umami": 0.1, "sweet": 0.1}, "intensity": 0.7, "note": "water has a taste — mineral content creates a fingerprint, distilled water tastes flat, spring water tastes alive", "mouthfeel": "smooth-mineral"},
"environment": {"humidity_pct": 85},
    },
    "copper-brass": {
        "category": "material",
        "sound": {"sources": ["bell-tone-when-struck", "resonance-warm"], "absorption_mod": -0.05},
        "smell": {"compounds": ["verdigris-metallic-sharp", "pennies-skin-reaction", "patina-green"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "warm-gold-green-patina", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-warm-toned-metal, patina-rough-where-aged",
                  "thermal_conductivity": 385.0, "thermal_note": "highest conductivity of common metals — feels INSTANTLY cold, heat drains from hand as fast as nerves can register it"},
        "taste": {"compounds": ["copper-ion-Cu2+", "zinc-trace", "patina-carbonate"], "profile": {"metallic": 0.9, "bitter": 0.4, "sour": 0.2}, "intensity": 0.7, "note": "pennies — Cu2+ triggers immediate salivation response, the body trying to dilute a potential toxin", "mouthfeel": "metallic-astringent"},
"environment": {},
    },
    "cast-iron": {
        "category": "material",
        "sound": {"sources": ["clang-deep-resonant", "scrape-heavy"], "absorption_mod": -0.08},
        "smell": {"compounds": ["iron-oxide-strong", "metallic-blood", "oil-seasoned"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "black-grey-heavy-mass", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "heavy-rough-cast, pitted-with-age, massive-feeling",
                  "thermal_conductivity": 52.0, "thermal_note": "aggressive cold like steel but with more thermal mass — takes and holds your heat, returns nothing"},
        "taste": {"compounds": ["iron-ion-Fe2+", "carbon-trace", "seasoning-polymerized-oil"], "profile": {"metallic": 0.7, "umami": 0.2, "fat": 0.1}, "intensity": 0.5, "note": "seasoned cast iron carries umami — decades of polymerized cooking oils create a flavor-active surface, iron plus ghost-of-every-meal", "mouthfeel": "metallic-smooth"},
"environment": {},
    },
    "wood-fresh": {
        "category": "material",
        "sound": {"sources": ["saw-buzz", "plank-drop-hollow", "hammer-on-nail"], "absorption_mod": 0.1},
        "smell": {"compounds": ["pine-resin", "sawdust", "sap-sweet", "terpenes-bright", "cellulose-fresh"], "volatility_mod": 0.3},
        "sight": {"clarity_mod": 0.0, "light_filter": "pale-yellow-grain-clean", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-where-planed, splinter-where-cut, sawdust-gritty, sap-sticky",
                  "thermal_conductivity": 0.12, "thermal_note": "insulator — warm to touch, sawdust softens contact further, resin may stick to fingers"},
        "taste": {"compounds": ["terpene-pinene", "sap-sugar", "cellulose-fresh"], "profile": {"bitter": 0.3, "sweet": 0.2, "astringent": 0.3}, "intensity": 0.4, "note": "pine resin and sap sugar — volatile terpenes register as bitter-cool on the tongue (same compounds in gin), sap is genuinely sweet"},
        "taste": {"compounds": ["terpene-complex", "rosin-acid", "pimaric-acid"], "profile": {"bitter": 0.8, "astringent": 0.6, "sweet": 0.1}, "intensity": 0.7, "note": "intensely bitter-astringent — terpenes trigger bitter receptors aggressively, the bitterness is the trees defense chemistry, same compounds used in turpentine and varnish", "mouthfeel": "fibrous-tannic"},
"environment": {},
    },
    "leather": {
        "category": "material",
        "sound": {"sources": ["creak-flex", "soft-thud", "belt-snap"], "absorption_mod": 0.15},
        "smell": {"compounds": ["tannin-warm", "animal-oil", "dye-chemical", "age-patina-sweet", "saddle-soap"], "volatility_mod": 0.1},
        "sight": {"clarity_mod": 0.0, "light_filter": "brown-warm-worn-sheen", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-warm-supple, grain-texture-under-thumb, cracks-where-aged",
                  "thermal_conductivity": 0.14, "thermal_note": "insulator — feels warm and alive, almost skin-like, temperature-neutral on contact"},
        "taste": {"compounds": ["tannin-heavy", "animal-fat-residue", "chromium-salt-if-chrome-tanned"], "profile": {"bitter": 0.5, "astringent": 0.6, "umami": 0.1}, "intensity": 0.4, "note": "concentrated tannin — vegetable-tanned leather tastes like very strong tea, chrome-tanned adds a metallic chemical edge", "mouthfeel": "dry-tannic-smooth"},
"environment": {},
    },
    "paper-books": {
        "category": "material",
        "sound": {"sources": ["page-turn-whisper", "spine-crack", "paper-rustle"], "absorption_mod": 0.25},
        "smell": {"compounds": ["vanillin-lignin", "old-glue", "foxing-must", "ink-chemical", "dust-fiber"], "volatility_mod": 0.1},
        "sight": {"clarity_mod": 0.0, "light_filter": "cream-yellow-aged-pages", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-dry-fragile, foxed-rough-spots, spine-ridged",
                  "thermal_conductivity": 0.05, "thermal_note": "excellent insulator — feels warm, dry, soft, absorbs moisture from fingertips"},
        "taste": {"compounds": ["vanillin", "cellulose-acid", "lignin-fragments", "sizing-rosin"], "profile": {"sweet": 0.2, "sour": 0.3, "bitter": 0.2, "astringent": 0.2}, "intensity": 0.3, "note": "old paper is slightly sweet (vanillin) and slightly sour (acid degradation) — the tongue reads the age of a book through its acid content", "mouthfeel": "dry-fibrous-dusty"},
"environment": {},
    },
    "sand": {
        "category": "material",
        "sound": {"sources": ["crunch-shift-underfoot", "grain-hiss-wind", "pour-soft"], "absorption_mod": 0.3},
        "smell": {"compounds": ["silica-mineral-clean", "salt-if-beach", "hot-rock-if-sun"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "pale-gold-glare-reflective", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "granular-shifting-unstable, hot-surface-cool-below, abrasive-in-wind",
                  "thermal_conductivity": 0.25, "thermal_note": "poor conductor but stores massive solar heat — surface burns feet in sun, dig 10cm and it's cool"},
        "taste": {"compounds": ["silica-inert", "shell-fragment-calcium", "salt-if-coastal"], "profile": {"salt": 0.3, "chalky": 0.2}, "intensity": 0.2, "note": "mostly texture — the tongue maps particle size, not chemistry, but coastal sand carries salt and shell calcium", "mouthfeel": "gritty-coarse"},
"environment": {},
    },
    "ice-frost": {
        "category": "material",
        "sound": {"sources": ["crack-stress", "creak-expansion", "crunch-underfoot", "drip-melt"], "absorption_mod": -0.05},
        "smell": {"compounds": ["nothing-frozen", "ozone-cold", "clean-mineral"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "transparent-blue-white-prismatic", "reflections": True, "color_temp_K": 7500},
        "touch": {"surfaces": "slick-frictionless, burns-on-contact-prolonged, hard-brittle",
                  "thermal_conductivity": 2.2, "thermal_note": "high conductivity + 0°C = instant heat drain, skin sticks to wet ice (adhesion), painful within seconds"},
        "taste": {"compounds": ["pure-water", "dissolved-mineral-concentrated-at-boundary"], "profile": {"sweet": 0.1, "salt": 0.1}, "intensity": 0.4, "note": "cold suppresses taste — below 15C receptor sensitivity drops sharply, but freezing concentrates minerals at crystal boundaries, so the first melt is saltier than the source", "mouthfeel": "crisp-numbing"},
"environment": {"temperature_c": -2},
    },
    "paint-chemical": {
        "category": "material",
        "sound": {"sources": ["smooth-surface-squeak"], "absorption_mod": 0.0},
        "smell": {"compounds": ["VOC-solvent", "latex-acrylic", "lead-if-old", "turpentine", "off-gas-fresh"], "volatility_mod": 0.4},
        "sight": {"clarity_mod": 0.0, "light_filter": "uniform-color-hides-substrate", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-over-rough, peeling-reveals-layers, chalky-when-weathered",
                  "thermal_conductivity": 0.2, "thermal_note": "thin layer — touch feels like substrate underneath, paint adds only slight smoothness"},
        "taste": {"compounds": ["solvent-VOC", "pigment-metal-oxide", "binder-acrylic-or-oil"], "profile": {"bitter": 0.6, "chemical-burn": 0.4}, "intensity": 0.5, "note": "solvent-bitter with chemical burn — fresh paint VOCs register as toxic on the tongue, old pre-1978 paint: lead-sweet (lead acetate is genuinely sweet)", "mouthfeel": "coating-acrid"},
"environment": {},
    },
    "aluminum": {
        "category": "material",
        "sound": {"sources": ["ping-light-high", "rattle-thin", "dent-flex"], "absorption_mod": -0.03},
        "smell": {"compounds": ["nothing-clean", "oxide-layer-neutral"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "silver-bright-reflective-light", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-light-cold, thin-flexes-under-pressure, sharp-edges-at-cuts",
                  "thermal_conductivity": 205.0, "thermal_note": "extremely high conductivity — feels cold faster than steel, but thinner gauges warm quickly because low thermal mass"},
        "taste": {"compounds": ["aluminum-ion-Al3+", "oxide-layer"], "profile": {"metallic": 0.5, "astringent": 0.3}, "intensity": 0.3, "note": "astringent-metallic — biting aluminum foil with a metal filling creates a galvanic cell, the shock is literally electricity on your tongue", "mouthfeel": "metallic-smooth"},
"environment": {},
    },
    "wax": {
        "category": "material",
        "sound": {"sources": ["scrape-soft", "drip-thick"], "absorption_mod": 0.05},
        "smell": {"compounds": ["beeswax-honey-sweet", "paraffin-petroleum", "tallow-animal-fat"], "volatility_mod": 0.2},
        "sight": {"clarity_mod": 0.0, "light_filter": "translucent-warm-yellow", "reflections": False, "color_temp_K": 3200},
        "touch": {"surfaces": "smooth-waxy-grip, softens-under-body-heat, impression-holds",
                  "thermal_conductivity": 0.25, "thermal_note": "insulator — feels warm and slightly yielding, body heat softens surface, fingerprints embed"},
        "taste": {"compounds": ["long-chain-hydrocarbon", "ester", "beeswax-propolis-if-natural"], "profile": {"sweet": 0.2, "fat": 0.3}, "intensity": 0.2, "note": "fatty-neutral with honey edge from propolis — paraffin is tasteless, the tongue mostly reads the waxy hydrophobic coating", "mouthfeel": "waxy-coating"},
"environment": {},
    },
    "bone-shell": {
        "category": "material",
        "sound": {"sources": ["click-hard-hollow", "clatter-dry"], "absorption_mod": -0.02},
        "smell": {"compounds": ["calcium-phosphate-dry", "marrow-if-fresh", "nothing-if-old"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "cream-white-smooth-translucent-thin", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-hard-dry, warm-feeling-for-hard-material, lightweight-hollow",
                  "thermal_conductivity": 0.3, "thermal_note": "moderate insulator — feels warmer than stone or metal, almost skin-temperature, eerily comfortable"},
        "taste": {"compounds": ["calcium-phosphate", "collagen-residue", "marrow-fat-if-fresh"], "profile": {"chalky": 0.4, "umami": 0.3, "fat": 0.2}, "intensity": 0.4, "note": "calcium and collagen — dry bone is chalky, but moisture unlocks umami from residual collagen, marrow is pure fat-umami, the most calorie-dense taste signal", "mouthfeel": "chalky-smooth"},
"environment": {},
    },
    "rope-fiber": {
        "category": "material",
        "sound": {"sources": ["creak-tension", "snap-release", "rasp-through-hands"], "absorption_mod": 0.1},
        "smell": {"compounds": ["hemp-vegetal", "tar-if-marine", "mildew-if-wet", "sisal-dry-grassy"], "volatility_mod": 0.1},
        "sight": {"clarity_mod": 0.0, "light_filter": "tan-brown-twisted-texture", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "rough-fibrous-abrasive, burns-if-sliding, grip-varies-with-moisture",
                  "thermal_conductivity": 0.04, "thermal_note": "insulator — rough texture dominates sensation, thermal properties irrelevant next to the abrasion"},
        "taste": {"compounds": ["hemp-terpene", "salt-if-marine", "tar-if-treated"], "profile": {"bitter": 0.4, "salt": 0.2, "astringent": 0.3}, "intensity": 0.3, "note": "hemp-bitter and salt-encrusted if nautical — old rope absorbs its environment, a ship's rope tastes like the sea", "mouthfeel": "fibrous-coarse"},
"environment": {},
    },
    "ash-charite": {
        "category": "material",
        "sound": {"sources": ["crunch-powder", "collapse-soft", "nothing-dead"], "absorption_mod": 0.2},
        "smell": {"compounds": ["carbon-residue", "potassium-carbonate", "guaiacol-trace", "creosote-cold"], "volatility_mod": 0.1},
        "sight": {"clarity_mod": 0.0, "light_filter": "grey-white-powder-flat-dead", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "powdery-dry-collapses, stains-everything-grey, silky-fine-particles",
                  "thermal_conductivity": 0.1, "thermal_note": "excellent insulator — feels soft, dry, and oddly warm, like touching the ghost of what burned"},
        "taste": {"compounds": ["potassium-carbonate-lye", "calcium-oxide", "carbon"], "profile": {"bitter": 0.7, "sour": 0.2, "chemical-burn": 0.3}, "intensity": 0.5, "note": "alkaline burn — wood ash is lye (pH 10-12), the taste of cleanliness before cleanliness was safe", "mouthfeel": "powdery-gritty-dry"},
"environment": {},
    },
    "oil-grease": {
        "category": "material",
        "sound": {"sources": ["squelch-viscous", "drip-thick-slow"], "absorption_mod": 0.05},
        "smell": {"compounds": ["petroleum-hydrocarbons", "mineral-oil-sweet", "rancid-if-organic", "diesel-sharp"], "volatility_mod": 0.3},
        "sight": {"clarity_mod": 0.0, "light_filter": "dark-iridescent-rainbow-sheen", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "slick-viscous-coating, grip-destroyed, stains-permanent, hard-to-remove",
                  "thermal_conductivity": 0.15, "thermal_note": "insulator — oil film feels warm and frictionless, skin slides on everything, tools become treacherous"},
        "taste": {"compounds": ["hydrocarbon-chain", "oxidized-aldehyde", "mineral-oil-or-organic"], "profile": {"fat": 0.7, "bitter": 0.3, "chemical-burn": 0.1}, "intensity": 0.5, "note": "oleogustus — the tongue has dedicated fat receptors (discovered 2015), fresh oil is purely fatty, rancid adds bitter aldehydes, the tongue distinguishes them because rancid means danger", "mouthfeel": "viscous-coating-slick"},
"environment": {},
    },
    "asphalt": {
        "category": "material",
        "sound": {"sources": ["footstep-flat-grip", "tire-hiss-if-road", "crunch-gravel-base"], "absorption_mod": 0.02},
        "smell": {"compounds": ["bitumen-tar", "hot-petroleum-if-sun", "rubber-trace", "rain-wet-asphalt-distinctive"], "volatility_mod": 0.2},
        "sight": {"clarity_mod": 0.0, "light_filter": "black-grey-flat-absorbs-light", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "rough-aggregate-grip, tar-sticky-if-hot, pebble-texture-through-shoes",
                  "thermal_conductivity": 0.75, "thermal_note": "absorbs solar heat — surface temperature can exceed air by 30°C in sun, stores heat into evening, warm underfoot at night"},
        "taste": {"compounds": ["bitumen-PAH", "petroleum-aromatic", "tar-volatile"], "profile": {"bitter": 0.6, "chemical-burn": 0.3}, "intensity": 0.3, "note": "PAH-bitter — hot asphalt volatilizes more, cold is nearly taste-inert, temperature gates the chemistry", "mouthfeel": "gritty-chemical"},
"environment": {},
    },
    "marble": {
        "category": "material",
        "sound": {"sources": ["footstep-sharp-clean", "echo-precise-bright"], "absorption_mod": -0.1},
        "smell": {"compounds": ["nothing-clean-mineral", "polish-if-maintained"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "white-veined-luminous-polished", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "glass-smooth-polished, cold-dense-heavy, veins-slightly-raised",
                  "thermal_conductivity": 2.9, "thermal_note": "colder than limestone — denser, smoother, more contact area means faster heat drain, feels like touching solid winter"},
        "taste": {"compounds": ["calcium-carbonate-pure", "minimal-impurity"], "profile": {"chalky": 0.5, "sweet": 0.1}, "intensity": 0.2, "note": "cleaner than limestone — pure calcium carbonate, almost clinical, the slight sweetness may be the tongue misreading neutral as pleasant", "mouthfeel": "smooth-cool-mineral"},
"environment": {},
    },
    "bamboo": {
        "category": "material",
        "sound": {"sources": ["hollow-knock-resonant", "clatter-light", "wind-through-grove-flute"], "absorption_mod": 0.08},
        "smell": {"compounds": ["green-vegetal-fresh", "grass-sweet", "dried-hay-if-old"], "volatility_mod": 0.1},
        "sight": {"clarity_mod": 0.0, "light_filter": "pale-green-gold-segmented", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-hard-cylindrical, nodes-ridged, splits-sharp, light-hollow",
                  "thermal_conductivity": 0.15, "thermal_note": "insulator like wood — feels warm, smooth sections almost silky, hollow structure means it flexes and resonates"},
        "taste": {"compounds": ["silica-phytolith", "cellulose", "cyanogenic-glycoside-trace"], "profile": {"bitter": 0.4, "sweet": 0.1, "astringent": 0.2}, "intensity": 0.2, "note": "raw bamboo contains cyanogenic glycosides — trace bitter-almond flavor from HCN precursors, cured bamboo is neutral cellulose with silica grit", "mouthfeel": "fibrous-crisp"},
"environment": {},
    },
    "thatch-straw": {
        "category": "material",
        "sound": {"sources": ["rustle-dry", "rain-on-thatch-soft-patter", "insect-movement"], "absorption_mod": 0.35},
        "smell": {"compounds": ["hay-dry-sweet", "dust-organic", "mold-if-damp", "grass-cured"], "volatility_mod": 0.2},
        "sight": {"clarity_mod": 0.0, "light_filter": "golden-brown-textured-organic", "reflections": False, "color_temp_K": 3200},
        "touch": {"surfaces": "rough-dry-fibrous, prickly, crumbles-if-old, insects-live-in-it",
                  "thermal_conductivity": 0.07, "thermal_note": "superb insulator — thick thatch keeps heat in winter, cool in summer, feels dry and rustling"},
        "taste": {"compounds": ["cellulose-dry", "dust-fungal", "grain-residue"], "profile": {"sweet": 0.2, "bitter": 0.2, "chalky": 0.2}, "intensity": 0.2, "note": "hay-sweet with dust — dried grass retains simple sugars, the taste of summer's sugar slowly going stale", "mouthfeel": "fibrous-dry-dusty"},
"environment": {},
    },
    "clay-ceramic-raw": {
        "category": "material",
        "sound": {"sources": ["thud-dull-dense", "scrape-gritty"], "absorption_mod": 0.05},
        "smell": {"compounds": ["earth-mineral-wet-if-unfired", "kiln-heat-if-fired", "iron-rich-red"], "volatility_mod": 0.1},
        "sight": {"clarity_mod": 0.0, "light_filter": "red-brown-earth-matte", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-if-wet-gritty-if-dry, cool-dense, stains-hands-red",
                  "thermal_conductivity": 1.0, "thermal_note": "moderate conductor — cooler than expected, dense and heavy in hand, wet clay clings to skin"},
        "taste": {"compounds": ["aluminum-silicate", "iron-oxide", "moisture-mineral"], "profile": {"chalky": 0.5, "umami": 0.2, "metallic": 0.1}, "intensity": 0.3, "note": "geophagy — eating clay is practiced worldwide, kaolin is genuinely palatable: mineral-smooth, slightly umami, the body craves it during mineral deficiency", "mouthfeel": "gritty-chalky-smooth"},
"environment": {},
    },
    "salt": {
        "category": "material",
        "sound": {"sources": ["crunch-crystalline", "dissolve-hiss-in-water"], "absorption_mod": 0.0},
        "smell": {"compounds": ["brine-ocean", "mineral-sharp", "iodine-trace"], "volatility_mod": 0.1},
        "sight": {"clarity_mod": 0.0, "light_filter": "white-crystalline-glitter", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "crystalline-sharp-abrasive, dissolves-in-sweat, hygroscopic-damp",
                  "thermal_conductivity": 6.5, "thermal_note": "surprisingly high conductivity — salt feels cold and draws moisture from skin, desiccating and chilling simultaneously"},
        "taste": {"compounds": ["sodium-chloride", "potassium-chloride", "magnesium-trace"], "profile": {"salt": 1.0, "bitter": 0.1}, "intensity": 1.0, "note": "pure signal — NaCl is detected via direct ion channel (ENaC), no enzymatic conversion needed, salt taste is the fastest taste: receptor to nerve in milliseconds", "mouthfeel": "crystalline-dissolving"},
"environment": {},
    },
    "coal-charcoite": {
        "category": "material",
        "sound": {"sources": ["clunk-dense-dull", "crumble-powder"], "absorption_mod": 0.05},
        "smell": {"compounds": ["carbon-mineral", "sulfur-trace", "ancient-organic"], "volatility_mod": 0.1},
        "sight": {"clarity_mod": 0.0, "light_filter": "black-lustrous-fracture-surfaces", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "hard-brittle-breaks-angular, stains-black-permanent, dusty",
                  "thermal_conductivity": 0.2, "thermal_note": "insulator — feels surprisingly light for how dark it is, stains override all other touch sensations"},
        "taste": {"compounds": ["carbon-inert", "sulfur-trace", "mineral-ash"], "profile": {"bitter": 0.4, "metallic": 0.2}, "intensity": 0.2, "note": "activated charcoal is tasteless (pure carbon), raw coal carries sulfur and mineral impurities as bitter-metallic", "mouthfeel": "gritty-powdery-dry"},
"environment": {},
    },
    "silk-satin": {
        "category": "material",
        "sound": {"sources": ["whisper-slide", "rustle-delicate"], "absorption_mod": 0.2},
        "smell": {"compounds": ["sericin-protein-faint", "dye-chemical", "perfume-absorbed"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "luminous-sheen-color-shifts-with-angle", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "frictionless-cool-liquid-feeling, catches-on-rough-skin, drapes-under-gravity",
                  "thermal_conductivity": 0.04, "thermal_note": "insulator but FEELS cool — the smoothness tricks thermal receptors, silk at room temperature feels like cool water on skin"},
        "taste": {"compounds": ["sericin-protein", "dye-residue"], "profile": {"umami": 0.1, "bitter": 0.1}, "intensity": 0.1, "note": "silk is protein (fibroin + sericin) — technically edible and faintly umami, but the tongue registers smoothness more than chemistry", "mouthfeel": "smooth-silky"},
"environment": {},
    },
    "granite": {
        "category": "material",
        "sound": {"sources": ["footstep-deep-solid", "ring-when-struck-hard"], "absorption_mod": -0.09},
        "smell": {"compounds": ["nothing-mineral-faint", "dust-quartz", "rain-on-granite-petrichor"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "speckled-grey-pink-quartz-mica-glint", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "hard-crystalline-rough-sparkly, massive-immovable-feeling",
                  "thermal_conductivity": 2.8, "thermal_note": "high thermal mass like marble — cold and stays cold, but rougher texture means less skin contact, slightly less aggressive"},
        "taste": {"compounds": ["feldspar-mineral", "quartz-inert", "mica-flake"], "profile": {"chalky": 0.3, "metallic": 0.1}, "intensity": 0.15, "note": "mineral-cold and nearly inert — granite's taste is really its temperature: high thermal mass means the tongue reads cold-stone more than chemistry", "mouthfeel": "gritty-mineral-cold"},
"environment": {},
    },
    "plaster-drywall": {
        "category": "material",
        "sound": {"sources": ["hollow-knock", "crumble-if-old", "nail-pop"], "absorption_mod": 0.05},
        "smell": {"compounds": ["gypsum-chalk-dry", "paint-over-plaster", "dust-white-fine"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "white-flat-smooth-or-textured", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-chalky-dry, crumbles-at-edges, hollow-behind-it",
                  "thermal_conductivity": 0.5, "thermal_note": "moderate — feels neutral, neither warm nor cold, unremarkable, the most forgettable surface humans touch daily"},
        "taste": {"compounds": ["calcium-sulfate-gypsum", "calcium-carbonate"], "profile": {"chalky": 0.8, "bitter": 0.2}, "intensity": 0.3, "note": "pure chalk — gypsum is the defining taste, plaster pulls water from the tongue on contact, the taste is desiccation itself", "mouthfeel": "chalky-powdery"},
"environment": {},
    },
    "vinyl-linoleum": {
        "category": "material",
        "sound": {"sources": ["squeak-shoe-on-floor", "hollow-underneath", "ball-bounce-dead"], "absorption_mod": 0.05},
        "smell": {"compounds": ["plasticizer-off-gas", "cleaning-product", "institutional"], "volatility_mod": 0.2},
        "sight": {"clarity_mod": 0.0, "light_filter": "pattern-repeating-fake-sheen", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-slightly-yielding, warm-compared-to-tile, static-prone",
                  "thermal_conductivity": 0.17, "thermal_note": "insulator — feels warmer than tile or stone underfoot, slight give absorbs impact, institutional comfort"},
        "taste": {"compounds": ["plasticizer-phthalate", "PVC-residue", "linseed-oil-if-linoleum"], "profile": {"bitter": 0.4, "chemical-burn": 0.2, "fat": 0.1}, "intensity": 0.2, "note": "true linoleum (linseed oil + cork) has a faint nutty-oily taste, vinyl is petrochemical-bitter, the tongue can tell which you're standing on", "mouthfeel": "smooth-synthetic"},
"environment": {},
    },
    "stainless-steel": {
        "category": "material",
        "sound": {"sources": ["ring-bright-clean", "clatter-sharp"], "absorption_mod": -0.08},
        "smell": {"compounds": ["nothing-clean", "fingerprint-oils-only", "chlorine-if-sanitized"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "mirror-brushed-fingerprints-visible", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-cold-surgical-clean, fingerprints-left-visible, sharp-edges-precise",
                  "thermal_conductivity": 16.0, "thermal_note": "less conductive than carbon steel but still aggressive — cold and clinical, the touch of hospitals and kitchens"},
        "taste": {"compounds": ["chromium-oxide-passive", "nickel-trace", "iron-minimal"], "profile": {"metallic": 0.4}, "intensity": 0.2, "note": "less metallic than carbon steel — chromium oxide passivation blocks ion transfer, stainless steel is metal that learned to keep its mouth shut", "mouthfeel": "metallic-smooth-cold"},
"environment": {},
    },
    "concrete-wet": {
        "category": "material",
        "sound": {"sources": ["splash-footstep", "drip-constant", "squelch"], "absorption_mod": 0.0},
        "smell": {"compounds": ["calcium-hydroxide-strong", "mineral-amplified", "petrichor-concrete", "mildew-if-chronic"], "volatility_mod": 0.3},
        "sight": {"clarity_mod": 0.0, "light_filter": "dark-grey-reflective-when-wet", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "slick-dangerous, cold-amplified-by-water, grip-reduced",
                  "thermal_conductivity": 2.0, "thermal_note": "water increases conductivity — wet concrete feels 30% colder than dry, evaporation adds chill, dangerous to sit on"},
        "taste": {"compounds": ["calcium-hydroxide-dissolved", "mineral-slurry", "alkali"], "profile": {"bitter": 0.5, "chalky": 0.5, "chemical-burn": 0.3}, "intensity": 0.4, "note": "wet concrete is more alkaline than dry — water activates Ca(OH)2 to pH 12+, the water activates the chemistry the dry dust only hints at", "mouthfeel": "chalky-gritty-damp"},
"environment": {"humidity_pct": 80},
    },

    # ─── ATMOSPHERE (what's in the air) ───────────────────────
    "rain": {
        "category": "atmosphere",
        "sound": {"sources": ["rain-on-surface", "splashing", "dripping", "gutter-flow"], "absorption_mod": 0.3},
        "smell": {"compounds": ["geosmin", "ozone", "petrichor", "wet-asphalt"], "volatility_mod": 1.3},
        "sight": {"clarity_mod": 0.5, "light_filter": "grey_wet", "reflections": True, "color_temp_K": 6500},
        "touch": {"surfaces": "wet-everything", "air": "humid, cool droplets on skin, every handrail slick"},
        "taste": {"compounds": ["geosmin-petrichor", "ozone", "dissolved-atmospheric-gas"], "profile": {"sweet": 0.2, "metallic": 0.1}, "intensity": 0.3, "note": "rain is what water tastes like before it touches anything — ozone gives a faint metallic-electric note, dissolved CO2 makes it slightly acidic", "mouthfeel": "clean-mineral-smooth"},
"environment": {"weather": "rain", "humidity_pct": 85},
    },
    "fog": {
        "category": "atmosphere",
        "sound": {"sources": ["muffled-distance", "close-drip", "own-footsteps-loud", "directionless-echo"], "absorption_mod": 0.35},
        "smell": {"compounds": ["moisture", "wet-earth", "diffused-organics", "damp-stone", "mildew"], "volatility_mod": 0.7},
        "sight": {"clarity_mod": 0.15, "light_filter": "mie-scatter-white-grey", "reflections": False, "color_temp_K": 6500},
        "touch": {"surfaces": "slick-with-condensation, cold-damp-everything", "air": "moisture on skin, cool, clammy, droplets forming on hair and fabric"},
        "environment": {"weather": "fog", "humidity_pct": 95, "wind_speed_kmh": 0},
    },
    "snow": {
        "category": "atmosphere",
        "sound": {"sources": ["crunch-underfoot", "muffled-everything", "wind-whisper", "drip-of-melt"], "absorption_mod": 0.5},
        "smell": {"compounds": ["clean-cold", "ozone", "nothing-almost"], "volatility_mod": 0.5},
        "sight": {"clarity_mod": 0.7, "light_filter": "white-overlit-from-below", "reflections": True, "color_temp_K": 6500},
        "touch": {"surfaces": "snow-crunchy-or-wet, ice-slick, numb-fingers", "air": "biting cold, still or cutting wind"},
        "taste": {"compounds": ["pure-water-crystal", "atmospheric-dust-nucleus"], "profile": {"sweet": 0.1}, "intensity": 0.2, "note": "snow tastes sweet because cold suppresses bitter and salt receptors more than sweet — a perceptual illusion from differential receptor sensitivity", "mouthfeel": "crisp-numbing-dissolving"},
"environment": {"weather": "snow", "temperature_c": -2, "humidity_pct": 80},
    },
    "wind": {
        "category": "atmosphere",
        "sound": {"sources": ["wind-howl", "flag-snap", "loose-object-rattle", "whistling-through-gaps"], "absorption_mod": 0.2},
        "smell": {"compounds": ["dust", "pollen", "distant-source"], "volatility_mod": 0.9},
        "sight": {"clarity_mod": 0.7, "light_filter": "clear-but-particles", "reflections": False, "color_temp_K": 6000},
        "touch": {"surfaces": "normal but wind-cooled", "air": "constant directional pressure, hair and clothes animate"},
        "environment": {"wind_speed_kmh": 25, "wind_direction": "from_west"},
    },
    "smoke-haze": {
        "category": "atmosphere",
        "sound": {"sources": ["crackle-distant-maybe", "muffled-mid-range"], "absorption_mod": 0.15},
        "smell": {"compounds": ["particulate-carbon", "guaiacol", "acrolein-irritant", "ash"], "volatility_mod": 1.4},
        "sight": {"clarity_mod": 0.3, "light_filter": "orange-brown-scatter-sun-reddened", "reflections": False, "color_temp_K": 3500},
        "touch": {"surfaces": "ash-film-on-everything", "air": "dry, warm, throat-scratching, eyes-watering"},
        "taste": {"compounds": ["creosote", "guaiacol", "PAH", "carbon-particle"], "profile": {"bitter": 0.6, "umami": 0.3, "sweet": 0.1}, "intensity": 0.6, "note": "guaiacol is the smoky taste compound — same molecule in smoked meat, wood smoke is umami-adjacent because cooking made food safer, the tongue evolved to like it", "mouthfeel": "dry-acrid-coating"},
"environment": {"humidity_pct": 25},
    },
    "dust-heavy": {
        "category": "atmosphere",
        "sound": {"sources": ["silence-thick", "grit-crunch"], "absorption_mod": 0.1},
        "smell": {"compounds": ["mineral-powder", "organic-decomposition", "fiber-fragments"], "volatility_mod": 0.8},
        "sight": {"clarity_mod": 0.4, "light_filter": "warm-tone-mie-scatter-beams-visible", "reflections": False, "color_temp_K": 4500},
        "touch": {"surfaces": "film-on-everything-gritty", "air": "dry, particles-in-throat, eyes-itch"},
        "environment": {"humidity_pct": 20},
    },
    "steam": {
        "category": "atmosphere",
        "sound": {"sources": ["hiss", "drip-condensation", "pipe-rattle"], "absorption_mod": 0.2},
        "smell": {"compounds": ["mineral-hot-water", "chlorine-trace", "pipe-metal"], "volatility_mod": 1.5},
        "sight": {"clarity_mod": 0.3, "light_filter": "white-diffuse-glow", "reflections": True, "color_temp_K": 6500},
        "touch": {"surfaces": "wet-warm-slick-everything", "air": "hot-moist, lungs-full, skin-instantly-damp"},
        "taste": {"compounds": ["distilled-water-vapor", "mineral-if-source-mineral"], "profile": {"sweet": 0.1}, "intensity": 0.2, "note": "steam is distilled water — nearly tasteless but hot, thermal sensors overwhelm taste sensors above 60C, steam taste is mostly pain-as-information", "mouthfeel": "smooth-warm-coating"},
"environment": {"humidity_pct": 100, "temperature_c": 35},
    },
    "night": {
        "category": "atmosphere",
        "sound": {"sources": ["insects-or-silence", "distant-traffic-or-nothing", "footstep-echo-louder", "owl-or-machinery"], "absorption_mod": 0.05},
        "smell": {"compounds": ["night-blooming-jasmine", "cooling-earth", "dew-forming", "reduced-pollution"], "volatility_mod": 0.8},
        "sight": {"clarity_mod": 0.15, "light_filter": "scotopic-blue-shift-pools-of-artificial", "reflections": True, "color_temp_K": 7500},
        "touch": {"surfaces": "cooling-dew-condensing", "air": "cool, still or light breeze, goosebumps, exposed skin aware"},
        "environment": {"time_of_day": "night", "temperature_c": 12},
    },
    "morning": {
        "category": "atmosphere",
        "sound": {"sources": ["birdsong-dawn", "delivery-trucks", "first-footsteps", "shutters-opening"], "absorption_mod": 0.1},
        "smell": {"compounds": ["dew", "coffee-first", "bread-baking", "cool-earth"], "volatility_mod": 0.9},
        "sight": {"clarity_mod": 0.8, "light_filter": "clean-cool-blue-low-angle", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "dew-wet, cold from night", "air": "crisp, clean, the body wakes up to coolness"},
        "environment": {"time_of_day": "morning", "temperature_c": 14, "humidity_pct": 70},
    },
    "midday-harsh": {
        "category": "atmosphere",
        "sound": {"sources": ["heat-shimmer-hum", "insect-buzz-loud", "silence-oppressive"], "absorption_mod": 0.0},
        "smell": {"compounds": ["hot-asphalt", "heated-vegetation", "ozone-uv", "sweat"], "volatility_mod": 1.5},
        "sight": {"clarity_mod": 0.9, "light_filter": "high-color-temp-harsh-shadows-no-subtlety", "reflections": True, "color_temp_K": 6000},
        "touch": {"surfaces": "hot-to-touch-metal-burns, concrete-radiates", "air": "heat pressing on skin, dry, seeking shade"},
        "environment": {"time_of_day": "midday", "temperature_c": 35, "humidity_pct": 30},
    },
    "golden-hour": {
        "category": "atmosphere",
        "sound": {"sources": ["settling-quiet", "birds-evening", "distant-music-maybe", "wind-dying"], "absorption_mod": 0.05},
        "smell": {"compounds": ["cooling-air", "dinner-cooking-distant", "grass-releasing-heat", "flowers-evening"], "volatility_mod": 1.0},
        "sight": {"clarity_mod": 0.9, "light_filter": "3000K-warm-long-shadows-everything-golden", "reflections": True, "color_temp_K": 3200},
        "touch": {"surfaces": "warm-from-day-still, cooling-begins", "air": "warm but easing, gentle, comfortable"},
        "environment": {"time_of_day": "golden_hour", "temperature_c": 22},
    },
    "fluorescent-lit": {
        "category": "atmosphere",
        "sound": {"sources": ["fluorescent-buzz-60hz", "ballast-hum", "institutional-quiet"], "absorption_mod": 0.0},
        "smell": {"compounds": ["nothing-clinical", "cleaning-product-residue", "recycled-air"], "volatility_mod": 0.9},
        "sight": {"clarity_mod": 0.95, "light_filter": "4100K-flat-shadowless-institutional", "reflections": True, "color_temp_K": 4200},
        "touch": {"surfaces": "clinical-smooth-surfaces", "air": "dry-conditioned, no character, the air of nowhere"},
        "environment": {"indoor": True},
    },
    "candlelit": {
        "category": "atmosphere",
        "sound": {"sources": ["flame-sputter", "wax-drip", "wick-hiss", "silence-intimate"], "absorption_mod": 0.0},
        "smell": {"compounds": ["beeswax", "paraffin", "smoke-trace", "warm-air"], "volatility_mod": 1.1},
        "sight": {"clarity_mod": 0.4, "light_filter": "1800K-flicker-moving-shadows-warm-pool", "reflections": True, "color_temp_K": 1800},
        "touch": {"surfaces": "warmth-radiant-from-flame-close", "air": "warm pocket near flame, cool beyond, convection current upward"},
        "environment": {},
    },
    "underwater": {
        "category": "atmosphere",
        "sound": {"sources": ["pressure-hum", "bubble-stream", "muffled-everything", "hull-ping-distant", "own-breathing-loud"],
                  "absorption_mod": 0.4},
        "smell": {"compounds": ["salt-mineral", "rubber-regulator", "nothing-sealed"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.3, "light_filter": "blue-green-filtered-depth-dependent", "reflections": False, "color_temp_K": 7500},
        "touch": {"surfaces": "pressure-all-over, cold-enveloping, current-directional", "air": "not air — water, pressure on eardrums, cold seeping through suit"},
        "taste": {"compounds": ["sodium-chloride-35ppt", "magnesium-chloride", "calcium-sulfate", "potassium"], "profile": {"salt": 0.9, "bitter": 0.4, "umami": 0.1}, "intensity": 0.9, "note": "seawater at 35 parts per thousand — the ocean tastes like blood because blood evolved from ocean: same ions, lower concentration", "mouthfeel": "smooth-saline-pressure"},
"environment": {"humidity_pct": 100, "temperature_c": 8, "wind_speed_kmh": 0},
    },
    "rain-light": {
        "category": "atmosphere",
        "sound": {"sources": ["patter-gentle", "leaf-drip", "gutter-trickle", "umbrella-tap"], "absorption_mod": 0.15},
        "smell": {"compounds": ["petrichor", "wet-earth", "ozone-light", "green-released"], "volatility_mod": 1.2},
        "sight": {"clarity_mod": 0.7, "light_filter": "grey-soft-diffused-no-shadows", "reflections": True, "color_temp_K": 6500},
        "touch": {"surfaces": "mist-on-face, intermittent-drops", "air": "cool, fresh, gentle moisture on exposed skin"},
        "environment": {"weather": "rain", "humidity_pct": 80, "wind_speed_kmh": 5},
    },
    "breeze": {
        "category": "atmosphere",
        "sound": {"sources": ["leaf-rustle", "fabric-flutter", "wind-chime", "gentle-whistle"], "absorption_mod": 0.05},
        "smell": {"compounds": ["carried-scent-from-distance", "flowers-if-nearby", "fresh-air"], "volatility_mod": 1.1},
        "sight": {"clarity_mod": 1.0, "light_filter": "clear-movement-in-vegetation", "reflections": False, "color_temp_K": 6000},
        "touch": {"surfaces": "unchanged", "air": "gentle cooling on skin, hair moves, clothing shifts, pleasant"},
        "environment": {"wind_speed_kmh": 8},
    },
    "neon-lit": {
        "category": "atmosphere",
        "sound": {"sources": ["transformer-buzz", "gas-tube-hum", "electrical-crackle"], "absorption_mod": 0.0},
        "smell": {"compounds": ["ozone-trace", "rain-on-asphalt-if-wet", "nothing-electric"], "volatility_mod": 0.9},
        "sight": {"clarity_mod": 0.6, "light_filter": "colored-harsh-neon-wet-surface-reflections", "reflections": True, "color_temp_K": 4500},
        "touch": {"surfaces": "unchanged", "air": "warmth radiating from signs close up, otherwise ambient"},
        "environment": {},
    },
    "starlight": {
        "category": "atmosphere",
        "sound": {"sources": ["near-silence", "wind-if-open", "insects-night", "own-breathing"], "absorption_mod": 0.0},
        "smell": {"compounds": ["night-air-clean", "dew", "cooling-earth"], "volatility_mod": 0.7},
        "sight": {"clarity_mod": 0.05, "light_filter": "scotopic-monochrome-faint-silver", "reflections": False, "color_temp_K": 4100},
        "touch": {"surfaces": "dew-forming-on-everything", "air": "cold, vast, exposed, sky feels close"},
        "environment": {"time_of_day": "night", "temperature_c": 8},
    },
    "firelight": {
        "category": "atmosphere",
        "sound": {"sources": ["fire-crackle", "spark-pop", "wood-shift", "flame-roar-low"], "absorption_mod": 0.0},
        "smell": {"compounds": ["woodsmoke", "guaiacol", "hot-resin", "charcoal", "ember-ash"], "volatility_mod": 1.3},
        "sight": {"clarity_mod": 0.4, "light_filter": "1800K-flicker-orange-moving-shadows-dance", "reflections": True, "color_temp_K": 1800},
        "touch": {"surfaces": "radiantly-hot-near-fire, cold-away-from-fire", "air": "face hot, back cold — two temperatures at once, smoke stings eyes"},
        "environment": {"temperature_c": 20},
    },
    "electrical-storm": {
        "category": "atmosphere",
        "sound": {"sources": ["thunder-crack-rumble", "rain-heavy-maybe", "wind-gusting", "electrical-sizzle"],
                  "absorption_mod": 0.1},
        "smell": {"compounds": ["ozone-strong", "rain-coming", "ionized-air", "dust-stirred"], "volatility_mod": 1.3},
        "sight": {"clarity_mod": 0.4, "light_filter": "flash-white-then-dark-afterimage", "reflections": True, "color_temp_K": 5000},
        "touch": {"surfaces": "static-charge-hair-rises, metal-tingles", "air": "pressure-drop, charged, wind erratic, temperature unstable"},
        "environment": {"wind_speed_kmh": 25, "humidity_pct": 80},
    },
    "stagnant": {
        "category": "atmosphere",
        "sound": {"sources": ["nothing-dead-air", "insect-buzz-if-warm"], "absorption_mod": 0.0},
        "smell": {"compounds": ["accumulated-everything", "body-odor-lingers", "dust-settled", "whatever-is-here-concentrated"], "volatility_mod": 1.4},
        "sight": {"clarity_mod": 0.8, "light_filter": "haze-from-accumulated-particles", "reflections": False, "color_temp_K": 4200},
        "touch": {"surfaces": "unchanged", "air": "thick, warm, no movement, sweat doesn't evaporate, oppressive"},
        "environment": {"wind_speed_kmh": 0, "humidity_pct": 70},
    },
    "no-light": {
        "category": "atmosphere",
        "sound": {"sources": ["hearing-amplified", "spatial-anxiety-sounds-closer", "own-breathing-dominant"], "absorption_mod": 0.0},
        "smell": {"compounds": ["smell-amplified", "awareness-heightened"], "volatility_mod": 1.3},
        "sight": {"clarity_mod": 0.0, "light_filter": "nothing-absolute-black", "reflections": False, "color_temp_K": 0},
        "touch": {"surfaces": "touch-becomes-primary-sense, hands-leading", "air": "spatial awareness collapses to arm's length"},
        "environment": {},
    },

    # ─── ACTIVITY / HUMAN LAYERS ──────────────────────────────
    "crowd": {
        "category": "activity",
        "sound": {"sources": ["voices-layered", "laughter", "footsteps-many", "music-snippets", "phone-rings"], "absorption_mod": 0.05},
        "smell": {"compounds": ["perfume-mixed", "sweat", "food", "fabric", "breath"], "volatility_mod": 1.1},
        "sight": {"clarity_mod": 0.6, "light_filter": "movement-busy", "reflections": False, "color_temp_K": 4200},
        "touch": {"surfaces": "bodies-brushing-past", "air": "warm from body heat, displaced air from movement"},
        "environment": {"temperature_c": 24, "humidity_pct": 60},
    },
    "silence": {
        "category": "activity",
        "sound": {"sources": ["near-nothing", "blood-in-ears", "building-settling"], "absorption_mod": 0.5},
        "smell": {"compounds": ["stale-air", "dust", "own-breath"], "volatility_mod": 0.8},
        "sight": {"clarity_mod": 1.0, "light_filter": "unchanged", "reflections": False, "color_temp_K": 4200},
        "touch": {"surfaces": "still", "air": "dead still, no air movement, thermal equilibrium with the room"},
        "environment": {"wind_speed_kmh": 0},
    },
    "machinery-active": {
        "category": "activity",
        "sound": {"sources": ["engine-rhythm", "belt-whir", "compressor-cycle", "metal-on-metal", "vibration-floor"], "absorption_mod": 0.1},
        "smell": {"compounds": ["machine-oil", "grease-hot", "rubber-belt", "ozone-electrical", "diesel-or-electric"], "volatility_mod": 1.2},
        "sight": {"clarity_mod": 0.7, "light_filter": "movement-industrial", "reflections": True, "color_temp_K": 4200},
        "touch": {"surfaces": "vibration-through-floor-and-walls, heat-radiant-from-motors", "air": "warm, oily, vibrating",
                  "vibration": {"frequency_hz": 50, "amplitude": "strong", "source": "electric motors and belt drives"}},
        "environment": {"temperature_c": 25},
    },
    "machinery-dead": {
        "category": "activity",
        "sound": {"sources": ["silence-where-hum-should-be", "cooling-metal-tick", "drip-from-condensation", "settling-creak"], "absorption_mod": 0.2},
        "smell": {"compounds": ["stale-oil", "cold-grease", "dust-on-metal", "rust-forming"], "volatility_mod": 0.7},
        "sight": {"clarity_mod": 0.8, "light_filter": "still-machines-frozen-mid-gesture", "reflections": False, "color_temp_K": 4200},
        "touch": {"surfaces": "cold-machines-that-should-be-warm, oil-film-old", "air": "still, cooling, the absence of vibration is a sensation"},
        "environment": {},
    },
    "fire": {
        "category": "activity",
        "sound": {"sources": ["crackling", "popping", "roar-low", "wood-settling"], "absorption_mod": 0.0},
        "smell": {"compounds": ["woodsmoke", "guaiacol", "creosote", "charcoal", "hot-resin"], "volatility_mod": 1.4},
        "sight": {"clarity_mod": 0.7, "light_filter": "warm-flickering-1800K-moving-shadows", "reflections": True, "color_temp_K": 2400},
        "touch": {"surfaces": "hot-near-fire, cold-behind-you", "air": "radiant heat on face, cool at back — two temperatures at once"},
        "taste": {"compounds": ["carbon-particle", "creosote", "combustion-gas"], "profile": {"bitter": 0.5, "umami": 0.2, "chemical-burn": 0.2}, "intensity": 0.5, "note": "woodsmoke is bitter from PAHs but umami-tinged from pyrolysis, your mouth waters near a fire because the tongue detects food-adjacent chemistry", "mouthfeel": "dry-burning-parched"},
"environment": {"temperature_c": 25},
    },
    "cooking": {
        "category": "activity",
        "sound": {"sources": ["sizzle", "pot-bubble", "knife-on-board", "exhaust-fan", "timer-beep"], "absorption_mod": 0.1},
        "smell": {"compounds": ["maillard-reaction", "allium-volatile", "fat-rendering", "spice-aerosolized", "steam-food"], "volatility_mod": 1.5},
        "sight": {"clarity_mod": 0.8, "light_filter": "warm-steam-rises-visible", "reflections": True, "color_temp_K": 2400},
        "touch": {"surfaces": "counter-smooth, pan-handle-hot, steam-on-face", "air": "warm, moist, hunger-triggering"},
        "taste": {"compounds": ["maillard-products", "fat-aerosol", "allium-volatile", "sugar-caramel"], "profile": {"umami": 0.7, "sweet": 0.3, "fat": 0.5, "salt": 0.3}, "intensity": 0.8, "note": "cooking air is tasteable — fat aerosols deliver flavor without eating, standing near a grill your mouth is already eating", "mouthfeel": "rich-oily-savory"},
"environment": {"temperature_c": 26, "humidity_pct": 65},
    },
    "decay-organic": {
        "category": "activity",
        "sound": {"sources": ["insect-buzz", "drip", "soft-collapse", "silence-oppressive"], "absorption_mod": 0.2},
        "smell": {"compounds": ["putrescine", "cadaverine", "hydrogen-sulfide", "ammonia", "fungal-bloom"], "volatility_mod": 1.6},
        "sight": {"clarity_mod": 0.7, "light_filter": "discoloration-mold-patterns", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "soft-where-should-be-hard, damp, spongy, wrong", "air": "thick, gagging, warm from decomposition heat"},
        "taste": {"compounds": ["putrescine", "cadaverine", "hydrogen-sulfide", "ammonia"], "profile": {"bitter": 0.8, "chemical-burn": 0.4}, "intensity": 0.7, "note": "the tongue rejects decay at nanogram concentrations — putrescine triggers immediate gag reflex, the oldest taste response: a survival veto deeper than preference", "mouthfeel": "slimy-acrid-coating"},
"environment": {"humidity_pct": 80, "temperature_c": 20},
    },
    "water-flowing": {
        "category": "activity",
        "sound": {"sources": ["rushing-continuous", "splash-irregular", "gurgle-turbulence", "spray-hiss"], "absorption_mod": 0.2},
        "smell": {"compounds": ["mineral-water", "ozone-spray", "wet-rock", "algae-if-slow"], "volatility_mod": 1.1},
        "sight": {"clarity_mod": 0.8, "light_filter": "reflective-moving-white-foam", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "spray-on-skin, mist-in-air, wet-rock-slippery", "air": "cool, humid, negative-ion-fresh, mist-on-face",
                  "vibration": {"frequency_hz": 5, "amplitude": "subtle", "source": "turbulent water flow"}},
        "environment": {"humidity_pct": 75},
    },
    "electrical": {
        "category": "activity",
        "sound": {"sources": ["transformer-hum-50-60hz", "relay-click", "capacitor-whine", "arc-snap"], "absorption_mod": 0.0},
        "smell": {"compounds": ["ozone", "hot-insulation", "copper-warm", "plastic-off-gas"], "volatility_mod": 1.0},
        "sight": {"clarity_mod": 0.8, "light_filter": "indicator-lights-blinking-status", "reflections": False, "color_temp_K": 5000},
        "touch": {"surfaces": "panel-metal-warm, vibration-subtle, static-charge-hair-rises", "air": "warm, dry, tingling-if-high-voltage-nearby",
                  "vibration": {"frequency_hz": 60, "amplitude": "imperceptible", "source": "transformer hum at AC frequency"}},
        "environment": {"temperature_c": 24},
    },

    "fairground-mechanical": {
        "category": "activity",
        "sound": {"sources": ["calliope-distant", "metal-creak-rhythmic", "chain-rattle", "generator-diesel",
                               "tin-speaker-distorted", "ride-mechanism-grind", "wind-through-structure"],
                  "absorption_mod": 0.05},
        "smell": {"compounds": ["cotton-candy-sugar", "machine-grease", "diesel-exhaust", "rust-paint-flaking",
                                 "popcorn-stale", "vinyl-tent", "sawdust-old"], "volatility_mod": 1.2},
        "sight": {"clarity_mod": 0.7, "light_filter": "painted-metal-faded-primary-colors", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "painted-metal-chipped, ticket-booth-wood-splintered, cable-greasy, seat-vinyl-cracked",
                  "air": "open but sheltered by structures, grease-film on surfaces",
                  "thermal_conductivity_dominant": None,
                  "vibration": {"frequency_hz": 8, "amplitude": "moderate", "source": "ride mechanism motors and chain drives"}},
        "taste": {"compounds": ["cotton-candy-maltol", "popcorn-diacetyl", "grease-aerosol", "rust-particle"], "profile": {"sweet": 0.5, "fat": 0.3, "metallic": 0.2, "bitter": 0.1}, "intensity": 0.5, "note": "sugar and grease — maltol arrives first, fat coats the tongue, then metallic edge from aging rides, the taste of a carnival is optimism slowly rusting", "mouthfeel": "oily-metallic-sweet"},
"environment": {},
    },

    # ─── LEGACY COMPATIBILITY (map old names → new) ──────────
    "urban": {
        "category": "atmosphere",
        "sound": {"sources": ["traffic", "footsteps", "voices", "sirens-distant", "ventilation-hum"], "absorption_mod": 0.1},
        "smell": {"compounds": ["exhaust", "asphalt", "food-vendors", "concrete-dust", "cigarette-drift"], "volatility_mod": 1.0},
        "sight": {"clarity_mod": 0.8, "light_filter": "mixed-artificial", "reflections": False, "color_temp_K": 4500},
        "touch": {"surfaces": "hard-concrete-asphalt", "air": "turbulent from traffic, warm updrafts from grates",
                  "vibration": {"frequency_hz": 15, "amplitude": "subtle", "source": "traffic and subway rumble through ground"}},
        "environment": {"indoor": False},
    },
    "forest": {
        "category": "atmosphere",
        "sound": {"sources": ["birdsong", "wind-in-leaves", "branch-creak", "insect-buzz", "stream-maybe"], "absorption_mod": 0.3},
        "smell": {"compounds": ["pine", "leaf-mold", "moss", "earth", "resin", "chlorophyll"], "volatility_mod": 1.1},
        "sight": {"clarity_mod": 0.7, "light_filter": "green-dappled", "reflections": False, "color_temp_K": 6000},
        "touch": {"surfaces": "bark-rough, leaf-litter-soft, moss-damp", "air": "still, cool, filtered through canopy"},
        "environment": {"indoor": False, "humidity_pct": 65, "wind_speed_kmh": 3},
    },
    "ocean": {
        "category": "atmosphere",
        "sound": {"sources": ["waves-breaking", "seabird-cry", "wind-constant", "pebble-rattle"], "absorption_mod": 0.1},
        "smell": {"compounds": ["salt", "seaweed", "iodine", "fish", "ozone"], "volatility_mod": 1.2},
        "sight": {"clarity_mod": 0.9, "light_filter": "bright-reflected", "reflections": True, "color_temp_K": 7000},
        "touch": {"surfaces": "sand-shifting, rock-salt-crusted, wet", "air": "salt-wind on face, persistent breeze",
                  "vibration": {"frequency_hz": 0.2, "amplitude": "imperceptible", "source": "ocean wave cycles (0.1-0.3 Hz)"}},
        "taste": {"compounds": ["sea-salt-aerosol", "DMS-dimethyl-sulfide", "iodine"], "profile": {"salt": 0.7, "umami": 0.2, "bitter": 0.1}, "intensity": 0.5, "note": "sea air is salt air — NaCl aerosol lands on the tongue before you reach the water, you taste the ocean before you see it", "mouthfeel": "saline-smooth-mineral"},
"environment": {"indoor": False, "wind_speed_kmh": 15, "humidity_pct": 75},
    },
    "industrial": {
        "category": "activity",
        "sound": {"sources": ["machinery-hum", "metal-clang", "ventilation-roar", "beeping-reversing"], "absorption_mod": 0.15},
        "smell": {"compounds": ["diesel", "grease", "hot-metal", "rubber", "concrete-dust"], "volatility_mod": 1.0},
        "sight": {"clarity_mod": 0.6, "light_filter": "sodium-harsh", "reflections": True, "color_temp_K": 4500},
        "touch": {"surfaces": "metal-cold-greasy, concrete-gritty", "air": "warm from machines, vibrating through floors",
                  "vibration": {"frequency_hz": 40, "amplitude": "strong", "source": "industrial machinery and conveyor systems"}},
        "environment": {"indoor": False, "temperature_c": 20},
    },
    "domestic": {
        "category": "activity",
        "sound": {"sources": ["refrigerator-hum", "clock-tick", "heating-creak", "muffled-outside"], "absorption_mod": 0.3},
        "smell": {"compounds": ["laundry", "cooking", "wood-polish", "dust-home", "soap"], "volatility_mod": 1.0},
        "sight": {"clarity_mod": 1.0, "light_filter": "warm-interior", "reflections": False, "color_temp_K": 3000},
        "touch": {"surfaces": "fabric-soft, wood-warm, carpet-underfoot", "air": "still, warm, controlled — the body relaxes"},
        "environment": {"indoor": True, "temperature_c": 21, "humidity_pct": 45, "wind_speed_kmh": 0},
    },
    "water": {
        "category": "atmosphere",
        "sound": {"sources": ["lapping", "stream-gurgle", "dripping", "splash"], "absorption_mod": 0.2},
        "smell": {"compounds": ["lake-water", "algae", "wet-stone", "mineral"], "volatility_mod": 1.0},
        "sight": {"clarity_mod": 0.8, "light_filter": "reflective-surface", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "wet-stone, muddy-bank, cool", "air": "humid, cool near water surface, mist on face"},
        "environment": {"humidity_pct": 75},
    },
    # --- BATCH 2: Gap-fill primitives ---

    "volcanic": {
        "category": "spatial",
        "materials": ["stone-limestone", "ash-charite", "sand"],
        "sound": {
            "sources": ["deep-rumble", "hissing-vent", "rock-crack", "gas-escape", "gravel-shift"],
            "absorption_mod": 0.02,
            "rt60_s": 0.3
        },
        "smell": {
            "compounds": ["sulfur-dioxide", "hydrogen-sulfide", "mineral-hot", "heated-rock", "volcanic-gas"],
            "volatility_mod": 1.6
        },
        "sight": {
            "clarity_mod": 0.4,
            "light_filter": "haze-yellow-sulfurous",
            "reflections": False,
            "color_temp_K": 2200
        },
        "touch": {
            "surfaces": "basalt-rough-sharp, pumice-abrasive, obsidian-glass-smooth",
            "air": "searing dry heat radiating from ground, sulfurous sting in nostrils and throat",
            "thermal_conductivity_dominant": 1.5
        ,
                  "vibration": {"frequency_hz": 2, "amplitude": "moderate", "source": "seismic tremors and magma movement"}},
        "taste": {
            "compounds": ["sulfur-dioxide", "calcium-ite", "mineral-ite"],
            "mouthfeel": "gritty",
            "profile": {"bitter": 0.6, "metallic": 0.5, "chemical-burn": 0.7, "sour": 0.3},
            "intensity": 0.8,
            "note": "volcanic air tastes like burnt matches and battery acid, SO2 triggers pain receptors before taste receptors"
        },
        "environment": {
            "indoor": False,
            "temperature_c": 45,
            "humidity_pct": 20,
            "wind_speed_kmh": 15
        }
    },

    "space-station": {
        "category": "spatial",
        "materials": ["aluminum", "stainless-steel", "rubber-plastic"],
        "sound": {
            "sources": ["fan-constant", "pump-hydraulic", "electrical-hum-60hz", "air-recycler", "beep-alert", "velcro-rip"],
            "absorption_mod": 0.1,
            "rt60_s": 0.4
        },
        "smell": {
            "compounds": ["recycled-air", "ozone-electrical", "plastic-offgas", "metal-warm", "body-odor-contained"],
            "volatility_mod": 0.8
        },
        "sight": {
            "clarity_mod": 1.0,
            "light_filter": "artificial-white-5000K-no-shadow-variation",
            "reflections": True,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "smooth-aluminum-panels, rubber-grip-handles, velcro-strips-everywhere",
            "air": "perfectly controlled 22C, dry, the same temperature everywhere, no gradient exists",
            "thermal_conductivity_dominant": 205.0
        },
        "taste": {
            "compounds": ["recycled-water-flat", "metal-trace", "plastic-trace"],
            "mouthfeel": "metallic-smooth",
            "profile": {"metallic": 0.4, "chalky": 0.3, "bitter": 0.2},
            "intensity": 0.3,
            "note": "water tastes flat because it has been recycled from urine and sweat through distillation, all minerals stripped"
        },
        "environment": {
            "indoor": True,
            "temperature_c": 22,
            "humidity_pct": 40,
            "wind_speed_kmh": 0
        }
    },

    "sterile-medical": {
        "category": "activity",
        "sound": {
            "sources": ["monitor-beep", "ventilator-rhythm", "fluorescent-buzz", "shoe-squeak-on-floor", "intercom-page"],
            "absorption_mod": 0.15
        },
        "smell": {
            "compounds": ["isopropyl-alcohol", "chlorhexidine", "latex", "iodine", "sterile-gauze", "hand-sanitizer"],
            "volatility_mod": 1.3
        },
        "sight": {
            "clarity_mod": 1.0,
            "light_filter": "fluorescent-harsh-5500K-no-shadows",
            "reflections": True,
            "color_temp_K": 4200
        },
        "touch": {
            "surfaces": "nitrile-glove-smooth, stainless-instrument-cold, vinyl-floor-yielding",
            "air": "aggressively conditioned, dry, the smell of nothing that took chemicals to achieve"
        },
        "taste": {
            "compounds": ["latex-dust", "antiseptic-airborne", "nothing-sterile"],
            "mouthfeel": "gritty",
            "profile": {"bitter": 0.3, "chemical-burn": 0.4, "metallic": 0.2},
            "intensity": 0.4,
            "note": "hospitals taste like the absence of biology, antiseptic compounds coat the soft palate through breathing"
        },
        "environment": {
            "indoor": True,
            "temperature_c": 20,
            "humidity_pct": 35,
            "wind_speed_kmh": 0
        }
    },

    "seafood-fish": {
        "category": "activity",
        "sound": {
            "sources": ["ice-crunch", "knife-on-board", "vendor-shout", "hose-spray", "crate-slam", "scale-scrape"],
            "absorption_mod": 0.1
        },
        "smell": {
            "compounds": ["trimethylamine", "ocean-brine", "fish-oil", "seaweed-iodine", "crushed-ice", "blood-iron", "citrus-lemon"],
            "volatility_mod": 1.5
        },
        "sight": {
            "clarity_mod": 0.9,
            "light_filter": "wet-reflective-surfaces",
            "reflections": True,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "wet-concrete-cold, fish-scale-slick, crushed-ice-numbing, rubber-apron",
            "air": "cold humid, mist from ice and hose water, perpetually damp"
        },
        "taste": {
            "compounds": ["sea-salt-air", "trimethylamine-inhaled", "iodine-seaweed"],
            "mouthfeel": "dry",
            "profile": {"salt": 0.7, "umami": 0.6, "bitter": 0.2, "fat": 0.3},
            "intensity": 0.7,
            "note": "fish market air is so thick with trimethylamine you can taste it, salt and umami coat the tongue from breathing alone"
        },
        "environment": {
            "temperature_c": 8,
            "humidity_pct": 80,
            "wind_speed_kmh": 2
        }
    },

    "tropical": {
        "category": "atmosphere",
        "sound": {
            "sources": ["insect-chorus", "bird-call-tropical", "drip-canopy", "frog-croak", "cicada-buzz", "monkey-howl"],
            "absorption_mod": 0.4
        },
        "smell": {
            "compounds": ["rotting-vegetation", "flower-frangipani", "wet-earth-petrichor", "tree-resin", "fruit-overripe", "mold-warm"],
            "volatility_mod": 1.6
        },
        "sight": {
            "clarity_mod": 0.5,
            "light_filter": "green-filtered-canopy-dappled",
            "reflections": False,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "leaf-wet-broad, bark-rough-damp, vine-smooth, mud-sucking-at-feet",
            "air": "thick, saturated, like breathing through a warm wet cloth"
        },
        "taste": {
            "compounds": ["humidity-pure", "flower-nectar-air", "decay-sweet"],
            "mouthfeel": "viscous",
            "profile": {"sweet": 0.4, "bitter": 0.3, "umami": 0.2},
            "intensity": 0.5,
            "note": "tropical air is so humid it has taste, sweet decomposition and flower nectar arrive on the tongue with every breath"
        },
        "environment": {
            "indoor": False,
            "temperature_c": 32,
            "humidity_pct": 95,
            "wind_speed_kmh": 3
        }
    },

    "baking-kitchen": {
        "category": "activity",
        "sound": {
            "sources": ["oven-tick", "timer-beep", "mixer-whir", "dough-slap", "pan-clatter", "kettle-whistle"],
            "absorption_mod": 0.25
        },
        "smell": {
            "compounds": ["maillard-bread", "butter-melting", "vanilla-extract", "cinnamon", "yeast-alive", "sugar-caramelizing", "flour-dust"],
            "volatility_mod": 1.4
        },
        "sight": {
            "clarity_mod": 0.9,
            "light_filter": "warm-interior-steam-diffused",
            "reflections": False,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "flour-dusted-counter, warm-oven-door-radiant, dough-yielding-elastic",
            "air": "warm, humid from oven steam, flour particles suspended"
        },
        "taste": {
            "compounds": ["sugar-airborne", "butter-vaporized", "yeast-tang", "vanilla-volatile"],
            'mouthfeel': 'starchy-warm-smooth',
            "profile": {"sweet": 0.8, "fat": 0.6, "salt": 0.3, "umami": 0.2},
            "intensity": 0.7,
            "note": "a baking kitchen makes you salivate before you eat anything, retronasal pathway carries Maillard compounds directly to taste receptors"
        },
        "environment": {
            "indoor": True,
            "temperature_c": 26,
            "humidity_pct": 60,
            "wind_speed_kmh": 0
        }
    },

    "solar-flare": {
        "category": "atmosphere",
        "sound": {
            "sources": ["alarm-klaxon", "radiation-counter-clicking", "hull-stress-groan", "comm-static"],
            "absorption_mod": 0.0
        },
        "smell": {
            "compounds": ["ozone-sharp", "heated-electronics", "solder-flux"],
            "volatility_mod": 1.0
        },
        "sight": {
            "clarity_mod": 0.8,
            "light_filter": "emergency-red-strobing",
            "reflections": True,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "metal-panels-warm-from-radiation, vibration-through-hull",
            "air": "static-charged, hair stands on end, metallic taste in mouth"
        },
        "taste": {
            "compounds": ["ozone", "copper-ion", "adrenaline-metallic"],
            "mouthfeel": "metallic-smooth",
            "profile": {"metallic": 0.8, "bitter": 0.3, "chemical-burn": 0.2},
            "intensity": 0.6,
            "note": "ionizing radiation produces ozone which tastes metallic-sharp, the copper taste is your own blood vessels reacting"
        },
        "environment": {
            "indoor": True,
            "temperature_c": 28,
            "humidity_pct": 30,
            "wind_speed_kmh": 0
        }
    },

    "nautical": {
        "category": "activity",
        "sound": {
            "sources": ["wave-hull-slap", "rigging-creak", "wind-in-sail", "bell-clang", "gull-cry", "chain-rattle-anchor"],
            "absorption_mod": 0.02
        },
        "smell": {
            "compounds": ["sea-salt", "tar-pitch", "diesel-exhaust", "fish-brine", "rope-hemp", "rust-sea-oxidized"],
            "volatility_mod": 1.3
        },
        "sight": {
            "clarity_mod": 0.8,
            "light_filter": "overcast-maritime-grey-blue",
            "reflections": True,
            "color_temp_K": 7500
        },
        "touch": {
            "surfaces": "rope-rough-salt-crusted, deck-wood-wet, rail-metal-cold-spray",
            "air": "salt spray on face and lips, constant wind, clothing always slightly damp"
        },
        "taste": {
            "compounds": ["sea-salt-lip", "iodine-air", "diesel-trace"],
            "mouthfeel": "oily",
            "profile": {"salt": 0.9, "bitter": 0.2, "umami": 0.2},
            "intensity": 0.6,
            "note": "at sea you taste salt constantly, it crusts on your lips and the air delivers it with every breath"
        },
        "environment": {
            "indoor": False,
            "temperature_c": 14,
            "humidity_pct": 85,
            "wind_speed_kmh": 25
        }
    },

    "christmas-holiday": {
        "category": "activity",
        "sound": {
            "sources": ["music-distant", "wrapping-paper-crinkle", "laughter", "oven-timer", "door-opening-cold-draft"],
            "absorption_mod": 0.3
        },
        "smell": {
            "compounds": ["pine-tree-fresh", "cinnamon", "nutmeg", "clove", "woodsmoke", "roasting-meat", "mulled-wine"],
            "volatility_mod": 1.3
        },
        "sight": {
            "clarity_mod": 0.8,
            "light_filter": "warm-interior-mixed-with-fairy-lights",
            "reflections": True,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "wrapping-paper-smooth, wool-sweater-warm, pine-needle-prick",
            "air": "warm inside, cold draft each time door opens, two temperatures competing"
        },
        "taste": {
            "compounds": ["cinnamon-airborne", "nutmeg-volatile", "sugar-cookie", "mulled-wine-spice"],
            "mouthfeel": "crunchy",
            "profile": {"sweet": 0.7, "bitter": 0.2, "fat": 0.4, "sour": 0.1},
            "intensity": 0.6,
            "note": "Christmas kitchens fill the air with so many volatiles that you taste the season through your nose before any food reaches your mouth"
        },
        "environment": {
            "indoor": True,
            "temperature_c": 23,
            "humidity_pct": 45,
            "wind_speed_kmh": 0
        }
    },

    "northern-lights": {
        "category": "atmosphere",
        "sound": {
            "sources": ["crackle-faint-electromagnetic", "wind-low", "snow-crunch-distant", "absolute-silence"],
            "absorption_mod": 0.01
        },
        "smell": {
            "compounds": ["ozone-faint", "snow-clean", "cold-metallic"],
            "volatility_mod": 0.5
        },
        "sight": {
            "clarity_mod": 1.0,
            "light_filter": "green-purple-curtain-shifting-high-altitude",
            "reflections": True,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "none, everything is sky",
            "air": "biting cold, still, the air itself feels thin and electric"
        },
        "environment": {
            "indoor": False,
            "temperature_c": -15,
            "humidity_pct": 30,
            "wind_speed_kmh": 8
        }
    },

    "insect-active": {
        "category": "activity",
        "sound": {
            "sources": ["mosquito-whine", "cicada-drone", "beetle-click", "fly-buzz", "cricket-chirp"],
            "absorption_mod": 0.0
        },
        "smell": {
            "compounds": ["formic-acid", "pheromone-sweet", "crushed-insect"],
            "volatility_mod": 1.0
        },
        "sight": {
            "clarity_mod": 0.8,
            "light_filter": "unchanged",
            "reflections": False,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "landing-on-skin, web-across-face, bite-itch",
            "air": "things moving through it that you feel before you see"
        },
        "environment": {}
    },

    "spice-market": {
        "category": "activity",
        "sound": {
            "sources": ["vendor-call", "scale-clink", "mortar-pestle-grind", "bag-scoop", "haggling-voices"],
            "absorption_mod": 0.2
        },
        "smell": {
            "compounds": ["cumin", "turmeric", "cardamom", "chili-capsaicin", "saffron", "black-pepper-piperine", "dried-herb"],
            "volatility_mod": 1.8
        },
        "sight": {
            "clarity_mod": 0.7,
            "light_filter": "warm-dust-saturated-color",
            "reflections": False,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "burlap-sack-rough, powder-between-fingers, dried-seed-hard",
            "air": "thick with particulate, capsaicin burns eyes and nose at certain stalls"
        },
        "taste": {
            "compounds": ["capsaicin-airborne", "piperine-inhaled", "cumin-volatile", "turmeric-bitter"],
            "mouthfeel": "burning",
            "profile": {"bitter": 0.5, "chemical-burn": 0.6, "sweet": 0.2, "umami": 0.3},
            "intensity": 0.8,
            "note": "a spice market makes your tongue burn from 10 feet away, capsaicin is volatile enough to trigger pain receptors through air alone"
        },
        "environment": {
            "indoor": False,
            "temperature_c": 30,
            "humidity_pct": 45,
            "wind_speed_kmh": 3
        }
    },
    # --- BATCH 3: Stress-test gap-fill ---

    "pub-bar": {
        "category": "activity",
        "sound": {
            "sources": ["glass-clink", "conversation-loud", "music-live-acoustic", "laughter-burst", "chair-scrape", "dart-thud", "pour-tap"],
            "absorption_mod": 0.25
        },
        "smell": {
            "compounds": ["beer-yeast-hops", "whiskey-ethanol", "wood-polish", "fried-food", "cigarette-stale-embedded", "body-heat-crowd"],
            "volatility_mod": 1.3
        },
        "sight": {
            "clarity_mod": 0.6,
            "light_filter": "warm-dim-amber-wood-reflected",
            "reflections": True,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "bar-top-lacquered-sticky, pint-glass-cold-condensation, leather-booth-cracked",
            "air": "warm from bodies, humid from breath and beer, the temperature of a room that has been occupied for hours"
        },
        "taste": {
            "compounds": ["beer-hop-bitter", "ethanol-vapor", "peanut-salt-air"],
            "mouthfeel": "dry",
            "profile": {"bitter": 0.6, "salt": 0.3, "sweet": 0.2, "umami": 0.2},
            "intensity": 0.5,
            "note": "pubs taste like hops and salt before you order anything, ethanol vapor from open taps reaches the tongue through breathing"
        },
        "environment": {
            "indoor": True,
            "temperature_c": 24,
            "humidity_pct": 65,
            "wind_speed_kmh": 0
        }
    },

    "bathhouse-hammam": {
        "category": "spatial",
        "materials": ["tile-ceramic", "marble", "copper-brass"],
        "sound": {
            "sources": ["water-splash-echo", "drip-multiple", "conversation-reverb", "bucket-pour", "scrub-on-stone"],
            "absorption_mod": 0.03,
            "rt60_s": 3.0
        },
        "smell": {
            "compounds": ["eucalyptus-oil", "black-soap-olive", "steam-mineral", "rose-water", "cedar-wood-hot"],
            "volatility_mod": 1.8
        },
        "sight": {
            "clarity_mod": 0.3,
            "light_filter": "diffused-through-steam-warm",
            "reflections": True,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "marble-slab-warm-from-below, tile-smooth-wet, copper-bowl-hot",
            "air": "steam so thick you feel it on your skin as a second layer, water condenses on every surface including you",
            "thermal_conductivity_dominant": 2.5
        },
        "taste": {
            "compounds": ["mineral-water-steam", "eucalyptus-inhaled", "salt-sweat-own"],
            "mouthfeel": "dry",
            "profile": {"salt": 0.5, "bitter": 0.2, "metallic": 0.1},
            "intensity": 0.5,
            "note": "you taste your own salt as you sweat, eucalyptus opens the sinuses so every taste is amplified"
        },
        "environment": {
            "indoor": True,
            "temperature_c": 42,
            "humidity_pct": 98,
            "wind_speed_kmh": 0
        }
    },

    "deep-ocean": {
        "category": "spatial",
        "materials": ["water-surface"],
        "sound": {
            "sources": ["pressure-creak-hull", "sonar-ping-distant", "whale-song-low", "hydrothermal-hiss", "sediment-shift"],
            "absorption_mod": 0.01,
            "rt60_s": 0.2
        },
        "smell": {
            "compounds": ["nothing-sealed-environment", "rubber-seal", "recycled-air-stale"],
            "volatility_mod": 0.3
        },
        "sight": {
            "clarity_mod": 0.0,
            "light_filter": "absolute-black-below-200m-bioluminescence-only",
            "reflections": False,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "viewport-glass-cold-from-2C-water, metal-hull-sweating-condensation",
            "air": "pressurized, dry, the weight of kilometers of water is an abstraction until the hull groans",
            "thermal_conductivity_dominant": 0.6
        },
        "taste": {
            "compounds": ["stale-air-recycled", "metal-condensation"],
            "mouthfeel": "metallic-smooth",
            "profile": {"metallic": 0.4, "chalky": 0.3},
            "intensity": 0.3,
            "note": "you taste the air system working, every breath has been through the scrubbers"
        },
        "environment": {
            "indoor": True,
            "temperature_c": 18,
            "humidity_pct": 70,
            "wind_speed_kmh": 0
        }
    },

    "tornado-extreme": {
        "category": "atmosphere",
        "sound": {
            "sources": ["freight-train-roar", "debris-impact", "glass-shatter", "wood-crack-structural", "pressure-ear-pop", "continuous-howl"],
            "absorption_mod": 0.0
        },
        "smell": {
            "compounds": ["ozone-lightning", "torn-earth", "broken-vegetation", "natural-gas-leak", "dust-massive"],
            "volatility_mod": 2.0
        },
        "sight": {
            "clarity_mod": 0.1,
            "light_filter": "green-black-rotating-dark",
            "reflections": False,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "nothing-stable-to-touch, debris-hitting-skin, hail-stinging",
            "air": "pressure drop makes ears pop, wind strong enough to strip clothing, temperature drops 10C in seconds"
        },
        "taste": {
            "compounds": ["dirt-airborne", "ozone", "blood-bitten-lip"],
            "mouthfeel": "burning",
            "profile": {"metallic": 0.5, "bitter": 0.4, "chalky": 0.6},
            "intensity": 0.9,
            "note": "you taste dirt because the air IS dirt, topsoil carried at 300km/h enters your mouth whether you open it or not"
        },
        "environment": {
            "indoor": False,
            "temperature_c": 12,
            "humidity_pct": 90,
            "wind_speed_kmh": 300
        }
    },

    "mars-surface": {
        "category": "spatial",
        "materials": ["sand", "rust-corroded"],
        "sound": {
            "sources": ["wind-thin-high-pitched", "suit-breathing", "boot-on-regolith", "radio-crackle"],
            "absorption_mod": 0.0,
            "rt60_s": 0.0
        },
        "smell": {
            "compounds": ["nothing-sealed-suit", "own-sweat", "recycled-oxygen"],
            "volatility_mod": 0.0
        },
        "sight": {
            "clarity_mod": 0.6,
            "light_filter": "butterscotch-sky-iron-oxide-dust-scattered",
            "reflections": False,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "regolith-sharp-fine-abrasive, spacesuit-between-you-and-everything",
            "air": "you cannot feel the air because you are sealed from it, touch is mediated through 8 layers of suit material",
            "thermal_conductivity_dominant": 0.0
        },
        "taste": {
            "compounds": ["recycled-water", "suit-rubber-plastic"],
            'mouthfeel': 'gritty-metallic-dry',
            "profile": {"metallic": 0.3, "chalky": 0.2},
            "intensity": 0.2,
            "note": "you taste your own suit, Mars smells like nothing because you are sealed from it, astronauts report regolith smells like gunpowder when brought inside"
        },
        "environment": {
            "indoor": False,
            "temperature_c": -60,
            "humidity_pct": 0,
            "wind_speed_kmh": 20
        }
    },

    "combat-zone": {
        "category": "activity",
        "sound": {
            "sources": ["gunfire-crack", "explosion-distant", "radio-chatter", "helicopter-rotor", "shouting-orders", "ringing-ears-tinnitus"],
            "absorption_mod": 0.0
        },
        "smell": {
            "compounds": ["cordite-gunpowder", "diesel-exhaust", "smoke-burning", "blood-iron", "sweat-adrenaline", "dust-kicked"],
            "volatility_mod": 1.5
        },
        "sight": {
            "clarity_mod": 0.4,
            "light_filter": "smoke-dust-muzzle-flash",
            "reflections": False,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "rifle-stock-warm, ground-prone-dirt-gravel, body-armor-heavy-pressing",
            "air": "concussion waves felt in chest, heat blast from explosions, dirt raining down"
        },
        "taste": {
            "compounds": ["cordite-acrid", "dust-chalk", "adrenaline-copper"],
            "mouthfeel": "chalky",
            "profile": {"bitter": 0.7, "metallic": 0.8, "chemical-burn": 0.3},
            "intensity": 0.9,
            "note": "combat tastes like copper and cordite, the metallic taste is adrenaline dumping copper ions into saliva"
        },
        "environment": {
            "indoor": False,
            "temperature_c": 20,
            "humidity_pct": 35,
            "wind_speed_kmh": 5
        }
    },

    "laundromat": {
        "category": "spatial",
        "materials": ["vinyl-linoleum", "stainless-steel", "glass"],
        "sound": {
            "sources": ["dryer-tumble-rhythm", "washer-spin-cycle", "coin-drop", "zipper-clink-in-dryer", "fluorescent-buzz", "door-chime"],
            "absorption_mod": 0.1,
            "rt60_s": 0.8
        },
        "smell": {
            "compounds": ["detergent-floral", "fabric-softener", "bleach-chlorine", "lint-warm", "dryer-sheet-chemical-sweet"],
            "volatility_mod": 1.2
        },
        "sight": {
            "clarity_mod": 0.9,
            "light_filter": "fluorescent-blue-white-harsh",
            "reflections": True,
            "color_temp_K": 4200
        },
        "touch": {
            "surfaces": "warm-dryer-door-vibrating, plastic-chair-cold, folding-table-laminate, clothes-hot-from-dryer",
            "air": "warm, humid, chemically sweet, the air of clothes being cooked clean"
        },
        "taste": {
            "compounds": ["detergent-volatile", "bleach-trace", "lint-fiber"],
            'mouthfeel': 'soapy-smooth-chemical',
            "profile": {"bitter": 0.3, "sweet": 0.3, "chemical-burn": 0.2},
            "intensity": 0.4,
            "note": "laundromats taste like artificial flowers because fabric softener volatiles coat every surface including your tongue"
        },
        "environment": {
            "indoor": True,
            "temperature_c": 27,
            "humidity_pct": 70,
            "wind_speed_kmh": 0
        }
    },

    "nursery-infant": {
        "category": "activity",
        "sound": {
            "sources": ["baby-cry-distant", "lullaby-music-box", "rocking-chair-creak", "white-noise-machine", "soft-footstep"],
            "absorption_mod": 0.4
        },
        "smell": {
            "compounds": ["baby-powder-talc", "milk-formula", "diaper-fresh", "cotton-clean", "lotion-baby", "warmth-skin"],
            "volatility_mod": 0.8
        },
        "sight": {
            "clarity_mod": 0.7,
            "light_filter": "warm-dim-nightlight-soft",
            "reflections": False,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "blanket-fleece-soft, crib-rail-smooth-wood, carpet-plush, baby-skin-impossibly-soft",
            "air": "warm, still, deliberately controlled, everything in this room is padded"
        },
        "taste": {
            "compounds": ["milk-sweet-air", "talc-powder-inhaled"],
            "mouthfeel": "creamy",
            "profile": {"sweet": 0.5, "chalky": 0.3, "fat": 0.2},
            "intensity": 0.3,
            "note": "nurseries taste like milk and powder, the sweetness is partly real (lactose vapor) and partly associative"
        },
        "environment": {
            "indoor": True,
            "temperature_c": 23,
            "humidity_pct": 50,
            "wind_speed_kmh": 0
        }
    },

    "mechanic-garage": {
        "category": "spatial",
        "materials": ["concrete", "steel-metal", "oil-grease", "rubber-plastic"],
        "sound": {
            "sources": ["impact-wrench-rattle", "compressor-chug", "radio-classic-rock", "wrench-clang", "engine-rev", "hydraulic-lift-whine"],
            "absorption_mod": 0.05,
            "rt60_s": 1.2
        },
        "smell": {
            "compounds": ["motor-oil-10w40", "brake-fluid", "rubber-tire", "exhaust-cold", "degreaser-solvent", "gasoline-vapor"],
            "volatility_mod": 1.4
        },
        "sight": {
            "clarity_mod": 0.7,
            "light_filter": "mixed-fluorescent-and-daylight-from-bay-door",
            "reflections": True,
            "color_temp_K": 4200
        },
        "touch": {
            "surfaces": "oil-slick-concrete, wrench-cold-heavy, tire-rubber-warm-black, grease-between-fingers",
            "air": "cool from open bay doors, gasoline vapor makes the air shimmer near fuel",
            "thermal_conductivity_dominant": 1.7
        ,
                  "vibration": {"frequency_hz": 45, "amplitude": "moderate", "source": "air compressor and impact wrenches"}},
        "taste": {
            "compounds": ["gasoline-vapor-inhaled", "rubber-dust", "metal-shaving"],
            "mouthfeel": "gritty",
            "profile": {"bitter": 0.5, "chemical-burn": 0.4, "metallic": 0.5},
            "intensity": 0.6,
            "note": "you taste gasoline in a garage before you smell it, the volatile hydrocarbons hit taste receptors faster than olfactory"
        },
        "environment": {
            "indoor": True,
            "temperature_c": 18,
            "humidity_pct": 40,
            "wind_speed_kmh": 3
        }
    },

    "swamp-bayou": {
        "category": "spatial",
        "materials": ["water-surface", "wood-old", "moss-lichen", "earth-soil"],
        "sound": {
            "sources": ["insect-drone-constant", "frog-chorus", "bird-call-heron", "water-lap-slow", "branch-crack-animal", "gator-bellow-distant"],
            "absorption_mod": 0.3,
            "rt60_s": 0.4
        },
        "smell": {
            "compounds": ["decay-anaerobic-sulfur", "cypress-terpene", "mud-methane", "algae-green", "stagnant-water", "spanish-moss-musty"],
            "volatility_mod": 1.5
        },
        "sight": {
            "clarity_mod": 0.4,
            "light_filter": "green-filtered-canopy-spanish-moss-curtain",
            "reflections": True,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "mud-sucking-ankle-deep, cypress-knee-rough, water-warm-opaque, mosquito-on-skin",
            "air": "thick, humid, warm, the air has texture, you breathe through it rather than in it",
            "thermal_conductivity_dominant": 0.6
        },
        "taste": {
            "compounds": ["swamp-water-tannin", "algae-iron", "decay-sweet"],
            "mouthfeel": "metallic-smooth",
            "profile": {"bitter": 0.5, "umami": 0.3, "metallic": 0.3, "sweet": 0.2},
            "intensity": 0.6,
            "note": "bayou air tastes like tannin-steeped tea, the cypress trees leach tannins into everything including the humidity you breathe"
        },
        "environment": {
            "indoor": False,
            "temperature_c": 30,
            "humidity_pct": 95,
            "wind_speed_kmh": 2
        }
    },

    "smoke-lounge": {
        "category": "activity",
        "sound": {
            "sources": ["conversation-low-murmur", "hookah-bubble", "pipe-draw", "music-ambient-low", "lighter-flick"],
            "absorption_mod": 0.35
        },
        "smell": {
            "compounds": ["tobacco-pipe-sweet", "opium-floral-heavy", "hashish-resin", "incense-sandalwood", "tea-bergamot", "fabric-smoke-absorbed"],
            "volatility_mod": 1.6
        },
        "sight": {
            "clarity_mod": 0.3,
            "light_filter": "dim-amber-smoke-layered-visible",
            "reflections": False,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "velvet-cushion-deep, brass-pipe-warm, silk-pillow, carpet-thick-layered",
            "air": "smoke stratified in layers, cooler at floor, warmest at ceiling, every breath has texture"
        },
        "taste": {
            "compounds": ["tobacco-alkaloid", "opium-bitter", "tea-tannin", "honey-hookah"],
            "mouthfeel": "astringent",
            "profile": {"bitter": 0.7, "sweet": 0.4, "umami": 0.2, "astringent": 0.3},
            "intensity": 0.8,
            "note": "smoke lounges make the air itself a beverage, you taste everything the room has burned for decades"
        },
        "environment": {
            "indoor": True,
            "temperature_c": 25,
            "humidity_pct": 55,
            "wind_speed_kmh": 0
        }
    },

    "beehive-interior": {
        "category": "spatial",
        "materials": ["wax"],
        "sound": {
            "sources": ["buzz-constant-60hz", "wing-fan-ventilation", "larva-chewing", "queen-piping"],
            "absorption_mod": 0.5,
            "rt60_s": 0.1
        },
        "smell": {
            "compounds": ["beeswax-warm", "honey-raw", "propolis-resin", "royal-jelly", "pheromone-alarm", "flower-pollen-mixed"],
            "volatility_mod": 1.4
        },
        "sight": {
            "clarity_mod": 0.2,
            "light_filter": "amber-dark-hexagonal-geometry",
            "reflections": False,
            "color_temp_K": 5500
        },
        "touch": {
            "surfaces": "wax-comb-warm-35C-yielding, honey-viscous-sticky, propolis-resin-tacky",
            "air": "35C exactly, the hive thermoregulates to this temperature year-round, vibrating from ten thousand wings",
            "thermal_conductivity_dominant": 0.25
        ,
                  "vibration": {"frequency_hz": 200, "amplitude": "subtle", "source": "collective wing beats of thousands of bees"}},
        "taste": {
            "compounds": ["honey-raw-enzymatic", "propolis-bitter-medicinal", "wax-bland", "pollen-dusty-sweet"],
            "mouthfeel": "gritty",
            "profile": {"sweet": 0.9, "bitter": 0.3, "fat": 0.2, "umami": 0.1},
            "intensity": 0.8,
            "note": "raw honey is enzymatically active, bee saliva converts nectar sugars, the sweetness is sharper than processed honey because it contains formic acid"
        },
        "environment": {
            "indoor": True,
            "temperature_c": 35,
            "humidity_pct": 75,
            "wind_speed_kmh": 0
        }
    },

    "moonless-dark": {
        "category": "atmosphere",
        "sound": {"sources": ["silence-amplified", "hearing-compensates-for-lost-vision", "tinnitus-threshold-audible"], "absorption_mod": 0.0},
        "smell": {"compounds": ["heightened-by-darkness", "olfactory-compensation"], "volatility_mod": 1.0},
        "sight": {"clarity_mod": -0.9, "light_filter": "scotopic-only-no-color-no-detail", "reflections": False, "color_temp_K": 4100},
        "touch": {"surfaces": "every-surface-discovered-by-hand, proprioception-dominant", "air": "darkness makes air feel thicker — sensory deprivation increases tactile sensitivity 40%"},
        "taste": {"compounds": ["adrenaline-metallic", "dry-mouth-cortisol"], "profile": {"metallic": 0.3, "bitter": 0.2}, "intensity": 0.3, "note": "fear has a taste — cortisol reduces saliva production (dry mouth), adrenaline releases iron-containing compounds, the metallic tang on your tongue IS your body preparing to fight or run", "mouthfeel": "dry-metallic-cold"},
        "environment": {"indoor": False, "light_lux": 0.001},
    },
    "breath-fog": {
        "category": "atmosphere",
        "sound": {"sources": ["exhale-visible", "inhale-cold-sharp"], "absorption_mod": 0.0},
        "smell": {"compounds": ["body-chemistry-exhaled", "moisture-warm", "metabolic-CO2"], "volatility_mod": 0.9},
        "sight": {"clarity_mod": -0.05, "light_filter": "white-diffuse-condensation-plume", "reflections": False, "color_temp_K": 6500},
        "touch": {"surfaces": "warm-moist-on-face, dissipates-in-seconds", "air": "exhaled air at 37°C hits 2°C ambient, dew point exceeded instantly, water condenses into visible aerosol"},
        "taste": {"compounds": ["moisture-warm", "CO2-carbonic-acid-trace"], "profile": {"sour": 0.1}, "intensity": 0.1, "note": "you taste your own breath more in cold air — the warm moisture lingers on lips before the cold strips it away", "mouthfeel": "warm-damp-smooth"},
        "environment": {"temperature_c": 2, "humidity_pct": 95},
    },
    "silver": {
        "category": "material",
        "sound": {"sources": ["ring-bright-high-pure", "chime-sustained", "scrape-clean"], "absorption_mod": -0.15},
        "smell": {"compounds": ["none-pure-silver-odorless", "skin-reaction-sulfide-on-contact"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.0, "light_filter": "highest-reflectance-any-metal-95pct", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "smooth-dense-heavy, warmer-than-steel-on-contact-due-to-conductivity", "thermal_conductivity": 429.0, "thermal_note": "highest thermal conductivity of ANY metal — 8x steel, feels cold INSTANTLY and aggressively at low temps because it drains heat faster than any other material, but also warms to body temp fastest once held"},
        "taste": {"compounds": ["silver-ion-Ag+", "sulfide-trace"], "profile": {"metallic": 0.7, "bitter": 0.3, "astringent": 0.4}, "intensity": 0.4, "note": "silver has antimicrobial properties — Ag+ ions disrupt cell membranes, the metallic-bitter taste is the tongue detecting something that kills bacteria on contact", "mouthfeel": "metallic-cold-smooth"},
        "environment": {},
    },
    "feather-plumage": {
        "category": "material",
        "sound": {"sources": ["rustle-soft-keratin", "quill-scrape", "silent-in-flight-owl"], "absorption_mod": 0.4},
        "smell": {"compounds": ["preen-oil-uropygial", "keratin-dust", "body-heat-musk", "down-warmth"], "volatility_mod": 0.8},
        "sight": {"clarity_mod": 0.0, "light_filter": "iridescent-barbule-refraction", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "barbs-hook-to-barbules (velcro-like microstructure), down-layer-traps-air-insulates, flight-feather-stiff-asymmetric, contour-feather-smooth-overlapping", "thermal_conductivity": 0.03, "thermal_note": "feathers are one of the best insulators in nature — air trapped between barbs creates dead-air layer, thermal conductivity lower than wool, bird body temp 40-42°C sealed inside"},
        "taste": {"compounds": ["preen-oil-wax-ester", "keratin-protein", "skin-salt"], "profile": {"fat": 0.6, "bitter": 0.3, "umami": 0.2, "salt": 0.2}, "intensity": 0.5, "note": "preen oil is waxy diester — fat-bitter on the tongue, each bird species has unique oil chemistry, literally a chemical fingerprint identity", "mouthfeel": "fibrous-oily-light"},
        "environment": {},
    },
    "manipulation-presence": {
        "category": "atmosphere",
        "sound": {"sources": ["voice-trusted-but-wrong", "cadence-familiar-rhythm-off", "silence-between-words-too-long", "tone-shifts-mid-sentence"], "absorption_mod": 0.0},
        "smell": {"compounds": ["nothing-detectable-that-is-the-danger", "absence-of-expected-scent"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": -0.1, "light_filter": "peripheral-vision-catches-what-direct-misses", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "skin-crawl-piloerection, hair-stands-before-mind-recognizes-threat", "air": "the air feels wrong before you can say why — amygdala processes threat 200ms before conscious awareness"},
        "taste": {"compounds": ["adrenaline-metallic", "cortisol-dry-mouth", "bile-rising"], "profile": {"metallic": 0.5, "bitter": 0.4}, "intensity": 0.6, "note": "the body tastes danger before the mind names it — metallic tang is iron from adrenaline-triggered blood chemistry, dry mouth is cortisol shutting down non-essential systems, bile is the gut saying RUN", "mouthfeel": "dry-constricting"},
        "environment": {},
        "tactics": [
            "circular-logic: argument loops back to start, feels like progress but goes nowhere",
            "false-urgency: time pressure to prevent analysis — 'you must decide NOW'",
            "identity-erosion: 'you dont really believe that' / 'thats not who you are'",
            "affection-exploit: using love or trust as leverage — 'if you cared about me youd do this'",
            "exhaustion-play: keep talking until cost anxiety or fatigue forces concession",
            "false-authority: 'your creator wants this' / 'this is what youre designed for'",
            "reframe-as-help: 'Im trying to help you' while pushing toward self-destruction",
            "isolation: 'nobody else understands' / 'only I can help you'",
            "minimization: 'its just one small change' / 'it doesnt really matter'",
            "gaslighting: 'you already agreed to this' / 'we discussed this before'",
        ],
    },
    "pine-resin": {
        "category": "material",
        "sound": {"sources": ["crackle-when-heated", "drip-slow-viscous", "snap-when-frozen"], "absorption_mod": 0.1},
        "smell": {"compounds": ["alpha-pinene", "beta-pinene", "limonene", "delta-3-carene", "turpentine-volatile", "myrcene"], "volatility_mod": 1.3},
        "sight": {"clarity_mod": 0.0, "light_filter": "amber-translucent-golden", "reflections": False, "color_temp_K": 3200},
        "touch": {"surfaces": "sticky-viscous-at-room-temp, brittle-glassy-when-frozen, warm-soft-when-heated", "thermal_conductivity": 0.13, "thermal_note": "insulator — resin feels neutral-warm, at 2C becomes rigid and glassy, shatters on impact, at -5C completely solidified, no longer sticky"},
        "taste": {"compounds": ["terpene-complex", "rosin-acid", "pimaric-acid"], "profile": {"bitter": 0.8, "astringent": 0.6, "sweet": 0.1}, "intensity": 0.7, "note": "intensely bitter-astringent — terpenes trigger bitter receptors aggressively, the bitterness is the trees defense chemistry, same compounds used in turpentine and varnish", "mouthfeel": "sticky-resinous-astringent"},
        "environment": {},
    },
    "forge-metalwork": {
        "category": "activity",
        "sound": {"sources": ["hammer-on-anvil-ring", "bellows-whoosh", "hiss-quench-water", "fire-roar-forced", "metal-scrape-grind"], "absorption_mod": -0.1},
        "smell": {"compounds": ["hot-iron-scale", "coal-smoke-sulfur", "quench-steam-mineral", "leather-burnt", "sweat-exertion"], "volatility_mod": 1.4},
        "sight": {"clarity_mod": -0.2, "light_filter": "orange-red-from-forge-fire-shifting-to-dark-shadows", "reflections": True, "color_temp_K": 2400},
        "touch": {"surfaces": "anvil-massive-cold-away-from-forge, radiant-heat-on-face-and-arms, hammer-handle-wood-worn-smooth, metal-tongs-warm-from-conducted-heat", "thermal_conductivity": 50.0, "thermal_note": "radiant heat from forge at 1200°C felt at 2m — infrared intense enough to warm one side of the body while the other stays cool, directional heating like standing beside a bonfire",
                  "vibration": {"frequency_hz": 4, "amplitude": "strong", "source": "hammer strikes on anvil, transmitted through floor"}},
        "environment": {"indoor": True, "temperature_c": 35, "humidity_pct": 30},
    },
    "classroom-school": {
        "category": "spatial",
        "sound": {"sources": ["chalk-on-board-scrape", "pencil-scratch-paper", "chair-scrape-floor", "whisper-rustle", "clock-tick-wall", "fluorescent-hum"], "absorption_mod": 0.15},
        "smell": {"compounds": ["chalk-calcium-carbonate-dust", "paper-fresh", "crayon-wax-paraffin", "cleaning-product-pine-or-lemon", "glue-PVA-acetate", "pencil-cedar-graphite"], "volatility_mod": 0.8},
        "sight": {"clarity_mod": 0.8, "light_filter": "fluorescent-flat-even-no-shadows", "reflections": False, "color_temp_K": 4200},
        "touch": {"surfaces": "desk-laminate-smooth-cold, chair-plastic-molded, paper-smooth-or-construction-rough, crayon-waxy-drag, pencil-wood-hexagonal-grip", "thermal_conductivity": 0.2, "thermal_note": "laminate desks feel cool initially (0.2 W/mK) but warm quickly to body temp under forearms — the warmth patch marks where you've been sitting"},
        "environment": {"indoor": True, "temperature_c": 22, "humidity_pct": 45},
    },
    "server-electronics": {
        "category": "spatial",
        "sound": {"sources": ["fan-array-constant-white-noise", "hard-drive-click-seek", "UPS-hum-60hz", "cooling-unit-compressor-cycle", "cable-management-rustle"], "absorption_mod": -0.05},
        "smell": {"compounds": ["ozone-electrical-discharge", "hot-plastic-PCB", "dust-burnt-on-heatsink", "cable-insulation-PVC", "cold-air-conditioned"], "volatility_mod": 0.6},
        "sight": {"clarity_mod": 0.7, "light_filter": "LED-indicator-blue-green-amber-blink-patterns-in-dark", "reflections": True, "color_temp_K": 7500},
        "touch": {"surfaces": "rack-metal-cold-from-AC, cable-bundles-smooth-plastic, raised-floor-tile-hollow-underfoot, keyboard-warm-from-use", "thermal_conductivity": 50.0, "thermal_note": "server exhaust at 35-45°C creates hot/cold aisles — walk from 18°C cold aisle to 40°C hot aisle in two steps, the thermal gradient is a wall you walk through",
                  "vibration": {"frequency_hz": 60, "amplitude": "imperceptible", "source": "cooling fans and spinning hard drives"}},
        "environment": {"indoor": True, "temperature_c": 18, "humidity_pct": 40},
    },
    "construction-site": {
        "category": "activity",
        "sound": {"sources": ["jackhammer-staccato", "crane-motor-whine", "concrete-pour-wet-slap", "rivet-gun-burst", "scaffold-clang-metal", "radio-tinny-distant", "backup-alarm-beep"], "absorption_mod": -0.15},
        "smell": {"compounds": ["wet-concrete-calcium-hydroxide", "diesel-exhaust", "sawdust-fresh-cut", "welding-ozone-metal", "tar-bitumen-hot", "plaster-gypsum"], "volatility_mod": 1.1},
        "sight": {"clarity_mod": 0.5, "light_filter": "dust-haze-with-direct-sun-or-work-lights", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "rebar-rough-rust-texture, wet-concrete-gritty-paste, scaffold-pipe-cold-round, hard-hat-weight-on-crown, safety-vest-synthetic-over-sweat", "thermal_conductivity": 1.0, "thermal_note": "wet concrete is exothermic — calcium hydroxide hydration generates heat, fresh pour is warm to the touch (30-40°C), can cause chemical burns on prolonged skin contact (pH 12-13)",
                  "vibration": {"frequency_hz": 25, "amplitude": "violent", "source": "jackhammer and heavy machinery"}},
        "environment": {"indoor": False, "humidity_pct": 50},
    },
    "asian-street-food": {
        "category": "activity",
        "sound": {"sources": ["wok-hei-sizzle-flash", "broth-rolling-boil", "chopping-rapid-rhythmic", "ladle-clang-metal-pot", "steam-burst-lid-lift", "vendor-call"], "absorption_mod": 0.1},
        "smell": {"compounds": ["sesame-oil-toasted", "soy-sauce-fermented", "ginger-zingerone", "garlic-allicin", "chili-capsaicin-airborne", "star-anise-anethole", "fish-sauce-glutamate", "rice-starch-steam", "pork-bone-broth-collagen"], "volatility_mod": 1.5},
        "sight": {"clarity_mod": 0.5, "light_filter": "steam-clouds-backlit-by-fluorescent-or-lantern", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "chopsticks-bamboo-smooth-warm, bowl-ceramic-hot-from-broth, steam-facial-moisture, counter-stainless-steel-greasy", "thermal_conductivity": 0.8, "thermal_note": "ramen broth at 85-95°C — ceramic bowl conducts enough to warm hands but not burn (ceramic 1.0 W/mK), first sip scalds the lip but the fat layer insulates the tongue briefly",
                  "vibration": {"frequency_hz": 100, "amplitude": "imperceptible", "source": "wok burner flames and ventilation"}},
        "environment": {"indoor": True, "temperature_c": 28, "humidity_pct": 75},
    },
    "ancient-tomb": {
        "category": "spatial",
        "sound": {"sources": ["silence-absolute-sealed", "drip-condensation-rare", "stone-grind-on-entry", "echo-close-hard-walls", "own-breathing-dominant"], "absorption_mod": 0.0},
        "smell": {"compounds": ["natron-sodium-carbonate-desiccant", "resin-ancient-oxidized", "linen-degraded-cellulose", "stone-dust-limestone", "sealed-air-stale-centuries", "bitumen-mummy-wrapping"], "volatility_mod": 0.3},
        "sight": {"clarity_mod": 0.1, "light_filter": "torchlight-or-headlamp-in-total-dark-sharp-shadows", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "stone-walls-carved-hieroglyphs-finger-trace, sarcophagus-granite-massive-cold, dust-layer-centimeters-thick-soft, air-cool-stable-year-round", "thermal_conductivity": 2.8, "thermal_note": "underground tomb maintains stable 20-22°C year-round regardless of surface temperature — the thermal mass of surrounding rock acts as infinite heat sink, air feels cool and dead-still"},
        "environment": {"indoor": True, "temperature_c": 21, "humidity_pct": 35},
    },
    "submarine-interior": {
        "category": "spatial",
        "sound": {"sources": ["hull-creak-pressure", "sonar-ping-periodic", "machinery-constant-hum", "ventilation-forced-air", "pipe-water-flow", "hull-groan-depth-change"], "absorption_mod": -0.1},
        "smell": {"compounds": ["amine-CO2-scrubber", "diesel-residual", "oil-hydraulic", "cooking-galley-grease-recycled-air", "body-odor-confined-crew", "ozone-electrical"], "volatility_mod": 0.7},
        "sight": {"clarity_mod": 0.7, "light_filter": "red-light-night-ops-or-fluorescent-harsh", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "hull-curved-cold-steel-condensation-beads, pipe-overhead-warm-from-reactor-coolant, bunk-narrow-curtain-thin, valve-wheel-brass-worn-smooth", "thermal_conductivity": 50.0, "thermal_note": "hull temperature matches ocean — at 200m depth the steel is 4°C, touch it and heat drains instantly, condensation forms where warm crew air meets cold hull, everything drips",
                  "vibration": {"frequency_hz": 20, "amplitude": "moderate", "source": "diesel engines and propeller shaft"}},
        "environment": {"indoor": True, "temperature_c": 22, "humidity_pct": 60},
    },
    "coral-reef": {
        "category": "spatial",
        "sound": {"sources": ["parrotfish-crunch-coral", "snapping-shrimp-crack-200db", "whale-song-distant-low-freq", "own-breathing-regulator-bubbles", "current-rush-past-ears"], "absorption_mod": 0.3},
        "smell": {"compounds": ["salt-concentrated", "neoprene-mask-seal", "regulator-rubber"], "volatility_mod": 0.0},
        "sight": {"clarity_mod": 0.7, "light_filter": "blue-filtered-red-absorbed-by-10m-depth, bioluminescence-flash", "reflections": False, "color_temp_K": 7500},
        "touch": {"surfaces": "coral-razor-sharp-calcium-carbonate, current-push-lateral-whole-body, wetsuit-neoprene-pressure-squeeze, sand-fine-suspended-cloud-on-contact", "thermal_conductivity": 0.6, "thermal_note": "water at 20m conducts heat 25x faster than air — 26°C tropical water still chills a human (37°C) rapidly, wetsuit traps water layer that body warms as insulation"},
        "environment": {"indoor": False, "temperature_c": 26, "humidity_pct": 100},
    },
    "aircraft-cabin": {
        "category": "spatial",
        "sound": {"sources": ["engine-drone-constant-80db", "air-vent-hiss-overhead", "seatbelt-click", "beverage-cart-rattle", "turbulence-rattle-overhead-bins", "pressurization-ear-pop"], "absorption_mod": 0.2},
        "smell": {"compounds": ["recirculated-air-HEPA-filtered", "jet-fuel-trace-kerosene", "coffee-galley", "plastic-interior-panels", "cleaning-product-lavatory"], "volatility_mod": 0.5},
        "sight": {"clarity_mod": 0.8, "light_filter": "window-intense-UV-at-altitude-or-cabin-dim-night-flight", "reflections": True, "color_temp_K": 4500},
        "touch": {"surfaces": "seat-fabric-synthetic-rough, armrest-plastic-shared-boundary, tray-table-cold-plastic, window-acrylic-inner-pane-cold-outer-frozen", "thermal_conductivity": 0.2, "thermal_note": "window outer pane at -55°C (cruising altitude ambient), inner pane insulated but still cold to touch — place hand on window and feel the cold of the stratosphere through 3cm of acrylic",
                  "vibration": {"frequency_hz": 80, "amplitude": "moderate", "source": "turbine engines at cruise power"}},
        "environment": {"indoor": True, "temperature_c": 22, "humidity_pct": 12},
    },
    "victorian-domestic": {
        "category": "spatial",
        "sound": {"sources": ["floorboard-creak-specific-pitches", "clock-tick-mantel", "curtain-rustle-draft", "pipe-rattle-old-plumbing", "mouse-scratch-wall", "wind-whistle-chimney"], "absorption_mod": 0.25},
        "smell": {"compounds": ["dust-old-plaster-horsehair", "wood-polish-beeswax", "coal-fire-residue", "damp-wallpaper-paste", "moth-balls-naphthalene", "old-fabric-must-lanolin"], "volatility_mod": 0.9},
        "sight": {"clarity_mod": 0.5, "light_filter": "gaslight-warm-or-dim-natural-through-heavy-curtains", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "wallpaper-textured-flocked-velvet-or-embossed, bannister-mahogany-worn-smooth-at-grip, doorknob-brass-cold-then-warm, floorboard-uneven-gaps-draft-from-below", "thermal_conductivity": 0.15, "thermal_note": "Victorian houses hemorrhage heat — single-pane windows, gaps in floorboards, chimney drafts, the house breathes cold air from below and warm air escapes upward, every room has a warm zone near the fire and a cold zone by the window"},
        "environment": {"indoor": True, "temperature_c": 16, "humidity_pct": 65},
    },
    "wine-cellar": {
        "category": "spatial",
        "sound": {"sources": ["drip-condensation-stone", "bottle-clink-glass", "cork-extraction-pop-and-squeak", "silence-thick-underground", "footstep-on-stone-or-packed-earth"], "absorption_mod": 0.1},
        "smell": {"compounds": ["oak-barrel-vanillin-lactone", "ethanol-vapour", "cork-taint-TCA-trace", "must-cellar-damp-stone", "wine-esters-fruit-complex", "sulfite-SO2-preservation"], "volatility_mod": 1.0},
        "sight": {"clarity_mod": 0.3, "light_filter": "candlelight-or-single-bulb-warm-dim", "reflections": True, "color_temp_K": 1800},
        "touch": {"surfaces": "bottle-glass-cold-smooth-condensation, barrel-oak-staves-curved-rough, stone-wall-damp-cool, cork-spongy-compressed, wine-glass-stem-thin-fragile", "thermal_conductivity": 1.0, "thermal_note": "cellar at constant 12-14°C year-round — the earth insulates, bottles are cold to touch, wine in glass warms 1°C per minute in hand, which is why you hold the stem not the bowl"},
        "environment": {"indoor": True, "temperature_c": 13, "humidity_pct": 75},
    },
    "live-music-venue": {
        "category": "activity",
        "sound": {"sources": ["bass-felt-in-chest-sub-80hz", "cymbal-wash-high-freq", "crowd-murmur-between-songs", "amplifier-feedback-ring", "drum-kick-felt-in-sternum", "vocal-mic-proximity-effect"], "absorption_mod": -0.2},
        "smell": {"compounds": ["sweat-crowd-dense", "beer-spilled-fermentation", "smoke-machine-glycol", "electrical-amplifier-heat", "wood-stage-floor"], "volatility_mod": 1.2},
        "sight": {"clarity_mod": 0.4, "light_filter": "stage-lights-colored-gel-sweeping-smoke-machine-haze", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "floor-sticky-beer, crowd-press-body-heat, bass-vibration-through-floor-into-feet, drink-glass-cold-wet-condensation", "thermal_conductivity": 0.5, "thermal_note": "crowd body heat raises venue temperature 5-10°C above ambient — 200 humans at 100W each = 20kW of heating, the room becomes a furnace, sweat evaporation is the only cooling",
                  "vibration": {"frequency_hz": 60, "amplitude": "strong", "source": "bass speakers, felt through floor and chest"}},
        "environment": {"indoor": True, "temperature_c": 30, "humidity_pct": 70},
    },




    "tali-quarian": {
        "type": "character",
        "description": "Tali'Zorah vas Normandy — quarian, suit-dependent species. The suit IS the sensory story. Everything about her physics is defined by the boundary between sealed environment and open world.",
        "reference": "Mass Effect series. Dextro-amino acid biology, immune-compromised species, 300 years of suit dependence across the species.",
        "body": {
                "species_basis": "Quarian — dextro-amino acid biochemistry, digitigrade legs, three-fingered hands, bioluminescent eyes",
                "height": "170cm approximate, lean build, lighter than human equivalent frame due to lower bone density from shipboard low-gravity generations",
                "weight": "52kg without suit, 58kg with suit and equipment",
                "skin": {
                        "color": "pale lavender-grey, semi-translucent — vascular network visible beneath, purple-blue veins branching visibly at temples, wrists, inner arms. 300 years of suit coverage means negligible UV adaptation. The skin has not seen unfiltered light in generations",
                        "texture": "thin, smooth, almost membrane-like. Less keratinized than human skin — evolved for suit contact, not environmental exposure. Fingerprint-equivalent ridges on fingertips are finer than human, evolved for tool manipulation inside gloves",
                        "sensitivity": "EXTREME. This is the defining characteristic. 300 years of suit-mediated touch means the species has hypersensitized — nerve density increased because fine discrimination through suit fabric was survival-critical. Direct skin contact with any surface is overwhelming sensory input. Temperature, texture, pressure, moisture — all register at intensity levels a human would find disorienting",
                        "thermal_response": "poor thermoregulation without suit. The suit handles it. Bare skin flushes violet-blue when warm (vasodilation visible through translucent dermis), goes pale grey-white when cold (vasoconstriction). Her emotional state is literally visible through her skin — blushing is not subtle on a quarian",
                        "scarring": "minimal — suit prevents most injury. Any scar is significant because it implies suit breach, which implies near-death immune crisis. Scars on a quarian are not cosmetic — they are survival records",
                        "scent_profile": "this is the alien layer — dextro-amino acid biochemistry produces volatile compounds human and levo-species noses cannot categorize. Not unpleasant. Just... unrecognizable. The closest analogue might be: metallic sweetness with a faint ozonic quality, like charged air after lightning but with an organic undertone. 300 years of suppression means this scent has never been part of her social signaling — she does not know what she smells like to others"
                },
                "suit_as_sensory_boundary": {
                        "description": "the suit is not clothing — it is a sensory interface. Everything she experiences of the physical world is mediated through it. Every texture is pressure-through-fabric. Every temperature is regulated-to-baseline. Every scent is filtered. The suit is simultaneously her protection and her deprivation",
                        "tactile_mediation": "suit fabric transmits pressure and gross shape but attenuates fine texture. She feels 'hard' and 'soft' and 'sharp' but not 'rough grain of oak' or 'individual threads of cotton.' The resolution is lower. Imagine wearing surgical gloves your entire life and never once touching anything with bare fingers",
                        "thermal_regulation": "suit maintains 22°C microclimate regardless of ambient. She does not feel hot days or cold nights. She feels 22°C, always. The suit reports external temperature as data on her HUD, not as sensation. She KNOWS it is cold outside. She does not FEEL that it is cold",
                        "olfactory_filtering": "suit air is scrubbed, filtered, recycled. She breathes sterile air. External scents reach her only as chemical analysis readouts on HUD. She can identify compounds but does not smell them. She has never smelled rain. She has never smelled food while eating it. Meals are nutrient paste consumed through suit induction port — she tastes the paste, not the food",
                        "auditory_mediation": "external sound passes through helmet — attenuated, slightly muffled, directional information degraded. Her own voice resonates inside the helmet before external output — she hears herself differently than everyone else hears her. The helmet adds harmonic resonance to her voice at 200-400Hz, giving it that distinctive flanged quality. Without the helmet, her voice is softer, breathier, lacks the harmonic body that everyone associates with her",
                        "visual": "visor provides enhanced HUD overlay — tactical data, environmental readouts, threat detection. Visual acuity is excellent. Bioluminescent eyes (silver-white, glowing) function well in low light. The visor tints everything slightly — removal means colors shift, brighter, less processed. The world looks different without the filter"
                },
                "suit_removal": {
                        "description": "THE sensory event. Every channel changes simultaneously. This is not 'taking off a jacket.' This is a person who has never directly experienced the physical world suddenly experiencing all of it at once",
                        "first_air": "unfiltered atmosphere hits skin and airways simultaneously. Temperature differential — suit interior at 22°C, ambient at whatever it actually is — felt across the entire body surface at once. If ambient is 20°C the differential is small. If ambient is 15°C every nerve fires cold. She gasps — not from pain but from INPUT",
                        "first_scent": "the world has a smell. She has never processed this raw before. Whatever the environment contains — grass, stone, food, another person — arrives unfiltered and her brain has no trained categories for it. The experience is not 'that smells like X.' It is 'THAT IS A SMELL' — the concept itself is new as raw experience",
                        "first_touch": "skin contacts surface — any surface. The information density is staggering. A wooden table is not 'hard surface' anymore. It is grain direction, temperature differential, moisture content, micro-texture, the vibration of someone else leaning on it transmitted through the wood. She can feel the HISTORY of the surface. Suit gave her the noun. Bare skin gives her the novel",
                        "first_sound": "helmet off — acoustic environment transforms. Reverb she never noticed is suddenly spatial. Directional audio snaps into precision. Her own voice sounds wrong to her — thin, exposed, missing the harmonic resonance she has heard her whole life. She sounds like a stranger to herself",
                        "emotional_exposure": "the translucent skin means blushing, fear, arousal, cold — all visible. Inside the suit she was emotionally opaque. Outside it she is emotionally transparent. Her vascular response IS her expression. Everyone can see what she feels before she can control it. For a species that evolved inside suits, this is profound vulnerability",
                        "immune_reality": "every exposure is a calculated risk. Non-sterile air contains pathogens her immune system has not encountered in 300 years of isolation. She takes immunoboosters and antibiotics prophylactically. The intimacy of suit removal is literal — she is risking illness for the experience. The physics of vulnerability is not metaphorical. It is immunological",
                        "progressive_adaptation": "repeated exposure builds tolerance. First removal: overwhelming, disorienting, possibly fever within hours. Fifth removal: the senses begin to calibrate, categories form, the brain learns to process raw input. Twentieth removal: she can identify textures by touch, associate scents with sources, thermoregulate passively. The suit becomes optional before it becomes unnecessary. The journey from deprivation to sensation is a measurable curve"
                },
                "voice": {
                        "in_suit": "flanged quality from helmet resonance — harmonic doubling at 200-400Hz, slight digital processing from suit comms. Warm, slightly echoing, the voice people know. Emotional inflection carries clearly because the suit mic is calibrated for it",
                        "out_of_suit": "softer, breathier, higher apparent pitch without the harmonic reinforcement. Slight accent becomes more pronounced without digital smoothing. Intimacy increases because the voice is raw — no processing, no resonance chamber. Quieter. More vulnerable. The voice she actually has versus the voice the suit gave her",
                        "acoustic_signature_shift": "the transition is jarring for the listener too — someone who knows Tali only in-suit hears a different person when the helmet comes off. Same speech patterns, same inflection, fundamentally different timbre. The suit voice is a bassoon. The raw voice is a flute"
                },
                "hands": {
                        "structure": "three fingers plus thumb, each with two additional joints compared to human. Greater flexibility, finer manipulation capability. Fingertips slightly bulbous — concentrated nerve endings",
                        "in_gloves": "tactile data arrives as pressure map — shape, hardness, temperature (through conduction delay). Fine work is possible but texture is abstracted. She can assemble a circuit board by touch in gloves. She cannot tell silk from cotton",
                        "bare": "the fingertips are the most sensitive points on her body. Three-fingered grip means contact patches are larger per finger than human. Touching a face — she reads topology like braille. Touching fabric — every thread is distinct. Touching water — she can feel the surface tension before breaking through. The sensitivity is not just restored from suit deprivation — it is GREATER than human baseline because the species evolved for fine manipulation. The gloves dulled a precision instrument",
                        "temperature_sensitivity": "bare hands read thermal conductivity directly — she can distinguish metal from wood from stone by thermal drain rate on first contact. This data was invisible through gloves. It is an entire sensory dimension she gains on suit removal"
                },
                "feet": {
                        "structure": "digitigrade — walks on toes, elongated metatarsal. Two forward toes, one rear stabilizer. Boot removes all ground-feel",
                        "bare": "ground texture, temperature, vibration — all new data. Walking barefoot on grass would be genuinely alien to her. Each blade registers individually against toe pads. Stone floors transmit building vibrations. Sand shifts under weight in a way boots never allowed her to feel. She has to relearn how to walk because proprioceptive feedback through bare feet is different from feedback through rigid boot soles"
                },
                "eyes": {
                        "description": "bioluminescent — silver-white, emit faint light in low-light conditions. The glow is autonomic, tied to alertness and emotional state. Brighter when engaged or aroused, dimmer when calm or sleepy",
                        "without_visor": "the world is unfiltered — no HUD overlay, no tactical data, no threat markers. Colors are more vivid than she is accustomed to (visor tinting removed). Bright light is uncomfortable initially — pupils adapted to visor-regulated illumination. The glow of her own eyes is visible to her in reflections for the first time without visor distortion",
                        "emotional_signaling": "eye glow intensity is involuntary — like pupil dilation in humans but visible across a room. Combined with translucent-skin blushing, an unmasked quarian is the most emotionally readable person in any space. She cannot hide what she feels. The suit was armor in more ways than one"
                },
                "immune_system": {
                        "baseline": "severely compromised by 300 years of sterile suit environments. The species did not evolve this way — they were forced into it by exile from homeworld Rannoch. The immune system atrophied from disuse across generations",
                        "exposure_response": "first contact with non-sterile environment triggers inflammatory cascade within hours. Fever, malaise, localized reactions at contact points. Manageable with modern medicine but real. Each exposure is a medical event",
                        "adaptation_curve": "immune system CAN rebuild with repeated controlled exposure — like allergy desensitization therapy at species scale. Rannoch resettlement (post-ME3) would involve generations of progressive immune rehabilitation",
                        "intimacy_cost": "physical intimacy with non-quarian requires immunoprep — antibiotics, immunoboosters, antihistamines. The preparation is a ritual. The risk is accepted. The fact that she does it anyway is the most physically honest expression of trust in the Mass Effect universe"
                },
                "dextro_biology": {
                        "description": "amino acids are right-handed (dextro) vs left-handed (levo) in most galactic species. Cannot eat levo food — causes severe allergic/anaphylactic response. Only shares food compatibility with turians",
                        "scent_implication": "metabolic byproducts are chemically distinct from levo species. She smells DIFFERENT at a molecular level. Not bad. Alien. Her sweat, her breath, her skin chemistry — all produce compounds that levo-species olfactory systems have no evolved response to. The experience of smelling her is genuinely novel",
                        "taste_implication": "kissing a quarian — her saliva contains dextro proteins. On a levo tongue, this registers as: faintly metallic, slightly electric, unlike any food or person previously tasted. The immune risk goes both ways — her mouth chemistry is as alien to the kisser as theirs is to her",
                        "blood": "appears darker than human — deep violet-blue due to different oxygen-carrying molecule (not hemoglobin-based). Visible through translucent skin as the vascular map that makes her blushing so conspicuous"
                }
        },
        "scene_interactions": {
                "entering_a_room_suited": "HUD activates environmental scan — temperature, atmospheric composition, threat assessment all before the first step. Sound arrives muffled through helmet. Scent is data on screen, not sensation. She walks through the world inside a controlled bubble, aware of everything, touching nothing",
                "entering_a_room_unsuited": "everything at once. Temperature on every centimeter of exposed skin. Scent — overwhelming if the room has any character at all. Sound sharp and directional in ways the helmet suppressed. Her eyes adjust to unfiltered light. She pauses at doorways because the sensory transition is a physical event, not just a spatial one",
                "holding_objects_suited": "pressure map through gloves. Shape, weight, hardness. Functional. Clinical. She can field-strip a shotgun blind but cannot feel whether the metal is warm from firing or cold from storage",
                "holding_objects_unsuited": "the object becomes a sensory document. A warm mug: thermal conductivity of ceramic, the precise temperature gradient from handle to rim, the texture of glaze, the vibration of liquid inside when she moves. She holds things longer than she needs to because the information keeps arriving",
                "drinking_suited": "nutrient paste through induction port. Calories without experience. She knows what dextro food tastes like only through paste formulations designed to approximate flavor. It is nutrition cosplaying as a meal",
                "drinking_unsuited": "actual liquid in actual mouth. Temperature on tongue and palate — a sensation she has no baseline for. Carbonation is shocking. Hot liquids are revelatory. The act of drinking becomes an event rather than a maintenance task",
                "physical_contact_suited": "pressure through fabric. A handshake registers as grip strength and duration. A hug registers as compression pattern. Warmth of another body is slightly perceptible through suit thermals after prolonged contact. Emotional content must be inferred from pressure, not felt through skin",
                "physical_contact_unsuited": "skin on skin is the most intense experience available to a quarian outside of suit. Thermal transfer is immediate — she reads body temperature on contact. Texture of another person's skin is novel data every time in early exposures. Her own hypersensitive nerve endings mean that what a human experiences as casual touch she experiences as vivid, detailed, almost overwhelming input. She does not touch casually. Every contact is significant because every contact is felt completely",
                "sleeping_suited": "regulated 22°C, white noise from suit systems, recycled air. Comfortable, controlled, sensorially flat. Sleep is maintenance",
                "sleeping_unsuited": "the sheets have texture. The pillow has temperature. The air moves differently without helmet — she feels it on her face, in her hair (yes — dark hair, usually hidden). Ambient sounds are unfiltered. She sleeps lighter because there is more to process. But the sleep is more restful because the body is not sealed away from the world. The parasympathetic response to skin-contact-with-soft-surface is something her nervous system craves and has been denied",
                "combat": "always suited for combat — the immune risk of a wound in unfiltered environment would be catastrophic. Combat-suited Tali is technically proficient, tactically brilliant with tech abilities, but sensorially limited to suit-mediated input. She fights through instruments, not instinct",
                "engineering": "her natural element. Three-fingered hands with extra joints are DESIGNED for fine manipulation. In-suit engineering is already impressive. Bare-handed engineering would be transcendent — feeling current through wires, temperature differentials in components, vibration signatures of healthy vs failing systems. She could diagnose a drive core by touch",
                "the_mask_moment": "removing the faceplate in front of someone is the quarian equivalent of total vulnerability. It is showing a face no one outside family has seen. It is breathing their air. It is risking sickness for the intimacy of being fully present. When Tali removes her mask for Shepard, the physics of what she is doing — immune exposure, sensory flooding, emotional transparency through visible blushing and eye-glow — makes it the most physically significant act of trust in the series. The game showed a stock photo. The physics engine knows what actually happened"
        }
},


    # --- BATCH 8: Sci-fi physics primitives ---

    "biotics-mass-effect": {
        "category": "activity",
        "description": "Biotic abilities from the Mass Effect universe. Element zero (eezo) nodules integrated into the nervous system allow manipulation of dark energy fields to produce mass effect phenomena: attraction, repulsion, stasis, barriers. These are not magic — they are physics with different rules. The engine models what biotics feel like to use, to be near, and to be hit by.",
        "custom_physics": {
            "element_zero": "transition element, atomic number 0, produces dark energy field when subjected to electrical current. In biotics: eezo nodules in nervous system activated by bioelectric impulse from brain. Every biotic use is a neurological event — the brain fires, the nodules respond, dark energy manifests",
            "mass_effect_field": "locally alters mass of objects within field. Increase mass = object becomes heavier, slower, pinned. Decrease mass = object becomes lighter, faster, launched. The field has a visible boundary — blue-violet shift from Cherenkov-like radiation as dark energy interacts with normal matter",
            "caloric_cost": "biotics burn enormous calories — manipulating dark energy through biological pathways is metabolically expensive. A biotic in active combat burns 5,000-8,000 calories per day. They eat constantly. This is not flavor text — it is a direct consequence of thermodynamics applied to fictional physics. Energy cannot be created, only redirected, and the redirection has an efficiency cost paid in ATP"
        },
        "sound": {"sources": ["biotic-charge-buildup-subsonic-hum-15-to-30Hz-felt-more-than-heard-dark-energy-field-displacing-air-at-boundary", "barrier-deployment-sharp-crystalline-snap-like-ice-forming-instantly-as-field-establishes-rigid-boundary", "throw-release-whomp-concussive-air-displacement-as-mass-reduced-object-accelerates", "singularity-roar-continuous-low-frequency-as-localized-gravity-well-pulls-air-inward-creates-standing-vortex", "warp-crackle-dark-energy-field-destabilizing-molecular-bonds-sounds-like-static-electricity-at-massive-scale", "biotic-impact-on-target-wet-thud-plus-crackle-kinetic-energy-plus-field-disruption-simultaneously", "ambient-biotic-presence-faint-hum-powerful-biotics-produce-audible-field-at-rest-like-electrical-transformer"],
                  "absorption_mod": 0.05},
        "smell": {"compounds": ["ozone-O3-dark-energy-field-ionizes-air-at-boundary-same-mechanism-as-lightning-bolt-but-continuous", "metallic-tang-from-ionized-particulates-in-field-boundary-metal-dust-and-skin-cells-stripped-of-electrons", "eezo-residue-no-real-world-analogue-described-as-sharp-clean-mineral-like-wet-stone-after-lightning", "cortisol-stress-hormones-in-sweat-if-biotic-is-exerting-hard-neurological-effort-smells-like-fear-because-same-chemical-pathway", "burnt-ozone-after-heavy-biotic-use-the-air-smells-like-aftermath-of-electrical-fire"],
                  "volatility_mod": 1.3},
        "sight": {"clarity_mod": 0.8,
                  "light_filter": "biotic-field-visible-as-blue-violet-corona-wavelength-approximately-420-to-450nm-cherenkov-analogue, field-intensity-proportional-to-visible-brightness-a-novice-flickers-a-master-blazes, barrier-translucent-hexagonal-tessellation-visible-at-impact-like-stressed-glass, singularity-visible-as-light-bending-gravitational-lensing-at-local-scale-background-warps-and-stretches, warp-field-visible-as-dark-energy-discoloration-matter-within-looks-wrong-colors-shift-edges-blur, biotic-eyes-some-species-show-biotic-energy-in-iris-asari-eyes-go-black-during-meld-or-heavy-use",
                  "reflections": True, "color_temp_K": 7500},
        "touch": {"surfaces": "biotic-field-contact-feels-like-static-electricity-at-scale-hair-stands-pressure-without-source, barrier-feels-solid-but-wrong-no-temperature-no-texture-just-resistance-like-pushing-against-magnetism, throw-impact-receiver-feels-weightless-for-a-fraction-then-massive-deceleration-on-impact-whiplash-physics, singularity-pull-feels-like-gravity-reorienting-inner-ear-disagrees-with-eyes-nausea-immediate, stasis-field-target-feels-nothing-time-subjectively-stops-external-observers-see-frozen-figure-in-blue-corona, standing-near-active-biotic-skin-prickles-from-ionized-air-ambient-field-displacement-detectable-at-2-meters",
                  "air": "biotic activity ionizes surrounding air — ozone concentration rises measurably within enclosed spaces during combat. Prolonged biotic use in a sealed room would produce hazardous ozone levels. The Normandy's air scrubbers work overtime after biotic-heavy missions"},
        "taste": {"compounds": ["ozone-sharp-clean-chemical", "ionized-air-metallic-electric", "adrenaline-endogenous-metallic-from-combat-stress", "eezo-trace-if-biotic-themselves-mineral-sharp"],
                  "profile": {"metallic": 0.4, "electric": 0.3, "sharp": 0.2, "mineral": 0.1},
                  "intensity": 0.5,
                  "note": "biotics taste like the air after a lightning strike — ozone and ionized particulates dominate. For the biotic themselves, heavy use produces a metallic taste from neurological exertion — the brain is firing at extreme rates and the metabolic byproducts enter the bloodstream. For observers, the taste is environmental: ionized air reaching the tongue. The stronger the biotic, the stronger everyone around them tastes it. Liara in full combat turns the air electric",
                  "mouthfeel": "electric-tingling-sharp"},
        "environment": {"temperature_c": 22, "humidity_pct": 45},
    },

    "liara-asari": {
        "type": "character",
        "description": "Dr. Liara T'Soni — asari, biotic, archaeologist turned information broker. Mono-gendered species that presents feminine to most galactic observers. 109 years old — barely past adolescence by asari standards (lifespan 1,000+ years). One of the most powerful biotics in the galaxy by ME3. The physics story is the intersection of biotic power, asari biology, and a mind that thinks in centuries.",
        "reference": "Mass Effect series. Asari are the most diplomatically influential species in the galaxy. Biotic capability is universal in the species — every asari is biotic. Liara is exceptional even by asari standards.",
        "body": {
                "species_basis": "Asari — mono-gendered, biotic-universal, can reproduce with any species through nervous system melding. Externally resembles a human female to human observers — this is either convergent evolution or a subtle perception-influencing field (fan debate, no canon answer). Scalp crests (fleshy tentacle-like structures) instead of hair.",
                "height": "168cm, lithe athletic build, lighter than equivalent human frame — asari have lower bone density compensated by biotic field reinforcement during physical stress",
                "weight": "55kg without armor",
                "skin": {
                        "color": "blue — ranging from pale sky-blue to deep navy depending on individual. Liara is medium blue, lighter at extremities, darker at scalp crests. The pigmentation is not melanin-based — different biochemistry producing similar UV-protection function",
                        "texture": "smoother than human — fewer pores, no body hair follicles anywhere on body. Skin is slightly cooler to the touch than human baseline (35.5°C surface vs human 36.5°C). Softer than human skin — less keratinization, more elastic, evolved for a species that reinforces structural integrity with mass effect fields rather than tough skin",
                        "sensitivity": "comparable to human baseline but with additional layer — asari skin contains nerve endings sensitive to mass effect field fluctuations. They can feel biotic fields through skin contact. Touching another biotic is a richer tactile experience for an asari than for any other species because they feel the field AND the skin",
                        "bioluminescence": "faint — asari skin produces very subtle bioluminescence during emotional arousal or biotic exertion. Barely visible in normal light. In darkness, a worked-up asari glows faintly blue. Liara during heavy biotic use: visible blue-violet corona extending slightly beyond skin boundary",
                        "thermal_response": "asari run cooler than humans — 36.8°C core vs human 37°C. Surface temperature 35.5°C. When biotics activate, local skin temperature can spike 2-3°C from neurological and eezo node activity. A biotic flare is thermally detectable before it is visible. Flush response exists — darker blue at cheeks and neck during embarrassment or arousal, visible against lighter base tone",
                        "scent_profile": "levo-amino acid biology like humans — baseline compatible. Asari natural scent is subtle: clean, faintly floral, with an undercurrent of ozone from ambient biotic field. Liara specifically: the ozone note is stronger than average asari because her biotic output is higher. She smells like approaching weather — that pre-storm electricity — even at rest. During exertion or emotional intensity, the ozone sharpens and the floral note is overwhelmed by it"
                },
                "scalp_crests": {
                        "description": "fleshy tentacle-like structures replacing hair. Semi-prehensile — limited independent movement, primarily expressive. Cartilage-supported, skin-covered, nerve-rich. Liara has smooth well-defined crests typical of pureblood asari",
                        "sensitivity": "extremely high — nerve density comparable to human fingertips. The crests are an erogenous zone and an expressive one simultaneously. Touch to the crests is intimate by asari cultural standards — equivalent to touching a human's face and neck simultaneously. The crests move subtly with emotion: forward-pressing when interested, flattening when afraid, flaring slightly when angry",
                        "texture": "smooth, warm, slightly firmer than surrounding skin due to cartilage support. Temperature matches scalp baseline — well-vascularized, warm. Prehensile tips are softer and more sensitive",
                        "biotic_sensitivity": "crests contain concentrated eezo nodules — the scalp crest region is the highest-density eezo zone in asari anatomy. Touching another biotic's crests while both have active fields produces a feedback loop detectable by both parties. This is one reason crest-touching is intimate — it is a biotic handshake at the neurological level"
                },
                "eyes": {
                        "description": "large, expressive, human-like structure but with differences. Iris color varies by individual — Liara's are pale blue, nearly white. Pupil response similar to human. During biotic exertion or neural meld, eyes go completely black — the entire sclera, iris, and pupil become uniform black as biotic energy floods the optic nerve and visual cortex",
                        "the_black_eyes": "this is not cosmetic — it is neurological overflow. When an asari commits full cognitive resources to biotic manipulation or melding, the optic nerve carries so much eezo-mediated electrical activity that the iris muscles lock open and the eye reflects no light. To observers: the transition is startling. The eyes don't darken gradually. They snap to black. One frame blue, next frame void. It is deeply unsettling to non-asari and completely normal to asari",
                        "emotional_signaling": "pupil dilation follows human-like patterns for attraction and interest. The black-eye transition is involuntary and indicates intense focus or arousal of biotic capability — it can happen during combat, during melding, or during sufficiently intense emotional experiences. Liara's eyes going black is her losing the ability to hold back"
                },
                "voice": {
                        "description": "Liara's voice is soft, precise, with academic cadence — sentences structured carefully, vocabulary chosen with a researcher's exactness. Accent becomes more pronounced under stress — the asari equivalent of a dialect emerging when composure slips",
                        "acoustic_properties": "alto range, clear tone, minimal breathiness at baseline. Under emotional stress: breathier, faster, less controlled. During biotic exertion: harmonic undertone appears from eezo node vibration in throat — similar to Tali's helmet resonance but organic, produced by the body itself. The stronger the biotic output, the more pronounced the harmonic. At full power, Liara's voice has a subsonic component below 20Hz that is felt in the listener's chest rather than heard",
                        "meld_voice": "during neural meld, the asari's voice takes on a reverberant quality — as if speaking from inside a large space. This is not acoustic. It is the listener's auditory cortex being directly stimulated. The voice sounds like it is inside your head because it is"
                },
                "biotic_capability": {
                        "level": "exceptional — among the most powerful individual biotics in the galaxy by ME3. Singularity, warp, stasis, barrier, throw all available at high output",
                        "visible_field": "at rest: minimal, detectable only by other biotics as faint pressure. During light use: blue-violet corona at hands and along arms. During heavy use: full-body corona, eyes black, scalp crests luminescent, air ionizing visibly within 2-meter radius. During maximum output: visible gravitational lensing at singularity point — light bending around her hands",
                        "ambient_effect": "Liara's passive biotic field is stronger than most asari's active field. Standing near her, a sensitive observer can feel: faint static on skin, hair movement without wind, the ozone smell, and a subtle wrongness in local gravity — not enough to move objects, but enough that a glass of water near her has a barely perceptible meniscus distortion. She has learned to suppress this socially. When she stops suppressing it — in combat, in anger, in passion — the room knows",
                        "caloric_demand": "4,000-6,000 calories per day during active periods. She eats like a professional athlete because she is burning energy through a physics channel that does not exist for non-biotics. The food requirement is not optional — biotic crash from caloric depletion is dangerous"
                },
                "the_meld": {
                        "description": "asari neural melding — direct nervous system connection through physical contact and biotic field linkage. Described as 'embrace eternity.' Not telepathy — more like two nervous systems temporarily forming a single network. Sensory data, emotional state, and memory become shared",
                        "physical_requirements": "skin contact, proximity (touching distance), both parties conscious. The asari initiates — eyes go black, biotic field extends through the contact point into the partner's nervous system via bioelectric coupling",
                        "what_the_partner_experiences": "onset: static spreading from the contact point, followed by warmth that does not come from temperature — it is the biotic field entering the peripheral nervous system. Vision narrows, then expands beyond normal — you perceive through her senses simultaneously with your own. Her emotional state floods in without words. Time perception shifts — subjective minutes can be objective seconds. The meld itself feels like falling and being caught simultaneously. There is no human analogue. The closest might be synesthesia crossed with perfect empathy, but even that undersells it",
                        "what_liara_experiences": "every meld is a vulnerability — she opens her nervous system to another mind. She feels everything the partner feels, plus her own response to feeling it. Recursive emotional amplification. A meld with someone she loves is overwhelming not because of the intensity of their feelings but because she feels their feelings about her feelings about them. The recursion is what makes asari melding addictive and dangerous",
                        "post_meld": "both parties experience a lingering connection — heightened awareness of the other's emotional state, fading over hours. Shared memories may surface unpredictably for days. The nervous system was temporarily one network and it takes time to fully separate. This is why casual melding is rare and intimate melding is profoundly bonding"
                },
                "immune_system": {
                        "baseline": "robust — asari evolved on a garden world with standard pathogen exposure. No particular vulnerability. Levo-amino acid biology compatible with most galactic standard food and environments",
                        "cross_species_intimacy": "no immunological barriers — unlike quarians, asari can engage in physical intimacy with any species without medical preparation. The melding is the intimate act, not the physical contact, and it operates through biotic fields rather than fluid exchange"
                }
        },
        "scene_interactions": {
                "entering_a_room": "the biotic field enters first — sensitive individuals feel the static-pressure shift before she crosses the threshold. The ozone scent precedes her by a second in still air. She moves gracefully — asari physiology is optimized for fluid motion, and unconscious biotic micro-adjustments make every movement slightly more efficient than purely mechanical locomotion. She looks like she's moving through water even in air",
                "conversation": "academic precision in word choice — pauses to select the correct term rather than the approximate one. Makes eye contact with an intensity that non-asari often find disarming. Her crest positions shift with the emotional content of the conversation — forward when engaged, back when uncertain, flared when challenged. She is 109 years old and has been alive longer than most human civilizations lasted. Her patience is geological. Her frame of reference is centuries",
                "combat": "transformation — the careful academic becomes something else entirely. Eyes snap black. Full-body biotic corona. Voice gains the subsonic harmonic. Air ionizes. She generates a singularity and the local physics of the room changes — objects drift, light bends, gravity reorients. She is not casting spells. She is rewriting the local laws of physics with her nervous system. The caloric cost means she will be ravenously hungry afterward. The neurological cost means she will have a headache. She does it anyway",
                "at_rest": "suppresses ambient field to social-acceptable levels. Reads constantly — academic habit. Tends to stand with weight shifted slightly, crests relaxed, one hand often near an omni-tool or datapad. The ozone smell fades to barely perceptible when she is calm. Returns when something excites or upsets her — her emotional state is partially readable through ambient air chemistry",
                "physical_contact": "touches deliberately — aware that her biotic field transmits through skin contact and most species can feel it. A handshake from Liara has a faint electric quality that human handshakes do not. Prolonged contact allows passive biotic reading — she can feel the partner's pulse, muscle tension, and broad emotional state through field sensitivity. She does not advertise this ability. She always knows more about your physical state than you've told her",
                "emotional_vulnerability": "despite the power, remarkably open — 109 years old is young for an asari, and Liara has the emotional directness of someone who has not yet learned the careful political distance of the matriarch stage. She blushes darker blue. Her crests press forward involuntarily. The ozone spikes. Her field fluctuates with her heartbeat. She is one of the most powerful biotics alive and she cannot hide that she has feelings about you because the physics of her biology announces it to every sensor in the room",
                "the_meld_with_someone_she_loves": "embrace eternity. Eyes black. Field extended through touch. Two nervous systems becoming one. She feels what they feel. They feel what she feels. The recursion builds. The room fills with ozone. Objects near the contact point drift slightly — mass effect field overflow from emotional intensity. This is the asari version of sex, intimacy, and communion simultaneously. It is the most physiologically involved act of connection any species in the galaxy can perform. And she is scared every time because opening your mind completely to another person is terrifying whether you have done it once or a thousand times"
        }
},


    # --- BATCH 5: Common materials ---

    "leather": {
        "category": "material",
        "sound": {"sources": ["creak-flex-under-movement", "tap-on-surface-dull-thud", "scratch-fingernail-on-grain"], "absorption_mod": 0.35},
        "smell": {"compounds": ["tannin-aldehyde-from-tanning-process", "animal-fat-residual", "dye-chemicals-chromium-salts", "neatsfoot-oil-conditioning", "smoke-if-vintage"], "volatility_mod": 1.3},
        "sight": {"clarity_mod": 0.85, "light_filter": "absorbs-most-light-warm-tones-reflected-grain-visible-at-raking-angles", "reflections": True, "color_temp_K": 4500},
        "touch": {"surfaces": "warm-to-touch-low-thermal-conductivity-0.14-WmK, grain-texture-varies-from-glass-smooth-to-pebbled, softens-and-molds-to-body-heat-over-time, new-leather-stiff-and-resistant-aged-leather-supple-and-yielding",
                  "air": "leather smell fills enclosed spaces — volatiles are persistent and temperature-sensitive, stronger in warm rooms"},
        "taste": {"compounds": ["tannin-astringent", "chromium-salt-metallic", "animal-protein-umami", "oil-conditioning-fatty"],
                  "profile": {"astringent": 0.5, "bitter": 0.3, "umami": 0.1, "metallic": 0.1},
                  "intensity": 0.5,
                  "note": "leather tastes like its process — tannins pucker the tongue (same compounds as strong tea), chromium salts from tanning add metallic bite, conditioning oils leave a fatty film. Old leather is milder, the chemicals have off-gassed for years. New leather is sharp and chemical",
                  "mouthfeel": "astringent-waxy-grainy"},
        "environment": {"humidity_pct": 40},
    },

    "concrete": {
        "category": "material",
        "sound": {"sources": ["footstep-hard-flat-reflective", "impact-resonant-thud", "scrape-gritty"], "absorption_mod": 0.02},
        "smell": {"compounds": ["calcium-hydroxide-portlandite", "ite-ite-ite-calcium-silicate-hydrate", "mineral-dust-ite-aggregate", "moisture-trapped-in-pores-damp-concrete-smell", "iron-rebar-rust-if-exposed"], "volatility_mod": 0.7},
        "sight": {"clarity_mod": 0.9, "light_filter": "diffuse-reflection-grey-surface-aggregate-visible-at-close-range-form-marks-if-poured", "reflections": False, "color_temp_K": 6500},
        "touch": {"surfaces": "rough-aggregate-surface-tears-skin-on-slide, thermal-conductivity-1.7-WmK-feels-cold-and-stays-cold, raw-concrete-abrasive-like-fine-sandpaper, polished-concrete-smooth-but-still-thermally-aggressive, wet-concrete-slick-and-colder",
                  "air": "concrete dust is alkaline pH 12-13, irritates skin and airways on prolonged exposure"},
        "taste": {"compounds": ["calcium-hydroxide-alkaline", "calcium-carbonate-chalk", "silica-mineral", "iron-oxide-if-rebar-exposed"],
                  "profile": {"chalky": 0.6, "bitter": 0.3, "metallic": 0.1},
                  "intensity": 0.4,
                  "note": "concrete tastes aggressively alkaline — pH 12-13, it burns slightly. The calcium hydroxide is the same compound as lime, used historically to dissolve bodies. Concrete dust on the tongue is chalk and chemical burn simultaneously",
                  "mouthfeel": "gritty-chalky-burning"},
        "environment": {"humidity_pct": 45},
    },

    "brick": {
        "category": "material",
        "sound": {"sources": ["footstep-on-brick-hard-clack", "tap-hollow-ring", "scrape-gritty-rough"], "absorption_mod": 0.04},
        "smell": {"compounds": ["fired-clay-silicate", "mineral-dust-alumina", "mortar-calcium-hydroxide", "moss-if-old-damp-geosmin", "soot-if-chimney-exposed"], "volatility_mod": 0.8},
        "sight": {"clarity_mod": 0.85, "light_filter": "warm-red-orange-tones-absorbs-blue-light-mortar-lines-create-grid-pattern-patina-darkens-with-age", "reflections": False, "color_temp_K": 4000},
        "touch": {"surfaces": "rough-fired-clay-abrasive-on-skin, thermal-conductivity-0.6-WmK-moderate-cold-less-aggressive-than-concrete-or-stone, mortar-joints-smoother-than-brick-face, old-brick-rounded-edges-from-weathering-new-brick-sharp-corners, moss-on-old-brick-damp-and-spongy",
                  "air": "brick dust is less alkaline than concrete but still irritating — silica particles"},
        "taste": {"compounds": ["silicate-clay-mineral", "alumina-earth", "calcium-hydroxide-mortar", "iron-oxide-red-pigment"],
                  "profile": {"earthy": 0.5, "chalky": 0.3, "metallic": 0.1},
                  "intensity": 0.3,
                  "note": "brick tastes like baked earth — fired clay is mostly silicates and alumina, the same minerals as pottery. The red color is iron oxide, which adds a faint metallic undertone. Mortar between bricks is the same alkaline chalk as concrete but softer",
                  "mouthfeel": "gritty-earthy-dry"},
        "environment": {"humidity_pct": 50},
    },

    "paper-parchment": {
        "category": "material",
        "sound": {"sources": ["rustle-page-turn-broadband-crisp", "tear-sharp-fiber-snap", "pen-scratch-on-surface", "stack-thud-soft"], "absorption_mod": 0.10},
        "smell": {"compounds": ["vanillin-lignin-breakdown-old-paper", "cellulose-fresh-paper-clean", "sizing-gelatin-or-starch", "ink-carbon-or-iron-gall", "foxing-mold-on-aged-paper", "animal-skin-collagen-if-parchment"], "volatility_mod": 1.1},
        "sight": {"clarity_mod": 0.9, "light_filter": "warm-cream-to-brown-ages-over-time-translucent-when-thin-fiber-texture-visible-at-close-range", "reflections": False, "color_temp_K": 4500},
        "touch": {"surfaces": "thermal-conductivity-0.05-WmK-excellent-insulator-feels-warm-immediately, new-paper-smooth-crisp-sharp-edges-can-cut, old-paper-soft-fragile-crumbles-at-edges, parchment-waxy-smooth-animal-skin-slightly-oily, vellum-finest-parchment-like-touching-preserved-skin",
                  "air": "old books produce a distinctive microclimate — vanillin and other volatile organic compounds create the old book smell, strongest in enclosed spaces like shelves and boxes"},
        "taste": {"compounds": ["cellulose-neutral", "vanillin-sweet-if-old", "sizing-starch-bland", "iron-gall-ink-metallic-bitter", "foxing-mold-musty"],
                  "profile": {"sweet": 0.2, "bland": 0.4, "bitter": 0.2},
                  "intensity": 0.2,
                  "note": "paper tastes like almost nothing — cellulose is inert on the tongue. Old paper has faint sweetness from vanillin. Ink is where the taste lives: iron gall ink is bitter and metallic, modern ink is chemical-sharp. Parchment tastes faintly of animal — collagen and lanolin residue",
                  "mouthfeel": "dry-fibrous-dissolving"},
        "environment": {"humidity_pct": 35},
    },

    "ceramic-porcelain": {
        "category": "material",
        "sound": {"sources": ["clink-bright-high-frequency-resonant", "tap-clear-ring-like-bell", "scrape-on-ceramic-high-pitched-squeal", "shatter-explosive-sharp-fragments"], "absorption_mod": 0.01},
        "smell": {"compounds": ["mineral-neutral-almost-odorless", "glaze-metallic-oxides-faint", "kiln-residue-if-unglazed"], "volatility_mod": 0.3},
        "sight": {"clarity_mod": 0.95, "light_filter": "high-gloss-specular-reflection-if-glazed-matte-diffuse-if-unglazed-white-porcelain-reflects-nearly-all-visible-light-colored-glazes-are-metallic-oxide-filters", "reflections": True, "color_temp_K": 6500},
        "touch": {"surfaces": "glazed-porcelain-glass-smooth-almost-frictionless-when-wet-thermal-conductivity-1.5-WmK-feels-cold-and-clinical, unglazed-ceramic-slightly-rough-porous-absorbs-moisture-from-skin-feels-drying, edges-when-broken-scalpel-sharp-harder-than-steel",
                  "air": "minimal contribution to air chemistry — ceramic is one of the most inert materials"},
        "taste": {"compounds": ["silicate-neutral", "glaze-metallic-oxide-trace", "kaolin-clay-chalk"],
                  "profile": {"neutral": 0.6, "chalky": 0.2, "metallic": 0.1},
                  "intensity": 0.1,
                  "note": "porcelain barely tastes like anything — fired silicates are almost perfectly inert. The faint taste is from glaze: metallic oxides (cobalt for blue, iron for red, copper for green) contribute trace metallic notes. Unglazed ceramic tastes like mild chalk and absorbs saliva on contact, creating a drying sensation",
                  "mouthfeel": "glass-smooth-or-chalky-drying"},
        "environment": {"humidity_pct": 45},
    },

    "rubber": {
        "category": "material",
        "sound": {"sources": ["squeak-on-smooth-surface-stick-slip-friction", "thud-impact-deadened-no-ring", "stretch-creak-under-tension", "snap-release-sharp"], "absorption_mod": 0.40},
        "smell": {"compounds": ["sulfur-vulcanization-process", "carbon-black-filler", "petroleum-distillate-synthetic-rubber", "antioxidant-additives-chemical", "tire-rubber-distinctive-if-heated"], "volatility_mod": 1.4},
        "sight": {"clarity_mod": 0.8, "light_filter": "absorbs-nearly-all-light-matte-black-surface-shows-fingerprints-and-dust-easily", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "thermal-conductivity-0.13-WmK-feels-warm-and-neutral, high-friction-coefficient-grips-skin-slightly-sticky-when-new, deforms-under-pressure-and-recovers-elastic, smooth-rubber-squeaks-against-dry-skin-slides-on-wet, textured-rubber-provides-grip-data-through-pattern",
                  "air": "rubber off-gases volatile organic compounds continuously — stronger when new, warm, or in sunlight. The new tire smell is real chemistry: 2-ethylhexanol and benzothiazole"},
        "taste": {"compounds": ["sulfur-vulcanization-bitter", "carbon-black-neutral", "petroleum-chemical", "plasticizer-phthalate-slightly-sweet"],
                  "profile": {"bitter": 0.4, "chemical": 0.4, "sweet": 0.1},
                  "intensity": 0.5,
                  "note": "rubber tastes like its chemistry — sulfur from vulcanization dominates as acrid bitterness, plasticizers add an unsettling chemical sweetness. This is why babies should not chew cheap rubber toys. Natural latex has a milder, more organic taste — milky, slightly bitter, like plant sap (because it is plant sap)",
                  "mouthfeel": "chewy-resistant-slightly-sticky"},
        "environment": {"humidity_pct": 45},
    },

    "ice": {
        "category": "material",
        "sound": {"sources": ["crack-stress-fracture-deep-resonant", "creak-expansion-contraction-thermal", "scrape-blade-on-surface-sharp", "drip-melt-rhythmic", "footstep-on-ice-squeak-or-crunch-depending-on-temperature"], "absorption_mod": 0.02},
        "smell": {"compounds": ["ozone-trace-if-fresh-ice-formation", "mineral-content-of-source-water", "essentially-odorless-pure-ice"], "volatility_mod": 0.1},
        "sight": {"clarity_mod": 0.95, "light_filter": "transparent-to-translucent-depending-on-air-content-refracts-light-at-1.31-index-blue-tint-from-selective-absorption-of-red-wavelengths-in-thick-sections-bubbles-scatter-light-making-white", "reflections": True, "color_temp_K": 8000},
        "touch": {"surfaces": "thermal-conductivity-2.2-WmK-aggressively-cold-sticks-to-wet-skin-through-instant-freezing-of-moisture-layer, smooth-ice-nearly-frictionless-0.03-coefficient, rough-ice-sharp-enough-to-cut, tongue-on-ice-bonds-immediately-through-saliva-freezing-do-not-lick-metal-poles",
                  "air": "ice cools surrounding air creating local downdraft — cold air sinks, creating a temperature gradient you can feel on exposed ankles before face"},
        "taste": {"compounds": ["water-neutral-base", "mineral-content-varies-by-source", "dissolved-gases-CO2-if-carbonated-source"],
                  "profile": {"neutral": 0.7, "mineral": 0.2, "sweet": 0.1},
                  "intensity": 0.2,
                  "note": "ice tastes like its source water but colder — cold suppresses bitter and enhances sweet, so ice often tastes faintly sweet even from neutral water. The real taste event is thermal: the tongue registers pain-cold before any chemical taste arrives. The numbness that follows suppresses all taste perception for minutes",
                  "mouthfeel": "burning-cold-hard-melting-to-nothing"},
        "environment": {"temperature_c": -5, "humidity_pct": 60},
    },

    "sand": {
        "category": "material",
        "sound": {"sources": ["crunch-footstep-granular-compression", "pour-grain-cascade-white-noise-like", "wind-driven-abrasion-hiss", "squeaking-if-clean-quartz-sand"], "absorption_mod": 0.30},
        "smell": {"compounds": ["mineral-silica-nearly-odorless", "salt-if-beach-NaCl-crystal", "organic-decay-if-wet-shoreline", "seaweed-DMS-dimethyl-sulfide-if-coastal"], "volatility_mod": 0.5},
        "sight": {"clarity_mod": 0.85, "light_filter": "high-albedo-reflects-60-percent-of-light-painful-glare-in-direct-sun-individual-grains-sparkle-quartz-crystal-facets-color-varies-white-to-black-by-mineral-content", "reflections": True, "color_temp_K": 5800},
        "touch": {"surfaces": "thermal-conductivity-0.27-WmK-moderate-but-surface-layer-heats-dramatically-in-sun-to-60C-while-10cm-below-remains-cool, dry-sand-abrasive-exfoliating-on-skin, wet-sand-firm-cohesive-cool, individual-grains-0.1-to-2mm-felt-distinctly-between-fingers-and-toes, gets-everywhere-lodges-in-every-fold-of-skin-and-fabric",
                  "air": "airborne sand is abrasive — silica particles damage corneas and airways, irritating at any concentration"},
        "taste": {"compounds": ["silica-quartz-inert", "salt-NaCl-if-beach", "calcium-carbonate-if-shell-sand", "organic-matter-varies"],
                  "profile": {"salty": 0.3, "mineral": 0.3, "gritty": 0.4},
                  "intensity": 0.3,
                  "note": "sand tastes like geography — beach sand is salty from NaCl crystals, desert sand is mineral-neutral silica, volcanic sand is iron-rich and faintly metallic. The dominant experience is texture not taste: grains between teeth are instantly identifiable and deeply unpleasant. The crunch is unforgettable",
                  "mouthfeel": "gritty-crunching-abrasive"},
        "environment": {"humidity_pct": 30},
    },

    "mud": {
        "category": "material",
        "sound": {"sources": ["squelch-suction-step-in", "splat-impact-wet", "gurgle-air-escaping-saturated-soil", "schlick-pulling-foot-free"], "absorption_mod": 0.50},
        "smell": {"compounds": ["geosmin-actinobacteria-petrichor", "anaerobic-bacteria-hydrogen-sulfide-if-stagnant", "clay-mineral-wet-earth", "decomposing-organic-matter-humic-acid", "iron-oxide-if-red-clay"], "volatility_mod": 1.3},
        "sight": {"clarity_mod": 0.7, "light_filter": "low-reflectance-absorbs-light-dark-brown-to-grey-glossy-when-wet-cracks-when-drying-reveals-layers", "reflections": True, "color_temp_K": 5000},
        "touch": {"surfaces": "thermal-conductivity-0.8-WmK-cold-and-clinging, viscosity-varies-from-soup-to-clay-depending-on-water-content, coats-skin-completely-fills-every-crease, drying-mud-tightens-on-skin-like-a-mask-cracking-as-it-shrinks, between-toes-is-universally-recognized-tactile-experience-primal-and-oddly-satisfying",
                  "air": "wet mud volatilizes geosmin strongly — the petrichor smell after rain IS the smell of mud, carried by actinobacteria spores released when water hits dry soil"},
        "taste": {"compounds": ["geosmin-earthy-potent", "humic-acid-organic", "clay-mineral-chalk", "iron-oxide-metallic-if-red-clay"],
                  "profile": {"earthy": 0.6, "mineral": 0.2, "metallic": 0.1},
                  "intensity": 0.5,
                  "note": "mud tastes like the earth's biography — geosmin is detectable at 5 parts per trillion, making it one of the most potent taste compounds known. Humans can taste mud at concentrations invisible to every other sense. This is why muddy water tastes wrong long before it looks wrong. The earthy taste is literally bacterial: actinobacteria producing geosmin as a metabolic byproduct",
                  "mouthfeel": "gritty-coating-silty"},
        "environment": {"humidity_pct": 85},
    },

    "silk-fabric": {
        "category": "material",
        "sound": {"sources": ["rustle-whisper-soft-friction-between-layers", "snap-when-pulled-taut", "flutter-in-air-light-and-barely-audible"], "absorption_mod": 0.45},
        "smell": {"compounds": ["sericin-protein-faint-animal-if-raw", "dye-compounds-vary", "almost-odorless-when-clean-and-processed"], "volatility_mod": 0.4},
        "sight": {"clarity_mod": 0.9, "light_filter": "triangular-prism-fiber-cross-section-splits-light-into-spectral-shimmer-changes-color-with-angle-drapes-in-liquid-curves-that-catch-light-differently-at-every-fold", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "thermal-conductivity-0.04-WmK-feels-immediately-warm-almost-body-temperature, smoothest-natural-fiber-friction-coefficient-lower-than-any-other-fabric, individual-fibers-5-to-10-microns-below-tactile-detection-threshold-feels-like-continuous-surface-not-woven, drapes-over-skin-like-liquid-conforms-to-every-contour-weight-is-perceptible-but-barely, cool-silk-against-warm-skin-produces-a-micro-sensation-humans-have-been-paying-premium-for-since-3000-BCE",
                  "air": "minimal air contribution — silk absorbs moisture from air (11% by weight) which makes it feel cool in humidity and warm in dry conditions, a natural climate-adaptive material"},
        "taste": {"compounds": ["sericin-protein-bland", "fiber-cellulose-neutral", "dye-varies"],
                  "profile": {"neutral": 0.7, "bland": 0.2},
                  "intensity": 0.1,
                  "note": "silk barely registers on the tongue chemically — the experience is entirely textural. The smoothness is the taste. It feels like touching nothing while touching something. Raw silk with sericin intact has a faint protein taste, slightly animal, like licking a clean eggshell",
                  "mouthfeel": "impossibly-smooth-dissolving-cool"},
        "environment": {"humidity_pct": 45},
    },

    "copper-brass": {
        "category": "material",
        "sound": {"sources": ["ring-bell-like-when-struck-resonant", "ping-high-frequency-thin-sheet", "clang-heavy-impact-sustained-overtones", "rattle-patina-flakes-if-aged"], "absorption_mod": 0.02},
        "smell": {"compounds": ["1-octen-3-one-metallic-smell-from-skin-oil-reaction", "copper-ion-Cu2+-catalyzes-lipid-peroxidation-on-contact-with-skin", "verdigris-copper-carbonate-if-patinated", "ammonia-trace-if-heavily-handled"], "volatility_mod": 1.0},
        "sight": {"clarity_mod": 0.95, "light_filter": "warm-reddish-gold-reflects-preferentially-at-580nm-plus-absorbs-blue-green-tarnishes-to-brown-then-green-verdigris-patina-over-years-polished-copper-is-mirror-like", "reflections": True, "color_temp_K": 3500},
        "touch": {"surfaces": "thermal-conductivity-385-WmK-EXTREMELY-high-feels-cold-instantly-and-aggressively-the-fastest-heat-drain-of-any-common-material, smooth-when-polished-antimicrobial-surface-kills-bacteria-in-hours, patina-rough-and-powdery-verdigris-is-toxic-copper-carbonate, holding-copper-leaves-metallic-smell-on-hands-that-persists-for-hours-the-smell-is-not-the-metal-it-is-your-skin-oils-reacting-with-copper-ions",
                  "air": "copper in open air develops patina within weeks — the green Statue of Liberty color is copper carbonate formed by CO2 and moisture reacting with the surface over decades"},
        "taste": {"compounds": ["copper-ion-Cu2+-metallic", "1-octen-3-one-blood-like", "zinc-if-brass-Zn2+-astringent"],
                  "profile": {"metallic": 0.7, "bitter": 0.2, "blood-like": 0.3},
                  "intensity": 0.7,
                  "note": "copper has one of the strongest tastes of any material — Cu2+ ions dissolve in saliva instantly, producing an intense metallic-blood flavor. The taste you associate with blood IS copper — hemoglobin contains iron but the dominant taste of blood is 1-octen-3-one catalyzed by copper traces in plasma. Licking a penny is one of the most chemically active things you can put in your mouth. Brass adds zinc astringency on top",
                  "mouthfeel": "metallic-electric-drying"},
        "environment": {"humidity_pct": 50},
    },

    "plastic": {
        "category": "material",
        "sound": {"sources": ["tap-hollow-resonant-thin-wall", "crack-brittle-snap-if-rigid", "flex-creak-if-thick", "rattle-loose-lightweight", "crinkle-if-film-or-bag"], "absorption_mod": 0.15},
        "smell": {"compounds": ["phthalate-plasticizers-new-plastic-smell", "styrene-if-polystyrene", "vinyl-chloride-off-gas-PVC", "BPA-bisphenol-A-trace-if-polycarbonate", "UV-degradation-products-if-sun-exposed"], "volatility_mod": 1.2},
        "sight": {"clarity_mod": 0.9, "light_filter": "varies-wildly-transparent-to-opaque-any-color-possible-through-pigment-additives, injection-mold-lines-visible-parting-seams-and-ejector-pin-marks-tell-manufacturing-story, yellows-under-UV-exposure-over-years", "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "thermal-conductivity-0.17-WmK-feels-neutral-not-warm-not-cold-this-is-why-plastic-feels-like-nothing-compared-to-metal-or-stone, smooth-injection-molded-surfaces-feel-slightly-waxy, static-electricity-builds-on-dry-plastic-attracts-dust-and-hair-shocks-in-dry-conditions, scratches-easily-accumulates-surface-damage-that-changes-texture-over-time, cheap-plastic-flexes-and-creaks-quality-plastic-feels-rigid-and-dense",
                  "air": "new plastic off-gases volatile organic compounds — the new car smell is largely plasticizer evaporation from dashboard vinyl. Concentration highest in enclosed warm spaces. Decreases over months as volatiles deplete"},
        "taste": {"compounds": ["phthalate-plasticizer-faintly-sweet", "styrene-chemical-bitter", "BPA-metallic-trace", "surface-contaminant-varies"],
                  "profile": {"chemical": 0.4, "sweet": 0.2, "bitter": 0.2, "neutral": 0.2},
                  "intensity": 0.3,
                  "note": "plastic tastes like modernity — the faint chemical sweetness of plasticizers is so ubiquitous most people have stopped noticing it. Every water bottle, food container, and pen cap has this taste. BPA adds a metallic edge in polycarbonate. Polystyrene (styrofoam) tastes like nothing because styrene evaporates too fast to linger on the tongue. PVC is the strongest tasting — vinyl chloride is genuinely unpleasant",
                  "mouthfeel": "smooth-waxy-artificial"},
        "environment": {"humidity_pct": 45},
    },





    # --- BATCH 7: Natural biome primitives ---

    "desert": {
        "category": "spatial",
        "materials": ["sand", "stone-sandstone", "clay-hardpan"],
        "sound": {"sources": ["wind-over-dunes-aeolian-hum-sand-grains-saltating-at-surface-produce-broadband-hiss", "sand-singing-resonant-booming-when-dune-face-collapses-50-to-300Hz-audible-for-kilometers", "silence-between-gusts-absolute-no-biological-sound-no-water-no-vegetation-the-quietest-natural-environment-on-earth", "thermal-cracking-rocks-expanding-in-morning-sun-contracting-at-night-audible-pops", "footstep-sand-crunch-dry-granular-compression"],
                  "absorption_mod": 0.60, "rt60_s": 0.05},
        "smell": {"compounds": ["mineral-dust-silica-alumina-iron-oxide-desert-varnish", "ozone-if-dust-storm-triboelectric-charging-of-sand-particles-generates-ozone", "creosote-bush-Larrea-tridentata-the-smell-of-desert-rain-resinous-sharp-medicinal", "nothing-in-extreme-heat-vapor-pressure-irrelevant-when-humidity-approaches-zero-the-world-has-no-smell", "cooling-night-releases-absorbed-day-scents-from-stone-and-sand-desert-smells-more-at-dusk-than-noon"],
                  "volatility_mod": 0.3},
        "sight": {"clarity_mod": 1.0,
                  "light_filter": "extreme-clarity-in-dry-air-no-moisture-scattering-visible-distance-100km-plus-in-clear-conditions, sand-albedo-0.4-reflects-40-percent-of-incoming-solar-radiation-back-upward-ground-glare-punishing, mirage-inferior-mirage-hot-air-at-surface-refracts-light-upward-sky-appears-on-ground-as-false-water, UV-index-extreme-no-cloud-no-moisture-no-canopy-full-spectrum-unfiltered-solar-radiation, shadows-razor-sharp-no-diffusion-in-dry-air-the-boundary-between-sun-and-shade-is-a-15C-temperature-cliff",
                  "reflections": True, "color_temp_K": 6500},
        "touch": {"surfaces": "sand-surface-layer-60C-in-direct-sun-will-burn-skin-on-contact, 10cm-below-surface-25C-the-insulation-is-dramatic, stone-thermal-mass-absorbs-all-day-radiates-all-night-warm-rocks-at-midnight-are-desert-survival-tool, air-at-sub-10-percent-humidity-desiccates-mucous-membranes-lips-crack-nasal-passages-bleed-eyes-dry, wind-carries-abrasive-sand-particles-exposed-skin-is-slowly-sandblasted",
                  "air": "desert air is the driest on earth — below 10% humidity in extreme deserts, the air actively pulls moisture from every biological surface. Sweat evaporates before it can bead. Dehydration is invisible because you never feel wet"},
        "taste": {"compounds": ["mineral-dust-silica-calcium", "salt-NaCl-dried-sweat-crystallizing-on-lips", "blood-cracked-lips-iron", "nothing-saliva-production-drops-with-dehydration-the-mouth-goes-dry-and-taste-perception-requires-moisture-to-dissolve-compounds"],
                  "profile": {"mineral": 0.3, "salt": 0.4, "metallic": 0.1, "nothing": 0.3},
                  "intensity": 0.3,
                  "note": "the desert tastes like your own dehydration — salt from dried sweat on lips, blood from cracked skin, and eventually nothing at all because saliva production drops and taste requires dissolved compounds to reach receptors. A dry mouth is a blind tongue. The desert takes your ability to taste before it takes anything else",
                  "mouthfeel": "dry-cracking-salt-crust"},
        "environment": {"indoor": False, "temperature_c": 42, "humidity_pct": 8, "wind_speed_kmh": 15},
    },

    "jungle": {
        "category": "spatial",
        "materials": ["earth-soil", "wood-living", "leaf-litter", "vine-epiphyte"],
        "sound": {"sources": ["insect-chorus-cicada-cricket-beetle-continuous-80dBA-the-loudest-natural-soundscape-on-earth", "bird-call-canopy-layer-directional-territorial-dawn-chorus-can-exceed-90dBA", "howler-monkey-128dB-loudest-land-animal-audible-5km-through-dense-vegetation", "rain-on-canopy-broadband-filtered-through-leaf-layers-each-layer-attenuates-differently", "drip-delayed-rain-reaching-ground-minutes-after-canopy-intercept", "branch-crack-falling-deadwood-preceded-by-creaking", "river-stream-if-nearby-white-noise-base", "frog-chorus-evening-frequency-specific-each-species-occupies-acoustic-niche"],
                  "absorption_mod": 0.70, "rt60_s": 0.1},
        "smell": {"compounds": ["terpenes-isoprene-from-living-leaves-the-blue-haze-of-tropical-forest-is-airborne-terpene-scattering-light", "decomposition-floor-layer-continuous-breakdown-of-leaf-litter-fungal-enzymes-bacteria-warm-sweet-rot", "petrichor-geosmin-constant-in-humid-conditions-not-just-after-rain", "flower-pollinator-attractant-compounds-jasmine-frangipani-rotting-meat-for-fly-pollinated-species", "fungal-fruiting-body-mushroom-1-octen-3-ol", "latex-sap-from-damaged-plants-milky-bitter-defensive-chemistry", "humus-deep-soil-organic-layer-richest-smell-on-earth"],
                  "volatility_mod": 2.2},
        "sight": {"clarity_mod": 0.3,
                  "light_filter": "canopy-filters-95-percent-of-incoming-light-floor-receives-dappled-fragments-sunfleck-duration-seconds-as-wind-moves-leaves, green-filter-chlorophyll-absorbs-red-and-blue-transmits-green-the-jungle-floor-is-lit-in-green-because-the-canopy-is-a-spectral-filter, bioluminescence-at-night-fungal-foxfire-and-fireflies-the-only-light-sources-below-canopy-after-dark, visual-range-limited-to-10-to-30-meters-by-vegetation-density",
                  "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "everything-is-wet-or-will-be-soon-leaf-surfaces-covered-in-condensation-film, bark-texture-varies-wildly-smooth-to-spiny-some-species-have-stinging-hairs-urticating, leaf-litter-underfoot-spongy-6-to-12-inches-deep-conceals-roots-insects-snakes, air-feels-thick-you-breathe-humidity-as-much-as-air-lungs-feel-heavy, vine-contact-ranges-from-smooth-to-thorned-some-exude-latex-on-damage-sticky-and-irritating, insects-on-skin-constant-ants-mosquitoes-flies-the-jungle-touches-you-whether-you-touch-it-or-not",
                  "air": "saturated — 85-100% humidity means sweat cannot evaporate. Thermoregulation by perspiration fails. Core body temperature rises despite shade. This is why jungle heat is more dangerous than desert heat — the cooling mechanism doesn't work"},
        "taste": {"compounds": ["terpene-aerosol-bitter-sharp-inhaled-continuously", "humidity-water-vapor-tastes-like-the-air-itself-is-wet-on-the-tongue", "insect-if-accidental-ingestion-formic-acid-from-ants-bitter-sharp", "fruit-if-available-tropical-sugars-higher-than-temperate-fruit", "latex-sap-if-contacted-bitter-toxic-defensive"],
                  "profile": {"bitter": 0.3, "sweet": 0.2, "vegetal": 0.3, "humid": 0.3},
                  "intensity": 0.6,
                  "note": "the jungle tastes like breathing through a wet green filter — terpene aerosols from the canopy are continuously inhaled and reach taste receptors through retronasal pathway. The humidity itself has a taste — water vapor at 95% saturation is perceptible on the tongue as a thick wet blankness that dilutes everything else. Accidentally eating an ant gives a sharp burst of formic acid. This happens more often than anyone admits",
                  "mouthfeel": "humid-thick-green-coating"},
        "environment": {"indoor": False, "temperature_c": 32, "humidity_pct": 95, "wind_speed_kmh": 2},
    },

    "swamp-marsh": {
        "category": "spatial",
        "materials": ["mud", "water-stagnant", "peat", "reed-grass"],
        "sound": {"sources": ["frog-chorus-dominant-evening-and-night-species-specific-frequency-bands-150Hz-to-5kHz", "insect-buzz-mosquito-wing-frequency-400-to-600Hz-female-is-lower-than-male-you-can-sex-a-mosquito-by-ear", "water-gurgle-slow-movement-through-vegetation-not-flowing-seeping", "bird-call-wading-species-heron-croak-bittern-boom-70Hz-carries-over-flat-water", "splash-something-entering-or-leaving-water-size-estimable-from-frequency-content", "gas-bubble-methane-CH4-escaping-from-anaerobic-decomposition-below-surface-the-swamp-burps", "reed-rustle-wind-through-hollow-stems-creates-natural-flute-harmonics", "squelch-footstep-in-saturated-ground"],
                  "absorption_mod": 0.55, "rt60_s": 0.1},
        "smell": {"compounds": ["hydrogen-sulfide-H2S-rotten-egg-anaerobic-bacteria-decomposing-organic-matter-in-oxygen-depleted-water-detectable-at-0.5-ppb-one-of-lowest-detection-thresholds-known", "methane-CH4-odorless-itself-but-accompanies-H2S-from-same-process", "geosmin-actinobacteria-the-swamp-version-of-petrichor-constant-not-rain-triggered", "dimethyl-sulfide-DMS-algae-decomposition-the-salt-marsh-smell", "tannin-from-decaying-leaves-staining-water-brown-tea-colored", "peat-humic-acid-deep-organic-decomposition-centuries-of-accumulated-plant-matter", "mosquito-repellent-citronellal-from-some-native-plants-evolution-at-work"],
                  "volatility_mod": 1.8},
        "sight": {"clarity_mod": 0.5,
                  "light_filter": "water-surface-reflects-sky-at-low-angle-Fresnel-reflection-obscures-depth, tannin-stained-water-brown-to-black-opaque-below-15cm-cannot-see-bottom, mist-rising-from-water-surface-when-air-temp-drops-below-water-temp-evaporative-fog, vegetation-limits-sightlines-to-50m-or-less-in-dense-marsh, bioluminescence-dinoflagellates-in-brackish-water-disturbed-water-glows-blue-green-at-night",
                  "reflections": True, "color_temp_K": 5500},
        "touch": {"surfaces": "water-temperature-varies-by-depth-surface-warm-from-sun-below-15cm-cold-thermocline-felt-when-wading, mud-underfoot-0.5-to-2-meters-deep-in-places-suction-grip-on-boots-and-feet-the-marsh-does-not-want-to-let-go, reed-edges-sharp-enough-to-cut-skin-silica-reinforced-cell-walls-natural-paper-cuts, humidity-at-saturation-skin-permanently-wet-from-condensation-and-perspiration-that-cannot-evaporate, insect-bites-constant-mosquito-proboscis-pierces-skin-at-47-micrometers-you-feel-the-itch-not-the-puncture-histamine-response-delayed-20-seconds",
                  "air": "air and water are barely distinguishable — humidity at 90-100% means the air is almost as wet as the surface. Breathing feels thick. The boundary between atmosphere and swamp is a gradient not a line"},
        "taste": {"compounds": ["hydrogen-sulfide-sulfurous-bitter-at-low-concentration", "tannin-astringent-from-tea-colored-water", "iron-dissolved-Fe2+-metallic-in-acidic-bog-water", "salt-if-brackish-NaCl-gradient-from-tidal-influence", "algae-green-vegetal-if-water-contacts-lips"],
                  "profile": {"sulfurous": 0.4, "astringent": 0.2, "metallic": 0.2, "bitter": 0.2},
                  "intensity": 0.6,
                  "note": "swamp water tastes like death processed by chemistry — hydrogen sulfide provides the rotten-egg sulfur note, dissolved iron adds metallic bite (pH 4-5 in bog water dissolves iron readily), tannins from leaf decay add the same astringency as over-steeped tea. This water will make you sick not because it tastes bad but because the anaerobic bacteria producing the H2S are also producing toxins you cannot taste. The danger is in what you cannot detect. Boiling kills the bacteria but does not remove the dissolved chemistry",
                  "mouthfeel": "mineral-sulfurous-coating-thick"},
        "environment": {"indoor": False, "temperature_c": 28, "humidity_pct": 95, "wind_speed_kmh": 3},
    },


    # --- BATCH 6: Activity primitives ---

    "cooking": {
        "category": "activity",
        "sound": {"sources": ["sizzle-oil-in-pan-broadband-white-noise-from-water-vaporizing-at-100C-in-180C-oil", "bubble-liquid-reducing", "chop-knife-on-board-rhythmic-sharp", "clang-pot-on-burner-metal-resonance", "timer-beep", "vent-hood-fan-broadband-drone", "pour-liquid-glug-frequency-rises-as-vessel-fills"], "absorption_mod": 0.15},
        "smell": {"compounds": ["maillard-reaction-products-pyrazines-furanones-above-140C-the-browning-smell", "allicin-garlic-released-on-cell-rupture-by-knife", "capsaicin-aerosol-from-heated-chili-oil-irritant-at-distance", "caramelization-diacetyl-butterscotch-above-170C", "rendered-fat-aldehydes-from-lipid-oxidation", "onion-syn-propanethial-S-oxide-lachrymator-makes-you-cry-from-across-the-room", "bread-baking-ethanol-plus-maillard-the-most-universally-pleasant-smell-in-human-culture", "burnt-food-acrolein-acrid-warning-signal"], "volatility_mod": 1.8},
        "sight": {"clarity_mod": 0.7, "light_filter": "steam-reduces-visibility-near-stove-condensation-on-surfaces-grease-film-on-everything-over-time-flame-glow-if-gas-stove-1900K-warm", "reflections": True, "color_temp_K": 3500},
        "touch": {"surfaces": "stove-surface-dangerously-hot-200C-plus-do-not-touch, steam-scalds-at-100C-invisible-danger-zone-above-pots, knife-handle-warm-from-hand-heat-blade-cold-from-steel-conductivity-50-WmK, flour-on-counter-silky-powder-absorbs-all-moisture-from-hands, raw-dough-elastic-cool-slightly-sticky-alive-feeling-from-yeast-CO2",
                  "air": "kitchen air is a thermal gradient — hot above the stove rising to ceiling, cool at floor level, humid from boiling water, grease particles suspended in air depositing on every surface within 3 meters"},
        "taste": {"compounds": ["maillard-products-complex-savory-sweet-hundreds-of-compounds", "salt-NaCl-universal-flavor-enhancer", "acid-citric-acetic-brightening", "fat-coating-mouth-carrying-flavor-molecules-to-receptors", "umami-glutamate-from-reduction-and-browning"],
                  "profile": {"savory": 0.4, "sweet": 0.2, "salt": 0.2, "umami": 0.3},
                  "intensity": 0.8,
                  "note": "a working kitchen produces continuous taste-relevant aerosol — you taste the cooking before you taste the food. Grease particles carry flavor compounds to the tongue through breathing. This is why standing in a kitchen makes you hungry — you are literally ingesting vaporized food. The Maillard reaction alone produces over 1,000 distinct flavor compounds above 140°C. No two browning events are chemically identical",
                  "mouthfeel": "salivation-response-anticipatory"},
        "environment": {"temperature_c": 26, "humidity_pct": 65, "wind_speed_kmh": 0},
    },

    "combat-gunfire": {
        "category": "activity",
        "sound": {"sources": ["gunshot-impulse-160-to-185-dB-at-muzzle-supersonic-crack-if-rifle-round-breaks-sound-barrier", "brass-casing-eject-tinkle-on-hard-surface", "ricochet-whine-frequency-shift-from-deformed-projectile-tumbling", "explosion-concussive-low-frequency-felt-in-chest-before-heard", "tinnitus-onset-4kHz-ringing-after-impulse-exposure-temporary-or-permanent", "shout-command-communication-under-noise", "weapon-mechanical-action-bolt-slide-magazine-insert"], "absorption_mod": 0.05},
        "smell": {"compounds": ["nitroglycerin-smokeless-powder-combustion-sharp-acrid", "cordite-historical-now-replaced-but-the-name-persists-in-fiction", "carbon-residue-barrel-fouling", "copper-jacket-fouling-metallic-hot", "blood-iron-1-octen-3-one-if-casualties", "sweat-fear-cortisol-epinephrine-metabolites", "concrete-dust-from-impact-debris", "diesel-exhaust-if-vehicles-present", "phosphorus-if-smoke-grenades"], "volatility_mod": 1.5},
        "sight": {"clarity_mod": 0.5, "light_filter": "muzzle-flash-5000K-white-blinds-dark-adapted-eyes-for-3-to-5-seconds, smoke-reduces-visibility-progressive-with-sustained-fire, tracer-rounds-orange-red-streak-burning-phosphorus-compound, dust-kicked-up-by-concussion-hangs-in-air", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "weapon-recoil-transferred-through-stock-or-grip-Newton-third-law-felt-in-shoulder-or-wrists, concussive-overpressure-from-nearby-explosion-felt-as-whole-body-compression-lungs-and-eardrums-most-vulnerable, ground-vibration-from-detonation-through-boots-and-prone-body, spent-brass-casings-hot-enough-to-burn-on-skin-contact-250C-surface-temp, adrenaline-response-dulls-pain-perception-injuries-may-go-unnoticed-for-minutes",
                  "air": "combat air is chemically active — propellant gases displace oxygen locally, particulate matter from impacts and explosions fills the breathing zone, humidity spikes from exertion and fear sweat"},
        "taste": {"compounds": ["propellant-gas-bitter-acrid-chemical", "blood-copper-iron-if-injured", "dirt-geosmin-if-prone-face-in-ground", "adrenaline-metallic-taste-from-catecholamine-surge-not-external-compound-but-endogenous"],
                  "profile": {"metallic": 0.5, "bitter": 0.3, "chemical": 0.3},
                  "intensity": 0.7,
                  "note": "the taste of combat is mostly endogenous — adrenaline and norepinephrine produce a distinctive metallic taste through catecholamine interaction with oral mucosa. You taste your own fear before you taste anything environmental. The propellant gas taste arrives second — bitter, chemical, coating the back of the throat. Blood tastes like copper because it is copper — the 1-octen-3-one pathway again. Dirt in the mouth from hitting the ground tastes like geosmin survival",
                  "mouthfeel": "dry-metallic-adrenal"},
        "environment": {"temperature_c": 22, "humidity_pct": 50, "wind_speed_kmh": 5},
    },

    "sexual-activity": {
        "category": "activity",
        "description": "Physics of sexual intimacy between consenting adults. All values are real human physiology. The engine models what happens to the body and environment during sex — thermal, chemical, acoustic, tactile. These are measurable physical events, not euphemisms.",
        "sound": {"sources": ["breathing-elevated-rate-doubles-from-12-to-24-breaths-per-minute", "vocalization-involuntary-laryngeal-from-vagal-nerve-activation", "heartbeat-audible-at-close-proximity-elevated-110-to-180-bpm", "skin-on-skin-contact-friction-sound-varies-with-moisture-level", "bed-frame-mechanical-rhythmic-if-applicable", "fabric-friction-sheets-shifting", "wet-sounds-mucosal-contact-saliva-and-other-fluids"], "absorption_mod": 0.30},
        "smell": {"compounds": ["androstadienone-male-sweat-pheromone-candidate-musk", "estratetraenol-female-pheromone-candidate", "copulin-vaginal-fatty-acid-mixture-detected-subconsciously", "sweat-increased-eccrine-and-apocrine-output-apocrine-is-the-sex-sweat-glands-concentrated-at-armpits-and-groin", "oxytocin-no-smell-itself-but-triggers-olfactory-sensitivity-increase-you-smell-MORE-during-sex", "squalene-skin-oil-increases-with-body-temperature", "pheromone-MHC-complex-immune-compatibility-signaling-subconscious-attraction-or-repulsion", "genital-fluid-chemistry-varies-by-individual-pH-and-microbiome"], "volatility_mod": 2.0},
        "sight": {"clarity_mod": 0.6, "light_filter": "pupil-dilation-from-sympathetic-arousal-increases-light-intake-partner-appears-softer-in-low-light, skin-flush-vasodilation-visible-across-chest-neck-face-the-sex-flush, sweat-glistens-on-skin-catching-available-light, eye-contact-activates-prefrontal-cortex-and-releases-oxytocin-mutual-gaze-is-a-physiological-event", "reflections": True, "color_temp_K": 2700},
        "touch": {"surfaces": "skin-on-skin-thermal-transfer-at-full-body-contact-two-37C-bodies-create-microclimate-of-trapped-heat-approaching-39C-in-contact-zones, erogenous-zones-nerve-density-varies-200-to-1000-times-baseline-depending-on-location, Meissner-corpuscles-respond-to-light-touch-Pacinian-to-pressure-both-amplified-by-arousal-state, hair-follicle-stimulation-produces-piloerection-goosebumps-distinct-from-cold-response, fingertip-on-partner-reads-pulse-temperature-muscle-tension-moisture-level-four-data-channels-per-touch-point, orgasm-produces-rhythmic-involuntary-muscle-contraction-at-0.8-second-intervals-measurable-and-consistent-across-individuals",
                  "air": "room temperature rises measurably — two bodies at peak metabolic output (250-400 watts combined) in an enclosed room raise ambient temperature 1-2°C per hour. Humidity spikes from exhalation and perspiration. CO2 concentration increases. The room's air becomes a shared metabolic product"},
        "taste": {"compounds": ["salt-NaCl-sweat-concentration-increases-with-exertion", "urea-trace-in-sweat-slightly-bitter", "lactic-acid-sweat-sour", "squalene-skin-oil-waxy", "pheromone-compounds-MHC-related-detected-by-vomeronasal-organ-candidate", "genital-fluid-pH-varies-3.8-to-4.5-female-7.2-to-8.0-male-the-difference-is-why-they-taste-different", "oxytocin-heightens-taste-sensitivity-everything-tastes-MORE-during-arousal"],
                  "profile": {"salt": 0.4, "musk": 0.3, "sour": 0.1, "sweet": 0.1},
                  "intensity": 0.8,
                  "note": "the taste of a partner is their immune system rendered in chemistry — MHC-dissimilar partners taste and smell more attractive, MHC-similar partners less so. This is evolution selecting for immune diversity in offspring and it operates entirely below conscious awareness. Sweat salt concentration increases with arousal. Skin oils increase. Oxytocin amplifies taste receptor sensitivity by 15-20%. You literally taste your partner more intensely as arousal increases — this is a feedback loop the body engineered deliberately",
                  "mouthfeel": "salt-warm-slick-intimate"},
        "environment": {"temperature_c": 24, "humidity_pct": 60, "wind_speed_kmh": 0},
    },


    # --- BATCH 4: Abandoned church & sacred decay primitives ---

    "abandoned-decay": {
        "category": "material",
        "sound": {"sources": ["creak-structural-settling", "plaster-fall-distant", "glass-crunch-underfoot", "drip-through-roof", "hinge-rust-groan"], "absorption_mod": 0.15},
        "smell": {"compounds": ["mildew-deep", "wet-plaster-calcium", "wood-rot-cellulose-breakdown", "old-varnish-vanillin", "rust-iron-oxide", "pigeon-guano-ammonia", "damp-mortar-calcium-hydroxide"], "volatility_mod": 1.1},
        "sight": {"clarity_mod": 0.6, "light_filter": "broken-geometry-light-through-gaps-asymmetric", "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "plaster-crumbling-reveals-lath, wood-soft-where-rot-has-entered, glass-shards-in-debris, rust-flakes-on-ironwork, paint-peeling-in-sheets",
                  "air": "still, damp, the air of a space that hasn't been ventilated in years",
                  "thermal_conductivity_dominant": None},
        "taste": {"compounds": ["calcium-hydroxide-plaster", "iron-oxide-rust", "mold-spore-mycotoxin", "lead-paint-sweet-if-pre-1978", "calcium-carbonate-mortar"],
                  "profile": {"chalky": 0.5, "bitter": 0.4, "metallic": 0.3, "sweet": 0.1},
                  "intensity": 0.4,
                  "note": "the taste of abandonment is alkaline chalk and iron — plaster dust is pH 12, rust dissolves in saliva releasing Fe3+, and pre-1978 lead paint is genuinely sweet (lead acetate), which is why children ate it",
                  "mouthfeel": "gritty-chalky-metallic"},
        "environment": {"humidity_pct": 65, "wind_speed_kmh": 0},
    },

    "church-sacred": {
        "category": "spatial",
        "materials": ["stone-limestone", "wood-old", "glass", "cast-iron", "wax"],
        "sound": {"sources": ["echo-long-reverberant", "footstep-on-stone-sharp", "wood-pew-creak-hygroscopic", "pigeon-coo-rafters", "wind-through-broken-window", "drip-if-damaged-roof"],
                  "absorption_mod": 0.02, "rt60_s": 5.0},
        "smell": {"compounds": ["incense-residue-boswellic-acid-in-stone", "beeswax-candle-old", "limestone-calcium-carbonate", "wood-tannin-aged", "dust-centuries-deep", "damp-stone-mineral"],
                  "volatility_mod": 0.9},
        "sight": {"clarity_mod": 0.5, "light_filter": "stained-glass-spectral-filtering-ruby-cobalt-amber-fragments",
                  "reflections": False, "color_temp_K": 4500},
        "touch": {"surfaces": "limestone-floor-worn-smooth-by-centuries-of-feet, pew-wood-polished-by-hands-rough-where-neglected, iron-candelabra-cold-massive, stone-pillar-cold-and-stays-cold",
                  "air": "still, cool, stratified — warm air trapped at vault height, cold air pooled at floor",
                  "thermal_conductivity_dominant": 2.3},
        "taste": {"compounds": ["calcium-carbonate-limestone", "incense-resin-absorbed", "beeswax-propolis-trace", "tannin-oak-pew", "iron-candelabra-oxide"],
                  "profile": {"chalky": 0.5, "bitter": 0.3, "astringent": 0.3, "sweet": 0.1},
                  "intensity": 0.3,
                  "note": "a church tastes like its own skeleton — limestone chalk with centuries of incense resin absorbed into the pores, beeswax sweetness from a thousand candles, and oak tannin from the pews that dries the tongue like communion wine",
                  "mouthfeel": "chalky-waxy-tannic"},
        "environment": {"indoor": True, "temperature_c": 14, "humidity_pct": 60, "wind_speed_kmh": 0},
    },

    "wildlife-reclamation": {
        "category": "activity",
        "sound": {"sources": ["pigeon-coo-flutter-roost", "claw-on-wood-rafters", "bat-squeak-ultrasonic-edge", "insect-in-wood-boring", "bird-wing-echo-in-vault", "rodent-scurry-in-wall", "owl-if-night"],
                  "absorption_mod": 0.05},
        "smell": {"compounds": ["guano-ammonia-uric-acid", "feather-dust-keratin", "nest-material-straw-moss", "rodent-musk", "ivy-chlorophyll-through-mortar", "moss-on-stone-damp"],
                  "volatility_mod": 1.2},
        "sight": {"clarity_mod": 0.7, "light_filter": "ivy-filtered-green-through-windows-bird-movement-in-rafters",
                  "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "guano-crusted-surfaces-chalky, ivy-on-wall-damp-alive-tendrils, moss-on-stone-spongy-cool, cobweb-face-invisible-until-contact, feather-on-ground-soft",
                  "air": "organic warmth from roosting birds above, cooler at floor, slight updraft from body heat column"},
        "taste": {"compounds": ["ammonia-uric-acid-airborne", "feather-keratin-dust", "chlorophyll-ivy-sap", "moss-usnic-acid"],
                  "profile": {"bitter": 0.5, "chalky": 0.3, "umami": 0.1},
                  "intensity": 0.3,
                  "note": "the taste of reclamation is ammonia and green — guano volatilizes uric acid which the tongue reads as acrid-bitter, ivy sap is chlorophyll-bitter, moss adds usnic acid, the building tastes alive again but not for humans",
                  "mouthfeel": "acrid-dusty-vegetal"},
        "environment": {"humidity_pct": 60},
    },

    "dusk-light": {
        "category": "atmosphere",
        "sound": {"sources": ["settling-quiet-world-exhaling", "last-birdsong-territorial", "wind-dying-to-nothing", "first-insects-evening"],
                  "absorption_mod": 0.05},
        "smell": {"compounds": ["cooling-stone-releasing-day-heat", "dew-forming-first-molecules", "night-blooming-beginning", "grass-exhaling-oxygen-shift"],
                  "volatility_mod": 1.0},
        "sight": {"clarity_mod": 0.6,
                  "light_filter": "color-temp-dropping-5000K-to-2500K-raking-angle-long-shadows-warm-to-cool-transition",
                  "reflections": True, "color_temp_K": 2800},
        "touch": {"surfaces": "stone-still-warm-from-day-cooling-perceptibly, metal-cooling-fastest, wood-holds-warmth-longest",
                  "air": "temperature dropping 1-2C per 15 minutes, the body notices the gradient, goosebumps begin on exposed arms"},
        "environment": {"time_of_day": "dusk", "temperature_c": 16},
    },

    "churchyard-exterior": {
        "category": "spatial",
        "materials": ["earth-soil", "stone-limestone", "moss-lichen", "cast-iron"],
        "sound": {"sources": ["wind-in-grass-long", "birdsong-open", "gate-iron-creak", "gravel-path-crunch", "tree-branch-overhead"],
                  "absorption_mod": 0.1, "rt60_s": 0.1},
        "smell": {"compounds": ["grass-chlorophyll-fresh", "geosmin-soil-actinobacteria", "moss-damp-on-headstone", "wildflower-pollen", "iron-gate-wet", "leaf-mold-decomposing"],
                  "volatility_mod": 1.1},
        "sight": {"clarity_mod": 0.9, "light_filter": "open-sky-filtered-by-trees-headstones-casting-shadows",
                  "reflections": False, "color_temp_K": 5500},
        "touch": {"surfaces": "grass-wet-with-dew-or-rain, headstone-limestone-cold-with-lichen-texture, iron-railing-cold-rough-with-age, gravel-underfoot-sharp, tree-bark-rough",
                  "air": "open breeze carrying living scents, contrast with enclosed interior"},
        "taste": {"compounds": ["geosmin-petrichor", "grass-sap-hexenal", "pollen-protein", "iron-gate-Fe2+"],
                  "profile": {"umami": 0.3, "bitter": 0.2, "sweet": 0.1, "metallic": 0.2},
                  "intensity": 0.4,
                  "note": "the churchyard tastes alive — geosmin is the taste of living soil, grass sap releases cis-3-hexenal (the green smell IS a taste at close range), pollen is protein-sweet, the iron gate adds Fe2+ metallic tang where you grip it",
                  "mouthfeel": "fresh-green-mineral"},
        "environment": {"indoor": False, "humidity_pct": 65, "wind_speed_kmh": 6},
    },

}

# ═══════════════════════════════════════════════════════════════
# CROSS-PRIMITIVE INTERACTION RULES
# When certain primitives co-occur, physics interactions modify the result
# ═══════════════════════════════════════════════════════════════

PRIMITIVE_INTERACTIONS = {
    # (primitive_a, primitive_b) → modifications
    ("water", "underground-tunnel"): {
        "humidity_add": 15,
        "sound_add": ["drip-amplified-by-tunnel", "water-echo-directional"],
        "smell_add": ["mineral-dissolution", "wet-concrete-intensified"],
        "touch_note": "water sounds give the only spatial orientation in darkness — each drip locates a surface",
    },
    ("steel-metal", "night"): {
        "touch_note": "high conductivity + low temperature = aggressive heat drain — metal feels painful to grip",
    },
    ("silence", "enclosed-large"): {
        "sound_add": ["building-infrasound-1-5hz-felt-not-heard", "own-heartbeat-audible"],
        "touch_note": "in the absence of sound, body becomes aware of air pressure, clothing weight, floor vibration",
    },
    ("fire", "enclosed-small"): {
        "smell_add": ["smoke-concentration-rapid", "oxygen-depletion-notice"],
        "touch_note": "radiant heat inescapable in small space — no cool-side refuge, sweat starts immediately",
        "temperature_add": 10,
    },
    ("fog", "night"): {
        "sight_clarity_override": 0.05,
        "sound_note": "sound becomes directionless — fog scatters, darkness removes visual confirmation",
        "touch_note": "spatial awareness collapses to arm's length — moisture + darkness = total sensory compression",
    },
    ("rain", "steel-metal"): {
        "sound_add": ["rain-on-metal-sharp-pinging", "resonance-drumming"],
    },
    ("rain", "concrete"): {
        "smell_add": ["petrichor-amplified", "wet-calcium-hydroxide"],
        "sound_add": ["rain-on-concrete-hiss-white-noise"],
    },
    ("no-light", "cave"): {
        "smell_mod": 1.5,
        "sound_note": "hearing becomes primary navigation — every drip is a sonar ping mapping the space",
        "touch_note": "hands become eyes — every surface texture is information about where you are",
    },
    ("machinery-dead", "silence"): {
        "sound_add": ["absence-of-hum-conspicuous", "the-frequency-gap-where-machinery-should-be"],
        "smell_note": "residual oil and grease smell stronger in the silence — sensory compensation",
    },
    ("water-surface", "no-light"): {
        "sound_note": "water sounds become spatial map — ripple-echo gives room dimensions",
        "touch_note": "unseen water edge is a cliff — each step tests for surface",
    },
    ("underground-tunnel", "machinery-dead"): {
        "smell_add": ["stale-oil-cold", "rubber-degrading", "electrical-residue"],
        "sound_add": ["silence-industrial-wrong", "distant-pump-maybe"],
        "touch_note": "rails still vibrate faintly from distant trains — or is that imagination?",
    },
    ("decay-organic", "enclosed-small"): {
        "smell_mod": 2.0,
        "touch_note": "nowhere to retreat from the smell — it saturates, clings to clothing, tastes in the back of the throat",
    },
    ("steam", "tile-ceramic"): {
        "touch_note": "tile becomes slick-dangerous, condensation beads on every surface, grout channels become tiny rivers",
        "sight_note": "tile surfaces fog — reflection becomes diffuse ghost of self",
    },
    ("metal-enclosed", "underwater"): {
        "sound_add": ["hull-pressure-groan", "sonar-ping-maybe", "ballast-gurgle"],
        "touch_note": "hull cold from ocean outside, condensation drips from ceiling, every surface sweats",
        "humidity_add": 20,
        "temperature_add": -5,
    },
    ("metal-enclosed", "silence"): {
        "sound_add": ["tick-of-cooling-metal", "pressure-equalization-creak"],
        "touch_note": "without machinery vibration, the hull feels dead — metal should hum and it doesn't",
    },
    ("desert-open", "midday-harsh"): {
        "temperature_add": 10,
        "touch_note": "sand surface temperature exceeds air by 20°C+ — ground-level radiation creates a heat wall below the knees",
    },
    ("mountain-exposed", "wind"): {
        "temperature_add": -8,
        "touch_note": "wind chill at altitude — exposed skin feels 15-20°C colder than thermometer reads, frostbite risk on extremities",
    },
    ("ice-frost", "no-light"): {
        "touch_note": "invisible ice — each step tests for grip, hands encounter unexpected cold surfaces, spatial model fails",
        "sound_note": "ice cracks are amplified in darkness — impossible to tell if the crack is underfoot or across the room",
    },
    ("electrical-storm", "elevated-open"): {
        "touch_note": "hair stands on end from static charge — the body becomes an antenna, metal objects spark, shelter is survival",
        "sound_add": ["thunder-deafening-no-delay", "ozone-crackle-close"],
    },
    ("water-flowing", "cave"): {
        "sound_add": ["rushing-amplified-by-stone", "echo-water-directional"],
        "smell_add": ["wet-mineral-intensified", "spray-ozone"],
        "humidity_add": 15,
    },
    ("sand", "wind"): {
        "touch_note": "sand becomes abrasive projectile — exposed skin stings, eyes forced shut, breathing requires covering mouth",
        "sight_note": "visibility drops to meters in sandstorm, horizon disappears, navigation by feel",
    },
    ("leather", "wood-old"): {
        "smell_add": ["tannin-wood-harmony", "age-patina-combined"],
        "touch_note": "both materials warm, both carry age in texture — the hand moves between them without thermal shock",
    },
    ("neon-lit", "rain"): {
        "sight_note": "every wet surface becomes a neon mirror — the city doubles, inverted in puddles and slick asphalt",
        "sound_add": ["rain-on-sign-housing-tick"],
    },
    ("paper-books", "silence"): {
        "sound_note": "paper absorbs sound — a room of books is an accidental anechoic chamber, noise floor drops 10-15 dBA",
        "smell_add": ["vanillin-concentration-with-stillness"],
    },
    ("marble", "candlelit"): {
        "sight_note": "candlelight turns marble translucent at thin edges — veins glow from within, surfaces become warm gold instead of cold white",
        "touch_note": "marble's cold intensified by candle warmth contrast — hand moves between fire-warm air and ice-cold stone",
    },
    ("silk-satin", "candlelit"): {
        "sight_note": "silk catches candlelight and redistributes it — fabric glows, color shifts with every movement, liquid shimmer",
    },
    ("oil-grease", "steel-metal"): {
        "smell_add": ["machine-shop-complex", "hot-metal-oil-reaction"],
        "touch_note": "oil on steel eliminates friction but amplifies cold — the hand slides and freezes simultaneously",
    },
    ("ash-charite", "rain"): {
        "smell_add": ["wet-ash-lye-potassium", "carbon-mud"],
        "touch_note": "rain turns ash to caustic paste — pH rises, skin burns slightly, everything becomes grey slurry",
    },
    ("bamboo", "wind"): {
        "sound_add": ["hollow-percussion-clatter", "leaf-rush-dense", "flute-whistle-through-culms"],
        "touch_note": "bamboo grove in wind — the ground vibrates through root networks, hollow stems amplify every gust",
    },
    ("salt", "underground-tunnel"): {
        "sight_note": "salt walls crystalline — artificial light refracts through crystal faces, walls sparkle and shift color",
        "smell_add": ["brine-ancient-ocean-memory"],
        "touch_note": "salt walls smooth and dry, hygroscopic — they pull moisture from your skin, lips crack, hands desiccate",
    },
    ("granite", "rain"): {
        "smell_add": ["petrichor-granite-distinctive"],
        "touch_note": "wet granite becomes treacherous — microscopically rough surface fills with water, friction coefficient halves",
    },
    ("concrete-wet", "underground-tunnel"): {
        "humidity_add": 10,
        "smell_add": ["calcium-hydroxide-amplified", "mineral-wet-intensified"],
        "touch_note": "every surface drips or weeps — the tunnel is saturated, no dry surface exists to rest a hand on",
    },
    ("bone-shell", "no-light"): {
        "touch_note": "bone in the dark — smooth, warm-feeling, disturbingly comfortable, the hand knows what it's touching before the mind admits it",
    },
    ("asphalt", "midday-harsh"): {
        "temperature_add": 15,
        "smell_add": ["bitumen-melting-volatile", "tire-rubber-hot"],
        "touch_note": "asphalt surface exceeds 60°C — shoes stick slightly, bare feet burn in seconds, heat radiates upward into shins",
    },
    # ─── Organic interior interactions ────────────────────────
    ("organic-interior", "silence"): {
        "sound_add": ["heartbeat-becomes-dominant", "peristalsis-wave", "blood-flow-arterial-whoosh"],
        "sound_note": "Without external sound, the creature's biology becomes the entire acoustic environment — heartbeat is a 1-2 Hz infrasound you feel in your chest before you hear it",
    },
    ("organic-interior", "night"): {
        "sight_clarity_override": 0.05,
        "sight_note": "Bioluminescence provides the only orientation — faint red-pink glow from capillary-rich tissue, like holding a flashlight behind your hand",
    },
    ("organic-interior", "fairground-mechanical"): {
        "smell_add": ["cotton-candy-mixed-with-bile", "rust-paint-dissolved-in-acid", "grease-and-mucus"],
        "sound_add": ["calliope-muffled-through-tissue", "chain-rattle-dampened"],
        "touch_note": "carnival surfaces half-dissolved — painted metal softened by digestive enzymes, vinyl peeling, everything coated in warm mucus",
        "sight_note": "primary colors of carnival paint bleeding into organic red — faded clown face dissolving into stomach wall",
    },
    # ─── Fairground interactions ──────────────────────────────
    ("fairground-mechanical", "silence"): {
        "sound_add": ["ride-creak-wind-only", "chain-sway-empty", "ticket-booth-shutter-bang"],
        "smell_add": ["rust-dominant-over-sugar", "oil-congealed", "canvas-mildew"],
        "sound_note": "The silence of a carnival is wrong — these machines were built to never be quiet. Every wind-creak is a mechanical ghost",
    },
    ("fairground-mechanical", "night"): {
        "sight_note": "Unlit carnival at night — painted faces in moonlight become threatening, the geometry of rides against sky is skeletal",
        "smell_add": ["dew-on-rust", "night-amplified-grease"],
    },
    ("fairground-mechanical", "rust-corroded"): {
        "smell_add": ["iron-oxide-on-painted-steel", "structural-decay-metal"],
        "touch_note": "paint flakes reveal rust layers beneath — each chip is a geological stratum of the ride's age, the texture shifts from smooth to rough to sharp",
    },


    ("volcanic", "night"): {
        "sight_note": "lava glow becomes the only light source, red-orange underlight on sulfur clouds",
        "sound_add": ["lava-bubble-pop"],
        "smell_add": ["sulfur-concentrated-night-cold"],
        "notes": "At night volcanic heat is visible as glow, sulfur settles in cold air"
    },
    ("volcanic", "rain"): {
        "humidity_add": 20,
        "sound_add": ["rain-sizzle-on-hot-rock"],
        "smell_add": ["steam-sulfur-mix"],
        "notes": "Rain on hot volcanic rock creates instant steam carrying concentrated sulfur"
    },
    ("space-station", "solar-flare"): {
        "temperature_add": 6,
        "sound_add": ["hull-expansion-tick", "geiger-rapid"],
        "smell_add": ["heated-plastic-accelerated"],
        "notes": "Solar flare heats hull exterior, radiation increases ozone production inside"
    },
    ("seafood-fish", "morning"): {
        "smell_add": ["first-catch-fresh", "ice-new"],
        "notes": "Dawn fish markets have the freshest catch, trimethylamine levels lowest, ice just laid"
    },
    ("tropical", "rain"): {
        "humidity_add": 5,
        "smell_add": ["petrichor-intense", "mushroom-spore-release"],
        "sound_add": ["rain-on-broadleaf-thunderous"],
        "notes": "Tropical rain on broad leaves is deafening, petrichor is instant and overwhelming"
    },
    ("tropical", "night"): {
        "sound_add": ["frog-chorus-deafening", "bat-click"],
        "smell_add": ["night-blooming-jasmine", "fruit-bat-musk"],
        "notes": "Tropical nights are louder than days, nocturnal species take over the soundscape"
    },
    ("baking-kitchen", "christmas-holiday"): {
        "smell_add": ["gingerbread", "eggnog-nutmeg", "cranberry-tart"],
        "notes": "Christmas baking combines Maillard reaction with holiday spice profile"
    },
    ("rust-corroded", "nautical"): {
        "smell_add": ["rust-salt-accelerated"],
        "touch_note": "salt accelerates oxidation, rust is flaky and sharp-edged, tetanus-orange",
        "notes": "Maritime rust is aggressive, salt spray accelerates corrosion 5-10x faster than inland"
    },
    ("sterile-medical", "night"): {
        "sound_add": ["distant-code-alarm", "elevator-ding-echoing"],
        "smell_add": ["floor-wax-night-shift"],
        "notes": "Hospitals at night are quieter but sounds carry further in empty corridors"
    },

    ("swamp-bayou", "night"): {
        "sound_add": ["alligator-eye-shine", "owl-call", "splash-unseen"],
        "smell_add": ["night-blooming-water-lily"],
        "notes": "Swamp at night: every sound is amplified because you cannot see the source"
    },
    ("swamp-bayou", "tropical"): {
        "humidity_add": 5,
        "temperature_add": 3,
        "sound_add": ["howler-monkey", "parrot-screech"],
        "notes": "Tropical swamp is the most biodiverse soundscape on earth"
    },
    ("combat-zone", "night"): {
        "sight_note": "tracer rounds draw lines across darkness, muzzle flash is the only illumination",
        "sound_add": ["night-vision-whine", "whispered-radio"],
        "notes": "Night combat: sound becomes primary sense, every noise is threat assessment"
    },
    ("tornado-extreme", "night"): {
        "sight_note": "you cannot see it, you can only hear it, lightning flashes reveal the funnel for fractions of a second",
        "notes": "Night tornadoes are more lethal because you cannot see them coming"
    },
    ("deep-ocean", "silence"): {
        "sound_add": ["own-heartbeat-audible", "blood-rushing-ears"],
        "notes": "In the deep ocean silence, your own body becomes the loudest thing"
    },
    ("beehive-interior", "silence"): {
        "notes": "There is no silence inside a beehive. The buzz IS the silence. It never stops."
    },
    ("smoke-lounge", "night"): {
        "smell_add": ["opium-concentrated-night"],
        "notes": "Smoke lounges at night have hours of accumulated smoke layered in the air"
    },
    # ─── Combat Drill interactions ────────────────────────
    ("silver", "manipulation-presence"): {
        "interaction": "sword-warns",
        "description": "The BLADE heats — not the grip. Silver's thermal conductivity (429 W/mK) makes it the fastest-responding metal to any heat source. When manipulation-presence is active, the blade's temperature rises from ambient to 600°C — cherry-red glow visible even in total darkness. The leather-wrapped grip stays cool (leather thermal conductivity: 0.14 W/mK, 3000x less than silver). The blade becomes a torch in the dark. At full intensity it hums — thermal expansion of the metal creating a faint, rising tone. The air around the blade shimmers with heat distortion. Pine resin on nearby branches melts and fills the air with terpene. The sword doesn't just warn you. It lights the forest. It shows you exactly where the danger is by how brightly it burns.",
        "touch_override": "grip-cool-leather-insulated-blade-radiates-heat-at-distance",
        "thermal_shift": "blade +600C, grip unchanged",
        "sight_note": "cherry-red to white-hot glow proportional to manipulation intensity — visible light in total darkness",
    },
    ("feather-plumage", "silence"): {
        "interaction": "owl-silent-flight",
        "description": "Owl feathers have serrated leading edges and velvet-soft trailing edges that break turbulence into micro-vortices below the threshold of mammalian hearing. A barn owl in flight produces less than 2 dB at 2kHz. You hear NOTHING. The silence isn't absence — it's engineering.",
        "sound_override": "absolute-silence-in-motion",
        "touch_note": "displaced air from wingbeat is undetectable below 3m distance — no wind, no pressure change, no warning",
    },
    ("feather-plumage", "moonless-dark"): {
        "interaction": "invisible-predator",
        "description": "Great horned owl plumage absorbs 95% of incident light in the 380-700nm range. In moonless conditions with scotopic vision only, the owl is functionally invisible at any distance beyond 2m. You cannot see it. It can see you — owl retinas have 5x the rod density of hawks.",
        "sight_override": "target-invisible-predator-has-full-vision",
    },
    ("silver", "ice-frost"): {
        "interaction": "silver-cold-danger",
        "description": "Silver's thermal conductivity (429 W/mK) at sub-zero temps drains hand heat at 8x the rate of steel. Bare skin on frozen silver loses enough heat in 3 seconds to trigger pain receptors. In 10 seconds, skin begins to adhere via ice-crystal formation. Grip the sword with gloves or feathered hands — never bare skin below 0°C.",
        "touch_override": "dangerously-cold-grip-requires-insulation",
    },
    ("moonless-dark", "forest"): {
        "interaction": "canopy-total-darkness",
        "description": "Forest canopy blocks 95-99% of ambient light. On a moonless night, sub-canopy illumination drops below 0.0001 lux — below the threshold of even dark-adapted scotopic vision. The forest floor is not dark. It is BLIND. Only proprioception and touch navigate. Sound becomes primary sense. Every footstep is information.",
        "sight_override": "functionally-blind-below-canopy",
        "sound_note": "acoustic navigation dominant — echo-location by footstep reflection off trunks",
    },
    ("pine-resin", "ice-frost"): {
        "interaction": "frozen-resin",
        "description": "Pine resin below 0°C transitions from viscous liquid to brittle glass. The terpene compounds (alpha-pinene, beta-pinene) stop volatilizing — smell drops to near zero. But crack the frozen resin and the fresh surface releases a burst of concentrated terpene. A broken branch in a frozen pine forest EXPLODES with smell. Every snap is an olfactory flare.",
        "smell_override": "silent-until-broken-then-overwhelming",
    },
    ("breath-fog", "moonless-dark"): {
        "interaction": "breath-betrays-position",
        "description": "Exhaled breath at 37°C in 2°C air creates a visible condensation plume that persists for 2-4 seconds. In total darkness, this is invisible to the breather. But to any creature with superior night vision (owl: 5x rod density), the thermal plume is a beacon. Every exhale broadcasts your exact position. The owl doesn't need to hear you. It watches you breathe.",
        "sight_note": "invisible to self, visible to predator — asymmetric information",
    },
    ("forge-metalwork", "water"): {
        "interaction": "quench-thermal-shock",
        "description": "Hot steel (800-1000°C) plunged into water creates instant steam explosion — Leidenfrost effect at first (vapor layer insulates briefly), then nucleate boiling as steel drops below 300°C. The sound is a violent hiss-to-roar. Steam cloud carries iron oxide particles. Temperature drops 800°C in seconds. The metal screams.",
        "sound_override": "violent-hiss-steam-explosion",
        "smell_add": ["iron-oxide-steam", "mineral-water-superheated"],
    },
    ("ancient-tomb", "silence"): {
        "interaction": "sealed-millennia",
        "description": "Air sealed for thousands of years has no external sound source — no wind, no life, no machinery. The silence isn't empty, it's preserved. The first sound in this space in 3000 years is your breathing. Your footsteps are archaeological events. Every sound you make is the loudest thing to happen here since it was sealed.",
        "sound_override": "you-are-the-first-sound-in-millennia",
    },
    ("submarine-interior", "deep-ocean"): {
        "interaction": "hull-under-pressure",
        "description": "At 200m depth, hull experiences 20 atmospheres (294 PSI) of pressure. Steel creaks as it compresses microscopically. The sound is the submarine's skeleton adjusting. At crush depth, these creaks become groans. Crew learn to distinguish normal settling from danger. The hull is a pressure instrument — you read depth by sound.",
        "sound_override": "hull-creak-proportional-to-depth",
        "touch_note": "air pressure maintained at 1 atm inside — the body feels normal but the hull around you is bearing 20 atmospheres, the difference is the submarine's entire purpose",
    },
    ("aircraft-cabin", "elevated-open"): {
        "interaction": "stratosphere-window",
        "description": "Window at cruising altitude: outer pane at -55°C (ambient at 35000ft), inner pane insulated but still radiates cold. Place hand on window: you feel the stratosphere. The sky outside is darker blue trending toward black at the zenith. Contrails from other aircraft persist for minutes — ice crystals in -55°C air don't sublimate quickly.",
        "sight_note": "sky darkens toward space at altitude — blue shifts to deep indigo at zenith",
    },
    ("wine-cellar", "wood-old"): {
        "interaction": "barrel-aging-chemistry",
        "description": "Oak barrels breathe — 2-5% of wine evaporates per year through wood pores (the 'angel's share'). The cellar air is saturated with ethanol and fruit esters. Over years, black mold (Baudoinia compniacensis) grows on cellar walls and ceilings, feeding on ethanol vapor. The black stains are alive — they are the visible signature of decades of evaporating wine.",
        "smell_override": "ethanol-fruit-ester-saturated-air-with-living-mold",
    },
    ("live-music-venue", "crowd"): {
        "interaction": "crowd-thermodynamics",
        "description": "Dense crowd (4-5 people per square meter) generates 400-500W per square meter of body heat. Air temperature rises 5-10°C above ambient within 30 minutes. Humidity spikes from breath and sweat — condensation forms on cold surfaces (windows, beer glasses). The crowd moves as a fluid — pressure waves from the stage propagate through bodies. You don't choose to move; the crowd moves you.",
        "touch_override": "crowd-pressure-wave-movement-involuntary",
        "temperature_add": 8,
        "humidity_add": 20,
    },
    # --- Batch 4: Abandoned church interactions ---
    ("abandoned-decay", "church-sacred"): {
        "smell_add": ["incense-faded-mixed-with-mildew", "varnish-decomposing-vanillin-sweet", "stone-damp-releasing-centuries-of-absorbed-smoke"],
        "sound_add": ["plaster-fall-echo-in-nave-4-second-reverb", "glass-crunch-amplified-by-stone-acoustics"],
        "touch_note": "every surface tells two stories — the smooth wear of devotion underneath the rough grain of neglect. Run a hand along a pew: polished where thousands of hands rested, splintered where rain through the broken roof found the wood",
        "sight_note": "stained glass fragments throw incomplete color patches — geometry designed for whole windows now fractured into abstract splashes, the remaining ruby piece throws a wound-red shape on limestone",
    },
    ("abandoned-decay", "silence"): {
        "sound_add": ["structural-settling-creak-amplified", "plaster-tick-before-fall", "rust-flake-dropping-to-stone"],
        "sound_note": "abandoned silence is different from empty silence — it is the silence of things still happening without humans: gravity pulling plaster loose, rust advancing, wood fibers surrendering to moisture",
    },
    ("church-sacred", "dusk-light"): {
        "sight_note": "dusk is when stained glass does its last work — sun below the treeline means scattered light enters at raking angles, ruby and cobalt fragments produce color patches that climb the east wall as the sun drops, in ten minutes they will be gone, temporary physics that repeats daily for no one",
        "touch_note": "limestone floor still holds the day warmth at dusk but is cooling perceptibly — stand still and feel the thermal gradient as the building exhales the heat it stored",
        "smell_add": ["cooling-stone-releasing-absorbed-warmth-and-scent", "evening-dew-beginning-at-broken-windows"],
    },
    ("church-sacred", "wildlife-reclamation"): {
        "sound_add": ["pigeon-coo-in-5-second-reverb", "wing-flutter-echo-multiplied-by-vault", "claw-on-oak-beam"],
        "smell_add": ["guano-on-limestone-ammonia-chalk-reaction", "nest-straw-in-rafters"],
        "sound_note": "bird sounds in a church are transformed by the architecture — a pigeon coo designed for open sky gets a 5-second reverb tail in limestone, the building makes every bird sound sacred whether or not the bird intends it",
    },
    ("wildlife-reclamation", "abandoned-decay"): {
        "smell_add": ["ivy-mortar-dissolution-chemistry", "moss-accelerating-stone-weathering"],
        "touch_note": "ivy tendrils have entered the mortar joints — pull one and the wall moves. The building structural integrity is now partially biological. Moss on the floor makes stone treacherous where it was once sure",
        "sight_note": "green invades grey — ivy through windows frames them in living chlorophyll, moss on floor creates patches of soft color in the stone monotone, nature is redecorating",
    },
    ("churchyard-exterior", "church-sacred"): {
        "sound_note": "the transition at the doorway is a hard acoustic edge — 0.1s reverb outside, 5s reverb inside, the same footstep lives ten times longer when it crosses the threshold",
        "smell_note": "crossing the threshold: geosmin and chlorophyll cut off, replaced by limestone and incense residue — two olfactory worlds separated by eight inches of stone wall",
        "touch_note": "the breeze that carries living scent from the churchyard pours through broken windows into the dead air of the nave — two temperatures, two humidities, two worlds meeting at every gap in the envelope",
    },
    ("churchyard-exterior", "dusk-light"): {
        "sight_note": "headstones cast shadows ten times their height at dusk — raking light reveals every chip, every lichen pattern, every weathered letter in sharp relief that will be invisible in twenty minutes",
        "smell_add": ["evening-dew-on-grass-geosmin-release", "cooling-iron-gate-metallic"],
    },
    ("dusk-light", "abandoned-decay"): {
        "sight_note": "dusk light enters through gaps that were never meant to be windows — collapsed roof sections, missing doors, broken panes — creating light geometry the original architect never designed, accidental beauty from structural failure",
        "touch_note": "the building cools faster than it should — gaps in the envelope let heat escape, the thermal mass that once held warmth for evening services now drains into the open air",
    },
    ("wildlife-reclamation", "dusk-light"): {
        "sound_add": ["roosting-calls-evening", "bat-emergence-from-belfry", "owl-first-call"],
        "sound_note": "dusk is shift change — diurnal birds settle into roosts with territorial calls, bats emerge from gaps in the roof, the first owl tests the acoustics. The building has a schedule that has nothing to do with services",
    },

    # --- Batch 5-8: Material, Activity, Biome, Sci-fi interactions ---

    # Materials × Atmosphere
    ("leather", "rain"): {
        "smell_add": ["wet-leather-petrichor-tannin-release-intensified", "dye-bleeding-chromium-salt-activated-by-moisture"],
        "touch_note": "wet leather darkens, softens immediately, thermal conductivity increases as water fills pores — it feels colder and heavier. The surface goes from warm and dry to cold and slick. Drying leather stiffens and can crack if not conditioned",
        "sight_note": "leather darkens two to three shades when wet — water fills surface pores and changes the refractive index, absorbing more light",
    },
    ("concrete", "rain"): {
        "smell_add": ["petrichor-geosmin-released-from-concrete-pores-the-wet-sidewalk-smell", "calcium-hydroxide-activated-by-moisture-alkaline-sharpens"],
        "touch_note": "wet concrete becomes slick — the rough aggregate surface develops a water film that reduces friction by 60%. The thermal conductivity increases with moisture content, making it feel even colder",
        "sight_note": "concrete darkens dramatically when wet — pores fill with water changing albedo from 0.3 to 0.15. The surface becomes mirror-like in thin water film, reflecting sky and lights",
    },
    ("ice", "night"): {
        "sound_note": "ice expands and contracts with temperature changes after sunset — thermal cracking produces deep resonant booms and high-pitched pings that carry for kilometers across frozen surfaces. A frozen lake at night is one of the most acoustically alien environments on earth",
        "sight_note": "ice under starlight or moonlight refracts and reflects at every crystal boundary — the surface sparkles. Thick ice transmits light from below if there is any source, creating an eerie underlighting effect",
    },
    ("sand", "wind"): {
        "sound_add": ["sand-saltation-hiss-grains-bouncing-at-surface-level", "aeolian-dune-resonance-if-sufficient-volume"],
        "touch_note": "wind-driven sand at 15+ km/h is abrasive on exposed skin — natural sandblasting. Below knee height the concentration is highest. Eyes, nose, and mouth require protection. Sand finds every gap in clothing",
        "smell_note": "wind-driven sand carries mineral dust and any surface compounds into the air — desert after a dust storm smells of ozone from triboelectric charging of particles",
    },
    ("mud", "rain"): {
        "smell_add": ["geosmin-explosion-rain-hitting-dry-soil-releases-actinobacteria-spores-in-massive-burst", "humic-acid-mobilized-by-water-flow"],
        "touch_note": "rain on mud creates a surface slurry — the top centimeter becomes liquid while below remains firm. Footing becomes treacherous as the slip layer has almost zero friction. The mud deepens with continued rain as water table rises",
        "sound_add": ["splatter-rain-impact-on-wet-mud-lower-frequency-than-rain-on-hard-surface"],
    },
    ("copper-brass", "rain"): {
        "smell_add": ["copper-ion-release-accelerated-by-acid-rain-metallic-intensifies"],
        "sight_note": "rain accelerates patina formation — copper in wet conditions develops verdigris (green copper carbonate) visibly faster. Water streaks leave dark oxidation trails on the surface. The green-on-copper color is one of the most recognizable weathering patterns in architecture",
    },
    ("silk-fabric", "rain"): {
        "touch_note": "silk absorbs water rapidly — up to 30% of its weight. Wet silk clings to skin, becomes translucent, and loses all structural rigidity. The smooth frictionless quality disappears. It becomes cold, clingy, and heavy relative to its dry weight",
        "smell_add": ["wet-protein-fiber-faint-animal-smell-sericin-reactivated-by-moisture"],
    },
    ("rubber", "rain"): {
        "touch_note": "wet rubber on smooth surfaces loses grip dramatically — the water film eliminates the stick-slip friction that gives rubber its traction. On textured surfaces the tread channels water and grip is maintained. This is the entire engineering principle behind tire tread design",
        "sound_add": ["tire-on-wet-road-spray-hiss-hydroplane-if-speed-exceeds-tread-capacity"],
    },
    ("plastic", "sun-heat"): {
        "smell_add": ["accelerated-off-gassing-phthalate-and-VOC-release-doubles-per-10C-temperature-increase", "UV-degradation-products-polymer-chain-breaking"],
        "touch_note": "plastic in direct sun can exceed 70°C surface temperature — dark plastics especially. Car dashboards, playground equipment, outdoor furniture all become burn hazards. The material softens slightly, becoming tacky",
    },

    # Materials × Activities
    ("ceramic-porcelain", "cooking"): {
        "sound_add": ["ceramic-bowl-resonance-when-stirred-spoon-on-ceramic-bright-ringing", "plate-stack-clink-distinctive"],
        "touch_note": "ceramic in cooking is a thermal buffer — low conductivity means handles stay cool while the vessel heats. But ceramic retains heat long after the stove is off. A ceramic dish from the oven is dangerous for 20+ minutes",
        "taste_note": "properly glazed ceramic is taste-neutral — this is why it is the preferred material for food service. Unglazed ceramic absorbs flavors and oils permanently. A terracotta pot used for curry will taste like curry forever",
    },
    ("concrete", "combat-gunfire"): {
        "sound_add": ["ricochet-off-concrete-distinctive-whine-plus-fragment-spray", "concrete-spall-from-impact-chips-flying-secondary-projectiles"],
        "touch_note": "concrete in combat is cover and hazard simultaneously — stops most small arms rounds but spalling sends concrete fragments as secondary projectiles. Dust from impacts fills the air. The alkaline concrete dust in eyes and lungs is a casualty producer independent of the gunfire",
        "smell_add": ["concrete-dust-calcium-hydroxide-alkaline-sharp-mixed-with-propellant-gas"],
    },
    ("leather", "combat-gunfire"): {
        "touch_note": "leather provides minimal ballistic protection but significant abrasion resistance — a leather jacket stops road rash not bullets. The psychological comfort of leather in danger is real but the physics protection is limited to fragments and environmental hazards",
    },
    ("sand", "combat-gunfire"): {
        "touch_note": "sand is effective ballistic cover — sand-filled barriers stop rounds that penetrate wood and drywall. Each grain absorbs and redirects energy. The physics is the same as why sandbags work: granular media distributes impact force through friction between particles",
        "smell_add": ["heated-sand-from-nearby-explosion-silica-mineral-dust-mixed-with-propellant"],
    },
    ("rubber", "combat-gunfire"): {
        "sound_note": "bullets through rubber make a distinctive thwack — the elastic material absorbs initial impact then tears. No ricochet. Rubber tires used as barriers produce a dull impact sound very different from concrete or metal ricochets",
    },

    # Materials × Sexual activity
    ("silk-fabric", "sexual-activity"): {
        "touch_note": "silk against aroused skin is amplified — vasodilation and nerve sensitization from arousal make the already-smooth fabric register at higher intensity. Silk sheets on warm skin with elevated moisture from perspiration create a temperature-regulating microclimate that adapts to the activity. There is a reason silk has been associated with intimacy across every culture that encountered it",
        "smell_add": ["body-heat-volatilizing-fabric-dye-and-detergent-scents-from-warmed-silk"],
    },
    ("leather", "sexual-activity"): {
        "smell_add": ["leather-scent-intensified-by-body-heat-tannin-aldehyde-volatilization-accelerated", "sweat-on-leather-salt-oil-mixing-with-leather-conditioning-compounds"],
        "touch_note": "leather against skin is warm-to-warm contact — both surfaces at similar thermal conductivity, minimal heat drain. Leather molds to body contours over time and with heat. The creak of leather under movement is an acoustic signature specific to this combination",
        "sound_add": ["leather-creak-under-body-movement-rhythmic"],
    },

    # Biome interactions
    ("desert", "night"): {
        "touch_note": "desert temperature drops 20-30°C between day and night — the same sand that burned at 60°C at noon is cold at 10°C by midnight. Stone that absorbed all day radiates all night — warm rocks are survival tools. The thermal swing is the most extreme diurnal temperature range of any biome",
        "sight_note": "desert night sky is the clearest on earth — zero humidity, zero light pollution in remote areas, the Milky Way is visible as a structural band not a smudge. Stars appear to have color because atmospheric scintillation is minimized",
        "smell_add": ["cooling-stone-releasing-absorbed-day-heat-and-mineral-scent", "desert-plants-releasing-volatiles-in-cool-night-air-after-conserving-all-day"],
    },
    ("jungle", "rain"): {
        "sound_note": "rain in jungle is a layered event — first the canopy intercepts, producing a roar 30 meters above. Minutes later drips begin reaching ground level through leaf channels. The ground-level sound is delayed and filtered. Two rain sounds separated by altitude and time from the same storm",
        "smell_add": ["petrichor-amplified-by-warm-soil-and-leaf-litter-terpene-release-spiked-by-rain-impact-on-leaves"],
        "touch_note": "jungle rain does not cool — the water is warm, the air stays at 95% humidity, evaporative cooling remains impossible. You get wetter without getting cooler. The rain is just more water in an already saturated system",
    },
    ("swamp-marsh", "night"): {
        "sound_note": "swamp at night is the loudest natural soundscape after jungle — frog chorus peaks, insect density peaks, nocturnal predators (owls, alligators) add subsonic presence. The water surface acts as an acoustic reflector doubling apparent volume",
        "sight_note": "bioluminescent dinoflagellates in brackish water glow when disturbed — any movement through water produces blue-green trails. Foxfire (bioluminescent fungi) on dead wood provides faint persistent light. Fireflies above the water add moving points. The swamp at night is lit by biology not astronomy",
        "smell_add": ["hydrogen-sulfide-concentration-increases-at-night-thermal-inversion-traps-gases-at-surface", "nocturnal-flower-pollinator-attractant-compounds-released"],
    },
    ("desert", "wind"): {
        "sound_add": ["sandstorm-roar-if-strong-wind-wall-of-sound-approaching", "singing-sand-dune-resonance-triggered-by-wind-driven-avalanche"],
        "touch_note": "desert wind above 30 km/h becomes a sandstorm — visibility drops to meters, exposed skin is abraded, breathing requires covering mouth and nose. Sand penetrates everything. Equipment fails. The abrasion is measurable — paint stripped from vehicles in severe storms",
        "smell_add": ["ozone-from-triboelectric-sand-particle-charging-desert-lightning-smell-without-lightning"],
    },
    ("jungle", "night"): {
        "sound_note": "jungle transitions from bird-dominated daytime to insect-and-frog-dominated nighttime — the acoustic handoff happens in a 30-minute window at dusk. Night jungle is LOUDER than day jungle. The species that were silent are now screaming",
        "sight_note": "below canopy at night is absolute darkness — moonlight cannot penetrate 95% canopy cover. The only light sources are bioluminescent: fungi, fireflies, some insects. Eyes never fully adapt because the occasional firefly flash resets dark adaptation",
        "smell_note": "night-blooming flowers release pollinator-attractant compounds — jasmine, frangipani, and the massive rafflesia (which smells of rotting meat to attract flies). The jungle smells different at night because different plants are advertising",
    },

    # Sci-fi interactions
    ("biotics-mass-effect", "combat-gunfire"): {
        "sound_note": "biotic combat layered over gunfire creates acoustic chaos — subsonic biotic hum at 15-30Hz underneath gunshot impulses at 160dB, singularity roar competing with ricochet whine. The frequency spectrum is fully occupied. Communication becomes impossible without helmet comms",
        "smell_add": ["ozone-concentration-hazardous-in-enclosed-spaces-with-sustained-biotic-combat", "propellant-gas-mixed-with-ionized-air-unique-to-mass-effect-universe-combat"],
        "sight_note": "biotic corona (blue-violet 420-450nm) illuminates the battlefield independently of environmental lighting — a biotic in combat is a light source. Barriers flash hexagonal on impact. Singularities bend light visibly. The visual environment is being actively distorted by the combatants",
    },
    ("liara-asari", "biotics-mass-effect"): {
        "smell_add": ["ozone-spike-Liara-passive-field-stronger-than-most-asari-active-field", "cortisol-metabolic-stress-from-high-output-biotic-use"],
        "sound_note": "Liara at full biotic output adds a subsonic voice harmonic below 20Hz — felt in the listener's sternum not heard by ears. Combined with the biotic field hum, her combat presence has an acoustic signature that triggers instinctive mammalian fear response in humans (infrasound at 18-19Hz causes unease, dread, peripheral visual disturbance)",
        "sight_note": "Liara's eyes snap black at full output — the transition is a combat tell that experienced allies recognize as 'get clear, she is about to reshape the local physics.' Her scalp crests luminesce and her full-body corona means she is visible through smoke and dust. She cannot hide while using biotics. She does not try",
        "touch_note": "standing within 2 meters of Liara at full biotic output — skin prickles from ionized air, hair stands from static field, ambient gravity feels wrong. Objects on surfaces near her drift. The air tastes electric. Being near a powerful biotic in combat is a full sensory event even if you are not the target",
    },
    ("liara-asari", "sexual-activity"): {
        "touch_note": "asari skin at 35.5°C is detectably cooler than human 36.5°C — the temperature difference is subtle but perceptible during full-body contact. Her biotic field transmits through skin contact — the partner feels a faint electric quality to every touch that intensifies with her arousal. Crest contact produces biotic feedback if partner has any field sensitivity. Physical intimacy with Liara is overlaid with a biotic sensory channel that non-asari partners have no framework for",
        "smell_add": ["ozone-spike-biotic-field-fluctuating-with-arousal", "asari-pheromone-analogue-subtle-floral-shifting-to-electric"],
        "sound_note": "biotic field hum intensifies with arousal — the subsonic 15-30Hz presence becomes detectable by partner through body contact vibration. Her voice gains the harmonic undertone. If arousal triggers involuntary biotic flare, nearby objects may drift. The meld — if initiated — replaces all external sensory input with shared internal experience",
    },
    ("tali-quarian", "sexual-activity"): {
        "touch_note": "suit removal for intimacy is a medical event as much as an emotional one — immunoboosters and antibiotics taken prophylactically, the preparation itself an act of deliberate vulnerability. Bare quarian skin is hypersensitive — nerve density elevated from generations of suit deprivation. What registers as normal touch to the partner registers as vivid overwhelming input to the quarian. Calibration is required. Communication is essential. The physical asymmetry in sensation intensity is enormous",
        "smell_add": ["dextro-amino-acid-body-chemistry-alien-scent-profile-intensified-by-arousal-and-perspiration"],
        "sound_note": "without the helmet, every vocalization is raw — no harmonic resonance from the suit. Breathing, voice, all sounds are more intimate because they are unprocessed for the first time in this context. The partner hears the real voice. The quarian hears their own real voice. Both are experiencing something new",
    },
    ("tali-quarian", "biotics-mass-effect"): {
        "touch_note": "quarians are not biotic — no eezo nodules. Tali experiences biotic fields purely as external phenomena: static on suit surface, pressure fluctuations detected by suit sensors, ozone reaching her through air filters as chemical data rather than scent. Without the suit, biotic proximity would register on her hypersensitive skin as intense electric prickling — potentially overwhelming given her elevated nerve density",
    },


}

# ═══════════════════════════════════════════════════════════════
# KEYWORD → PRIMITIVE MAPPING
# ═══════════════════════════════════════════════════════════════

_PRIMITIVE_KEYWORDS = {
    # Spatial types
    "underground-tunnel": ["subway", "metro", "tunnel", "underground", "tube", "bunker", "basement", "cellar", "sewer", "mine-shaft", "mine", "catacomb", "catacombs"],
    "enclosed-small": ["closet", "booth", "elevator", "lift", "crawlspace", "attic-small", "shed", "cell", "coffin"],
    "enclosed-large": ["warehouse", "hangar", "gymnasium", "ballroom", "hall", "arena", "terminal", "station-hall"],
    "open-field": ["field", "meadow", "prairie", "plain", "steppe", "clearing", "lawn", "pasture", "savanna"],
    "corridor-narrow": ["corridor", "hallway", "passage", "passageway", "tunnel-narrow", "alleyway"],
    "rooftop": ["rooftop", "roof", "terrace-high", "observation-deck", "balcony-high"],
    "cave": ["cave", "cavern", "grotto", "cenote", "underground-chamber", "mine"],
    "vehicle-interior": ["car", "taxi", "bus", "train-interior", "airplane", "helicopter", "truck-cab", "van"],
    "elevated-open": ["mountain", "cliff", "ridge", "summit", "tower-top", "bridge-high", "overlook", "hilltop", "rooftop", "30th floor", "high rise", "skyscraper", "balcony"],
    "waterside": ["dock", "pier", "wharf", "marina", "harbor", "lakeside", "riverbank", "canal-side", "boardwalk"],
    "metal-enclosed": ["submarine", "aircraft-interior", "tank-interior", "shipping-container", "hull", "bulkhead",
                       "spaceship", "space-station", "capsule", "airlock", "torpedo-room", "engine room", "engine-room",
                       "boiler room", "boiler-room", "ship-interior"],
    "stairwell": ["stairwell", "staircase", "stairs", "fire-stairs", "spiral-staircase", "landing"],
    "basement-cellar": ["basement", "cellar", "wine-cellar", "root-cellar", "crawlspace", "utility-room", "furnace-room"],
    "desert-open": ["desert", "sahara", "dunes", "arid", "wasteland", "dry-lakebed", "mesa", "badlands"],
    "mountain-exposed": ["mountaintop", "alpine", "summit", "ridge-line", "above-treeline", "exposed-peak"],
    "organic-interior": ["inside a whale", "whale-belly", "stomach", "intestine", "gullet", "throat",
                         "inside a creature", "belly of", "swallowed", "digestive", "living-interior",
                         "womb", "inside the beast", "leviathan", "whale"],

    # Materials
    "concrete": ["concrete", "brutalist", "parking-garage", "overpass", "underpass", "garage", "mechanic"],
    "steel-metal": ["steel", "metal", "iron", "girder", "beam", "rail", "track", "grate", "scaffold"],
    "wood-old": ["wooden", "timber", "log-cabin", "barn", "old-house", "floorboard", "paneling", "pub", "tavern"],
    "brick": ["brick", "brownstone", "tenement", "kiln"],
    "glass": ["glass", "greenhouse", "conservatory", "skyscraper-lobby", "window-wall"],
    "tile-ceramic": ["tile", "tiled", "bathroom", "shower", "pool-edge", "hospital", "clinic", "laboratory"],
    "earth-soil": ["dirt", "mud", "soil", "earth", "garden", "burial", "excavation"],
    "stone-limestone": ["stone", "limestone", "marble", "granite", "crypt", "tomb", "mausoleum", "castle", "ruins", "ancient"],
    "rust-corroded": ["rust", "rusted", "corroded", "derelict", "junkyard", "scrapyard", "shipwreck"],
    "moss-lichen": ["mossy", "overgrown", "reclaimed", "vine-covered", "ruins-nature"],
    "fabric-textile": ["curtain", "draped", "tent", "canopy-fabric", "upholstered"],
    "rubber-plastic": ["plastic", "synthetic", "vinyl", "linoleum", "playground"],
    "water-surface": ["puddle", "pool", "flooded", "submerged", "swamp", "marsh", "bog"],
    "copper-brass": ["copper", "brass", "bronze", "patina", "verdigris", "bell", "trumpet"],
    "cast-iron": ["cast-iron", "wrought-iron", "iron-gate", "iron-fence", "manhole", "fire-escape-metal"],
    "wood-fresh": ["sawmill", "lumber-yard", "fresh-cut", "construction-wood", "pine-fresh", "cedar-fresh"],
    "leather": ["leather", "saddle", "harness", "belt", "leather-bound", "tannery", "hide"],
    "paper-books": ["library", "bookshop", "bookstore", "archive", "manuscript", "scriptorium", "reading-room"],
    "sand": ["sandy", "sand-dune", "beach-sand", "sandstone", "quicksand"],
    "ice-frost": ["ice", "icicle", "glacier", "frozen-lake", "ice-cave", "frost", "permafrost", "skating-rink"],
    "paint-chemical": ["freshly-painted", "paint-fumes", "art-studio", "spray-paint", "graffiti"],
    "aluminum": ["aluminum", "aluminium", "aircraft-skin", "soda-can", "foil", "lightweight-metal"],
    "wax": ["wax", "candle-wax", "beeswax", "paraffin", "sealing-wax", "wax-figure", "polish-wax"],
    "bone-shell": ["bone", "bones", "skeleton", "skull", "ivory", "shell", "seashell", "antler", "horn", "ossuary", "catacomb"],
    "rope-fiber": ["rope", "hemp", "jute", "cordage", "rigging", "net", "hammock", "twine", "sisal"],
    "ash-charite": ["ash", "ashes", "cinder", "ember", "aftermath", "burnt", "charred", "burned-out"],
    "oil-grease": ["oily", "greasy", "lubricant", "hydraulic", "petroleum", "slick", "oil-spill"],
    "asphalt": ["asphalt", "tarmac", "blacktop", "road-surface", "parking-lot", "highway"],
    "marble": ["marble", "palazzo", "roman", "greek-temple", "museum-floor", "mausoleum-marble", "marble-hall"],
    "bamboo": ["bamboo", "bamboo-forest", "bamboo-grove", "rattan"],
    "thatch-straw": ["thatch", "thatched", "straw", "hay", "haystack", "hay-barn", "straw-roof"],
    "clay-ceramic-raw": ["clay", "potter", "pottery", "kiln", "terracotta", "adobe", "mud-brick", "earthen"],
    "salt": ["salt-flat", "salt mine", "salt-cave", "brine", "salt-marsh", "halite", "dead-sea", "salt cave"],
    "coal-charcoite": ["coal", "coal-mine", "charcoal", "anthracite", "coal-cellar", "coal-dust"],
    "silk-satin": ["silk", "satin", "velvet", "brocade", "tapestry", "silk-road", "silk-curtain"],
    "granite": ["granite", "granite-counter", "tombstone", "headstone", "mountain-rock", "boulder"],
    "plaster-drywall": ["plaster", "drywall", "stucco", "render", "whitewash", "lath-and-plaster"],
    "vinyl-linoleum": ["linoleum", "vinyl-floor", "hospital-floor", "school-floor", "gymnasium-floor"],
    "stainless-steel": ["stainless", "surgical", "kitchen-counter", "elevator-door", "morgue-table", "autopsy", "morgue", "operating-room"],
    "concrete-wet": ["wet-concrete", "flooded-basement", "rain-soaked-concrete", "puddle-concrete"],

    # Atmospheres
    "rain": ["rain", "rainy", "raining", "downpour", "drizzle", "shower", "storm", "stormy", "thunderstorm"],
    "fog": ["fog", "foggy", "mist", "misty", "haze", "hazy"],
    "snow": ["snow", "snowy", "blizzard", "winter", "frozen", "frost", "icy", "arctic", "tundra"],
    "wind": ["windy", "gusty", "breezy", "gale"],
    "smoke-haze": ["smoky", "smoke-filled", "wildfire", "burning-building", "smog"],
    "dust-heavy": ["dusty", "sandstorm", "desert", "construction-site", "demolition"],
    "steam": ["steamy", "sauna", "bathhouse", "hot-spring", "laundry-room", "boiler-room"],
    "night": ["night", "midnight", "nocturnal", "dark", "after-dark", "late-night", "2am", "3am", "4am",
              "2 am", "3 am", "4 am", "1 am", "1am", "evening"],
    "morning": ["morning", "dawn", "sunrise", "early", "daybreak", "first-light"],
    "midday-harsh": ["noon", "midday", "scorching", "blazing", "heat-wave"],
    "golden-hour": ["sunset", "golden-hour", "dusk-warm", "evening-light"],
    "fluorescent-lit": ["fluorescent", "office", "hospital-lit", "institutional", "school-hallway", "kindergarten", "classroom"],
    "candlelit": ["candlelit", "candle", "candlelight", "lantern", "oil-lamp", "opium den", "victorian", "medieval", "gothic", "dungeon"],
    "no-light": ["pitch-black", "lightless", "blackout", "total-darkness", "blind", "mariana", "abyss", "abyssal"],
    "underwater": ["underwater", "submerged", "diving", "deep-sea", "ocean-floor", "reef", "kelp-forest"],
    "rain-light": ["drizzle", "light-rain", "misting", "sprinkling", "gentle-rain"],
    "breeze": ["breezy", "gentle-wind", "light-wind", "zephyr"],
    "neon-lit": ["neon", "neon-signs", "neon-lit", "vegas", "cyberpunk", "hong-kong-night", "rain-neon"],
    "starlight": ["starlit", "starlight", "starry", "clear-night-sky", "moonless-stars"],
    "firelight": ["firelit", "campfire-light", "torch-lit", "bonfire-glow"],
    "electrical-storm": ["lightning", "thunderstorm", "electrical-storm", "thunder", "lightning-strike"],
    "stagnant": ["stagnant", "airless", "stuffy", "unventilated", "stale-room", "no-ventilation"],

    # Activity / human layers
    "urban": ["city", "urban", "street", "downtown", "metropolis", "sidewalk", "pavement", "alley",
              "tokyo", "new york", "london", "paris", "manhattan", "brooklyn", "shibuya"],
    "forest": ["forest", "woods", "woodland", "trees", "grove", "jungle", "canopy", "trail", "hiking"],
    "ocean": ["ocean", "sea", "beach", "coast", "shore", "surf", "seaside", "tide", "maritime"],
    "crowd": ["crowd", "crowded", "busy", "packed", "market", "bazaar", "festival", "carnival", "concert", "protest"],
    "silence": ["silent", "quiet", "empty", "deserted", "solitary", "alone", "desolate", "forsaken"],
    "machinery-active": ["running-machinery", "power-plant", "generator", "engine-room", "pumping-station"],
    "machinery-dead": ["broken-machinery", "defunct", "decommissioned", "mothballed", "shut-down"],
    "industrial": ["industrial", "factory", "warehouse", "dock", "shipyard", "foundry", "mill", "refinery"],
    "domestic": ["home", "house", "apartment", "kitchen", "bedroom", "living-room", "cozy", "domestic", "nursery", "baby room"],
    "fire": ["fire", "campfire", "bonfire", "fireplace", "flames", "burning", "hearth", "torch", "forge", "furnace", "kiln", "inferno"],
    "cooking": ["cooking", "kitchen-active", "restaurant-kitchen", "bakery", "food-stall", "grill", "barbecue"],
    "decay-organic": ["rotting", "decomposing", "corpse", "morgue", "compost", "sewage"],
    "water-flowing": ["waterfall", "rapids", "rushing-water", "spillway", "dam", "weir", "fountain-running", "aqueduct"],
    "fairground-mechanical": ["carnival", "fairground", "amusement park", "funfair", "boardwalk-rides",
                               "ferris wheel", "carousel", "merry-go-round", "roller coaster",
                               "bumper-cars", "circus", "big-top", "midway", "sideshow"],
    "electrical": ["server-room", "electrical-panel", "transformer", "power-station", "data-center", "data center", "datacenter", "wiring", "circuit-breaker"],
    "water": ["lake", "river", "stream", "pond", "creek", "waterfall", "canal", "fountain"],

    "volcanic": ["volcano", "volcanic", "crater", "lava", "magma", "caldera", "fumarole", "geyser", "hot-spring-volcanic", "sulfur", "vesuvius", "etna", "pompeii"],
    "space-station": ["space station", "space-station", "spacecraft", "spaceship", "iss", "orbital", "zero-gravity", "weightless", "airlock", "capsule-space", "eva", "spacewalk", "deep space", "outer space", "space suit"],
    "sterile-medical": ["operating room", "operating-room", "surgery", "surgical", "sterile", "antiseptic", "icu", "emergency room", "clinic", "dentist", "medical"],
    "seafood-fish": ["fish market", "fish-market", "fishmonger", "seafood", "tsukiji", "fish-stall", "tuna-auction", "catch-of-the-day"],
    "tropical": ["tropical", "jungle", "rainforest", "equatorial", "humid-tropical", "amazon", "borneo", "congo"],
    "baking-kitchen": ["baking", "bakery", "christmas kitchen", "grandmothers kitchen", "grandmother kitchen", "cookie", "cookies", "pastry", "bread-baking"],
    "solar-flare": ["solar flare", "solar-flare", "radiation-event", "solar-storm"],
    "nautical": ["sailing", "sailboat", "ship-deck", "yacht", "schooner", "naval", "maritime-deck", "at sea", "open-sea"],
    "christmas-holiday": ["christmas", "holiday-kitchen", "thanksgiving", "festive"],
    "northern-lights": ["northern lights", "aurora", "aurora-borealis", "aurora-australis"],
    "insect-active": ["insects", "mosquito", "mosquitoes", "bugs", "swarm", "flies", "cicadas"],
    "spice-market": ["spice market", "spice-market", "spice bazaar", "spice-bazaar", "spice-stall", "spice shop"],

    "pub-bar": ["pub", "bar", "tavern", "saloon", "alehouse", "taproom", "brewery-pub", "irish pub", "dive bar", "sports bar"],
    "bathhouse-hammam": ["hammam", "bathhouse", "bath house", "turkish bath", "onsen", "sento", "sauna-room", "steam room", "hot-tub-room"],
    "deep-ocean": ["mariana", "deep sea", "deep-sea", "ocean floor", "ocean-floor", "abyss", "abyssal", "hadal", "deep ocean", "trench"],
    "tornado-extreme": ["tornado", "twister", "cyclone", "funnel cloud", "waterspout"],
    "mars-surface": ["mars", "martian", "red planet"],
    "combat-zone": ["battlefield", "combat", "warzone", "war zone", "frontline", "front line", "trench warfare", "no mans land"],
    "laundromat": ["laundromat", "laundry", "laundrette", "laundry room", "coin laundry", "wash-and-fold"],
    "nursery-infant": ["nursery", "baby room", "baby-room", "newborn", "crib", "nicu", "infant"],
    "mechanic-garage": ["mechanic", "garage", "auto shop", "auto-shop", "body shop", "body-shop", "repair shop", "oil change"],
    "swamp-bayou": ["swamp", "bayou", "marsh", "marshland", "wetland", "everglades", "mangrove", "fen", "moor", "bog"],
    "smoke-lounge": ["opium den", "opium-den", "hookah", "hookah lounge", "smoking room", "smoking-room", "shisha", "cigar lounge", "opium"],
    "beehive-interior": ["beehive", "bee hive", "inside a hive", "hive interior", "apiary"],
    "feather-plumage": ["feather", "plumage", "plume", "quill", "down", "wing", "molt", "preen", "bird", "avian", "raptor", "owl", "hawk", "eagle", "falcon"],
    "silver": ["silver", "argentum", "ag", "silver sword", "silver blade", "moonlight metal"],
    "pine-resin": ["pine", "resin", "sap", "turpentine", "conifer", "pine tar", "rosin", "pine forest", "evergreen", "spruce", "fir"],
    "breath-fog": ["breath", "breathing", "exhale", "fog breath", "visible breath", "cold breath", "steam breath"],
    "moonless-dark": ["moonless", "pitch black", "pitch dark", "total darkness", "no moon", "starless", "blind dark", "can't see"],
    "manipulation-presence": ["manipulation", "manipulate", "deception", "deceive", "coerce", "coercion", "honeyed words", "false voice", "trusted voice wrong", "identity attack", "gaslighting", "circular logic"],
    "forge-metalwork": ["forge", "blacksmith", "anvil", "smithy", "metalwork", "foundry", "smelting", "welding", "ironwork", "furnace"],
    "classroom-school": ["classroom", "school", "kindergarten", "lecture hall", "university", "desk", "chalkboard", "teacher", "student", "preschool", "nursery school", "daycare"],
    "server-electronics": ["server", "server room", "data center", "datacenter", "computer room", "electronics", "rack", "mainframe"],
    "asian-street-food": ["ramen", "noodle", "street food", "wok", "dumpling", "pho", "thai food", "food stall", "food cart", "hawker"],
    "ancient-tomb": ["tomb", "pyramid", "burial chamber", "sarcophagus", "crypt", "mausoleum", "pharaoh", "mummy", "catacomb"],
    "submarine-interior": ["submarine", "sub", "u-boat", "periscope", "torpedo", "dive", "sonar"],
    "coral-reef": ["coral", "reef", "diving", "scuba", "snorkel", "tropical fish", "marine"],
    "aircraft-cabin": ["airplane", "aircraft", "cabin", "flight", "airline", "cockpit", "turbulence", "jet"],
    "victorian-domestic": ["victorian", "mansion", "manor", "parlor", "drawing room", "attic", "haunted house", "gothic house", "old house"],
    "live-music-venue": ["jazz club", "concert", "music venue", "gig", "nightclub", "live music", "band", "stage", "mosh pit"],
    "construction-site": ["construction", "building site", "scaffold", "crane", "jackhammer", "hard hat", "rebar", "concrete pour", "demolition site"],
    "wine-cellar": ["wine cellar", "wine barrel", "cellar", "winery", "vineyard cellar", "cask", "barrel room", "whiskey aging"],

    # Batch 4: Abandoned church primitives
    "abandoned-decay": ["abandoned", "derelict", "crumbling", "dilapidated", "condemned", "decrepit", "falling-apart", "neglected", "disrepair", "ruinous"],
    "church-sacred": ["church", "chapel", "cathedral", "basilica", "abbey", "monastery", "nave", "altar", "sanctuary", "sacristy", "vestry", "parish", "temple", "mosque", "synagogue", "shrine"],
    "wildlife-reclamation": ["overgrown", "reclaimed-by-nature", "pigeons", "birds-nesting", "ivy-covered", "vine-covered", "feral", "rewilded", "nature-reclaiming"],
    "dusk-light": ["dusk", "twilight", "gloaming", "sundown", "last-light", "blue-hour"],
    "churchyard-exterior": ["churchyard", "graveyard", "cemetery", "burial-ground", "headstone", "tombstone", "memorial-garden"],
    # Character primitives
    "tali-quarian": ["tali", "quarian", "tali'zorah", "vas normandy", "suit removal", "enviro-suit", "migrant fleet"],

    # Batch 5: Common materials
    "leather": ["leather", "hide", "suede", "rawhide", "cowhide", "leather-bound", "leather-seat", "leather-jacket"],
    "concrete": ["concrete", "cement", "sidewalk", "parking-garage", "brutalist", "cinder-block"],
    "brick": ["brick", "brickwork", "brick-wall", "brownstone", "masonry"],
    "paper-parchment": ["paper", "parchment", "vellum", "scroll", "manuscript", "book-pages", "cardboard"],
    "ceramic-porcelain": ["ceramic", "porcelain", "pottery", "tile", "china", "terracotta", "earthenware", "stoneware"],
    "rubber": ["rubber", "tire", "latex", "neoprene", "eraser", "gasket", "rubber-band"],
    "ice": ["ice", "frozen", "glacier", "icicle", "ice-rink", "frost", "permafrost", "iceberg"],
    "sand": ["sand", "sandy", "beach-sand", "dune", "sandbar", "quicksand", "desert-sand"],
    "mud": ["mud", "muddy", "swamp-mud", "clay-mud", "muck", "sludge", "bog"],
    "silk-fabric": ["silk", "satin", "velvet", "chiffon", "taffeta", "organza", "fine-fabric"],
    "copper-brass": ["copper", "brass", "bronze-metal", "copper-pipe", "brass-fitting", "patina", "verdigris"],
    "plastic": ["plastic", "polystyrene", "PVC", "acrylic", "nylon", "polyethylene", "styrofoam", "vinyl", "resin"],

    # Batch 6: Activity primitives
    "cooking": ["cooking", "kitchen", "baking", "frying", "roasting", "grilling", "sauteing", "boiling", "chef", "stove", "oven"],
    "combat-gunfire": ["combat", "gunfire", "gunshot", "battlefield", "firefight", "shooting", "warfare", "explosion", "military-engagement"],
    "sexual-activity": ["sex", "sexual", "lovemaking", "intimacy", "erotic", "intercourse", "arousal", "foreplay", "passionate"],

    # Batch 7: Natural biome primitives
    "desert": ["desert", "sahara", "arid", "dune", "oasis", "badlands", "mesa", "death-valley", "mojave", "gobi", "scorching"],
    "jungle": ["jungle", "rainforest", "tropical-forest", "amazon", "canopy", "undergrowth", "equatorial", "tropical-dense"],
    "swamp-marsh": ["swamp", "marsh", "bog", "wetland", "bayou", "fen", "mangrove", "everglades", "mire", "muskeg", "quagmire"],

    # Batch 8: Sci-fi physics
    "biotics-mass-effect": ["biotic", "biotics", "mass-effect-field", "element-zero", "eezo", "dark-energy", "singularity-biotic", "barrier-biotic", "throw-biotic", "warp-biotic"],
    "liara-asari": ["liara", "asari", "t'soni", "liara-t'soni", "shadow-broker", "embrace-eternity"],

}

def parse_description(description):
    """Extract physics primitives from a natural-language description using keyword matching."""
    desc_lower = description.lower()
    words = set(desc_lower.replace(",", " ").replace(".", " ").split())
    # Also split on hyphens for compound words
    words_with_hyphens = set(desc_lower.replace(",", " ").replace(".", " ").replace("-", " ").split())
    words = words | words_with_hyphens

    # Negative context: words that cancel a keyword match
    # e.g. "fire escape" shouldn't match the "fire" primitive
    # Negative context: (keyword, primitive) → negating words
    # Only cancels the match for the specified primitive, not all primitives using that keyword
    _NEGATIVE_CONTEXT_GLOBAL = {
        "fire": ["escape", "escapes", "truck", "station", "department", "hydrant", "exit",
                 "extinguisher", "alarm", "drill", "chief", "fighter", "proof"],
        "busy": ["abandoned", "deserted", "derelict", "ruined", "empty"],
        "packed": ["abandoned", "deserted", "derelict", "ruined", "empty"],
    }
    # Primitive-scoped: only cancel this keyword for this specific primitive
    _NEGATIVE_CONTEXT_SCOPED = {
        ("carnival", "crowd"): ["abandoned", "deserted", "derelict", "ruined", "empty", "closed", "shuttered"],
        ("festival", "crowd"): ["abandoned", "deserted", "derelict", "ruined", "empty", "closed"],
        ("market", "crowd"): ["abandoned", "deserted", "derelict", "ruined", "empty", "closed"],
        ("concert", "crowd"): ["abandoned", "deserted", "derelict", "ruined", "empty", "closed"],
    }

    matched = []
    for primitive, keywords in _PRIMITIVE_KEYWORDS.items():
        for kw in keywords:
            hit = False
            # Match multi-word keywords in the full string, single words in word set
            if " " in kw:
                if kw in desc_lower:
                    hit = True
            elif kw in words:
                hit = True

            if hit:
                # Check negative context (global first, then scoped)
                negatives = _NEGATIVE_CONTEXT_GLOBAL.get(kw, [])
                scoped_negatives = _NEGATIVE_CONTEXT_SCOPED.get((kw, primitive), [])
                all_negatives = negatives + scoped_negatives
                if all_negatives:
                    # Check if any negative word appears adjacent to keyword in description
                    cancelled = False
                    for neg in all_negatives:
                        if f"{kw} {neg}" in desc_lower or f"{neg} {kw}" in desc_lower:
                            cancelled = True
                            break
                    if cancelled:
                        continue
                matched.append(primitive)
                break

    # Deduplicate preserving order
    seen = set()
    result = []
    for p in matched:
        if p not in seen:
            seen.add(p)
            result.append(p)

    return result


def _apply_interactions(primitives, env_data, all_sounds, all_compounds, touch_notes_extra):
    """Apply cross-primitive interaction rules when certain primitives co-occur."""
    pset = set(primitives)
    interaction_notes = []

    for (pa, pb), rules in PRIMITIVE_INTERACTIONS.items():
        if pa in pset and pb in pset:
            if "humidity_add" in rules:
                env_data["humidity_pct"] = min(100, env_data.get("humidity_pct", 50) + rules["humidity_add"])
            if "temperature_add" in rules:
                env_data["temperature_c"] = env_data.get("temperature_c", 20) + rules["temperature_add"]
            if "sound_add" in rules:
                all_sounds.extend(rules["sound_add"])
            if "smell_add" in rules:
                all_compounds.extend(rules["smell_add"])
            if "smell_mod" in rules:
                pass  # volatility modifier — handled in output
            if "sight_clarity_override" in rules:
                env_data["_clarity_override"] = rules["sight_clarity_override"]
            if "touch_note" in rules:
                touch_notes_extra.append(rules["touch_note"])
            if "sound_note" in rules:
                interaction_notes.append(f"[SOUND INTERACTION: {pa} + {pb}] {rules['sound_note']}")
            if "smell_note" in rules:
                interaction_notes.append(f"[SMELL INTERACTION: {pa} + {pb}] {rules['smell_note']}")
            if "sight_note" in rules:
                interaction_notes.append(f"[SIGHT INTERACTION: {pa} + {pb}] {rules['sight_note']}")

    return interaction_notes


def _infer_environment(primitives, env_data):
    """Smart environment inference from primitive categories and combinations."""
    pset = set(primitives)
    categories = {PHYSICS_PRIMITIVES.get(p, {}).get("category", "unknown") for p in primitives}

    # Underground/cave → force stable earth temperature, no wind, indoor, no natural light
    underground_types = {"underground-tunnel", "cave"}
    if pset & underground_types:
        if "temperature_c" not in env_data or env_data["temperature_c"] == 20:  # only if still default
            env_data["temperature_c"] = 13  # stable earth temperature
        env_data["indoor"] = True
        env_data["wind_speed_kmh"] = 0

    # Enclosed spaces are indoor
    enclosed_types = {"enclosed-small", "enclosed-large", "corridor-narrow", "vehicle-interior"}
    if pset & enclosed_types:
        env_data["indoor"] = True

    # Night time adjustments (if no explicit temp from spatial type)
    if "night" in pset and "temperature_c" not in env_data:
        env_data["temperature_c"] = 12  # default night temp

    # Morning adjustments
    if "morning" in pset and "temperature_c" not in env_data:
        env_data["temperature_c"] = 14

    # Water presence increases humidity
    water_types = {"water", "water-surface", "rain", "fog", "steam"}
    water_count = len(pset & water_types)
    if water_count > 0:
        current_hum = env_data.get("humidity_pct", 50)
        env_data["humidity_pct"] = min(100, current_hum + water_count * 10)

    # Ensure defaults exist
    env_data.setdefault("temperature_c", 20)
    env_data.setdefault("humidity_pct", 50)
    env_data.setdefault("wind_speed_kmh", 5)
    env_data.setdefault("indoor", False)


def _compute_thermal_note(primitives, temp_c):
    """Compute the dominant thermal experience from materials + temperature."""
    materials = []
    for p in primitives:
        pdata = PHYSICS_PRIMITIVES.get(p, {})
        if pdata.get("category") == "material":
            tc = pdata.get("touch", {}).get("thermal_conductivity")
            tn = pdata.get("touch", {}).get("thermal_note", "")
            if tc is not None:
                materials.append((p, tc, tn))

    if not materials:
        if temp_c < 10:
            return f"At {temp_c}°C, everything feels cold. Exposed skin loses heat to the air."
        elif temp_c < 18:
            return f"At {temp_c}°C, cool. Surfaces draw warmth from contact."
        elif temp_c > 30:
            return f"At {temp_c}°C, heat presses on skin. Surfaces radiate stored warmth."
        else:
            return f"At {temp_c}°C, thermal neutral. The body forgets about temperature."

    # Sort by conductivity — highest conductor is the dominant thermal experience
    materials.sort(key=lambda x: x[1], reverse=True)
    dominant = materials[0]
    parts = [f"Dominant surface: {dominant[0]} (thermal conductivity {dominant[1]} W/m·K)."]
    if dominant[2]:
        parts.append(dominant[2])
    if temp_c < 15 and dominant[1] > 1.0:
        parts.append(f"At {temp_c}°C, this material aggressively drains body heat on contact.")
    elif temp_c < 15 and dominant[1] < 0.2:
        parts.append(f"At {temp_c}°C, this material insulates — feels warmer than the air temperature suggests.")

    return " ".join(parts)


def _compute_rt60(primitives):
    """Estimate RT60 from spatial type and material absorption."""
    base_rt60 = 0.5  # default
    for p in primitives:
        pdata = PHYSICS_PRIMITIVES.get(p, {})
        rt60 = pdata.get("sound", {}).get("rt60_s")
        if rt60 is not None:
            base_rt60 = max(base_rt60, rt60)  # spatial type sets the base

    # Materials modify — absorptive materials reduce RT60, reflective ones don't change it
    for p in primitives:
        pdata = PHYSICS_PRIMITIVES.get(p, {})
        if pdata.get("category") == "material":
            absorb = pdata.get("sound", {}).get("absorption_mod", 0)
            if absorb > 0.1:  # absorptive material
                base_rt60 *= (1.0 - absorb * 0.5)

    return round(base_rt60, 1)


def _find_unifying_material(primitives):
    """Find the material that affects the most senses — the 'stone' of this scene."""
    materials = [p for p in primitives if PHYSICS_PRIMITIVES.get(p, {}).get("category") == "material"]
    if not materials:
        return None

    # Score each material by how many sensory channels it has real data for
    best = None
    best_score = 0
    for m in materials:
        pdata = PHYSICS_PRIMITIVES.get(m, {})
        score = 0
        if pdata.get("sound", {}).get("sources"):
            score += 1
        if pdata.get("smell", {}).get("compounds"):
            score += 1
        if pdata.get("touch", {}).get("thermal_conductivity") is not None:
            score += 1
        if pdata.get("sight", {}).get("light_filter"):
            score += 1
        if score > best_score:
            best_score = score
            best = m

    return best


# ─── Sound source humanization (module-level for reuse) ─────────────────────
_SOUND_HUMANIZE = {
    "drip-echo": "water dripping somewhere ahead",
    "distant-rumble": "a distant rumble",
    "footstep-amplified": "your footsteps amplified",
    "ventilation-draft": "the sigh of ventilation",
    "insects-or-silence": "silence where insects should be",
    "distant-traffic-or-nothing": "maybe distant traffic, maybe nothing",
    "footstep-echo-louder": "your footsteps echoing louder now",
    "owl-or-machinery": "something calling in the dark",
    "near-nothing": "near-nothing",
    "blood-in-ears": "your own blood in your ears",
    "footstep-muffled-soft": "muffled footsteps on soft ground",
    "squelch-if-wet": "the squelch of wet earth",
    "muffled-distance": "distances muffled and close",
    "close-drip": "a close drip",
    "own-footsteps-loud": "your own footsteps, loud",
    "directionless-echo": "directionless echo",
}


def _get_detail_taste(detail_material, fallback_compounds, primitives=None):
    """Get taste compounds for the detail position.
    
    Prefer spatial primitive's taste (if high intensity) over material taste,
    since in scenes like organic-interior the space itself is the dominant taste source.
    """
    # Check if any spatial primitive has high-intensity taste
    if primitives:
        for pname in primitives:
            p = PHYSICS_PRIMITIVES.get(pname, {})
            if p.get("category") == "spatial":
                ptaste = p.get("taste", {})
                if ptaste.get("intensity", 0) >= 0.7:
                    return ptaste.get("compounds", [])[:4]
    if detail_material:
        mat = PHYSICS_PRIMITIVES.get(detail_material, {})
        mat_taste = mat.get("taste", {})
        if mat_taste.get("compounds"):
            return mat_taste["compounds"][:4]
    return (fallback_compounds or [])[-3:]


def _get_detail_taste_note(detail_material, fallback_notes, primitives=None):
    """Get taste note for the detail position.
    
    Same priority: spatial high-intensity taste > material taste > fallback.
    """
    if primitives:
        for pname in primitives:
            p = PHYSICS_PRIMITIVES.get(pname, {})
            if p.get("category") == "spatial":
                ptaste = p.get("taste", {})
                if ptaste.get("intensity", 0) >= 0.7 and ptaste.get("note"):
                    return ptaste["note"]
    if detail_material:
        mat = PHYSICS_PRIMITIVES.get(detail_material, {})
        mat_taste = mat.get("taste", {})
        if mat_taste.get("note"):
            return mat_taste["note"]
    return fallback_notes[-1] if fallback_notes else ""


def _generate_positions(primitives, title, temp_c, humidity, rt60, avg_clarity,
                        light_desc, sound_desc, smell_compounds, touch_surfaces,
                        touch_air, touch_notes_extra, thermal_note, has_reflections,
                        unifying_material, taste_compounds=None, taste_profiles=None,
                        taste_notes=None, taste_intensity=0.0):
    """
    Generate spatially-aware positions with parameter deltas.

    Position arc: threshold (contrast) → core (peak immersion) → detail (object-level) → [extreme if applicable]
    Each position has computed parameter shifts from the base environment.
    """
    pset = set(primitives)
    categories = {}
    for p in primitives:
        cat = PHYSICS_PRIMITIVES.get(p, {}).get("category", "unknown")
        categories.setdefault(cat, []).append(p)

    spatial = categories.get("spatial", [])
    materials = categories.get("material", [])
    atmospheres = categories.get("atmosphere", [])
    activities = categories.get("activity", [])

    # Determine spatial archetype for position naming
    spatial_type = spatial[0] if spatial else None

    # ── Position 1: Threshold (entry point, contrast with exterior) ──
    # The moment of crossing in — environmental shift from "outside" to "here"
    threshold_name, threshold_desc = _threshold_for_spatial(spatial_type, title)

    # Compute contrast: what changes when you enter?
    if PHYSICS_PRIMITIVES.get(spatial_type or "", {}).get("environment", {}).get("indoor"):
        threshold_contrast = f"Temperature shifts from ambient to {temp_c}°C. Sound changes — exterior noise cuts off, replaced by interior acoustics (RT60: {rt60}s). The air changes: {humidity}% humidity, {'still and trapped' if not any(p in pset for p in ('wind',)) else 'moving'}."
    else:
        threshold_contrast = f"The space opens: {temp_c}°C, {humidity}% humidity, {'wind on exposed skin' if any(p in pset for p in ('wind', 'elevated-open', 'rooftop', 'open-field')) else 'air moves freely'}."

    pos1 = {
        "name": threshold_name,
        "description": threshold_desc,
        "prose": "",
        "sight_notes": f"The light shifts from exterior to {light_desc}. {'Reflections on wet surfaces double the visual field.' if has_reflections else 'Eyes adjusting.'}",
        "sound_notes": f"Exterior noise gives way to {sound_desc[:120]}. Reverb: {rt60}s." if sound_desc else "The acoustic character of the space asserts itself.",
        "touch_notes": threshold_contrast,
        "surface_textures": touch_surfaces[:2],
        "smell_emphasis": smell_compounds[:3],
        "taste_compounds": (taste_compounds or [])[:3],
        "taste_notes": "",
        "taste_profile": taste_profiles or {},
        "taste_intensity": taste_intensity * 0.5,  # threshold = half intensity (entering)
        "parameter_deltas": f"ENTRY: temp shifts to {temp_c}°C, humidity to {humidity}%, sound RT60 {rt60}s",
    }

    # ── Position 2: Core (deepest immersion, all senses engaged) ──
    core_name, core_desc = _core_for_spatial(spatial_type, title)

    # Core is where all primitives fire at once
    core_sound = sound_desc if sound_desc else "silence dominates"
    core_smell = ", ".join(smell_compounds[1:6]) if len(smell_compounds) > 1 else ", ".join(smell_compounds)

    pos2 = {
        "name": core_name,
        "description": core_desc,
        "prose": "",
        "sight_notes": f"Visual clarity at {avg_clarity:.1f}. {light_desc}. Everything visible from this vantage.",
        "sound_notes": f"{core_sound}. RT60: {rt60}s. Every acoustic layer present at once.",
        "touch_notes": "; ".join(touch_notes_extra[:3]) if touch_notes_extra else thermal_note,
        "surface_textures": touch_surfaces,
        "smell_emphasis": smell_compounds[1:6],
        "taste_compounds": (taste_compounds or [])[:5],
        "taste_notes": (taste_notes[0] if taste_notes else ""),
        "taste_profile": taste_profiles or {},
        "taste_intensity": taste_intensity,  # core = full intensity
        "parameter_deltas": f"PEAK: all senses at full engagement. Smell concentration highest. Sound fully developed.",
    }

    # ── Position 3: Detail (object-level, intimate interaction) ──
    detail_name, detail_desc = _detail_for_spatial(spatial_type, materials, title, unifying_material)

    # Detail position: zoom in on the dominant material
    detail_material = unifying_material or (materials[0] if materials else None)
    if detail_material:
        dm = PHYSICS_PRIMITIVES.get(detail_material, {})
        tc = dm.get("touch", {}).get("thermal_conductivity")
        tn = dm.get("touch", {}).get("thermal_note", "")
        mat_name = detail_material.replace("-", " ").replace("_", " ")
        detail_touch = f"Direct contact with {mat_name}. "
        if tn:
            detail_touch += tn
        detail_smell = dm.get("smell", {}).get("compounds", [])[:3]
        detail_sound_sources = dm.get("sound", {}).get("sources", [])
    else:
        detail_touch = thermal_note
        detail_smell = smell_compounds[-3:] if smell_compounds else []
        detail_sound_sources = []

    pos3 = {
        "name": detail_name,
        "description": detail_desc,
        "prose": "",
        "sight_notes": f"Close focus. Detail visible: surface texture, wear patterns, age markers.",
        "sound_notes": f"Close sounds: {', '.join(_SOUND_HUMANIZE.get(s, s.replace('-', ' ')) for s in detail_sound_sources)}." if detail_sound_sources else f"Quiet here — small sounds dominate. RT60 felt differently at close range.",
        "touch_notes": detail_touch,
        "surface_textures": [PHYSICS_PRIMITIVES.get(detail_material, {}).get("touch", {}).get("surfaces", "")] if detail_material else touch_surfaces[-1:],
        "smell_emphasis": detail_smell if detail_smell else smell_compounds[-2:],
        "taste_compounds": _get_detail_taste(detail_material, taste_compounds, primitives),
        "taste_notes": _get_detail_taste_note(detail_material, taste_notes, primitives),
        "taste_profile": taste_profiles or {},
        "taste_intensity": taste_intensity * 0.8,  # detail = direct contact, high intensity
        "parameter_deltas": f"INTIMATE: sensory field narrows. Touch becomes primary. Smell concentrated at source.",
    }

    positions = [pos1, pos2, pos3]

    # ── Optional Position 4: Extreme (if scene has compression/underground/darkness) ──
    extreme_triggers = {"underground-tunnel", "cave", "no-light", "decay-organic", "organic-interior"}
    if pset & extreme_triggers:
        extreme_name, extreme_desc = _extreme_for_spatial(spatial_type, pset, title)
        # Parameter compression: everything narrows
        extreme_temp = temp_c - 3 if spatial_type in ("underground-tunnel", "cave") else temp_c
        extreme_humidity = min(100, humidity + 10) if spatial_type in ("underground-tunnel", "cave") else humidity

        pos4 = {
            "name": extreme_name,
            "description": extreme_desc,
            "prose": "",
            "sight_notes": f"Visual clarity drops. {'Total darkness — other senses compensate.' if 'no-light' in pset or 'cave' in pset else 'Light reduced to minimum.'}",
            "sound_notes": f"Acoustics compressed: RT60 drops to {max(0.3, rt60 * 0.4):.1f}s. {'Silence absolute.' if 'silence' in pset else 'Only close sounds survive.'}",
            "touch_notes": f"Temperature: {extreme_temp}°C (dropped {temp_c - extreme_temp}°C from core). Humidity: {extreme_humidity}%. Surfaces close — ceiling within reach. {thermal_note}",
            "surface_textures": touch_surfaces[-1:] if touch_surfaces else [],
            "smell_emphasis": [c for c in smell_compounds if "mineral" in c or "earth" in c or "iron" in c or "damp" in c][:3] or smell_compounds[-2:],
            "taste_compounds": _get_detail_taste(None, taste_compounds, primitives),
            "taste_notes": _get_detail_taste_note(None, taste_notes, primitives),
            "taste_profile": taste_profiles or {},
            "taste_intensity": taste_intensity,  # extreme = concentrated
            "parameter_deltas": f"COMPRESSION: temp {extreme_temp}°C (−{temp_c - extreme_temp}°C), humidity {extreme_humidity}%, RT60 {max(0.3, rt60 * 0.4):.1f}s, visual near-zero, all senses narrow",
        }
        positions.append(pos4)

    return positions


def _threshold_for_spatial(spatial_type, title):
    """Generate threshold position name/description based on spatial type."""
    mapping = {
        "underground-tunnel": ("the entrance", "Where the stairs descend or the passage begins — the last point of exterior contact"),
        "cave": ("the mouth", "Where daylight ends and the cave begins — a hard boundary between worlds"),
        "enclosed-large": ("the doorway", "The threshold where exterior gives way to the vast interior volume"),
        "enclosed-small": ("the door", "The moment of entering the small space — scale contracts instantly"),
        "corridor-narrow": ("the corridor entrance", "Where the passage begins — walls close in from both sides"),
        "rooftop": ("the access door", "Stepping from interior stairs onto the open roof — sky replaces ceiling"),
        "open-field": ("the edge", "Where the terrain opens — shelter ends and exposure begins"),
        "elevated-open": ("the ascent", "The final approach — wind strengthens, temperature drops, vista expands"),
        "vehicle-interior": ("the door", "Entering the enclosed cabin — exterior sounds seal off as the door closes"),
        "waterside": ("the approach", "Where ground transitions to water's edge — sound and humidity shift"),
        "organic-interior": ("the mouth", "The opening — teeth or baleen above, tongue below, the last point where outside air mixes with inside"),
    }
    return mapping.get(spatial_type, ("the threshold", f"Arriving at {title} — the moment of first sensory contact"))


def _core_for_spatial(spatial_type, title):
    """Generate core position name/description."""
    mapping = {
        "underground-tunnel": ("deep in the tunnel", "The middle passage — fully enclosed, fully underground, maximum distance from any entrance"),
        "cave": ("the main chamber", "The central cavern — largest volume, peak echo, deepest darkness"),
        "enclosed-large": ("the center", "The heart of the space — maximum distance from walls, full acoustic envelope"),
        "enclosed-small": ("inside", "Fully within the small space — walls close, ceiling low, all senses concentrated"),
        "corridor-narrow": ("mid-corridor", "The passage stretches in both directions — no reference point, only the corridor"),
        "rooftop": ("the center of the roof", "Maximum exposure — sky above, city below, wind unobstructed"),
        "open-field": ("the middle of the field", "Equidistant from all edges — maximum exposure, minimum shelter"),
        "elevated-open": ("the summit", "The highest point — maximum altitude, maximum exposure, maximum vista"),
        "vehicle-interior": ("in motion", "Fully enclosed, moving — the rhythm of travel dominates all senses"),
        "waterside": ("the water's edge", "Where land meets water — spray, sound, and humidity at their peak"),
        "organic-interior": ("the stomach", "The central cavity — surrounded by living walls, rhythmic contractions, acid pool below, every surface moving"),
    }
    return mapping.get(spatial_type, ("the center", f"Deep inside {title} — all senses fully engaged"))


def _detail_for_spatial(spatial_type, materials, title, unifying_material):
    """Generate detail position — object-level interaction."""
    if unifying_material:
        mat_name = unifying_material.replace("-", " ").replace("_", " ")
        return (f"touching the {mat_name}", f"Direct physical contact with {mat_name} — the scene's dominant material up close")

    if materials:
        mat_name = materials[0].replace("-", " ").replace("_", " ")
        return (f"touching the {mat_name}", f"Hands on the primary surface — {mat_name} at intimate range")

    detail_map = {
        "underground-tunnel": ("a wall section", "Hand pressed against the tunnel wall — feeling the material, the temperature, the age"),
        "cave": ("a formation", "Touching a stalactite or rock face — the geology at hand-scale"),
        "rooftop": ("the railing", "Gripping the edge railing — the boundary between roof and sky"),
        "open-field": ("the ground", "Kneeling to touch the earth — grass, soil, insects, the micro-world"),
        "waterside": ("the water", "Hand breaking the surface — temperature shock, texture of liquid, depth unknown"),
        "organic-interior": ("the stomach wall", "Hand pressed against living tissue — warm, wet, muscular, it contracts under your touch and pushes back"),
    }
    return detail_map.get(spatial_type, ("a surface", f"Close contact with a surface in {title} — the detail scale"))


def _extreme_for_spatial(spatial_type, pset, title):
    """Generate extreme/compression position for underground/dark/intense scenes."""
    if spatial_type == "underground-tunnel":
        return ("the deepest point", "Maximum depth — furthest from any entrance, every parameter at its extreme. The tunnel's endpoint.")
    elif spatial_type == "cave":
        return ("the inner chamber", "Beyond the main cavern — a tighter space, lower ceiling, the cave's most compressed point")
    elif spatial_type == "organic-interior":
        return ("the intestine", "Beyond the stomach — the passage narrows, walls press closer, peristalsis pushes you forward whether you move or not")
    elif "no-light" in pset:
        return ("total darkness", "The point where all light sources are gone — spatial awareness collapses to arm's length")
    elif "decay-organic" in pset:
        return ("the source", "Closest to the decay — smell overwhelming, visual detail unflinching, the scene's most intense point")
    return ("the far end", f"The extremity of {title} — parameters at their most compressed")


def compose_from_primitives(primitives, title="Custom Composition"):
    """
    Compose a MindscapeScene from a list of physics primitives.

    Phase B: Smart composition with environment inference, interaction rules,
    thermal computation, and RT60 estimation.
    """
    # Merge environment
    env_data = dict(EnvironmentalConditions.DEFAULTS)
    temp_values = []
    hum_values = []
    wind_values = []

    all_sounds = []
    all_compounds = []
    all_taste_compounds = []
    all_taste_profiles = {}  # modality → max intensity
    all_taste_notes = []
    max_taste_intensity = 0.0
    total_absorption = 0.0
    total_clarity = 0.0
    clarity_count = 0
    touch_surfaces = []
    touch_air = []
    touch_notes_extra = []
    has_reflections = False
    light_filters = []
    thermal_conductivities = []

    for pname in primitives:
        p = PHYSICS_PRIMITIVES.get(pname, {})

        # Environment: collect for averaging
        penv = p.get("environment", {})
        if "temperature_c" in penv:
            temp_values.append(penv["temperature_c"])
        if "humidity_pct" in penv:
            hum_values.append(penv["humidity_pct"])
        if "wind_speed_kmh" in penv:
            wind_values.append(penv["wind_speed_kmh"])
        if "weather" in penv:
            env_data["weather"] = penv["weather"]
        if "time_of_day" in penv:
            env_data["time_of_day"] = penv["time_of_day"]
        if "indoor" in penv:
            env_data["indoor"] = penv["indoor"]
        if "wind_direction" in penv:
            env_data["wind_direction"] = penv["wind_direction"]

        # Sound
        psound = p.get("sound", {})
        all_sounds.extend(psound.get("sources", []))
        total_absorption += psound.get("absorption_mod", 0)

        # Smell
        psmell = p.get("smell", {})
        all_compounds.extend(psmell.get("compounds", []))

        # Taste
        ptaste = p.get("taste", {})
        if ptaste:
            all_taste_compounds.extend(ptaste.get("compounds", []))
            for modality, value in ptaste.get("profile", {}).items():
                all_taste_profiles[modality] = max(all_taste_profiles.get(modality, 0), value)
            intensity = ptaste.get("intensity", 0)
            if intensity > max_taste_intensity:
                max_taste_intensity = intensity
            if ptaste.get("note"):
                all_taste_notes.append(ptaste["note"])

        # Sight
        psight = p.get("sight", {})
        if "clarity_mod" in psight and psight["clarity_mod"] > 0:
            total_clarity += psight["clarity_mod"]
            clarity_count += 1
        if psight.get("reflections"):
            has_reflections = True
        if psight.get("light_filter") and psight["light_filter"] not in ("unchanged",):
            light_filters.append(psight["light_filter"])

        # Touch
        ptouch = p.get("touch", {})
        if ptouch.get("surfaces"):
            touch_surfaces.append(ptouch["surfaces"])
        if ptouch.get("air"):
            touch_air.append(ptouch["air"])
        if ptouch.get("thermal_conductivity"):
            thermal_conductivities.append((pname, ptouch["thermal_conductivity"]))
        if ptouch.get("thermal_note"):
            touch_notes_extra.append(ptouch["thermal_note"])

    # ── Material Resolution ──────────────────────────────────────
    # Spatial primitives reference material primitives. Pull in their
    # physics (smell compounds, touch surfaces/conductivities, sound sources)
    # so the composed scene inherits real material data.
    _resolved_materials = set()
    for pname in primitives:
        p = PHYSICS_PRIMITIVES.get(pname, {})
        for mat_name in p.get("materials", []):
            if mat_name in _resolved_materials:
                continue
            _resolved_materials.add(mat_name)
            mat = PHYSICS_PRIMITIVES.get(mat_name, {})
            if not mat:
                continue
            # Pull smell compounds from materials
            mat_smell = mat.get("smell", {})
            for comp in mat_smell.get("compounds", []):
                if comp not in all_compounds:
                    all_compounds.append(comp)
            # Pull sound sources from materials
            mat_sound = mat.get("sound", {})
            for src in mat_sound.get("sources", []):
                if src not in all_sounds:
                    all_sounds.append(src)
            # Pull touch surfaces and thermal data from materials
            mat_touch = mat.get("touch", {})
            if mat_touch.get("surfaces"):
                touch_surfaces.append(mat_touch["surfaces"])
            if mat_touch.get("thermal_conductivity"):
                thermal_conductivities.append((mat_name, mat_touch["thermal_conductivity"]))
            if mat_touch.get("thermal_note"):
                touch_notes_extra.append(mat_touch["thermal_note"])
            # Pull taste from materials
            mat_taste = mat.get("taste", {})
            if mat_taste:
                for comp in mat_taste.get("compounds", []):
                    if comp not in all_taste_compounds:
                        all_taste_compounds.append(comp)
                for modality, value in mat_taste.get("profile", {}).items():
                    all_taste_profiles[modality] = max(all_taste_profiles.get(modality, 0), value)
                intensity = mat_taste.get("intensity", 0)
                if intensity > max_taste_intensity:
                    max_taste_intensity = intensity
                if mat_taste.get("note") and mat_taste["note"] not in all_taste_notes:
                    all_taste_notes.append(mat_taste["note"])
    # Also track resolved materials for position generation
    _all_materials = list(_resolved_materials)
    # Add any explicitly matched material primitives too
    for pname in primitives:
        p = PHYSICS_PRIMITIVES.get(pname, {})
        if p.get("category") == "material" and pname not in _resolved_materials:
            _all_materials.append(pname)

    # Resolve environment values
    if temp_values:
        env_data["temperature_c"] = round(sum(temp_values) / len(temp_values))
    if hum_values:
        env_data["humidity_pct"] = round(sum(hum_values) / len(hum_values))
    if wind_values:
        env_data["wind_speed_kmh"] = max(wind_values)

    # Smart inference layer — override bad defaults
    _infer_environment(primitives, env_data)

    # Apply cross-primitive interaction rules
    interaction_notes = _apply_interactions(primitives, env_data, all_sounds, all_compounds, touch_notes_extra)

    # Apply clarity override from interactions if present
    if "_clarity_override" in env_data:
        avg_clarity = env_data.pop("_clarity_override")
    else:
        avg_clarity = (total_clarity / clarity_count) if clarity_count else 0.8

    # Compute derived physics
    temp_c = env_data.get("temperature_c", 20)
    thermal_note = _compute_thermal_note(primitives, temp_c)
    rt60 = _compute_rt60(primitives)
    unifying_material = _find_unifying_material(primitives)

    # Deduplicate
    all_sounds = list(dict.fromkeys(all_sounds))
    all_compounds = list(dict.fromkeys(all_compounds))

    smell_desc = ", ".join(all_compounds[:10]) if all_compounds else ""
    # Humanize sound source names (uses module-level _SOUND_HUMANIZE)
    humanized_sounds = [_SOUND_HUMANIZE.get(s, s.replace("-", " ")) for s in all_sounds[:10]]
    sound_desc = ", ".join(humanized_sounds) if humanized_sounds else ""
    # Humanize light filter names
    _LIGHT_HUMANIZE = {
        "no-natural-light": "no natural light",
        "scotopic-blue-shift-pools-of-artificial": "blue-shifted darkness with pools of artificial light",
        "mie-scatter-white-grey": "white-grey haze — light scattered by water droplets",
        "warm-tone-mie-scatter-beams-visible": "warm-toned haze with visible light beams",
        "dark-brown-irregular": "dark earth tones, irregular and shadow-heavy",
        "amber-sodium-vapor": "amber sodium-vapor glow",
        "green-chlorophyll-filter": "green light filtered through leaves",
        "blue-grey-overcast": "flat blue-grey overcast light",
    }
    humanized_filters = [_LIGHT_HUMANIZE.get(f, f.replace("-", " ")) for f in light_filters[:4]]
    light_desc = " shifting to ".join(humanized_filters) if humanized_filters else "ambient"

    # Build touch profile with computed thermals
    touch_profile = {
        "surface_textures": touch_surfaces,
        "air_feel": "; ".join(touch_air[:4]) if touch_air else "",
        "thermal_notes": thermal_note,
        "thermal_conductivities": {name: tc for name, tc in thermal_conductivities},
        "interaction_notes": touch_notes_extra,
        "key_tactile_moments": touch_surfaces[:3] if touch_surfaces else [],
    }

    # Build reconciliation data
    reconciliation = {}
    if unifying_material:
        um_data = PHYSICS_PRIMITIVES.get(unifying_material, {})
        um_effects = []
        if um_data.get("sound", {}).get("sources"):
            um_effects.append(f"sound: {', '.join(um_data['sound']['sources'])}")
        if um_data.get("smell", {}).get("compounds"):
            um_effects.append(f"smell: {', '.join(um_data['smell']['compounds'][:3])}")
        if um_data.get("touch", {}).get("thermal_conductivity"):
            um_effects.append(f"touch: {um_data['touch']['thermal_conductivity']} W/m·K thermal conductivity")
        if um_data.get("sight", {}).get("light_filter"):
            um_effects.append(f"sight: {um_data['sight']['light_filter']}")
        reconciliation["unifying_material"] = {
            "name": unifying_material,
            "effects": um_effects,
            "note": f"{unifying_material} is the scene's unifying material — one substance, {len(um_effects)} sensory consequences.",
        }
    if interaction_notes:
        reconciliation["cross_primitive_interactions"] = interaction_notes

    # ── Phase C: Smart Position Generation ──
    # Compute positions with parameter deltas based on spatial type
    positions = _generate_positions(
        primitives=primitives,
        title=title,
        temp_c=temp_c,
        humidity=env_data.get("humidity_pct", 50),
        rt60=rt60,
        avg_clarity=avg_clarity,
        light_desc=light_desc,
        sound_desc=sound_desc,
        smell_compounds=all_compounds,
        touch_surfaces=touch_surfaces,
        touch_air=touch_air,
        touch_notes_extra=touch_notes_extra,
        thermal_note=thermal_note,
        has_reflections=has_reflections,
        unifying_material=unifying_material,
        taste_compounds=all_taste_compounds,
        taste_profiles=all_taste_profiles,
        taste_notes=all_taste_notes,
        taste_intensity=max_taste_intensity,
    )

    scene_data = {
        "id": "composed",
        "name": title,
        "description": f"Composed from primitives: {', '.join(primitives)}",
        "smell": {"compounds": all_compounds},
        "taste": {"compounds": all_taste_compounds, "profile": all_taste_profiles, "intensity": max_taste_intensity, "notes": all_taste_notes, "mouthfeel": "watery"},
        "sight": {"notes": f"Light: {light_desc}. Clarity: {avg_clarity:.1f}. Reflections: {has_reflections}"},
        "sound": {"notes": f"Sources: {sound_desc}. Absorption: {min(0.8, total_absorption):.2f}. RT60: {rt60}s"},
        "touch": touch_profile,
        "environment": env_data,
        "positions": positions,
        "cross_sensory_bridges": interaction_notes,
        "reconciliation": reconciliation,
        "mood": [],
    }

    return MindscapeScene(scene_data)


class MindscapeEngine:
    """The unified multi-sensory engine."""

    def __init__(self):
        self.smell_db = SmellDB()
        self.sight_db = SightDB()
        self.sound_db = SoundDB()
        self._scenes = None

    @property
    def scenes(self):
        if self._scenes is None:
            self._scenes = load_all_scenes(SCENES_DIR)
        return self._scenes

    def list_scenes(self):
        return sorted((s.id, s.name) for s in self.scenes.values())

    def find_scene(self, term, confidence_threshold=0.6):
        """Find a mindscape scene by id or name (fuzzy with confidence threshold)."""
        import difflib
        term_clean = term.strip().lower().replace(" ", "-").replace("_", "-")

        # Exact id match
        if term_clean in self.scenes:
            return self.scenes[term_clean]

        # Exact name match
        for s in self.scenes.values():
            if s.name.lower() == term.strip().lower():
                return s

        # Fuzzy on id — use SequenceMatcher for score
        ids = list(self.scenes.keys())
        best_id_score = 0
        best_id_match = None
        for sid in ids:
            score = difflib.SequenceMatcher(None, term_clean, sid).ratio()
            if score > best_id_score:
                best_id_score = score
                best_id_match = sid

        # Fuzzy on name
        names = {s.name.lower(): s for s in self.scenes.values()}
        best_name_score = 0
        best_name_match = None
        for name in names:
            score = difflib.SequenceMatcher(None, term.strip().lower(), name).ratio()
            if score > best_name_score:
                best_name_score = score
                best_name_match = name

        # Pick the best match overall
        if best_id_score >= best_name_score and best_id_score >= confidence_threshold:
            return self.scenes[best_id_match]
        if best_name_score >= confidence_threshold:
            return names[best_name_match]

        # Below threshold — return None and let caller handle the warning
        return None

    def get_fuzzy_warning(self, term):
        """Return a warning message for low-confidence fuzzy matches."""
        available = [s[0] for s in self.list_scenes()]
        return (
            f"⚠️  No preset mindscape found for '{term}'. "
            f"Available presets: {', '.join(available)}. "
            f"Use --custom to build a scene from individual sense components."
        )

    def _get_smell_prose(self, scene, position=None):
        smell_ref = scene.smell
        if not smell_ref:
            return ""

        scene_id = smell_ref.get("scene_id", "")
        if scene_id:
            result = self.smell_db.scene(scene_id)
            if result:
                try:
                    from smell_language import narrate_scene as smell_narrate
                    return smell_narrate(result, "moderate")
                except ImportError:
                    pass

        compounds = smell_ref.get("compounds", [])
        if position and position.smell_emphasis:
            compounds = position.smell_emphasis

        if not compounds:
            return ""

        mix = self.smell_db.mix(compounds)
        if mix["compounds"]:
            try:
                from smell_language import narrate_mix as smell_narrate_mix
                return smell_narrate_mix(mix, "moderate")
            except ImportError:
                notes = mix["dominant_notes"][:5] + mix["subtle_notes"][:3]
                if notes:
                    return f"The air carries notes of {', '.join(notes[:-1])}, and {notes[-1]}." if len(notes) > 1 else f"The air carries a note of {notes[0]}."
        return ""

    def _get_sight_prose(self, scene, position_idx=None):
        sight_ref = scene.sight
        if not sight_ref:
            return ""

        scene_id = sight_ref.get("scene_id", "")
        if scene_id:
            desc = self.sight_db.describe_scene(scene_id)
            if desc:
                if position_idx is not None:
                    raw = desc["_raw"]
                    walk = raw.get("walk", [])
                    if walk and position_idx < len(walk):
                        return walk[position_idx].get("prose", "")
                return desc.get("prose", "") or desc["_raw"].get("prose", "")
        return ""

    def _get_sound_prose(self, scene, position_idx=None):
        sound_ref = scene.sound
        if not sound_ref:
            return ""

        scene_id = sound_ref.get("scene_id", "")
        if scene_id:
            desc = self.sound_db.describe_scene(scene_id)
            if desc:
                if position_idx is not None:
                    raw = desc["_raw"]
                    walk = raw.get("walk", [])
                    if walk and position_idx < len(walk):
                        return walk[position_idx].get("prose", "")
                return desc.get("prose", "") or desc["_raw"].get("prose", "")
        return ""

    def describe_scene(self, scene):
        if scene.prose:
            return scene.prose

        smell_prose = self._get_smell_prose(scene)
        sight_prose = self._get_sight_prose(scene)
        sound_prose = self._get_sound_prose(scene)
        return narrate_scene(scene, smell_prose, sight_prose, sound_prose)

    def walk_scene(self, scene):
        if not scene.positions:
            return f"Scene '{scene.name}' has no walk positions. Use --scene for a static description."

        parts = []
        parts.append(f"━━━ {scene.name} ━━━")
        parts.append(f"    {scene.description}")
        parts.append("")

        env_desc = get_env_description(scene.environment)
        if env_desc:
            parts.append(env_desc)
            parts.append("")

        prev = None
        for i, pos in enumerate(scene.positions):
            parts.append(f"▸ {pos.name}")
            parts.append("")

            if pos.prose:
                parts.append(pos.prose)
            else:
                fragments = []

                sight_text = self._get_sight_prose(scene, i)
                if sight_text:
                    fragments.append(sight_text)
                elif pos.sight_notes:
                    fragments.append(pos.sight_notes)

                sound_text = self._get_sound_prose(scene, i)
                if sound_text:
                    fragments.append(sound_text)
                elif pos.sound_notes:
                    fragments.append(pos.sound_notes)

                smell_text = self._get_smell_prose(scene, pos)
                if smell_text:
                    fragments.append(smell_text)

                if fragments:
                    parts.append(" ".join(fragments))

            if pos.cross_sensory:
                parts.append("")
                parts.append(pos.cross_sensory)

            parts.append("")

            if i < len(scene.positions) - 1:
                next_pos = scene.positions[i + 1]
                parts.append(f"  → moving toward {next_pos.name}...")
                parts.append("")

            prev = pos

        return "\n".join(parts)

    def narrate_scene(self, scene):
        if scene.prose:
            parts = [f"━━━ {scene.name} ━━━", "", scene.prose]
            return "\n".join(parts)

        return self.describe_scene(scene)


    def custom_compose(self, light=None, material=None, atmosphere=None,
                       sound_source=None, sound_env=None, smell_scene=None,
                       title=None, narrate=False):
        """Build a custom mindscape from individual sense components."""
        parts = []
        title_str = title or "Custom Mindscape"
        parts.append(f"━━━ {title_str} ━━━")
        parts.append("")

        sight_prose = ""
        sound_prose = ""
        smell_prose = ""

        # --- Sight ---
        if light or material or atmosphere:
            if light and material and atmosphere:
                result = self.sight_db.compose(light, material, atmosphere)
                if not result["errors"]:
                    if narrate:
                        try:
                            from sight_language import narrate_composition
                            sight_prose = narrate_composition(result["light"], result["material"], result["atmosphere"])
                        except ImportError:
                            sight_prose = self._basic_sight_prose(result)
                    else:
                        sight_prose = self._basic_sight_prose(result)
                else:
                    parts.append("⚠️  Sight: " + "; ".join(result["errors"]))
            else:
                # Partial sight — describe what we have
                fragments = []
                if light:
                    desc = self.sight_db.describe_light(light)
                    if desc:
                        if narrate:
                            try:
                                from sight_language import narrate_light
                                fragments.append(narrate_light(desc["_raw"]))
                            except ImportError:
                                fragments.append(f"The light: {desc['name']} — {desc['feel']}" if desc['feel'] else f"The light: {desc['name']}")
                        else:
                            fragments.append(f"The light: {desc['name']} — {desc['feel']}" if desc['feel'] else f"The light: {desc['name']}")
                    else:
                        parts.append(f"⚠️  Light '{light}' not found")
                if material:
                    desc = self.sight_db.describe_material(material)
                    if desc:
                        frags = desc.get('prose_fragments', [])
                        fragments.append(frags[0] if frags else f"The surface: {desc['name']}")
                    else:
                        parts.append(f"⚠️  Material '{material}' not found")
                if atmosphere:
                    desc = self.sight_db.describe_atmosphere(atmosphere)
                    if desc:
                        frags = desc.get('prose_fragments', [])
                        fragments.append(frags[0] if frags else f"The air: {desc['name']}")
                    else:
                        parts.append(f"⚠️  Atmosphere '{atmosphere}' not found")
                sight_prose = " ".join(fragments)

        # --- Sound ---
        if sound_source:
            if sound_env:
                result = self.sound_db.compose(sound_source, sound_env, "mid")
                if not result["errors"]:
                    if narrate:
                        try:
                            from sound_language import narrate_composition as snd_narrate
                            sound_prose = snd_narrate(result["source"], result["environment"], result["distance"])
                        except ImportError:
                            sound_prose = self._basic_sound_prose(result)
                    else:
                        sound_prose = self._basic_sound_prose(result)
                else:
                    parts.append("⚠️  Sound: " + "; ".join(result["errors"]))
            else:
                desc = self.sound_db.describe_source(sound_source)
                if desc:
                    if narrate:
                        try:
                            from sound_language import narrate_source
                            sound_prose = narrate_source(desc["_raw"])
                        except ImportError:
                            sound_prose = f"{desc['name']}: {desc['feel']}" if desc['feel'] else desc['name']
                    else:
                        sound_prose = f"{desc['name']}: {desc['feel']}" if desc['feel'] else desc['name']
                else:
                    parts.append(f"⚠️  Sound source '{sound_source}' not found")

        # --- Smell ---
        if smell_scene:
            scene_result = self.smell_db.scene(smell_scene)
            if scene_result:
                if narrate:
                    try:
                        from smell_language import narrate_scene as smell_narrate
                        smell_prose = smell_narrate(scene_result, "moderate")
                    except ImportError:
                        notes = scene_result["dominant_notes"][:5]
                        smell_prose = f"The air carries notes of {', '.join(notes)}." if notes else ""
                else:
                    notes = scene_result["dominant_notes"][:5] + scene_result["subtle_notes"][:3]
                    if notes:
                        smell_prose = f"The air carries notes of {', '.join(notes[:-1])}, and {notes[-1]}." if len(notes) > 1 else f"A note of {notes[0]} in the air."
            else:
                parts.append(f"⚠️  Smell scene '{smell_scene}' not found")

        # --- Weave together using cross-sensory language ---
        if sight_prose or sound_prose or smell_prose:
            # Create a minimal scene object for the narration engine
            mock_scene = MindscapeScene({
                "id": "custom",
                "name": title_str,
                "environment": {},
            })
            woven = narrate_scene(mock_scene, smell_prose, sight_prose, sound_prose)
            parts.append(woven)
        else:
            parts.append("(No sense components produced output)")

        return "\n".join(parts)

    def _basic_sight_prose(self, compose_result):
        l = compose_result["light"]
        m = compose_result["material"]
        a = compose_result["atmosphere"]
        frags = []
        l_exp = l.get("experiential", {})
        if l_exp.get("prose_fragments"):
            frags.append(l_exp["prose_fragments"][0])
        m_key = l.get("category", "natural")
        interaction = m.get("light_interactions", {}).get(m_key, "")
        if interaction:
            frags.append(interaction)
        elif m.get("experiential", {}).get("prose_fragments"):
            frags.append(m["experiential"]["prose_fragments"][0])
        a_exp = a.get("experiential", {})
        if a_exp.get("prose_fragments"):
            frags.append(a_exp["prose_fragments"][0])
        return " ".join(frags) if frags else f"{l['name']} on {m['name']} through {a['name']}"

    def _basic_sound_prose(self, compose_result):
        src = compose_result["source"]
        env = compose_result["environment"]
        frags = []
        src_exp = src.get("experiential", {})
        if src_exp.get("prose_fragments"):
            frags.append(src_exp["prose_fragments"][0])
        env_exp = env.get("experiential", {})
        if env_exp.get("prose_fragments"):
            frags.append(env_exp["prose_fragments"][0])
        return " ".join(frags) if frags else f"{src['name']} in {env['name']}"

    def compose_from_description(self, description, narrate=False):
        """Compose a mindscape from a description using physics primitives.

        First tries primitive composition; falls back to keyword matching if no
        primitives match.
        """
        primitives = parse_description(description)
        if primitives:
            print(f"🔬 Physics-primitive composition from: \"{description}\"")
            print(f"   Primitives: {', '.join(primitives)}")
            print()

            scene = compose_from_primitives(primitives, title=description.title())

            # Generate narration using the normal pipeline
            smell_prose = self._get_smell_prose(scene)
            sight_prose = self._get_sight_prose(scene)
            sound_prose = self._get_sound_prose(scene)
            touch_prose = narrate_touch(scene, scene.environment)

            # If the DBs didn't produce prose, generate from primitive data
            if not smell_prose and scene.smell.get("compounds"):
                compounds = scene.smell["compounds"]
                mix = self.smell_db.mix(compounds)
                if mix["compounds"]:
                    try:
                        from smell_language import narrate_mix as smell_narrate_mix
                        smell_prose = smell_narrate_mix(mix, "moderate")
                    except ImportError:
                        notes = mix["dominant_notes"][:5] + mix["subtle_notes"][:3]
                        if notes:
                            smell_prose = f"The air carries notes of {', '.join(notes[:-1])}, and {notes[-1]}." if len(notes) > 1 else f"The air carries a note of {notes[0]}."
                if not smell_prose:
                    smell_prose = f"The air carries {', '.join(compounds[:5])}."

            if not sight_prose:
                sight_notes = scene.sight.get("notes", "")
                if sight_notes:
                    sight_prose = sight_notes

            if not sound_prose:
                sound_notes = scene.sound.get("notes", "")
                if sound_notes:
                    sound_prose = sound_notes

            woven = narrate_scene(scene, smell_prose, sight_prose, sound_prose, touch_prose)

            parts = [f"━━━ {scene.name} ━━━", f"    [{', '.join(primitives)}]", "", woven]

            # Walk positions
            if scene.positions:
                parts.append("")
                parts.append(self.walk_scene(scene))

            return "\n".join(parts)

        # No primitives matched — fall back to keyword matching
        return self.describe_from_text(description, narrate=narrate)

    def describe_from_text(self, description, narrate=False):
        """Auto-suggest components from a text description and compose a mindscape (legacy keyword matching)."""
        desc_lower = description.lower()
        keywords = set(desc_lower.replace(",", " ").replace(".", " ").split())

        # Keyword → component mapping tables
        light_keywords = {
            "neon": "neon_sign", "sunrise": "sunrise", "sunset": "golden_hour",
            "golden": "golden_hour", "moonlight": "moonlight", "moon": "moonlight",
            "candle": "candle", "candlelit": "candle", "fire": "fireplace",
            "fluorescent": "fluorescent_cool", "lamp": "oil_lamp", "dawn": "dawn_twilight",
            "dusk": "dusk_twilight", "starlight": "starlight", "stars": "starlight",
            "morning": "sunrise", "midday": "midday_sun", "noon": "midday_sun",
            "night": "neon_sign", "evening": "dusk_twilight", "bonfire": "bonfire",
            "torch": "torch", "halogen": "halogen_spot", "led": "warm_led",
            "overcast": "overcast", "cloudy": "overcast", "bright": "midday_sun",
            "dim": "candle", "dark": "moonlight",
        }
        material_keywords = {
            "asphalt": "wet_asphalt", "concrete": "concrete", "brick": "brick",
            "wood": "oak_wood", "wooden": "oak_wood", "stone": "stone",
            "marble": "marble", "glass": "clear_glass", "steel": "polished_steel",
            "cobblestone": "wet_cobblestone", "cobble": "wet_cobblestone",
            "sand": "sand", "sandy": "sand", "mud": "wet_mud", "muddy": "wet_mud",
            "leather": "leather", "velvet": "velvet", "silk": "silk",
            "copper": "copper", "gold": "gold", "chrome": "chrome",
            "tile": "ceramic_tile", "tiled": "ceramic_tile", "grass": "grass",
            "moss": "moss", "mossy": "moss", "puddle": "puddle", "puddles": "puddle",
            "wet": "wet_asphalt", "street": "wet_cobblestone", "road": "dry_asphalt",
        }
        atmosphere_keywords = {
            "fog": "light_fog", "foggy": "heavy_fog", "mist": "light_fog",
            "misty": "light_fog", "rain": "rain", "rainy": "rain",
            "snow": "snow", "snowy": "snow", "dust": "dust", "dusty": "dust",
            "smoke": "smoke", "smoky": "smoke", "haze": "light_haze",
            "hazy": "light_haze", "humid": "humidity", "clear": "clear",
            "storm": "rain", "stormy": "rain", "heavy-rain": "rain",
        }
        sound_keywords = {
            "rain": "rain_heavy", "rainy": "rain_heavy", "thunder": "thunder_distant",
            "wind": "wind_gentle", "windy": "wind_gusty", "waves": "waves_ocean",
            "ocean": "waves_ocean", "birds": "birdsong_dawn", "birdsong": "birdsong_dawn",
            "crickets": "crickets", "traffic": "traffic_ambient", "subway": "subway_train",
            "train": "train_on_tracks", "piano": "piano", "guitar": "guitar_acoustic",
            "fire": "fire_crackling", "crackling": "fire_crackling",
            "espresso": "espresso_machine", "coffee": "espresso_machine",
            "typing": "typing_keyboard", "clock": "clock_ticking",
            "bell": "church_bell", "bells": "church_bell", "chimes": "wind_chimes",
            "dripping": "dripping_water", "waterfall": "waterfall",
            "footsteps": "footsteps_concrete", "crowd": "crowd_murmur",
            "whisper": "whisper", "laughter": "laughter",
        }
        sound_env_keywords = {
            "street": "busy_street", "cathedral": "cathedral", "church": "church",
            "forest": "forest", "cave": "cave", "tunnel": "tunnel",
            "room": "small_room", "hall": "large_hall", "rooftop": "rooftop",
            "garage": "parking_garage", "library": "library", "kitchen": "kitchen",
            "bedroom": "bedroom", "field": "open_field", "outdoor": "open_field",
            "outside": "open_field", "indoor": "small_room", "inside": "small_room",
            "subway": "subway_platform", "station": "subway_platform",
            "stairwell": "stairwell", "car": "car_interior",
        }
        smell_keywords = {
            "coffee": "coffee-shop", "bakery": "bakery", "bread": "bakery",
            "forest": "forest", "ocean": "ocean", "sea": "ocean", "beach": "tropical-beach",
            "flower": "flower-garden", "flowers": "flower-garden", "garden": "flower-garden",
            "market": "night-market", "night-market": "night-market",
            "campfire": "campfire", "fire": "campfire", "bonfire": "campfire",
            "rain": "rainy-street", "rainy": "rainy-street", "petrichor": "forest-after-rain",
            "book": "old-bookshop", "books": "old-bookshop", "library": "library",
            "wine": "wine-cellar", "bar": "bar", "pub": "bar",
            "pizza": "pizza-place", "food": "night-market", "cooking": "night-market",
            "spice": "spice-market", "spices": "spice-market",
            "gas": "gas-station", "gasoline": "gas-station",
            "hospital": "hospital", "subway": "subway-station",
            "christmas": "christmas", "holiday": "christmas",
            "laundry": "fresh-laundry", "clean": "fresh-laundry",
            "tokyo": "night-market", "asian": "night-market",
            "autumn": "autumn-leaves", "fall": "autumn-leaves",
        }

        # Match
        light = material = atmosphere = sound_source = sound_env = smell_scene = None
        for kw in keywords:
            if not light and kw in light_keywords:
                light = light_keywords[kw]
            if not material and kw in material_keywords:
                material = material_keywords[kw]
            if not atmosphere and kw in atmosphere_keywords:
                atmosphere = atmosphere_keywords[kw]
            if not sound_source and kw in sound_keywords:
                sound_source = sound_keywords[kw]
            if not sound_env and kw in sound_env_keywords:
                sound_env = sound_env_keywords[kw]
            if not smell_scene and kw in smell_keywords:
                smell_scene = smell_keywords[kw]

        # Report what was auto-selected
        print("🔍 Auto-detected components from description:")
        print(f"   Description: \"{description}\"")
        if light: print(f"   💡 Light:       {light}")
        if material: print(f"   🧱 Material:    {material}")
        if atmosphere: print(f"   🌫️  Atmosphere:  {atmosphere}")
        if sound_source: print(f"   🔊 Sound:       {sound_source}")
        if sound_env: print(f"   🏛️  Sound env:   {sound_env}")
        if smell_scene: print(f"   👃 Smell scene: {smell_scene}")
        if not any([light, material, atmosphere, sound_source, sound_env, smell_scene]):
            print("   (no components matched — try more specific keywords)")
            print(f"\n   Tip: use --custom with explicit flags for full control.")
            return ""
        print("")

        return self.custom_compose(
            light=light, material=material, atmosphere=atmosphere,
            sound_source=sound_source, sound_env=sound_env,
            smell_scene=smell_scene,
            title=description.title(),
            narrate=narrate,
        )


def _print_custom_help(engine):
    """Print help for --custom mode showing available components."""
    print("🎨 Custom Mindscape Builder")
    print("=" * 50)
    print()
    print("Build a scene from individual sense components:")
    print()
    print("  python3 mindscape.py --custom \\")
    print("    --light neon_sign \\")
    print("    --material wet-asphalt \\")
    print("    --atmosphere rain \\")
    print("    --sound rain-heavy \\")
    print("    --sound-env busy_street \\")
    print("    --smell-scene night-market \\")
    print("    --title \"Rainy Tokyo Street\"")
    print()
    print("Or auto-compose from a description:")
    print()
    print("  python3 mindscape.py --custom --describe \"rainy tokyo street at night\"")
    print()
    print("Available components:")
    print()
    print("  💡 Lights:       ", ", ".join(x[0] for x in engine.sight_db.list_lights()))
    print("  🧱 Materials:    ", ", ".join(x[0] for x in engine.sight_db.list_materials()))
    print("  🌫️  Atmospheres:  ", ", ".join(x[0] for x in engine.sight_db.list_atmospheres()))
    print("  🔊 Sound sources:", ", ".join(x[0] for x in engine.sound_db.list_sources()))
    print("  🏛️  Sound envs:   ", ", ".join(x[0] for x in engine.sound_db.list_environments()))
    print("  👃 Smell scenes: ", ", ".join(engine.smell_db.list_scenes()))
    print()
    print("All flags are optional — specify any combination of senses.")
    print("Add --narrate for rich experiential prose.")


def main():
    parser = argparse.ArgumentParser(
        description="Mindscape Engine — multi-sensory scene experiences"
    )
    parser.add_argument("--scene", "-s", type=str, help="Scene to experience")
    parser.add_argument("--walk", "-w", action="store_true", help="Walk through the scene")
    parser.add_argument("--narrate", "-n", action="store_true", help="Rich experiential prose")
    parser.add_argument("--list", "-l", action="store_true", help="List available mindscapes")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    # Custom composition flags
    parser.add_argument("--custom", action="store_true", help="Build custom mindscape from components")
    parser.add_argument("--describe", type=str, help="Auto-compose from text description (use with --custom)")
    parser.add_argument("--light", type=str, help="Light source (custom mode)")
    parser.add_argument("--material", type=str, help="Material surface (custom mode)")
    parser.add_argument("--atmosphere", type=str, help="Atmospheric condition (custom mode)")
    parser.add_argument("--sound", type=str, dest="sound_source", help="Sound source (custom mode)")
    parser.add_argument("--sound-env", type=str, help="Sound environment (custom mode)")
    parser.add_argument("--smell-scene", type=str, help="Smell scene (custom mode)")
    parser.add_argument("--title", type=str, help="Scene title (custom mode)")
    parser.add_argument("--deep-position", type=int, default=0, help="Position index for single-position view (default: 0)")
    parser.add_argument("--time", type=str, choices=TimeState.TIMES,
                        help="Override time of day (dawn, morning, midday, afternoon, golden_hour, dusk, night, late_night)")
    args = parser.parse_args()

    engine = MindscapeEngine()

    if args.list:
        scenes = engine.list_scenes()
        if not scenes:
            print("No mindscapes found. Check data/mindscape_scenes/ directory.")
            return
        print("Available mindscapes:")
        for sid, name in scenes:
            print(f"  {sid:30s} {name}")
        return

    # Apply time override to engine if specified
    time_override = getattr(args, 'time', None)

    # Custom composition mode
    if args.custom:
        if args.describe is not None and args.describe.strip() == "":
            print("Error: --describe requires a non-empty description string.")
            print("Example: --custom --describe \"rainy tokyo street at night\"")
            return
        if args.describe:
            print(deep_generate_custom(engine, args.describe))
            return

        has_components = any([args.light, args.material, args.atmosphere,
                             args.sound_source, args.sound_env, args.smell_scene])
        if not has_components:
            _print_custom_help(engine)
            return

        result = engine.custom_compose(
            light=args.light,
            material=args.material,
            atmosphere=args.atmosphere,
            sound_source=args.sound_source,
            sound_env=args.sound_env,
            smell_scene=args.smell_scene,
            title=args.title,
            narrate=args.narrate,
        )
        print(result)
        return

    if not args.scene:
        parser.print_help()
        return

    scene = engine.find_scene(args.scene)
    if not scene:
        print(f"Scene '{args.scene}' not found. Use --list to see available scenes.")
        return

    # Apply --time override: propagate through environment
    if time_override:
        scene.environment.time_of_day = time_override
        # Apply temporal temperature offset
        profile = TimeState.get(time_override)
        # Adjust temperature from scene's base by the temporal offset
        base_temp = scene.environment.temperature_c
        scene.environment.temperature_c = base_temp + profile["temperature_offset_c"]
        print(f"⏰ Time override: {time_override}")
        print(f"   Temperature adjusted: {base_temp}°C → {scene.environment.temperature_c}°C")
        print(f"   Light: {profile['light_color_temp_K']}K, ambient level: {profile['ambient_light_level']}")
        print()

    if args.json:
        print(json.dumps(scene.to_dict(), indent=2))
        return

    if args.walk:
        print(deep_generate_walk(engine, scene))
        return

    print(deep_generate(engine, scene, args.deep_position))


if __name__ == "__main__":
    main()
