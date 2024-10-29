import asyncio
import os

from dotenv import load_dotenv
from time import sleep
from websockets import ConnectionClosedError
from skay.Logger import setup_logger
from skay.Bot import Bot


load_dotenv()

logger = setup_logger(os.getenv("BOT_NAME"))



if __name__ == "__main__":
    try:
        asyncio.run(Bot().run())
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt')
    except ConnectionClosedError:
        logger.error("ConnectionClosedError")
        sleep(20)
        asyncio.run(Bot().run())
    except TimeoutError:
        logger.error("ConnectionClosedError")
        sleep(20)
        asyncio.run(Bot().run())


