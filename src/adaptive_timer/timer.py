import asyncio
from .interval import Interval, PRECISION


class AdaptiveTimer:
    """Executes a callback periodically while attempting to maintain the
    interval within a set variance."""

    def __init__(
        self,
        target_interval: float,
        max_variance: float | None = None,
    ) -> None:
        """

        Args:
            target_interval:
                Duration (in seconds) between value updates
            max_variance:
                An exception will be raised if the actual interval deviates from target_interval
                more than max_variance.

                If None, breaches of max_variance are ignored.

                Defaults to None

        Raises:
            ValueError if the actual interval exceeds max_variance, if specified.
        """

        assert target_interval > 0, f"target_interval ({target_interval}) is not > 0"

        assert (
            max_variance is None or max_variance > 0
        ), f"max_variance ({max_variance}) is less than 0"

        self._interval = Interval(target_interval)

        self.max_variance = max_variance
        self._new_value_available = asyncio.Event()
        self._value = None
        self._stop = None

    async def value(self) -> None | object:
        """Awaits the value returned during the next interval

        Returns:
            None | object: value returned by the get_value callback
            provided to AdaptiveTimer.start()
        """
        await self._new_value_available.wait()
        self._new_value_available.clear()
        return self._value

    @property
    def interval(self) -> float:
        """Returns the current target interval."""

        return self._interval.target

    @interval.setter
    def interval(self, target_interval: float) -> None:
        """Sets the target interval."""

        assert (
            target_interval > 0
        ), f"target_interval ({
            target_interval}) is not > 0"

        self._interval.target = target_interval

    async def start(self, get_value, exception_handler=None) -> None:
        """Starts a loop to call get_value at the target interval

            Call stop() to exit the loop.

        Args:
            get_value (Callable[[], object]): callback
            exception_handler (FuncType | None): If specified, any
            exception raised by get_value will be passed to it for initial handling
            Expects a single argument of type Exception
        """

        self._interval.reset()
        self._stop = False

        while not self._stop:

            try:

                self._value = get_value()

            # pylint: disable=broad-exception-caught

            except Exception as e:
                # If the get_value() callback throws an exception,
                # try again after delegating the exception

                if exception_handler is not None:
                    exception_handler(e)
                else:
                    raise e

                self._value = None
                self._interval.reset()

            else:
                self._interval.cycle()

            self._new_value_available.set()
            self._interval.offset = self._estimate_offset()

            await self._interval.wait_for_next_cycle()

    def stop(self) -> None:
        """Stops the excecution of the loop."""
        self._stop = True

    def _estimate_offset(self) -> float:

        # pecentage delta between _interval.actual and _interval.target
        variance_from_target = self._interval.variance()

        current_offset = self._interval.offset

        # Scenario 1
        #
        # When variance_from_target cannot be calculated
        # continue to use current_offset

        if not variance_from_target:
            return current_offset

        # Scenario 2
        #
        # Raise a ValueError if variance_from_target exceedes maximum variance, if specified

        if (self.max_variance is not None) and (
            abs(variance_from_target) > self.max_variance
        ):
            raise ValueError(
                f"Timer interval of {self._interval.actual}s "
                f"deviates more than {self.max_variance:.2%} "
                f"from expected interval of {self._interval.target}s"
            )

        # Scenario 3
        #

        # Adjust the current offset by amount of variance from the target interval
        target_offset = current_offset - (variance_from_target * self._interval.target)

        # ensure the offset remains in the range of -target_interval <= offset <= 0
        # interval cannot be offset more than itelf, and having a positive offset means an interval
        # that is greater than the target, which doesn't make sense to do.

        new_offset = round(
            max(
                -self._interval.target,
                min(
                    target_offset,
                    0,
                ),
            ),
            PRECISION,
        )

        return new_offset

    def state(self) -> dict[str, int | float | None]:
        """Returns a dictionary with the timer's internal state:

        actualInterval:
            Duration (in seconds) of the most recent measured interval.
            'None' for the initial iteration or when previous iteration
            was inavalidated
        actualIntervalDelta:
            Most recent change in actualInterval.
        maxVariance:
            'None' or the maximum variance allowed by the timer
        variance:
            Percentage difference between the actual and target intervals.
        offset:
            Used internally by the timer to calculate how long to sleep between intervals.
        offsetDelta: Most recent change in the offset
        """

        result = {
            "actualInterval": self._interval.actual,
            "actualIntervalDelta": self._interval.actual_delta(),
            "maxVariance": self.max_variance,
            "variance": self._interval.variance(),
            "offset": self._interval.offset,
            "offsetDelta": self._interval.offset_delta(),
        }

        return result
