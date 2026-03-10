"""
sound_language.py — Experiential sound language layer.

Transforms sound descriptors into evocative, temporal prose.
Key differentiator from sight: sound unfolds in TIME (onset → sustain → decay).
Pure lookup/template system — no LLM, stdlib only.
"""

import random

# ─── Descriptor → Experiential Phrases ───────────────────────────────────────

DESCRIPTOR_PHRASES = {
    "rumble": ["a low, felt vibration", "bass that lives in the chest, not the ears", "the ground remembering thunder"],
    "rumbling": ["a low, rolling vibration", "something heavy turning over underground", "bass you feel in your molars"],
    "crackling": ["tiny explosions in rapid succession", "the sound of something surrendering to heat", "a percussive whisper of breaking things"],
    "hissing": ["air escaping through a narrow gap", "the sharp breath of pressurized things", "a continuous sibilant whisper"],
    "tinkling": ["bright, scattered notes like tiny bells", "small bright collisions", "a shower of metallic light"],
    "roar": ["a wall of sound with no individual parts", "volume without detail", "the sonic equivalent of a fist"],
    "patter": ["a hundred soft taps", "percussion played with felt mallets", "the gentlest possible bombardment"],
    "clicking": ["sharp, discrete, metronomic", "the smallest possible percussion", "binary sound — on, off, on, off"],
    "humming": ["a continuous, felt tone", "the baseline drone of machinery at rest", "vibration just barely promoted to sound"],
    "chirping": ["bright, rhythmic pulses", "nature's morse code", "small, insistent, impossible to ignore"],
    "whooshing": ["air displaced in a rush", "the sound of something passing", "movement made audible"],
    "banging": ["impact without apology", "a blunt announcement", "force meeting surface"],
    "droning": ["a sound that forgets to stop", "continuous, toneless, omnipresent", "the acoustic wallpaper of machines"],
    "wailing": ["a sound that climbs and falls", "distress given a frequency", "the voice of urgency"],
    "screeching": ["high-frequency protest", "metal objecting to metal", "a sound that triggers the flinch reflex"],
    "bubbling": ["liquid negotiating with air", "the voice of water at work", "air escaping upward through liquid"],
    "popping": ["small, sharp detonations", "contained bursts", "the percussion of things giving way"],
    "creaking": ["slow protest from wood or metal", "the voice of strain", "a joint that needs oil or mercy"],
    "jingling": ["a chaotic scatter of bright tones", "tiny metal things in collision", "a pocket orchestra"],
    "sloshing": ["liquid shifting in a container", "water looking for its level", "the lazy sound of captured liquid"],
    "gurgling": ["liquid finding its voice", "water with opinions", "the throat-sound of plumbing"],
    "tapping": ["precise, light impacts", "a fingertip's percussion", "the smallest intentional sound"],
    "booming": ["bass that fills the space", "low-frequency authority", "the sound of something large happening"],
    "singing": ["a sustained, melodic tone", "vibration refined into beauty", "the sound of something resonating with purpose"],
    "whirring": ["rotation made audible", "the hum of things spinning", "mechanical patience in circular motion"],
    "buzzing": ["vibration at insect frequency", "an electric tremor", "the sound of energy looking for ground"],
    "crunching": ["compression with texture", "the destruction of small structures", "the sound of things being rearranged underfoot"],
    "splashing": ["liquid meeting surface with force", "water's applause", "impact translated into spray"],
    "whistling": ["air forced through a narrow gap", "wind finding a voice", "a tube of moving air"],
    "clapping": ["skin meeting skin at speed", "the simplest percussion", "approval made percussive"],
    "murmuring": ["voices blurred into texture", "language reduced to tone", "the warm wash of human presence"],
    "rattling": ["loose things shaking", "a container of small complaints", "vibration exposing every loose joint"],
    "sizzling": ["moisture meeting heat", "the Maillard reaction, audible", "the sound of cooking at proper temperature"],
    "thumping": ["a dull, heavy impact", "bass percussion felt in the floor", "weight landing on surface"],
    "bright": ["a sound that catches attention", "clarity that cuts through", "the audio equivalent of a flash"],
    "metallic": ["the ring of shaped metal", "hard, bright, and sustaining", "the voice of forged things"],
    "percussive": ["impact as communication", "rhythm through collision", "the original music"],
    "resonant": ["a sound that lingers and blooms", "the vibrating aftermath", "the note the object was born to sing"],
    "sharp": ["a quick, defined edge", "no ambiguity in the attack", "precision in sound form"],
    "soft": ["sound at whisper volume", "gentleness made audible", "barely above the threshold of hearing"],
    "deep": ["low enough to feel", "bass that speaks to the bones", "frequency below thought"],
    "warm": ["round, full, inviting sound", "acoustic comfort", "the tonal equivalent of a blanket"],
    "piercing": ["a frequency that demands attention", "sound that bypasses the ears and hits the nerves", "sharpness without mercy"],
}

