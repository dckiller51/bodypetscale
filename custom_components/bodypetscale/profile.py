"""Shared scale support for BodyPetScale.

A single scale weight sensor can be shared by several pets (and people).
Each pet entry gets a ``PetScaleHandler`` which listens to the scale and
decides whether a measurement belongs to this pet, using one of the
identification methods also used by bodymiscale:

  none           dedicated weight sensor for this pet (legacy behaviour)
  weight_range   weight in [min, max[
  nearest_weight nearest last known weight among the pets, within a tolerance
  notification   interactive notification: tap the pet name

A pet can also be weighed in the arms of a person.  When a holder weight
sensor is configured (the person's weight, e.g. from bodymiscale or an
input_number), the net weight ``scale - holder`` is also considered:

  none           the holder weight is always subtracted
  weight_range   "alone" if the scale weight is in range, else "held" if the
                 net weight is in range
  nearest_weight the closest of the scale weight and the net weight wins
  notification   two buttons per pet: "<name>" (alone) and "<name> (carried)"

The holder weight is read when the measurement arrives, before the person's
own profile (e.g. bodymiscale) may update it with the carried weight.
"""

from __future__ import annotations

import json
import logging
import os
import unicodedata
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Coroutine
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_NAME,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later, async_track_state_change_event

from .const import (
    CONF_HOLDER_WEIGHT_SENSOR,
    CONF_INITIAL_WEIGHT,
    CONF_LAST_TIME_SENSOR,
    CONF_NEAREST_TOLERANCE,
    CONF_NOTIFY_DEVICE_ID,
    CONF_NOTIFY_WEIGHT_MAX,
    CONF_NOTIFY_WEIGHT_MIN,
    CONF_PROFILE_METHOD,
    CONF_STABILIZED_SENSOR,
    CONF_WEIGHT_MAX,
    CONF_WEIGHT_MIN,
    CONF_WEIGHT_SENSOR,
    DEFAULT_NEAREST_TOLERANCE,
    DOMAIN,
    LB_TO_KG,
    NOTIFICATION_ACTION_PREFIX,
    NOTIFICATION_COORDINATOR,
    NOTIFICATION_SEND_DELAY,
    NOTIFICATION_TAG,
    PENDING_MEASUREMENT_TIMEOUT,
    PROFILE_METHOD_NEAREST,
    PROFILE_METHOD_NONE,
    PROFILE_METHOD_NOTIFY,
    PROFILE_METHOD_WEIGHT,
    STABILIZED_READ_DELAY,
    UNIT_POUNDS,
    WEIGHING_ALONE,
    WEIGHING_HELD,
)

if TYPE_CHECKING:
    from .coordinator import BodyPetScaleCoordinator

_LOGGER = logging.getLogger(__name__)

_INVALID_STATES = (STATE_UNAVAILABLE, STATE_UNKNOWN)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Candidate:
    """A possible interpretation of a scale measurement for a pet."""

    mode: str
    weight: float


def state_to_kg(state: State | None) -> float | None:
    """Return the state value in kg, or None if it is not a number."""
    if state is None or state.state in _INVALID_STATES:
        return None
    try:
        value = float(state.state)
    except ValueError:
        return None
    if state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UNIT_POUNDS:
        value *= LB_TO_KG
    return value


def weighing_candidates(gross: float, holder: float | None) -> list[Candidate]:
    """Return the alone and, when a holder weight is known, carried candidates."""
    candidates = [Candidate(WEIGHING_ALONE, round(gross, 2))]
    if holder is not None and gross - holder > 0:
        candidates.append(Candidate(WEIGHING_HELD, round(gross - holder, 2)))
    return candidates


def _held(candidates: list[Candidate]) -> Candidate | None:
    return next((c for c in candidates if c.mode == WEIGHING_HELD), None)


