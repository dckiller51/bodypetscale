"""Config flow for BodyPetScale."""

from __future__ import annotations

import logging
from types import MappingProxyType
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_NAME
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


def get_options_schema(
    defaults: dict[str, Any] | MappingProxyType[str, Any],
) -> vol.Schema:
    """Return the options schema."""

    schema: dict[vol.Optional | vol.Required, Any] = {}

    schema[vol.Required(CONF_MORPHOLOGY)] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=MORPHOLOGY_OPTIONS,
            mode=selector.SelectSelectorMode.DROPDOWN,
            translation_key="morphology",
        )
    )

    weight_suggest = defaults.get(CONF_WEIGHT_SENSOR)
    schema[vol.Required(
        CONF_WEIGHT_SENSOR,
        description={"suggested_value": weight_suggest} if weight_suggest else None
    )] = selector.EntitySelector(
        selector.EntitySelectorConfig(domain=["sensor", "input_number", "number"])
    )

    last_time_suggest = defaults.get(CONF_LAST_TIME_SENSOR)
    schema[vol.Optional(
        CONF_LAST_TIME_SENSOR,
        description={"suggested_value": last_time_suggest} if last_time_suggest else None
    )] = selector.EntitySelector(
        selector.EntitySelectorConfig(domain=["sensor", "input_datetime"])
    )

    return vol.Schema(schema)


class BodyPetScaleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BodyPetScale."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.data: dict[str, Any] = {}

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> BodyPetScaleOptionsFlow:
        """Get the options flow for this handler."""
        return BodyPetScaleOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            existing_entries = self._async_current_entries()
            for entry in existing_entries:
                if entry.data.get(CONF_NAME, "").strip().lower() == user_input[CONF_NAME].strip().lower():
                    errors[CONF_NAME] = "name_exists"
                    break

            if not errors:
                self.data = user_input
                await self.async_set_unique_id(user_input[CONF_NAME].strip().lower())
                return await self.async_step_options()

        user_schema = vol.Schema(
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
        )

        return self.async_show_form(
            step_id="user",
            data_schema=user_schema,
            errors=errors,
        )

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the options step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            weight_sensor_id = user_input.get(CONF_WEIGHT_SENSOR)
            if not weight_sensor_id or not self.hass.states.get(weight_sensor_id):
                return self.async_show_form(
                    step_id="options",
                    data_schema=await self.hass.async_add_executor_job(
                        get_options_schema, self.data
                    ),
                    errors={CONF_WEIGHT_SENSOR: "invalid_weight_sensor"},
                )

            return self.async_create_entry(
                title=self.data[CONF_NAME],
                data=self.data,
                options=user_input,
            )

        options_schema = await self.hass.async_add_executor_job(
            get_options_schema, self.data
        )

        return self.async_show_form(
            step_id="options",
            data_schema=options_schema,
            errors=errors,
        )


class BodyPetScaleOptionsFlow(OptionsFlow):
    """Handle BodyPetScale options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage BodyPetScale options."""
        if user_input is not None:
            _LOGGER.info("Updating BodyPetScale options: %s", user_input)
            return self.async_create_entry(data=user_input)

        options_schema = await self.hass.async_add_executor_job(
            get_options_schema, self.config_entry.options
        )

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                options_schema, self.config_entry.options
            ),
            description_placeholders={
                CONF_NAME: self.config_entry.data.get(CONF_NAME, "pet")
            },
        )
