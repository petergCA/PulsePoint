"""Config flow for PulsePoint."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    ObjectSelector,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import (
    PulsePointClient,
    PulsePointConnectionError,
    PulsePointDecryptError,
    PulsePointError,
    PulsePointInvalidAgency,
    PulsePointServiceUnavailable,
)
from .const import (
    CONF_AGENCY_ID,
    CONF_CLOSED_TTL,
    CONF_INCIDENT_TYPES,
    CONF_SCAN_INTERVAL,
    CONF_WATCH_RADIUS_KM,
    CONF_WATCHED_ADDRESSES,
    DEFAULT_CLOSED_TTL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_WATCH_RADIUS_KM,
    DOMAIN,
    INCIDENT_TYPES,
)

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_AGENCY_ID): str,
    }
)


async def _validate_agency(hass, agency_id: str) -> None:
    """Hit the API once to make sure the agency returns decryptable data."""
    session = async_get_clientsession(hass)
    client = PulsePointClient(session, agency_id)
    await client.async_get_incidents()


class PulsePointConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the user-facing setup flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            agency_id = user_input[CONF_AGENCY_ID].strip()
            await self.async_set_unique_id(f"agency_{agency_id}")
            self._abort_if_unique_id_configured()

            try:
                await _validate_agency(self.hass, agency_id)
            except PulsePointInvalidAgency:
                errors["base"] = "invalid_agency"
            except PulsePointDecryptError:
                errors["base"] = "decrypt_failed"
            # Must precede PulsePointConnectionError — it's a subclass. Keeps a
            # PulsePoint outage from reading like a bad agency ID.
            except PulsePointServiceUnavailable:
                errors["base"] = "service_unavailable"
            except PulsePointConnectionError:
                errors["base"] = "cannot_connect"
            except PulsePointError:
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"PulsePoint Agency {agency_id}",
                    data={CONF_AGENCY_ID: agency_id},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
            description_placeholders={
                "instructions": (
                    "Find your agency ID at https://web.pulsepoint.org — "
                    "pick your agency, open browser devtools, filter Network "
                    "by Fetch/XHR, and copy the `agencyid` param from the "
                    "request to api.pulsepoint.org."
                )
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return PulsePointOptionsFlow(config_entry)


class PulsePointOptionsFlow(config_entries.OptionsFlow):
    """Options flow: scan interval, type filter, watched addresses."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        current = self._entry.options or {}

        if user_input is not None:
            # Merge watched_addresses since that's edited in a sub-step
            merged = dict(current)
            merged.update(user_input)
            return self.async_create_entry(title="", data=merged)

        type_options = [
            {"value": code, "label": f"{code} — {name}"}
            for code, name in sorted(INCIDENT_TYPES.items(), key=lambda kv: kv[1])
        ]

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current.get(
                        CONF_SCAN_INTERVAL, int(DEFAULT_SCAN_INTERVAL.total_seconds())
                    ),
                ): NumberSelector(NumberSelectorConfig(
                    min=15, max=3600, step=1,
                    unit_of_measurement="s",
                    mode=NumberSelectorMode.BOX,
                )),
                vol.Optional(
                    CONF_INCIDENT_TYPES,
                    default=current.get(CONF_INCIDENT_TYPES, []),
                ): SelectSelector(SelectSelectorConfig(
                    options=type_options,
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )),
                vol.Optional(
                    CONF_WATCH_RADIUS_KM,
                    default=current.get(CONF_WATCH_RADIUS_KM, DEFAULT_WATCH_RADIUS_KM),
                ): NumberSelector(NumberSelectorConfig(
                    min=0.05, max=50.0, step=0.05,
                    unit_of_measurement="km",
                    mode=NumberSelectorMode.BOX,
                )),
                vol.Optional(
                    CONF_WATCHED_ADDRESSES,
                    default=current.get(CONF_WATCHED_ADDRESSES, []),
                ): ObjectSelector(),
                vol.Optional(
                    CONF_CLOSED_TTL,
                    default=current.get(CONF_CLOSED_TTL, DEFAULT_CLOSED_TTL),
                ): NumberSelector(NumberSelectorConfig(
                    min=0, max=1440, step=1,
                    unit_of_measurement="min",
                    mode=NumberSelectorMode.BOX,
                )),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
