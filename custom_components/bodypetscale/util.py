"""Util module."""

import logging

from .const import MORPHOLOGY_PERCENTAGES

_LOGGER = logging.getLogger(__name__)


def calculate_ideal_weight(weight, morphology, animal_type):
    """Calculate ideal weight based on morphology and animal type."""
    if weight is None or not morphology or not animal_type:
        return None

    try:
        morph_index = int(morphology.split("_")[0])
    except (ValueError, IndexError):
        _LOGGER.warning(
            "Impossible d'extraire l'indice de morphologie depuis %s", morphology
        )
        return None

    if morph_index not in MORPHOLOGY_PERCENTAGES:
        _LOGGER.warning("Indice de morphologie inconnu: %s", morph_index)
        return None

    try:
        percentage = MORPHOLOGY_PERCENTAGES[morph_index][animal_type]
        return round(weight * percentage, 2)
    except KeyError:
        _LOGGER.warning("Type d'animal inconnu ou valeur manquante: %s", animal_type)
    except TypeError as e:
        _LOGGER.error("Erreur de type dans le calcul du poids idéal: %s", e)
    return None


def get_config_option(entry, key, default=None):
    """Récupère une option dans la config avec fallback."""
    return entry.options.get(key) or entry.data.get(key, default)
