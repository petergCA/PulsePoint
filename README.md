# PulsePoint — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![HA version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io)
[![GitHub Release](https://img.shields.io/github/v/release/petergCA/ha-pulsepoint)](https://github.com/petergCA/ha-pulsepoint/releases)

A custom Home Assistant integration that polls the [PulsePoint](https://www.pulsepoint.org) incident feed for one or more fire/EMS agencies and surfaces active and recent incidents as sensor entities with full attribute data.

---

## Features

- **Per-agency sensors** — Active incident count and Recent incident count, each carrying the full incident list as attributes
- **Rich incident attributes** — incident type, address, lat/lon, time received, responding units, and distance from home (in miles)
- **HA bus events** — fires `pulsepoint_new_incident`, `pulsepoint_incident_cleared`, and `pulsepoint_watched_address_hit` for use in automations
- **Watched addresses** — configurable list of addresses or geo-pins; fires a dedicated event when an incident occurs nearby
- **Incident type filter** — optionally restrict the feed to specific incident type codes (e.g. only fire and medical)
- **Configurable poll interval** — 15 s to 60 min
- **Custom Lovelace card** — clean incident viewer with distance slider, agency filter pills, and incident-type icons

---

## Requirements

| Requirement | Version |
|---|---|
| Home Assistant | 2024.1+ |
| Python | 3.11+ |
| `cryptography` | ≥ 41.0.0 (auto-installed) |

---

## Installation

### HACS (recommended)

1. Open HACS → **Integrations** → ⋮ → **Custom repositories**
2. Add `https://github.com/petergCA/ha-pulsepoint` as type **Integration**
3. Search for **PulsePoint** and install
4. Restart Home Assistant

### Manual

1. Copy the `custom_components/pulsepoint/` folder into your HA config directory
2. Restart Home Assistant

---

## Setup

### Finding your Agency ID

1. Open [web.pulsepoint.org](https://web.pulsepoint.org) and select your agency
2. Open browser DevTools → **Network** tab → filter by **Fetch/XHR**
3. Look for a request to `api.pulsepoint.org` — copy the `agencyid` query parameter (e.g. `ECA001`)

### Adding the integration

1. **Settings → Devices & Services → Add Integration → PulsePoint**
2. Enter the Agency ID and click **Submit**
3. Repeat for additional agencies — each gets its own config entry

---

## Configuration Options

After setup, click **Configure** on the integration card to adjust:

| Option | Default | Description |
|---|---|---|
| Poll interval (seconds) | `60` | How often to fetch the feed (15–3600 s) |
| Incident types | *(all)* | Whitelist of incident type codes; leave empty to show all |
| Watched-address radius (km) | `1.0` | Geo-proximity radius for watched addresses |
| Watched addresses | *(none)* | YAML list of locations to watch (see below) |

### Watched Addresses

Each entry can use a text address match, a lat/lon pin, or both:

```yaml
- name: Home
  address: "123 Main St"

- name: Work
  latitude: 38.5678
  longitude: -121.4321

- name: Parent's House
  address: "456 Oak Ave"
  latitude: 38.6000
  longitude: -121.5000
```

A `pulsepoint_watched_address_hit` event fires when a new incident matches any entry.

---

## Entities

Each configured agency creates the following entities:

### `sensor.<agency>_active_incidents`

| Field | Value |
|---|---|
| State | Count of currently active incidents |
| `agency_id` | Agency identifier |
| `by_type` | Dict of `{ "incident type": count }` |
| `incidents` | List of incident objects (see below) |

### `sensor.<agency>_recent_incidents`

| Field | Value |
|---|---|
| State | Count of recently closed incidents |
| `agency_id` | Agency identifier |
| `incidents` | List of incident objects |

> The Recent incidents sensor is disabled by default. Enable it in **Settings → Entities**.

### Incident object schema

Each entry in the `incidents` attribute list contains:

```yaml
incident_id: "12345678"
incident_type: "Structure Fire"
incident_type_code: "WSF"
address: "1234 Main Street, Sacramento, CA"
latitude: 38.5678
longitude: -121.4321
received: "2024-06-15T18:24:03+00:00"
units:
  - UnitID: "E12"
  - UnitID: "T4"
  - UnitID: "BC3"
distance_from_home_miles: 0.83
```

---

## Events

### `pulsepoint_new_incident`

Fired when a new incident appears in the active feed.

```yaml
agency_id: "ECA001"
incident_id: "12345678"
incident_type: "Structure Fire"
incident_type_code: "WSF"
address: "1234 Main Street"
latitude: 38.5678
longitude: -121.4321
received: "2024-06-15T18:24:03+00:00"
units: [...]
```

### `pulsepoint_incident_cleared`

Fired when an active incident drops off the feed. Same payload as above.

### `pulsepoint_watched_address_hit`

Fired when a new incident matches a watched address entry. Contains all fields above plus:

```yaml
name: "Home"          # name from your watched address config
match: "address"      # "address" or "geo"
distance_km: 0.42     # null for address-text matches
```

---

## Services

### `pulsepoint.refresh`

Force an immediate poll of all configured agencies.

```yaml
service: pulsepoint.refresh
```

---

## Automations

### Critical phone alert for a specific address

```yaml
automation:
  alias: "PulsePoint: Incident at 8305 Leda Ct"
  triggers:
    - trigger: event
      event_type: pulsepoint_new_incident
  conditions:
    - condition: template
      value_template: >-
        {{ '8305 leda' in (trigger.event.data.address | lower) }}
  actions:
    - action: notify.mobile_app_your_phone
      data:
        title: "PulsePoint Incident at 8305 Leda Ct"
        message: >-
          {{ trigger.event.data.incident_type }} at
          {{ trigger.event.data.address }}
          (received {{ trigger.event.data.received | as_timestamp | timestamp_custom('%I:%M %p') }})
        data:
          push:
            sound:
              name: default
              critical: 1
              volume: 1.0
```

### Alert when any incident occurs within 1 mile

```yaml
automation:
  alias: "PulsePoint: Nearby incident"
  triggers:
    - trigger: event
      event_type: pulsepoint_watched_address_hit
      event_data:
        name: "Home"
  actions:
    - action: notify.mobile_app_your_phone
      data:
        title: "Incident Near Home"
        message: >-
          {{ trigger.event.data.incident_type }} at
          {{ trigger.event.data.address }}
```

---

## Lovelace Card

A custom card is included at `www/pulsepoint-card.js`.

### Resource registration

**Settings → Dashboards → ⋮ → Resources → Add**

| Field | Value |
|---|---|
| URL | `/local/pulsepoint-card.js` |
| Resource type | JavaScript module |

### Card configuration

```yaml
type: custom:pulsepoint-card
title: Nearby Incidents          # optional, default "PulsePoint"
entities:
  - sensor.pulsepoint_eca001_active_incidents
  - sensor.pulsepoint_sac001_active_incidents   # add more agencies as needed
default_distance: 6              # slider starting position in miles (default: 6)
max_distance: 25                 # slider upper limit in miles (default: 25)
```

### Card features

- **Distance slider** — filters the list in real time; colour-coded distance badges (green < 1 mi · amber 1–3 mi · red > 3 mi)
- **Agency pills** — appear automatically when multiple agencies are configured; tap to show/hide each agency's incidents
- **Incident rows** — icon bubble colour-matched to incident category, type name, address, relative time, and responding units
- **Empty state** — clean message when no incidents match the current filter
- Incidents sorted closest-first
- Respects HA light and dark themes via CSS custom properties

### Supported incident type icons

| Category | Codes | Icon |
|---|---|---|
| Fire | `FIRE` `WSF` `OF` `TRSF` | 🔴 `mdi:fire` |
| Fire alarm | `FA` `AIA` `ALM` | 🟠 `mdi:alarm-light` |
| Smoke | `SD` `SH` | 🟠 `mdi:smoke` |
| Medical | `ME` `BLS` `MA` | 🔵 `mdi:medical-bag` |
| Ambulance | `AMB` `AMBS` | 🔵 `mdi:ambulance` |
| Traffic / MVA | `MVA` `TC` `TCE` `TCS` | 🟠 `mdi:car-emergency` |
| Hazmat | `HAZ` `HMR` `GAS` `FL` | 🟡 `mdi:hazard-lights` |
| Carbon monoxide | `CMA` `CMI` | 🟡 `mdi:molecule-co` |
| Explosion | `EX` `EXP` | 🔴 `mdi:explosion` |
| Water rescue | `WA` `WR` `DROWN` | 🔵 `mdi:waves` |
| Rescue | `RE` `RESC` `TE` `CS` | 🩵 `mdi:lifebuoy` |
| Police | `PA` `PAA` `CP` | 🟣 `mdi:police-badge` |
| Aircraft | `AC` `AE` `AES` | 🔴 `mdi:airplane-alert` |
| Earthquake | `EQ` | 🟣 `mdi:earth` |
| Other / unknown | — | ⚫ `mdi:alert-circle` |

---

## Incident Type Codes Reference

<details>
<summary>Full code list</summary>

| Code | Type |
|---|---|
| `AA` | Auto Aid |
| `AC` | Aircraft Crash |
| `AE` | Aircraft Emergency |
| `AES` | Aircraft Emergency Standby |
| `AIA` | Automatic Alarm |
| `ALM` | Alarm |
| `AMB` | Ambulance |
| `AMBS` | Ambulance Standby |
| `AR` | Animal Rescue |
| `BLS` | Basic Life Support |
| `BP` | Burn Patient |
| `BT` | Bomb Threat |
| `CMA` | Carbon Monoxide Alarm |
| `CMI` | Carbon Monoxide Incident |
| `CP` | Community Policing |
| `CS` | Confined Space |
| `CSR` | Confined Space Rescue |
| `CVA` | Citizen Assist |
| `DROWN` | Drowning |
| `EE` | Elevator Emergency |
| `EQ` | Earthquake |
| `EX` / `EXP` | Explosion |
| `FA` | Fire Alarm |
| `FIRE` | Fire |
| `FL` | Fuel Leak |
| `FWA` | Fireworks Activity |
| `GAS` | Gas Leak |
| `HAZ` | Hazardous Condition |
| `HMR` | Hazmat Response |
| `IFT` | Interfacility Transfer |
| `INV` | Investigation |
| `LA` | Lift Assist |
| `LR` | Ladder Request |
| `MA` | Medical Alarm |
| `MCI` | Multi Casualty Incident |
| `ME` | Medical Emergency |
| `MU` | Mutual Aid |
| `MVA` | Motor Vehicle Accident |
| `OA` | Outside Assist |
| `OF` | Outside Fire |
| `PA` | Police Assist |
| `PAA` | Police Activity Assist |
| `PI` | Person Injured |
| `PS` | Public Service |
| `RE` / `RESC` | Rescue |
| `RR` | Rope Rescue |
| `SD` | Smoke Detector |
| `SH` | Smoke/Haze |
| `ST` | Strike Team/Task Force |
| `SUSP` | Suspicious Package |
| `TC` | Traffic Collision |
| `TCE` | Expanded Traffic Collision |
| `TCS` | Traffic Collision Involving Structure |
| `TE` | Technical Rescue |
| `TRF` | Traffic |
| `TRSF` | Transformer Fire |
| `WA` / `WR` | Water Rescue |
| `WF` | Water Flow |
| `WFI` | Water Flow Investigation |
| `WSF` | Working Structure Fire |

</details>

---

## Disclaimer

This integration uses the **unofficial** PulsePoint API. PulsePoint may change or restrict access at any time. It is intended for personal awareness only — never rely on it for emergency response decisions.

---

## License

MIT
