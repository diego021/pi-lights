import datetime
import random
import zoneinfo
from typing import Final

DEFAULT_TZ = zoneinfo.ZoneInfo('America/Bogota')
THRESHOLD: Final = 50


def check_night(tz: zoneinfo.ZoneInfo = DEFAULT_TZ) -> bool:
    start = datetime.time(18, 15, 0)
    end = datetime.time(5, 45, 0)
    now = datetime.datetime.now(tz=tz).time()
    return now >= start or now <= end


def get_reading(tz: zoneinfo.ZoneInfo = DEFAULT_TZ) -> int:
    reading = random.randrange(1, 1000)
    print('READING:', reading, 'at', str(datetime.datetime.now(tz=tz)))
    return reading
