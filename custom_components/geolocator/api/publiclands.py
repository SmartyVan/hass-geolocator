import logging
import async_timeout
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

ATTRIBUTE_KEYS = [
    "Unit_Nm",
    "Pub_Access",
    "MngTp_Desc",
    "MngNm_Desc",
    "DesTp_Desc",
]

ACCESS_MAP = {
    "OA": "Open to the Public",
    "RA": "Restricted Access",
    "XA": "Closed to the Public",
    "PA": "Public Access by Permit",
    "TA": "Temporary Access Allowed",
    "UK": "Unknown",
}

async def fetch_public_lands_data(hass, lat, lon) -> dict:
    url = (
        f"https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/"
        f"PADUS_Public_Access/FeatureServer/0/query"
        f"?geometry={lon},{lat}&geometryType=esriGeometryPoint"
        f"&inSR=4326&outFields=Unit_Nm,Pub_Access,MngTp_Desc,MngNm_Desc,DesTp_Desc"
        f"&returnGeometry=false&f=json"
    )

    session = async_get_clientsession(hass)
    try:
        async with async_timeout.timeout(10):
            response = await session.get(url)
            data = await response.json()

        if data.get("features"):
            attributes = data["features"][0]["attributes"]
            # Map Pub_Access code to readable form
            if "Pub_Access" in attributes:
                attributes["Pub_Access"] = ACCESS_MAP.get(attributes["Pub_Access"], "Unknown Access Type")
            return attributes
        else:
            _LOGGER.warning("GeoLocator: No public lands data found")
            return {}

    except Exception as e:
        _LOGGER.error("GeoLocator: Error fetching public lands data: %s", e)
        return {}
