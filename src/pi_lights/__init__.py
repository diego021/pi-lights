import contextlib
import logging
from collections.abc import AsyncIterator

import fastapi

from . import lights, schedule, sensor

logging.basicConfig(level=logging.DEBUG)

RELAY_4_PIN = 24
SENSOR_PORT = '/dev/serial0'


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI) -> AsyncIterator[None]:
    app.state.lights = lights.Lights(pin=RELAY_4_PIN)
    app.state.sensor = sensor.PresenceSensor(
        port=SENSOR_PORT,
        on_change=app.state.lights.switch,
        active_when=schedule.always,
    )
    app.state.sensor.start()
    yield
    app.state.sensor.stop()
    app.state.lights.close()


app = fastapi.FastAPI(lifespan=lifespan)


@app.post('/lights/auto')
def set_auto_mode() -> dict:
    app.state.sensor.resume()
    return {'mode': 'auto'}


@app.post('/lights/on')
def set_lights_on() -> dict:
    app.state.sensor.pause()
    app.state.lights.turn_on()
    return {'mode': 'on'}


@app.post('/lights/off')
def set_lights_off() -> dict:
    app.state.sensor.pause()
    app.state.lights.turn_off()
    return {'mode': 'off'}
