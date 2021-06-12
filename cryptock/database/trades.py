import csv
import logging
import os
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone

import requests
import sqlalchemy

from .common import AbstractDynamicTable


@dataclass
class Trade:
    trade_id: int
    time: datetime
    price: float


class TradeTable(AbstractDynamicTable):
    def __init__(self, db_url, symbol: str, year: int, month: int, create_if_not_exists=False):
        columns = [
            sqlalchemy.Column('trade_id', sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column('time', sqlalchemy.DateTime),
            sqlalchemy.Column('price', sqlalchemy.Float)
        ]

        table_name = f'{symbol}_{year:04}_{month:02}'

        super().__init__(
            engine=sqlalchemy.create_engine(db_url),
            entity_type=Trade,
            name=table_name,
            columns=columns,
            create_if_not_exists=create_if_not_exists
        )

    def find_all(self, begin: datetime = None, end: datetime = None):
        return self.query().filter(
            sqlalchemy.and_(
                begin <= self.proxy.datetime if begin else True,
                self.proxy.datetime <= end if end else True,
            )
        ).all()


class TradeTableBuilder:
    def __init__(
            self,
            db_url: str,
            symbol: str,
            year: int,
            month: int,
            create_if_not_exists: bool
    ):
        self.table = TradeTable(
            db_url=db_url, symbol=symbol, year=year, month=month,
            create_if_not_exists=create_if_not_exists
        )

    def build(self, csv_file: str):
        self.table.open()
        with open(csv_file) as f:
            logging.debug(f'Counting row count in {csv_file}...')
            row_count = 0
            for _ in csv.reader(f, delimiter=','):
                row_count += 1

        with open(csv_file) as f:
            inserted = 0
            trade_buffer = []
            for row in csv.reader(f, delimiter=','):
                trade_buffer.append(
                    Trade(
                        trade_id=int(row[0]),
                        time=datetime.fromtimestamp(int(row[4]) / 1000, timezone.utc),
                        price=float(row[1])
                    )
                )

                if len(trade_buffer) >= 10000:
                    logging.debug(f'Inserting {len(trade_buffer)} records...')
                    self.table.insert_all(trade_buffer)
                    inserted += len(trade_buffer)
                    logging.debug(f'Inserted {inserted}/{row_count}')
                    trade_buffer = []

            self.table.insert_all(trade_buffer)

        self.table.session.commit()
        self.table.close()


def download_trades_csv(symbol: str, year: int, month: int):
    """
    해당 심볼의 기간 내 tick 정보를 csv 파일 형식으로 다운로드 한다. zip 파일 다운로드 후 압축 해제 후 csv 파일 경로를 반환한다.
    """
    local_tmpdir = 'tmp'
    os.makedirs(local_tmpdir, exist_ok=True)
    zip_name = f'{symbol}-trades-{year}-{month:02}.zip'
    uri = f'https://data.binance.vision/data/spot/monthly/trades/{symbol}/{zip_name}'

    # 요청 수행
    response = requests.get(uri, stream=True)
    assert response.status_code == 200, f'The response not ok: {response.status_code}'

    # 파일 저장
    zip_path = os.path.join(local_tmpdir, zip_name)
    csv_path = '.'.join(zip_path.split('.')[:-1]) + '.csv'

    if os.path.isfile(csv_path):
        logging.debug(f'{csv_path} already exists.')
        return csv_path

    content_length = response.headers.get('content-length')
    loaded_length = 0
    chunk_size = 100 * 1024 * 1024
    with open(zip_path, 'wb') as f:
        if content_length:
            for data in response.iter_content(chunk_size=chunk_size):
                loaded_length += len(data)
                f.write(data)
                logging.debug(f'Downloading trades... [{loaded_length}/{content_length}]')

        else:
            logging.debug('Downloading trades...')
            f.write(response.content)

    # 압축 해제
    output_dir = os.path.dirname(zip_path)
    logging.debug(f'Extracting at {os.path.abspath(output_dir)}')
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(output_dir)

    # zip 파일 삭제
    logging.debug(f'Removing {zip_path}')
    os.remove(zip_path)

    # csv 파일 경로
    return csv_path
