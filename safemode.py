"""
handle selected modes of safe mode
"""
import alarm
import microcontroller
import supervisor
import time


safe_mode_reason = supervisor.runtime.safe_mode_reason

if safe_mode_reason == supervisor.SafeModeReason.HARD_FAULT:
    microcontroller.reset()  # Reset and start over.
elif safe_mode_reason == supervisor.SafeModeReason.BROWNOUT:
    # Sleep for ten minutes and then run code.py again.
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic + 10 * 60)
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)
elif safe_mode_reason == supervisor.SafeModeReason.SAFE_MODE_WATCHDOG:
    microcontroller.reset()  # Reset and start over.

# Otherwise, do nothing. The safe mode reason will be printed in the
# console, and nothing will run.
