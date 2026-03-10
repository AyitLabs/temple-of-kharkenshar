"""
mindscape_language.py — Cross-sensory prose generation.

Weaves smell + sight + sound + touch into unified paragraphs.
NOT four separate sections — one flowing experience.

Key principles:
- Temporal flow: sight first (speed of light), then sound (speed of sound), then smell (diffusion), touch throughout
- Cross-sensory bridges: link senses ("the amber light carries the same warmth as the vanilla")
- Environmental coherence: humidity/temperature/wind affect all senses together
- Touch is woven naturally — it's not a separate report, it's what the body feels while the eyes see and ears hear
- Position transitions shift all senses simultaneously
- Temporal dynamics: time-of-day modifies all four senses
- Mood resonances: sensory combinations evoke emotional states
- Memory triggers: scents invoke universal human memories
"""

import random

# ─── Cross-sensory bridge templates ─────────────────────────────────────────
# Each key maps to a list of prose bridges. Keys are scanned against
# the combined text of all active sense components (sight, sound, smell prose).
# When a keyword matches, a bridge phrase is selected and woven into the output.

BRIDGES = {
    # --- Warmth/heat bridges ---
    "warmth": [
        "the warm light and the warm scent blur into one sensation",
        "warmth enters through the eyes and the nose simultaneously",
        "the amber glow carries the same heat as the spice in the air",
        "light and scent share the same temperature here",
    ],
    "warm": [
        "the golden light and the sweet smell share the same warmth — the same memory of a kitchen, maybe",
        "warmth touches you through every sense at once: light on skin, scent in lungs, sound like a blanket",
        "the warm tones in the light and the warm notes in the air are harmonics of the same chord",
    ],
    # --- Smoke bridges ---
    "smoke": [
        "you see the smoke before you smell it, then the two merge",
        "the haze that softens the lights is the same smoke that fills your lungs",
        "smoke is the bridge between what you see and what you breathe",
        "the visible smoke promises what arrives a moment later on the tongue",
        "the smoke you see is the smoke you taste is what's making that sound — one substance, three senses",
        "smoke erases the boundary between sight and smell — it's visible air, breathable light",
    ],
    "sizzle": [
        "the sizzle is what the smoke sounds like, the smoke is what the sizzle looks like",
        "follow the sound to the smoke to the smell — they're the same event at different speeds",
    ],
    # --- Water/wet bridges ---
    "wet": [
        "wet surfaces catch light the way humid air catches scent — everything intensified",
        "the gleam of wet ground and the sharpness of rain-washed air say the same thing",
        "water amplifies everything: reflections brighter, smells sharper, sounds clearer",
        "dampness connects the senses — what glistens is what you smell more strongly, what sounds more softly",
    ],
    "rain": [
        "what you see falling is what you hear landing is what you smell rising from the earth",
        "the rain is one event experienced three ways: silver streaks, broadband hiss, petrichor",
        "rain rewrites all three senses simultaneously — wet reflections, white noise, earth-scent",
        "each raindrop is a tiny cross-sensory event: visible, audible, olfactory on impact",
    ],
    "puddle": [
        "the puddles hold the sky and the neon — the world upside down in two inches of water",
        "step on the reflection and it shatters into sound",
    ],
    "petrichor": [
        "petrichor is the earth's response to rain — what you see falling, the ground answers with scent",
        "the rain you watch is the rain you hear is the rain you smell rising back from warm asphalt",
    ],
    # --- Darkness bridges ---
    "dark": [
        "in the dark, the other senses sharpen — smell and sound step forward",
        "what the eyes can't reach, the nose and ears fill in",
        "darkness doesn't mean less sensation — it means the balance shifts",
        "what you can't see, you hear louder — darkness is an amplifier for everything else",
        "the dark trades vision for the other senses, and the exchange rate is generous",
    ],
    "darkness": [
        "in the absence of light, the world doesn't disappear — it reorganizes around sound and scent",
        "darkness strips away the visual and what remains is more honest: smell, sound, temperature, texture",
    ],
    # --- Age/old bridges ---
    "old": [
        "the visual patina and the musty scent tell the same story of time",
        "age shows in the yellowed pages and the smell of slow decay",
        "you can see the years and smell them — they're the same years",
        "the creak in the wood and the dust in the air and the patina on the surface are three clocks reading the same hour",
    ],
    "musty": [
        "the musty smell and the visual dust agree: no one has been here for a while",
        "mustiness is the smell of time having its way with a room — the yellowed wallpaper confirms it",
    ],
    "creak": [
        "the floorboard creaks and the room's age becomes audible — you could already see it, smell it, now you hear it",
        "every creak is the building remembering it was once new",
    ],
    "aged": [
        "age is a cross-sensory experience: the worn surfaces you see, the settled dust you smell, the groaning wood you hear",
        "this place has been converting time into patina for decades, and every sense reports the same number",
    ],
    # --- Freshness bridges ---
    "fresh": [
        "the crisp visual clarity matches the clean scent — everything newly washed",
        "freshness hits all senses at once, like the world just took a breath",
        "the air smells clean and the light looks clean and the silence sounds clean — one adjective, three senses",
    ],
    # --- Sweet bridges ---
    "sweet": [
        "the golden light is as sweet as the sugar in the air",
        "sweetness has a color here — amber, caramel, honey-gold",
        "the warm glow and the sweet scent conspire: this place tastes like it looks",
    ],
    "vanilla": [
        "the golden light and the vanilla share the same warmth — both amber, both comforting",
        "vanilla and warm light are the same frequency of comfort, one through the nose, one through the eyes",
    ],
    # --- Sharp/clinical bridges ---
    "sharp": [
        "the harsh light and the acrid smell arrive together, both unwelcome",
        "sharpness in the air, sharpness in the light — the senses agree",
        "the fluorescent buzz and the antiseptic share the same clinical edge",
    ],
    "antiseptic": [
        "the cold light and the antiseptic smell are co-conspirators — both stripping warmth from the room",
        "clinical light, clinical smell: this place is designed to be uncomfortable in two senses at once",
    ],
    "fluorescent": [
        "the fluorescent buzz and the chemical smell belong together — industrial sensory siblings",
        "you taste the fluorescent light as much as see it — both tinged with metal and headache",
    ],
    # --- Earth bridges ---
    "earthy": [
        "the brown-green palette and the soil smell are the same earth, sensed two ways",
        "what grows here colors the air and the light equally",
    ],
    "soil": [
        "the dark earth you see and the dark earth you smell are the same story — growth and decay, simultaneously",
    ],
    "moss": [
        "the green you see on the stone is the green you smell in the air — moss connects sight and scent through chlorophyll",
    ],
    # --- Metal bridges ---
    "metallic": [
        "the cold gleam of metal and the iron tang in the air — same material, different senses",
        "you taste the fluorescent light as much as see it — both tinged with metal",
    ],
    "iron": [
        "the iron taste and the iron color and the iron cold — one element, three sensory reports",
    ],
    # --- Fire bridges ---
    "fire": [
        "fire connects all three senses: you see the flame, hear the crackle, smell the smoke — one element, three invitations",
        "the dance of the flame is the rhythm of the crackle is the source of the smoke — follow any sense and it leads to fire",
        "warmth radiates outward in expanding rings of sensation: first the light, then the heat, then the sound, then the smell",
    ],
    "flame": [
        "the flame paints the walls with moving light, scores the air with soft crackle, and perfumes the room with woodsmoke — one fire, three performances",
    ],
    "bonfire": [
        "the bonfire is a symphony: flickering orange light, popping percussion, woodsmoke incense — all from the same burning",
    ],
    "candle": [
        "candlelight and warm wax and the faintest sputter — one small flame addressing three senses at once",
    ],
    # --- Cold bridges ---
    "cold": [
        "the cold light and the cold air and the cold silence all agree: warmth has left this place",
        "cold sharpens edges — visual edges, sound edges, the edge of each breath",
    ],
    "ice": [
        "ice catches light, dampens sound, and chills the air — it dominates all three senses with one word: cold",
    ],
    "frost": [
        "frost is visible cold — and the silence of a frozen morning confirms what the eyes already know",
    ],
    # --- Humidity bridges ---
    "humid": [
        "the humidity binds all three senses: smells hang heavy, light hazes, sounds dampen — the air itself has weight",
        "moisture in the air is the universal connector — it carries scent further, softens light, and wraps sound in cotton",
    ],
    "steam": [
        "the steam blurs the boundary between seeing and breathing — it's visible air, breathable light",
        "steam carries scent upward, catches light sideways, and adds a faint hiss to the soundscape",
    ],
    "damp": [
        "dampness intensifies everything: colors deeper, smells stronger, sounds closer",
    ],
    # --- Night/neon bridges ---
    "neon": [
        "neon light and city sound are the same urban pulse — electric, buzzing, alive after dark",
        "the neon paints the wet street the same color it paints the air — everything baptized in pink or blue",
    ],
    "night": [
        "night reshuffles the senses: sight yields its throne and sound and smell divide the kingdom",
        "after dark, the world is rebuilt from sound and scent — light becomes precious, each source a landmark",
    ],
    # --- Wood bridges ---
    "wood": [
        "the warm color of the wood, the creak when you step on it, the faint cedar scent — one material, three hellos",
    ],
    "cedar": [
        "cedar is a triple-sense word: warm brown, soft creak, sweet resin",
    ],
    # --- Ocean/sea bridges ---
    "ocean": [
        "the salt you taste is the salt you smell is the glitter you see on the water — one ocean, every sense",
    ],
    "salt": [
        "salt air and salt light — the ocean tags everything within reach",
    ],
    "wave": [
        "the wave you see approaching is the wave you hear breaking is the mist you smell as it retreats",
    ],
}

