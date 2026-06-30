"""Low-level client for the (unofficial) PulsePoint incident feed.

The PulsePoint web endpoint returns an AES-256-CBC-encrypted JSON payload.
The key derivation and password construction here matches the scheme used by
the PulsePoint web client and is documented in several community projects
(Davnit/pulse.py gist, Podskio/pulsepoint, TrevorBagels/PulsepointScraperV2).

This is an *unofficial* interface. PulsePoint may change the scheme at any
time; we handle that by raising :class:`PulsePointDecryptError` so the caller
can surface a clean error in the UI instead of crashing.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import aiohttp
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .const import API_URL, API_URL_LEGACY, REQUEST_HEADERS, incident_type_name

_LOGGER = logging.getLogger(__name__)


class PulsePointError(Exception):
    """Base exception for PulsePoint client errors."""


class PulsePointConnectionError(PulsePointError):
    """Raised when the HTTP request fails."""


class PulsePointDecryptError(PulsePointError):
    """Raised when the encrypted payload can't be decoded.

    This usually means PulsePoint has changed their encoding scheme.
    """


class PulsePointInvalidAgency(PulsePointError):
    """Raised when the agency ID returns no data."""


@dataclass
class Incident:
    """A normalized PulsePoint incident."""

    id: str
    type_code: str
    type_name: str
    address: str
    latitude: float | None
    longitude: float | None
    received: datetime | None
    cleared: datetime | None
    is_active: bool
    units: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


def _build_password() -> str:
    """Reconstruct the password PulsePoint's web client uses.

    The web client assembles this from pieces of the string "CommonIncidents"
    plus a few hardcoded tokens. Keeping the obfuscation verbatim so any
    future tweaks by PulsePoint can be diffed cleanly.
    """
    e = "CommonIncidents"
    return e[13] + e[1] + e[2] + "brady" + "5" + "r" + e.lower()[6] + e[5] + "gs"


def _derive_key(password: str, salt: bytes, length: int = 32) -> bytes:
    """OpenSSL-compatible MD5-based key derivation (EVP_BytesToKey)."""
    key = b""
    block = b""
    while len(key) < length:
        hasher = hashlib.md5()  # noqa: S324 - interop with OpenSSL EVP scheme
        if block:
            hasher.update(block)
        hasher.update(password.encode())
        hasher.update(salt)
        block = hasher.digest()
        key += block
    return key[:length]


def _decrypt_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Decrypt a `{ct, iv, s}` envelope returned by the PulsePoint API."""
    try:
        ct = base64.b64decode(payload["ct"])
        iv = bytes.fromhex(payload["iv"])
        salt = bytes.fromhex(payload["s"])
    except (KeyError, ValueError, TypeError) as err:
        raise PulsePointDecryptError(f"Malformed envelope: {err}") from err

    key = _derive_key(_build_password(), salt)

    try:
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ct) + decryptor.finalize()
    except Exception as err:  # noqa: BLE001 - cryptography raises a grab bag
        raise PulsePointDecryptError(f"AES decryption failed: {err}") from err

    # The plaintext is a JSON-encoded string wrapped in quotes and with PKCS#7
    # padding bytes. Strip the leading byte and the padding up to the last
    # closing quote, then un-escape the inner quotes.
    try:
        inner = plaintext[1 : plaintext.rindex(b'"')].decode("utf-8", errors="replace")
        inner = inner.replace(r"\"", r'"')
        return json.loads(inner)
    except (ValueError, json.JSONDecodeError) as err:
        raise PulsePointDecryptError(f"Could not parse plaintext JSON: {err}") from err


def _parse_dt(value: Any) -> datetime | None:
    """Parse a PulsePoint timestamp (e.g. `2024-01-15T18:24:03Z`) safely."""
    if not value or not isinstance(value, str):
        return None
    try:
        # fromisoformat in 3.11+ handles the trailing Z, but be defensive
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _to_float(value: Any) -> float | None:
    """Best-effort float conversion."""
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_incident(raw: dict[str, Any], *, is_active: bool) -> Incident | None:
    """Convert a raw incident dict into a typed Incident."""
    incident_id = raw.get("ID") or raw.get("id")
    if not incident_id:
        return None
    code = raw.get("PulsePointIncidentCallType") or raw.get("type") or ""
    return Incident(
        id=str(incident_id),
        type_code=code,
        type_name=incident_type_name(code),
        address=raw.get("FullDisplayAddress") or raw.get("address") or "",
        latitude=_to_float(raw.get("Latitude") or raw.get("latitude")),
        longitude=_to_float(raw.get("Longitude") or raw.get("longitude")),
        received=_parse_dt(raw.get("CallReceivedDateTime") or raw.get("receivedTime")),
        cleared=_parse_dt(raw.get("ClosedDateTime") or raw.get("clearedTime")),
        is_active=is_active,
        units=raw.get("Unit") or raw.get("units") or [],
        raw=raw,
    )


