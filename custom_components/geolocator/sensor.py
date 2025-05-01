from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from zoneinfo import ZoneInfo
from datetime import datetime

from .const import DOMAIN

SENSOR_KEYS = {
    "current_address": "Current Address",
    "neighborhood": "Neighborhood",
    "city": "City",
    "state": "State",
    "country": "Country",
    "timezone_id": "Timezone ID",
    "timezone_abbreviation": "Timezone Abbreviation",
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    api_data = hass.data[DOMAIN][entry.entry_id]
    sensors = []

    for key, name in SENSOR_KEYS.items():
        sensors.append(GeoLocatorSensor(hass=hass, entry=entry, key=key, name=name, api_data=api_data))

    async_add_entities(sensors)


class GeoLocatorSensor(SensorEntity):
    def __init__(self, hass, entry, key, name, api_data):
        self._entry = entry
        self._key = key
        self._name = name
        self._api_data = api_data
        self._attr_name = f"GeoLocator: {name}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"

        # Register self for updates
        hass.data[DOMAIN][entry.entry_id]["entities"].append(self)

    @property
    def state(self):
        if self._key in ("timezone_id", "timezone_name", "timezone_abbreviation"):
            tz_id = self._api_data.get("last_timezone")
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
        else:
            last = self._api_data.get("last_address")
            if not last:
                return None
            return last.get(self._key)
