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
    ACTIVITY_LEVELS,
    ANIMAL_TYPES,
    BREED_OPTIONS,
    CAT_TEMPERAMENT_OPTIONS,
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
    DOG_APPETITE_OPTIONS,
    DOMAIN,
    LIVING_ENVIRONMENT_OPTIONS,
    MORPHOLOGY_OPTIONS,
    REPRODUCTIVE_STATUS,
)

_LOGGER = logging.getLogger(__name__)


def get_options_schema(
    defaults: dict[str, Any] | MappingProxyType[str, Any],
    animal_type: str,
) -> vol.Schema:
    """Return the options schema."""

    schema: dict[vol.Optional | vol.Required, Any] = {}

    living_environment_options = LIVING_ENVIRONMENT_OPTIONS.get(animal_type, [])
    schema[vol.Required(CONF_LIVING_ENVIRONMENT)] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=living_environment_options,
            mode=selector.SelectSelectorMode.DROPDOWN,
            translation_key="living_environment",
            sort=True,
        )
    )

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
        """Handle the initial step (name and animal type)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            existing_entries = self._async_current_entries()
            for entry in existing_entries:
                if entry.data.get(CONF_NAME) == user_input[CONF_NAME].strip().lower():
                    errors[CONF_NAME] = "name_exists"
                    break

            if not errors:
                self.data.update(user_input)
                return await self.async_step_profile()

        user_schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_ANIMAL_TYPE): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=ANIMAL_TYPES,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key="animal_type",
                        sort=True,
                    )
                ),
                vol.Required(CONF_BIRTHDAY): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.DATE,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=user_schema,
            errors=errors,
        )

    async def async_step_profile(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle profile selection based on animal type."""
        errors: dict[str, str] = {}

        animal_type: str = self.data[CONF_ANIMAL_TYPE]
        activity_options = ACTIVITY_LEVELS.get(animal_type, [])
        breed_options = BREED_OPTIONS.get(animal_type, [])

        profile_schema_dict = {
            vol.Required(CONF_BREED): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=breed_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="breed_options",
                    sort=True,
                )
            ),
            vol.Required(CONF_ACTIVITY): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=activity_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="activity_level",
                    sort=True,
                )
            ),
            vol.Required(CONF_REPRODUCTIVE): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=REPRODUCTIVE_STATUS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="reproductive_status",
                )
            ),
        }

        if animal_type == "cat":
            profile_schema_dict[vol.Required(CONF_TEMPERAMENT)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=CAT_TEMPERAMENT_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="temperament",
                )
            )
        elif animal_type == "dog":
            profile_schema_dict[vol.Required(CONF_APPETITE)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=DOG_APPETITE_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="appetite",
                )
            )

        if user_input is not None:
            self.data.update(user_input)
            await self.async_set_unique_id(self.data[CONF_NAME].strip().lower())
            return await self.async_step_options()

        return self.async_show_form(
            step_id="profile",
            data_schema=vol.Schema(profile_schema_dict),
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
                animal_type = self.data[CONF_ANIMAL_TYPE]
                return self.async_show_form(
                    step_id="options",
                    data_schema=await self.hass.async_add_executor_job(
                        get_options_schema, self.data, animal_type
                    ),
                    errors={CONF_WEIGHT_SENSOR: "invalid_weight_sensor"},
                )

            return self.async_create_entry(
                title=self.data[CONF_NAME],
                data=self.data,
                options=user_input,
            )

        animal_type = self.data[CONF_ANIMAL_TYPE]
        options_schema = await self.hass.async_add_executor_job(
            get_options_schema, self.data, animal_type
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

        animal_type = self.hass.data[DOMAIN][self.config_entry.entry_id].config.animal_type

        options_schema = await self.hass.async_add_executor_job(
            get_options_schema, self.config_entry.options, animal_type
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
