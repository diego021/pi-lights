import time
import threading

import fastapi

from . import sensor, switch


def infinite_loop() -> None:
    mv_serial = sensor.Sensor()
    stream = mv_serial.read_loop()
    while True:
        if not sensor.check_night():
            time.sleep(60)
            mv_serial.flush()
            continue

        reading = next(stream)
        print(reading)
        if reading.present:
            # import os
            # os.system('pw-play /usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga')  # Test
            # time.sleep(1)
            switch.turn_on_for(10)
            mv_serial.flush()


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
