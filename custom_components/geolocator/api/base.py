import aiohttp

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)


class GeoLocatorAPIError(Exception):
    """The provider returned an error (bad key, quota exceeded, etc.)."""


class GeoLocatorAPI:
    """Abstract base class for geolocation APIs."""

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    async def _get_json(self, url: str, params: dict, headers: dict | None = None) -> dict:
        """GET a JSON response, raising GeoLocatorAPIError on HTTP errors."""
        async with self._session.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT) as resp:
            try:
                data = await resp.json(content_type=None)
            except ValueError:
                data = {}
            if resp.status >= 400:
                message = data.get("status", {}).get("message") if isinstance(data.get("status"), dict) else None
                message = message or data.get("description") or data.get("error_message") or data.get("error") or resp.reason
                raise GeoLocatorAPIError(f"HTTP {resp.status}: {message}")
            return data

    async def reverse_geocode(self, latitude: float, longitude: float, language: str = "en") -> dict:
        """Return a dict of address components."""
        raise NotImplementedError

    async def get_timezone(self, latitude: float, longitude: float, language: str = "en") -> str:
        """Return an IANA time zone string."""
        raise NotImplementedError

    def extract_timezone(self, data: dict) -> str | None:
        """Return the IANA time zone from a reverse_geocode response, if the provider includes it."""
        return None
