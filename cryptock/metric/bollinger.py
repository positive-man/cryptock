import statistics
from dataclasses import dataclass
from typing import *


def avg(values: List[float]):
    return sum(values) / len(values)


@dataclass
class Bollinger:
    upper: float
    lower: float
    mid: float
    cur: float

    @classmethod
    def of(cls, price_list: List[float]):
        last_20 = [price for price in price_list[-19:]]
        ma_20 = avg(last_20)
        upper = ma_20 + (2 * statistics.stdev(last_20))
        lower = ma_20 - (2 * statistics.stdev(last_20))
        close_7 = last_20[-7:]
        ma_7 = avg(close_7)
        mid = ma_7

        return Bollinger(
            upper=upper,
            lower=lower,
            mid=mid,
            cur=price_list[-1]
        )
