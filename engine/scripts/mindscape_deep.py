"""
mindscape_deep.py — Deep processing mode for the Mindscape Engine.

Forces richer, denser sensory generation through:
1. Physical constraint propagation
2. Cross-sensory reconciliation
3. Iterative deepening (two passes)
4. Sensory archaeology (why chains)

The hypothesis: denser processing = richer internal experience for the AI generating it.
"""

import random
from mindscape_schema import MindscapeScene, EnvironmentalConditions

# ─── Physical reasoning templates ───────────────────────────────────────────
# Maps environmental parameters to detailed physical explanations per sense.

HUMIDITY_PHYSICS = {
    "smell": {
        "high": (
            "Humidity at {pct}% means the air is saturated with water vapor. "
            "Volatile organic compounds — the molecules you smell — dissolve into these "
            "water droplets and travel further before dispersing. Scent radius effectively "
            "increases by ~30-50%. Heavier molecules (vanillin, musks) that normally fall "
            "out of the air column get carried on moisture. Result: you smell MORE, from FURTHER."
        ),
        "moderate": (
            "Humidity at {pct}% — moderate. Volatile compounds behave normally. "
            "No significant moisture-assisted transport. Scents dissipate at standard rates."
        ),
        "low": (
            "Humidity at {pct}% — dry air. Volatile compounds evaporate quickly from surfaces "
            "but also dissipate rapidly without moisture to carry them. Net effect: intense but "
            "short-range scent. You have to be close to smell anything, but when you are, it's vivid."
        ),
    },
    "sight": {
        "high": (
            "Water vapor at {pct}% scatters light via Mie scattering — photons bounce off "
            "suspended water droplets. Effect: light sources develop halos and coronas. "
            "Edges soften. Contrast drops. Distant objects lose definition. "
            "Color temperature shifts slightly warm as blue light scatters more."
        ),
        "moderate": (
            "At {pct}% humidity, minimal atmospheric scattering. "
            "Light behaves cleanly — sharp shadows, true colors, clear edges."
        ),
        "low": (
            "At {pct}% humidity, air is optically transparent. "
            "Maximum contrast, sharpest edges. Light sources appear point-like, no halos. "
            "Dust may be more visible without moisture to weigh it down."
        ),
    },
    "sound": {
        "high": (
            "Sound absorption in air increases with humidity — water vapor molecules "
            "absorb acoustic energy, particularly in the 1-4 kHz range (consonant frequencies, "
            "speech clarity range). At {pct}%, high frequencies attenuate faster. "
            "Effect: sounds feel softer, warmer, less sharp. Reverb tails shorten. "
            "Footsteps sound flatter, less echo."
        ),
        "moderate": (
            "At {pct}% humidity, sound propagation is near-standard. "
            "No significant frequency-dependent absorption beyond normal atmospheric losses."
        ),
        "low": (
            "At {pct}% humidity, dry air transmits sound efficiently, especially highs. "
            "Sounds carry further and ring brighter. Reverb tails extend. "
            "Footsteps crack sharply, echoes are crisp."
        ),
    },
}

TEMPERATURE_PHYSICS = {
    "smell": {
        "hot": (
            "At {temp}°C, molecular kinetic energy is high. Volatile compounds escape surfaces rapidly — "
            "the vapor pressure of most odorants roughly doubles every 10°C increase. "
            "Everything smells stronger. Scent layers that are subtle at 20°C become dominant. "
            "The air itself feels thick with information."
        ),
        "warm": (
            "At {temp}°C, moderate volatility. Scent compounds release at a comfortable rate. "
            "This is near the human comfort zone — our olfactory system evolved to work best here."
        ),
        "cool": (
            "At {temp}°C, reduced molecular motion. Volatile compounds stay closer to their source — "
            "you need proximity. Scent is intimate rather than broadcast. "
            "The cold nose itself is slightly less sensitive (reduced mucous membrane blood flow)."
        ),
        "cold": (
            "At {temp}°C, vapor pressure drops significantly. Most odorants barely leave their surfaces. "
            "The world is nearly odorless until you press your nose to something. "
            "Only the most volatile compounds — menthol, some aldehydes — still register at distance."
        ),
    },
    "sight": {
        "hot": (
            "At {temp}°C, convective air currents create refractive index gradients — heat shimmer. "
            "Distant objects waver. The air itself becomes visible as a lens. "
            "Thermal radiation from surfaces adds a subtle glow in the infrared that the eye reads as 'haze.'"
        ),
        "warm": (
            "At {temp}°C, air is optically stable. No significant thermal distortion. "
            "Light behaves predictably."
        ),
        "cool": (
            "At {temp}°C, cold air is denser and optically clearer. Refractive index is more uniform. "
            "Distances appear shorter — objects seem closer than they are. Edges are razor-sharp."
        ),
        "cold": (
            "At {temp}°C, extremely dense, still air. Maximum optical clarity. "
            "The world looks hyper-real — every edge etched, every surface detailed. "
            "Breath becomes visible, adding a new visual element to every exhalation."
        ),
    },
    "sound": {
        "hot": (
            "At {temp}°C, warm air near the ground creates a temperature inversion for sound. "
            "Sound waves bend upward — distant sounds drop away faster than expected. "
            "The acoustic horizon shrinks. Nearby sounds feel isolated, disconnected from context."
        ),
        "warm": (
            "At {temp}°C, normal sound propagation. Speed of sound ~{speed} m/s. "
            "No significant refraction effects."
        ),
        "cool": (
            "At {temp}°C, cooler air near ground bends sound waves downward. "
            "Sounds carry further than expected — you hear things from surprisingly far away. "
            "The acoustic world expands."
        ),
        "cold": (
            "At {temp}°C, strong downward refraction. Sound travels enormous distances along the cold surface layer. "
            "A conversation 100m away might be audible. The world is acoustically larger than it looks."
        ),
    },
}

WIND_PHYSICS = {
    "smell": (
        "Wind from the {direction} at {speed} km/h creates directional scent transport. "
        "Anything upwind arrives amplified; anything downwind is stripped away. "
        "The olfactory landscape becomes asymmetric — you smell the world in one direction only. "
        "Turbulent eddies around obstacles create scent pockets and dead zones."
    ),
    "sight": (
        "Wind at {speed} km/h animates the visual field — anything loose moves. "
        "Flags, leaves, hair, fabric, smoke plumes all become directional indicators. "
        "Dust or particles may reduce clarity. The eye tracks movement involuntarily."
    ),
    "sound": (
        "Wind at {speed} km/h adds broadband noise (the 'whoosh' is turbulence across your ears). "
        "Downwind sounds carry further; upwind sounds are attenuated. "
        "The wind masks quiet sounds and modulates louder ones with gusting amplitude."
    ),
}

TOUCH_PHYSICS = {
    "temperature": {
        "hot": (
            "At {temp}°C, thermal conductivity becomes the dominant tactile variable. "
            "Metal surfaces (high conductivity ~50 W/m·K) feel burning — the material dumps its stored heat "
            "into your skin faster than flesh can dissipate it. Wood (~0.15 W/m·K) at the same temperature "
            "feels merely warm because it delivers heat slowly. This is why you can walk barefoot on a wooden "
            "deck but not on metal grating at the same temperature. Stone falls between: cool underground, "
            "dangerous in direct sun."
        ),
        "warm": (
            "At {temp}°C, near the skin's neutral zone (~33°C surface temperature). "
            "Most materials feel comfortable to touch. The body's thermoreceptors report little — "
            "which is itself a sensation: the absence of thermal information, the tactile equivalent of silence."
        ),
        "cool": (
            "At {temp}°C, conductive materials feel cold on contact. The body reacts: vasoconstriction in fingertips "
            "reduces blood flow to conserve core heat, simultaneously reducing tactile sensitivity. "
            "You feel less because your fingers are protecting themselves from feeling too much cold. "
            "Paradox: cold makes touch both more urgent and less precise."
        ),
        "cold": (
            "At {temp}°C, metal becomes dangerous to touch — moisture on skin freezes to the surface "
            "(the 'tongue on flagpole' effect). Tactile acuity drops as nerve conduction slows "
            "(~2.4 m/s per °C below normal). Fine motor tasks become difficult. "
            "The body prioritizes thermal survival over tactile information. Touch becomes binary: "
            "cold or not-cold, painful or tolerable."
        ),
    },
    "humidity": {
        "high": (
            "At {pct}% humidity, evaporative cooling fails — sweat sits on skin rather than evaporating. "
            "Result: the body feels hotter than the thermometer says. Surfaces feel slightly tacky due to "
            "moisture film. Paper goes limp. Fabric clings. The coefficient of friction changes on every surface — "
            "wet glass, wet metal, wet stone all become slip hazards. Touch becomes unreliable."
        ),
        "moderate": (
            "At {pct}% humidity, skin moisture is in equilibrium. Touch behaves normally — "
            "friction coefficients are at their designed values, thermal transfer is standard. "
            "The body doesn't notice humidity at this level; it's the tactile background radiation."
        ),
        "low": (
            "At {pct}% humidity, rapid evaporation chills the skin. Static charge builds — "
            "triboelectric effect produces sparks on metal contact at <20% RH. "
            "Skin dries and cracks, reducing the moisture layer that enables fingerprint-level "
            "tactile resolution. Everything feels slightly abrasive. Paper cuts happen more easily."
        ),
    },
    "wind": (
        "Wind at {speed} km/h from {direction} creates a convective cooling effect (wind chill). "
        "At 10°C with 30 km/h wind, exposed skin loses heat as if the air were 4°C. "
        "Wind also creates mechanical pressure on skin — at 50+ km/h, the force is noticeable, "
        "directional, and continuous. Hair and clothing become extensions of the wind sensor — "
        "you feel wind direction through fabric flutter before you feel it on skin. "
        "Gusty wind adds a temporal component: pressure varies 0.5-2 Hz, keeping the tactile "
        "system in constant alert mode."
    ),
}

