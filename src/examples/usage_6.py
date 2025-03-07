"""Demonstrates how to handle exceptions raised by the get_value callback"""

import asyncio
import random
import traceback

from adaptive_timer import AdaptiveTimer

random.seed()

timer = AdaptiveTimer(1)


interval = 0


def produce_value():
    if interval == 5:
        raise Exception("Simulating an error condition in the callback")

    return random.randint(0, 100)


def producer_exception_handler(e):
    print(f"Handling exception and carrying on: {e}")


async def produce_value_every_second():
    await timer.start(produce_value, producer_exception_handler)


async def consume_values():
    global interval

    while interval < 10:
        interval += 1

        value = await timer.value()
        print(f"Value({interval}): {value}")

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
