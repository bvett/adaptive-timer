"""Enables visualization of AdaptiveTimer under dfferent conditions"""

# pylint: disable=missing-function-docstring
import asyncio
import math
import random
import time
import traceback
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import ticker

from adaptive_timer import AdaptiveTimer

np.random.seed()
plt.ion()

# Number of iterations to display
X_WIDTH = 200


class SCENARIO:
    """Collection of configuration attributes"""

    target_interval = 0.25
    max_variance = None
    workload = lambda: Workload.constant(SCENARIO.target_interval * 0.30)


class Workload:
    """Defines methods intended that simulate different workloads when
    used as a callback to AdaptiveTimer.start()."""

    iteration: int = 0

    synthetic_workload: list[float | None] = []

    @classmethod
    def constant(cls, seconds: float):
        """Workload as a fixed number of seconds"""

        cls.synthetic_workload.append(seconds)
        cls.iteration += 1
        time.sleep(seconds)
        return seconds

    @classmethod
    def oscillate(cls, iterations_per_cycle: int, max_load: float) -> float:
        """Workload as a sine wave

        Args:
            iterations_per_cycle (int): Period of the workload sine wave.
                                        Higher numbers result in a lower frequency
            max_load (float): Amplitude of the sine wave, in seconds. Higher numbers result in
                                        overload, where the workload exceeds the ability for
                                        the AdaptiveTimer to maintain the target interval.


        Returns:
            float: Workload expressed in seconds.
        """

        radians = ((cls.iteration / iterations_per_cycle * 360) - 90) * (np.pi / 180)
        factor = (1 + math.sin(radians)) / 2

        workload = factor * max_load

        cls.synthetic_workload.append(workload)
        cls.iteration += 1
        time.sleep(workload)
        return workload

    @classmethod
    def random(cls, base: float, variation: float):

        if cls.iteration == 0:
            load = 0
        else:
            load = random.uniform(base * (1 - variation), base * (1 + variation))

        time.sleep(load)
        cls.synthetic_workload.append(load)
        cls.iteration += 1
        return load


async def consume_timer(timer: AdaptiveTimer):

    x: dict[str, list[float | None]] = {}
    x["actual"] = []
    x["offset"] = []
    x["variance"] = []

    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)

    plt.suptitle("Demonstration of AdaptiveTimer")

    while plt.fignum_exists(fig.number):

        await timer.value()
        state = timer.state()

        x["actual"].append(state["actualInterval"])
        x["offset"].append(state["offset"])
        x["variance"].append(state["variance"])

        ax1.clear()
        ax2.clear()

        ax1.set_title(
            f"target:{SCENARIO.target_interval} | " f"max={timer.max_variance} | ",
            fontsize="10",
            color="grey",
        )

        ax1.grid(axis="x")
        ax1.set_ylabel("Seconds")

        ax2.grid(axis="x")
        ax2.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1.0))
        ax2.set_xlabel("Iteration")
        ax2.set_ylabel("Variance")

        iterations = np.arange(len(x["offset"]))
        ax2.set_xlim(max(0, len(iterations) - X_WIDTH), max(1, len(iterations) - 1))

        ax1.plot(iterations, x["offset"], color="orange", linestyle="-", label="offset")

        ax1.plot(iterations, x["actual"], color="lightseagreen", label="actual")

        ax1.plot(
            iterations,
            Workload.synthetic_workload,
            color="grey",
            label="synthethic load",
        )

        ax1.hlines(
            timer.interval,
            ax2.get_xlim()[0],
            ax2.get_xlim()[1],
            color="green",
            linestyle="dotted",
            label="target",
        )

        ax1.fill_between(
            iterations,
            y1=ax1.get_ylim()[-1] * 0.90,
            y2=-SCENARIO.target_interval,
            where=[v == -SCENARIO.target_interval for v in x["offset"]],
            facecolor="red",
            alpha=0.1,
        )

        ax2.plot(
            iterations,
            x["variance"],
            color="skyblue",
            linestyle="--",
            label="variance",
        )

        if timer.max_variance is not None:

            ax2.hlines(
                [-timer.max_variance, timer.max_variance],
                ax2.get_xlim()[0],
                ax2.get_xlim()[1],
                color="red",
                linestyle="dotted",
                label="max",
            )

        for axis in [ax1, ax2]:
            for line in axis.get_lines():
                y_val = line.get_ydata()[-1]
                axis.annotate(
                    y_val,
                    xy=(1, y_val),
                    xytext=(6, 0),
                    color=line.get_color(),
                    xycoords=axis.get_yaxis_transform(),
                    textcoords="offset points",
                    va="center",
                )

        ax1.legend(loc="upper left")
        ax2.legend(loc="upper left")
        plt.pause(0.01)

        await asyncio.sleep(0)


async def run_timer(timer: AdaptiveTimer):

    try:
        await timer.start(SCENARIO.workload)

    except ValueError as e:
        print(e)
        timer.stop()
        input("Press the Enter/Return key to exit.")


async def main():

    t = AdaptiveTimer(
        SCENARIO.target_interval,
        max_variance=SCENARIO.max_variance,
    )

    try:
        # await asyncio.gather(consume_timer(t), run_timer(t))
        tasks = [
            asyncio.create_task(consume_timer(t)),
            asyncio.create_task(run_timer(t)),
        ]
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    except Exception:
        print(traceback.print_exc())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting.")
