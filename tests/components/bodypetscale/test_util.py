"""Tests for the bodypetscale util module."""

from __future__ import annotations

from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bodypetscale.const import CONF_WEIGHT_SENSOR, DOMAIN
from custom_components.bodypetscale.util import (
    EnergyConfig,
    calculate_energy_need,
    calculate_ideal_weight,
    get_age_in_months,
    get_age_string,
    get_cat_age_stage,
    get_common_energy_factor,
    get_config_option,
    get_dog_age_stage,
)

TODAY = "2026-10-20 12:00:00"


def _dog_config(**overrides: Any) -> EnergyConfig:
    """Return a valid dog energy config (total factor 0.72)."""
    values: dict[str, Any] = {
        "animal_type": "dog",
        "breed": "beagle",
        "life_stage": "adult",
        "activity": "normal",
        "reproductive": "neutered",
        "morphology": "5_ideal",
        "environment": "indoors",
        "appetite": "normal",
    }
    values.update(overrides)
    return EnergyConfig(**values)


def _cat_config(**overrides: Any) -> EnergyConfig:
    """Return a valid cat energy config (total factor 0.5832)."""
    values: dict[str, Any] = {
        "animal_type": "cat",
        "breed": "chartreux",
        "life_stage": "adult",
        "activity": "no_outdoor_access",
        "reproductive": "neutered",
        "morphology": "6_slightly_overweight",
        "environment": "indoors",
        "temperament": "calm",
    }
    values.update(overrides)
    return EnergyConfig(**values)


# ---------------------------------------------------------------------------
# calculate_ideal_weight
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("weight", "morphology", "animal_type", "expected"),
    [
        (10.0, "5_ideal", "dog", 10.0),
        (10.0, "7_overweight", "dog", 8.0),
        (10.0, "1_very_thin", "dog", 14.0),
        (4.0, "6_slightly_overweight", "cat", 3.7),
        (4.0, "9_very_obese", "cat", 2.8),
    ],
)
def test_calculate_ideal_weight(
    weight: float, morphology: str, animal_type: str, expected: float
) -> None:
    """Ideal weight is the weight scaled by the morphology percentage."""
    assert calculate_ideal_weight(weight, morphology, animal_type) == pytest.approx(
        expected
    )


@pytest.mark.parametrize(
    ("weight", "morphology", "animal_type"),
    [
        (None, "5_ideal", "dog"),
        (10.0, None, "dog"),
        (10.0, "5_ideal", None),
        (10.0, "ideal", "dog"),
        (10.0, "12_unknown", "dog"),
        (10.0, "5_ideal", "rabbit"),
    ],
)
def test_calculate_ideal_weight_invalid(
    weight: float | None, morphology: str | None, animal_type: str | None
) -> None:
    """Invalid or missing input returns None."""
    assert calculate_ideal_weight(weight, morphology, animal_type) is None


# ---------------------------------------------------------------------------
# get_config_option
# ---------------------------------------------------------------------------


