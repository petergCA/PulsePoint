"""PulsePoint sensor entities.

Creates a small, stable set of sensors per agency:
  * Active incidents (count)
  * Recent incidents (count)
  * Last incident type (state = human-readable type, attrs = full details)
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import Incident
from .const import DOMAIN, MANUFACTURER
from .coordinator import PulsePointCoordinator, _haversine_km

KM_PER_MILE = 1.60934


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PulsePointCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            PulsePointActiveCountSensor(coordinator, entry),
            PulsePointRecentCountSensor(coordinator, entry),
        ]
    )


class _Base(CoordinatorEntity[PulsePointCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: PulsePointCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"PulsePoint {coordinator.agency_id}",
            manufacturer=MANUFACTURER,
            model="Incident Feed",
            configuration_url="https://web.pulsepoint.org/",
        )


class PulsePointActiveCountSensor(_Base):
    _attr_name = "Active incidents"
    _attr_icon = "mdi:fire-truck"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "incidents"

    def __init__(self, coordinator: PulsePointCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_active_count"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("active", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        incidents: list[Incident] = self.coordinator.data.get("active") or []
        return {
            "agency_id": self.coordinator.agency_id,
            "by_type": self.coordinator.data.get("active_by_type", {}),
            "incidents": [_incident_dict(i, self.hass) for i in incidents],
        }


class PulsePointRecentCountSensor(_Base):
    _attr_name = "Recent incidents"
    _attr_icon = "mdi:history"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "incidents"
    _attr_entity_registry_enabled_default = False  # less interesting, off by default

    def __init__(self, coordinator: PulsePointCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_recent_count"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("recent", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        incidents: list[Incident] = self.coordinator.data.get("recent") or []
        return {
            "agency_id": self.coordinator.agency_id,
            "incidents": [_incident_dict(i, self.hass) for i in incidents],
        }



def _incident_dict(incident: Incident, hass: HomeAssistant) -> dict[str, Any]:
    distance_miles: float | None = None
    if incident.latitude is not None and incident.longitude is not None:
        km = _haversine_km(
            hass.config.latitude, hass.config.longitude,
            incident.latitude, incident.longitude,
        )
        distance_miles = round(km / KM_PER_MILE, 2)
    return {
        "incident_id": incident.id,
        "incident_type": incident.type_name,
        "incident_type_code": incident.type_code,
        "address": incident.address,
        "latitude": incident.latitude,
        "longitude": incident.longitude,
        "received": incident.received.isoformat() if incident.received else None,
        "units": incident.units,
        "distance_from_home_miles": distance_miles,
    }
