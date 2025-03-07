"""Prints the variance of each interval"""

import asyncio
import random
import traceback
from time import sleep

from adaptive_timer import AdaptiveTimer

random.seed()

timer = AdaptiveTimer(1)


def produce_value():
    return random.randint(0, 100)


async def produce_value_every_second():
    await timer.start(produce_value)


interval = 0


async def consume_values():
    global interval

    while interval < 10:
        interval += 1

        value = await timer.value()

        state = timer.state()

        print(
            f"Value({interval}): {value} "
            f"Actual Interval: {state['actualInterval']} "
            f"Variance: {state['variance']}"
        )

        if interval == 5:
            print("Setting the timer interval to 0.5s.")
            timer.interval = 0.5

        if interval == 7:
            sleep(0.75)

    timer.stop()


async def main():

    try:
        await asyncio.gather(produce_value_every_second(), consume_values())

    except ValueError as e:
        print(e)
    except Exception as e:
        print(traceback.print_exc())
    else:
        print("Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting.")
