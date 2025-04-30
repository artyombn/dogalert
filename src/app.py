import asyncio
import logging

import uvicorn

from src.bot.create_bot import bot, dp
from src.web.main import app

logger = logging.getLogger(__name__)

async def run_web() -> None:
    config = uvicorn.Config(app, host="0.0.0.0", port=8001, reload=True)
    server = uvicorn.Server(config)
    await server.serve()

async def run_bot() -> None:
    await dp.start_polling(bot)

async def main() -> None:
    try:
        tasks = [
            run_web(),
            # run_bot()
        ]
        await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"Error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
