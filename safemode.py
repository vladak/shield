"""
handle selected modes of safe mode
"""

import time

# pylint: disable=import-error
import alarm
import microcontroller

# pylint: disable=import-error
import supervisor

safe_mode_reason = supervisor.runtime.safe_mode_reason

if safe_mode_reason == supervisor.SafeModeReason.HARD_FAULT:
    # pylint: disable=no-member
    microcontroller.reset()  # Reset and start over.
elif safe_mode_reason == supervisor.SafeModeReason.BROWNOUT:
    # Sleep for ten minutes and then run code.py again.
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic + 10 * 60)
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)
elif safe_mode_reason == supervisor.SafeModeReason.SAFE_MODE_WATCHDOG:
    # pylint: disable=no-member
    microcontroller.reset()  # Reset and start over.

# Otherwise, do nothing. The safe mode reason will be printed in the
# console, and nothing will run.
