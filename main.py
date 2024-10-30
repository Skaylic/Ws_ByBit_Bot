import asyncio
import os

from dotenv import load_dotenv
from time import sleep
from websockets import ConnectionClosedError
from skay.Logger import setup_logger
from skay.Bot import Bot


load_dotenv()

logger = setup_logger(os.getenv("BOT_NAME"))

bot = Bot()


def main():
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt')
    except ConnectionClosedError:
        logger.error("ConnectionClosedError")
        sleep(60)
        main()
    except TimeoutError:
        logger.error("ConnectionClosedError")
        sleep(60)
        main()


if __name__ == "__main__":
    main()
