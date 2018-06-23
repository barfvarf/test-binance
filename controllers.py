# -*- coding:utf-8 -*-

import json
import config
import urllib
import requests
from flask import render_template
from misc import Log
from binance.client import Client
from binance.websockets import BinanceSocketManager
from collections import OrderedDict
from datetime import datetime
from bintest import file_handler
from models import PriceLog


buffer_dict = OrderedDict()
allowed_symbols = ["BTCUSDT"]


class IndexViewController(object):
    """Basic index view"""

    def __init__(self):
        self.log = Log(file_handler, self.__class__.__name__)

    def call(self):
        self.get_socket()

        return render_template("index.html", channel_href=config.channel_href)

    def get_socket(self):
        client = Client(config.api_key, config.api_secret)
        bm = BinanceSocketManager(client)
        bm.start_trade_socket("BTCUSDT", self.process_message)
        return bm.start()

    def process_message(self, msg):
        utime = str(msg.get("T"))[:10]
        ms = str(msg.get("T"))[-3:]
        dt = datetime.fromtimestamp(int(utime)).replace(microsecond=int(ms) * 1000)
        symbol = msg.get("s")
        price = "%.2f" % float(msg.get("p"))
        buffer_dict.update({dt: {"symbol": symbol, "price": price}})
        last_trade_time = max(buffer_dict)
        delete_keys = []
        for k in buffer_dict.keys():
            if (last_trade_time - k).seconds > config.timeframe:
                delete_keys.append(k)
        if delete_keys:
            for k in delete_keys:
                del buffer_dict[k]
            self.log.info("Deleted keys: %s" % delete_keys)
        prices = [p.get("price") for p in buffer_dict.values()]
        if prices:
            max_price = max(prices)
            min_price = min(prices)
            if prices.index(max_price) < prices.index(min_price):
                drop_percent = (float(max_price) - float(min_price)) / float(max_price)
                if drop_percent > config.percent_threshhold:
                    self.send_notification(symbol, max_price, min_price, "{:.2%}".format(drop_percent))
                    PriceLog.create(symbol=symbol, max_price=max_price,
                                    min_price=min_price, drop_percent=round(drop_percent * 100, 2))

    def send_notification(self, symbol, max_price, min_price, drop_percent):
        text = ("In the last %s seconds the price of %s has dropped by *%s* from %s to %s" %
                (config.timeframe, symbol, drop_percent, max_price, min_price))
        url = "".join([config.bot_api_url, config.bot_token, "/sendMessage?",
                       urllib.parse.urlencode(dict(chat_id=config.chat_id,
                                                   text=str(text),
                                                   parse_mode=config.parse_mode))])

        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            self.log.info("Sent notification to channel %s: %s" % (config.chat_id, text))
        else:
            self.log.info("Failed to send notification to channel %s; Telegram response: %s" % (config.chat_id,
                                                                                                response.text))


class GetLatestPriceController(object):
    """Gets the latest known price for a given symbol"""

    def __init__(self):
        self.log = Log(file_handler, self.__class__.__name__)

    def call(self, symbol):
        if symbol not in allowed_symbols or not buffer_dict:
            self.log.debug("Requested symbol %s is not allowed or has no data." % symbol)
            return json.dumps({"result": None})
        last_trade_time = max(buffer_dict)
        data = buffer_dict.get(last_trade_time)
        result = {"symbol": data.get("symbol"),
                  "price": data.get("price"),
                  "time": last_trade_time.strftime("%Y-%m-%d %H:%M:%S")}
        return json.dumps({"result": result})


class GetChartDataController(object):
    """Gets chart data for a given symbol"""

    def __init__(self):
        self.log = Log(file_handler, self.__class__.__name__)

    def call(self, symbol):
        if symbol not in allowed_symbols or not buffer_dict:
            self.log.debug("Requested symbol %s is not allowed or has no data." % symbol)
            return json.dumps({"result": None})
        labels = [k.strftime("%H:%M:%S") for k in buffer_dict.keys()]
        data = [p.get("price") for p in buffer_dict.values()]
        result = {"symbol": symbol,
                  "labels": labels,
                  "data": data,
                  "min": float(min(data)) - 10,
                  "max": float(max(data)) + 10}
        return json.dumps({"result": result})
