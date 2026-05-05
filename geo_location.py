"""PulsePoint geo_location entities — one per incident, shown on the built-in map.

Entities are created when an incident becomes active and stay on the map in a
"closed" state after the incident clears, for a configurable TTL (default 60 min).
"""
from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import Incident
from .const import CONF_CLOSED_TTL, DEFAULT_CLOSED_TTL, DOMAIN
from .coordinator import PulsePointCoordinator

GEO_SOURCE = "pulsepoint"

_TYPE_ICONS: dict[str, str] = {
    # Fire
    "SF": "mdi:fire",
    "WSF": "mdi:fire",
    "WF": "mdi:fire",
    "RF": "mdi:fire",
    "CF": "mdi:fire",
    "WCF": "mdi:fire",
    "WRF": "mdi:fire",
    "VEG": "mdi:fire",
    "WVEG": "mdi:fire",
    "FIRE": "mdi:fire",
    # Medical
    "ME": "mdi:ambulance",
    "CPR": "mdi:heart-pulse",
    "MCI": "mdi:ambulance",
    # Vehicle
    "TC": "mdi:car-crash",
    "TCP": "mdi:car-crash",
    "TCE": "mdi:car-crash",
    "VF": "mdi:car-emergency",
    # Hazmat / Gas
    "HMR": "mdi:biohazard",
    "GAS": "mdi:gas-cylinder",
    "CMA": "mdi:molecule-co2",
    # Rescue
    "RES": "mdi:lifebuoy",
    "WR": "mdi:lifebuoy",
    "TR": "mdi:lifebuoy",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PulsePointCoordinator = hass.data[DOMAIN][entry.entry_id]
    known: dict[str, PulsePointIncidentGeoEvent] = {}
    scheduled_removals: dict[str, Callable] = {}

    def _schedule_removal(inc_id: str) -> None:
        ttl_seconds = int(entry.options.get(CONF_CLOSED_TTL, DEFAULT_CLOSED_TTL)) * 60

        @callback
        def _do_remove(_now) -> None:
            scheduled_removals.pop(inc_id, None)
            entity = known.pop(inc_id, None)
            if entity is not None:
                hass.async_create_task(entity.async_remove())

        scheduled_removals[inc_id] = hass.async_call_later(ttl_seconds, _do_remove)

    def _cancel_removal(inc_id: str) -> None:
        cancel = scheduled_removals.pop(inc_id, None)
        if cancel is not None:
            cancel()

    @callback
    def _handle_update() -> None:
        if not coordinator.data:
            return
        active: list[Incident] = coordinator.data.get("active") or []
        active_map = {
            inc.id: inc for inc in active
            if inc.latitude is not None and inc.longitude is not None
        }

        new_entities: list[PulsePointIncidentGeoEvent] = []
        for inc_id, inc in active_map.items():
            if inc_id not in known:
                entity = PulsePointIncidentGeoEvent(coordinator, inc)
                known[inc_id] = entity
                new_entities.append(entity)
            else:
                entity = known[inc_id]
                if not entity.is_active:
                    # Incident reactivated — cancel the pending TTL removal.
                    _cancel_removal(inc_id)
                entity.update_incident(inc, is_active=True)

        # Detect newly-closed incidents (were active last poll, gone now).
        for inc_id, entity in list(known.items()):
            if inc_id not in active_map and entity.is_active:
                entity.update_incident(entity._incident, is_active=False)
                _schedule_removal(inc_id)

        if new_entities:
            async_add_entities(new_entities)

    @callback
    def _cleanup() -> None:
        for inc_id in list(scheduled_removals):
            _cancel_removal(inc_id)

    entry.async_on_unload(coordinator.async_add_listener(_handle_update))
    entry.async_on_unload(_cleanup)
    _handle_update()


class PulsePointIncidentGeoEvent(GeolocationEvent):
    """A single PulsePoint incident shown as a pin on the built-in map."""

    _attr_should_poll = False
    _attr_source = GEO_SOURCE

    def __init__(self, coordinator: PulsePointCoordinator, incident: Incident) -> None:
        self._incident = incident
        self._is_active = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_geo_{incident.id}"
        self._attr_name = incident.type_name
        self._attr_latitude = incident.latitude
        self._attr_longitude = incident.longitude
        self._attr_icon = _TYPE_ICONS.get(incident.type_code, "mdi:fire-truck")

    @property
    def state(self) -> str:
        return "active" if self._is_active else "closed"

    @property
    def is_active(self) -> bool:
        return self._is_active

    def update_incident(self, incident: Incident, is_active: bool) -> None:
        """Refresh incident snapshot and push updated state to HA."""
        self._incident = incident
        self._is_active = is_active
        self._attr_latitude = incident.latitude
        self._attr_longitude = incident.longitude
        self.async_write_ha_state()

    @property
    def distance(self) -> float | None:
        return None

    @property
    def extra_state_attributes(self) -> dict:
        inc = self._incident
        return {
            "incident_id": inc.id,
            "type_code": inc.type_code,
            "address": inc.address,
            "received": inc.received.isoformat() if inc.received else None,
            "cleared": inc.cleared.isoformat() if inc.cleared else None,
            "units": [u.get("UnitID") for u in inc.units if u.get("UnitID")],
        }
