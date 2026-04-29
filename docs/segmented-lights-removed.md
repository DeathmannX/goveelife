# Segmented Light Support — Removed in v3.2.0

## Why It Was Removed

Per-segment light entities were introduced to allow individual control of each LED segment on RGBIC/multi-zone Govee lights (e.g. H60A4, H7127). While functional, this caused significant UX problems for the majority of users:

- Devices with 15–18 segments spawned 15–18 extra light entities per device
- Users reported event bus overload and HA instability from the additional polling
- Most users had no use for per-segment control from HA and found it confusing

The decision was made to remove the feature entirely in favor of simplicity (Issue #142).

---

## What Was Removed

### 1. `GoveeLifeSegmentLight` class (`light.py`)

A subclass of `GoveeLifeLight` representing a single segment. Key methods:

- `__init__`: accepted `segment_index`, set `platform = f"light_seg{segment_index}"`, overrode `_name` and `uniqueid`
- `supported_color_modes`: returned `{ColorMode.RGB}` or `{ColorMode.BRIGHTNESS}` based on segment capability
- `color_mode`: returned matching `ColorMode`
- `_get_segment_raw_brightness()`: read `segmentedBrightness` from cached state, filtered by `segment_index`
- `brightness`: converted raw 0–100 API value via `value_to_brightness((1, 100), raw)`
- `rgb_color`: read `segmentedColorRgb` cached state, filtered by `segment_index`
- `state`: derived from brightness (0 = off) or rgb ((0,0,0) = off), fallback to parent
- `async_turn_on`: sent `segmentedColorRgb` or `segmentedBrightness` cap for the specific segment index; fallback to white restore on RGB devices
- `async_turn_off`: sent `brightness=0` for segmentedBrightness, then `rgb=0` for segmentedRgb (required on RGBIC devices — hardware clamps brightness to ~1%, rgb=0/black is needed to fully extinguish)

### 2. Segment entity spawning in `async_setup_entry` (`light.py`)

```python
if entity._segment_count > 1:
    for seg_idx in range(entity._segment_count):
        seg_entity = GoveeLifeSegmentLight(hass, entry, coordinator, device_cfg, segment_index=seg_idx)
        entities.append(seg_entity)
```

### 3. Segment fields in `GoveeLifeLight._platform_specific_init` (`light.py`)

```python
self._segment_count = 0
self._support_segmented_rgb = False
self._support_segmented_brightness = False
```

And the capability detection block for `devices.capabilities.segment_color_setting`:

```python
elif cap["type"] == "devices.capabilities.segment_color_setting":
    if cap["instance"] == "segmentedColorRgb":
        self._support_segmented_rgb = True
        seg_field = next((f for f in cap["parameters"]["fields"] if f["fieldName"] == "segment"), {})
        self._segment_count = max(self._segment_count or 0, seg_field.get("size", {}).get("max", 0))
        _LOGGER.info(...)
    elif cap["instance"] == "segmentedBrightness":
        self._support_segmented_brightness = True
        seg_field = next((f for f in cap["parameters"]["fields"] if f["fieldName"] == "segment"), {})
        self._segment_count = max(self._segment_count or 0, seg_field.get("size", {}).get("max", 0))
        _LOGGER.info(...)
```

And corresponding final-state log fields: `segment_count`, `segmented_rgb`, `segmented_brightness`.

---

## Capability Types Used (for re-implementation reference)

| Capability type | Instance | Notes |
|---|---|---|
| `devices.capabilities.segment_color_setting` | `segmentedColorRgb` | Per-segment RGB. Value: `{"segment": [idx], "rgb": int}` |
| `devices.capabilities.segment_color_setting` | `segmentedBrightness` | Per-segment brightness. Value: `{"segment": [idx], "brightness": 0–100}` |

Segment index is 0-based. The `segment` field in the capability payload is a **list** (you can theoretically target multiple segments in one call).

The `segment` array size (max segments) is in:
```
cap["parameters"]["fields"] → fieldName == "segment" → size.max
```

---

## Known Hardware Quirks

- **RGBIC devices (e.g. H60A4):** `brightness=0` alone does not fully turn off the LEDs — hardware clamps to ~1% minimum. Must send `rgb=0` (black) to fully extinguish a segment.
- **Brightness-only devices:** `brightness=0` is sufficient for off.

---

## Re-implementation Checklist

To restore segment support:

1. Add `_segment_count`, `_support_segmented_rgb`, `_support_segmented_brightness` back to `_platform_specific_init`
2. Add `devices.capabilities.segment_color_setting` detection back to the capability loop
3. Restore `GoveeLifeSegmentLight` class (see above)
4. Restore segment spawning loop in `async_setup_entry`
5. Consider making it opt-in via a config flow boolean (default: off) to avoid the entity explosion problem that caused this removal
