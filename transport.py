"""
RFM69 or WiFi setup
"""

import adafruit_logging as logging
import board
import busio
import digitalio

# pylint: disable=unused-wildcard-import, wildcard-import
from names import *


def wifi_tunables_ready(secrets: dict) -> bool:
    """
    check whether tunables for using Wi-Fi transport are available
    """
    logger = logging.getLogger("")

    if secrets.get(SSID) is None:
        logger.info(f"{SSID} not set in secrets, no Wi-Fi fallback")
        return False

    if secrets.get(PASSWORD) is None:
        logger.info(f"{PASSWORD} not set in secrets, no Wi-Fi fallback")
        return False

    if secrets.get(BROKER) is None:
        logger.info(f"{BROKER} not set in secrets, no WiFi fallback")
        return False

    return True


# pylint: disable=too-many-locals,too-many-statements
def setup_transport(secrets: dict):
    """
    Setup transport to send data.
    Return a tuple of RFM69 object and MQTT client object, either can be None.
    """
    logger = logging.getLogger("")

    mqtt_client = None
    rfm69 = None
    # Try packetized radio first. If that does not work, fall back to WiFi.
    try:
        spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        # The D-pin values assume certain wiring of the Radio FeatherWing.
        try:
            reset = digitalio.DigitalInOut(board.D6)
            cs = digitalio.DigitalInOut(board.D5)
        except AttributeError:
            # ESP32V2
            reset = digitalio.DigitalInOut(board.D32)
            cs = digitalio.DigitalInOut(board.D14)

        # pylint: disable=import-outside-toplevel
        import adafruit_rfm69

        logger.info("Setting up RFM69")
        rfm69 = adafruit_rfm69.RFM69(
            spi, cs, reset, 433
        )  # hard-coded frequency for Europe

        tx_power = secrets.get(TX_POWER)
        if rfm69.high_power and tx_power is not None:
            logger.debug(f"Setting TX power to {tx_power}")
            rfm69.tx_power = tx_power

        encryption_key = secrets.get(ENCRYPTION_KEY)
        if encryption_key:
            logger.info("Setting encryption key")
            rfm69.encryption_key = encryption_key
    except Exception as rfm69_exc:  # pylint: disable=broad-exception-caught
        logger.info(f"RFM69 failed to initialize: {rfm69_exc}")

        if not wifi_tunables_ready(secrets):
            return None, None

        logger.info("will attempt to connect to Wi-Fi")

        # pylint: disable=import-outside-toplevel
        import wifi

        logger.debug(f"MAC address: {wifi.radio.mac_address}")

        # Connect to Wi-Fi
        logger.info("Connecting to wifi")
        wifi.radio.connect(secrets[SSID], secrets[PASSWORD], timeout=10)
        logger.info(f"Connected to {secrets['ssid']}")
        logger.debug(f"IP: {wifi.radio.ipv4_address}")

        # pylint: disable=import-error,import-outside-toplevel
        import socketpool

        # Create a socket pool
        pool = socketpool.SocketPool(wifi.radio)  # pylint: disable=no-member

        # pylint: disable=import-outside-toplevel
        from mqtt import mqtt_client_setup
        from mqtt_handler import MQTTHandler

        broker_addr = secrets[BROKER]
        broker_port = secrets.get(BROKER_PORT)
        if broker_port is None:
            broker_port = 1883
            logger.info(
                f"Broker port not set in secrets, using default value of {broker_port}"
            )
        mqtt_client = mqtt_client_setup(
            pool, broker_addr, broker_port, logger.getEffectiveLevel()
        )
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
