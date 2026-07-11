import logging

import aiohttp

from .base import GeoLocatorAPI
from ..const import DEFAULT_OSM_USER_AGENT, OSM_ATTRIBUTION

_LOGGER = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"


class OSMAPI(GeoLocatorAPI):
    """GeoLocator API using OpenStreetMap's Nominatim service.

    Complies with the Nominatim Usage Policy
    (https://operations.osmfoundation.org/policies/nominatim/):
    a single request is made per call (rate limiting is enforced by the
    coordinator, which hard-caps this provider at 1 request/second), a
    valid identifying User-Agent is always sent, and the ODbL attribution
    returned by the API (or a fallback notice) is exposed via
    ``extract_attribution`` for display alongside the data.
    """

    def __init__(self, user_agent: str | None = None):
        self.user_agent = user_agent or DEFAULT_OSM_USER_AGENT

    async def reverse_geocode(self, latitude, longitude, language="en"):
        headers = {
            "User-Agent": self.user_agent,
        }
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "jsonv2",
            "addressdetails": 1,
            "accept-language": language,
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(NOMINATIM_URL, params=params) as resp:
                data = await resp.json()
                _LOGGER.debug("Nominatim reverse geocode response: %s", data)
                return data

    async def get_timezone(self, latitude, longitude, language="en"):
        # Nominatim does not provide timezone info; the coordinator falls
        # back to the local timezonefinder library for this provider.
        return None

    def format_full_address(self, data):
        return data.get("display_name", "")

    def extract_neighborhood(self, data):
        return data.get("address", {}).get("neighbourhood")

    def extract_city(self, data):
        address = data.get("address", {})
        return (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("county")
        )

    def extract_state_long(self, data):
        return data.get("address", {}).get("state")

    def extract_country(self, data):
        return data.get("address", {}).get("country")

    def extract_attribution(self, data):
        return data.get("licence") or OSM_ATTRIBUTION
