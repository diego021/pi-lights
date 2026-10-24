import dataclasses
import enum
import logging
import struct
import threading
from collections.abc import Callable
from typing import Self

import serial

logger = logging.getLogger(__name__)

type _Condition = Callable[[], bool]
type _PresenceHandler = Callable[[bool], None]

# HLK-LD2410 frame: HEADER | data length (uint16 LE) | data | TAIL
HEADER = b'\xf4\xf3\xf2\xf1'
TAIL = b'\xf8\xf7\xf6\xf5'
_LENGTH = struct.Struct('<H')
PREFIX_SIZE = len(HEADER) + _LENGTH.size

# Target data: frame type | frame head | target payload
_TARGET_PREFIX = bytes([0x02, 0xAA])
_TARGET = struct.Struct('<BHBHBH')
_MIN_TARGET_LENGTH = len(_TARGET_PREFIX) + _TARGET.size


class TargetState(enum.Enum):
    NONE = 0
    MOVING = 1
    STATIONARY = 2
    BOTH = 3

    @property
    def present(self) -> bool:
        return self is not TargetState.NONE


@dataclasses.dataclass(frozen=True)
class Reading:
    state: TargetState
    moving_cm: int
    moving_energy: int
    still_cm: int
    still_energy: int
    distance_cm: int

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        st, md, me, sd, se, dd = _TARGET.unpack_from(payload)
        return cls(
            state=TargetState(st),
            moving_cm=md,
            moving_energy=me,
            still_cm=sd,
            still_energy=se,
            distance_cm=dd,
        )


def _parse_frames(buffer: bytes) -> tuple[list[Reading], bytes]:
    """Parse all complete frames in buffer; return readings and leftover bytes."""
    readings = []
    while (start := buffer.find(HEADER)) >= 0:
        data_start = start + PREFIX_SIZE
        if len(buffer) < data_start:
            break
        (data_length,) = _LENGTH.unpack_from(buffer, start + len(HEADER))
        end = data_start + data_length + len(TAIL)
        if len(buffer) < end:
            break

        data = buffer[data_start : data_start + data_length]
        buffer = buffer[end:]

        if len(data) >= _MIN_TARGET_LENGTH and data.startswith(_TARGET_PREFIX):
            readings.append(Reading.from_bytes(data[len(_TARGET_PREFIX) :]))
    return readings, buffer


class PresenceSensor:
    def __init__(
        self,
        port: str,
        on_change: _PresenceHandler,
        active_when: _Condition = lambda: True,
        baud: int = 256_000,
    ) -> None:
        self._serial = serial.Serial(port, baud, timeout=1)
        self._buffer = b''
        self._on_change = on_change
        self._active_when = active_when
        self._present = False
        self._lock = threading.Lock()
        self._reader_thread: threading.Thread | None = None
        self._stopping = threading.Event()
        self._active = threading.Event()
        self._active.set()

    def _should_listen(self) -> bool:
        return self._active.is_set() and self._active_when()

    def _set_present(self, present: bool) -> None:
        with self._lock:
            if not self._active.is_set() or present == self._present:
                return
            self._present = present
            self._on_change(present)

    def _read(self) -> list[Reading]:
        self._buffer += self._serial.read(64)
        readings, self._buffer = _parse_frames(self._buffer)
        return readings

    def _flush(self) -> None:
        self._serial.reset_input_buffer()
        self._buffer = b''

    def _run(self) -> None:
        while not self._stopping.is_set():
            if not self._should_listen():
                self._set_present(False)
                self._stopping.wait(1)
                self._flush()
                continue

            for reading in self._read():
                logger.debug('%s', reading)
                self._set_present(reading.state.present)

    def start(self) -> None:
        if self._reader_thread and self._reader_thread.is_alive():
            return
        self._reader_thread = threading.Thread(target=self._run, daemon=True)
        self._reader_thread.start()

    def pause(self) -> None:
        """Stop reacting to presence, without notifying on_change."""
        with self._lock:
            self._active.clear()
            self._present = False

    def resume(self) -> None:
        self._active.set()

    def stop(self) -> None:
        self._stopping.set()
        if self._reader_thread:
            self._reader_thread.join(timeout=5)
        self._set_present(False)
        self._serial.close()
