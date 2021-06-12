# 일단 볼린저 백테스트에 초점을 맞춘다.
# 볼린저 밴드 백테스트는... 우선, 분봉 20개와 현재가가 필요하다

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import *

from binance import Client

from database.trades import Trade, download_trades_csv
from metric.bollinger import Bollinger
import logging
from utils import log

client = Client(api_key='', api_secret='')


class NotEnoughDataException(BaseException):
    def __str__(self):
        return f'Not enough data'


@dataclass
class Ohlc:
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    close_time: datetime

    @classmethod
    def of(cls, trades: List[Trade]):
        prices = [trade.price for trade in trades]
        return Ohlc(
            open_time=trades[0].time,
            open=prices[0],
            high=max(prices),
            low=min(prices),
            close=prices[-1],
            close_time=trades[-1].time
        )


def read_trades(csv_file: str):
    with open(csv_file) as f:
        for row in csv.reader(f, delimiter=','):
            yield Trade(
                trade_id=int(row[0]),
                time=datetime.fromtimestamp(int(row[4]) / 1000, timezone.utc),
                price=float(row[1])
            )


class BacktestRunner:
    def __init__(
            self,
            symbol: str,
            year: int,
            month: int
    ):
        self.symbol = symbol
        self.year = year
        self.month = month

    def start(self, callback: Callable[[Trade], None]):
        # with TradeTable(
        #         db_url='postgresql://hermes:hermes@218.147.138.41:5432/coin_trades',
        #         symbol=self.symbol,
        #         year=self.year,
        #         month=self.month
        # ) as trade_table:
        #     for trade in trade_table.query().yield_per(count=1000):
        #         callback(trade)

        trades_csv = download_trades_csv(self.symbol, self.year, self.month)
        for trade in read_trades(trades_csv):
            callback(trade)


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
            open_time=datetime.fromtimestamp(values[0] / 1000).astimezone(),
            open=float(values[1]),
            high=float(values[2]),
            low=float(values[3]),
            close=float(values[4]),
            vol=float(values[5]),
            close_time=datetime.fromtimestamp(values[6] / 1000).astimezone()
        )


def get_klines(symbol: str, end_time: datetime):
    return [Kline.of(*raw) for raw in
            client.get_klines(
                symbol=symbol,
                interval=Client.KLINE_INTERVAL_1MINUTE,
                endTime=int(end_time.timestamp() * 1000)
            )]


class X:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.holding = False
        self.last_trade = None
        self.buy_price = None
        self.klines = None

    @classmethod
    def log(cls, *values):
        logging.info(', '.join([str(v) for v in values]))

    def callback(self, trade: Trade):
        if self.klines is None or self.klines[-1].close_time < trade.time:
            # Update klines
            self.klines = [kline for kline in get_klines(
                symbol=self.symbol,
                end_time=trade.time
            )]

        bollinger = Bollinger.of(price_list=[kline.close for kline in self.klines[:-1]] + [trade.price])
        if not self.holding and self.klines[-1].open >= bollinger.lower >= trade.price:
            self.holding = True
            self.buy_price = trade.price
            self.log('매수', trade.time, trade.price, bollinger.upper, bollinger.mid, bollinger.lower)

        # 중단 상향 돌파 시, 매도
        if self.holding and trade.price > bollinger.mid:
            margin = trade.price - self.buy_price
            self.log('매도', trade.time, trade.price, bollinger.upper, bollinger.mid, bollinger.lower,
                     self.buy_price, margin, round((margin / self.buy_price) * 100, 2))
            self.holding = False
            self.buy_price = 0


# fixme: db 쓰지말고 그냥 csv에서 읽어오자
# todo: 골든데드크로스에서 급등 종목 제외
def main():
    symbol = 'BTCUSDT'
    runner = BacktestRunner(symbol='BTCUSDT', year=2021, month=2)
    runner.start(callback=X(symbol).callback)


if __name__ == '__main__':
    log.init()
    main()