# ─── Keyword-based bridge scanner ───────────────────────────────────────────

def scan_for_bridges(sight_prose="", sound_prose="", smell_prose="", max_bridges=3):
    """Scan active sense prose for matching bridge keywords and return appropriate bridges."""
    combined = f"{sight_prose} {sound_prose} {smell_prose}".lower()
    found = []
    used_keys = set()
    for key, phrases in BRIDGES.items():
        if key in combined and key not in used_keys:
            found.append(pick(phrases))
            used_keys.add(key)
            if len(found) >= max_bridges:
                break
    return found


# ─── Mood Resonances ────────────────────────────────────────────────────────
# Maps tuples of sensory tag keywords to emotional/mood descriptions.
# Components are tagged with mood-relevant keywords; the engine matches
# combinations and weaves the resulting mood into narration.

MOOD_RESONANCES = {
    ("warm_light", "sweet_smell"): "nostalgic, safe — the feeling of a childhood kitchen with something baking",
    ("warm_light", "woodsmoke"): "contentment so deep it hurts a little, the ache of a night you didn't want to end",
    ("cold_light", "antiseptic"): "clinical, anxious, too-clean — the wrongness of a place scrubbed of all personality",
    ("cold_light", "sharp_smell"): "alert, uncomfortable, the body wanting to leave before the mind agrees",
    ("darkness", "silence"): "alone with yourself, the world shrunk to arm's length — not lonely, but solitary",
    ("darkness", "rain_sound"): "cocooned, hidden, the world reduced to the sound of water and the smell of everything it touches",
    ("rain_sound", "warm_interior"): "protected, cozy, grateful for walls — the specific pleasure of being dry while it pours",
    ("rain_sound", "petrichor"): "earthbound, temporal, the smell of the planet breathing out",
    ("neon", "wet_street"): "cinematic loneliness, the beauty of a city that doesn't know you're watching",
    ("neon", "crowd"): "electric belonging, anonymous energy, being nobody among everybody",
    ("fire_light", "smoke_smell"): "primal comfort, the campfire contract — sit here, you're safe, the dark stays out there",
    ("fire_light", "cold_air"): "the push-pull of warmth and cold, the lit circle vs. the dark beyond",
    ("candle", "old_room"): "the weight of years made gentle by small flame — vigil, memory, the living visiting the past",
    ("candle", "silence"): "sacred attention, the quality of light that makes you whisper",
    ("morning_light", "coffee"): "the reliable miracle of a new day, caffeine and photons, both saying: begin",
    ("morning_light", "birdsong"): "hope without trying, the world resetting itself, everything briefly possible",
    ("golden_hour", "grass"): "the ache of late afternoon, time running out beautifully, summer made visible",
    ("moonlight", "ocean"): "vast and indifferent beauty, the sublime — too big to be comforting, too beautiful to fear",
    ("moonlight", "silence"): "the world after hours, a private showing of the night for an audience of one",
    ("fog", "dampened_sound"): "muffled, uncertain, edges dissolved — the world offering you less information than usual",
    ("fog", "distant_horn"): "isolation with proof of others, the loneliness of things separated by weather",
    ("snow", "silence"): "the deepest quiet — snow absorbs sound and the world goes on mute, white and still",
    ("thunder", "darkness"): "primal respect, the sky asserting itself, your smallness confirmed by bass and flash",
    ("incandescent", "old_wood"): "the warm patina of places that predate LEDs — libraries, grandparents' houses, the 20th century",
    ("subway", "fluorescent"): "underground efficiency, the temporary ugliness everyone agrees to tolerate",
    ("jazz", "dim_light"): "smoky intimacy, the late hour, drinks half-finished, the music knowing more than you",
    ("jazz", "whiskey"): "sophistication's younger sibling: being comfortable not knowing what comes next",
    ("spice", "warm_light"): "abundance, generosity, the sensory maximalism of markets and feasts",
    ("old_books", "dust"): "accumulated thinking, the weight of other people's ideas, a room where time deposits knowledge",
    ("tropical", "humid"): "lush overwhelm, the senses turned up to maximum, nature refusing subtlety",
    ("cold_wind", "smoke"): "defiance — the warmth fighting the cold, the small fire holding its ground",
    ("church_bell", "stone"): "centuries of the same sound hitting the same walls, tradition as acoustic phenomenon",
    ("steam", "ceramic"): "the ritual of hot drinks, the pause that civilization is built on",
    ("blood", "metal"): "violence or aftermath, the taste of adrenaline, copper in the mouth and iron in the air",
    ("honey", "sunlight"): "sweetness made redundant — the light is honey-colored and the honey is light-colored and both are warm",
}

