"""Tests for the shared scale: identification methods and holder weight."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_NAME, UnitOfMass
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.bodypetscale.const import (
    ATTR_MAIN,
    ATTR_WEIGHING_MODE,
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
    CONF_STABILIZED_SENSOR,
    CONF_WEIGHT_SENSOR,
    DOMAIN,
    NOTIFICATION_COORDINATOR,
    PENDING_MEASUREMENT_TIMEOUT,
    PROFILE_METHOD_NEAREST,
    PROFILE_METHOD_NONE,
    PROFILE_METHOD_NOTIFY,
    PROFILE_METHOD_WEIGHT,
    WEIGHING_ALONE,
    WEIGHING_HELD,
)
from custom_components.bodypetscale.coordinator import BodyPetScaleCoordinator
from custom_components.bodypetscale.profile import (
    Candidate,
    action_id,
    state_to_kg,
    weighing_candidates,
)

from .conftest import CAT_DATA, DOG_DATA

SCALE = "sensor.shared_scale"
STABILIZED = "binary_sensor.shared_scale_stabilized"
OWNER = "sensor.owner_weight"
NOW = "2026-10-20 12:00:00+00:00"


@pytest.fixture(autouse=True)
def _freeze(freezer: Any) -> None:
    """Freeze time so that ages and timers are predictable."""
    freezer.move_to(NOW)


def _entry(data: dict[str, Any], method: str, **options: Any) -> MockConfigEntry:
    """Return a pet entry using the shared scale."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=data[CONF_NAME],
        unique_id=data[CONF_NAME].lower(),
        data=dict(data),
        options={
            CONF_LIVING_ENVIRONMENT: "indoors",
            CONF_MORPHOLOGY: "5_ideal",
            CONF_WEIGHT_SENSOR: SCALE,
            CONF_PROFILE_METHOD: method,
            **options,
        },
    )


async def _setup(hass: HomeAssistant, *entries: MockConfigEntry) -> None:
    hass.states.async_set(SCALE, "unknown")
    for entry in entries:
        entry.add_to_hass(hass)
    # Setting up the first entry sets up the integration with all its entries
    assert await hass.config_entries.async_setup(entries[0].entry_id)
    await hass.async_block_till_done()
    for entry in entries:
        assert entry.state is ConfigEntryState.LOADED


async def _weigh(hass: HomeAssistant, weight: float | str, **attrs: Any) -> None:
    hass.states.async_set(SCALE, str(weight), attrs)
    await hass.async_block_till_done()


def _coordinator(
    hass: HomeAssistant, entry: MockConfigEntry
) -> BodyPetScaleCoordinator:
    return hass.data[DOMAIN][entry.entry_id]


def _weight(hass: HomeAssistant, entry: MockConfigEntry) -> float | None:
    return _coordinator(hass, entry).weight


def _main_state(hass: HomeAssistant, entry: MockConfigEntry) -> State:
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_{ATTR_MAIN}"
    )
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    return state


# ===========================================================================
# Helpers
# ===========================================================================


def test_weighing_candidates() -> None:
    """The carried candidate only exists with a known, lower holder weight."""
    assert weighing_candidates(10.0, None) == [Candidate(WEIGHING_ALONE, 10.0)]
    assert weighing_candidates(79.25, 75.0) == [
        Candidate(WEIGHING_ALONE, 79.25),
        Candidate(WEIGHING_HELD, 4.25),
    ]
    assert weighing_candidates(70.0, 75.0) == [Candidate(WEIGHING_ALONE, 70.0)]


def test_state_to_kg() -> None:
    """Pounds are converted and invalid states return None."""
    assert state_to_kg(State(SCALE, "10")) == 10.0
    pounds = state_to_kg(
        State(SCALE, "22.05", {"unit_of_measurement": UnitOfMass.POUNDS})
    )
    assert pounds == pytest.approx(10.0, abs=0.01)
    assert state_to_kg(State(SCALE, "unavailable")) is None
    assert state_to_kg(State(SCALE, "abc")) is None
    assert state_to_kg(None) is None


def test_action_id() -> None:
    """Action ids are prefixed and upper case."""
    assert action_id("01abc", WEIGHING_HELD) == "BODYPETSCALE_01ABC_HELD"


# ===========================================================================
# Weight range
# ===========================================================================


