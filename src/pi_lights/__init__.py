import threading
import time

import fastapi

from . import sensor, switch


def infinite_loop() -> None:
    while True:
        if sensor.check_night() and sensor.get_reading() < sensor.THRESHOLD:
            switch.turn_on_for(20)
            continue
        time.sleep(1)


thread = threading.Thread(target=infinite_loop, daemon=True)
thread.start()
app = fastapi.FastAPI()


@app.post('/lights/on_movement')
def turn_lights_on_movement() -> dict:
    succeed = False
    reason = 'daytime'

    if sensor.check_night():
        switch.turn_on_for(seconds=15)
        succeed = True
        reason = 'movement-detected'

    return {'succeed': succeed, 'reason': reason}


@app.post('/lights/on')
def turn_on_lights() -> dict:
    switch.turn_on()
    return {'succeed': True, 'reason': 'on-demand'}


@app.post('/lights/off')
def turn_off_lights() -> dict:
    switch.turn_off()
    return {'succeed': True, 'reason': 'on-demand'}
