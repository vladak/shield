# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: Unlicense
"""
Acquire values from various sensors, publish to MQTT topic or send via RFM69, enter deep sleep.

This is meant for battery powered devices such as QtPy or ESP32 based devices from Adafruit.
"""
import time
import traceback

import adafruit_logging as logging

try:
    import adafruit_max1704x
except ImportError:
    pass


import board
import busio
import microcontroller

# pylint: disable=import-error
import supervisor

# pylint: disable=no-name-in-module
from microcontroller import watchdog
from watchdog import WatchDogMode, WatchDogTimeout

from confchecks import ConfCheckException, bail, check_tunables
from data import send_data
from logutil import get_log_level

# pylint: disable=wildcard-import, unused-wildcard-import
from names import *
from sensors import Sensors
from sleep import SleepKind, enter_sleep, get_deep_sleep_duration
from transport import setup_transport

try:
    from secrets import secrets  # type: ignore [attr-defined]
except ImportError:
    print(
        "WiFi credentials and configuration are kept in secrets.py, please add them there!"
    )
    raise

# Estimated run time in seconds with some extra room.
# This is used to compute the watchdog timeout.
ESTIMATED_RUN_TIME = 20


#
# Cannot add type hint for the argument because the neopixel import
# is done in a code block to avoid unnecessary execution.
#
def blink(pixel) -> None:
    """
    Blink the Neo pixel blue.
    """
    pixel.brightness = 0.3
    pixel.fill((0, 0, 255))
    time.sleep(0.5)
    pixel.brightness = 0


# pylint: disable=too-many-locals,too-many-statements,too-many-branches
def main():
    """
    Collect environment metrics and battery level
    and publish to MQTT topic or send over RFM69 radio.
    """

    try:
        check_tunables(secrets)
    except ConfCheckException as exception:
        bail(str(exception))

    log_level = get_log_level(secrets.get(LOG_LEVEL))
    logger = logging.getLogger("")
    logger.setLevel(log_level)

    logger.info("Running")

    watchdog.timeout = ESTIMATED_RUN_TIME
    watchdog.mode = WatchDogMode.RAISE

    # Create sensor objects, using the board's default I2C bus.
    try:
        i2c = board.I2C()
    except RuntimeError:
        # QtPy
        i2c = busio.I2C(board.SCL1, board.SDA1)

    #
    # The presence of battery monitor changes the flow (see below),
    # hence it is not part of Sensors.
    #
    battery_monitor = None
    try:
        battery_monitor = adafruit_max1704x.MAX17048(i2c)
    except (NameError, ValueError):
        logger.info("No library for battery gauge (max17048)")

    # Use the LED only in debug mode when powered by battery (to save the battery).
    pixel = None
    if not battery_monitor or log_level == logging.DEBUG:  # pylint: disable=no-member
        # pylint: disable=import-outside-toplevel
        import neopixel

        pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)

    sensors = Sensors(i2c, light_gain=secrets.get(LIGHT_GAIN))

    mqtt_client, rfm69 = setup_transport(secrets)

    while True:
        battery_capacity = None
        if battery_monitor:
            battery_capacity = battery_monitor.cell_percent
            logger.info(f"Battery capacity {battery_capacity:.2f} %")

        # Note that MQTT topic is used for both transports.
        send_data(rfm69, mqtt_client, secrets[MQTT_TOPIC], sensors, battery_capacity)

        if pixel:
            blink(pixel)

        watchdog.feed()

        # Assuming that if the battery monitor is present, the device is running on battery power.
        if battery_monitor:
            logger.info("Running on battery power, breaking out")
            break

        sleep_duration_short = secrets.get(SLEEP_DURATION_SHORT)
        if sleep_duration_short:
            timeout = sleep_duration_short
        else:
            timeout = ESTIMATED_RUN_TIME // 2
        if mqtt_client:
            logger.info(f"Waiting for MQTT event with timeout {timeout} seconds")
            mqtt_client.loop(timeout=timeout)
        else:
            logger.info(f"Sleeping for {timeout} seconds")
            time.sleep(timeout)

    #
    # The rest of the code in this function applies only to devices running on battery power.
    #

    # Sleep a bit so one can break to the REPL when using console via web workflow.
    light_sleep_duration = secrets.get(LIGHT_SLEEP_DURATION)
    if light_sleep_duration is None:
        light_sleep_duration = 10
    if light_sleep_duration > 0:
        enter_sleep(
            light_sleep_duration, SleepKind(SleepKind.LIGHT)
        )  # ugh, ESTIMATED_RUN_TIME

    if mqtt_client:
        mqtt_client.disconnect()

    # Disarm the watchdog.
    watchdog.mode = None

    deep_sleep_duration = get_deep_sleep_duration(secrets, battery_monitor, logger)
    enter_sleep(deep_sleep_duration, SleepKind(SleepKind.DEEP))


def hard_reset(exception):
    """
    Sometimes soft reset is not enough. Perform hard reset.
    """
    watchdog.mode = None
    print(f"Got exception: {exception}")
    reset_time = 15
    print(f"Performing hard reset in {reset_time} seconds")
    time.sleep(reset_time)
    microcontroller.reset()  # pylint: disable=no-member


try:
    main()
except ConnectionError as e:
    # When this happens, it usually means that the microcontroller's wifi/networking is botched.
    # The only way to recover is to perform hard reset.
    hard_reset(e)
except MemoryError as e:
    # This is usually the case of delayed exception from the 'import wifi' statement,
    # possibly caused by a bug (resource leak) in CircuitPython that manifests
    # after a sequence of ConnectionError exceptions thrown from withing the wifi module.
    # Should not happen given the above 'except ConnectionError',
    # however adding that here just in case.
    hard_reset(e)
except Exception as e:  # pylint: disable=broad-except
    # This assumes that such exceptions are quite rare.
    # Otherwise, this would drain the battery quickly by restarting
    # over and over in a quick succession.
    watchdog.mode = None
    print("Code stopped by unhandled exception:")
    print(traceback.format_exception(None, e, e.__traceback__))
    RELOAD_TIME = 10
    print(f"Performing a supervisor reload in {RELOAD_TIME} seconds")
    time.sleep(RELOAD_TIME)
    supervisor.reload()
except WatchDogTimeout as e:
    hard_reset(e)