# ─── Temporal Narration (the key sound differentiator) ───────────────────────

ONSET_PHRASES = [
    "It begins with {detail}.",
    "First comes {detail}.",
    "The sound arrives as {detail}.",
    "It starts — {detail}.",
    "Before anything else: {detail}.",
    "The first thing you hear is {detail}.",
    "It announces itself: {detail}.",
]

SUSTAIN_PHRASES = [
    "It settles into {detail}.",
    "Underneath, the constant {detail}.",
    "The sound finds its rhythm: {detail}.",
    "Then it sustains — {detail}.",
    "The body of the sound: {detail}.",
    "What remains is {detail}.",
    "It holds there — {detail}.",
]

DECAY_PHRASES = [
    "It fades to {detail}.",
    "The last echoes: {detail}.",
    "As it dies away, {detail}.",
    "What's left is {detail}.",
    "The sound releases: {detail}.",
    "Then, gradually — {detail}.",
    "It lets go: {detail}.",
]

# ─── Distance Effects ────────────────────────────────────────────────────────

DISTANCE_EFFECTS = {
    "near": {
        "quality": "crisp, detailed, present",
        "phrases": [
            "close enough to feel the air move",
            "every detail sharp and immediate",
            "the sound is right here — intimate, unfiltered",
            "near enough to hear the texture inside the sound",
            "present and undiminished, the full frequency range intact",
        ],
        "modifier": "The sound is close — {detail}",
    },
    "mid": {
        "quality": "blended, contextual, placed",
        "phrases": [
            "at a comfortable distance, blended with the space",
            "present but not dominating — part of the scene, not the whole",
            "the details soften, the overall character strengthens",
            "close enough to identify, far enough to coexist with other sounds",
            "the room has started to color the sound",
        ],
        "modifier": "From across the space — {detail}",
    },
    "far": {
        "quality": "washed, muffled, atmospheric",
        "phrases": [
            "distance has washed away the detail, leaving only the shape",
            "muffled by air and walls, reduced to its essence",
            "far enough that it becomes atmosphere rather than event",
            "the high frequencies stripped away by distance, only the low body remaining",
            "a suggestion more than a presence",
        ],
        "modifier": "From far away — {detail}",
    },
}

# ─── Environment Interaction ─────────────────────────────────────────────────

