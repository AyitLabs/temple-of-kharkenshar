"""
mindscape_schema.py — Unified multi-sensory scene format for Project Senses.

A MindscapeScene holds smell + sight + sound + touch profiles, spatial layout,
environmental conditions, temporal dynamics, and cross-sensory coherence rules.
"""

import json
from pathlib import Path


# ─── Temporal Dynamics ──────────────────────────────────────────────────────

class TimeState:
    """Time-of-day as a physics variable affecting all senses."""

    TIMES = ["dawn", "morning", "midday", "afternoon", "golden_hour", "dusk", "night", "late_night"]

    # Each time state defines physical parameters that propagate through senses
    PROFILES = {
        "dawn": {
            "light_color_temp_K": 3000,
            "ambient_light_level": 0.15,
            "typical_sounds_modifier": 1.3,    # dawn chorus amplified
            "smell_volatility_modifier": 0.7,   # dew suppresses volatiles
            "temperature_offset_c": -4,          # coolest part of day
            "touch_notes": "dew-wet surfaces, cool still air, moisture on skin",
        },
        "morning": {
            "light_color_temp_K": 4500,
            "ambient_light_level": 0.6,
            "typical_sounds_modifier": 1.1,
            "smell_volatility_modifier": 0.9,
            "temperature_offset_c": -2,
            "touch_notes": "warming surfaces, evaporating dew, gentle air",
        },
        "midday": {
            "light_color_temp_K": 6500,
            "ambient_light_level": 1.0,
            "typical_sounds_modifier": 0.9,     # heat dampens activity
            "smell_volatility_modifier": 1.3,   # heat drives volatiles
            "temperature_offset_c": 3,
            "touch_notes": "hot surfaces, radiant heat from above, dry air",
        },
        "afternoon": {
            "light_color_temp_K": 5500,
            "ambient_light_level": 0.85,
            "typical_sounds_modifier": 1.0,
            "smell_volatility_modifier": 1.2,
            "temperature_offset_c": 2,
            "touch_notes": "warm materials retaining heat, ambient warmth",
        },
        "golden_hour": {
            "light_color_temp_K": 3500,
            "ambient_light_level": 0.5,
            "typical_sounds_modifier": 1.0,
            "smell_volatility_modifier": 1.1,
            "temperature_offset_c": 0,
            "touch_notes": "cooling air on warm skin, long shadows creating cool patches",
        },
        "dusk": {
            "light_color_temp_K": 2800,
            "ambient_light_level": 0.2,
            "typical_sounds_modifier": 1.2,     # evening activity
            "smell_volatility_modifier": 1.0,
            "temperature_offset_c": -2,
            "touch_notes": "cooling surfaces, slight chill in shade, damp settling",
        },
        "night": {
            "light_color_temp_K": 4100,         # moonlight is actually cool
            "ambient_light_level": 0.05,
            "typical_sounds_modifier": 1.4,     # night amplifies perception
            "smell_volatility_modifier": 0.8,
            "temperature_offset_c": -5,
            "touch_notes": "cold surfaces, damp air, heightened skin sensitivity in dark",
        },
        "late_night": {
            "light_color_temp_K": 4100,
            "ambient_light_level": 0.02,
            "typical_sounds_modifier": 1.5,     # maximum quiet = maximum perception
            "smell_volatility_modifier": 0.7,
            "temperature_offset_c": -6,
            "touch_notes": "coldest surfaces, still heavy air, numbness at extremities",
        },
    }

    @classmethod
    def get(cls, time_of_day):
        """Return the profile for a given time, defaulting to afternoon."""
        return cls.PROFILES.get(time_of_day, cls.PROFILES["afternoon"])

    @classmethod
    def effective_temperature(cls, base_temp, time_of_day):
        """Apply temporal offset to base temperature."""
        profile = cls.get(time_of_day)
        return base_temp + profile["temperature_offset_c"]

    @classmethod
    def effective_smell_volatility(cls, time_of_day):
        """Smell volatility modifier for this time."""
        return cls.get(time_of_day)["smell_volatility_modifier"]

    @classmethod
    def effective_sound_modifier(cls, time_of_day):
        """Sound perception modifier for this time."""
        return cls.get(time_of_day)["typical_sounds_modifier"]


