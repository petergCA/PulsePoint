(() => {
  'use strict';

  const CARD_VERSION = '0.2.0';

  // ── User-configurable options and their defaults ───────────────────────────
  const DEFAULTS = {
    title: 'PulsePoint',
    default_distance: 6,          // mi — initial slider position / fixed radius
    max_distance: 25,             // mi — slider upper bound
    show_distance_slider: true,   // hide to pin the radius at default_distance
    show_agency_filter: true,     // agency toggle chips (multi-agency only)
    show_time: true,              // "21m ago" in the meta line
    show_units: true,             // responding units in the meta line
    sort_by: 'distance',          // 'distance' | 'newest'
    max_incidents: 0,             // 0 = unlimited; else collapse with "Show more"
    highlight_recent_minutes: 10, // pulse-dot incidents newer than this; 0 = off
  };

  // ── Incident type → icon + colour ──────────────────────────────────────────
  // Codes sourced from https://www.pulsepoint.org/incident-types
  const STYLES = {
    // ── AID ──────────────────────────────────────────────────────────────────
    AA:    { icon: 'mdi:handshake',               color: '#64748b' }, // Auto Aid
    MU:    { icon: 'mdi:handshake',               color: '#64748b' }, // Mutual Aid
    ST:    { icon: 'mdi:handshake',               color: '#64748b' }, // Strike Team/Task Force

    // ── AIRCRAFT ─────────────────────────────────────────────────────────────
    AC:    { icon: 'mdi:airplane-alert',          color: '#ef4444' }, // Aircraft Crash
    AE:    { icon: 'mdi:airplane-alert',          color: '#ef4444' }, // Aircraft Emergency
    AES:   { icon: 'mdi:airplane',                color: '#f97316' }, // Aircraft Emergency Standby
    LZ:    { icon: 'mdi:helicopter-landing',      color: '#64748b' }, // Landing Zone

    // ── ALARM ────────────────────────────────────────────────────────────────
    AED:   { icon: 'mdi:heart-pulse',             color: '#f97316' }, // AED Alarm
    CMA:   { icon: 'mdi:molecule-co',             color: '#eab308' }, // Carbon Monoxide
    FA:    { icon: 'mdi:fire-alert',              color: '#f97316' }, // Fire Alarm
    MA:    { icon: 'mdi:alarm-light',             color: '#f97316' }, // Manual Alarm
    OA:    { icon: 'mdi:alarm-light',             color: '#f97316' }, // Alarm
    SD:    { icon: 'mdi:smoke-detector-alert',    color: '#f97316' }, // Smoke Detector
    TRBL:  { icon: 'mdi:alarm-light-outline',     color: '#f97316' }, // Trouble Alarm
    WFA:   { icon: 'mdi:sprinkler-fire',          color: '#f97316' }, // Waterflow Alarm

    // ── ASSIST ───────────────────────────────────────────────────────────────
    FL:    { icon: 'mdi:home-flood',              color: '#0ea5e9' }, // Flooding
    LA:    { icon: 'mdi:human-handsup',           color: '#3b82f6' }, // Lift Assist
    LR:    { icon: 'mdi:ladder',                  color: '#06b6d4' }, // Ladder Request
    PA:    { icon: 'mdi:police-badge',            color: '#6366f1' }, // Police Assist
    PS:    { icon: 'mdi:account-hard-hat',        color: '#64748b' }, // Public Service
    SH:    { icon: 'mdi:pipe-leak',               color: '#0ea5e9' }, // Sheared Hydrant

    // ── EXPLOSION ────────────────────────────────────────────────────────────
    EX:    { icon: 'mdi:explosion',               color: '#ef4444' }, // Explosion
    PE:    { icon: 'mdi:pipe-leak',               color: '#ef4444' }, // Pipeline Emergency
    TE:    { icon: 'mdi:transmission-tower',      color: '#ef4444' }, // Transformer Explosion

    // ── FIRE ─────────────────────────────────────────────────────────────────
    AF:    { icon: 'mdi:fire',                    color: '#f97316' }, // Appliance Fire
    CB:    { icon: 'mdi:campfire',                color: '#64748b' }, // Controlled Burn/Prescribed Fire
    CF:    { icon: 'mdi:fire',                    color: '#ef4444' }, // Commercial Fire
    CHIM:  { icon: 'mdi:chimney',                 color: '#f97316' }, // Chimney Fire
    EF:    { icon: 'mdi:fire-off',                color: '#64748b' }, // Extinguished Fire
    ELF:   { icon: 'mdi:lightning-bolt',          color: '#f97316' }, // Electrical Fire
    FIRE:  { icon: 'mdi:fire',                    color: '#ef4444' }, // Fire
    FULL:  { icon: 'mdi:fire-truck',              color: '#ef4444' }, // Full Assignment
    GF:    { icon: 'mdi:trash-can',               color: '#f97316' }, // Refuse/Garbage Fire
    IF:    { icon: 'mdi:fire-alert',              color: '#f97316' }, // Illegal Fire
    MF:    { icon: 'mdi:ferry',                   color: '#ef4444' }, // Marine Fire
    OF:    { icon: 'mdi:fire',                    color: '#ef4444' }, // Outside Fire
    PF:    { icon: 'mdi:transmission-tower',      color: '#f97316' }, // Pole Fire
    RF:    { icon: 'mdi:fire',                    color: '#ef4444' }, // Residential Fire
    SF:    { icon: 'mdi:fire',                    color: '#ef4444' }, // Structure Fire
    TF:    { icon: 'mdi:propane-tank',            color: '#ef4444' }, // Tank Fire
    VEG:   { icon: 'mdi:fire',                    color: '#f97316' }, // Vegetation Fire
    VF:    { icon: 'mdi:car-emergency',           color: '#ef4444' }, // Vehicle Fire
    WCF:   { icon: 'mdi:fire',                    color: '#ef4444' }, // Working Commercial Fire
    WF:    { icon: 'mdi:fire',                    color: '#ef4444' }, // Working Fire
    WRF:   { icon: 'mdi:fire',                    color: '#ef4444' }, // Working Residential Fire
    WSF:   { icon: 'mdi:fire',                    color: '#ef4444' }, // Confirmed Structure Fire
    WVEG:  { icon: 'mdi:fire',                    color: '#ef4444' }, // Confirmed Vegetation Fire

    // ── HAZARD ───────────────────────────────────────────────────────────────
    BT:    { icon: 'mdi:bomb',                    color: '#ef4444' }, // Bomb Threat
    EE:    { icon: 'mdi:lightning-bolt',          color: '#eab308' }, // Electrical Emergency
    EM:    { icon: 'mdi:alert',                   color: '#ef4444' }, // Emergency
    ER:    { icon: 'mdi:alert-circle',            color: '#ef4444' }, // Emergency Response
    GAS:   { icon: 'mdi:gas-cylinder',            color: '#eab308' }, // Gas Leak
    HC:    { icon: 'mdi:hazard-lights',           color: '#eab308' }, // Hazardous Condition
    HMR:   { icon: 'mdi:chemical-weapon',         color: '#eab308' }, // Hazmat Response
    TD:    { icon: 'mdi:tree',                    color: '#64748b' }, // Tree Down
    WE:    { icon: 'mdi:water-alert',             color: '#0ea5e9' }, // Water Emergency

    // ── INVESTIGATION ────────────────────────────────────────────────────────
    AI:    { icon: 'mdi:fire-alert',              color: '#6366f1' }, // Arson Investigation
    FWI:   { icon: 'mdi:firework',                color: '#6366f1' }, // Fireworks Investigation
    HMI:   { icon: 'mdi:hazard-lights',           color: '#6366f1' }, // Hazmat Investigation
    INV:   { icon: 'mdi:magnify',                 color: '#6366f1' }, // Investigation
    OI:    { icon: 'mdi:magnify',                 color: '#6366f1' }, // Odor Investigation
    SI:    { icon: 'mdi:smoke',                   color: '#6366f1' }, // Smoke Investigation

    // ── LOCKOUT ──────────────────────────────────────────────────────────────
    CL:    { icon: 'mdi:door-closed-lock',        color: '#64748b' }, // Commercial Lockout
    LO:    { icon: 'mdi:lock',                    color: '#64748b' }, // Lockout
    RL:    { icon: 'mdi:home-lock',               color: '#64748b' }, // Residential Lockout
    VL:    { icon: 'mdi:car-key',                 color: '#64748b' }, // Vehicle Lockout

    // ── MEDICAL ──────────────────────────────────────────────────────────────
    CP:    { icon: 'mdi:medical-bag',             color: '#3b82f6' }, // Community Paramedicine
    CPR:   { icon: 'mdi:heart-pulse',             color: '#ef4444' }, // CPR Needed
    IFT:   { icon: 'mdi:ambulance',               color: '#64748b' }, // Interfacility Transfer
    ME:    { icon: 'mdi:medical-bag',             color: '#3b82f6' }, // Medical Emergency
    MCI:   { icon: 'mdi:hospital',                color: '#ef4444' }, // Multi Casualty

    // ── NATURAL DISASTER ─────────────────────────────────────────────────────
    EQ:    { icon: 'mdi:earth',                   color: '#8b5cf6' }, // Earthquake
    FLW:   { icon: 'mdi:home-flood',              color: '#0ea5e9' }, // Flood Warning
    TOW:   { icon: 'mdi:weather-tornado',         color: '#8b5cf6' }, // Tornado Warning
    TSW:   { icon: 'mdi:water-alert',             color: '#0ea5e9' }, // Tsunami Warning
    WX:    { icon: 'mdi:weather-lightning-rainy', color: '#64748b' }, // Weather Incident

    // ── OTHER ────────────────────────────────────────────────────────────────
    BP:    { icon: 'mdi:fire',                    color: '#f97316' }, // Burn Permit
    CA:    { icon: 'mdi:account-group',           color: '#64748b' }, // Community Activity
    FW:    { icon: 'mdi:binoculars',              color: '#64748b' }, // Fire Watch
    MC:    { icon: 'mdi:fire-truck',              color: '#64748b' }, // Move-up/Cover
    NO:    { icon: 'mdi:bell',                    color: '#64748b' }, // Notification
    STBY:  { icon: 'mdi:timer-sand',              color: '#64748b' }, // Standby
    TEST:  { icon: 'mdi:test-tube',               color: '#64748b' }, // Test
    TRNG:  { icon: 'mdi:school',                  color: '#64748b' }, // Training

    // ── RESCUE ───────────────────────────────────────────────────────────────
    AR:    { icon: 'mdi:paw',                     color: '#06b6d4' }, // Animal Rescue
    CR:    { icon: 'mdi:terrain',                 color: '#06b6d4' }, // Cliff Rescue
    CSR:   { icon: 'mdi:tunnel',                  color: '#06b6d4' }, // Confined Space Rescue
    EER:   { icon: 'mdi:elevator',                color: '#06b6d4' }, // Elevator/Escalator Rescue
    ELR:   { icon: 'mdi:elevator',                color: '#06b6d4' }, // Elevator Rescue
    IA:    { icon: 'mdi:factory',                 color: '#06b6d4' }, // Industrial Accident
    IR:    { icon: 'mdi:snowflake-alert',         color: '#06b6d4' }, // Ice Rescue
    RES:   { icon: 'mdi:lifebuoy',                color: '#06b6d4' }, // Rescue
    RR:    { icon: 'mdi:rope',                    color: '#06b6d4' }, // Rope Rescue
    SC:    { icon: 'mdi:home-alert',              color: '#06b6d4' }, // Structural Collapse
    TNR:   { icon: 'mdi:tunnel',                  color: '#06b6d4' }, // Trench Rescue
    TR:    { icon: 'mdi:crane',                   color: '#06b6d4' }, // Technical Rescue
    USAR:  { icon: 'mdi:lifebuoy',                color: '#06b6d4' }, // Urban Search and Rescue
    VS:    { icon: 'mdi:ferry',                   color: '#06b6d4' }, // Vessel Sinking
    WR:    { icon: 'mdi:waves',                   color: '#0ea5e9' }, // Water Rescue

    // ── VEHICLE ──────────────────────────────────────────────────────────────
    RTE:   { icon: 'mdi:train',                   color: '#f97316' }, // Railroad/Train Emergency
    TC:    { icon: 'mdi:car-emergency',           color: '#f97316' }, // Traffic Collision
    TCP:   { icon: 'mdi:car-emergency',           color: '#ef4444' }, // Collision Involving Pedestrian
    TCE:   { icon: 'mdi:car-emergency',           color: '#ef4444' }, // Expanded Traffic Collision
    TCS:   { icon: 'mdi:car-emergency',           color: '#ef4444' }, // Collision Involving Structure
    TCT:   { icon: 'mdi:train',                   color: '#ef4444' }, // Collision Involving Train

    // ── WIRES ────────────────────────────────────────────────────────────────
    PLE:   { icon: 'mdi:transmission-tower',      color: '#eab308' }, // Powerline Emergency
    WA:    { icon: 'mdi:lightning-bolt',          color: '#eab308' }, // Wires Arcing
    WD:    { icon: 'mdi:power-plug-off',          color: '#eab308' }, // Wires Down
    WDA:   { icon: 'mdi:lightning-bolt',          color: '#eab308' }, // Wires Down/Arcing

    // ── Default ──────────────────────────────────────────────────────────────
    _:     { icon: 'mdi:alert-circle',            color: '#64748b' },
  };

  function incidentStyle(code) {
    return STYLES[(code || '').toUpperCase()] || STYLES._;
  }

  function relativeTime(iso) {
    if (!iso) return '';
    const diff = Math.floor((Date.now() - new Date(iso)) / 1000);
    if (diff < 60)   return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) {
      const h = Math.floor(diff / 3600);
      const m = Math.floor((diff % 3600) / 60);
      return m ? `${h}h ${m}m ago` : `${h}h ago`;
    }
    return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  }

  function unitLabels(units) {
    if (!Array.isArray(units) || !units.length) return null;
    return units
      .map(u => (typeof u === 'string' ? u : (u.UnitID || u.unit_id || u.id || null)))
      .filter(Boolean)
      .join(' · ');
  }

  function hexRgb(hex) {
    return `${parseInt(hex.slice(1,3),16)}, ${parseInt(hex.slice(3,5),16)}, ${parseInt(hex.slice(5,7),16)}`;
  }

  // Entities from a config, normalized to [{entity, name?}, ...]
  function entityConfigsOf(config) {
    const e = config?.entities ?? config?.entity ?? [];
    return (Array.isArray(e) ? e : [e])
      .filter(Boolean)
      .map(item => typeof item === 'string' ? { entity: item } : item);
  }

  // ── Card element ───────────────────────────────────────────────────────────
  class PulsepointCard extends HTMLElement {
    constructor() {
      super();
      this._config = null;
      this._hass   = null;
      this._filterDist = 25;
      this._hiddenAgencies = new Set();
      this._expanded = false;
      this.attachShadow({ mode: 'open' });
    }

    static getConfigElement() { return document.createElement('pulsepoint-card-editor'); }

    static getStubConfig(hass) {
      // Prefer the per-agency "Active incidents" sensors from the PulsePoint
      // integration (they carry the incident list + agency_id as attributes).
      const ids = hass
        ? Object.keys(hass.states).filter(id =>
            id.startsWith('sensor.') &&
            hass.states[id].attributes?.agency_id !== undefined &&
            Array.isArray(hass.states[id].attributes?.incidents))
        : [];
      const active = ids.filter(id => id.includes('active'));
      return { entities: (active.length ? active : ids).slice(0, 1) };
    }

    setConfig(config) {
      if (!config.entities && !config.entity)
        throw new Error('pulsepoint-card: "entities" or "entity" required');
      this._config = { ...DEFAULTS, ...config };
      this._filterDist = Number(this._config.default_distance) || DEFAULTS.default_distance;
      this._expanded = false;
      this._render();
    }

    set hass(hass) {
      const old = this._hass;
      this._hass = hass;
      if (!this._config) return;
      // Skip the (expensive) full re-render unless one of our entities changed.
      if (old && this._entityIds().every(id => old.states[id] === hass.states[id])) return;
      this._render();
    }

    getCardSize() { return 4; }

    // ── Data helpers ──────────────────────────────────────────────────────────
    _entityConfigs() { return entityConfigsOf(this._config); }

    _entityIds() {
      return this._entityConfigs().map(c => c.entity);
    }

    _agencyOf(cfg) {
      const state = this._hass?.states[cfg.entity];
      return state?.attributes.agency_id || cfg.entity;
    }

    _allIncidents() {
      if (!this._hass) return [];
      return this._entityConfigs().flatMap(cfg => {
        const state = this._hass.states[cfg.entity];
        if (!state) return [];
        const agency = state.attributes.agency_id || cfg.entity;
        const agencyLabel = cfg.name || agency;
        return (state.attributes.incidents || []).map(inc => ({ ...inc, _agency: agency, _agencyLabel: agencyLabel }));
      });
    }

    _withinDistance(inc) {
      const d = inc.distance_from_home_miles;
      return d === null || d === undefined || d <= this._filterDist;
    }

    _filtered() {
      const incidents = this._allIncidents()
        .filter(inc => !this._hiddenAgencies.has(inc._agency) && this._withinDistance(inc));
      if (this._config.sort_by === 'newest') {
        return incidents.sort((a, b) =>
          new Date(b.received ?? 0) - new Date(a.received ?? 0));
      }
      return incidents.sort((a, b) =>
        (a.distance_from_home_miles ?? Infinity) - (b.distance_from_home_miles ?? Infinity));
    }

    _agencyCount(agency) {
      return this._allIncidents()
        .filter(inc => inc._agency === agency && this._withinDistance(inc)).length;
    }

    _lastUpdatedLabel() {
      if (!this._hass) return '';
      const times = this._entityIds()
        .map(id => this._hass.states[id]?.last_updated)
        .filter(Boolean)
        .map(t => new Date(t).getTime());
      if (!times.length) return '';
      const t = relativeTime(new Date(Math.max(...times)).toISOString());
      return t === 'Just now' ? 'Updated just now' : `Updated ${t}`;
    }

    // ── Full render ───────────────────────────────────────────────────────────
    _render() {
      if (!this._config) return;

      const cfg         = this._config;
      const title       = cfg.title;
      const maxSlider   = Math.max(Number(cfg.max_distance) || DEFAULTS.max_distance, this._filterDist);
      const multiAgency = this._entityConfigs().length > 1;
      const showSlider  = cfg.show_distance_slider !== false;
      const showChips   = multiAgency && cfg.show_agency_filter !== false;
      const incidents   = this._filtered();

      this.shadowRoot.innerHTML = `
        <style>
          *, *::before, *::after { box-sizing: border-box; }
          :host { display: block; }

          ha-card { overflow: hidden; }

          /* ── Header ── */
          .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 16px 0;
          }
          .title {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 1rem;
            font-weight: 600;
            color: var(--primary-text-color);
          }
          .title ha-icon { --mdc-icon-size: 20px; color: var(--primary-color); }

          .count {
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            padding: 5px 13px;
            border-radius: 999px;
            background: transparent;
            color: var(--primary-color);
            min-width: 80px;
            text-align: center;
          }
          .count.zero {
            background: var(--secondary-background-color);
            color: var(--secondary-text-color);
            border: 1.5px solid transparent;
          }

          /* ── Filters ── */
          .filters {
            padding: 12px 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            border-bottom: 1px solid var(--divider-color);
          }
          .filters.none { padding: 6px 0 0; border-bottom: 1px solid var(--divider-color); }

          .dist-row {
            display: flex;
            align-items: center;
            gap: 10px;
          }
          .dist-label {
            font-size: 0.78rem;
            color: var(--secondary-text-color);
            white-space: nowrap;
          }
          input[type=range] {
            flex: 1;
            -webkit-appearance: none;
            appearance: none;
            height: 4px;
            border-radius: 2px;
            background: var(--divider-color);
            outline: none;
            cursor: pointer;
          }
          input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: var(--primary-color);
            cursor: pointer;
          }
          .dist-val {
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--primary-text-color);
            min-width: 80px;
            text-align: center;
          }

          /* ── Agency chips ── */
          .chips {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
          }
          .chip {
            font: inherit;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 999px;
            border: 1px solid var(--divider-color);
            background: var(--secondary-background-color);
            color: var(--primary-text-color);
            cursor: pointer;
            transition: opacity 0.12s, background 0.12s;
          }
          .chip .chip-count {
            font-size: 0.7rem;
            font-weight: 700;
            padding: 1px 7px;
            border-radius: 999px;
            background: rgba(69,39,160,0.7);
            color: #fff;
          }
          .chip.off { opacity: 0.4; }
          .chip.off .chip-count { background: var(--divider-color); color: var(--secondary-text-color); }

          /* ── Incident list ── */
          .list { }

          .row {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 12px 16px;
            border-bottom: 1px solid var(--divider-color);
            transition: background 0.12s;
            cursor: pointer;
          }
          .row:last-child { border-bottom: none; }
          .row:hover { background: var(--secondary-background-color); }

          .icon-bubble {
            flex-shrink: 0;
            width: 42px;
            height: 42px;
            border-radius: 13px;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          .icon-bubble ha-icon { --mdc-icon-size: 22px; }

          .body { flex: 1; min-width: 0; }
          .inc-type {
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--primary-text-color);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          .inc-addr {
            font-size: 0.8rem;
            color: var(--secondary-text-color);
            margin-top: 2px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          .meta {
            margin-top: 5px;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 4px;
            font-size: 0.72rem;
            color: var(--secondary-text-color);
          }
          .meta .dot { opacity: 0.35; }
          .units {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 180px;
          }

          .live-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #ef4444;
            display: inline-block;
            flex-shrink: 0;
            animation: pp-pulse 1.6s ease-out infinite;
          }
          @keyframes pp-pulse {
            0%   { box-shadow: 0 0 0 0 rgba(239,68,68,0.5); }
            70%  { box-shadow: 0 0 0 6px rgba(239,68,68,0); }
            100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
          }

          .right {
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
          }
          .dist-pill {
            font-size: 0.82rem;
            font-weight: 700;
            padding: 5px 13px;
            border-radius: 999px;
            white-space: nowrap;
            min-width: 80px;
            text-align: center;
          }
          .agency-lbl {
            font-size: 0.75rem;
            font-weight: 500;
            color: var(--primary-text-color);
            opacity: 0.7;
          }

          /* ── Show more / less ── */
          .more-btn {
            font: inherit;
            display: block;
            width: 100%;
            padding: 10px 16px;
            border: none;
            border-top: 1px solid var(--divider-color);
            background: transparent;
            color: var(--primary-color);
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
          }
          .more-btn:hover { background: var(--secondary-background-color); }

          /* ── Empty state — mirrors an incident row so card height matches ── */
          .row.empty-row { cursor: default; }
          .row.empty-row:hover { background: transparent; }
        </style>

        <ha-card>
          <div class="header">
            <div class="title">
              <ha-icon icon="mdi:fire-truck"></ha-icon>
              ${title}
            </div>
            <div class="count ${incidents.length === 0 ? 'zero' : ''}">
              ${incidents.length} active
            </div>
          </div>

          ${showSlider || showChips ? `
          <div class="filters">
            ${showSlider ? `
            <div class="dist-row">
              <span class="dist-label">Within</span>
              <input type="range" min="0.5" max="${maxSlider}"
                     step="0.5" value="${this._filterDist}">
              <span class="dist-val">${this._filterDist.toFixed(1)} mi</span>
            </div>` : ''}
            ${showChips ? `
            <div class="chips">
              ${this._entityConfigs().map(c => {
                const agency = this._agencyOf(c);
                const label  = c.name || agency;
                const off    = this._hiddenAgencies.has(agency);
                return `<button class="chip ${off ? 'off' : ''}" data-agency="${agency}">
                          ${label}<span class="chip-count">${this._agencyCount(agency)}</span>
                        </button>`;
              }).join('')}
            </div>` : ''}
          </div>` : '<div class="filters none"></div>'}

          <div class="list">
            ${this._listHTML(incidents, multiAgency)}
          </div>
        </ha-card>
      `;

      // Slider — live update without full re-render
      const slider = this.shadowRoot.querySelector('input[type=range]');
      if (slider) {
        slider.addEventListener('input', e => {
          this._filterDist = parseFloat(e.target.value);
          this.shadowRoot.querySelector('.dist-val').textContent =
            `${this._filterDist.toFixed(1)} mi`;
          this._refreshList(multiAgency);
        });
      }

      // Agency chips — toggle visibility per agency
      this.shadowRoot.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
          const agency = chip.dataset.agency;
          if (this._hiddenAgencies.has(agency)) this._hiddenAgencies.delete(agency);
          else this._hiddenAgencies.add(agency);
          this._render();
        });
      });

      this._attachListEvents();
    }

    _attachListEvents() {
      this.shadowRoot.querySelector('.list').addEventListener('click', e => {
        const more = e.target.closest('.more-btn');
        if (more) {
          this._expanded = !this._expanded;
          this._render();
          return;
        }
        const row = e.target.closest('.row');
        if (!row) return;
        const addr = row.dataset.addr;
        if (addr && addr !== 'Address unknown')
          window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(addr)}`, '_blank');
      });
    }

    _refreshList(multiAgency) {
      const incidents = this._filtered();
      this.shadowRoot.querySelector('.list').innerHTML = this._listHTML(incidents, multiAgency);
      const badge = this.shadowRoot.querySelector('.count');
      badge.textContent = `${incidents.length} active`;
      badge.classList.toggle('zero', incidents.length === 0);
      this.shadowRoot.querySelectorAll('.chip').forEach(chip => {
        const countEl = chip.querySelector('.chip-count');
        if (countEl) countEl.textContent = this._agencyCount(chip.dataset.agency);
      });
    }

    _listHTML(incidents, multiAgency) {
      if (!incidents.length) {
        const time = this._lastUpdatedLabel();
        return `
          <div class="row empty-row">
            <div class="icon-bubble" style="background:rgba(34,197,94,.14)">
              <ha-icon icon="mdi:check" style="color:#22c55e"></ha-icon>
            </div>
            <div class="body">
              <div class="inc-type">All clear</div>
              <div class="inc-addr">No active incidents within ${this._filterDist.toFixed(1)} mi</div>
              <div class="meta"><span>${time || 'Monitoring'}</span></div>
            </div>
          </div>`;
      }

      const limit   = Number(this._config.max_incidents) || 0;
      const visible = (limit > 0 && !this._expanded) ? incidents.slice(0, limit) : incidents;
      const rows    = visible.map(inc => this._rowHTML(inc, multiAgency)).join('');

      if (limit > 0 && incidents.length > limit) {
        const label = this._expanded
          ? 'Show less'
          : `Show ${incidents.length - limit} more`;
        return rows + `<button class="more-btn">${label}</button>`;
      }
      return rows;
    }

    _rowHTML(inc, showAgency) {
      const cfg = this._config;
      const s   = incidentStyle(inc.incident_type_code);
      const rgb = hexRgb(s.color);
      const d   = inc.distance_from_home_miles;

      const distLabel = (d === null || d === undefined) ? '— mi' : `${d.toFixed(1)} mi`;
      const distBg = 'rgba(69,39,160,0.7)';
      const distFg = '#fff';

      const units = cfg.show_units !== false ? unitLabels(inc.units) : null;
      const time  = cfg.show_time !== false ? relativeTime(inc.received) : '';
      const type  = inc.incident_type || inc.incident_type_code || 'Unknown';
      const addr  = inc.address || 'Address unknown';

      const hlMins = Number(cfg.highlight_recent_minutes) || 0;
      const isNew  = hlMins > 0 && inc.received &&
        (Date.now() - new Date(inc.received)) < hlMins * 60000;

      return `
        <div class="row" data-addr="${addr.replace(/"/g, '&quot;')}">
          <div class="icon-bubble"
               style="background:rgba(${rgb},.14)">
            <ha-icon icon="${s.icon}" style="color:${s.color}"></ha-icon>
          </div>
          <div class="body">
            <div class="inc-type">${type}</div>
            <div class="inc-addr">${addr}</div>
            <div class="meta">
              ${isNew ? `<span class="live-dot"></span>` : ''}
              ${time ? `<span>${time}</span>` : ''}
              ${time && units ? `<span class="dot">·</span>` : ''}
              ${units ? `<span class="units">${units}</span>` : ''}
            </div>
          </div>
          <div class="right">
            <div class="dist-pill"
                 style="background:${distBg};color:${distFg}">${distLabel}</div>
            ${showAgency ? `<div class="agency-lbl">${inc._agencyLabel}</div>` : ''}
          </div>
        </div>`;
    }
  }

  // ── Visual editor ──────────────────────────────────────────────────────────
  const EDITOR_SCHEMA = [
    { name: 'title', selector: { text: {} } },
    { name: 'entities',
      selector: { entity: { multiple: true,
                            filter: [{ integration: 'pulsepoint', domain: 'sensor' }] } } },
    { type: 'grid', name: '', schema: [
      { name: 'default_distance',
        selector: { number: { min: 0.5, max: 100, step: 0.5,
                              unit_of_measurement: 'mi', mode: 'box' } } },
      { name: 'max_distance',
        selector: { number: { min: 1, max: 100, step: 1,
                              unit_of_measurement: 'mi', mode: 'box' } } },
    ]},
    { type: 'grid', name: '', schema: [
      { name: 'show_distance_slider', selector: { boolean: {} } },
      { name: 'show_agency_filter',   selector: { boolean: {} } },
      { name: 'show_time',            selector: { boolean: {} } },
      { name: 'show_units',           selector: { boolean: {} } },
    ]},
    { type: 'grid', name: '', schema: [
      { name: 'sort_by',
        selector: { select: { mode: 'dropdown', options: [
          { value: 'distance', label: 'Closest first' },
          { value: 'newest',   label: 'Newest first' },
        ]}}},
      { name: 'max_incidents',
        selector: { number: { min: 0, max: 50, step: 1, mode: 'box' } } },
    ]},
    { name: 'highlight_recent_minutes',
      selector: { number: { min: 0, max: 120, step: 1,
                            unit_of_measurement: 'min', mode: 'box' } } },
  ];

  const EDITOR_LABELS = {
    title: 'Title',
    entities: 'Agencies (PulsePoint incident sensors)',
    default_distance: 'Default distance',
    max_distance: 'Slider maximum',
    show_distance_slider: 'Show distance slider',
    show_agency_filter: 'Show agency filter chips',
    show_time: 'Show incident time',
    show_units: 'Show responding units',
    sort_by: 'Sort incidents by',
    max_incidents: 'Max rows before "Show more"',
    highlight_recent_minutes: 'Highlight incidents newer than',
  };

  const EDITOR_HELPERS = {
    entities: 'Pick the "Active incidents" sensor for each agency you want on the card.',
    default_distance: 'Initial radius. If the slider is hidden, this radius is used permanently.',
    show_agency_filter: 'Only shown when more than one agency is configured.',
    max_incidents: '0 shows every incident with no collapsing.',
    highlight_recent_minutes: 'Pulsing dot on fresh incidents. 0 disables.',
  };

  class PulsepointCardEditor extends HTMLElement {
    setConfig(config) {
      this._raw = config || {};
      this._render();
    }

    set hass(hass) {
      this._hass = hass;
      this._render();
    }

    _render() {
      if (!this._hass || !this._raw) return;
      if (!this._form) {
        this._form = document.createElement('ha-form');
        this._form.computeLabel  = s => EDITOR_LABELS[s.name] ?? s.name;
        this._form.computeHelper = s => EDITOR_HELPERS[s.name];
        this._form.addEventListener('value-changed', e => this._valueChanged(e));
        this.appendChild(this._form);
      }
      this._form.hass   = this._hass;
      this._form.schema = EDITOR_SCHEMA;
      this._form.data   = {
        ...DEFAULTS,
        ...this._raw,
        entities: entityConfigsOf(this._raw).map(c => c.entity),
      };
    }

    _valueChanged(e) {
      e.stopPropagation();
      const value = e.detail.value;

      // Preserve {entity, name} objects from hand-written YAML configs.
      const named = new Map(
        entityConfigsOf(this._raw)
          .filter(c => Object.keys(c).length > 1)
          .map(c => [c.entity, c])
      );

      const config = { type: 'custom:pulsepoint-card', ...this._raw, ...value };
      config.entities = (value.entities || []).map(id => named.get(id) ?? id);
      delete config.entity;

      // Keep the stored YAML minimal: drop options still at their default.
      for (const [key, def] of Object.entries(DEFAULTS)) {
        if (config[key] === def && !(key in this._raw)) delete config[key];
      }

      this._raw = config;
      this.dispatchEvent(new CustomEvent('config-changed', {
        detail: { config }, bubbles: true, composed: true,
      }));
    }
  }

  if (!customElements.get('pulsepoint-card'))
    customElements.define('pulsepoint-card', PulsepointCard);
  if (!customElements.get('pulsepoint-card-editor'))
    customElements.define('pulsepoint-card-editor', PulsepointCardEditor);

  window.customCards = window.customCards || [];
  if (!window.customCards.some(c => c.type === 'pulsepoint-card')) {
    window.customCards.push({
      type: 'pulsepoint-card',
      name: 'PulsePoint Card',
      description: 'Live fire/EMS incidents from your PulsePoint agencies, with distance and agency filters.',
      preview: false,
      documentationURL: 'https://github.com/petergCA/PulsePoint',
    });
  }

  console.info(
    `%c PULSEPOINT-CARD %c v${CARD_VERSION}`,
    'background:#c0392b;color:#fff;font-weight:700;padding:2px 6px;border-radius:3px 0 0 3px',
    'background:#2c3e50;color:#fff;padding:2px 6px;border-radius:0 3px 3px 0',
  );
})();
