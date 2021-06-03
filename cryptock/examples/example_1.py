"""
CCXT - Rest API를 기반으로 한 실시간 데이터 스트리밍 및 볼린저 밴드 계산
"""

from typing import *

import ccxt

from ccxtx import list_to_ohlcv
from ccxtx import ticker_names
from metric.bollinger import Bollinger

binance = ccxt.binance()


class BollingerStreamer:

    def __init__(self, symbol: str, timeframe: str = '1m'):
        self.symbol = symbol
        self.timeframe = timeframe
        self.stopped = False
        self.subscribers: List[Callable[[Bollinger], None]] = []

    def start(self):
        while not self.stopped:
            self.fetch()

    def stop(self):
        self.stopped = True

    def fetch(self):
        for subscriber in self.subscribers:
            subscriber(
                Bollinger.of(
                    price_list=[list_to_ohlcv(item).close for item in
                                binance.fetch_ohlcv(self.symbol, timeframe=self.timeframe)]
                )
            )


def main():
    print(ticker_names())
    bollinger_streamer = BollingerStreamer(symbol='BTC/USDT')
    bollinger_streamer.subscribers.append(
        lambda bollinger: print(bollinger)
    )
    bollinger_streamer.start()


if __name__ == '__main__':
    main()
