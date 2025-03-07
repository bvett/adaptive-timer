# Print 'Hello, World!' every 1s while toggling on/off an extra 0.75s load every 5s

import asyncio
import time
from adaptive_timer import AdaptiveTimer


async def loop():

    def workload():
        nonlocal t, i

        suffix = ""

        if int(i / 5) % 2 == 1:
            suffix = " (with 0.75s load)"
            time.sleep(0.75)

        now = time.time()
        print(f"Hello, World! Time since last message: {now-t:.3f}{suffix}")
        t = now

        i += 1

    t = time.time()
    i = 0

    await AdaptiveTimer(1).start(workload)


asyncio.run(loop())