def _in_range(weight: float, w_min: Any, w_max: Any) -> bool:
    """Return True if weight is in [w_min, w_max[ (open bounds when None)."""
    if w_min is not None and weight < float(w_min):
        return False
    return not (w_max is not None and weight >= float(w_max))


# ---------------------------------------------------------------------------
# Profile filters
# ---------------------------------------------------------------------------


class ProfileFilter(ABC):
    """Decide whether a measurement belongs to a pet."""

    @abstractmethod
    def select(
        self, handler: PetScaleHandler, candidates: list[Candidate]
    ) -> Candidate | None:
        """Return the accepted candidate, or None if rejected."""


class NoFilterProfile(ProfileFilter):
    """Dedicated sensor: accept every measurement.

    With a holder sensor the holder weight is always subtracted.
    """

    def select(
        self, handler: PetScaleHandler, candidates: list[Candidate]
    ) -> Candidate | None:
        """Return the measurement, net of the holder weight if configured."""
        if handler.config.get(CONF_HOLDER_WEIGHT_SENSOR):
            held = _held(candidates)
            if held is None:
                _LOGGER.debug(
                    "[%s] Holder weight unknown or too high — rejected", handler.name
                )
            return held
        return candidates[0]


class WeightRangeFilter(ProfileFilter):
    """Accept the first candidate whose weight is in [min, max[."""

    def select(
        self, handler: PetScaleHandler, candidates: list[Candidate]
    ) -> Candidate | None:
        """Return the first candidate in the configured range."""
        w_min = handler.config.get(CONF_WEIGHT_MIN)
        w_max = handler.config.get(CONF_WEIGHT_MAX)
        if w_min is None or w_max is None:
            _LOGGER.warning("[%s] Weight range incomplete — rejected", handler.name)
            return None
        for candidate in candidates:
            if float(w_min) <= candidate.weight < float(w_max):
                return candidate
        _LOGGER.debug(
            "[%s] %s not in [%s, %s[ — rejected", handler.name, candidates, w_min, w_max
        )
        return None


class NearestWeightFilter(ProfileFilter):
    """Accept if this pet's last weight is the nearest among nearest-weight pets."""

    def select(
        self, handler: PetScaleHandler, candidates: list[Candidate]
    ) -> Candidate | None:
        """Return the nearest candidate if this pet wins the comparison."""
        own = handler.nearest_candidate(candidates)
        if own is None:
            _LOGGER.debug("[%s] No known weight yet — rejected", handler.name)
            return None

        gross = candidates[0].weight
        ranking: list[tuple[float, str]] = []
        for other in handler.registry.values():
            if other.method != PROFILE_METHOD_NEAREST:
                continue
            best = other.nearest_candidate(
                weighing_candidates(gross, other.holder_weight())
            )
            if best is not None:
                ranking.append((best[0], other.name.casefold()))

        if not ranking:
            return None
        best_distance, best_name = min(ranking)
        distance, candidate = own
        if distance != best_distance or handler.name.casefold() != best_name:
            _LOGGER.debug("[%s] Not the nearest pet — rejected", handler.name)
            return None
        tolerance = float(
            handler.config.get(CONF_NEAREST_TOLERANCE, DEFAULT_NEAREST_TOLERANCE)
        )
        if distance > tolerance:
            _LOGGER.debug(
                "[%s] %.2f kg away, tolerance %.2f — rejected",
                handler.name,
                distance,
                tolerance,
            )
            return None
        return candidate


_FILTERS: dict[str, type[ProfileFilter]] = {
    PROFILE_METHOD_NONE: NoFilterProfile,
    PROFILE_METHOD_WEIGHT: WeightRangeFilter,
    PROFILE_METHOD_NEAREST: NearestWeightFilter,
}


def build_profile_filter(method: str) -> ProfileFilter:
    """Return the filter for a profile method (notification has none)."""
    return _FILTERS.get(method, NoFilterProfile)()


# ---------------------------------------------------------------------------
# Per-pet handler
# ---------------------------------------------------------------------------