REVERB_PHRASES = {
    "dry": [
        "the sound dies where it's made — no reflections, no echo, just the direct signal",
        "acoustically dead — the room absorbs everything",
        "bone-dry. Every sound exists only once.",
    ],
    "intimate": [
        "close walls return the sound quickly, adding warmth without echo",
        "the room is small enough to hold the sound gently",
        "a brief, warm reflection — the acoustic signature of small spaces",
    ],
    "echoey": [
        "the sound bounces back from every hard surface, multiplied and smeared",
        "echoes layering on echoes — the space won't let the sound die",
        "each sound repeated by the walls, the original blurring into its reflections",
    ],
    "reverberant": [
        "the sound blooms and lingers, the space adding its own long, shimmering tail",
        "reverb stretching every sound into something larger than itself",
        "the room sings along — every note sustained by the architecture",
    ],
    "cavernous": [
        "sound transforms here — a single note becomes a chord of reflections layered across seconds",
        "the reverb is so long that phrases overlap themselves, the space composing its own harmonies",
        "every sound echoes for seconds, the stone refusing to let anything go",
    ],
    "absorptive": [
        "the space swallows sound — no echoes, no reflections, just direct signal and silence",
        "acoustically muffled, the environment eating reflections before they can form",
        "dead air — the sound has nowhere to go and nothing to bounce off",
    ],
    "hushed": [
        "the space itself seems to demand quiet — every surface absorbing, dampening, hushing",
        "acoustically padded — the room conspires to keep things soft",
        "sound is rationed here, each noise louder than it should be against the enforced quiet",
    ],
    "warm": [
        "a flattering acoustic — the room adds richness without blur",
        "warmth in the reverb, the space enhancing rather than distorting",
        "the reflections add body, the way a good room makes a voice sound better",
    ],
    "bright": [
        "hard surfaces making everything sharp and present",
        "the room adds brightness — high frequencies reflected and amplified",
        "an active, lively acoustic that flatters nothing but reveals everything",
    ],
    "open": [
        "sound escapes upward into open air — no ceiling to return it",
        "half the sound leaves and never comes back",
        "the acoustic of outdoors: direct sound only, with distance as the only modifier",
    ],
    "dead": [
        "engineered silence — every reflection killed, every resonance trapped",
        "the deadest acoustic humans can build — no room sound, just the source",
        "sound stripped naked, examined without the flattery of any room",
    ],
    "muffled": [
        "everything attenuated, highs stripped away, the world heard through a blanket",
        "the medium itself filters the sound — thick, directionless, bass-heavy",
        "muffled and strange, the usual acoustic rules suspended",
    ],
    "noisy": [
        "the ambient noise floor is high — everything competes to be heard",
        "a wall of background sound that every other sound must fight through",
        "loud by default — conversation requires raised voices",
    ],
}

RT60_PHRASES = {
    0.0: "sound dies instantly — no reverb at all",
    0.1: "the briefest hint of room — sound barely lingers",
    0.2: "dry and controlled — the room stays out of the way",
    0.3: "a short, intimate reflection — the room's smallest contribution",
    0.4: "just enough reverb to soften edges",
    0.5: "a hint of space in the sound",
    0.6: "the room beginning to assert itself",
    1.0: "a noticeable tail — sounds linger and overlap slightly",
    1.5: "generous reverb — the room is an active participant",
    2.0: "long reverb — every sound trails a shimmer of reflections",
    2.5: "the space stretches sound across seconds",
    3.0: "each sound echoes and re-echoes, the room holding onto everything",
    3.5: "extreme reverb — sounds overlap themselves, phrases blur into ambient",
    5.0: "five seconds of reverb — a single note becomes a self-harmonizing chord",
}

# ─── Layer Placement (foreground/midground/background) ───────────────────────

LAYER_PLACEMENT = {
    "foreground": [
        "In the foreground:",
        "Closest to you:",
        "Dominating the soundscape:",
        "The primary sound:",
        "Front and center:",
    ],
    "midground": [  # mapped from "ambient" role too
        "In the middle distance:",
        "Filling the space around:",
        "The ambient layer:",
        "Woven through the scene:",
        "Neither near nor far:",
    ],
    "background": [
        "Behind everything:",
        "At the edges of hearing:",
        "Underneath it all:",
        "The foundation layer:",
        "Almost beneath notice:",
    ],
}

ROLE_TO_LAYER = {
    "foreground": "foreground",
    "ambient": "midground",
    "background": "background",
}

# ─── Scene Narration Transitions ─────────────────────────────────────────────

SCENE_TRANSITIONS = [
    "And then —",
    "Listen closer:",
    "The ear travels:",
    "Layered beneath that,",
    "And underneath all of it,",
    "The sounds accumulate:",
    "Further away,",
    "Step back and hear:",
    "At the edges of hearing,",
    "Notice this:",
    "Woven through it,",
    "Meanwhile,",
]

