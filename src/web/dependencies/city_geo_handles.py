import asyncio
import logging

import aiohttp

logger = logging.getLogger(__name__)


def extract_city_name(data: dict) -> str | None:
    raw = (
            data["address"]["city"]
            or data["address"]["town"]
            or data["address"]["village"]
            or data["address"]["municipality"]
            or data["address"]["state_district"]
    )

    if not raw:
        return None

    replacements = [
        "городской округ ",
        "поселение ",
        "муниципальный район ",
        "район ",
    ]
    for prefix in replacements:
        if raw.lower().startswith(prefix):
            return raw[len(prefix):].strip()
    return raw

def check_city(data: dict) -> dict | None:
    country_code = data.get("address", {}).get("country_code")
    if country_code != "ru":
        return None
    return data

async def get_city_from_geo(
        lat: float,
        lon: float,
        session: aiohttp.ClientSession,
) -> dict | None:
    """
    # https://nominatim.openstreetmap.org/reverse?lat=55.78481894445758&lon=37.84803289439989&format=json
    """
    try:
        async with session.get(
            f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json",
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            if response.status != 200:
                logger.warning(f"OpenStreetMap returned status {response.status}")
                return None
            data = await response.json()
            logger.info(f"OpenStreetMap DATA = {data}")
            if data.get("error"):
                return None
            return data
    except asyncio.TimeoutError:
        logger.error("OpenStreetMap request timed out")
        return None
    except Exception as e:
        logger.exception(f"OpenStreetMap request failed: {e}")
        return None

async def get_geo_from_city(
        city: str,
        session: aiohttp.ClientSession,
) -> dict | None:
    """
    https://nominatim.openstreetmap.org/search.php?q=Москва&format=jsonv2
    """
    try:
        async with session.get(
                f"https://nominatim.openstreetmap.org/search.php?q={city}&format=jsonv2",
                timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            if response.status != 200:
                logger.info(f"RESPONSE STATUS = {response.status}")
                return None
            data = await response.json()
            logger.info(f"DATA = {data}, type = {type(data)}")
            if not data:
                return None
            lat_city = data[0]["lat"]
            lon_city = data[0]["lon"]
            logger.info(f"CITY DATA = {city}, lat = {lat_city}, lon = {lon_city}")
            return {"lat": lat_city, "lon": lon_city}
    except asyncio.TimeoutError:
        logger.error("Client timed out of 10 sec")
        return None
    except Exception as e:
        logger.exception(f"Exception: {e}")
        return None
