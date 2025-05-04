"""Constants for the BodyPetScale integration."""

DOMAIN = "bodypetscale"
NAME = "BodyPetScale"
VERSION = "2025.5.0"

ISSUE_URL = "https://github.com/dckiller51/bodypetscale/issues"

CONF_ANIMAL_TYPE = "animal_type"
CONF_MORPHOLOGY = "morphology"
CONF_WEIGHT_SENSOR = "weight"
CONF_LAST_TIME_SENSOR = "last_measurement_time"

ATTR_BODY_TYPE = "body_type"
ATTR_IDEAL = "ideal_weight"
ATTR_MAIN = "main"

ANIMAL_LABELS = {"dog": "Dog", "cat": "Cat"}

ANIMAL_TYPES = ["dog", "cat"]

MORPHOLOGY_OPTIONS = [
    "1_very_thin",
    "2_underweight",
    "3_slightly_underweight",
    "4_ideal",
    "5_ideal",
    "6_slightly_overweight",
    "7_overweight",
    "8_obese",
    "9_very_obese",
]

# Table (Index, % Dog, % Cat)
MORPHOLOGY_PERCENTAGES = {
    1: {"dog": 1.4, "cat": 1.3},
    2: {"dog": 1.3, "cat": 1.225},
    3: {"dog": 1.2, "cat": 1.15},
    4: {"dog": 1.1, "cat": 1.075},
    5: {"dog": 1.0, "cat": 1.0},
    6: {"dog": 0.9, "cat": 0.925},
    7: {"dog": 0.8, "cat": 0.85},
    8: {"dog": 0.7, "cat": 0.775},
    9: {"dog": 0.6, "cat": 0.7},
}

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
