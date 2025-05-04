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

PLATFORMS = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BodyPetScale from a config entry."""
    _LOGGER.info(STARTUP_MESSAGE)

    _LOGGER.debug("Loaded entry data: %s", entry.data)
    _LOGGER.debug("Loaded entry options: %s", entry.options)

    weight_sensor = entry.options.get(CONF_WEIGHT_SENSOR)
    if not weight_sensor:
        _LOGGER.error("Missing weight sensor entity in config entry")
        return False
    last_time_sensor_entity = entry.data.get(CONF_LAST_TIME_SENSOR)  # optionnel

    data = {
        "name": entry.data.get(CONF_NAME),
        "animal_type": entry.data.get(CONF_ANIMAL_TYPE),
    }

    coordinator = BodyPetScaleCoordinator(
        hass,
        data,
        weight_sensor_entity=weight_sensor,
        last_time_sensor_entity=last_time_sensor_entity,
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(entry.domain, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[entry.domain].pop(entry.entry_id)
    return unload


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
