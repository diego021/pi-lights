import datetime
import time
import zoneinfo

DEFAULT_TZ = zoneinfo.ZoneInfo('America/Bogota')


def check_night(tz: zoneinfo.ZoneInfo = DEFAULT_TZ) -> bool:
    start = datetime.time(18, 15, 0)
    end = datetime.time(5, 45, 0)
    now = datetime.datetime.now(tz=tz).time()
    return now >= start or now <= end


def turn_on() -> None:
    print('Turning lights ON!')


def turn_off() -> None:
    print('Turning lights OFF!')


def turn_on_for(seconds: int) -> None:
    turn_on()
    time.sleep(seconds)
    turn_off()
