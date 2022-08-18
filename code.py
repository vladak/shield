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
import digitalio
import microcontroller
import neopixel
import socketpool
import supervisor
import wifi
from adafruit_lc709203f import LC709203F, PackSize
from microcontroller import watchdog
from watchdog import WatchDogMode, WatchDogTimeout

try:
    from secrets import secrets
except ImportError:
    print(
        "WiFi and Adafruit IO credentials are kept in secrets.py, please add them there!"
    )
    raise


# pylint: disable=unused-argument, redefined-outer-name
def connect(mqtt_client, userdata, flags, rc):
    """
    This function will be called when the mqtt_client is connected
    successfully to the broker.
    """
    logger = logging.getLogger(__name__)

    logger.info("Connected to MQTT Broker!")
    logger.debug("Flags: {0}\n RC: {1}".format(flags, rc))


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

    logger.info("Published to {0} with PID {1}".format(topic, pid))


def go_to_sleep(sleep_period):
    # Turn off I2C power by setting it to input
    i2c_power = digitalio.DigitalInOut(board.I2C_POWER)
    i2c_power.switch_to_input()

    # Create an alarm that will trigger sleep_period number of seconds from now.
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_period)
    # Exit and deep sleep until the alarm wakes us.
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)


def blink():
    pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)

    pixel.brightness = 0.3
    pixel.fill((0, 255, 0))
    time.sleep(0.5)


def main():
    sleep_duration = secrets["sleep_duration"]

    # Estimated run time in seconds with some extra room.
    # This is used to compute the watchdog timeout.
    estimated_run_time = 20

    watchdog.timeout = sleep_duration + estimated_run_time
    watchdog.mode = WatchDogMode.RAISE

    logger = logging.getLogger(__name__)

    logger.info("Running")

    # Create sensor objects, using the board's default I2C bus.
    i2c = board.I2C()
    tmp117 = adafruit_tmp117.TMP117(i2c)
    temperature = tmp117.temperature
    battery_monitor = LC709203F(board.I2C())
    battery_monitor.pack_size = PackSize.MAH2000

    logger.info("Temperature: {:.1f} C".format(temperature))
    # logger.info("Battery Percent: {:.2f} %".format(battery_monitor.cell_percent))

    try:
        # Connect to Wi-Fi
        logger.info("Connecting to wifi")
        wifi.radio.connect(secrets["ssid"], secrets["password"], timeout=10)
        logger.info("Connected to {}!".format(secrets["ssid"]))
        logger.debug(f"IP: {wifi.radio.ipv4_address}")
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Troubles getting IP connectivity: {e}")
        go_to_sleep(sleep_duration // 5)
        return

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
    try:
        mqtt_client.connect()
    except Exception as exc:
        logger.error(f"Got exception when connecting to MQTT broker: {exc}")
        go_to_sleep(sleep_duration // 5)
        return

    mqtt_topic = secrets["mqtt_topic"]
    logger.info(f"Publishing to {mqtt_topic}")
    data = {
        "temperature": "{:.1f}".format(temperature),
        "battery_level": "{:.2f}".format(battery_monitor.cell_percent),
    }
    try:
        mqtt_client.publish(mqtt_topic, json.dumps(data))
    except Exception as exc:
        logger.error(f"Got exception when publishing to MQTT broker: {exc}")
        go_to_sleep(sleep_duration // 5)
        return

    mqtt_client.disconnect()

    watchdog.feed()

    # TODO: blink the LED only in debug mode (to save the battery)
    # blink()

    logger.info(f"Going to sleep for {sleep_duration} seconds")
    go_to_sleep(sleep_duration)


try:
    main()
except Exception as e:
    print("Code stopped by unhandled exception:")
    print(traceback.format_exception(None, e, e.__traceback__))
    # Can we log here?
    print("Performing a supervisor reload in 15s")
    time.sleep(15)  # TODO: Make sure this is shorter than watchdog timeout
    supervisor.reload()
except WatchDogTimeout:
    print("Code stopped by WatchDog timeout!")
    # NB, sometimes soft reset is not enough! need to do hard reset here
    print("Performing hard reset in 15s")
    time.sleep(15)
    microcontroller.reset()