async def test_weight_range_shared_scale(hass: HomeAssistant) -> None:
    """Each pet only takes the measurements in its own range."""
    rex = _entry(DOG_DATA, PROFILE_METHOD_WEIGHT, weight_min=8, weight_max=12)
    felix = _entry(CAT_DATA, PROFILE_METHOD_WEIGHT, weight_min=3, weight_max=6)
    await _setup(hass, rex, felix)
    assert _weight(hass, rex) is None

    await _weigh(hass, 10.2)
    assert _weight(hass, rex) == 10.2
    assert _weight(hass, felix) is None

    await _weigh(hass, 4.3)
    assert _weight(hass, felix) == 4.3
    assert _weight(hass, rex) == 10.2

    # A person on the scale: nobody takes it
    await _weigh(hass, 75)
    assert _weight(hass, rex) == 10.2
    assert _weight(hass, felix) == 4.3

    # The scale resets to 0: ignored
    await _weigh(hass, 0)
    assert _weight(hass, felix) == 4.3


async def test_weight_range_carried(hass: HomeAssistant) -> None:
    """A pet carried by its owner gets the net weight."""
    felix = _entry(
        CAT_DATA,
        PROFILE_METHOD_WEIGHT,
        weight_min=3,
        weight_max=6,
        holder_weight_sensor=OWNER,
    )
    hass.states.async_set(OWNER, "75.0")
    await _setup(hass, felix)

    await _weigh(hass, 79.2)
    coordinator = _coordinator(hass, felix)
    assert coordinator.weight == 4.2
    assert coordinator.weighing_mode == WEIGHING_HELD
    assert coordinator.data[ATTR_WEIGHING_MODE] == WEIGHING_HELD
    assert coordinator.data[CONF_LAST_TIME_SENSOR] is not None
    assert _main_state(hass, felix).attributes[ATTR_WEIGHING_MODE] == WEIGHING_HELD

    # Weighed alone afterwards
    await _weigh(hass, 4.4)
    assert coordinator.weight == 4.4
    assert coordinator.weighing_mode == WEIGHING_ALONE


async def test_holder_weight_read_at_measurement(hass: HomeAssistant) -> None:
    """The holder weight updated after the weighing does not change the result."""
    felix = _entry(
        CAT_DATA,
        PROFILE_METHOD_WEIGHT,
        weight_min=3,
        weight_max=6,
        holder_weight_sensor=OWNER,
    )
    hass.states.async_set(OWNER, "75.0")
    await _setup(hass, felix)

    await _weigh(hass, 79.2)
    # e.g. bodymiscale attributes the carried weight to the owner afterwards
    hass.states.async_set(OWNER, "79.2")
    await hass.async_block_till_done()
    assert _weight(hass, felix) == 4.2


# ===========================================================================
# Nearest weight
# ===========================================================================


async def test_nearest_weight(hass: HomeAssistant) -> None:
    """The measurement goes to the pet with the nearest last weight."""
    rex = _entry(
        DOG_DATA,
        PROFILE_METHOD_NEAREST,
        initial_weight=10.0,
        nearest_tolerance=2.0,
    )
    felix = _entry(
        CAT_DATA,
        PROFILE_METHOD_NEAREST,
        initial_weight=4.0,
        nearest_tolerance=2.0,
        holder_weight_sensor=OWNER,
    )
    hass.states.async_set(OWNER, "75.0")
    await _setup(hass, rex, felix)
    assert _weight(hass, rex) == 10.0
    assert _weight(hass, felix) == 4.0

    await _weigh(hass, 9.6)
    assert _weight(hass, rex) == 9.6
    assert _weight(hass, felix) == 4.0

    await _weigh(hass, 4.4)
    assert _weight(hass, felix) == 4.4
    assert _weight(hass, rex) == 9.6

    # Too far from both pets
    await _weigh(hass, 7.0)
    assert _weight(hass, rex) == 9.6
    assert _weight(hass, felix) == 4.4

    # Felix carried by the owner
    await _weigh(hass, 79.5)
    assert _weight(hass, felix) == 4.5
    assert _coordinator(hass, felix).weighing_mode == WEIGHING_HELD
    assert _weight(hass, rex) == 9.6


async def test_nearest_weight_without_known_weight(hass: HomeAssistant) -> None:
    """Without any known weight, a nearest-weight pet cannot be identified."""
    rex = _entry(DOG_DATA, PROFILE_METHOD_NEAREST, nearest_tolerance=2.0)
    await _setup(hass, rex)
    await _weigh(hass, 10.0)
    assert _weight(hass, rex) is None


# ===========================================================================
# No identification (dedicated sensor) with a holder
# ===========================================================================


async def test_none_with_holder_always_subtracts(hass: HomeAssistant) -> None:
    """With the none method, the holder weight is always subtracted."""
    felix = _entry(CAT_DATA, PROFILE_METHOD_NONE, holder_weight_sensor=OWNER)
    hass.states.async_set(OWNER, "75.0")
    await _setup(hass, felix)

    await _weigh(hass, 79.1)
    assert _weight(hass, felix) == 4.1
    assert _coordinator(hass, felix).weighing_mode == WEIGHING_HELD

    # Holder unknown: the measurement cannot be computed
    hass.states.async_set(OWNER, "unavailable")
    await _weigh(hass, 80.0)
    assert _weight(hass, felix) == 4.1


