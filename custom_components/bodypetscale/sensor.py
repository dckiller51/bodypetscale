"""Sensor platform for BodyPetScale."""

import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
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
    ATTR_IDEAL,
    ATTR_MAIN,
    CONF_ANIMAL_TYPE,
    CONF_LAST_TIME_SENSOR,
    CONF_MORPHOLOGY,
    CONF_WEIGHT_SENSOR,
    DOMAIN,
)
from .util import calculate_ideal_weight, get_config_option

_LOGGER = logging.getLogger(__name__)


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
        self._animal_type = get_config_option(config_entry, CONF_ANIMAL_TYPE, "unknown")
        self._morphology = config_entry.options.get(CONF_MORPHOLOGY, "default_value")
        self._weight_sensor = config_entry.options.get(CONF_WEIGHT_SENSOR)

        if not self._weight_sensor:
            _LOGGER.error("The weight sensor is missing in the configuration")
            return

        pet_name = config_entry.data.get(CONF_NAME)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"BodyPetScale {(pet_name)}",
            manufacturer="BodyPetScale",
        )


class IdealWeightSensor(BasePetSensor):
    """Sensor that calculates the ideal weight based on morphology and animal type."""

    def __init__(self, coordinator: DataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the IdealWeightSensor with a coordinator and configuration entry."""
        description = SensorEntityDescription(
            key=ATTR_IDEAL,
            name="Ideal Weight",
            translation_key="ideal_weight",
            icon="mdi:scale-bathroom",
            native_unit_of_measurement=UnitOfMass.KILOGRAMS,
            state_class=SensorStateClass.MEASUREMENT,
        )
        super().__init__(coordinator, config_entry, description)

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        weight = self.coordinator.data.get("weight")
        return calculate_ideal_weight(weight, self._morphology, self._animal_type)


class BodyTypeSensor(BasePetSensor):
    """Sensor that returns the body type based on morphology."""

    def __init__(self, coordinator: DataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the BodyTypeSensor."""
        description = SensorEntityDescription(
            key=ATTR_BODY_TYPE,
            name="Body Type",
            translation_key="body_type",
            icon="mdi:weight",
        )
        super().__init__(coordinator, config_entry, description)

    @property
    def native_value(self) -> str:
        """Return the body type based on morphology."""
        return self._morphology or "unknown"


class MainSensor(BasePetSensor):
    """Main sensor that represents the global pet status."""

    def __init__(self, coordinator: DataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the MainSensor."""
        description = SensorEntityDescription(
            key=ATTR_MAIN,
            name="Main",
            translation_key="main",
        )
        super().__init__(coordinator, config_entry, description)
        self._animal_type = config_entry.data.get(CONF_ANIMAL_TYPE)
        self._last_time_sensor = config_entry.data.get(CONF_LAST_TIME_SENSOR)
        self._attributes = {
            "animal_type": self._animal_type,
            "body_type": self._morphology,
        }

    @property
    def native_value(self) -> str:
        """Return OK or PROBLEM based on weight value."""
        current_weight = self.coordinator.data.get("weight")
        self._attributes["weight"] = current_weight

        if not isinstance(current_weight, (int, float, str)) or current_weight in [None, "unknown", "unavailable"]:
            self._attributes["issue"] = "weight_unavailable"
            return "problem"

        try:
            weight = float(current_weight)
        except (ValueError, TypeError):
            self._attributes["issue"] = "weight_unavailable"
            return "problem"

        self._attributes["ideal_weight"] = calculate_ideal_weight(
            weight, self._morphology, self._animal_type
        )

        if self._last_time_sensor:
            self._attributes["last_measurement_time"] = self.coordinator.data.get(
                self._last_time_sensor
            )

        if weight == 0:
            self._attributes["issue"] = "weight_low"
            return "problem"
        if weight >= 100:
            self._attributes["issue"] = "weight_high"
            return "problem"

        self._attributes.pop("issue", None)
        return "ok"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        return self._attributes

    @property
    def icon(self) -> str:
        """Return an icon depending on the selected animal type (dog, cat, or default scale)."""
        if self._animal_type == "dog":
            return "mdi:dog"
        if self._animal_type == "cat":
            return "mdi:cat"
        return "mdi:scale"


async def _async_update_data(
    hass: HomeAssistant,
    weight_sensor: str,
    last_time_sensor: str | None = None
) -> dict[str, float | None]:
    """Logic to fetch new data from sensors."""
    data: dict[str, float | None] = {}

    weight_state = hass.states.get(weight_sensor)
    _LOGGER.debug("Weight sensor state (%s): %s", weight_sensor, weight_state)

    if weight_state and weight_state.state not in ["unavailable", "unknown"]:
        try:
            data["weight"] = float(weight_state.state)
        except ValueError:
            _LOGGER.warning(
                "Unable to convert the weight sensor state (%s) to a number: %s",
                weight_sensor,
                weight_state.state,
            )
            data["weight"] = None
    else:
        data["weight"] = None

    if last_time_sensor:
        last_time_state = hass.states.get(last_time_sensor)
        if last_time_state and last_time_state.state not in ["unavailable", "unknown"]:
            try:
                data[last_time_sensor] = float(last_time_state.state)
            except ValueError:
                data[last_time_sensor] = None
        else:
            data[last_time_sensor] = None

    return data


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Configure the sensor platform for BodyPetScale."""
    # Extract configuration information
    weight_sensor = entry.options.get(CONF_WEIGHT_SENSOR)
    last_time_sensor = entry.data.get(
        CONF_LAST_TIME_SENSOR
    )  # Retrieve the optional sensor
    if not weight_sensor:
        _LOGGER.error("Le capteur de poids est manquant dans l'entrée de configuration")
        return

    # Create a coordinator for data updates
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="BodyPetScale Coordinator",
        update_method=lambda: _async_update_data(hass, weight_sensor, last_time_sensor),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except (ValueError, RuntimeError) as err:
        _LOGGER.error("Error during the initial data fetch: %s", err)
        return  # Do not proceed if the initial fetch fails

    main_sensor = MainSensor(coordinator, entry)
    ideal_weight_sensor = IdealWeightSensor(coordinator, entry)
    body_type_sensor = BodyTypeSensor(coordinator, entry)

    # Add the sensors to the platform
    async_add_entities(
        [
            main_sensor,
            ideal_weight_sensor,
            body_type_sensor,
        ]
    )

    # Add a listener to update when the weight sensor or last update sensor changes
    listeners = [weight_sensor]
    if last_time_sensor:
        listeners.append(last_time_sensor)

    async def async_state_changed_listener(event: Event[EventStateChangedData]) -> None:
        """Update when the state of monitored sensors changes."""
        if event.data["entity_id"] in listeners:
            _LOGGER.info(
                "Monitored sensor %s changed, updating",
                event.data["entity_id"],
            )
            await coordinator.async_refresh()

    async_track_state_change_event(hass, listeners, async_state_changed_listener)
