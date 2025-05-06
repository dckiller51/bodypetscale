"""Coordinator for the BodyPetScale integration."""

import logging
from datetime import datetime
from typing import Any, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.util.dt import parse_datetime

from .const import CONF_LAST_TIME_SENSOR, CONF_WEIGHT_SENSOR
from .util import calculate_ideal_weight, PetScaleConfig

_LOGGER = logging.getLogger(__name__)


async def _get_state_as_float(hass: HomeAssistant, entity_id: str) -> Optional[float]:
    """Get the state of a sensor as a float, return None if invalid."""
    state = hass.states.get(entity_id)
    if state is None or state.state in ["unavailable", "unknown"]:
        return None
    try:
        return float(state.state)
    except ValueError:
        _LOGGER.warning("Unable to convert state of %s to float", entity_id)
        return None


async def _get_state_as_string(hass: HomeAssistant, entity_id: str) -> Optional[str]:
    """Retrieve the state of an entity as a string."""
    state = hass.states.get(entity_id)
    if state is None or state.state in ["unavailable", "unknown"]:
        return None
    return state.state


class BodyPetScaleCoordinator(DataUpdateCoordinator):
    """Coordinator for the BodyPetScale integration."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: PetScaleConfig
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name="BodyPetScaleCoordinator",
        )
        self.config = config
        self._last_time: Optional[datetime] = None

    @property
    def last_time(self) -> Optional[datetime]:
        """Return the last time measurement."""
        return self._last_time

    async def _async_update_data(self) -> dict:
        """Fetch and calculate data for pet scale sensors."""
        weight = await _get_state_as_float(self.hass, self.config.weight_sensor)
        last_time = await _get_state_as_string(self.hass, self.config.last_time_sensor) if self.config.last_time_sensor else None
        tz = dt_util.DEFAULT_TIME_ZONE

        data: dict[str, Any] = {
            CONF_WEIGHT_SENSOR: weight,
        }

        if weight is not None:
            data["ideal_weight"] = calculate_ideal_weight(weight, self.config.morphology, self.config.animal_type)
            data["body_type"] = self.config.morphology
        else:
            data["ideal_weight"] = None
            data["body_type"] = None

        if last_time is not None:
            if isinstance(last_time, str):
                try:
                    dt = parse_datetime(last_time)
                    if dt:
                        self._last_time = dt.astimezone(tz)
                        data[CONF_LAST_TIME_SENSOR] = self._last_time
                    else:
                        _LOGGER.warning("Conversion error for 'last_time': %s", last_time)
                        data[CONF_LAST_TIME_SENSOR] = None
                except ValueError as e:
                    _LOGGER.warning("Invalid format for 'last_time': %s - %s", last_time, e)
                    data[CONF_LAST_TIME_SENSOR] = None
        else:
            data[CONF_LAST_TIME_SENSOR] = None

        return data