SCENE_OPENERS = [
    "Close your eyes. Listen.",
    "The soundscape arranges itself in layers.",
    "Every sound has a place in the mix.",
    "First: the silence. Then what fills it.",
    "Start with what's closest. Work outward.",
    "The world is talking. Here's what it's saying.",
]

COMPOSE_OPENERS = [
    "A sound, a space, and the distance between you:",
    "Three elements conspire — source, environment, distance:",
    "The sound arrives, shaped by the space it crosses:",
    "Listen to how the room changes what you hear:",
    "What was made, how far it traveled, and what the space did to it:",
]

WALK_TRANSITIONS = [
    "You move. The mix shifts.",
    "A few steps change everything.",
    "New position, new soundscape.",
    "The same sounds, rearranged by distance.",
    "Your ears recalibrate.",
]

# ─── Temporal Pattern Descriptions ───────────────────────────────────────────

TEMPORAL_PATTERNS = {
    "continuous": "a sound that doesn't stop — a sustained presence, constant and unwavering",
    "rhythmic": "a sound with a pulse — repeating, patterned, metronomic or organic",
    "impulse": "a single event — sudden, brief, then gone, leaving only its echo",
    "decay": "a sound that starts strong and fades — all attack, long release",
}

# ─── Loudness Context ────────────────────────────────────────────────────────

LOUDNESS_CONTEXT = {
    (0, 20): "barely above silence — a sound you have to lean into",
    (20, 35): "quiet — the volume of intimate spaces and late hours",
    (35, 50): "moderate — present without demanding attention",
    (50, 65): "clearly audible — a sound that holds its own in a room",
    (65, 80): "loud — conversation becomes difficult, attention commanded",
    (80, 95): "very loud — the body starts to object, the ears push back",
    (95, 130): "overwhelming — pain threshold territory, the world reduced to this one sound",
}


# ─── Core Functions ──────────────────────────────────────────────────────────

def _pick(lst, seed=None):
    if not lst:
        return ""
    if seed is not None:
        return lst[hash(str(seed)) % len(lst)]
    return random.choice(lst)


def _capitalize(s):
    s = s.strip()
    return s[0].upper() + s[1:] if s else s


def _lower(s):
    s = s.strip()
    return s[0].lower() + s[1:] if s else s


def _join_sentences(sentences):
    result = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if s[-1] not in ".!?—:":
            s += "."
        result.append(s)
    return " ".join(result)


def get_loudness_phrase(db_level):
    """Get a contextual description for a dB level."""
    for (lo, hi), phrase in LOUDNESS_CONTEXT.items():
        if lo <= db_level < hi:
            return phrase
    return "at extreme volume"


def get_descriptor_phrases(descriptors, limit=3):
    """Get experiential phrases for a list of descriptors."""
    phrases = []
    for d in descriptors:
        d_key = d.lower().replace("-", "_").replace(" ", "_")
        if d_key in DESCRIPTOR_PHRASES:
            phrases.append(_pick(DESCRIPTOR_PHRASES[d_key], seed=d))
        if len(phrases) >= limit:
            break
    return phrases


def get_distance_description(distance, source_name=None):
    """Get description of how distance affects the sound."""
    dist = DISTANCE_EFFECTS.get(distance, DISTANCE_EFFECTS["mid"])
    phrase = _pick(dist["phrases"], seed=source_name or distance)
    return phrase


def get_reverb_description(environment):
    """Get description of how the environment shapes sound."""
    char = environment.get("character", "dry")
    if char in REVERB_PHRASES:
        return _pick(REVERB_PHRASES[char], seed=environment.get("id"))
    return ""


def get_rt60_description(rt60):
    """Get description for a specific RT60 value."""
    keys = sorted(RT60_PHRASES.keys())
    closest = min(keys, key=lambda k: abs(k - rt60))
    return RT60_PHRASES[closest]


# ─── Narration Functions ─────────────────────────────────────────────────────

