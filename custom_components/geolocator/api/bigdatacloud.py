import logging
from .base import GeoLocatorAPI

_LOGGER = logging.getLogger(__name__)

BIGDATACLOUD_URL = "https://api.bigdatacloud.net/data/reverse-geocode-client"


class BigDataCloudAPI(GeoLocatorAPI):
    """GeoLocator API using BigDataCloud (no key required)."""

    async def reverse_geocode(self, latitude, longitude, language="en"):
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "localityLanguage": "en"
        }
        data = await self._get_json(BIGDATACLOUD_URL, params)
        _LOGGER.debug("BigDataCloud response: %s", data)
        return data

    async def get_timezone(self, latitude, longitude, language="en"):
        return self.extract_timezone(await self.reverse_geocode(latitude, longitude))

    def extract_timezone(self, data):
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

    def extract_locality(self, data):
        return data.get("locality") or data.get("city") or self.extract_county(data)

    def extract_county(self, data):
        # adminLevel 6 is the county in the US; elsewhere it's the equivalent second-level division
        for item in data.get("localityInfo", {}).get("administrative", []):
            if item.get("adminLevel") == 6 and item.get("name"):
                return item["name"]
        return None

    def extract_state_long(self, data):
        return data.get("principalSubdivision")

    def extract_country(self, data):
        return data.get("countryName")
