import os
import sqlite3
import zipfile

import requests
from utils import log
import logging
import csv
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

conn = sqlite3.connect(':memory:')


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
    with zipfile.ZipFile(zip_path) as z:
        logging.debug(f'Extracting at {os.path.abspath(output_dir)}')
        z.extractall(output_dir)

    # zip 파일 삭제
    os.remove(zip_path)

    # csv 파일 경로
    csv_path = '.'.join(zip_path.split('.')[:-1]) + '.csv'
    return csv_path


# 최종 목표: 과거 데이터로 실투 하는 것 처럼 시스템 트레이딩 할 수 있다.
# 초 단위 데이터가를 fetch 할 수 있으면 됨
# 1차 목표: 틱 데이터가 샘플링 되어야 한다(초 단위 또는 2초단위?)
# 2차 목표: 초 단위 데이터에 의해 지정된 함수가 콜백된다
# 3차 목표: 콜백 내에서 매수/매도가 일어난다

@dataclass
class Trade:
    time: datetime
    value: float


class TradesCsvReader:
    def __init__(self, csv_file: str, fs=1):
        self.csv_file = csv_file
        self.candles = []
        self.fs = fs
        # todo 캐싱: 캐싱을 해야되는데... 로컬 데이터 베이스...

    def stream(self, buffer_size=2000):
        buffer = []
        with open(self.csv_file) as f:
            for x in csv.reader(f, delimiter=','):
                # 거래 시간
                time = datetime.fromtimestamp(int(x[4]) / 1000, timezone.utc)
                # 거래 값
                value = float(x[1])
                # 거래
                trade = Trade(time, value)
                # 버퍼에 추가 후 반환
                buffer.append(trade)
                buffer = buffer[-buffer_size:]
                yield buffer


def main():
    csv_file = download_trades_csv(
        symbol='ETCUSDT',
        year=2021,
        month=5
    )

    for buffer in TradesCsvReader(csv_file).stream():
        print(buffer[-1])


if __name__ == '__main__':
    log.init(level=logging.DEBUG)
    main()
