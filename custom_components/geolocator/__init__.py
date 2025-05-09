import logging
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_register_admin_service

from .const import DOMAIN, SERVICE_SET_TIMEZONE, API_PROVIDER_META
from .api.google import GoogleMapsAPI
from .api.geonames import GeoNamesAPI
from .api.bigdatacloud import BigDataCloudAPI

from timezonefinder import TimezoneFinder

from openlocationcode import openlocationcode as olc

from babel.dates import get_timezone_name
from zoneinfo import ZoneInfo
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async def async_set_home_timezone(call: ServiceCall):
        await hass.config.async_update(time_zone=call.data["timezone"])

    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_SET_TIMEZONE,
        async_set_home_timezone,
        vol.Schema({"timezone": cv.time_zone}),
    )
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
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
    elif provider == "offline":
        api = None
    else:
        raise ValueError(f"Unsupported API provider: {provider}")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "entry": entry,
        "last_address": None,
        "last_timezone": None,
        "last_timezone_source": None,
        "entities": [],
    }

    async def async_update_location_service(call: ServiceCall | None = None):
        lat = hass.config.latitude
        lon = hass.config.longitude
        _LOGGER.debug("GeoLocator: Fetching location for lat=%s, lon=%s", lat, lon)

        try:
            address_data = {}
            timezone_id = None
            source = None
            plus_code = olc.encode(lat, lon)

            if api is not None:
                try:
                    geocode_raw = await api.reverse_geocode(lat, lon)
                    timezone_id = await api.get_timezone(lat, lon)

                    address_data = {
                        "current_address": api.format_full_address(geocode_raw),
                        "city": api.extract_city(geocode_raw),
                        "state": api.extract_state_long(geocode_raw),
                        "country": api.extract_country(geocode_raw),
                        "plus_code": plus_code,
                    }
                    source = API_PROVIDER_META[provider]["name"]

                except Exception as e:
                    _LOGGER.warning("GeoLocator: Failed to update location: %s", e)

            if not timezone_id:
                try:
                    def _find_timezone():
                        tf = TimezoneFinder(in_memory=True)
                        try:
                            return tf.timezone_at(lat=lat, lng=lon)
                        except Exception as e:
                            _LOGGER.warning("GeoLocator: Exception while finding timezone: %s", e)
                            return None

                    tz = await hass.async_add_executor_job(_find_timezone)
                    if tz:
                        timezone_id = tz
                        source = "Local Fallback"
                    else:
                        source = "Error"
                except Exception as e:
                    _LOGGER.warning("GeoLocator: Failed to find local timezone: %s", e)

            # Add full timezone name using Babel and zoneinfo
            try:
                if timezone_id:
                    tz = ZoneInfo(timezone_id)
                    dt = datetime.now(tz)
                    locale = str(hass.config.language or "en_US")
                    is_dst = dt.dst() is not None and dt.dst().total_seconds() != 0
                    zone_variant = 'daylight' if is_dst else 'standard'
                    def _get_full_timezone_name():
                        from babel.dates import get_timezone
                        tzinfo = get_timezone(timezone_id)
                        from babel.core import Locale
                        loc = Locale.parse(locale)
                        return get_timezone_name(
                            dt,
                            locale=loc
                        )
                    full_name = await hass.async_add_executor_job(_get_full_timezone_name)
                else:
                    full_name = None
            except Exception as e:
                _LOGGER.warning("GeoLocator: Failed to get full timezone name: %s", e)
                full_name = None

            hass.data[DOMAIN][entry.entry_id]["last_address"] = address_data
            hass.data[DOMAIN][entry.entry_id]["last_timezone"] = timezone_id
            hass.data[DOMAIN][entry.entry_id]["last_timezone_source"] = source
            hass.data[DOMAIN][entry.entry_id]["last_plus_code"] = plus_code
            hass.data[DOMAIN][entry.entry_id]["timezone_full"] = full_name

            # Call the timezone-setting service with the computed timezone_id
            if timezone_id:
                try:
                    await hass.services.async_call(
                        DOMAIN,
                        SERVICE_SET_TIMEZONE,
                        {"timezone": timezone_id},
                        blocking=True
                    )
                except Exception as e:
                    _LOGGER.error("GeoLocator: Failed to call set_home_timezone: %s", e)

            for entity in hass.data[DOMAIN][entry.entry_id]["entities"]:
                entity.async_schedule_update_ha_state(True)

        except Exception as e:
            _LOGGER.exception("GeoLocator: Unexpected error during location update: %s", e)


    hass.data[DOMAIN][entry.entry_id]["update_func"] = async_update_location_service
    hass.services.async_register(DOMAIN, "update_location", async_update_location_service)

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    await async_update_location_service()
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
