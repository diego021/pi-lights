import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from typing import Literal, TypedDict

import fastapi

from . import lights, schedule, sensor

logging.basicConfig(level=logging.DEBUG)

RELAY_4_PIN = 24
SENSOR_PORT = '/dev/serial0'


class ModeResponse(TypedDict):
    mode: Literal['auto', 'on', 'off']


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI) -> AsyncIterator[None]:
    # Opening and closing the hardware blocks, so it runs off the event loop.
    # The exit stack releases whatever was opened, even if startup fails midway.
    async with contextlib.AsyncExitStack() as stack:
        app.state.lights = await asyncio.to_thread(lights.Lights, pin=RELAY_4_PIN)
        stack.push_async_callback(asyncio.to_thread, app.state.lights.close)

        app.state.sensor = await asyncio.to_thread(
            sensor.PresenceSensor,
            port=SENSOR_PORT,
            on_change=app.state.lights.switch,
            active_when=schedule.always,
        )
        stack.push_async_callback(asyncio.to_thread, app.state.sensor.stop)

        app.state.sensor.start()
        yield


app = fastapi.FastAPI(lifespan=lifespan)


@app.post('/lights/auto')
def set_auto_mode() -> ModeResponse:
    app.state.sensor.resume()
    return {'mode': 'auto'}


@app.post('/lights/on')
def set_lights_on() -> ModeResponse:
    app.state.sensor.pause()
    app.state.lights.turn_on()
    return {'mode': 'on'}


@app.post('/lights/off')
def set_lights_off() -> ModeResponse:
    app.state.sensor.pause()
    app.state.lights.turn_off()
    return {'mode': 'off'}
