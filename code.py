# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: Unlicense
"""
Acquire temperature and battery level and publish it to MQTT topic.
"""
import alarm
import time
import board
import wifi
import digitalio
import ssl
import socketpool
import json
import board
import neopixel
import time
import sys
import adafruit_logging as logging
import adafruit_tmp117
# from adafruit_bme280 import basic as adafruit_bme280
from adafruit_lc709203f import LC709203F, PackSize
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from microcontroller import watchdog
from watchdog import WatchDogMode, WatchDogTimeout
import microcontroller
import supervisor
import traceback

try:
    from secrets import secrets
except ImportError:
    print("WiFi and Adafruit IO credentials are kept in secrets.py, please add them there!")
    raise

# MQTT Topic
# Use this topic if you'd like to connect to a standard MQTT broker
mqtt_topic = "devices/terasa/shield"

# Duration of sleep in seconds. Default is 600 seconds (10 minutes).
# Feather will sleep for this duration between sensor readings.
sleep_duration = 300


def log(msg):
    logger = logging.getLogger(__name__)

    # TODO: replace with logger
    print(f"{time.monotonic()}: {msg}")


# pylint: disable=unused-argument, redefined-outer-name
def connect(mqtt_client, userdata, flags, rc):
    logger = logging.getLogger(__name__)

    # This function will be called when the mqtt_client is connected
    # successfully to the broker.
    logger.info("Connected to MQTT Broker!")
    logger.debug("Flags: {0}\n RC: {1}".format(flags, rc))


def disconnect(mqtt_client, userdata, rc):
    # This method is called when the mqtt_client disconnects
    # from the broker.
    log("Disconnected from MQTT Broker!")


def publish(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client publishes data to a feed.
    log("Published to {0} with PID {1}".format(topic, pid))


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
    global sleep_duration

    watchdog.timeout = sleep_duration * 2
    watchdog.mode = WatchDogMode.RAISE

    # TODO: setup logger formatter to include timestamp
    logger = logging.getLogger(__name__)

    logger.info("Running")

    # Create sensor objects, using the board's default I2C bus.
    i2c = board.I2C()
    # bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
    tmp117 = adafruit_tmp117.TMP117(i2c)
    temperature = tmp117.temperature
    battery_monitor = LC709203F(board.I2C())
    battery_monitor.pack_size = PackSize.MAH2000

    logger.info("Temperature: {:.1f} C".format(temperature))
    # logger.info("Battery Percent: {:.2f} %".format(battery_monitor.cell_percent))

    try:
        # Connect to Wi-Fi
        log("Connecting to wifi")
        wifi.radio.connect(secrets["ssid"], secrets["password"], timeout=10)
        log("Connected to {}!".format(secrets["ssid"]))
        log(f"IP: {wifi.radio.ipv4_address}")
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

    log("Attempting to connect to MQTT broker %s" % mqtt_client.broker)
    try:
        mqtt_client.connect()
    except Exception as e:
        logger.error(f"Got exception when connecting to MQTT broker: {e}")
        go_to_sleep(sleep_duration // 5)
        return

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
    print(f'Code stopped by unhandled exception:')
    print(traceback.format_exception(None, e, e.__traceback__))
    # Can we log here?
    print('Performing a supervisor reload in 15s')
    time.sleep(15)  # TODO: Make sure this is shorter than watchdog timeout
    supervisor.reload()
except WatchDogTimeout:
    print('Code stopped by WatchDog timeout!')
    # supervisor.reload()
    # NB, sometimes soft reset is not enough! need to do hard reset here
    print('Performing hard reset in 15s')
    time.sleep(15)
    microcontroller.reset()
