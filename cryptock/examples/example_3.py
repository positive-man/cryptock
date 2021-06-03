"""
볼린저 밴드 기반 전략에 따라 매매하고 그에 따른 평가를 수행함
"""
import configparser
from datetime import datetime

from binance import Client

from metric.bollinger import Bollinger
from typing import *
from threading import Thread
import time

config = configparser.ConfigParser()
config.read('config.ini')
config_root = config['root']
api_key = config_root['api_key']
api_secret = config_root['api_secret']

client = Client(api_key=api_key, api_secret=api_secret)


class Tester:
    def __init__(self, symbol):
        self.symbol = symbol
        self.holding = False

    def log(self, *values: List[Any]):
        all_values = [self.symbol, datetime.now()]
        all_values.extend(values)
        print(', '.join([str(v) for v in all_values]))

    def start(self):
        holding = False
        while True:
            klines = client.get_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_1MINUTE)
            last_open = float(klines[-1][1])
            closes = [float(kline[4]) for kline in klines]
            last_close = closes[-1]
            bollinger = Bollinger.of(price_list=closes)
            # 하단 하향 돌파 시, 매수
            if not holding and last_open >= bollinger.lower >= last_close:
                self.log('매수', last_close, bollinger)
                holding = True

            # 중단 상향 돌파 시, 매도
            if holding and last_close > bollinger.mid:
                self.log('매도', last_close, bollinger)
                holding = False

            time.sleep(0.5)


def main():
    Thread(target=Tester('ETHBUSD').start).start()
    Thread(target=Tester('BTCBUSD').start).start()
    Thread(target=Tester('BNBBUSD').start).start()
    Thread(target=Tester('DOGEBUSD').start).start()
    Thread(target=Tester('ADABUSD').start).start()


if __name__ == "__main__":
    main()
