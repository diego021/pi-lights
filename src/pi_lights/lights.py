import logging

import gpiozero

logger = logging.getLogger(__name__)


class Lights:
    def __init__(self, pin: int) -> None:
        self._pin = pin
        self._relay = gpiozero.OutputDevice(pin, active_high=False, initial_value=False)

    def __repr__(self) -> str:
        return f'{type(self).__name__}(pin={self._pin!r})'

    def turn_on(self) -> None:
        logger.info('Turning lights ON')
        self._relay.on()

    def turn_off(self) -> None:
        logger.info('Turning lights OFF')
        self._relay.off()

    def switch(self, on: bool) -> None:
        if on:
            self.turn_on()
        else:
            self.turn_off()

    def close(self) -> None:
        self._relay.close()