class PulsePointClient:
    """Async client that fetches and decodes the incident feed."""

    def __init__(self, session: aiohttp.ClientSession, agency_id: str) -> None:
        self._session = session
        self._agency_id = agency_id

    @property
    def agency_id(self) -> str:
        return self._agency_id

    async def async_get_incidents(self) -> tuple[list[Incident], list[Incident]]:
        """Fetch the feed, returning (active, recent)."""
        data = await self._fetch_raw()
        try:
            decrypted = _decrypt_payload(data)
        except PulsePointDecryptError:
            raise
        except Exception as err:  # noqa: BLE001
            raise PulsePointDecryptError(str(err)) from err

        incidents_block = decrypted.get("incidents") or {}
        active_raw = incidents_block.get("active") or []
        recent_raw = incidents_block.get("recent") or []

        if not isinstance(active_raw, list) or not isinstance(recent_raw, list):
            raise PulsePointInvalidAgency(
                f"Agency {self._agency_id} returned no incident lists"
            )

        active = [i for i in (_normalize_incident(r, is_active=True) for r in active_raw) if i]
        recent = [i for i in (_normalize_incident(r, is_active=False) for r in recent_raw) if i]
        return active, recent

    async def _fetch_raw(self) -> dict[str, Any]:
        """Fetch the encrypted `{ct, iv, s}` envelope from PulsePoint.

        Tries the modern endpoint first, then the legacy one. PulsePoint returns
        an *empty* HTTP 200 body to clients that don't present a browser-like
        User-Agent, so we send :data:`REQUEST_HEADERS` explicitly to override the
        shared HA session's "HomeAssistant/<version>" User-Agent (which now gets
        an empty body and previously surfaced as a "char 0" JSON decode error).

        Each endpoint is isolated: a non-200 status, an empty body, a non-JSON
        body, or an unexpected JSON shape is recorded and we move on to the next
        endpoint rather than letting one bad endpoint abort setup. Only if every
        endpoint fails do we raise, with the per-endpoint diagnostics attached.
        """
        endpoints = [
            (API_URL, {"resource": "incidents", "agencyid": self._agency_id}),
            (API_URL_LEGACY, {"agency_id": self._agency_id}),
        ]
        errors: list[str] = []
        for url, params in endpoints:
            try:
                async with self._session.get(
                    url,
                    params=params,
                    headers=REQUEST_HEADERS,
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp:
                    status = resp.status
                    body = await resp.text()
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                errors.append(f"{url}: {type(err).__name__}: {err}")
                _LOGGER.debug("PulsePoint fetch from %s failed: %s", url, err)
                continue

            if status != 200:
                errors.append(f"{url}: HTTP {status}")
                _LOGGER.debug("PulsePoint %s returned HTTP %s", url, status)
                continue

            stripped = body.strip()
            if not stripped:
                errors.append(f"{url}: empty response body")
                _LOGGER.debug(
                    "PulsePoint %s returned an empty body (User-Agent gating?)", url
                )
                continue

            try:
                payload = json.loads(stripped)
            except ValueError as err:
                snippet = stripped[:80].replace("\n", " ")
                errors.append(f"{url}: non-JSON body ({err})")
                _LOGGER.debug("PulsePoint %s returned non-JSON: %s", url, snippet)
                continue

            if isinstance(payload, dict) and {"ct", "iv", "s"} <= payload.keys():
                _LOGGER.debug("PulsePoint fetched encrypted envelope from %s", url)
                return payload

            shape = (
                f"keys={sorted(payload)[:6]}"
                if isinstance(payload, dict)
                else type(payload).__name__
            )
            errors.append(f"{url}: unexpected JSON shape ({shape})")
            _LOGGER.debug("Unexpected payload from %s: %r", url, payload)

        raise PulsePointConnectionError(
            "All PulsePoint endpoints failed: " + "; ".join(errors)
        )