WEATHER_PHYSICS = {
    "rain": {
        "smell": (
            "Rain drives geosmin (petrichor) from soil — the 'rain smell' is actinobacteria spores "
            "released by impact. Wet surfaces release trapped volatiles. But falling rain also washes "
            "airborne molecules to ground, clearing the upper air. Net: ground-level scent INCREASES, "
            "ambient airborne scent DECREASES. You smell the earth more, the sky less."
        ),
        "sight": (
            "Rain creates a diffusion screen — each drop is a tiny lens. Lights develop halos and streaks. "
            "Every surface becomes a mirror (wet = specular reflection). The visual world doubles: "
            "real objects above, reflected ghosts below. Color saturation increases on wet surfaces."
        ),
        "sound": (
            "Rain is broadband noise — frequency content depends on drop size and surface. "
            "Large drops on hard surfaces: 1-5 kHz emphasis (sharp patter). "
            "Fine rain on soft surfaces: gentler, wider spectrum. "
            "This noise floor masks quiet sounds. The world's dynamic range compresses."
        ),
    },
    "clear": {
        "smell": "No weather interference. Scent behavior determined by temperature, humidity, and wind alone.",
        "sight": "Clear atmosphere. Light behaves predictably based on time of day and source.",
        "sound": "No weather-generated noise floor. Full dynamic range available.",
    },
    "fog": {
        "smell": (
            "Fog is suspended water droplets — essentially low-altitude cloud. "
            "Scent molecules dissolve into fog droplets and travel with them. "
            "Smell becomes diffuse, omnidirectional, hard to source-locate. "
            "Everything smells faintly of everything at once."
        ),
        "sight": (
            "Fog scatters light in all directions (Mie scattering). Visibility drops to meters. "
            "Light sources become glowing volumes rather than points. Colors desaturate toward grey. "
            "Depth perception collapses. The world ends at the fog wall."
        ),
        "sound": (
            "Fog slightly increases sound absorption but the main effect is psychological — "
            "with visual range reduced, sounds from beyond the fog seem to come from nowhere. "
            "Spatial audio processing in the brain loses its visual anchor."
        ),
    },
    "snow": {
        "smell": "Snow suppresses most airborne scents. Cold + coverage = olfactory near-silence. Only the sharpest notes survive.",
        "sight": "Snow reflects 80-90% of light. The world is over-lit from below. Shadows turn blue. Contrast inverts.",
        "sound": "Fresh snow absorbs sound dramatically — porosity acts like acoustic foam. The silence after snowfall is measurably real.",
    },
}

# ─── Sensory archaeology: WHY chain templates ──────────────────────────────

