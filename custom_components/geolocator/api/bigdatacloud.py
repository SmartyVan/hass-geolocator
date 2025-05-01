# custom_components/geolocator/api/bigdatacloud.py

import aiohttp
import logging
from .base import GeoLocatorAPI

_LOGGER = logging.getLogger(__name__)

BIGDATACLOUD_URL = "https://api.bigdatacloud.net/data/reverse-geocode-client"

class BigDataCloudAPI(GeoLocatorAPI):
    """GeoLocator API using BigDataCloud (no key required)."""

    def __init__(self):
        self._last_timezone_info = None

    async def reverse_geocode(self, latitude, longitude):
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "localityLanguage": "en"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(BIGDATACLOUD_URL, params=params) as resp:
                data = await resp.json()
                _LOGGER.debug("BigDataCloud response: %s", data)
                # Try to extract timezone from localityInfo.informative
                tz = None
                try:
                    informative = data.get("localityInfo", {}).get("informative", [])
                    for item in informative:
                        if item.get("description", "").lower() == "time zone":
                            tz = item.get("name")
                            break
                except Exception as e:
                    _LOGGER.warning("BigDataCloud: Failed to extract timezone: %s", e)

                self._last_timezone_info = {"id": tz} if tz else None
                return data

    async def get_timezone(self, latitude, longitude):
        if self._last_timezone_info:
            return self._last_timezone_info.get("id")
        return None

    def format_full_address(self, data):
        return data.get("locality", "") + ", " + data.get("principalSubdivision", "") + ", " + data.get("countryName", "")

    def extract_neighborhood(self, data):
        return None  # Not provided

    def extract_city(self, data):
        return data.get("locality")

    def extract_state_long(self, data):
        return data.get("principalSubdivision")

    def extract_country(self, data):
        return data.get("countryName")