@dataclass
class PendingMeasurement:
    """A measurement waiting for a notification answer."""

    gross: float
    holder: float | None
    cancel_timeout: CALLBACK_TYPE


class PetScaleHandler:
    """Listen to the scale sensors and feed accepted weights to the coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        coordinator: BodyPetScaleCoordinator,
        registry: dict[str, PetScaleHandler],
    ) -> None:
        """Initialize the handler."""
        self.hass = hass
        self.entry_id = entry.entry_id
        self.name: str = entry.data.get(CONF_NAME, entry.title)
        self.config: dict[str, Any] = {**entry.data, **entry.options}
        self.coordinator = coordinator
        self.registry = registry
        self.method: str = self.config.get(CONF_PROFILE_METHOD) or PROFILE_METHOD_NONE
        self._filter = build_profile_filter(self.method)
        self._removers: list[CALLBACK_TYPE] = []
        self._stabilized_cancel: CALLBACK_TYPE | None = None
        self._last_seen: float | None = None
        self.pending: PendingMeasurement | None = None

    # ── Properties ──────────────────────────────────────────────────────────

    @property
    def weight_sensor(self) -> str:
        """Return the scale weight sensor entity id."""
        return cast(str, self.config[CONF_WEIGHT_SENSOR])

    @property
    def mirror(self) -> bool:
        """Return True for a dedicated sensor mirrored as is (legacy mode)."""
        return self.method == PROFILE_METHOD_NONE and not self.config.get(
            CONF_HOLDER_WEIGHT_SENSOR
        )

    @property
    def notification_coordinator(self) -> NotificationCoordinator | None:
        """Return the domain notification coordinator, if any."""
        return cast(
            NotificationCoordinator | None,
            self.hass.data.get(DOMAIN, {}).get(NOTIFICATION_COORDINATOR),
        )

    def holder_weight(self) -> float | None:
        """Return the current weight of the person holding the pet, in kg."""
        holder_id = self.config.get(CONF_HOLDER_WEIGHT_SENSOR)
        if not holder_id:
            return None
        return state_to_kg(self.hass.states.get(holder_id))

    def nearest_candidate(
        self, candidates: list[Candidate]
    ) -> tuple[float, Candidate] | None:
        """Return (distance, candidate) closest to this pet's last weight."""
        current = self.coordinator.weight
        if current is None:
            return None
        return min(
            ((abs(c.weight - current), c) for c in candidates),
            key=lambda item: item[0],
        )

    # ── Lifecycle ───────────────────────────────────────────────────────────

    @callback
    def async_start(self) -> None:
        """Bootstrap the weight and subscribe to the sensors."""
        self._last_seen = state_to_kg(self.hass.states.get(self.weight_sensor))
        if self.mirror:
            self.coordinator.set_weight(self._mirror_value(), stamp=False)
        elif self.coordinator.weight is None and self.method == PROFILE_METHOD_NEAREST:
            initial = self.config.get(CONF_INITIAL_WEIGHT)
            if initial is not None:
                self.coordinator.set_weight(float(initial), stamp=False)

        self._removers.append(
            async_track_state_change_event(
                self.hass, [self.weight_sensor], self._on_weight_change
            )
        )
        if stabilized := self.config.get(CONF_STABILIZED_SENSOR):
            self._removers.append(
                async_track_state_change_event(
                    self.hass, [stabilized], self._on_stabilized_change
                )
            )
        if last_time := self.config.get(CONF_LAST_TIME_SENSOR):
            self._removers.append(
                async_track_state_change_event(
                    self.hass, [last_time], self._on_last_time_change
                )
            )
        if self.method == PROFILE_METHOD_NOTIFY:
            coordinator = self.notification_coordinator
            if coordinator is None:
                coordinator = NotificationCoordinator(self.hass)
                self.hass.data[DOMAIN][NOTIFICATION_COORDINATOR] = coordinator
            coordinator.register(self)

    @callback
    def unload(self) -> None:
        """Remove listeners and pending timers."""
        for remove in self._removers:
            remove()
        self._removers.clear()
        if self._stabilized_cancel is not None:
            self._stabilized_cancel()
            self._stabilized_cancel = None
        self.clear_pending()
        coordinator = self.notification_coordinator
        if coordinator is not None:
            coordinator.unregister(self.entry_id)
            if not coordinator.has_entries():
                coordinator.unload()
                self.hass.data[DOMAIN][NOTIFICATION_COORDINATOR] = None

    # ── Events ──────────────────────────────────────────────────────────────

    def _mirror_value(self) -> float | None:
        """Return the raw weight for the dedicated sensor mode."""
        state = self.hass.states.get(self.weight_sensor)
        if state is None or state.state in _INVALID_STATES:
            return None
        try:
            float(state.state)
        except ValueError:
            return None
        return state_to_kg(state)

    @callback
    def _on_weight_change(self, event: Event[EventStateChangedData]) -> None:
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]
        value = state_to_kg(new_state)
        restored = (
            value is not None
            and value == self._last_seen
            and (old_state is None or old_state.state in _INVALID_STATES)
        )
        if value is not None:
            self._last_seen = value

        if self.config.get(CONF_STABILIZED_SENSOR):
            # The measurement is read when the stabilized sensor turns ON.
            return

        if self.mirror:
            if not restored:
                self._run(
                    self.coordinator.async_set_weight(self._mirror_value(), stamp=True)
                )
            return

        if restored:
            _LOGGER.debug("[%s] Scale back with its last value — ignored", self.name)
            return
        if value is not None and value > 0:
            self._on_measurement(value)

    @callback
    def _on_stabilized_change(self, event: Event[EventStateChangedData]) -> None:
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]
        if (
            new_state is None
            or new_state.state != STATE_ON
            or old_state is None
            or old_state.state == STATE_ON
        ):
            return
        if self._stabilized_cancel is not None:
            self._stabilized_cancel()
        self._stabilized_cancel = async_call_later(
            self.hass, STABILIZED_READ_DELAY, self._read_stabilized
        )

    @callback
    def _read_stabilized(self, _now: datetime) -> None:
        self._stabilized_cancel = None
        if self.mirror:
            self._run(
                self.coordinator.async_set_weight(self._mirror_value(), stamp=True)
            )
            return
        value = state_to_kg(self.hass.states.get(self.weight_sensor))
        if value is not None and value > 0:
            self._on_measurement(value)

    @callback
    def _on_last_time_change(self, _event: Event[EventStateChangedData]) -> None:
        self._run(self.coordinator.async_refresh())

    # ── Measurement ─────────────────────────────────────────────────────────

    @callback
    def _on_measurement(self, gross: float) -> None:
        holder = self.holder_weight()
        candidates = weighing_candidates(gross, holder)
        _LOGGER.debug("[%s] Measurement %s", self.name, candidates)

        if self.method == PROFILE_METHOD_NOTIFY:
            self._start_pending(gross, holder)
            return

        candidate = self._filter.select(self, candidates)
        if candidate is not None:
            self._accept(candidate)

    @callback
    def _accept(self, candidate: Candidate) -> None:
        _LOGGER.debug("[%s] Accepted %s", self.name, candidate)
        self._run(
            self.coordinator.async_set_weight(
                candidate.weight, stamp=True, mode=candidate.mode
            )
        )

    @callback
    def _start_pending(self, gross: float, holder: float | None) -> None:
        self.clear_pending()
        self.pending = PendingMeasurement(
            gross=gross,
            holder=holder,
            cancel_timeout=async_call_later(
                self.hass, PENDING_MEASUREMENT_TIMEOUT, self._expire_pending
            ),
        )
        coordinator = self.notification_coordinator
        if coordinator is not None:
            coordinator.schedule_send()

    @callback
    def _expire_pending(self, _now: datetime) -> None:
        _LOGGER.debug("[%s] Pending measurement expired", self.name)
        self.pending = None

    @callback
    def clear_pending(self) -> None:
        """Forget the measurement waiting for a notification answer."""
        if self.pending is not None:
            self.pending.cancel_timeout()
            self.pending = None

    def notification_candidates(self) -> list[Candidate]:
        """Return the pending candidates allowed by the notification range."""
        if self.pending is None:
            return []
        w_min = self.config.get(CONF_NOTIFY_WEIGHT_MIN)
        w_max = self.config.get(CONF_NOTIFY_WEIGHT_MAX)
        candidates = weighing_candidates(self.pending.gross, self.pending.holder)
        return [c for c in candidates if _in_range(c.weight, w_min, w_max)]

    @callback
    def confirm(self, mode: str) -> bool:
        """Accept the pending measurement after a notification answer."""
        if self.pending is None:
            _LOGGER.debug("[%s] No pending measurement to confirm", self.name)
            return False
        candidates = weighing_candidates(self.pending.gross, self.pending.holder)
        candidate = next((c for c in candidates if c.mode == mode), None)
        self.clear_pending()
        if candidate is None:
            return False
        self._accept(candidate)
        return True

    def _run(self, coro: Coroutine[Any, Any, None]) -> None:
        self.hass.async_create_task(coro, eager_start=True)


