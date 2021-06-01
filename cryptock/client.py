# noinspection SpellCheckingInspection
__author__ = 'wookjae.jo'

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import *
from model import Ohlcv
from cctxu import list_to_ohlcv

import ccxt

binance = ccxt.binance()


class TimeUnit(Enum):
    """
    시간 단위를 표현하기 위한 클래스
    """

    MINUTE = 'm'
    HOUR = 'h'
    DAY = 'd'

    def timedelta(self):
        if self == TimeUnit.MINUTE:
            return timedelta(minutes=1)
        elif self == TimeUnit.HOUR:
            return timedelta(hours=1)
        elif self == TimeUnit.DAY:
            return timedelta(days=1)
        else:
            raise Exception(f'Not supported time unit for timedelta: {self}')


@dataclass
class TimeFrame:
    """
    시간 프레임을 표현하기 위한 클래스
    """

    def __init__(self, time_unit: TimeUnit, value: int):
        self.time_unit = time_unit
        self.value = value

    def __str__(self):
        return f'{self.value}{self.time_unit.value}'

    def timedelta(self):
        return self.time_unit.timedelta() * self.value


def ticker_names() -> List[str]:
    """
    모든 티커 이름을 반환한다.
    """
    return list(tickers().keys())


def tickers() -> Dict[str, Dict[str, Any]]:
    """
    모든 티커 정보를 반환한다.
    """
    return binance.fetch_tickers()


def fetch_ohlcv(
        symbol: str,
        time_frame: TimeFrame,
        begin: datetime,
        end: datetime
) -> Generator[Ohlcv, None, None]:
    """
    특정 티커의 Ohlcv 리스트를 조회하여 반환한다. 설정 기간 내 데이터가 한번의 API 요청으로 불가능한 경우가 빈번하기 때문에 여러 번 나누어 요청한다.
    :param symbol: 티커 심볼. EX) ETH/BTC
    :param time_frame: Ohlcv 간격
    :param begin: 조회 기간의 시작 시각
    :param end: 조회 기간의 종료 시각
    :return: Ohlcv 리스트
    """
    limit = 1500  # 개수 제한 최대로 설정
    delta = end - begin  # 기간
    delta_per = time_frame.timedelta() * limit  # 1회 요청에 대한 기간
    loop_count = math.ceil(delta / delta_per)  # 루프 횟수
    for i in range(loop_count):
        since = int((begin + delta_per * i).timestamp() * 1000)
        ohlcv_list = binance.fetch_ohlcv(
            symbol,
            timeframe=str(time_frame),
            since=since,
            limit=limit,
            params={}
        )

        ohlcv_list.sort(key=lambda x: x[0])

        for ohlcv in ohlcv_list:
            dt = datetime.fromtimestamp(ohlcv[0] / 1000)
            if dt > end:  # 조회 기간 외 데이터: 조회 완료
                return

            yield list_to_ohlcv(ohlcv)
