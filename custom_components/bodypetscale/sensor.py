"""Sensor platform for BodyPetScale."""

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, UnitOfMass
from homeassistant.core import Event, EventStateChangedData, HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    ATTR_BODY_TYPE,
    ATTR_ENERGY_NEED,
    ATTR_IDEAL,
    ATTR_MAIN,
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
    VERSION,
)
from .coordinator import BodyPetScaleCoordinator
from .util import get_config_option

_LOGGER = logging.getLogger(__name__)

SENSORS = [
    SensorEntityDescription(
        key=CONF_WEIGHT_SENSOR,
        translation_key="weight",
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_IDEAL,
        name="Ideal Weight",
        translation_key="ideal_weight",
        icon="mdi:scale-bathroom",
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_BODY_TYPE,
        name="Body Type",
        translation_key="body_type",
        icon="mdi:weight",
    ),
    SensorEntityDescription(
        key=ATTR_ENERGY_NEED,
        name="Energy need",
        translation_key="energy_need",
        icon="mdi:food-croissant",
        native_unit_of_measurement="kcal",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=CONF_LAST_TIME_SENSOR,
        translation_key="last_measurement_time",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
]


class BasePetSensor(CoordinatorEntity, SensorEntity):
    """Base class for BodyPetScale sensors."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize a BodyPetScale base sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"
        self._activity = get_config_option(config_entry, CONF_ACTIVITY)
        self._appetite = get_config_option(config_entry, CONF_APPETITE)
        self._animal_type = get_config_option(config_entry, CONF_ANIMAL_TYPE)
        self._birthday = get_config_option(config_entry, CONF_BIRTHDAY)
        self._breed = get_config_option(config_entry, CONF_BREED)
        self._last_time_sensor = config_entry.options.get(CONF_LAST_TIME_SENSOR)
        self._living_environment = get_config_option(
            config_entry, CONF_LIVING_ENVIRONMENT
        )
        self._morphology = config_entry.options.get(CONF_MORPHOLOGY)
        self._reproductive = get_config_option(config_entry, CONF_REPRODUCTIVE)
        self._temperament = get_config_option(config_entry, CONF_TEMPERAMENT)
        self._weight_sensor = config_entry.options.get(CONF_WEIGHT_SENSOR)

        if not self._weight_sensor:
            _LOGGER.error("The weight sensor is missing in the configuration")
            return

        pet_name = config_entry.data.get(CONF_NAME)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"BodyPetScale {(pet_name)}",
            sw_version=VERSION,
            manufacturer="BodyPetScale",
        )

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor.

        This method retrieves the current value of the sensor from the coordinator's data.
        The value is logged for debugging purposes.

        Returns:
            The current value of the sensor, or None if the value is not available.
        """
        value = self.coordinator.data.get(self.entity_description.key)
        _LOGGER.debug("Sensor %s has value: %s", self.entity_description.key, value)
        return value


class PetMetricSensor(BasePetSensor):
    """Generic sensor for pet metrics (weight, ideal, body type, last measurement)."""


class MainSensor(BasePetSensor):
    """Main sensor that represents the global pet status."""

    def __init__(
        self, coordinator: BodyPetScaleCoordinator, config_entry: ConfigEntry
    ) -> None:
        """Initialize the MainSensor."""
        description = SensorEntityDescription(
            key=ATTR_MAIN,
            name="Main",
            translation_key="main",
        )
        super().__init__(coordinator, config_entry, description)
        self._animal_type = config_entry.data.get(CONF_ANIMAL_TYPE)
        self.coordinator: BodyPetScaleCoordinator = coordinator
        self._morphology = config_entry.data.get(CONF_MORPHOLOGY)
        self._last_time_sensor = config_entry.data.get(CONF_LAST_TIME_SENSOR)
        self._issue: str | None = None
        self._last_time: datetime | None = None

    @property
    def native_value(self) -> str:
        """Return OK or PROBLEM based on weight and last_time validity."""
        self._issue = None
        self._last_time = None
        result = "ok"

        current_weight = self.coordinator.data.get(CONF_WEIGHT_SENSOR)

        if not isinstance(current_weight, (int, float)) or current_weight is None:
            self._issue = "weight_unavailable"
            result = "problem"
        else:
            try:
                weight = float(current_weight)
                if weight == 0:
                    self._issue = "weight_low"
                    result = "problem"
                elif weight >= 100:
                    self._issue = "weight_high"
                    result = "problem"
            except (ValueError, TypeError):
                self._issue = "weight_unavailable"
                result = "problem"

        if self._last_time_sensor:
            last_time = self.coordinator.data.get(CONF_LAST_TIME_SENSOR)

            if not isinstance(last_time, datetime):
                if isinstance(last_time, str):
                    self._issue = "last_time_invalid_format"
                    result = "problem"
                else:
                    self._issue = "last_time_unavailable"
                    result = "problem"
            else:
                self._last_time = last_time

        return result

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        _LOGGER.debug(
            "MainSensor last_measurement_time: %s", self.coordinator.last_time
        )
        attrs = {
            "animal_type": self._animal_type,
            "body_type": self.coordinator.data.get("body_type"),
            "ideal_weight": self.coordinator.data.get("ideal_weight"),
            "weight": self.coordinator.data.get(CONF_WEIGHT_SENSOR),
        }

        if self._issue:
            attrs["issue"] = self._issue
        if self.coordinator.last_time:
            attrs["last_measurement_time"] = self.coordinator.last_time

        return attrs

    @property
    def icon(self) -> str:
        """Return an icon depending on the selected animal type (dog, cat, or default scale)."""
        if self._animal_type == "dog":
            return "mdi:dog"
        if self._animal_type == "cat":
            return "mdi:cat"
        return "mdi:scale"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Configure the sensor platform for BodyPetScale."""
    weight_sensor = entry.options.get(CONF_WEIGHT_SENSOR)
    last_time_sensor = entry.options.get(CONF_LAST_TIME_SENSOR)

    if not weight_sensor:
        _LOGGER.error("The weight sensor is missing in the configuration entry")
        return

    coordinator: BodyPetScaleCoordinator = hass.data[DOMAIN][entry.entry_id]

    try:
        await coordinator.async_config_entry_first_refresh()
    except (ValueError, RuntimeError) as err:
        _LOGGER.error("Error during the initial data fetch: %s", err)
        return  # Do not proceed if the initial fetch fails

    main_sensor = MainSensor(coordinator, entry)

    metric_keys = [CONF_WEIGHT_SENSOR, ATTR_IDEAL, ATTR_BODY_TYPE, ATTR_ENERGY_NEED]

    if last_time_sensor:
        metric_keys.append(CONF_LAST_TIME_SENSOR)

    metric_sensors = [desc for desc in SENSORS if desc.key in metric_keys]

    sensor_entities = [
        PetMetricSensor(coordinator, entry, desc) for desc in metric_sensors
    ]

    entities = [main_sensor] + sensor_entities

    async_add_entities(entities)

    # Add a listener to update when the weight sensor or last update sensor changes
    listeners = [weight_sensor]
    if last_time_sensor:
        listeners.append(last_time_sensor)

    async def async_state_changed_listener(event: Event[EventStateChangedData]) -> None:
        """Update when the state of monitored sensors changes."""
        entity_id = event.data["entity_id"]

        if entity_id in listeners:
            _LOGGER.info(
                "Monitored sensor %s changed, updating",
                entity_id,
            )
            await coordinator.async_refresh()

    for entity_id in listeners:
        async_track_state_change_event(hass, entity_id, async_state_changed_listener)
