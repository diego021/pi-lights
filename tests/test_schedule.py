import datetime
from typing import Self, override

import pytest

from pi_lights import schedule


@pytest.mark.parametrize(
    ('t', 'expected'),
    [
        (datetime.time(12, 0), False),
        (datetime.time(18, 14), False),
        (datetime.time(18, 15), True),
        (datetime.time(23, 59), True),
        (datetime.time(0, 0), True),
        (datetime.time(5, 45), True),
        (datetime.time(5, 46), False),
    ],
)
def test_is_night(
    monkeypatch: pytest.MonkeyPatch, t: datetime.time, expected: bool
) -> None:
    class FrozenDatetime(datetime.datetime):
        @override
        @classmethod
        def now(cls, tz: datetime.tzinfo | None = None) -> Self:
            return cls.combine(datetime.date(2026, 1, 1), t, tzinfo=tz)

    monkeypatch.setattr(schedule.datetime, 'datetime', FrozenDatetime)

    assert schedule.is_night() is expected


def test_always() -> None:
    assert schedule.always() is True
