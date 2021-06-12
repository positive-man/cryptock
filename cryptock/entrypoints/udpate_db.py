import logging

from database.trades import TradeTableBuilder, download_trades_csv
from utils import log


def main():
    symbol = 'BTCUSDT'

    year = 2021
    for i in range(4):
        month = 2 + i
        logging.info(f'Downloading {symbol}-{year:04}-{month:02}...')
        csv_file = download_trades_csv(symbol=symbol, year=year, month=month)
        logging.info(f'Building DB table...')
        trade_table_builder = TradeTableBuilder(
            db_url='postgresql://hermes:hermes@218.147.138.41:5432/coin_trades', symbol=symbol, year=year, month=month,
            create_if_not_exists=True
        )
        trade_table_builder.build(csv_file)


if __name__ == '__main__':
    log.init(level=logging.DEBUG)
    main()
