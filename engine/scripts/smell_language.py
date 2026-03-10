"""
language.py — Experiential smell language layer.

Transforms raw scent descriptors into evocative, sensory prose.
Pure lookup/template system — no LLM calls, stdlib only.
"""

import random
import re
from collections import Counter, defaultdict

# ─── Descriptor → Experiential Phrase Mappings ───────────────────────────────
# Each descriptor maps to a list of phrases; we pick contextually or randomly.

DESCRIPTOR_PHRASES = {
    # Sweet family
    "sweet": [
        "something sweet lingering just under the surface",
        "a sweetness that settles on the tongue before the nose",
        "the unmistakable pull of sugar in warm air",
    ],
    "vanilla": [
        "warm vanilla, the kind that clings to wooden spoons",
        "a soft vanilla haze, like opening an old recipe book",
        "vanilla pooling in the air, thick and golden",
    ],
    "creamy": [
        "something rich and creamy drifting close",
        "a rounded, cream-soft warmth",
        "the velvet weight of cream left out in a warm kitchen",
    ],
    "chocolate": [
        "dark chocolate — the bitter edge before the melt",
        "cocoa dust hanging in the air, bittersweet",
        "chocolate warmth, deep and slightly roasted",
    ],
    "caramel": [
        "burnt sugar just past golden, edging toward caramel",
        "caramel darkening in a copper pan",
        "that sticky-sweet caramel smell that makes you lean in",
    ],
    "honey": [
        "honey thickened by summer heat, almost waxy",
        "wild honey — floral underneath, golden on top",
        "the dense amber sweetness of old honeycomb",
    ],
    "candy": [
        "bright candy sweetness, almost synthetic in its perfection",
        "sugar spun thin and warm",
        "the sticky-sweet air of a candy shop",
    ],
    "sugar": [
        "raw sugar, warm and slightly molasses-dark",
        "crystalline sweetness dissolving in humid air",
    ],
    "maple": [
        "maple sap reduced to dark amber, woodsmoke underneath",
        "the breakfast-table warmth of real maple",
    ],
    "butterscotch": [
        "butterscotch melting slowly, butter and burnt sugar intertwined",
        "golden butterscotch warmth",
    ],
    "cotton candy": [
        "cotton candy haze — pure spun sugar dissolving",
    ],
    "molasses": [
        "dark molasses, heavy and bittersweet, almost iron-tinged",
    ],

    # Spice family
    "spicy": [
        "a sharp spice note that prickles the back of the throat",
        "warmth with an edge — spice that builds slowly",
        "spice threading through the air like a whispered dare",
    ],
    "cinnamon": [
        "cinnamon bark, freshly cracked — warm and slightly dusty",
        "cinnamon heat spiraling upward",
        "the red-brown warmth of cinnamon sticks in a simmering pot",
    ],
    "clove": [
        "clove — sharp, almost numbing, like biting a whole bud",
        "dried cloves in a mortar, their oil just released",
        "the dental-sharp sweetness of clove",
    ],
    "pepper": [
        "cracked black pepper, that first sharp inhale",
        "pepper heat rising from a warm surface",
    ],
    "peppery": [
        "a peppery bite, sharp and warm, lingering at the back of the throat",
        "the crack of fresh peppercorns, heat without fire",
    ],
    "nutmeg": [
        "freshly grated nutmeg, warm and slightly narcotic",
        "nutmeg dust in warm milk — cozy and ancient",
    ],
    "ginger": [
        "fresh ginger root snapped open, bright and stinging",
        "ginger heat — citrus-sharp underneath the burn",
    ],
    "cardamom": [
        "cardamom pods crushed between fingertips, eucalyptus-sweet",
        "the cool-warm paradox of cardamom",
    ],
    "anise": [
        "anise — that unmistakable licorice sharpness",
        "black licorice and fennel, herbal and polarizing",
    ],
    "anisic": [
        "a soft anise sweetness, licorice wrapped in warmth",
    ],
    "warm": [
        "a generalized warmth, like sun-heated skin",
        "something warm radiating from below",
    ],
    "allspice": [
        "allspice — cinnamon, clove, and nutmeg all at once",
    ],
    "cumin": [
        "cumin's earthy musk, slightly sweaty, deeply savory",
    ],
    "cooling": [
        "a cooling sensation, like breathing mountain air through ice",
        "a bracing coolness threading through the warmth",
    ],

    # Floral family
    "floral": [
        "flowers — not one kind, but the general hum of a garden",
        "a floral drift, petals warming in the sun",
        "something blooming nearby, sweet and alive",
    ],
    "rose": [
        "rose petals bruised between fingers, almost jammy",
        "old garden roses after rain, heavy and sweet",
    ],
    "jasmine": [
        "jasmine at night — heady, almost too much, intoxicating",
        "jasmine blooming in humid air, thick and narcotic",
    ],
    "lavender": [
        "lavender fields — purple haze of calm, slightly medicinal underneath",
        "dried lavender in a linen drawer",
    ],
    "violet": [
        "violets — powdery, sweet, appearing and vanishing",
        "that elusive violet scent that disappears the moment you chase it",
    ],
    "lily": [
        "lily — waxy petals, almost funereal sweetness",
        "heavy white lily, sweet enough to feel physical",
    ],
    "geranium": [
        "geranium leaf, green-rosy and slightly peppery",
    ],
    "orchid": [
        "orchid — faint, waxy, tropical and elusive",
    ],
    "muguet": [
        "lily of the valley — green, dewy, impossibly fresh",
    ],
    "patchouli": [
        "patchouli — dark, earthy, the scent of old incense and damp soil",
        "rich patchouli, musty-sweet and grounding",
    ],

    # Fruity family
    "fruity": [
        "ripe fruit — not specific, just that universal juicy sweetness",
        "something fruity tumbling through the air",
    ],
    "citrus": [
        "citrus zest — that bright spray when you break the peel",
        "sharp citrus cutting through everything else",
    ],
    "lemon": [
        "lemon peel twisted over a glass, oils misting",
        "bright lemon — clean and almost electric",
    ],
    "orange": [
        "orange rind drying in the sun, sweet and slightly bitter",
        "fresh-peeled orange, juice running down your wrist",
    ],
    "berry": [
        "crushed berries, seeds and juice and skin all at once",
        "summer berries warming in a bowl",
    ],
    "apple": [
        "crisp apple — green skin, white flesh, cool sweetness",
    ],
    "peach": [
        "ripe peach, sun-warmed, fuzz and all",
        "peach juice on a cutting board, sticky-sweet",
    ],
    "pear": [
        "pear — delicate, watery-sweet, easily missed",
    ],
    "tropical": [
        "tropical fruit — mango or papaya, something sun-drenched",
    ],
    "banana": [
        "banana — ripe, almost fermented, candy-like",
    ],
    "grape": [
        "concord grape — that purple candy-sweet burst",
    ],
    "pineapple": [
        "pineapple sharpness, sweet and acidic simultaneously",
    ],
    "coconut": [
        "coconut cream — sun-warmed, tropical, slightly oily",
        "fresh coconut, milky and sweet",
    ],
    "melon": [
        "ripe melon — watery, green-sweet, summer afternoon",
    ],
    "cherry": [
        "dark cherry — almost medicinal, syrupy-sweet",
        "maraschino cherry, bright red and candy-like",
    ],
    "plum": [
        "ripe plum, skin taut, juice darkening to purple",
    ],
    "apricot": [
        "dried apricot — concentrated sunshine, tangy-sweet",
    ],
    "strawberry": [
        "strawberry — that specific red sweetness, slightly green at the stem",
    ],
    "tomato": [
        "sun-warmed tomato vine, green and sharp, that garden musk",
        "ripe tomato — savory-sweet, the smell of summer gardens",
    ],
    "cabbage": [
        "cooked cabbage — sulfurous and vegetal, the smell of honest kitchens",
        "raw cabbage, crisp and faintly bitter",
    ],
    "radish": [
        "fresh radish, peppery and sharp, earth still clinging to the skin",
    ],
    "corn": [
        "sweet corn, starchy and golden, summer cookout warmth",
    ],

    # Green / Herbal family
    "green": [
        "fresh-cut green — stems snapped, chlorophyll released",
        "green and alive, like walking through wet grass",
    ],
    "herbal": [
        "dried herbs crumbling between palms",
        "an herbal complexity — garden-fresh, slightly medicinal",
    ],
    "grassy": [
        "freshly cut grass, that sharp green exhale",
    ],
    "minty": [
        "mint — cool and sharp, almost crystalline",
    ],
    "mint": [
        "crushed mint leaves, that cool green shock",
        "mint so fresh it makes the air feel cold",
    ],
    "eucalyptus": [
        "eucalyptus — clearing the sinuses, camphorous and clean",
    ],
    "basil": [
        "fresh basil torn by hand, peppery-green and sweet",
    ],
    "thyme": [
        "thyme — earthy, medicinal, sun-dried on the hillside",
    ],
    "tea": [
        "loose-leaf tea, slightly tannic, quietly aromatic",
    ],
    "hay": [
        "fresh-dried hay, golden and sun-baked",
    ],
    "mossy": [
        "damp moss on old stone — green, ancient, cool",
    ],
    "leafy": [
        "crushed leaves underfoot, green sap and autumn decay",
    ],
    "vegetable": [
        "something vegetal — green, raw, straight from the garden",
        "a quiet vegetable note, like celery hearts and fresh stems",
    ],

    # Woody family
    "woody": [
        "warm wood — something aged, sanded smooth by time",
        "a woody base note, solid and grounding",
    ],
    "cedar": [
        "cedar chest opened after years — dry, aromatic, almost sacred",
    ],
    "sandalwood": [
        "sandalwood — creamy, meditative, the scent of still rooms",
    ],
    "pine": [
        "pine resin bleeding from bark, sharp and clean",
        "pine forest after rain, resinous and electric",
    ],
    "oak": [
        "aged oak — tannic, wine-stained, full of history",
    ],
    "birch": [
        "birch bark peeling, sweet and slightly smoky",
    ],
    "terpenic": [
        "terpenes — that sharp resinous bite of conifers",
    ],
    "resinous": [
        "tree resin, sticky-golden, ancient and aromatic",
    ],

    # Smoky / Burnt family
    "smoky": [
        "woodsmoke drifting on cold air",
        "smoke — the memory of fire, thin and blue",
    ],
    "burnt": [
        "something charred at the edges, not unpleasant",
        "the controlled burn of roasted things",
    ],
    "roasted": [
        "deep roast — coffee or nuts, that Maillard darkness",
        "something slow-roasted, brown and complex",
    ],
    "charred": [
        "charcoal and ash, the aftermath of real heat",
    ],
    "ashy": [
        "cold ash — the morning after a fire",
    ],
    "toasted": [
        "toast just done — golden-brown warmth",
    ],
    "coffee": [
        "fresh coffee — dark, roasted, the scent that pulls you from sleep",
        "coffee grounds still warm, bitter and inviting",
    ],

    # Earthy family
    "earthy": [
        "damp earth after rain — petrichor's quieter cousin",
        "rich soil turned over, mineral and alive",
    ],
    "mushroom": [
        "forest mushrooms — damp, umami, slightly mysterious",
    ],
    "musty": [
        "old books and dust, a room unopened for seasons",
    ],
    "dusty": [
        "fine dust in a shaft of light — dry and ancient",
    ],
    "mineral": [
        "wet stone, mineral-sharp, like licking a river rock",
    ],
    "soil": [
        "fresh-turned soil, rich and dark and full of life",
    ],
    "petrichor": [
        "rain on dry earth — that universal exhale of relief",
    ],
    "moss": [
        "damp moss, green and prehistoric",
    ],

    # Animal / Musk family
    "musk": [
        "musk — warm skin, intimate, slightly animal",
        "a musky undertone, body-warm and persistent",
    ],
    "leather": [
        "old leather — saddle-worn, rich, slightly smoky",
        "leather warmed by sun, supple and deep",
    ],
    "animalic": [
        "something animal — raw, primal, unsettling in its honesty",
    ],
    "animal": [
        "a faint animal warmth, hide and musk, the scent of living things",
        "something primal and skin-close underneath it all",
    ],
    "waxy": [
        "beeswax warming near a flame, honey-tinged",
    ],
    "fatty": [
        "rendered fat, rich and heavy, kitchen-warm",
        "a fatty richness, like tallow slowly melting",
    ],
    "oily": [
        "warm oil — slick, slightly nutty, coating the air",
        "something oily and dense clinging to every surface",
    ],
    "fishy": [
        "the sharp tang of fresh fish — brine and silver scales",
        "something briny and marine, the dock at low tide",
    ],
    "seafood": [
        "a seafood counter — crushed ice, shellfish, clean ocean salt",
        "the briny sweetness of fresh shellfish",
    ],
    "ambergris": [
        "ambergris — oceanic, musky, like salt-cured driftwood",
        "a deep marine musk, ancient and oddly sweet",
    ],

    # Marine / Aquatic family
    "marine": [
        "salt air and seaweed — the ocean announcing itself",
    ],
    "oceanic": [
        "ocean spray on rocks, mineral and infinite",
    ],
    "salty": [
        "salt on warm skin, or the sea from a distance",
    ],
    "seaweed": [
        "seaweed drying on hot rocks — iodine and brine",
    ],
    "fresh": [
        "clean, fresh air — the absence of everything heavy",
        "something freshly washed, simple and bright",
    ],
    "clean": [
        "scrubbed-clean, almost sterile, like white tiles",
    ],
    "ozone": [
        "ozone — that electric-blue smell before a storm",
    ],

    # Chemical / Medicinal family
    "medicinal": [
        "medicine cabinet — antiseptic, camphor, old remedies",
    ],
    "camphor": [
        "camphor — penetrating, clearing, slightly numbing",
    ],
    "camphoreous": [
        "a camphor-bright sharpness, clearing the head like cold air through pines",
        "that camphorous bite — medicinal, resinous, bracing",
    ],
    "menthol": [
        "menthol frost, the air itself turning cold",
    ],
    "phenolic": [
        "phenolic sharpness — medicinal, tar-adjacent, industrial",
    ],
    "chemical": [
        "something chemical — sharp, synthetic, unmistakably artificial",
    ],
    "metallic": [
        "metal — blood-iron tang, copper pennies in a warm hand",
    ],
    "sulfurous": [
        "sulfur — struck match, hot springs, something volcanic",
        "a sulfurous whisper, like distant hot springs",
    ],
    "petroleum": [
        "petroleum — thick, dark, industrial underground",
    ],
    "solvent": [
        "solvent sharpness — nail polish, paint thinner, evaporating fast",
    ],
    "acetone": [
        "acetone sting — nail salon, chemical brightness",
    ],
    "alcoholic": [
        "alcohol vapors rising, sharp and evaporating",
        "the clean burn of spirits, volatile and warm",
    ],
    "ammonia": [
        "ammonia — eyes watering, nose stinging, step back",
    ],
    "ammoniacal": [
        "a sharp ammonia edge, acrid and nose-stinging",
    ],
    "vinegar": [
        "sharp vinegar bite, acetic and puckering",
    ],
    "acidic": [
        "an acidic sharpness, tart and mouth-watering",
        "something acidic cutting through — clean, sour, bright",
    ],
    "ethereal": [
        "something light and volatile, gone almost before you catch it",
        "an ethereal top note, evaporating like spirits in warm air",
    ],

    # Food / Savory family
    "buttery": [
        "melting butter in a hot pan, golden and sizzling",
        "butter — rich, dairy-warm, comfort itself",
    ],
    "butter": [
        "fresh butter, cold and clean, faintly sweet",
    ],
    "nutty": [
        "toasted nuts — warm, brown, slightly oily",
    ],
    "almond": [
        "bitter almond — marzipan sweetness with a cyanide whisper",
    ],
    "popcorn": [
        "popcorn — that buttery, salty, movie-theater cloud",
    ],
    "bread": [
        "fresh bread cooling on a rack, yeasty and golden",
    ],
    "yeasty": [
        "rising dough — warm, alive, slightly sour",
    ],
    "bready": [
        "warm bread crust, just this side of burnt",
    ],
    "meaty": [
        "cooked meat — savory, brown, primal hunger",
        "slow-braised meat, rich with rendered fat and time",
    ],
    "savory": [
        "deep savory richness — umami condensed",
    ],
    "bacon": [
        "bacon — smoky, salty, fat rendering, impossible to ignore",
    ],
    "ham": [
        "cured ham — salty, smoky, slightly sweet at the edges",
    ],
    "cheese": [
        "aged cheese — sharp, funky, complex",
    ],
    "chicken": [
        "roasted chicken skin — golden, savory, Sunday-dinner warmth",
        "chicken broth simmering, homey and nourishing",
    ],
    "garlic": [
        "garlic just hitting hot oil — that first sharp, savory bloom",
        "roasted garlic, sweet and caramelized, paper skins crisping",
    ],
    "onion": [
        "onion — sharp, tear-inducing, softening to sweetness over heat",
        "caramelized onion, dark gold and deeply savory",
    ],
    "alliaceous": [
        "that sharp allium bite — garlic, onion, something from the bulb family",
        "an alliaceous pungency, sulfurous and savory",
    ],

    # Powdery / Soft family
    "powdery": [
        "fine powder — talc, iris root, something grandmother-soft",
    ],
    "talc": [
        "talcum powder, baby-soft and slightly floral",
    ],
    "soft": [
        "soft — no edges, nothing sharp, just gentle presence",
    ],
    "delicate": [
        "barely there — you have to hold still to catch it",
    ],

    # Miscellaneous
    "aromatic": [
        "broadly aromatic — complex enough to keep unfolding",
    ],
    "pungent": [
        "pungent — hits you before you're ready, fills the room",
    ],
    "acrid": [
        "acrid sharpness — burning, caustic, makes you turn away",
    ],
    "rancid": [
        "something gone off — oil oxidized, staleness turned aggressive",
    ],
    "sour": [
        "sour note — fermented, acidic, not quite spoiled",
    ],
    "bitter": [
        "bitter — dark roast, raw cacao, tonic water",
    ],
    "sharp": [
        "a sharp edge cutting through the softer notes",
    ],
    "dry": [
        "bone-dry, the moisture pulled from the air itself",
    ],
    "cool": [
        "a cool note — mentholated or high-altitude, bracing",
    ],
    "balsamic": [
        "balsamic warmth — resinous, sweet, church-like",
    ],
    "amber": [
        "amber — warm, resinous, ancient sunlight trapped in stone",
    ],
    "tobacco": [
        "cured tobacco leaf, sweet and leathery and addictive",
    ],
    "paintlike": [
        "wet paint — chemical, sharp, the smell of new rooms",
    ],
    "painty": [
        "paint fumes — turpentine edge, linseed oil underneath",
    ],
    "rubbery": [
        "hot rubber — tires on asphalt, industrial and thick",
    ],
    "plastic": [
        "new plastic — synthetic, slightly sweet, off-gassing",
    ],
    "soapy": [
        "fresh soap — clean, floral-edged, civilized",
    ],
    "odorless": [
        "",  # Special: empty string means skip this descriptor
    ],
    "bland": [
        "",  # Skip — adds nothing to narration
    ],

    # Additional coverage
    "cloth": [
        "clean linen dried in the sun, soft and faintly warm",
    ],
    "laundered cloth": [
        "freshly laundered cloth — detergent, warmth, the hum of a dryer",
    ],
    "spice": [
        "dried spices in a wooden drawer, complex and layered",
    ],
    "winey": [
        "red wine — tannic, fruity, oak-barrel depth",
    ],
    "fermented": [
        "something fermented — alive, tangy, on the edge of wild",
    ],
    "malty": [
        "warm malt, biscuity and slightly sweet, like a brewhouse",
    ],
    "hoppy": [
        "hops — bitter, floral, resinous, the backbone of beer",
    ],
    "milky": [
        "warm milk, faintly sweet, comfort in a cup",
    ],
    "creamy buttery": [
        "pure dairy warmth — butter melting into cream",
    ],
    "cooked": [
        "the warm smell of something just cooked, brown and inviting",
    ],
    "baked": [
        "something fresh from the oven, golden-crusted and warm",
    ],
    "fried": [
        "hot oil and golden edges — the sizzle still in the air",
    ],
    "caramellic": [
        "a caramel note, dark sugar slowly browning",
    ],
    "watery": [
        "thin, watery, like morning dew on glass",
    ],
    "floral fruity": [
        "floral and fruity at once — blossoms about to become fruit",
    ],
    "rosy": [
        "the blush of rose, soft and faintly jammy",
    ],
    "herbaceous": [
        "crushed herbs — green, vital, slightly bitter at the stem",
    ],
    "coniferous": [
        "evergreen needles crushed underfoot, resinous and clean",
    ],
    "piney": [
        "pine sap, sticky and sharp, forest-deep",
    ],
    "musky": [
        "a musky warmth rising from underneath everything else",
    ],
    "fusel": [
        "fusel alcohol — heavy, slightly overripe, the bottom of fermentation",
    ],
    "woody spicy": [
        "spice-rubbed wood, sandalwood and pepper intertwined",
    ],
    "fruity floral": [
        "where fruit meets flower — peach blossoms, maybe, or apple in bloom",
    ],
    "green fresh": [
        "green and freshly cut, the sharp exhale of living stems",
    ],
    "sweet floral": [
        "sweet flowers opening in warmth, nectar-heavy and inviting",
    ],
    "sweet fruity": [
        "candy-ripe fruit, sugar-dusted and sun-warm",
    ],
    "sweet woody": [
        "sweetened wood — cedar honey, vanilla bark",
    ],
    "spicy woody": [
        "spice and old wood — a merchant's cabinet, centuries of trade",
    ],
    "fruity sweet": [
        "overripe fruit sweetness, heavy and intoxicating",
    ],
    "roasted coffee": [
        "dark-roasted coffee beans, oily and cracked, the bitter heart of morning",
    ],
    "coffee roasted coffee": [
        "dark-roasted coffee — the deep, oily, almost-burnt intensity of a serious roast",
    ],
    "cherry maraschino cherry": [
        "maraschino cherry — bright, artificial, candy-sweet and lurid red",
    ],
    "onion cooked onion": [
        "slow-cooked onion, collapsed into golden sweetness",
    ],
    "cloth laundered cloth": [
        "fresh laundry — sun-dried cotton, the warmth of a clean fold",
    ],
}