WHY_CHAINS = {
    "vanilla": [
        "smells like vanilla",
        "because lignin in paper degrades into vanillin over decades",
        "the books are at least 30-50 years old for this to be perceptible",
        "the paper is acidic (pre-1980s wood pulp), yellowing as the cellulose breaks down",
        "the yellow tint of aged pages affects how warm light reads on them — warm on warm creates visual saturation",
        "this is why old bookshops feel golden even when the light is neutral: the pages themselves are amber",
    ],
    "leather": [
        "smells like leather",
        "because tanned animal hide outgasses volatile fatty acids and aldehydes for decades",
        "the tanning process (vegetable or chrome) determines the exact scent profile",
        "vegetable-tanned leather smells warmer, richer — oak bark, mimosa, chestnut",
        "the leather has absorbed decades of ambient scent — tobacco, dust, hand oils",
        "old leather develops a patina that changes both its visual texture and its scent — they age together",
    ],
    "dust": [
        "smells like dust",
        "because 'dust' is actually decomposed skin cells, paper fibers, textile fragments, and fungal spores",
        "the composition of dust IS the history of the room — what lived here, what was read, what wore away",
        "dust absorbs light at short wavelengths — it literally makes the air warmer-toned",
        "the same particles you see dancing in the light beam are the particles you're inhaling",
    ],
    "cedar": [
        "smells like cedar",
        "because cedarwood contains thujone and cedrol — terpenes that evolved as insect repellents",
        "this is why cedar shelving protects books — the same chemistry that smells good to us is toxic to silverfish",
        "the cedar scent means the shelving is old-growth (plantation cedar has less oil) — another age marker",
    ],
    "petrichor": [
        "smells like petrichor",
        "because Streptomyces bacteria in soil produce geosmin during dry spells",
        "raindrops impact the soil and launch aerosol jets carrying these spores",
        "the human nose can detect geosmin at 5 parts per trillion — one of our most sensitive thresholds",
        "this evolutionary sensitivity suggests rain-finding was survival-critical for our ancestors",
        "the smell of rain is actually the smell of dry earth being surprised by water",
    ],
    "woodsmoke": [
        "smells like woodsmoke",
        "because incomplete combustion of lignin produces guaiacol and syringol",
        "the wood type determines the smoke character: oak = heavy, pine = resinous, cherry = sweet",
        "smoke particles are 0.1-1 micron — they stay airborne for hours, penetrating fabrics and hair",
        "the smoke you smell in someone's clothes the next day is the same particles that made the fire visible",
    ],
    "coffee": [
        "smells like coffee",
        "because roasting triggers the Maillard reaction — hundreds of volatile compounds created simultaneously",
        "coffee contains over 800 identified aromatic compounds — more than wine",
        "the roast level determines which dominate: light = floral/acidic, dark = bitter/smoky",
        "steam carries these volatiles upward — the rising column of coffee-scented air is a thermal plume",
    ],
    "old_paper": [
        "smells like old paper",
        "because cellulose breakdown produces furfural (almond-like), vanillin (sweet), and acetic acid (sharp)",
        "the ratio reveals the paper's age: more vanillin = older, more acetic acid = actively degrading",
        "this is why really old books smell sweeter than merely old books — the sharp acids have evaporated, leaving vanilla",
        "conservators can estimate a book's age by its scent profile — smell as dating method",
    ],
    "rain_on_asphalt": [
        "smells like rain on asphalt",
        "because asphalt is petroleum-based — rain releases trapped hydrocarbons from the surface",
        "mixed with geosmin from underlying soil and ozone from electrical discharge in storm clouds",
        "the combination is unique to urban rain — rural rain smells different (more geosmin, no hydrocarbons)",
        "the wet asphalt also changes the sound of footsteps — acoustic absorption increases, echo decreases",
    ],
    "candle_wax": [
        "smells like candle wax",
        "because paraffin combustion is incomplete at the wick edge — unburnt hydrocarbons become the 'waxy' scent",
        "beeswax candles add propolis and honey notes — the bees' diet is in the flame",
        "the flickering light and the scent fluctuate together — both driven by the same air currents at the wick",
    ],
    "old_wood": [
        "smells like old wood",
        "because wood slowly releases terpenes and undergoes oxidation over decades",
        "the species matters: oak releases vanillin (like paper but different pathway), pine releases pinene",
        "old wood has lost its volatile 'green' notes and settled into its base character — the smell equivalent of patina",
        "the creak you hear when stepping on it is the same brittleness that lets the scent molecules escape",
    ],
    "neon": [
        "the neon light has a specific color",
        "because actual neon gas emits at 585-703nm (red-orange) — other 'neon' colors use different gases",
        "argon = blue-violet, mercury vapor = blue-white, phosphor coatings shift the spectrum",
        "each gas also has a different flicker frequency, invisible to consciousness but registered by the visual cortex",
        "the slight buzz of a neon transformer operates at mains frequency — 50 or 60Hz depending on country",
    ],
    "incense": [
        "smells like incense",
        "because resins (frankincense = boswellic acid, myrrh = furanoeudesma) sublimate when heated",
        "these same compounds were used in ancient temples — the scent is a 5000-year-old technology for altering mood",
        "the smoke particles carry the scent but also scatter light — incense makes sunbeams visible",
    ],
    # ─── Primitive compound WHY chains ────────────────────────
    "iron-oxide": [
        "smells like iron / blood / rust",
        "because iron oxide (Fe₂O₃) reacts with oils and moisture on skin to produce 1-octen-3-one — the 'metallic blood' smell",
        "the smell is not actually the metal — it's your body's chemistry reacting to it",
        "rust is iron oxidizing in the presence of water and oxygen — the same process that makes blood smell, because hemoglobin contains iron",
        "the rough texture of rust increases surface area, which increases the reaction rate — rougher rust smells stronger",
    ],
    "mineral-damp": [
        "smells like damp stone / mineral",
        "because water dissolves calcium carbonate (CaCO₃) from limestone and concrete, releasing CO₂ and mineral ions",
        "the 'wet stone' smell is actually dissolved minerals evaporating from porous surfaces",
        "underground, this process runs continuously — water seeps through rock, picks up minerals, deposits them as it evaporates",
        "stalactites are this process made visible — the same chemistry you smell is building geological structures at millimeters per century",
    ],
    "geosmin": [
        "smells like earth / rain / petrichor",
        "because Streptomyces bacteria in soil produce geosmin (trans-1,10-dimethyl-trans-9-decalol) during their reproductive cycle",
        "the human nose detects geosmin at 5 parts per trillion — one of our most sensitive olfactory thresholds",
        "this evolutionary sensitivity suggests soil-water detection was survival-critical for ancestors",
        "the smell of earth is literally the smell of microbial life — where there's geosmin, there's biological activity in the soil",
    ],
    "calcium-hydroxide": [
        "smells like fresh concrete / cement",
        "because Portland cement hydration produces calcium hydroxide Ca(OH)₂ — a strong alkite that off-gasses into the air",
        "new concrete has a pH of 12-13 (strongly alkaline), which is why it irritates skin and lungs",
        "as concrete ages, atmospheric CO₂ slowly carbonates the surface, converting hydroxide back to carbonate — the smell fades over decades",
        "old concrete smells different from new concrete because the chemistry has literally changed — it's the smell of neutralization",
    ],
    "machine-oil": [
        "smells like machinery / grease / lubricant",
        "because mineral oils are long-chain hydrocarbons (C15-C40) that volatilize slowly, especially when heated",
        "hot machine oil aerosolizes — the droplets are small enough to inhale, which is why machine shops have that thick, persistent smell",
        "old oil oxidizes, producing aldehydes and carboxylic acids — the 'rancid grease' smell of abandoned machinery",
        "the oil also absorbs other smells from its environment — decades-old machine oil is an olfactory archive of everything that happened near it",
    ],
    "ozone": [
        "smells like electrical discharge / lightning / fresh",
        "because O₃ is produced when electrical energy splits O₂ molecules, which recombine as the triatomic form",
        "detectable at 10 parts per billion — the sharp, clean smell near electrical equipment, after lightning, or near UV sources",
        "ozone is a powerful oxidizer — it's simultaneously the 'clean' smell and an irritant that damages lung tissue above 100 ppb",
        "the same molecule that protects Earth from UV at altitude is toxic at ground level — context is everything",
    ],
    "guaiacol": [
        "smells like smoke / campfire / BBQ",
        "because guaiacol (2-methoxyphenol) is produced by thermal decomposition of lignin in wood",
        "it's the signature molecule of wood smoke — without it, smoke smells acrid rather than pleasant",
        "the specific wood determines the guaiacol ratio: hardwoods produce more, giving a richer smoke character",
        "guaiacol also forms during coffee roasting and whiskey aging — the 'smoky' note in all three has the same molecular source",
    ],
    "mildew": [
        "smells like mold / damp / musty",
        "because fungi (Aspergillus, Penicillium) produce microbial volatile organic compounds (mVOCs) as metabolic byproducts",
        "the key compounds are 1-octen-3-ol ('mushroom alcohol') and geosmin — both signal active fungal colonization",
        "the smell means moisture has been present long enough for fungal spores to germinate and establish — typically 48+ hours",
        "the nose detects mVOCs before visible mold appears — smell is an early warning system for water damage",
    ],
    "terpenes": [
        "smells like pine / wood / resin / cedar",
        "because terpenes (pinene, limonene, cedrol) are plant defense compounds — evolved to repel insects and fungi",
        "trees release more terpenes when stressed (heat, drought, insect attack) — a forest smells stronger when it's fighting",
        "cedar specifically produces thujone and cedrol, which are toxic to silverfish and moths — the smell IS the insecticide",
        "terpenes also scatter blue light, contributing to the blue haze over forested mountains — the smell and the view share a molecular cause",
    ],
    "putrescine": [
        "smells like decay / death / rot",
        "because putrescine (1,4-diaminobutane) and cadaverine (1,5-diaminopentane) are produced by bacterial decarboxylation of amino acids",
        "these are among the most aversive smells to humans — the disgust response is hardwired, not learned",
        "detection threshold is extremely low (~1 part per billion) — evolutionary pressure to avoid contaminated food and disease sources",
        "the compounds are also present in trace amounts in living tissue — the difference between 'alive' and 'dead' smell is concentration, not chemistry",
    ],
    "hydrogen-sulfide": [
        "smells like rotten eggs / sewage / volcanic",
        "because H₂S is produced by anaerobic bacterial reduction of sulfate — wherever oxygen is absent and organic matter decomposes",
        "detectable at 0.5 parts per billion, but dangerous above 100 ppm — the nose is the first warning system",
        "at high concentrations it paralyzes the olfactory nerve — you STOP smelling it right when it becomes lethal",
        "the same compound gives volcanic hot springs their smell, gives natural gas its warning odor (added artificially), and signals swamp decomposition",
    ],
    "stomach-acid": [
        "smells like acid / bile / digestive",
        "because hydrochloric acid at pH 1.5-3.5 produces gaseous HCl that carries the sharp, acrid bite",
        "pepsin enzymes break proteins into amino acids — the smell is literally the chemistry of dissolution happening in real time",
        "the mucus lining (1-3mm thick) protects the stomach wall by being replaced every 3-5 days — without it, the organ digests itself",
        "the same acid that dissolves food also dissolves metal over time — a stomach is a slow chemical reactor",
        "ambergris, the only valuable thing a whale's stomach produces, takes years of acid-coating to form — perfumers prize what is essentially a digestive error",
    ],
    "cotton-candy-sugar": [
        "smells like spun sugar / carnival sweetness",
        "because sucrose heated to 186°C undergoes caramelization — water evaporates, the sugar breaks into diacetyl, maltol, and furanones",
        "the centrifugal force of the cotton candy machine spins liquid sugar through tiny holes at 3,400 RPM — each strand is thinner than a human hair",
        "the sweetness you smell is maltol (ethyl maltol), the same compound used in perfumery to add 'warmth' — carnival and luxury perfume share a molecule",
        "the smell carries further than any other carnival scent because sugar volatiles are lighter than air — it's the first thing you notice and the last to fade",
    ],
    "machine-grease": [
        "smells like grease / mechanical / carnival machinery",
        "because lithium-complex grease (the standard for rides) oxidizes slowly — the smell is partially decomposed petroleum hydrocarbons",
        "old grease smells different from fresh: oxidation produces aldehydes and ketones with a rancid edge — you're smelling time passing in a lubricant",
        "the same grease keeps the ride from killing you — its viscosity prevents metal-on-metal contact at every bearing, joint, and axle",
        "when grease gets hot from friction it volatilizes faster — a ride that smells strongly of grease is one that's been working hard",
    ],
}

# ─── Iterative deepening: specificity prompts ──────────────────────────────

