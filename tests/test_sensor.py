import copy
import dataclasses

import pytest

from pi_lights import sensor
from pi_lights.sensor import Reading, TargetState

READING = Reading(
    state=TargetState.MOVING,
    moving_cm=120,
    moving_energy=80,
    still_cm=90,
    still_energy=40,
    distance_cm=100,
)


def target_frame(reading: Reading = READING) -> bytes:
    state, *fields = dataclasses.astuple(reading)
    payload = sensor._TARGET.pack(state.value, *fields)
    # Real LD2410 target frames end with 0x55 0x00 after the payload
    return frame(sensor._TARGET_PREFIX + payload + b'\x55\x00')


def target_frame_with(state: TargetState) -> bytes:
    return target_frame(copy.replace(READING, state=state))


def frame(data: bytes) -> bytes:
    return sensor.HEADER + sensor._LENGTH.pack(len(data)) + data + sensor.TAIL


def test_parses_single_frame() -> None:
    readings, leftover = sensor._parse_frames(target_frame())

    assert readings == [READING]
    assert leftover == b''


def test_parses_consecutive_frames() -> None:
    buffer = target_frame_with(TargetState.MOVING) + target_frame_with(TargetState.NONE)

    readings, leftover = sensor._parse_frames(buffer)

    assert [r.state for r in readings] == [TargetState.MOVING, TargetState.NONE]
    assert leftover == b''


def test_discards_bytes_before_header() -> None:
    readings, leftover = sensor._parse_frames(b'\x00\x01junk' + target_frame())

    assert len(readings) == 1
    assert leftover == b''


@pytest.mark.parametrize('cut', [2, len(sensor.HEADER) + 1, -1])
def test_keeps_incomplete_frame(cut: int) -> None:
    complete = target_frame_with(TargetState.STATIONARY)
    partial = complete[:cut]

    readings, leftover = sensor._parse_frames(partial)

    assert readings == []
    # Completing the leftover yields the frame
    readings, leftover = sensor._parse_frames(leftover + complete[len(partial) :])
    assert [r.state for r in readings] == [TargetState.STATIONARY]
    assert leftover == b''


def test_drops_noise_without_header() -> None:
    readings, leftover = sensor._parse_frames(bytes(1000))

    assert readings == []
    assert len(leftover) < len(sensor.HEADER)


def test_ignores_non_target_frames() -> None:
    readings, leftover = sensor._parse_frames(frame(b'\x01\xaa\x00\x00'))

    assert readings == []
    assert leftover == b''


def test_ignores_truncated_target_payload() -> None:
    readings, _ = sensor._parse_frames(frame(sensor._TARGET_PREFIX + b'\x01\x00'))

    assert readings == []


@pytest.mark.parametrize(
    ('state', 'present'),
    [
        (TargetState.NONE, False),
        (TargetState.MOVING, True),
        (TargetState.STATIONARY, True),
        (TargetState.BOTH, True),
    ],
)
def test_target_state_present(state: TargetState, present: bool) -> None:
    assert state.present is present


def test_presence_sensor_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sensor.serial, 'Serial', lambda *_, **__: None)

    presence = sensor.PresenceSensor('/dev/ttyUSB0', on_change=print, baud=9600)

    assert repr(presence) == "PresenceSensor(port='/dev/ttyUSB0', baud=9600)"
