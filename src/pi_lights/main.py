import fastapi

app = fastapi.FastAPI()


@app.post('/lights/on')
def turn_on_lights():
    print('Checking time and turning lights on...')
    return {'lights_on': True}
