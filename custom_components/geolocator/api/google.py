import aiohttp
from .base import GeoLocatorAPI

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
TIMEZONE_URL = "https://maps.googleapis.com/maps/api/timezone/json"

class GoogleMapsAPI(GeoLocatorAPI):
    def __init__(self, api_key, language="en"):
        self.api_key = api_key

    async def reverse_geocode(self, lat, lon, language="en"):
        async with aiohttp.ClientSession() as session:
            params = {
                "latlng": f"{lat},{lon}",
                "key": self.api_key,
                "language": language,
            }
            async with session.get(GEOCODE_URL, params=params) as resp:
                return await resp.json()

    async def get_timezone(self, lat, lon, language="en"):
        import time
        import logging
        _LOGGER = logging.getLogger(__name__)

        timestamp = int(time.time())
        async with aiohttp.ClientSession() as session:
            params = {
                "location": f"{lat},{lon}",
                "timestamp": timestamp,
                "key": self.api_key,
                "language": language,
            }
            async with session.get(TIMEZONE_URL, params=params) as resp:
                data = await resp.json()
                _LOGGER.debug("Google Timezone API response: %s", data)
                return data.get("timeZoneId")

    def _get_component(self, data, type_name):
        for result in data.get("results", []):
            for comp in result.get("address_components", []):
                if type_name in comp.get("types", []):
                    return comp.get("long_name")
        return None

    def format_full_address(self, data):
        if not data.get("results"):
            return ""
        return data["results"][0].get("formatted_address", "")

    def extract_neighborhood(self, data):
        return self._get_component(data, "neighborhood")

    def extract_city(self, data):
        return self._get_component(data, "locality")

    def extract_state_long(self, data):
        return self._get_component(data, "administrative_area_level_1")

    def extract_country(self, data):
        return self._get_component(data, "country")
