import logging
import os
from dotenv import load_dotenv
import hmac
import json
import time
import websockets
from pprint import pp
from pybit.unified_trading import HTTP

load_dotenv()


class ByBit:

    def __init__(self):
        self.logger = logging.getLogger(os.getenv('BOT_NAME'))
        self.logger.info("Bot is started!")
        self.api_key = os.getenv("API_KEY")
        self.api_secret = os.getenv("API_SECRET")
        self.session = HTTP(
            testnet=False,
            api_key=self.api_key,
            api_secret=self.api_secret,
        )
        self.symbol = os.getenv("SYMBOL")
        self.interval = os.getenv("INTERVAL")
        self.instruments = None
        self.min_qty = 0.0
        self.baseCoin = ''
        self.quoteCoin = ''
        self.balance = {}
        self.kline = {}
        self.orderId = None
        self.order = None

    async def send(self, ws, op: str, args: list, ids=''):
        if not ids:
            subs = dict(op=op, args=args)
        else:
            subs = dict(id=ids, op=op, args=args)
        await ws.send(json.dumps(subs))

    def sign(self):
        expires = int((time.time() + 10) * 1000)
        _val = f'GET/realtime{expires}'
        signature = str(hmac.new(
            bytes(self.api_secret, 'utf-8'),
            bytes(_val, 'utf-8'), digestmod='sha256'
        ).hexdigest())
        return expires, signature

    async def callbackMessage(self, ws):
        while True:
            try:
                msg = json.loads(await ws.recv())
                op = msg.get('op', None)
                type = msg.get('type', None)
                topic = msg.get('topic', None)
                data = msg.get('data', None)
            except websockets.ConnectionClosedOK:
                print('Connection closed')
                break
            if op == 'auth' and msg['success'] == True:
                return "login"
            if topic and msg['topic'] == f"kline.{self.interval}.{self.symbol}":
                self.kline = msg['data'][0]
            elif topic and msg['topic'] == 'order':
                self.order = msg['data'][0]
            elif topic and msg['topic'] == 'wallet':
                for i in data[0]['coin']:
                    if i['coin'] == self.quoteCoin:
                        self.balance[self.quoteCoin] = float(i['walletBalance'])
                    elif i['coin'] == self.baseCoin:
                        self.balance[self.baseCoin] = float(i['walletBalance'])
            else:
                pp(msg)

    async def ws_private(self):
        url = 'wss://stream.bybit.com/v5/private'

        async with websockets.connect(url) as self.ws:
            e, s = self.sign()
            await self.send(self.ws, 'auth', [self.api_key, e, s])
            r = await self.callbackMessage(self.ws)
            if r == 'login':
                await self.send(self.ws, 'subscribe', ["wallet"])
                await self.send(self.ws, 'subscribe', ['order'])
                await self.callbackMessage(self.ws)

    async def ws_public(self):
        url = 'wss://stream.bybit.com/v5/public/spot'
        async with websockets.connect(url) as self.ws_1:
            await self.send(self.ws_1, 'subscribe', [f"kline.{self.interval}.{self.symbol}"])
            await self.callbackMessage(self.ws_1)

    def sendTicker(self, qty, side="Buy", tag=''):
        marketUnit = "baseCoin"
        if side == "Sell":
            marketUnit = "quoteCoin"
        r = self.session.place_order(
            category="spot",
            symbol=self.symbol,
            side=side,
            orderType="Market",
            qty=qty,
            price=self.kline['close'],
            marketUnit=marketUnit,
            orderLinkId=tag
        )
        self.orderId = r['result']['orderId']
        self.getOrderHistory(self.orderId)
        return self

    def getInstruments(self):
        r = self.session.get_instruments_info(
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
        r = self.session.get_wallet_balance(
            accountType="UNIFIED",
        )
        for i in r['result']['list'][0]['coin']:
            if i['coin'] == self.quoteCoin:
                self.balance[self.quoteCoin] = float(i['walletBalance'])
            elif i['coin'] == self.baseCoin:
                self.balance[self.baseCoin] = float(i['walletBalance'])

    def getOrderHistory(self, ordId=''):
        if not ordId:
            r = self.session.get_order_history(
                category="spot",
                simbol=self.symbol,
                orderId=ordId,
            )
        else:
            r = self.session.get_order_history(
                category="spot",
                simbol=self.symbol,
                limit=50
            )
        data = r['result']['list']
        return data