# ---------------------------------------------------------------------------
# Notification coordinator (one per Home Assistant instance)
# ---------------------------------------------------------------------------


def action_id(entry_id: str, mode: str) -> str:
    """Return the notification action id for a pet and weighing mode."""
    return f"{NOTIFICATION_ACTION_PREFIX}_{entry_id}_{mode}".upper()


class NotificationCoordinator:
    """Send one interactive notification per device and route the answers."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize and listen to mobile app notification actions."""
        self._hass = hass
        self._handlers: dict[str, PetScaleHandler] = {}
        self._send_cancel: CALLBACK_TYPE | None = None
        self._remove_listener = hass.bus.async_listen(
            "mobile_app_notification_action", self._on_action
        )

    def register(self, handler: PetScaleHandler) -> None:
        """Register a pet using the notification method."""
        self._handlers[handler.entry_id] = handler

    def unregister(self, entry_id: str) -> None:
        """Unregister a pet."""
        self._handlers.pop(entry_id, None)

    def has_entries(self) -> bool:
        """Return True if at least one pet is registered."""
        return bool(self._handlers)

    def unload(self) -> None:
        """Stop listening and cancel a scheduled notification."""
        self._remove_listener()
        if self._send_cancel is not None:
            self._send_cancel()
            self._send_cancel = None
        self._handlers.clear()

    @callback
    def schedule_send(self) -> None:
        """Send the notification shortly, once every pet got the measurement."""
        if self._send_cancel is not None:
            return
        self._send_cancel = async_call_later(
            self._hass, NOTIFICATION_SEND_DELAY, self._send_now
        )

    @callback
    def _send_now(self, _now: datetime) -> None:
        self._send_cancel = None
        self._hass.async_create_task(self.async_send(), eager_start=True)

    async def async_send(self) -> None:
        """Send one notification per mobile device with the pending pets."""
        by_device: dict[str, list[tuple[PetScaleHandler, Candidate]]] = defaultdict(
            list
        )
        gross: float | None = None
        for handler in self._handlers.values():
            if handler.pending is None:
                continue
            gross = handler.pending.gross
            for candidate in handler.notification_candidates():
                by_device[handler.config[CONF_NOTIFY_DEVICE_ID]].append(
                    (handler, candidate)
                )

        if not by_device or gross is None:
            _LOGGER.debug("No pet matches the measurement — no notification")
            return

        texts = await self._async_texts()
        title = texts.get("weighing_title", "BodyPetScale — Who is on the scale?")
        message = _format(
            texts.get("weighing_message"), "New measurement: {weight:.1f} kg", gross
        )
        held_tpl = texts.get("action_held", "{name} (carried)")

        for device_id, items in by_device.items():
            service = await self._async_resolve_notify_service(device_id)
            if service is None:
                continue
            actions = [
                {
                    "action": action_id(handler.entry_id, candidate.mode),
                    "title": handler.name
                    if candidate.mode == WEIGHING_ALONE
                    else _format_name(held_tpl, handler.name),
                }
                for handler, candidate in items
            ]
            await self._hass.services.async_call(
                "notify",
                service,
                {
                    "title": title,
                    "message": message,
                    "data": {"tag": NOTIFICATION_TAG, "actions": actions},
                },
            )

    @callback
    def _on_action(self, event: Event) -> None:
        action = str(event.data.get("action", "")).upper()
        if not action.startswith(f"{NOTIFICATION_ACTION_PREFIX}_"):
            return
        match = next(
            (
                (handler, mode)
                for handler in self._handlers.values()
                for mode in (WEIGHING_ALONE, WEIGHING_HELD)
                if action == action_id(handler.entry_id, mode)
            ),
            None,
        )
        if match is None:
            _LOGGER.debug("Notification action %s matches no pet", action)
            return
        handler, mode = match
        if handler.confirm(mode):
            # One measurement belongs to one pet only
            for other in self._handlers.values():
                if other is not handler:
                    other.clear_pending()

    async def _async_texts(self) -> dict[str, str]:
        """Load the notification texts from the translation files."""
        translations_dir = os.path.join(os.path.dirname(__file__), "translations")
        language = self._hass.config.language

        def _load() -> dict[str, str]:
            for lang in (language, "en"):
                path = os.path.join(translations_dir, f"{lang}.json")
                if not os.path.exists(path):
                    continue
                try:
                    with open(path, encoding="utf-8") as file:
                        common = json.load(file).get("common", {})
                except OSError, ValueError:
                    continue
                if common:
                    return cast(dict[str, str], common)
            return {}

        return await self._hass.async_add_executor_job(_load)

    async def _async_resolve_notify_service(self, device_id: str) -> str | None:
        """Return the mobile_app notify service of a device."""
        device = dr.async_get(self._hass).async_get(device_id)
        if device is None:
            _LOGGER.warning("Notification device %s not found", device_id)
            return None

        services = self._hass.services.async_services().get("notify", {})
        mobile_services = [s for s in services if s.startswith("mobile_app_")]

        # 1. mobile_app identifier of the device
        for domain, identifier in device.identifiers:
            if domain != "mobile_app":
                continue
            for service in mobile_services:
                if service.lower() == f"mobile_app_{identifier}".lower():
                    return service

        # 2. unique_id of the device entities: "<device id>_<suffix>"
        for entity in er.async_entries_for_device(er.async_get(self._hass), device_id):
            unique_id = entity.unique_id or ""
            for service in mobile_services:
                if unique_id.startswith(service.removeprefix("mobile_app_")):
                    return service

        # 3. slugified device name, as the companion app does
        if device.name:
            normalized = unicodedata.normalize("NFKD", device.name.strip())
            slug = "".join(c for c in normalized if not unicodedata.combining(c))
            slug = "".join(c if c.isalnum() else "_" for c in slug.lower())
            while "__" in slug:
                slug = slug.replace("__", "_")
            candidate = f"mobile_app_{slug.strip('_')}"
            if candidate in mobile_services:
                return candidate

        _LOGGER.warning(
            "Cannot find the notify service of device '%s'. Check that the "
            "Home Assistant Companion App is installed on it",
            device.name,
        )
        return None


def _format(template: str | None, fallback: str, weight: float) -> str:
    try:
        return (template or fallback).format(weight=weight)
    except KeyError, IndexError, ValueError:
        return fallback.format(weight=weight)


def _format_name(template: str, name: str) -> str:
    try:
        return template.format(name=name)
    except KeyError, IndexError, ValueError:
        return f"{name} (carried)"
