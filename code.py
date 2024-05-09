# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: Unlicense
"""
Acquire values from various sensors, publish it to MQTT topic, enter deep sleep.

This is meant for battery powered devices such as QtPy or ESP32 based devices
from Adafruit.
"""
import json
import struct
import sys
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

# Try to import both RFM69 and WiFi modules so that fallback to WiFi can be done in main().
try:
    import adafruit_rfm69
except ImportError:
    pass

try:
    import wifi

    IMPORT_EXCEPTION = None
except MemoryError as e:
    # Let this fall through to main() so that appropriate reset can be performed.
    IMPORT_EXCEPTION = e

import digitalio

# pylint: disable=no-name-in-module
from microcontroller import watchdog
from watchdog import WatchDogMode, WatchDogTimeout

from logutil import get_log_level
from mqtt import mqtt_client_setup
from mqtt_handler import MQTTHandler
from sensors import Sensors
from sleep import SleepKind, enter_sleep

try:
    from secrets import secrets
except ImportError:
    print(
        "WiFi credentials and configuration are kept in secrets.py, please add them there!"
    )
    raise

# Estimated run time in seconds with some extra room.
# This is used to compute the watchdog timeout.
ESTIMATED_RUN_TIME = 20

BATTERY_CAPACITY_THRESHOLD = "battery_capacity_threshold"
SLEEP_DURATION_SHORT = "sleep_duration_short"
SLEEP_DURATION = "sleep_duration"
BROKER_PORT = "broker_port"
LOG_TOPIC = "log_topic"
MQTT_TOPIC = "mqtt_topic"
BROKER = "broker"
PASSWORD = "password"
SSID = "ssid"
LOG_LEVEL = "log_level"
TX_POWER = "tx_power"
ENCRYPTION_KEY = "encryption_key"


def blink(pixel):
    """
    Blink the Neo pixel blue.
    """
    pixel.brightness = 0.3
    pixel.fill((0, 0, 255))
    time.sleep(0.5)
    pixel.brightness = 0


def bail(message):
    """
    Print message and exit with code 1.
    """
    print(message)
    sys.exit(1)


def check_string(name, mandatory=True):
    """
    Check is string with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        bail(f"{name} is missing")

    if value and not isinstance(value, str):
        bail(f"not a string value for {name}: {value}")


def check_int(name, mandatory=True):
    """
    Check is integer with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        bail(f"{name} is missing")

    if value and not isinstance(value, int):
        bail(f"not a integer value for {name}: {value}")


