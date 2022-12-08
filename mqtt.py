"""
MQTT utility functions
"""
import ssl

import adafruit_logging as logging
import adafruit_minimqtt.adafruit_minimqtt as MQTT


# pylint: disable=unused-argument, redefined-outer-name, invalid-name
def connect(mqtt_client, userdata, flags, rc):
    """
    This function will be called when the mqtt_client is connected
    successfully to the broker.
    """
    logger = logging.getLogger(__name__)

    logger.info("Connected to MQTT Broker!")
    logger.debug(f"Flags: {flags}\n RC: {rc}")


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


def mqtt_client_setup(pool, broker, port):
    """
    Set up a MiniMQTT Client
    """

    mqtt_client = MQTT.MQTT(
        broker=broker,
        port=port,
        socket_pool=pool,
        ssl_context=ssl.create_default_context(),
    )
    # Connect callback handlers to mqtt_client
    mqtt_client.on_connect = connect
    mqtt_client.on_disconnect = disconnect
    mqtt_client.on_publish = publish

    return mqtt_client