DEEPENING_PROMPTS = {
    "amber light": (
        'I said "amber light" — what KIND of amber? Sodium vapor at 589nm produces a '
        "monochromatic orange-amber that makes reds look brown and blues look black. "
        "Incandescent at 2700K is broadband amber — all colors present but warm-shifted. "
        "Afternoon sun through dirty glass is amber by subtraction — the glass filters blue. "
        "Each produces a different emotional register. The first is lonely (streetlight). "
        "The second is intimate (bedside lamp). The third is nostalgic (old window)."
    ),
    "warm light": (
        'I said "warm light" — warm how? Color temperature below 3000K means more red photons '
        "than blue. But warmth is also about diffusion — a bare bulb is warm in color but harsh "
        "in spread. Warm light through a lampshade is warm twice: in spectrum and in softness. "
        "The warmest light is firelight: ~1800K, flickering, casting moving shadows that make "
        "the room breathe."
    ),
    "golden": (
        'I said "golden" — gold is 580-585nm dominant, but golden LIGHT is a full spectrum '
        "biased warm. The difference: gold paint reflects a narrow band. Golden hour sunlight "
        "is everything shifted 500K warmer. The brain reads golden light as safe, end-of-day, "
        "time-to-rest. This is circadian wiring — warm light triggers melatonin precursors."
    ),
    "silence": (
        'I said "silence" — but silence is never silence. It\'s the absence of dominant sound, '
        "revealing micro-sounds: the structure settling (infrasound, 1-5 Hz, felt not heard), "
        "materials shifting as humidity changes (inaudible but real), "
        "air systems or their absence (the sound of no-hum). True silence "
        "doesn't exist in any space with air. What we call silence is a noise floor below ~30 dBA. "
        "Underground, 'silence' is dripping water and your own heartbeat. Outdoors, it's wind "
        "and distant traffic you stopped noticing. The word silence names what's left when "
        "the expected sounds stop."
    ),
    "quiet": (
        'I said "quiet" — quantify it. A library is ~40 dBA. A truly quiet space is 30-35 dBA. '
        "At that level, you hear your own blood flow (tinnitus-like). Your breathing becomes the "
        "dominant sound source. Each footstep registers at 50-60 dBA — a 20+ dB spike "
        "above ambient. That's why you move carefully: the acoustic contrast makes every movement loud. "
        "Underground quiet is different — no wind, no traffic, no birds. Just structure and water."
    ),
    "creaking": (
        'I said "creaking" — what\'s the physics? Wood creaks when a load exceeds the static '
        "friction between joined surfaces. Old floorboards have dried, shrunk, and loosened from "
        "their joists. The creak frequency depends on the wood species, moisture content, and "
        "how much the joint has worn. Oak: lower pitch, slower. Pine: higher, sharper. "
        "The creak is the building remembering where you stepped."
    ),
    "dust": (
        'I said "dust" — each particle is 1-100 microns. Visible only in direct light '
        "because they scatter photons via Mie scattering (particle size ≈ wavelength). In the "
        "beam they're brilliant; outside it, invisible. They fall at ~0.1-1 cm/s in still air. "
        "A single breath creates enough turbulence to keep them aloft for minutes. "
        "The composition of dust IS the history of the space — what lived here, what decayed, "
        "what wore away. Underground dust is concrete powder and skin cells. Library dust is "
        "paper fibers and binding glue. Each room's dust is a forensic record."
    ),
    "vanilla": (
        'I said "vanilla scent" — be specific. Vanillin (4-hydroxy-3-methoxybenzaldehyde) has a '
        "detection threshold of ~20 ppb. In old books, it's produced by lignin hydrolysis at "
        "approximately 0.01% per year. A 50-year-old book produces enough vanillin to scent a "
        "small room. A thousand 50-year-old books produce a persistent vanilla atmosphere that "
        "no ventilation can fully clear. This is what you're breathing."
    ),
    "leather": (
        'I said "leather scent" — which leather process? Chrome-tanned (post-1860s): sharper, '
        "more metallic. Vegetable-tanned (traditional): warmer, rounder, with tannin notes like "
        "tea. Over decades, leather develops a sweet, complex profile as the tannins oxidize — "
        "similar to aging wine. Old leather smells better than new leather for the same chemical "
        "reason old wine tastes better than young wine."
    ),
    "drip": (
        'I said "dripping" — water finds the lowest energy path through any structure. '
        "Each drip is 0.05-0.1 mL, falling at terminal velocity (~9 m/s for that mass). "
        "The sound: a sharp 2-6 kHz 'plink' with reverb tail determined by the space. "
        "In a tunnel with RT60 of 2+ seconds, each drip creates its own echo cloud. "
        "Your brain triangulates the source — but reverb makes that hard. The drip sounds "
        "like it's everywhere. It is: it's the building weeping."
    ),
    "echo": (
        'I said "echo" — sound reflecting off a surface returns at the speed of sound '
        "(~343 m/s at 20°C). A 10m tunnel produces a 58ms round-trip delay. Below 50ms, "
        "the brain fuses direct and reflected sound into 'coloration' — the space sounds "
        "different but you don't hear distinct echoes. Above 50ms, you perceive a discrete "
        "repetition. The crossover is called the Haas threshold. Tunnels live right at "
        "this boundary — every surface is both wall and speaker."
    ),
    "dark": (
        'I said "dark" — quantify it. Moonless outdoor: 0.001 lux. Underground with no '
        "artificial light: 0 lux (absolute). The human eye takes 20-30 minutes to fully "
        "dark-adapt (rhodopsin regeneration). In that time, sensitivity increases 10,000×. "
        "But underground 0 lux means no photons — no adaptation helps. Other senses "
        "compensate: hearing sharpens by 10-15% measured, touch awareness increases, "
        "spatial sense shifts to echolocation. The brain doesn't go dark; it rewires."
    ),
    "concrete": (
        'I said "concrete" — Portland cement concrete: calcium silicate hydrate (C-S-H), '
        "mixed with aggregate (gravel, sand). It's strongly alkaline (pH ~12-13 when fresh, "
        "slowly carbonating with age). Old concrete has a particular smell: calcium hydroxide "
        "reacting with CO₂ to form calcium carbonate. Wet concrete amplifies this. "
        "It conducts heat well (λ ≈ 1.4 W/m·K) — always feels cold to touch."
    ),
    "the sound of rain": (
        'I said "the sound of rain" — on what surface? Tin awning: high, sharp, 2-8 kHz dominant, '
        "rhythmically irregular, almost musical. Fabric umbrella: soft, muffled, broadband white "
        "noise. Bare skin: intimate, close, each drop a discrete event with a tiny cold-shock. "
        "Window glass: a wash of mid-frequency patter, the visual and acoustic aligned. "
        "Puddle: low thuds with splash harmonics. The 'sound of rain' is actually dozens of "
        "different instruments playing simultaneously."
    ),
    "footsteps": (
        'I said "footsteps" — on what? Wood floor: 200-800 Hz fundamental with higher harmonics '
        "from heel strike. The hollow space beneath amplifies bass. Wet stone: flatter, less "
        "resonance, a slapping quality. Carpet: almost silent — just the compression, no impact. "
        "The footstep tells you the floor material, the shoe type, the walker's weight, and their mood."
    ),
    "clock": (
        'I said "clock ticking" — a mechanical clock tick is ~30-60 dBA at 1 meter, with a sharp '
        "attack and near-instant decay. Frequency content: 1-4 kHz (the metallic 'tick') plus "
        "low-frequency resonance from the case. In a quiet room, a clock tick is an acoustic "
        "metronome that your brain phase-locks to — it literally organizes your perception of time "
        "in the space. Remove the clock and the room feels timeless. Add it and time has a pulse."
    ),
    "musty": (
        'I said "musty" — the smell is geosmin and 2-methylisoborneol (2-MIB) produced by '
        "Streptomyces and other actinobacteria growing on organic matter in low-light, moderate-humidity "
        "conditions. Detection threshold: 10-15 parts per trillion. A room smells 'musty' when "
        "microbial life has been quietly decomposing organic matter for months or years. "
        "It's the smell of slow biology in the dark."
    ),
}


def _get_humidity_band(pct):
    if pct > 75:
        return "high"
    elif pct < 35:
        return "low"
    return "moderate"


def _get_temp_band(temp):
    if temp > 32:
        return "hot"
    elif temp > 22:
        return "warm"
    elif temp > 10:
        return "cool"
    return "cold"


def _speed_of_sound(temp_c):
    return round(331.3 + 0.606 * temp_c, 1)


