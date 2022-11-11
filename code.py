# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: Unlicense
"""
Acquire temperature and battery level and publish it to MQTT topic.
"""
import json
import ssl
import time
import traceback

import adafruit_logging as logging
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_tmp117
import alarm
import board
import adafruit_max1704x
import microcontroller
import neopixel
import socketpool
import supervisor
import wifi
from microcontroller import watchdog
from watchdog import WatchDogMode, WatchDogTimeout

from logutil import get_log_level

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


# pylint: disable=unused-argument, redefined-outer-name, invalid-name
def connect(mqtt_client, userdata, flags, rc):
    """
    This function will be called when the mqtt_client is connected
    successfully to the broker.
    """
    logger = logging.getLogger(__name__)

    logger.info("Connected to MQTT Broker!")
    logger.debug("Flags: {0}\n RC: {1}".format(flags, rc))


# pylint: disable=unused-argument, invalid-name
def disconnect(mqtt_client, userdata, rc):
    """
    This method is called when the mqtt_client disconnects from the broker.
    """
    logger = logging.getLogger(__name__)

    logger.info("Disconnected from MQTT Broker!")


def publish(mqtt_client, userdata, topic, pid):
    """
    This method is called when the mqtt_client publishes data to a feed.
    """
    logger = logging.getLogger(__name__)

    logger.info(f"Published to {topic} with PID {pid}")


def go_to_sleep(sleep_period):
    """
    Enters "deep sleep".
    """
    # Create an alarm that will trigger sleep_period number of seconds from now.
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_period)
    # Exit and deep sleep until the alarm wakes us.
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)


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
    Collect temperature from the tmp117 sensor and battery level
    and publish with MQTT.
    """
    watchdog.timeout = ESTIMATED_RUN_TIME
    watchdog.mode = WatchDogMode.RAISE

    sleep_duration = secrets["sleep_duration"]

    log_level = get_log_level(secrets["log_level"])
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    logger.info("Running")

    # Create sensor objects, using the board's default I2C bus.
    i2c = board.I2C()
    tmp117 = adafruit_tmp117.TMP117(i2c)
    temperature = tmp117.temperature
    battery_monitor = adafruit_max1704x.MAX17048(i2c)

    logger.info("Temperature: {:.1f} C".format(temperature))
    # TODO: this cannot be displayed due to 'incomplete format'
    #       - maybe it needs to wait for something ?
    # logger.info("Battery Percent: {:.2f} %".format(battery_monitor.cell_percent))

    # Connect to Wi-Fi
    logger.info("Connecting to wifi")
    wifi.radio.connect(secrets["ssid"], secrets["password"], timeout=10)
    logger.info("Connected to {}".format(secrets["ssid"]))
    logger.debug(f"IP: {wifi.radio.ipv4_address}")

    # Create a socket pool
    pool = socketpool.SocketPool(wifi.radio)

    # Set up a MiniMQTT Client
    mqtt_client = MQTT.MQTT(
        broker=secrets["broker"],
        port=secrets["broker_port"],
        socket_pool=pool,
        ssl_context=ssl.create_default_context(),
    )

    # Connect callback handlers to mqtt_client
    mqtt_client.on_connect = connect
    mqtt_client.on_disconnect = disconnect
    mqtt_client.on_publish = publish

    logger.info(f"Attempting to connect to MQTT broker {mqtt_client.broker}")
    mqtt_client.connect()

    mqtt_topic = secrets["mqtt_topic"]
    logger.info(f"Publishing to {mqtt_topic}")
    data = {
        "temperature": "{:.1f}".format(temperature),
    }
    if battery_monitor:
        data["battery_level"] = "{:.2f}".format(battery_monitor.cell_percent)

    mqtt_client.publish(mqtt_topic, json.dumps(data))
    mqtt_client.disconnect()

    watchdog.feed()

    # Blink the LED only in debug mode (to save the battery).
    if log_level == logging.DEBUG:
        blink()

    # Sleep a bit so one can break to the REPL when using console via web workflow.
    close_sleep = 10
    logger.info(f"Sleeping for {close_sleep} seconds")
    time.sleep(close_sleep)  # ugh, ESTIMATED_RUN_TIME

    logger.info(f"Going to deep sleep for {sleep_duration} seconds")
    watchdog.deinit()
    go_to_sleep(sleep_duration)


try:
    main()
# pylint: disable=broad-except
except Exception as e:
    # This assumes that such exceptions are quite rare.
    # Otherwise this would drain the battery quickly.
    watchdog.deinit()
    print("Code stopped by unhandled exception:")
    print(traceback.format_exception(None, e, e.__traceback__))
    RELOAD_TIME = 10
    print(f"Performing a supervisor reload in {RELOAD_TIME} seconds")
    time.sleep(RELOAD_TIME)
    supervisor.reload()
except WatchDogTimeout:
    print("Code stopped by WatchDog timeout!")
    # NB, sometimes soft reset is not enough! need to do hard reset here
    RESET_TIME = 15
    print(f"Performing hard reset in {RESET_TIME} seconds")
    time.sleep(RESET_TIME)
    microcontroller.reset()
