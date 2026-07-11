from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from zoneinfo import ZoneInfo
from datetime import datetime

from .const import DOMAIN

SENSOR_KEYS = {
    "current_address": "Current Address",
    "city": "City",
    "state": "State",
    "country": "Country",
    "timezone_id": "Timezone ID",
    "timezone_full": "Timezone",
    "timezone_abbreviation": "Timezone Abbreviation",
    "timezone_source": "Data Source",
    "plus_code": "Plus Code",
}

SENSOR_ICONS = {
    "current_address": "mdi:map-marker",
    "city": "mdi:city",
    "state": "mdi:flag-variant",
    "country": "mdi:earth",
    "timezone_id": "mdi:calendar-clock",
    "timezone_full": "mdi:map-clock-outline",
    "timezone_abbreviation": "mdi:map-clock",
    "timezone_source": "mdi:cloud-download",
    "plus_code": "mdi:crosshairs-gps",
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    sensors = []

    provider = entry.options.get("api_provider") or entry.data.get("api_provider", "google")

    for key, name in SENSOR_KEYS.items():
        if provider == "offline" and key not in ("timezone_id", "timezone_abbreviation", "timezone_source"):
            continue
        if key == "timezone_source":
            sensors.append(TimezoneSourceSensor(coordinator=coordinator, entry=entry))
        else:
            sensors.append(GeoLocatorSensor(coordinator=coordinator, entry=entry, key=key, name=name))

    async_add_entities(sensors)


class GeoLocatorSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry, key, name):
        super().__init__(coordinator)
        self._entry = entry
        self._key = key
        self._name = name
        self._attr_name = f"GeoLocator: {name}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_icon = SENSOR_ICONS.get(key, "mdi:map-marker-question")

    @property
    def state(self):
        data = self.coordinator.data or {}
        if self._key in ("timezone_id", "timezone_abbreviation"):
            tz_id = data.get("timezone_id")
            if not tz_id:
                return None
            try:
                now = datetime.now(ZoneInfo(tz_id))
                if self._key == "timezone_id":
                    return tz_id
                elif self._key == "timezone_abbreviation":
                    return now.tzname()
            except Exception:
                return None
        elif self._key == "timezone_full":
            return data.get("timezone_full")
        else:
            return data.get(self._key)

    @property
    def extra_state_attributes(self):
        if self._key != "current_address":
            return None
        attribution = (self.coordinator.data or {}).get("attribution")
        return {"attribution": attribution} if attribution else None


class TimezoneSourceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "GeoLocator: Data Source"
        self._attr_unique_id = f"{entry.entry_id}_data_source"
        self._attr_icon = SENSOR_ICONS.get("timezone_source", "mdi:cloud-question")

    @property
    def state(self):
        return (self.coordinator.data or {}).get("timezone_source")