# ─── Descriptor Categories for Grouping ──────────────────────────────────────
# Maps each descriptor to a scent family for intelligent grouping in narration.

DESCRIPTOR_FAMILIES = {
    # Sweet
    "sweet": "sweet", "vanilla": "sweet", "creamy": "sweet", "chocolate": "sweet",
    "caramel": "sweet", "honey": "sweet", "candy": "sweet", "sugar": "sweet",
    "maple": "sweet", "butterscotch": "sweet", "cotton candy": "sweet",
    "molasses": "sweet", "caramellic": "sweet",
    # Spice
    "spicy": "spice", "cinnamon": "spice", "clove": "spice", "pepper": "spice",
    "peppery": "spice", "nutmeg": "spice", "ginger": "spice", "cardamom": "spice",
    "anise": "spice", "anisic": "spice", "warm": "spice", "allspice": "spice",
    "cumin": "spice",
    # Floral
    "floral": "floral", "rose": "floral", "jasmine": "floral", "lavender": "floral",
    "violet": "floral", "lily": "floral", "geranium": "floral", "orchid": "floral",
    "muguet": "floral", "patchouli": "floral", "rosy": "floral",
    # Fruit
    "fruity": "fruit", "citrus": "fruit", "lemon": "fruit", "orange": "fruit",
    "berry": "fruit", "apple": "fruit", "peach": "fruit", "pear": "fruit",
    "tropical": "fruit", "banana": "fruit", "grape": "fruit", "pineapple": "fruit",
    "coconut": "fruit", "melon": "fruit", "cherry": "fruit", "plum": "fruit",
    "apricot": "fruit", "strawberry": "fruit", "tomato": "fruit",
    # Green / Herbal
    "green": "green", "herbal": "green", "grassy": "green", "minty": "green",
    "mint": "green", "eucalyptus": "green", "basil": "green", "thyme": "green",
    "tea": "green", "hay": "green", "mossy": "green", "leafy": "green",
    "vegetable": "green", "herbaceous": "green", "cabbage": "green",
    "radish": "green", "corn": "green",
    # Woody
    "woody": "woody", "cedar": "woody", "sandalwood": "woody", "pine": "woody",
    "oak": "woody", "birch": "woody", "terpenic": "woody", "resinous": "woody",
    "coniferous": "woody", "piney": "woody",
    # Smoky / Roast
    "smoky": "smoky", "burnt": "smoky", "roasted": "smoky", "charred": "smoky",
    "ashy": "smoky", "toasted": "smoky", "coffee": "smoky",
    # Earthy
    "earthy": "earthy", "mushroom": "earthy", "musty": "earthy", "dusty": "earthy",
    "mineral": "earthy", "soil": "earthy", "petrichor": "earthy", "moss": "earthy",
    # Animal / Musk
    "musk": "musk", "leather": "musk", "animalic": "musk", "animal": "musk",
    "waxy": "musk", "fatty": "musk", "oily": "musk", "musky": "musk",
    "ambergris": "musk",
    # Marine
    "marine": "marine", "oceanic": "marine", "salty": "marine", "seaweed": "marine",
    "fresh": "marine", "clean": "marine", "ozone": "marine", "fishy": "marine",
    "seafood": "marine",
    # Chemical / Sharp
    "medicinal": "chemical", "camphor": "chemical", "camphoreous": "chemical",
    "menthol": "chemical", "phenolic": "chemical", "chemical": "chemical",
    "metallic": "chemical", "sulfurous": "chemical", "petroleum": "chemical",
    "solvent": "chemical", "acetone": "chemical", "alcoholic": "chemical",
    "ammonia": "chemical", "ammoniacal": "chemical", "vinegar": "chemical",
    "acidic": "chemical", "ethereal": "chemical", "cooling": "chemical",
    # Savory food
    "buttery": "savory", "butter": "savory", "nutty": "savory", "almond": "savory",
    "popcorn": "savory", "bread": "savory", "yeasty": "savory", "bready": "savory",
    "meaty": "savory", "savory": "savory", "bacon": "savory", "ham": "savory",
    "cheese": "savory", "chicken": "savory", "garlic": "savory", "onion": "savory",
    "alliaceous": "savory",
    # Texture / Abstract
    "powdery": "texture", "talc": "texture", "soft": "texture", "delicate": "texture",
    "aromatic": "texture", "pungent": "texture", "sharp": "texture", "dry": "texture",
    "cool": "texture", "sour": "texture", "bitter": "texture", "acrid": "texture",
    "rancid": "texture",
}

