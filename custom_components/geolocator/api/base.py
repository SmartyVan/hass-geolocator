class GeoLocatorAPI:
    """Abstract base class for geolocation APIs."""

    async def reverse_geocode(self, latitude: float, longitude: float) -> dict:
        """Return a dict of address components."""
        raise NotImplementedError

    async def get_timezone(self, latitude: float, longitude: float) -> str:
        """Return an IANA time zone string."""
        raise NotImplementedError
