import os
import re
from time import sleep, strftime
import logging
from skay.ByBit import ByBit
from skay.DataBase import DataBase
from skay.Models import Orders

logger = logging.getLogger("SkayBot")

db = DataBase().set_db()


class Bot(ByBit):

    def __init__(self):
        super(Bot, self).__init__()
        self.min = float(os.getenv("MIN"))
        self.max = float(os.getenv("MAX"))
        self.percent = float(os.getenv("PERCENT"))
        self.grid = []
        self.grid_px = 0.0
        self.position_px = 0.0
        self.to_buy = 0
        self.close_kline = 0

    def grid_positions(self):
        x = self.min
        while x <= self.max:
            x += (x * self.percent / 100)
            self.grid.append(x)

    def array_grid(self, a, val):
        self.grid_px = round(min([x for x in a if x > val] or [None]), 9)
        return self

    def is_position(self):
        _ord = (
            db.query(Orders).filter(Orders.side == 'Buy', Orders.profit < self.kline['close'], Orders.is_active == True)
            .order_by(Orders.px).first())
        if _ord:
            return _ord
        _ord = db.query(Orders).filter(Orders.side == 'Buy', Orders.grid_px == self.grid_px,
                                       Orders.is_active == True).first()
        if _ord:
            return None
        else:
            return False

    def save_order(self, order, active=True):
        _ord = Orders(
            ordId=order.get('orderId'),
            cTime=strftime('%Y%m%d%H%M%S'),
            sz=order.get('cumExecValue'),
            px=order.get('avgPrice'),
            profit=order.get('profit'),
            fee=order.get('cumExecFee'),
            grid_px=order.get('grid_px'),
            feeCurrency=order.get('feeCurrency'),
            side=order.get('side'),
            status=order.get('orderStatus'),
            symbol=order.get('symbol'),
            orderType=order.get('orderType'),
            marketUnit=order.get('marketUnit'),
            orderLinkId=order.get('orderLinkId'),
            is_active=active,
        )
        db.add(_ord)
        db.commit()
        logger.info(_ord)
        return _ord

    def check(self):
        if len(self.instruments) < 1:
            self.getInstruments()
            self.min_qty = float(self.instruments['lotSizeFilter']['minOrderQty'])
        while self.kline and self.qty <= self.min_qty * self.kline['close']:
            self.qty = self.qty + .5
        if len(self.balance) < 1:
            self.getBalance()
        if self.kline and len(self.grid) < 1:
            self.grid_positions()
        if self.kline and self.grid:
            self.array_grid(self.grid, self.kline['close'])
        pos = self.is_position()
        if self.kline['close'] > self.kline['open'] and self.to_buy == 0:
            self.position_px = self.grid_px
            self.close_kline = self.kline['close']
            self.to_buy = 1
        elif self.kline['close'] < self.kline['open'] and self.to_buy == 1:
            self.to_buy = 0
        if pos and self.balance[self.baseCoin] > pos.sz / pos.px and self.order is False:
            self.sendTicker(pos.sz / pos.px, 'Sell', strftime('bot_%Y%m%d%H%M%S'))
        elif pos and self.balance[self.baseCoin] < pos.sz / pos.px and self.order is False:
            print("Buy complete 1!")
            self.sendTicker(self.min_qty * self.kline['close'], 'Buy')
        elif (pos is False and self.balance[self.quoteCoin] > self.qty and self.to_buy == 1
              and self.kline['close'] > self.position_px and self.order is False):
            self.sendTicker(self.qty, 'Buy', strftime('bot_%Y%m%d%H%M%S'))
            self.position_px = self.grid_px
        if self.order and self.order['orderId'] == self.orderId:
            if self.order and re.match(r'bot_+[0-9]+', self.order['orderLinkId']) and self.order['side'] == "Sell":
                self.save_order(self.order, active=False)
                pos.is_active = False
                db.commit()
                self.order = False
            elif re.match(r'bot_+[0-9]+', self.order['orderLinkId']) and self.order['side'] == "Buy":
                self.order['grid_px'] = self.grid_px
                self.order['profit'] = float(self.order['avgPrice']) + (float(self.order['avgPrice']) / 100 * self.percent)
                self.save_order(self.order, active=True)
                self.order = False
                exit()
            else:
                print("Bot complete 2!")
                self.order['grid_px'] = self.grid_px
                self.order['profit'] = self.order['avgPrice'] + (self.order['avgPrice'] / 100 * self.percent)
                self.save_order(self.order, active=False)
                self.order = False
        elif self.order and self.order['orderId'] != self.orderId:
            self.order = False

    def start(self):
        logger.info("Bot is started!")
        self.getKline()
        self.getOrder()
        self.getWallet()
        while True:
            self.check()
            sleep(1)
