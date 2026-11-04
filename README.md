# pi-lights

Presence-activated lights control for a Raspberry Pi 3B+. An HLK-LD2410
mmWave radar sensor detects people, and a relay switches the lights on while
someone is present, but only at night. A small HTTP API lets you override the
sensor manually.

## How it works

- **Sensor** (`sensor.py`): a background thread reads LD2410 frames from the
  serial port (256000 baud) and reports presence changes (moving, stationary,
  or both counts as present).
- **Lights** (`lights.py`): drives a relay through `gpiozero` (active-low,
  starts off).
- **Schedule** (`schedule.py`): the sensor only reacts during the night window,
  18:15 to 05:45 in the `America/Bogota` timezone. Outside it, lights stay off.
- **API** (`__init__.py`): a FastAPI app wiring everything together.

## Hardware

| Part                      | Connection                         |
| ------------------------- | ---------------------------------- |
| Relay module (channel 4)  | GPIO 24 (`RELAY_4_PIN`)            |
| HLK-LD2410 radar          | UART on `/dev/serial0` (`SENSOR_PORT`) |

Enable the serial port on the Pi (`raspi-config` → Interface Options → Serial
Port: login shell **off**, hardware serial **on**) and make sure your user
can access GPIO and `/dev/serial0` (groups `gpio` and `dialout`).

## Requirements

- Python 3.14 or newer
- [uv](https://docs.astral.sh/uv/)

## Running

```bash
./start.sh        # production: fastapi run
./start.sh dev    # development: listens on 0.0.0.0 with auto-reload
```

The server listens on port 8000 by default.

## Running as a service

`deploy/pi-lights.service` is a systemd unit that starts the app at boot and
restarts it if it crashes. It assumes the user `pi` and the repository cloned
at `/home/pi/pi-lights`. If yours differ, edit `User=` and `APP_DIR` at the top
of the `[Service]` section. The unit looks for `uv` in `~/.local/bin` (its
default install location) or on the system `PATH`.

1. Install the dependencies once as that user, so the first start is fast:

   ```bash
   cd ~/pi-lights
   uv sync
   ```

2. Install and start the unit:

   ```bash
   sudo cp deploy/pi-lights.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now pi-lights
   ```

3. Check that it's running and follow the logs:

   ```bash
   systemctl status pi-lights
   journalctl -u pi-lights -f
   ```

After pulling new changes, run `sudo systemctl restart pi-lights`. If you edit
the unit file, copy it again and run `sudo systemctl daemon-reload` before
restarting.

## API

All endpoints are `POST` and return the resulting mode.

| Endpoint       | Effect                                                        |
| -------------- | ------------------------------------------------------------ |
| `/lights/auto` | Resume sensor control (lights follow presence at night)       |
| `/lights/on`   | Pause the sensor and turn the lights on                       |
| `/lights/off`  | Pause the sensor and turn the lights off                      |

```bash
curl -X POST http://raspberrypi.local:8000/lights/on
# {"mode":"on"}
```

Interactive docs are available at `/docs`.

## Configuration

Settings are constants in the source:

- `RELAY_4_PIN`, `SENSOR_PORT` in `src/pi_lights/__init__.py`
- `NIGHT_START`, `NIGHT_END`, `DEFAULT_TZ` in `src/pi_lights/schedule.py`

## Development

```bash
uv sync
uv run ruff check
uv run ruff format
```
