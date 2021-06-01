import statistics
from dataclasses import dataclass
from datetime import datetime
from typing import *

import ccxt

from cctxu import list_to_ohlcv
from model import Ohlcv

binance = ccxt.binance()


def avg(values: List[float]):
    return sum(values) / len(values)


@dataclass
class Bolinger:
    datetime: datetime
    upper: float
    lower: float
    mid: float
    cur: float


class BollingerStreamer:

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.stopped = False
        self.subscribers: List[Callable[[Bolinger], None]] = []

    def start(self):
        while not self.stopped:
            self.fetch()

    def stop(self):
        self.stopped = True

    def fetch(self):
        data = binance.fetch_ohlcv(
            self.symbol,
            timeframe='1m'
        )

        ohlcv_list: List[Ohlcv] = [list_to_ohlcv(item) for item in data]
        close_20 = [ohlcv.close for ohlcv in ohlcv_list[-20:]]
        ma_20 = avg(close_20)
        upper = ma_20 + (2 * statistics.stdev(close_20))
        lower = ma_20 - (2 * statistics.stdev(close_20))
        close_7 = [ohlcv.close for ohlcv in ohlcv_list[-7:]]
        ma_7 = avg(close_7)
        mid = ma_7
        cur = binance.fetch_ticker(self.symbol).get('last')

        for subscriber in self.subscribers:
            subscriber(
                Bolinger(
                    datetime=ohlcv_list[-1].datetime,
                    upper=upper,
                    lower=lower,
                    mid=mid,
                    cur=cur
                )
            )
