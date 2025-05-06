"""The BodyPetScale integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ANIMAL_TYPE,
    CONF_LAST_TIME_SENSOR,
    CONF_WEIGHT_SENSOR,
    STARTUP_MESSAGE,
)
from .coordinator import BodyPetScaleCoordinator
from .util import get_config_option, PetScaleConfig

PLATFORMS = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BodyPetScale from a config entry."""
    _LOGGER.info(STARTUP_MESSAGE)

    _LOGGER.debug("Loaded entry data: %s", entry.data)
    _LOGGER.debug("Loaded entry options: %s", entry.options)

    weight_sensor_entity = get_config_option(entry, CONF_WEIGHT_SENSOR)
    if not weight_sensor_entity:
        _LOGGER.error("Missing weight sensor entity in config entry")
        return False

    last_time_entity = get_config_option(entry, CONF_LAST_TIME_SENSOR)  # Optionnel
    animal_type = entry.data.get(CONF_ANIMAL_TYPE, "")
    morphology = entry.options.get("morphology", "")
    name = entry.data.get(CONF_NAME, "")

    config = PetScaleConfig(
        weight_sensor=weight_sensor_entity,
        last_time_sensor=last_time_entity,
        animal_type=animal_type,
        morphology=morphology,
        name=name,
    )

    coordinator = BodyPetScaleCoordinator(hass, config)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(entry.domain, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok: bool = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[entry.domain].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
