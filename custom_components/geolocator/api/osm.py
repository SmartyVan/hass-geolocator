import aiohttp
from .base import GeoLocatorAPI

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

class OSMAPI(GeoLocatorAPI):
    """GeoLocator API using OpenStreetMap's Nominatim service."""

    def __init__(self, user_agent: str = "geo_locator_home_assistant"):
        self.user_agent = user_agent

    async def reverse_geocode(self, latitude, longitude):
        headers = {
            "User-Agent": self.user_agent
        }
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "jsonv2",
            "addressdetails": 1,
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(NOMINATIM_URL, params=params) as resp:
                return await resp.json()

    async def get_timezone(self, latitude, longitude):
        # OSM does not provide timezone info
        return None

    def format_full_address(self, data):
        return data.get("display_name", "")

    def extract_neighborhood(self, data):
        return data.get("address", {}).get("neighbourhood")

    def extract_city(self, data):
        return data.get("address", {}).get("city") or \
               data.get("address", {}).get("town") or \
               data.get("address", {}).get("village")

    def extract_state_long(self, data):
        return data.get("address", {}).get("state")

    def extract_country(self, data):
        return data.get("address", {}).get("country")
