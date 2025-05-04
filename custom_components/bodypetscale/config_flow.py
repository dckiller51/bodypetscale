"""Config flow for BodyPetScale."""

from __future__ import annotations

import logging
from types import MappingProxyType
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    ANIMAL_TYPES,
    CONF_ANIMAL_TYPE,
    CONF_LAST_TIME_SENSOR,
    CONF_MORPHOLOGY,
    CONF_WEIGHT_SENSOR,
    DOMAIN,
    MORPHOLOGY_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)


@callback  # type: ignore[misc]
def get_options_schema(
    defaults: dict[str, Any] | MappingProxyType[str, Any],
) -> vol.Schema:
    """Return options schema."""
    _LOGGER.debug("Generating options schema with defaults: %s", defaults)
    return vol.Schema(
        {
            vol.Required(CONF_MORPHOLOGY): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=MORPHOLOGY_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="morphology",
                )
            ),
            vol.Required(
                CONF_WEIGHT_SENSOR,
                description=(
                    {"suggested_value": defaults.get(CONF_WEIGHT_SENSOR)}
                    if CONF_WEIGHT_SENSOR in defaults
                    else None
                ),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["sensor", "input_number", "number"]
                )
            ),
            vol.Optional(
                CONF_LAST_TIME_SENSOR,
                description=(
                    {"suggested_value": defaults.get(CONF_LAST_TIME_SENSOR)}
                    if CONF_LAST_TIME_SENSOR in defaults
                    else None
                ),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["sensor", "input_datetime"]
                )
            ),
        }
    )


class BodyPetScaleConfigFlow(ConfigFlow, domain=DOMAIN):  # type: ignore[misc, call-arg]
    """Config flow for BodyPetScale."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    @staticmethod
    @callback  # type: ignore[misc]
    def async_get_options_flow(config_entry: ConfigEntry) -> BodyPetScaleOptionsFlow:
        return BodyPetScaleOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            _LOGGER.debug("Step 'user' input: %s", user_input)
            self._data = user_input
            return await self.async_step_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Required(CONF_ANIMAL_TYPE): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=ANIMAL_TYPES,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            translation_key="animal_type",
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle options step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            _LOGGER.debug("Step 'options' input: %s", user_input)

            # Validation : weight sensor must exist
            weight_sensor_id = user_input.get(CONF_WEIGHT_SENSOR)
            if not weight_sensor_id or not self.hass.states.get(weight_sensor_id):
                _LOGGER.warning(
                    "Invalid or missing weight sensor: %s", weight_sensor_id
                )
                errors[CONF_WEIGHT_SENSOR] = "invalid_weight_sensor"
                return self.async_show_form(
                    step_id="options",
                    data_schema=get_options_schema(self._data),
                    errors=errors,
                )

            _LOGGER.info(
                "Creating config entry: data=%s, options=%s", self._data, user_input
            )
            return self.async_create_entry(
                title=self._data[CONF_NAME],
                data=self._data,
                options=user_input,
            )

        return self.async_show_form(
            step_id="options",
            data_schema=get_options_schema(self._data),
            errors=errors,
        )


class BodyPetScaleOptionsFlow(OptionsFlow):  # type: ignore[misc]
    """Options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle options."""
        if user_input is not None:
            _LOGGER.info("Updating config options: %s", user_input)
            return self.async_create_entry(
                title=self._entry.title,
                data=user_input,
            )

        return self.async_show_form(
            step_id="init",
            data_schema=get_options_schema(self._entry.options),
        )
