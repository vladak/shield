"""
data manipulation functions
"""

import json
import struct

import adafruit_logging as logging


# pylint: disable=too-many-arguments,too-many-positional-arguments
def pack_data(mqtt_topic, battery_level, co2_ppm, humidity, temperature, lux):
    """
    Pack the structure with data.
    """
    logger = logging.getLogger("")

    # Note: at most 60 bytes can be sent in single packet so pack the data.
    # The following encoding scheme was designed to fit that constraint.
    mqtt_prefix = "MQTT:"
    max_mqtt_topic_len = 32
    if len(mqtt_topic) > max_mqtt_topic_len:
        # Assuming ASCII encoding.
        raise ValueError(f"Maximum MQTT topic length is {max_mqtt_topic_len}")
    fmt = f">{len(mqtt_prefix)}s{max_mqtt_topic_len}sffIff"
    logger.info(
        f"Sending data over radio: {(humidity, temperature, co2_ppm, battery_level, lux)}"
    )
    data = struct.pack(
        fmt,
        mqtt_prefix.encode("ascii"),
        mqtt_topic.encode("ascii"),
        humidity,
        temperature,
        co2_ppm,
        battery_level,
        lux,
    )
    return data


def send_data(rfm69, mqtt_client, mqtt_topic, sensors, battery_capacity):
    """
    Pick a transport, acquire sensor data and send them.
    """
    logger = logging.getLogger("")

    if mqtt_client:
        data = sensors.get_measurements_dict()
        if battery_capacity:
            data["battery_level"] = f"{battery_capacity:.2f}"

        if len(data) == 0:
            logger.warning("No sensor data available, will not publish")
            return

        logger.info(f"Publishing to {mqtt_topic}: {data}")
        mqtt_client.publish(mqtt_topic, json.dumps(data))
    elif rfm69:
        humidity, temperature, co2_ppm, lux = sensors.get_measurements()
        if (
            humidity is None
            and temperature is None
            and co2_ppm is None
            and battery_capacity is None
            and lux is None
        ):
            logger.warning("No sensor data available, will not send anything")
            return

        if temperature is None:
            temperature = 0

        if humidity is None:
            humidity = 0
        
        if battery_capacity is None:
            battery_level = 0
        else:
            battery_level = battery_capacity

        if co2_ppm is None:
            co2_ppm = 0

        if lux is None:
            lux = 0

        data = pack_data(mqtt_topic, battery_level, co2_ppm, humidity, temperature, lux)
        logger.debug(f"Raw data to be sent: {data}")
        rfm69.send(data)
    else:
        logger.error("No way to send the data")
