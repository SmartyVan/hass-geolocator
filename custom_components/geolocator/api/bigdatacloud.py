import aiohttp
import logging
from .base import GeoLocatorAPI

_LOGGER = logging.getLogger(__name__)

BIGDATACLOUD_URL = "https://api.bigdatacloud.net/data/reverse-geocode-client"


class BigDataCloudAPI(GeoLocatorAPI):
    """GeoLocator API using BigDataCloud (no key required)."""

    def __init__(self):
        pass  # Removed _last_timezone_info; no longer needed

    async def reverse_geocode(self, latitude, longitude, language="en"):
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "localityLanguage": "en"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(BIGDATACLOUD_URL, params=params) as resp:
                data = await resp.json()
                _LOGGER.debug("BigDataCloud response: %s", data)
                return data

    async def get_timezone(self, latitude, longitude, language="en"):
        data = await self.reverse_geocode(latitude, longitude)
        informative = data.get("localityInfo", {}).get("informative", [])
        for item in informative:
            if item.get("description", "").lower() == "time zone":
                return item.get("name")
        return None

    def format_full_address(self, data):
        # Handle missing parts safely
        locality = data.get("locality", "")
        state = data.get("principalSubdivision", "")
        country = data.get("countryName", "")
        parts = [p for p in [locality, state, country] if p]
        return ", ".join(parts)

    def extract_neighborhood(self, data):
        return None  # Not available from BigDataCloud

    def extract_city(self, data):
        return data.get("locality")

    def extract_state_long(self, data):
        return data.get("principalSubdivision")

    def extract_country(self, data):
        return data.get("countryName")
