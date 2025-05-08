import logging

import aiohttp

logger = logging.getLogger(__name__)

# https://nominatim.openstreetmap.org/reverse?lat=55.78481894445758&lon=37.84803289439989&format=json

async def get_city_from_geo(
        lat: float,
        lon: float,
        session: aiohttp.ClientSession
) -> str | None:
    try:
        async with session.get(f'https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json', timeout=10) as response:
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
    except aiohttp.ClientTimeoutError:
        logger.error(f"Client timed out of 10 sec")
        return None
    except Exception as e:
        logger.exception(f"Exception: {e}")
        return None