# Family display priority (most evocative first)
FAMILY_PRIORITY = [
    "smoky", "savory", "sweet", "spice", "fruit", "woody",
    "green", "floral", "earthy", "marine", "musk", "chemical", "texture",
]

# Family intro phrases — used when narrating a group of related descriptors
FAMILY_INTROS = {
    "sweet": [
        "The sweetness comes first —",
        "Sugar and warmth, layered:",
    ],
    "spice": [
        "Then the spice —",
        "Spice cuts through:",
    ],
    "floral": [
        "Something floral rises —",
        "Flowers in the mix:",
    ],
    "fruit": [
        "Fruit notes surface —",
        "A fruity brightness:",
    ],
    "green": [
        "Green and alive —",
        "The green notes underneath:",
    ],
    "woody": [
        "A woody backbone —",
        "Wood and resin grounding it:",
    ],
    "smoky": [
        "Smoke and roast —",
        "The dark notes:",
    ],
    "earthy": [
        "Earth and depth —",
        "Something ancient beneath:",
    ],
    "musk": [
        "Warmth and skin —",
        "An animal warmth:",
    ],
    "marine": [
        "Salt and air —",
        "The ocean in it:",
    ],
    "chemical": [
        "A sharp edge —",
        "Something volatile:",
    ],
    "savory": [
        "The savory heart of it —",
        "Rich and food-warm:",
    ],
    "texture": [
        "And hovering over all of it,",
        "The texture of it:",
    ],
}