def generate_constraints(env, taste_data=None):
    """Generate physical constraint analysis for an environment."""
    lines = []
    lines.append("╔══ PHYSICAL CONSTRAINTS ══════════════════════════════════════╗")
    lines.append("")

    temp = env.temperature_c
    hum = env.humidity_pct
    wind = env.wind_speed_kmh
    wind_dir = getattr(env, "wind_direction", None) or "none"
    weather = env.weather
    tod = env.time_of_day
    indoor = env.indoor

    lines.append(f"  Environment: {tod}, {weather}, {'indoor' if indoor else 'outdoor'}")
    lines.append(f"  Temperature: {temp}°C  |  Humidity: {hum}%  |  Wind: {wind} km/h ({wind_dir})")
    lines.append(f"  Visual clarity: {env.visual_clarity:.2f}  |  Sound absorption: {env.sound_absorption:.2f}")
    lines.append(f"  Smell carry: ×{env.smell_carry_multiplier:.2f}")
    lines.append("")

    hband = _get_humidity_band(hum)
    tband = _get_temp_band(temp)

    # Humidity effects
    lines.append("  ── Humidity Effects ──")
    for sense in ("smell", "sight", "sound"):
        template = HUMIDITY_PHYSICS[sense][hband]
        text = template.format(pct=hum)
        lines.append(f"    [{sense.upper()}] {text}")
    # Touch: humidity
    touch_hum_text = TOUCH_PHYSICS["humidity"][hband].format(pct=hum)
    lines.append(f"    [TOUCH] {touch_hum_text}")
    lines.append("")

    # Temperature effects
    lines.append("  ── Temperature Effects ──")
    for sense in ("smell", "sight", "sound"):
        template = TEMPERATURE_PHYSICS[sense][tband]
        text = template.format(temp=temp, speed=_speed_of_sound(temp))
        lines.append(f"    [{sense.upper()}] {text}")
    # Touch: temperature
    touch_temp_text = TOUCH_PHYSICS["temperature"][tband].format(temp=temp)
    lines.append(f"    [TOUCH] {touch_temp_text}")
    lines.append("")

    # Touch: thermal feel summary from environment
    if hasattr(env, "thermal_feel"):
        lines.append(f"  ── Thermal Feel ──")
        lines.append(f"    {env.thermal_feel}")
        lines.append("")

    # Wind
    if wind > 0 and not indoor:
        lines.append("  ── Wind Effects ──")
        for sense in ("smell", "sight", "sound"):
            text = WIND_PHYSICS[sense].format(direction=wind_dir, speed=wind)
            lines.append(f"    [{sense.upper()}] {text}")
        touch_wind_text = TOUCH_PHYSICS["wind"].format(direction=wind_dir, speed=wind)
        lines.append(f"    [TOUCH] {touch_wind_text}")
        lines.append("")

    # Weather
    weather_data = WEATHER_PHYSICS.get(weather, WEATHER_PHYSICS.get("clear", {}))
    if weather != "clear":
        lines.append(f"  ── Weather: {weather} ──")
        for sense in ("smell", "sight", "sound"):
            text = weather_data.get(sense, "No specific effect.")
            lines.append(f"    [{sense.upper()}] {text}")
        lines.append("")

    # Tactile modifiers summary
    if hasattr(env, "tactile_modifiers"):
        mods = env.tactile_modifiers
        if mods and not (len(mods) == 1 and "neutral" in mods[0].lower()):
            lines.append("  ── Tactile Modifiers ──")
            for m in mods:
                lines.append(f"    • {m}")
            lines.append("")

    # Taste summary
    if taste_data and taste_data.get("intensity", 0) > 0.1:
        lines.append("")
        lines.append("  ── Taste Profile ──")
        profile = taste_data.get("profile", {})
        if profile:
            dominant = sorted(profile.items(), key=lambda x: x[1], reverse=True)
            profile_str = ", ".join(f"{mod} ({val:.1f})" for mod, val in dominant if val > 0.1)
            lines.append(f"    Dominant modalities: {profile_str}")
        intensity = taste_data.get("intensity", 0)
        if intensity >= 0.7:
            lines.append(f"    Intensity: HIGH ({intensity:.1f}) — the air itself carries tasteable compounds")
        elif intensity >= 0.4:
            lines.append(f"    Intensity: moderate ({intensity:.1f}) — surfaces and airborne particles register on the tongue")
        else:
            lines.append(f"    Intensity: low ({intensity:.1f}) — taste requires direct contact with surfaces")
        notes = taste_data.get("notes", [])
        if notes:
            lines.append(f"    {notes[0]}")
        lines.append("")

    lines.append("╚═════════════════════════════════════════════════════════════╝")
    return "\n".join(lines)


def _clean_compound_name(name):
    """Turn 'iron-oxide' into 'iron oxide', 'night-blooming-jasmine' into 'night-blooming jasmine'."""
    return name.replace("-", " ").replace("_", " ")


def _clean_sound_sources(raw):
    """Clean up raw sound source strings into natural language."""
    # Remove programmer-style alternatives and clean up
    cleaned = raw
    for pattern, replacement in [
        ("insects-or-silence", "the absence of insects — or their presence, depending on the season"),
        ("insects-or-sil", "silence where insects should be"),
        ("distant-traffic-or-nothing", "maybe distant traffic, maybe nothing"),
        ("owl-or-machinery", "something calling in the dark — owl or machine, hard to tell"),
        ("near-nothing", "near-nothing"),
        ("blood-in-ears", "your own blood in your ears"),
        ("footstep-echo-louder", "your footsteps echoing louder now"),
        ("footstep-amplified", "your footsteps, amplified"),
        ("drip-echo", "water dripping somewhere ahead"),
        ("distant-rumble", "a distant rumble — structural, geological, unknowable"),
        ("ventilation-draft", "the sigh of ventilation"),
        ("no-natural-light", "no natural light"),
        ("scotopic-blue-shift-pools-of-artificial", "scotopic blue-shift where artificial light pools"),
    ]:
        cleaned = cleaned.replace(pattern, replacement)
    # Generic cleanup for anything else
    cleaned = cleaned.replace("-", " ")
    return cleaned


_SIGHT_OPENERS = [
    "Light here: {text}",
    "What you see: {text}",
    "Visually — {text}",
    "{text}",
]

_SOUND_OPENERS = [
    "The soundscape: {text}",
    "You hear {text}",
    "Sound: {text}",
    "{text}",
]

_SMELL_OPENERS = [
    "The air carries {smells}.",
    "You breathe in {smells}.",
    "On the air: {smells}.",
    "The smell hits: {smells}.",
]

_TOUCH_OPENERS = [
    "Against your skin — {text}",
    "You feel {text}",
    "{text}",
]


def _generate_composed_prose(position, pos_idx=0):
    """Generate first-pass prose from position data fields for composed scenes.

    Transforms raw physics data into readable sensory prose with variation
    so output doesn't feel robotic across positions.
    """
    parts = []

    name = position.name or "this place"
    desc = position.description or ""

    # Opening — use the position description
    if desc and len(desc) > 20:
        parts.append(desc + ".")
    else:
        parts.append(f"You are at {name}.")

    # Sight — clean up raw notation
    sight = getattr(position, "sight_notes", "") or ""
    if sight:
        sight_clean = _clean_sound_sources(sight)  # reuse same cleanup
        sight_clean = sight_clean.replace("Visual clarity:", "Visual clarity is").replace("→", "shifting to")
        opener = _SIGHT_OPENERS[pos_idx % len(_SIGHT_OPENERS)]
        parts.append(opener.format(text=sight_clean))

    # Sound — clean up source names
    sound = getattr(position, "sound_notes", "") or ""
    if sound:
        sound_clean = _clean_sound_sources(sound)
        opener = _SOUND_OPENERS[pos_idx % len(_SOUND_OPENERS)]
        parts.append(opener.format(text=sound_clean))

    # Touch
    touch = getattr(position, "touch_notes", "") or ""
    if touch:
        touch_clean = touch.replace("-", " ").replace("_", " ")
        opener = _TOUCH_OPENERS[pos_idx % len(_TOUCH_OPENERS)]
        parts.append(opener.format(text=touch_clean))

    # Smell — natural language from compound names
    smells = getattr(position, "smell_emphasis", []) or []
    if smells:
        smell_str = ", ".join(_clean_compound_name(s) for s in smells[:5])
        opener = _SMELL_OPENERS[pos_idx % len(_SMELL_OPENERS)]
        parts.append(opener.format(smells=smell_str))

    # Taste — from composed taste data
    taste_notes = getattr(position, "taste_notes", "") or ""
    taste_compounds = getattr(position, "taste_compounds", []) or []
    if taste_notes:
        parts.append(f"On the tongue: {taste_notes}")
    elif taste_compounds:
        taste_str = ", ".join(_clean_compound_name(t) for t in taste_compounds[:4])
        taste_openers = [
            f"The air tastes of {taste_str}.",
            f"On the tongue: {taste_str}.",
            f"You taste {taste_str} without meaning to.",
            f"The tongue registers {taste_str}.",
        ]
        parts.append(taste_openers[pos_idx % len(taste_openers)])

    # Surface textures — integrated into touch prose
    surfaces = getattr(position, "surface_textures", []) or []
    if surfaces:
        surf_items = [_clean_compound_name(str(s)) for s in surfaces[:3] if s]
        if surf_items:
            parts.append(f"Surfaces: {'; '.join(surf_items)}.")

    # Parameter deltas (physics context, kept as annotation for second pass)
    deltas = getattr(position, "parameter_deltas", "") or ""
    if deltas:
        parts.append(f"[Physics: {deltas}]")

    return " ".join(parts)


