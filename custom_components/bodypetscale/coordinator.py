"""Coordinator for the BodyPetScale integration."""

import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.util.dt import parse_datetime

from .const import ATTR_WEIGHING_MODE, CONF_LAST_TIME_SENSOR, CONF_WEIGHT_SENSOR
from .util import (
    EnergyConfig,
    PetScaleConfig,
    calculate_energy_need,
    calculate_ideal_weight,
    get_cat_age_stage,
    get_dog_age_stage,
)

_LOGGER = logging.getLogger(__name__)


async def _get_state_as_string(hass: HomeAssistant, entity_id: str) -> str | None:
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
        config: PetScaleConfig,
        store: Store[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name="BodyPetScaleCoordinator",
        )
        self.config = config
        self._store = store
        self._last_time: datetime | None = None
        # Weight accepted for this pet (net of the holder weight if carried)
        self.weight: float | None = None
        self.measured_at: datetime | None = None
        self.weighing_mode: str | None = None

    @property
    def last_time(self) -> datetime | None:
        """Return the last time measurement."""
        return self._last_time

    async def async_load(self) -> None:
        """Restore the last accepted measurement."""
        if self._store is None or (stored := await self._store.async_load()) is None:
            return
        weight = stored.get("weight")
        self.weight = float(weight) if weight is not None else None
        measured_at = stored.get("measured_at")
        self.measured_at = parse_datetime(measured_at) if measured_at else None
        self.weighing_mode = stored.get("weighing_mode")

    def set_weight(
        self, weight: float | None, *, stamp: bool, mode: str | None = None
    ) -> None:
        """Set the accepted weight without refreshing the sensors."""
        self.weight = weight
        if stamp:
            self.measured_at = dt_util.utcnow()
            self.weighing_mode = mode

    async def async_set_weight(
        self, weight: float | None, *, stamp: bool, mode: str | None = None
    ) -> None:
        """Set the accepted weight, persist it and refresh the sensors."""
        self.set_weight(weight, stamp=stamp, mode=mode)
        if self._store is not None:
            await self._store.async_save(
                {
                    "weight": self.weight,
                    "measured_at": self.measured_at.isoformat()
                    if self.measured_at
                    else None,
                    "weighing_mode": self.weighing_mode,
                }
            )
        await self.async_refresh()

    async def _async_update_data(self) -> dict:
        """Calculate data for pet scale sensors."""
        weight = self.weight

        data: dict[str, Any] = {
            CONF_WEIGHT_SENSOR: weight,
            ATTR_WEIGHING_MODE: self.weighing_mode,
        }

        self._process_weight_data(weight, data)
        if self.config.last_time_sensor:
            self._process_last_time_data(
                await _get_state_as_string(self.hass, self.config.last_time_sensor),
                data,
            )
        else:
            self._last_time = (
                self.measured_at.astimezone(dt_util.DEFAULT_TIME_ZONE)
                if self.measured_at
                else None
            )
            data[CONF_LAST_TIME_SENSOR] = self._last_time

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