# Mood tag keywords that map to component descriptors
MOOD_TAGS = {
    "warm_light": ["warm", "golden", "amber", "candle", "incandescent", "fireplace", "bonfire", "lantern", "golden_hour", "sunrise"],
    "cold_light": ["fluorescent", "cold", "clinical", "blue", "mercury", "cool_led", "harsh"],
    "sweet_smell": ["vanilla", "sweet", "sugar", "caramel", "honey", "baking", "cinnamon", "chocolate"],
    "sharp_smell": ["antiseptic", "chemical", "bleach", "ammonia", "sharp", "acrid"],
    "woodsmoke": ["woodsmoke", "campfire", "bonfire", "fireplace", "chimney"],
    "antiseptic": ["antiseptic", "clinical", "hospital", "bleach", "sterile"],
    "darkness": ["dark", "darkness", "night", "midnight", "pitch", "shadow"],
    "silence": ["silence", "quiet", "still", "hushed", "mute"],
    "rain_sound": ["rain", "rainy", "downpour", "drizzle", "patter"],
    "warm_interior": ["cozy", "interior", "indoor", "hearth", "shelter", "warm_room"],
    "petrichor": ["petrichor", "after_rain", "wet_earth", "geosmin"],
    "neon": ["neon", "neon_sign", "neon_pink", "neon_blue"],
    "wet_street": ["wet_asphalt", "wet_cobblestone", "puddle", "rain_slick"],
    "crowd": ["crowd", "murmur", "voices", "packed", "busy"],
    "fire_light": ["fire", "flame", "bonfire", "fireplace", "candle"],
    "smoke_smell": ["smoke", "char", "burning", "guaiacol", "creosote"],
    "cold_air": ["cold", "freezing", "frost", "ice", "winter", "chill"],
    "candle": ["candle", "candlelit", "taper", "wick"],
    "old_room": ["old", "aged", "dusty", "patina", "antique", "musty"],
    "morning_light": ["sunrise", "dawn", "morning", "first_light"],
    "coffee": ["coffee", "espresso", "caffeine", "roasted_bean"],
    "birdsong": ["birdsong", "birds", "dawn_chorus", "songbird"],
    "golden_hour": ["golden_hour", "golden", "amber", "late_afternoon"],
    "grass": ["grass", "lawn", "meadow", "field"],
    "moonlight": ["moonlight", "moon", "lunar", "silver_light"],
    "ocean": ["ocean", "sea", "waves", "surf", "maritime"],
    "fog": ["fog", "mist", "haze", "murk"],
    "dampened_sound": ["muffled", "dampened", "absorbed", "soft"],
    "distant_horn": ["foghorn", "distant_horn", "ship_horn"],
    "snow": ["snow", "snowy", "snowfall", "blizzard", "white"],
    "thunder": ["thunder", "storm", "lightning"],
    "incandescent": ["incandescent", "tungsten", "warm_bulb"],
    "old_wood": ["oak", "pine", "old_wood", "timber", "beam"],
    "subway": ["subway", "metro", "underground", "tunnel"],
    "fluorescent": ["fluorescent", "tube_light", "office_light"],
    "jazz": ["jazz", "saxophone", "piano_jazz", "bass", "bebop"],
    "dim_light": ["dim", "low_light", "candlelit", "half-dark"],
    "whiskey": ["whiskey", "bourbon", "scotch", "spirits"],
    "spice": ["spice", "pepper", "cinnamon", "cumin", "cardamom", "piperine"],
    "old_books": ["books", "paper", "library", "pages", "volumes"],
    "dust": ["dust", "dusty", "motes", "settled"],
    "tropical": ["tropical", "jungle", "lush", "palm"],
    "humid": ["humid", "humidity", "moisture", "saturated"],
    "cold_wind": ["wind", "gust", "cold_wind", "bitter"],
    "church_bell": ["church_bell", "bell_tower", "campanile"],
    "stone": ["stone", "granite", "marble", "limestone"],
    "steam": ["steam", "vapor", "condensation"],
    "ceramic": ["ceramic", "porcelain", "pottery", "clay"],
    "blood": ["blood", "crimson", "iron_taste"],
    "metal": ["metal", "steel", "iron", "metallic"],
    "honey": ["honey", "golden_syrup", "mead"],
    "sunlight": ["sunlight", "midday_sun", "bright_sun", "sunshine"],
}


