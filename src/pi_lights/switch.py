import time
from collections.abc import Callable

import gpiozero

relay_4 = gpiozero.OutputDevice(24, active_high=False, initial_value=False)


def turn_on() -> None:
    print('Turning lights ON!')
    relay_4.on()


def turn_off() -> None:
    print('Turning lights OFF!')
    relay_4.off()


def turn_on_while(condition: Callable[[], bool], interval: int = 1) -> None:
    turn_on()
    while condition():
        time.sleep(interval)
    turn_off()
