"""
볼린저 밴드 기반 전략에 따라 매매하고 그에 따른 평가를 수행함
"""
import configparser

from binance import ThreadedWebsocketManager, Client

from metric.bollinger import Bollinger
from datetime import datetime

config = configparser.ConfigParser()
config.read('config.ini')
config_root = config['root']
api_key = config_root['api_key']
api_secret = config_root['api_secret']


def main():
    symbol = 'BTCUSDT'

    client = Client(api_key=api_key, api_secret=api_secret)
    websocket = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    websocket.start()

    buy_price = 0

    def handle_socket_message(msg: dict):
        klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE)
        print(datetime.fromtimestamp(klines[-1][0] / 1000))
        closes=[float(kline[4]) for kline in klines]
        last=float(msg.get('c'))
        bollinger = Bollinger.of(price_list=closes, last=last)
        print(bollinger)

        # 하단 하향 돌파 시, 매수
        if closes[-1] < bollinger.lower < last:
            pass

        # 중단 상향 돌파 시, 매도


    websocket.start_symbol_ticker_socket(callback=handle_socket_message, symbol=symbol)
    websocket.join()


if __name__ == "__main__":
    main()