class EnvironmentalConditions:
    """Physical conditions that link all senses."""

    DEFAULTS = {
        "temperature_c": 22,
        "humidity_pct": 50,
        "wind_speed_kmh": 0,
        "wind_direction": None,  # "from_north", etc.
        "time_of_day": "day",    # dawn, morning, day, afternoon, golden_hour, dusk, night, late_night
        "weather": "clear",      # clear, cloudy, overcast, rain, heavy_rain, fog, snow, storm
        "altitude_m": 0,
        "indoor": False,
    }

    def __init__(self, data=None):
        d = dict(self.DEFAULTS)
        if data:
            d.update(data)
        for k, v in d.items():
            setattr(self, k, v)

    def to_dict(self):
        return {k: getattr(self, k) for k in self.DEFAULTS}

    # ─── Cross-sensory physics ───────────────────────────────────────

    @property
    def smell_carry_multiplier(self):
        """How far smells travel. Humidity and wind increase carry."""
        base = 1.0
        if self.humidity_pct > 70:
            base *= 1.3
        elif self.humidity_pct > 85:
            base *= 1.5
        elif self.humidity_pct < 30:
            base *= 0.7
        if self.temperature_c > 30:
            base *= 1.3
        elif self.temperature_c < 5:
            base *= 0.6
        if self.wind_speed_kmh > 15:
            base *= 1.4
        elif self.wind_speed_kmh > 5:
            base *= 1.2
        if self.weather in ("rain", "heavy_rain"):
            base *= 0.8
        # Temporal modifier
        base *= TimeState.effective_smell_volatility(self.time_of_day)
        return base

    @property
    def visual_clarity(self):
        """0-1 scale. Fog, rain, humidity reduce it."""
        base = 1.0
        if self.weather == "fog":
            base = 0.2
        elif self.weather in ("rain", "heavy_rain"):
            base = 0.5
        elif self.weather == "snow":
            base = 0.6
        if self.humidity_pct > 85:
            base *= 0.7
        if self.temperature_c > 35:
            base *= 0.9
        # Temporal: light level affects effective visual clarity
        time_profile = TimeState.get(self.time_of_day)
        base *= max(0.3, time_profile["ambient_light_level"])
        return max(0.1, min(1.0, base))

    @property
    def sound_absorption(self):
        """Higher = more absorbed (softer). Humidity, rain, snow absorb sound."""
        base = 0.0
        if self.humidity_pct > 80:
            base += 0.2
        if self.weather in ("rain", "heavy_rain"):
            base += 0.3
        if self.weather == "snow":
            base += 0.4
        if self.weather == "fog":
            base += 0.15
        if self.wind_speed_kmh > 20:
            base += 0.2
        return min(0.8, base)

    @property
    def adds_petrichor(self):
        return self.weather in ("rain", "heavy_rain") or (
            self.weather == "clear" and self.humidity_pct > 80
        )

    @property
    def light_quality(self):
        """Describe the dominant light character based on time + weather."""
        tod = self.time_of_day
        w = self.weather
        if tod in ("night", "late_night"):
            if w == "clear":
                return "moonlit" if not self.indoor else "artificial"
            return "dark"
        if tod in ("dawn", "dusk"):
            return "twilight"
        if tod == "golden_hour":
            return "golden"
        if w == "fog":
            return "diffused"
        if w in ("overcast", "cloudy"):
            return "flat"
        if w in ("rain", "heavy_rain"):
            return "grey_wet"
        return "daylight"

    # ─── Touch physics ───────────────────────────────────────────────

    @property
    def thermal_feel(self):
        """
        How temperature actually feels on skin, accounting for humidity and wind.
        Wind chill, humid heat, dry cold — the felt temperature vs actual.
        """
        temp = self.temperature_c
        wind = self.wind_speed_kmh
        hum = self.humidity_pct

        # Wind chill (simplified Siple-Passel for cold + wind)
        if temp < 10 and wind > 5:
            # Wind strips body heat
            chill_offset = wind * 0.3  # rough: each 10kmh = ~3°C colder feel
            felt_temp = temp - chill_offset
            if felt_temp < -10:
                return f"biting cold (feels like {felt_temp:.0f}°C with wind chill) — exposed skin stings, metal burns to touch"
            elif felt_temp < 0:
                return f"sharp cold (feels like {felt_temp:.0f}°C) — wind strips warmth from any exposed surface"
            else:
                return f"cutting chill (feels like {felt_temp:.0f}°C) — wind makes it feel colder than the thermometer says"

        # Humid heat (heat index approximation)
        if temp > 27 and hum > 60:
            # Sweat can't evaporate — feels hotter
            heat_add = (hum - 50) * 0.1  # rough: each 10% above 50 = ~1°C hotter feel
            felt_temp = temp + heat_add
            if felt_temp > 40:
                return f"oppressive heat (feels like {felt_temp:.0f}°C) — humidity traps body heat, skin stays slick, nothing dries"
            else:
                return f"sticky warmth (feels like {felt_temp:.0f}°C) — humid air resists evaporative cooling, sweat lingers"

        # Dry cold
        if temp < 5 and hum < 30:
            return f"dry cold at {temp}°C — skin tightens, lips crack, static builds on every surface you touch"

        # Dry heat
        if temp > 30 and hum < 30:
            return f"dry heat at {temp}°C — sweat evaporates instantly, skin feels papery, metal and stone radiate stored warmth"

        # Comfortable range
        if 18 <= temp <= 26:
            if hum > 70:
                return f"warm and slightly clammy at {temp}°C — the air itself feels thick on skin"
            elif hum < 30:
                return f"comfortably dry at {temp}°C — air moves freely across skin"
            return f"neutral — {temp}°C, the body forgets about temperature entirely"

        # Cool
        if 5 <= temp < 18:
            if wind > 10:
                return f"cool and wind-swept at {temp}°C — air pressure on exposed skin, goosebumps"
            return f"cool at {temp}°C — surfaces are cold to initial touch, then warm under your hand"

        # Warm
        if 26 < temp <= 30:
            return f"warm at {temp}°C — surfaces hold heat, the air feels textured"

        return f"{temp}°C — unremarkable on skin"

    @property
    def tactile_modifiers(self):
        """How environment modifies tactile experience — friction, numbness, wetness."""
        mods = []
        weather = self.weather
        temp = self.temperature_c
        hum = self.humidity_pct
        wind = self.wind_speed_kmh

        # Wet surfaces
        if weather in ("rain", "heavy_rain"):
            mods.append("wet surfaces reduce grip, increase slip — every handrail and step needs attention")
            mods.append("rain on skin: each drop a discrete cold point, constant micro-impacts")
        elif weather == "snow":
            mods.append("snow compresses underfoot with a specific crunch — dry snow squeaks, wet snow thuds")
            mods.append("cold numbs fingertips within minutes, reducing fine motor control")
        elif weather == "fog":
            mods.append("fog deposits micro-droplets on every surface — everything feels slightly damp to touch")

        # Temperature effects on touch
        if temp < 0:
            mods.append("metal sticks to wet skin — thermal conductivity makes metal feel far colder than wood or cloth")
            mods.append("numbness begins at extremities, spreading inward — tactile resolution drops")
        elif temp < 10:
            mods.append("cold surfaces leach heat from fingertips on contact — stone and metal feel hostile")
        elif temp > 35:
            mods.append("surfaces in direct sun too hot to touch — asphalt, metal, car roofs burn")
            mods.append("sweat makes grip uncertain on smooth surfaces")

        # Humidity effects
        if hum > 80:
            mods.append("high humidity: skin stays slightly tacky, paper feels limp, fabric clings")
        elif hum < 25:
            mods.append("dry air: static shocks from metal contact, skin feels tight, paper crackles")

        # Wind
        if wind > 20:
            mods.append("strong wind creates constant pressure on exposed skin — directional, insistent")
        elif wind > 10:
            mods.append("breeze is tactile: you feel air direction changes on your face and hands")

        if not mods:
            mods.append("neutral conditions — touch behaves normally, no environmental modifiers")

        return mods


