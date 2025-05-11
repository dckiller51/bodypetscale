"""Util module."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from homeassistant.config_entries import ConfigEntry

from .data_tables import (
    ACTIVITY_FACTORS,
    APPETITE_FACTORS,
    BREED_FACTORS,
    CAT_LIFE_STAGE_FACTORS,
    DOG_LIFE_STAGE_FACTORS,
    ENVIRONMENT_FACTORS,
    MORPHOLOGY_FACTORS,
    MORPHOLOGY_PERCENTAGES,
    PUPPY_STAGES,
    REPRODUCTIVE_FACTORS,
    TEMPERAMENT_FACTORS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class EnergyConfig:
    """Subset of config used to calculate energy needs."""
    animal_type: str
    breed: str
    life_stage: str
    activity: str
    reproductive: str
    morphology: str
    environment: str
    appetite: Optional[str] = None
    temperament: Optional[str] = None


@dataclass
class PetScaleConfig:
    """Configuration container for BodyPetScale coordinator."""
    weight_sensor: str
    last_time_sensor: Optional[str]
    activity: str
    appetite: str
    animal_type: str
    birthday: str
    breed: str
    environment: str
    morphology: str
    name: str
    reproductive: str
    temperament: str


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


def get_age(date: str) -> int:
    """Get current age from birthdate."""
    born = datetime.strptime(date, "%Y-%m-%d")
    today = datetime.today()
    age = today.year - born.year
    if (today.month, today.day) < (born.month, born.day):
        age -= 1
    return age


def get_age_in_months(date: str) -> int:
    """Get current age in months from birthdate."""
    age_years = get_age(date)
    today = datetime.today()
    months = today.month + (age_years * 12)
    if today.day < datetime.strptime(date, "%Y-%m-%d").day:
        months -= 1
    return months


def get_cat_age_stage(date: str) -> str:
    """Return cat life stage based on age in months."""
    age_months = get_age_in_months(date)

    if 2 <= age_months < 4:
        return "kitten_2_4"
    if 4 <= age_months < 6:
        return "kitten_4_6"
    if 6 <= age_months < 8:
        return "kitten_6_8"
    if 8 <= age_months < 12:
        return "young_adult_8_12"
    if 12 <= age_months < 84:
        return "adult"
    return "senior"


def get_dog_age_stage(date: str, weight: float) -> str:
    """Return dog life stage based on age in months and adult weight."""
    age_months = get_age_in_months(date)

    if age_months >= 96:
        return "senior"

    for (weight_min, weight_max), (age_min, age_max), stage in PUPPY_STAGES:
        if weight_min <= weight < weight_max and age_min <= age_months <= age_max:
            return stage

    return "adult"


def get_common_energy_factor(config: EnergyConfig) -> float:
    """Calculate the common energy factor for cats or dogs."""

    if config.animal_type not in ("cat", "dog"):
        raise ValueError(f"Invalid animal_type '{config.animal_type}' (must be 'cat' or 'dog').")

    try:
        breed_factor = BREED_FACTORS[config.breed]
        life_stage_factor = (
            CAT_LIFE_STAGE_FACTORS[config.life_stage]
            if config.animal_type == "cat"
            else DOG_LIFE_STAGE_FACTORS[config.life_stage]
        )
        activity_factor = ACTIVITY_FACTORS[config.activity]
        reproductive_factor = REPRODUCTIVE_FACTORS[config.reproductive]
        morphology_factor = MORPHOLOGY_FACTORS[config.morphology]
        environment_factor = ENVIRONMENT_FACTORS[config.environment]

        if config.animal_type == "cat":
            if not config.temperament:
                raise ValueError("Temperament is required for cats.")
            temperament_factor = TEMPERAMENT_FACTORS[config.temperament]
            total_factor = (
                breed_factor
                * life_stage_factor
                * activity_factor
                * reproductive_factor
                * morphology_factor
                * environment_factor
                * temperament_factor
            )
        else:
            if not config.appetite:
                raise ValueError("Appetite is required for dogs.")
            appetite_factor = APPETITE_FACTORS[config.appetite]
            total_factor = (
                breed_factor
                * life_stage_factor
                * activity_factor
                * reproductive_factor
                * morphology_factor
                * environment_factor
                * appetite_factor
            )

    except KeyError as e:
        raise ValueError(f"Invalid factor key: {e.args[0]}") from e

    return total_factor


def calculate_energy_need(
    config: EnergyConfig,
    ideal_weight: float,
) -> Optional[int]:
    """Calculate energy need for a pet based on multiple factors."""

    if config.animal_type == "cat":
        required = [config.activity, config.breed, config.life_stage,
                    config.environment, config.reproductive,
                    config.morphology, config.temperament]
    elif config.animal_type == "dog":
        required = [config.activity, config.breed, config.life_stage,
                    config.environment, config.reproductive,
                    config.morphology, config.appetite]
    else:
        _LOGGER.error("Invalid animal type: %s", config.animal_type)
        return None

    if not all(required):
        _LOGGER.error("One or more required configuration values are missing for %s.", config.animal_type)
        return None

    try:
        total_factor = get_common_energy_factor(config)
    except ValueError as e:
        _LOGGER.error("Error calculating energy factor: %s", e)
        return None

    if config.animal_type == "cat":
        base_energy = 100 * (ideal_weight ** 0.667)
        energy_need = round(total_factor * base_energy, 0)
    else:
        if ideal_weight < 21:
            base_energy = (ideal_weight ** 0.75) * 120
        else:
            base_energy = (ideal_weight ** 0.667) * 156
        energy_need = base_energy * total_factor

    return int(round(energy_need))
