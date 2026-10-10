import contextlib
from collections.abc import AsyncIterator

import fastapi

from . import sensor, switch

SENSORS = []


@contextlib.asynccontextmanager
async def lifespan(_app: fastapi.FastAPI) -> AsyncIterator[None]:
    light_sensor = sensor.Sensor(port='/dev/serial0')
    light_sensor.add_trigger(trigger=switch.turn_on_while)
    light_sensor.start_loop()
    SENSORS.append(light_sensor)
    yield
    for s in SENSORS:
        s.shutdown()
    SENSORS.clear()


app = fastapi.FastAPI(lifespan=lifespan)


@app.post('/lights/auto')
def turn_auto_lights() -> dict:
    # switch.MODE = switch.Mode.AUTO
    for s in SENSORS:
        s.resume()
    return {'succeed': True, 'reason': 'on-demand'}


@app.post('/lights/on')
def turn_on_lights() -> dict:
    # switch.MODE = switch.Mode.ON
    for s in SENSORS:
        s.pause()
    switch.turn_on()
    return {'succeed': True, 'reason': 'on-demand'}


@app.post('/lights/off')
def turn_off_lights() -> dict:
    # switch.MODE = switch.Mode.OFF
    for s in SENSORS:
        s.pause()
    switch.turn_off()
    return {'succeed': True, 'reason': 'on-demand'}
