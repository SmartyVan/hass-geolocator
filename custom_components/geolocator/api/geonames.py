import aiohttp
from .base import GeoLocatorAPI

GEONAMES_REVERSE_URL = "http://api.geonames.org/findNearestAddressJSON"
GEONAMES_PLACE_URL = "http://api.geonames.org/findNearbyPlaceNameJSON"
GEONAMES_TIMEZONE_URL = "http://api.geonames.org/timezoneJSON"

class GeoNamesAPI(GeoLocatorAPI):
    def __init__(self, username: str):
        self.username = username

    async def reverse_geocode(self, lat, lon):
        async with aiohttp.ClientSession() as session:
            reverse_resp = await session.get(GEONAMES_REVERSE_URL, params={"lat": lat, "lng": lon, "username": self.username})
            place_resp = await session.get(GEONAMES_PLACE_URL, params={"lat": lat, "lng": lon, "username": self.username})
            reverse_data = await reverse_resp.json()
            place_data = await place_resp.json()
            return {"reverse": reverse_data, "place": place_data}

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
        if "geonames" in data:
            return data.get("geonames", [{}])[0]
        elif "address" in data:
            return data["address"]
        return {}

    def format_full_address(self, data):
        reverse_top = self._get_top_result(data["reverse"])
        place_top = self._get_top_result(data["place"])

        # Combine street number + street (no comma)
        street_number = reverse_top.get("streetNumber")
        street = reverse_top.get("street")
        street_line = f"{street_number} {street}".strip() if street or street_number else None

        # City / locality
        placename = reverse_top.get("placename")

        # Combine state + postal code (no comma)
        admin = reverse_top.get("adminCode1")
        postal = reverse_top.get("postalcode")
        region_line = f"{admin} {postal}".strip() if admin or postal else None

        country = place_top.get("countryName")

        # Final join with correct commas
        return ", ".join(filter(None, [street_line, placename, region_line, country]))

    def extract_city(self, data):
        place_top = self._get_top_result(data["place"])
        return place_top.get("name")

    def extract_state_long(self, data):
        reverse_top = self._get_top_result(data["reverse"])
        return reverse_top.get("adminName1")

    def extract_country(self, data):
        place_top = self._get_top_result(data["place"])
        return place_top.get("countryName")