# ─── Cluster Phrases ─────────────────────────────────────────────────────────

CLUSTER_PHRASES = [
    ({"sweet", "vanilla", "creamy"}, [
        "warm bakery counter, something caramelized underneath, the kind of sweetness that makes you inhale deeper",
        "vanilla warmth thick enough to taste — cream and sugar and slow Sunday mornings",
    ]),
    ({"smoky", "woody", "burnt"}, [
        "campfire aftermath, charred wood still warm, thin blue smoke curling",
        "the morning after a bonfire — ash and oak and memory",
    ]),
    ({"sweet", "spicy", "cinnamon", "warm"}, [
        "cinnamon rolls just pulled from the oven — sugar-crusted, spice-heated, irresistible",
        "mulled wine simmering on the stove, cinnamon sticks bobbing in dark red",
    ]),
    ({"floral", "sweet", "fresh"}, [
        "a flower market at dawn — buckets of fresh stems, cold water, sweet petals everywhere",
        "spring garden in full bloom, bees already working, sweetness carried on a breeze",
    ]),
    ({"earthy", "woody", "green"}, [
        "forest floor — damp leaves, exposed roots, the green smell of growing things",
        "deep woods after rain, every surface breathing",
    ]),
    ({"citrus", "fresh", "green"}, [
        "lime zest and wet grass — morning sharp and electric-green",
        "citrus grove at dawn, dew on the leaves, peel oil in the air",
    ]),
    ({"coffee", "roasted", "bitter"}, [
        "espresso machine hissing in a small café, dark roast crema, the bitter edge that wakes you up",
    ]),
    ({"sweet", "fruity", "tropical"}, [
        "tropical fruit stand — mango, passion fruit, warm juice running over the counter",
    ]),
    ({"leather", "smoky", "woody"}, [
        "old study — leather armchair, pipe tobacco residue, oak bookshelves",
    ]),
    ({"salty", "marine", "fresh"}, [
        "the coastline — salt spray, kelp on rocks, wind off the Atlantic",
    ]),
    ({"herbal", "green", "fresh"}, [
        "herb garden just watered — basil, thyme, parsley, the soil still steaming",
    ]),
    ({"sweet", "chocolate", "creamy"}, [
        "hot chocolate in a ceramic mug — dark, rich, whipped cream melting on top",
    ]),
    ({"floral", "powdery", "soft"}, [
        "grandmother's vanity — face powder, dried roses, lace doilies",
    ]),
    ({"pine", "resinous", "fresh"}, [
        "deep in a pine forest — resin on your fingers, needles underfoot, air so clean it stings",
    ]),
    ({"meaty", "smoky", "savory"}, [
        "barbecue pit — low smoke, charred edges, fat dripping on hot coals",
    ]),
    ({"sweet", "honey", "floral"}, [
        "wildflower meadow humming with bees, honey in the making, pollen-thick air",
    ]),
    ({"musty", "earthy", "woody"}, [
        "antique shop — old wood, dust, the ghost of someone's attic",
    ]),
    ({"garlic", "onion", "alliaceous"}, [
        "the allium family in force — garlic and onion hitting hot oil, savory and sharp",
        "garlic and onion, that primal kitchen perfume, eyes stinging, mouth watering",
    ]),
    ({"meaty", "savory", "fatty"}, [
        "slow-cooked meat, fat rendering, the kind of richness that fills a house for hours",
    ]),
    ({"sour", "acidic", "vinegar"}, [
        "a sharp acidity — pickled things, vinegar splashed on hot surfaces, bracing and alive",
        "vinegar and acid, the tang of fermentation and brine",
    ]),
    ({"herbal", "camphoreous", "medicinal"}, [
        "old apothecary — dried herbs in glass jars, camphor and remedy, dust on the labels",
    ]),
    ({"pine", "terpenic", "woody"}, [
        "deep in a conifer stand, resin dripping from bark, the air sharp with terpenes",
    ]),
    ({"herbal", "woody", "fresh"}, [
        "mountain trail — crushed sage underfoot, pine overhead, wind carrying it all",
    ]),
    ({"sweet", "buttery", "roasted"}, [
        "fresh pastry — butter-layered, golden-brown, sugar crystallizing on top",
    ]),
    ({"coffee", "roasted", "smoky"}, [
        "the first sip's worth of aroma from a dark roast — charred, deep, slightly ashy, completely addictive",
    ]),
    ({"nutty", "roasted", "sweet"}, [
        "praline — roasted nuts glazed in caramel, warm from the pan",
    ]),
    ({"fishy", "marine", "salty"}, [
        "the fish market at dawn — crushed ice, salt brine, silver scales catching light",
    ]),
    ({"herbal", "eucalyptus", "camphoreous"}, [
        "a eucalyptus grove after rain — camphorous, clean, almost medicinal in its clarity",
    ]),
    ({"spicy", "peppery", "warm"}, [
        "a pepper mill turning slowly — warm, sharp, building heat",
    ]),
]

