"""
sight_language.py — Experiential visual language layer.

Transforms visual descriptors (light quality, material appearance, atmosphere)
into evocative, sensory prose. Pure lookup/template system — no LLM, stdlib only.
"""

import random

# ─── Light Quality → Experiential Phrases ────────────────────────────────────

LIGHT_QUALITY_PHRASES = {
    "warm": [
        "warm light pooling like honey",
        "amber warmth settling on every surface",
        "that golden glow that forgives everything it touches",
    ],
    "cool": [
        "cool light draining warmth from the world",
        "a blue-tinged clarity, crisp and unsentimental",
        "cold light that reveals more than it flatters",
    ],
    "soft": [
        "light diffused to a gentle wash",
        "softness in the light — no hard edges, no harsh truths",
        "the kind of light that makes everything look like a memory",
    ],
    "harsh": [
        "hard light carving shadows with surgical precision",
        "unforgiving brightness exposing every crack and line",
        "light sharp enough to cut",
    ],
    "directional": [
        "light pouring from one direction, sculpting the world in relief",
        "angled light turning every surface into a story of highlight and shadow",
    ],
    "diffuse": [
        "light coming from everywhere and nowhere",
        "directionless illumination, flat and even, like the sky itself is glowing",
    ],
    "flickering": [
        "restless light, breathing with the flame",
        "shadows that dance and shift — nothing stays fixed",
        "the ancient rhythm of firelight, never the same twice",
    ],
    "steady": [
        "unwavering light, constant and reliable",
        "the electric steadiness of modern illumination",
    ],
    "dappled": [
        "coins of light scattered through the canopy",
        "light and shadow trading places with every breeze",
    ],
    "long-shadowed": [
        "shadows stretching to impossible lengths",
        "long shadows that make everything taller, more dramatic",
    ],
    "short-shadowed": [
        "shadows huddled tight beneath things, barely there",
    ],
    "shadowless": [
        "no shadows anywhere — the world flattened to pure surface",
    ],
    "silvery": [
        "silver light that turns the world monochrome",
        "moonlight-pale, everything rendered in blue and grey",
    ],
    "monochromatic": [
        "all color drained away, the world in a single hue",
    ],
    "intimate": [
        "the small light of close spaces",
        "light that draws the world in to arm's reach",
    ],
    "electric": [
        "neon-bright, buzzing with voltage",
        "the electric candy glow of artificial color",
    ],
    "colored": [
        "colored light bleeding its hue into everything it touches",
    ],
    "focused": [
        "a cone of light isolating one thing from the dark",
    ],
    "faint": [
        "barely enough light to distinguish shape from shadow",
    ],
    "low-angle": [
        "light raking in from low on the horizon, gilding every raised edge",
    ],
    "omnidirectional": [
        "light radiating outward in all directions from its source",
    ],
    "smoky": [
        "light tangled with smoke, diffused and layered",
    ],
    "pre-dawn": [
        "the grey light before color returns to the world",
    ],
    "fading": [
        "light dimming, the day letting go",
    ],
    "even": [
        "perfectly even illumination, every surface equally lit",
    ],
    "green-filtered": [
        "light sieved through green, chlorophyll-tinted",
    ],
    "shifting": [
        "light in constant motion, restless and alive",
    ],
    "warm-cool_gradient": [
        "warmth near the source fading to cool in the shadows",
    ],
    "clean": [
        "clean light, free of color cast",
    ],
    "flat": [
        "flat light that compresses depth to nothing",
    ],
    "alarming": [
        "urgent light that accelerates the pulse",
    ],
    "red": [
        "red light washing everything in blood-tones",
    ],
    "blue-green": [
        "that sick blue-green glow of discharge lamps",
    ],
}

# ─── Intensity Modifiers ─────────────────────────────────────────────────────

INTENSITY_PHRASES = {
    "dim": [
        "barely there — more suggestion than illumination",
        "so faint the eyes strain to find shape in the dark",
        "a whisper of light",
    ],
    "low": [
        "gentle, understated light",
        "enough to see by, not enough to see well",
    ],
    "moderate": [
        "comfortable brightness, neither too much nor too little",
        "a natural, easy level of light",
    ],
    "bright": [
        "brightness that fills the space completely",
        "strong light leaving no corner untouched",
    ],
    "intense": [
        "blazing, eye-narrowing brightness",
        "light so strong it bleaches color from the nearest surfaces",
    ],
    "blinding": [
        "too bright to look at — a white void where the source should be",
    ],
}