# ===========================================================================
# Scale behaviour
# ===========================================================================


async def test_scale_back_with_same_value_ignored(hass: HomeAssistant) -> None:
    """A scale coming back from unavailable with its last value is not a weighing."""
    rex = _entry(DOG_DATA, PROFILE_METHOD_WEIGHT, weight_min=8, weight_max=12)
    await _setup(hass, rex)
    await _weigh(hass, 10.2)
    first = _coordinator(hass, rex).measured_at
    assert first is not None

    await _weigh(hass, "unavailable")
    hass.states.async_set(SCALE, "10.2")
    await hass.async_block_till_done()
    assert _coordinator(hass, rex).measured_at == first


async def test_stabilized_sensor(hass: HomeAssistant, freezer: Any) -> None:
    """With a stabilized sensor, the weight is read once the measurement is stable."""
    rex = _entry(
        DOG_DATA,
        PROFILE_METHOD_WEIGHT,
        weight_min=8,
        weight_max=12,
        stabilized_sensor=STABILIZED,
    )
    hass.states.async_set(STABILIZED, "off")
    await _setup(hass, rex)

    await _weigh(hass, 9.0)
    await _weigh(hass, 10.4)
    assert _weight(hass, rex) is None

    hass.states.async_set(STABILIZED, "on")
    await hass.async_block_till_done()
    assert _weight(hass, rex) is None

    freezer.tick(timedelta(seconds=2))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert _weight(hass, rex) == 10.4


# ===========================================================================
# Persistence
# ===========================================================================


async def test_weight_restored_after_reload(hass: HomeAssistant) -> None:
    """The accepted weight and time survive a reload of the integration."""
    rex = _entry(DOG_DATA, PROFILE_METHOD_WEIGHT, weight_min=8, weight_max=12)
    await _setup(hass, rex)
    await _weigh(hass, 10.2)
    measured_at = _coordinator(hass, rex).measured_at

    # Another pet (or person) is the last one on the scale
    await _weigh(hass, 30.0)
    assert await hass.config_entries.async_reload(rex.entry_id)
    await hass.async_block_till_done()

    coordinator = _coordinator(hass, rex)
    assert coordinator.weight == 10.2
    assert coordinator.measured_at == measured_at
    assert coordinator.weighing_mode == WEIGHING_ALONE


async def test_last_time_entity_with_shared_scale(hass: HomeAssistant) -> None:
    """The last measurement time entity is created for a shared scale."""
    rex = _entry(DOG_DATA, PROFILE_METHOD_WEIGHT, weight_min=8, weight_max=12)
    await _setup(hass, rex)
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{rex.entry_id}_{CONF_LAST_TIME_SENSOR}"
    )
    assert entity_id is not None
    assert hass.states.get(entity_id).state == "unknown"

    await _weigh(hass, 10.2)
    assert hass.states.get(entity_id).state == "2026-10-20T12:00:00+00:00"


# ===========================================================================
# Notification
# ===========================================================================


@pytest.fixture
def phone(hass: HomeAssistant) -> str:
    """Register a mobile_app phone and return its device id."""
    phone_entry = MockConfigEntry(domain="mobile_app")
    phone_entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=phone_entry.entry_id,
        identifiers={("mobile_app", "abc123")},
        name="Phone",
    )
    return device.id


async def _flush_notification(hass: HomeAssistant, freezer: Any) -> None:
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def test_notification_alone_and_carried(
    hass: HomeAssistant, phone: str, freezer: Any
) -> None:
    """One notification lists each pet alone and carried, the tap sets the weight."""
    calls = async_mock_service(hass, "notify", "mobile_app_abc123")
    rex = _entry(DOG_DATA, PROFILE_METHOD_NOTIFY, notify_device_id=phone)
    felix = _entry(
        CAT_DATA,
        PROFILE_METHOD_NOTIFY,
        notify_device_id=phone,
        holder_weight_sensor=OWNER,
    )
    hass.states.async_set(OWNER, "75.0")
    await _setup(hass, rex, felix)

    await _weigh(hass, 79.2)
    assert _weight(hass, felix) is None
    await _flush_notification(hass, freezer)

    assert len(calls) == 1
    data = calls[0].data
    assert data["message"] == "New measurement: 79.2 kg"
    assert data["data"]["actions"] == [
        {"action": action_id(rex.entry_id, WEIGHING_ALONE), "title": "Rex"},
        {"action": action_id(felix.entry_id, WEIGHING_ALONE), "title": "Felix"},
        {
            "action": action_id(felix.entry_id, WEIGHING_HELD),
            "title": "Felix (carried)",
        },
    ]

    # The owner's own profile updates the holder weight before the answer
    hass.states.async_set(OWNER, "79.2")
    hass.bus.async_fire(
        "mobile_app_notification_action",
        {"action": action_id(felix.entry_id, WEIGHING_HELD)},
    )
    await hass.async_block_till_done()

    assert _weight(hass, felix) == 4.2
    assert _coordinator(hass, felix).weighing_mode == WEIGHING_HELD
    assert _weight(hass, rex) is None

    # The measurement belongs to Felix: a late tap on Rex does nothing
    hass.bus.async_fire(
        "mobile_app_notification_action",
        {"action": action_id(rex.entry_id, WEIGHING_ALONE)},
    )
    await hass.async_block_till_done()
    assert _weight(hass, rex) is None


