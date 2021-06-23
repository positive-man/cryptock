from __future__ import annotations

__author__ = 'wookjae.jo'

from dataclasses import dataclass
from datetime import datetime

from binance import ThreadedWebsocketManager, Client


@dataclass
class BinanceWebsocketEvent:
    """
    raw:
    {
        "e": "24hrTicker",  // Event type
        "E": 123456789,     // Event time
        "s": "BNBBTC",      // Symbol
        ...
    }
    """

    event_type: str
    event_time: datetime
    symbol: str

    def reflect(self, d: dict):
        self.event_type = d.get('e')
        self.event_time = datetime.fromtimestamp(d.get('E') / 1000)
        self.symbol = d.get('s')


@dataclass
class DayTicker(BinanceWebsocketEvent):
    """
    raw:
    {
        "e": "24hrTicker",  // Event type
        "E": 123456789,     // Event time
        "s": "BNBBTC",      // Symbol
        "p": "0.0015",      // Price change
        "P": "250.00",      // Price change percent
        "w": "0.0018",      // Weighted average price
        "x": "0.0009",      // First trade(F)-1 price (first trade before the 24hr rolling window)
        "c": "0.0025",      // Last price
        "Q": "10",          // Last quantity
        "b": "0.0024",      // Best bid price
        "B": "10",          // Best bid quantity
        "a": "0.0026",      // Best ask price
        "A": "100",         // Best ask quantity
        "o": "0.0010",      // Open price
        "h": "0.0025",      // High price
        "l": "0.0010",      // Low price
        "v": "10000",       // Total traded base asset volume
        "q": "18",          // Total traded quote asset volume
        "O": 0,             // Statistics open time
        "C": 86400000,      // Statistics close time
        "F": 0,             // First trade ID
        "L": 18150,         // Last trade Id
        "n": 18151          // Total number of trades
    }
    """

    price_change: float
    price_change_percent: float
    weighted_average_price: float
    x: float
    last_price: float
    last_quantity: float
    best_bid_price: float
    best_bid_quantity: float
    best_ask_price: float
    best_ask_quantity: float
    open_price: float
    high_price: float
    low_price: float
    total_traded_base_asset_volume: float
    total_traded_quote_asset_volumn: float
    open_time: datetime
    close_time: datetime
    first_trade_id: int
    last_trade_id: int
    total_number_of_trades: int

    def reflect(self, d: dict):
        super(DayTicker, self).reflect(d)
        self.price_change = float(d.get('p'))
        self.price_change_percent = float(d.get('P'))
        self.weighted_average_price = float(d.get('w'))
        self.x = float(d.get('x'))
        self.last_price = float(d.get('c'))
        self.last_quantity = float(d.get('Q'))
        self.best_bid_price = float(d.get('b'))
        self.best_bid_quantity = float(d.get('B'))
        self.best_ask_price = float(d.get('a'))
        self.best_ask_quantity = float(d.get('A'))
        self.open_price = float(d.get('o'))
        self.high_price = float(d.get('h'))
        self.low_price = float(d.get('l'))
        self.total_traded_base_asset_volume = float(d.get('v'))
        self.total_traded_quote_asset_volumn = float(d.get('q'))
        self.open_time = datetime.fromtimestamp(d.get('O') / 1000)
        self.close_time = datetime.fromtimestamp(d.get('C') / 1000)
        self.first_trade_id = int(d.get('F'))
        self.last_trade_id = int(d.get('L'))
        self.total_number_of_trades = int(d.get('n'))


@dataclass
class KlineEvent(BinanceWebsocketEvent):
    def reflect(self, d: dict):
        super(KlineEvent, self).reflect(d)


@dataclass
class TradeEvent(BinanceWebsocketEvent):
    @classmethod
    def from_dict(cls, d: dict):
        pass


binance_client = Client(
    api_key='',
    api_secret=''
)


class BinanceSyncStore:
    __instance: BinanceSyncStore = None

    def __init__(self):
        self.binance_websock = ThreadedWebsocketManager(
            api_key='',
            api_secret=''
        )
        self.binance_websock.start()
        self.__start_updating()

    def __new__(cls, *args, **kwargs):
        assert not cls.__instance, 'Do not instantiate singleton class.'
        return super(BinanceSyncStore, cls).__new__(cls, *args, **kwargs)

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            __instance = BinanceSyncStore()
        return cls.__instance

    def __start_updating(self):
        def echo(msg):
            print(msg)

        # todo: KeyboardInterrupt 등 오류 핸들링 공통 로직을 annotation으로 wrapping 하자
        self.binance_websock.start_ticker_socket(callback=echo)
