import unittest
import time
from adaptive_timer.interval import Interval


class TestInterval(unittest.TestCase):

    def assert_initial_state(self, i):
        self.assertIsNone(i.actual)
        self.assertIsNone(i.actual_delta())
        self.assertIsNone(i.variance())

    def test_initial_state(self):

        for _, value in enumerate([10, 11.5]):

            i = Interval(value)
            self.assertEqual(i.target, value)
            self.assertEqual(i.offset, 0)
            self.assertIsNone(i.offset_delta())
            self.assert_initial_state(i)

    def test_delta_calculations_and_reset(self):
        i = Interval(1.2)

        i.offset = -1
        self.assertEqual(i.offset, -1)
        self.assertEqual(i.offset_delta(), -1)
        i.offset = -0.6
        self.assertEqual(i.offset, -0.6)
        self.assertEqual(i.offset_delta(), 0.4)

        i._set_actual(0.001)
        self.assertEqual(i.actual, 0.001)
        self.assertIsNone(i.actual_delta())

        i._set_actual(9.8)
        self.assertEqual(i.actual_delta(), 9.799)
        i._set_actual(9.799)

        self.assertEqual(i.actual_delta(), -0.001)

        i.reset()
        self.assert_initial_state(i)

    def test_variance(self):
        i = Interval(5)
        self.assertIsNone(i.variance())

        i._set_actual(5.5)
        self.assertEqual(i.variance(), 0.1)

        i._set_actual(4)
        self.assertEqual(i.variance(), -0.2)

    def test_assertions(self):
        # ensure that the actual remains positive
        i1 = Interval(1)

        with self.assertRaises(AssertionError):
            i1._set_actual(-1)

        with self.assertRaises(AssertionError):
            i1._set_actual(0)

        with self.assertRaises(AssertionError):
            i2 = Interval(-1)

        i3 = Interval(0)

    def test_target_updates(self):

        i = Interval(1)
        self.assertEqual(i.target, 1)
        i.target = 2
        self.assertEqual(i.target, 2)
        i.target = 0
        self.assertEqual(i.target, 0)

        with self.assertRaises(AssertionError):
            i.target = -1

    def test_update(self):
        i = Interval(42)
        self.assertIsNone(i.actual)
        self.assertIsNone(i._begin_timestamp)

        i.cycle()
        self.assertIsNotNone(i._begin_timestamp)
        self.assertIsNone(i.actual)
        time.sleep(0.001)
        i.cycle()
        self.assertIsNotNone(i._begin_timestamp)
        self.assertIsNotNone(i.actual)

    def test_offset_validation(self):

        i = Interval(10)

        with self.assertRaises(AssertionError):
            i.offset = 1

        with self.assertRaises(AssertionError):
            i.offset = -11

        i.offset = 0
        i.offset = -10

        self.assertEqual(i.offset, -10)
        i.target = 11
        self.assertEqual(i.offset, 0)
