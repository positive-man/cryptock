from metric.bollinger import BollingerStreamer
from client import ticker_names

def main():
    print(ticker_names())

    bollinger_streamer = BollingerStreamer(symbol='ETH/USDT')
    bollinger_streamer.subscribers.append(
        lambda bollinger: print(bollinger)
    )
    bollinger_streamer.start()


if __name__ == '__main__':
    main()
