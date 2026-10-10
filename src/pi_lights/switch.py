import time
from collections.abc import Callable


def turn_on() -> None:
    print('Turning lights ON!')


def turn_off() -> None:
    print('Turning lights OFF!')


def turn_on_while(condition: Callable[[], bool], interval: int = 1) -> None:
    turn_on()
    while condition():
        time.sleep(interval)
    turn_off()
