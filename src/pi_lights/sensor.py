import dataclasses
import datetime
import enum
import struct
import threading
import zoneinfo
from collections.abc import Callable, Iterator

import serial

DEFAULT_TZ = zoneinfo.ZoneInfo('America/Bogota')


type _ActionFunc = Callable[[], bool]
type _TriggerFunc = Callable[[_ActionFunc], None]


class State(enum.Enum):
    NONE = 0
    MOVING = 1
    STATIONARY = 2
    BOTH = 3

    @property
    def present(self) -> bool:
        return self.value > 0


@dataclasses.dataclass(frozen=True)
class Reading:
    state: State
    moving_cm: int
    moving_energy: int
    still_cm: int
    still_energy: int
    distance_cm: int


def check_night(tz: zoneinfo.ZoneInfo = DEFAULT_TZ) -> bool:
    start = datetime.time(18, 15, 0)
    end = datetime.time(5, 45, 0)
    now = datetime.datetime.now(tz=tz).time()
    return now >= start or now <= end


class Sensor:
    LENGTH_META = 2
    HEADER = b'\xf4\xf3\xf2\xf1'
    TAIL = b'\xf8\xf7\xf6\xf5'

    FRAME_HEAD_TARGET = 0xAA
    FRAME_TYPE_TARGET = 0x02
    MIN_TARGET_LENGTH = 11

    def __init__(
        self,
        port: str,
        baud: int = 256_000,
    ) -> None:
        self.sensor = serial.Serial(port, baud, timeout=1)
        self._buffer = b''
        self._present = False
        self._trigger: _TriggerFunc | None = None
        self._thread_action: threading.Thread | None = None
        self._thread: threading.Thread | None = None
        self._kill = threading.Event()
        self._enabled = threading.Event()
        self._enabled.set()

    @property
    def _full_header_size(self) -> int:
        return len(self.HEADER) + self.LENGTH_META

    def _fire(self) -> None:
        if self._trigger is None:
            return
        if self._thread_action and self._thread_action.is_alive():
            return
        self._thread_action = threading.Thread(
            target=self._trigger, args=(self._is_present,), daemon=True
        )
        self._thread_action.start()

    def _is_present(self) -> bool:
        return self._enabled.is_set() and not self._kill.is_set() and self._present

    def _stream(self) -> Iterator[Reading]:
        while not self._kill.is_set():
            self._buffer += self.sensor.read(64)
            while (i := self._buffer.find(self.HEADER)) >= 0 and len(
                self._buffer
            ) >= i + self._full_header_size:
                length_start = i + len(self.HEADER)
                data_start = i + self._full_header_size
                data_length = struct.unpack(
                    '<H', self._buffer[length_start:data_start]
                )[0]
                end = data_start + data_length + len(self.TAIL)

                if len(self._buffer) < end:
                    break

                data = self._buffer[data_start : data_start + data_length]
                self._buffer = self._buffer[end:]

                if (
                    len(data) >= self.MIN_TARGET_LENGTH
                    and data[0] == self.FRAME_TYPE_TARGET
                    and data[1] == self.FRAME_HEAD_TARGET
                ):
                    st, md, me, sd, se, dd = struct.unpack('<BHBHBH', data[2:11])
                    yield Reading(
                        state=State(st),
                        moving_cm=md,
                        moving_energy=me,
                        still_cm=sd,
                        still_energy=se,
                        distance_cm=dd,
                    )

    def _loop(self) -> None:
        stream = self._stream()
        while not self._kill.is_set():
            if not self._enabled.is_set():
                self._present = False
                self._enabled.wait(1)
                self.flush()
                continue

            if not check_night():
                self._present = False
                if self._kill.wait(60):
                    break
                self.flush()
                continue

            try:
                reading = next(stream)
            except StopIteration:
                break

            print(reading)
            self._present = reading.state.present
            if self._is_present():
                self._fire()

    def add_trigger(self, trigger: _TriggerFunc) -> None:
        self._trigger = trigger

    def flush(self) -> None:
        self.sensor.reset_input_buffer()
        self._buffer = b''

    def pause(self) -> None:
        self._enabled.clear()
        if self._thread_action:
            self._thread_action.join(timeout=2)

    def resume(self) -> None:
        self._enabled.set()

    def shutdown(self) -> None:
        self._kill.set()
        self._enabled.set()
        for t in (self._thread, self._thread_action):
            if t:
                t.join(timeout=5)
        self.sensor.close()

    def start_loop(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
