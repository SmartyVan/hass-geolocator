import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from openlocationcode import openlocationcode as olc

from .const import API_PROVIDER_META, DOMAIN, OSM_MIN_REQUEST_INTERVAL, SERVICE_SET_TIMEZONE

_LOGGER = logging.getLogger(__name__)

ADDRESS_KEYS = ("current_address", "city", "state", "country", "attribution")


class GeoLocatorUpdateCoordinator(DataUpdateCoordinator):
    """Coordinates GeoLocator updates.

    This integration never polls on a timer (by design, see README) -
    every refresh is triggered manually via the ``geolocator.update_location``
    service, so ``update_interval`` is left at ``None`` and callers use
    ``async_request_refresh``.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        api,
        provider: str,
        max_requests_per_second: float,
        max_requests_per_day: int,
    ) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        self.api = api
        self.provider = provider
        self._max_requests_per_second = max_requests_per_second
        self._max_requests_per_day = max_requests_per_day
        self._last_request_time = 0.0

    @property
    def _min_request_interval(self) -> float:
        min_interval = 0.0
        if self._max_requests_per_second > 0:
            min_interval = max(min_interval, 1.0 / self._max_requests_per_second)
        if self._max_requests_per_day > 0:
            min_interval = max(min_interval, 86400.0 / self._max_requests_per_day)
        if self.provider == "osm":
            # Nominatim Usage Policy hard limit: never exceed 1 request/second,
            # regardless of the user's configured rate limits.
            min_interval = max(min_interval, OSM_MIN_REQUEST_INTERVAL)
        return min_interval

    async def _async_update_data(self) -> dict:
        try:
            return await self._async_fetch()
        except Exception as err:  # noqa: BLE001 - never fail the coordinator; fall back gracefully
            _LOGGER.exception("GeoLocator: Unexpected error during location update: %s", err)
            return self.data or {}

    async def _async_fetch(self) -> dict:
        hass = self.hass
        lat = hass.config.latitude
        lon = hass.config.longitude
        plus_code = olc.encode(lat, lon)

        previous = self.data or {}
        address_data = {key: previous.get(key) for key in ADDRESS_KEYS}

        timezone_id = None
        source = None

        if self.api is not None:
            try:
                now = time.monotonic()
                min_interval = self._min_request_interval
                elapsed = now - self._last_request_time

                if elapsed < min_interval:
                    _LOGGER.warning(
                        "GeoLocator: API call rate limited. Last request was %0.2fs ago, "
                        "min interval is %0.2fs. Skipping API call.",
                        elapsed,
                        min_interval,
                    )
                else:
                    # Update request time immediately to prevent concurrent spam
                    self._last_request_time = now

                    user_language = hass.config.language or "en"
                    geocode_raw = await self.api.reverse_geocode(lat, lon, user_language)
                    timezone_id = await self.api.get_timezone(lat, lon, user_language)

                    address_data = {
                        "current_address": self.api.format_full_address(geocode_raw),
                        "city": self.api.extract_city(geocode_raw),
                        "state": self.api.extract_state_long(geocode_raw),
                        "country": self.api.extract_country(geocode_raw),
                        "attribution": self.api.extract_attribution(geocode_raw),
                    }
                    source = API_PROVIDER_META[self.provider]["name"]
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("GeoLocator: Failed to update location: %s", err)

        if not timezone_id:
            tz = await self._async_local_timezone(lat, lon)
            if tz:
                timezone_id = tz
                source = "Local Fallback"
            else:
                source = "Error"

        full_name = await self._async_full_timezone_name(
            timezone_id, hass.config.language or "en-US"
        )

        # Call the timezone-setting service with the computed timezone_id
        if timezone_id:
            try:
                await hass.services.async_call(
                    DOMAIN,
                    SERVICE_SET_TIMEZONE,
                    {"timezone": timezone_id},
                    blocking=True,
                )
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("GeoLocator: Failed to call set_home_timezone: %s", err)

        return {
            **address_data,
            "plus_code": plus_code,
            "timezone_id": timezone_id,
            "timezone_source": source,
            "timezone_full": full_name,
        }

    async def _async_local_timezone(self, lat: float, lon: float) -> str | None:
        def _find_timezone():
            from timezonefinder import TimezoneFinder

            tf = TimezoneFinder(in_memory=True)
            try:
                return tf.timezone_at(lat=lat, lng=lon)
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("GeoLocator: Exception while finding timezone: %s", err)
                return None

        return await self.hass.async_add_executor_job(_find_timezone)

    async def _async_full_timezone_name(
        self, timezone_id: str | None, user_locale: str
    ) -> str | None:
        if not timezone_id:
            return None

        try:
            tz = ZoneInfo(timezone_id)
            dt = datetime.now(tz)

            def _get_full_timezone_name():
                from babel.core import Locale, UnknownLocaleError
                from babel.dates import get_timezone_name

                try:
                    loc = Locale.parse(user_locale, sep="-")
                except UnknownLocaleError:
                    loc = Locale.parse("en-US", sep="-")

                return get_timezone_name(dt, locale=loc)

            return await self.hass.async_add_executor_job(_get_full_timezone_name)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("GeoLocator: Failed to get full timezone name: %s", err)
            return None
