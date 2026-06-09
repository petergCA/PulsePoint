"""PulsePoint switch entities.

Exposes a per-agency "Show incidents on map" switch that toggles the
visibility of the geo_location incident pins at runtime (no reload). The
switch owns no data of its own — it flips a flag on the coordinator and
fires a dispatcher signal that the geo_location platform listens for.

State is restored across restarts via RestoreEntity, so the map stays the
way the user left it.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DEFAULT_SHOW_MAP_PINS, DOMAIN, MANUFACTURER, signal_map_pins
from .coordinator import PulsePointCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PulsePointCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PulsePointMapPinsSwitch(coordinator, entry)])


class PulsePointMapPinsSwitch(RestoreEntity, SwitchEntity):
    """Show / hide PulsePoint incident pins on the built-in map."""

    _attr_has_entity_name = True
    _attr_name = "Show incidents on map"
    _attr_icon = "mdi:map-marker-radius"

    def __init__(
        self, coordinator: PulsePointCoordinator, entry: ConfigEntry
    ) -> None:
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_show_map_pins"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"PulsePoint {coordinator.agency_id}",
            manufacturer=MANUFACTURER,
            model="Incident Feed",
            configuration_url="https://web.pulsepoint.org/",
        )

    async def async_added_to_hass(self) -> None:
        """Restore the last known visibility and sync the geo platform."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            enabled = last_state.state == "on"
        else:
            enabled = DEFAULT_SHOW_MAP_PINS
        self._coordinator.map_pins_enabled = enabled
        # geo_location may have set up before us with the default value; push
        # the restored value so the map reflects it on startup.
        async_dispatcher_send(
            self.hass, signal_map_pins(self._entry.entry_id), enabled
        )

    @property
    def is_on(self) -> bool:
        return self._coordinator.map_pins_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set_enabled(False)

    async def _set_enabled(self, enabled: bool) -> None:
        self._coordinator.map_pins_enabled = enabled
        async_dispatcher_send(
            self.hass, signal_map_pins(self._entry.entry_id), enabled
        )
        self.async_write_ha_state()
