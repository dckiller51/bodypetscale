"""The BodyPetScale integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
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
    HANDLERS,
    STARTUP_MESSAGE,
    STORAGE_VERSION,
)
from .coordinator import BodyPetScaleCoordinator
from .profile import PetScaleHandler
from .util import PetScaleConfig, get_config_option

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


def _store(hass: HomeAssistant, entry: ConfigEntry) -> Store:
    """Return the storage of the last accepted measurement of a pet."""
    return Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BodyPetScale from a config entry."""
    _LOGGER.info(STARTUP_MESSAGE)
    _LOGGER.debug("Loaded entry data: %s", entry.data)
    _LOGGER.debug("Loaded entry options: %s", entry.options)

    if not get_config_option(entry, CONF_WEIGHT_SENSOR):
        _LOGGER.error("Missing weight sensor entity in config entry")
        return False

    config = build_pet_config(entry)
    coordinator = BodyPetScaleCoordinator(hass, config, _store(hass, entry))
    await coordinator.async_load()

    domain_data = hass.data.setdefault(DOMAIN, {})
    handlers: dict[str, PetScaleHandler] = domain_data.setdefault(HANDLERS, {})
    handler = PetScaleHandler(hass, entry, coordinator, handlers)
    handlers[entry.entry_id] = handler
    handler.async_start()

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        handlers.pop(entry.entry_id).unload()
        raise

    domain_data[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        domain_data = hass.data.get(DOMAIN, {})
        domain_data.pop(entry.entry_id, None)
        handler: PetScaleHandler | None = domain_data.get(HANDLERS, {}).pop(
            entry.entry_id, None
        )
        if handler is not None:
            handler.unload()
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove the stored measurement when a pet is deleted."""
    await _store(hass, entry).async_remove()


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
