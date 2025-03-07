"""Demonstration of AdaptiveTimer for maintaining steady loop intervals in the presence
of a noisy neighbor"""

import asyncio
import random
from statistics import mean, pvariance
import traceback
from time import sleep, time

from adaptive_timer import AdaptiveTimer

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

    await AdaptiveTimer(1).start(do_something)


async def noisy_neighbor():

    while True:
        # Simulate a workload of 0.5s with +/- 50% variation and 0.25s pause

        noisy_workload = random.uniform(0.25, 0.75)
        sleep(noisy_workload)

        await asyncio.sleep(0.25)


def deleteme_main():

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    tasks = [
        loop.create_task(do_something_every_second()),
        loop.create_task(noisy_neighbor()),
    ]

    try:
        loop.run_until_complete(asyncio.wait(tasks))
    except KeyboardInterrupt:
        print(
            f"\nmean(actual_interval): {mean(interval_history):.4f}\n"
            f"variance(actual_interval): {pvariance(interval_history, 1):.4f} (relative to 1s target)"
        )
    finally:
        for task in tasks:
            task.cancel()


async def main():

    try:
        await asyncio.gather(do_something_every_second(), noisy_neighbor())

    except Exception as e:
        print(traceback.print_exc())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(
            f"\nmean(actual_interval): {mean(interval_history):.4f}\n"
            f"variance(actual_interval): {pvariance(interval_history, 1):.4f} (relative to 1s target)"
        )
