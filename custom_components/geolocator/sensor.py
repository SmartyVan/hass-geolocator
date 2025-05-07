from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from zoneinfo import ZoneInfo
from datetime import datetime

from .const import DOMAIN

class GeoLocatorSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, key: str, name: str) -> None:
        self._hass = hass
        self._entry = entry
        self._key = key
        self._attr_name = f"GeoLocator: {name}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_icon = SENSOR_ICONS.get(key, "mdi:map-marker-question")
        self._api_data = hass.data[DOMAIN][entry.entry_id]
        hass.data[DOMAIN][entry.entry_id]["entities"].append(self)

    @property
    def state(self):
        if self._key in ("timezone_id", "timezone_abbreviation"):
            tz_id = self._api_data.get("last_timezone")
            if not tz_id:
                return None
            try:
                now = datetime.now(ZoneInfo(tz_id))
                return tz_id if self._key == "timezone_id" else now.tzname()
            except Exception:
                return None
        last = self._api_data.get("last_address") or {}
        return last.get(self._key)

class TimezoneSourceSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._attr_name = "GeoLocator: Data Source"
        self._attr_unique_id = f"{entry.entry_id}_data_source"
        self._attr_icon = SENSOR_ICONS.get("timezone_source", "mdi:cloud-download")
        hass.data[DOMAIN][entry.entry_id]["entities"].append(self)

    @property
    def state(self):
        return self._hass.data[DOMAIN][self._entry.entry_id].get("last_timezone_source")

class PublicLandsSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, key: str, name: str) -> None:
        self._hass = hass
        self._entry = entry
        self._key = key
        self._attr_name = f"GeoLocator: {name}"
        self._attr_unique_id = f"{entry.entry_id}_uspl_{key}"
        self._attr_icon = SENSOR_ICONS.get(key, "mdi:map-marker-question")
        self._api_data = hass.data[DOMAIN][entry.entry_id]
        hass.data[DOMAIN][entry.entry_id]["entities"].append(self)

    @property
    def state(self):
        public_data = self._api_data.get("us_public_lands_data") or {}
        return public_data.get(self._key) or "Unavailable"

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    config = entry.options or entry.data
    provider = config.get("api_provider", "google")
    uspl_enabled = config.get("enable_us_public_lands", False)
    sensors: list[SensorEntity] = []

    for spec in SENSOR_DEFINITIONS:
        if not spec["include_if"](provider, uspl_enabled):
            continue
        if spec["cls"] is TimezoneSourceSensor:
            inst = spec["cls"](hass, entry)
        else:
            inst = spec["cls"](hass, entry, spec["key"], spec["name"])
        sensors.append(inst)

    async_add_entities(sensors)

SENSOR_DEFINITIONS: list[dict] = [
    {"key": "current_address", "name": "Current Address", "cls": GeoLocatorSensor, "include_if": lambda provider, uspl: provider != "offline"},
    {"key": "city", "name": "City", "cls": GeoLocatorSensor, "include_if": lambda provider, uspl: provider != "offline"},
    {"key": "state", "name": "State", "cls": GeoLocatorSensor, "include_if": lambda provider, uspl: provider != "offline"},
    {"key": "country", "name": "Country", "cls": GeoLocatorSensor, "include_if": lambda provider, uspl: provider != "offline"},
    {"key": "timezone_id", "name": "Timezone ID", "cls": GeoLocatorSensor, "include_if": lambda provider, uspl: True},
    {"key": "timezone_abbreviation", "name": "Timezone Abbreviation", "cls": GeoLocatorSensor, "include_if": lambda provider, uspl: True},
    {"key": "timezone_source", "name": "Data Source", "cls": TimezoneSourceSensor, "include_if": lambda provider, uspl: True},
    {"key": "DesTp_Desc", "name": "USPL Designation", "cls": PublicLandsSensor, "include_if": lambda provider, uspl: uspl},
    {"key": "MngNm_Desc", "name": "USPL Management Name", "cls": PublicLandsSensor, "include_if": lambda provider, uspl: uspl},
    {"key": "MngTp_Desc", "name": "USPL Management Type", "cls": PublicLandsSensor, "include_if": lambda provider, uspl: uspl},
    {"key": "Pub_Access", "name": "USPL Public Access", "cls": PublicLandsSensor, "include_if": lambda provider, uspl: uspl},
    {"key": "Unit_Nm", "name": "USPL Unit Name", "cls": PublicLandsSensor, "include_if": lambda provider, uspl: uspl},
]

SENSOR_ICONS = {
    "current_address": "mdi:map-marker",
    "city": "mdi:city",
    "state": "mdi:flag-variant",
    "country": "mdi:earth",
    "timezone_id": "mdi:calendar-clock",
    "timezone_abbreviation": "mdi:map-clock",
    "timezone_source": "mdi:cloud-download",
    "DesTp_Desc": "mdi:forest",
    "MngNm_Desc": "mdi:office-building",
    "MngTp_Desc": "mdi:account-tie",
    "Pub_Access": "mdi:lock-open",
    "Unit_Nm": "mdi:information-outline",
}
