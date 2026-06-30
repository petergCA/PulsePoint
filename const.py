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

# Headers sent with every PulsePoint request.
#
# PulsePoint's endpoints return an *empty* HTTP 200 body to clients that don't
# present a browser-like User-Agent. Home Assistant's shared aiohttp session
# sends a "HomeAssistant/<version>" User-Agent, which now gets an empty
# response and surfaced as a JSON decode error ("unexpected character: line 1
# column 1 (char 0)"). Sending these headers makes the request look like the
# web app. No API key or authentication is required.
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://web.pulsepoint.org/",
}

# Config entry keys
CONF_AGENCY_ID = "agency_id"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_INCIDENT_TYPES = "incident_types"
CONF_WATCHED_ADDRESSES = "watched_addresses"
CONF_WATCH_RADIUS_KM = "watch_radius_km"
CONF_CLOSED_TTL = "closed_ttl"
CONF_SHOW_MAP_PINS = "show_map_pins"

# Defaults
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)
DEFAULT_WATCH_RADIUS_KM = 1.0
# Minutes to keep a cleared incident's pin on the map in a "closed" state.
# 0 (default) removes the pin immediately when the incident clears.
DEFAULT_CLOSED_TTL = 0
DEFAULT_SHOW_MAP_PINS = True

# Events fired on the HA bus
EVENT_NEW_INCIDENT = f"{DOMAIN}_new_incident"
EVENT_INCIDENT_CLEARED = f"{DOMAIN}_incident_cleared"
EVENT_WATCHED_ADDRESS_HIT = f"{DOMAIN}_watched_address_hit"


def signal_map_pins(entry_id: str) -> str:
    """Dispatcher signal used to toggle map-pin visibility for one entry."""
    return f"{DOMAIN}_map_pins_{entry_id}"


ATTR_AGENCY_ID = "agency_id"
ATTR_INCIDENT_ID = "incident_id"
ATTR_INCIDENT_TYPE = "incident_type"
ATTR_INCIDENT_TYPE_CODE = "incident_type_code"
ATTR_ADDRESS = "address"
ATTR_RECEIVED = "received"
ATTR_UNITS = "units"

# PulsePoint incident type codes -> human-readable name.
# Sourced from https://www.pulsepoint.org/incident-types
# Unknown codes fall back to the raw code string.
INCIDENT_TYPES: dict[str, str] = {
    # Aid
    "AA":   "Auto Aid",
    "MU":   "Mutual Aid",
    "ST":   "Strike Team/Task Force",
    # Aircraft
    "AC":   "Aircraft Crash",
    "AE":   "Aircraft Emergency",
    "AES":  "Aircraft Emergency Standby",
    "LZ":   "Landing Zone",
    # Alarm
    "AED":  "AED Alarm",
    "CMA":  "Carbon Monoxide",
    "FA":   "Fire Alarm",
    "MA":   "Manual Alarm",
    "OA":   "Alarm",
    "SD":   "Smoke Detector",
    "TRBL": "Trouble Alarm",
    "WFA":  "Waterflow Alarm",
    # Assist
    "FL":   "Flooding",
    "LA":   "Lift Assist",
    "LR":   "Ladder Request",
    "PA":   "Police Assist",
    "PS":   "Public Service",
    "SH":   "Sheared Hydrant",
    # Explosion
    "EX":   "Explosion",
    "PE":   "Pipeline Emergency",
    "TE":   "Transformer Explosion",
    # Fire
    "AF":   "Appliance Fire",
    "CB":   "Controlled Burn/Prescribed Fire",
    "CF":   "Commercial Fire",
    "CHIM": "Chimney Fire",
    "EF":   "Extinguished Fire",
    "ELF":  "Electrical Fire",
    "FIRE": "Fire",
    "FULL": "Full Assignment",
    "GF":   "Refuse/Garbage Fire",
    "IF":   "Illegal Fire",
    "MF":   "Marine Fire",
    "OF":   "Outside Fire",
    "PF":   "Pole Fire",
    "RF":   "Residential Fire",
    "SF":   "Structure Fire",
    "TF":   "Tank Fire",
    "VEG":  "Vegetation Fire",
    "VF":   "Vehicle Fire",
    "WCF":  "Working Commercial Fire",
    "WF":   "Working Fire",
    "WRF":  "Working Residential Fire",
    "WSF":  "Confirmed Structure Fire",
    "WVEG": "Confirmed Vegetation Fire",
    # Hazard
    "BT":   "Bomb Threat",
    "EE":   "Electrical Emergency",
    "EM":   "Emergency",
    "ER":   "Emergency Response",
    "GAS":  "Gas Leak",
    "HC":   "Hazardous Condition",
    "HMR":  "Hazmat Response",
    "TD":   "Tree Down",
    "WE":   "Water Emergency",
    # Investigation
    "AI":   "Arson Investigation",
    "FWI":  "Fireworks Investigation",
    "HMI":  "Hazmat Investigation",
    "INV":  "Investigation",
    "OI":   "Odor Investigation",
    "SI":   "Smoke Investigation",
    # Lockout
    "CL":   "Commercial Lockout",
    "LO":   "Lockout",
    "RL":   "Residential Lockout",
    "VL":   "Vehicle Lockout",
    # Medical
    "CP":   "Community Paramedicine",
    "CPR":  "CPR Needed",
    "IFT":  "Interfacility Transfer",
    "MCI":  "Multi Casualty",
    "ME":   "Medical Emergency",
    # Natural Disaster
    "EQ":   "Earthquake",
    "FLW":  "Flood Warning",
    "TOW":  "Tornado Warning",
    "TSW":  "Tsunami Warning",
    "WX":   "Weather Incident",
    # Other
    "BP":   "Burn Permit",
    "CA":   "Community Activity",
    "FW":   "Fire Watch",
    "MC":   "Move-up/Cover",
    "NO":   "Notification",
    "STBY": "Standby",
    "TEST": "Test",
    "TRNG": "Training",
    # Rescue
    "AR":   "Animal Rescue",
    "CR":   "Cliff Rescue",
    "CSR":  "Confined Space Rescue",
    "EER":  "Elevator/Escalator Rescue",
    "ELR":  "Elevator Rescue",
    "IA":   "Industrial Accident",
    "IR":   "Ice Rescue",
    "RES":  "Rescue",
    "RR":   "Rope Rescue",
    "SC":   "Structural Collapse",
    "TNR":  "Trench Rescue",
    "TR":   "Technical Rescue",
    "USAR": "Urban Search and Rescue",
    "VS":   "Vessel Sinking",
    "WR":   "Water Rescue",
    # Vehicle
    "RTE":  "Railroad/Train Emergency",
    "TC":   "Traffic Collision",
    "TCP":  "Collision Involving Pedestrian",
    "TCE":  "Expanded Traffic Collision",
    "TCS":  "Collision Involving Structure",
    "TCT":  "Collision Involving Train",
    # Wires
    "PLE":  "Powerline Emergency",
    "WA":   "Wires Arcing",
    "WD":   "Wires Down",
    "WDA":  "Wires Down/Arcing",
}


def incident_type_name(code: str | None) -> str:
    """Translate an incident type code to a human name, or return the code."""
    if not code:
        return "Unknown"
    return INCIDENT_TYPES.get(code.upper(), code)