# ─── Intensity Language ──────────────────────────────────────────────────────

INTENSITY_TEMPLATES = {
    "trace": [
        "If you hold very still, there's the faintest suggestion of {phrase}.",
        "Almost nothing — but wait. The ghost of {phrase}.",
        "Barely perceptible: {phrase}. You might be imagining it.",
    ],
    "faint": [
        "Underneath everything, faintly: {phrase}.",
        "A whisper of {phrase} — easy to miss if you're not paying attention.",
        "Just barely there: {phrase}.",
    ],
    "moderate": [
        "{phrase}.",
        "Clearly present: {phrase}.",
        "There it is — {phrase}.",
    ],
    "strong": [
        "{phrase} — filling the space, impossible to ignore.",
        "Strongly: {phrase}. It's the first thing you notice.",
        "{phrase}, assertive and unmistakable.",
    ],
    "overwhelming": [
        "{phrase} — overwhelming, saturating everything, almost too much.",
        "It hits you like a wall: {phrase}. Your eyes water.",
        "{phrase} — so thick you can practically taste it.",
    ],
}

# ─── Connective Tissue ──────────────────────────────────────────────────────

TRANSITIONS = [
    "Underneath that,",
    "And then,",
    "Layered beneath:",
    "Woven through it,",
    "At the edges,",
    "Rising above,",
    "Deeper in,",
    "Behind it all,",
    "Then, arriving late,",
    "Hovering just above,",
    "Mixed in,",
    "And carrying it all forward,",
    "Closer, you catch",
    "Threading through everything,",
]

