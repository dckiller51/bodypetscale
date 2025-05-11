"""The BodyPetScale integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ACTIVITY,
    CONF_APPETITE,
    CONF_ANIMAL_TYPE,
    CONF_BIRTHDAY,
    CONF_BREED,
    CONF_LAST_TIME_SENSOR,
    CONF_LIVING_ENVIRONMENT,
    CONF_MORPHOLOGY,
    CONF_REPRODUCTIVE,
    CONF_TEMPERAMENT,
    CONF_WEIGHT_SENSOR,
    STARTUP_MESSAGE,
)
from .coordinator import BodyPetScaleCoordinator
from .util import get_config_option, PetScaleConfig

PLATFORMS = [Platform.SENSOR]
_LOGGER = logging.getLogger(__name__)


def build_pet_config(entry: ConfigEntry) -> PetScaleConfig:
    """Build and return a PetScaleConfig from the config entry."""
    return PetScaleConfig(
        weight_sensor=get_config_option(entry, CONF_WEIGHT_SENSOR),
        last_time_sensor=get_config_option(entry, CONF_LAST_TIME_SENSOR),
        activity=entry.data.get(CONF_ACTIVITY, ""),
        appetite=entry.data.get(CONF_APPETITE, ""),
        animal_type=entry.data.get(CONF_ANIMAL_TYPE, ""),
        birthday=entry.data.get(CONF_BIRTHDAY, ""),
        breed=entry.data.get(CONF_BREED, ""),
        environment=entry.options.get(CONF_LIVING_ENVIRONMENT, ""),
        morphology=entry.options.get(CONF_MORPHOLOGY, ""),
        name=entry.data.get(CONF_NAME, ""),
        reproductive=entry.data.get(CONF_REPRODUCTIVE, ""),
        temperament=entry.data.get(CONF_TEMPERAMENT, ""),
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BodyPetScale from a config entry."""
    _LOGGER.info(STARTUP_MESSAGE)
    _LOGGER.debug("Loaded entry data: %s", entry.data)
    _LOGGER.debug("Loaded entry options: %s", entry.options)

    if not get_config_option(entry, CONF_WEIGHT_SENSOR):
        _LOGGER.error("Missing weight sensor entity in config entry")
        return False

    config = build_pet_config(entry)
    coordinator = BodyPetScaleCoordinator(hass, config)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(entry.domain, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[entry.domain].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
