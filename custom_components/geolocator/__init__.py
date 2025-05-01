import logging
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_register_admin_service

from .const import DOMAIN, SERVICE_SET_TIMEZONE
from .api.google import GoogleMapsAPI
from .api.geonames import GeoNamesAPI
from .api.bigdatacloud import BigDataCloudAPI


_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async def async_set_home_timezone(call: ServiceCall):
        await hass.config.async_update(time_zone=call.data["time_zone"])

    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_SET_TIMEZONE,
        async_set_home_timezone,
        vol.Schema({"time_zone": cv.time_zone}),
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # _LOGGER.warning("GeoLocator: async_setup_entry() was triggered")

    config = entry.options if entry.options else entry.data

    provider = config.get("api_provider", "google")
    api_key = config.get("api_key", "")

    original_provider = entry.data.get("api_provider", "google")
    if entry.options and provider != original_provider:
        _LOGGER.info("GeoLocator: API provider changed from '%s' to '%s' via options", original_provider, provider)
    else:
        _LOGGER.info("GeoLocator: Using API provider: %s", provider)

    if provider == "google":
        api = GoogleMapsAPI(api_key)
    elif provider == "geonames":
        api = GeoNamesAPI(api_key)
    elif provider == "bigdatacloud":
        api = BigDataCloudAPI()

    else:
        raise ValueError(f"Unsupported API provider: {provider}")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "entry": entry,
        "last_address": None,
        "last_timezone": None,
        "entities": [],  # sensor instances will register here
    }

    async def async_update_location_service(call: ServiceCall | None = None):
        lat = hass.config.latitude
        lon = hass.config.longitude
        _LOGGER.debug("GeoLocator: Fetching reverse geocode for lat=%s, lon=%s", lat, lon)

        try:
            geocode_raw = await api.reverse_geocode(lat, lon)
            timezone_id = await api.get_timezone(lat, lon)

            address_data = {
                "current_address": api.format_full_address(geocode_raw),
                "neighborhood": api.extract_neighborhood(geocode_raw),
                "city": api.extract_city(geocode_raw),
                "state": api.extract_state_long(geocode_raw),
                "country": api.extract_country(geocode_raw),
            }

            hass.data[DOMAIN][entry.entry_id]["last_address"] = address_data
            hass.data[DOMAIN][entry.entry_id]["last_timezone"] = timezone_id

            _LOGGER.info("GeoLocator: Location updated: %s", address_data)
            _LOGGER.info("GeoLocator: Timezone ID: %s", timezone_id)

            # Update HA system timezone if changed
            if timezone_id:
                await hass.config.async_update(time_zone=timezone_id)

            # Force refresh of sensor entities
            for entity in hass.data[DOMAIN][entry.entry_id].get("entities", []):
                entity.async_write_ha_state()

            _LOGGER.debug("GeoLocator: Updated %d sensor entities", len(hass.data[DOMAIN][entry.entry_id]["entities"]))

        except Exception as e:
            _LOGGER.exception("GeoLocator: Failed to update location: %s", e)

    hass.data[DOMAIN][entry.entry_id]["update_func"] = async_update_location_service
    hass.services.async_register(DOMAIN, "update_location", async_update_location_service)

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    await async_update_location_service()

    # Enable automatic reload when options are updated
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))


    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload GeoLocator config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload GeoLocator config entry when options are updated."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