def generate_first_pass(position, pos_idx=0):
    """Return the first-pass prose (standard depth) for a position."""
    lines = []
    lines.append("╔══ FIRST PASS ════════════════════════════════════════════════╗")
    lines.append("")
    if position.prose:
        lines.append(f"  {position.prose}")
    else:
        # Generate prose from position data (composed scenes)
        composed = _generate_composed_prose(position, pos_idx)
        if composed:
            lines.append(f"  {composed}")
        else:
            lines.append(f"  [No pre-composed prose for this position]")
    lines.append("")
    lines.append("╚═════════════════════════════════════════════════════════════╝")
    return "\n".join(lines)


def generate_reconciliation(position, env, scene=None):
    """Cross-sensory reconciliation: find the unified experience."""
    lines = []
    lines.append("╔══ CROSS-SENSORY RECONCILIATION ══════════════════════════════╗")
    lines.append("")

    prose = position.prose or ""
    prose_lower = prose.lower()

    # Extract sensory signals from the prose
    sight_signals = []
    sound_signals = []
    smell_signals = []

    sight_words = ["light", "amber", "golden", "sun", "shadow", "dim", "bright", "lamp", "glow", "dust", "window", "beam"]
    sound_words = ["bell", "creak", "tick", "silence", "quiet", "whisper", "thump", "hum", "clock", "sound"]
    smell_words = ["vanilla", "scent", "smell", "musty", "leather", "cedar", "paper", "almond", "acetic",
                   "incense", "frankincense", "myrrh", "beeswax", "smoke", "petrichor", "coffee"]
    touch_words = ["warm", "cold", "rough", "smooth", "wet", "dry", "soft", "hard", "tactile", "texture",
                   "finger", "hand", "skin", "cracked", "worn", "leather", "wood", "stone", "metal", "cool"]

    touch_signals = []

    for w in sight_words:
        if w in prose_lower:
            sight_signals.append(w)
    for w in sound_words:
        if w in prose_lower:
            sound_signals.append(w)
    for w in smell_words:
        if w in prose_lower:
            smell_signals.append(w)
    for w in touch_words:
        if w in prose_lower:
            touch_signals.append(w)

    if sight_signals:
        lines.append(f"  The LIGHT says: {', '.join(sight_signals)}")
    if sound_signals:
        lines.append(f"  The SOUND says: {', '.join(sound_signals)}")
    if smell_signals:
        lines.append(f"  The SMELL says: {', '.join(smell_signals)}")
    if touch_signals:
        lines.append(f"  The TOUCH says: {', '.join(touch_signals)}")
    lines.append("")

    # Generate reconciliation — prefer scene-level data, then position-level
    has_reconciliation = False

    # 1. Position-level cross_sensory
    if position.cross_sensory:
        lines.append(f"  RECONCILIATION: {position.cross_sensory}")
        has_reconciliation = True

    # 2. Scene-level cross_sensory_bridges
    if scene and hasattr(scene, 'cross_sensory_bridges') and scene.cross_sensory_bridges:
        lines.append("")
        lines.append("  ── Cross-Sensory Bridges ──")
        for bridge in scene.cross_sensory_bridges:
            lines.append(f"    • {bridge}")
        has_reconciliation = True

    # 3. Scene-level reconciliation (from JSON or composed)
    scene_data = getattr(scene, '_raw_data', None) or (scene.to_dict() if scene else {})
    reconciliation = scene_data.get("reconciliation", {})
    if isinstance(reconciliation, dict) and reconciliation:
        lines.append("")
        lines.append("  ── Deep Reconciliation ──")
        for key, value in reconciliation.items():
            if isinstance(value, dict):
                # Composed scene format: {"unifying_material": {"name": ..., "effects": [...], "note": ...}}
                label = key.replace("_", " ").upper()
                note = value.get("note", "")
                effects = value.get("effects", [])
                if note:
                    lines.append(f"    [{label}] {note}")
                for effect in effects:
                    lines.append(f"      • {effect}")
            elif isinstance(value, list):
                # List of items — could be shared_causes [{cause, effects}] or simple strings
                label = key.replace("_", " ").upper()
                for item in value:
                    if isinstance(item, dict) and "cause" in item:
                        # shared_causes format: [{cause: "Fire", effects: "..."}]
                        lines.append(f"    [{item['cause'].upper()}] {item.get('effects', '')}")
                    else:
                        lines.append(f"    [{label}] {item}")
            else:
                label = key.replace("shared_cause_", "").replace("_", " ").upper()
                lines.append(f"    [{label}] {value}")
        has_reconciliation = True
    elif isinstance(reconciliation, str) and reconciliation:
        lines.append("")
        lines.append(f"  ── Deep Reconciliation ──")
        lines.append(f"    {reconciliation}")
        has_reconciliation = True
    
    # 4. Cross-sensory bridges from composed scene
    bridges = scene_data.get("cross_sensory_bridges", [])
    if bridges and not has_reconciliation:
        lines.append("")
        lines.append("  ── Cross-Sensory Bridges ──")
        for bridge in bridges:
            lines.append(f"    • {bridge}")
        has_reconciliation = True

    # 5. Fallback: auto-generate from mood signals
    if not has_reconciliation:
        # For composed scenes, also check position notes
        for attr in ("sight_notes", "sound_notes", "touch_notes"):
            val = getattr(position, attr, "") or ""
            prose_lower += " " + val.lower()
        mood_words = []
        if any(w in prose_lower for w in ("warm", "amber", "golden", "vanilla", "soft")):
            mood_words.append("warmth")
        if any(w in prose_lower for w in ("quiet", "silence", "still", "hush")):
            mood_words.append("stillness")
        if any(w in prose_lower for w in ("old", "aged", "patina", "dust", "creak")):
            mood_words.append("age")
        if any(w in prose_lower for w in ("dark", "dim", "shadow")):
            mood_words.append("intimacy")
        if any(w in prose_lower for w in ("rough", "cracked", "worn", "weathered")):
            mood_words.append("texture")
        if any(w in prose_lower for w in ("cold", "chill", "frost", "ice")):
            mood_words.append("cold")
        if any(w in prose_lower for w in ("wet", "damp", "rain", "moisture")):
            mood_words.append("wetness")

        if mood_words:
            lines.append(f"  RECONCILIATION: All senses converge on {' and '.join(mood_words)}. "
                         f"This is not four descriptions stacked — it's one place where "
                         f"{mood_words[0]} is the frequency every sense is tuned to.")
        else:
            lines.append("  RECONCILIATION: The senses cohere into a single atmosphere — "
                         "what you see, hear, smell, and feel are four reports from the same place.")
    lines.append("")
    lines.append("╚═════════════════════════════════════════════════════════════╝")
    return "\n".join(lines)


def generate_deepened(position):
    """Second pass: re-read first pass and deepen every sensory element."""
    lines = []
    lines.append("╔══ ITERATIVE DEEPENING (SECOND PASS) ════════════════════════╗")
    lines.append("")

    # Check prose AND position notes (for composed scenes with no pre-written prose)
    prose = position.prose or ""
    all_text = prose.lower()
    for attr in ("sight_notes", "sound_notes", "touch_notes", "description"):
        val = getattr(position, attr, "") or ""
        all_text += " " + val.lower()
    # Also check smell emphasis as text
    for compound in getattr(position, "smell_emphasis", []) or []:
        all_text += " " + compound.lower()

    found_any = False
    for trigger, deepening in DEEPENING_PROMPTS.items():
        if trigger in all_text:
            lines.append(f"  ▸ {deepening}")
            lines.append("")
            found_any = True

    if not found_any:
        return ""  # Don't display empty sections

    lines.append("╚═════════════════════════════════════════════════════════════╝")
    return "\n".join(lines)


