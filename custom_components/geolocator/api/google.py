import logging
import time

from .base import GeoLocatorAPI, GeoLocatorAPIError

_LOGGER = logging.getLogger(__name__)

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
TIMEZONE_URL = "https://maps.googleapis.com/maps/api/timezone/json"

# Only ask for address-type results. Points of interest can carry wrong data
# (e.g. a business near a US address listed in another country). The plus_code
# result is kept because its locality is the nearest named place, which is more
# accurate in rural areas than the postal town on the road's result.
RESULT_TYPES = "|".join((
    "street_address",
    "route",
    "neighborhood",
    "locality",
    "administrative_area_level_2",
    "administrative_area_level_1",
    "country",
    "plus_code",
))

class GoogleMapsAPI(GeoLocatorAPI):
    def __init__(self, session, api_key):
        super().__init__(session)
        self.api_key = api_key

    @staticmethod
    def _check_status(data, api_name):
        # Google returns HTTP 200 with a status field for errors like REQUEST_DENIED
        status = data.get("status")
        if status not in ("OK", "ZERO_RESULTS"):
            raise GeoLocatorAPIError(f"Google {api_name}: {status}: {data.get('errorMessage') or data.get('error_message', '')}")

    async def reverse_geocode(self, lat, lon, language="en"):
        params = {
            "latlng": f"{lat},{lon}",
            "result_type": RESULT_TYPES,
            "key": self.api_key,
            "language": language,
        }
        data = await self._get_json(GEOCODE_URL, params)
        self._check_status(data, "Geocoding API")
        return data

    async def get_timezone(self, lat, lon, language="en"):
        params = {
            "location": f"{lat},{lon}",
            "timestamp": int(time.time()),
            "key": self.api_key,
            "language": language,
        }
        data = await self._get_json(TIMEZONE_URL, params)
        _LOGGER.debug("Google Timezone API response: %s", data)
        self._check_status(data, "Time Zone API")
        return data.get("timeZoneId")

    def _get_component(self, data, type_name, results=None):
        for result in data.get("results", []) if results is None else results:
            for comp in result.get("address_components", []):
                if type_name in comp.get("types", []):
                    return comp.get("long_name")
        return None

    @staticmethod
    def _is_plus_code(result):
        return "plus_code" in result.get("types", [])

    def format_full_address(self, data):
        # The plus_code result's address is just the code (e.g. "366X+2X Elk Lake"),
        # which the Plus Code sensor already shows
        for result in data.get("results", []):
            if not self._is_plus_code(result):
                return result.get("formatted_address", "")
        return ""

    def extract_neighborhood(self, data):
        return self._get_component(data, "neighborhood")

    def extract_locality(self, data):
        # Nearest named place from the plus_code result first. Outside towns the
        # road's locality is its postal town, which can be far away
        # (e.g. "Tuolumne Meadows" for a campground in Yosemite Valley).
        plus_code_results = [r for r in data.get("results", []) if self._is_plus_code(r)]
        for type_name in ("locality", "postal_town"):
            value = self._get_component(data, type_name, plus_code_results)
            if value:
                return value

        # Then city, then progressively broader areas for rural locations.
        # postal_town is what Google uses for towns in the UK and Sweden.
        for type_name in (
            "locality",
            "postal_town",
            "sublocality",
            "administrative_area_level_3",
            "administrative_area_level_2",
        ):
            value = self._get_component(data, type_name)
            if value:
                return value
        return None

    def extract_county(self, data):
        return self._get_component(data, "administrative_area_level_2")

    def extract_state_long(self, data):
        return self._get_component(data, "administrative_area_level_1")

    def extract_country(self, data):
        return self._get_component(data, "country")
