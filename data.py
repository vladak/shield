"""
data manipulation functions
"""

import json
import struct

import adafruit_logging as logging

from sensors import Sensors

#
# Note: at most 60 bytes can be sent in single packet so pack the data.
# The following encoding scheme was designed to fit that constraint.
#
MAX_MQTT_TOPIC_LEN = 32
MQTT_PREFIX = "MQTT:"
DATA_PACK_FMT = f">{len(MQTT_PREFIX)}s{MAX_MQTT_TOPIC_LEN}sffIff"


# pylint: disable=too-many-arguments,too-many-positional-arguments
def pack_data(
    mqtt_topic: str, battery_capacity, co2_ppm, humidity, temperature, lux
) -> bytes:
    """
    Pack the structure with data.
    """
    logger = logging.getLogger("")

    if len(mqtt_topic) > MAX_MQTT_TOPIC_LEN:
        # Assuming ASCII encoding.
        raise ValueError(f"Maximum MQTT topic length is {MAX_MQTT_TOPIC_LEN}")

    if humidity is None:
        humidity = float("nan")

    if temperature is None:
        temperature = float("nan")

    if co2_ppm is None:
        co2_ppm = 0

    if battery_capacity is None:
        battery_level = float("nan")
    else:
        battery_level = battery_capacity

    if lux is None:
        lux = float("nan")

    logger.info(f"Packing data: {(humidity, temperature, co2_ppm, battery_level, lux)}")
    data = struct.pack(
        DATA_PACK_FMT,
        MQTT_PREFIX.encode("ascii"),
        mqtt_topic.encode("ascii"),
        humidity,
        temperature,
        co2_ppm,
        battery_level,
        lux,
    )
    return data


def unpack_data(data):
    """
    Unpack data into tuple. Used only for testing.
    """
    return struct.unpack(DATA_PACK_FMT, data)


def send_data(
    rfm69, mqtt_client, mqtt_topic: str, sensors: Sensors, battery_capacity
) -> None:
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

        #
        # mypy gets confused by the 'data' variable assignment in the adjacent
        # if branch above and thinks it should be of type dict and complains:
        #
        #  Incompatible types in assignment (expression has type "bytes",
        #  variable has type "dict[Any, Any] | None")
        #
        # So, the warning has to be suppressed (after several things were tried
        # to make it happy).
        #
        data = pack_data(
            mqtt_topic, battery_capacity, co2_ppm, humidity, temperature, lux
        )  # type: ignore [assignment]
        logger.debug(f"Raw data to be sent: {data}")
        rfm69.send(data)
    else:
        logger.error("No way to send the data")
