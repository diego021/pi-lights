from collections.abc import Iterator

import gpiozero
import pytest
from gpiozero.pins.mock import MockFactory

from pi_lights.lights import Lights


@pytest.fixture
def lights() -> Iterator[Lights]:
    gpiozero.Device.pin_factory = MockFactory()
    lights = Lights(pin=24)
    yield lights
    lights.close()
    gpiozero.Device.pin_factory = None


def test_repr(lights: Lights) -> None:
    assert repr(lights) == 'Lights(pin=24)'


def test_switch_drives_active_low_relay(lights: Lights) -> None:
    pin = gpiozero.Device.pin_factory.pin(24)

    lights.switch(on=True)
    assert pin.state is False

    lights.switch(on=False)
    assert pin.state is True
