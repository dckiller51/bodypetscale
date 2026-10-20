"""Tests for the bodypetscale sensors and coordinator."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bodypetscale.const import (
    ATTR_BODY_TYPE,
    ATTR_ENERGY_NEED,
    ATTR_IDEAL,
    ATTR_MAIN,
    CONF_LAST_TIME_SENSOR,
    CONF_WEIGHT_SENSOR,
    DOMAIN,
)

from .conftest import LAST_TIME_SENSOR, WEIGHT_SENSOR

NOW = "2026-10-20 12:00:00+00:00"
LAST_TIME = "2026-10-20T08:00:00+00:00"


@pytest.fixture(autouse=True)
def _freeze(freezer: Any) -> None:
    """Freeze time so that pet ages are stable."""
    freezer.move_to(NOW)


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


def _entity_id(hass: HomeAssistant, entry: MockConfigEntry, key: str) -> str | None:
    return er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_{key}"
    )


def _state(hass: HomeAssistant, entry: MockConfigEntry, key: str) -> Any:
    entity_id = _entity_id(hass, entry, key)
    assert entity_id is not None, f"no entity for {key}"
    state = hass.states.get(entity_id)
    assert state is not None
    return state


async def test_dog_sensors(hass: HomeAssistant, dog_entry: MockConfigEntry) -> None:
    """A dog entry exposes main, weight, ideal weight, body type and energy."""
    hass.states.async_set(WEIGHT_SENSOR, "10")
    await _setup(hass, dog_entry)

    assert _state(hass, dog_entry, CONF_WEIGHT_SENSOR).state == "10.0"
    assert _state(hass, dog_entry, ATTR_IDEAL).state == "10.0"
    assert _state(hass, dog_entry, ATTR_BODY_TYPE).state == "5_ideal"
    assert _state(hass, dog_entry, ATTR_ENERGY_NEED).state == "486"
    # No last time sensor configured: the entity is not created.
    assert _entity_id(hass, dog_entry, CONF_LAST_TIME_SENSOR) is None

    main = _state(hass, dog_entry, ATTR_MAIN)
    assert main.state == "ok"
    assert main.attributes["icon"] == "mdi:dog"
    assert main.attributes["animal_type"] == "dog"
    assert main.attributes["breed"] == "beagle"
    assert main.attributes["ideal_weight"] == 10.0
    assert main.attributes["energy_need"] == 486
    assert main.attributes["appetite"] == "normal"
    assert main.attributes["age"] == "6 years and 9 months"
    assert "issue" not in main.attributes


async def test_cat_sensors(hass: HomeAssistant, cat_entry: MockConfigEntry) -> None:
    """A cat entry also exposes the last measurement time."""
    hass.states.async_set(WEIGHT_SENSOR, "4")
    hass.states.async_set(LAST_TIME_SENSOR, LAST_TIME)
    await _setup(hass, cat_entry)

    assert _state(hass, cat_entry, ATTR_IDEAL).state == "3.7"
    assert _state(hass, cat_entry, ATTR_ENERGY_NEED).state == "140"
    assert _state(hass, cat_entry, CONF_LAST_TIME_SENSOR).state == LAST_TIME

    main = _state(hass, cat_entry, ATTR_MAIN)
    assert main.state == "ok"
    assert main.attributes["icon"] == "mdi:cat"
    assert main.attributes["temperament"] == "calm"
    assert "last_measurement_time" in main.attributes


async def test_sensors_follow_weight_changes(
    hass: HomeAssistant, dog_entry: MockConfigEntry
) -> None:
    """Sensors are refreshed when the source weight sensor changes."""
    hass.states.async_set(WEIGHT_SENSOR, "10")
    await _setup(hass, dog_entry)
    assert _state(hass, dog_entry, ATTR_ENERGY_NEED).state == "486"

    hass.states.async_set(WEIGHT_SENSOR, "30")
    await hass.async_block_till_done()

    assert _state(hass, dog_entry, CONF_WEIGHT_SENSOR).state == "30.0"
    assert _state(hass, dog_entry, ATTR_IDEAL).state == "30.0"
    assert _state(hass, dog_entry, ATTR_ENERGY_NEED).state == "1086"


@pytest.mark.parametrize(
    ("weight", "issue"),
    [
        ("unavailable", "weight_unavailable"),
        ("not_a_number", "weight_unavailable"),
        ("0", "weight_low"),
        ("120", "weight_high"),
    ],
)
async def test_main_sensor_weight_problems(
    hass: HomeAssistant, dog_entry: MockConfigEntry, weight: str, issue: str
) -> None:
    """The main sensor reports a problem for invalid weights."""
    hass.states.async_set(WEIGHT_SENSOR, weight)
    await _setup(hass, dog_entry)

    main = _state(hass, dog_entry, ATTR_MAIN)
    assert main.state == "problem"
    assert main.attributes["issue"] == issue


async def test_unavailable_weight_clears_metrics(
    hass: HomeAssistant, dog_entry: MockConfigEntry
) -> None:
    """Without a weight, ideal weight and energy need are unknown."""
    hass.states.async_set(WEIGHT_SENSOR, "unavailable")
    await _setup(hass, dog_entry)

    assert _state(hass, dog_entry, ATTR_IDEAL).state == "unknown"
    assert _state(hass, dog_entry, ATTR_BODY_TYPE).state == "unknown"
    assert _state(hass, dog_entry, ATTR_ENERGY_NEED).state == "unknown"


async def test_invalid_last_time(
    hass: HomeAssistant, cat_entry: MockConfigEntry
) -> None:
    """An unparsable last time value is ignored by the coordinator."""
    hass.states.async_set(WEIGHT_SENSOR, "4")
    hass.states.async_set(LAST_TIME_SENSOR, "yesterday")
    await _setup(hass, cat_entry)

    assert _state(hass, cat_entry, CONF_LAST_TIME_SENSOR).state == "unknown"
    coordinator = hass.data[DOMAIN][cat_entry.entry_id]
    assert coordinator.data[CONF_LAST_TIME_SENSOR] is None
    assert coordinator.last_time is None


@pytest.mark.parametrize(
    ("last_time", "issue"),
    [
        ("yesterday", "last_time_unavailable"),
        ("unavailable", "last_time_unavailable"),
    ],
)
async def test_main_sensor_last_time_problems(
    hass: HomeAssistant, cat_entry: MockConfigEntry, last_time: str, issue: str
) -> None:
    """The main sensor checks the last time sensor configured in the options."""
    hass.states.async_set(WEIGHT_SENSOR, "4")
    hass.states.async_set(LAST_TIME_SENSOR, last_time)
    await _setup(hass, cat_entry)

    main = _state(hass, cat_entry, ATTR_MAIN)
    assert main.state == "problem"
    assert main.attributes["issue"] == issue


async def test_main_sensor_ignores_last_time_when_not_configured(
    hass: HomeAssistant, dog_entry: MockConfigEntry
) -> None:
    """Without a last time sensor, the main sensor only checks the weight."""
    hass.states.async_set(WEIGHT_SENSOR, "10")
    await _setup(hass, dog_entry)

    main = _state(hass, dog_entry, ATTR_MAIN)
    assert main.state == "ok"
    assert "issue" not in main.attributes
