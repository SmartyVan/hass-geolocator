class GeoLocatorAPI:
    """Abstract base class for geolocation APIs."""

    async def reverse_geocode(self, latitude: float, longitude: float, language: str = "en") -> dict:
        """Return a dict of address components."""
        raise NotImplementedError

    async def get_timezone(self, latitude: float, longitude: float, language: str = "en") -> str:
        """Return an IANA time zone string."""
        raise NotImplementedError

    def extract_attribution(self, data: dict) -> str | None:
        """Return an attribution string that must be displayed alongside this data, if required."""
        return None
