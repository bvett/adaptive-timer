

# AdaptiveTimer
### Contents
- [Introduction](#introduction)
- [Hello, World!](#hello-world)
- [Feature Demos](#feature-demos)
  - [asyncio.sleep() vs AdaptiveTimer](#asynciosleep-vs-adaptivetimer)
  - [Producer / Consumer](#producer--consumer)
  - [Start / Stop](#start--stop)
  - [Changing the Target Interval](#changing-the-target-interval)
  - [Variance Limit](#variance-limit)
  - [Handling Exceptions](#handling-exceptions)
  - [Introspection](#introspection)
- [Simulation](#simulation)
  - [Configuration](#configuration)
  - [Interpreting the Plots](#interpreting-the-plots)
  - [Sample Scenarios](#sample-scenarios)
    - [Constant Load](#constant-load)
    - [Oscillating Load](#oscillating-load)
    - [Overload](#overload)
    - [Overload With Max](#overload-with-max)
    - [Random Chaos](#random-chaos)

## Introduction
AdaptiveTimer executes a workload at a designated interval while minimizing variance.  It is designed for use in single-threaded applications using cooperative multitasking, such as those running on microcontrollers with [MicroPython](https://micropython.org/).

For example, the following code intends to execute *do_something()* once every second:

```python
async def do_something_every_second():
    while True:
        do_something()
        await asyncio.sleep(1)
```

However, the actual interval in which *do_something()* may vary from 1 second due to:
* Time required for *do_something()* to execute
* Time spent awaiting other tasks

The [Hello, World!](#hello-world) example demonstrates this along with how to apply AdaptiveTimer to reduce the variance.

### AdaptiveTimer Features
- Minimizes variance between actual and target intervals
- Enforces variance upper limit
- Supports decoupled producer/consumer model for data capture and distribution

### Concepts
The *start(get_value)* and *stop()* instance methods of AdaptiveTimer control a loop that:
1. Executes the get_value callback, stores its return value, then notifies consumers 
2. Calculates how much time has elapsed since the last loop and stores this as the **actual interval**
3. Compares the **actual interval** to the **target interval** and calculates the percentage difference as the **variance**
4. If the **variance** exceeds **max variance**, raises an exception
5. Calculates an **offset** to compensate for any variance from the target interval.
6. Sleeps for **target interval + offset** seconds. (Offset is a negative number)

While the loop is sleeping, and tasks awaiting on the *value()* instance method will wake up and process the value obtained during the most recent interval of the loop.

## Hello, World!
This example uses AdaptiveTimer to print a message every second, while compensating for a 0.75 second workload that is toggled on/off every 5s.

The shell commands below assume use of Linux/MacOS.  

1. Ensure you are using python 3.9 or later
```shell
$ python --version
Python 3.13.1
```

2. In an empty directory, create a virtual environment and activate it
``` shell
$ python -m venv .venv
$ source .venv/bin/activate
(.venv) $ 
```

3. Install the latest version of adaptive-timer using pip

```shell
(.venv) $ pip install adaptive-timer
Collecting adaptive-timer
  Downloading adaptive_timer-0.3.5-py3-none-any.whl.metadata (23 kB)
Collecting pycopy-cpython-utime>=0.5.2 (from adaptive-timer)
  Using cached pycopy_cpython_utime-0.5.2-py3-none-any.whl
Downloading adaptive_timer-0.3.5-py3-none-any.whl (11 kB)
Installing collected packages: pycopy-cpython-utime, adaptive-timer
Successfully installed adaptive-timer-0.3.5 pycopy-cpython-utime-0.5.2
```

4. Create [hello_world.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/hello_world.py) with the following:
```python
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

```

5. Run hello_world.py for about 20-30 seconds, then press ctrl-c to exit:

```shell
(.venv) $ python hello_world.py 
Hello, World! Time since last message: 0.000
Hello, World! Time since last message: 1.001
Hello, World! Time since last message: 1.000
Hello, World! Time since last message: 1.000
Hello, World! Time since last message: 1.001
Hello, World! Time since last message: 1.755 (with 0.75s load)
Hello, World! Time since last message: 0.998 (with 0.75s load)
Hello, World! Time since last message: 1.001 (with 0.75s load)
Hello, World! Time since last message: 1.001 (with 0.75s load)
Hello, World! Time since last message: 1.000 (with 0.75s load)
Hello, World! Time since last message: 0.245
Hello, World! Time since last message: 1.000
Hello, World! Time since last message: 1.000
Hello, World! Time since last message: 1.000
Hello, World! Time since last message: 1.000
Hello, World! Time since last message: 1.753 (with 0.75s load)
Hello, World! Time since last message: 1.001 (with 0.75s load)
Hello, World! Time since last message: 1.001 (with 0.75s load)
Hello, World! Time since last message: 0.997 (with 0.75s load)
Hello, World! Time since last message: 1.003 (with 0.75s load)
Hello, World! Time since last message: 0.245
Hello, World! Time since last message: 1.000
Hello, World! Time since last message: 1.000
Hello, World! Time since last message: 1.000
Hello, World! Time since last message: 1.000
Hello, World! Time since last message: 1.755 (with 0.75s load)
Hello, World! Time since last message: 1.000 (with 0.75s load)
Hello, World! Time since last message: 1.000 (with 0.75s load)
Hello, World! Time since last message: 1.000 (with 0.75s load)
Hello, World! Time since last message: 1.000 (with 0.75s load)
Hello, World! Time since last message: 0.245
Hello, World! Time since last message: 1.000
Hello, World! Time since last message: 1.000
Hello, World! Time since last message: 1.000
Hello, World! Time since last message: 1.000
Hello, World! Time since last message: 1.755 (with 0.75s load)
Hello, World! Time since last message: 1.000 (with 0.75s load)
Hello, World! Time since last message: 1.000 (with 0.75s load)
Hello, World! Time since last message: 1.000 (with 0.75s load)
Hello, World! Time since last message: 0.997 (with 0.75s load)
Hello, World! Time since last message: 0.248
Hello, World! Time since last message: 1.000
^CTraceback (most recent call last):

```
Ignore the stack trace - there is no exception handling in this example.

### What This Demonstrates
AdaptiveTimer automatically attempts to compensate when the actual interval deviates from the target (1s, in this example.)   When the workload appears, the interval temporarily increases proportionately, but then returns to the target interval as AdaptiveTimer compensates in its internal cycle.  The opposite happens when the workload is removed.


## Feature Demos

### asyncio.sleep() vs AdaptiveTimer
This section provides a side-by-side comparison of a simple application that attempts to print a message at exactly 1-second intervals.  In the first example, the interval is achieved by calling *asyncio.sleep()*, while the second interval is modified to use AdaptiveTimer.

#### Example 1: Fixed Interval
[example_1.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/example_1.py) measures the actual time spent in a cycle of *do_something_every_second()* given a 0.1s time cost for *do_something()* and a competing coroutine, *noisy_neighbor()*:
 
```python
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

```

To help ensure a realistic comparison, *do_something_every_second()* sleeps for 0.9s rather than the target interval of 1.0s.  A developer would likely make this adjustment knowing that do_something() imparts a 0.1s time cost.

From the project directory, execute [src/examples/example_1.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/example_1.py) for a few iterations then press **ctrl-c** to terminate:

```shell
[adaptive-timer]$ python src/examples/example_1.py 
Hello, World! actual_interval: 1.378s
Hello, World! actual_interval: 1.006s
Hello, World! actual_interval: 1.137s
Hello, World! actual_interval: 1.578s
Hello, World! actual_interval: 1.007s
Hello, World! actual_interval: 1.007s
Hello, World! actual_interval: 1.540s
Hello, World! actual_interval: 1.064s
Hello, World! actual_interval: 1.006s
Hello, World! actual_interval: 1.122s
Hello, World! actual_interval: 1.007s
Hello, World! actual_interval: 1.153s
^C
mean(actual_interval): 1.1670
variance(actual_interval): 0.0692 (relative to 1s target)
[adaptive-timer]$ 
```

The statistics show the mean interval and statistical variance relative to the target of 1s.  These are used for comparison next.

#### Example 2: Adaptive Interval

[example_2.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/example_2.py) adapts example_1.py to use AdaptiveTimer to achieve the desired interval of 1s:

```python
async def do_something_every_second():

    await AdaptiveTimer(1).start(do_something)
```

Execute [src/examples/example_2.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/example_2.py) for a few iterations then press ctrl-c to terminate. 

```shell
[adaptive-timer]$ python src/examples/example_2.py 
Hello, World! actual_interval: 1.373s
Hello, World! actual_interval: 0.736s
Hello, World! actual_interval: 1.324s
Hello, World! actual_interval: 0.713s
Hello, World! actual_interval: 1.282s
Hello, World! actual_interval: 0.862s
Hello, World! actual_interval: 0.816s
Hello, World! actual_interval: 1.502s
Hello, World! actual_interval: 0.593s
Hello, World! actual_interval: 0.905s
Hello, World! actual_interval: 1.000s
^C
mean(actual_interval): 1.0097
variance(actual_interval): 0.0868 (relative to 1s target)
```

The result above shows how using AdaptiveTimer results in intervals that are closer to the 1s target.


### Producer / Consumer
[usage_1.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/usage_1.py) demonstrates how AdaptiveTimer can be used in a basic producer/consumer application.  

This is useful when downstream processing (such as storage, display, or transmitting) needs to occur whenever a value is captured.   

```python
timer = AdaptiveTimer(1)

def produce_value():
    return random.randint(0, 100)

async def produce_value_every_second():
    await timer.start(produce_value)

async def consume_values():
    while True:
        value = await timer.value()
        print(f"Value: {value}")
```

AdaptiveTimer (*timer*, in these examples) executes *produce_values()* once every second, and makes the latest result available through *value()*

*consume_values()* is a second coroutine that awaits *timer.value()* until a new value is produced.  This allows multiple consumers to be notified without the need for polling.

For IoT devices using MicroPython, this is a useful pattern to follow for processing sensor input, replacing *random.randint()* with hardware-specific instructions.

Execute [src/examples/usage_1.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/usage_1.py)  for a few iterations and exit by pressing ctrl-c:

```shell
[adaptive-timer]$ python src/examples/usage_1.py 
Value: 64
Value: 24
Value: 53
Value: 28
Value: 15
Value: 69
Value: 22
Value: 7
Value: 51
Value: 39
^CExiting.
```

### Start / Stop
In the previous examples, AdaptiveTimer has been allowed to run indefinitely until interrupted by the user.   To programmatically stop AdaptiveTimer, use its *stop()* instance method.

**Note:** : It is up to the application to ensure other coroutines/tasks are cancelled after *stop()* is executed.  Otherwise, those routines will become deadlocked awaiting *timer.value()*

[usage_2.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/usage_2.py) modifies *consume_values()* to exit and stop *timer* after 10 iterations:


```python
interval = 0

async def consume_values():
    global interval

    while interval < 10:
        interval += 1

        value = await timer.value()
        print(f"Value({interval}): {value}")

    timer.stop()

```
It also introduces a minor modification in *main()* to print *"Goodbye!"* when the application exits naturally:

```python
...
try:
        loop.run_until_complete(asyncio.wait(tasks))
    except KeyboardInterrupt:
        print("Exiting.")
    else:
        print("Goodbye!")
    finally:
        for task in tasks:
            task.cancel()

```

Executing [src/examples/usage_2.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/usage_2.py) shows the result of these changes:

```shell
[adaptive-timer]$ python src/examples/usage_2.py 
Value(1): 44
Value(2): 95
Value(3): 15
Value(4): 13
Value(5): 2
Value(6): 8
Value(7): 0
Value(8): 20
Value(9): 48
Value(10): 58
Goodbye!
[adaptive-timer]$ 
```

### Changing the Target Interval

There may be times when an application needs to change the target interval after *timer.start()* is called, for example in response to user input.  This is accomplished by setting the *interval* property of an AdaptiveTimer.

Executing [src/examples/usage_3.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/usage_3.py) demonstrates this by reducing the interval from 1s to 0.5s after 5 iterations:

```python
async def consume_values():
    global interval

    while interval < 10:
        interval += 1

        value = await timer.value()
        print(f"Value({interval}): {value}")

        if interval == 5:
            print("Setting the timer interval to 0.5s.")
            timer.interval = 0.5

    timer.stop()
```

```shell
[adaptive-timer]$ python src/examples/usage_3.py 
Value(1): 47
Value(2): 23
Value(3): 80
Value(4): 13
Value(5): 25
Setting the timer interval to 0.5s.
Value(6): 80
Value(7): 10
Value(8): 18
Value(9): 80
Value(10): 22
Goodbye!
[adaptive-timer]$ 
```


### Variance Limit
This example demonstrates how to configure AdaptiveTimer to raise an exception when the [variance](#concepts) exceeds a designated maximum.  By default, the variance is unbounded.

First step is to modify *consume_values()* in [usage_4.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/usage_4.py) to print the variance, and to introduce an additional delay on the 7th iteration:

```python
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

```

This introduces *AdaptiveTimer.state()* which is useful for getting the internal state of the timer.  A full list of attributes available via this method is described in section [Introspection](#introspection)

The delay is being introduced in a contrived manner here for simplicity.  In practice, unexpected delays can happen due for many reasons, such as I/O delays or exceptions in other coroutines.

Executing [src/examples/usage_4.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/usage_4.py) shows an approximately 51% variance between intervals 7 and 8:

```shell
[adaptive-timer]$ python src/examples/usage_4.py 
Value(1): 35 Actual Interval: None Variance: None
Value(2): 22 Actual Interval: 1.001 Variance: 0.001
Value(3): 50 Actual Interval: 1.001 Variance: 0.001
Value(4): 92 Actual Interval: 0.999 Variance: -0.001
Value(5): 41 Actual Interval: 1.001 Variance: 0.001
Setting the timer interval to 0.5s.
Value(6): 82 Actual Interval: None Variance: None
Value(7): 1 Actual Interval: 0.501 Variance: 0.002
Value(8): 8 Actual Interval: 0.756 Variance: 0.512
Value(9): 92 Actual Interval: 0.244 Variance: -0.512
Value(10): 40 Actual Interval: 0.501 Variance: 0.002
Goodbye!
[adaptive-timer]$ 
```

This is allowed to pass because instance attribute *max_variance* is *None* by default.

Modifying the initialization of *timer* as shown below will result in an exception if the variance exceeds 25% (positive or negative.)

```python
timer = AdaptiveTimer(1, max_variance=0.25)
```

[src/examples/usage_5.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/usage_5.py) contains this minor modification, and running it results in a ValueError exception being thrown:

```shell
[adaptive-timer]$ python src/examples/usage_5.py 
Value(1): 22 Actual Interval: None Variance: None
Value(2): 48 Actual Interval: 1.002 Variance: 0.002
Value(3): 9 Actual Interval: 0.999 Variance: -0.001
Value(4): 16 Actual Interval: 1.001 Variance: 0.001
Value(5): 78 Actual Interval: 0.998 Variance: -0.002
Setting the timer interval to 0.5s.
Value(6): 63 Actual Interval: None Variance: None
Value(7): 65 Actual Interval: 0.501 Variance: 0.002
Value(8): 40 Actual Interval: 0.754 Variance: 0.508
Timer interval of 0.754s deviates more than 25.00% from expected interval of 0.5s
[adaptive-timer]$ 
```

There is no universally 'correct' value for *max_variance* - it depends on the natural volatility of the application, which is minimal in these contrived examples.  The section on [Simulation](#simulation) provides a visualization of variance under different types of workload. 

### Handling Exceptions
```python
async def start(self, get_value, exception_handler=None)
```
To enable better exception handling, *start()* supports a second callback, *exception_handler*.  If provided, any exception raised by *get_value* is first sent to *exception_handler*, and if not handled, raised up through AdaptiveTimer.

This is useful for dealing with intermittent hardware failures that prevent value-capture.

By default, any exceptions raised while calling the *get_value* parameter of *timer.start()* are propagated up through AdaptiveTimer, essentially treating any exception as fatal.  


[usage_6.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/usage_6.py) demonstrates this by modifying an earlier example to raise an exception on the 5th iteration, and have it handled (swallowed) by providing a custom exception handler to *timer.start()*:

```python

interval = 0

def produce_value():
    if interval == 5:
        raise Exception("Simulating an error condition in the callback")

    return random.randint(0, 100)


def producer_exception_handler(e):
    print(f"Handling exception and carrying on: {e}")


async def produce_value_every_second():
    await timer.start(produce_value, producer_exception_handler)

```

Executing [src/examples/usage_6.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/usage_6.py) demonstrates this:

```shell
[adaptive-timer]$ python src/examples/usage_6.py 
Value(1): 34
Value(2): 73
Value(3): 38
Value(4): 85
Handling exception and carrying on: Simulating an error condition in the callback
Value(5): None
Value(6): 79
Value(7): 17
Value(8): 11
Value(9): 100
Value(10): 36
Goodbye!
[adaptive-timer]$ 
```

### Introspection

```python
def state(self) -> dict[str, int | float | None]:
```

The *state()* instance method of an AdaptiveTimer returns a dictionary containing its internal state.  This is useful for testing and visualization, as demonstrated in [usage_5.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/usage_5.py) and [simulator.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/simulator.py) (introduced in a following section) 


The following properties are returned:

  - **actualInterval**: Duration (in seconds) of the most recent measured interval. 'None' for the initial iteration or when previous iteration was invalidated
  - **actualIntervalDelta**: Most recent change in actualInterval.
  - **maxVariance**: 'None' or the maximum variance allowed by the timer
  - **variance**: Percentage difference between the actual and target intervals.
  - **offset**: Used internally by the timer to calculate how long to sleep between intervals.
  - **offsetDelta**: Most recent change in the offset


## Simulation
[simulator.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/simulator.py) executes an AdaptiveTimer at a designated *target_interval* and with a simulated workload.  It then plots the resulting *actual_interval* and *variance* to show how well the AdaptiveTimer is able to maintain the target_interval.
### Configuration

#### Install Dependencies
In addition to adaptive-timer, install NumPy and Matplotlib.

```shell
(.venv) $ pip install adaptive-timer numpy matplotlib
```
#### Configure Scenario

Before running any of the following ([scenarios](#sample-scenarios)), edit the *Scenario* class in [simulator.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/simulator.py).  Jump ahead to [Sample Scenarios](#sample-scenarios) below to execute simulations.

```python
class Scenario:
    """Collection of configuration attributes"""

    target_interval = 0.1 
    max_variance = None
    workload = lambda: Workload.oscillate(50, SCENARIO.target_interval * 0.25)
```
  * **target_interval** : Expected duration of each interval, in seconds.

  * **max_variance** :  Defines the upper limit for *variance*.  If specified, a *ValueError* will be raised if exceeded.

  * **workload** : Defines the amount of simulated workload that is generated at each interval.
    - Changes in workload result in AdaptiveTimer having to recalculate the amount of time it sleeps in between intervals.   See *offset* (below) for details.
    - Defined by a lambda that calls one of the helper methods of the *Workload* class.
      + **Workload.constant(seconds)** : Sleeps for a fixed number of seconds.
      + **Workload.oscillate(iterations_per_cycle, max_load)** : Sine-wave workload that varies between zero and (*max_load* * *target_interval*) seconds.  Setting *max_load* too high (e.g. closer to 1.00) will result in overload, where AdaptiveTimer is not able to compensate further.
      + **Workload.random(base, variation)** : Generates random workloads that are within *variation* percent of *base* 

### Interpreting the Plots
  * <ins>target</ins>: target interval.  Specified by Scenario.target_interval.
  * <ins>synthetic load</ins>: Amount of artificial delay injected into an interval
  * <ins>actual</ins>: Actual duration of the interval.  AdaptiveTimer attempts to keep this close to *target*
  * <ins>variance</ins>: Percentage difference between actual and target.
  * <ins>offset</ins>: Typically moves opposite of *synthetic load*.  AdaptiveTimer sleeps for (*target_interval* + *offset*) seconds in between each interval, and will decrease *offset* to compensate for variance increases.
  * <ins>max</ins>: If specified, indicates the maximum limits for *variance*
  * <ins>overload</ins>: Red shading appears on the plots when *offset* == -*target*, meaning that AdaptiveTimer cannot shorten the interval any further.  Further increases in workload will result in a proportionate increase in the actual interval.

### Sample Scenarios
To execute one of these scenarios, first modify the *Scenario* class as indicated then execute [simulator.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/simulator.py).  Close the window to exit.

#### Constant Load

Executes with a fixed load of 30% of *target_interval*:

In [simulator.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/simulator.py):
```python

class SCENARIO:
    """Collection of configuration attributes"""

    target_interval = 0.25
    max_variance = None
    workload = lambda: Workload.constant(SCENARIO.target_interval * 0.30)
```

![simulator_1.png](https://github.com/bvett/adaptive-timer/blob/main/doc/simulator_1.png?raw=true)

With a load of 0.075s, AdaptiveTimer corrects the initial variance by maintaining an offset of -0.077s.  The additional 0.002s is compensating for other processing, such as the overhead of the Matplotlib graphing library.

#### Oscillating Load

This demonstrates how AdaptiveTimer is able to maintain the target interval when presented with a oscillating workload.  As with the previous example, the peak workload is limited to 30% of the target, and the actual interval remains closely aligned to the target interval.

In [simulator.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/simulator.py):
```python
class SCENARIO:
    """Collection of configuration attributes"""

    target_interval = 0.25
    max_variance = None
    workload = lambda: Workload.oscillate(50, SCENARIO.target_interval * 0.30)

```

![simulator_2.png](https://github.com/bvett/adaptive-timer/blob/main/doc/simulator_2.png?raw=true)



Notice how the maximum deflection of the variance occurs when the workload delta is greatest.  This reflects the currently reactive nature AdaptiveTimer, where it can only apply a corrected offset based on the variance of the previous interval.

#### Overload

Similar to the previous example, but with a higher maximum workload of 75% of the target to demonstrate what happens when the timer is not able to further compensate for a high variance.

In [simulator.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/simulator.py):
```python
class SCENARIO:
    """Collection of configuration attributes"""

    target_interval = 0.25
    max_variance = None
    workload = lambda: Workload.oscillate(50, SCENARIO.target_interval * 0.75)

```
![simulator_3.png](https://github.com/bvett/adaptive-timer/blob/main/doc/simulator_3.png?raw=true)

The shaded areas indicate where the offset has reached -target_interval, and therefore AdaptiveTimer cannot shorten the interval further.

#### Overload With Max

Sets an upper limit on the variance to force an exception:

In [simulator.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/simulator.py):
```python
class SCENARIO:
    """Collection of configuration attributes"""

    target_interval = 0.25
    max_variance = 0.2
    workload = lambda: Workload.oscillate(50, SCENARIO.target_interval * 0.90)
```
Increasing the workload and setting a maximum variance of 20% raises the exception as expected, indicating that the AdaptiveTimer failed to maintain an interval within *max_variance*:

![simulator_4.png](https://github.com/bvett/adaptive-timer/blob/main/doc/simulator_4.png?raw=true)

Press enter/return in the terminal to exit the application:

```shell
[adaptive-timer]$ python src/examples/simulator.py 
Timer interval of 0.304s deviates more than 20.00% from expected interval of 0.25s
Press the Enter/Return key to exit.
```

#### Random Chaos
This scenario is more for fun and/or making improvements:

In [simulator.py](https://github.com/bvett/adaptive-timer/blob/main/src/examples/simulator.py):
```python
class SCENARIO:
    """Collection of configuration attributes"""

    target_interval = 0.25
    max_variance = None
    workload = lambda: Workload.random(SCENARIO.target_interval * 0.7, 0.30)
```

This generates random workloads that vary +/- 30% from 0.175 (70% of the target interval)

![simulator_5.png](https://github.com/bvett/adaptive-timer/blob/main/doc/simulator_5.png?raw=true)

Such an unpredictable environment makes it a challenge to maintain a steady interval, however this is where setting *max_variance* can be helpful to throw an exception in the event that the environment unexpectedly become chaotic or overwhelmed.
