import fastapi

from . import switch

app = fastapi.FastAPI()


@app.post('/lights/on_movement')
def turn_lights_on_movement() -> dict:
    succeed = False
    reason = 'daytime'

    if switch.check_night():
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
