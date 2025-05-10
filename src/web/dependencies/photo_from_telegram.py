import asyncio
import logging

import aiohttp

from src.config.config import settings

logger = logging.getLogger(__name__)

# async def get_file_url_by_file_id(file_id: str) -> str | None:
#     get_file_url = f"https://api.telegram.org/bot{settings.TOKEN}/getFile?file_id={file_id}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(get_file_url)
#         if response.status_code != 200 or not response.json().get("ok"):
#             return None
#         file_path = response.json()["result"]["file_path"]
#         return f"https://api.telegram.org/file/bot{settings.TOKEN}/{file_path}"

async def get_file_url_by_file_id(
        file_id: str,
        session: aiohttp.ClientSession,
) -> str | None:
    get_file_url = f"https://api.telegram.org/bot{settings.TOKEN}/getFile?file_id={file_id}"
    try:
        async with session.get(get_file_url, timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status != 200:
                return None
            data = await response.json()
            if not data.get("ok"):
                return None
            file_path = data["result"]["file_path"]
            return f"https://api.telegram.org/file/bot{settings.TOKEN}/{file_path}"
    except asyncio.TimeoutError:
        logger.error("Client timed out of 10 sec")
        return None
    except Exception as e:
        logger.exception(f"Exception: {e}")
        return None


