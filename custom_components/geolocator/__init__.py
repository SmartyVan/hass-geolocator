import logging
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service import async_register_admin_service

from .const import DOMAIN, SERVICE_SET_TIMEZONE, API_PROVIDER_META
from .api.google import GoogleMapsAPI
from .api.opencage import OpenCageAPI
from .api.locationiq import LocationIQAPI
from .api.geonames import GeoNamesAPI
from .api.bigdatacloud import BigDataCloudAPI

from timezonefinder import TimezoneFinder

from openlocationcode import openlocationcode as olc

from pygeomag import GeoMag, calculate_decimal_year

from babel.dates import get_timezone_name
from zoneinfo import ZoneInfo
from datetime import datetime

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

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

    session = async_get_clientsession(hass)
    if provider == "google":
        api = GoogleMapsAPI(session, api_key)
    elif provider == "opencage":
        api = OpenCageAPI(session, api_key)
    elif provider == "locationiq":
        api = LocationIQAPI(session, api_key)
    elif provider == "geonames":
        api = GeoNamesAPI(session, api_key)
    elif provider == "bigdatacloud":
        api = BigDataCloudAPI(session)
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
                    user_language = hass.config.language or "en"
                    geocode_raw = await api.reverse_geocode(lat, lon, user_language)
                    # OpenCage and BigDataCloud include the timezone in the geocode response,
                    # so only make a separate timezone request when it's not there
                    timezone_id = api.extract_timezone(geocode_raw) or await api.get_timezone(lat, lon, user_language)

                    address_data = {
                        "current_address": api.format_full_address(geocode_raw),
                        # Key stays "city" so existing entity IDs are preserved
                        "city": api.extract_locality(geocode_raw),
                        "county": api.extract_county(geocode_raw),
                        "state": api.extract_state_long(geocode_raw),
                        "country": api.extract_country(geocode_raw),
                        "plus_code": plus_code,
                    }
                    source = API_PROVIDER_META[provider]["name"]

                except Exception as e:
                    _LOGGER.warning("GeoLocator: %s lookup failed, falling back to local timezone: %s", API_PROVIDER_META[provider]["name"], str(e) or type(e).__name__)
                    address_data = {}
                    timezone_id = None

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

            # Magnetic declination from the World Magnetic Model (computed locally, works offline)
            def _calculate_declination():
                geo_mag = GeoMag()  # bundled WMM coefficients (WMM2025, valid 2025.0-2030.0)
                result = geo_mag.calculate(
                    glat=lat,
                    glon=lon,
                    alt=(hass.config.elevation or 0) / 1000,  # metres -> km
                    time=calculate_decimal_year(datetime.now()),
                )
                return round(result.d, 2)

            try:
                declination = await hass.async_add_executor_job(_calculate_declination)
            except Exception as e:
                _LOGGER.warning("GeoLocator: Failed to calculate magnetic declination: %s", e)
                declination = None

            # Add full timezone name using Babel and zoneinfo
            try:
                if timezone_id:
                    tz = ZoneInfo(timezone_id)
                    dt = datetime.now(tz)
                    user_locale = hass.config.language or "en-US"
                    is_dst = dt.dst() is not None and dt.dst().total_seconds() != 0
                    zone_variant = 'daylight' if is_dst else 'standard'

                    def _get_full_timezone_name():
                        from babel.dates import get_timezone, get_timezone_name
                        from babel.core import Locale, UnknownLocaleError

                        tzinfo = get_timezone(timezone_id)

                        try:
                            loc = Locale.parse(user_locale, sep='-')
                        except UnknownLocaleError:
                            loc = Locale.parse("en-US", sep='-')

                        return get_timezone_name(dt, locale=loc)

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
            hass.data[DOMAIN][entry.entry_id]["magnetic_declination"] = declination

            # Only write the HA core config when the timezone actually changed
            if timezone_id and timezone_id != hass.config.time_zone:
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
    # Let HA run the unload callbacks; calling unload/setup directly added another update listener on every reload
    await hass.config_entries.async_reload(entry.entry_id)