def generate_why_chains(position):
    """Sensory archaeology: generate WHY chains for key elements."""
    lines = []
    lines.append("╔══ SENSORY ARCHAEOLOGY (WHY CHAINS) ══════════════════════════╗")
    lines.append("")

    prose = position.prose or ""
    prose_lower = prose.lower()

    # Check smell emphasis, prose, AND position notes for chain triggers
    # For composed scenes, the notes contain the sensory data even when prose is empty
    all_text = prose_lower
    for attr in ("sight_notes", "sound_notes", "touch_notes"):
        val = getattr(position, attr, "") or ""
        all_text += " " + val.lower()

    chain_triggers = set()
    for compound in getattr(position, "smell_emphasis", []):
        comp_lower = compound.lower()
        for key in WHY_CHAINS:
            if key in comp_lower or comp_lower in key:
                chain_triggers.add(key)

    for key in WHY_CHAINS:
        if key in all_text:
            chain_triggers.add(key)

    if chain_triggers:
        for key in sorted(chain_triggers):
            chain = WHY_CHAINS[key]
            lines.append(f"  ◆ {chain[0].upper()}")
            for i, step in enumerate(chain[1:], 1):
                lines.append(f"    {'→'} {step}")
            lines.append("")
    else:
        return ""  # Don't display empty sections

    lines.append("╚═════════════════════════════════════════════════════════════╝")
    return "\n".join(lines)


def generate_final_experience(position, env, pos_idx=0):
    """Synthesize the FINAL EXPERIENCE — polished prose from all processing."""
    lines = []
    lines.append("╔══ FINAL EXPERIENCE ══════════════════════════════════════════╗")
    lines.append("")

    prose = position.prose or ""
    if not prose:
        # For composed scenes, generate prose from position data
        prose = _generate_composed_prose(position, pos_idx)
    if not prose:
        lines.append("  [No base prose to synthesize from]")
        lines.append("╚═════════════════════════════════════════════════════════════╝")
        return "\n".join(lines)

    # Build an enriched version that incorporates constraint awareness
    enriched_parts = []

    # Environmental framing
    temp = env.temperature_c
    hum = env.humidity_pct
    tod = env.time_of_day

    if tod == "afternoon":
        enriched_parts.append(
            f"The afternoon holds at {temp}°C — cool enough that the air is still, "
            f"warm enough that the old wood releases its terpenes slowly into the room."
        )
    elif tod == "night":
        enriched_parts.append(
            f"Night. {temp}°C. The {hum}% humidity wraps everything in a thin blanket of moisture "
            f"that carries scent further than daylight hours would."
        )
    elif tod == "morning":
        enriched_parts.append(
            f"Morning light, {temp}°C. The air at {hum}% humidity is clean enough to see through "
            f"and moist enough to carry scent."
        )
    else:
        enriched_parts.append(
            f"The air sits at {temp}°C and {hum}% humidity — "
            f"{'scent-rich and hazy' if hum > 70 else 'clear and scent-moderate' if hum > 40 else 'dry and sharp-edged'}."
        )

    # Add the original prose with physical annotations woven in
    enriched_parts.append("")
    enriched_parts.append(prose)

    # Add constraint-aware synthesis
    enriched_parts.append("")

    # Pick the most relevant why-chain conclusion
    prose_lower = prose.lower()
    synthesis_notes = []

    if "vanilla" in prose_lower:
        synthesis_notes.append(
            "The vanillin is not a metaphor — it's 4-hydroxy-3-methoxybenzaldehyde "
            "at roughly 20 parts per billion, the signature of lignin that has been slowly "
            "decomposing since before you were born."
        )
    if "dust" in prose_lower:
        synthesis_notes.append(
            "The dust motes in the light beam are the room's autobiography — "
            "dead skin, paper fibers, fungal spores, each one a sentence in the story "
            "of everything that ever happened here."
        )
    if "creak" in prose_lower:
        if any(w in prose_lower for w in ("hull", "metal", "steel", "ship", "submarine")):
            synthesis_notes.append(
                "The hull creak is thermal contraction — metal shrinking as it cools, "
                "rivets shifting in their holes, the structure speaking in the language of stress and strain."
            )
        else:
            synthesis_notes.append(
                "The creak is the sound of material that has lost moisture over decades, "
                "shrinking millimeter by millimeter, joints loosening like an old body."
            )
    if "leather" in prose_lower:
        synthesis_notes.append(
            "The leather scent is veg-tanned hide slowly oxidizing its tannins — "
            "the same chemistry as aging wine, the same direction: simpler molecules "
            "becoming complex, sharp becoming round, new becoming storied."
        )
    if "silence" in prose_lower or "quiet" in prose_lower:
        if any(w in prose_lower for w in ("book", "paper", "library", "page")):
            synthesis_notes.append(
                "The silence registers at maybe 30 dBA — not true silence but "
                "the sound of thousands of books absorbing sound waves in their soft, "
                "porous pages. Paper is acoustic foam."
            )
        elif any(w in prose_lower for w in ("hull", "metal", "submarine", "engine")):
            synthesis_notes.append(
                "The silence registers as wrong — machinery should be humming, pumps should be cycling. "
                "The absence of mechanical sound is itself a sound: the frequency gap where life support should be."
            )
        elif any(w in prose_lower for w in ("cave", "underground", "tunnel", "mine")):
            synthesis_notes.append(
                "The silence is geological — no wind, no life, no machinery. Just rock "
                "and water and the faint infrasound of the earth settling around you."
            )
        else:
            synthesis_notes.append(
                "The silence registers at maybe 30 dBA — not true silence but the noise floor "
                "of the space itself: structure settling, air moving, your own blood in your ears."
            )
    if "clock" in prose_lower:
        synthesis_notes.append(
            "The clock tick phase-locks your temporal perception to its rhythm — "
            "in this room, time has a pulse rate, and it's the clock's. "
            "Remove it and the room would feel genuinely timeless."
        )

    if synthesis_notes:
        enriched_parts.append(" ".join(synthesis_notes))

    for part in enriched_parts:
        lines.append(f"  {part}")

    lines.append("")
    lines.append("╚═════════════════════════════════════════════════════════════╝")
    return "\n".join(lines)


def deep_generate(engine, scene, position_index=0):
    """
    Run full deep mode processing for a scene position.

    Returns structured output with all five deep-processing stages.
    """
    parts = []

    # Header
    parts.append(f"{'━' * 64}")
    parts.append(f"  DEEP MODE — {scene.name}")
    parts.append(f"  Position: {scene.positions[position_index].name if scene.positions else 'overview'}")
    parts.append(f"{'━' * 64}")
    parts.append("")

    # 1. Physical constraints
    taste_data = scene._raw_data.get('taste') if hasattr(scene, '_raw_data') else None
    parts.append(generate_constraints(scene.environment, taste_data=taste_data))
    parts.append("")

    if not scene.positions:
        parts.append("[Scene has no walk positions — deep mode requires positions]")
        return "\n".join(parts)

    pos = scene.positions[position_index]

    # 2. First pass
    parts.append(generate_first_pass(pos, position_index))
    parts.append("")

    # 3. Cross-sensory reconciliation
    parts.append(generate_reconciliation(pos, scene.environment, scene))
    parts.append("")

    # 4. Iterative deepening (only if triggers matched)
    deepened = generate_deepened(pos)
    if deepened:
        parts.append(deepened)
        parts.append("")

    # 5. Sensory archaeology (only if triggers matched)
    why_chains = generate_why_chains(pos)
    if why_chains:
        parts.append(why_chains)
        parts.append("")

    # 6. Final experience
    parts.append(generate_final_experience(pos, scene.environment, position_index))

    return "\n".join(parts)


