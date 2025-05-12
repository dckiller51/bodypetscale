"""Coordinator for the BodyPetScale integration."""

import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.util.dt import parse_datetime

from .const import CONF_LAST_TIME_SENSOR, CONF_WEIGHT_SENSOR
from .util import (
    EnergyConfig,
    PetScaleConfig,
    calculate_energy_need,
    calculate_ideal_weight,
    get_cat_age_stage,
    get_dog_age_stage,
)

_LOGGER = logging.getLogger(__name__)


async def _get_state_as_float(hass: HomeAssistant, entity_id: str) -> float | None:
    """Get the state of a sensor as a float, return None if invalid."""
    state = hass.states.get(entity_id)
    if state is None or state.state in ["unavailable", "unknown"]:
        return None
    try:
        return float(state.state)
    except ValueError:
        _LOGGER.warning("Unable to convert state of %s to float", entity_id)
        return None


async def _get_state_as_string(hass: HomeAssistant, entity_id: str) -> str | None:
    """Retrieve the state of an entity as a string."""
    state = hass.states.get(entity_id)
    if state is None or state.state in ["unavailable", "unknown"]:
        return None
    return state.state


class BodyPetScaleCoordinator(DataUpdateCoordinator):
    """Coordinator for the BodyPetScale integration."""

    def __init__(self, hass: HomeAssistant, config: PetScaleConfig) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name="BodyPetScaleCoordinator",
        )
        self.config = config
        self._last_time: datetime | None = None

    @property
    def last_time(self) -> datetime | None:
        """Return the last time measurement."""
        return self._last_time

    async def _async_update_data(self) -> dict:
        """Fetch and calculate data for pet scale sensors."""
        weight = await _get_state_as_float(self.hass, self.config.weight_sensor)
        last_time = (
            await _get_state_as_string(self.hass, self.config.last_time_sensor)
            if self.config.last_time_sensor
            else None
        )

        data: dict[str, Any] = {
            CONF_WEIGHT_SENSOR: weight,
        }

        self._process_weight_data(weight, data)
        self._process_last_time_data(last_time, data)

        if weight is not None and data.get("ideal_weight") is not None:
            self._process_energy_need(weight, data)

        return data

    def _process_weight_data(self, weight: float | None, data: dict[str, Any]) -> None:
        if weight is not None:
            data["ideal_weight"] = calculate_ideal_weight(
                weight, self.config.morphology, self.config.animal_type
            )
            data["body_type"] = self.config.morphology
        else:
            data["ideal_weight"] = None
            data["body_type"] = None

    def _process_last_time_data(
        self, last_time_str: str | None, data: dict[str, Any]
    ) -> None:
        if not last_time_str:
            data[CONF_LAST_TIME_SENSOR] = None
            return

        try:
            dt = parse_datetime(last_time_str)
            if dt:
                self._last_time = dt.astimezone(dt_util.DEFAULT_TIME_ZONE)
                data[CONF_LAST_TIME_SENSOR] = self._last_time
            else:
                _LOGGER.warning("Conversion error for 'last_time': %s", last_time_str)
                data[CONF_LAST_TIME_SENSOR] = None
        except ValueError as e:
            _LOGGER.warning("Invalid format for 'last_time': %s - %s", last_time_str, e)
            data[CONF_LAST_TIME_SENSOR] = None

    def _process_energy_need(self, weight: float, data: dict[str, Any]) -> None:
        if self.config.animal_type == "cat":
            life_stage = get_cat_age_stage(self.config.birthday)
        elif self.config.animal_type == "dog":
            life_stage = get_dog_age_stage(self.config.birthday, weight)
        else:
            _LOGGER.warning("Unknown animal type: %s", self.config.animal_type)
            return

        if not life_stage:
            _LOGGER.warning(
                "Invalid life_stage for %s, cannot calculate energy need.",
                self.config.animal_type,
            )
            return

        ideal_weight = data.get("ideal_weight")
        if ideal_weight is None:
            _LOGGER.warning("Ideal weight is None, cannot calculate energy need.")
            return

        config = EnergyConfig(
            animal_type=self.config.animal_type,
            breed=self.config.breed,
            life_stage=life_stage,
            activity=self.config.activity,
            reproductive=self.config.reproductive,
            morphology=self.config.morphology,
            environment=self.config.environment,
            appetite=self.config.appetite,
            temperament=self.config.temperament,
        )

        energy_need = calculate_energy_need(config, ideal_weight)

        data["energy_need"] = energy_need
