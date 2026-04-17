"""Constants for the PulsePoint integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "pulsepoint"
MANUFACTURER = "PulsePoint Foundation"

# PulsePoint endpoint. The legacy `web.pulsepoint.org/DB/giba.php` host still
# works, but the newer `api.pulsepoint.org/v1/webapp` endpoint is what the
# current web app uses. We default to the new one and fall back to the old one.
API_URL = "https://api.pulsepoint.org/v1/webapp"
API_URL_LEGACY = "https://web.pulsepoint.org/DB/giba.php"

# Config entry keys
CONF_AGENCY_ID = "agency_id"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_INCIDENT_TYPES = "incident_types"
CONF_WATCHED_ADDRESSES = "watched_addresses"
CONF_WATCH_RADIUS_KM = "watch_radius_km"

# Defaults
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)
DEFAULT_WATCH_RADIUS_KM = 1.0

# Events fired on the HA bus
EVENT_NEW_INCIDENT = f"{DOMAIN}_new_incident"
EVENT_INCIDENT_CLEARED = f"{DOMAIN}_incident_cleared"
EVENT_WATCHED_ADDRESS_HIT = f"{DOMAIN}_watched_address_hit"


ATTR_AGENCY_ID = "agency_id"
ATTR_INCIDENT_ID = "incident_id"
ATTR_INCIDENT_TYPE = "incident_type"
ATTR_INCIDENT_TYPE_CODE = "incident_type_code"
ATTR_ADDRESS = "address"
ATTR_RECEIVED = "received"
ATTR_UNITS = "units"

# PulsePoint incident type codes -> human-readable name.
# This map is derived from the public PulsePoint incident type list and the
# community-maintained `incident_types.json` used by Podskio/pulsepoint and
# TrevorBagels/PulsepointScraperV2. Unknown codes fall back to the raw code.
INCIDENT_TYPES: dict[str, str] = {
    "AA": "Auto Aid",
    "AC": "Aircraft Crash",
    "AE": "Aircraft Emergency",
    "AES": "Aircraft Emergency Standby",
    "AI": "Arson Investigation",
    "AIA": "Automatic Alarm",
    "ALM": "Alarm",
    "AMB": "Ambulance",
    "AMBS": "Ambulance Standby",
    "AR": "Animal Rescue",
    "BLS": "Basic Life Support",
    "BP": "Burn Patient",
    "BT": "Bomb Threat",
    "CL": "Commercial Lockout",
    "CMA": "Carbon Monoxide Alarm",
    "CMI": "Carbon Monoxide Incident",
    "CP": "Community Policing",
    "CS": "Confined Space",
    "CSR": "Confined Space Rescue",
    "CVA": "Citizen Assist",
    "DA": "Door Alarm",
    "DROWN": "Drowning",
    "EE": "Elevator Emergency",
    "EM": "Emergency",
    "EQ": "Earthquake",
    "ER": "Emergency Response",
    "EX": "Explosion",
    "EXP": "Explosion",
    "FA": "Fire Alarm",
    "FIRE": "Fire",
    "FL": "Fuel Leak",
    "FWA": "Fire Works Activity",
    "GAS": "Gas Leak",
    "HAZ": "Hazardous Condition",
    "HMR": "Hazmat Response",
    "IFT": "Interfacility Transfer",
    "INV": "Investigation",
    "LA": "Lift Assist",
    "LR": "Ladder Request",
    "MA": "Medical Alarm",
    "MCI": "Multi Casualty Incident",
    "ME": "Medical Emergency",
    "MU": "Mutual Aid",
    "MVA": "Motor Vehicle Accident",
    "NEWS": "News",
    "NO": "Notification",
    "OA": "Outside Assist",
    "OF": "Outside Fire",
    "PA": "Police Assist",
    "PAA": "Police Activity Assist",
    "PI": "Person Injured",
    "PS": "Public Service",
    "RE": "Rescue",
    "RESC": "Rescue",
    "RR": "Rope Rescue",
    "SD": "Smoke Detector",
    "SH": "Smoke/Haze",
    "ST": "Strike Team/Task Force",
    "STBY": "Standby",
    "SUSP": "Suspicious Package",
    "TC": "Traffic Collision",
    "TCE": "Expanded Traffic Collision",
    "TCS": "Traffic Collision Involving Structure",
    "TE": "Technical Rescue",
    "TEST": "Test Incident",
    "TRF": "Traffic",
    "TRNG": "Training",
    "TRSF": "Transformer Fire",
    "WA": "Water Rescue",
    "WF": "Water Flow",
    "WFI": "Water Flow Investigation",
    "WR": "Water Rescue",
    "WSF": "Working Structure Fire",
}


def incident_type_name(code: str | None) -> str:
    """Translate an incident type code to a human name, or return the code."""
    if not code:
        return "Unknown"
    return INCIDENT_TYPES.get(code.upper(), code)