# ─── Shadow Character Phrases ────────────────────────────────────────────────

SHADOW_PHRASES = {
    "soft": "soft-edged shadows bleeding into the light",
    "hard": "razor-cut shadows, edges sharp enough to trace with a finger",
    "none": "no shadows at all — just flat, even brightness",
    "dappled": "shadows scattered like puzzle pieces through the light",
    "medium": "shadows with character but not cruelty",
}

SHADOW_COLOR_PHRASES = {
    "blue-purple": "shadows stained blue-violet, the cool complement to the warm light",
    "blue-violet": "blue-violet shadows pooling where the gold can't reach",
    "black": "absolute black shadows, voids cut from the scene",
    "blue": "blue shadows — the sky painting itself into every hollow",
    "blue-grey": "blue-grey shadows, cool and quiet",
    "dark": "deep, featureless dark in the shadows",
    "warm": "warm shadows — darker, yes, but still holding color",
    "warm-grey": "shadows tinged with warmth, never quite cold",
    "deep-warm": "shadows so warm they seem to glow with their own dark amber",
    "deep-black": "the deepest black in the hollows, fire's own shadow",
    "green-black": "shadows tinted green-black by the canopy above",
    "grey-green": "grey-green shadows, slightly sickly",
    "grey-blue": "cool grey-blue shadows",
    "grey": "neutral grey shadows",
    "none": "",
    "sign_color": "shadows tinted with the reflected color of the sign",
    "blue-grey": "blue-grey shadows",
}

SHADOW_LENGTH_PHRASES = {
    "very_long": "shadows stretching almost to the horizon",
    "long": "long shadows dragging eastward like taffy",
    "medium": "shadows of honest length, proportional and grounded",
    "short": "short shadows pooled close to their sources",
    "sharp": "sharp shadow edges cutting the ground",
    "dancing": "shadows dancing to the rhythm of the flame",
    "scattered": "shadows scattered in shifting patterns",
    "multiple": "multiple faint shadows overlapping from different sources",
    "none": "",
}

# ─── Material Appearance Under Light ─────────────────────────────────────────

LIGHT_ON_MATERIAL_VERBS = {
    "warm": [
        "bathes", "gilds", "warms", "honeyed", "turns golden",
        "pours amber across", "softens", "enriches",
    ],
    "cool": [
        "washes", "chills", "drains", "steels", "reveals",
        "strips warmth from", "sharpens",
    ],
    "dim": [
        "barely touches", "hints at", "suggests", "ghosts across",
        "traces the outline of",
    ],
    "neutral": [
        "illuminates", "renders", "shows", "presents",
        "reveals the true face of",
    ],
}

# ─── Color Shift Descriptions ────────────────────────────────────────────────

COLOR_SHIFT_PHRASES = {
    "warm_on_warm": [
        "the warm tones amplify — gold on gold, amber on amber, almost too rich",
        "warmth compounds, every warm surface blazing",
    ],
    "warm_on_cool": [
        "the cool surface resists the warm light, going neutral — neither warm nor cold",
        "warm light and cool surface negotiate a truce in muted tones",
    ],
    "cool_on_warm": [
        "the warm material fights the cool light, going strange — salmon, mauve, uncertain",
        "cool light drains the warmth, leaving something unsettled",
    ],
    "cool_on_cool": [
        "cool on cool — clinical, clean, stripped of all pretense",
        "the cool tones reinforce each other into icy clarity",
    ],
}

# ─── Reflectance Type Descriptions ───────────────────────────────────────────

REFLECTANCE_PHRASES = {
    "specular": [
        "mirror-bright, throwing the light source back in sharp points",
        "reflections precise enough to read by",
    ],
    "diffuse": [
        "absorbing light and returning it softened, scattered",
        "matte and even, the surface drinking light without giving back highlights",
    ],
    "mixed": [
        "part mirror, part matte — highlights sliding over a textured surface",
        "some light reflected sharply, the rest scattered into soft glow",
    ],
    "subsurface": [
        "light entering the surface and scattering within, glowing from the inside",
        "translucent warmth — light goes in and comes back changed, softened, scattered",
    ],
    "retroreflective": [
        "light falling in and vanishing — only the edges catch anything",
    ],
    "transmissive": [
        "light passing through, color saturating as it goes",
    ],
    "anisotropic": [
        "highlights stretched along the grain, directional and precise",
    ],
    "dynamic_specular": [
        "reflections shattered into dancing fragments by the moving surface",
    ],
    "complex_refractive": [
        "every droplet a tiny lens bending light in its own direction",
    ],
    "diffuse_transmissive": [
        "light scattered as it passes through — a soft, milky glow",
    ],
}