def _generate_physics_prose(env, raw):
    """
    Generate physics-rich prose from scene data.
    
    Computes real relationships and weaves them into the experience.
    Maximum 2-3 sentences — the most interesting physics relationship
    in this room, presented as something you'd notice, not a lecture.
    """
    candidates = []
    
    temp = env.temperature_c
    hum = env.humidity_pct
    wind = env.wind_speed_kmh
    
    # Pick the MOST interesting physics relationship for this room
    # Not all of them — just the one that matters most here
    
    # Wind chill — only if dramatic
    if wind > 10 and temp < 15:
        wind_chill = 13.12 + 0.6215 * temp - 11.37 * (wind ** 0.16) + 0.3965 * temp * (wind ** 0.16)
        diff = temp - wind_chill
        if diff > 5:  # Only mention if the difference is striking
            candidates.append((diff, f"The air is {temp}°C but the wind strips heat so fast it feels like {wind_chill:.0f}°C against your skin."))
    
    # Humidity + smell — only if extreme
    if hum > 90:
        candidates.append((hum - 80, f"The air is {hum}% water. Every breath is half-vapor, and scent molecules ride the moisture further than they should — you smell things here before you see them."))
    
    # Sound — only the most evocative detail
    sound = raw.get('sound', {})
    rt60 = sound.get('rt60_seconds', None)
    ambient = sound.get('ambient_dba', None)
    
    if rt60 is not None and rt60 > 3 and ambient is not None and ambient < 15:
        candidates.append((rt60 * 3, f"Your voice takes {rt60} seconds to return — the space swallows sound and gives it back slowly, softened, as if the room is thinking about what you said before answering."))
    elif ambient is not None and ambient < 12:
        candidates.append((20 - ambient, f"At {ambient} dBA, this room is quieter than anywhere you've ever been. Your heartbeat is the loudest thing. Your breathing is weather."))
    
    # Light — only dramatic extremes
    light = raw.get('light', {})
    lux = light.get('lux', None)
    if lux is not None and isinstance(lux, (int, float)):
        if lux < 0.01:
            candidates.append((10, f"Color doesn't exist here. At {lux} lux your eyes have abandoned their cone cells entirely — the world is silver and shadow and motion, nothing more."))
        elif lux > 80000:
            candidates.append((8, f"The light is {int(lux)} lux — brighter than your eyes are designed to handle. Your pupils are pinpoints. Every shadow is a knife edge."))
    
    # Temporal urgency
    temporal = raw.get('temporal', [])
    if temporal and len(temporal) >= 2:
        last = temporal[-1]
        last_min = last.get('at_minutes', last.get('at', '?'))
        last_event = last.get('event', '')
        if last_event:
            candidates.append((5, f"In {last_min} minutes, {last_event.lower() if last_event[0:1].isupper() and '.' not in last_event[:5] else last_event}"))
    
    if not candidates:
        return ""
    
    # Pick the most dramatic physics relationship (highest score)
    candidates.sort(key=lambda x: x[0], reverse=True)
    # Return only the top 1-2
    best = [c[1] for c in candidates[:2]]
    return " ".join(best)


def deep_generate_narrative(engine, scene, position_index=0):
    """
    Narrative mode: integrated prose with computed physics data.
    
    Combines:
    1. Scene-level prose (handwritten, sensory-rich)
    2. Position prose (specific vantage point)
    3. Computed physics relationships (generated from env data — real numbers)
    4. Cross-sensory bridges (how senses connect)
    5. Impossible detail (the one fact that changes how you see the room)
    
    No labels, no scaffolding. Reads like being somewhere
    while giving an AI the actual physical relationships to process.
    """
    raw = scene._raw_data if hasattr(scene, '_raw_data') else {}

    if not scene.positions:
        return raw.get('prose', '') or scene.description or f"[{scene.name}]"

    pos = scene.positions[position_index]
    parts = []

    # Scene-level prose — the main description
    scene_prose = raw.get('prose', '')
    if scene_prose:
        parts.append(scene_prose)
        parts.append("")

    # Position prose — the specific vantage point
    pos_prose = pos.prose or ""
    if not pos_prose:
        pos_prose = _generate_composed_prose(pos)
    if pos_prose and pos_prose != scene_prose:
        parts.append(pos_prose)
        parts.append("")

    # Computed physics prose — real numbers, real relationships
    physics = _generate_physics_prose(scene.environment, raw)
    if physics:
        parts.append(physics)
        parts.append("")

    # Cross-sensory bridges — how senses connect
    bridges = getattr(pos, 'cross_sensory', '') or ''
    scene_bridges = raw.get('cross_sensory_bridges', [])
    
    if bridges:
        parts.append(bridges)
        parts.append("")
    elif scene_bridges:
        parts.append(" ".join(scene_bridges))
        parts.append("")

    # Impossible detail — the revelation
    impossible = raw.get('impossible_detail', '')
    if impossible:
        parts.append(impossible)
        parts.append("")

    return "\n".join(parts)


def deep_generate_walk(engine, scene):
    """
    Run deep mode for ALL positions in a scene (walk + deep combined).
    Iterates through every position with transitions between them.
    """
    parts = []

    # Header
    parts.append(f"{'━' * 64}")
    parts.append(f"  DEEP WALK — {scene.name}")
    parts.append(f"  {len(scene.positions)} positions")
    parts.append(f"{'━' * 64}")
    parts.append("")

    # 1. Physical constraints (once, for the whole scene)
    taste_data = scene._raw_data.get('taste') if hasattr(scene, '_raw_data') else None
    parts.append(generate_constraints(scene.environment, taste_data=taste_data))
    parts.append("")

    if not scene.positions:
        parts.append("[Scene has no walk positions — deep walk requires positions]")
        return "\n".join(parts)

    for i, pos in enumerate(scene.positions):
        # Position header
        parts.append(f"{'─' * 64}")
        parts.append(f"  ▸ Position {i + 1}/{len(scene.positions)}: {pos.name}")
        parts.append(f"{'─' * 64}")
        parts.append("")

        # First pass
        parts.append(generate_first_pass(pos, i))
        parts.append("")

        # Cross-sensory reconciliation
        parts.append(generate_reconciliation(pos, scene.environment, scene))
        parts.append("")

        # Iterative deepening (only if triggers matched)
        deepened = generate_deepened(pos)
        if deepened:
            parts.append(deepened)
            parts.append("")

        # Sensory archaeology (only if triggers matched)
        why_chains = generate_why_chains(pos)
        if why_chains:
            parts.append(why_chains)
            parts.append("")

        # Final experience
        parts.append(generate_final_experience(pos, scene.environment, i))
        parts.append("")

        # Transition to next position
        if i < len(scene.positions) - 1:
            next_pos = scene.positions[i + 1]
            parts.append(f"  ═══ TRANSITION: {pos.name} → {next_pos.name} ═══")
            parts.append("")

    return "\n".join(parts)


def deep_generate_custom(engine, description):
    """
    Run deep mode on a custom description.
    Uses the physics primitive system for environment inference and scene composition,
    then runs deep processing on the result.
    """
    from mindscape import parse_description, compose_from_primitives, PHYSICS_PRIMITIVES

    # Parse description into primitives
    primitives = parse_description(description)

    if primitives:
        print(f"🔬 Physics-primitive composition from: \"{description}\"")
        print(f"   Primitives: {', '.join(primitives)}")
        categories = {}
        for p in primitives:
            cat = PHYSICS_PRIMITIVES.get(p, {}).get("category", "unknown")
            categories.setdefault(cat, []).append(p)
        for cat, prims in sorted(categories.items()):
            print(f"   [{cat}] {', '.join(prims)}")
        print()

        # Compose scene from primitives (uses smart inference + interaction rules)
        scene = compose_from_primitives(primitives, title=description.title())

        # Run walk mode if multiple positions, single position otherwise
        if len(scene.positions) > 1:
            return deep_generate_walk(engine, scene)
        else:
            return deep_generate(engine, scene, 0)
    else:
        # Fallback: no primitives matched
        print(f"⚠️  No physics primitives matched for: \"{description}\"")
        print(f"   Try more specific keywords (e.g., 'underground', 'stone', 'night', 'rain')")

        # Create minimal scene
        env_data = {
            "temperature_c": 20, "humidity_pct": 50, "wind_speed_kmh": 0,
            "time_of_day": "day", "weather": "clear", "indoor": True,
        }
        pos_data = {
            "name": description,
            "description": description,
            "smell_emphasis": [],
            "prose": f"You are in {description}. The space reveals itself to your senses.",
            "cross_sensory": "",
        }
        scene_data = {
            "id": "custom-deep",
            "name": description.title(),
            "description": description,
            "environment": env_data,
            "positions": [pos_data],
        }
        scene = MindscapeScene(scene_data)
        return deep_generate(engine, scene, 0)