def narrate_source(source):
    """Full temporal prose narration of a sound source."""
    parts = []
    name = source.get("name", "Unknown Sound")
    parts.append(f"🔊 {name}")
    parts.append("")

    # Feel
    exp = source.get("experiential", {})
    feel = exp.get("feel", "")
    if feel:
        parts.append(f"The feeling: {feel}.")
        parts.append("")

    # Temporal arc — the key differentiator
    onset = source.get("onset", "")
    sustain = source.get("sustain", "")
    decay = source.get("decay", "")

    if onset:
        template = _pick(ONSET_PHRASES, seed=source.get("id"))
        parts.append(template.format(detail=_lower(onset)))
        parts.append("")

    if sustain:
        template = _pick(SUSTAIN_PHRASES, seed=name)
        parts.append(template.format(detail=_lower(sustain)))
        parts.append("")

    if decay:
        template = _pick(DECAY_PHRASES, seed=f"{name}_decay")
        parts.append(template.format(detail=_lower(decay)))
        parts.append("")

    # Prose fragments
    frags = exp.get("prose_fragments", [])
    if frags:
        parts.append(_join_sentences([_capitalize(f) for f in frags[:2]]))

    return "\n".join(parts)


def narrate_environment(environment):
    """Full prose narration of an acoustic environment."""
    parts = []
    name = environment.get("name", "Unknown Environment")
    parts.append(f"🏛️ {name}")
    parts.append("")

    exp = environment.get("experiential", {})
    feel = exp.get("feel", "")
    if feel:
        parts.append(f"The feeling: {feel}.")
        parts.append("")

    # Reverb character
    reverb_desc = get_reverb_description(environment)
    if reverb_desc:
        parts.append(_capitalize(reverb_desc) + ".")
        parts.append("")

    # RT60
    rt60 = environment.get("rt60", 0)
    rt60_desc = get_rt60_description(rt60)
    parts.append(f"Reverb time: {rt60}s — {rt60_desc}.")
    parts.append("")

    # Absorption
    absorption = environment.get("absorption", "")
    if absorption:
        parts.append(absorption)
        parts.append("")

    # Prose fragments
    frags = exp.get("prose_fragments", [])
    if frags:
        for frag in frags:
            parts.append(frag)

    return "\n".join(parts)


def narrate_composition(source, environment, distance):
    """Narrate source + environment + distance as flowing prose."""
    parts = []
    src_name = source.get("name", "the sound")
    env_name = environment.get("name", "the space")
    dist_key = distance if distance in DISTANCE_EFFECTS else "mid"

    parts.append(_pick(COMPOSE_OPENERS, seed=f"{src_name}_{env_name}"))
    parts.append("")

    # Paragraph 1: The source and its temporal arc
    onset = source.get("onset", "")
    sustain = source.get("sustain", "")
    decay = source.get("decay", "")

    p1 = []
    if onset:
        p1.append(_capitalize(onset))
    if sustain:
        p1.append(_capitalize(sustain))
    if p1:
        parts.append(_join_sentences(p1))
        parts.append("")

    # Paragraph 2: Distance and environment interaction
    p2 = []
    dist_phrase = get_distance_description(dist_key, src_name)
    p2.append(_capitalize(dist_phrase))

    reverb_desc = get_reverb_description(environment)
    if reverb_desc:
        p2.append(f"The {env_name.lower()} shapes what arrives: {_lower(reverb_desc)}")

    rt60 = environment.get("rt60", 0)
    if rt60 > 1.0:
        rt60_desc = get_rt60_description(rt60)
        p2.append(f"With {rt60}s of reverb — {rt60_desc}")

    parts.append(_join_sentences(p2))
    parts.append("")

    # Paragraph 3: Decay through space
    p3 = []
    if decay:
        p3.append(_capitalize(decay))

    env_frags = environment.get("experiential", {}).get("prose_fragments", [])
    if env_frags:
        p3.append(_pick(env_frags, seed=src_name))

    if p3:
        parts.append(_join_sentences(p3))

    return "\n".join(parts)


