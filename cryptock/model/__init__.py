from dataclasses import dataclass
from datetime import datetime


@dataclass
class Ohlcv:
    """
    Ohlcv: Open, High, Low, Close, Volume
    """
    datetime: datetime  # 시각
    open: float  # 시가
    high: float  # 고가
    low: float  # 저가
    close: float  # 종가
    vol: float  # 거래량
