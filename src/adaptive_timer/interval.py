import logging
import asyncio
from utime import ticks_diff, ticks_us

# pylint: disable=missing-function-docstring

# Used for ensuring consistent rounding
PRECISION = 7

logger = logging.getLogger(__name__)


class Interval:
    """Used internally by AdaptiveTimer to track interval-related attributes"""

    def __init__(self, target: int | float) -> None:

        assert target >= 0, "target interval must be >= 0"

        self._target = target
        self._begin_timestamp = None

        # Tuples of (value, delta)
        self._actual = (None, None)
        self._offset = (0, None)

    @property
    def target(self) -> int | float:
        return self._target

    @target.setter
    def target(self, value: int | float) -> None:
        assert value >= 0, "target interval must be >= 0"
        self._target = value
        self._offset = (0, None)
        logger.debug("Resetting target interval to %i seconds", self._target)
        self.reset()

    @property
    def actual(self) -> int | float | None:
        return self._actual[0]

    def _set_actual(self, value: int | float):

        assert value > 0, "actual interval must be >0"

        current_value = self._actual[0]

        if current_value is None:
            self._actual = (value, None)
            return

        self._actual = (value, round(value - current_value, PRECISION))

    def actual_delta(self) -> int | float | None:
        return self._actual[1]

    @property
    def offset(self) -> int | float:
        return self._offset[0]

    @offset.setter
    def offset(self, value: int | float) -> None:

        assert value <= 0, "offset must be <= 0"

        assert (
            value + self._target >= 0
        ), f"target + offset must be >=0. ({self._target} + {value}) "

        current_offset = self._offset[0]

        self._offset = (value, round(value - current_offset, PRECISION))

    def offset_delta(self) -> int | float | None:
        return self._offset[1]

    def cycle(self) -> None:
        """Begins new interval after calculating duraction of previous interval"""
        now = ticks_us()

        if self._begin_timestamp is not None:

            td = ticks_diff(now, self._begin_timestamp)

            self._set_actual(td / 1_000_000)

        self._begin_timestamp = now

    async def _sleep(self, seconds):
        """Wraps asyncio.sleep to enable mocking in unit tests"""
        await asyncio.sleep(seconds)  # pragma: no cover

    async def wait_for_next_cycle(self):
        await self._sleep(self._target + self.offset)

    def reset(self) -> None:
        """Invalidates timing of the current interval and forces recalculation."""

        self._actual = (None, None)
        self._begin_timestamp = None

    def variance(self) -> float | None:
        """Returns the percentage deviation of actual to target interval"""
        if self.actual is not None:
            return round((self.actual - self._target) / self._target, PRECISION)

        return None
