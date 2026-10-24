import datetime
import zoneinfo

DEFAULT_TZ = zoneinfo.ZoneInfo('America/Bogota')
NIGHT_START = datetime.time(18, 15)
NIGHT_END = datetime.time(5, 45)


def is_night(tz: zoneinfo.ZoneInfo = DEFAULT_TZ) -> bool:
    now = datetime.datetime.now(tz=tz).time()
    return now >= NIGHT_START or now <= NIGHT_END