class WalkPosition:
    """A position within a mindscape you can stand at / walk to."""

    def __init__(self, data):
        self.name = data.get("name", "unknown")
        self.description = data.get("description", "")
        # Per-sense emphasis at this position
        self.smell_emphasis = data.get("smell_emphasis", [])
        self.sight_notes = data.get("sight_notes", "")
        self.sound_notes = data.get("sound_notes", "")
        # Touch at this position
        self.touch_notes = data.get("touch_notes", "")
        self.surface_textures = data.get("surface_textures", [])
        # Taste at this position
        self.taste_compounds = data.get("taste_compounds", [])
        self.taste_notes = data.get("taste_notes", "")
        self.taste_profile = data.get("taste_profile", {})
        self.taste_intensity = data.get("taste_intensity", 0.0)
        # Cross-sensory notes
        self.cross_sensory = data.get("cross_sensory", "")
        self.ambient = data.get("ambient", False)
        # Pre-composed prose (if available)
        self.prose = data.get("prose", "")

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "smell_emphasis": self.smell_emphasis,
            "sight_notes": self.sight_notes,
            "sound_notes": self.sound_notes,
            "touch_notes": self.touch_notes,
            "surface_textures": self.surface_textures,
            "taste_compounds": self.taste_compounds,
            "taste_notes": self.taste_notes,
            "taste_profile": self.taste_profile,
            "taste_intensity": self.taste_intensity,
            "cross_sensory": self.cross_sensory,
            "ambient": self.ambient,
            "prose": self.prose,
        }


