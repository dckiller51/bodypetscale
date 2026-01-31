"""Config flow for BodyPetScale."""

from __future__ import annotations

import logging
from types import MappingProxyType
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    ACTIVITY_LEVELS,
    ANIMAL_TYPES,
    BREED_OPTIONS,
    CAT_TEMPERAMENT_OPTIONS,
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
    DOG_APPETITE_OPTIONS,
    DOMAIN,
    LIVING_ENVIRONMENT_OPTIONS,
    MORPHOLOGY_OPTIONS,
    MORPHOLOGY_URL,
    REPRODUCTIVE_STATUS,
)

_LOGGER = logging.getLogger(__name__)


def get_options_schema(
    defaults: dict[str, Any] | MappingProxyType[str, Any],
    animal_type: str,
) -> vol.Schema:
    """Return the options schema."""

    living_environment_options = LIVING_ENVIRONMENT_OPTIONS.get(animal_type, [])

    return vol.Schema(
        {
            vol.Required(
                CONF_LIVING_ENVIRONMENT, default=defaults.get(CONF_LIVING_ENVIRONMENT)
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=living_environment_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="living_environment",
                    sort=True,
                )
            ),
            vol.Required(
                CONF_MORPHOLOGY, default=defaults.get(CONF_MORPHOLOGY)
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=MORPHOLOGY_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="morphology",
                )
            ),
            vol.Required(
                CONF_WEIGHT_SENSOR,
                default=defaults.get(CONF_WEIGHT_SENSOR),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["sensor", "input_number", "number"]
                )
            ),
            vol.Optional(
                CONF_LAST_TIME_SENSOR,
                default=defaults.get(CONF_LAST_TIME_SENSOR),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor", "input_datetime"])
            ),
        }
    )


class BodyPetScaleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BodyPetScale."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self.data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> BodyPetScaleOptionsFlow:
        """Get the options flow for this handler."""
        return BodyPetScaleOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step (name and animal type)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_NAME].strip().lower())
            self._abort_if_unique_id_configured()

            self.data.update(user_input)
            return await self.async_step_profile()

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
                    vol.Required(CONF_BIRTHDAY): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.DATE)
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_profile(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle profile selection based on animal type."""
        errors: dict[str, str] = {}
        animal_type = self.data[CONF_ANIMAL_TYPE]

        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_options()

        schema_dict = {
            vol.Required(CONF_BREED): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=BREED_OPTIONS.get(animal_type, []),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="breed_options",
                )
            ),
            vol.Required(CONF_ACTIVITY): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=ACTIVITY_LEVELS.get(animal_type, []),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="activity_level",
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
            schema_dict[vol.Required(CONF_TEMPERAMENT)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=CAT_TEMPERAMENT_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="temperament",
                )
            )
        else:
            schema_dict[vol.Required(CONF_APPETITE)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=DOG_APPETITE_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="appetite",
                )
            )

        return self.async_show_form(
            step_id="profile",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the options step."""
        errors: dict[str, str] = {}
        placeholders = {"learn_more_link": MORPHOLOGY_URL}

        if user_input is not None:
            if not self.hass.states.get(user_input[CONF_WEIGHT_SENSOR]):
                errors[CONF_WEIGHT_SENSOR] = "invalid_weight_sensor"
            else:
                return self.async_create_entry(
                    title=self.data[CONF_NAME],
                    data=self.data,
                    options=user_input,
                )

        animal_type = self.data[CONF_ANIMAL_TYPE]
        schema = await self.hass.async_add_executor_job(
            get_options_schema, {}, animal_type
        )

        return self.async_show_form(
            step_id="options",
            data_schema=schema,
            errors=errors,
            description_placeholders=placeholders,
        )


class BodyPetScaleOptionsFlow(OptionsFlow):
    """Handle BodyPetScale options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage BodyPetScale options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        animal_type = self.config_entry.data.get(CONF_ANIMAL_TYPE, "cat")

        schema = await self.hass.async_add_executor_job(
            get_options_schema, self.config_entry.options, animal_type
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={"learn_more_link": MORPHOLOGY_URL},
        )
