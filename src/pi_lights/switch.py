import time


def turn_on() -> None:
    print('Turning lights ON!')


def turn_off() -> None:
    print('Turning lights OFF!')


def turn_on_for(seconds: int) -> None:
    turn_on()
    time.sleep(seconds)
    turn_off()