async def test_notification_weight_filters(
    hass: HomeAssistant, phone: str, freezer: Any
) -> None:
    """Notification weight bounds limit the proposed pets and modes."""
    calls = async_mock_service(hass, "notify", "mobile_app_abc123")
    rex = _entry(
        DOG_DATA,
        PROFILE_METHOD_NOTIFY,
        notify_device_id=phone,
        notify_weight_max=30,
    )
    felix = _entry(
        CAT_DATA,
        PROFILE_METHOD_NOTIFY,
        notify_device_id=phone,
        notify_weight_min=2,
        notify_weight_max=8,
        holder_weight_sensor=OWNER,
    )
    hass.states.async_set(OWNER, "75.0")
    await _setup(hass, rex, felix)

    await _weigh(hass, 79.2)
    await _flush_notification(hass, freezer)
    assert [a["title"] for a in calls[0].data["data"]["actions"]] == ["Felix (carried)"]

    # A person alone: nobody to propose, no notification
    hass.states.async_set(OWNER, "unavailable")
    await _weigh(hass, 80.0)
    await _flush_notification(hass, freezer)
    assert len(calls) == 1


async def test_notification_expires(
    hass: HomeAssistant, phone: str, freezer: Any
) -> None:
    """An answer after the timeout is ignored."""
    async_mock_service(hass, "notify", "mobile_app_abc123")
    rex = _entry(DOG_DATA, PROFILE_METHOD_NOTIFY, notify_device_id=phone)
    await _setup(hass, rex)

    await _weigh(hass, 10.0)
    freezer.tick(timedelta(seconds=PENDING_MEASUREMENT_TIMEOUT + 1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    hass.bus.async_fire(
        "mobile_app_notification_action",
        {"action": action_id(rex.entry_id, WEIGHING_ALONE)},
    )
    await hass.async_block_till_done()
    assert _weight(hass, rex) is None


async def test_notification_unknown_device(hass: HomeAssistant, freezer: Any) -> None:
    """A missing phone does not break the measurement handling."""
    rex = _entry(DOG_DATA, PROFILE_METHOD_NOTIFY, notify_device_id="missing")
    await _setup(hass, rex)
    await _weigh(hass, 10.0)
    await _flush_notification(hass, freezer)
    assert _weight(hass, rex) is None


async def test_notification_coordinator_lifecycle(
    hass: HomeAssistant, phone: str
) -> None:
    """The notification coordinator lives as long as a notification pet exists."""
    rex = _entry(DOG_DATA, PROFILE_METHOD_NOTIFY, notify_device_id=phone)
    felix = _entry(CAT_DATA, PROFILE_METHOD_NOTIFY, notify_device_id=phone)
    await _setup(hass, rex, felix)
    assert hass.data[DOMAIN][NOTIFICATION_COORDINATOR] is not None

    assert await hass.config_entries.async_unload(rex.entry_id)
    assert hass.data[DOMAIN][NOTIFICATION_COORDINATOR] is not None
    assert await hass.config_entries.async_unload(felix.entry_id)
    assert hass.data[DOMAIN][NOTIFICATION_COORDINATOR] is None


async def test_unused_options_ignored(hass: HomeAssistant) -> None:
    """Settings of another method do not affect the selected one."""
    rex = _entry(
        DOG_DATA,
        PROFILE_METHOD_WEIGHT,
        weight_min=8,
        weight_max=12,
        **{
            CONF_INITIAL_WEIGHT: 50,
            CONF_NEAREST_TOLERANCE: 99,
            CONF_NOTIFY_DEVICE_ID: "x",
            CONF_NOTIFY_WEIGHT_MIN: 0,
            CONF_NOTIFY_WEIGHT_MAX: 1,
            CONF_STABILIZED_SENSOR: None,
            CONF_HOLDER_WEIGHT_SENSOR: None,
        },
    )
    await _setup(hass, rex)
    assert _weight(hass, rex) is None
    await _weigh(hass, 50)
    assert _weight(hass, rex) is None
    await _weigh(hass, 9)
    assert _weight(hass, rex) == 9