GROUP_TRANSITIONS = [
    "",  # First group gets no transition
    "Underneath that,",
    "And woven through it all,",
    "Deeper in,",
    "At the edges,",
    "Then, arriving late,",
    "Behind everything,",
    "And finally,",
]

SCENE_INTROS = [
    "You walk in and the air tells you everything.",
    "The first breath says it all.",
    "Close your eyes. The air here is layered.",
    "Before you see anything, you smell it.",
    "The air is thick with presence.",
]

MIX_INTROS = [
    "The blend unfolds in layers:",
    "Together, they become something new:",
    "These notes tangle and merge:",
    "The combination reads like this:",
    "Mixed together, the air shifts:",
]


def _pick(lst, seed=None):
    """Pick from a list, optionally seeded for reproducibility."""
    if seed is not None:
        return lst[hash(seed) % len(lst)]
    return random.choice(lst)


def _normalize_descriptor(desc):
    """Normalize a descriptor string for matching."""
    return desc.strip().lower().replace("-", "").replace("_", " ")


def _find_clusters(descriptors):
    """Find matching descriptor clusters and return (matched_cluster_phrases, remaining_descriptors)."""
    desc_set = {_normalize_descriptor(d) for d in descriptors}
    used = set()
    cluster_results = []

    sorted_clusters = sorted(CLUSTER_PHRASES, key=lambda x: len(x[0]), reverse=True)

    for cluster_keys, phrases in sorted_clusters:
        normalized_keys = {_normalize_descriptor(k) for k in cluster_keys}
        if normalized_keys.issubset(desc_set) and not normalized_keys.intersection(used):
            cluster_results.append(_pick(phrases))
            used.update(normalized_keys)

    remaining = [d for d in descriptors if _normalize_descriptor(d) not in used]
    return cluster_results, remaining


def _descriptor_to_phrase(descriptor):
    """Convert a single descriptor to an experiential phrase."""
    norm = _normalize_descriptor(descriptor)

    # Direct match
    if norm in DESCRIPTOR_PHRASES:
        phrases = DESCRIPTOR_PHRASES[norm]
        # Skip empty phrases (odorless, bland, etc.)
        if phrases and phrases[0] == "":
            return None
        return _pick(phrases, seed=norm)

    # Partial match
    for key, phrases in DESCRIPTOR_PHRASES.items():
        if norm in key or key in norm:
            if phrases and phrases[0] == "":
                return None
            return _pick(phrases, seed=norm)

    # Fallback — but make it more graceful than before
    return f"a note of {descriptor}, hard to place but distinctly present"


def _group_by_family(descriptors):
    """Group descriptors by scent family. Returns dict of family → [descriptors]."""
    groups = defaultdict(list)
    ungrouped = []
    for d in descriptors:
        norm = _normalize_descriptor(d)
        family = DESCRIPTOR_FAMILIES.get(norm)
        if family:
            groups[family].append(d)
        else:
            ungrouped.append(d)
    return groups, ungrouped


def _select_top_descriptors(descriptors, max_count=9):
    """
    Select the most interesting/diverse descriptors, capped at max_count.
    Prioritizes: one from each family, then fills with remaining.
    Skips odorless/bland.
    """
    skip = {"odorless", "bland", ""}
    filtered = [d for d in descriptors if _normalize_descriptor(d) not in skip]

    if len(filtered) <= max_count:
        return filtered

    groups, ungrouped = _group_by_family(filtered)

    selected = []
    seen_families = set()

    # First pass: pick the best from each family (in priority order)
    for family in FAMILY_PRIORITY:
        if family in groups and family not in seen_families:
            # Pick the first (most prominent) descriptor from this family
            selected.append(groups[family][0])
            seen_families.add(family)
            if len(selected) >= max_count:
                break

    # Second pass: fill remaining slots with additional descriptors from populated families
    if len(selected) < max_count:
        for family in FAMILY_PRIORITY:
            if family in groups:
                for d in groups[family][1:]:
                    if d not in selected:
                        selected.append(d)
                        if len(selected) >= max_count:
                            break
            if len(selected) >= max_count:
                break

    # Add ungrouped if still room
    for d in ungrouped:
        if len(selected) >= max_count:
            break
        if d not in selected:
            selected.append(d)

    return selected[:max_count]


def _narrate_grouped(descriptors, intensity="moderate"):
    """
    Narrate descriptors by grouping related ones into unified impressions.
    Produces flowing prose rather than a list.
    """
    if not descriptors:
        return "Nothing. Clean air. The absence of scent is its own information."

    # First, try clusters on the full set
    cluster_phrases, remaining = _find_clusters(descriptors)

    # Select top descriptors from remaining
    remaining = _select_top_descriptors(remaining, max_count=max(0, 9 - len(cluster_phrases)))

    # Group remaining by family
    groups, ungrouped = _group_by_family(remaining)

    # Build paragraphs: clusters first, then grouped families
    paragraphs = []

    # Add cluster phrases as leading impressions
    for cp in cluster_phrases:
        paragraphs.append(cp)

    # Add family groups — narrate each family as a mini-impression
    for family in FAMILY_PRIORITY:
        if family not in groups:
            continue
        descs = groups[family]
        phrases = []
        for d in descs:
            p = _descriptor_to_phrase(d)
            if p:
                phrases.append(p)
        if phrases:
            if len(phrases) == 1:
                paragraphs.append(phrases[0])
            else:
                # Combine into a single flowing sentence
                combined = phrases[0] + " — " + ", ".join(phrases[1:])
                paragraphs.append(combined)

    # Add ungrouped
    for d in ungrouped:
        p = _descriptor_to_phrase(d)
        if p:
            paragraphs.append(p)

    if not paragraphs:
        return "Nothing. Clean air. The absence of scent is its own information."

    # Assemble prose with transitions
    intensity = intensity.lower() if intensity else "moderate"
    if intensity not in INTENSITY_TEMPLATES:
        intensity = "moderate"

    lines = []
    # First paragraph gets intensity treatment
    template = _pick(INTENSITY_TEMPLATES[intensity], seed=paragraphs[0])
    lines.append(template.format(phrase=paragraphs[0]))

    # Remaining get group transitions
    trans_pool = list(GROUP_TRANSITIONS[1:])  # skip the empty first one
    random.shuffle(trans_pool)
    # Extend pool if needed so every paragraph gets a transition
    while len(trans_pool) < len(paragraphs) - 1:
        trans_pool.extend(TRANSITIONS)
    for i, para in enumerate(paragraphs[1:]):
        t = trans_pool[i]
        if t:
            lines.append(f"{t} {para[0].lower() + para[1:]}.")
        else:
            lines.append(f"{para}.")

    return " ".join(lines)


