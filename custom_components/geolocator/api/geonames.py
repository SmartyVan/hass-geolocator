import aiohttp
from .base import GeoLocatorAPI

GEONAMES_REVERSE_URL = "http://api.geonames.org/findNearbyPlaceNameJSON"
GEONAMES_TIMEZONE_URL = "http://api.geonames.org/timezoneJSON"

class GeoNamesAPI(GeoLocatorAPI):
    def __init__(self, username: str):
        self.username = username

    async def reverse_geocode(self, lat, lon):
        params = {
            "lat": lat,
            "lng": lon,
            "username": self.username,
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(GEONAMES_REVERSE_URL, params=params) as resp:
                return await resp.json()

    async def get_timezone(self, lat, lon):
        params = {
            "lat": lat,
            "lng": lon,
            "username": self.username,
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(GEONAMES_TIMEZONE_URL, params=params) as resp:
                data = await resp.json()
                return data.get("timezoneId")

    def _get_top_result(self, data):
        return data.get("geonames", [{}])[0]

    def format_full_address(self, data):
        top = self._get_top_result(data)
        parts = [top.get("name"), top.get("adminName1"), top.get("countryName")]
        return ", ".join(p for p in parts if p)

    def extract_neighborhood(self, data):
        return None  # GeoNames doesn't provide this

    def extract_city(self, data):
        return self._get_top_result(data).get("name")

    def extract_state_long(self, data):
        return self._get_top_result(data).get("adminName1")

    def extract_country(self, data):
        return self._get_top_result(data).get("countryName")