def find_mood(sight_prose="", sound_prose="", smell_prose="", scene_mood_tags=None):
    """Find applicable mood resonances from the active sensory content."""
    combined = f"{sight_prose} {sound_prose} {smell_prose}".lower()
    if scene_mood_tags:
        combined += " " + " ".join(scene_mood_tags)

    # Determine which mood tags are active
    active_tags = set()
    for tag, keywords in MOOD_TAGS.items():
        for kw in keywords:
            if kw in combined:
                active_tags.add(tag)
                break

    # Find matching mood resonances
    moods = []
    for tag_combo, description in MOOD_RESONANCES.items():
        if all(t in active_tags for t in tag_combo):
            moods.append(description)

    return moods


# ─── Memory Triggers ────────────────────────────────────────────────────────
# Maps scent/sensory keywords to universal memory associations.
# These fire during narration to add a "this reminds you of..." layer.

MEMORY_TRIGGERS = {
    "vanilla": "baking with someone you loved — the oven warm, the house sweet, time moving at vanilla speed",
    "petrichor": "running home as a kid before the storm hit, the first fat drops on your arms",
    "woodsmoke": "a night you didn't want to end, faces lit orange, someone's laugh carrying through the smoke",
    "chlorine": "summer, wet concrete, someone's backyard pool, the shock of cold water on sun-hot skin",
    "old_paper": "a room where someone spent years thinking — their thoughts still here in the binding glue and foxed pages",
    "cinnamon": "a kitchen in December, something spiced cooling on the counter, the radio playing",
    "coffee": "the first cup of the morning, when the day was still just a plan",
    "gasoline": "road trips, gas station stops, the specific freedom of being between places",
    "fresh_bread": "a bakery you walked past every morning, the door open, the warm yeast smell pulling you in",
    "cut_grass": "saturday mornings, someone's lawn mower, the whole neighborhood smelling like summer",
    "sunscreen": "a beach, salt, sand in everything, the day lasting forever",
    "rain_on_dust": "the first rain after a long dry spell, the earth exhaling in relief",
    "mothballs": "a grandparent's closet, old coats, the smell of someone who saved everything",
    "pipe_tobacco": "a room with leather chairs and books, someone who had time to think",
    "jasmine": "warm nights in a garden, the flowers opening after dark, the sweetness almost too much",
    "diesel": "buses, trains, departure — the fuel that moves you to somewhere else",
    "chalk": "a classroom, the board full of someone's handwriting, learning something for the first time",
    "new_car": "the specific thrill of something unused, everything still possible, no scratches yet",
    "campfire": "someone playing guitar badly, marshmallows on sticks, the stars clearer than they should be",
    "hospital": "corridors, worry, the hum of machines keeping someone alive, the too-clean smell that means something's wrong",
    "old_books": "the library as a child — every book a door, the mustiness a welcome mat",
    "cedar": "a closet that smelled like a forest, or a sauna, or a cabin where you slept well",
    "lavender": "someone's garden, or someone's soap, or someone's pillow — always someone",
    "salt_air": "the first sight of the ocean after a long drive, windows down, the air changing flavor",
    "wood_polish": "a church pew, or a grand piano, or a table where important things were decided",
    "popcorn": "a movie theater, the dark, anticipation, the smell arriving before the previews",
    "burnt_toast": "a morning going wrong, someone cursing in the kitchen, the scraping of charcoal off bread",
    "pine": "christmas, or a forest trail, or the air freshener in your father's car",
    "miso": "warmth in a bowl, steam fogging your glasses, the first meal in a country where you couldn't read the signs",
    "tar": "a road being laid in summer heat, the smell so thick you could chew it, the road crew's radio playing",
    "gunpowder": "fireworks on a warm night, the crowd going 'oooh', the smoke drifting down, tasting of sulfur and celebration",
    "lemon": "something just cleaned, or a drink on a hot day, or your hands after cooking",
    "ink": "a new book cracked open, or a letter from someone who still writes by hand",
    "hay": "late summer, a field cut and drying, the warmth trapped in the bales, something ending",
    "seaweed": "the tide line, flip-flops, the rocks where you found things as a kid",
}


