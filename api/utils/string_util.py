import datetime as dt
from datetime import timezone, datetime


def generate_filename_prefix() -> str:

    now_utc = datetime.now(timezone.utc)

    d = dt.date(now_utc.year, now_utc.month, now_utc.day)
    t = dt.time(now_utc.hour, now_utc.minute)
    now = dt.datetime.combine(d, t)
    return now.strftime("%Y%m%d_%H%M%S")
