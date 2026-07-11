import logging
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_register_admin_service

from .const import (
    DOMAIN,
    SERVICE_SET_TIMEZONE,
    API_PROVIDER_META,
    CONF_API_PROVIDER,
    CONF_API_KEY,
    CONF_USER_AGENT,
    CONF_MAX_REQUESTS_PER_SECOND,
    CONF_MAX_REQUESTS_PER_DAY,
    DEFAULT_OSM_USER_AGENT,
)
from .api.google import GoogleMapsAPI
from .api.opencage import OpenCageAPI
from .api.geonames import GeoNamesAPI
from .api.bigdatacloud import BigDataCloudAPI
from .api.osm import OSMAPI
from .coordinator import GeoLocatorUpdateCoordinator

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
    provider = config.get(CONF_API_PROVIDER, "google")
    api_key = config.get(CONF_API_KEY, "")
    user_agent = config.get(CONF_USER_AGENT) or DEFAULT_OSM_USER_AGENT

    try:
        max_requests_per_second = float(config.get(CONF_MAX_REQUESTS_PER_SECOND, 0.0) or 0.0)
    except (TypeError, ValueError):
        max_requests_per_second = 0.0

    try:
        max_requests_per_day = int(config.get(CONF_MAX_REQUESTS_PER_DAY, 0) or 0)
    except (TypeError, ValueError):
        max_requests_per_day = 0

    original_provider = entry.data.get(CONF_API_PROVIDER, "google")
    if entry.options and provider != original_provider:
        _LOGGER.info("GeoLocator: API provider changed from '%s' to '%s' via options", original_provider, provider)
    else:
        _LOGGER.info("GeoLocator: Using API provider: %s", provider)

    if provider == "google":
        api = GoogleMapsAPI(api_key)
    elif provider == "opencage":
        api = OpenCageAPI(api_key)
    elif provider == "geonames":
        api = GeoNamesAPI(api_key)
    elif provider == "bigdatacloud":
        api = BigDataCloudAPI()
    elif provider == "osm":
        api = OSMAPI(user_agent=user_agent)
    elif provider == "offline":
        api = None
    else:
        raise ValueError(f"Unsupported API provider: {provider}")

    coordinator = GeoLocatorUpdateCoordinator(
        hass,
        api=api,
        provider=provider,
        max_requests_per_second=max_requests_per_second,
        max_requests_per_day=max_requests_per_day,
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "entry": entry,
        "coordinator": coordinator,
    }

    await coordinator.async_config_entry_first_refresh()

    async def async_update_location_service(call: ServiceCall | None = None):
        await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, "update_location", async_update_location_service)

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

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
