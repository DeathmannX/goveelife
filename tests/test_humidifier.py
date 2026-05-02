from __future__ import annotations

from copy import deepcopy

import pytest
from homeassistant.const import CONF_STATE

from custom_components.goveelife.const import DOMAIN
from custom_components.goveelife.humidifier import GoveeLifeHumidifier
from tests.conftest import build_hass_data, load_device_fixture

HUMIDIFIER_FIXTURE = "h7140_2025-12-31.json"


def _build_stateful_hass_data(entry, coordinator, device_cfg, capabilities):
    hass_data = build_hass_data(entry, coordinator, device_cfg)
    hass_data[DOMAIN][entry.entry_id][CONF_STATE] = {
        device_cfg["device"]: {
            "capabilities": capabilities,
        }
    }
    return hass_data


def _create_humidifier(hass, entry, coordinator, device_cfg):
    return GoveeLifeHumidifier(hass, entry, coordinator, device_cfg, platform="humidifier")


def test_target_humidity_reads_cached_range_state(hass, mock_config_entry, mock_coordinator):
    device_cfg = load_device_fixture(HUMIDIFIER_FIXTURE)
    capabilities = deepcopy(device_cfg["capabilities"])

    for capability in capabilities:
        if capability["type"] == "devices.capabilities.range" and capability["instance"] == "humidity":
            capability["state"] = {"value": 55}
        elif capability["type"] == "devices.capabilities.property" and capability["instance"] == "sensorHumidity":
            capability["state"] = {"value": 47}

    hass.data = _build_stateful_hass_data(mock_config_entry, mock_coordinator, device_cfg, capabilities)
    humidifier = _create_humidifier(hass, mock_config_entry, mock_coordinator, device_cfg)

    assert humidifier.min_humidity == 40
    assert humidifier.max_humidity == 80
    assert humidifier.target_humidity == 55


@pytest.mark.asyncio
async def test_async_set_humidity_sends_range_control_and_updates_cache(
    hass, mock_config_entry, mock_coordinator, monkeypatch
):
    device_cfg = load_device_fixture(HUMIDIFIER_FIXTURE)
    capabilities = deepcopy(device_cfg["capabilities"])

    for capability in capabilities:
        if capability["type"] == "devices.capabilities.range" and capability["instance"] == "humidity":
            capability["state"] = {"value": 50}

    hass.data = _build_stateful_hass_data(mock_config_entry, mock_coordinator, device_cfg, capabilities)
    humidifier = _create_humidifier(hass, mock_config_entry, mock_coordinator, device_cfg)

    calls = []

    async def fake_control_device(hass_obj, entry_id, device, state_capability):
        calls.append(state_capability)
        for cached_capability in hass_obj.data[DOMAIN][entry_id][CONF_STATE][device["device"]]["capabilities"]:
            if (
                cached_capability["type"] == state_capability["type"]
                and cached_capability["instance"] == state_capability["instance"]
            ):
                cached_capability["state"] = {"value": state_capability["value"]}
        return True

    monkeypatch.setattr("custom_components.goveelife.humidifier.async_GoveeAPI_ControlDevice", fake_control_device)

    await humidifier.async_set_humidity(60)

    assert calls == [
        {
            "type": "devices.capabilities.range",
            "instance": "humidity",
            "value": 60,
        }
    ]
    assert humidifier.target_humidity == 60
