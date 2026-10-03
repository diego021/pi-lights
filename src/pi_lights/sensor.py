import random
import time
from typing import Final

from . import switch

THRESHOLD: Final = 50


def run_loop() -> None:
    while True:
        reading = random.randrange(1, 1000)
        print('READING:', reading)
        if reading < THRESHOLD:
            switch.turn_on_for(20)
            continue
        time.sleep(1)
