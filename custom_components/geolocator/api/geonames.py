from .base import GeoLocatorAPI, GeoLocatorAPIError

GEONAMES_REVERSE_URL = "https://secure.geonames.org/findNearestAddressJSON"
GEONAMES_PLACE_URL = "https://secure.geonames.org/findNearbyPlaceNameJSON"
GEONAMES_TIMEZONE_URL = "https://secure.geonames.org/timezoneJSON"

# GeoNames status codes that mean "nothing here" rather than a failure
# (11 = record does not exist, 15 = no result found)
GEONAMES_NO_RESULT_CODES = (11, 15)

class GeoNamesAPI(GeoLocatorAPI):
    def __init__(self, session, username: str):
        super().__init__(session)
        self.username = username

    @staticmethod
    def _check_status(data):
        # GeoNames returns HTTP 200 with a status object for errors like bad username or quota exceeded
        status = data.get("status")
        if status and status.get("value") not in GEONAMES_NO_RESULT_CODES:
            raise GeoLocatorAPIError(f"GeoNames: {status.get('message')} (code {status.get('value')})")

    async def reverse_geocode(self, lat, lon, language="en"):
        reverse_data = await self._get_json(GEONAMES_REVERSE_URL, {"lat": lat, "lng": lon, "username": self.username})
        self._check_status(reverse_data)
        place_data = await self._get_json(GEONAMES_PLACE_URL, {"lat": lat, "lng": lon, "username": self.username, "cities": "cities500"})
        self._check_status(place_data)
        return {"reverse": reverse_data, "place": place_data}

    async def get_timezone(self, lat, lon, language="en"):
        params = {
            "lat": lat,
            "lng": lon,
            "username": self.username,
        }
        data = await self._get_json(GEONAMES_TIMEZONE_URL, params)
        self._check_status(data)
        return data.get("timezoneId")

    def _get_top_result(self, data):
        if "geonames" in data:
            return data.get("geonames", [{}])[0]
        elif "address" in data:
            return data["address"]
        return {}

    def format_full_address(self, data):
        reverse_top = self._get_top_result(data.get("reverse", {}))
        place_top = self._get_top_result(data.get("place", {}))

        # Combine street number + street (no comma)
        street_number = reverse_top.get("streetNumber")
        street = reverse_top.get("street")
        street_line = f"{street_number} {street}".strip() if street or street_number else None

        # City / locality with fallback
        placename = reverse_top.get("placename")
        if not placename:
            placename = place_top.get("name")  # Fallback to populated place name

        # Combine state + postal code (no comma)
        admin = reverse_top.get("adminCode1")
        postal = reverse_top.get("postalcode")
        region_line = f"{admin} {postal}".strip() if admin or postal else None

        country = place_top.get("countryName")

        # Final join with correct commas
        return ", ".join(filter(None, [street_line, placename, region_line, country]))


    def extract_locality(self, data):
        reverse_top = self._get_top_result(data.get("reverse", {}))
        locality = reverse_top.get("placename")

        if not locality:
            place_top = self._get_top_result(data.get("place", {}))
            locality = place_top.get("name") or place_top.get("adminName2")  # Fallback to nearby populated place name

        return locality

    def extract_state_long(self, data):
        # The address lookup only works in the US and returns nothing in rural areas,
        # so fall back to the nearby populated place
        reverse_top = self._get_top_result(data.get("reverse", {}))
        place_top = self._get_top_result(data.get("place", {}))
        return reverse_top.get("adminName1") or place_top.get("adminName1")

    def extract_country(self, data):
        place_top = self._get_top_result(data.get("place", {}))
        return place_top.get("countryName")