# ─── Atmosphere Effect Phrases ───────────────────────────────────────────────

ATMOSPHERE_EFFECT_PHRASES = {
    "scattering": {
        "rayleigh_only": "air crystal-clear, light traveling undisturbed",
        "mild_forward": "a soft veil over distance, edges slightly blurred",
        "strong_forward": "the air itself visible, catching and scattering light",
        "extreme_forward": "air thick as milk, light unable to travel more than arm's length",
        "moderate_forward": "light bending through the medium, softened in transit",
        "moderate_isotropic": "light scattered equally in all directions by suspended particles",
        "rayleigh_enhanced": "atmospheric scattering painting the sky in long-wavelength colors",
        "rayleigh_moderate": "moderate scattering warming the light as it travels",
        "none": "no scattering — light travels in straight lines from source to eye",
    },
    "contrast": {
        0.0: "full contrast — the sharpest difference between light and dark",
        0.1: "contrast barely softened",
        0.15: "a slight haze eating at the edges of far things",
        0.2: "moderate softening — details fading at distance",
        0.3: "contrast noticeably reduced — the scene flattening",
        0.4: "significant contrast loss — near and far blurring together",
        0.5: "half the contrast gone — the world in soft focus",
        0.6: "most contrast dissolved — shapes losing definition",
        0.9: "almost no contrast — everything the same pale tone",
        1.0: "total whiteout — no contrast survives",
    },
}

# ─── Mood Descriptors ────────────────────────────────────────────────────────

MOOD_PHRASES = {
    "nostalgic": "there's something remembered about this light",
    "cinematic": "the scene composes itself like a film still",
    "intimate": "the world shrinks to arm's reach",
    "ethereal": "everything slightly unreal, slightly beautiful",
    "clinical": "stripped of romance, honest to a fault",
    "noir": "high contrast, deep shadow, urban poetry",
    "cozy": "warmth enclosed, shelter made visible",
    "vast": "space opening outward in every direction",
    "melancholy": "a quiet sadness in the light itself",
    "dramatic": "light and shadow in active conversation",
    "peaceful": "stillness made visible",
    "mysterious": "more hidden than revealed",
    "enchanted": "ordinary things made extraordinary by the light",
    "industrial": "function over beauty, but beauty sneaking in anyway",
    "pristine": "untouched, clean, first-light-of-the-world perfect",
    "electric": "buzzing with artificial energy",
    "primal": "before electricity, before walls — the oldest light",
}

# ─── Scene Narration Transitions ─────────────────────────────────────────────

SCENE_TRANSITIONS = [
    "And then —",
    "Look closer:",
    "The eye travels:",
    "Everywhere you look,",
    "And underneath all of it,",
    "The details accumulate:",
    "Further in,",
    "Step back and see:",
    "At the edges,",
    "Notice this:",
]

SCENE_OPENERS = [
    "The light tells you everything before your eyes adjust.",
    "You see it before you understand it.",
    "The scene arranges itself around the light.",
    "First: the light. Everything else follows.",
    "Start with what the light is doing.",
]

COMPOSE_OPENERS = [
    "The light, the surface, the air between — all conspiring:",
    "Three things are happening at once.",
    "The physics is simple. The result is not.",
    "Light meets material through atmosphere:",
    "What you see is the conversation between light and surface, overheard through air.",
]

# ─── Narration Intensity ─────────────────────────────────────────────────────

NARRATION_INTENSITY = {
    "dim": {
        "prefix": [
            "In the near-dark,",
            "Barely visible —",
            "Straining to see:",
        ],
        "suffix": [
            "More felt than seen.",
            "The eyes reach for more and find only suggestion.",
        ],
    },
    "low": {
        "prefix": [
            "In soft, low light,",
            "Quietly lit —",
        ],
        "suffix": [
            "Gentle enough to miss if you're not looking.",
        ],
    },
    "moderate": {
        "prefix": [""],
        "suffix": [""],
    },
    "bright": {
        "prefix": [
            "In full, bright light,",
            "Brightly —",
        ],
        "suffix": [
            "Everything visible, nothing hidden.",
        ],
    },
    "intense": {
        "prefix": [
            "Under blazing light,",
            "Searing brightness —",
        ],
        "suffix": [
            "Almost too much to take in.",
            "The eyes narrow against it.",
        ],
    },
}

