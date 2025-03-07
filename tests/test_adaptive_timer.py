import asyncio
from random import randrange
import sys
import time
import unittest
import unittest.mock
from unittest.mock import patch
from adaptive_timer import AdaptiveTimer


PRINT_INFO = True


class TestAdaptiveTimer(unittest.IsolatedAsyncioTestCase):

    def setUp(self):

        # Mock ticks_diff to enable simulation of actual interval durations

        self.ticks_diff_patcher = patch("adaptive_timer.interval.ticks_diff")
        self.ticks_diff_mock = self.ticks_diff_patcher.start()

        # Use an Event to control when the timer advances to the next cycle
        # Enables assertions timer state and changes to timer attributes

        self._timer_step_event = asyncio.Event()

        async def _sleep_mock(interval, _):

            interval._waiting_task = asyncio.create_task(self._timer_step_event.wait())
            await interval._waiting_task

            self._timer_step_event.clear()

        self._wait_patcher = patch(
            "adaptive_timer.interval.Interval._sleep", new=_sleep_mock
        )

        self._wait_patcher.start()

        def loop_exception_handler(_, context):  # pragma: no cover
            e = context["exception"]
            raise e

        asyncio.get_event_loop().set_exception_handler(loop_exception_handler)

    def tearDown(self):
        self.ticks_diff_patcher.stop()
        self._wait_patcher.stop()

    def assert_timer_state(self, timer, print_info=PRINT_INFO):
        """Used by the test cases to validate the state of the timer at each teration"""
        state = timer.state()
        target_interval = timer.interval
        offset = state["offset"]
        offset_delta = state["offsetDelta"]
        waiting_time = round(offset + target_interval, 7)
        actual_interval = state["actualInterval"]
        actual_interval_delta = state["actualIntervalDelta"]
        variance = state["variance"]
        val = timer._value

        if print_info is True:
            print(
                f"val:{val} target interval:{target_interval} offset:{offset} "
                f"waiting time:{waiting_time}({offset_delta}) "
                f"actual interval:{actual_interval}({actual_interval_delta}) "
                f"variance:{variance}"
            )  # pragma: no cover

        self.assertGreaterEqual(waiting_time, 0, "waiting time >= 0")

        self.assertLessEqual(
            waiting_time, target_interval, "waiting time <= target interval"
        )

        if variance and waiting_time:
            self.assertNotEqual(
                offset_delta,
                0,
                msg="offset delta is nonzero when variance is nonzero",
            )

            if waiting_time != 0:
                self.assertLess(
                    offset_delta * variance,
                    0,
                    "waiting time moves opposite of variance",
                )

    def sensor_exception_handler(self, e):
        pass

    async def mock_consumer(self, timer, iterations) -> None:

        await timer.value()
        self.assert_timer_state(timer)
        self._timer_step_event.set()

        for iteration in iterations:
            new_interval = iteration[1]
            if new_interval is not None:
                timer.interval = new_interval

            await timer.value()
            self.assert_timer_state(timer)

            self._timer_step_event.set()

        timer.stop()

    async def run_scenario(
        self,
        iterations,
        target_interval=2,
        max_variance: float | None = 0.5,
        sensor_mock=None,
    ):

        if sensor_mock is None:
            sensor_mock = self.SensorMock()

        timer = AdaptiveTimer(target_interval, max_variance=max_variance)
        self.ticks_diff_mock.side_effect = [i[0] * 1_000_000 for i in iterations]

        # is an exception expected?

        expect_exception = len([x for x in iterations if x[2] is True]) > 0

        if expect_exception is True:
            with self.assertRaises(ValueError):

                await asyncio.gather(
                    timer.start(sensor_mock.value, self.sensor_exception_handler),
                    self.mock_consumer(timer, iterations),
                )
        else:

            await asyncio.gather(
                timer.start(sensor_mock.value, self.sensor_exception_handler),
                self.mock_consumer(timer, iterations),
            )

    async def test_data_validation(self):

        # catch negative target_interval
        with self.assertRaises(AssertionError):
            AdaptiveTimer(target_interval=-1)

        # catch zero target_interval
        with self.assertRaises(AssertionError):
            AdaptiveTimer(target_interval=0)

        # catch negative max_variance
        with self.assertRaises(AssertionError):
            AdaptiveTimer(target_interval=2, max_variance=-1)

    async def test_start(self):
        iterations = (
            (2.4, None, False),
            (2.5, None, False),
            (2.0, None, False),
            (2.0, None, False),
            (2.5, None, False),
            (2.5, None, False),
            (2.0, None, False),
            (1.5, None, False),
            (1.5, None, False),
            (2.0, None, False),
            (3.5, None, False),
            (3.5, None, False),
        )

        await self.run_scenario(iterations, max_variance=0.75)

    async def test_exceed_max_variance(self):

        iterations = (
            (4, None, False),
            (4, None, False),
            (6.05, None, True),
            (4, None, False),
        )

        await self.run_scenario(iterations, target_interval=4)

        iterations = (
            (6.05, None, True),
            (4, None, False),
            (4, None, False),
            (4, None, False),
        )

        await self.run_scenario(iterations, target_interval=4)

        iterations = (
            (4, None, False),
            (4, None, False),
            (6, None, False),
            (4, None, False),
        )

        await self.run_scenario(iterations, target_interval=4)

        iterations = (
            (4, None, False),
            (4, None, False),
            (4, None, False),
            (6, None, False),
        )

        await self.run_scenario(iterations, target_interval=4)

    async def test_changed_interval(self):

        iterations = (
            (2, None, False),
            (2, None, False),
            (2, None, False),
            (4, None, True),
            (5, None, False),
            (6, None, False),
            (6, None, False),
        )

        await self.run_scenario(iterations)

        iterations = (
            (2, None, False),
            (2, None, False),
            (2, None, False),
            (4, 4, False),
            (5, None, False),
            (6, None, False),
            (6, None, False),
        )

        await self.run_scenario(iterations)

    async def test_sensor_exception(self):

        iterations = (
            (2.5, None, False),
            (2.5, None, False),
            (2, None, False),
            (2.5, None, False),
            (2, None, False),
            (2, None, False),
            (2, None, False),
            (2, None, False),
        )

        await self.run_scenario(iterations, sensor_mock=self.SensorMockWithExceptions())

    async def test_no_max_variance(self):

        iterations = (
            (2, None, False),
            (2.01, None, False),
            (sys.maxsize, None, False),
            (2, None, False),
            (sys.maxsize, None, False),
            (sys.maxsize, None, False),
            (sys.maxsize, None, False),
            (2, None, False),
        )

        await self.run_scenario(iterations, max_variance=None)

    class SensorMock:
        def value(self):
            return randrange(1, 100)

    class SensorMockWithExceptions:

        def __init__(self, exception_on_iterations=[3, 6]):
            self.exception_on_iterations = exception_on_iterations
            self.iteration = -1

        def value(self):
            self.iteration += 1
            if self.iteration in self.exception_on_iterations:
                raise RuntimeError("Expected Test Exception")
            return randrange(0, 100)
