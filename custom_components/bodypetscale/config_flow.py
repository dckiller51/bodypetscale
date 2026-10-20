"""Config flow for BodyPetScale."""

from __future__ import annotations

import logging
from types import MappingProxyType
from typing import Any

import probatio
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
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
    CONF_HOLDER_WEIGHT_SENSOR,
    CONF_INITIAL_WEIGHT,
    CONF_LAST_TIME_SENSOR,
    CONF_LIVING_ENVIRONMENT,
    CONF_MORPHOLOGY,
    CONF_NEAREST_TOLERANCE,
    CONF_NOTIFY_DEVICE_ID,
    CONF_NOTIFY_WEIGHT_MAX,
    CONF_NOTIFY_WEIGHT_MIN,
    CONF_PROFILE_METHOD,
    CONF_REPRODUCTIVE,
    CONF_STABILIZED_SENSOR,
    CONF_TEMPERAMENT,
    CONF_WEIGHT_MAX,
    CONF_WEIGHT_MIN,
    CONF_WEIGHT_SENSOR,
    DEFAULT_NEAREST_TOLERANCE,
    DOG_APPETITE_OPTIONS,
    DOMAIN,
    LIVING_ENVIRONMENT_OPTIONS,
    MORPHOLOGY_OPTIONS,
    MORPHOLOGY_URL,
    PROFILE_METHOD_NEAREST,
    PROFILE_METHOD_NONE,
    PROFILE_METHOD_NOTIFY,
    PROFILE_METHOD_OPTIONS,
    PROFILE_METHOD_WEIGHT,
    REPRODUCTIVE_STATUS,
)

_LOGGER = logging.getLogger(__name__)


def get_options_schema(
    defaults: dict[str, Any] | MappingProxyType[str, Any],
    animal_type: str,
) -> probatio.Schema:
    """Return the options schema."""

    living_environment_options = LIVING_ENVIRONMENT_OPTIONS.get(animal_type, [])

    return probatio.Schema(
        {
            probatio.Required(
                CONF_LIVING_ENVIRONMENT,
                description={"suggested_value": defaults.get(CONF_LIVING_ENVIRONMENT)},
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=living_environment_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="living_environment",
                    sort=True,
                )
            ),
            probatio.Required(
                CONF_MORPHOLOGY,
                description={"suggested_value": defaults.get(CONF_MORPHOLOGY)},
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=MORPHOLOGY_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="morphology",
                )
            ),
            probatio.Required(
                CONF_WEIGHT_SENSOR,
                description={"suggested_value": defaults.get(CONF_WEIGHT_SENSOR)},
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["sensor", "input_number", "number"]
                )
            ),
            probatio.Optional(
                CONF_LAST_TIME_SENSOR,
                description={"suggested_value": defaults.get(CONF_LAST_TIME_SENSOR)},
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor", "input_datetime"])
            ),
            probatio.Optional(
                CONF_STABILIZED_SENSOR,
                description={"suggested_value": defaults.get(CONF_STABILIZED_SENSOR)},
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["binary_sensor"])
            ),
            probatio.Optional(
                CONF_HOLDER_WEIGHT_SENSOR,
                description={
                    "suggested_value": defaults.get(CONF_HOLDER_WEIGHT_SENSOR)
                },
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["sensor", "input_number", "number"]
                )
            ),
            probatio.Required(
                CONF_PROFILE_METHOD,
                default=defaults.get(CONF_PROFILE_METHOD, PROFILE_METHOD_NONE),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=PROFILE_METHOD_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="profile_method",
                )
            ),
        }
    )


def _weight_selector(step: float = 0.01) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            mode=selector.NumberSelectorMode.BOX,
            min=0,
            max=150,
            step=step,
            unit_of_measurement="kg",
        )
    )


def get_method_schema(
    method: str, defaults: dict[str, Any] | MappingProxyType[str, Any]
) -> probatio.Schema | None:
    """Return the schema of the profile method settings, if any."""

    def suggested(key: str) -> dict[str, Any]:
        return {"suggested_value": defaults.get(key)}

    if method == PROFILE_METHOD_WEIGHT:
        return probatio.Schema(
            {
                probatio.Required(
                    CONF_WEIGHT_MIN, description=suggested(CONF_WEIGHT_MIN)
                ): _weight_selector(),
                probatio.Required(
                    CONF_WEIGHT_MAX, description=suggested(CONF_WEIGHT_MAX)
                ): _weight_selector(),
            }
        )
    if method == PROFILE_METHOD_NEAREST:
        return probatio.Schema(
            {
                probatio.Required(
                    CONF_INITIAL_WEIGHT, description=suggested(CONF_INITIAL_WEIGHT)
                ): _weight_selector(0.1),
                probatio.Required(
                    CONF_NEAREST_TOLERANCE,
                    default=defaults.get(
                        CONF_NEAREST_TOLERANCE, DEFAULT_NEAREST_TOLERANCE
                    ),
                ): _weight_selector(0.1),
            }
        )
    if method == PROFILE_METHOD_NOTIFY:
        return probatio.Schema(
            {
                probatio.Required(
                    CONF_NOTIFY_DEVICE_ID, description=suggested(CONF_NOTIFY_DEVICE_ID)
                ): selector.DeviceSelector(
                    selector.DeviceSelectorConfig(integration="mobile_app")
                ),
                probatio.Optional(
                    CONF_NOTIFY_WEIGHT_MIN,
                    description=suggested(CONF_NOTIFY_WEIGHT_MIN),
                ): _weight_selector(0.1),
                probatio.Optional(
                    CONF_NOTIFY_WEIGHT_MAX,
                    description=suggested(CONF_NOTIFY_WEIGHT_MAX),
                ): _weight_selector(0.1),
            }
        )
    return None