# ─── Combination Logic ───────────────────────────────────────────────────────


def _pick(lst, seed=None):
    if not lst:
        return ""
    if seed is not None:
        return lst[hash(str(seed)) % len(lst)]
    return random.choice(lst)


def _classify_light_warmth(light):
    """Classify a light source as warm, cool, or neutral."""
    qualities = light.get("quality", [])
    shift = light.get("color_bias", {}).get("neutral_shift", "neutral")
    if "warm" in qualities or shift == "warm":
        return "warm"
    if "cool" in qualities or shift == "cool":
        return "cool"
    return "neutral"


def _classify_material_warmth(material):
    """Classify a material's inherent warmth from its base color."""
    color = material.get("base_color", {}).get("primary", "")
    warm_words = ["warm", "orange", "red", "amber", "gold", "brown", "honey", "copper", "yellow"]
    cool_words = ["cool", "blue", "silver", "grey", "white", "ice", "steel"]
    color_lower = color.lower()
    for w in warm_words:
        if w in color_lower:
            return "warm"
    for w in cool_words:
        if w in color_lower:
            return "cool"
    return "neutral"


def get_light_interaction_key(light):
    """Get the appropriate light_interactions key for a light source."""
    warmth = _classify_light_warmth(light)
    intensity = light.get("intensity", "moderate")
    if intensity in ("dim", "low"):
        return "under_dim_light"
    if warmth == "warm":
        return "under_warm_light"
    if warmth == "cool":
        return "under_cool_light"
    return "under_warm_light"


def describe_light_qualities(light):
    """Generate prose phrases for a light source's qualities."""
    phrases = []
    for q in light.get("quality", []):
        q_lower = q.lower().replace("-", "_").replace(" ", "_")
        if q_lower in LIGHT_QUALITY_PHRASES:
            phrases.append(_pick(LIGHT_QUALITY_PHRASES[q_lower], seed=q))
    return phrases


def describe_light_intensity(light):
    """Return an intensity phrase for the light."""
    intensity = light.get("intensity", "moderate")
    if intensity in INTENSITY_PHRASES:
        return _pick(INTENSITY_PHRASES[intensity], seed=light.get("id"))
    return ""


def describe_shadow(light):
    """Generate shadow description from light's shadow_character."""
    sc = light.get("shadow_character", {})
    parts = []
    h = sc.get("hardness", "")
    if h and h in SHADOW_PHRASES:
        parts.append(SHADOW_PHRASES[h])
    c = sc.get("color", "")
    if c and c in SHADOW_COLOR_PHRASES and SHADOW_COLOR_PHRASES[c]:
        parts.append(SHADOW_COLOR_PHRASES[c])
    l = sc.get("length", "")
    if l and l in SHADOW_LENGTH_PHRASES and SHADOW_LENGTH_PHRASES[l]:
        parts.append(SHADOW_LENGTH_PHRASES[l])
    return parts


def describe_light_on_material(light, material):
    """Describe how a specific light interacts with a specific material."""
    key = get_light_interaction_key(light)
    interactions = material.get("light_interactions", {})
    if key in interactions:
        return interactions[key]
    # Fallback
    for fallback_key in ["under_warm_light", "under_cool_light", "under_dim_light"]:
        if fallback_key in interactions:
            return interactions[fallback_key]
    return ""


def describe_color_shift(light, material):
    """Describe the color interaction between light and material."""
    lw = _classify_light_warmth(light)
    mw = _classify_material_warmth(material)
    if lw == "neutral":
        lw = "warm"  # neutral defaults to warm path
    if mw == "neutral":
        mw = "warm"
    key = f"{lw}_on_{mw}"
    if key in COLOR_SHIFT_PHRASES:
        return _pick(COLOR_SHIFT_PHRASES[key], seed=f"{light.get('id')}_{material.get('id')}")
    return ""


