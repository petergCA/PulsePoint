# PulsePoint — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![HA version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io)
[![GitHub Release](https://img.shields.io/github/v/release/petergCA/PulsePoint)](https://github.com/petergCA/PulsePoint/releases)

A custom Home Assistant integration that polls the [PulsePoint](https://www.pulsepoint.org) incident feed for one or more fire/EMS agencies and surfaces active and recent incidents as sensors, live map pins, and Home Assistant bus events.

---

## Features

- **Per-agency sensors** — an active-incident count and a recent-incident count, each carrying the full incident list as attributes.
- **Live map pins** — each active incident is shown as a `geo_location` pin on Home Assistant's built-in map, with a category-matched icon. Pins are transient: they appear while an incident is active and are removed when it clears.
- **Per-agency map toggle** — a "Show incidents on map" switch turns the pins on or off at runtime, no reload required.
- **Configurable pin grace period** — optionally keep a cleared incident's pin on the map for a set number of minutes before it disappears (default: removed immediately).
- **Rich incident attributes** — incident type, address, latitude/longitude, time received, responding units, and distance from your Home Assistant location (in miles).
- **Home Assistant bus events** — fires `pulsepoint_new_incident`, `pulsepoint_incident_cleared`, and `pulsepoint_watched_address_hit` for use in automations.
- **Watched addresses** — a configurable list of addresses or geo-pins that fires a dedicated event when an incident occurs nearby.
- **Incident type filter** — optionally restrict the feed to specific incident type codes (e.g. only fire and medical).
- **Configurable poll interval** — 15 seconds to 60 minutes.
- **Multiple agencies** — add as many agencies as you like; each gets its own device, entities, and options.

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

1. Open HACS → **Integrations** → ⋮ → **Custom repositories**.
2. Add `https://github.com/petergCA/PulsePoint` as type **Integration**.
3. Search for **PulsePoint** and install.
4. Restart Home Assistant.

### Manual

1. Create the folder `custom_components/pulsepoint/` in your Home Assistant config directory.
2. Copy the contents of this repository into that folder (the integration files live in the repository root).
3. Restart Home Assistant.

---

## Setup

### Finding your Agency ID

1. Open [web.pulsepoint.org](https://web.pulsepoint.org) and select your agency.
2. Open your browser's DevTools → **Network** tab → filter by **Fetch/XHR**.
3. Look for a request to `api.pulsepoint.org` and copy the `agencyid` query parameter.

### Adding the integration

1. **Settings → Devices & Services → Add Integration → PulsePoint**.
2. Enter the Agency ID and click **Submit**.
3. Repeat for additional agencies — each gets its own config entry.

---

## Configuration Options

After setup, click **Configure** on the integration card (this is per agency) to adjust:

| Option | Default | Description |
|---|---|---|
| Poll interval (seconds) | `60` | How often to fetch the feed (15–3600 s). |
| Incident types | *(all)* | Whitelist of incident type codes; leave empty to show all. |
| Watched-address radius (km) | `1.0` | Geo-proximity radius for watched addresses (0.05–50 km). |
| Watched addresses | *(none)* | List of locations to watch (see below). |
| Map pin grace period (minutes) | `0` | How long a cleared incident's pin stays on the map before it's removed. `0` removes it immediately (0–1440 min). |

### Watched Addresses

Each entry can use a text address match, a latitude/longitude pin, or both:

```yaml
- name: Home
  address: "123 Main St"

- name: Work
  latitude: 38.0000
  longitude: -121.0000

- name: Family
  address: "456 Oak Ave"
  latitude: 38.1000
  longitude: -121.1000
```

A `pulsepoint_watched_address_hit` event fires when a new incident matches any entry — either because the incident address contains the entry's `address` text, or because the incident falls within the watched-address radius of the entry's latitude/longitude.

---

## Entities

Each configured agency creates the following entities, grouped under a single PulsePoint device.

### `sensor.<agency>_active_incidents`

| Field | Value |
|---|---|
| State | Count of currently active incidents |
| `agency_id` | Agency identifier |
| `by_type` | Dict of `{ "incident type": count }` |
| `incidents` | List of incident objects (see schema below) |

### `sensor.<agency>_recent_incidents`

| Field | Value |
|---|---|
| State | Count of recently closed incidents |
| `agency_id` | Agency identifier |
| `incidents` | List of incident objects |

> The Recent incidents sensor is disabled by default. Enable it in **Settings → Devices & Services → Entities** if you want it.

### `switch.<agency>_show_incidents_on_map`

Turns the agency's map pins on or off at runtime (no reload). Defaults to **on**, and the last state is restored across restarts.

### `geo_location.<incident_type>` (map pins)

One transient pin per active incident — see [Map Pins](#map-pins) below.

### Incident object schema

Each entry in an `incidents` attribute list contains:

```yaml
incident_id: "12345678"
incident_type: "Structure Fire"
incident_type_code: "SF"
address: "1234 Main Street, Anytown, CA"
latitude: 38.0000
longitude: -121.0000
received: "2024-06-15T18:24:03+00:00"
units:
  - UnitID: "E12"
  - UnitID: "T4"
  - UnitID: "BC3"
distance_from_home_miles: 0.83
```

`distance_from_home_miles` is measured from your Home Assistant configured location.

---

## Map Pins

When **Show incidents on map** is on, each active incident appears as a `geo_location` pin on Home Assistant's **built-in map** (the default Map dashboard, or any [Map card](https://www.home-assistant.io/dashboards/map/) you add). No custom card is required.

Pins are **transient**: a pin is created when its incident becomes active and is removed when the incident clears, so the map reflects only what's currently happening. By default a cleared incident's pin is removed immediately; set a positive **Map pin grace period** in the agency's options to keep recently-cleared pins visible for a while.

Each pin's state is `active` (or `closed` during a grace period), and it carries `incident_id`, `type_code`, `address`, `received`, `cleared`, and `units` attributes.

### Pin icons

| Icon | Incident type codes |
|---|---|
| `mdi:fire` | `FIRE` `SF` `WSF` `WF` `RF` `CF` `WCF` `WRF` `VEG` `WVEG` |
| `mdi:ambulance` | `ME` `MCI` |
| `mdi:heart-pulse` | `CPR` |
| `mdi:car-crash` | `TC` `TCP` `TCE` |
| `mdi:car-emergency` | `VF` |
| `mdi:biohazard` | `HMR` |
| `mdi:gas-cylinder` | `GAS` |
| `mdi:molecule-co2` | `CMA` |
| `mdi:lifebuoy` | `RES` `WR` `TR` |
| `mdi:fire-truck` | *(any other code)* |

---

## Events

### `pulsepoint_new_incident`

Fired when a new incident appears in the active feed.

```yaml
agency_id: "12345"
incident_id: "12345678"
incident_type: "Structure Fire"
incident_type_code: "SF"
address: "1234 Main Street"
latitude: 38.0000
longitude: -121.0000
received: "2024-06-15T18:24:03+00:00"
units: [...]
```

### `pulsepoint_incident_cleared`

Fired when an active incident drops off the feed. Same payload as above.

### `pulsepoint_watched_address_hit`

Fired when a new incident matches a watched-address entry. Contains all fields above plus:

```yaml
name: "Home"          # name from your watched-address config
match: "address"      # "address" (text match) or "geo" (within radius)
distance_km: 0.42     # great-circle distance for geo matches; null for text matches
```

---

## Services

### `pulsepoint.refresh`

Force an immediate poll of all configured agencies.

```yaml
action: pulsepoint.refresh
```

---

## Automation Examples

### Critical phone alert for a watched address

```yaml
automation:
  alias: "PulsePoint: Incident at a watched address"
  triggers:
    - trigger: event
      event_type: pulsepoint_new_incident
  conditions:
    - condition: template
      value_template: >-
        {{ '123 main st' in (trigger.event.data.address | lower) }}
  actions:
    - action: notify.mobile_app_your_phone
      data:
        title: "PulsePoint Incident Nearby"
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

### Alert when an incident occurs near a watched location

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

## Incident Type Codes Reference

The integration maps PulsePoint type codes to human-readable names; unknown codes fall back to the raw code.

<details>
<summary>Full code list</summary>

| Code | Type |
|---|---|
| `AA` | Auto Aid |
| `MU` | Mutual Aid |
| `ST` | Strike Team/Task Force |
| `AC` | Aircraft Crash |
| `AE` | Aircraft Emergency |
| `AES` | Aircraft Emergency Standby |
| `LZ` | Landing Zone |
| `AED` | AED Alarm |
| `CMA` | Carbon Monoxide |
| `FA` | Fire Alarm |
| `MA` | Manual Alarm |
| `OA` | Alarm |
| `SD` | Smoke Detector |
| `TRBL` | Trouble Alarm |
| `WFA` | Waterflow Alarm |
| `FL` | Flooding |
| `LA` | Lift Assist |
| `LR` | Ladder Request |
| `PA` | Police Assist |
| `PS` | Public Service |
| `SH` | Sheared Hydrant |
| `EX` | Explosion |
| `PE` | Pipeline Emergency |
| `TE` | Transformer Explosion |
| `AF` | Appliance Fire |
| `CB` | Controlled Burn/Prescribed Fire |
| `CF` | Commercial Fire |
| `CHIM` | Chimney Fire |
| `EF` | Extinguished Fire |
| `ELF` | Electrical Fire |
| `FIRE` | Fire |
| `FULL` | Full Assignment |
| `GF` | Refuse/Garbage Fire |
| `IF` | Illegal Fire |
| `MF` | Marine Fire |
| `OF` | Outside Fire |
| `PF` | Pole Fire |
| `RF` | Residential Fire |
| `SF` | Structure Fire |
| `TF` | Tank Fire |
| `VEG` | Vegetation Fire |
| `VF` | Vehicle Fire |
| `WCF` | Working Commercial Fire |
| `WF` | Working Fire |
| `WRF` | Working Residential Fire |
| `WSF` | Confirmed Structure Fire |
| `WVEG` | Confirmed Vegetation Fire |
| `BT` | Bomb Threat |
| `EE` | Electrical Emergency |
| `EM` | Emergency |
| `ER` | Emergency Response |
| `GAS` | Gas Leak |
| `HC` | Hazardous Condition |
| `HMR` | Hazmat Response |
| `TD` | Tree Down |
| `WE` | Water Emergency |
| `AI` | Arson Investigation |
| `FWI` | Fireworks Investigation |
| `HMI` | Hazmat Investigation |
| `INV` | Investigation |
| `OI` | Odor Investigation |
| `SI` | Smoke Investigation |
| `CL` | Commercial Lockout |
| `LO` | Lockout |
| `RL` | Residential Lockout |
| `VL` | Vehicle Lockout |
| `CP` | Community Paramedicine |
| `CPR` | CPR Needed |
| `IFT` | Interfacility Transfer |
| `MCI` | Multi Casualty |
| `ME` | Medical Emergency |
| `EQ` | Earthquake |
| `FLW` | Flood Warning |
| `TOW` | Tornado Warning |
| `TSW` | Tsunami Warning |
| `WX` | Weather Incident |
| `BP` | Burn Permit |
| `CA` | Community Activity |
| `FW` | Fire Watch |
| `MC` | Move-up/Cover |
| `NO` | Notification |
| `STBY` | Standby |
| `TEST` | Test |
| `TRNG` | Training |
| `AR` | Animal Rescue |
| `CR` | Cliff Rescue |
| `CSR` | Confined Space Rescue |
| `EER` | Elevator/Escalator Rescue |
| `ELR` | Elevator Rescue |
| `IA` | Industrial Accident |
| `IR` | Ice Rescue |
| `RES` | Rescue |
| `RR` | Rope Rescue |
| `SC` | Structural Collapse |
| `TNR` | Trench Rescue |
| `TR` | Technical Rescue |
| `USAR` | Urban Search and Rescue |
| `VS` | Vessel Sinking |
| `WR` | Water Rescue |
| `RTE` | Railroad/Train Emergency |
| `TC` | Traffic Collision |
| `TCP` | Collision Involving Pedestrian |
| `TCE` | Expanded Traffic Collision |
| `TCS` | Collision Involving Structure |
| `TCT` | Collision Involving Train |
| `PLE` | Powerline Emergency |
| `WA` | Wires Arcing |
| `WD` | Wires Down |
| `WDA` | Wires Down/Arcing |

</details>

---

## Disclaimer

This integration uses the **unofficial** PulsePoint API. PulsePoint may change or restrict access at any time. It is intended for personal awareness only — never rely on it for emergency response decisions.

---

## License

MIT
