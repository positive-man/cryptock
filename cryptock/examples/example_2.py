"""
볼린저 밴드 기반 전략에 따라 매매하고 그에 따른 평가를 수행함
"""
import configparser

from binance import ThreadedWebsocketManager, Client

from datetime import datetime
from dataclasses import dataclass
from typing import *
import logging

from metric.bollinger import Bollinger
from utils import log

config = configparser.ConfigParser()
config.read('config.ini')
config_root = config['root']
api_key = config_root['api_key']
api_secret = config_root['api_secret']
websocket = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
websocket.start()
client = Client(api_key=api_key, api_secret=api_secret)


@dataclass
class Kline:
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    vol: float
    close_time: datetime

    @classmethod
    def of(cls, *values):
        return Kline(
            open_time=datetime.fromtimestamp(values[0] / 1000),
            open=float(values[1]),
            high=float(values[2]),
            low=float(values[3]),
            close=float(values[4]),
            vol=float(values[5]),
            close_time=datetime.fromtimestamp(values[6] / 1000)
        )

        return result


class Bot:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.klines: List[Kline] = []
        self.update(force=True)
        self.hold = False
        self.buy_price = 0

    def update(self, force=False):
        if force or self.klines[-1].close_time < datetime.now():
            logging.debug('Updating klines...')
            self.klines = [Kline.of(*raw) for raw in
                           client.get_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_1MINUTE)]

    @classmethod
    def log_order(cls, *values):
        logging.critical(', '.join([''] + [str(v) for v in values]))

    def on_message(self, msg):
        self.update()
        last = float(msg.get('c'))
        bollinger = Bollinger.of([k.close for k in self.klines][-19:] + [last])

        if self.hold:
            if bollinger.mid <= last:
                self.hold = False
                margin = last - self.buy_price
                margin_percent = margin / self.buy_price * 100
                self.log_order(self.symbol, 'SELL', last, self.buy_price, margin, margin_percent)
                self.buy_price = 0
        else:
            if bollinger.lower >= last:
                self.hold = True
                self.buy_price = last
                self.log_order(self.symbol, 'BUY', last)

    def join(self):
        websocket.start_symbol_ticker_socket(callback=self.on_message, symbol=self.symbol)


def main():
    all_symbols = [ticker.get('symbol') for ticker in client.get_symbol_ticker()]
    symbols = [symbol for symbol in all_symbols if symbol.endswith('USDT')]
    for symbol in symbols:
        Bot(symbol).join()

    websocket.join()


if __name__ == "__main__":
    log.init(level=logging.INFO)
    logging.getLogger('websockets').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    main()