def describe_reflectance(material):
    """Describe the material's reflectance character."""
    rtype = material.get("reflectance", {}).get("type", "diffuse")
    if rtype in REFLECTANCE_PHRASES:
        return _pick(REFLECTANCE_PHRASES[rtype], seed=material.get("id"))
    return ""


def describe_atmosphere_effect(atmosphere, light=None):
    """Describe how atmosphere modifies the scene."""
    parts = []
    mods = atmosphere.get("light_modifications", {})

    scattering = mods.get("scattering", "")
    if scattering in ATMOSPHERE_EFFECT_PHRASES["scattering"]:
        parts.append(ATMOSPHERE_EFFECT_PHRASES["scattering"][scattering])

    contrast = mods.get("contrast_reduction", 0)
    # Find the closest contrast key
    contrast_keys = sorted(ATMOSPHERE_EFFECT_PHRASES["contrast"].keys())
    closest = min(contrast_keys, key=lambda k: abs(k - contrast))
    parts.append(ATMOSPHERE_EFFECT_PHRASES["contrast"][closest])

    if mods.get("halo_around_lights"):
        parts.append("every light source wears a halo, its edges bled into the surrounding air")

    # Add atmosphere-specific light color effect
    if light:
        warmth = _classify_light_warmth(light)
        ce = atmosphere.get("color_effect", {})
        if warmth == "warm" and "warm_light_response" in ce:
            parts.append(ce["warm_light_response"])
        elif warmth == "cool" and "cool_light_response" in ce:
            parts.append(ce["cool_light_response"])
        elif "daylight_response" in ce:
            parts.append(ce["daylight_response"])

    return parts


def narrate_light(light):
    """Full prose narration of a light source."""
    parts = []
    name = light.get("name", "Unknown light")
    exp = light.get("experiential", {})

    parts.append(f"✦ {name}")
    parts.append("")

    # Feel
    feel = exp.get("feel", "")
    if feel:
        parts.append(f"The feeling: {feel}.")
    parts.append("")

    # Prose fragments
    frags = exp.get("prose_fragments", [])
    if frags:
        parts.append(" ".join(f.capitalize() if not f[0].isupper() else f for f in frags[:2]) + ".")

    # Quality phrases
    quality_phrases = describe_light_qualities(light)
    if quality_phrases:
        parts.append(" ".join(quality_phrases[:3]) + ".")

    # Shadow
    shadow_parts = describe_shadow(light)
    if shadow_parts:
        parts.append(" ".join(shadow_parts) + ".")

    # Intensity
    ip = describe_light_intensity(light)
    if ip:
        parts.append(ip + ".")

    return "\n".join(parts)


def narrate_material(material):
    """Full prose narration of a material under neutral light."""
    parts = []
    name = material.get("name", "Unknown material")
    exp = material.get("experiential", {})

    parts.append(f"✦ {name}")
    parts.append("")

    frags = exp.get("prose_fragments", [])
    if frags:
        parts.append(" ".join(frags[:2]) + ".")

    ref = describe_reflectance(material)
    if ref:
        parts.append(ref + ".")

    # Texture
    tex = material.get("texture", {}).get("visual", [])
    if tex:
        parts.append(f"To the eye: {', '.join(tex)}.")

    return "\n".join(parts)


def narrate_atmosphere(atmosphere):
    """Full prose narration of an atmospheric condition."""
    parts = []
    name = atmosphere.get("name", "Unknown atmosphere")
    exp = atmosphere.get("experiential", {})

    parts.append(f"✦ {name}")
    parts.append("")

    feel = exp.get("feel", "")
    if feel:
        parts.append(f"The feeling: {feel}.")
    parts.append("")

    frags = exp.get("prose_fragments", [])
    if frags:
        parts.append(" ".join(frags) + ".")

    vis = atmosphere.get("visibility_m")
    if vis:
        parts.append(f"Visibility: {vis}m.")

    return "\n".join(parts)


