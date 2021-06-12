# noinspection SpellCheckingInspection
__author__ = 'wookjae.jo'

from dataclasses import dataclass
from typing import *

from binance import Client

client = Client(
    api_key='EL7VGu0vmcbc686iDA2czXIxMEdTnH0vwy1X9TcWJY9Rtg5ONKuqpZYVVh0n3Ryi',
    api_secret='WsDUHzKk8ais9AzPkkwSS2jrlqwqGbCQ4gg5mnlwnkqeZ1r1nvWiSpmrHjj628Id'
)


@dataclass
class SymbolSummary:
    symbol: str
    status: str
    base_asset: str  # 암호화폐명
    quote_asset: str  # 거래 통화 단위
    price: float


@dataclass
class Margin:
    asset: str
    market_from: str
    market_to: str
    price_from: float
    price_to: float
    margin: float
    margin_percent: float

    @classmethod
    def of(cls, asset: str, market_from: str, market_to: str, price_from: float, price_to: float):
        return Margin(
            asset=asset,
            market_from=market_from,
            market_to=market_to,
            price_from=price_from,
            price_to=price_to,
            margin=price_to - price_from,
            margin_percent=round((price_to - price_from) / price_from * 100, 2)
        )

    def __str__(self):
        return f'{self.asset}{self.market_from}*{self.market_from}{self.market_to}({self.price_from}) -> {self.asset}{self.market_to}({self.price_to}): {self.margin}({self.margin_percent}%)'


def exchange(asset: str, base: str, target: str):
    price_map = {ticker.get('symbol'): float(ticker.get('price')) for ticker in client.get_all_tickers()}
    symbol_summaries = {}
    for symbol_info in client.get_exchange_info().get('symbols'):
        symbol = symbol_info.get('symbol')
        symbol_summaries.update(
            {
                symbol: SymbolSummary(
                    symbol=symbol,
                    status=symbol_info.get('status'),
                    base_asset=symbol_info.get('baseAsset'),
                    quote_asset=symbol_info.get('quoteAsset'),
                    price=price_map.get(symbol)
                )
            }
        )
    return price_map.get(f'{asset}{base}') * price_map.get(f'{base}{target}')


class ExchangeWatcher:
    def __init__(self):
        exchange_info = client.get_exchange_info()
        self.symbol_summaries = {}
        self.price_map = {ticker.get('symbol'): float(ticker.get('price')) for ticker in client.get_all_tickers()}
        for symbol_info in exchange_info.get('symbols'):
            if not symbol_info.get('status') == 'TRADING':
                continue
            symbol = symbol_info.get('symbol')
            self.symbol_summaries.update(
                {
                    symbol: SymbolSummary(
                        symbol=symbol,
                        status=symbol_info.get('status'),
                        base_asset=symbol_info.get('baseAsset'),
                        quote_asset=symbol_info.get('quoteAsset'),
                        price=self.price_map.get(symbol)
                    )
                }
            )

    def find_all_by_quote(self, quote_asset) -> List[SymbolSummary]:
        result = []
        for symbol in self.symbol_summaries:
            summary = self.symbol_summaries.get(symbol)
            if summary.quote_asset == quote_asset:
                result.append(summary)
        return result

    def find_all_by_base(self, base_asset) -> List[SymbolSummary]:
        result = []
        for symbol in self.symbol_summaries:
            summary = self.symbol_summaries.get(symbol)
            if summary.base_asset == base_asset:
                result.append(summary)
        return result

    def exchange(self, symbol_from: str, symbol_to: str):
        source = self.symbol_summaries.get(symbol_from)
        target = self.symbol_summaries.get(symbol_to)
        waypoint = self.symbol_summaries.get(f'{source.quote_asset}{target.quote_asset}')
        if waypoint:
            return source.price * waypoint.price

    def get_margins(self):
        margins = []
        for symbol in self.symbol_summaries:
            x = self.symbol_summaries.get(symbol)
            for y in self.find_all_by_base(x.base_asset):
                if x == y:
                    continue
                price_to = self.exchange(x.symbol, y.symbol)
                if price_to:
                    margin = Margin.of(
                        asset=x.base_asset,
                        market_from=x.quote_asset,
                        market_to=y.quote_asset,
                        price_from=price_to,
                        price_to=y.price
                    )
                    margins.append(margin)
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

    def get(self, asset: str):
        for balance in self.balances:
            if balance.asset == asset:
                return balance


import time


def main():
    while True:
        print(sorted(ExchangeWatcher().get_margins(), key=lambda m: m.percentage, reverse=True)[0])
        print(sorted(ExchangeWatcher().get_margins(), key=lambda m: m.percentage, reverse=True)[1])
        print(sorted(ExchangeWatcher().get_margins(), key=lambda m: m.percentage, reverse=True)[2])
        print()

        time.sleep(1)

    if top_margin.percentage < 2:
        return
    balance_list = BalanceList()
    balance = balance_list.get(top_margin.asset)
    if balance.free == 0:
        # 안 가지고 있으면 from 에서 산다
        symbol_from = f'{top_margin.asset}{top_margin.market_from}'
        print(f'산다 {symbol_from}')
        client.order_oco_buy()
    while True:
        balance_list.reload()
        balance = balance_list.get(top_margin.asset)
        symbol_to = f'{top_margin.asset}{top_margin.market_to}'
        client.order_market_sell()
        if balance.free > 0:
            # 가지고 있으면 to 에다가 판다
            print(f'판다 - {symbol_to}')
            pass


if __name__ == '__main__':
    main()
