"""Tests for the bodypetscale integration setup."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bodypetscale import build_pet_config
from custom_components.bodypetscale.const import (
    CONF_MORPHOLOGY,
    CONF_WEIGHT_SENSOR,
    DOMAIN,
)
from custom_components.bodypetscale.coordinator import BodyPetScaleCoordinator

from .conftest import CAT_DATA, LAST_TIME_SENSOR, WEIGHT_SENSOR


def test_build_pet_config(cat_entry: MockConfigEntry) -> None:
    """The pet config merges data and options of the entry."""
    config = build_pet_config(cat_entry)
    assert config.name == "Felix"
    assert config.animal_type == "cat"
    assert config.birthday == CAT_DATA["birthday"]
    assert config.breed == "chartreux"
    assert config.temperament == "calm"
    assert config.appetite == ""
    assert config.environment == "indoors"
    assert config.morphology == "6_slightly_overweight"
    assert config.weight_sensor == WEIGHT_SENSOR
    assert config.last_time_sensor == LAST_TIME_SENSOR


async def test_setup_and_unload(
    hass: HomeAssistant, dog_entry: MockConfigEntry, freezer: Any
) -> None:
    """The entry sets up a coordinator and unloads cleanly."""
    freezer.move_to("2026-10-20 12:00:00+00:00")
    hass.states.async_set(WEIGHT_SENSOR, "10")
    dog_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(dog_entry.entry_id)
    await hass.async_block_till_done()

    assert dog_entry.state is ConfigEntryState.LOADED
    coordinator = hass.data[DOMAIN][dog_entry.entry_id]
    assert isinstance(coordinator, BodyPetScaleCoordinator)
    assert coordinator.data[CONF_WEIGHT_SENSOR] == 10.0

    assert await hass.config_entries.async_unload(dog_entry.entry_id)
    await hass.async_block_till_done()

    assert dog_entry.state is ConfigEntryState.NOT_LOADED
    assert dog_entry.entry_id not in hass.data[DOMAIN]


async def test_setup_without_weight_sensor(hass: HomeAssistant) -> None:
    """Setup fails when no weight sensor is configured."""
    entry = MockConfigEntry(domain=DOMAIN, title="Ghost", data={"name": "Ghost"})
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR


async def test_options_update_reloads_entry(
    hass: HomeAssistant, dog_entry: MockConfigEntry, freezer: Any
) -> None:
    """Changing the options reloads the entry with the new values."""
    freezer.move_to("2026-10-20 12:00:00+00:00")
    hass.states.async_set(WEIGHT_SENSOR, "10")
    dog_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(dog_entry.entry_id)
    await hass.async_block_till_done()

    old_coordinator = hass.data[DOMAIN][dog_entry.entry_id]
    assert old_coordinator.data["ideal_weight"] == 10.0

    hass.config_entries.async_update_entry(
        dog_entry, options={**dog_entry.options, CONF_MORPHOLOGY: "7_overweight"}
    )
    await hass.async_block_till_done()

    assert dog_entry.state is ConfigEntryState.LOADED
    new_coordinator = hass.data[DOMAIN][dog_entry.entry_id]
    assert new_coordinator is not old_coordinator
    assert new_coordinator.config.morphology == "7_overweight"
    assert new_coordinator.data["ideal_weight"] == 8.0
