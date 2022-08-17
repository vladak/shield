#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: Unlicense
"""
Demonstrates MQTT client hang. Run 'nc -l 4444' on the '172.40.0.3' server first.
"""
try:
    import alarm
    import board
    import wifi
    import socketpool
    circuitpython_present = True
except ModuleNotFoundError:
    circuitpython_present = False
    import socket
import time
import digitalio
import ssl
import json
import time
import sys
import adafruit_minimqtt.adafruit_minimqtt as MQTT
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
sleep_duration = 20

def log(msg):    
    print(f"{time.monotonic()}: {msg}")

### Code ###
# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connect(mqtt_client, userdata, flags, rc):
    # This function will be called when the mqtt_client is connected
    # successfully to the broker.
    log("Connected to MQTT Broker!")
    log("Flags: {0}\n RC: {1}".format(flags, rc))


def disconnect(mqtt_client, userdata, rc):
    # This method is called when the mqtt_client disconnects
    # from the broker.
    log("Disconnected from MQTT Broker!")


def publish(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client publishes data to a feed.
    log("Published to {0} with PID {1}".format(topic, pid))


def go_to_sleep(sleep_period):
    if circuitpython_present:
        log("Going to sleep")
        # Turn off I2C power by setting it to input
        i2c_power = digitalio.DigitalInOut(board.I2C_POWER)
        i2c_power.switch_to_input()

        # Create an alarm that will trigger sleep_period number of seconds from now.
        time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_period)
        # Exit and deep sleep until the alarm wakes us.
        alarm.exit_and_deep_sleep_until_alarms(time_alarm)


def main():
    log(f"Running with {MQTT.__version__}")
    try:
        if circuitpython_present:
            # Connect to Wi-Fi
            log("Connecting to wifi")
            wifi.radio.connect(secrets["ssid"], secrets["password"], timeout=10)
            log("Connected to {}!".format(secrets["ssid"]))
            log(f"IP: {wifi.radio.ipv4_address}")
    except Exception as e:  # pylint: disable=broad-except
        log(f"Troubles getting IP connectivity: {e}")
        go_to_sleep(60)
        return

    # Create a socket pool
    if circuitpython_present:
        pool = socketpool.SocketPool(wifi.radio)
    else:
        pool = socket

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
        log(f"Got exception when connecting to MQTT broker, setting sleep timeout to 60s: {e}")
        go_to_sleep(60)
        return

    log(f"Publishing to {mqtt_topic}")
    data = {
        "foo": "bar",
    }
    mqtt_client.publish(mqtt_topic, json.dumps(data))
    log("Disconnecting from MQTT broker")
    mqtt_client.disconnect()

    go_to_sleep(sleep_duration)
    

try:
    main()
except Exception as e:
    log(f"error: {e}")

