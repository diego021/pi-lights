import dataclasses
import datetime
import enum
import struct
import zoneinfo
from collections.abc import Iterator

import serial

DEFAULT_TZ = zoneinfo.ZoneInfo('America/Bogota')


class State(enum.Enum):
    NONE = 0
    MOVING = 1
    STATIONARY = 2
    BOTH = 3


@dataclasses.dataclass(frozen=True)
class Reading:
    state: State
    present: bool
    moving_cm: int
    moving_energy: int
    still_cm: int
    still_energy: int
    distance_cm: int


class Sensor:
    PORT = '/dev/serial0'
    BAUD = 256_000

    LENGTH_META = 2
    HEADER = b'\xf4\xf3\xf2\xf1'
    TAIL = b'\xf8\xf7\xf6\xf5'

    FRAME_HEAD_TARGET = 0xAA
    FRAME_TYPE_TARGET = 0x02
    MIN_TARGET_LENGTH = 11

    def __init__(self, port: str | None = None, baud: int | None = None) -> None:
        self.buffer = b''
        self.port = port or self.PORT
        self.baud = baud or self.BAUD
        self.sensor = serial.Serial(self.port, self.baud, timeout=1)

    @property
    def _full_header_size(self) -> int:
        return len(self.HEADER) + self.LENGTH_META

    def close(self) -> None:
        self.sensor.close()

    def flush(self) -> None:
        self.sensor.reset_input_buffer()
        self.buffer = b''

    def read_once(self) -> Reading:
        self.sensor.reset_input_buffer()
        return next(self.read_loop())

    def read_loop(self) -> Iterator[Reading]:
        while True:
            self.buffer += self.sensor.read(64)
            while (i := self.buffer.find(self.HEADER)) >= 0 and len(
                self.buffer
            ) >= i + self._full_header_size:
                length_start = i + len(self.HEADER)
                data_start = i + self._full_header_size
                data_length = struct.unpack('<H', self.buffer[length_start:data_start])[
                    0
                ]
                end = data_start + data_length + len(self.TAIL)

                if len(self.buffer) < end:
                    break

                data = self.buffer[data_start : data_start + data_length]
                self.buffer = self.buffer[end:]

                if (
                    len(data) >= self.MIN_TARGET_LENGTH
                    and data[0] == self.FRAME_TYPE_TARGET
                    and data[1] == self.FRAME_HEAD_TARGET
                ):
                    st, md, me, sd, se, dd = struct.unpack('<BHBHBH', data[2:11])
                    yield Reading(
                        state=State(st),
                        present=st > 0,
                        moving_cm=md,
                        moving_energy=me,
                        still_cm=sd,
                        still_energy=se,
                        distance_cm=dd,
                    )


def check_night(tz: zoneinfo.ZoneInfo = DEFAULT_TZ) -> bool:
    start = datetime.time(18, 15, 0)
    end = datetime.time(5, 45, 0)
    now = datetime.datetime.now(tz=tz).time()
    return now >= start or now <= end
