"""Tests for the bodypetscale config flow."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import probatio
import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_validation as cv
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bodypetscale.config_flow import get_options_schema
from custom_components.bodypetscale.const import (
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
    MORPHOLOGY_URL,
)

from .conftest import (
    CAT_DATA,
    CAT_OPTIONS,
    DOG_DATA,
    DOG_OPTIONS,
    LAST_TIME_SENSOR,
    WEIGHT_SENSOR,
)

SETUP_ENTRY = "custom_components.bodypetscale.async_setup_entry"


def _user_step(data: dict[str, Any]) -> dict[str, Any]:
    return {key: data[key] for key in (CONF_NAME, CONF_ANIMAL_TYPE, CONF_BIRTHDAY)}


def _profile_step(data: dict[str, Any]) -> dict[str, Any]:
    keys = (CONF_NAME, CONF_ANIMAL_TYPE, CONF_BIRTHDAY)
    return {key: value for key, value in data.items() if key not in keys}


def _field_names(schema: probatio.Schema) -> list[str]:
    return [str(key) for key in schema.schema]


# ===========================================================================
# Options schema (probatio)
# ===========================================================================


@pytest.mark.parametrize(
    ("animal_type", "environments"),
    [
        ("dog", ["indoors", "outdoors_summer_20"]),
        ("cat", ["indoors", "outdoors_summer"]),
    ],
)
def test_options_schema_is_probatio(animal_type: str, environments: list[str]) -> None:
    """The options schema is a probatio schema serializable by Home Assistant."""
    schema = get_options_schema({CONF_MORPHOLOGY: "5_ideal"}, animal_type)
    assert isinstance(schema, probatio.Schema)

    fields = probatio.to_field_list(schema, custom_serializer=cv.custom_serializer)
    by_name = {field["name"]: field for field in fields}

    assert list(by_name) == [
        CONF_LIVING_ENVIRONMENT,
        CONF_MORPHOLOGY,
        CONF_WEIGHT_SENSOR,
        CONF_LAST_TIME_SENSOR,
    ]
    assert by_name[CONF_WEIGHT_SENSOR]["required"] is True
    assert by_name[CONF_LAST_TIME_SENSOR]["required"] is False
    assert by_name[CONF_MORPHOLOGY]["description"] == {"suggested_value": "5_ideal"}
    assert by_name[CONF_WEIGHT_SENSOR]["description"] == {"suggested_value": None}

    env_options = by_name[CONF_LIVING_ENVIRONMENT]["selector"]["select"]["options"]
    for environment in environments:
        assert environment in env_options


def test_options_schema_validates() -> None:
    """The options schema accepts valid input and rejects a missing field."""
    schema = get_options_schema({}, "dog")
    assert schema(dict(DOG_OPTIONS)) == DOG_OPTIONS

    incomplete = dict(DOG_OPTIONS)
    del incomplete[CONF_WEIGHT_SENSOR]
    with pytest.raises(probatio.Invalid):
        schema(incomplete)


# ===========================================================================
# Config flow
# ===========================================================================


async def test_flow_user_step_shows_form(hass: HomeAssistant) -> None:
    """Step 'user' shows a form when called without input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}
    assert _field_names(result["data_schema"]) == [
        CONF_NAME,
        CONF_ANIMAL_TYPE,
        CONF_BIRTHDAY,
    ]


@pytest.mark.parametrize(
    ("data", "options", "specific_field", "absent_field"),
    [
        (DOG_DATA, DOG_OPTIONS, CONF_APPETITE, CONF_TEMPERAMENT),
        (CAT_DATA, CAT_OPTIONS, CONF_TEMPERAMENT, CONF_APPETITE),
    ],
)
async def test_full_flow(
    hass: HomeAssistant,
    data: dict[str, Any],
    options: dict[str, Any],
    specific_field: str,
    absent_field: str,
) -> None:
    """A complete flow creates an entry with data and options split."""
    hass.states.async_set(WEIGHT_SENSOR, "10")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], _user_step(data)
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "profile"
    fields = _field_names(result["data_schema"])
    assert specific_field in fields
    assert absent_field not in fields
    for key in (CONF_BREED, CONF_ACTIVITY, CONF_REPRODUCTIVE):
        assert key in fields

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], _profile_step(data)
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options"
    assert result["description_placeholders"] == {"learn_more_link": MORPHOLOGY_URL}

    with patch(SETUP_ENTRY, return_value=True) as mock_setup:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], dict(options)
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == data[CONF_NAME]
    assert result["data"] == data
    assert result["options"] == options
    assert result["result"].unique_id == data[CONF_NAME].lower()
    assert len(mock_setup.mock_calls) == 1


async def test_flow_invalid_weight_sensor(hass: HomeAssistant) -> None:
    """An unknown weight sensor shows an error, then the flow can finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], _user_step(DOG_DATA)
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], _profile_step(DOG_DATA)
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], dict(DOG_OPTIONS)
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options"
    assert result["errors"] == {CONF_WEIGHT_SENSOR: "invalid_weight_sensor"}

    hass.states.async_set(WEIGHT_SENSOR, "10")
    with patch(SETUP_ENTRY, return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], dict(DOG_OPTIONS)
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_flow_already_configured(
    hass: HomeAssistant, dog_entry: MockConfigEntry
) -> None:
    """A second pet with the same name (case/space-insensitive) is rejected."""
    dog_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**_user_step(DOG_DATA), CONF_NAME: "  REX "}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


# ===========================================================================
# Options flow
# ===========================================================================


async def test_options_flow(hass: HomeAssistant, cat_entry: MockConfigEntry) -> None:
    """The options flow pre-fills current values and saves new ones."""
    cat_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(cat_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["description_placeholders"] == {"learn_more_link": MORPHOLOGY_URL}

    fields = probatio.to_field_list(
        result["data_schema"], custom_serializer=cv.custom_serializer
    )
    suggested = {f["name"]: f["description"]["suggested_value"] for f in fields}
    assert suggested == {
        CONF_LIVING_ENVIRONMENT: "indoors",
        CONF_MORPHOLOGY: "6_slightly_overweight",
        CONF_WEIGHT_SENSOR: WEIGHT_SENSOR,
        CONF_LAST_TIME_SENSOR: LAST_TIME_SENSOR,
    }

    new_options = {
        CONF_LIVING_ENVIRONMENT: "outdoors_winter",
        CONF_MORPHOLOGY: "5_ideal",
        CONF_WEIGHT_SENSOR: "sensor.other_weight",
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], new_options
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert cat_entry.options == new_options