def test_get_config_option_prefers_options() -> None:
    """Options take precedence over data, data is the fallback."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_WEIGHT_SENSOR: "sensor.data", "only_data": "d"},
        options={CONF_WEIGHT_SENSOR: "sensor.options"},
    )
    assert get_config_option(entry, CONF_WEIGHT_SENSOR) == "sensor.options"
    assert get_config_option(entry, "only_data") == "d"
    assert get_config_option(entry, "missing", "default") == "default"


# ---------------------------------------------------------------------------
# Age helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("birthday", "months"),
    [
        ("2026-10-20", 0),
        ("2026-09-21", 0),
        ("2026-09-20", 1),
        ("2025-10-20", 12),
        ("2020-01-15", 81),
    ],
)
def test_get_age_in_months(freezer: Any, birthday: str, months: int) -> None:
    """Age in months only counts completed months."""
    freezer.move_to(TODAY)
    assert get_age_in_months(birthday) == months


@pytest.mark.parametrize(
    ("birthday", "expected"),
    [
        ("2026-07-20", "3 months"),
        ("2026-09-20", "1 month"),
        ("2025-10-20", "1 year"),
        ("2023-10-20", "3 years"),
        ("2025-09-20", "1 year and 1 month"),
        ("2020-01-15", "6 years and 9 months"),
    ],
)
def test_get_age_string(freezer: Any, birthday: str, expected: str) -> None:
    """Age string uses singular and plural labels."""
    freezer.move_to(TODAY)
    assert get_age_string(birthday) == expected


@pytest.mark.parametrize(
    ("birthday", "stage"),
    [
        ("2026-09-20", "senior"),  # 1 month: below the kitten range
        ("2026-07-20", "kitten_2_4"),
        ("2026-05-20", "kitten_4_6"),
        ("2026-03-20", "kitten_6_8"),
        ("2026-01-20", "young_adult_8_12"),
        ("2021-06-10", "adult"),
        ("2018-10-20", "senior"),
    ],
)
def test_get_cat_age_stage(freezer: Any, birthday: str, stage: str) -> None:
    """Cat life stage follows the age in months."""
    freezer.move_to(TODAY)
    assert get_cat_age_stage(birthday) == stage


@pytest.mark.parametrize(
    ("birthday", "weight", "stage"),
    [
        ("2026-06-20", 5.0, "puppy_low_3_4"),
        ("2026-04-20", 15.0, "puppy_20_6_9"),
        ("2025-10-20", 30.0, "puppy_35_11_15"),
        ("2025-10-20", 40.0, "puppy_50_8_13"),
        ("2025-03-20", 60.0, "puppy_high_14_21"),
        ("2025-10-20", 5.0, "adult"),
        ("2020-01-15", 10.0, "adult"),
        ("2018-10-20", 10.0, "senior"),
    ],
)
def test_get_dog_age_stage(
    freezer: Any, birthday: str, weight: float, stage: str
) -> None:
    """Dog life stage depends on age and weight class."""
    freezer.move_to(TODAY)
    assert get_dog_age_stage(birthday, weight) == stage


# ---------------------------------------------------------------------------
# Energy factor and need
# ---------------------------------------------------------------------------


def test_get_common_energy_factor_dog() -> None:
    """Dog factor multiplies all dog factors including appetite."""
    assert get_common_energy_factor(_dog_config()) == pytest.approx(0.72)


def test_get_common_energy_factor_cat() -> None:
    """Cat factor multiplies all cat factors including temperament."""
    assert get_common_energy_factor(_cat_config()) == pytest.approx(0.5832)


@pytest.mark.parametrize(
    "config",
    [
        _dog_config(animal_type="rabbit"),
        _dog_config(appetite=None),
        _cat_config(temperament=None),
        _dog_config(breed="unknown_breed"),
        _cat_config(life_stage="puppy_low_3_4"),
    ],
)
def test_get_common_energy_factor_invalid(config: EnergyConfig) -> None:
    """Invalid configuration raises ValueError."""
    with pytest.raises(ValueError):
        get_common_energy_factor(config)


@pytest.mark.parametrize(
    ("config", "ideal_weight", "expected"),
    [
        (_dog_config(), 10.0, 486),  # small dog formula (< 21 kg)
        (_dog_config(), 30.0, 1086),  # large dog formula (>= 21 kg)
        (_cat_config(), 3.7, 140),
    ],
)
def test_calculate_energy_need(
    config: EnergyConfig, ideal_weight: float, expected: int
) -> None:
    """Energy need is computed in kcal and rounded to an int."""
    result = calculate_energy_need(config, ideal_weight)
    assert result == expected
    assert isinstance(result, int)


@pytest.mark.parametrize(
    "config",
    [
        _dog_config(animal_type="rabbit"),
        _dog_config(appetite=""),
        _cat_config(temperament=""),
        _dog_config(environment=""),
        _dog_config(breed="unknown_breed"),
    ],
)
def test_calculate_energy_need_invalid(config: EnergyConfig) -> None:
    """Missing or invalid configuration returns None."""
    assert calculate_energy_need(config, 10.0) is None
