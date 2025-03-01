"""
Utility functions and class for putting the microcontroller to sleep.
"""

import time

import adafruit_logging as logging

# pylint: disable=import-error
import alarm

# pylint: disable=unused-wildcard-import, wildcard-import
from names import *


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

    #
    # time.monotonic() will start losing precision rather quickly,
    # however for the deep sleep this is not a problem because the internal
    # clock gets reset on deep sleep. It is assumed that light sleep
    # is always followed by deep sleep.
    #
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


def get_deep_sleep_duration(secrets, battery_monitor, logger):
    """
    Get sleep duration, either default or shortened.
    Assumes the device is running on battery.
    """

    sleep_duration = secrets[DEEP_SLEEP_DURATION]

    # If the battery (if there is one) is charged above the threshold,
    # reduce the sleep period. This should help getting the data out more frequently.
    sleep_duration_short = secrets.get(SLEEP_DURATION_SHORT)
    battery_capacity_threshold = secrets.get(BATTERY_CAPACITY_THRESHOLD)
    if (
        sleep_duration_short
        and battery_monitor
        and battery_capacity_threshold
        and sleep_duration_short < sleep_duration
    ):
        current_capacity = battery_monitor.cell_percent
        if current_capacity > battery_capacity_threshold:
            logger.info(
                # f-string would be nicer however CircuitPython does not like 2 f-strings.
                # pylint: disable=consider-using-f-string
                "battery capacity more than {}, using shorter sleep of {} seconds".format(
                    battery_capacity_threshold, sleep_duration_short
                )
            )
            sleep_duration = sleep_duration_short

    return sleep_duration
