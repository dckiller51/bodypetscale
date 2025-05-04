"""Coordinator for the BodyPetScale integration."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class BodyPetScaleCoordinator(DataUpdateCoordinator):
    """Coordinator for the BodyPetScale integration."""

    def __init__(
        self,
        hass: HomeAssistant,
        data: dict,
        weight_sensor_entity=None,
        last_time_sensor_entity=None,
    ) -> None:
        """Initialize the coordinator with fixed data."""
        super().__init__(
            hass,
            logger=logging.getLogger(DOMAIN),
            name="BodyPetScaleCoordinator",
        )
        self.data = data
        self.weight_sensor_entity = weight_sensor_entity
        self.last_time_sensor_entity = last_time_sensor_entity

    async def _async_update_data(self) -> dict:
        """Update the data from sensors."""
        return self.data
