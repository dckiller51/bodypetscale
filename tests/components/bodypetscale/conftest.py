"""Fixtures for bodypetscale tests."""

from __future__ import annotations

import pytest
from homeassistant.const import CONF_NAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bodypetscale.const import (
    CONF_ACTIVITY,
    CONF_ANIMAL_TYPE,
    CONF_APPETITE,
    CONF_BIRTHDAY,
    CONF_BREED,
    CONF_LAST_TIME_SENSOR,
    CONF_LIVING_ENVIRONMENT,
    CONF_MORPHOLOGY,
    CONF_REPRODUCTIVE,
    CONF_TEMPERAMENT,
    CONF_WEIGHT_SENSOR,
    DOMAIN,
)

WEIGHT_SENSOR = "sensor.pet_weight"
LAST_TIME_SENSOR = "sensor.pet_last_weighing"

DOG_DATA = {
    CONF_NAME: "Rex",
    CONF_ANIMAL_TYPE: "dog",
    CONF_BIRTHDAY: "2020-01-15",
    CONF_BREED: "beagle",
    CONF_ACTIVITY: "normal",
    CONF_REPRODUCTIVE: "neutered",
    CONF_APPETITE: "normal",
}

DOG_OPTIONS = {
    CONF_LIVING_ENVIRONMENT: "indoors",
    CONF_MORPHOLOGY: "5_ideal",
    CONF_WEIGHT_SENSOR: WEIGHT_SENSOR,
}

CAT_DATA = {
    CONF_NAME: "Felix",
    CONF_ANIMAL_TYPE: "cat",
    CONF_BIRTHDAY: "2021-06-10",
    CONF_BREED: "chartreux",
    CONF_ACTIVITY: "no_outdoor_access",
    CONF_REPRODUCTIVE: "neutered",
    CONF_TEMPERAMENT: "calm",
}

CAT_OPTIONS = {
    CONF_LIVING_ENVIRONMENT: "indoors",
    CONF_MORPHOLOGY: "6_slightly_overweight",
    CONF_WEIGHT_SENSOR: WEIGHT_SENSOR,
    CONF_LAST_TIME_SENSOR: LAST_TIME_SENSOR,
}


@pytest.fixture
def dog_entry() -> MockConfigEntry:
    """Return a config entry for a dog without last time sensor."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Rex",
        unique_id="rex",
        data=dict(DOG_DATA),
        options=dict(DOG_OPTIONS),
    )


@pytest.fixture
def cat_entry() -> MockConfigEntry:
    """Return a config entry for a cat with a last time sensor."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Felix",
        unique_id="felix",
        data=dict(CAT_DATA),
        options=dict(CAT_OPTIONS),
    )