def narrate_descriptors(descriptors, intensity="moderate"):
    """
    Transform a list of raw descriptors into experiential prose.
    """
    return _narrate_grouped(descriptors, intensity)


def narrate_compound(result, intensity="moderate"):
    """Narrate a single compound query result."""
    if not result.get("descriptors"):
        name = result.get("name") or result.get("query", "this")
        return f"No scent data for {name} — it might be odorless, or we just don't have the words yet."

    name = result.get("name") or result.get("query", "Something")
    prose = narrate_descriptors(result["descriptors"], intensity)
    return f"✦ {name}\n{prose}"


def narrate_mix(mix_result, intensity="moderate"):
    """Narrate a compound mixture result."""
    if not mix_result.get("compounds"):
        return "Nothing in this blend registers — either odorless or unknown."

    lines = []
    lines.append(_pick(MIX_INTROS))
    lines.append("")

    # Combine all notes into one unified narration
    all_notes = mix_result.get("all_notes_ranked", [])
    if all_notes:
        lines.append(narrate_descriptors(all_notes, intensity))
    else:
        dominant = mix_result.get("dominant_notes", [])
        subtle = mix_result.get("subtle_notes", [])
        combined = dominant + subtle
        lines.append(narrate_descriptors(combined, intensity))

    return "\n".join(lines)


def narrate_scene(scene_result, intensity="moderate"):
    """Narrate a full scene as flowing, evocative prose."""
    if scene_result is None:
        return "This place has no scent profile — or maybe it just smells like everywhere."

    lines = []
    scene_name = scene_result.get("scene_name", "Unknown place")
    scene_desc = scene_result.get("scene_description", "")

    lines.append(f"✦ {scene_name}")
    if scene_desc:
        lines.append(f"  {scene_desc}")
    lines.append("")

    lines.append(_pick(SCENE_INTROS))
    lines.append("")

    # Unify all notes into a single, curated narration
    all_notes = scene_result.get("all_notes_ranked", [])
    if all_notes:
        lines.append(narrate_descriptors(all_notes, intensity))
    else:
        dominant = scene_result.get("dominant_notes", [])
        subtle = scene_result.get("subtle_notes", [])
        combined = dominant + subtle
        lines.append(narrate_descriptors(combined, intensity))

    return "\n".join(lines)


# ─── Scene Walk (from transitions.py) ────────────────────────────────────

"""
transitions.py — Spatial movement through scent scenes.

Generates multi-position "walks" through a scene, with smells shifting
based on proximity, ambient vs point-source logic, and airflow.
"""




# ─── Position Narrative Templates ────────────────────────────────────────────

POSITION_OPENERS = {
    # Keyed by position index (0 = first, -1 = last, else middle)
    "first": [
        "You're still outside. The air shifts before you even cross the threshold —",
        "Standing at the edge, the first thing that reaches you:",
        "Before you step in, the air is already different here.",
        "You approach, and the boundary between outside and here blurs —",
        "The space announces itself from the doorway.",
    ],
    "middle": [
        "You move deeper.",
        "A few steps in, the air reshuffles.",
        "The balance shifts as you drift further.",
        "Now you're in it. The scent layers rearrange —",
        "Midway through, the profile changes.",
        "The smell bends around you as you go deeper.",
        "Here, the air thickens.",
        "You pause. Something different reaches you from this angle.",
    ],
    "last": [
        "At the heart of it now.",
        "You've arrived at the center. This is where it all converges.",
        "This deep in, the air is saturated.",
        "You stop here. The scent is loudest at this spot.",
        "The deepest point. Everything distilled.",
        "And here, at the core of the space —",
    ],
}

MOVEMENT_CONNECTORS = [
    "You pass through a curtain of {smell} as you move.",
    "Something catches you mid-step — {smell}.",
    "The air carries {smell} from somewhere to your left.",
    "A draft pushes {smell} past you.",
    "Wind shifts. Now there's {smell} underneath everything.",
    "{smell} drifts in from nearby, mixing with what was already here.",
    "You turn your head and catch {smell} on the air current.",
    "The breeze is doing something — carrying {smell} from further in.",
]

AMBIENT_PHRASES = [
    "Everywhere, like wallpaper for the nose: {smell}.",
    "{smell} — it's constant, soaked into the walls, the floor, the air itself.",
    "The baseline here is {smell}. It never leaves.",
    "{smell} hangs in the air like humidity. Inescapable.",
    "Under everything, always: {smell}.",
]

INTENSITY_SHIFTS = {
    "approaching": [
        "growing stronger now —",
        "building as you get closer —",
        "intensifying with each step —",
        "sharpening —",
    ],
    "fading": [
        "fading behind you now,",
        "thinning as you move past,",
        "dissolving into the background,",
        "growing fainter,",
    ],
    "peak": [
        "hitting full force —",
        "at its strongest right here —",
        "concentrated, almost overwhelming —",
        "peaking —",
    ],
}

# Default walk structure for scenes without explicit walk data
DEFAULT_POSITIONS = [
    {"name": "outside", "zone": "approach"},
    {"name": "the entrance", "zone": "threshold"},
    {"name": "inside", "zone": "interior"},
    {"name": "the far end", "zone": "deep"},
]


