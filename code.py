# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: Unlicense
"""
Acquire values from various sensors, publish it to MQTT topic, enter deep sleep.

This is meant for battery powered devices such as QtPy or ESP32 based devices
from Adafruit.
"""
import json
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
import neopixel

# pylint: disable=import-error
import socketpool

# pylint: disable=import-error
import supervisor

try:
    import wifi
except MemoryError as e:
    # Let this fall through to main() so that appropriate reset can be performed.
    IMPORT_EXCEPTION = e

# from digitalio import DigitalInOut
# pylint: disable=no-name-in-module
from microcontroller import watchdog
from watchdog import WatchDogMode, WatchDogTimeout

from logutil import get_log_level
from mqtt import mqtt_client_setup
from mqtt_handler import MQTTHandler
from sensors import get_measurements
from sleep import SleepKind, enter_sleep

try:
    from secrets import secrets
except ImportError:
    print(
        "WiFi and Adafruit IO credentials are kept in secrets.py, please add them there!"
    )
    raise

# Estimated run time in seconds with some extra room.
# This is used to compute the watchdog timeout.
ESTIMATED_RUN_TIME = 20

# For storing import exceptions so that they can be raised from main().
IMPORT_EXCEPTION = None


def blink():
    """
    Blink the Neo pixel blue.
    """
    pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)

    pixel.brightness = 0.3
    pixel.fill((0, 0, 255))
    time.sleep(0.5)


def main():
    """
    Collect temperature/humidity and battery level
    and publish to MQTT topic.
    """

    log_level = get_log_level(secrets["log_level"])
    logger = logging.getLogger("")
    logger.setLevel(log_level)

    logger.info("Running")

    if IMPORT_EXCEPTION:
        raise IMPORT_EXCEPTION

    # If the 'SW38' button on the ESP32 V2 was pressed, exit the program so that
    # web based workflow can be used.
    # button = DigitalInOut(board.BUTTON)
    # if button.value:
    #    logger.info("button pressed, exiting")
    #    button.value = False
    #    return

    watchdog.timeout = ESTIMATED_RUN_TIME
    watchdog.mode = WatchDogMode.RAISE

    sleep_duration = secrets["sleep_duration"]

    # Create sensor objects, using the board's default I2C bus.
    try:
        i2c = board.I2C()
    except RuntimeError:
        # QtPy
        i2c = busio.I2C(board.SCL1, board.SDA1)

    humidity, temperature = get_measurements(i2c)

    battery_monitor = None
    try:
        battery_monitor = adafruit_max1704x.MAX17048(i2c)
    except NameError:
        logger.info("No library for battery gauge (max17048)")

    logger.debug(f"MAC address: {wifi.radio.mac_address}")

    # Connect to Wi-Fi
    logger.info("Connecting to wifi")
    wifi.radio.connect(secrets["ssid"], secrets["password"], timeout=10)
    logger.info(f"Connected to {secrets['ssid']}")
    logger.debug(f"IP: {wifi.radio.ipv4_address}")

    # Create a socket pool
    pool = socketpool.SocketPool(wifi.radio)  # pylint: disable=no-member

    broker_addr = secrets["broker"]
    broker_port = secrets["broker_port"]
    mqtt_client = mqtt_client_setup(pool, broker_addr, broker_port, log_level)
    try:
        log_topic = secrets["log_topic"]
        # Log both to the console and via MQTT messages.
        # Up to now the logger was using the default (built-in) handler,
        # now it is necessary to add the Stream handler explicitly as
        # with a non-default handler set only the non-default handlers will be used.
        logger.addHandler(logging.StreamHandler())
        logger.addHandler(MQTTHandler(mqtt_client, log_topic))
    except KeyError:
        pass

    logger.info(f"Attempting to connect to MQTT broker {broker_addr}:{broker_port}")
    mqtt_client.connect()

    data = {}
    fill_data_dict(data, battery_monitor, humidity, temperature)

    if len(data) > 0:
        mqtt_topic = secrets["mqtt_topic"]
        logger.info(f"Publishing to {mqtt_topic}")
        mqtt_client.publish(mqtt_topic, json.dumps(data))

    watchdog.feed()

    # Blink the LED only in debug mode (to save the battery).
    if log_level == logging.DEBUG:  # pylint: disable=no-member
        blink()

    # Sleep a bit so one can break to the REPL when using console via web workflow.
    enter_sleep(10, SleepKind(SleepKind.LIGHT))  # ugh, ESTIMATED_RUN_TIME

    mqtt_client.disconnect()

    watchdog.deinit()

    enter_sleep(sleep_duration, SleepKind(SleepKind.DEEP))


def fill_data_dict(data, battery_monitor, humidity, temperature):
    """
    Put the metrics into dictionary.
    """

    logger = logging.getLogger("")

    if temperature:
        logger.info(f"Temperature: {temperature:.1f} C")
        data["temperature"] = f"{temperature:.1f}"
    if humidity:
        logger.info(f"Humidity: {humidity:.1f} %%")
        data["humidity"] = f"{humidity:.1f}"
    if battery_monitor:
        capacity = battery_monitor.cell_percent
        logger.info(f"Battery capacity {capacity:.2f} %%")
        data["battery_level"] = f"{capacity:.2f}"

    logger.debug(f"data: {data}")


def hard_reset(exception):
    """
    Sometimes soft reset is not enough. Perform hard reset.
    """
    watchdog.deinit()
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
    watchdog.deinit()
    print("Code stopped by unhandled exception:")
    print(traceback.format_exception(None, e, e.__traceback__))
    RELOAD_TIME = 10
    print(f"Performing a supervisor reload in {RELOAD_TIME} seconds")
    time.sleep(RELOAD_TIME)
    supervisor.reload()
except WatchDogTimeout as e:
    hard_reset(e)
