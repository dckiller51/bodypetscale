"""Util module."""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from homeassistant.config_entries import ConfigEntry

from .const import MORPHOLOGY_PERCENTAGES

_LOGGER = logging.getLogger(__name__)


def calculate_ideal_weight(weight: Optional[float], morphology: Optional[str], animal_type: Optional[str]) -> Optional[float]:
    """Calculate ideal weight based on morphology and animal type."""
    if weight is None or not morphology or not animal_type:
        return None

    try:
        morph_index = int(morphology.split("_")[0])
    except (ValueError, IndexError):
        _LOGGER.warning(
            "Unable to extract morphology index from %s", morphology
        )
        return None

    if morph_index not in MORPHOLOGY_PERCENTAGES:
        _LOGGER.warning("Unknown morphology index: %s", morph_index)
        return None

    try:
        percentage = MORPHOLOGY_PERCENTAGES[morph_index][animal_type]
        return round(weight * percentage, 2)
    except KeyError:
        _LOGGER.warning("Unknown or missing animal type: %s", animal_type)
    except TypeError as e:
        _LOGGER.error("Type error in ideal weight calculation: %s", e)
    return None


def get_config_option(entry: ConfigEntry, key: str, default: Any = None) -> Any:
    """Retrieve an option from the config with fallback."""
    return entry.options.get(key) or entry.data.get(key, default)


@dataclass
class PetScaleConfig:
    """Configuration container for BodyPetScale coordinator."""
    weight_sensor: str
    last_time_sensor: Optional[str]
    animal_type: str
    morphology: str
    name: str