def narrate_composition(light, material, atmosphere):
    """
    Full prose narration of a light + material + atmosphere combination.
    Produces flowing, unified paragraphs — not bullet-point fragments.
    """
    light_name = light.get("name", "the light")
    mat_name = material.get("name", "the surface")
    atm_name = atmosphere.get("name", "the air")

    # Gather raw material
    light_exp = light.get("experiential", {})
    light_feel = light_exp.get("feel", "")
    light_frags = light_exp.get("prose_fragments", [])
    light_frag = _pick(light_frags, seed=light.get("id")) if light_frags else ""

    interaction = describe_light_on_material(light, material)
    mat_exp = material.get("experiential", {})
    mat_frags = mat_exp.get("prose_fragments", [])
    mat_frag = _pick(mat_frags, seed=material.get("id")) if mat_frags else ""

    ref = describe_reflectance(material)
    shadow_parts = describe_shadow(light)
    quality_phrases = describe_light_qualities(light)

    atm_effects = describe_atmosphere_effect(atmosphere, light)
    atm_exp = atmosphere.get("experiential", {})
    atm_feel = atm_exp.get("feel", "")
    atm_frags = atm_exp.get("prose_fragments", [])
    atm_frag = _pick(atm_frags, seed=atmosphere.get("id")) if atm_frags else ""

    # Build unified paragraphs
    # --- Paragraph 1: Light meets material ---
    p1_sentences = []
    if light_frag:
        p1_sentences.append(_capitalize_first(light_frag))
    if quality_phrases:
        p1_sentences.append(_capitalize_first(_pick(quality_phrases, seed=mat_name)))
    if interaction:
        p1_sentences.append(f"On the {mat_name.lower()}, {_lower_first(interaction)}")
    if mat_frag:
        p1_sentences.append(_capitalize_first(mat_frag))
    if ref:
        # Weave reflectance into the material sentence rather than isolated
        p1_sentences.append(f"The surface itself: {_lower_first(ref)}")

    # --- Paragraph 2: Shadow and atmosphere ---
    p2_sentences = []
    if shadow_parts:
        p2_sentences.append(_capitalize_first(shadow_parts[0]))
        if len(shadow_parts) > 1:
            p2_sentences.append(_capitalize_first(shadow_parts[1]))
    if atm_frag:
        p2_sentences.append(_capitalize_first(atm_frag))
    for e in atm_effects[:2]:
        if e:
            p2_sentences.append(_capitalize_first(e))

    # --- Assemble ---
    paragraphs = []
    if p1_sentences:
        paragraphs.append(_join_sentences(p1_sentences))
    if p2_sentences:
        paragraphs.append(_join_sentences(p2_sentences))

    return "\n\n".join(paragraphs)


def _capitalize_first(s):
    """Ensure first character is uppercase."""
    s = s.strip()
    if not s:
        return s
    return s[0].upper() + s[1:]


def _lower_first(s):
    """Lowercase the first character."""
    s = s.strip()
    if not s:
        return s
    return s[0].lower() + s[1:]


def _join_sentences(sentences):
    """Join sentence fragments into a flowing paragraph with proper punctuation."""
    result = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        # Ensure sentence ends with punctuation
        if s[-1] not in ".!?—":
            s += "."
        result.append(s)
    return " ".join(result)


def narrate_walk(scene):
    """
    Narrate a spatial walk through a scene with multiple positions.
    Returns flowing prose describing how light/materials/atmosphere change.
    """
    name = scene.get("name", "Unknown Scene")
    walk = scene.get("walk", [])
    if not walk:
        return f"✦ {name}\n\n(This scene does not have a spatial walk defined.)"

    parts = []
    parts.append(f"✦ Walking through: {name}")
    parts.append("")

    for i, step in enumerate(walk):
        position = step.get("position", f"position {i+1}")
        prose = step.get("prose", "")
        parts.append(f"— {position.title()} —")
        parts.append("")
        parts.append(prose)
        if i < len(walk) - 1:
            parts.append("")

    return "\n".join(parts)


def narrate_scene(scene, lights_data=None, materials_data=None, atmosphere_data=None):
    """
    Narrate a pre-composed scene. Uses the scene's own prose if available,
    or builds from components.
    """
    parts = []
    name = scene.get("name", "Unknown Scene")
    parts.append(f"✦ {name}")
    parts.append("")

    prose = scene.get("prose", "")
    if prose:
        parts.append(prose)
    else:
        parts.append(_pick(SCENE_OPENERS))
        parts.append("")
        # No pre-composed prose — add mood as a coda
        mood = scene.get("mood", [])
        if mood:
            mood_phrases = [MOOD_PHRASES.get(m, m) for m in mood if m in MOOD_PHRASES]
            if mood_phrases:
                parts.append(_pick(mood_phrases, seed=name) + ".")
        else:
            parts.append("[Scene composition from components would appear here.]")

    return "\n".join(parts)
