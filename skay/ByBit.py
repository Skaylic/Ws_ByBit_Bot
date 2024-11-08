import os
from pybit.unified_trading import WebSocket, HTTP
import logging

logger = logging.getLogger("SkayBot")


class ByBit():

    def __init__(self):
        logger.info("Bot is loaded!")
        self.api_key = os.getenv("API_KEY", 0)
        self.api_secret = os.getenv("API_SECRET", 0)
        self.interval = os.getenv("INTERVAL", 0)
        self.symbol = os.getenv("SYMBOL", "")
        self.qty = float(os.getenv("QTY", 0.0))
        self.instruments = {}
        self.quoteCoin = ""
        self.baseCoin = ""
        self.min_qty = 0.0
        self.kline = {}
        self.balance = {}
        self.orderId = False
        self.order = False

    def callback_public(self, message):
        if message.get("success") is True:
            logger.info("Kline chanel connection!")
        data = message.get("data", {})
        if data:
            self.kline = {
                "open": float(data[0]["open"]),
                "close": float(data[0]["close"])
            }

    def callback_wallet(self, message):
        if message.get("success") is True and message.get("req_id"):
            logger.info("Wallet chanel connection!")
        data = message.get("data", {})
        if data:
            for i in data["coin"]:
                if i["coin"] == self.quoteCoin:
                    self.balance[self.quoteCoin] = i["walletBalance"]
                elif i['coin'] == self.baseCoin:
                    self.balance[self.baseCoin] = i["walletBalance"]

    def callback_order(self, message):
        if message.get("success") is True and message.get("req_id"):
            logger.info("Order chanel connection!")
        data = message.get("data", {})
        if data:
            self.order = data[0]
            print(self.order)

    def getKline(self):
        ws = WebSocket(
            testnet=False,
            channel_type="spot",
            # trace_logging=True,
            callback_function=self.callback_public
        )
        ws.kline_stream(self.interval, self.symbol, self.callback_public)

    def getWallet(self):
        ws = WebSocket(
            testnet=False,
            channel_type="private",
            api_key=os.getenv("API_KEY", 0),
            api_secret=os.getenv("API_SECRET", 0),
            # trace_logging=True,
            callback_function=self.callback_wallet
        )
        ws.wallet_stream(self.callback_wallet)

    def getOrder(self):
        ws = WebSocket(
            testnet=False,
            channel_type="private",
            api_key=os.getenv("API_KEY", 0),
            api_secret=os.getenv("API_SECRET", 0),
            # trace_logging=True,
            callback_function=self.callback_order
        )
        ws.order_stream(self.callback_order)

    def getInstruments(self):
        session = HTTP(
            testnet=False,
            api_key=self.api_key,
            api_secret=self.api_secret,
        )
        r = session.get_instruments_info(
            category="spot",
            symbol=self.symbol,
        )
        data = r['result']['list'][0]
        self.instruments = data
        self.min_qty = float(data['lotSizeFilter']['minOrderQty'])
        self.baseCoin = data['baseCoin']
        self.quoteCoin = data['quoteCoin']
        return self

    def getBalance(self):
        session = HTTP(
            testnet=False,
            api_key=self.api_key,
            api_secret=self.api_secret,
        )
        r = session.get_wallet_balance(
            accountType="UNIFIED",
        )
        for i in r['result']['list'][0]['coin']:
            if i['coin'] == self.quoteCoin:
                self.balance[self.quoteCoin] = float(i['walletBalance'])
            elif i['coin'] == self.baseCoin:
                self.balance[self.baseCoin] = float(i['walletBalance'])

    def sendTicker(self, sz, side="Buy", tag=""):
        coin = "quoteCoin"
        if side == "Sell":
            coin = "baseCoin"
        session = HTTP(
            testnet=False,
            api_key=self.api_key,
            api_secret=self.api_secret,
        )
        r = session.place_order(
            category="spot",
            symbol=self.symbol,
            side=side,
            orderType="Market",
            qty=sz,
            price=self.kline['close'],
            marketUnit=coin,
            orderLinkId=tag
        )
        self.orderId = r['result']['orderId']