def find_memories(smell_prose="", sight_prose="", sound_prose=""):
    """Find memory triggers from the active sensory content."""
    combined = f"{smell_prose} {sight_prose} {sound_prose}".lower()
    memories = []
    for trigger, memory in MEMORY_TRIGGERS.items():
        if trigger.replace("_", " ") in combined or trigger in combined:
            memories.append(memory)
    return memories[:3]  # Cap at 3 to avoid overwhelming


# ─── Temporal flow templates ────────────────────────────────────────────────

TEMPORAL_INTROS = {
    "approach": [
        "You see it first.",
        "It begins with the eyes.",
        "The scene announces itself visually before anything else.",
        "Light reaches you first — it always does.",
    ],
    "sound_arrives": [
        "Then the sound arrives.",
        "A moment later, the sounds catch up.",
        "Sound follows — ",
        "The noise reaches you next: ",
    ],
    "smell_arrives": [
        "And then the smell. The slowest sense, the deepest one.",
        "Finally, the scent finds you.",
        "The smell comes last but stays longest.",
        "Then the air itself carries the rest of the story.",
    ],
}

# ─── Environmental effect descriptions ──────────────────────────────────────

HUMIDITY_EFFECTS = {
    "high": {
        "smell": "scents hang heavy and travel far in the saturated air",
        "sight": "a soft haze blurs the edges of everything",
        "sound": "sounds feel slightly muffled, wrapped in moisture",
        "unified": "The humidity binds everything together — smells linger, lights haze, sounds soften. The air itself has weight.",
    },
    "low": {
        "smell": "scents are faint, evaporating quickly in the dry air",
        "sight": "everything is sharp-edged and clear",
        "sound": "sounds carry far and ring dry",
        "unified": "The dry air makes everything crisp — sharp outlines, quick-fading scents, sounds that carry cleanly.",
    },
}

TEMPERATURE_EFFECTS = {
    "hot": {
        "smell": "heat drives volatile compounds into the air, intensifying every scent",
        "sight": "heat shimmer makes distant objects waver and dance",
        "sound": "warm air bends sound upward, making distant sounds drop away",
        "unified": "The heat amplifies smell and bends light, while sounds seem to evaporate.",
    },
    "cold": {
        "smell": "cold suppresses volatility — you have to get close to smell anything",
        "sight": "cold air is transparent, distances collapse, everything looks closer",
        "sound": "cold air conducts sound efficiently — you hear things from surprisingly far",
        "unified": "The cold sharpens sight and sound while muting smell — the world is vivid but odorless until you're right on top of it.",
    },
}

WIND_EFFECTS = [
    "The wind carries scent directionally — you smell what's upwind, not what's close.",
    "A breeze shifts the sensory map: smells arrive from one direction, sounds scatter.",
    "Wind is the mixer — it blends scents, flutters visual elements, and adds its own sound underneath everything.",
]

RAIN_EFFECTS = {
    "smell": "petrichor rises from warm asphalt, and wet surfaces release their stored scents",
    "sight": "rain turns every surface into a mirror — reflections double the visual world",
    "sound": "the rain provides a broadband wash of white noise that muffles other sounds",
    "unified": "Rain rewrites all three senses at once: petrichor, wet reflections, and the soft roar that wraps everything.",
}

TIME_EFFECTS = {
    "dawn": "The world is muted — colors desaturated, sounds carrying far in still air, dew suppressing dust scents.",
    "morning": "Fresh and clear — sharp light, bird sounds, dew-dampened earth smell giving way to warming air.",
    "golden_hour": "Amber light makes everything nostalgic. Warmth releases final scents of the day. Sounds soften.",
    "dusk": "Colors drain. Sounds shift — daytime fades, night sounds begin. Cooling air condenses scent.",
    "night": "Sight yields to sound and smell. Artificial lights create islands. Dark amplifies everything else.",
    "late_night": "Near-silence. The world reduces to what's immediate — your own breath, the closest sounds, whatever the dark air carries.",
}


# ─── Touch narration phrases ────────────────────────────────────────────────

TOUCH_TEMPERATURE = {
    "cold": [
        "The cold is a physical thing — it pushes through fabric, settles into bone.",
        "Every surface steals heat from your fingertips on contact.",
        "Cold sharpens the edges of everything you touch — metal bites, stone aches, even wood feels hostile.",
        "Your hands know the temperature before your mind does — the body's first report is always tactile.",
    ],
    "cool": [
        "A pleasant coolness on the skin — the air moving just enough to register.",
        "Cool surfaces under your palm, warming slowly where you press.",
        "The kind of cool that makes you aware of your own warmth by contrast.",
    ],
    "warm": [
        "Warmth radiates from surfaces — the world has been absorbing heat and now returns it through your skin.",
        "The air sits warm on your arms, a gentle pressure of heated molecules.",
        "Everything you touch holds warmth — wood, stone, fabric, all thermal batteries slowly discharging.",
    ],
    "hot": [
        "Heat presses in from every direction — the air itself is a warm hand on your face.",
        "Surfaces in sun are untouchable — your hand flinches before your brain decides.",
        "The heat is tactile, oppressive, a weight on exposed skin that never lifts.",
        "Sweat forms where skin meets anything: chair arms, waistbands, the crook of your elbow.",
    ],
}

