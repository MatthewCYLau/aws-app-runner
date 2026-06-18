from dataclasses import dataclass
from random import randint


@dataclass
class Counter:
    counter: int


def get_counters_chunk(data_list, chunksize: int):
    for i in range(0, len(data_list), chunksize):
        yield data_list[i : i + chunksize]


def custom_get_random_int():
    counters_list = [Counter(randint(1, 5)) for _ in range(10)]

    counters_chunk = get_counters_chunk(counters_list, 2)

    counters_sum = 0

    for chunk in counters_chunk:
        chuck_sum = sum(i.counter for i in chunk)
        counters_sum += chuck_sum

    return counters_sum // len(counters_list)
