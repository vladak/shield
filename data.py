"""
data manipulation functions
"""

import struct

import adafruit_logging as logging


# pylint: disable=too-many-arguments
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
    fmt = f">{len(mqtt_prefix)}s{max_mqtt_topic_len}sffIfI"
    logger.info(
        f"Sending data over radio: {(humidity, temperature, co2_ppm, battery_level)}"
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
