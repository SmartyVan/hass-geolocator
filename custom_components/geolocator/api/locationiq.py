import logging
from .base import GeoLocatorAPI, GeoLocatorAPIError

_LOGGER = logging.getLogger(__name__)

GEOCODE_URL = "https://us1.locationiq.com/v1/reverse"
TIMEZONE_URL = "https://us1.locationiq.com/v1/timezone"


class LocationIQAPI(GeoLocatorAPI):
    """LocationIQ reverse geocoding and timezone API (OpenStreetMap data)."""

    def __init__(self, session, api_key):
        super().__init__(session)
        self.api_key = api_key

    async def reverse_geocode(self, lat, lon, language="en"):
        params = {
            "key": self.api_key,
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1,
            "normalizeaddress": 1,
            "normalizecity": 1,  # fills "city" from town/village/hamlet when there is no city
            "accept-language": language,
        }
        try:
            data = await self._get_json(GEOCODE_URL, params)
        except GeoLocatorAPIError as e:
            # LocationIQ answers 404 "Unable to geocode" for places with no address (e.g. at sea)
            if str(e).startswith("HTTP 404"):
                return {}
            raise
        _LOGGER.debug("LocationIQ reverse geocode response: %s", data)
        return data

    async def get_timezone(self, lat, lon, language="en"):
        params = {"key": self.api_key, "lat": lat, "lon": lon}
        data = await self._get_json(TIMEZONE_URL, params)
        _LOGGER.debug("LocationIQ timezone response: %s", data)
        name = data.get("timezone", {}).get("name")
        # At sea LocationIQ returns nautical zones such as Etc/GMT+8, which have no DST.
        # Let the local timezonefinder fallback pick the nearby land zone instead, as with
        # the other providers.
        if name and name.startswith("Etc/"):
            return None
        return name

    def _address(self, data):
        return data.get("address", {})

    def format_full_address(self, data):
        addr = self._address(data)
        street = " ".join(p for p in (addr.get("house_number"), addr.get("road")) if p)
        region = " ".join(p for p in (addr.get("state"), addr.get("postcode")) if p)
        parts = [p for p in (street, addr.get("city"), region, addr.get("country")) if p]
        return ", ".join(parts) or data.get("display_name", "")

    def extract_neighborhood(self, data):
        return self._address(data).get("neighbourhood")

    def extract_locality(self, data):
        addr = self._address(data)
        for key in ("city", "town", "village", "hamlet", "county"):
            if addr.get(key):
                return addr[key]
        return None

    def extract_county(self, data):
        return self._address(data).get("county")

    def extract_state_long(self, data):
        return self._address(data).get("state")

    def extract_country(self, data):
        return self._address(data).get("country")
