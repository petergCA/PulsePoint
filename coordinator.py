"""DataUpdateCoordinator for PulsePoint.

Polls the agency feed on a configurable interval, diffs against the previous
snapshot, and fires HA bus events for new / cleared incidents. Also handles
watched-address matching (both exact text match and geo-proximity).
"""
from __future__ import annotations

import logging
import math
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    Incident,
    PulsePointClient,
    PulsePointConnectionError,
    PulsePointDecryptError,
    PulsePointError,
)
from .const import (
    ATTR_ADDRESS,
    ATTR_AGENCY_ID,
    ATTR_INCIDENT_ID,
    ATTR_INCIDENT_TYPE,
    ATTR_INCIDENT_TYPE_CODE,
    ATTR_RECEIVED,
    ATTR_UNITS,
    CONF_AGENCY_ID,
    CONF_INCIDENT_TYPES,
    CONF_SCAN_INTERVAL,
    CONF_WATCH_RADIUS_KM,
    CONF_WATCHED_ADDRESSES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_WATCH_RADIUS_KM,
    DOMAIN,
    EVENT_INCIDENT_CLEARED,
    EVENT_NEW_INCIDENT,
    EVENT_WATCHED_ADDRESS_HIT,
)

_LOGGER = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0088


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points in kilometers."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


class PulsePointCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Pulls incident data and fans out events/signals."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self._agency_id: str = entry.data[CONF_AGENCY_ID]

        options = entry.options or {}
        scan_seconds = options.get(
            CONF_SCAN_INTERVAL, int(DEFAULT_SCAN_INTERVAL.total_seconds())
        )
        self._type_filter: set[str] = {
            t.upper() for t in options.get(CONF_INCIDENT_TYPES, []) if t
        }
        # Watched addresses are a list of dicts: {name, address?, latitude?, longitude?}
        self._watched: list[dict[str, Any]] = options.get(CONF_WATCHED_ADDRESSES, []) or []
        self._watch_radius_km: float = float(
            options.get(CONF_WATCH_RADIUS_KM, DEFAULT_WATCH_RADIUS_KM)
        )

        self._client = PulsePointClient(async_get_clientsession(hass), self._agency_id)
        self._known_active: dict[str, Incident] = {}

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({self._agency_id})",
            update_interval=timedelta(seconds=scan_seconds),
        )

    @property
    def agency_id(self) -> str:
        return self._agency_id

    def _matches_filter(self, incident: Incident) -> bool:
        """Return True if the incident passes the user's type filter."""
        if not self._type_filter:
            return True
        return incident.type_code.upper() in self._type_filter

    def _check_watched(self, incident: Incident) -> list[dict[str, Any]]:
        """Return a list of watched-address entries this incident matches."""
        hits: list[dict[str, Any]] = []
        incident_addr = (incident.address or "").casefold()
        for watch in self._watched:
            name = watch.get("name") or watch.get("address") or "watched"

            # Text match: substring on the display address (case-insensitive)
            target_addr = (watch.get("address") or "").casefold().strip()
            if target_addr and target_addr in incident_addr:
                hits.append({"name": name, "match": "address", "distance_km": None})
                continue

            # Geo match: within radius of a lat/lon pin
            wlat = watch.get("latitude")
            wlon = watch.get("longitude")
            if (
                wlat is not None
                and wlon is not None
                and incident.latitude is not None
                and incident.longitude is not None
            ):
                dist = _haversine_km(
                    float(wlat), float(wlon), incident.latitude, incident.longitude
                )
                if dist <= self._watch_radius_km:
                    hits.append(
                        {"name": name, "match": "geo", "distance_km": round(dist, 3)}
                    )
        return hits

    def _event_payload(self, incident: Incident) -> dict[str, Any]:
        return {
            ATTR_AGENCY_ID: self._agency_id,
            ATTR_INCIDENT_ID: incident.id,
            ATTR_INCIDENT_TYPE: incident.type_name,
            ATTR_INCIDENT_TYPE_CODE: incident.type_code,
            ATTR_ADDRESS: incident.address,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
            ATTR_RECEIVED: incident.received.isoformat() if incident.received else None,
            ATTR_UNITS: incident.units,
        }

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            active, recent = await self._client.async_get_incidents()
        except PulsePointDecryptError as err:
            raise UpdateFailed(
                f"PulsePoint decryption failed (the encoding may have changed): {err}"
            ) from err
        except PulsePointConnectionError as err:
            raise UpdateFailed(f"PulsePoint connection error: {err}") from err
        except PulsePointError as err:
            raise UpdateFailed(f"PulsePoint error: {err}") from err

        filtered_active = [i for i in active if self._matches_filter(i)]
        filtered_recent = [i for i in recent if self._matches_filter(i)]

        new_active: dict[str, Incident] = {i.id: i for i in filtered_active}

        # Fire events for new incidents
        for incident_id, incident in new_active.items():
            if incident_id not in self._known_active:
                _LOGGER.debug("New incident %s: %s", incident_id, incident.type_name)
                self.hass.bus.async_fire(EVENT_NEW_INCIDENT, self._event_payload(incident))

                for hit in self._check_watched(incident):
                    payload = self._event_payload(incident)
                    payload.update(hit)
                    self.hass.bus.async_fire(EVENT_WATCHED_ADDRESS_HIT, payload)

        # Fire events for cleared incidents
        for incident_id, incident in self._known_active.items():
            if incident_id not in new_active:
                _LOGGER.debug("Incident cleared: %s", incident_id)
                self.hass.bus.async_fire(
                    EVENT_INCIDENT_CLEARED, self._event_payload(incident)
                )

        self._known_active = new_active

        return {
            "active": filtered_active,
            "recent": filtered_recent,
            "active_by_type": _bucket_by_type(filtered_active),
        }


def _bucket_by_type(incidents: list[Incident]) -> dict[str, int]:
    out: dict[str, int] = {}
    for i in incidents:
        out[i.type_name] = out.get(i.type_name, 0) + 1
    return out