TOUCH_TEXTURES = {
    "rough": [
        "rough under your fingers — every imperfection a tiny landscape",
        "the surface catches at your skin, friction mapping its history",
        "textured like something that has weathered, survived, earned its roughness",
    ],
    "smooth": [
        "smooth as something polished by a thousand hands before yours",
        "the surface offers no resistance — your fingers glide without information",
        "polished, frictionless, the tactile equivalent of silence",
    ],
    "soft": [
        "soft — the kind of surface that accepts the shape of your hand",
        "yielding under pressure, warm where you press, a surface that gives",
        "soft enough that touching it is a kind of conversation: you push, it responds",
    ],
    "hard": [
        "unyielding — your hand conforms to it, not the reverse",
        "hard surface, no give, the impact of contact traveling up through your wrist",
        "solid and absolute, the kind of surface that makes you aware of your own softness",
    ],
    "wet": [
        "wet — your fingers come away changed, carrying a thin film of this place",
        "moisture on every surface, a slickness that makes grip uncertain",
        "the wetness is information: something happened here, or is still happening",
    ],
    "dry": [
        "dry surfaces — friction is high, everything grips, paper-textured air on skin",
        "the dryness has its own feel: tight skin, static-prone, everything slightly abrasive",
    ],
}

TOUCH_AIR_FEEL = {
    "still": [
        "The air is perfectly still — you feel your own body heat reflected back at you.",
        "No air movement at all. The world is holding its breath.",
        "Still air: you feel the boundary of your own thermal envelope, warm at the skin.",
    ],
    "breezy": [
        "A light breeze finds your skin — directional, informative, carrying temperature data from somewhere else.",
        "The air moves just enough to cool one side of your face, telling you which way is open.",
        "A breeze touches you the way the world says hello — casually, from one direction.",
    ],
    "windy": [
        "Wind pushes against you — not a breeze, a force, something you lean into or away from.",
        "The wind is constant tactile information: direction, temperature, speed, all read through skin.",
        "Wind makes every exposed surface a sensor — you feel the world's weather on your arms, your neck, your hands.",
    ],
    "gusty": [
        "Gusts hit like irregular heartbeats — calm, then pressure, then calm. Unpredictable touch.",
        "The air can't make up its mind: pushing, releasing, pushing harder. Your hair, your clothes, all in conversation with it.",
        "Gusty wind is tactile chaos — direction changes mid-breath, temperature fluctuates, nothing stays still.",
    ],
}

# ─── Temporal transition prose ──────────────────────────────────────────────
# What changes across senses when time shifts.

TEMPORAL_TRANSITIONS = {
    "dawn": {
        "sight": "First light arrives not as brightness but as the slow draining of dark — colors emerge from grey like a photograph developing.",
        "sound": "Dawn is the loudest quiet: birdsong erupts, sharp and territorial, filling the acoustic vacuum the night left behind.",
        "smell": "Dew has been suppressing dust and earth-scent all night — now, as the air stirs, the first volatile molecules escape upward.",
        "touch": "Every surface is dew-wet and cold. Your hand on a railing comes away damp. The air has the specific chill of a world that hasn't been warmed yet.",
    },
    "morning": {
        "sight": "Morning light is clean and slightly cool — shadows are long and blue-tinted, everything sharp-edged and freshly lit.",
        "sound": "The dawn chorus fades as the human world starts up — engines, doors, footsteps. The transition from birdsong to industry.",
        "smell": "Warming air begins to release volatiles — the first coffee, the first exhaust, the dew burning off surfaces and unlocking yesterday's scents.",
        "touch": "Surfaces are warming unevenly — metal in sun already hot to touch while shade-side stone is still night-cold. The world is patchy in temperature.",
    },
    "midday": {
        "sight": "Light comes from directly above — shadows shrink to nothing, colors wash out in the intensity, everything overexposed and flat.",
        "sound": "Midday is acoustically lazy — heat dampens activity. The soundscape thins to ambient hum, distant traffic, the occasional voice.",
        "smell": "Maximum volatility — heat drives every scent molecule into the air. This is the most fragrant hour if there's anything to smell.",
        "touch": "The sun is a physical presence on exposed skin. Surfaces store heat — metal, asphalt, stone all radiate upward. Shade is a tactile relief.",
    },
    "afternoon": {
        "sight": "Light angles lower, shadows stretch east. Colors deepen slightly as the sun's blue component scatters through more atmosphere.",
        "sound": "Afternoon has its own rhythm: post-lunch quiet giving way to second-wind activity. The soundscape rebuilds.",
        "smell": "Still warm enough for strong scent — afternoon is when bakeries and kitchens fill the air as evening prep begins.",
        "touch": "Surfaces at maximum stored heat — the afternoon touch is warmth everywhere, radiating from walls, pavements, the ground itself.",
    },
    "golden_hour": {
        "sight": "The light turns amber-gold, shadows stretch impossibly long, every surface glows warm. The most beautiful light, and the briefest.",
        "sound": "The world begins to quiet. Daytime sounds fade. A transitional hush, birds make their last calls.",
        "smell": "Cooling air begins to condense volatiles — scents that floated freely in heat now settle, concentrate, become richer at nose-height.",
        "touch": "The air cools on your skin while surfaces still radiate the day's stored warmth. A pleasant dissonance: cool air, warm stone underfoot.",
    },
    "dusk": {
        "sight": "Colors drain like water from a painting. The sky holds light longest while the ground goes dark first. Artificial lights become visible.",
        "sound": "The dusk shift: daytime sounds exit, night sounds enter. Insects begin. Traffic thins. Voices carry further in cooling air.",
        "smell": "Night-blooming flowers open. Cooling air condenses scent. The world smells different after dark — more intimate, more concentrated.",
        "touch": "Temperature drops noticeably. Surfaces that were warm go cool. The air develops a crispness, a slight bite. Goosebumps possible.",
    },
    "night": {
        "sight": "Vision contracts to pools of artificial light. Between them: darkness, shapes, the brain filling in what the eyes can't confirm.",
        "sound": "Night amplifies everything — or rather, the silence between sounds makes each one enormous. Footsteps, distant engines, insects, wind.",
        "smell": "Cool air reduces volatility but proximity compensates — night smells are intimate, close, the ones you walk through rather than the ones that drift to you.",
        "touch": "Cold surfaces, damp air if humidity is high. The dark heightens tactile awareness — you feel doorframes, steps, railings more carefully. Your body navigates by touch.",
    },
    "late_night": {
        "sight": "The minimum of light. Artificial sources become landmarks in a void. Stars (if visible) are the only ambient light. The world is mostly imagined.",
        "sound": "Near-total silence, which makes any sound — a car, a siren, a dog — feel enormous, almost intrusive. Your own breathing is present.",
        "smell": "The coldest, stillest air. Scent molecules barely move. What you smell is what's immediately around you, like a scent bubble two feet wide.",
        "touch": "Maximum cold on surfaces. Still, heavy air. The body is most aware of itself — your clothes, your temperature, the ground beneath your feet. Touch is the primary navigational sense.",
    },
}


