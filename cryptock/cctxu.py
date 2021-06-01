from model import Ohlcv
from datetime import datetime


def list_to_ohlcv(data: list) -> Ohlcv:
    assert len(data) == 6, 'Illegal argument. Length of data must be 6'
    return Ohlcv(
        datetime=datetime.fromtimestamp(data[0] / 1000),
        open=data[1],
        high=data[2],
        low=data[3],
        close=data[4],
        vol=data[5]
    )
