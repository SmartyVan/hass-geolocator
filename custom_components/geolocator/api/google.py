import logging
import time

from .base import GeoLocatorAPI, GeoLocatorAPIError

_LOGGER = logging.getLogger(__name__)

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
TIMEZONE_URL = "https://maps.googleapis.com/maps/api/timezone/json"

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