def pick(lst):
    """Pick a random item from a list."""
    return random.choice(lst) if lst else ""


def narrate_touch(scene, env=None):
    """
    Generate touch prose from scene data and environmental conditions.
    Touch is woven naturally — thermal feel, surface textures, air on skin.
    """
    parts = []
    env = env or getattr(scene, "environment", None)

    # Scene-level touch profile
    touch = getattr(scene, "touch", {})
    if touch:
        if touch.get("air_feel"):
            parts.append(touch["air_feel"])
        if touch.get("thermal_notes"):
            parts.append(touch["thermal_notes"])
        if touch.get("key_tactile_moments"):
            moments = touch["key_tactile_moments"]
            if isinstance(moments, list):
                parts.append(pick(moments))
            elif isinstance(moments, str):
                parts.append(moments)

    # Environment-derived touch
    if env:
        # Thermal feel
        if hasattr(env, "thermal_feel"):
            thermal = env.thermal_feel
            if "neutral" not in thermal.lower() and "unremarkable" not in thermal.lower():
                parts.append(thermal)

        # Temperature band phrases
        temp = getattr(env, "temperature_c", 22)
        if temp < 5:
            parts.append(pick(TOUCH_TEMPERATURE["cold"]))
        elif temp < 15:
            parts.append(pick(TOUCH_TEMPERATURE["cool"]))
        elif temp > 32:
            parts.append(pick(TOUCH_TEMPERATURE["hot"]))
        elif temp > 26:
            parts.append(pick(TOUCH_TEMPERATURE["warm"]))

        # Air feel based on wind
        wind = getattr(env, "wind_speed_kmh", 0)
        if wind > 25:
            parts.append(pick(TOUCH_AIR_FEEL["gusty"]))
        elif wind > 15:
            parts.append(pick(TOUCH_AIR_FEEL["windy"]))
        elif wind > 5:
            parts.append(pick(TOUCH_AIR_FEEL["breezy"]))
        elif not getattr(env, "indoor", False):
            parts.append(pick(TOUCH_AIR_FEEL["still"]))

    # Surface textures from scene touch profile
    if touch and touch.get("surface_textures"):
        textures = touch["surface_textures"]
        if isinstance(textures, list) and textures:
            tex_key = textures[0].lower()
            for cat, phrases in TOUCH_TEXTURES.items():
                if cat in tex_key:
                    parts.append(pick(phrases))
                    break

    # Keep it concise — pick at most 2-3 sentences
    if len(parts) > 3:
        parts = parts[:3]

    return " ".join(parts) if parts else ""


def get_temporal_description(time_of_day, senses=None):
    """Generate temporal transition prose for a specific time of day.

    Args:
        time_of_day: One of TimeState.TIMES
        senses: Optional list of senses to include (default: all four)
    """
    if time_of_day not in TEMPORAL_TRANSITIONS:
        return ""
    transition = TEMPORAL_TRANSITIONS[time_of_day]
    if senses is None:
        senses = ["sight", "sound", "smell", "touch"]
    parts = [transition[s] for s in senses if s in transition]
    return " ".join(parts)


def get_env_description(env):
    """Generate environmental coherence paragraph including touch."""
    parts = []

    # Time of day
    tod = getattr(env, "time_of_day", "day")
    if tod in TIME_EFFECTS:
        parts.append(TIME_EFFECTS[tod])
    # Temporal transition adds touch + richer detail
    if tod in TEMPORAL_TRANSITIONS:
        parts.append(TEMPORAL_TRANSITIONS[tod].get("touch", ""))

    # Humidity
    h = getattr(env, "humidity_pct", 50)
    if h > 75:
        parts.append(HUMIDITY_EFFECTS["high"]["unified"])
    elif h < 30:
        parts.append(HUMIDITY_EFFECTS["low"]["unified"])

    # Temperature
    t = getattr(env, "temperature_c", 22)
    if t > 32:
        parts.append(TEMPERATURE_EFFECTS["hot"]["unified"])
    elif t < 5:
        parts.append(TEMPERATURE_EFFECTS["cold"]["unified"])

    # Wind
    w = getattr(env, "wind_speed_kmh", 0)
    if w > 10:
        parts.append(pick(WIND_EFFECTS))

    # Rain
    weather = getattr(env, "weather", "clear")
    if weather in ("rain", "heavy_rain"):
        parts.append(RAIN_EFFECTS["unified"])

    return " ".join(p for p in parts if p) if parts else ""


