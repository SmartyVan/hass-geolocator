# custom_components/geolocator/const.py

DOMAIN = "geolocator"

CONF_API_PROVIDER = "api_provider"
CONF_API_KEY = "api_key"
CONF_MAX_REQUESTS_PER_SECOND = "max_requests_per_second"
CONF_MAX_REQUESTS_PER_DAY = "max_requests_per_day"

SERVICE_UPDATE_LOCATION = "update_location"
SERVICE_SET_TIMEZONE = "set_home_timezone"


ATTR_LATITUDE = "latitude"
ATTR_LONGITUDE = "longitude"
ATTR_TIMESTAMP = "timestamp"

TIMEZONE_SENSOR = "current_timezone"
LOCATION_SENSOR = "current_location"

API_PROVIDER_META = {
    "google": {"name": "Google Maps", "needs_key": True},
    "opencage": {"name": "OpenCage", "needs_key": True},
    "geonames": {"name": "GeoNames", "needs_key": True},
    "bigdatacloud": {"name": "BigDataCloud", "needs_key": False},
    "offline": {"name": "Offline", "needs_key": False},
}