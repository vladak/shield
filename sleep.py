"""
Utility functions and class for putting the microcontroller to sleep.
"""

import time

import adafruit_logging as logging

# pylint: disable=import-error
import alarm


# pylint: disable=too-few-public-methods
# There is no Enum class in CircuitPython so this is a bare class.
class SleepKind:
    """
    Sleep kind.
    """

    LIGHT = 1
    DEEP = 2

    def __init__(self, kind: int):
        if kind not in (self.LIGHT, self.DEEP):
            raise ValueError("not a valid kind")

        self.kind = kind

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.kind == self.LIGHT:
            return "light"
        if self.kind == self.DEEP:
            return "deep"

        return "N/A"


def enter_sleep(sleep_period: int, sleep_kind: SleepKind) -> None:
    """
    Enters light or deep sleep.
    """
    logger = logging.getLogger("")

    logger.info(f"Going to {sleep_kind} sleep for {sleep_period} seconds")

    now = time.monotonic()
    logger.debug(f"time now: {now}")
    logger.debug(f"alarm time: {now + sleep_period}")
    # Create an alarm that will trigger sleep_period number of seconds from now.
    time_alarm = alarm.time.TimeAlarm(monotonic_time=now + sleep_period)

    if sleep_kind.kind == SleepKind.LIGHT:
        alarm.light_sleep_until_alarms(time_alarm)
    else:
        # Exit and deep sleep until the alarm wakes us.
        alarm.exit_and_deep_sleep_until_alarms(time_alarm)
