"""Shows what happens when attempting to maintain a constant looping interval
with a noisy neighbot using cooperative multitasking"""

import asyncio
import random
import traceback
from statistics import mean, pvariance
from time import sleep, time


random.seed()

previous = None
interval_history = []


def do_something():
    global previous, interval_history

    sleep(0.1)  # Simulate a workload of 0.1s

    now = time()

    if previous is not None:

        actual_interval = now - previous
        interval_history.append(actual_interval)
        print(f"Hello, World! actual_interval: {actual_interval:.3f}s")

    previous = now


async def do_something_every_second():

    while True:
        do_something()
        await asyncio.sleep(0.9)  # deducting .1s to compensate for known workload


async def noisy_neighbor():

    while True:
        # Simulate a workload of 0.5s with +/- 50% variation and 0.25s pause

        noisy_workload = random.uniform(0.25, 0.75)
        sleep(noisy_workload)

        await asyncio.sleep(0.25)


async def main():

    try:
        await asyncio.gather(do_something_every_second(), noisy_neighbor())

    except Exception:
        print(traceback.print_exc())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(
            f"\nmean(actual_interval): {mean(interval_history):.4f}\n"
            f"variance(actual_interval): {pvariance(interval_history, 1):.4f} (relative to 1s target)"
        )
