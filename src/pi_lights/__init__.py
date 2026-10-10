import fastapi

from . import sensor, switch

SENSORS = []


def _setup_sensors() -> None:
    light_sensor = sensor.Sensor(trigger=lambda: switch.turn_on_for(10))
    light_sensor.start_loop()
    SENSORS.append(light_sensor)


app = fastapi.FastAPI()
_setup_sensors()


@app.post('/lights/auto')
def turn_auto_lights() -> dict:
    # switch.MODE = switch.Mode.AUTO
    return {'succeed': True, 'reason': 'on-demand'}


@app.post('/lights/on')
def turn_on_lights() -> dict:
    # switch.MODE = switch.Mode.ON
    switch.turn_on()
    return {'succeed': True, 'reason': 'on-demand'}


@app.post('/lights/off')
def turn_off_lights() -> dict:
    # switch.MODE = switch.Mode.OFF
    switch.turn_off()
    return {'succeed': True, 'reason': 'on-demand'}