class SceneWalk:
    """
    Generates a spatial narrative walk through a scene.
    
    Takes a scene's compound data and optional walk layout,
    produces multi-paragraph prose describing smells shifting
    as you move through the space.
    """

    def __init__(self, scene_data, walk_data, compound_results, db):
        """
        Args:
            scene_data: dict with name, description, compounds
            walk_data: optional dict with positions list, or None
            compound_results: list of (compound_name, query_result) tuples
            db: SmellDB instance for lookups
        """
        self.scene_data = scene_data
        self.walk_data = walk_data
        self.compound_results = compound_results
        self.db = db
        
        # Build compound → descriptors map
        self.compound_descriptors = {}
        self.all_descriptors = []
        for name, result in compound_results:
            if result and result.get("descriptors"):
                self.compound_descriptors[name.lower()] = result["descriptors"]
                self.all_descriptors.extend(result["descriptors"])

    def _get_positions(self):
        """Get walk positions — from walk data or generate defaults."""
        if self.walk_data and "positions" in self.walk_data:
            return self.walk_data["positions"]
        return self._generate_default_positions()

    def _generate_default_positions(self):
        """Generate reasonable default positions from compound list."""
        compounds = list(self.compound_descriptors.keys())
        if not compounds:
            return DEFAULT_POSITIONS

        random.shuffle(compounds)
        
        # Split compounds across default positions
        positions = []
        n = len(compounds)
        chunks = [
            compounds[:max(1, n // 4)],
            compounds[max(1, n // 4):max(2, n // 2)],
            compounds[max(2, n // 2):max(3, 3 * n // 4)],
            compounds[max(3, 3 * n // 4):],
        ]
        
        for i, default in enumerate(DEFAULT_POSITIONS):
            pos = dict(default)
            pos["emphasis"] = chunks[i] if i < len(chunks) else []
            pos["ambient"] = (i >= 1)  # outside is not ambient
            positions.append(pos)
        
        return positions

    def _get_descriptors_for_position(self, position, pos_index, total_positions):
        """
        Get weighted descriptors for a position based on emphasis,
        ambient/point-source logic, and proximity.
        """
        emphasis = [e.lower() for e in position.get("emphasis", [])]
        is_ambient = position.get("ambient", False)
        
        descriptors = []
        
        # Emphasized compounds at this position — full descriptors
        for compound in emphasis:
            if compound in self.compound_descriptors:
                descriptors.extend(self.compound_descriptors[compound])
        
        # Ambient compounds bleed into every position (at reduced count)
        if self.walk_data and "positions" in self.walk_data:
            for other_pos in self.walk_data["positions"]:
                if other_pos.get("ambient", False) and other_pos != position:
                    for compound in [c.lower() for c in other_pos.get("emphasis", [])]:
                        if compound in self.compound_descriptors:
                            # Take only 1-2 descriptors from ambient sources
                            descs = self.compound_descriptors[compound]
                            descriptors.extend(descs[:min(2, len(descs))])
        
        # If this position IS ambient, add the "soaked in" quality
        if is_ambient and emphasis:
            for compound in emphasis:
                if compound in self.compound_descriptors:
                    descriptors.extend(self.compound_descriptors[compound])
        
        # For positions without emphasis, sample from all compounds
        if not emphasis:
            all_compounds = list(self.compound_descriptors.keys())
            sample_size = min(3, len(all_compounds))
            sampled = random.sample(all_compounds, sample_size)
            for compound in sampled:
                descriptors.extend(self.compound_descriptors[compound][:3])
        
        return descriptors

    def _narrate_position(self, position, descriptors, pos_index, total):
        """Generate prose for a single position."""
        if not descriptors:
            return ""
        
        # Select position opener
        if pos_index == 0:
            opener = _pick(POSITION_OPENERS["first"])
        elif pos_index == total - 1:
            opener = _pick(POSITION_OPENERS["last"])
        else:
            opener = _pick(POSITION_OPENERS["middle"])
        
        pos_name = position.get("name", "here")
        is_ambient = position.get("ambient", False)
        
        # Build the scent narrative for this position
        selected = _select_top_descriptors(descriptors, max_count=7)
        cluster_phrases, remaining = _find_clusters(selected)
        
        parts = []
        
        # Opener with position name
        parts.append(f"**{pos_name.title()}**")
        parts.append("")
        parts.append(opener)
        parts.append("")
        
        # Cluster phrases first
        for cp in cluster_phrases:
            parts.append(cp + ".")
        
        # Individual descriptors with movement language
        phrases_used = 0
        for desc in remaining:
            phrase = _descriptor_to_phrase(desc)
            if not phrase:
                continue
            
            if is_ambient and phrases_used == 0:
                template = _pick(AMBIENT_PHRASES)
                parts.append(template.format(smell=phrase))
            elif phrases_used == 0 and not cluster_phrases:
                parts.append(phrase[0].upper() + phrase[1:] + ".")
            else:
                # Use movement connectors occasionally
                if random.random() < 0.35 and phrases_used > 0:
                    connector = _pick(MOVEMENT_CONNECTORS)
                    parts.append(connector.format(smell=phrase))
                else:
                    trans = _pick(TRANSITIONS)
                    parts.append(f"{trans} {phrase}.")
            phrases_used += 1
            if phrases_used >= 4:
                break
        
        # Add intensity shift hint for transitions
        if pos_index > 0 and pos_index < total - 1:
            emphasis = [e.lower() for e in position.get("emphasis", [])]
            if emphasis and emphasis[0] in self.compound_descriptors:
                descs = self.compound_descriptors[emphasis[0]]
                if descs:
                    shift_phrase = _pick(INTENSITY_SHIFTS["approaching"])
                    hint = _descriptor_to_phrase(descs[0])
                    if hint:
                        parts.append(f"{shift_phrase} {hint}.")
        elif pos_index == total - 1:
            emphasis = [e.lower() for e in position.get("emphasis", [])]
            if emphasis and emphasis[0] in self.compound_descriptors:
                descs = self.compound_descriptors[emphasis[0]]
                if descs:
                    shift_phrase = _pick(INTENSITY_SHIFTS["peak"])
                    hint = _descriptor_to_phrase(descs[0])
                    if hint:
                        parts.append(f"{shift_phrase} {hint}.")
        
        return " ".join(parts)

    def generate(self):
        """Generate the full walk narrative."""
        positions = self._get_positions()
        if not positions:
            return "This place has no geography to walk through."
        
        scene_name = self.scene_data.get("name", "Unknown")
        scene_desc = self.scene_data.get("description", "")
        
        sections = []
        sections.append(f"✦ Walking Through: {scene_name}")
        if scene_desc:
            sections.append(f"  {scene_desc}")
        sections.append("")
        sections.append("─" * 50)
        
        total = len(positions)
        for i, pos in enumerate(positions):
            descriptors = self._get_descriptors_for_position(pos, i, total)
            narrative = self._narrate_position(pos, descriptors, i, total)
            if narrative:
                sections.append("")
                sections.append(narrative)
                if i < total - 1:
                    sections.append("")
                    sections.append("─" * 50)
        
        sections.append("")
        sections.append("─" * 50)
        # Closing line
        closers = [
            f"You carry the scent of {scene_name.lower()} with you when you leave. It clings.",
            f"Step outside, and for a moment, {scene_name.lower()} is still in your lungs.",
            f"The air outside feels thin after that. Empty. You didn't realize how much {scene_name.lower()} had surrounded you until it was gone.",
        ]
        sections.append(_pick(closers))
        
        return "\n".join(sections)


def walk_scene(db, scene_name):
    """
    Main entry point: generate a walk narrative for a scene.
    
    Args:
        db: SmellDB instance
        scene_name: scene key string
    
    Returns:
        str: full walk narrative, or error message
    """
    import difflib as _difflib
    
    scenes = db.load_scenes()
    scene_key = scene_name.strip().lower()
    
    if scene_key not in scenes:
        matches = _difflib.get_close_matches(scene_key, scenes.keys(), n=1, cutoff=0.5)
        if matches:
            scene_key = matches[0]
        else:
            available = ", ".join(sorted(scenes.keys()))
            return f"❌ Scene '{scene_name}' not found. Available: {available}"
    
    scene_data = scenes[scene_key]
    walk_data = scene_data.get("walk", None)
    
    # Look up all compounds
    compound_results = []
    for compound in scene_data.get("compounds", []):
        result = db.query(compound)
        compound_results.append((compound, result))
    
    walker = SceneWalk(scene_data, walk_data, compound_results, db)
    return walker.generate()
