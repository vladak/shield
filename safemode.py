"""
handle selected modes of safe mode
"""

import time

# pylint: disable=import-error
import alarm
import microcontroller
import storage

# pylint: disable=import-error
import supervisor


# safemode.py & boot.py file write
def precode_file_write(file, data):
    """
    Append data to file with newline. Meant to be run before code.py gets to run.
    """
    storage.remount("/", False)  # writeable by CircuitPython
    with open(file, "a+", encoding="ascii") as file_obj:
        file_obj.write(f"{data}\n")
        file_obj.flush()
    storage.remount("/", True)  # writeable by USB host


reason = supervisor.runtime.safe_mode_reason
precode_file_write("/safemode.log", f"{supervisor.ticks_ms()}: {str(reason)}")

if reason == supervisor.SafeModeReason.HARD_FAULT:
    # pylint: disable=no-member
    microcontroller.reset()  # Reset and start over.
elif reason == supervisor.SafeModeReason.BROWNOUT:
    # Sleep for ten minutes and then run code.py again.
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 10 * 60)
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)
elif reason == supervisor.SafeModeReason.WATCHDOG:
    # pylint: disable=no-member
    microcontroller.reset()  # Reset and start over.

# Otherwise, do nothing. The safe mode reason will be printed in the
# console, and nothing will run.
