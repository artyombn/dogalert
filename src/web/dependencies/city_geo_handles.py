import asyncio
import logging

import aiohttp

logger = logging.getLogger(__name__)


def check_city_exists(city: str) -> str | None:
    from src.web.static.city.ru_cities import region_city

    if city in region_city:
        return city
    return None

async def get_city_from_geo(
        lat: float,
        lon: float,
        session: aiohttp.ClientSession,
) -> str | None:
    """
    # https://nominatim.openstreetmap.org/reverse?lat=55.78481894445758&lon=37.84803289439989&format=json
    """
    try:
        async with session.get(
                f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json",
                timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            if response.status != 200:
                logger.info(f"RESPONSE STATUS = {response.status}")
                return None
            data = await response.json()
            logger.info(f"DATA = {data}")
            if not data or not isinstance(data, dict):
                return None
            city = data["address"]["city"]
            logger.info(f"ADDRESS = {city}")
            return city
    except asyncio.TimeoutError:
        logger.error("Client timed out of 10 sec")
        return None
    except Exception as e:
        logger.exception(f"Exception: {e}")
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
