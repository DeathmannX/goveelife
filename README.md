# GoveeLife — Home Assistant Integration

A community-maintained [HACS](https://hacs.xyz) custom integration connecting Govee smart home devices to Home Assistant via the [Govee OpenAPI v2](https://developer.govee.com/).

---

## Supported Devices

The integration auto-discovers all devices on your Govee account and creates entities based on reported capabilities — no SKU hardcoding.

| Device Type | HA Platform | Capabilities |
|---|---|---|
| Lights | `light` | On/off, brightness, RGB, color temp, scenes, DIY scenes, RGBIC segments |
| Heaters / Kettles | `climate` | On/off, target/current temperature, HVAC mode |
| Air Purifiers / Fans | `fan` | On/off, speed, preset modes, oscillation |
| Humidifiers | `humidifier` | On/off, target humidity, preset modes + sensors |
| Ice Makers / Diffusers / Plugs | `switch` | On/off |
| Wi-Fi Thermometers | `sensor` | Temperature, humidity |

**RGBIC / Segmented lights** (H6076, H60A1, H60A4, H60B2, H70C7, H7075 and any device exposing `segment_color_setting`) get individual `light` entities per zone with independent color and brightness control.

---

## Installation

**Via HACS (recommended):**
1. In HACS → ⋮ menu → **Custom repositories** → add `https://github.com/disforw/goveelife` as type **Integration**
2. Search for **goveelife** → **Download** → restart Home Assistant

**Manual:** Copy `custom_components/goveelife` into your `config/custom_components/` directory and restart.

---

## Configuration

1. Get your API key: Govee Home app → **Settings → Apply for API Key** (delivered by email)
2. In HA: **Settings → Devices & Services → Add Integration → GoveeLife**
3. Enter your API key and set a poll interval (60–120s recommended — Govee rate limits apply)

---

## Troubleshooting

- **Device not showing up** — confirm it's visible in the Govee Home app; not all devices have API support
- **Stale state / controls not working** — Govee API rate limits (~10 req/min); check HA logs for `goveelife` errors
- **Segments won't turn off** — fixed in v4.B4; upgrade via HACS
- **Reporting a bug** — include your device diagnostics: **Settings → Devices & Services → GoveeLife → ⋮ → Download Diagnostics**

---

## Contributing

PRs welcome. Open an issue first for significant changes. Follow existing async/type-hint/HA patterns and test against a real device.

Maintained by [@disforw](https://github.com/disforw).