def check_bytes(name, length, mandatory=True):
    """
    Check is bytes with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        bail(f"{name} is missing")

    if value and not isinstance(value, bytes):
        bail(f"not a byte value for {name}: {value}")

    if value and len(value) != length:
        bail(f"not correct length for {name}: {len(value)} should be {length}")


def check_tunables():
    """
    Check that tunables are present and of correct type.
    Will exit the program on error.
    """
    check_string(LOG_LEVEL)
    check_string(SSID)
    check_string(PASSWORD)
    check_string(BROKER)
    check_string(MQTT_TOPIC)
    check_string(LOG_TOPIC, mandatory=False)

    check_int(BROKER_PORT)
    broker_port = secrets.get(BROKER_PORT)
    if broker_port < 0 or broker_port > 65535:
        bail(f"invalid {BROKER_PORT} value: {broker_port}")

    check_int(SLEEP_DURATION)
    check_int(SLEEP_DURATION_SHORT, mandatory=False)

    # Check consistency of the sleep values.
    sleep_default = secrets.get(SLEEP_DURATION)
    sleep_short = secrets.get(SLEEP_DURATION_SHORT)
    if sleep_short is not None and sleep_short > sleep_default:
        bail(
            f"value of {SLEEP_DURATION_SHORT} bigger than value of {SLEEP_DURATION}: "
            + f"{sleep_short} > {sleep_default}"
        )

    check_int(BATTERY_CAPACITY_THRESHOLD, mandatory=False)

    check_int(TX_POWER, mandatory=False)
    check_bytes(ENCRYPTION_KEY, 16, mandatory=False)


# pylint: disable=too-many-locals,too-many-statements,too-many-branches
def main():
    """
    Collect temperature/humidity and battery level
    and publish to MQTT topic.
    """

    check_tunables()

    log_level = get_log_level(secrets[LOG_LEVEL])
    logger = logging.getLogger("")
    logger.setLevel(log_level)

    logger.info("Running")

    if IMPORT_EXCEPTION:
        raise IMPORT_EXCEPTION

    watchdog.timeout = ESTIMATED_RUN_TIME
    watchdog.mode = WatchDogMode.RAISE

    pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)

    # Create sensor objects, using the board's default I2C bus.
    try:
        i2c = board.I2C()
    except RuntimeError:
        # QtPy
        i2c = busio.I2C(board.SCL1, board.SDA1)

    battery_monitor = None
    try:
        battery_monitor = adafruit_max1704x.MAX17048(i2c)
    except NameError:
        logger.info("No library for battery gauge (max17048)")

    sensors = Sensors(i2c)

    mqtt_client, rfm69 = setup_transport()

    # MQTT topic is used for both transports.
    mqtt_topic = secrets[MQTT_TOPIC]

    while True:
        battery_level = None
        if battery_monitor:
            capacity = battery_monitor.cell_percent
            logger.info(f"Battery capacity {capacity:.2f} %")
            battery_level = capacity

        if mqtt_client:
            data = sensors.get_measurements_dict()
            if battery_level:
                data["battery_level"] = f"{capacity:.2f}"

            if len(data) > 0:
                logger.info(f"Publishing to {mqtt_topic}: {data}")
                mqtt_client.publish(mqtt_topic, json.dumps(data))
        elif rfm69:
            if battery_level is None:
                battery_level = 0
            humidity, temperature, co2_ppm = sensors.get_measurements()
            if co2_ppm is None:
                co2_ppm = 0

            # Note: at most 60 bytes can be sent in single packet so pack the data.
            fmt = ">30sIfII"
            if struct.calcsize(fmt) > 60:
                logger.warning(
                    "the format for structure packing is bigger than 60 bytes"
                )
            logger.info(
                "Sending data over radio: {(humidity,temperature,co2_ppm,battery_level)}"
            )
            data = struct.pack(
                fmt,
                mqtt_topic.encode("ascii"),
                humidity,
                temperature,
                co2_ppm,
                battery_level,
            )
            rfm69.send(data)
        else:
            logger.error("No way to send the data")

        # Blink the LED only in debug mode when powered by battery (to save the battery).
        if (
            not battery_monitor
            or log_level == logging.DEBUG  # pylint: disable=no-member
        ):
            blink(pixel)

        watchdog.feed()

        # Assuming that if the battery monitor is present, the device is running on battery power.
        if battery_monitor:
            logger.info("Running on battery power, breaking out")
            break

        if mqtt_client:
            sleep_duration_short = secrets.get(SLEEP_DURATION_SHORT)
            if sleep_duration_short:
                mqtt_timeout = sleep_duration_short
            else:
                mqtt_timeout = ESTIMATED_RUN_TIME // 2
            logger.info(f"Waiting for MQTT event with timeout {mqtt_timeout} seconds")
            mqtt_client.loop(timeout=mqtt_timeout)

    #
    # The rest of the code in this function applies only to devices running on battery power.
    #

    # Sleep a bit so one can break to the REPL when using console via web workflow.
    enter_sleep(10, SleepKind(SleepKind.LIGHT))  # ugh, ESTIMATED_RUN_TIME

    if mqtt_client:
        mqtt_client.disconnect()

    watchdog.mode = None

    sleep_duration = get_sleep_duration(battery_monitor, logger)

    enter_sleep(sleep_duration, SleepKind(SleepKind.DEEP))


def setup_transport():
    """
    Setup transport to send data.
    Return a tuple of RFM69 object and MQTT client object, either can be None.
    """
    logger = logging.getLogger(__name__)

    mqtt_client = None
    rfm69 = None
    # Try packetized radio first. If that does not work, fall back to WiFi.
    try:
        spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        # The D-pin values assume certain wiring of the Radio FeatherWing.
        cs = digitalio.DigitalInOut(board.D14)
        reset = digitalio.DigitalInOut(board.D32)
        logger.info("Setting up RFM69")
        rfm69 = adafruit_rfm69.RFM69(
            spi, cs, reset, 433
        )  # hard-coded frequency for Europe

        tx_power = secrets.get(TX_POWER)
        if rfm69.high_power and tx_power:
            logger.debug(f"setting TX power to {tx_power}")
            rfm69.tx_power = tx_power

        encryption_key = secrets.get(ENCRYPTION_KEY)
        if encryption_key:
            logger.debug("Setting encryption key")
            rfm69.encryption_key = encryption_key
    except Exception:  # pylint: disable=broad-exception-caught
        logger.debug(f"MAC address: {wifi.radio.mac_address}")

        # Connect to Wi-Fi
        logger.info("Connecting to wifi")
        wifi.radio.connect(secrets[SSID], secrets[PASSWORD], timeout=10)
        logger.info(f"Connected to {secrets['ssid']}")
        logger.debug(f"IP: {wifi.radio.ipv4_address}")

        # Create a socket pool
        pool = socketpool.SocketPool(wifi.radio)  # pylint: disable=no-member

        broker_addr = secrets[BROKER]
        broker_port = secrets[BROKER_PORT]
        mqtt_client = mqtt_client_setup(pool, broker_addr, broker_port, logger.getEffectiveLevel())
        try:
            log_topic = secrets[LOG_TOPIC]
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

    return mqtt_client, rfm69


def get_sleep_duration(battery_monitor, logger):
    """
    Get sleep duration, either default or shortened.
    Assumes the device is running on battery.
    """

    sleep_duration = secrets[SLEEP_DURATION]

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
