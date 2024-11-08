import os
from dotenv import load_dotenv
from skay.Logger import setup_logger
from skay.Bot import Bot

load_dotenv()

logger = setup_logger("SkayBot")

bot = Bot()


if __name__ == '__main__':
    try:
        bot.start()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")
    except Exception as e:
       print(e)
