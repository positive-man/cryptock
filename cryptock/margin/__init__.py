# noinspection SpellCheckingInspection
__author__ = 'wookjae.jo'

import time
from dataclasses import dataclass
from typing import *

from binance import Client

client = Client(
    api_key='EL7VGu0vmcbc686iDA2czXIxMEdTnH0vwy1X9TcWJY9Rtg5ONKuqpZYVVh0n3Ryi',
    api_secret='WsDUHzKk8ais9AzPkkwSS2jrlqwqGbCQ4gg5mnlwnkqeZ1r1nvWiSpmrHjj628Id'
)


@dataclass
class Price:
    bid: float
    ask: float
    last: float


@dataclass
class SymbolObject:
    symbol: str
    base_asset: str
    quote_asset: str
    is_trading: bool
    is_spot_trading_allowed: bool
    price: Price

    @classmethod
    def of(cls, symbol_dict: dict, price: Price):
        return SymbolObject(
            symbol=symbol_dict.get('symbol'),
            is_trading=symbol_dict.get('status') == 'TRADING',
            base_asset=symbol_dict.get('baseAsset'),
            quote_asset=symbol_dict.get('quoteAsset'),
            is_spot_trading_allowed=symbol_dict.get('isSpotTradingAllowed'),
            price=price
        )


class SymbolObjectList:
    def __init__(self, items: List[SymbolObject]):
        self.items = items

    def find_all_by_base_asset(self, base_asset: str) -> List[SymbolObject]:
        result = []
        for symbol_obj in self.items:
            if symbol_obj.base_asset == base_asset:
                result.append(symbol_obj)
        return result

    def find_all_by_quote_asset(self, quote_asset: str) -> List[SymbolObject]:
        result = []
        for symbol_obj in self.items:
            if symbol_obj.quote_asset == quote_asset:
                result.append(symbol_obj)
        return result

    def find(self, symbol: str) -> SymbolObject:
        for symbol_obj in self.items:
            if symbol_obj.symbol == symbol:
                return symbol_obj


def load_active_symbol_list() -> SymbolObjectList:
    price_by_symbol: Dict[str, Price] = {
        ticker.get('symbol'): Price(bid=float(ticker.get('bidPrice')), ask=float(ticker.get('askPrice')),
                                    last=float(ticker.get('lastPrice'))) for ticker in
        client.get_ticker()
    }
    symbol_dicts: Dict[str, dict] = {x.get('symbol'): x for x in client.get_exchange_info().get('symbols')}

    symbol_objects = []
    for symbol in price_by_symbol:
        symbol_object = SymbolObject.of(
            symbol_dict=symbol_dicts.get(symbol),
            price=price_by_symbol.get(symbol)
        )

        if symbol_object.is_spot_trading_allowed and symbol_object.is_trading:
            symbol_objects.append(symbol_object)

    symbol_object_list = SymbolObjectList(items=symbol_objects)
    whitelist = []  # fixme: 이거 맞냐?
    for symbol_obj in symbol_objects:
        asset_btc = symbol_object_list.find(f'{symbol_obj.base_asset}BTC')
        if symbol_obj.base_asset != 'BTC' and asset_btc and asset_btc.price.last > 0.00001:
            whitelist.append(symbol_obj)

    return SymbolObjectList(items=whitelist)


@dataclass
class Margin:
    symbol_from: SymbolObject
    symbol_bridge: SymbolObject
    symbol_to: SymbolObject
    price: float
    percentage: float

    @classmethod
    def of(cls, symbol_from: SymbolObject, symbol_bridge: SymbolObject, symbol_to: SymbolObject):
        exchanged_price = symbol_from.price.last * symbol_bridge.price.last
        return Margin(
            symbol_from=symbol_from,
            symbol_bridge=symbol_bridge,
            symbol_to=symbol_to,
            price=symbol_to.price.last - exchanged_price,
            percentage=(symbol_to.price.last - exchanged_price) / exchanged_price * 100
        )

    def __str__(self):
        exchanged_price = self.symbol_from.price.last * self.symbol_bridge.price.last
        return f'{round(self.percentage, 2)}%({self.price}): {self.symbol_from.symbol}*{self.symbol_bridge.symbol}({exchanged_price}) => {self.symbol_to.symbol}({self.symbol_to.price})'


def calculate_margins(symbol_object_list: SymbolObjectList) -> List[Margin]:
    margins: List[Margin] = []
    for symbol_obj in symbol_object_list.items:
        for symbol_obj2 in symbol_object_list.find_all_by_base_asset(base_asset=symbol_obj.base_asset):
            symbol_bridge = symbol_object_list.find(f'{symbol_obj.quote_asset}{symbol_obj2.quote_asset}')
            if not symbol_bridge:
                continue

            margins.append(
                Margin.of(
                    symbol_from=symbol_obj,
                    symbol_bridge=symbol_bridge,
                    symbol_to=symbol_obj2
                )
            )

    return margins


@dataclass
class Balance:
    asset: str
    free: float
    locked: float

    @classmethod
    def of(cls, d: dict):
        return Balance(
            asset=d.get('asset'),
            free=float(d.get('free')),
            locked=float(d.get('locked'))
        )


class BalanceList:
    def __init__(self):
        self.balances = []
        self.reload()

    def reload(self):
        account = client.get_account()
        self.balances = [Balance.of(d) for d in account.get('balances')]

    def get(self, asset: str) -> Union[Balance]:
        for balance in self.balances:
            if balance.asset == asset:
                return balance


def try_cancel_order(symbol: str, order_id: int):
    try:
        client.cancel_order(symbol=symbol, orderId=order_id)
    except BaseException as e:
        print(f'[WARNING] {e}')


def try_sell_all(symbol: SymbolObject):
    balance_list = BalanceList()
    balance = balance_list.get(symbol.base_asset)
    if balance.free > 0:
        print(f'Selling {balance.free} {symbol.symbol}')
        client.order_market_sell(
            symbol=symbol.symbol,
            quantity=balance.free
        )
        return True

    return False


def eat_margin(
        active_symbol_list: SymbolObjectList,
        symbol_from: SymbolObject,
        symbol_to: SymbolObject
):
    quote_usdt = active_symbol_list.find(symbol=f'{symbol_from.quote_asset}USDT').price.last
    buy_amount_usdt = 20
    quote_order_qty = buy_amount_usdt / quote_usdt
    print(f'Buying {symbol_from.symbol}...')
    buy_order = client.order_market_buy(
        symbol=symbol_from.symbol,
        quoteOrderQty=round(quote_order_qty, 6)
    )
    print(f'Buy ordered: {buy_order}')
    buy_time = time.time()

    while try_sell_all(symbol=symbol_to):
        deadline = 10
        if time.time() - buy_time > deadline:
            print(f'Trying canceling the order because {deadline} seconds have passed...')
            try_cancel_order(
                symbol=buy_order.get('symbol'),
                order_id=buy_order.get('orderId')
            )
            break

        time.sleep(0.1)

    try_sell_all(symbol=symbol_to)