def validate_options(hass: HomeAssistant, user_input: dict[str, Any]) -> dict[str, str]:
    """Validate the options step."""
    errors: dict[str, str] = {}
    if not hass.states.get(user_input[CONF_WEIGHT_SENSOR]):
        errors[CONF_WEIGHT_SENSOR] = "invalid_weight_sensor"
    if user_input.get(CONF_HOLDER_WEIGHT_SENSOR) == user_input[CONF_WEIGHT_SENSOR]:
        errors[CONF_HOLDER_WEIGHT_SENSOR] = "holder_same_as_scale"
    return errors


def validate_method(user_input: dict[str, Any]) -> dict[str, str]:
    """Validate the profile method step."""
    for key_min, key_max in (
        (CONF_WEIGHT_MIN, CONF_WEIGHT_MAX),
        (CONF_NOTIFY_WEIGHT_MIN, CONF_NOTIFY_WEIGHT_MAX),
    ):
        w_min, w_max = user_input.get(key_min), user_input.get(key_max)
        if w_min is not None and w_max is not None and w_min >= w_max:
            return {key_max: "invalid_weight_range"}
    return {}


class BodyPetScaleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BodyPetScale."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self.data: dict[str, Any] = {}
        self.options: dict[str, Any] = {}

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
            data_schema=probatio.Schema(
                {
                    probatio.Required(CONF_NAME): str,
                    probatio.Required(CONF_ANIMAL_TYPE): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=ANIMAL_TYPES,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            translation_key="animal_type",
                        )
                    ),
                    probatio.Required(CONF_BIRTHDAY): selector.TextSelector(
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
            probatio.Required(CONF_BREED): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=BREED_OPTIONS.get(animal_type, []),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="breed_options",
                )
            ),
            probatio.Required(CONF_ACTIVITY): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=ACTIVITY_LEVELS.get(animal_type, []),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="activity_level",
                )
            ),
            probatio.Required(CONF_REPRODUCTIVE): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=REPRODUCTIVE_STATUS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="reproductive_status",
                )
            ),
        }

        if animal_type == "cat":
            schema_dict[probatio.Required(CONF_TEMPERAMENT)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=CAT_TEMPERAMENT_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="temperament",
                )
            )
        else:
            schema_dict[probatio.Required(CONF_APPETITE)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=DOG_APPETITE_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="appetite",
                )
            )

        return self.async_show_form(
            step_id="profile",
            data_schema=probatio.Schema(schema_dict),
            errors=errors,
        )

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the options step (sensors and identification method)."""
        errors: dict[str, str] = {}
        placeholders = {"learn_more_link": MORPHOLOGY_URL}

        if user_input is not None:
            errors = validate_options(self.hass, user_input)
            if not errors:
                self.options = dict(user_input)
                if get_method_schema(user_input[CONF_PROFILE_METHOD], {}) is None:
                    return self._create_entry()
                return await self.async_step_method()

        animal_type = self.data[CONF_ANIMAL_TYPE]
        schema = await self.hass.async_add_executor_job(
            get_options_schema, user_input or {}, animal_type
        )

        return self.async_show_form(
            step_id="options",
            data_schema=schema,
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_method(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the settings of the identification method."""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = validate_method(user_input)
            if not errors:
                self.options.update(user_input)
                return self._create_entry()

        method = self.options[CONF_PROFILE_METHOD]
        return self.async_show_form(
            step_id="method",
            data_schema=get_method_schema(method, user_input or {}),
            errors=errors,
        )

    def _create_entry(self) -> ConfigFlowResult:
        return self.async_create_entry(
            title=self.data[CONF_NAME],
            data=self.data,
            options=self.options,
        )


class BodyPetScaleOptionsFlow(OptionsFlow):
    """Handle BodyPetScale options."""

    def __init__(self) -> None:
        """Initialize."""
        self.options: dict[str, Any] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage BodyPetScale options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = validate_options(self.hass, user_input)
            if not errors:
                self.options = dict(user_input)
                if get_method_schema(user_input[CONF_PROFILE_METHOD], {}) is None:
                    return self.async_create_entry(title="", data=self.options)
                return await self.async_step_method()

        animal_type = self.config_entry.data.get(CONF_ANIMAL_TYPE, "cat")

        schema = await self.hass.async_add_executor_job(
            get_options_schema, user_input or self.config_entry.options, animal_type
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
            description_placeholders={"learn_more_link": MORPHOLOGY_URL},
        )

    async def async_step_method(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the settings of the identification method."""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = validate_method(user_input)
            if not errors:
                self.options.update(user_input)
                return self.async_create_entry(title="", data=self.options)

        method = self.options[CONF_PROFILE_METHOD]
        return self.async_show_form(
            step_id="method",
            data_schema=get_method_schema(
                method, user_input or self.config_entry.options
            ),
            errors=errors,
        )
