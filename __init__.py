"""The PulsePoint integration."""
from __future__ import annotations

import logging
import os

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .const import DOMAIN
from .coordinator import PulsePointCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.GEO_LOCATION, Platform.SWITCH]

SERVICE_REFRESH = "refresh"

CARD_URL = "/pulsepoint/pulsepoint-card.js"


async def _async_register_card(hass: HomeAssistant) -> None:
    """Register the bundled Lovelace card as a dashboard resource."""
    lovelace = hass.data.get("lovelace")
    resources = getattr(lovelace, "resources", None)
    # YAML-mode resource collections are read-only (no async_create_item).
    # Duck-type instead of checking lovelace.mode — HA 2026.7 renamed that
    # attribute to resource_mode.
    if resources is None or not hasattr(resources, "async_create_item"):
        _LOGGER.warning(
            "Lovelace resources are YAML-managed; add %s as a dashboard "
            "resource manually",
            CARD_URL,
        )
        return

    if not resources.loaded:
        await resources.async_load()
        resources.loaded = True

    integration = await async_get_integration(hass, DOMAIN)
    versioned_url = f"{CARD_URL}?v={integration.version}"

    for item in resources.async_items():
        if item["url"].split("?")[0] == CARD_URL:
            if item["url"] != versioned_url:
                await resources.async_update_item(item["id"], {"url": versioned_url})
                _LOGGER.debug("Updated card resource to %s", versioned_url)
            return

    await resources.async_create_item({"res_type": "module", "url": versioned_url})
    _LOGGER.debug("Registered card resource %s", versioned_url)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the bundled Lovelace card and register it as a resource."""
    card_path = os.path.join(os.path.dirname(__file__), "pulsepoint-card.js")
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, card_path, cache_headers=True)]
    )
    await _async_register_card(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PulsePoint from a config entry."""
    coordinator = PulsePointCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    if coordinator.last_update_success is False:
        raise ConfigEntryNotReady("Initial PulsePoint fetch failed")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async def _handle_refresh(call: ServiceCall) -> None:
        """Force-refresh all loaded PulsePoint coordinators."""
        for coord in hass.data.get(DOMAIN, {}).values():
            await coord.async_request_refresh()

    # Register the service once (idempotent)
    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        hass.services.async_register(DOMAIN, SERVICE_REFRESH, _handle_refresh)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
            hass.data.pop(DOMAIN)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when the user changes options."""
    await hass.config_entries.async_reload(entry.entry_id)