class MindscapeScene:
    """A unified multi-sensory scene."""

    def __init__(self, data=None):
        if data is None:
            data = {}
        self._raw_data = data
        self.id = data.get("id", "unknown")
        self.name = data.get("name", "Unknown")
        self.description = data.get("description", "")

        # Sense profiles
        self.smell = data.get("smell", {})
        self.sight = data.get("sight", {})
        self.sound = data.get("sound", {})
        self.touch = data.get("touch", {})  # surface_textures, air_feel, thermal_notes, key_tactile_moments

        # Environmental conditions
        self.environment = EnvironmentalConditions(data.get("environment", {}))

        # Walk positions
        self.positions = [
            WalkPosition(p) for p in data.get("positions", [])
        ]

        # Cross-sensory coherence notes
        self.cross_sensory_bridges = data.get("cross_sensory_bridges", [])

        # Overall pre-composed prose
        self.prose = data.get("prose", "")

        # Mood tags
        self.mood = data.get("mood", [])

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "smell": self.smell,
            "sight": self.sight,
            "sound": self.sound,
            "touch": self.touch,
            "environment": self.environment.to_dict(),
            "positions": [p.to_dict() for p in self.positions],
            "cross_sensory_bridges": self.cross_sensory_bridges,
            "prose": self.prose,
            "mood": self.mood,
        }

    @classmethod
    def from_file(cls, path):
        with open(path) as f:
            return cls(json.load(f))

    def save(self, path):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


def load_all_scenes(scenes_dir):
    """Load all mindscape scenes from a directory."""
    scenes = {}
    p = Path(scenes_dir)
    if not p.exists():
        return scenes
    for f in sorted(p.glob("*.json")):
        try:
            scene = MindscapeScene.from_file(f)
            scenes[scene.id] = scene
        except (json.JSONDecodeError, KeyError):
            pass
    return scenes