def narrate_scene(scene, sources_db=None):
    """Narrate a pre-composed scene with temporal and spatial layering."""
    parts = []
    name = scene.get("name", "Unknown Scene")
    parts.append(f"🎧 {name}")
    parts.append("")

    prose = scene.get("prose", "")
    if prose:
        parts.append(prose)
    else:
        parts.append(_pick(SCENE_OPENERS, seed=name))
        parts.append("")

        # Build from layers
        layers = scene.get("layers", [])
        if layers and sources_db:
            for i, layer in enumerate(layers):
                src = sources_db.get(layer.get("source"))
                if not src:
                    continue
                role = layer.get("role", "ambient")
                dist = layer.get("distance", "mid")
                note = layer.get("note", "")

                lyr = ROLE_TO_LAYER.get(role, "midground")
                placement = _pick(LAYER_PLACEMENT[lyr], seed=f"{name}_{i}")

                desc_parts = []
                desc_parts.append(f"{src['name']}")
                if note:
                    desc_parts.append(f"— {note}")
                dist_phrase = _pick(DISTANCE_EFFECTS[dist]["phrases"], seed=src["id"])
                desc_parts.append(f"({dist_phrase})")

                parts.append(f"{placement} {' '.join(desc_parts)}.")
                if i < len(layers) - 1:
                    parts.append("")

    # Mood coda
    mood = scene.get("mood", [])
    if mood:
        parts.append("")
        parts.append(f"The mood: {', '.join(mood)}.")

    return "\n".join(parts)


def narrate_walk(scene, sources_db=None):
    """Narrate a spatial walk through a scene."""
    name = scene.get("name", "Unknown Scene")
    walk = scene.get("walk", [])
    if not walk:
        return f"🎧 {name}\n\n(This scene does not have spatial walk data.)"

    parts = []
    parts.append(f"🎧 Walking through: {name}")
    parts.append("")

    for i, step in enumerate(walk):
        position = step.get("position", f"position {i+1}")
        prose = step.get("prose", "")
        parts.append(f"— {position.title()} —")
        parts.append("")
        parts.append(prose)
        if i < len(walk) - 1:
            parts.append("")
            parts.append(_pick(WALK_TRANSITIONS, seed=f"{name}_{i}"))
            parts.append("")

    return "\n".join(parts)


def narrate_scene_rich(scene, sources_db=None):
    """
    Enhanced scene narration that weaves temporal arcs and spatial layering
    into flowing prose. Used when --narrate is combined with --scene.
    Falls back to the scene's own prose if available (it's usually excellent).
    """
    parts = []
    name = scene.get("name", "Unknown Scene")
    parts.append(f"🎧 {name}")
    parts.append("")

    prose = scene.get("prose", "")
    if prose:
        # The hand-written prose in scenes is top quality — use it
        parts.append(prose)
    else:
        parts.append(_pick(SCENE_OPENERS, seed=name))

    # Add temporal dimension if we have source data
    layers = scene.get("layers", [])
    if layers and sources_db:
        parts.append("")
        parts.append("— The Temporal Arc —")
        parts.append("")

        # Onset phase: what you hear first
        onset_parts = []
        for layer in layers:
            src = sources_db.get(layer.get("source"))
            if src and layer.get("role") == "foreground":
                onset = src.get("onset", "")
                if onset:
                    onset_parts.append(f"{src['name']}: {_lower(onset)}")

        if onset_parts:
            joined = " ".join(onset_parts[:2])
            if joined[-1] not in ".!?—":
                joined += "."
            parts.append("The scene opens: " + joined)
            parts.append("")

        # Sustain: the steady state
        sustain_parts = []
        for layer in layers:
            src = sources_db.get(layer.get("source"))
            if src and layer.get("role") in ("ambient", "foreground"):
                sustain = src.get("sustain", "")
                if sustain:
                    sustain_parts.append(_capitalize(sustain))

        if sustain_parts:
            joined = " ".join(sustain_parts[:2])
            if joined and joined[-1] not in ".!?—":
                joined += "."
            parts.append("It settles: " + joined)

    # Mood
    mood = scene.get("mood", [])
    if mood:
        parts.append("")
        parts.append(f"The mood: {', '.join(mood)}.")

    return "\n".join(parts)