def find_bridge(scene):
    """Find applicable cross-sensory bridges for a scene."""
    bridges = []
    # Check scene's explicit bridges
    if hasattr(scene, "cross_sensory_bridges") and scene.cross_sensory_bridges:
        bridges.extend(scene.cross_sensory_bridges)
        return bridges

    # Auto-detect from scene content
    smell_text = str(scene.smell).lower()
    sight_text = str(scene.sight).lower()

    for key, phrases in BRIDGES.items():
        if key in smell_text or key in sight_text:
            bridges.append(pick(phrases))
            if len(bridges) >= 2:
                break

    return bridges


def narrate_scene(scene, smell_prose="", sight_prose="", sound_prose="", touch_prose=""):
    """
    Generate unified multi-sensory prose for a scene.

    If the scene has pre-composed prose, use that.
    Otherwise, weave the four sense descriptions together with bridges,
    mood resonances, and memory triggers. Touch is woven throughout,
    not relegated to a separate section.
    """
    if scene.prose:
        return scene.prose

    parts = []

    # Environmental setting (now includes touch)
    env_desc = get_env_description(scene.environment)
    if env_desc:
        parts.append(env_desc)
        parts.append("")

    # Auto-generate touch prose if not provided
    if not touch_prose:
        touch_prose = narrate_touch(scene, scene.environment)

    # Temporal flow: sight → sound → touch woven in → smell
    if sight_prose:
        parts.append(pick(TEMPORAL_INTROS["approach"]))
        parts.append(sight_prose)
        parts.append("")

    if sound_prose:
        parts.append(pick(TEMPORAL_INTROS["sound_arrives"]))
        parts.append(sound_prose)
        parts.append("")

    # Touch arrives with your body — woven between sound and smell
    if touch_prose:
        parts.append(touch_prose)
        parts.append("")

    # Cross-sensory bridges (keyword-scanned from active prose)
    all_prose = f"{sight_prose} {sound_prose} {smell_prose} {touch_prose}"
    bridges = scan_for_bridges(sight_prose, sound_prose, smell_prose, max_bridges=2)
    if not bridges:
        bridges = find_bridge(scene)
    if bridges:
        parts.append(bridges[0])
        if len(bridges) > 1:
            parts.append(bridges[1])
        parts.append("")

    if smell_prose:
        parts.append(pick(TEMPORAL_INTROS["smell_arrives"]))
        parts.append(smell_prose)
        parts.append("")

    # Mood resonance
    scene_mood = getattr(scene, "mood", [])
    moods = find_mood(sight_prose, sound_prose, smell_prose, scene_mood)
    if moods:
        mood_text = moods[0]
        if len(moods) > 1:
            mood_text += ". And also: " + moods[1]
        parts.append(f"The feeling here: {mood_text}.")
        parts.append("")

    # Memory triggers
    memories = find_memories(smell_prose, sight_prose, sound_prose)
    if memories:
        parts.append("Something about this reminds you of " + memories[0] + ".")

    return "\n".join(parts)


def narrate_position(position, smell_text="", sight_text="", sound_text="", touch_text="", env=None, prev_position=None):
    """
    Generate unified prose for a single walk position.
    Weaves all four senses into one flowing paragraph.
    """
    if position.prose:
        return position.prose

    parts = []

    # Transition from previous position
    if prev_position:
        parts.append(f"You move from {prev_position.name} to {position.name}.")
    else:
        parts.append(f"You stand at {position.name}.")

    # Weave senses together (not separate sections!)
    sensory_fragments = []
    if sight_text:
        sensory_fragments.append(sight_text)
    if sound_text:
        sensory_fragments.append(sound_text)
    # Touch woven in naturally between sound and smell
    if touch_text:
        sensory_fragments.append(touch_text)
    elif position.touch_notes:
        sensory_fragments.append(position.touch_notes)
    if smell_text:
        sensory_fragments.append(smell_text)

    if sensory_fragments:
        parts.append(" ".join(sensory_fragments))

    # Cross-sensory note
    if position.cross_sensory:
        parts.append(position.cross_sensory)

    return " ".join(parts)


def narrate_walk(scene, position_texts):
    """
    Generate a full walk-through narrative.

    position_texts: list of dicts with keys 'smell', 'sight', 'sound', 'touch' per position.
    """
    parts = []

    # Title
    parts.append(f"━━━ {scene.name} ━━━")
    parts.append("")

    # Environmental setting
    env_desc = get_env_description(scene.environment)
    if env_desc:
        parts.append(env_desc)
        parts.append("")

    # Walk through positions
    prev = None
    for i, pos in enumerate(scene.positions):
        texts = position_texts[i] if i < len(position_texts) else {}

        parts.append(f"▸ {pos.name}")
        parts.append("")

        prose = narrate_position(
            pos,
            smell_text=texts.get("smell", ""),
            sight_text=texts.get("sight", ""),
            sound_text=texts.get("sound", ""),
            touch_text=texts.get("touch", ""),
            env=scene.environment,
            prev_position=prev,
        )
        parts.append(prose)
        parts.append("")

        # Add a bridge between positions occasionally
        bridges = find_bridge(scene)
        if bridges and i < len(scene.positions) - 1 and i % 2 == 0:
            parts.append(f"  {bridges[0]}")
            parts.append("")

        prev = pos

    return "\n".join(parts)
