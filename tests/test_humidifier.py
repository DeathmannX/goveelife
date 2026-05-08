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


@pytest.mark.parametrize("sku", ["H7140", "H714E"])
def test_special_models_target_humidity_in_auto_mode(hass, mock_config_entry, mock_coordinator, sku):
    device_cfg = load_device_fixture(HUMIDIFIER_FIXTURE)
    device_cfg["sku"] = sku
    capabilities = deepcopy(device_cfg["capabilities"])

    for capability in capabilities:
        if capability["type"] == "devices.capabilities.work_mode" and capability["instance"] == "workMode":
            capability["state"] = {"value": {"workMode": 3, "modeValue": 65}}
        elif capability["type"] == "devices.capabilities.range" and capability["instance"] == "humidity":
            capability["state"] = {"value": 55}

    hass.data = _build_stateful_hass_data(mock_config_entry, mock_coordinator, device_cfg, capabilities)
    humidifier = _create_humidifier(hass, mock_config_entry, mock_coordinator, device_cfg)

    assert humidifier.target_humidity == 65
    assert humidifier.mode == "Auto"


@pytest.mark.asyncio
@pytest.mark.parametrize("sku", ["H7140", "H714E"])
async def test_special_models_async_set_humidity_in_auto_mode(
    hass, mock_config_entry, mock_coordinator, monkeypatch, sku
):
    device_cfg = load_device_fixture(HUMIDIFIER_FIXTURE)
    device_cfg["sku"] = sku
    capabilities = deepcopy(device_cfg["capabilities"])

    for capability in capabilities:
        if capability["type"] == "devices.capabilities.work_mode" and capability["instance"] == "workMode":
            capability["state"] = {"value": {"workMode": 3, "modeValue": 50}}

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
            "type": "devices.capabilities.work_mode",
            "instance": "workMode",
            "value": {
                "workMode": 3,
                "modeValue": 60,
            },
        }
    ]
    assert humidifier.target_humidity == 60


def test_regression_non_special_model_target_humidity(hass, mock_config_entry, mock_coordinator):
    device_cfg = load_device_fixture(HUMIDIFIER_FIXTURE)
    device_cfg["sku"] = "H7143"
    capabilities = deepcopy(device_cfg["capabilities"])

    for capability in capabilities:
        if capability["type"] == "devices.capabilities.work_mode" and capability["instance"] == "workMode":
            capability["state"] = {"value": {"workMode": 3, "modeValue": 0}}
        elif capability["type"] == "devices.capabilities.range" and capability["instance"] == "humidity":
            capability["state"] = {"value": 55}

    hass.data = _build_stateful_hass_data(mock_config_entry, mock_coordinator, device_cfg, capabilities)
    humidifier = _create_humidifier(hass, mock_config_entry, mock_coordinator, device_cfg)

    assert humidifier.target_humidity == 55


def test_feature_exposure_target_humidity(hass, mock_config_entry, mock_coordinator):
    device_cfg = load_device_fixture(HUMIDIFIER_FIXTURE)
    humidifier = _create_humidifier(hass, mock_config_entry, mock_coordinator, device_cfg)

    from homeassistant.components.humidifier import HumidifierEntityFeature

    # The existing code doesn't explicitly set target humidity feature because it's usually default
    # but it should be supported if min_humidity/max_humidity are set.
    # In HA, HumidifierEntity doesn't have a TARGET_HUMIDITY feature flag, it's assumed if supported.
    assert humidifier.min_humidity == 40
    assert humidifier.max_humidity == 80
