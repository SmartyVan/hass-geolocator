import logging
from .base import GeoLocatorAPI

_LOGGER = logging.getLogger(__name__)
GEOCODE_URL = "https://api.opencagedata.com/geocode/v1/json"

class OpenCageAPI(GeoLocatorAPI):
    def __init__(self, session, api_key):
        super().__init__(session)
        self.api_key = api_key

    async def reverse_geocode(self, lat, lon, language="en"):
        params = {
            "q": f"{lat},{lon}",
            "key": self.api_key,
            "language": language,
        }
        data = await self._get_json(GEOCODE_URL, params)
        _LOGGER.debug("OpenCage reverse geocode response: %s", data)
        return data

    async def get_timezone(self, lat, lon, language="en"):
        return self.extract_timezone(await self.reverse_geocode(lat, lon, language))

    def extract_timezone(self, data):
        try:
            return data["results"][0]["annotations"]["timezone"]["name"]
        except (IndexError, KeyError):
            _LOGGER.warning("OpenCage: Failed to extract timezone from response")
            return None

    def format_full_address(self, data):
        try:
            return data["results"][0]["formatted"]
        except (IndexError, KeyError):
            return ""

    def extract_city(self, data):
        try:
            return data["results"][0]["components"].get("city") or \
                   data["results"][0]["components"].get("town") or \
                   data["results"][0]["components"].get("village") or \
                   data["results"][0]["components"].get("county")
        except (IndexError, KeyError):
            return None

    def extract_state_long(self, data):
        try:
            return data["results"][0]["components"].get("state")
        except (IndexError, KeyError):
            return None

    def extract_country(self, data):
        try:
            return data["results"][0]["components"].get("country")
        except (IndexError, KeyError):
            return None
