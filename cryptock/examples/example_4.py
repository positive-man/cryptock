from dataclasses import dataclass

from binance import Client

client = Client(
    api_key='cPZmBjWZGhPljnQZyTWA7i7wNwJ3oBqZ9s9JCslmPwBzim78lVw7ZCAPhWED4zRA',
    api_secret='feEjIsySX05X39tjvWzW7YzzDmJtt3vLvpsS4Kf79dP1eCgyNNYDyTniHypNI3sW'
)

CURRENCIES = [
    'BTC',
    'BNB',
    'USD',
    'USDT'
]


@dataclass
class Ticker:
    name: str
    currency: str
    price: float

    @classmethod
    def of(cls, symbol: str, price: float):
        for currency in CURRENCIES:
            if symbol.endswith(currency):
                name = symbol[:-len(currency)]
                return Ticker(name=name, currency=currency, price=price)


class TickerManager:
    def __init__(self):
        self.tickers = []
        for ticker in client.get_all_tickers():
            t = Ticker.of(ticker.get('symbol'), float(ticker.get('price')))
            if t:
                self.tickers.append(t)

    def get(self, name, currency):
        for ticker in self.tickers:
            if ticker.name == name and ticker.currency == currency:
                return ticker

    def exchange(self, name: str, currency_from: str, currency_to: str):
        return self.get(name, currency_from).price * self.get(currency_from, currency_to).price



def main():
    ticker_mgr = TickerManager()
    print(ticker_mgr.get('ATA', 'USDT').price)
    print(ticker_mgr.exchange('ATA', currency_from='BNB', currency_to='USDT'))


if __name__ == '__main__':
    main()
